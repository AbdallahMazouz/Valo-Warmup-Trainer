"""
Audio system — plays procedurally-generated beeps for hit/miss/flash feedback.
Pure Python + pygame mixer (no external sound files required).
"""
import pygame
import numpy as np
import struct
import io
from .constants import DEFAULT_VOLUME


def _make_sine(freq: float, duration: float, volume: float = 0.5, sample_rate: int = 44100) -> bytes:
    """Generate a short sine-wave WAV as raw bytes."""
    n_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    wave = np.sin(2 * np.pi * freq * t)
    # Apply fast exponential decay
    decay = np.exp(-6.0 * t / duration)
    wave = (wave * decay * volume * 32767).astype(np.int16)
    # Build minimal WAV
    buf = io.BytesIO()
    data_size = n_samples * 2
    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + data_size))
    buf.write(b"WAVE")
    buf.write(b"fmt ")
    buf.write(struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16))
    buf.write(b"data")
    buf.write(struct.pack("<I", data_size))
    buf.write(wave.tobytes())
    buf.seek(0)
    return buf


class AudioManager:
    def __init__(self) -> None:
        self._volume: float = DEFAULT_VOLUME
        self._sounds: dict = {}
        self._ready = False
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
            self._build_sounds()
            self._ready = True
        except Exception as e:
            print(f"[Audio] Could not init mixer: {e}")

    def _build_sounds(self) -> None:
        specs = {
            "hit":     (880.0, 0.08, 0.6),   # clean ping
            "kill":    (1320.0, 0.15, 0.8),  # higher ping
            "miss":    (200.0, 0.10, 0.3),   # low thud
            "flash":   (400.0, 0.25, 0.5),   # mid whirr
            "start":   (660.0, 0.20, 0.5),
            "pb":      (1047.0, 0.35, 0.7),  # personal best chime
            "tick":    (500.0, 0.05, 0.25),
        }
        for name, (freq, dur, vol) in specs.items():
            try:
                buf = _make_sine(freq, dur, vol)
                self._sounds[name] = pygame.mixer.Sound(buf)
                self._sounds[name].set_volume(self._volume)
            except Exception as e:
                print(f"[Audio] Failed to build sound '{name}': {e}")

    def set_volume(self, v: float) -> None:
        self._volume = max(0.0, min(1.0, v))
        for snd in self._sounds.values():
            snd.set_volume(self._volume)

    def play(self, name: str) -> None:
        if not self._ready:
            return
        snd = self._sounds.get(name)
        if snd:
            snd.play()
