from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

from app_paths import app_root

ROOT = app_root()
REQUIREMENTS = ROOT / "requirements.txt"

REQUIRED_MODULES = [
    ("requests", "requests"),
    ("minecraft_launcher_lib", "minecraft-launcher-lib"),
    ("customtkinter", "customtkinter"),
    ("webview", "pywebview"),
]


def module_exists(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def main() -> int:
    missing = [package for module, package in REQUIRED_MODULES if not module_exists(module)]
    if missing:
        print("Installing StoneLight Launcher dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)])

    entry = ROOT / "StoneLightLauncherWeb.pyw"
    if not entry.exists():
        print("ERROR: StoneLightLauncherWeb.pyw not found.")
        return 1

    return subprocess.call([sys.executable, str(entry)])


if __name__ == "__main__":
    raise SystemExit(main())
