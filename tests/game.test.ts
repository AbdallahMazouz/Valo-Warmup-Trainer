// =====================================================================
// tests/game.test.ts — Unit Tests for Scenarios, Settings & Store
// =====================================================================

import { describe, it, expect, beforeEach } from 'vitest';
import { SCENARIOS, getScenarioById, getScenariosByCategory, TRAINING_ROUTINES } from '../src/scenarios';
import { SettingsManager } from '../src/settings';
import { Store } from '../src/store';
import type { SessionResult } from '../src/types';

describe('Scenario Definitions', () => {
  it('should have comprehensive scenarios across all required categories', () => {
    expect(SCENARIOS.length).toBeGreaterThanOrEqual(15);

    const categories = new Set(SCENARIOS.map(s => s.category));
    expect(categories.has('flick')).toBe(true);
    expect(categories.has('tracking')).toBe(true);
    expect(categories.has('tactical')).toBe(true);
    expect(categories.has('flash')).toBe(true);
    expect(categories.has('reaction')).toBe(true);
    expect(categories.has('hybrid')).toBe(true);
  });

  it('should retrieve scenario by ID', () => {
    const s = getScenarioById('flick-static');
    expect(s).toBeDefined();
    expect(s?.name).toBe('Static Flicks');
    expect(s?.category).toBe('flick');
    expect(s?.durationSec).toBe(60);
  });

  it('should filter scenarios by category', () => {
    const tactical = getScenariosByCategory('tactical');
    expect(tactical.length).toBeGreaterThanOrEqual(4);
    for (const sc of tactical) {
      expect(sc.category).toBe('tactical');
    }
  });

  it('should contain curated training routines', () => {
    expect(TRAINING_ROUTINES.length).toBe(3);
    const routine5 = TRAINING_ROUTINES.find(r => r.id === 'routine-5m');
    expect(routine5).toBeDefined();
    expect(routine5?.scenarioIds.length).toBeGreaterThan(0);
  });
});

describe('Settings Manager', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should load default settings', () => {
    const sm = new SettingsManager();
    expect(sm.get('sensitivity')).toBe(0.12);
    expect(sm.get('fov')).toBe(103);
    expect(sm.get('crosshairColor')).toBe('#00ff78');
  });

  it('should update and persist settings', () => {
    const sm = new SettingsManager();
    sm.set('sensitivity', 0.25);
    sm.set('fov', 110);

    const sm2 = new SettingsManager();
    expect(sm2.get('sensitivity')).toBe(0.25);
    expect(sm2.get('fov')).toBe(110);
  });

  it('should reset to defaults', () => {
    const sm = new SettingsManager();
    sm.set('sensitivity', 0.88);
    sm.reset();
    expect(sm.get('sensitivity')).toBe(0.12);
  });
});

describe('Store & Statistics', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  const makeDummySession = (score: number, acc = 90): SessionResult => ({
    id: `session_${Math.random()}`,
    scenarioId: 'flick-static',
    scenarioName: 'Static Flicks',
    category: 'flick',
    difficulty: 'intermediate',
    timestamp: Date.now(),
    durationSec: 60,
    score,
    hits: 50,
    misses: 5,
    headshots: 20,
    accuracy: acc,
    avgReactionMs: 220,
    medianReactionMs: 210,
    bestReactionMs: 160,
    targetsPerSecond: 0.83,
  });

  it('should record sessions and recognize personal bests', () => {
    const store = new Store();
    const r1 = store.addSession(makeDummySession(1000));
    expect(r1.isPB).toBe(true);

    const pb1 = store.getPB('flick-static');
    expect(pb1?.score).toBe(1000);

    // Higher score -> new PB
    const r2 = store.addSession(makeDummySession(1500));
    expect(r2.isPB).toBe(true);
    expect(store.getPB('flick-static')?.score).toBe(1500);

    // Lower score -> not PB
    const r3 = store.addSession(makeDummySession(1200));
    expect(r3.isPB).toBe(false);
    expect(store.getPB('flick-static')?.score).toBe(1500);
  });

  it('should calculate aggregate statistics accurately', () => {
    const store = new Store();
    store.addSession(makeDummySession(1000, 80));
    store.addSession(makeDummySession(1200, 90));

    expect(store.totalSessions()).toBe(2);
    expect(store.totalTimePlayed()).toBe(120);
    // Total hits = 100, misses = 10 -> acc = 100 / 110 * 100 = 90.9%
    expect(store.overallAccuracy()).toBeCloseTo(90.9, 1);
  });
});
