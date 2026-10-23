"""
build_exe.py — Create a standalone Windows executable with PyInstaller.

Usage:
    python build_exe.py

Output:
    dist/ValoWarmupTrainer/ValoWarmupTrainer.exe
"""
import subprocess
import sys

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--name=ValoWarmupTrainer",
    "--onedir",
    "--windowed",
    "--icon=assets/icon.ico",
    "--add-data=assets;assets",
    "--noconfirm",
    "main.py",
]

print("Building executable…")
result = subprocess.run(cmd)
sys.exit(result.returncode)
