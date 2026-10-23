// =====================================================================
// store.ts — Session history and personal bests (localStorage)
// =====================================================================

import { LS_SESSIONS, LS_PERSONAL_BESTS } from './constants';
import type { SessionResult, PersonalBest } from './types';

const MAX_SESSIONS = 500;

export class Store {
  private sessions: SessionResult[];
  private pbs: Record<string, PersonalBest>;

  constructor() {
    this.sessions = this.loadSessions();
    this.pbs = this.loadPBs();
  }

  // ── Sessions ──────────────────────────────────────────────────────
  addSession(result: SessionResult): { isPB: boolean } {
    this.sessions.unshift(result);
    if (this.sessions.length > MAX_SESSIONS) {
      this.sessions = this.sessions.slice(0, MAX_SESSIONS);
    }
    this.saveSessions();
    const isPB = this.updatePB(result);
    return { isPB };
  }

  getSessions(scenarioId?: string, limit = 20): SessionResult[] {
    let s = this.sessions;
    if (scenarioId) s = s.filter(x => x.scenarioId === scenarioId);
    return s.slice(0, limit);
  }

  getRecentSessions(limit = 10): SessionResult[] {
    return this.sessions.slice(0, limit);
  }

  // ── Personal bests ─────────────────────────────────────────────────
  getPB(scenarioId: string): PersonalBest | null {
    return this.pbs[scenarioId] ?? null;
  }

  getAllPBs(): Record<string, PersonalBest> {
    return { ...this.pbs };
  }

  // ── Aggregate stats ─────────────────────────────────────────────────
  totalTimePlayed(): number {
    return this.sessions.reduce((s, r) => s + r.durationSec, 0);
  }

  overallAccuracy(): number {
    const total = this.sessions.reduce((s, r) => s + r.hits + r.misses, 0);
    const hits  = this.sessions.reduce((s, r) => s + r.hits, 0);
    return total > 0 ? (hits / total) * 100 : 0;
  }

  totalSessions(): number { return this.sessions.length; }

  categoryBreakdown(): Record<string, number> {
    const map: Record<string, number> = {};
    for (const s of this.sessions) {
      map[s.category] = (map[s.category] ?? 0) + 1;
    }
    return map;
  }

  // ── Private helpers ─────────────────────────────────────────────────
  private updatePB(result: SessionResult): boolean {
    const prev = this.pbs[result.scenarioId];
    if (!prev || result.score > prev.score) {
      this.pbs[result.scenarioId] = {
        scenarioId:   result.scenarioId,
        score:        result.score,
        accuracy:     result.accuracy,
        avgReactionMs:result.avgReactionMs,
        timestamp:    result.timestamp,
      };
      this.savePBs();
      return true;
    }
    return false;
  }

  private loadSessions(): SessionResult[] {
    try {
      const raw = localStorage.getItem(LS_SESSIONS);
      return raw ? (JSON.parse(raw) as SessionResult[]) : [];
    } catch { return []; }
  }

  private saveSessions(): void {
    try { localStorage.setItem(LS_SESSIONS, JSON.stringify(this.sessions)); } catch {}
  }

  private loadPBs(): Record<string, PersonalBest> {
    try {
      const raw = localStorage.getItem(LS_PERSONAL_BESTS);
      return raw ? (JSON.parse(raw) as Record<string, PersonalBest>) : {};
    } catch { return {}; }
  }

  private savePBs(): void {
    try { localStorage.setItem(LS_PERSONAL_BESTS, JSON.stringify(this.pbs)); } catch {}
  }
}
