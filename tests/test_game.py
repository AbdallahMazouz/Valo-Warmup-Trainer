"""
Unit tests for Valo Warmup Trainer.
Run: python -m pytest tests/ -v
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class TestSettings:
    def test_defaults(self, tmp_path, monkeypatch):
        monkeypatch.setenv("APPDATA", str(tmp_path))
        from src.settings import Settings
        s = Settings()
        assert 0.0 < s.sensitivity < 5.0
        assert 60 <= s.fov <= 120
        assert s.volume == pytest.approx(0.7, abs=0.01)

    def test_set_and_save(self, tmp_path, monkeypatch):
        monkeypatch.setenv("APPDATA", str(tmp_path))
        from src.settings import Settings
        s = Settings()
        s.set("sensitivity", 0.5)
        # Reload
        s2 = Settings()
        assert s2.sensitivity == pytest.approx(0.5, abs=0.001)

    def test_reset(self, tmp_path, monkeypatch):
        monkeypatch.setenv("APPDATA", str(tmp_path))
        from src.settings import Settings
        s = Settings()
        s.set("sensitivity", 9.9)
        s.reset()
        from src.constants import DEFAULT_SENSITIVITY
        assert s.sensitivity == pytest.approx(DEFAULT_SENSITIVITY, abs=0.001)


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

class TestStats:
    def _fresh_manager(self, tmp_path):
        """Return a StatsManager that reads/writes to an isolated temp path."""
        import importlib
        import src.stats as stats_mod
        from pathlib import Path
        path = tmp_path / "stats.json"
        sm = stats_mod.StatsManager(path=path)
        return sm

    def _make_result(self, score=500, scenario_id="flick", difficulty="Medium",
                     hits=10, misses=2, accuracy=83.3, avg_rt=220.0):
        from src.stats import SessionResult
        return SessionResult(
            scenario_id=scenario_id,
            difficulty=difficulty,
            duration_sec=60.0,
            hits=hits,
            misses=misses,
            score=score,
            accuracy=accuracy,
            avg_reaction_ms=avg_rt,
        )

    def test_record_and_best(self, tmp_path):
        sm = self._fresh_manager(tmp_path)
        r1 = self._make_result(score=300)
        r2 = self._make_result(score=500)
        sm.record(r1)
        sm.record(r2)
        best = sm.get_best("flick", "Medium")
        assert best is not None
        assert best["score"] == 500

    def test_pb_flag(self, tmp_path):
        sm = self._fresh_manager(tmp_path)
        r1 = self._make_result(score=100)
        r2 = self._make_result(score=200)
        r3 = self._make_result(score=150)
        assert sm.record(r1) is True    # First run → always PB
        assert sm.record(r2) is True    # Higher score → PB
        assert sm.record(r3) is False   # Lower score → not PB

    def test_overall_accuracy(self, tmp_path):
        sm = self._fresh_manager(tmp_path)
        r = self._make_result(hits=8, misses=2, accuracy=80.0)
        sm.record(r)
        # overall_accuracy is computed from hits/misses counts
        assert sm.overall_accuracy() == pytest.approx(80.0, abs=0.1)

    def test_total_time(self, tmp_path):
        sm = self._fresh_manager(tmp_path)
        for _ in range(3):
            r = self._make_result()
            r.duration_sec = 60.0
            sm.record(r)
        assert sm.total_time_played() == pytest.approx(180.0, abs=0.1)


# ---------------------------------------------------------------------------
# Target
# ---------------------------------------------------------------------------

class TestTarget:
    def _make_target(self, x=100, y=100, radius=20):
        # Pygame not initialized — skip display but test logic
        import importlib
        try:
            import pygame
            pygame.init()
        except Exception:
            pytest.skip("pygame not available")
        from src.target import Target
        return Target(x=x, y=y, radius=radius, bounds=(0, 0, 1920, 1080))

    def test_hit_detection(self):
        tgt = self._make_target(100, 100, 20)
        assert tgt.is_clicked(100, 100)      # dead center
        assert tgt.is_clicked(115, 100)      # inside
        assert not tgt.is_clicked(125, 100)  # outside

    def test_register_hit(self):
        tgt = self._make_target(100, 100, 20)
        killed = tgt.register_hit()
        assert killed is True
        assert tgt.hit is True

    def test_hp_depletion(self):
        import pygame
        pygame.init()
        from src.target import Target
        tgt = Target(x=100, y=100, radius=20, hp=3, bounds=(0, 0, 1920, 1080))
        assert tgt.register_hit() is False
        assert tgt.register_hit() is False
        assert tgt.register_hit() is True

    def test_update_static(self):
        tgt = self._make_target(100, 100, 20)
        orig_x, orig_y = tgt.x, tgt.y
        tgt.update(0.1)
        assert tgt.x == orig_x
        assert tgt.y == orig_y

    def test_lifetime_expire(self):
        import pygame
        pygame.init()
        from src.target import Target
        tgt = Target(x=100, y=100, radius=20, lifetime=0.5, bounds=(0, 0, 1920, 1080))
        tgt.update(0.6)
        assert tgt.alive is False


# ---------------------------------------------------------------------------
# Scenario
# ---------------------------------------------------------------------------

class TestScenarios:
    def setup_method(self):
        try:
            import pygame
            pygame.init()
            pygame.display.set_mode((800, 600))
        except Exception:
            pytest.skip("pygame display not available")

    def _make_settings(self, tmp_path, monkeypatch):
        monkeypatch.setenv("APPDATA", str(tmp_path))
        from src.settings import Settings
        return Settings()

    def test_flick_scenario_basic(self, tmp_path, monkeypatch):
        s = self._make_settings(tmp_path, monkeypatch)
        from src.scenarios import FlickScenario
        sc = FlickScenario(s, "Medium")
        sc.start((0, 56, 1920, 1080))
        assert sc.running
        assert len(sc._targets) > 0

    def test_miss_decrements_score(self, tmp_path, monkeypatch):
        s = self._make_settings(tmp_path, monkeypatch)
        from src.scenarios import FlickScenario
        sc = FlickScenario(s, "Medium")
        sc.start((0, 56, 1920, 1080))
        sc.score = 200
        sc.on_click(0, 0)   # definitely a miss
        assert sc.misses == 1
        assert sc.score < 200

    def test_scenario_finishes_on_time(self, tmp_path, monkeypatch):
        s = self._make_settings(tmp_path, monkeypatch)
        from src.scenarios import FlickScenario
        sc = FlickScenario(s, "Medium")
        sc.start((0, 56, 800, 600))
        sc.update(sc.total_dur + 0.1, [])
        assert sc.finished

    def test_make_scenario_factory(self, tmp_path, monkeypatch):
        s = self._make_settings(tmp_path, monkeypatch)
        from src.scenarios import make_scenario, SCENARIO_CLASSES
        for sid in SCENARIO_CLASSES:
            sc = make_scenario(sid, s, "Medium")
            assert sc is not None
