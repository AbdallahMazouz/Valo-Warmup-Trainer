"""
Target entity — a 2D circle rendered on the play surface.
"""
import pygame
import math
import random
from typing import Optional, Tuple
from .constants import (
    TARGET_COLOR_IDLE, TARGET_COLOR_HIT, TARGET_COLOR_KILL,
    COLOR_PRIMARY, COLOR_WHITE,
)


class Target:
    """A circular aim target with optional movement patterns."""

    # Movement mode constants
    STATIC    = "static"
    STRAFE    = "strafe"        # horizontal oscillation
    JIGGLE    = "jiggle"        # rapid left-right jiggle
    WANDER    = "wander"        # smooth random wander
    PEEK      = "peek"          # peek from a cover position

    def __init__(
        self,
        x: float,
        y: float,
        radius: float = 20.0,
        color=None,
        hp: int = 1,
        move_mode: str = STATIC,
        speed: float = 0.0,
        bounds: Tuple[int, int, int, int] = (0, 0, 1920, 1080),
        lifetime: float = 0.0,   # 0 = infinite
        peek_origin: Optional[Tuple[float, float]] = None,
        peek_range: float = 80.0,
    ) -> None:
        self.x       = x
        self.y       = y
        self.radius  = radius
        self.color   = color or TARGET_COLOR_IDLE
        self.hp      = hp
        self.max_hp  = hp
        self.move_mode  = move_mode
        self.speed      = speed
        self.bounds     = bounds   # (left, top, right, bottom)
        self.lifetime   = lifetime
        self.age        = 0.0
        self.alive      = True
        self.hit        = False
        self.hit_timer  = 0.0
        self.HIT_ANIM   = 0.18    # seconds for hit animation

        # Strafe / jiggle
        self._phase     = random.uniform(0, math.tau)
        self._dir       = random.choice([-1, 1])
        self._ox        = x  # oscillation origin

        # Wander
        self._wx        = x
        self._wy        = y
        self._wangle    = random.uniform(0, math.tau)
        self._wchange   = 0.0

        # Peek
        self._peek_origin = peek_origin or (x, y)
        self._peek_range  = peek_range
        self._peek_phase  = 0.0
        self._peek_exposed = False

        # Pulse animation
        self._pulse      = 0.0

    # ------------------------------------------------------------------
    def update(self, dt: float) -> None:
        if not self.alive:
            return

        self.age += dt
        self._pulse = (self._pulse + dt * 4.0) % math.tau

        if self.hit:
            self.hit_timer -= dt
            if self.hit_timer <= 0:
                self.alive = False
            return

        if self.lifetime > 0 and self.age >= self.lifetime:
            self.alive = False
            return

        # Movement
        l, t, r, b = self.bounds
        if self.move_mode == self.STRAFE:
            self.x = self._ox + math.sin(self.age * self.speed + self._phase) * 200
            self.x = max(l + self.radius, min(r - self.radius, self.x))

        elif self.move_mode == self.JIGGLE:
            amp = 40.0
            self.x = self._ox + math.sin(self.age * self.speed * 2.5 + self._phase) * amp
            self.x = max(l + self.radius, min(r - self.radius, self.x))

        elif self.move_mode == self.WANDER:
            self._wchange -= dt
            if self._wchange <= 0:
                self._wangle += random.uniform(-1.2, 1.2)
                self._wchange = random.uniform(0.3, 0.9)
            spd = self.speed * 120.0
            nx = self.x + math.cos(self._wangle) * spd * dt
            ny = self.y + math.sin(self._wangle) * spd * dt
            # Bounce off bounds
            if nx < l + self.radius or nx > r - self.radius:
                self._wangle = math.pi - self._wangle
                nx = max(l + self.radius, min(r - self.radius, nx))
            if ny < t + self.radius or ny > b - self.radius:
                self._wangle = -self._wangle
                ny = max(t + self.radius, min(b - self.radius, ny))
            self.x, self.y = nx, ny

        elif self.move_mode == self.PEEK:
            self._peek_phase += dt * self.speed
            ox, oy = self._peek_origin
            self.x = ox + math.sin(self._peek_phase) * self._peek_range
            self._peek_exposed = abs(math.sin(self._peek_phase)) > 0.5

    def register_hit(self) -> bool:
        """Returns True if target is eliminated."""
        if not self.alive or self.hit:
            return False
        self.hp -= 1
        if self.hp <= 0:
            self.hit = True
            self.hit_timer = self.HIT_ANIM
            self.color = TARGET_COLOR_KILL
            return True
        else:
            # Flash color for damage
            self.color = TARGET_COLOR_HIT
            return False

    def is_clicked(self, mx: int, my: int) -> bool:
        dx = mx - self.x
        dy = my - self.y
        return dx * dx + dy * dy <= self.radius * self.radius

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        if not self.alive:
            return

        cx, cy = int(self.x), int(self.y)
        r = int(self.radius)

        if self.hit:
            # Shrink + fade on kill
            prog = 1.0 - (self.hit_timer / self.HIT_ANIM)
            r = max(1, int(self.radius * (1.0 - prog * 0.5)))
            alpha = int(255 * (1.0 - prog))
            s = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color[:3], alpha), (r + 2, r + 2), r)
            surface.blit(s, (cx - r - 2, cy - r - 2))
            return

        # HP fraction for visual health ring
        hp_ratio = self.hp / max(1, self.max_hp)

        # Body
        pygame.draw.circle(surface, self.color, (cx, cy), r)

        # Subtle pulsing highlight ring
        pulse_alpha = int(60 + 40 * math.sin(self._pulse))
        ring_surf = pygame.Surface((r * 2 + 6, r * 2 + 6), pygame.SRCALPHA)
        pygame.draw.circle(ring_surf, (*self.color[:3], pulse_alpha), (r + 3, r + 3), r + 3, 2)
        surface.blit(ring_surf, (cx - r - 3, cy - r - 3))

        # Dot center
        pygame.draw.circle(surface, COLOR_WHITE, (cx, cy), max(2, r // 6))

        # Lifetime timer arc (if limited lifetime)
        if self.lifetime > 0:
            remaining = max(0, self.lifetime - self.age)
            ratio = remaining / self.lifetime
            self._draw_timer_ring(surface, cx, cy, r + 5, ratio)

    @staticmethod
    def _draw_timer_ring(surface, cx, cy, radius, ratio):
        if ratio <= 0:
            return
        steps = 32
        start = -math.pi / 2
        end   = start + math.tau * ratio
        pts   = []
        for i in range(steps + 1):
            t = start + (end - start) * i / steps
            pts.append((cx + radius * math.cos(t), cy + radius * math.sin(t)))
        if len(pts) >= 2:
            pygame.draw.lines(surface, (255, 200, 50), False, pts, 2)
