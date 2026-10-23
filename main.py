"""
Valo Warmup Trainer — main entry point.
Run this file to start the game.
"""
import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import App


def main() -> None:
    app = App()
    app.run()


if __name__ == "__main__":
    main()
