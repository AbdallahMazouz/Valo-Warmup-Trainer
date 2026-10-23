"""
Statistics, personal bests, and session history — saved to JSON.
"""
import json
import time
from pathlib import Path
import os
from typing import Optional

STATS_PATH = Path(os.getenv("APPDATA", ".")) / "ValoWarmupTrainer" / "stats.json"


def _resolve_stats_path() -> Path:
    """Always re-read APPDATA so monkeypatching works in tests."""
    return Path(os.getenv("APPDATA", ".")) / "ValoWarmupTrainer" / "stats.json"


class SessionResult:
    """Result of one completed scenario run."""
    __slots__ = (
        "scenario_id", "difficulty", "duration_sec",
        "hits", "misses", "score", "accuracy", "avg_reaction_ms",
        "timestamp",
    )

    def __init__(
        self,
        scenario_id: str,
        difficulty: str,
        duration_sec: float,
        hits: int,
        misses: int,
        score: int,
        accuracy: float,
        avg_reaction_ms: float,
    ) -> None:
        self.scenario_id     = scenario_id
        self.difficulty      = difficulty
        self.duration_sec    = duration_sec
        self.hits            = hits
        self.misses          = misses
        self.score           = score
        self.accuracy        = accuracy
        self.avg_reaction_ms = avg_reaction_ms
        self.timestamp       = time.time()

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__slots__}

    @classmethod
    def from_dict(cls, d: dict) -> "SessionResult":
        r = cls.__new__(cls)
        for k in cls.__slots__:
            setattr(r, k, d.get(k, 0))
        return r


class StatsManager:
    def __init__(self, path: Optional[Path] = None) -> None:
        self._history: list[dict] = []
        self._bests: dict[str, dict] = {}  # scenario_id → best session dict
        self._path = path  # None = use dynamic APPDATA path
        self.load()

    def _get_path(self) -> Path:
        if self._path is not None:
            return self._path
        return _resolve_stats_path()

    # ------------------------------------------------------------------
    def load(self) -> None:
        try:
            p = self._get_path()
            if p.exists():
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._history = data.get("history", [])
                self._bests   = data.get("bests", {})
        except Exception:
            self._history = []
            self._bests   = {}

    def save(self) -> None:
        p = self._get_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"history": self._history, "bests": self._bests}, f, indent=2)

    # ------------------------------------------------------------------
    def record(self, result: SessionResult) -> bool:
        """Record result. Returns True if a new personal best was set."""
        d = result.to_dict()
        self._history.append(d)
        # Keep last 1000 sessions
        if len(self._history) > 1000:
            self._history = self._history[-1000:]

        key = f"{result.scenario_id}_{result.difficulty}"
        is_pb = False
        prev = self._bests.get(key)
        if prev is None or result.score > prev["score"]:
            self._bests[key] = d
            is_pb = True
        self.save()
        return is_pb

    def get_best(self, scenario_id: str, difficulty: str) -> Optional[dict]:
        return self._bests.get(f"{scenario_id}_{difficulty}")

    def get_history(self, scenario_id: str = None, limit: int = 20) -> list[dict]:
        h = self._history
        if scenario_id:
            h = [s for s in h if s.get("scenario_id") == scenario_id]
        return h[-limit:]

    def get_recent_sessions(self, limit: int = 10) -> list[dict]:
        return list(reversed(self._history[-limit:]))

    def total_time_played(self) -> float:
        return sum(s.get("duration_sec", 0) for s in self._history)

    def overall_accuracy(self) -> float:
        total_hits   = sum(s.get("hits", 0) for s in self._history)
        total_misses = sum(s.get("misses", 0) for s in self._history)
        denom = total_hits + total_misses
        return (total_hits / denom * 100.0) if denom else 0.0
