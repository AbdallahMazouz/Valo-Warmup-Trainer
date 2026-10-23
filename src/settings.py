"""
Persistent settings management — saved to JSON.
"""
import json
import os
from pathlib import Path
from .constants import (
    DEFAULT_SENSITIVITY, DEFAULT_FOV, DEFAULT_FPS,
    DEFAULT_WIDTH, DEFAULT_HEIGHT, DEFAULT_VOLUME,
)

SETTINGS_PATH = Path(os.getenv("APPDATA", ".")) / "ValoWarmupTrainer" / "settings.json"

_DEFAULTS: dict = {
    "sensitivity":  DEFAULT_SENSITIVITY,
    "fov":          DEFAULT_FOV,
    "width":        DEFAULT_WIDTH,
    "height":       DEFAULT_HEIGHT,
    "fps_cap":      DEFAULT_FPS,
    "fullscreen":   False,
    "volume":       DEFAULT_VOLUME,
    "crosshair_color": [0, 255, 120],
    "crosshair_size":  8,
    "crosshair_gap":   4,
    "crosshair_thick": 2,
    "difficulty":   "Medium",
    "show_fps":     True,
    "colorblind":   False,
}


class Settings:
    def __init__(self) -> None:
        self._data: dict = dict(_DEFAULTS)
        self.load()

    # ------------------------------------------------------------------
    def load(self) -> None:
        try:
            if SETTINGS_PATH.exists():
                with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                    stored = json.load(f)
                # Merge: keep defaults for any missing keys
                for k, v in stored.items():
                    if k in self._data:
                        self._data[k] = v
        except Exception:
            pass  # Corrupt file → use defaults

    def save(self) -> None:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    # ------------------------------------------------------------------
    def __getattr__(self, name: str):
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name: str, value) -> None:
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            self._data[name] = value

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        self._data[key] = value
        self.save()

    def reset(self) -> None:
        self._data = dict(_DEFAULTS)
        self.save()
