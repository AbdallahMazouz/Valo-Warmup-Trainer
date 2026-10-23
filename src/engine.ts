// =====================================================================
// engine.ts — Core Simulation Engine & Session Lifecycle
// =====================================================================

import * as THREE from 'three';
import { Renderer } from './renderer';
import { Controls } from './controls';
import { TargetManager } from './targetManager';
import { AudioManager } from './audio';
import { SettingsManager } from './settings';
import { Store } from './store';
import {
  SCORE_HIT,
  SCORE_HEADSHOT,
  SCORE_MISS,
  SCORE_SPEED_MAX,
  SCORE_SPEED_DECAY,
} from './constants';
import type { ScenarioConfig, SessionResult } from './types';

export interface EngineCallbacks {
  onTick?: (hud: EngineHUDState) => void;
  onHit?: (pts: number, headshot: boolean, x: number, y: number) => void;
  onMiss?: () => void;
  onFlash?: (intensity: number, durationMs: number) => void;
  onScenarioComplete?: (result: SessionResult, isPB: boolean) => void;
  onMovementInaccurate?: () => void;
}

export interface EngineHUDState {
  timeRemaining: number;
  totalDuration: number;
  score: number;
  hits: number;
  misses: number;
  accuracy: number;
  headshots: number;
  fps: number;
  isTracking: boolean;
}

export class Engine {
  renderer: Renderer;
  controls: Controls;
  targets: TargetManager;
  audio: AudioManager;
  settings: SettingsManager;
  store: Store;

  activeConfig: ScenarioConfig | null = null;
  isRunning = false;
  isPaused = false;

  private startTime = 0;
  private durationSec = 60;
  private score = 0;
  private hits = 0;
  private misses = 0;
  private headshots = 0;
  private reactions: number[] = [];

  // Tracking metrics
  private totalTrackingTicks = 0;
  private onTargetTrackingTicks = 0;

  // Flash metrics
  private nextFlashTime = 0;
  private flashAvoidCount = 0;
  private totalFlashes = 0;

  // Frame timing
  private lastTime = 0;
  private fpsFrames = 0;
  private fpsLastCalc = 0;
  private currentFps = 60;

  callbacks: EngineCallbacks = {};

  constructor(
    renderer: Renderer,
    controls: Controls,
    audio: AudioManager,
    settings: SettingsManager,
    store: Store
  ) {
    this.renderer = renderer;
    this.controls = controls;
    this.audio = audio;
    this.settings = settings;
    this.store = store;

    this.targets = new TargetManager(this.renderer);

    // Bind controls
    this.controls.onShoot = this.handleShoot.bind(this);
    this.controls.sensitivity = this.settings.get('sensitivity');
    this.controls.invertY = this.settings.get('invertY');
    this.renderer.updateFov(this.settings.get('fov'));
  }

  startScenario(config: ScenarioConfig): void {
    this.activeConfig = config;
    this.durationSec = config.durationSec;
    this.score = 0;
    this.hits = 0;
    this.misses = 0;
    this.headshots = 0;
    this.reactions = [];
    this.totalTrackingTicks = 0;
    this.onTargetTrackingTicks = 0;
    this.flashAvoidCount = 0;
    this.totalFlashes = 0;

    this.targets.clear();
    this.controls.reset(
      new THREE.Vector3(0, 1.7, 0),
      0,
      0
    );

    // Initial target spawn
    for (let i = 0; i < config.targetCount; i++) {
      this.targets.spawnTarget(config);
    }

    if (config.flashEnabled) {
      this.nextFlashTime = performance.now() + 4000 + Math.random() * 5000;
    }

    this.startTime = performance.now();
    this.lastTime = performance.now();
    this.fpsLastCalc = performance.now();
    this.fpsFrames = 0;
    this.isRunning = true;
    this.isPaused = false;

    this.audio.playStart();
  }

  stopScenario(): void {
    if (!this.isRunning) return;
    this.isRunning = false;
    this.targets.clear();
  }

  private handleShoot(): void {
    if (!this.isRunning || this.isPaused || !this.activeConfig) return;

    // Movement inaccuracy check (Valorant counter-strafing requirement)
    if (this.activeConfig.requireSteadyAim) {
      if (!this.controls.isCounterStrafed()) {
        // Player shot while moving!
        this.misses++;
        this.score = Math.max(0, this.score + SCORE_MISS * 2);
        this.audio.playMiss();
        if (this.callbacks.onMovementInaccurate) {
          this.callbacks.onMovementInaccurate();
        }
        if (this.callbacks.onMiss) {
          this.callbacks.onMiss();
        }
        return;
      }
    }

    const ray = this.controls.getRay();
    const hit = this.targets.checkHit(ray);

    if (hit.hit) {
      this.hits++;
      this.reactions.push(hit.reactionMs);

      let pts = SCORE_HIT;
      if (hit.headshot) {
        this.headshots++;
        pts += SCORE_HEADSHOT;
      }

      // Bonus for center accuracy
      pts += Math.round(hit.accuracyScore * 50);

      // Speed bonus: faster flick = higher score
      const speedBonus = Math.max(0, Math.round(SCORE_SPEED_MAX - hit.reactionMs * SCORE_SPEED_DECAY));
      pts += speedBonus;

      this.score += pts;
      this.audio.playHit(hit.headshot);
      this.renderer.flashTarget(hit.targetId);

      // Despawn and replace target
      this.targets.removeTarget(hit.targetId);
      if (this.targets.getActiveCount() < this.activeConfig.targetCount) {
        this.targets.spawnTarget(this.activeConfig);
      }

      if (this.callbacks.onHit) {
        this.callbacks.onHit(pts, hit.headshot, 0, 0);
      }
    } else {
      if (this.activeConfig.penalizeMiss) {
        this.misses++;
        this.score = Math.max(0, this.score + SCORE_MISS);
        this.audio.playMiss();
        if (this.callbacks.onMiss) {
          this.callbacks.onMiss();
        }
      }
    }
  }

  update(): void {
    const now = performance.now();
    const delta = (now - this.lastTime) / 1000;
    this.lastTime = now;

    // Calculate FPS
    this.fpsFrames++;
    if (now - this.fpsLastCalc >= 500) {
      this.currentFps = Math.round((this.fpsFrames * 1000) / (now - this.fpsLastCalc));
      this.fpsFrames = 0;
      this.fpsLastCalc = now;
    }

    if (!this.isRunning || this.isPaused || !this.activeConfig) {
      // Just render scene
      this.renderer.render();
      return;
    }

    const elapsed = (now - this.startTime) / 1000;
    const remaining = Math.max(0, this.durationSec - elapsed);

    // Update player movement (enable movement if scenario involves counter-strafing or evasion)
    const movementEnabled = this.activeConfig.category === 'movement' ||
      this.activeConfig.id === 'tactical-counter-strafe' ||
      this.activeConfig.id.includes('duel') ||
      this.activeConfig.id.includes('clutch');

    this.controls.update(delta, movementEnabled);
    this.targets.update(delta, now);

    // Maintain target count
    while (this.targets.getActiveCount() < this.activeConfig.targetCount) {
      this.targets.spawnTarget(this.activeConfig);
    }

    // Tracking scenario logic
    let isCurrentlyTracking = false;
    if (this.activeConfig.category === 'tracking') {
      this.totalTrackingTicks++;
      const ray = this.controls.getRay();
      const track = this.targets.checkTracking(ray);
      if (track.isOnTarget) {
        this.onTargetTrackingTicks++;
        isCurrentlyTracking = true;
        // Continuous score accumulation for tracking
        this.score += Math.round(15 * (0.8 + 0.4 * track.accuracy));
      }
    }

    // Flash scenario logic
    if (this.activeConfig.flashEnabled && now >= this.nextFlashTime) {
      this.totalFlashes++;
      this.audio.playFlash();

      // Check if player turned away from flash position (placed at 0, 1.8, -10)
      const flashPos = new THREE.Vector3(0, 1.8, -10);
      const camDir = new THREE.Vector3();
      this.controls.camera.getWorldDirection(camDir);

      const toFlash = new THREE.Vector3().subVectors(flashPos, this.controls.yawObject.position).normalize();
      const dot = camDir.dot(toFlash);

      // If dot < 0.25, the player has turned away > 75 degrees!
      let flashIntensity = this.activeConfig.flashIntensity;
      if (dot < 0.25) {
        // Successful flash dodge!
        this.flashAvoidCount++;
        flashIntensity *= 0.12; // minimal glare
        this.score += 250; // reward for turning flash
      }

      const dur = this.activeConfig.flashDurationMs;
      if (this.callbacks.onFlash) {
        this.callbacks.onFlash(flashIntensity, dur);
      }

      this.nextFlashTime = now + 6000 + Math.random() * 7000;
    }

    // HUD Callback
    const totalShots = this.hits + this.misses;
    const accuracy = totalShots > 0 ? (this.hits / totalShots) * 100 : 0;

    if (this.callbacks.onTick) {
      this.callbacks.onTick({
        timeRemaining: remaining,
        totalDuration: this.durationSec,
        score: this.score,
        hits: this.hits,
        misses: this.misses,
        accuracy,
        headshots: this.headshots,
        fps: this.currentFps,
        isTracking: isCurrentlyTracking,
      });
    }

    // Render frame
    this.renderer.render();

    // Check completion
    if (remaining <= 0) {
      this.completeScenario();
    }
  }

  private completeScenario(): void {
    if (!this.isRunning || !this.activeConfig) return;
    this.isRunning = false;
    this.audio.playEnd();

    const totalShots = this.hits + this.misses;
    const accuracy = totalShots > 0 ? (this.hits / totalShots) * 100 : 0;

    // Reactions statistics
    const sorted = [...this.reactions].sort((a, b) => a - b);
    const avgReaction = this.reactions.length > 0
      ? this.reactions.reduce((a, b) => a + b, 0) / this.reactions.length
      : 0;
    const medianReaction = sorted.length > 0
      ? sorted[Math.floor(sorted.length / 2)]
      : 0;
    const bestReaction = sorted.length > 0 ? sorted[0] : 0;
    const targetsPerSec = this.durationSec > 0 ? (this.hits / this.durationSec) : 0;

    const timeOnTarget = this.totalTrackingTicks > 0
      ? (this.onTargetTrackingTicks / this.totalTrackingTicks)
      : undefined;

    const flashAvoidRate = this.totalFlashes > 0
      ? (this.flashAvoidCount / this.totalFlashes) * 100
      : undefined;

    const result: SessionResult = {
      id: `session_${Date.now()}`,
      scenarioId: this.activeConfig.id,
      scenarioName: this.activeConfig.name,
      category: this.activeConfig.category,
      difficulty: this.activeConfig.difficulty,
      timestamp: Date.now(),
      durationSec: this.durationSec,
      score: this.score,
      hits: this.hits,
      misses: this.misses,
      headshots: this.headshots,
      accuracy,
      avgReactionMs: Math.round(avgReaction),
      medianReactionMs: Math.round(medianReaction),
      bestReactionMs: Math.round(bestReaction),
      targetsPerSecond: Number(targetsPerSec.toFixed(2)),
      timeOnTarget: timeOnTarget ? Number((timeOnTarget * 100).toFixed(1)) : undefined,
      flashAvoidRate: flashAvoidRate ? Number(flashAvoidRate.toFixed(1)) : undefined,
    };

    const { isPB } = this.store.addSession(result);
    if (isPB) {
      this.audio.playPB();
    }

    if (this.callbacks.onScenarioComplete) {
      this.callbacks.onScenarioComplete(result, isPB);
    }
  }

  applySettings(): void {
    this.controls.sensitivity = this.settings.get('sensitivity');
    this.controls.invertY = this.settings.get('invertY');
    this.renderer.updateFov(this.settings.get('fov'));
    this.audio.setVolume(this.settings.get('volume'));
  }
}
