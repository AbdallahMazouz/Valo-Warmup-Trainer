// =====================================================================
// ui.ts — Professional Esports UI, HUD, Routing & Pages
// =====================================================================

import type { Engine, EngineHUDState } from './engine';
import { SCENARIOS, TRAINING_ROUTINES, getScenarioById } from './scenarios';
import type { PageId, SessionResult, Settings } from './types';

export class UIManager {
  private engine: Engine;
  private appContainer: HTMLElement;
  private canvas: HTMLCanvasElement;

  private currentPage: PageId = 'home';
  private selectedCategory = 'all';

  // HUD elements
  private hudEl!: HTMLElement;
  private timerEl!: HTMLElement;
  private scoreEl!: HTMLElement;
  private accEl!: HTMLElement;
  private fpsEl!: HTMLElement;
  private flashOverlay!: HTMLElement;
  private hitMarkerEl!: HTMLElement;
  private lockOverlay!: HTMLElement;
  private resultOverlay!: HTMLElement;
  private movementWarningEl!: HTMLElement;

  // Active playlist queue for training plans
  private currentRoutine: string[] = [];
  private routineIndex = 0;

  constructor(engine: Engine, appContainer: HTMLElement, canvas: HTMLCanvasElement) {
    this.engine = engine;
    this.appContainer = appContainer;
    this.canvas = canvas;

    this.buildBaseDOM();
    this.bindEngineCallbacks();
    this.bindControls();
    this.applyCrosshairStyles(this.engine.settings.getAll());
    this.renderPage('home');
  }

  private buildBaseDOM(): void {
    this.appContainer.innerHTML = `
      <nav class="nav">
        <a href="#" class="nav-logo" data-page="home">VALO <span>WARMUP</span></a>
        <div class="nav-link active" data-page="home">Home</div>
        <div class="nav-link" data-page="scenarios">Scenarios</div>
        <div class="nav-link" data-page="plans">Warm-Up Plans</div>
        <div class="nav-link" data-page="stats">Statistics</div>
        <div class="nav-link" data-page="settings">Settings</div>
        <div class="nav-spacer"></div>
        <button class="btn btn-primary btn-sm" id="btn-quick-play">START TRAINING</button>
      </nav>

      <main class="page active" id="page-container"></main>

      <!-- In-Game HUD -->
      <div id="hud">
        <div class="hud-top">
          <div class="hud-timer" id="hud-timer">60</div>
          <div class="hud-score-box">
            <div class="hud-score" id="hud-score">0</div>
            <div class="hud-score-label">SCORE</div>
          </div>
          <div>
            <div class="hud-acc" id="hud-acc">100%</div>
            <div class="hud-acc-label">ACCURACY</div>
          </div>
        </div>

        <div id="hud-movement-warning" style="display:none; position:fixed; top:20%; left:50%; transform:translateX(-50%); background:rgba(255,70,85,0.9); color:#fff; font-family:var(--font-game); font-weight:700; padding:8px 24px; border-radius:4px; letter-spacing:0.1em; z-index:20; box-shadow:0 0 20px rgba(255,70,85,0.8);">
          STOP MOVING TO SHOOT! (COUNTER-STRAFE)
        </div>

        <div class="crosshair" id="crosshair">
          <div class="crosshair-line ch-h ch-left"></div>
          <div class="crosshair-line ch-h ch-right"></div>
          <div class="crosshair-line ch-v ch-top"></div>
          <div class="crosshair-line ch-v ch-bottom"></div>
          <div class="ch-dot" id="ch-dot" style="display:none; position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); border-radius:50%;"></div>
        </div>

        <div id="hud-fps" style="position:fixed; bottom:12px; right:16px; font-size:12px; color:var(--text-dim); font-family:monospace; pointer-events:none;">FPS: 60</div>
        <div style="position:fixed; bottom:12px; left:16px; font-size:13px; color:var(--text-dim); pointer-events:none;">ESC — Pause / Return to Menu</div>
      </div>

      <!-- Hit Marker -->
      <div id="hit-marker">
        <svg viewBox="0 0 32 32" fill="none" stroke="#00ff88" stroke-width="2.5">
          <line x1="6" y1="6" x2="11" y2="11" />
          <line x1="26" y1="6" x2="21" y2="11" />
          <line x1="6" y1="26" x2="11" y2="21" />
          <line x1="26" y1="26" x2="21" y2="21" />
        </svg>
      </div>

      <!-- Flash Overlay -->
      <div id="flash-overlay"></div>

      <!-- Pointer Lock Overlay -->
      <div id="lock-overlay">
        <h2>CLICK TO ENTER ARENA</h2>
        <p>Your mouse will be locked for precision 3D aim training.<br>Press <strong>ESC</strong> at any time to exit or pause.</p>
        <button class="btn btn-primary btn-lg" id="btn-lock-confirm">RESUME TRAINING</button>
      </div>

      <!-- Results Overlay -->
      <div id="result-overlay">
        <div id="result-modal-content" style="max-width:680px; width:90%; background:var(--panel); border:1px solid var(--border-2); border-radius:var(--r-xl); padding:36px; box-shadow:0 12px 48px rgba(0,0,0,0.6); text-align:center;">
          <!-- Dynamically populated -->
        </div>
      </div>

      <!-- Toast container -->
      <div id="toast-container"></div>
    `;

    // Cache elements
    this.hudEl = document.getElementById('hud')!;
    this.timerEl = document.getElementById('hud-timer')!;
    this.scoreEl = document.getElementById('hud-score')!;
    this.accEl = document.getElementById('hud-acc')!;
    this.fpsEl = document.getElementById('hud-fps')!;
    this.flashOverlay = document.getElementById('flash-overlay')!;
    this.hitMarkerEl = document.getElementById('hit-marker')!;
    this.lockOverlay = document.getElementById('lock-overlay')!;
    this.resultOverlay = document.getElementById('result-overlay')!;
    this.movementWarningEl = document.getElementById('hud-movement-warning')!;
  }

  private bindControls(): void {
    // Navigation links
    this.appContainer.querySelectorAll('.nav-link, .nav-logo').forEach(el => {
      el.addEventListener('click', e => {
        e.preventDefault();
        const page = (el as HTMLElement).dataset.page as PageId;
        if (page) this.navigateTo(page);
      });
    });

    // Quick play header button
    document.getElementById('btn-quick-play')?.addEventListener('click', () => {
      this.launchScenario('flick-static');
    });

    // Resume click on pointer lock overlay
    document.getElementById('btn-lock-confirm')?.addEventListener('click', () => {
      this.engine.controls.lock();
    });

    this.lockOverlay.addEventListener('click', () => {
      this.engine.controls.lock();
    });

    // Listen to pointer lock state changes
    this.engine.controls.onLockChange = (locked: boolean) => {
      if (this.engine.isRunning) {
        if (!locked) {
          this.lockOverlay.classList.add('visible');
        } else {
          this.lockOverlay.classList.remove('visible');
        }
      }
    };

    // ESC key to stop session if pointer lock unlocked
    window.addEventListener('keydown', e => {
      if (e.code === 'Escape' && this.engine.isRunning) {
        if (this.lockOverlay.classList.contains('visible')) {
          this.exitToMenu();
        }
      }
    });

    // Window resize
    window.addEventListener('resize', () => {
      this.engine.renderer.resize(window.innerWidth, window.innerHeight);
    });
  }

  private bindEngineCallbacks(): void {
    this.engine.callbacks.onTick = (hud: EngineHUDState) => {
      const remainingSec = Math.ceil(hud.timeRemaining);
      this.timerEl.textContent = `${remainingSec}s`;

      if (remainingSec <= 5) {
        this.timerEl.className = 'hud-timer danger';
      } else if (remainingSec <= 15) {
        this.timerEl.className = 'hud-timer warning';
      } else {
        this.timerEl.className = 'hud-timer';
      }

      this.scoreEl.textContent = hud.score.toLocaleString();
      this.accEl.textContent = `${Math.round(hud.accuracy)}%`;
      this.fpsEl.textContent = `FPS: ${hud.fps}`;
    };

    this.engine.callbacks.onHit = () => {
      this.hitMarkerEl.classList.remove('show');
      void this.hitMarkerEl.offsetWidth; // trigger reflow
      this.hitMarkerEl.classList.add('show');
    };

    this.engine.callbacks.onMovementInaccurate = () => {
      this.movementWarningEl.style.display = 'block';
      setTimeout(() => {
        this.movementWarningEl.style.display = 'none';
      }, 700);
    };

    this.engine.callbacks.onFlash = (intensity: number, durationMs: number) => {
      this.flashOverlay.style.opacity = `${intensity}`;
      setTimeout(() => {
        this.flashOverlay.style.transition = `opacity ${durationMs}ms ease-out`;
        this.flashOverlay.style.opacity = '0';
        setTimeout(() => {
          this.flashOverlay.style.transition = 'opacity 80ms linear';
        }, durationMs);
      }, 120);
    };

    this.engine.callbacks.onScenarioComplete = (result: SessionResult, isPB: boolean) => {
      this.showResultsScreen(result, isPB);
    };
  }

  navigateTo(page: PageId): void {
    this.currentPage = page;

    // Update nav active classes
    this.appContainer.querySelectorAll('.nav-link').forEach(link => {
      const p = (link as HTMLElement).dataset.page;
      link.classList.toggle('active', p === page);
    });

    this.renderPage(page);
  }

  private renderPage(page: PageId): void {
    const container = document.getElementById('page-container')!;
    container.innerHTML = '';

    switch (page) {
      case 'home':
        container.innerHTML = this.renderHomeHTML();
        this.attachHomeListeners(container);
        break;
      case 'scenarios':
        container.innerHTML = this.renderScenariosHTML();
        this.attachScenariosListeners(container);
        break;
      case 'plans':
        container.innerHTML = this.renderPlansHTML();
        this.attachPlansListeners(container);
        break;
      case 'stats':
        container.innerHTML = this.renderStatsHTML();
        break;
      case 'settings':
        container.innerHTML = this.renderSettingsHTML();
        this.attachSettingsListeners(container);
        break;
    }
  }

  // ── Pages HTML Generators ───────────────────────────────────────────

  private renderHomeHTML(): string {
    const pbs = this.engine.store.getAllPBs();
    const pbEntries = Object.values(pbs);
    const recent = this.engine.store.getRecentSessions(4);

    return `
      <div class="page-inner">
        <section class="hero">
          <div class="badge badge-red font-game">VALORANT-SPECIFIC AIM TRAINER</div>
          <h1 class="hero-title">ELEVATE YOUR <span class="accent">CROSSHAIR</span> MASTERY</h1>
          <p class="hero-sub">
            Warm up your flicks, micro-adjustments, strafe tracking, and counter-strafing in a dedicated 3D arena built for tactical shooter mechanics.
          </p>
          <div class="hero-actions">
            <button class="btn btn-primary btn-lg" id="btn-hero-play">START QUICK WARM-UP</button>
            <button class="btn btn-secondary btn-lg" id="btn-hero-browse">BROWSE SCENARIOS</button>
          </div>
        </section>

        <!-- Quick Warm-Up Routines Grid -->
        <div class="section-header mt-32">
          <h2>RECOMMENDED WARM-UP ROUTINES</h2>
          <span class="section-sub">Curated routines designed for quick match readiness</span>
        </div>
        <div class="grid-3">
          ${TRAINING_ROUTINES.map(r => `
            <div class="card scenario-card" data-routine="${r.id}">
              <div class="badge badge-teal">${r.durationLabel}</div>
              <div class="scenario-card-title mt-8">${r.name}</div>
              <p class="scenario-card-desc">${r.description}</p>
              <button class="btn btn-primary btn-sm w-full mt-8">START ROUTINE</button>
            </div>
          `).join('')}
        </div>

        <!-- Personal Bests & Recent Activity -->
        <div class="grid-2 mt-32">
          <div class="card">
            <div class="section-header" style="margin-bottom:12px;">
              <h3>TOP PERSONAL BESTS</h3>
            </div>
            ${pbEntries.length === 0 ? `
              <p class="text-dim text-sm">No personal bests recorded yet. Complete a training scenario to see your scores!</p>
            ` : `
              <div style="display:flex; flex-direction:column; gap:10px;">
                ${pbEntries.slice(0, 5).map(pb => {
                  const scen = getScenarioById(pb.scenarioId);
                  return `
                    <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid var(--border);">
                      <div>
                        <div style="font-weight:600; font-size:0.95rem;">${scen?.name ?? pb.scenarioId}</div>
                        <div class="text-dim text-sm">${pb.accuracy.toFixed(0)}% acc &bull; ${pb.avgReactionMs}ms reaction</div>
                      </div>
                      <div class="font-game font-bold text-gold" style="font-size:1.4rem;">${pb.score.toLocaleString()}</div>
                    </div>
                  `;
                }).join('')}
              </div>
            `}
          </div>

          <div class="card">
            <div class="section-header" style="margin-bottom:12px;">
              <h3>RECENT SESSIONS</h3>
            </div>
            ${recent.length === 0 ? `
              <p class="text-dim text-sm">No recent sessions yet. Jump into an arena drill!</p>
            ` : `
              <div style="display:flex; flex-direction:column; gap:10px;">
                ${recent.map(s => `
                  <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid var(--border);">
                    <div>
                      <div style="font-weight:600; font-size:0.95rem;">${s.scenarioName}</div>
                      <div class="text-dim text-sm">${s.accuracy.toFixed(0)}% accuracy &bull; ${s.hits} hits</div>
                    </div>
                    <div class="font-game font-bold text-teal" style="font-size:1.3rem;">${s.score.toLocaleString()}</div>
                  </div>
                `).join('')}
              </div>
            `}
          </div>
        </div>
      </div>
    `;
  }

  private attachHomeListeners(container: HTMLElement): void {
    container.querySelector('#btn-hero-play')?.addEventListener('click', () => {
      this.launchScenario('flick-static');
    });

    container.querySelector('#btn-hero-browse')?.addEventListener('click', () => {
      this.navigateTo('scenarios');
    });

    container.querySelectorAll('[data-routine]').forEach(el => {
      el.addEventListener('click', () => {
        const rId = (el as HTMLElement).dataset.routine;
        const routine = TRAINING_ROUTINES.find(r => r.id === rId);
        if (routine) {
          this.startRoutine(routine);
        }
      });
    });
  }

  private renderScenariosHTML(): string {
    const categories = [
      { id: 'all', label: 'All Categories' },
      { id: 'flick', label: 'Flicks' },
      { id: 'tracking', label: 'Tracking' },
      { id: 'tactical', label: 'Valorant Tactical' },
      { id: 'flash', label: 'Flash Recovery' },
      { id: 'reaction', label: 'Reaction Time' },
      { id: 'hybrid', label: 'Hybrid' },
    ];

    const filtered = this.selectedCategory === 'all'
      ? SCENARIOS
      : SCENARIOS.filter(s => s.category === this.selectedCategory);

    return `
      <div class="page-inner">
        <div class="section-header">
          <h2>TRAINING SCENARIOS</h2>
          <span class="section-sub">Choose a specialized exercise targeting your aim weaknesses</span>
        </div>

        <!-- Filter pills -->
        <div style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:24px;">
          ${categories.map(c => `
            <button class="btn btn-sm ${this.selectedCategory === c.id ? 'btn-primary' : 'btn-secondary'}" data-cat="${c.id}">
              ${c.label}
            </button>
          `).join('')}
        </div>

        <!-- Grid of scenarios -->
        <div class="scenario-grid">
          ${filtered.map(s => {
            const pb = this.engine.store.getPB(s.id);
            return `
              <div class="card scenario-card" data-scen="${s.id}">
                <div class="scenario-card-meta">
                  <span class="badge badge-red">${s.category}</span>
                  <span class="badge badge-teal">${s.difficulty}</span>
                  <span class="badge badge-gold">${s.durationSec}s</span>
                </div>
                <div class="scenario-card-title">${s.name}</div>
                <p class="scenario-card-desc">${s.description}</p>
                <div class="text-dim text-sm mb-8"><strong>Skill:</strong> ${s.skill}</div>
                <div class="scenario-card-pb">
                  <span class="pb-label">Personal Best</span>
                  <span class="pb-value">${pb ? pb.score.toLocaleString() : '—'}</span>
                </div>
                <button class="btn btn-primary btn-sm w-full mt-16">PLAY SCENARIO</button>
              </div>
            `;
          }).join('')}
        </div>
      </div>
    `;
  }

  private attachScenariosListeners(container: HTMLElement): void {
    container.querySelectorAll('[data-cat]').forEach(btn => {
      btn.addEventListener('click', () => {
        this.selectedCategory = (btn as HTMLElement).dataset.cat ?? 'all';
        this.renderPage('scenarios');
      });
    });

    container.querySelectorAll('[data-scen]').forEach(card => {
      card.addEventListener('click', () => {
        const scenId = (card as HTMLElement).dataset.scen;
        if (scenId) this.launchScenario(scenId);
      });
    });
  }

  private renderPlansHTML(): string {
    return `
      <div class="page-inner">
        <div class="section-header">
          <h2>STRUCTURED WARM-UP ROUTINES</h2>
          <span class="section-sub">Play through sequential scenario playlists with automatic transitions</span>
        </div>

        <div style="display:flex; flex-direction:column; gap:20px;">
          ${TRAINING_ROUTINES.map(r => `
            <div class="card" style="display:flex; justify-content:space-between; align-items:center; gap:24px; flex-wrap:wrap;">
              <div style="flex:1; min-width:280px;">
                <div class="badge badge-teal font-game mb-8">${r.durationLabel} ROUTINE</div>
                <h3>${r.name}</h3>
                <p class="text-dim text-sm mt-8">${r.description}</p>
                <div style="display:flex; gap:6px; flex-wrap:wrap; margin-top:12px;">
                  ${r.scenarioIds.map(sid => {
                    const sc = getScenarioById(sid);
                    return `<span class="badge badge-gold">${sc?.name ?? sid}</span>`;
                  }).join('')}
                </div>
              </div>
              <div>
                <button class="btn btn-primary btn-lg" data-plan-id="${r.id}">START ROUTINE</button>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  private attachPlansListeners(container: HTMLElement): void {
    container.querySelectorAll('[data-plan-id]').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = (btn as HTMLElement).dataset.planId;
        const routine = TRAINING_ROUTINES.find(r => r.id === id);
        if (routine) this.startRoutine(routine);
      });
    });
  }

  private renderStatsHTML(): string {
    const totalSessions = this.engine.store.totalSessions();
    const totalTimeMin = Math.round(this.engine.store.totalTimePlayed() / 60);
    const overallAcc = this.engine.store.overallAccuracy();
    const pbs = this.engine.store.getAllPBs();
    const pbList = Object.values(pbs);
    const sessions = this.engine.store.getRecentSessions(20);

    return `
      <div class="page-inner">
        <div class="section-header">
          <h2>TRAINING STATISTICS</h2>
          <span class="section-sub">Track your aim consistency, speed, and long-term improvement</span>
        </div>

        <!-- Metric Cards -->
        <div class="grid-4 mb-32">
          <div class="card stats-summary-card">
            <div class="stat-value text-red">${totalSessions}</div>
            <div class="stat-label">Total Sessions</div>
          </div>
          <div class="card stats-summary-card">
            <div class="stat-value text-teal">${totalTimeMin} min</div>
            <div class="stat-label">Time Played</div>
          </div>
          <div class="card stats-summary-card">
            <div class="stat-value text-gold">${overallAcc.toFixed(1)}%</div>
            <div class="stat-label">Overall Accuracy</div>
          </div>
          <div class="card stats-summary-card">
            <div class="stat-value text-green">${pbList.length}</div>
            <div class="stat-label">Personal Bests Set</div>
          </div>
        </div>

        <!-- All Personal Bests Table -->
        <div class="card mb-32">
          <h3 class="mb-16">ALL PERSONAL BESTS</h3>
          ${pbList.length === 0 ? `
            <p class="text-dim text-sm">No personal bests yet.</p>
          ` : `
            <div style="overflow-x:auto;">
              <table style="width:100%; border-collapse:collapse; text-align:left; font-size:0.9rem;">
                <thead>
                  <tr style="border-bottom:1px solid var(--border-2); color:var(--text-dim); text-transform:uppercase; font-size:0.75rem; letter-spacing:0.08em;">
                    <th style="padding:10px;">Scenario</th>
                    <th style="padding:10px;">Score</th>
                    <th style="padding:10px;">Accuracy</th>
                    <th style="padding:10px;">Avg Reaction</th>
                    <th style="padding:10px;">Date</th>
                  </tr>
                </thead>
                <tbody>
                  ${pbList.map(pb => {
                    const sc = getScenarioById(pb.scenarioId);
                    return `
                      <tr style="border-bottom:1px solid var(--border);">
                        <td style="padding:12px 10px; font-weight:600;">${sc?.name ?? pb.scenarioId}</td>
                        <td style="padding:12px 10px; font-weight:700; color:var(--gold); font-family:var(--font-game); font-size:1.15rem;">${pb.score.toLocaleString()}</td>
                        <td style="padding:12px 10px; color:var(--teal); font-weight:600;">${pb.accuracy.toFixed(1)}%</td>
                        <td style="padding:12px 10px;">${pb.avgReactionMs} ms</td>
                        <td style="padding:12px 10px; color:var(--text-dim); font-size:0.8rem;">${new Date(pb.timestamp).toLocaleDateString()}</td>
                      </tr>
                    `;
                  }).join('')}
                </tbody>
              </table>
            </div>
          `}
        </div>

        <!-- Recent Session History -->
        <div class="card">
          <h3 class="mb-16">SESSION HISTORY</h3>
          ${sessions.length === 0 ? `
            <p class="text-dim text-sm">No session logs available.</p>
          ` : `
            <div style="overflow-x:auto;">
              <table style="width:100%; border-collapse:collapse; text-align:left; font-size:0.9rem;">
                <thead>
                  <tr style="border-bottom:1px solid var(--border-2); color:var(--text-dim); text-transform:uppercase; font-size:0.75rem; letter-spacing:0.08em;">
                    <th style="padding:10px;">Scenario</th>
                    <th style="padding:10px;">Score</th>
                    <th style="padding:10px;">Hits / Misses</th>
                    <th style="padding:10px;">Accuracy</th>
                    <th style="padding:10px;">Avg Reaction</th>
                    <th style="padding:10px;">Headshots</th>
                  </tr>
                </thead>
                <tbody>
                  ${sessions.map(s => `
                    <tr style="border-bottom:1px solid var(--border);">
                      <td style="padding:12px 10px; font-weight:600;">${s.scenarioName}</td>
                      <td style="padding:12px 10px; font-weight:700; color:var(--text); font-family:var(--font-game); font-size:1.1rem;">${s.score.toLocaleString()}</td>
                      <td style="padding:12px 10px;"><span class="text-green">${s.hits}</span> / <span class="text-red">${s.misses}</span></td>
                      <td style="padding:12px 10px; color:var(--teal); font-weight:600;">${s.accuracy.toFixed(1)}%</td>
                      <td style="padding:12px 10px;">${s.avgReactionMs} ms</td>
                      <td style="padding:12px 10px; color:var(--gold);">${s.headshots}</td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          `}
        </div>
      </div>
    `;
  }

  private renderSettingsHTML(): string {
    const s = this.engine.settings.getAll();

    return `
      <div class="page-inner" style="max-width:960px;">
        <div class="section-header">
          <h2>SETTINGS & CALIBRATION</h2>
          <span class="section-sub">Configure mouse look, field of view, audio, and visual ergonomics</span>
        </div>

        <!-- Mouse Settings -->
        <div class="card settings-section">
          <div class="settings-section-title">MOUSE & SENSITIVITY</div>

          <div class="settings-row">
            <div class="settings-row-info">
              <div class="settings-row-label">Sensitivity</div>
              <div class="settings-row-desc">Calibrated for Valorant (e.g. 0.35 at 800 DPI &approx; 0.12 scale)</div>
            </div>
            <div class="settings-row-control">
              <div class="range-row">
                <input type="range" id="set-sens" min="0.01" max="1.0" step="0.01" value="${s.sensitivity}">
                <span class="range-value" id="val-sens">${s.sensitivity.toFixed(2)}</span>
              </div>
            </div>
          </div>

          <div class="settings-row">
            <div class="settings-row-info">
              <div class="settings-row-label">Invert Y Axis</div>
              <div class="settings-row-desc">Reverse vertical pitch aiming direction</div>
            </div>
            <div class="settings-row-control">
              <label class="toggle">
                <input type="checkbox" id="set-invert-y" ${s.invertY ? 'checked' : ''}>
                <span class="toggle-slider"></span>
              </label>
            </div>
          </div>
        </div>

        <!-- Visuals & FOV -->
        <div class="card settings-section">
          <div class="settings-section-title">FIELD OF VIEW & VISUALS</div>

          <div class="settings-row">
            <div class="settings-row-info">
              <div class="settings-row-label">Field of View (Horizontal)</div>
              <div class="settings-row-desc">Valorant standard is 103&deg; horizontal FOV</div>
            </div>
            <div class="settings-row-control">
              <div class="range-row">
                <input type="range" id="set-fov" min="70" max="120" step="1" value="${s.fov}">
                <span class="range-value" id="val-fov">${s.fov}&deg;</span>
              </div>
            </div>
          </div>

          <div class="settings-row">
            <div class="settings-row-info">
              <div class="settings-row-label">Flash Intensity</div>
              <div class="settings-row-desc">Controls max brightness and whiteout during flash training</div>
            </div>
            <div class="settings-row-control">
              <div class="range-row">
                <input type="range" id="set-flash" min="0.1" max="1.0" step="0.05" value="${s.flashIntensity}">
                <span class="range-value" id="val-flash">${Math.round(s.flashIntensity * 100)}%</span>
              </div>
            </div>
          </div>

          <div class="settings-row">
            <div class="settings-row-info">
              <div class="settings-row-label">Show Real-Time FPS</div>
              <div class="settings-row-desc">Display frame rate counter on HUD</div>
            </div>
            <div class="settings-row-control">
              <label class="toggle">
                <input type="checkbox" id="set-show-fps" ${s.showFps ? 'checked' : ''}>
                <span class="toggle-slider"></span>
              </label>
            </div>
          </div>
        </div>

        <!-- Crosshair Settings with Live Preview -->
        <div class="card settings-section">
          <div class="settings-section-title">CROSSHAIR ERGONOMICS</div>

          <div style="display:flex; gap:32px; align-items:flex-start; flex-wrap:wrap;">
            <div style="flex:1; min-width:280px;">
              <div class="settings-row">
                <div class="settings-row-info">
                  <div class="settings-row-label">Color Preset</div>
                </div>
                <div class="settings-row-control" style="display:flex; gap:6px;">
                  <button class="btn btn-sm btn-secondary ch-color-btn" data-color="#00ff78" style="color:#00ff78;">Green</button>
                  <button class="btn btn-sm btn-secondary ch-color-btn" data-color="#00ffff" style="color:#00ffff;">Cyan</button>
                  <button class="btn btn-sm btn-secondary ch-color-btn" data-color="#ffff00" style="color:#ffff00;">Yellow</button>
                  <button class="btn btn-sm btn-secondary ch-color-btn" data-color="#ffffff" style="color:#ffffff;">White</button>
                  <button class="btn btn-sm btn-secondary ch-color-btn" data-color="#ff4655" style="color:#ff4655;">Red</button>
                </div>
              </div>

              <div class="settings-row">
                <div class="settings-row-info">
                  <div class="settings-row-label">Crosshair Size (Length)</div>
                </div>
                <div class="settings-row-control">
                  <div class="range-row">
                    <input type="range" id="set-ch-size" min="3" max="24" step="1" value="${s.crosshairSize}">
                    <span class="range-value" id="val-ch-size">${s.crosshairSize}px</span>
                  </div>
                </div>
              </div>

              <div class="settings-row">
                <div class="settings-row-info">
                  <div class="settings-row-label">Inner Offset / Gap</div>
                </div>
                <div class="settings-row-control">
                  <div class="range-row">
                    <input type="range" id="set-ch-gap" min="1" max="16" step="1" value="${s.crosshairGap}">
                    <span class="range-value" id="val-ch-gap">${s.crosshairGap}px</span>
                  </div>
                </div>
              </div>

              <div class="settings-row">
                <div class="settings-row-info">
                  <div class="settings-row-label">Line Thickness</div>
                </div>
                <div class="settings-row-control">
                  <div class="range-row">
                    <input type="range" id="set-ch-thick" min="1" max="6" step="1" value="${s.crosshairThickness}">
                    <span class="range-value" id="val-ch-thick">${s.crosshairThickness}px</span>
                  </div>
                </div>
              </div>

              <div class="settings-row">
                <div class="settings-row-info">
                  <div class="settings-row-label">Center Dot</div>
                </div>
                <div class="settings-row-control">
                  <label class="toggle">
                    <input type="checkbox" id="set-ch-dot" ${s.crosshairDot ? 'checked' : ''}>
                    <span class="toggle-slider"></span>
                  </label>
                </div>
              </div>
            </div>

            <!-- Interactive Preview Box -->
            <div style="display:flex; flex-direction:column; align-items:center; gap:8px;">
              <div class="ch-preview-box" id="ch-preview">
                <div class="crosshair" id="ch-preview-inner">
                  <div class="crosshair-line ch-h ch-left"></div>
                  <div class="crosshair-line ch-h ch-right"></div>
                  <div class="crosshair-line ch-v ch-top"></div>
                  <div class="crosshair-line ch-v ch-bottom"></div>
                  <div class="ch-dot" id="ch-preview-dot" style="display:none; position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); border-radius:50%;"></div>
                </div>
              </div>
              <span class="text-dim text-sm">Live Preview</span>
            </div>
          </div>
        </div>

        <!-- Audio Settings -->
        <div class="card settings-section">
          <div class="settings-section-title">AUDIO & SOUND FX</div>

          <div class="settings-row">
            <div class="settings-row-info">
              <div class="settings-row-label">Master Volume</div>
              <div class="settings-row-desc">Hit pings, headshot sounds, flash detonations</div>
            </div>
            <div class="settings-row-control">
              <div class="range-row">
                <input type="range" id="set-vol" min="0" max="1.0" step="0.05" value="${s.volume}">
                <span class="range-value" id="val-vol">${Math.round(s.volume * 100)}%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Reset Button -->
        <div style="display:flex; justify-content:flex-end; gap:12px; margin-top:24px;">
          <button class="btn btn-secondary" id="btn-reset-settings">RESET TO DEFAULTS</button>
        </div>
      </div>
    `;
  }

  private attachSettingsListeners(container: HTMLElement): void {
    const bindRange = (
      sliderId: string,
      labelId: string,
      suffix: string,
      setter: (v: number) => void
    ) => {
      const slider = container.querySelector(`#${sliderId}`) as HTMLInputElement;
      const label = container.querySelector(`#${labelId}`);
      slider?.addEventListener('input', () => {
        const val = parseFloat(slider.value);
        if (label) label.textContent = `${val}${suffix}`;
        setter(val);
        this.engine.applySettings();
      });
    };

    bindRange('set-sens', 'val-sens', '', v => this.engine.settings.set('sensitivity', v));
    bindRange('set-fov', 'val-fov', '°', v => this.engine.settings.set('fov', v));
    bindRange('set-flash', 'val-flash', '%', v => this.engine.settings.set('flashIntensity', v));
    bindRange('set-vol', 'val-vol', '%', v => this.engine.settings.set('volume', v));

    // Crosshair sliders
    bindRange('set-ch-size', 'val-ch-size', 'px', v => {
      this.engine.settings.set('crosshairSize', v);
      this.applyCrosshairStyles(this.engine.settings.getAll());
    });
    bindRange('set-ch-gap', 'val-ch-gap', 'px', v => {
      this.engine.settings.set('crosshairGap', v);
      this.applyCrosshairStyles(this.engine.settings.getAll());
    });
    bindRange('set-ch-thick', 'val-ch-thick', 'px', v => {
      this.engine.settings.set('crosshairThickness', v);
      this.applyCrosshairStyles(this.engine.settings.getAll());
    });

    // Checkboxes
    container.querySelector('#set-invert-y')?.addEventListener('change', e => {
      this.engine.settings.set('invertY', (e.target as HTMLInputElement).checked);
      this.engine.applySettings();
    });

    container.querySelector('#set-show-fps')?.addEventListener('change', e => {
      const checked = (e.target as HTMLInputElement).checked;
      this.engine.settings.set('showFps', checked);
      this.fpsEl.style.display = checked ? 'block' : 'none';
    });

    container.querySelector('#set-ch-dot')?.addEventListener('change', e => {
      const checked = (e.target as HTMLInputElement).checked;
      this.engine.settings.set('crosshairDot', checked);
      this.applyCrosshairStyles(this.engine.settings.getAll());
    });

    // Color buttons
    container.querySelectorAll('.ch-color-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const color = (btn as HTMLElement).dataset.color;
        if (color) {
          this.engine.settings.set('crosshairColor', color);
          this.applyCrosshairStyles(this.engine.settings.getAll());
        }
      });
    });

    // Reset settings
    container.querySelector('#btn-reset-settings')?.addEventListener('click', () => {
      this.engine.settings.reset();
      this.engine.applySettings();
      this.applyCrosshairStyles(this.engine.settings.getAll());
      this.renderPage('settings');
      this.showToast('Settings restored to default presets.', 'info');
    });

    this.applyCrosshairStyles(this.engine.settings.getAll());
  }

  // ── Crosshair Styling ───────────────────────────────────────────────
  private applyCrosshairStyles(s: Settings): void {
    const root = document.documentElement;
    root.style.setProperty('--crosshair-color', s.crosshairColor);
    root.style.setProperty('--ch-size', `${s.crosshairSize}px`);
    root.style.setProperty('--ch-gap', `${s.crosshairGap}px`);
    root.style.setProperty('--ch-thick', `${s.crosshairThickness}px`);

    const dotEl = document.getElementById('ch-dot');
    if (dotEl) {
      dotEl.style.display = s.crosshairDot ? 'block' : 'none';
      dotEl.style.width = `${Math.max(2, s.crosshairThickness + 1)}px`;
      dotEl.style.height = `${Math.max(2, s.crosshairThickness + 1)}px`;
      dotEl.style.backgroundColor = s.crosshairColor;
    }

    const previewDot = document.getElementById('ch-preview-dot');
    if (previewDot) {
      previewDot.style.display = s.crosshairDot ? 'block' : 'none';
      previewDot.style.width = `${Math.max(2, s.crosshairThickness + 1)}px`;
      previewDot.style.height = `${Math.max(2, s.crosshairThickness + 1)}px`;
      previewDot.style.backgroundColor = s.crosshairColor;
    }
  }

  // ── Training Lifecycle & Overlays ───────────────────────────────────
  launchScenario(scenarioId: string): void {
    const config = getScenarioById(scenarioId);
    if (!config) return;

    // Show canvas & HUD
    this.canvas.classList.add('visible');
    this.hudEl.classList.add('visible');
    this.resultOverlay.classList.remove('visible');

    // Hide UI page
    document.getElementById('page-container')!.style.display = 'none';

    // Start engine
    this.engine.audio.init();
    this.engine.startScenario(config);

    // Request pointer lock
    this.engine.controls.lock();
  }

  startRoutine(routine: { id: string; name: string; scenarioIds: string[] }): void {
    this.currentRoutine = [...routine.scenarioIds];
    this.routineIndex = 0;
    if (this.currentRoutine.length > 0) {
      this.launchScenario(this.currentRoutine[0]);
    }
  }

  exitToMenu(): void {
    this.engine.stopScenario();
    this.engine.controls.unlock();
    this.canvas.classList.remove('visible');
    this.hudEl.classList.remove('visible');
    this.lockOverlay.classList.remove('visible');
    this.resultOverlay.classList.remove('visible');
    document.getElementById('page-container')!.style.display = 'block';
    this.renderPage(this.currentPage);
  }

  private showResultsScreen(result: SessionResult, isPB: boolean): void {
    this.engine.controls.unlock();
    this.lockOverlay.classList.remove('visible');

    const content = document.getElementById('result-modal-content')!;
    content.innerHTML = `
      ${isPB ? `
        <div style="background:rgba(245,197,24,0.15); border:1px solid var(--gold); border-radius:var(--r-md); padding:10px 20px; color:var(--gold); font-family:var(--font-game); font-weight:700; font-size:1.4rem; letter-spacing:0.06em; margin-bottom:20px; animation:pulse-gold 1s infinite alternate;">
          🏆 NEW PERSONAL BEST!
        </div>
      ` : ''}

      <div class="badge badge-teal font-game" style="font-size:0.9rem;">${result.category.toUpperCase()} &bull; ${result.difficulty.toUpperCase()}</div>
      <h2 style="font-size:2.4rem; margin:10px 0 24px;">${result.scenarioName}</h2>

      <div class="grid-3 mb-24">
        <div class="card" style="padding:16px;">
          <div class="stat-value text-gold" style="font-size:2.4rem;">${result.score.toLocaleString()}</div>
          <div class="stat-label">Final Score</div>
        </div>
        <div class="card" style="padding:16px;">
          <div class="stat-value text-teal" style="font-size:2.4rem;">${result.accuracy.toFixed(1)}%</div>
          <div class="stat-label">Accuracy</div>
        </div>
        <div class="card" style="padding:16px;">
          <div class="stat-value text-green" style="font-size:2.4rem;">${result.avgReactionMs} ms</div>
          <div class="stat-label">Avg Reaction</div>
        </div>
      </div>

      <div class="grid-4 mb-32" style="font-size:0.95rem;">
        <div><span class="text-dim">Hits:</span> <strong>${result.hits}</strong></div>
        <div><span class="text-dim">Misses:</span> <strong>${result.misses}</strong></div>
        <div><span class="text-dim">Headshots:</span> <strong>${result.headshots}</strong></div>
        <div><span class="text-dim">Kills/Sec:</span> <strong>${result.targetsPerSecond}</strong></div>
      </div>

      <div style="display:flex; justify-content:center; gap:16px; flex-wrap:wrap;">
        <button class="btn btn-primary btn-lg" id="btn-res-retry">PLAY AGAIN</button>
        ${this.currentRoutine.length > 0 && this.routineIndex < this.currentRoutine.length - 1 ? `
          <button class="btn btn-primary btn-lg" id="btn-res-next" style="background:var(--teal); border-color:var(--teal);">NEXT IN ROUTINE &rarr;</button>
        ` : ''}
        <button class="btn btn-secondary btn-lg" id="btn-res-menu">RETURN TO MENU</button>
      </div>
    `;

    this.resultOverlay.classList.add('visible');

    // Button actions
    content.querySelector('#btn-res-retry')?.addEventListener('click', () => {
      this.resultOverlay.classList.remove('visible');
      this.launchScenario(result.scenarioId);
    });

    content.querySelector('#btn-res-next')?.addEventListener('click', () => {
      this.routineIndex++;
      const nextId = this.currentRoutine[this.routineIndex];
      this.resultOverlay.classList.remove('visible');
      if (nextId) this.launchScenario(nextId);
    });

    content.querySelector('#btn-res-menu')?.addEventListener('click', () => {
      this.currentRoutine = [];
      this.exitToMenu();
    });
  }

  showToast(message: string, type: 'success' | 'info' | 'pb' = 'info'): void {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
      toast.remove();
    }, 3000);
  }
}
