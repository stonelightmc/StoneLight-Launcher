from __future__ import annotations

import subprocess
import sys
import traceback
from pathlib import Path
from tkinter import messagebox
from app_paths import ensure_runtime_files


ROOT = Path(__file__).resolve().parent


def ensure_runtime_dependencies():
    """Install runtime dependencies if this source build is launched directly.

    In a frozen PyInstaller build dependencies are bundled.
    """
    if getattr(sys, "frozen", False):
        return

    req = ROOT / "requirements.txt"
    if not req.exists():
        return

    checks = {
        "customtkinter": "customtkinter",
        "requests": "requests",
        "minecraft-launcher-lib": "minecraft_launcher_lib",
    }

    missing = []
    for _pkg, module in checks.items():
        try:
            __import__(module)
        except Exception:
            missing.append(module)

    if missing:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req)])


def main():
    try:
        ensure_runtime_files()
        ensure_runtime_dependencies()
        import launcher_gui
        launcher_gui.main()
    except SystemExit:
        raise
    except Exception:
        details = traceback.format_exc()
        try:
            messagebox.showerror(
                "StoneLight Launcher",
                "Launcher crashed.\n\nDetails were printed to stderr/debug console.\n\n" + details[-1200:],
            )
        except Exception:
            pass
        print(details, file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
