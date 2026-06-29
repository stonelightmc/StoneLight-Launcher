
import json
import os
import re
import subprocess
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"


class UpdateError(RuntimeError):
    pass


def parse_version(value: str) -> tuple[int, ...]:
    value = (value or "").strip().removeprefix("v").removeprefix("V")
    parts = re.findall(r"\d+", value)
    return tuple(int(part) for part in parts[:4]) or (0,)


def is_newer_version(latest: str, current: str) -> bool:
    return parse_version(latest) > parse_version(current)


def load_config() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_config(config: dict):
    CONFIG_PATH.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


def github_latest_release(repo: str, timeout: int = 12) -> dict:
    repo = (repo or "").strip().strip("/")
    if not repo or "/" not in repo:
        raise UpdateError("Некорректный GitHub repo для обновлений.")

    url = f"https://api.github.com/repos/{repo}/releases/latest"
    response = requests.get(
        url,
        timeout=timeout,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "StoneLight-Launcher-Updater",
        },
    )
    if response.status_code == 404:
        raise UpdateError(f"В репозитории {repo} не найден latest release.")
    response.raise_for_status()
    return response.json()


def release_version(release: dict) -> str:
    tag = str(release.get("tag_name") or release.get("name") or "").strip()
    match = re.search(r"\d+(?:\.\d+)+", tag)
    return match.group(0) if match else tag.removeprefix("v").removeprefix("V")


def find_asset(release: dict, *, keyword: str = "", prefix: str = "", suffix: str = ".zip") -> dict | None:
    keyword = (keyword or "").lower()
    prefix = (prefix or "").lower()
    suffix = (suffix or "").lower()

    assets = release.get("assets") or []
    for asset in assets:
        name = str(asset.get("name") or "")
        lower = name.lower()
        if keyword and keyword not in lower:
            continue
        if prefix and not lower.startswith(prefix):
            continue
        if suffix and not lower.endswith(suffix):
            continue
        if asset.get("browser_download_url"):
            return asset

    for asset in assets:
        name = str(asset.get("name") or "")
        lower = name.lower()
        if suffix and lower.endswith(suffix) and asset.get("browser_download_url"):
            return asset

    return None


def check_launcher_update(config: dict | None = None) -> dict:
    config = config or load_config()
    current = str(config.get("launcher_version", "0.0.0"))
    repo = config.get("launcher_update_repo", "stonelightmc/StoneLight-Launcher")
    keyword = config.get("launcher_update_asset_keyword", "GitHub.zip")

    release = github_latest_release(repo)
    latest = release_version(release)
    asset = find_asset(release, keyword=keyword, suffix=".zip")

    return {
        "kind": "launcher",
        "repo": repo,
        "current_version": current,
        "latest_version": latest,
        "has_update": bool(latest and is_newer_version(latest, current)),
        "release_name": release.get("name") or release.get("tag_name") or latest,
        "release_url": release.get("html_url", ""),
        "asset_name": asset.get("name", "") if asset else "",
        "asset_url": asset.get("browser_download_url", "") if asset else "",
    }


def infer_minecraft_version_from_modpack_name(name: str) -> str:
    match = re.search(r"mods[_-](\d+(?:\.\d+)+)", name or "", re.IGNORECASE)
    return match.group(1) if match else ""


def check_official_modpack_update(config: dict | None = None) -> dict:
    config = config or load_config()
    repo = config.get("official_modpack_update_repo", "stonelightmc/stonelightmc.github.io")
    prefix = config.get("official_modpack_asset_prefix", "mods_")
    suffix = config.get("official_modpack_asset_suffix", ".zip")

    release = github_latest_release(repo)
    asset = find_asset(release, prefix=prefix, suffix=suffix)
    asset_name = asset.get("name", "") if asset else ""
    asset_url = asset.get("browser_download_url", "") if asset else ""
    current_url = config.get("mods_zip_url", "")
    latest_mc = infer_minecraft_version_from_modpack_name(asset_name)

    return {
        "kind": "official_modpack",
        "repo": repo,
        "current_url": current_url,
        "current_minecraft_version": config.get("minecraft_version", ""),
        "latest_minecraft_version": latest_mc,
        "has_update": bool(asset_url and asset_url != current_url),
        "release_name": release.get("name") or release.get("tag_name") or "",
        "release_url": release.get("html_url", ""),
        "asset_name": asset_name,
        "asset_url": asset_url,
    }


def download_file(url: str, dest: Path, progress_callback=None) -> Path:
    if not url:
        raise UpdateError("Нет URL для скачивания обновления.")

    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=30, headers={"User-Agent": "StoneLight-Launcher-Updater"}) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length") or 0)
        done = 0
        with dest.open("wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 256):
                if not chunk:
                    continue
                f.write(chunk)
                done += len(chunk)
                if progress_callback and total:
                    progress_callback(done, total)
    return dest


def download_launcher_update(info: dict, progress_callback=None) -> Path:
    name = info.get("asset_name") or "StoneLightLauncher_update.zip"
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", name)
    dest = ROOT / "data" / "updates" / safe_name
    return download_file(info.get("asset_url", ""), dest, progress_callback=progress_callback)


def apply_official_modpack_update_to_config(info: dict, config: dict | None = None) -> dict:
    config = dict(config or load_config())

    if not info.get("asset_url"):
        raise UpdateError("Не найден asset официальной сборки.")

    config["mods_zip_url"] = info["asset_url"]
    config["mods_zip_sha256"] = ""
    if info.get("latest_minecraft_version"):
        config["minecraft_version"] = info["latest_minecraft_version"]

    save_config(config)
    return config


def create_launcher_update_script(update_zip: Path) -> Path:
    update_zip = Path(update_zip).resolve()
    if not update_zip.exists():
        raise UpdateError(f"Архив обновления не найден: {update_zip}")

    script = ROOT / "apply_launcher_update.cmd"
    root = ROOT.resolve()

    content = f'''@echo off
chcp 65001 >nul
title StoneLight Launcher Update

echo StoneLight Launcher updater
echo.
echo Launcher folder:
echo {root}
echo.
echo Update archive:
echo {update_zip}
echo.
echo Waiting for launcher to close...
timeout /t 3 /nobreak >nul

set "ROOT={root}"
set "ZIP={update_zip}"
set "TMP=%TEMP%\\StoneLightLauncher_update_%RANDOM%%RANDOM%"

if exist "%TMP%" rmdir /s /q "%TMP%"
mkdir "%TMP%"

powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Force -LiteralPath '%ZIP%' -DestinationPath '%TMP%'"
if errorlevel 1 (
  echo Failed to unpack update archive.
  pause
  exit /b 1
)

set "SRC="
for /d %%D in ("%TMP%\\StoneLightLauncher*") do (
  set "SRC=%%D"
  goto found_src
)
:found_src

if not defined SRC set "SRC=%TMP%"

echo.
echo Copying files...
robocopy "%SRC%" "%ROOT%" /MIR /XD ".git" "data" "__pycache__" ".venv" "venv" "env" /XF "accounts.json" "user_settings.json" "instances.json" "*.log" "*.zip" "apply_launcher_update.cmd"
set "RC=%ERRORLEVEL%"

if %RC% GEQ 8 (
  echo.
  echo Update failed. Robocopy code: %RC%
  pause
  exit /b %RC%
)

echo.
echo Update applied successfully.

if exist "%ROOT%\\StoneLightLauncher.cmd" (
  start "" "%ROOT%\\StoneLightLauncher.cmd"
) else if exist "%ROOT%\\StoneLightLauncher.bat" (
  start "" "%ROOT%\\StoneLightLauncher.bat"
) else (
  start "" python "%ROOT%\\launcher_gui.py"
)

exit /b 0
'''
    script.write_text(content, encoding="utf-8")
    return script


def run_update_script_and_exit(script: Path):
    script = Path(script).resolve()
    subprocess.Popen(["cmd", "/c", "start", "", str(script)], cwd=str(ROOT), shell=False)
    os._exit(0)
