# Valo Warmup Trainer

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)
![Pygame](https://img.shields.io/badge/Pygame-2.6-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

**A standalone FPS aim-training game built for VALORANT players.**  
Flick. Track. React. Dominate.

</div>

---

## Features

### 10 Training Scenarios
| Scenario | Focus |
|---|---|
| **Flick Training** | Pure flick speed across the screen |
| **Smooth Tracking** | Hold crosshair on a wandering target |
| **Target Switching** | Rapid multi-target sequence elimination |
| **Micro-Adjustments** | Sub-pixel precision corrections |
| **Wide Swing** | Extreme angle flicks left/right |
| **Jiggle Peek** | Anticipate and shoot peeking targets |
| **Angle Clearing** | Fast pre-aim at map-inspired angles |
| **Reaction Time** | Flash dodge + immediate elimination |
| **Counter-Strafe** | Strafing targets + stillness zone |
| **Tactical Combo** | Full warm-up rotation of all modes |

### Quality of Life
- 🎯 **4 difficulty levels** — Easy / Medium / Hard / Valorant Pro
- 📊 **Session statistics** — Score, accuracy, hits/misses, avg reaction time
- 🏆 **Personal bests** tracked per scenario × difficulty
- ⚙️ **Configurable controls** — sensitivity, FOV, crosshair, FPS cap
- 🔊 **Procedural audio feedback** — hit pings, miss thuds, flash sounds
- 🖥️ **Resizable window + F11 fullscreen**
- 💾 **Persistent saves** in `%APPDATA%/ValoWarmupTrainer/`

---

## Quick Start

### Requirements
- Python 3.11+
- Windows / Linux / macOS

### Install & Run

```bash
git clone https://github.com/AbdallahMazouz/valo-warmup-trainer.git
cd valo-warmup-trainer
pip install -r requirements.txt
python main.py
```

---

## Controls

| Input | Action |
|---|---|
| **Mouse** | Aim |
| **Left Click** | Shoot target |
| **ESC** | End session / Back |
| **F11** | Toggle fullscreen |

---

## Project Structure

```
valo-warmup-trainer/
├── main.py              # Entry point
├── requirements.txt
├── build_exe.py         # PyInstaller build script
├── src/
│   ├── app.py           # Application + game loop
│   ├── screens.py       # Menu / Game / Results / Settings / Profile
│   ├── scenarios.py     # All 10 training scenarios
│   ├── target.py        # Target entity with movement modes
│   ├── ui.py            # Drawing helpers (buttons, bars, crosshair…)
│   ├── audio.py         # Procedural audio (no external files needed)
│   ├── settings.py      # Persistent settings (JSON)
│   ├── stats.py         # Session history and personal bests (JSON)
│   └── constants.py     # Global constants and config
├── tests/
│   └── test_game.py     # pytest unit tests
└── assets/              # Icons and future art assets
```

---

## Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

---

## Building a Standalone Executable

```bash
pip install pyinstaller
python build_exe.py
# Output: dist/ValoWarmupTrainer/ValoWarmupTrainer.exe
```

---

## Settings

All settings are stored in `%APPDATA%/ValoWarmupTrainer/settings.json` and persist between sessions.

| Setting | Default | Range |
|---|---|---|
| Sensitivity | 0.12 | 0.01 – 2.0 |
| FOV | 103° | 60° – 120° |
| FPS Cap | 165 | 30 – 360 |
| Volume | 0.7 | 0.0 – 1.0 |
| Crosshair Size | 8 | 4 – 20 |
| Crosshair Gap | 4 | 0 – 12 |
| Crosshair Thickness | 2 | 1 – 6 |

---

## Changelog

### v1.0.0 (2026-10-23)
- Initial release
- 10 training scenarios fully implemented
- Session stats, personal bests, profile screen
- Settings screen with live crosshair preview
- Procedural audio engine (no external sound files)
- Animated menu background
- Full pytest test suite

---

## Important

> **This game does NOT interact with the VALORANT client.**  
> All training is 100% standalone. No memory reading, no injection, no automation.

---

## License

MIT — See [LICENSE](LICENSE) for details.

---

*Built for the community. Not affiliated with Riot Games.*
