from __future__ import annotations

import json
import mimetypes
import base64
import os
import shutil
import socket
import subprocess
import sys
import time
import threading
import hashlib
import traceback
import urllib.parse
import urllib.request
import uuid
import webbrowser
import zipfile
from pathlib import Path
from io import BytesIO
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable

from app_paths import app_root
from i18n import set_language, tr
from accounts import (
    add_or_update_microsoft_account,
    add_or_update_offline_account,
    delete_account as delete_saved_account,
    find_account_by_id,
    get_selected_account,
    has_licensed_account,
    load_accounts,
    refresh_microsoft_account,
    save_accounts,
)
from instances import (
    default_official_instance,
    ensure_unique_instance_name,
    normalize_instance,
    slugify_instance_name,
    validate_instance_name,
)
from launcher_core import (
    LauncherCore,
    RUNNING_GAME_LOCK,
    RUNNING_GAME_PROCESSES,
    get_console_key_for_instance,
    get_loader_versions,
    get_minecraft_versions,
    load_user_settings,
    normalize_global_launch_settings,
    normalize_loader_version_for_install,
    recommended_java_major_for_minecraft,
    save_user_settings,
)
from updater import (
    apply_official_modpack_update_to_config,
    check_launcher_update,
    check_official_modpack_update,
    create_launcher_update_script,
    download_launcher_update,
)


ROOT = app_root()

try:
    from PIL import Image
except Exception:  # Pillow is optional at runtime; full preview still works.
    Image = None

CONFIG_PATH = ROOT / "config.json"
INSTANCES_PATH = ROOT / "instances.json"
ACCOUNTS_PATH = ROOT / "accounts.json"
USER_SETTINGS_PATH = ROOT / "user_settings.json"
LOG_PATH = ROOT / "data" / "launcher.log"

ALLOWED_LOADERS = {"vanilla", "fabric", "forge", "quilt", "neoforge"}
ALLOWED_JAVA_PRESETS = {
    "auto", "global", "java8", "java16", "java17", "java21", "java25", "manual"
}

TOGGLEABLE_FOLDER_SUFFIXES = {
    "mods": (".jar", ".jar.disabled"),
    "resourcepacks": (".zip", ".zip.disabled"),
    "shaderpacks": (".zip", ".zip.disabled"),
}

SCREENSHOT_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}

MODRINTH_PROJECT_TYPES = {"mod", "resourcepack", "shader", "modpack"}
MODRINTH_INSTALL_FOLDERS = {
    "mod": "mods",
    "resourcepack": "resourcepacks",
    "shader": "shaderpacks",
}
MODRINTH_ALLOWED_SUFFIXES = {
    "mod": (".jar",),
    "resourcepack": (".zip",),
    "shader": (".zip",),
    "modpack": (".mrpack",),
}

MODRINTH_FILTER_LAYOUT = {
    "mod": ["game_version", "loader", "category"],
    "resourcepack": ["category", "feature", "resolution", "game_version"],
    "shader": ["category", "feature", "performance_impact", "loader"],
    "modpack": ["category", "environment", "game_version", "loader"],
}
MODRINTH_ENVIRONMENT_OPTIONS = [
    {"id": "client", "label": "Client"},
    {"id": "server", "label": "Server"},
    {"id": "both", "label": "Client + Server"},
]
MODRINTH_FALLBACK_LOADERS = [
    {"id": "fabric", "label": "Fabric"},
    {"id": "forge", "label": "Forge"},
    {"id": "neoforge", "label": "NeoForge"},
    {"id": "quilt", "label": "Quilt"},
]
MODRINTH_SHADER_LOADERS = [
    {"id": "iris", "label": "Iris"},
    {"id": "optifine", "label": "OptiFine"},
    {"id": "canvas", "label": "Canvas"},
    {"id": "vanilla", "label": "Vanilla"},
]

CURSEFORGE_CLASS_IDS = {
    "mod": 6,
    "resourcepack": 12,
    "modpack": 4471,
    "shader": 6552,
}
CURSEFORGE_SORT_FIELDS = {
    "relevancy": 1,
    "popularity": 2,
    "lastUpdated": 3,
    "name": 4,
    "author": 5,
    "totalDownloads": 6,
    "category": 7,
    "gameVersion": 8,
}
CURSEFORGE_PROJECT_TYPES = {"mod", "resourcepack", "shader", "modpack"}

INSTANCE_ICON_PACK = [
    {
        "id": "vanilla",
        "label": "Vanilla",
        "category": "type",
        "url": "assets/instance_icons/vanilla.svg",
        "terms": "vanilla classic survival grass"
    },
    {
        "id": "modded",
        "label": "Modded",
        "category": "type",
        "url": "assets/instance_icons/modded.svg",
        "terms": "modded mods custom pack puzzle"
    },
    {
        "id": "tech",
        "label": "Tech",
        "category": "type",
        "url": "assets/instance_icons/tech.svg",
        "terms": "technology automation redstone machines"
    },
    {
        "id": "magic",
        "label": "Magic",
        "category": "type",
        "url": "assets/instance_icons/magic.svg",
        "terms": "magic spells fantasy portal"
    },
    {
        "id": "rpg",
        "label": "RPG",
        "category": "type",
        "url": "assets/instance_icons/rpg.svg",
        "terms": "roleplay classes fantasy quest"
    },
    {
        "id": "adventure",
        "label": "Adventure",
        "category": "type",
        "url": "assets/instance_icons/adventure.svg",
        "terms": "adventure exploration map"
    },
    {
        "id": "building",
        "label": "Building",
        "category": "type",
        "url": "assets/instance_icons/building.svg",
        "terms": "building creative base architecture"
    },
    {
        "id": "pvp",
        "label": "PvP",
        "category": "type",
        "url": "assets/instance_icons/pvp.svg",
        "terms": "pvp combat sword arena"
    },
    {
        "id": "hardcore",
        "label": "Hardcore",
        "category": "type",
        "url": "assets/instance_icons/hardcore.svg",
        "terms": "hardcore survival heart"
    },
    {
        "id": "creative",
        "label": "Creative",
        "category": "type",
        "url": "assets/instance_icons/creative.svg",
        "terms": "creative build blocks"
    },
    {
        "id": "skyblock",
        "label": "SkyBlock",
        "category": "type",
        "url": "assets/instance_icons/skyblock.svg",
        "terms": "skyblock island void"
    },
    {
        "id": "oneblock",
        "label": "OneBlock",
        "category": "type",
        "url": "assets/instance_icons/oneblock.svg",
        "terms": "oneblock island challenge"
    },
    {
        "id": "cobblemon",
        "label": "Cobblemon",
        "category": "type",
        "url": "assets/instance_icons/cobblemon.svg",
        "terms": "cobblemon pixelmon creatures"
    },
    {
        "id": "create",
        "label": "Create",
        "category": "type",
        "url": "assets/instance_icons/create.svg",
        "terms": "create cog gears mechanics"
    },
    {
        "id": "quest",
        "label": "Quest",
        "category": "type",
        "url": "assets/instance_icons/quest.svg",
        "terms": "quest book story tasks"
    },
    {
        "id": "performance",
        "label": "Performance",
        "category": "type",
        "url": "assets/instance_icons/performance.svg",
        "terms": "performance fps optimization"
    },
    {
        "id": "shaders",
        "label": "Shaders",
        "category": "type",
        "url": "assets/instance_icons/shaders.svg",
        "terms": "shaders lighting visuals"
    },
    {
        "id": "testing",
        "label": "Testing",
        "category": "type",
        "url": "assets/instance_icons/testing.svg",
        "terms": "testing dev beta experimental"
    },
    {
        "id": "old_versions",
        "label": "Old versions",
        "category": "type",
        "url": "assets/instance_icons/old_versions.svg",
        "terms": "old versions legacy classic"
    },
    {
        "id": "snapshots",
        "label": "Snapshots",
        "category": "type",
        "url": "assets/instance_icons/snapshots.svg",
        "terms": "snapshots preview beta"
    },
    {
        "id": "grass",
        "label": "Grass",
        "category": "biome",
        "url": "assets/instance_icons/grass.svg",
        "terms": "grass overworld biome vanilla"
    },
    {
        "id": "cave",
        "label": "Cave",
        "category": "biome",
        "url": "assets/instance_icons/cave.svg",
        "terms": "cave mining underground"
    },
    {
        "id": "deep_dark",
        "label": "Deep Dark",
        "category": "biome",
        "url": "assets/instance_icons/deep_dark.svg",
        "terms": "deep dark warden sculk"
    },
    {
        "id": "jungle",
        "label": "Jungle",
        "category": "biome",
        "url": "assets/instance_icons/jungle.svg",
        "terms": "jungle trees vines"
    },
    {
        "id": "cherry",
        "label": "Cherry Grove",
        "category": "biome",
        "url": "assets/instance_icons/cherry.svg",
        "terms": "cherry grove pink blossom"
    },
    {
        "id": "swamp",
        "label": "Swamp",
        "category": "biome",
        "url": "assets/instance_icons/swamp.svg",
        "terms": "swamp mud water"
    },
    {
        "id": "mountain",
        "label": "Mountain",
        "category": "biome",
        "url": "assets/instance_icons/mountain.svg",
        "terms": "mountain peaks cliffs"
    },
    {
        "id": "village",
        "label": "Village",
        "category": "biome",
        "url": "assets/instance_icons/village.svg",
        "terms": "village villagers houses"
    },
    {
        "id": "ocean",
        "label": "Ocean",
        "category": "biome",
        "url": "assets/instance_icons/ocean.svg",
        "terms": "ocean water sea"
    },
    {
        "id": "desert",
        "label": "Desert",
        "category": "biome",
        "url": "assets/instance_icons/desert.svg",
        "terms": "desert sand sun"
    },
    {
        "id": "snow",
        "label": "Snow",
        "category": "biome",
        "url": "assets/instance_icons/snow.svg",
        "terms": "snow ice winter"
    },
    {
        "id": "nether",
        "label": "Nether",
        "category": "biome",
        "url": "assets/instance_icons/nether.svg",
        "terms": "nether fire lava"
    },
    {
        "id": "end",
        "label": "End",
        "category": "biome",
        "url": "assets/instance_icons/end.svg",
        "terms": "end void dragon"
    },
    {
        "id": "fabric",
        "label": "Fabric",
        "category": "loader",
        "url": "assets/instance_icons/fabric.svg",
        "terms": "fabric loader mods"
    },
    {
        "id": "forge",
        "label": "Forge",
        "category": "loader",
        "url": "assets/instance_icons/forge.svg",
        "terms": "forge loader mods"
    },
    {
        "id": "neoforge",
        "label": "NeoForge",
        "category": "loader",
        "url": "assets/instance_icons/neoforge.svg",
        "terms": "neoforge loader mods"
    },
    {
        "id": "quilt",
        "label": "Quilt",
        "category": "loader",
        "url": "assets/instance_icons/quilt.svg",
        "terms": "quilt loader mods"
    },
    {
        "id": "server",
        "label": "Server",
        "category": "utility",
        "url": "assets/instance_icons/server.svg",
        "terms": "server multiplayer network"
    },
    {
        "id": "backup",
        "label": "Backup",
        "category": "utility",
        "url": "assets/instance_icons/backup.svg",
        "terms": "backup save archive"
    },
    {
        "id": "experimental",
        "label": "Experimental",
        "category": "utility",
        "url": "assets/instance_icons/experimental.svg",
        "terms": "experimental lab unstable"
    },
    {
        "id": "repair",
        "label": "Repair",
        "category": "utility",
        "url": "assets/instance_icons/repair.svg",
        "terms": "repair fix tools"
    },
    {
        "id": "favorite",
        "label": "Favorite",
        "category": "utility",
        "url": "assets/instance_icons/favorite.svg",
        "terms": "favorite star pinned"
    },
    {
        "id": "archive",
        "label": "Archive",
        "category": "utility",
        "url": "assets/instance_icons/archive.svg",
        "terms": "archive storage old"
    },
    {
        "id": "local",
        "label": "Local",
        "category": "utility",
        "url": "assets/instance_icons/local.svg",
        "terms": "local offline desktop"
    },
    {
        "id": "multiplayer",
        "label": "Multiplayer",
        "category": "utility",
        "url": "assets/instance_icons/multiplayer.svg",
        "terms": "multiplayer friends server"
    },
    {
        "id": "cozy",
        "label": "Cozy",
        "category": "atmosphere",
        "url": "assets/instance_icons/cozy.svg",
        "terms": "cozy calm cottage"
    },
    {
        "id": "horror",
        "label": "Horror",
        "category": "atmosphere",
        "url": "assets/instance_icons/horror.svg",
        "terms": "horror dark scary"
    },
    {
        "id": "space",
        "label": "Space",
        "category": "atmosphere",
        "url": "assets/instance_icons/space.svg",
        "terms": "space stars sci-fi"
    },
    {
        "id": "medieval",
        "label": "Medieval",
        "category": "atmosphere",
        "url": "assets/instance_icons/medieval.svg",
        "terms": "medieval castle knights"
    },
    {
        "id": "steampunk",
        "label": "Steampunk",
        "category": "atmosphere",
        "url": "assets/instance_icons/steampunk.svg",
        "terms": "steampunk gears brass"
    },
    {
        "id": "futuristic",
        "label": "Futuristic",
        "category": "atmosphere",
        "url": "assets/instance_icons/futuristic.svg",
        "terms": "futuristic neon sci-fi"
    }
]


class LauncherWebAPI:
    """Safe bridge between the local web shell and the existing Python core.

    Only JSON-friendly values are returned to JavaScript. Microsoft tokens and
    other private account fields never leave Python.
    """

    def __init__(self):
        self.window = None
        self._operation_lock = threading.Lock()
        self._busy = False
        self._busy_action = ""
        self._selected_instance_id = ""
        self._microsoft_login_sessions = {}
        self._microsoft_login_lock = threading.Lock()
        self._modrinth_tags_cache = {}
        self._ensure_web_runtime_state()
        self._load_base_state()

    def bind_window(self, window):
        self.window = window

    def _ensure_web_runtime_state(self):
        """Create an empty first-run state without auto-adding StoneLight."""
        for relative in (
            "data",
            "data/cache",
            "data/instances",
            "data/instance_icons",
        ):
            (ROOT / relative).mkdir(parents=True, exist_ok=True)

        LOG_PATH.touch(exist_ok=True)

        defaults = (
            (INSTANCES_PATH, {"selected_instance_id": "", "instances": []}),
            (ACCOUNTS_PATH, {"selected_account_id": "", "accounts": []}),
            (USER_SETTINGS_PATH, {}),
        )
        for path, payload in defaults:
            if path.exists():
                continue
            path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

        self._append_startup_log("Web runtime state initialized.")

    def _append_startup_log(self, message: str):
        try:
            LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with LOG_PATH.open("a", encoding="utf-8") as handle:
                handle.write(f"[web-ui] {message}\n")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # State loading
    # ------------------------------------------------------------------
    def _load_config(self) -> dict:
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RuntimeError(f"Не удалось прочитать config.json: {exc}") from exc

    def _load_base_state(self):
        self.config = self._load_config()
        self.settings = load_user_settings()
        set_language(self.settings.get("language") or self.config.get("default_language") or "uk")
        data = self._load_instances_optional()
        self._selected_instance_id = (
            self.settings.get("selected_instance_id")
            or data.get("selected_instance_id")
            or ""
        )

    def _load_instances_optional(self) -> dict:
        """Load instances without auto-creating the official StoneLight instance."""
        if not INSTANCES_PATH.exists():
            return {"selected_instance_id": "", "instances": []}

        try:
            raw_data = json.loads(INSTANCES_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {"selected_instance_id": "", "instances": []}

        if not isinstance(raw_data, dict):
            return {"selected_instance_id": "", "instances": []}

        cleaned = []
        seen = set()
        for raw in raw_data.get("instances", []):
            if not isinstance(raw, dict):
                continue

            requested = bool(
                raw.get("installation_requested")
                or raw.get("web_install_requested")
            )

            instance = normalize_instance(raw, self.config)
            if not instance:
                continue

            instance_id = str(instance.get("id") or "")
            if not instance_id or instance_id in seen:
                continue

            if instance_id == "stonelight":
                installed = self._is_instance_installed(instance)
                if (
                    self.config.get("official_instance_optional", True)
                    and self.config.get("ignore_uninstalled_official_placeholder", True)
                    and not installed
                    and not requested
                ):
                    continue
                if requested:
                    instance["installation_requested"] = True

            seen.add(instance_id)
            cleaned.append(instance)

        selected = str(raw_data.get("selected_instance_id") or "")
        if selected not in seen:
            selected = cleaned[0]["id"] if cleaned else ""

        return {"selected_instance_id": selected, "instances": cleaned}

    def _save_instances_optional(self, data: dict):
        INSTANCES_PATH.parent.mkdir(parents=True, exist_ok=True)
        INSTANCES_PATH.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _absolute_path(self, value: str | Path) -> Path:
        path = Path(value)
        if not path.is_absolute():
            path = ROOT / path
        return path.resolve()

    def _is_instance_installed(self, instance: dict) -> bool:
        game_dir = self._absolute_path(instance.get("game_directory") or "")
        versions_dir = game_dir / "versions"
        if not versions_dir.exists():
            return False
        try:
            return any(versions_dir.glob("*/*.json"))
        except OSError:
            return False

    def _instance_is_running(self, instance: dict) -> bool:
        key = get_console_key_for_instance(instance, ROOT)
        with RUNNING_GAME_LOCK:
            process = RUNNING_GAME_PROCESSES.get(key)
            if process and process.poll() is None:
                return True
            if process and process.poll() is not None:
                RUNNING_GAME_PROCESSES.pop(key, None)
        return False

    def _instance_install_state(self, instance: dict) -> dict:
        game_dir = self._absolute_path(instance.get("game_directory") or "")
        return {
            "installed": self._is_instance_installed(instance),
            "running": self._instance_is_running(instance),
            "game_directory_exists": game_dir.exists(),
        }

    def _icon_pack_by_id(self, icon_id: str) -> dict | None:
        icon_id = str(icon_id or "").strip()
        for item in INSTANCE_ICON_PACK:
            if item.get("id") == icon_id:
                return item
        return None

    def _default_icon_id_for_instance(self, instance: dict) -> str:
        if instance.get("official") or instance.get("locked") or instance.get("id") == "stonelight":
            return "stonelight"

        loader = str(instance.get("loader") or "vanilla").lower()
        if loader in {"fabric", "forge", "quilt", "neoforge"}:
            return loader

        version_type = str(instance.get("version_type") or "").lower()
        if version_type == "snapshot":
            return "snapshots"

        name = str(instance.get("name") or "").casefold()
        rules = [
            ("hardcore", "hardcore"),
            ("skyblock", "skyblock"),
            ("oneblock", "oneblock"),
            ("create", "create"),
            ("quest", "quest"),
            ("shader", "shaders"),
            ("pvp", "pvp"),
            ("tech", "tech"),
            ("magic", "magic"),
            ("rpg", "rpg"),
            ("test", "testing"),
            ("dev", "testing"),
            ("old", "old_versions"),
            ("backup", "backup"),
            ("server", "server"),
        ]
        for needle, icon_id in rules:
            if needle in name:
                return icon_id

        return "vanilla"

    def _instance_icon_url(self, instance: dict) -> str:
        icon = str(instance.get("icon") or "").strip()
        icon_id = str(instance.get("icon_pack_id") or "").strip()

        if icon.startswith(("https://", "http://")):
            return icon

        if icon_id == "stonelight" or icon == "assets/stonelight_logo_128.png":
            return "assets/stonelight_logo_128.png"

        item = self._icon_pack_by_id(icon_id) or self._icon_pack_by_id(icon)
        if item:
            return str(item.get("url") or "")

        if icon.startswith("assets/instance_icons/") and icon.endswith(".svg"):
            return icon

        default_id = self._default_icon_id_for_instance(instance)
        item = self._icon_pack_by_id(default_id)
        return str(item.get("url") or "") if item else ""

    def _safe_instance(self, instance: dict) -> dict:
        state = self._instance_install_state(instance)
        return {
            "id": instance.get("id", ""),
            "name": instance.get("name", "Instance"),
            "official": bool(instance.get("official") or instance.get("locked")),
            "locked": bool(instance.get("locked")),
            "minecraft_version": instance.get("minecraft_version", "?"),
            "loader": instance.get("loader", "vanilla"),
            "loader_version": instance.get("loader_version", ""),
            "java_preset": instance.get("java_preset", "auto"),
            "game_directory": instance.get("game_directory", ""),
            "icon": instance.get("icon", ""),
            "icon_pack_id": instance.get("icon_pack_id", ""),
            "icon_url": self._instance_icon_url(instance),
            "source": instance.get("source", {}) if isinstance(instance.get("source", {}), dict) else {},
            "installation_requested": bool(instance.get("installation_requested")),
            "forge_install_mode": instance.get("forge_install_mode", "auto"),
            "server_ip": instance.get("server_ip", ""),
            "ensure_server_in_list": bool(instance.get("ensure_server_in_list", False)),
            **state,
        }

    @staticmethod
    def _safe_account(account: dict) -> dict:
        username = account.get("username") or account.get("display_name") or "Player"
        licensed = account.get("type") == "microsoft"
        helm_name = username if licensed else "Steve"
        return {
            "id": account.get("id", ""),
            "type": account.get("type", "offline"),
            "username": username,
            "display_name": account.get("display_name") or username,
            "licensed": licensed,
            "avatar_url": f"https://crafthead.net/helm/{urllib.parse.quote(helm_name)}",
        }

    def _selected_instance(self) -> dict | None:
        data = self._load_instances_optional()
        selected_id = self._selected_instance_id or data.get("selected_instance_id", "")
        for instance in data.get("instances", []):
            if instance.get("id") == selected_id:
                return instance
        return data.get("instances", [None])[0] if data.get("instances") else None

    def _raw_instance_by_id(self, instance_id: str) -> dict | None:
        data = self._load_instances_optional()
        for instance in data.get("instances", []):
            if instance.get("id") == instance_id:
                return instance
        return None

    def get_instance_editor_data(self, instance_id: str = "") -> dict:
        if not instance_id:
            return {
                "ok": True,
                "mode": "create",
                "instance": {
                    "id": "",
                    "name": "",
                    "locked": False,
                    "official": False,
                    "minecraft_version": self.config.get("minecraft_version", "26.1.2"),
                    "version_type": "release",
                    "loader": "vanilla",
                    "loader_version": "",
                    "java_preset": "auto",
                    "java_executable": "",
                    "game_directory": "",
                },
                "options": self._instance_editor_options(),
            }

        instance = self._raw_instance_by_id(instance_id)
        if not instance:
            return {"ok": False, "error": "Сборка не найдена."}

        safe = self._safe_instance(instance)
        safe.update({
            "version_type": instance.get("version_type", "release"),
            "java_executable": instance.get("java_executable", ""),
        })
        return {
            "ok": True,
            "mode": "edit",
            "instance": safe,
            "options": self._instance_editor_options(),
        }

    def _instance_editor_options(self) -> dict:
        return {
            "loaders": ["vanilla", "fabric", "forge", "quilt", "neoforge"],
            "java_presets": [
                "auto", "global", "java8", "java16", "java17", "java21", "java25", "manual"
            ],
            "version_types": ["release", "snapshot"],
        }

    def get_minecraft_version_options(self, include_snapshots: bool = False) -> dict:
        try:
            versions = get_minecraft_versions(
                include_snapshots=bool(include_snapshots),
                limit=None,
            )
            versions = [str(v) for v in versions if str(v).strip()]
            return {
                "ok": True,
                "versions": versions,
                "count": len(versions),
                "include_snapshots": bool(include_snapshots),
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc), "versions": [], "count": 0}

    def get_loader_version_options(
        self,
        loader: str,
        minecraft_version: str,
        automatic_only: bool = True,
    ) -> dict:
        loader = str(loader or "").strip().lower()
        minecraft_version = str(minecraft_version or "").strip()

        if loader in ("", "vanilla"):
            return {
                "ok": True,
                "loader": "vanilla",
                "minecraft_version": minecraft_version,
                "versions": [],
            }
        if loader not in ALLOWED_LOADERS:
            return {"ok": False, "error": "Неизвестный загрузчик.", "versions": []}
        if not minecraft_version:
            return {
                "ok": False,
                "error": "Сначала выбери версию Minecraft.",
                "versions": [],
            }

        try:
            versions = get_loader_versions(
                loader,
                minecraft_version,
                stable_only=False,
                automatic_only=bool(automatic_only),
            )
            versions = [str(v) for v in versions if str(v).strip()]
            return {
                "ok": True,
                "loader": loader,
                "minecraft_version": minecraft_version,
                "versions": versions,
                "count": len(versions),
                "recommended_java": recommended_java_major_for_minecraft(
                    minecraft_version
                ),
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc), "versions": []}

    def _validate_instance_payload(self, payload: dict, current_id: str = "") -> dict:
        if not isinstance(payload, dict):
            raise ValueError("Некорректные данные сборки.")

        name = str(payload.get("name") or "").strip()
        ok, message = validate_instance_name(name)
        if not ok:
            raise ValueError(message)

        data = self._load_instances_optional()
        ensure_unique_instance_name(data, name, current_id=current_id or None)

        minecraft_version = str(payload.get("minecraft_version") or "").strip()
        if not minecraft_version or len(minecraft_version) > 40:
            raise ValueError("Укажи корректную версию Minecraft.")

        loader = str(payload.get("loader") or "vanilla").strip().lower()
        if loader not in ALLOWED_LOADERS:
            raise ValueError("Неизвестный загрузчик.")

        loader_version = normalize_loader_version_for_install(
            loader,
            minecraft_version,
            str(payload.get("loader_version") or "").strip(),
        )
        if loader == "vanilla":
            loader_version = ""

        version_type = str(payload.get("version_type") or "release").strip().lower()
        if version_type not in {"release", "snapshot"}:
            version_type = "release"

        java_preset = str(payload.get("java_preset") or "auto").strip().lower()
        if java_preset not in ALLOWED_JAVA_PRESETS:
            raise ValueError("Некорректный Java preset.")

        java_executable = str(payload.get("java_executable") or "").strip()
        if java_preset != "manual":
            java_executable = ""

        return {
            "name": name,
            "minecraft_version": minecraft_version,
            "version_type": version_type,
            "loader": loader,
            "loader_version": loader_version,
            "java_preset": java_preset,
            "java_executable": java_executable,
        }

    def _modrinth_api_url(self, path: str, query: dict | None = None) -> str:
        base = str(self.config.get("modrinth_api_base") or "https://api.modrinth.com/v2").rstrip("/")
        url = f"{base}/{str(path).lstrip('/')}"
        if query:
            clean = {key: value for key, value in query.items() if value not in (None, "")}
            if clean:
                url += "?" + urllib.parse.urlencode(clean)
        return url

    def _modrinth_read_json(self, path: str, query: dict | None = None) -> dict | list:
        url = self._modrinth_api_url(path, query)
        headers = {
            "User-Agent": str(self.config.get("modrinth_user_agent") or "StoneLightLauncher/0.6"),
            "Accept": "application/json",
        }
        request = urllib.request.Request(url, headers=headers)
        timeout = int(self.config.get("modrinth_api_timeout_seconds", 45) or 45)
        retries = max(1, int(self.config.get("modrinth_api_retries", 2) or 2))
        last_error: Exception | None = None

        for attempt in range(1, retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except (TimeoutError, socket.timeout) as exc:
                last_error = TimeoutError("Modrinth API не ответил вовремя. Проверь соединение и повтори попытку.")
                self._append_startup_log(f"Modrinth API timeout on attempt {attempt}/{retries}: {exc}")
            except Exception as exc:
                last_error = exc
                self._append_startup_log(f"Modrinth API request failed on attempt {attempt}/{retries}: {exc}")

            if attempt < retries:
                time.sleep(0.8 * attempt)

        raise last_error or TimeoutError("Modrinth API не ответил вовремя. Проверь соединение и повтори попытку.")

    def _normalize_filter_values(self, value) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            raw = [value]
        elif isinstance(value, (list, tuple, set)):
            raw = list(value)
        else:
            raw = [str(value)]
        result = []
        for item in raw:
            item = str(item or "").strip()
            if item and item not in result:
                result.append(item)
        return result

    def _modrinth_filter_value(self, filters: dict, key: str, fallback: str = "") -> str:
        if not isinstance(filters, dict):
            return fallback
        value = str(filters.get(key) or "").strip()
        return value or fallback

    def _add_category_facet_group(self, facets: list[list[str]], values) -> None:
        clean = self._normalize_filter_values(values)
        if clean:
            facets.append([f"categories:{value}" for value in clean])

    def _modrinth_facets(self, project_type: str, instance: dict | None, filters: dict | None = None) -> str:
        filters = filters or {}
        facets: list[list[str]] = [[f"project_type:{project_type}"]]

        instance_mc = str(instance.get("minecraft_version") or "").strip() if instance else ""
        instance_loader = str(instance.get("loader") or "vanilla").strip().lower() if instance else "vanilla"

        mc_version = self._modrinth_filter_value(filters, "game_version", instance_mc)
        loader = self._modrinth_filter_value(filters, "loader", instance_loader).lower()

        if mc_version:
            facets.append([f"versions:{mc_version}"])

        if project_type in {"mod", "modpack"} and loader and loader != "vanilla":
            facets.append([f"categories:{loader}"])
        elif project_type == "shader" and loader:
            facets.append([f"categories:{loader}"])

        for key in ("category", "feature", "resolution", "performance_impact"):
            self._add_category_facet_group(facets, filters.get(key) if isinstance(filters, dict) else [])

        if project_type == "modpack":
            environment = self._modrinth_filter_value(filters, "environment", "client").lower()
            if environment == "server":
                facets.append(["server_side:required", "server_side:optional"])
            elif environment == "both":
                facets.append(["client_side:required", "client_side:optional"])
                facets.append(["server_side:required", "server_side:optional"])
            else:
                facets.append(["client_side:required", "client_side:optional"])

        return json.dumps(facets, separators=(",", ":"))

    def _modrinth_tag_cache_get(self, key: str):
        cache = getattr(self, "_modrinth_tags_cache", {})
        item = cache.get(key)
        if not item:
            return None
        created_at, value = item
        if time.time() - float(created_at or 0) > 3600:
            return None
        return value

    def _modrinth_tag_cache_set(self, key: str, value):
        if not hasattr(self, "_modrinth_tags_cache"):
            self._modrinth_tags_cache = {}
        self._modrinth_tags_cache[key] = (time.time(), value)
        return value

    def _modrinth_category_tags(self) -> list[dict]:
        cached = self._modrinth_tag_cache_get("categories")
        if cached is not None:
            return cached
        try:
            data = self._modrinth_read_json("tag/category")
            if isinstance(data, list):
                return self._modrinth_tag_cache_set("categories", data)
        except Exception as exc:
            self._append_startup_log(f"Modrinth category tags failed: {exc}")
        return self._modrinth_tag_cache_set("categories", [])

    def _modrinth_loader_tags(self) -> list[dict]:
        cached = self._modrinth_tag_cache_get("loaders")
        if cached is not None:
            return cached
        try:
            data = self._modrinth_read_json("tag/loader")
            if isinstance(data, list):
                return self._modrinth_tag_cache_set("loaders", data)
        except Exception as exc:
            self._append_startup_log(f"Modrinth loader tags failed: {exc}")
        return self._modrinth_tag_cache_set("loaders", [])

    def _modrinth_game_version_tags(self) -> list[dict]:
        cached = self._modrinth_tag_cache_get("game_versions")
        if cached is not None:
            return cached
        try:
            data = self._modrinth_read_json("tag/game_version")
            if isinstance(data, list):
                return self._modrinth_tag_cache_set("game_versions", data)
        except Exception as exc:
            self._append_startup_log(f"Modrinth game version tags failed: {exc}")
        return self._modrinth_tag_cache_set("game_versions", [])

    @staticmethod
    def _tag_label(tag: dict) -> str:
        return str(tag.get("name") or tag.get("display_name") or tag.get("id") or "").strip()

    @staticmethod
    def _tag_id(tag: dict) -> str:
        return str(tag.get("name") or tag.get("id") or tag.get("version") or "").strip()

    def _category_filter_key(self, tag: dict) -> str:
        header = str(tag.get("header") or "").strip().lower().replace("-", " ").replace("_", " ")
        name = str(tag.get("name") or "").strip().lower()

        if "resolution" in header:
            return "resolution"
        if "performance" in header or "impact" in header:
            return "performance_impact"
        if "feature" in header:
            return "feature"
        if "loader" in header:
            return "loader"
        if header in {"category", "categories", "content", ""}:
            return "category"

        # Modrinth occasionally groups tags under human-readable headers.
        # Unknown headers are treated as normal categories rather than hidden.
        if name in {"iris", "optifine", "canvas"}:
            return "loader"
        return "category"

    def _modrinth_category_choices(self, project_type: str, key: str) -> list[dict]:
        project_type = str(project_type or "").strip().lower()
        choices = []
        seen = set()
        for tag in self._modrinth_category_tags():
            if str(tag.get("project_type") or "").lower() != project_type:
                continue
            if self._category_filter_key(tag) != key:
                continue
            tag_id = self._tag_id(tag)
            if not tag_id or tag_id in seen:
                continue
            seen.add(tag_id)
            choices.append({
                "id": tag_id,
                "label": self._tag_label(tag) or tag_id,
                "header": tag.get("header") or "",
            })
        choices.sort(key=lambda item: item["label"].casefold())
        return choices

    def _modrinth_loader_choices(self, project_type: str, instance: dict | None) -> list[dict]:
        project_type = str(project_type or "").strip().lower()
        instance_loader = str(instance.get("loader") or "vanilla").strip().lower() if instance else "vanilla"

        if project_type == "shader":
            dynamic = self._modrinth_category_choices("shader", "loader")
            fallback = MODRINTH_SHADER_LOADERS
            # Vanilla is not a usable shader loader. Keep "Any", then real shader loaders.
            source = [{"id": "", "label": "Any"}, *(dynamic or fallback)]
        else:
            dynamic = []
            for tag in self._modrinth_loader_tags():
                loader_id = self._tag_id(tag)
                if not loader_id:
                    continue
                if loader_id in {"fabric", "forge", "neoforge", "quilt"}:
                    dynamic.append({"id": loader_id, "label": self._tag_label(tag) or loader_id})
            source = dynamic or MODRINTH_FALLBACK_LOADERS

        # Vanilla is not applicable as a loader filter for mods, shaders or modpacks.
        source = [item for item in source if str(item.get("id") or "").strip().lower() != "vanilla"]

        seen = set()
        result = []
        for item in source:
            item_id = str(item.get("id") or "").strip()
            # Empty id is allowed only for shader "Any"; otherwise skip empty values.
            if item_id == "" and project_type == "shader":
                if item_id not in seen:
                    seen.add(item_id)
                    result.append({"id": item_id, "label": str(item.get("label") or "Any")})
                continue
            if not item_id or item_id in seen:
                continue
            seen.add(item_id)
            result.append({"id": item_id, "label": str(item.get("label") or item_id)})
        return result

    def _modrinth_game_version_choices(self, instance: dict | None, include_snapshots: bool = False) -> list[dict]:
        selected = str(instance.get("minecraft_version") or "").strip() if instance else ""
        choices = []
        seen = set()

        if selected:
            choices.append({"id": selected, "label": selected, "version_type": "selected"})
            seen.add(selected)

        for tag in self._modrinth_game_version_tags():
            version = self._tag_id(tag)
            if not version or version in seen:
                continue
            version_type = str(tag.get("version_type") or tag.get("type") or "").lower()
            if not include_snapshots and version_type and version_type != "release":
                continue
            label = version
            if include_snapshots and version_type and version_type != "release":
                label = f"{version} ({version_type})"
            choices.append({"id": version, "label": label, "version_type": version_type or "release"})
            seen.add(version)
            if len(choices) >= (360 if include_snapshots else 180):
                break

        return choices

    def _filter_section(self, key: str, label: str, choices: list[dict], control: str, default_value: str = "") -> dict:
        return {
            "key": key,
            "label": label,
            "control": control,
            "default": default_value,
            "choices": choices,
        }

    def get_modrinth_filter_options(self, payload: dict | None = None) -> dict:
        payload = payload or {}
        project_type = str(payload.get("project_type") or "mod").strip().lower()
        instance_id = str(payload.get("instance_id") or "").strip()
        filters = payload.get("filters") if isinstance(payload.get("filters"), dict) else {}
        include_snapshots = bool(payload.get("include_snapshots"))

        if project_type not in MODRINTH_PROJECT_TYPES:
            project_type = "mod"

        instance = self._instance_by_id_or_selected(instance_id) if instance_id else self._selected_instance()
        if not instance:
            return {"ok": False, "error": "Сборка не выбрана."}

        instance_mc = str(instance.get("minecraft_version") or "").strip()
        instance_loader = str(instance.get("loader") or "vanilla").strip().lower()

        sections = []
        for key in MODRINTH_FILTER_LAYOUT.get(project_type, []):
            if key == "game_version":
                sections.append(self._filter_section(
                    key, "Game version", self._modrinth_game_version_choices(instance, include_snapshots), "select", instance_mc
                ))
            elif key == "loader":
                loader_choices = self._modrinth_loader_choices(project_type, instance)
                choice_ids = {str(item.get("id") or "") for item in loader_choices}
                default_loader = instance_loader if project_type != "shader" and instance_loader in choice_ids else ""
                sections.append(self._filter_section(
                    key, "Loader", loader_choices, "select", default_loader
                ))
            elif key == "environment":
                sections.append(self._filter_section(
                    key, "Environment", MODRINTH_ENVIRONMENT_OPTIONS, "select", "client"
                ))
            elif key in {"category", "feature", "resolution", "performance_impact"}:
                sections.append(self._filter_section(
                    key, key, self._modrinth_category_choices(project_type, key), "chips", ""
                ))

        return {
            "ok": True,
            "project_type": project_type,
            "instance": self._safe_instance(instance),
            "sections": sections,
        }

    def _modrinth_project_url(self, project_type: str, slug: str) -> str:
        project_type = str(project_type or "").strip().lower()
        slug = str(slug or "").strip()
        path = {
            "mod": "mod",
            "resourcepack": "resourcepack",
            "shader": "shader",
            "modpack": "modpack",
        }.get(project_type, "project")
        if not slug:
            return "https://modrinth.com"
        return f"https://modrinth.com/{path}/{urllib.parse.quote(slug, safe='')}"

    def _safe_modrinth_hit(self, hit: dict) -> dict:
        icon_url = hit.get("icon_url") or ""
        categories = hit.get("categories") or []
        loaders = [
            item for item in categories
            if str(item).lower() in {"fabric", "forge", "quilt", "neoforge", "liteloader", "rift"}
        ]

        return {
            "project_id": hit.get("project_id") or hit.get("project_id") or "",
            "slug": hit.get("slug") or "",
            "title": hit.get("title") or hit.get("slug") or "Modrinth project",
            "description": hit.get("description") or "",
            "project_type": hit.get("project_type") or "",
            "project_url": self._modrinth_project_url(hit.get("project_type") or "", hit.get("slug") or ""),
            "icon_url": icon_url,
            "downloads": int(hit.get("downloads") or 0),
            "follows": int(hit.get("follows") or 0),
            "date_modified": hit.get("date_modified") or "",
            "latest_version": hit.get("latest_version") or "",
            "client_side": hit.get("client_side") or "",
            "server_side": hit.get("server_side") or "",
            "categories": categories[:12],
            "loaders": loaders,
        }

    def search_modrinth(self, payload: dict | None = None) -> dict:
        payload = payload or {}
        query = str(payload.get("query") or "").strip()
        project_type = str(payload.get("project_type") or "mod").strip().lower()
        index = str(payload.get("index") or "relevance").strip().lower()
        instance_id = str(payload.get("instance_id") or "").strip()
        filters = payload.get("filters") if isinstance(payload.get("filters"), dict) else {}
        try:
            limit = int(payload.get("limit") or 24)
        except (TypeError, ValueError):
            limit = 24
        try:
            offset = int(payload.get("offset") or 0)
        except (TypeError, ValueError):
            offset = 0
        limit = max(1, min(24, limit))
        offset = max(0, offset)

        if project_type not in MODRINTH_PROJECT_TYPES:
            project_type = "mod"
        if index not in {"relevance", "downloads", "follows", "updated", "newest"}:
            index = "relevance"

        instance = self._instance_by_id_or_selected(instance_id) if instance_id else self._selected_instance()
        if not instance:
            return {"ok": False, "error": "Сборка не выбрана.", "hits": []}

        facets = self._modrinth_facets(project_type, instance, filters)

        try:
            data = self._modrinth_read_json(
                "search",
                {
                    "query": query,
                    "facets": facets,
                    "index": index,
                    "limit": str(limit),
                    "offset": str(offset),
                },
            )
            hits = data.get("hits") if isinstance(data, dict) else []
            total_hits = int(data.get("total_hits") or len(hits or [])) if isinstance(data, dict) else len(hits or [])
            return {
                "ok": True,
                "query": query,
                "project_type": project_type,
                "index": index,
                "filters": filters,
                "instance": self._safe_instance(instance) if instance else None,
                "hits": [self._safe_modrinth_hit(hit) for hit in (hits or [])],
                "total_hits": total_hits,
                "offset": offset,
                "limit": limit,
                "page": (offset // limit) + 1 if limit else 1,
                "total_pages": max(1, (total_hits + limit - 1) // limit) if limit else 1,
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc), "hits": []}

    def _modrinth_versions_for_instance(self, project_id: str, project_type: str, instance: dict) -> list[dict]:
        mc_version = str(instance.get("minecraft_version") or "").strip()
        loader = str(instance.get("loader") or "vanilla").strip().lower()

        query = {}
        if mc_version:
            query["game_versions"] = json.dumps([mc_version], separators=(",", ":"))

        if project_type == "mod" and loader != "vanilla":
            query["loaders"] = json.dumps([loader], separators=(",", ":"))
        elif project_type == "modpack" and loader != "vanilla":
            query["loaders"] = json.dumps([loader], separators=(",", ":"))

        versions = self._modrinth_read_json(f"project/{urllib.parse.quote(project_id, safe="")}/version", query)
        return versions if isinstance(versions, list) else []

    def _choose_modrinth_file(self, version: dict, project_type: str) -> dict | None:
        allowed = MODRINTH_ALLOWED_SUFFIXES.get(project_type, ())
        files = version.get("files") or []
        primary = [item for item in files if item.get("primary")]
        ordered = primary + [item for item in files if item not in primary]

        for file_info in ordered:
            filename = str(file_info.get("filename") or "").strip()
            url = str(file_info.get("url") or "").strip()
            if not filename or not url:
                continue
            if allowed and not filename.lower().endswith(allowed):
                continue
            return file_info
        return None

    def _download_modrinth_file(self, file_info: dict, target: Path) -> None:
        url = str(file_info.get("url") or "").strip()
        if not url:
            raise ValueError("У файла Modrinth нет ссылки для скачивания.")

        headers = {
            "User-Agent": str(self.config.get("modrinth_user_agent") or "StoneLightLauncher/0.6"),
            "Accept": "*/*",
        }
        request = urllib.request.Request(url, headers=headers)

        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".download")
        timeout = int(self.config.get("modrinth_download_timeout_seconds", 180) or 180)
        retries = max(1, int(self.config.get("modrinth_download_retries", 3) or 3))
        chunk_size = max(64 * 1024, int(self.config.get("modrinth_download_chunk_kb", 512) or 512) * 1024)

        last_error: Exception | None = None

        for attempt in range(1, retries + 1):
            try:
                if tmp.exists():
                    tmp.unlink()

                attempt_suffix = f" ({attempt}/{retries})" if retries > 1 else ""
                self._emit("status", {
                    "busy": True,
                    "message": f"Скачиваю проект Modrinth...{attempt_suffix}",
                    "progress": 0,
                })

                with urllib.request.urlopen(request, timeout=timeout) as response, tmp.open("wb") as fh:
                    total_raw = response.headers.get("Content-Length") or response.headers.get("content-length") or "0"
                    try:
                        total = int(total_raw)
                    except ValueError:
                        total = 0

                    downloaded = 0
                    last_progress_percent = -1

                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break

                        fh.write(chunk)
                        downloaded += len(chunk)

                        if total > 0:
                            progress = max(0.0, min(0.98, downloaded / total))
                            percent = int(progress * 100)
                            # Do not flood WebView with too many events.
                            if percent >= last_progress_percent + 5 or percent == 98:
                                last_progress_percent = percent
                                self._emit("status", {
                                    "busy": True,
                                    "message": f"Скачиваю проект Modrinth... {percent}%",
                                    "progress": progress,
                                })

                if not tmp.exists() or tmp.stat().st_size <= 0:
                    raise ValueError("Modrinth скачал пустой файл.")

                hashes = file_info.get("hashes") or {}
                expected_sha1 = hashes.get("sha1")
                if expected_sha1:
                    digest = hashlib.sha1(tmp.read_bytes()).hexdigest()
                    if digest.lower() != str(expected_sha1).lower():
                        raise ValueError("SHA1 файла Modrinth не совпал.")

                if target.exists():
                    target.unlink()
                tmp.replace(target)
                return

            except (TimeoutError, socket.timeout) as exc:
                last_error = TimeoutError("Превышено время ожидания загрузки файла Modrinth.") 
                self._append_startup_log(f"Modrinth download timeout on attempt {attempt}/{retries}: {exc}")
            except Exception as exc:
                last_error = exc
                self._append_startup_log(f"Modrinth download failed on attempt {attempt}/{retries}: {exc}")
            finally:
                if tmp.exists():
                    try:
                        tmp.unlink()
                    except Exception:
                        pass

            if attempt < retries:
                time.sleep(1.2 * attempt)

        raise ValueError(f"Не удалось скачать файл Modrinth после {retries} попыток. Последняя ошибка: {last_error}")

    def _safe_relative_game_path(self, game_dir: Path, relative_path: str) -> Path:
        value = str(relative_path or "").replace("\\", "/").strip("/")
        if not value or value.startswith("/") or "\x00" in value:
            raise ValueError("Некорректный путь файла в модпаке.")
        parts = Path(value).parts
        if any(part in {"", ".", ".."} for part in parts):
            raise ValueError("Некорректный путь файла в модпаке.")
        target = (game_dir / Path(*parts)).resolve()
        target.relative_to(game_dir.resolve())
        return target

    def _modrinth_cache_path(self, project_id: str, version_id: str, filename: str) -> Path:
        safe_project = slugify_instance_name(project_id or "project")
        safe_version = slugify_instance_name(version_id or "version")
        safe_name = Path(str(filename or "download")).name
        return ROOT / "data" / "cache" / "modrinth" / safe_project / safe_version / safe_name

    def _modrinth_version_minecraft(self, version: dict) -> str:
        versions = version.get("game_versions") or []
        for value in versions:
            if str(value).strip():
                return str(value).strip()
        return ""

    def _modrinth_loader_from_dependencies(self, dependencies: dict) -> tuple[str, str]:
        dependencies = dependencies or {}
        if "fabric-loader" in dependencies:
            return "fabric", str(dependencies.get("fabric-loader") or "")
        if "quilt-loader" in dependencies:
            return "quilt", str(dependencies.get("quilt-loader") or "")
        if "neoforge" in dependencies:
            return "neoforge", str(dependencies.get("neoforge") or "")
        if "forge" in dependencies:
            return "forge", str(dependencies.get("forge") or "")
        return "vanilla", ""

    def _modrinth_target_label(self, instance: dict) -> str:
        loader = str(instance.get("loader") or "vanilla").strip().lower()
        mc_version = str(instance.get("minecraft_version") or "?").strip() or "?"
        return f"{loader} {mc_version}"

    def _verify_mrpack_matches_instance(self, index_data: dict, version: dict, target: dict) -> tuple[str, str, str]:
        dependencies = index_data.get("dependencies") or {}
        pack_mc = str(dependencies.get("minecraft") or self._modrinth_version_minecraft(version) or "").strip()
        if not pack_mc:
            raise ValueError("В Modrinth-модпаке не указана версия Minecraft.")

        pack_loader, pack_loader_version = self._modrinth_loader_from_dependencies(dependencies)
        target_mc = str(target.get("minecraft_version") or "").strip()
        target_loader = str(target.get("loader") or "vanilla").strip().lower()

        if target_mc and pack_mc != target_mc:
            raise ValueError(
                f"Modrinth-модпак не совпадает с выбранной сборкой: нужен Minecraft {target_mc}, "
                f"а найден Minecraft {pack_mc}."
            )

        if pack_loader != target_loader:
            raise ValueError(
                f"Modrinth-модпак не совпадает с выбранной сборкой: нужен loader {target_loader}, "
                f"а найден loader {pack_loader}."
            )

        return pack_mc, pack_loader, pack_loader_version

    def _normalize_mrpack_loader_version(self, loader: str, minecraft_version: str, loader_version: str) -> str:
        loader = (loader or "vanilla").lower()
        loader_version = str(loader_version or "").strip()
        minecraft_version = str(minecraft_version or "").strip()

        if loader == "forge" and loader_version and minecraft_version and not loader_version.startswith(minecraft_version + "-"):
            return f"{minecraft_version}-{loader_version}"
        return loader_version

    def _create_modrinth_instance_record(self, data: dict, project: dict, version: dict, index_data: dict, file_info: dict) -> dict:
        dependencies = index_data.get("dependencies") or {}
        minecraft_version = str(dependencies.get("minecraft") or self._modrinth_version_minecraft(version) or "").strip()
        if not minecraft_version:
            raise ValueError("В Modrinth-модпаке не указана версия Minecraft.")

        loader, loader_version = self._modrinth_loader_from_dependencies(dependencies)
        loader_version = self._normalize_mrpack_loader_version(loader, minecraft_version, loader_version)

        base_name = str(index_data.get("name") or project.get("title") or project.get("slug") or "Modrinth Pack").strip()
        if len(base_name) > 32:
            base_name = base_name[:32].rstrip(" ._-")
        ok, _ = validate_instance_name(base_name)
        if not ok:
            base_name = str(project.get("slug") or "Modrinth Pack").replace("-", " ").strip() or "Modrinth Pack"
            if len(base_name) > 32:
                base_name = base_name[:32].rstrip(" ._-")

        slug = slugify_instance_name(base_name)
        existing_ids = {str(item.get("id") or "") for item in data.get("instances", [])}
        existing_names = {str(item.get("name") or "").strip().casefold() for item in data.get("instances", [])}

        instance_id = slug
        name = base_name
        suffix = 2
        while instance_id in existing_ids or name.casefold() in existing_names:
            tail = f" {suffix}"
            name = (base_name[: max(1, 32 - len(tail))].rstrip(" ._-") + tail).strip()
            instance_id = f"{slug}_{suffix}"
            suffix += 1

        source = {
            "type": "modrinth_modpack",
            "project_id": project.get("id") or "",
            "slug": project.get("slug") or "",
            "title": project.get("title") or name,
            "version_id": version.get("id") or "",
            "version_number": version.get("version_number") or "",
            "file_name": file_info.get("filename") or "",
            "installed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        raw = {
            "id": instance_id,
            "name": name,
            "locked": False,
            "official": False,
            "game_directory": f"data/instances/{instance_id}/.minecraft",
            "minecraft_version": minecraft_version,
            "version_type": "release",
            "loader": loader,
            "loader_version": loader_version,
            "java_preset": "auto",
            "java_executable": "",
            "ram_mb": int(self.config.get("default_ram_mb", 4096)),
            "forge_install_mode": "auto",
            "install_modpack": False,
            "modpack_url": "",
            "modpack_sha256": "",
            "server_ip": "",
            "server_port": "25565",
            "ensure_server_in_list": False,
            "server_list_name": name,
            "icon": self._instance_icon_url({"loader": loader, "name": name, "official": False}),
            "icon_pack_id": loader if loader in {"fabric", "forge", "quilt", "neoforge"} else "modded",
            "source": source,
        }

        normalized = normalize_instance(raw, self.config)
        if not normalized:
            raise ValueError("Не удалось создать сборку из Modrinth-модпака.")
        normalized["source"] = source
        return normalized

    def _extract_mrpack_overrides(self, archive_path: Path, game_dir: Path) -> int:
        copied = 0
        prefixes = ("overrides/", "client-overrides/")
        with zipfile.ZipFile(archive_path) as zf:
            for info in zf.infolist():
                name = info.filename.replace("\\", "/")
                if info.is_dir():
                    continue

                prefix = next((item for item in prefixes if name.startswith(item)), "")
                if not prefix:
                    continue

                relative = name[len(prefix):]
                if not relative:
                    continue

                target = self._safe_relative_game_path(game_dir, relative)
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
                copied += 1
        return copied

    def _read_mrpack_index(self, archive_path: Path) -> dict:
        with zipfile.ZipFile(archive_path) as zf:
            try:
                with zf.open("modrinth.index.json") as fh:
                    data = json.loads(fh.read().decode("utf-8"))
            except KeyError as exc:
                raise ValueError("В .mrpack не найден modrinth.index.json.") from exc

        if not isinstance(data, dict):
            raise ValueError("Некорректный modrinth.index.json.")
        if not isinstance(data.get("files", []), list):
            raise ValueError("Некорректный список файлов в modrinth.index.json.")
        return data

    @staticmethod
    def _normalize_mrpack_relative_path(path_value: str) -> str:
        clean = str(path_value or "").strip().replace("\\", "/")
        while clean.startswith("./"):
            clean = clean[2:]
        return clean.strip("/")

    def _mrpack_managed_entries(self, index_data: dict) -> list[dict]:
        entries: list[dict] = []
        seen = set()
        for entry in index_data.get("files") or []:
            if not isinstance(entry, dict):
                continue
            env = entry.get("env") or {}
            if str(env.get("client") or "required").lower() == "unsupported":
                continue

            relative_path = self._normalize_mrpack_relative_path(entry.get("path") or "")
            if not relative_path or relative_path in seen:
                continue

            hashes = entry.get("hashes") or {}
            entries.append({
                "path": relative_path,
                "sha1": str(hashes.get("sha1") or "").lower(),
                "sha512": str(hashes.get("sha512") or "").lower(),
            })
            seen.add(relative_path)
        return entries

    def _read_modrinth_sources_data(self, instance: dict) -> dict:
        path = self._modrinth_sources_path(instance)
        try:
            data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _prune_removed_modpack_files(self, instance: dict, new_index_data: dict) -> dict:
        """Delete files removed from the new .mrpack only when we can prove they
        were installed by the previous Modrinth modpack version and were not
        modified by the user. Overrides are intentionally not tracked/pruned.
        """
        data = self._read_modrinth_sources_data(instance)
        old_modpack = data.get("modpack") if isinstance(data.get("modpack"), dict) else {}
        old_entries = old_modpack.get("managed_files") if isinstance(old_modpack, dict) else []
        if not isinstance(old_entries, list) or not old_entries:
            return {
                "deleted_files": 0,
                "skipped_modified": 0,
                "skipped_missing": 0,
                "skipped_untracked": 0,
                "deleted": [],
            }

        new_paths = {item["path"] for item in self._mrpack_managed_entries(new_index_data) if item.get("path")}
        game_dir = self._instance_game_dir(instance)
        deleted: list[str] = []
        skipped_modified = 0
        skipped_missing = 0
        skipped_untracked = 0

        for item in old_entries:
            if not isinstance(item, dict):
                continue
            relative_path = self._normalize_mrpack_relative_path(item.get("path") or "")
            if not relative_path or relative_path in new_paths:
                continue

            expected_sha1 = str(item.get("sha1") or "").strip().lower()
            # No old hash means we cannot prove the file is still launcher-owned.
            if not expected_sha1:
                skipped_untracked += 1
                continue

            try:
                target = self._safe_relative_game_path(game_dir, relative_path)
            except Exception:
                skipped_untracked += 1
                continue

            if not target.exists():
                skipped_missing += 1
                continue
            if not target.is_file():
                skipped_untracked += 1
                continue

            try:
                current_sha1 = hashlib.sha1(target.read_bytes()).hexdigest().lower()
            except Exception:
                skipped_modified += 1
                continue

            if current_sha1 != expected_sha1:
                skipped_modified += 1
                continue

            try:
                target.unlink()
                deleted.append(relative_path)
            except Exception:
                skipped_modified += 1

        if deleted:
            self._append_startup_log(
                "Modrinth smart prune removed files: " + ", ".join(deleted[:20])
                + ("..." if len(deleted) > 20 else "")
            )

        return {
            "deleted_files": len(deleted),
            "skipped_modified": skipped_modified,
            "skipped_missing": skipped_missing,
            "skipped_untracked": skipped_untracked,
            "deleted": deleted[:50],
        }

    def _install_mrpack_files(self, archive_path: Path, instance: dict, index_data: dict) -> dict:
        game_dir = self._instance_game_dir(instance)
        game_dir.mkdir(parents=True, exist_ok=True)

        overrides_count = self._extract_mrpack_overrides(archive_path, game_dir)
        files = index_data.get("files") or []
        installed = 0
        skipped = 0
        managed_files: list[dict] = []

        for idx, entry in enumerate(files, start=1):
            env = entry.get("env") or {}
            if str(env.get("client") or "required").lower() == "unsupported":
                skipped += 1
                continue

            downloads = entry.get("downloads") or []
            if not downloads:
                skipped += 1
                continue

            relative_path = self._normalize_mrpack_relative_path(entry.get("path") or "")
            if not relative_path:
                skipped += 1
                continue

            target = self._safe_relative_game_path(game_dir, relative_path)
            target.parent.mkdir(parents=True, exist_ok=True)

            hashes = entry.get("hashes") or {}
            expected_sha1 = str(hashes.get("sha1") or "").lower()
            already_current = False
            if target.exists() and expected_sha1:
                try:
                    already_current = hashlib.sha1(target.read_bytes()).hexdigest().lower() == expected_sha1
                except Exception:
                    already_current = False

            if already_current:
                installed += 1
                managed_files.append({
                    "path": relative_path,
                    "sha1": expected_sha1,
                    "sha512": str(hashes.get("sha512") or "").lower(),
                })
                continue

            filename = Path(relative_path).name
            file_info = {
                "url": str(downloads[0]),
                "filename": filename,
                "hashes": hashes,
            }

            self._emit("status", {
                "busy": True,
                "message": f"Скачиваю файлы модпака Modrinth... {idx}/{len(files)}",
                "progress": 0,
            })
            self._download_modrinth_file(file_info, target)
            installed += 1
            managed_files.append({
                "path": relative_path,
                "sha1": expected_sha1,
                "sha512": str(hashes.get("sha512") or "").lower(),
            })

        return {
            "installed_files": installed,
            "skipped_files": skipped,
            "overrides": overrides_count,
            "managed_files": managed_files,
        }

    def _record_modrinth_modpack_source(self, instance: dict, project: dict, version: dict, file_info: dict, index_data: dict, install_result: dict) -> None:
        path = self._modrinth_sources_path(instance)
        try:
            data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        except Exception:
            data = {}

        data["modpack"] = {
            "source": "modrinth",
            "project_id": project.get("id") or "",
            "slug": project.get("slug") or "",
            "title": project.get("title") or project.get("slug") or instance.get("name", ""),
            "project_type": "modpack",
            "version_id": version.get("id") or "",
            "version_number": version.get("version_number") or "",
            "file_name": file_info.get("filename") or "",
            "minecraft_version": instance.get("minecraft_version") or "",
            "loader": instance.get("loader") or "",
            "loader_version": instance.get("loader_version") or "",
            "installed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "installed_files": int(install_result.get("installed_files") or 0),
            "skipped_files": int(install_result.get("skipped_files") or 0),
            "overrides": int(install_result.get("overrides") or 0),
            "smart_prune": install_result.get("smart_prune", {}),
            "managed_files": install_result.get("managed_files", []),
        }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _update_instance_from_modrinth_modpack(
        self,
        target: dict,
        project: dict,
        version: dict,
        index_data: dict,
        file_info: dict,
    ) -> dict:
        dependencies = index_data.get("dependencies") or {}
        minecraft_version = str(dependencies.get("minecraft") or self._modrinth_version_minecraft(version) or "").strip()
        if not minecraft_version:
            raise ValueError("В Modrinth-модпаке не указана версия Minecraft.")

        loader, loader_version = self._modrinth_loader_from_dependencies(dependencies)
        loader_version = self._normalize_mrpack_loader_version(loader, minecraft_version, loader_version)

        source = {
            "type": "modrinth_modpack",
            "project_id": project.get("id") or "",
            "slug": project.get("slug") or "",
            "title": project.get("title") or target.get("name", ""),
            "version_id": version.get("id") or "",
            "version_number": version.get("version_number") or "",
            "file_name": file_info.get("filename") or "",
            "installed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        target.update({
            "minecraft_version": minecraft_version,
            "version_type": "release",
            "loader": loader,
            "loader_version": loader_version,
            "install_modpack": False,
            "modpack_url": "",
            "modpack_sha256": "",
            "source": source,
        })

        icon_url = str(project.get("icon_url") or "").strip()
        if icon_url:
            target["icon"] = icon_url
            target["icon_pack_id"] = "modrinth_modpack"
        else:
            target["icon"] = self._instance_icon_url({"loader": loader, "name": target.get("name", ""), "official": False})
            target["icon_pack_id"] = loader if loader in {"fabric", "forge", "quilt", "neoforge"} else "modded"

        return target

    def _install_modrinth_modpack_project(self, instance_id: str, project_id: str, filters: dict | None = None) -> dict:
        data = self._load_instances_optional()
        target = next(
            (item for item in data.get("instances", []) if item.get("id") == instance_id),
            None,
        )
        if not target:
            raise ValueError("Сборка не выбрана.")
        if target.get("locked") or target.get("official"):
            raise ValueError("Modrinth-модпак нельзя установить поверх официальной сборки.")

        project = self._modrinth_read_json(f"project/{urllib.parse.quote(project_id, safe='')}")
        if not isinstance(project, dict):
            raise ValueError("Не удалось прочитать проект Modrinth.")
        if project.get("project_type") != "modpack":
            raise ValueError("Выбранный проект Modrinth не является модпаком.")

        filters = filters or {}
        target_mc = str(target.get("minecraft_version") or "").strip()
        target_loader = str(target.get("loader") or "vanilla").strip().lower()
        selected_mc = self._modrinth_filter_value(filters, "game_version", target_mc)
        selected_loader = self._modrinth_filter_value(filters, "loader", target_loader).lower()

        if not selected_mc:
            raise ValueError("У выбранной сборки не указана версия Minecraft.")

        version_target = {**target, "minecraft_version": selected_mc, "loader": selected_loader}
        versions = self._modrinth_versions_for_instance(project_id, "modpack", version_target)
        if not isinstance(versions, list) or not versions:
            raise ValueError(
                f"Не найдена версия Modrinth-модпака для выбранных фильтров: {selected_loader} {selected_mc}."
            )

        selected_version = None
        selected_file = None
        index_data = None
        mrpack_path = None

        for version in versions:
            file_info = self._choose_modrinth_file(version, "modpack")
            if not file_info:
                continue

            filename = Path(str(file_info.get("filename") or f"{project_id}.mrpack")).name
            candidate_path = self._modrinth_cache_path(project.get("id") or project_id, version.get("id") or "version", filename)

            self._emit("status", {"busy": True, "message": "Скачиваю Modrinth-модпак...", "progress": 0})
            self._download_modrinth_file(file_info, candidate_path)
            candidate_index = self._read_mrpack_index(candidate_path)

            # API filters should already do this, but .mrpack dependencies are
            # the final source of truth. This prevents installing NeoForge 1.21.x
            # into a Forge 1.19.2 target when a project has multiple variants.
            self._verify_mrpack_matches_instance(candidate_index, version, version_target)

            selected_version = version
            selected_file = file_info
            index_data = candidate_index
            mrpack_path = candidate_path
            break

        if not selected_version or not selected_file or not index_data or not mrpack_path:
            raise ValueError(
                f"В версиях Modrinth-модпака не найден .mrpack файл для выбранных фильтров: {selected_loader} {selected_mc}."
            )

        target = self._update_instance_from_modrinth_modpack(target, project, selected_version, index_data, selected_file)
        normalized = normalize_instance(target, self.config)
        if not normalized:
            raise ValueError("Не удалось обновить выбранную сборку под Modrinth-модпак.")
        normalized["source"] = target.get("source", {})
        normalized["icon"] = target.get("icon", "")
        normalized["icon_pack_id"] = target.get("icon_pack_id", "")

        for idx, item in enumerate(data.get("instances", [])):
            if item.get("id") == instance_id:
                data["instances"][idx] = normalized
                break

        data["selected_instance_id"] = normalized["id"]
        self._save_instances_optional(data)

        self._selected_instance_id = normalized["id"]
        self.settings = load_user_settings()
        self.settings["selected_instance_id"] = normalized["id"]
        save_user_settings(self.settings)

        self._emit("status", {"busy": True, "message": "Устанавливаю Modrinth-модпак в выбранную сборку...", "progress": 0})
        core = self._make_core(normalized)
        core.update_only(self._java_argument(normalized), force_download=False)

        install_result = self._install_mrpack_files(mrpack_path, normalized, index_data)

        self._emit("status", {"busy": True, "message": "Удаляю устаревшие файлы Modrinth-модпака...", "progress": 0.98})
        prune_result = self._prune_removed_modpack_files(normalized, index_data)
        install_result["smart_prune"] = prune_result

        self._record_modrinth_modpack_source(normalized, project, selected_version, selected_file, index_data, install_result)

        self._append_startup_log(
            f"Modrinth modpack installed into instance: {normalized.get('name')} "
            f"({install_result.get('installed_files', 0)} files, "
            f"{prune_result.get('deleted_files', 0)} pruned)"
        )

        self._emit("status", {
            "busy": False,
            "message": "Modrinth-модпак установлен в выбранную сборку.",
            "progress": 1,
        })

        return {
            "ok": True,
            "message": "Modrinth-модпак установлен в выбранную сборку.",
            "target_instance_id": normalized.get("id", ""),
            "state": self.get_app_state(),
            "project": {
                "title": project.get("title") or project.get("slug") or project_id,
                "project_id": project.get("id") or project_id,
                "project_type": "modpack",
                "icon_url": project.get("icon_url") or "",
            },
            "version": {
                "id": selected_version.get("id") or "",
                "number": selected_version.get("version_number") or "",
            },
            **install_result,
        }

    def _modrinth_modpack_source_info(self, instance: dict) -> dict:
        source = instance.get("source", {}) if isinstance(instance.get("source", {}), dict) else {}
        if source.get("type") != "modrinth_modpack":
            return {
                "supported": False,
                "source": {},
                "message": "У этой сборки нет связи с Modrinth-модпаком.",
            }

        sources_data = self._read_modrinth_sources_data(instance)
        modpack_data = sources_data.get("modpack") if isinstance(sources_data.get("modpack"), dict) else {}
        managed_files = modpack_data.get("managed_files") if isinstance(modpack_data, dict) else []
        managed_count = len(managed_files) if isinstance(managed_files, list) else 0

        return {
            "supported": True,
            "checked": False,
            "needs_update": False,
            "source": source,
            "current_version_id": source.get("version_id") or "",
            "current_version_number": source.get("version_number") or "",
            "project_id": source.get("project_id") or source.get("slug") or "",
            "title": source.get("title") or "Modrinth modpack",
            "smart_prune_available": managed_count > 0,
            "managed_files": managed_count,
            "message": "Сборка установлена из Modrinth-модпака.",
        }

    def _find_latest_modrinth_modpack_version(self, instance: dict) -> tuple[dict, dict, dict] | None:
        source = instance.get("source", {}) if isinstance(instance.get("source", {}), dict) else {}
        project_id = str(source.get("project_id") or source.get("slug") or "").strip()
        if not project_id:
            raise ValueError("В сборке не сохранён ID проекта Modrinth.")

        project = self._modrinth_read_json(f"project/{urllib.parse.quote(project_id, safe='')}")
        if not isinstance(project, dict):
            raise ValueError("Не удалось прочитать проект Modrinth.")
        if project.get("project_type") != "modpack":
            raise ValueError("Сохранённый проект Modrinth не является модпаком.")

        versions = self._modrinth_versions_for_instance(project_id, "modpack", instance)
        if not versions:
            raise ValueError("Не найдены совместимые версии Modrinth-модпака.")

        for version in versions:
            file_info = self._choose_modrinth_file(version, "modpack")
            if file_info:
                return project, version, file_info

        raise ValueError("В совместимых версиях Modrinth-модпака не найден .mrpack файл.")

    def check_modrinth_modpack_update(self, instance_id: str = "") -> dict:
        instance = self._instance_by_id_or_selected(instance_id)
        if not instance:
            return {"ok": False, "error": "Сборка не выбрана."}

        info = self._modrinth_modpack_source_info(instance)
        if not info.get("supported"):
            return {"ok": True, **info}

        try:
            project, latest_version, file_info = self._find_latest_modrinth_modpack_version(instance)
            source = info.get("source") or {}
            current_id = str(source.get("version_id") or "")
            latest_id = str(latest_version.get("id") or "")
            needs_update = bool(latest_id and latest_id != current_id)

            info.update({
                "ok": True,
                "checked": True,
                "needs_update": needs_update,
                "project_id": project.get("id") or info.get("project_id") or "",
                "slug": project.get("slug") or source.get("slug") or "",
                "title": project.get("title") or source.get("title") or "Modrinth modpack",
                "current_version_id": current_id,
                "current_version_number": source.get("version_number") or "",
                "latest_version_id": latest_id,
                "latest_version_number": latest_version.get("version_number") or "",
                "latest_file_name": file_info.get("filename") or "",
                "message": "Доступно обновление Modrinth-модпака." if needs_update else "Modrinth-модпак уже актуален.",
            })
            return info
        except Exception as exc:
            return {"ok": False, "error": str(exc), **info}

    def apply_modrinth_modpack_update(self, instance_id: str = "") -> dict:
        instance = self._instance_by_id_or_selected(instance_id)
        if not instance:
            return {"ok": False, "error": "Сборка не выбрана."}

        info = self.check_modrinth_modpack_update(instance.get("id", ""))
        if not info.get("ok"):
            return info
        if not info.get("supported"):
            return {"ok": False, "error": "У этой сборки нет связи с Modrinth-модпаком."}
        if not info.get("needs_update"):
            return {
                "ok": True,
                "message": "Modrinth-модпак уже актуален.",
                "update": info,
                "state": self.get_app_state(),
            }

        filters = {
            "game_version": instance.get("minecraft_version") or "",
            "loader": instance.get("loader") or "",
        }
        project_id = info.get("project_id") or (instance.get("source", {}) or {}).get("project_id") or ""
        result = self._install_modrinth_modpack_project(instance.get("id", ""), project_id, filters)
        if result.get("ok"):
            result["message"] = "Modrinth-модпак обновлён."
            target_id = result.get("target_instance_id") or instance.get("id", "")
            result["update"] = self.check_modrinth_modpack_update(target_id)
        return result

    def _modrinth_sources_path(self, instance: dict) -> Path:
        return self._instance_game_dir(instance) / ".stonelight_sources.json"

    def _record_modrinth_source(self, instance: dict, project: dict, version: dict, file_info: dict, folder_key: str, target: Path) -> None:
        path = self._modrinth_sources_path(instance)
        try:
            data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        except Exception:
            data = {}

        modrinth = data.setdefault("modrinth", {})
        projects = modrinth.setdefault("projects", {})
        project_id = str(project.get("id") or project.get("slug") or "")
        projects[project_id] = {
            "source": "modrinth",
            "project_id": project.get("id") or "",
            "slug": project.get("slug") or "",
            "title": project.get("title") or project.get("slug") or target.stem,
            "project_type": project.get("project_type") or "",
            "version_id": version.get("id") or "",
            "version_number": version.get("version_number") or "",
            "folder": folder_key,
            "filename": target.name,
            "url": file_info.get("url") or "",
            "installed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def install_modrinth_project(self, payload: dict | None = None) -> dict:
        payload = payload or {}
        instance_id = str(payload.get("instance_id") or "").strip()
        project_id = str(payload.get("project_id") or payload.get("slug") or "").strip()
        project_type = str(payload.get("project_type") or "mod").strip().lower()
        filters = payload.get("filters") if isinstance(payload.get("filters"), dict) else {}

        if not project_id:
            return {"ok": False, "error": "Проект Modrinth не выбран."}
        if project_type not in MODRINTH_PROJECT_TYPES:
            return {"ok": False, "error": "Некорректный тип проекта Modrinth."}
        if project_type == "modpack":
            if not instance_id:
                return {"ok": False, "error": "Сборка не выбрана."}
            try:
                return self._install_modrinth_modpack_project(instance_id, project_id, filters)
            except Exception as exc:
                self._emit("status", {"busy": False, "message": str(exc), "error": True, "progress": 0})
                return {"ok": False, "error": str(exc)}

        instance = self._instance_by_id_or_selected(instance_id) if instance_id else self._selected_instance()
        if not instance:
            return {"ok": False, "error": "Сборка не выбрана."}

        loader = str(instance.get("loader") or "vanilla").lower()
        if project_type == "mod" and loader == "vanilla":
            return {"ok": False, "error": "Для установки модов нужна сборка с модлоадером."}

        folder_key = MODRINTH_INSTALL_FOLDERS.get(project_type)
        if not folder_key:
            return {"ok": False, "error": "Для этого типа проекта пока нет папки установки."}

        try:
            project = self._modrinth_read_json(f"project/{urllib.parse.quote(project_id, safe="")}")
            if not isinstance(project, dict):
                raise ValueError("Не удалось прочитать проект Modrinth.")

            selected_mc = self._modrinth_filter_value(filters, "game_version", str(instance.get("minecraft_version") or "").strip())
            selected_loader = self._modrinth_filter_value(filters, "loader", str(instance.get("loader") or "vanilla").strip().lower()).lower()
            version_target = {**instance, "minecraft_version": selected_mc, "loader": selected_loader}

            versions = self._modrinth_versions_for_instance(project_id, project_type, version_target)
            if not versions:
                return {
                    "ok": False,
                    "error": "Не найдена совместимая версия для выбранных фильтров.",
                }

            selected_version = None
            selected_file = None
            for version in versions:
                file_info = self._choose_modrinth_file(version, project_type)
                if file_info:
                    selected_version = version
                    selected_file = file_info
                    break

            if not selected_version or not selected_file:
                return {"ok": False, "error": "В совместимых версиях не найден подходящий файл."}

            filename = Path(str(selected_file.get("filename") or "")).name
            folder = self._instance_subfolder(instance, folder_key)
            folder.mkdir(parents=True, exist_ok=True)
            suffixes = MODRINTH_ALLOWED_SUFFIXES.get(project_type, ())
            if suffixes and not filename.lower().endswith(suffixes):
                return {"ok": False, "error": "Файл имеет неподдерживаемый формат."}

            target = self._safe_folder_file(folder, filename)
            self._emit("status", {"busy": True, "message": "Скачиваю проект Modrinth...", "progress": 0})
            self._download_modrinth_file(selected_file, target)
            self._record_modrinth_source(instance, project, selected_version, selected_file, folder_key, target)
            self._append_startup_log(f"Modrinth installed: {project.get('title') or project_id} -> {folder_key}/{target.name}")
            self._emit("status", {"busy": False, "message": "Проект Modrinth установлен.", "progress": 1})

            response = {
                "ok": True,
                "message": "Проект Modrinth установлен.",
                "project": {
                    "title": project.get("title") or project.get("slug") or project_id,
                    "project_id": project.get("id") or project_id,
                    "project_type": project_type,
                },
                "version": {
                    "id": selected_version.get("id") or "",
                    "number": selected_version.get("version_number") or "",
                },
                "filename": target.name,
                "folder": folder_key,
            }


            try:
                response["folder_data"] = self.list_instance_folder(instance.get("id", ""), folder_key)
            except Exception:
                pass

            return response
        except Exception as exc:
            self._emit("status", {"busy": False, "message": str(exc), "error": True, "progress": 0})
            return {"ok": False, "error": str(exc)}

    def open_external_url(self, url: str) -> dict:
        url = str(url or "").strip()
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in {"https", "http"} or not parsed.netloc:
            return {"ok": False, "error": "Некорректная ссылка."}
        try:
            webbrowser.open(url)
            return {"ok": True, "url": url}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def _curseforge_api_key(self) -> str:
        self.settings = load_user_settings()
        return str(self.settings.get("curseforge_api_key") or "").strip()

    def get_curseforge_settings(self) -> dict:
        key = self._curseforge_api_key()
        return {
            "ok": True,
            "has_key": bool(key),
            "masked_key": ("••••" + key[-4:]) if key else "",
            "api_base": self.config.get("curseforge_api_base", "https://api.curseforge.com/v1"),
        }

    def save_curseforge_api_key(self, payload: dict | str | None = None) -> dict:
        if isinstance(payload, dict):
            api_key = str(payload.get("api_key") or "").strip()
        else:
            api_key = str(payload or "").strip()

        self.settings = load_user_settings()
        if api_key:
            self.settings["curseforge_api_key"] = api_key
            message = "CurseForge API key сохранён."
        else:
            self.settings.pop("curseforge_api_key", None)
            message = "CurseForge API key очищен."

        save_user_settings(self.settings)
        return {
            "ok": True,
            "message": message,
            "settings": self.get_curseforge_settings(),
        }

    def _curseforge_api_url(self, path: str, query: dict | None = None) -> str:
        base = str(self.config.get("curseforge_api_base") or "https://api.curseforge.com/v1").rstrip("/")
        url = f"{base}/{str(path).lstrip('/')}"
        if query:
            clean = {key: value for key, value in query.items() if value not in (None, "")}
            if clean:
                url += "?" + urllib.parse.urlencode(clean)
        return url

    def _curseforge_read_json(self, path: str, query: dict | None = None) -> dict:
        api_key = self._curseforge_api_key()
        if not api_key:
            raise ValueError("Для CurseForge нужен Core API key.")

        url = self._curseforge_api_url(path, query)
        headers = {
            "Accept": "application/json",
            "x-api-key": api_key,
            "User-Agent": str(self.config.get("curseforge_user_agent") or "StoneLightLauncher/0.6"),
        }
        request = urllib.request.Request(url, headers=headers)
        timeout = int(self.config.get("curseforge_api_timeout_seconds", 45) or 45)
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def _curseforge_type_to_class_id(self, project_type: str) -> int:
        return int(CURSEFORGE_CLASS_IDS.get(str(project_type or "mod").lower(), 6))

    def _curseforge_project_url(self, project: dict, project_type: str) -> str:
        links = project.get("links") or {}
        website = str(links.get("websiteUrl") or "").strip()
        if website:
            return website
        slug = str(project.get("slug") or project.get("name") or "").strip()
        if not slug:
            return "https://www.curseforge.com/minecraft"
        path = {
            "mod": "mc-mods",
            "resourcepack": "texture-packs",
            "shader": "shaders",
            "modpack": "modpacks",
        }.get(project_type, "mc-mods")
        return f"https://www.curseforge.com/minecraft/{path}/{urllib.parse.quote(slug, safe='')}"

    def _safe_curseforge_hit(self, project: dict, project_type: str) -> dict:
        logo = project.get("logo") or {}
        authors = project.get("authors") or []
        categories = project.get("categories") or []
        latest_files = project.get("latestFilesIndexes") or project.get("latestFiles") or []

        game_versions = []
        loaders = []
        for item in latest_files[:8]:
            gv = item.get("gameVersion") if isinstance(item, dict) else ""
            if gv and gv not in game_versions:
                game_versions.append(gv)
            loader = item.get("modLoader") if isinstance(item, dict) else None
            if loader and str(loader) not in loaders:
                loaders.append(str(loader))

        return {
            "project_id": str(project.get("id") or ""),
            "slug": project.get("slug") or "",
            "title": project.get("name") or project.get("slug") or "CurseForge project",
            "description": project.get("summary") or "",
            "project_type": project_type,
            "project_url": self._curseforge_project_url(project, project_type),
            "icon_url": logo.get("thumbnailUrl") or logo.get("url") or "",
            "downloads": int(project.get("downloadCount") or 0),
            "date_modified": project.get("dateModified") or project.get("dateReleased") or "",
            "authors": [str(item.get("name") or "") for item in authors if isinstance(item, dict) and item.get("name")][:4],
            "categories": [str(item.get("name") or "") for item in categories if isinstance(item, dict) and item.get("name")][:6],
            "game_versions": game_versions[:6],
            "loaders": loaders[:4],
        }

    def search_curseforge(self, payload: dict | None = None) -> dict:
        payload = payload or {}
        query = str(payload.get("query") or "").strip()
        project_type = str(payload.get("project_type") or "mod").strip().lower()
        index = str(payload.get("index") or "relevancy").strip()
        instance_id = str(payload.get("instance_id") or "").strip()

        if project_type not in CURSEFORGE_PROJECT_TYPES:
            project_type = "mod"
        sort_field = CURSEFORGE_SORT_FIELDS.get(index, CURSEFORGE_SORT_FIELDS["relevancy"])

        try:
            page_size = int(payload.get("page_size") or self.config.get("curseforge_page_size", 24) or 24)
        except (TypeError, ValueError):
            page_size = 24
        try:
            index_offset = int(payload.get("offset") or 0)
        except (TypeError, ValueError):
            index_offset = 0
        page_size = max(1, min(24, page_size))
        index_offset = max(0, index_offset)

        instance = self._instance_by_id_or_selected(instance_id) if instance_id else self._selected_instance()
        game_version = str(payload.get("game_version") or (instance or {}).get("minecraft_version") or "").strip()

        params = {
            "gameId": int(self.config.get("curseforge_game_id", 432)),
            "classId": self._curseforge_type_to_class_id(project_type),
            "searchFilter": query,
            "sortField": sort_field,
            "sortOrder": "desc",
            "pageSize": page_size,
            "index": index_offset,
        }
        if game_version:
            params["gameVersion"] = game_version

        try:
            response = self._curseforge_read_json("mods/search", params)
            data = response.get("data") or []
            pagination = response.get("pagination") or {}
            total = int(pagination.get("totalCount") or len(data))
            return {
                "ok": True,
                "query": query,
                "project_type": project_type,
                "index": index,
                "game_version": game_version,
                "instance": self._safe_instance(instance) if instance else None,
                "hits": [self._safe_curseforge_hit(item, project_type) for item in data],
                "total_hits": total,
                "offset": int(pagination.get("index") or index_offset),
                "limit": int(pagination.get("pageSize") or page_size),
                "page": (index_offset // page_size) + 1 if page_size else 1,
                "total_pages": max(1, (total + page_size - 1) // page_size) if page_size else 1,
            }
        except Exception as exc:
            return {
                "ok": False,
                "error": str(exc),
                "missing_key": "API key" in str(exc) or "Core API key" in str(exc),
                "hits": [],
            }

    def get_instance_icon_pack(self, instance_id: str = "") -> dict:
        instance = self._raw_instance_by_id(instance_id) if instance_id else self._selected_instance()
        selected_icon = ""
        if instance:
            selected_icon = str(instance.get("icon_pack_id") or instance.get("icon") or self._default_icon_id_for_instance(instance))
            if selected_icon == "assets/stonelight_logo_128.png":
                selected_icon = "stonelight"
            elif selected_icon.startswith("assets/instance_icons/"):
                selected_icon = Path(selected_icon).stem

        official_item = {
            "id": "stonelight",
            "label": "StoneLight",
            "category": "Official",
            "url": "assets/stonelight_logo_128.png",
            "terms": "official stonelight logo",
        }

        return {
            "ok": True,
            "instance_id": instance.get("id", "") if instance else "",
            "selected_icon": selected_icon,
            "icons": [official_item, *INSTANCE_ICON_PACK],
            "categories": ["All", "Official", "type", "biome", "loader", "utility", "atmosphere"],
        }

    def set_instance_icon(self, instance_id: str, icon_id: str) -> dict:
        if self._busy:
            return {"ok": False, "error": "Дождись завершения текущей операции."}

        icon_id = str(icon_id or "").strip()
        allowed_ids = {"auto", "stonelight"} | {str(item.get("id")) for item in INSTANCE_ICON_PACK}
        if icon_id not in allowed_ids:
            return {"ok": False, "error": "Иконка не найдена."}

        data = self._load_instances_optional()
        target = next(
            (item for item in data.get("instances", []) if item.get("id") == instance_id),
            None,
        )
        if not target:
            return {"ok": False, "error": "Сборка не найдена."}

        if icon_id == "auto":
            target["icon_pack_id"] = ""
            target["icon"] = ""
            saved_icon = self._default_icon_id_for_instance(target)
        elif icon_id == "stonelight":
            target["icon_pack_id"] = "stonelight"
            target["icon"] = "assets/stonelight_logo_128.png"
            saved_icon = "stonelight"
        else:
            item = self._icon_pack_by_id(icon_id)
            target["icon_pack_id"] = icon_id
            target["icon"] = str(item.get("url") or "")
            saved_icon = icon_id

        self._save_instances_optional(data)
        self._append_startup_log(f"Instance icon updated: {instance_id} -> {saved_icon}")
        return {
            "ok": True,
            "message": "Иконка сборки обновлена.",
            "state": self.get_app_state(),
        }

    def create_instance(self, payload: dict) -> dict:
        if self._busy:
            return {"ok": False, "error": "Дождись завершения текущей операции."}

        try:
            values = self._validate_instance_payload(payload)
            data = self._load_instances_optional()

            slug = slugify_instance_name(values["name"])
            instance_id = slug
            existing_ids = {str(item.get("id") or "") for item in data.get("instances", [])}
            suffix = 2
            while instance_id in existing_ids:
                instance_id = f"{slug}_{suffix}"
                suffix += 1

            raw = {
                "id": instance_id,
                "name": values["name"],
                "locked": False,
                "official": False,
                "game_directory": f"data/instances/{slug}/.minecraft",
                "minecraft_version": values["minecraft_version"],
                "version_type": values["version_type"],
                "loader": values["loader"],
                "loader_version": values["loader_version"],
                "java_preset": values["java_preset"],
                "java_executable": values["java_executable"],
                "ram_mb": int(self.config.get("default_ram_mb", 4096)),
                "forge_install_mode": "auto",
                "install_modpack": False,
                "modpack_url": "",
                "modpack_sha256": "",
                "server_ip": "",
                "server_port": "25565",
                "ensure_server_in_list": False,
                "server_list_name": values["name"],
                "icon": self._instance_icon_url({"loader": values["loader"], "official": False}),
                "icon_pack_id": values["loader"] if values["loader"] in {"fabric", "forge", "quilt", "neoforge"} else "vanilla",
            }

            normalized = normalize_instance(raw, self.config)
            if not normalized:
                raise ValueError("Не удалось создать сборку.")

            data.setdefault("instances", []).append(normalized)
            data["selected_instance_id"] = instance_id
            self._save_instances_optional(data)

            self._selected_instance_id = instance_id
            self.settings = load_user_settings()
            self.settings["selected_instance_id"] = instance_id
            save_user_settings(self.settings)
            self._append_startup_log(f"Instance created: {values['name']} ({instance_id})")

            return {
                "ok": True,
                "instance_id": instance_id,
                "state": self.get_app_state(),
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def update_instance(self, instance_id: str, payload: dict) -> dict:
        if self._busy:
            return {"ok": False, "error": "Дождись завершения текущей операции."}

        data = self._load_instances_optional()
        target = next(
            (item for item in data.get("instances", []) if item.get("id") == instance_id),
            None,
        )
        if not target:
            return {"ok": False, "error": "Сборка не найдена."}

        try:
            if target.get("locked") or target.get("official"):
                java_preset = str(payload.get("java_preset") or target.get("java_preset") or "auto").lower()
                if java_preset not in ALLOWED_JAVA_PRESETS:
                    raise ValueError("Некорректный Java preset.")
                target["java_preset"] = java_preset
                target["java_executable"] = (
                    str(payload.get("java_executable") or "").strip()
                    if java_preset == "manual"
                    else ""
                )
            else:
                values = self._validate_instance_payload(payload, current_id=instance_id)
                target.update({
                    "name": values["name"],
                    "minecraft_version": values["minecraft_version"],
                    "version_type": values["version_type"],
                    "loader": values["loader"],
                    "loader_version": values["loader_version"],
                    "java_preset": values["java_preset"],
                    "java_executable": values["java_executable"],
                    "server_list_name": target.get("server_list_name") or values["name"],
                })

            self._save_instances_optional(data)
            self._append_startup_log(f"Instance updated: {instance_id}")
            return {"ok": True, "state": self.get_app_state()}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def delete_instance(self, instance_id: str, delete_files: bool = False) -> dict:
        if self._busy:
            return {"ok": False, "error": "Дождись завершения текущей операции."}

        data = self._load_instances_optional()
        target = next(
            (item for item in data.get("instances", []) if item.get("id") == instance_id),
            None,
        )
        if not target:
            return {"ok": False, "error": "Сборка не найдена."}
        if self._instance_is_running(target):
            return {"ok": False, "error": "Сначала останови запущенную сборку."}

        data["instances"] = [
            item for item in data.get("instances", [])
            if item.get("id") != instance_id
        ]
        next_selected = data["instances"][0]["id"] if data["instances"] else ""
        if data.get("selected_instance_id") == instance_id:
            data["selected_instance_id"] = next_selected

        self._save_instances_optional(data)
        self._selected_instance_id = data.get("selected_instance_id", "")
        self.settings = load_user_settings()
        self.settings["selected_instance_id"] = self._selected_instance_id
        save_user_settings(self.settings)

        removed_path = ""
        if delete_files:
            game_dir = self._absolute_path(target.get("game_directory") or "")
            instance_root = game_dir.parent if game_dir.name == ".minecraft" else game_dir
            allowed_root = (ROOT / "data" / "instances").resolve()
            try:
                instance_root.relative_to(allowed_root)
            except ValueError:
                return {
                    "ok": False,
                    "error": "Папка сборки находится вне data/instances и не была удалена.",
                }
            if instance_root.exists():
                shutil.rmtree(instance_root, ignore_errors=False)
                removed_path = str(instance_root)

        self._append_startup_log(f"Instance deleted: {instance_id}")
        return {
            "ok": True,
            "removed_path": removed_path,
            "state": self.get_app_state(),
        }

    def _selected_account(self) -> dict | None:
        accounts = load_accounts()
        selected_id = (
            self.settings.get("selected_account_id")
            or accounts.get("selected_account_id")
            or ""
        )
        return find_account_by_id(accounts, selected_id) or get_selected_account(accounts)

    def get_app_state(self) -> dict:
        self._load_base_state()
        instance_data = self._load_instances_optional()
        safe_instances = [self._safe_instance(instance) for instance in instance_data["instances"]]

        if self._selected_instance_id not in {item["id"] for item in safe_instances}:
            self._selected_instance_id = safe_instances[0]["id"] if safe_instances else ""

        account_data = load_accounts()
        safe_accounts = [self._safe_account(account) for account in account_data.get("accounts", [])]
        selected_account = self._selected_account()
        selected_instance = self._selected_instance()

        global_launch = normalize_global_launch_settings(self.settings, self.config)

        return {
            "launcher": {
                "name": self.config.get("launcher_name", "StoneLight Launcher"),
                "version": self.config.get("launcher_version", "0.6.69"),
                "github_url": self.config.get("github_url", "https://github.com/stonelightmc/StoneLight-Launcher"),
                "bug_report_url": self.config.get("bug_report_url", "https://github.com/stonelightmc/StoneLight-Launcher/issues"),
                "community_site_url": self.config.get("community_site_url", "https://stonelightmc.github.io"),
                "community_discord_url": self.config.get("community_discord_url", "https://discord.gg/GCfnjCsurR"),
                "autocheck_updates": bool(self.config.get("autocheck_updates", True)),
                "update_autocheck_interval_hours": int(self.config.get("update_autocheck_interval_hours", 24) or 24),
            },
            "preferences": {
                "theme": self.settings.get("theme", self.config.get("theme", "dark")),
                "language": self.settings.get("language", self.config.get("language", "en")),
                "available_themes": self.config.get(
                    "available_themes",
                    ["dark", "light", "laconic", "neon", "retro_future"],
                ),
                "available_languages": ["en", "uk", "kk"],
            },
            "instances": safe_instances,
            "selected_instance_id": self._selected_instance_id,
            "selected_instance": self._safe_instance(selected_instance) if selected_instance else None,
            "official_offer": {
                "available": not any(item["official"] for item in safe_instances),
                "name": "StoneLight",
                "minecraft_version": self.config.get("minecraft_version", "26.1.2"),
                "loader": self.config.get("loader", "fabric"),
                "loader_version": self.config.get("fabric_loader_version", "0.19.3"),
            },
            "accounts": safe_accounts,
            "selected_account_id": selected_account.get("id", "") if selected_account else "",
            "selected_account": self._safe_account(selected_account) if selected_account else None,
            "java": {
                "preset": (selected_instance or {}).get("java_preset", "auto"),
                "manual_path": (selected_instance or {}).get("java_executable", ""),
            },
            "global_launch": global_launch,
            "status": {
                "busy": self._busy,
                "action": self._busy_action,
                "message": "Готово.",
                "progress": 0,
            },
            "features": {
                "modrinth": "supported",
                "curseforge": "removed",
                "classic_ui": True,
                "optional_official_instance": True,
            },
        }

    # ------------------------------------------------------------------
    # Instance window / folders / mods
    # ------------------------------------------------------------------
    def _instance_by_id_or_selected(self, instance_id: str = "") -> dict | None:
        if not instance_id:
            return self._selected_instance()
        return self._raw_instance_by_id(instance_id)

    def _instance_game_dir(self, instance: dict) -> Path:
        return self._absolute_path(instance.get("game_directory") or "")

    def _instance_subfolder(self, instance: dict, subfolder: str) -> Path:
        allowed = {
            "root": "",
            "minecraft": "",
            "mods": "mods",
            "resourcepacks": "resourcepacks",
            "shaderpacks": "shaderpacks",
            "saves": "saves",
            "config": "config",
            "logs": "logs",
            "screenshots": "screenshots",
        }
        key = str(subfolder or "root").strip().lower()
        if key not in allowed:
            raise ValueError("Неизвестная папка сборки.")

        game_dir = self._instance_game_dir(instance)
        return game_dir / allowed[key] if allowed[key] else game_dir

    def _safe_mod_filename(self, filename: str) -> str:
        name = Path(str(filename or "")).name
        if not name or name in {".", ".."}:
            raise ValueError("Некорректное имя файла мода.")
        lowered = name.lower()
        if not (lowered.endswith(".jar") or lowered.endswith(".jar.disabled")):
            raise ValueError("Поддерживаются только .jar и .jar.disabled файлы.")
        if "/" in name or "\\" in name:
            raise ValueError("Некорректное имя файла мода.")
        return name

    def _safe_folder_file(self, folder: Path, filename: str) -> Path:
        name = Path(str(filename or "")).name
        if not name or name in {".", ".."}:
            raise ValueError("Некорректное имя файла.")
        target = (folder / name).resolve()
        target.relative_to(folder.resolve())
        return target

    def _screenshot_thumbnail_data_url(self, path: Path, size: int) -> str:
        """Return a small thumbnail data URL for WebView tiles."""
        if not path.is_file() or path.suffix.lower() not in SCREENSHOT_SUFFIXES:
            return ""

        # Prefer real thumbnails to embedding full 5+ MB screenshots in every tile.
        if Image is not None and size <= 64 * 1024 * 1024:
            try:
                with Image.open(path) as image:
                    image.thumbnail((420, 240))
                    if image.mode not in ("RGB", "L"):
                        image = image.convert("RGB")
                    buffer = BytesIO()
                    image.save(buffer, format="JPEG", quality=72, optimize=True)
                encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
                return f"data:image/jpeg;base64,{encoded}"
            except Exception:
                pass

        # Fallback for environments where Pillow is not installed.
        # This keeps average 5 MB screenshots visible, but avoids very large files.
        if 0 < size <= 8 * 1024 * 1024:
            try:
                mime = mimetypes.guess_type(path.name)[0] or "image/png"
                encoded = base64.b64encode(path.read_bytes()).decode("ascii")
                return f"data:{mime};base64,{encoded}"
            except Exception:
                return ""
        return ""

    def _file_row(self, path: Path, folder_key: str) -> dict:
        try:
            stat = path.stat()
            size = stat.st_size
            modified = int(stat.st_mtime)
        except OSError:
            size = 0
            modified = 0

        suffixes = TOGGLEABLE_FOLDER_SUFFIXES.get(folder_key)
        enabled = None
        display_name = path.name
        toggleable = False
        if suffixes and path.is_file():
            active_suffix, disabled_suffix = suffixes
            lower = path.name.lower()
            if lower.endswith(disabled_suffix):
                enabled = False
                toggleable = True
                display_name = path.name[:-len(".disabled")]
            elif lower.endswith(active_suffix):
                enabled = True
                toggleable = True

        is_image = path.suffix.lower() in SCREENSHOT_SUFFIXES
        thumbnail_data_url = ""

        if folder_key == "screenshots" and path.is_file() and is_image:
            thumbnail_data_url = self._screenshot_thumbnail_data_url(path, size)

        return {
            "filename": path.name,
            "display_name": display_name,
            "is_dir": path.is_dir(),
            "size_bytes": size,
            "modified": modified,
            "toggleable": toggleable,
            "enabled": enabled,
            "is_image": is_image,
            "thumbnail_data_url": thumbnail_data_url,
        }

    def list_instance_folder(self, instance_id: str = "", subfolder: str = "mods") -> dict:
        instance = self._instance_by_id_or_selected(instance_id)
        if not instance:
            return {"ok": False, "error": "Сборка не выбрана.", "files": []}
        try:
            folder = self._instance_subfolder(instance, subfolder)
            folder.mkdir(parents=True, exist_ok=True)
            rows = []
            seen = set()
            for item in sorted(folder.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
                if item.name in {".gitkeep"}:
                    continue
                try:
                    resolved = item.resolve()
                except OSError:
                    continue
                key = str(resolved).lower() if os.name == "nt" else str(resolved)
                if key in seen:
                    continue
                seen.add(key)
                rows.append(self._file_row(item, str(subfolder or "").lower()))
            return {
                "ok": True,
                "folder": str(subfolder or ""),
                "path": str(folder),
                "files": rows,
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc), "files": []}

    def set_folder_file_enabled(self, instance_id: str, subfolder: str, filename: str, enabled: bool) -> dict:
        folder_key = str(subfolder or "").strip().lower()
        suffixes = TOGGLEABLE_FOLDER_SUFFIXES.get(folder_key)
        if not suffixes:
            return {"ok": False, "error": "Для этой папки нельзя включать/выключать файлы."}

        instance = self._instance_by_id_or_selected(instance_id)
        if not instance:
            return {"ok": False, "error": "Сборка не выбрана."}

        try:
            folder = self._instance_subfolder(instance, folder_key)
            folder.mkdir(parents=True, exist_ok=True)
            source = self._safe_folder_file(folder, filename)
            if not source.exists() or not source.is_file():
                return {"ok": False, "error": "Файл не найден."}

            active_suffix, disabled_suffix = suffixes
            lower = source.name.lower()
            desired = bool(enabled)
            current_enabled = lower.endswith(active_suffix) and not lower.endswith(disabled_suffix)

            if lower.endswith(disabled_suffix):
                current_enabled = False
            elif lower.endswith(active_suffix):
                current_enabled = True
            else:
                return {"ok": False, "error": "Неподдерживаемый тип файла."}

            if current_enabled == desired:
                return self.list_instance_folder(instance.get("id", ""), folder_key)

            if desired:
                target_name = source.name[:-len(".disabled")]
            else:
                target_name = source.name + ".disabled"

            target = self._safe_folder_file(folder, target_name)
            if target.exists():
                return {"ok": False, "error": f"Файл уже существует: {target.name}"}

            source.rename(target)
            self._append_startup_log(f"Folder item toggled: {source.name} -> {target.name}")
            return self.list_instance_folder(instance.get("id", ""), folder_key)
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def delete_folder_file(self, instance_id: str, subfolder: str, filename: str) -> dict:
        instance = self._instance_by_id_or_selected(instance_id)
        if not instance:
            return {"ok": False, "error": "Сборка не выбрана."}
        try:
            folder_key = str(subfolder or "").strip().lower()
            folder = self._instance_subfolder(instance, folder_key)
            target = self._safe_folder_file(folder, filename)
            if not target.exists() or not target.is_file():
                return {"ok": False, "error": "Файл не найден."}
            target.unlink()
            self._append_startup_log(f"Folder item deleted: {folder_key}/{filename}")
            return self.list_instance_folder(instance.get("id", ""), folder_key)
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def get_screenshot_data(self, instance_id: str, filename: str) -> dict:
        instance = self._instance_by_id_or_selected(instance_id)
        if not instance:
            return {"ok": False, "error": "Сборка не выбрана."}
        try:
            folder = self._instance_subfolder(instance, "screenshots")
            target = self._safe_folder_file(folder, filename)
            if target.suffix.lower() not in SCREENSHOT_SUFFIXES:
                return {"ok": False, "error": "Это не поддерживаемый формат изображения."}
            if not target.exists() or not target.is_file():
                return {"ok": False, "error": "Изображение не найдено."}
            if target.stat().st_size > 16 * 1024 * 1024:
                return {"ok": False, "error": "Файл слишком большой для предпросмотра."}

            mime = mimetypes.guess_type(target.name)[0] or "image/png"
            encoded = base64.b64encode(target.read_bytes()).decode("ascii")
            return {
                "ok": True,
                "filename": target.name,
                "data_url": f"data:{mime};base64,{encoded}",
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def copy_screenshot_path(self, instance_id: str, filename: str) -> dict:
        instance = self._instance_by_id_or_selected(instance_id)
        if not instance:
            return {"ok": False, "error": "Сборка не выбрана."}
        try:
            folder = self._instance_subfolder(instance, "screenshots")
            target = self._safe_folder_file(folder, filename)
            if not target.exists() or not target.is_file():
                return {"ok": False, "error": "Изображение не найдено."}
            # Copy path as text. Copying binary files to OS clipboard is platform-dependent,
            # so a full copy/cut workflow is reserved for a later Windows-specific pass.
            try:
                if os.name == "nt":
                    subprocess.run(
                        ["powershell", "-NoProfile", "-Command", "Set-Clipboard -LiteralPath $args[0]", str(target)],
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                else:
                    subprocess.run(["xclip", "-selection", "clipboard"], input=str(target), text=True, check=False)
            except Exception:
                pass
            return {"ok": True, "path": str(target)}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def _list_instance_mods_raw(self, instance: dict) -> list[dict]:
        mods_dir = self._instance_subfolder(instance, "mods")
        if not mods_dir.exists():
            return []

        rows = []
        for file in sorted(mods_dir.iterdir(), key=lambda p: p.name.lower()):
            if not file.is_file():
                continue
            lowered = file.name.lower()
            if not (lowered.endswith(".jar") or lowered.endswith(".jar.disabled")):
                continue

            enabled = lowered.endswith(".jar")
            display_name = file.name[:-9] if lowered.endswith(".disabled") else file.name
            try:
                stat = file.stat()
                size_bytes = stat.st_size
                modified = int(stat.st_mtime)
            except OSError:
                size_bytes = 0
                modified = 0

            rows.append({
                "filename": file.name,
                "display_name": display_name,
                "enabled": enabled,
                "size_bytes": size_bytes,
                "modified": modified,
            })
        return rows

    def _pack_manifest_path_for_instance(self, instance: dict) -> Path:
        return self._instance_game_dir(instance) / ".stonelight_pack_manifest.json"

    def _legacy_official_manifest_path_for_instance(self, instance: dict) -> Path:
        return self._instance_game_dir(instance) / ".stonelight_official_manifest.json"

    def _official_manifest_path_for_instance(self, instance: dict) -> Path:
        # Backward-compatible alias. New installs use the generic pack manifest.
        return self._pack_manifest_path_for_instance(instance)

    def _read_pack_manifest_for_instance(self, instance: dict) -> tuple[dict, Path | None]:
        for manifest_path in (
            self._pack_manifest_path_for_instance(instance),
            self._legacy_official_manifest_path_for_instance(instance),
        ):
            if not manifest_path.exists():
                continue

            try:
                return json.loads(manifest_path.read_text(encoding="utf-8")), manifest_path
            except Exception:
                return {}, manifest_path

        return {}, None

    def _official_expected_manifest(self, instance: dict) -> dict:
        return {
            "minecraft_version": instance.get("minecraft_version", ""),
            "loader": instance.get("loader", ""),
            "loader_version": instance.get("loader_version", ""),
            # Archive/checksum are kept for technical manifest/debug use, but
            # they are not user-facing update indicators because GitHub Release
            # fallback can legitimately install a different ZIP filename/hash.
            "mods_zip_url": instance.get("modpack_url", ""),
            "mods_zip_sha256": instance.get("modpack_sha256", ""),
            "mods_release_repo": self.config.get("mods_release_repo", ""),
            "mods_release_tag": self.config.get("mods_release_tag", ""),
        }

    def _official_update_status(self, instance: dict) -> dict:
        if not (instance.get("official") or instance.get("id") == "stonelight"):
            return {"official": False, "needs_update": False, "changes": []}

        expected = self._official_expected_manifest(instance)
        installed, manifest_path = self._read_pack_manifest_for_instance(instance)
        manifest_exists = bool(manifest_path and manifest_path.exists())

        installed_flag = self._is_instance_installed(instance)

        # Only show meaningful user-facing changes. Archive URL/checksum/release
        # metadata are too noisy with fallback discovery and should not keep the
        # update banner visible after a successful install.
        labels = {
            "minecraft_version": "Minecraft",
            "loader": "Loader",
            "loader_version": "Loader version",
        }

        # Old installs from versions before the manifest existed should not be
        # displayed as "unknown -> current" when the instance metadata already
        # matches config.json. Treat the current instance metadata as a backfill.
        baseline = installed if manifest_exists else {
            "minecraft_version": instance.get("minecraft_version", ""),
            "loader": instance.get("loader", ""),
            "loader_version": instance.get("loader_version", ""),
        }

        changes = []
        for key, label in labels.items():
            current = str(baseline.get(key, "") or "")
            target = str(expected.get(key, "") or "")
            if current != target:
                changes.append({
                    "key": key,
                    "label": label,
                    "current": current or "unknown",
                    "target": target or "auto",
                })

        needs_update = (not installed_flag) or bool(changes)

        return {
            "official": True,
            "installed": installed_flag,
            "manifest_exists": manifest_exists,
            "needs_update": needs_update,
            "changes": changes,
        }

    def get_instance_window_data(self, instance_id: str = "") -> dict:
        instance = self._instance_by_id_or_selected(instance_id)
        if not instance:
            return {"ok": False, "error": "Сборка не выбрана."}

        folders = []
        for key, label in (
            ("mods", "mods"),
            ("resourcepacks", "resourcepacks"),
            ("shaderpacks", "shaderpacks"),
            ("config", "config"),
            ("saves", "saves"),
            ("logs", "logs"),
            ("screenshots", "screenshots"),
        ):
            try:
                path = self._instance_subfolder(instance, key)
                folders.append({
                    "key": key,
                    "label": label,
                    "path": str(path),
                    "exists": path.exists(),
                })
            except Exception:
                pass

        return {
            "ok": True,
            "instance": self._safe_instance(instance),
            "official_update": self._official_update_status(instance),
            "modrinth_modpack_update": self._modrinth_modpack_source_info(instance),
            "folders": folders,
            "folder_files": {
                key: self.list_instance_folder(instance.get("id", ""), key).get("files", [])
                for key in ("mods", "resourcepacks", "shaderpacks", "screenshots")
            },
            "mods": self._list_instance_mods_raw(instance),
        }

    def open_instance_subfolder(self, instance_id: str = "", subfolder: str = "root") -> dict:
        instance = self._instance_by_id_or_selected(instance_id)
        if not instance:
            return {"ok": False, "error": "Сборка не выбрана."}
        try:
            folder = self._instance_subfolder(instance, subfolder)
            folder.mkdir(parents=True, exist_ok=True)
            return {"ok": self._open_path(folder), "path": str(folder)}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def list_instance_mods(self, instance_id: str = "") -> dict:
        instance = self._instance_by_id_or_selected(instance_id)
        if not instance:
            return {"ok": False, "error": "Сборка не выбрана.", "mods": []}
        try:
            mods_dir = self._instance_subfolder(instance, "mods")
            mods_dir.mkdir(parents=True, exist_ok=True)
            return {
                "ok": True,
                "mods": self._list_instance_mods_raw(instance),
                "path": str(mods_dir),
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc), "mods": []}

    def set_mod_enabled(self, instance_id: str, filename: str, enabled: bool) -> dict:
        instance = self._instance_by_id_or_selected(instance_id)
        if not instance:
            return {"ok": False, "error": "Сборка не выбрана."}

        try:
            mods_dir = self._instance_subfolder(instance, "mods")
            mods_dir.mkdir(parents=True, exist_ok=True)

            safe_name = self._safe_mod_filename(filename)
            source = (mods_dir / safe_name).resolve()
            mods_root = mods_dir.resolve()
            source.relative_to(mods_root)

            if not source.exists() or not source.is_file():
                return {"ok": False, "error": "Файл мода не найден."}

            lowered = source.name.lower()
            currently_enabled = lowered.endswith(".jar")
            desired = bool(enabled)

            if currently_enabled == desired:
                return self.list_instance_mods(instance.get("id", ""))

            if desired:
                if not lowered.endswith(".jar.disabled"):
                    return {"ok": False, "error": "Этот файл нельзя включить как мод."}
                target_name = source.name[:-9]
            else:
                if not lowered.endswith(".jar"):
                    return {"ok": False, "error": "Этот файл нельзя выключить как мод."}
                target_name = source.name + ".disabled"

            target = (mods_dir / target_name).resolve()
            target.relative_to(mods_root)
            if target.exists():
                return {
                    "ok": False,
                    "error": f"Нельзя переименовать: {target.name} уже существует.",
                }

            source.rename(target)
            self._append_startup_log(
                f"Mod {'enabled' if desired else 'disabled'}: {source.name} -> {target.name}"
            )
            return self.list_instance_mods(instance.get("id", ""))
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def delete_instance_mod(self, instance_id: str, filename: str) -> dict:
        instance = self._instance_by_id_or_selected(instance_id)
        if not instance:
            return {"ok": False, "error": "Сборка не выбрана."}

        try:
            mods_dir = self._instance_subfolder(instance, "mods")
            safe_name = self._safe_mod_filename(filename)
            target = (mods_dir / safe_name).resolve()
            mods_root = mods_dir.resolve()
            target.relative_to(mods_root)

            if not target.exists() or not target.is_file():
                return {"ok": False, "error": "Файл мода не найден."}

            target.unlink()
            self._append_startup_log(f"Mod deleted: {safe_name}")
            return self.list_instance_mods(instance.get("id", ""))
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    # ------------------------------------------------------------------
    # Microsoft OAuth for Web UI
    # ------------------------------------------------------------------
    def _microsoft_auth_config(self) -> tuple[str, str, str | None]:
        client_id = (
            self.settings.get("microsoft_client_id")
            or self.config.get("microsoft_client_id")
            or ""
        ).strip()
        redirect_uri = (
            self.settings.get("microsoft_redirect_uri")
            or self.config.get("microsoft_redirect_uri")
            or "http://localhost:8765/callback"
        ).strip()
        client_secret = self.config.get("microsoft_client_secret", "") or None

        if not client_id:
            raise ValueError("Не указан Microsoft Azure App Client ID.")

        self.settings["microsoft_client_id"] = client_id
        self.settings["microsoft_redirect_uri"] = redirect_uri
        save_user_settings(self.settings)

        return client_id, redirect_uri, client_secret

    def _wait_for_microsoft_redirect(self, redirect_uri: str, timeout_seconds: int = 240) -> str:
        parsed = urllib.parse.urlparse(redirect_uri)
        scheme = parsed.scheme or "http"
        host = parsed.hostname or "localhost"
        port = parsed.port or 8765
        path = parsed.path or "/callback"

        if host not in {"localhost", "127.0.0.1"}:
            raise ValueError("Автоперехват Microsoft login поддерживает только localhost redirect URI.")

        received = {"url": "", "error": ""}
        done = threading.Event()

        class CallbackHandler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                return

            def do_GET(self):
                request_path = self.path.split("?", 1)[0]
                if request_path != path:
                    self.send_response(404)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write("StoneLight Launcher callback path mismatch.".encode("utf-8"))
                    return

                received["url"] = f"{scheme}://{host}:{port}{self.path}"

                html = """<!doctype html>
<html lang="uk">
<head><meta charset="utf-8"><title>StoneLight Launcher</title></head>
<body style="font-family: sans-serif; padding: 32px;">
<h2>Вхід завершено</h2>
<p>Можна повернутися в StoneLight Launcher. Це вікно браузера можна закрити.</p>
</body>
</html>"""
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html.encode("utf-8"))
                done.set()

        server = None
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), CallbackHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self._append_startup_log(f"Microsoft callback server started: http://localhost:{port}{path}")

            if not done.wait(timeout_seconds):
                raise TimeoutError("Время ожидания входа Microsoft истекло. Повтори попытку.")

            if not received["url"]:
                raise ValueError("Microsoft callback не вернул redirect URL.")

            return received["url"]
        finally:
            if server:
                try:
                    server.shutdown()
                except Exception:
                    pass
                try:
                    server.server_close()
                except Exception:
                    pass

    def start_microsoft_login(self) -> dict:
        """Start Microsoft OAuth in the browser and return immediately.

        The Web UI polls get_microsoft_login_status(session_id), so the bridge
        call does not block and no classic/Tk window is needed.
        """
        try:
            import minecraft_launcher_lib.microsoft_account as microsoft_account

            client_id, redirect_uri, client_secret = self._microsoft_auth_config()
            parsed = urllib.parse.urlparse(redirect_uri)
            scheme = parsed.scheme or "http"
            host = parsed.hostname or "localhost"
            port = parsed.port or 8765
            path = parsed.path or "/callback"

            if host not in {"localhost", "127.0.0.1"}:
                raise ValueError("Автоперехват Microsoft login поддерживает только localhost redirect URI.")

            login_url, state, code_verifier = microsoft_account.get_secure_login_data(client_id, redirect_uri)
            if self.config.get("microsoft_prompt_select_account", True):
                login_url = self._add_query_params(login_url, prompt="select_account")

            session_id = uuid.uuid4().hex
            session = {
                "id": session_id,
                "status": "waiting",
                "message": "Ожидаю вход Microsoft в браузере...",
                "error": "",
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "state": state,
                "code_verifier": code_verifier,
                "server": None,
                "thread": None,
                "created_at": time.time(),
                "result": None,
            }

            api = self
            done_once = threading.Event()

            class CallbackHandler(BaseHTTPRequestHandler):
                def log_message(self, *_args):
                    return

                def do_GET(self):
                    request_path = self.path.split("?", 1)[0]
                    if request_path != path:
                        self.send_response(404)
                        self.send_header("Content-Type", "text/html; charset=utf-8")
                        self.end_headers()
                        self.wfile.write("StoneLight Launcher callback path mismatch.".encode("utf-8"))
                        return

                    redirected_url = f"{scheme}://{host}:{port}{self.path}"

                    html = """<!doctype html>
<html lang="uk">
<head><meta charset="utf-8"><title>StoneLight Launcher</title></head>
<body style="font-family: sans-serif; padding: 32px;">
<h2>Вхід завершено</h2>
<p>Можна повернутися в StoneLight Launcher. Це вікно браузера можна закрити.</p>
</body>
</html>"""
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(html.encode("utf-8"))

                    if not done_once.is_set():
                        done_once.set()
                        threading.Thread(
                            target=api._complete_microsoft_login_session,
                            args=(session_id, redirected_url),
                            daemon=True,
                        ).start()

            try:
                server = ThreadingHTTPServer(("127.0.0.1", port), CallbackHandler)
            except OSError as exc:
                raise ValueError(
                    f"Не удалось запустить локальный callback-сервер на порту {port}. "
                    f"Возможно, порт занят или заблокирован. Детали: {exc}"
                )

            session["server"] = server
            session["thread"] = threading.Thread(target=server.serve_forever, daemon=True)

            with self._microsoft_login_lock:
                self._microsoft_login_sessions[session_id] = session

            session["thread"].start()
            webbrowser.open(login_url)

            self._append_startup_log(f"Microsoft login started in Web UI: http://localhost:{port}{path}")

            return {
                "ok": True,
                "session_id": session_id,
                "message": "Открыт браузер Microsoft login. Заверши вход в браузере.",
            }
        except Exception as exc:
            self._append_startup_log(f"Microsoft login start failed: {exc}")
            return {"ok": False, "error": str(exc)}

    def _complete_microsoft_login_session(self, session_id: str, redirected_url: str) -> None:
        session = self._microsoft_login_sessions.get(session_id)
        if not session:
            return

        session["status"] = "processing"
        session["message"] = "Получен callback Microsoft. Завершаю вход..."

        try:
            import minecraft_launcher_lib.microsoft_account as microsoft_account

            auth_code = microsoft_account.parse_auth_code_url(redirected_url, session["state"])

            try:
                response = microsoft_account.complete_login(
                    session["client_id"],
                    session["client_secret"],
                    session["redirect_uri"],
                    auth_code,
                    session["code_verifier"],
                )
            except TypeError:
                response = microsoft_account.complete_login(
                    session["client_id"],
                    session["redirect_uri"],
                    auth_code,
                    session["code_verifier"],
                )

            data, message = add_or_update_microsoft_account(response)
            selected_id = data.get("selected_account_id", "")

            self.settings = load_user_settings()
            self.settings["selected_account_id"] = selected_id
            self.settings["microsoft_client_id"] = session["client_id"]
            self.settings["microsoft_redirect_uri"] = session["redirect_uri"]
            save_user_settings(self.settings)

            username = response.get("name", "")
            final_message = f"{message} {username}".strip()
            session["status"] = "done"
            session["message"] = final_message
            session["result"] = {
                "message": final_message,
            }

            self._append_startup_log(final_message)
        except Exception as exc:
            session["status"] = "error"
            session["error"] = str(exc)
            session["message"] = str(exc)
            self._append_startup_log(f"Microsoft login failed: {exc}")
        finally:
            server = session.get("server")
            if server:
                try:
                    server.shutdown()
                except Exception:
                    pass
                try:
                    server.server_close()
                except Exception:
                    pass
                session["server"] = None

    def get_microsoft_login_status(self, session_id: str) -> dict:
        session = self._microsoft_login_sessions.get(session_id)
        if not session:
            return {"ok": False, "error": "Microsoft login session not found."}

        # Timeout stale sessions so the UI does not wait forever.
        if session.get("status") in {"waiting", "processing"} and time.time() - float(session.get("created_at", 0)) > 300:
            session["status"] = "error"
            session["error"] = "Время ожидания входа Microsoft истекло. Повтори попытку."
            server = session.get("server")
            if server:
                try:
                    server.shutdown()
                    server.server_close()
                except Exception:
                    pass
                session["server"] = None

        payload = {
            "ok": True,
            "status": session.get("status", "waiting"),
            "message": session.get("message", ""),
            "error": session.get("error", ""),
        }

        if session.get("status") == "done":
            payload["account_manager"] = self.get_account_manager_data()
            payload["state"] = self.get_app_state()
            payload["message"] = session.get("message", "Лицензионный аккаунт добавлен.")

        return payload

    def add_microsoft_account(self) -> dict:
        try:
            import minecraft_launcher_lib.microsoft_account as microsoft_account

            client_id, redirect_uri, client_secret = self._microsoft_auth_config()

            login_url, state, code_verifier = microsoft_account.get_secure_login_data(client_id, redirect_uri)
            if self.config.get("microsoft_prompt_select_account", True):
                login_url = self._add_query_params(login_url, prompt="select_account")

            webbrowser.open(login_url)
            self._append_startup_log("Microsoft login opened in browser.")

            redirected_url = self._wait_for_microsoft_redirect(redirect_uri)
            auth_code = microsoft_account.parse_auth_code_url(redirected_url, state)

            try:
                response = microsoft_account.complete_login(
                    client_id,
                    client_secret,
                    redirect_uri,
                    auth_code,
                    code_verifier,
                )
            except TypeError:
                response = microsoft_account.complete_login(
                    client_id,
                    redirect_uri,
                    auth_code,
                    code_verifier,
                )

            data, message = add_or_update_microsoft_account(response)
            selected_id = data.get("selected_account_id", "")

            self.settings = load_user_settings()
            self.settings["selected_account_id"] = selected_id
            self.settings["microsoft_client_id"] = client_id
            self.settings["microsoft_redirect_uri"] = redirect_uri
            save_user_settings(self.settings)

            username = response.get("name", "")
            self._append_startup_log(f"{message} {username}".strip())

            return {
                "ok": True,
                "message": f"{message} {username}".strip(),
                "account_manager": self.get_account_manager_data(),
                "state": self.get_app_state(),
            }
        except Exception as exc:
            self._append_startup_log(f"Microsoft login failed: {exc}")
            return {"ok": False, "error": str(exc)}

    @staticmethod
    def _add_query_params(url: str, **params) -> str:
        parsed = urllib.parse.urlparse(url)
        query = dict(urllib.parse.parse_qsl(parsed.query, keep_blank_values=True))
        query.update({key: str(value) for key, value in params.items() if value is not None})
        return urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(query)))

    # ------------------------------------------------------------------
    # Account manager
    # ------------------------------------------------------------------
    def get_account_manager_data(self) -> dict:
        data = load_accounts()
        accounts = [self._safe_account(account) for account in data.get("accounts", [])]
        selected = get_selected_account(data)
        license_exists = has_licensed_account(data)
        return {
            "ok": True,
            "accounts": accounts,
            "selected_account_id": selected.get("id", "") if selected else "",
            "selected_account": self._safe_account(selected) if selected else None,
            "has_licensed_account": license_exists,
            "can_add_offline": license_exists,
        }

    def add_offline_account(self, username: str) -> dict:
        try:
            data, message = add_or_update_offline_account(username)
            selected_id = data.get("selected_account_id", "")

            self.settings = load_user_settings()
            self.settings["selected_account_id"] = selected_id
            save_user_settings(self.settings)

            self._append_startup_log(f"Offline account saved: {username}")
            return {
                "ok": True,
                "message": message,
                "account_manager": self.get_account_manager_data(),
                "state": self.get_app_state(),
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def delete_account(self, account_id: str) -> dict:
        try:
            data, message = delete_saved_account(account_id)
            selected_id = data.get("selected_account_id", "")

            self.settings = load_user_settings()
            self.settings["selected_account_id"] = selected_id
            save_user_settings(self.settings)

            self._append_startup_log(f"Account deleted: {account_id}")
            return {
                "ok": True,
                "message": message,
                "account_manager": self.get_account_manager_data(),
                "state": self.get_app_state(),
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def refresh_selected_account(self) -> dict:
        account = self._selected_account()
        if not account:
            return {"ok": False, "error": "Аккаунт не выбран."}
        if account.get("type") != "microsoft":
            return {"ok": False, "error": "Обновлять можно только Microsoft-аккаунт."}

        try:
            refreshed, message = refresh_microsoft_account(
                account["id"],
                self.config.get("microsoft_client_id", ""),
                self.config.get("microsoft_redirect_uri", ""),
                self.config.get("microsoft_client_secret", ""),
            )
            selected_id = refreshed.get("selected_account_id", "")

            self.settings = load_user_settings()
            self.settings["selected_account_id"] = selected_id
            save_user_settings(self.settings)

            return {
                "ok": True,
                "message": message,
                "account_manager": self.get_account_manager_data(),
                "state": self.get_app_state(),
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    # ------------------------------------------------------------------
    # Selection / preferences
    # ------------------------------------------------------------------
    def select_instance(self, instance_id: str) -> dict:
        data = self._load_instances_optional()
        ids = {instance.get("id") for instance in data.get("instances", [])}
        if instance_id not in ids:
            return {"ok": False, "error": "Сборка не найдена."}

        data["selected_instance_id"] = instance_id
        self._save_instances_optional(data)
        self._selected_instance_id = instance_id
        self.settings = load_user_settings()
        self.settings["selected_instance_id"] = instance_id
        save_user_settings(self.settings)
        return {"ok": True, "state": self.get_app_state()}

    def select_account(self, account_id: str) -> dict:
        data = load_accounts()
        if not find_account_by_id(data, account_id):
            return {"ok": False, "error": "Аккаунт не найден."}

        data["selected_account_id"] = account_id
        save_accounts(data)
        self.settings = load_user_settings()
        self.settings["selected_account_id"] = account_id
        save_user_settings(self.settings)
        return {"ok": True, "state": self.get_app_state()}

    def set_preference(self, key: str, value: str) -> dict:
        allowed = {
            "theme": set(self.config.get("available_themes", [])),
            "language": {"en", "uk", "kk"},
        }
        if key not in allowed or value not in allowed[key]:
            return {"ok": False, "error": "Недопустимое значение настройки."}

        self.settings = load_user_settings()
        self.settings[key] = value
        save_user_settings(self.settings)
        return {"ok": True, "preferences": self.get_app_state()["preferences"]}

    def get_launch_settings_data(self) -> dict:
        self.settings = load_user_settings()
        return {
            "ok": True,
            "settings": normalize_global_launch_settings(self.settings, self.config),
        }

    @staticmethod
    def _optional_int(value, min_value: int, max_value: int, field_name: str) -> int | str:
        text = str(value if value is not None else "").strip()
        if not text:
            return ""
        try:
            number = int(text)
        except ValueError:
            raise ValueError(f"{field_name}: потрібно вказати число.")
        if not (min_value <= number <= max_value):
            raise ValueError(f"{field_name}: допустимий діапазон {min_value}–{max_value}.")
        return number

    def save_launch_settings(self, payload: dict) -> dict:
        try:
            payload = payload or {}
            window_mode = str(payload.get("window_mode") or "unchanged").strip().lower()
            if window_mode not in {"unchanged", "windowed", "fullscreen"}:
                raise ValueError("Некоректний режим вікна.")

            ram_min = self._optional_int(payload.get("ram_min_mb"), 256, 65536, "RAM min")
            ram_max = self._optional_int(payload.get("ram_max_mb"), 1024, 131072, "RAM max")
            if ram_min != "" and ram_max != "" and int(ram_min) > int(ram_max):
                raise ValueError("RAM min не може бути більше RAM max.")

            window_width = self._optional_int(payload.get("window_width"), 320, 7680, "Window width")
            window_height = self._optional_int(payload.get("window_height"), 240, 4320, "Window height")
            if (window_width == "") != (window_height == ""):
                raise ValueError("Для розміру вікна потрібно вказати і ширину, і висоту.")

            render_distance = self._optional_int(payload.get("render_distance"), 2, 64, "Render distance")
            simulation_distance = self._optional_int(payload.get("simulation_distance"), 2, 32, "Simulation distance")
            fps_limit = self._optional_int(payload.get("fps_limit"), 10, 1000, "FPS limit")

            vsync = str(payload.get("vsync") or "unchanged").strip().lower()
            if vsync not in {"unchanged", "on", "off"}:
                raise ValueError("Некоректне значення VSync.")

            graphics = str(payload.get("graphics") or "unchanged").strip().lower()
            if graphics not in {"unchanged", "fast", "fancy", "fabulous"}:
                raise ValueError("Некоректний режим графіки.")

            particles = str(payload.get("particles") or "unchanged").strip().lower()
            if particles not in {"unchanged", "all", "decreased", "minimal"}:
                raise ValueError("Некоректне значення частинок.")

            graphics_profile = str(payload.get("graphics_profile") or "custom").strip().lower()
            if graphics_profile not in {"unchanged", "performance", "balanced", "quality", "custom"}:
                raise ValueError("Некоректний профіль графіки.")

            self.settings = load_user_settings()

            # Java is intentionally per-instance. Clean v0.6.28 temporary keys
            # so the global dialog cannot affect Java selection anymore.
            self.settings.pop("global_java_preset", None)
            self.settings.pop("global_java_executable", None)
            self.settings.pop("java_executable", None)

            if ram_min == "":
                self.settings.pop("ram_min_mb", None)
                self.settings.pop("global_ram_min_mb", None)
            else:
                self.settings["ram_min_mb"] = int(ram_min)

            if ram_max == "":
                self.settings.pop("ram_max_mb", None)
                self.settings.pop("ram_mb", None)
                self.settings.pop("global_ram_max_mb", None)
            else:
                self.settings["ram_max_mb"] = int(ram_max)

            self.settings["window_mode"] = window_mode
            # Remove old fullscreen keys so "unchanged" really means unchanged.
            self.settings.pop("fullscreen", None)
            self.settings.pop("global_fullscreen", None)

            if window_width == "":
                self.settings.pop("window_width", None)
                self.settings.pop("resolution_width", None)
            else:
                self.settings["window_width"] = int(window_width)

            if window_height == "":
                self.settings.pop("window_height", None)
                self.settings.pop("resolution_height", None)
            else:
                self.settings["window_height"] = int(window_height)

            optional_numeric = {
                "render_distance": render_distance,
                "simulation_distance": simulation_distance,
                "fps_limit": fps_limit,
            }
            for key, value in optional_numeric.items():
                if value == "":
                    self.settings.pop(key, None)
                else:
                    self.settings[key] = int(value)

            self.settings["vsync"] = vsync
            self.settings["graphics"] = graphics
            self.settings["particles"] = particles
            self.settings["graphics_profile"] = graphics_profile

            save_user_settings(self.settings)
            return {
                "ok": True,
                "settings": normalize_global_launch_settings(self.settings, self.config),
                "state": self.get_app_state(),
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    # ------------------------------------------------------------------
    # Local desktop actions
    # ------------------------------------------------------------------
    def _open_path(self, path: Path) -> bool:
        path = path.resolve()
        path.mkdir(parents=True, exist_ok=True) if path.suffix == "" else None
        try:
            if os.name == "nt":
                os.startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
            return True
        except Exception:
            return False

    def open_instance_folder(self, instance_id: str = "") -> dict:
        if instance_id:
            self.select_instance(instance_id)
        instance = self._selected_instance()
        if not instance:
            return {"ok": False, "error": "Сборка не выбрана."}
        game_dir = self._absolute_path(instance.get("game_directory") or "")
        game_dir.mkdir(parents=True, exist_ok=True)
        return {"ok": self._open_path(game_dir), "path": str(game_dir)}

    def open_log(self) -> dict:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not LOG_PATH.exists():
            LOG_PATH.write_text("", encoding="utf-8")
        return {"ok": self._open_path(LOG_PATH), "path": str(LOG_PATH)}

    def open_github(self) -> dict:
        url = self.config.get("github_url", "https://github.com/stonelightmc/StoneLight-Launcher")
        webbrowser.open(url)
        return {"ok": True}

    def open_classic_ui(self) -> dict:
        try:
            if getattr(sys, "frozen", False):
                command = [sys.executable, "--classic"]
            else:
                command = [sys.executable, str(ROOT / "StoneLightLauncher.pyw")]
            subprocess.Popen(command, cwd=str(ROOT))
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    # ------------------------------------------------------------------
    # Official instance / launcher operations
    # ------------------------------------------------------------------
    def install_official(self) -> dict:
        data = self._load_instances_optional()
        official = next(
            (instance for instance in data.get("instances", []) if instance.get("id") == "stonelight"),
            None,
        )
        if not official:
            official = default_official_instance(self.config)
            official["installation_requested"] = True
            data.setdefault("instances", []).insert(0, official)
        else:
            official["installation_requested"] = True
        data["selected_instance_id"] = "stonelight"
        self._save_instances_optional(data)
        self._selected_instance_id = "stonelight"
        self.settings = load_user_settings()
        self.settings["selected_instance_id"] = "stonelight"
        save_user_settings(self.settings)
        return self._start_operation("install", official)

    def apply_launcher_update(self) -> dict:
        try:
            info = check_launcher_update(self.config)
            if not info.get("has_update"):
                return {"ok": False, "error": "Обновление лаунчера не найдено.", "launcher": info}

            if not info.get("asset_url"):
                return {"ok": False, "error": "В релизе не найден ZIP-архив обновления лаунчера.", "launcher": info}

            self._emit("status", {"message": "Скачиваю обновление лаунчера...", "busy": True, "action": "launcher_update"})
            update_zip = download_launcher_update(
                info,
                progress_callback=lambda current, total: self._emit(
                    "progress",
                    {
                        "current": current,
                        "total": total,
                        "progress": (current / total) if total else 0,
                    },
                ),
            )
            script = create_launcher_update_script(update_zip)
            self._append_startup_log(f"Launcher update script created: {script}")

            if os.name == "nt":
                subprocess.Popen(["cmd", "/c", "start", "", str(script)], cwd=str(ROOT), shell=False)
            else:
                subprocess.Popen([str(script)], cwd=str(ROOT), shell=False)

            self._emit("status", {"message": "Запущен скрипт обновления лаунчера. Лаунчер закроется.", "busy": False})
            # Give the Web UI a moment to receive the response before closing.
            threading.Timer(0.6, lambda: os._exit(0)).start()
            return {
                "ok": True,
                "message": "Скрипт обновления лаунчера запущен. Лаунчер закроется.",
                "launcher": info,
            }
        except Exception as exc:
            self._emit("status", {"message": str(exc), "busy": False, "error": True})
            return {"ok": False, "error": str(exc)}

    def apply_official_update(self) -> dict:
        try:
            info = check_official_modpack_update(self.config)
            if not info.get("has_update"):
                return {"ok": False, "error": "Обновление официальной сборки не найдено.", "official": info}

            apply_official_modpack_update_to_config(info, self.config)
            self._load_base_state()
            self._append_startup_log("Official modpack config updated from release asset.")

            result = self.install_official()
            result["official"] = info
            result["message"] = "Обновление официальной сборки запущено."
            return result
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def _official_instance_for_update_center(self) -> dict | None:
        return next(
            (
                item for item in self._load_instances_optional().get("instances", [])
                if item.get("id") == "stonelight" or item.get("official")
            ),
            None,
        )

    def _read_official_manifest_for_update_center(self, instance: dict) -> dict:
        if not instance:
            return {}
        manifest, _manifest_path = self._read_pack_manifest_for_instance(instance)
        return manifest

    def _official_cache_asset_path_for_update_center(self, asset_name: str) -> Path | None:
        asset_name = str(asset_name or "").strip()
        if not asset_name:
            return None

        candidates = [
            ROOT / "data" / "cache" / asset_name,
            ROOT / asset_name,
        ]
        for candidate in candidates:
            try:
                if candidate.exists() and candidate.is_file():
                    return candidate
            except OSError:
                continue
        return None

    def _backfill_official_manifest_for_update_center(self, instance: dict, archive_path: Path, info: dict) -> None:
        if not instance or not archive_path:
            return
        try:
            manifest_path = self._official_manifest_path_for_instance(instance)
            manifest_path.parent.mkdir(parents=True, exist_ok=True)

            payload = {
                "manifest_version": 2,
                "pack_type": "official_zip",
                "instance_id": instance.get("id", ""),
                "instance_name": instance.get("name", "StoneLight"),
                "minecraft_version": instance.get("minecraft_version") or self.config.get("minecraft_version", ""),
                "loader": instance.get("loader") or self.config.get("loader", ""),
                "loader_version": instance.get("loader_version") or self.config.get("fabric_loader_version", ""),
                "mods_zip_url": self.config.get("mods_zip_url", ""),
                "mods_zip_sha256": self.config.get("mods_zip_sha256", ""),
                "mods_release_repo": self.config.get("mods_release_repo", ""),
                "mods_release_tag": self.config.get("mods_release_tag", ""),
                "last_archive": archive_path.name,
                "last_archive_sha256": "",
                "backfilled_by": "update_center",
            }

            try:
                from launcher_core import LauncherCore
                core = LauncherCore(instance=instance)
                payload["last_archive_sha256"] = core.sha256_file(archive_path)
            except Exception:
                pass

            manifest_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            self._append_startup_log(f"Official manifest backfilled from cached asset: {archive_path.name}")
        except Exception as exc:
            self._append_startup_log(f"Could not backfill official manifest: {exc}")

    def _official_update_center_info(self) -> dict:
        official_instance = self._official_instance_for_update_center()
        official_installed = bool(
            official_instance and self._is_instance_installed(official_instance)
        )

        if not official_installed:
            return {
                "kind": "official_modpack",
                "installed": False,
                "not_installed": True,
                "has_update": False,
                "message": "Сборка не установлена",
                "repo": self.config.get("official_modpack_update_repo", "stonelightmc/stonelightmc.github.io"),
                "current_url": self.config.get("mods_zip_url", ""),
                "current_minecraft_version": self.config.get("minecraft_version", ""),
                "latest_minecraft_version": "",
                "release_name": "",
                "release_url": "",
                "asset_name": "",
                "asset_url": "",
            }

        info = check_official_modpack_update(self.config)
        info["installed"] = True
        info["not_installed"] = False

        manifest = self._read_official_manifest_for_update_center(official_instance)
        installed_archive = str(manifest.get("last_archive") or "")
        installed_minecraft = str(
            manifest.get("minecraft_version")
            or official_instance.get("minecraft_version")
            or self.config.get("minecraft_version", "")
            or ""
        )

        info["installed_archive_name"] = installed_archive
        info["installed_minecraft_version"] = installed_minecraft
        info["manifest_exists"] = bool(manifest)

        latest_asset = str(info.get("asset_name") or "")
        latest_minecraft = str(info.get("latest_minecraft_version") or "")

        # Important hotfix: after first install through GitHub Releases fallback,
        # config.json may still contain the old direct mods_zip_url, while the
        # actually installed archive recorded in the manifest is already the
        # latest release asset. Do not report an update just because config URL
        # differs from the latest asset URL.
        if latest_asset and installed_archive and latest_asset == installed_archive:
            info["has_update"] = False
            info["update_reason"] = "installed_archive_matches_latest_asset"
        elif latest_asset and not installed_archive:
            # Backward-compatible recovery for installs made by v0.6.34 or older:
            # the official instance is installed, the latest release ZIP is still
            # in the launcher cache, but no manifest was written. Treat that as
            # current and backfill the manifest for future checks.
            cached_asset = self._official_cache_asset_path_for_update_center(latest_asset)
            if cached_asset:
                info["installed_archive_name"] = latest_asset
                info["has_update"] = False
                info["update_reason"] = "latest_asset_present_in_cache"
                self._backfill_official_manifest_for_update_center(official_instance, cached_asset, info)
        elif latest_minecraft and installed_minecraft and latest_minecraft == installed_minecraft and not latest_asset:
            info["has_update"] = False
            info["update_reason"] = "installed_minecraft_matches_latest"

        return info

    def run_action(self, action: str) -> dict:
        action = (action or "").strip().lower()
        if action == "official_install":
            return self.install_official()

        if action == "check_updates":
            try:
                # Launcher updates are independent from the selected instance.
                # Official instance status should also be readable when the user
                # has no instances yet, so this branch must run before the
                # selected-instance guard below.
                return {
                    "ok": True,
                    "launcher": check_launcher_update(self.config),
                    "official": self._official_update_center_info(),
                }
            except Exception as exc:
                return {"ok": False, "error": str(exc)}

        instance = self._selected_instance()
        if not instance:
            return {"ok": False, "error": "Сначала выбери или добавь сборку."}

        if action in {"install", "update", "play", "stop", "forge_repair", "forge_manual", "forge_check"}:
            if action.startswith("forge_") and (instance.get("loader") or "").lower() != "forge":
                return {"ok": False, "error": "Эта команда доступна только для Forge-сборок."}
            return self._start_operation(action, instance)

        return {"ok": False, "error": f"Неизвестное действие: {action}"}

    def _java_argument(self, instance: dict) -> str:
        preset = str(instance.get("java_preset") or "auto").strip().lower()
        if preset == "manual":
            return str(instance.get("java_executable") or "").strip()
        if preset == "global":
            # Global means system Java from the OS/PATH, not a cross-instance
            # launcher-managed Java version. Per-version Java should stay on
            # Auto or explicit per-instance presets.
            return str(self.config.get("java_executable") or "java")
        return preset or "auto"

    def _refresh_account_for_launch(self, account: dict) -> dict:
        if not account or account.get("type") != "microsoft":
            return account
        if not account.get("refresh_token"):
            return account

        client_id = self.config.get("microsoft_client_id", "")
        redirect_uri = self.config.get("microsoft_redirect_uri", "")
        client_secret = self.config.get("microsoft_client_secret", "")
        try:
            refreshed, _ = refresh_microsoft_account(
                account["id"],
                client_id,
                redirect_uri,
                client_secret,
            )
            return get_selected_account(refreshed) or account
        except Exception as exc:
            self._emit("log", {"message": f"Не удалось обновить Microsoft-сессию: {exc}"})
            return account

    def _start_operation(self, action: str, instance: dict) -> dict:
        if action == "stop":
            try:
                core = self._make_core(instance)
                message = core.force_stop_game()
                self._emit("status", {"message": message, "busy": False})
                self._emit("state", self.get_app_state())
                return {"ok": True, "message": message}
            except Exception as exc:
                return {"ok": False, "error": str(exc)}

        with self._operation_lock:
            if self._busy:
                return {
                    "ok": False,
                    "error": f"Уже выполняется задача: {self._busy_action or 'операция'}.",
                }
            self._busy = True
            self._busy_action = action

        thread = threading.Thread(
            target=self._operation_worker,
            args=(action, dict(instance)),
            daemon=True,
        )
        thread.start()
        self._emit(
            "status",
            {
                "message": {
                    "play": "Подготавливаю запуск...",
                    "install": "Устанавливаю сборку...",
                    "update": "Обновляю сборку...",
                    "forge_repair": "Запускаю Forge repair...",
                    "forge_manual": "Запускаю Forge Installer...",
                    "forge_check": "Проверяю Forge...",
                }.get(action, "Выполняю операцию..."),
                "busy": True,
                "action": action,
                "progress": 0,
            },
        )
        return {"ok": True, "started": True, "action": action}

    def _make_core(self, instance: dict) -> LauncherCore:
        return LauncherCore(
            instance=instance,
            log_callback=lambda message: self._emit("log", {"message": message}),
            status_callback=lambda message: self._emit(
                "status",
                {"message": message, "busy": True, "action": self._busy_action},
            ),
            progress_callback=lambda current, total: self._emit(
                "progress",
                {
                    "current": current,
                    "total": total,
                    "progress": (current / total) if total else 0,
                },
            ),
            console_callback=lambda message: self._emit("log", {"message": message}),
        )

    def _operation_worker(self, action: str, instance: dict):
        try:
            core = self._make_core(instance)
            java_argument = self._java_argument(instance)

            if action in {"install", "update"}:
                core.update_only(java_argument, force_download=True)
                result_message = "Сборка установлена/обновлена."
            elif action == "forge_repair":
                core.repair_instance(java_argument)
                result_message = "Repair завершён."
            elif action == "forge_manual":
                core.run_forge_installer_manual(java_argument)
                result_message = "Forge Installer запущен."
            elif action == "forge_check":
                installed = core.check_forge_installed()
                result_message = f"Forge найден: {installed}" if installed else "Forge не найден."
            elif action == "play":
                account = self._selected_account()
                if not account:
                    raise RuntimeError(
                        "Для запуска нужен аккаунт. Добавь его через классический интерфейс."
                    )
                account = self._refresh_account_for_launch(account)
                global_launch = normalize_global_launch_settings(
                    load_user_settings(),
                    self.config,
                )
                core.run_full(
                    account.get("username", "Player"),
                    int(global_launch["ram_max_mb"]),
                    java_argument,
                    force_modpack_download=False,
                    account=account,
                )
                result_message = "Minecraft запущен."
            else:
                raise RuntimeError(f"Операция пока не поддерживается: {action}")

            self._emit(
                "done",
                {"ok": True, "message": result_message, "action": action},
            )
        except Exception as exc:
            self._emit(
                "done",
                {
                    "ok": False,
                    "message": str(exc),
                    "action": action,
                    "details": traceback.format_exc(),
                },
            )
        finally:
            with self._operation_lock:
                self._busy = False
                self._busy_action = ""
            self._emit("state", self.get_app_state())

    # ------------------------------------------------------------------
    # Python -> JavaScript events
    # ------------------------------------------------------------------
    def _localize_value(self, value: Any) -> Any:
        if isinstance(value, str):
            return tr(value)
        if isinstance(value, dict):
            return {key: self._localize_value(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._localize_value(item) for item in value]
        return value

    def _emit(self, event_name: str, payload: Any):
        if not self.window:
            return
        try:
            event_json = json.dumps(event_name, ensure_ascii=False)
            payload_json = json.dumps(self._localize_value(payload), ensure_ascii=False)
            script = (
                "window.StoneLightBridge && "
                f"window.StoneLightBridge.receive({event_json}, {payload_json});"
            )
            self.window.evaluate_js(script)
        except Exception:
            pass
