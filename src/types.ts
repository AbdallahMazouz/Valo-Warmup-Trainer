// =====================================================================
// types.ts — Shared TypeScript interfaces and types
// =====================================================================

export type CategoryId =
  | 'flick' | 'tracking' | 'tactical'
  | 'flash' | 'reaction' | 'movement' | 'hybrid';

export type DifficultyId = 'beginner' | 'intermediate' | 'advanced' | 'pro';

export interface ScenarioConfig {
  id: string;
  name: string;
  category: CategoryId;
  description: string;
  skill: string;
  difficulty: DifficultyId;
  durationSec: number;
  targetCount: number;
  targetSizeMultiplier: number;
  targetSpeedMultiplier: number;
  spawnRadius: number;
  movementPattern: MovementPattern;
  headLevel: boolean;
  flashEnabled: boolean;
  flashIntensity: number;
  flashDurationMs: number;
  requireSteadyAim: boolean;
  penalizeMiss: boolean;
}

export type MovementPattern =
  | 'static'
  | 'strafe'
  | 'jiggle'
  | 'wander'
  | 'peek'
  | 'vertical'
  | 'variable';

export interface HitResult {
  hit: boolean;
  headshot: boolean;
  targetId: string;
  distanceMetres: number;
  reactionMs: number;
  accuracyScore: number; // 0-1, 1 = dead center
}

export interface SessionResult {
  id: string;
  scenarioId: string;
  scenarioName: string;
  category: CategoryId;
  difficulty: DifficultyId;
  timestamp: number;
  durationSec: number;
  score: number;
  hits: number;
  misses: number;
  headshots: number;
  accuracy: number;           // 0-100
  avgReactionMs: number;
  medianReactionMs: number;
  bestReactionMs: number;
  targetsPerSecond: number;
  timeOnTarget?: number;      // for tracking (0-1)
  flashAvoidRate?: number;    // for flash scenarios
}

export interface PersonalBest {
  scenarioId: string;
  score: number;
  accuracy: number;
  avgReactionMs: number;
  timestamp: number;
}

export interface Settings {
  sensitivity: number;
  fov: number;
  crosshairColor: string;
  crosshairSize: number;
  crosshairGap: number;
  crosshairThickness: number;
  crosshairDot: boolean;
  volume: number;
  flashIntensity: number;
  reducedEffects: boolean;
  highContrast: boolean;
  showFps: boolean;
  showHitNumbers: boolean;
  invertY: boolean;
}

export interface Vec3 { x: number; y: number; z: number; }

export interface TargetState {
  id: string;
  position: Vec3;
  radius: number;
  velocity: Vec3;
  alive: boolean;
  spawnTime: number;
  pattern: MovementPattern;
  patternPhase: number;
  patternOrigin: Vec3;
  patternRange: number;
  patternSpeed: number;
}

export type PageId =
  | 'home' | 'scenarios' | 'plans' | 'stats' | 'settings';
