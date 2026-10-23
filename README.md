# Valo Warmup Trainer — Professional Web-Based 3D Aim Trainer

<div align="center">

![TypeScript](https://img.shields.io/badge/TypeScript-5.7-blue?logo=typescript)
![Three.js](https://img.shields.io/badge/Three.js-0.170-black?logo=three.js)
![Vite](https://img.shields.io/badge/Vite-6.0-purple?logo=vite)
![Vitest](https://img.shields.io/badge/Vitest-2.1-green?logo=vitest)
![License](https://img.shields.io/badge/License-MIT-yellow)

**A high-performance, browser-based 3D first-person aim trainer engineered specifically for tactical shooter and VALORANT players.**  
*Inspired by iShotU Aim, Aimlabs, and KovaaK's.*

[Live Demo](https://abdallahmazouz.github.io/valo-warmup-trainer/) &bull; [Features](#features) &bull; [Scenarios](#training-scenarios) &bull; [Quick Start](#quick-start) &bull; [Architecture](#architecture)

</div>

---

## Overview

**Valo Warmup Trainer** is a zero-install, client-side 3D aim-training web application. Built with modern TypeScript, WebGL (Three.js), and the browser Pointer Lock API, it delivers low-latency mouse aiming with zero input smoothing and accurate ballistic hit registration.

The trainer is tailored around authentic tactical FPS mechanics:
- **True First-Person 3D Arena** with realistic target depth and collision geometry.
- **Valorant Movement Accuracy (Counter-Strafing)**: Moving while firing penalizes your shots; players must master ADAD counter-strafing to shoot accurately.
- **Head-Level Crosshair Discipline**: Slicing angles at head elevation with dedicated headshot multipliers.
- **Dynamic Tactical Situations**: Wide swings, shoulder/jiggle peeks, angle clearing, and clutch duels.
- **Flash Avoidance & Recovery**: Pop flashes detonate in real-time; players turn away (>75°) to dodge blinding effects or recover quickly for duels.
- **Procedural Synthesizer Audio**: Responsive hit pings, headshot bells, and miss cues without external media dependencies.
- **Full Local Persistence**: Settings, personal bests, and session history stored in `localStorage`.

---

## Features

### 1. Training Scenarios
- **Flick Training**: Static Flicks, Micro Flicks, Wide Flicks, Multi-Target Flicks, Precision Flicks, Reactive Flicks.
- **Smooth & Reactive Tracking**: Wander tracking, fast direction shifts, ADAD strafing tracking, vertical recoil/updraft tracking.
- **VALORANT Tactical Duels**: Wide-swing corner peeks, jiggle-peek timing, angle clearing, first-shot trigger discipline, counter-strafing dead-zone practice.
- **Flash Simulation & Recovery**: Real-time blinding flash simulation with camera turn-away angle detection and post-flash target acquisition.
- **Reaction Time Tests**: Stimulus-to-click visual reaction latency, peripheral vision snap tests.
- **Hybrid Scenarios**: Tactical combo exercises and 1v3 clutch simulation.

### 2. Structured Warm-Up Routines
- **5-Minute Quick Warm-Up**: Essential wrist conditioning and head-level alignment before entering competitive queue.
- **10-Minute Standard Routine**: Comprehensive warm-up covering flicks, micro-adjustments, strafe tracking, and counter-strafing.
- **20-Minute Pro Conditioning**: Tournament-grade endurance routine with precision flicking, reactive tracking, and high-pressure clutch duels.

### 3. Esports Interface & Customization
- **Full Mouse Sensitivity Calibration**: Scaled to Valorant in-game sensitivity (e.g., 0.35 @ 800 DPI).
- **Horizontal Field of View (FOV)**: Configurable from 70° to 120° (defaults to Valorant standard 103°).
- **Interactive Crosshair Customizer**: Custom color presets (Green, Cyan, Yellow, White, Red), size, thickness, inner gap, and center dot with live preview.
- **Detailed Session Analytics**: Accuracy, hits, misses, headshot count, targets/second, average and median reaction time.
- **Personal Best Tracking**: Automatically tracks records per scenario with celebration alerts.

---

## Quick Start

### Prerequisites
- [Node.js](https://nodejs.org/) v18+ and `npm`

### Local Development
```bash
# Clone the standalone repository
git clone https://github.com/AbdallahMazouz/valo-warmup-trainer.git
cd valo-warmup-trainer

# Install dependencies
npm install

# Start development server
npm run dev
```
Open [http://localhost:5173/valo-warmup-trainer/](http://localhost:5173/valo-warmup-trainer/) in your browser.

### Run Tests
```bash
npm run test
```

### Production Build
```bash
npm run build
```
Production assets are generated in `dist/`.

---

## Controls

| Action | Control |
|---|---|
| **Aim / Look** | Mouse (Pointer Lock) |
| **Fire / Click** | Left Mouse Button |
| **Movement** | `W`, `A`, `S`, `D` |
| **Jump** | `Space` |
| **Pause / Release Mouse** | `ESC` |
| **Fullscreen** | `F11` (or browser default) |

---

## Project Structure

```
valo-warmup-trainer/
├── index.html                  # HTML entry point with canvas and UI shell
├── package.json                # Project dependencies and npm scripts
├── tsconfig.json               # Strict TypeScript configuration
├── vite.config.ts              # Vite bundler and Vitest configuration
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions deployment to GitHub Pages
├── src/
│   ├── main.ts                 # Bootstrap and application loop
│   ├── constants.ts            # Physics, scoring, and engine constants
│   ├── types.ts                # TypeScript interfaces & types
│   ├── renderer.ts             # Three.js scene, arena geometry, lighting
│   ├── controls.ts             # Pointer lock camera and movement physics
│   ├── targetManager.ts        # Target spawning, movement patterns, hit detection
│   ├── scenarios.ts            # Complete scenario catalog and warm-up plans
│   ├── engine.ts               # Scenario simulation loop, scoring, timers
│   ├── audio.ts                # Web Audio API procedural sound effects
│   ├── settings.ts             # Persistent settings manager
│   ├── store.ts                # Session history & personal bests manager
│   ├── ui.ts                   # Esports UI, HUD, page routing, results modal
│   └── style.css               # Dark theme esports CSS styles
└── tests/
    └── game.test.ts            # Unit tests for scoring, scenarios, settings & store
```

---

## Deployment to GitHub Pages

This project is configured for automated CI/CD deployment via GitHub Actions:
1. Ensure the repository has GitHub Pages enabled under **Settings > Pages > Source > GitHub Actions**.
2. Push commits to the `main` branch.
3. The workflow builds the production bundle, runs tests, and deploys to:
   `https://abdallahmazouz.github.io/valo-warmup-trainer/`

---

## Critical Project Isolation Notice

This project is an **independent, standalone product** and is completely decoupled from any other repositories:
- Local Folder: `Valo-Warmup-Trainer`
- Dedicated Remote: `https://github.com/AbdallahMazouz/valo-warmup-trainer`
- No shared Git history, branches, or files with `First-Game-Project`.

---

## Fair Play & Security Disclaimer

This is a **standalone web trainer**. It operates entirely within the web browser and **does not interact with, read memory from, inject code into, or modify the live VALORANT game client**. No account details or Riot Games credentials are required.

---

## License

MIT &copy; 2026 Abdallah Mazouz. See [LICENSE](LICENSE) for details.
