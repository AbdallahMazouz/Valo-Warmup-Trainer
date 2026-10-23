"""
Global constants for Valo Warmup Trainer.
"""

# Window
TITLE = "Valo Warmup Trainer"
DEFAULT_WIDTH = 1920
DEFAULT_HEIGHT = 1080
DEFAULT_FPS = 165

# Colors (R, G, B)
COLOR_BG          = (13, 13, 20)
COLOR_PRIMARY     = (255, 70, 85)     # Valorant red
COLOR_SECONDARY   = (0, 212, 170)     # Teal accent
COLOR_WHITE       = (255, 255, 255)
COLOR_GRAY        = (120, 120, 140)
COLOR_DARK_GRAY   = (30, 30, 42)
COLOR_PANEL       = (18, 18, 28)
COLOR_HIGHLIGHT   = (255, 70, 85, 60)
COLOR_TEXT        = (220, 220, 235)
COLOR_GOLD        = (255, 210, 50)
COLOR_GREEN       = (80, 220, 100)
COLOR_ORANGE      = (255, 155, 50)

# Crosshair
CROSSHAIR_SIZE    = 8
CROSSHAIR_GAP     = 4
CROSSHAIR_THICK   = 2
CROSSHAIR_COLOR   = (0, 255, 120)

# Target defaults
TARGET_MIN_RADIUS = 10
TARGET_MAX_RADIUS = 40
TARGET_COLOR_IDLE = (220, 50, 60)
TARGET_COLOR_HIT  = (0, 255, 120)
TARGET_COLOR_KILL = (255, 200, 0)

# Gameplay
DEFAULT_SENSITIVITY = 0.12   # deg/pixel at 800 DPI
DEFAULT_FOV         = 103.0  # Valorant default ~103 horizontal
DEFAULT_VOLUME      = 0.7

# Scenario IDs
SCENARIO_FLICK       = "flick"
SCENARIO_TRACKING    = "tracking"
SCENARIO_SWITCHING   = "switching"
SCENARIO_MICRO       = "micro_adjust"
SCENARIO_WIDESWING   = "wide_swing"
SCENARIO_JIGGLE      = "jiggle_peek"
SCENARIO_ANGLE       = "angle_clearing"
SCENARIO_REACTION    = "reaction_time"
SCENARIO_COUNTER     = "counter_strafe"
SCENARIO_TACTICAL    = "tactical_combo"

SCENARIO_ORDER = [
    SCENARIO_FLICK,
    SCENARIO_TRACKING,
    SCENARIO_SWITCHING,
    SCENARIO_MICRO,
    SCENARIO_WIDESWING,
    SCENARIO_JIGGLE,
    SCENARIO_ANGLE,
    SCENARIO_REACTION,
    SCENARIO_COUNTER,
    SCENARIO_TACTICAL,
]

SCENARIO_NAMES = {
    SCENARIO_FLICK:    "Flick Training",
    SCENARIO_TRACKING: "Smooth Tracking",
    SCENARIO_SWITCHING:"Target Switching",
    SCENARIO_MICRO:    "Micro-Adjustments",
    SCENARIO_WIDESWING:"Wide Swing",
    SCENARIO_JIGGLE:   "Jiggle Peek",
    SCENARIO_ANGLE:    "Angle Clearing",
    SCENARIO_REACTION: "Reaction Time",
    SCENARIO_COUNTER:  "Counter-Strafe",
    SCENARIO_TACTICAL: "Tactical Combo",
}

SCENARIO_DESCRIPTIONS = {
    SCENARIO_FLICK:    "Click fast-appearing targets across the screen. Pure flick speed.",
    SCENARIO_TRACKING: "Keep your crosshair locked on moving targets.",
    SCENARIO_SWITCHING:"Click targets in rapid sequence — builds target transfer speed.",
    SCENARIO_MICRO:    "Fine-tune tiny corrections on close, near-still targets.",
    SCENARIO_WIDESWING:"Targets appear at extreme angles — practice wide swings.",
    SCENARIO_JIGGLE:   "Targets jiggle left-right. Anticipate and flick on exposure.",
    SCENARIO_ANGLE:    "Clear pre-aim angles fast. Precision over speed.",
    SCENARIO_REACTION: "Wait for flash end, then eliminate the target. Tests RT.",
    SCENARIO_COUNTER:  "Targets move, you must strafe and aim simultaneously.",
    SCENARIO_TACTICAL: "Combined scenario: flick, track, switch, react — full warm-up.",
}

# Difficulty
DIFFICULTIES = ["Easy", "Medium", "Hard", "Valorant Pro"]
DIFFICULTY_MULTIPLIERS = {
    "Easy":         0.6,
    "Medium":       1.0,
    "Hard":         1.4,
    "Valorant Pro": 2.0,
}

# Warm-up routines (minutes → seconds)
WARMUP_ROUTINES = {
    "5-minute":  5 * 60,
    "10-minute": 10 * 60,
    "20-minute": 20 * 60,
}
