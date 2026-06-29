from pathlib import Path
import shutil
import sys


def app_root() -> Path:
    """Return the writable launcher root.

    Source mode: folder containing the Python files.
    PyInstaller mode: folder containing StoneLight Launcher.exe.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def bundled_root() -> Path:
    """Return PyInstaller bundled resource root when frozen."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", app_root())).resolve()
    return Path(__file__).resolve().parent


def bundled_path(relative_path: str) -> Path:
    return bundled_root() / relative_path


def ensure_external_file(relative_path: str, *, overwrite: bool = False) -> Path:
    """Ensure a bundled file exists in the writable launcher root."""
    target = app_root() / relative_path
    if target.exists() and not overwrite:
        return target

    source = bundled_path(relative_path)
    if source.exists() and source.is_file():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    return target


def ensure_external_dir(relative_path: str, *, overwrite: bool = False) -> Path:
    target = app_root() / relative_path
    if target.exists() and not overwrite:
        return target

    source = bundled_path(relative_path)
    if source.exists() and source.is_dir():
        if target.exists() and overwrite:
            shutil.rmtree(target, ignore_errors=True)
        shutil.copytree(source, target, dirs_exist_ok=True)

    return target


def ensure_runtime_files():
    """Copy first-run bundled resources next to the exe if needed."""
    ensure_external_file("config.json")
    ensure_external_file("requirements.txt")
    ensure_external_file("README.md")
    ensure_external_file("SECURITY.md")
    ensure_external_file("MODS_FOUND.md")
    ensure_external_dir("docs")
    ensure_external_dir("assets")
