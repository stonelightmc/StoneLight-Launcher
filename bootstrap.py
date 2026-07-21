import importlib.util
import os
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
]


def module_exists(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def install_requirements():
    if not REQUIREMENTS.exists():
        print("ERROR: requirements.txt not found.")
        return False

    print("Installing/updating launcher dependencies...")
    print(f"Using Python: {sys.executable}")
    print()

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)])
        return True
    except subprocess.CalledProcessError as exc:
        print()
        print("ERROR: dependency installation failed.")
        print(f"Exit code: {exc.returncode}")
        return False


def main():
    missing = [(module, package) for module, package in REQUIRED_MODULES if not module_exists(module)]

    if missing:
        print("Missing Python modules:")
        for module, package in missing:
            print(f" - {module}  package: {package}")
        print()
        ok = install_requirements()
        if not ok:
            print()
            print("Try manually:")
            print(f'"{sys.executable}" -m pip install -r requirements.txt')
            return 1

    # Re-check after install
    still_missing = [(module, package) for module, package in REQUIRED_MODULES if not module_exists(module)]
    if still_missing:
        print("ERROR: modules are still missing after install:")
        for module, package in still_missing:
            print(f" - {module}")
        return 1

    launcher = ROOT / "launcher_gui.py"
    if not launcher.exists():
        print("ERROR: launcher_gui.py not found.")
        return 1

    print("Starting StoneLight Launcher...")
    print()
    return subprocess.call([sys.executable, str(launcher)])


if __name__ == "__main__":
    raise SystemExit(main())
