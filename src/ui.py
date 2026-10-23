"""
2D UI drawing helpers — built on top of pygame.
"""
import pygame
import math
from typing import Optional, Tuple
from .constants import (
    COLOR_PRIMARY, COLOR_SECONDARY, COLOR_WHITE, COLOR_GRAY,
    COLOR_PANEL, COLOR_TEXT, COLOR_BG, COLOR_DARK_GRAY,
    COLOR_GOLD, COLOR_GREEN, COLOR_ORANGE,
)

# ---------------------------------------------------------------------------
# Font cache
# ---------------------------------------------------------------------------
_font_cache: dict = {}

def get_font(size: int, bold: bool = False, italic: bool = False) -> pygame.font.Font:
    key = (size, bold, italic)
    if key not in _font_cache:
        # Try to use a system font that looks modern; fall back to default
        for name in ("Segoe UI", "Arial", "Helvetica", "DejaVu Sans", None):
            try:
                _font_cache[key] = pygame.font.SysFont(name, size, bold=bold, italic=italic)
                break
            except Exception:
                continue
    return _font_cache[key]


def init_fonts() -> None:
    """Call once after pygame.font.init()."""
    for sz in (12, 14, 16, 18, 20, 24, 28, 32, 36, 48, 64, 80):
        get_font(sz)
        get_font(sz, bold=True)


# ---------------------------------------------------------------------------
# Drawing primitives
# ---------------------------------------------------------------------------

def draw_text(
    surface: pygame.Surface,
    text: str,
    x: int,
    y: int,
    size: int = 20,
    color=COLOR_TEXT,
    bold: bool = False,
    center: bool = False,
    right: bool = False,
    alpha: int = 255,
) -> pygame.Rect:
    font = get_font(size, bold=bold)
    surf = font.render(str(text), True, color)
    if alpha < 255:
        surf.set_alpha(alpha)
    rect = surf.get_rect()
    if center:
        rect.centerx = x
    elif right:
        rect.right = x
    else:
        rect.left = x
    rect.top = y
    surface.blit(surf, rect)
    return rect


def draw_panel(
    surface: pygame.Surface,
    rect: Tuple[int, int, int, int],
    color=COLOR_PANEL,
    border_color=None,
    border_width: int = 1,
    radius: int = 8,
    alpha: int = 255,
) -> None:
    x, y, w, h = rect
    panel = pygame.Surface((w, h), pygame.SRCALPHA)
    r, g, b = color[:3]
    a = color[3] if len(color) == 4 else alpha
    pygame.draw.rect(panel, (r, g, b, a), (0, 0, w, h), border_radius=radius)
    if border_color:
        pygame.draw.rect(panel, border_color, (0, 0, w, h), border_width, border_radius=radius)
    surface.blit(panel, (x, y))


def draw_bar(
    surface: pygame.Surface,
    x: int,
    y: int,
    width: int,
    height: int,
    value: float,          # 0.0 – 1.0
    fg_color=COLOR_PRIMARY,
    bg_color=COLOR_DARK_GRAY,
    radius: int = 4,
) -> None:
    pygame.draw.rect(surface, bg_color, (x, y, width, height), border_radius=radius)
    filled = int(width * max(0.0, min(1.0, value)))
    if filled > 0:
        pygame.draw.rect(surface, fg_color, (x, y, filled, height), border_radius=radius)


def draw_button(
    surface: pygame.Surface,
    rect: Tuple[int, int, int, int],
    label: str,
    hovered: bool = False,
    active: bool = False,
    font_size: int = 20,
    radius: int = 6,
) -> None:
    x, y, w, h = rect
    if active:
        bg = COLOR_PRIMARY
        tc = COLOR_WHITE
    elif hovered:
        bg = (60, 20, 30)
        tc = COLOR_PRIMARY
    else:
        bg = COLOR_DARK_GRAY
        tc = COLOR_TEXT
    border = COLOR_PRIMARY if (active or hovered) else COLOR_GRAY

    draw_panel(surface, rect, color=bg, border_color=border, radius=radius)
    draw_text(surface, label, x + w // 2, y + h // 2 - font_size // 2,
              size=font_size, color=tc, bold=active or hovered, center=True)


def draw_crosshair(
    surface: pygame.Surface,
    cx: int,
    cy: int,
    size: int = 8,
    gap: int = 4,
    thick: int = 2,
    color=(0, 255, 120),
    dot: bool = False,
) -> None:
    # Horizontal lines
    pygame.draw.line(surface, color, (cx - size - gap, cy), (cx - gap, cy), thick)
    pygame.draw.line(surface, color, (cx + gap, cy), (cx + size + gap, cy), thick)
    # Vertical lines
    pygame.draw.line(surface, color, (cx, cy - size - gap), (cx, cy - gap), thick)
    pygame.draw.line(surface, color, (cx, cy + gap), (cx, cy + size + gap), thick)
    if dot:
        pygame.draw.circle(surface, color, (cx, cy), thick)


def draw_hit_flash(
    surface: pygame.Surface,
    cx: int,
    cy: int,
    radius: int,
    progress: float,    # 0.0 = just hit, 1.0 = done
    color=COLOR_GREEN,
) -> None:
    """Expanding ring that fades on hit."""
    alpha = int(255 * (1.0 - progress))
    r = int(radius + radius * progress * 1.5)
    ring_surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
    c = (*color[:3], alpha)
    pygame.draw.circle(ring_surf, c, (r + 2, r + 2), r, 2)
    surface.blit(ring_surf, (cx - r - 2, cy - r - 2))


def draw_score_popup(
    surface: pygame.Surface,
    text: str,
    x: int,
    y: int,
    progress: float,    # 0→1
    color=COLOR_GOLD,
) -> None:
    """Floating score text that rises and fades."""
    alpha = int(255 * (1.0 - progress))
    offset_y = int(40 * progress)
    draw_text(surface, text, x, y - offset_y, size=22, color=color,
              bold=True, center=True, alpha=alpha)


def draw_timer_arc(
    surface: pygame.Surface,
    cx: int,
    cy: int,
    radius: int,
    remaining: float,
    total: float,
    color=COLOR_SECONDARY,
    bg_color=COLOR_DARK_GRAY,
    thick: int = 4,
) -> None:
    """Draw a circular countdown arc."""
    ratio = max(0.0, remaining / total) if total > 0 else 0.0
    # Background circle
    pygame.draw.circle(surface, bg_color, (cx, cy), radius, thick)
    # Arc (approximated with small line segments)
    if ratio > 0:
        steps = 60
        start_angle = -math.pi / 2
        end_angle = start_angle + 2 * math.pi * ratio
        pts = []
        for i in range(steps + 1):
            t = start_angle + (end_angle - start_angle) * i / steps
            pts.append((cx + radius * math.cos(t), cy + radius * math.sin(t)))
        if len(pts) >= 2:
            pygame.draw.lines(surface, color, False, pts, thick)
