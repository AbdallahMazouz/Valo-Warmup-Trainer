"""
Application entry point — window, screen router, game loop.
"""
import sys
import pygame
import time

from .constants import TITLE, DEFAULT_WIDTH, DEFAULT_HEIGHT, DEFAULT_FPS
from .settings import Settings
from .stats import StatsManager
from .audio import AudioManager
from .screens import (
    MenuScreen, ScenarioSelectScreen, GameScreen,
    ResultsScreen, ProfileScreen, SettingsScreen,
)
from .ui import init_fonts, draw_text, get_font
from .constants import COLOR_BG, COLOR_GRAY, COLOR_PRIMARY


class App:
    def __init__(self) -> None:
        pygame.init()
        pygame.font.init()

        self.settings = Settings()
        self.stats    = StatsManager()
        self.audio    = AudioManager()

        # Window
        W = self.settings.width
        H = self.settings.height
        flags = pygame.FULLSCREEN if self.settings.fullscreen else pygame.RESIZABLE
        self._screen = pygame.display.set_mode((W, H), flags)
        pygame.display.set_caption(TITLE)
        self._clock = pygame.time.Clock()

        init_fonts()

        # Screens
        self._screens: dict = {
            "menu":            MenuScreen(self),
            "scenario_select": ScenarioSelectScreen(self),
            "game":            GameScreen(self),
            "results":         ResultsScreen(self),
            "profile":         ProfileScreen(self),
            "settings":        SettingsScreen(self),
        }
        self._current_screen = None
        self.goto("menu")

        self._fps_hist: list[float] = []

    # ------------------------------------------------------------------
    @property
    def W(self) -> int:
        return self._screen.get_width()

    @property
    def H(self) -> int:
        return self._screen.get_height()

    # ------------------------------------------------------------------
    def goto(self, name: str, **kwargs) -> None:
        if self._current_screen:
            self._current_screen.on_exit()
        screen = self._screens.get(name)
        if screen is None:
            return
        # Pass kwargs to configure() if screen supports it
        if kwargs and hasattr(screen, "configure"):
            screen.configure(**kwargs)
        self._current_screen = screen
        screen.on_enter()

    # ------------------------------------------------------------------
    def run(self) -> None:
        fps_cap = self.settings.fps_cap

        while True:
            dt = self._clock.tick(fps_cap) / 1000.0
            dt = min(dt, 0.05)  # Cap delta to avoid spiral of death

            # Events
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self._quit()
                if event.type == pygame.VIDEORESIZE:
                    self._screen = pygame.display.set_mode(
                        (event.w, event.h), pygame.RESIZABLE)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        self._toggle_fullscreen()
                if self._current_screen:
                    self._current_screen.handle_event(event)

            # Update
            if self._current_screen:
                self._current_screen.update(dt)

            # Draw
            self._screen.fill(COLOR_BG)
            if self._current_screen:
                self._current_screen.draw(self._screen)

            # FPS overlay
            if self.settings.show_fps:
                fps = self._clock.get_fps()
                draw_text(self._screen, f"FPS: {fps:.0f}",
                          self.W - 8, 6, size=13, color=COLOR_GRAY, right=True)

            pygame.display.flip()

    def _toggle_fullscreen(self) -> None:
        fs = not self.settings.fullscreen
        self.settings.set("fullscreen", fs)
        if fs:
            self._screen = pygame.display.set_mode(
                (0, 0), pygame.FULLSCREEN)
        else:
            self._screen = pygame.display.set_mode(
                (self.settings.width, self.settings.height), pygame.RESIZABLE)

    def _quit(self) -> None:
        self.settings.save()
        pygame.quit()
        sys.exit(0)
