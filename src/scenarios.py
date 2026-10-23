"""
All training scenarios — each is a self-contained class.
"""
import pygame
import math
import random
import time
from typing import Optional, List, Tuple

from .target import Target
from .constants import (
    COLOR_BG, COLOR_PRIMARY, COLOR_SECONDARY, COLOR_WHITE, COLOR_GRAY,
    COLOR_DARK_GRAY, COLOR_TEXT, COLOR_GOLD, COLOR_GREEN, COLOR_ORANGE,
    DIFFICULTY_MULTIPLIERS,
    TARGET_MIN_RADIUS, TARGET_MAX_RADIUS,
)
from .ui import (
    draw_text, draw_panel, draw_bar, draw_crosshair,
    draw_hit_flash, draw_score_popup, draw_timer_arc,
)


# ---------------------------------------------------------------------------
# Base Scenario
# ---------------------------------------------------------------------------

class BaseScenario:
    """Abstract base for all training scenarios."""

    SCENARIO_ID = "base"
    DURATION    = 60.0   # seconds

    def __init__(self, settings, difficulty: str = "Medium") -> None:
        self.settings   = settings
        self.difficulty = difficulty
        self.diff_mult  = DIFFICULTY_MULTIPLIERS.get(difficulty, 1.0)

        self.running    = False
        self.finished   = False
        self.elapsed    = 0.0
        self.total_dur  = self.DURATION

        self.hits       = 0
        self.misses     = 0
        self.score      = 0
        self.reactions: List[float] = []   # ms per hit

        self._targets:  List[Target] = []
        self._popups:   List[dict]   = []     # {text, x, y, t, color}
        self._flashes:  List[dict]   = []     # {x, y, r, t, color}
        self._last_spawn = 0.0
        self._target_appear: Optional[float] = None  # time target appeared

        # Play area (set by start())
        self._area: Tuple[int, int, int, int] = (0, 0, 1920, 1080)

        # Audio callback (set externally)
        self.audio_cb = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start(self, area: Tuple[int, int, int, int]) -> None:
        self._area   = area
        self.running = True
        self.finished = False
        self.elapsed  = 0.0
        self.hits     = 0
        self.misses   = 0
        self.score    = 0
        self.reactions.clear()
        self._targets.clear()
        self._popups.clear()
        self._flashes.clear()
        self._target_appear = None
        self._on_start()

    def _on_start(self) -> None:
        """Override for scenario-specific init."""

    def update(self, dt: float, events: list) -> None:
        if not self.running or self.finished:
            return
        self.elapsed += dt
        if self.elapsed >= self.total_dur:
            self.elapsed = self.total_dur
            self.running = False
            self.finished = True
            return

        self._update_targets(dt)
        self._update_popups(dt)
        self._update_flashes(dt)
        self._on_update(dt, events)

    def _on_update(self, dt: float, events: list) -> None:
        """Override for scenario-specific per-frame logic."""

    def on_click(self, mx: int, my: int) -> None:
        if self.finished:
            return
        self._on_click(mx, my)

    def _on_click(self, mx: int, my: int) -> None:
        hit_any = False
        for target in list(self._targets):
            if target.alive and not target.hit and target.is_clicked(mx, my):
                self._handle_hit(target, mx, my)
                hit_any = True
                break
        if not hit_any:
            self._handle_miss(mx, my)

    def _handle_hit(self, target: Target, mx: int, my: int) -> None:
        killed = target.register_hit()
        if killed:
            self.hits += 1
            pts = self._calc_score(target, mx, my)
            self.score += pts
            if self._target_appear is not None:
                rt = (time.perf_counter() - self._target_appear) * 1000
                self.reactions.append(rt)
                self._target_appear = None
            self._add_popup(f"+{pts}", mx, my, COLOR_GOLD)
            self._add_flash(mx, my, target.radius, COLOR_GREEN)
            if self.audio_cb:
                self.audio_cb("hit")

    def _handle_miss(self, mx: int, my: int) -> None:
        self.misses += 1
        self.score  = max(0, self.score - 50)
        self._add_popup("-50", mx, my, (220, 60, 60))
        if self.audio_cb:
            self.audio_cb("miss")

    def _calc_score(self, target: Target, mx: int, my: int) -> int:
        # Closer to center = more points
        dx = mx - target.x
        dy = my - target.y
        dist = math.sqrt(dx * dx + dy * dy)
        acc = max(0.0, 1.0 - dist / target.radius)
        base = 100
        if self._target_appear is not None:
            rt = (time.perf_counter() - self._target_appear) * 1000
            speed_bonus = max(0, int(400 - rt * 0.4))
        else:
            speed_bonus = 0
        return int((base + speed_bonus) * (1 + acc) * self.diff_mult)

    # ------------------------------------------------------------------
    # Target helpers
    # ------------------------------------------------------------------
    def _spawn_target(
        self,
        move_mode: str = Target.STATIC,
        speed: float = 0.0,
        radius: Optional[float] = None,
        lifetime: float = 0.0,
        color=None,
        hp: int = 1,
        peek_origin=None,
        peek_range: float = 80.0,
    ) -> Target:
        l, t, r, b = self._area
        pad = 60
        x = random.uniform(l + pad, r - pad)
        y = random.uniform(t + pad, b - pad)
        if radius is None:
            radius = random.uniform(
                TARGET_MIN_RADIUS,
                TARGET_MAX_RADIUS / self.diff_mult,
            )
        radius = max(TARGET_MIN_RADIUS, min(TARGET_MAX_RADIUS, radius))
        tgt = Target(
            x=x, y=y, radius=radius, hp=hp,
            move_mode=move_mode, speed=speed,
            bounds=self._area, lifetime=lifetime,
            color=color, peek_origin=peek_origin,
            peek_range=peek_range,
        )
        self._targets.append(tgt)
        self._target_appear = time.perf_counter()
        return tgt

    def _update_targets(self, dt: float) -> None:
        for tgt in self._targets:
            tgt.update(dt)
        self._targets = [t for t in self._targets if t.alive]

    # ------------------------------------------------------------------
    # Popup / flash
    # ------------------------------------------------------------------
    def _add_popup(self, text: str, x: int, y: int, color=(255, 200, 50)) -> None:
        self._popups.append({"text": text, "x": x, "y": y, "t": 0.0, "color": color})

    def _add_flash(self, x: int, y: int, r: float, color) -> None:
        self._flashes.append({"x": x, "y": y, "r": r, "t": 0.0, "color": color})

    def _update_popups(self, dt: float) -> None:
        for p in self._popups:
            p["t"] += dt
        self._popups = [p for p in self._popups if p["t"] < 0.7]

    def _update_flashes(self, dt: float) -> None:
        for f in self._flashes:
            f["t"] += dt
        self._flashes = [f for f in self._flashes if f["t"] < 0.4]

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        self._draw_play_area(surface)
        for target in self._targets:
            target.draw(surface)
        for f in self._flashes:
            draw_hit_flash(surface, int(f["x"]), int(f["y"]),
                           int(f["r"]), f["t"] / 0.4, f["color"])
        for p in self._popups:
            draw_score_popup(surface, p["text"], p["x"], p["y"],
                             p["t"] / 0.7, p["color"])
        self._draw_hud(surface)
        self._on_draw_extra(surface)

    def _draw_play_area(self, surface: pygame.Surface) -> None:
        l, t, r, b = self._area
        pygame.draw.rect(surface, (10, 10, 18), (l, t, r - l, b - t))
        pygame.draw.rect(surface, (30, 30, 45), (l, t, r - l, b - t), 2)

    def _draw_hud(self, surface: pygame.Surface) -> None:
        l, t, r, b = self._area
        # Timer bar at top
        remaining = self.total_dur - self.elapsed
        ratio = remaining / self.total_dur
        bar_color = COLOR_GREEN if ratio > 0.4 else (COLOR_ORANGE if ratio > 0.15 else COLOR_PRIMARY)
        draw_bar(surface, l + 10, t + 8, r - l - 20, 6, ratio, fg_color=bar_color)
        # Time text
        draw_text(surface, f"{int(remaining)}s", l + 14, t + 20, size=18, color=COLOR_TEXT)
        # Score
        draw_text(surface, f"Score: {self.score:,}", r - 14, t + 20, size=18,
                  color=COLOR_GOLD, bold=True, right=True)
        # Accuracy
        total = self.hits + self.misses
        acc = (self.hits / total * 100) if total else 0
        draw_text(surface, f"Acc: {acc:.1f}%", (l + r) // 2, t + 20,
                  size=18, color=COLOR_SECONDARY, center=True)

    def _on_draw_extra(self, surface: pygame.Surface) -> None:
        """Override for extra drawings."""

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------
    @property
    def avg_reaction_ms(self) -> float:
        return sum(self.reactions) / len(self.reactions) if self.reactions else 0.0

    @property
    def accuracy(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total * 100.0) if total else 0.0


# ===========================================================================
# Concrete Scenarios
# ===========================================================================

class FlickScenario(BaseScenario):
    """Targets appear one at a time at random positions. Pure flick training."""
    SCENARIO_ID = "flick"
    DURATION    = 60.0

    def _on_start(self) -> None:
        self._spawn_next()

    def _on_update(self, dt, events) -> None:
        if not any(t.alive and not t.hit for t in self._targets):
            self._spawn_next()

    def _spawn_next(self) -> None:
        lifetime = max(0.8, 2.5 / self.diff_mult)
        self._spawn_target(lifetime=lifetime)

    def _on_click(self, mx, my) -> None:
        hit_any = False
        for target in list(self._targets):
            if target.alive and not target.hit and target.is_clicked(mx, my):
                self._handle_hit(target, mx, my)
                hit_any = True
                break
        if not hit_any:
            self._handle_miss(mx, my)

    def _on_update(self, dt, events) -> None:
        # Auto-expire targets that time out (count as miss)
        for tgt in list(self._targets):
            if tgt.lifetime > 0 and tgt.age >= tgt.lifetime and tgt.alive and not tgt.hit:
                self.misses += 1
                tgt.alive = False
        if not any(t.alive and not t.hit for t in self._targets):
            self._spawn_next()


class TrackingScenario(BaseScenario):
    """Single moving target — hold crosshair on it for time-on-target score."""
    SCENARIO_ID = "tracking"
    DURATION    = 60.0

    def _on_start(self) -> None:
        self._track_target: Optional[Target] = None
        self._time_on_target = 0.0
        self._tot_ticks      = 0
        self._mouse_pos      = (0, 0)
        self._spawn_tracker()

    def _spawn_tracker(self) -> None:
        speed = 0.8 * self.diff_mult
        tgt = self._spawn_target(move_mode=Target.WANDER, speed=speed, radius=22.0)
        tgt.lifetime = 0  # infinite
        self._track_target = tgt
        self._target_appear = None  # tracking doesn't use reaction time

    def _on_update(self, dt, events) -> None:
        for e in events:
            if e.type == pygame.MOUSEMOTION:
                self._mouse_pos = e.pos
        if self._track_target and self._track_target.alive:
            mx, my = self._mouse_pos
            if self._track_target.is_clicked(mx, my):
                self._time_on_target += dt
                self._tot_ticks += 1
                self.score += int(10 * self.diff_mult)
        # Respawn if lost
        if not any(t.alive and not t.hit for t in self._targets):
            self._spawn_tracker()

    def _on_click(self, mx, my) -> None:
        pass  # tracking doesn't register clicks as hits

    def _on_draw_extra(self, surface) -> None:
        l, t, r, b = self._area
        tot = self.elapsed
        ratio = self._time_on_target / tot if tot > 0 else 0
        draw_bar(surface, l + 10, b - 24, r - l - 20, 10, ratio,
                 fg_color=COLOR_SECONDARY)
        draw_text(surface, f"Time-on-target: {ratio * 100:.1f}%",
                  (l + r) // 2, b - 40, size=16, color=COLOR_SECONDARY, center=True)


class SwitchingScenario(BaseScenario):
    """Multiple targets on screen — click them all as fast as possible."""
    SCENARIO_ID = "switching"
    DURATION    = 60.0
    N_TARGETS   = 5

    def _on_start(self) -> None:
        self._wave = 0
        self._spawn_wave()

    def _spawn_wave(self) -> None:
        self._wave += 1
        n = self.N_TARGETS + int(self.diff_mult - 1)
        for _ in range(n):
            self._spawn_target(lifetime=0)

    def _on_update(self, dt, events) -> None:
        if not any(t.alive and not t.hit for t in self._targets):
            self._spawn_wave()


class MicroAdjustScenario(BaseScenario):
    """Small near-still targets, high precision required."""
    SCENARIO_ID = "micro_adjust"
    DURATION    = 60.0

    def _on_start(self) -> None:
        self._spawn_micro()

    def _spawn_micro(self) -> None:
        r = random.uniform(8.0, 14.0)
        lt = max(1.0, 3.0 / self.diff_mult)
        self._spawn_target(radius=r, lifetime=lt)

    def _on_update(self, dt, events) -> None:
        if not any(t.alive and not t.hit for t in self._targets):
            self._spawn_micro()

    def _on_click(self, mx, my) -> None:
        hit_any = False
        for target in list(self._targets):
            if target.alive and not target.hit and target.is_clicked(mx, my):
                self._handle_hit(target, mx, my)
                hit_any = True
                break
        if not hit_any:
            self._handle_miss(mx, my)


class WideSwingScenario(BaseScenario):
    """Targets appear at extreme angles from center — trains wide flicks."""
    SCENARIO_ID = "wide_swing"
    DURATION    = 60.0

    def _on_start(self) -> None:
        self._last_side = 0
        self._spawn_wide()

    def _spawn_wide(self) -> None:
        l, t, r, b = self._area
        cx, cy = (l + r) / 2, (t + b) / 2
        # Alternate sides
        side = -self._last_side or random.choice([-1, 1])
        self._last_side = side
        margin = 80
        x = cx + side * random.uniform((r - l) * 0.3, (r - l) * 0.45)
        y = random.uniform(t + margin, b - margin)
        x = max(l + margin, min(r - margin, x))
        tgt = Target(x=x, y=y, radius=random.uniform(16, 28),
                     bounds=self._area, lifetime=max(0.8, 2.0 / self.diff_mult))
        self._targets.append(tgt)
        self._target_appear = time.perf_counter()

    def _on_update(self, dt, events) -> None:
        for tgt in list(self._targets):
            if tgt.lifetime > 0 and tgt.age >= tgt.lifetime and tgt.alive and not tgt.hit:
                self.misses += 1
                tgt.alive = False
        if not any(t.alive and not t.hit for t in self._targets):
            self._spawn_wide()


class JigglePeekScenario(BaseScenario):
    """Targets jiggle left-right. Click when exposed."""
    SCENARIO_ID = "jiggle_peek"
    DURATION    = 60.0

    def _on_start(self) -> None:
        self._spawn_jiggler()

    def _spawn_jiggler(self) -> None:
        spd = 2.0 * self.diff_mult
        self._spawn_target(move_mode=Target.JIGGLE, speed=spd,
                           radius=random.uniform(14, 24), lifetime=0)

    def _on_update(self, dt, events) -> None:
        if not any(t.alive and not t.hit for t in self._targets):
            self._spawn_jiggler()


class AngleClearingScenario(BaseScenario):
    """Fixed angles — targets appear peeking from predefined corner/angle positions."""
    SCENARIO_ID = "angle_clearing"
    DURATION    = 60.0
    ANGLES      = [
        "Left Wall", "Right Wall", "Center Door",
        "Left Corner", "Right Corner", "High Ground",
    ]

    def _on_start(self) -> None:
        self._angle_idx = 0
        self._spawn_angle()

    def _get_angle_pos(self, name: str) -> Tuple[float, float]:
        l, t, r, b = self._area
        cx, cy = (l + r) / 2, (t + b) / 2
        positions = {
            "Left Wall":   (l + 80,  cy),
            "Right Wall":  (r - 80,  cy),
            "Center Door": (cx,       cy),
            "Left Corner": (l + 80,  t + 80),
            "Right Corner":(r - 80,  t + 80),
            "High Ground": (cx,       t + 60),
        }
        return positions.get(name, (cx, cy))

    def _spawn_angle(self) -> None:
        name = self.ANGLES[self._angle_idx % len(self.ANGLES)]
        self._angle_idx += 1
        x, y = self._get_angle_pos(name)
        jitter = 30
        x += random.uniform(-jitter, jitter)
        y += random.uniform(-jitter, jitter)
        l, t, r, b = self._area
        x = max(l + 40, min(r - 40, x))
        y = max(t + 40, min(b - 40, y))
        lt = max(0.5, 1.5 / self.diff_mult)
        tgt = Target(x=x, y=y, radius=random.uniform(14, 22),
                     bounds=self._area, lifetime=lt)
        self._targets.append(tgt)
        self._target_appear = time.perf_counter()
        self._current_angle = name

    def _on_update(self, dt, events) -> None:
        for tgt in list(self._targets):
            if tgt.lifetime > 0 and tgt.age >= tgt.lifetime and tgt.alive and not tgt.hit:
                self.misses += 1
                tgt.alive = False
        if not any(t.alive and not t.hit for t in self._targets):
            self._spawn_angle()

    def _on_draw_extra(self, surface) -> None:
        name = getattr(self, "_current_angle", "")
        if name:
            l, t, r, b = self._area
            draw_text(surface, f"Angle: {name}", (l + r) // 2, b - 40,
                      size=16, color=COLOR_GRAY, center=True)


class ReactionTimeScenario(BaseScenario):
    """Flash effect → wait → target appears. Measures pure reaction time."""
    SCENARIO_ID = "reaction_time"
    DURATION    = 60.0

    def _on_start(self) -> None:
        self._state     = "waiting"   # waiting | flashing | ready
        self._flash_t   = 0.0
        self._flash_dur = 0.0
        self._wait_t    = 0.0
        self._wait_dur  = random.uniform(0.5, 1.5)
        self._flash_alpha = 0

    def _on_update(self, dt, events) -> None:
        if self._state == "waiting":
            self._wait_t += dt
            if self._wait_t >= self._wait_dur:
                self._state     = "flashing"
                self._flash_dur = random.uniform(0.15, 0.45) / self.diff_mult
                self._flash_t   = 0.0
                if self.audio_cb:
                    self.audio_cb("flash")

        elif self._state == "flashing":
            self._flash_t += dt
            # Lerp flash alpha
            prog = self._flash_t / self._flash_dur
            self._flash_alpha = int(220 * max(0, 1.0 - prog))
            if self._flash_t >= self._flash_dur:
                self._state = "ready"
                self._targets.clear()
                lt = max(0.5, 1.5 / self.diff_mult)
                self._spawn_target(lifetime=lt)

        elif self._state == "ready":
            for tgt in list(self._targets):
                if tgt.lifetime > 0 and tgt.age >= tgt.lifetime and tgt.alive and not tgt.hit:
                    self.misses += 1
                    tgt.alive = False
            if not any(t.alive and not t.hit for t in self._targets):
                self._reset_round()

    def _reset_round(self) -> None:
        self._state    = "waiting"
        self._wait_t   = 0.0
        self._wait_dur = random.uniform(0.5, 2.0)
        self._flash_alpha = 0

    def _on_draw_extra(self, surface) -> None:
        if self._state == "flashing" and self._flash_alpha > 0:
            l, t, r, b = self._area
            flash = pygame.Surface((r - l, b - t), pygame.SRCALPHA)
            flash.fill((255, 255, 200, self._flash_alpha))
            surface.blit(flash, (l, t))
        elif self._state == "waiting":
            l, t, r, b = self._area
            draw_text(surface, "Dodge the flash...", (l + r) // 2, (t + b) // 2,
                      size=24, color=COLOR_GRAY, center=True)


class CounterStrafeScenario(BaseScenario):
    """Strafing targets + player must hold still (cursor in zone) to shoot."""
    SCENARIO_ID = "counter_strafe"
    DURATION    = 60.0

    def _on_start(self) -> None:
        self._zone_t    = 0.0
        self._zone_dur  = 0.0
        self._mouse_pos = (0, 0)
        self._zone_rect = None
        self._zone_charged = False
        self._spawn_strafe()
        self._new_zone()

    def _spawn_strafe(self) -> None:
        spd = 1.2 * self.diff_mult
        self._spawn_target(move_mode=Target.STRAFE, speed=spd,
                           radius=random.uniform(16, 26), lifetime=0)

    def _new_zone(self) -> None:
        l, t, r, b = self._area
        cx = random.randint(l + 100, r - 100)
        cy = random.randint(t + 100, b - 100)
        sz = 60
        self._zone_rect = pygame.Rect(cx - sz // 2, cy - sz // 2, sz, sz)
        self._zone_t    = 0.0
        self._zone_dur  = max(0.4, 0.8 / self.diff_mult)
        self._zone_charged = False

    def _on_update(self, dt, events) -> None:
        for e in events:
            if e.type == pygame.MOUSEMOTION:
                self._mouse_pos = e.pos

        mx, my = self._mouse_pos
        if self._zone_rect and self._zone_rect.collidepoint(mx, my):
            self._zone_t += dt
            if self._zone_t >= self._zone_dur:
                self._zone_charged = True
        else:
            self._zone_t = max(0, self._zone_t - dt * 2)

        if not any(t.alive and not t.hit for t in self._targets):
            self._spawn_strafe()

    def _on_click(self, mx, my) -> None:
        if not self._zone_charged:
            self._handle_miss(mx, my)
            return
        for target in list(self._targets):
            if target.alive and not target.hit and target.is_clicked(mx, my):
                self._handle_hit(target, mx, my)
                self._zone_charged = False
                self._new_zone()
                return
        self._handle_miss(mx, my)

    def _on_draw_extra(self, surface) -> None:
        if not self._zone_rect:
            return
        ratio = min(1.0, self._zone_t / self._zone_dur) if self._zone_dur else 0
        alpha = int(40 + 100 * ratio)
        color = COLOR_SECONDARY if self._zone_charged else (100, 180, 255)
        zone_surf = pygame.Surface((self._zone_rect.width, self._zone_rect.height), pygame.SRCALPHA)
        zone_surf.fill((*color, alpha))
        surface.blit(zone_surf, (self._zone_rect.x, self._zone_rect.y))
        pygame.draw.rect(surface, color, self._zone_rect, 2, border_radius=4)
        l, t, r, b = self._area
        msg = "Hold cursor in zone, then shoot" if not self._zone_charged else "SHOOT!"
        draw_text(surface, msg, (l + r) // 2, b - 40, size=16,
                  color=COLOR_SECONDARY if self._zone_charged else COLOR_GRAY, center=True)


class TacticalComboScenario(BaseScenario):
    """Full warm-up: rotates through flick, tracking, switching, reaction."""
    SCENARIO_ID = "tactical_combo"
    DURATION    = 90.0

    PHASES = ["flick", "tracking", "switching", "reaction"]
    PHASE_DUR = 20.0  # seconds each

    def _on_start(self) -> None:
        self._phase_idx  = 0
        self._phase_t    = 0.0
        self._sub: Optional[BaseScenario] = None
        self._mouse_pos  = (0, 0)
        self._start_phase()

    def _start_phase(self) -> None:
        mapping = {
            "flick":     FlickScenario,
            "tracking":  TrackingScenario,
            "switching": SwitchingScenario,
            "reaction":  ReactionTimeScenario,
        }
        pname = self.PHASES[self._phase_idx % len(self.PHASES)]
        cls   = mapping[pname]
        self._sub = cls(self.settings, self.difficulty)
        self._sub.audio_cb = self.audio_cb
        self._sub.start(self._area)
        self._phase_t   = 0.0
        self._phase_name = pname

    def _on_update(self, dt, events) -> None:
        for e in events:
            if e.type == pygame.MOUSEMOTION:
                self._mouse_pos = e.pos
        self._phase_t += dt
        if self._phase_t >= self.PHASE_DUR:
            # Collect sub-stats
            if self._sub:
                self.hits   += self._sub.hits
                self.misses += self._sub.misses
                self.score  += self._sub.score
                self.reactions.extend(self._sub.reactions)
            self._phase_idx += 1
            self._start_phase()

        if self._sub:
            self._sub.elapsed = self._phase_t
            self._sub.update(dt, events)

    def _on_click(self, mx, my) -> None:
        if self._sub:
            self._sub.on_click(mx, my)
            # Mirror back
            self.hits   = sum(s.hits if hasattr(s, "hits") else 0 for s in [self._sub])
            self.misses = sum(s.misses if hasattr(s, "misses") else 0 for s in [self._sub])
            self.score  = sum(s.score if hasattr(s, "score") else 0 for s in [self._sub])

    def draw(self, surface) -> None:
        if self._sub:
            self._sub.draw(surface)
        self._draw_hud(surface)
        self._draw_phase_banner(surface)

    def _draw_phase_banner(self, surface) -> None:
        l, t, r, b = self._area
        name = self._phase_name.replace("_", " ").title() if hasattr(self, "_phase_name") else ""
        remaining_phase = max(0, self.PHASE_DUR - self._phase_t)
        phases_total = len(self.PHASES)
        cur_phase_n  = (self._phase_idx % phases_total) + 1
        draw_text(surface, f"Phase {cur_phase_n}/{phases_total}: {name}  ({int(remaining_phase)}s)",
                  (l + r) // 2, t + 38, size=20, color=COLOR_PRIMARY, bold=True, center=True)

    def _draw_hud(self, surface) -> None:
        super()._draw_hud(surface)


# ===========================================================================
# Registry
# ===========================================================================

SCENARIO_CLASSES = {
    "flick":         FlickScenario,
    "tracking":      TrackingScenario,
    "switching":     SwitchingScenario,
    "micro_adjust":  MicroAdjustScenario,
    "wide_swing":    WideSwingScenario,
    "jiggle_peek":   JigglePeekScenario,
    "angle_clearing":AngleClearingScenario,
    "reaction_time": ReactionTimeScenario,
    "counter_strafe":CounterStrafeScenario,
    "tactical_combo":TacticalComboScenario,
}


def make_scenario(scenario_id: str, settings, difficulty: str) -> BaseScenario:
    cls = SCENARIO_CLASSES.get(scenario_id, FlickScenario)
    return cls(settings, difficulty)
