// =====================================================================
// settings.ts — Persistent settings via localStorage
// =====================================================================

import { LS_SETTINGS } from './constants';
import type { Settings } from './types';

const DEFAULTS: Settings = {
  sensitivity:        0.12,
  fov:                103,
  crosshairColor:     '#00ff78',
  crosshairSize:      9,
  crosshairGap:       5,
  crosshairThickness: 2,
  crosshairDot:       false,
  volume:             0.6,
  flashIntensity:     0.85,
  reducedEffects:     false,
  highContrast:       false,
  showFps:            true,
  showHitNumbers:     true,
  invertY:            false,
};

export class SettingsManager {
  private data: Settings;

  constructor() {
    this.data = this.load();
  }

  private load(): Settings {
    try {
      const raw = localStorage.getItem(LS_SETTINGS);
      if (raw) {
        const parsed = JSON.parse(raw) as Partial<Settings>;
        return { ...DEFAULTS, ...parsed };
      }
    } catch { /* ignore */ }
    return { ...DEFAULTS };
  }

  get<K extends keyof Settings>(key: K): Settings[K] {
    return this.data[key];
  }

  set<K extends keyof Settings>(key: K, value: Settings[K]): void {
    this.data[key] = value;
    this.save();
  }

  getAll(): Readonly<Settings> {
    return { ...this.data };
  }

  reset(): void {
    this.data = { ...DEFAULTS };
    this.save();
  }

  private save(): void {
    try {
      localStorage.setItem(LS_SETTINGS, JSON.stringify(this.data));
    } catch { /* quota exceeded — ignore */ }
  }
}
