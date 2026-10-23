"""
All game screens — Menu, Scenario Select, Game, Results, Settings, Profile.
"""
import pygame
import math
import time
from typing import Optional, Callable

from .constants import *
from .ui import *
from .scenarios import make_scenario, SCENARIO_CLASSES
from .stats import SessionResult, StatsManager
from .settings import Settings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


# ---------------------------------------------------------------------------
# Base Screen
# ---------------------------------------------------------------------------

class Screen:
    """All screens inherit from this."""

    def __init__(self, app) -> None:
        self.app = app

    def on_enter(self) -> None:
        """Called when this screen becomes active."""

    def on_exit(self) -> None:
        """Called when leaving this screen."""

    def handle_event(self, event: pygame.event.Event) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        pass

    # Helpers
    @property
    def W(self) -> int:
        return self.app.W

    @property
    def H(self) -> int:
        return self.app.H

    def _goto(self, name: str, **kwargs) -> None:
        self.app.goto(name, **kwargs)


# ---------------------------------------------------------------------------
# Animated background
# ---------------------------------------------------------------------------

class AnimBG:
    """Subtle animated grid/particle background."""

    def __init__(self, W: int, H: int) -> None:
        self.W, self.H = W, H
        self.t = 0.0
        import random
        self._particles = [
            {
                "x": random.uniform(0, W),
                "y": random.uniform(0, H),
                "vx": random.uniform(-20, 20),
                "vy": random.uniform(-20, 20),
                "r": random.uniform(1, 3),
                "alpha": random.uniform(30, 80),
            }
            for _ in range(60)
        ]

    def update(self, dt: float) -> None:
        self.t += dt
        for p in self._particles:
            p["x"] = (p["x"] + p["vx"] * dt) % self.W
            p["y"] = (p["y"] + p["vy"] * dt) % self.H

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        # Grid
        grid_surf = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        spacing = 60
        offset_x = (self.t * 6) % spacing
        offset_y = (self.t * 3) % spacing
        for x in range(-spacing, self.W + spacing, spacing):
            alpha = 12 + int(8 * math.sin(self.t + x * 0.01))
            pygame.draw.line(grid_surf, (255, 70, 85, alpha),
                             (x + offset_x, 0), (x + offset_x, self.H))
        for y in range(-spacing, self.H + spacing, spacing):
            alpha = 12 + int(8 * math.sin(self.t * 0.7 + y * 0.01))
            pygame.draw.line(grid_surf, (0, 212, 170, alpha),
                             (0, y + offset_y), (self.W, y + offset_y))
        surface.blit(grid_surf, (0, 0))
        # Particles
        for p in self._particles:
            s = pygame.Surface((int(p["r"]) * 2 + 2,) * 2, pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 70, 85, int(p["alpha"])),
                               (int(p["r"]) + 1,) * 2, int(p["r"]))
            surface.blit(s, (int(p["x"]), int(p["y"])))


# ---------------------------------------------------------------------------
# Main Menu Screen
# ---------------------------------------------------------------------------

class MenuScreen(Screen):
    BUTTONS = [
        ("PLAY",      "scenario_select"),
        ("PROFILE",   "profile"),
        ("SETTINGS",  "settings"),
        ("QUIT",      None),
    ]

    def __init__(self, app) -> None:
        super().__init__(app)
        self._bg = AnimBG(app.W, app.H)
        self._hover = -1
        self._t = 0.0

    def on_enter(self) -> None:
        self._t = 0.0

    def handle_event(self, event) -> None:
        if event.type == pygame.MOUSEMOTION:
            self._hover = -1
            for i, rect in enumerate(self._btn_rects):
                if rect.collidepoint(event.pos):
                    self._hover = i
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self._btn_rects):
                if rect.collidepoint(event.pos):
                    label, dest = self.BUTTONS[i]
                    if dest is None:
                        pygame.event.post(pygame.event.Event(pygame.QUIT))
                    else:
                        self._goto(dest)

    def update(self, dt) -> None:
        self._t += dt
        self._bg.update(dt)

    def draw(self, surface) -> None:
        self._bg.draw(surface)

        # Logo
        title_y = self.H // 2 - 200
        pulse = math.sin(self._t * 2.0) * 3
        draw_text(surface, "VALO", self.W // 2, title_y,
                  size=int(80 + pulse), color=COLOR_PRIMARY, bold=True, center=True)
        draw_text(surface, "WARMUP TRAINER", self.W // 2, title_y + 80,
                  size=32, color=COLOR_WHITE, bold=True, center=True)
        draw_text(surface, "Precision. Speed. Domination.",
                  self.W // 2, title_y + 124,
                  size=18, color=COLOR_GRAY, center=True)

        # Horizontal divider
        pygame.draw.line(surface, COLOR_PRIMARY,
                         (self.W // 2 - 150, title_y + 155),
                         (self.W // 2 + 150, title_y + 155), 1)

        # Buttons
        bw, bh = 240, 52
        bx = self.W // 2 - bw // 2
        by = self.H // 2 - 50
        self._btn_rects = []
        for i, (label, _) in enumerate(self.BUTTONS):
            rect = (bx, by + i * (bh + 12), bw, bh)
            self._btn_rects.append(pygame.Rect(*rect))
            draw_button(surface, rect, label,
                        hovered=(self._hover == i),
                        font_size=22)

        # Footer
        draw_text(surface, "v1.0.0  |  github.com/AbdallahMazouz/valo-warmup-trainer",
                  self.W // 2, self.H - 28, size=13, color=COLOR_GRAY, center=True)


# ---------------------------------------------------------------------------
# Scenario Select Screen
# ---------------------------------------------------------------------------

class ScenarioSelectScreen(Screen):
    COLS = 2

    def __init__(self, app) -> None:
        super().__init__(app)
        self._bg      = AnimBG(app.W, app.H)
        self._hover   = -1
        self._selected_diff = app.settings.difficulty
        self._card_rects: list = []

    def on_enter(self) -> None:
        self._selected_diff = self.app.settings.difficulty

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._goto("menu")
        if event.type == pygame.MOUSEMOTION:
            self._hover = -1
            for i, r in enumerate(self._card_rects):
                if r.collidepoint(event.pos):
                    self._hover = i
            # Difficulty buttons
            mx, my = event.pos
            for i, r in enumerate(self._diff_rects):
                pass  # handled in click
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # Back button
            if self._back_rect.collidepoint(mx, my):
                self._goto("menu")
                return
            # Difficulty
            for i, r in enumerate(self._diff_rects):
                if r.collidepoint(mx, my):
                    self._selected_diff = DIFFICULTIES[i]
                    self.app.settings.set("difficulty", self._selected_diff)
                    return
            # Scenario cards
            for i, r in enumerate(self._card_rects):
                if r.collidepoint(mx, my):
                    sid = SCENARIO_ORDER[i]
                    self._goto("game", scenario_id=sid, difficulty=self._selected_diff)
                    return

    def update(self, dt) -> None:
        self._bg.update(dt)

    def draw(self, surface) -> None:
        self._bg.draw(surface)

        # Title
        draw_text(surface, "SELECT SCENARIO", self.W // 2, 30,
                  size=36, color=COLOR_WHITE, bold=True, center=True)

        # Difficulty selector
        diff_labels = DIFFICULTIES
        dw, dh = 160, 36
        total_dw = len(diff_labels) * (dw + 10) - 10
        dx_start = self.W // 2 - total_dw // 2
        dy = 88
        self._diff_rects = []
        for i, d in enumerate(diff_labels):
            dx = dx_start + i * (dw + 10)
            rect = (dx, dy, dw, dh)
            self._diff_rects.append(pygame.Rect(*rect))
            draw_button(surface, rect, d, active=(d == self._selected_diff), font_size=16)

        draw_text(surface, "DIFFICULTY:", dx_start - 130, dy + 8,
                  size=17, color=COLOR_GRAY, bold=True)

        # Scenario grid
        padding = 24
        card_w = (self.W - padding * 3) // self.COLS
        card_h = 110
        grid_top = 150
        self._card_rects = []

        for i, sid in enumerate(SCENARIO_ORDER):
            col = i % self.COLS
            row = i // self.COLS
            cx = padding + col * (card_w + padding)
            cy = grid_top + row * (card_h + padding)
            rect = pygame.Rect(cx, cy, card_w, card_h)
            self._card_rects.append(rect)

            hovered = (self._hover == i)
            bg_col = (30, 10, 15) if hovered else COLOR_PANEL
            border  = COLOR_PRIMARY if hovered else (40, 40, 60)
            draw_panel(surface, (cx, cy, card_w, card_h),
                       color=bg_col, border_color=border, radius=10)

            # Best score badge
            best = self.app.stats.get_best(sid, self._selected_diff)
            if best:
                draw_text(surface, f"PB: {best['score']:,}", cx + card_w - 12,
                          cy + 10, size=13, color=COLOR_GOLD, bold=True, right=True)

            draw_text(surface, SCENARIO_NAMES[sid], cx + 16, cy + 14,
                      size=20, color=COLOR_WHITE, bold=True)
            draw_text(surface, SCENARIO_DESCRIPTIONS[sid], cx + 16, cy + 44,
                      size=13, color=COLOR_GRAY)

            # Arrow indicator
            if hovered:
                draw_text(surface, "▶  PLAY", cx + card_w // 2, cy + card_h - 26,
                          size=15, color=COLOR_PRIMARY, bold=True, center=True)

        # Back button
        self._back_rect = pygame.Rect(20, 20, 100, 36)
        draw_button(surface, (20, 20, 100, 36), "← BACK", font_size=16)


# ---------------------------------------------------------------------------
# Game Screen
# ---------------------------------------------------------------------------

class GameScreen(Screen):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._scenario = None
        self._scenario_id = ""
        self._difficulty   = "Medium"
        self._mouse_locked = False
        self._show_crosshair = True

    def on_enter(self) -> None:
        pass

    def configure(self, scenario_id: str, difficulty: str) -> None:
        self._scenario_id = scenario_id
        self._difficulty  = difficulty
        self._scenario = make_scenario(scenario_id, self.app.settings, difficulty)
        self._scenario.audio_cb = self.app.audio.play
        # Play area = full window minus HUD strip at top
        pad = 4
        area = (pad, 56, self.W - pad, self.H - pad)
        self._scenario.start(area)
        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._end_early()
                return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._scenario and self._scenario.running:
                mx, my = event.pos
                self._scenario.on_click(mx, my)

    def _end_early(self) -> None:
        if self._scenario:
            self._scenario.running = False
            self._scenario.finished = True
        self._finish()

    def update(self, dt) -> None:
        if self._scenario:
            events = pygame.event.get(pump=False)
            self._scenario.update(dt, events)
            if self._scenario.finished:
                self._finish()

    def _finish(self) -> None:
        s = self._scenario
        if s is None:
            self._goto("menu")
            return
        result = SessionResult(
            scenario_id     = self._scenario_id,
            difficulty      = self._difficulty,
            duration_sec    = s.elapsed,
            hits            = s.hits,
            misses          = s.misses,
            score           = s.score,
            accuracy        = s.accuracy,
            avg_reaction_ms = s.avg_reaction_ms,
        )
        is_pb = self.app.stats.record(result)
        if is_pb:
            self.app.audio.play("pb")
        self._goto("results", result=result, is_pb=is_pb)

    def draw(self, surface) -> None:
        if self._scenario:
            self._scenario.draw(surface)
            # Draw crosshair
            s = self.app.settings
            mx, my = pygame.mouse.get_pos()
            draw_crosshair(
                surface, mx, my,
                size=s.crosshair_size,
                gap=s.crosshair_gap,
                thick=s.crosshair_thick,
                color=tuple(s.crosshair_color),
            )
            # ESC hint
            draw_text(surface, "ESC — End Session", self.W // 2, self.H - 22,
                      size=13, color=COLOR_GRAY, center=True)
        else:
            surface.fill(COLOR_BG)


# ---------------------------------------------------------------------------
# Results Screen
# ---------------------------------------------------------------------------

class ResultsScreen(Screen):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._result: Optional[SessionResult] = None
        self._is_pb   = False
        self._t       = 0.0
        self._hover   = -1
        self._btn_rects: list = []

    def configure(self, result: SessionResult, is_pb: bool) -> None:
        self._result = result
        self._is_pb  = is_pb
        self._t      = 0.0

    def on_enter(self) -> None:
        self._t = 0.0

    def handle_event(self, event) -> None:
        if event.type == pygame.MOUSEMOTION:
            self._hover = -1
            for i, r in enumerate(self._btn_rects):
                if r.collidepoint(event.pos):
                    self._hover = i
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            labels = ["PLAY AGAIN", "SCENARIO SELECT", "MAIN MENU"]
            dests  = ["game",       "scenario_select", "menu"]
            for i, r in enumerate(self._btn_rects):
                if r.collidepoint(mx, my):
                    if dests[i] == "game":
                        self._goto("game",
                                   scenario_id=self._result.scenario_id,
                                   difficulty =self._result.difficulty)
                    else:
                        self._goto(dests[i])
                    return

    def update(self, dt) -> None:
        self._t += dt

    def draw(self, surface) -> None:
        surface.fill(COLOR_BG)
        if not self._result:
            return
        r = self._result
        W, H = self.W, self.H
        cy = 60

        # PB badge
        if self._is_pb:
            pb_pulse = math.sin(self._t * 4) * 0.15 + 1.0
            draw_text(surface, "🏆 NEW PERSONAL BEST!", W // 2, cy,
                      size=int(30 * pb_pulse), color=COLOR_GOLD, bold=True, center=True)
            cy += 56
        else:
            draw_text(surface, "SESSION COMPLETE", W // 2, cy,
                      size=36, color=COLOR_WHITE, bold=True, center=True)
            cy += 52

        # Scenario name
        sname = SCENARIO_NAMES.get(r.scenario_id, r.scenario_id)
        draw_text(surface, f"{sname}  ·  {r.difficulty}", W // 2, cy,
                  size=20, color=COLOR_GRAY, center=True)
        cy += 50

        # Stat cards
        stats_data = [
            ("SCORE",       f"{r.score:,}",               COLOR_GOLD),
            ("ACCURACY",    f"{r.accuracy:.1f}%",          COLOR_GREEN),
            ("HITS",        str(r.hits),                   COLOR_SECONDARY),
            ("MISSES",      str(r.misses),                 COLOR_PRIMARY),
            ("AVG REACTION",f"{r.avg_reaction_ms:.0f} ms", COLOR_ORANGE),
            ("TIME",        f"{r.duration_sec:.0f}s",      COLOR_WHITE),
        ]
        ncols = 3
        card_w, card_h = 200, 90
        total_w = ncols * card_w + (ncols - 1) * 16
        sx = W // 2 - total_w // 2
        for i, (label, val, color) in enumerate(stats_data):
            col = i % ncols
            row = i // ncols
            cx2 = sx + col * (card_w + 16)
            cy2 = cy + row * (card_h + 16)
            draw_panel(surface, (cx2, cy2, card_w, card_h),
                       color=COLOR_PANEL, border_color=(40, 40, 60), radius=8)
            draw_text(surface, label, cx2 + card_w // 2, cy2 + 12,
                      size=13, color=COLOR_GRAY, center=True)
            draw_text(surface, val, cx2 + card_w // 2, cy2 + 34,
                      size=28, color=color, bold=True, center=True)

        cy += (len(stats_data) // ncols) * (card_h + 16) + 30

        # Compare with PB
        best = self.app.stats.get_best(r.scenario_id, r.difficulty)
        if best and not self._is_pb:
            draw_text(surface, f"Personal Best: {best['score']:,}", W // 2, cy,
                      size=18, color=COLOR_GOLD, center=True)
            cy += 32

        # Buttons
        labels = ["PLAY AGAIN", "SCENARIO SELECT", "MAIN MENU"]
        bw, bh = 200, 46
        total_bw = len(labels) * (bw + 16) - 16
        bx_start = W // 2 - total_bw // 2
        self._btn_rects = []
        for i, label in enumerate(labels):
            bx = bx_start + i * (bw + 16)
            rect = (bx, cy, bw, bh)
            self._btn_rects.append(pygame.Rect(*rect))
            draw_button(surface, rect, label, hovered=(self._hover == i),
                        active=(i == 0), font_size=17)


# ---------------------------------------------------------------------------
# Profile Screen
# ---------------------------------------------------------------------------

class ProfileScreen(Screen):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._hover_back = False

    def handle_event(self, event) -> None:
        if event.type == pygame.MOUSEMOTION:
            self._hover_back = pygame.Rect(20, 20, 100, 36).collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._goto("menu")
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if pygame.Rect(20, 20, 100, 36).collidepoint(event.pos):
                self._goto("menu")

    def update(self, dt) -> None:
        pass

    def draw(self, surface) -> None:
        surface.fill(COLOR_BG)
        W, H = self.W, self.H

        draw_text(surface, "PLAYER PROFILE", W // 2, 30,
                  size=36, color=COLOR_WHITE, bold=True, center=True)
        draw_button(surface, (20, 20, 100, 36), "← BACK",
                    hovered=self._hover_back, font_size=16)

        st = self.app.stats
        total_time = st.total_time_played()
        overall_acc = st.overall_accuracy()
        recent = st.get_recent_sessions(10)

        # Summary row
        summary = [
            ("Sessions Played", str(len(st._history))),
            ("Total Time",      f"{total_time / 60:.1f} min"),
            ("Overall Accuracy",f"{overall_acc:.1f}%"),
        ]
        sw, sh = 220, 80
        total_sw = len(summary) * (sw + 16) - 16
        sx = W // 2 - total_sw // 2
        for i, (label, val) in enumerate(summary):
            cx = sx + i * (sw + 16)
            cy = 100
            draw_panel(surface, (cx, cy, sw, sh), color=COLOR_PANEL,
                       border_color=(40, 40, 60), radius=8)
            draw_text(surface, label, cx + sw // 2, cy + 10,
                      size=13, color=COLOR_GRAY, center=True)
            draw_text(surface, val, cx + sw // 2, cy + 32,
                      size=26, color=COLOR_WHITE, bold=True, center=True)

        # Personal bests
        draw_text(surface, "PERSONAL BESTS", W // 2, 210,
                  size=22, color=COLOR_SECONDARY, bold=True, center=True)

        y = 248
        for sid in SCENARIO_ORDER:
            best = st.get_best(sid, self.app.settings.difficulty)
            name = SCENARIO_NAMES[sid]
            if best:
                val_str = f"{best['score']:,}  ·  {best['accuracy']:.0f}%  ·  {best['avg_reaction_ms']:.0f}ms"
            else:
                val_str = "No run yet"
            col = COLOR_GOLD if best else COLOR_GRAY
            draw_text(surface, name, W // 2 - 300, y, size=16, color=COLOR_TEXT)
            draw_text(surface, val_str, W // 2 + 50, y, size=16, color=col, bold=bool(best))
            y += 28
            if y > H - 60:
                break

        # Recent sessions list
        if recent:
            draw_text(surface, "RECENT SESSIONS", W // 2, y + 20,
                      size=18, color=COLOR_SECONDARY, bold=True, center=True)
            y += 48
            for sess in recent[:6]:
                sname = SCENARIO_NAMES.get(sess.get("scenario_id", ""), "?")
                sc    = sess.get("score", 0)
                acc   = sess.get("accuracy", 0)
                draw_text(surface, f"{sname}  ·  {sc:,}  ·  {acc:.0f}%",
                          W // 2, y, size=14, color=COLOR_GRAY, center=True)
                y += 22


# ---------------------------------------------------------------------------
# Settings Screen
# ---------------------------------------------------------------------------

class SettingsScreen(Screen):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._hover_back = False
        self._sliders = {}   # name → (rect, min, max, attr)
        self._dragging = None
        self._hover_btn = {}

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._goto("menu")
        if event.type == pygame.MOUSEMOTION:
            self._hover_back = pygame.Rect(20, 20, 100, 36).collidepoint(event.pos)
            mx, my = event.pos
            if self._dragging:
                self._update_slider(self._dragging, mx)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if pygame.Rect(20, 20, 100, 36).collidepoint(mx, my):
                self.app.settings.save()
                self._goto("menu")
                return
            for name, (rect, lo, hi, attr) in self._sliders.items():
                if rect.collidepoint(mx, my):
                    self._dragging = name
                    self._update_slider(name, mx)
            # Difficulty radio
            for i, d in enumerate(DIFFICULTIES):
                r = self._diff_rects[i] if hasattr(self, "_diff_rects") else None
                if r and r.collidepoint(mx, my):
                    self.app.settings.set("difficulty", d)
            # Crosshair color presets
            for name, r in self._color_btns.items() if hasattr(self, "_color_btns") else []:
                pass
            # Reset button
            if hasattr(self, "_reset_rect") and self._reset_rect.collidepoint(mx, my):
                self.app.settings.reset()
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._dragging:
                self.app.settings.save()
            self._dragging = None

    def _update_slider(self, name: str, mx: int) -> None:
        rect, lo, hi, attr = self._sliders[name]
        ratio = (mx - rect.left) / rect.width
        ratio = max(0.0, min(1.0, ratio))
        val   = lo + (hi - lo) * ratio
        if attr == "volume":
            self.app.settings.set(attr, round(val, 2))
            self.app.audio.set_volume(val)
        elif attr == "fps_cap":
            self.app.settings.set(attr, int(val))
        elif attr == "crosshair_size":
            self.app.settings.set(attr, int(val))
        elif attr == "crosshair_gap":
            self.app.settings.set(attr, int(val))
        else:
            self.app.settings.set(attr, round(val, 3))

    def update(self, dt) -> None:
        pass

    def draw(self, surface) -> None:
        surface.fill(COLOR_BG)
        W, H = self.W, self.H

        draw_text(surface, "SETTINGS", W // 2, 30,
                  size=36, color=COLOR_WHITE, bold=True, center=True)
        draw_button(surface, (20, 20, 100, 36), "← SAVE",
                    hovered=self._hover_back, font_size=16)

        self._sliders = {}
        self._diff_rects = []
        self._color_btns = {}

        col1_x = W // 4
        col2_x = W * 3 // 4

        # --- Left column ---
        y = 110
        self._draw_section(surface, "MOUSE", col1_x, y)
        y += 36
        y = self._draw_slider(surface, "Sensitivity", "sensitivity",
                              col1_x - 140, y, 280, 0.01, 2.0)
        y = self._draw_slider(surface, "FOV", "fov",
                              col1_x - 140, y, 280, 60.0, 120.0)

        y += 10
        self._draw_section(surface, "DISPLAY", col1_x, y)
        y += 36
        y = self._draw_slider(surface, "FPS Cap", "fps_cap",
                              col1_x - 140, y, 280, 30, 360)

        y += 10
        self._draw_section(surface, "AUDIO", col1_x, y)
        y += 36
        y = self._draw_slider(surface, "Volume", "volume",
                              col1_x - 140, y, 280, 0.0, 1.0)

        # --- Right column ---
        y = 110
        self._draw_section(surface, "CROSSHAIR", col2_x, y)
        y += 36
        y = self._draw_slider(surface, "Size", "crosshair_size",
                              col2_x - 140, y, 280, 4, 20)
        y = self._draw_slider(surface, "Gap", "crosshair_gap",
                              col2_x - 140, y, 280, 0, 12)
        y = self._draw_slider(surface, "Thickness", "crosshair_thick",
                              col2_x - 140, y, 280, 1, 6)

        # Crosshair preview
        s = self.app.settings
        preview_x = col2_x
        preview_y = y + 40
        draw_panel(surface, (preview_x - 60, preview_y - 40, 120, 80),
                   color=COLOR_DARK_GRAY, border_color=(40, 40, 60))
        draw_crosshair(surface, preview_x, preview_y,
                       size=s.crosshair_size, gap=s.crosshair_gap,
                       thick=s.crosshair_thick, color=tuple(s.crosshair_color))
        draw_text(surface, "Preview", preview_x, preview_y + 48,
                  size=13, color=COLOR_GRAY, center=True)
        y += 110

        # Crosshair color presets
        self._draw_section(surface, "CROSSHAIR COLOR", col2_x, y)
        y += 36
        color_presets = {
            "Green":   (0, 255, 120),
            "Cyan":    (0, 220, 255),
            "White":   (255, 255, 255),
            "Yellow":  (255, 230, 0),
            "Red":     (255, 60, 60),
        }
        cx_btn = col2_x - 140
        for cname, cval in color_presets.items():
            r = pygame.Rect(cx_btn, y, 50, 26)
            self._color_btns[cname] = r
            is_active = tuple(s.crosshair_color) == cval
            pygame.draw.rect(surface, cval, r, border_radius=4)
            if is_active:
                pygame.draw.rect(surface, COLOR_WHITE, r, 2, border_radius=4)
            if pygame.mouse.get_pressed()[0]:
                mx2, my2 = pygame.mouse.get_pos()
                if r.collidepoint(mx2, my2):
                    self.app.settings.set("crosshair_color", list(cval))
            cx_btn += 58

        # Default difficulty
        y += 48
        self._draw_section(surface, "DEFAULT DIFFICULTY", col2_x, y)
        y += 36
        dw = 130
        dx = col2_x - 140
        for i, d in enumerate(DIFFICULTIES):
            dr = pygame.Rect(dx, y, dw, 30)
            self._diff_rects.append(dr)
            draw_button(surface, (dx, y, dw, 30), d,
                        active=(d == s.difficulty), font_size=14)
            dx += dw + 8

        # Reset button
        self._reset_rect = pygame.Rect(W // 2 - 70, H - 60, 140, 38)
        draw_button(surface, (W // 2 - 70, H - 60, 140, 38), "RESET DEFAULTS",
                    hovered=False, font_size=15)

    def _draw_section(self, surface, title: str, cx: int, y: int) -> None:
        draw_text(surface, title, cx, y, size=15, color=COLOR_SECONDARY,
                  bold=True, center=True)
        pygame.draw.line(surface, COLOR_SECONDARY,
                         (cx - 150, y + 22), (cx + 150, y + 22), 1)

    def _draw_slider(self, surface, label: str, attr: str,
                     x: int, y: int, width: int,
                     lo: float, hi: float) -> int:
        val = getattr(self.app.settings, attr, lo)
        ratio = (val - lo) / (hi - lo) if hi != lo else 0
        ratio = max(0.0, min(1.0, ratio))

        draw_text(surface, label, x, y, size=14, color=COLOR_TEXT)
        if isinstance(val, float):
            draw_text(surface, f"{val:.2f}", x + width + 8, y, size=14, color=COLOR_SECONDARY)
        else:
            draw_text(surface, str(int(val)), x + width + 8, y, size=14, color=COLOR_SECONDARY)

        bar_y = y + 22
        rect  = pygame.Rect(x, bar_y, width, 6)
        pygame.draw.rect(surface, COLOR_DARK_GRAY, rect, border_radius=3)
        filled = int(width * ratio)
        if filled:
            pygame.draw.rect(surface, COLOR_PRIMARY,
                             (x, bar_y, filled, 6), border_radius=3)
        # Thumb
        thumb_x = x + filled
        pygame.draw.circle(surface, COLOR_WHITE, (thumb_x, bar_y + 3), 8)
        pygame.draw.circle(surface, COLOR_PRIMARY, (thumb_x, bar_y + 3), 6)

        self._sliders[attr] = (rect, lo, hi, attr)
        return y + 46
