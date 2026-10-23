// =====================================================================
// targetManager.ts — Target lifecycle, movement patterns & hit detection
// =====================================================================

import * as THREE from 'three';
import { Renderer } from './renderer';
import {
  TARGET_SIZE_DEFAULT,
  HEAD_LEVEL_Y,
  TARGET_SPAWN_DIST_MIN,
  TARGET_SPAWN_DIST_MAX,
} from './constants';
import type { MovementPattern, HitResult, ScenarioConfig } from './types';

export interface ActiveTarget {
  id: string;
  position: THREE.Vector3;
  radius: number;
  pattern: MovementPattern;
  origin: THREE.Vector3;
  velocity: THREE.Vector3;
  phase: number;
  speed: number;
  range: number;
  alive: boolean;
  spawnTime: number;
  lifetimeSec: number;
  isCovered?: boolean;
}

export class TargetManager {
  private renderer: Renderer;
  private targets = new Map<string, ActiveTarget>();
  private nextId = 1;

  constructor(renderer: Renderer) {
    this.renderer = renderer;
  }

  clear(): void {
    this.targets.clear();
    this.renderer.clearTargets();
  }

  getActiveCount(): number {
    return this.targets.size;
  }

  getTargets(): ActiveTarget[] {
    return Array.from(this.targets.values());
  }

  spawnTarget(
    config: ScenarioConfig,
    customPos?: THREE.Vector3,
    customPattern?: MovementPattern,
    lifetimeSec = 0
  ): ActiveTarget {
    const id = `target_${this.nextId++}`;
    const radius = TARGET_SIZE_DEFAULT * config.targetSizeMultiplier;

    let pos: THREE.Vector3;

    if (customPos) {
      pos = customPos.clone();
    } else {
      // Random angle in front of player (arc of approx 140° or wide swing)
      let arc = Math.PI * 0.75;
      if (config.category === 'tactical' && config.name.includes('Wide Swing')) {
        arc = Math.PI * 0.95;
      }

      const angle = (Math.random() - 0.5) * arc;
      const dist = TARGET_SPAWN_DIST_MIN + Math.random() * (TARGET_SPAWN_DIST_MAX - TARGET_SPAWN_DIST_MIN);

      const x = Math.sin(angle) * dist;
      const z = -Math.cos(angle) * dist;

      let y = HEAD_LEVEL_Y;
      if (!config.headLevel) {
        y = HEAD_LEVEL_Y + (Math.random() - 0.5) * 1.8;
      }

      pos = new THREE.Vector3(x, Math.max(0.4, y), z);
    }

    const pattern = customPattern || config.movementPattern;
    const speed = (2.0 + Math.random() * 2.5) * config.targetSpeedMultiplier;
    const range = 2.0 + Math.random() * 3.5;

    const target: ActiveTarget = {
      id,
      position: pos.clone(),
      radius,
      pattern,
      origin: pos.clone(),
      velocity: new THREE.Vector3(
        (Math.random() - 0.5) * speed,
        0,
        (Math.random() - 0.5) * speed
      ),
      phase: Math.random() * Math.PI * 2,
      speed,
      range,
      alive: true,
      spawnTime: performance.now(),
      lifetimeSec,
    };

    this.targets.set(id, target);
    this.renderer.addTarget(id, target.position, target.radius);
    return target;
  }

  update(delta: number, now = performance.now()): void {
    const dt = Math.min(delta, 0.1);
    const toRemove: string[] = [];

    for (const [id, target] of this.targets) {
      if (!target.alive) {
        toRemove.push(id);
        continue;
      }

      // Check lifetime expiration
      if (target.lifetimeSec > 0) {
        const elapsed = (now - target.spawnTime) / 1000;
        if (elapsed >= target.lifetimeSec) {
          toRemove.push(id);
          continue;
        }
      }

      target.phase += dt * target.speed;

      switch (target.pattern) {
        case 'static':
          // Stays at origin
          target.position.copy(target.origin);
          break;

        case 'strafe': {
          // Strafe laterally perpendicular to Z
          const offset = Math.sin(target.phase) * target.range;
          target.position.x = target.origin.x + offset;
          break;
        }

        case 'jiggle': {
          // Sharp fast jiggle peek (simulate Valorant ADAD peek)
          // Uses square-wave / sharp sine pattern
          const raw = Math.sin(target.phase * 2.8);
          const jiggleX = Math.sign(raw) * Math.pow(Math.abs(raw), 0.3) * (target.range * 0.6);
          target.position.x = target.origin.x + jiggleX;
          break;
        }

        case 'wander': {
          // Smooth 2D wandering in arena
          const nx = target.origin.x + Math.sin(target.phase * 0.7) * target.range;
          const nz = target.origin.z + Math.cos(target.phase * 0.9) * (target.range * 0.7);
          target.position.x = nx;
          target.position.z = nz;
          break;
        }

        case 'peek': {
          // Emerge from cover, stay exposed briefly, then retreat
          // Half-wave pulse
          const cycle = (target.phase % (Math.PI * 2));
          if (cycle < Math.PI) {
            target.position.x = target.origin.x + Math.sin(cycle) * target.range;
            target.isCovered = false;
          } else {
            target.position.x = target.origin.x;
            target.isCovered = true;
          }
          break;
        }

        case 'vertical': {
          // Oscillate elevation to practice micro adjustments on crouch/jump
          const vertOffset = Math.sin(target.phase * 1.5) * (target.range * 0.4);
          target.position.y = Math.max(0.4, target.origin.y + vertOffset);
          break;
        }

        case 'variable': {
          // Variable speed / sudden stops
          const speedFactor = 0.5 + 0.5 * Math.sin(target.phase * 0.5);
          const varOffset = Math.sin(target.phase * speedFactor * 2.0) * target.range;
          target.position.x = target.origin.x + varOffset;
          break;
        }
      }

      this.renderer.updateTargetPosition(id, target.position);
    }

    for (const id of toRemove) {
      this.removeTarget(id);
    }
  }

  removeTarget(id: string): void {
    const target = this.targets.get(id);
    if (target) {
      target.alive = false;
      this.targets.delete(id);
      this.renderer.removeTarget(id);
    }
  }

  // Raycast from crosshair (camera center) to find closest target hit
  checkHit(ray: THREE.Ray): HitResult {
    let closestTarget: ActiveTarget | null = null;
    let minDistance = Infinity;
    let hitAccScore = 0;
    let isHeadshot = false;

    for (const target of this.targets.values()) {
      if (!target.alive) continue;

      // Vector from ray origin to sphere center
      const toCenter = new THREE.Vector3().subVectors(target.position, ray.origin);
      const proj = toCenter.dot(ray.direction);

      // Sphere is behind the ray
      if (proj <= 0) continue;

      // Perpendicular distance from ray to target center
      const closestPointOnRay = new THREE.Vector3().copy(ray.origin).addScaledVector(ray.direction, proj);
      const perpDist = closestPointOnRay.distanceTo(target.position);

      if (perpDist <= target.radius) {
        // Target is hit! Check if closest hit along ray
        if (proj < minDistance) {
          minDistance = proj;
          closestTarget = target;

          // Accuracy: 1.0 = dead center, 0.0 = edge of radius
          hitAccScore = Math.max(0, 1 - (perpDist / target.radius));

          // Headshot: upper 35% of the target sphere
          const hitPointY = closestPointOnRay.y;
          isHeadshot = hitPointY > (target.position.y + target.radius * 0.25);
        }
      }
    }

    if (closestTarget) {
      const reactionMs = performance.now() - closestTarget.spawnTime;
      return {
        hit: true,
        headshot: isHeadshot,
        targetId: closestTarget.id,
        distanceMetres: minDistance,
        reactionMs,
        accuracyScore: hitAccScore,
      };
    }

    return {
      hit: false,
      headshot: false,
      targetId: '',
      distanceMetres: 0,
      reactionMs: 0,
      accuracyScore: 0,
    };
  }

  // Evaluates tracking: is crosshair currently hovering over a target?
  checkTracking(ray: THREE.Ray): { isOnTarget: boolean; targetId?: string; accuracy: number } {
    for (const target of this.targets.values()) {
      if (!target.alive) continue;

      const toCenter = new THREE.Vector3().subVectors(target.position, ray.origin);
      const proj = toCenter.dot(ray.direction);
      if (proj <= 0) continue;

      const closestPointOnRay = new THREE.Vector3().copy(ray.origin).addScaledVector(ray.direction, proj);
      const perpDist = closestPointOnRay.distanceTo(target.position);

      if (perpDist <= target.radius) {
        const accuracy = Math.max(0, 1 - (perpDist / target.radius));
        return { isOnTarget: true, targetId: target.id, accuracy };
      }
    }
    return { isOnTarget: false, accuracy: 0 };
  }
}
