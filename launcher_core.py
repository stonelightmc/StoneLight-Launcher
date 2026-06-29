import hashlib
import json
import os
import re
import shutil
import subprocess
import threading
import tempfile
import time
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

import requests

from nbt_servers import ensure_server_in_list

try:
    import minecraft_launcher_lib
except ImportError as exc:
    raise RuntimeError(
        "Не установлена библиотека minecraft-launcher-lib. "
        "Запусти setup.cmd или pip install -r requirements.txt"
    ) from exc


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"
USER_SETTINGS_PATH = ROOT / "user_settings.json"

RUNNING_GAME_PROCESSES: dict[str, subprocess.Popen] = {}
RUNNING_GAME_LOCK = threading.Lock()
CONSOLE_HISTORY: dict[str, list[str]] = {}
CONSOLE_LISTENERS: dict[str, list[Callable[[str], None]]] = {}
CONSOLE_LOCK = threading.Lock()
CONSOLE_HISTORY_LIMIT = 1200


def normalize_console_key(path: Path | str) -> str:
    return str(Path(path).resolve()).casefold()


def get_console_key_for_instance(instance: dict, root: Path = ROOT) -> str:
    game_directory = (instance or {}).get("game_directory") or "data/.minecraft"
    path = Path(game_directory)
    if not path.is_absolute():
        path = Path(root) / path
    return normalize_console_key(path)


def register_console_listener(key: str, callback: Callable[[str], None]):
    if not key or not callback:
        return
    with CONSOLE_LOCK:
        listeners = CONSOLE_LISTENERS.setdefault(key, [])
        if callback not in listeners:
            listeners.append(callback)


def unregister_console_listener(key: str, callback: Callable[[str], None]):
    if not key or not callback:
        return
    with CONSOLE_LOCK:
        listeners = CONSOLE_LISTENERS.get(key, [])
        if callback in listeners:
            listeners.remove(callback)


def get_console_history(key: str, limit: int = 500) -> list[str]:
    with CONSOLE_LOCK:
        history = list(CONSOLE_HISTORY.get(key, []))
    return history[-limit:]


def _record_console_history(key: str, message: str):
    if not key:
        return
    with CONSOLE_LOCK:
        history = CONSOLE_HISTORY.setdefault(key, [])
        history.append(message)
        if len(history) > CONSOLE_HISTORY_LIMIT:
            del history[:-CONSOLE_HISTORY_LIMIT]


def _broadcast_console(key: str, message: str, exclude=None):
    if not key:
        return
    with CONSOLE_LOCK:
        listeners = list(CONSOLE_LISTENERS.get(key, []))
    for callback in listeners:
        if exclude is not None and callback == exclude:
            continue
        try:
            callback(message)
        except Exception:
            pass


class LauncherError(RuntimeError):
    pass


def parse_minecraft_version_numbers(minecraft_version: str) -> tuple[int | None, int | None, int | None]:
    version = (minecraft_version or "").strip().lower()
    match = re.match(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?", version)
    if not match:
        return None, None, None
    return (
        int(match.group(1)),
        int(match.group(2) or 0),
        int(match.group(3) or 0),
    )


def required_java_major_for_minecraft(minecraft_version: str) -> tuple[int | None, int | None, str]:
    version = (minecraft_version or "").strip().lower()
    major, minor, patch = parse_minecraft_version_numbers(version)

    # StoneLight/new-version scheme: 26.x and future lines currently need Java 25+.
    # This also prevents future 26.2/26.3 builds from falling back to manual Java selection.
    if major is not None and major >= 26:
        return 25, None, "Java 25+"

    if major == 1:
        if minor is not None and minor >= 21:
            return 21, None, "Java 21+"
        if minor == 20:
            if patch is not None and patch >= 5:
                return 21, None, "Java 21+"
            return 17, None, "Java 17+"
        if minor in (18, 19):
            return 17, None, "Java 17+"
        if minor == 17:
            return 16, 16, "Java 16"
        if minor is not None and 7 <= minor <= 16:
            return 8, 8, "Java 8"

    # Unknown future release/snapshot: use newest managed Java instead of asking the user for a path.
    return 25, None, "Java 25+"


def suggest_java_for_minecraft(minecraft_version: str) -> str:
    _min_major, _max_major, label = required_java_major_for_minecraft(minecraft_version)
    return label


def recommended_java_major_for_minecraft(minecraft_version: str) -> int | None:
    min_major, max_major, _label = required_java_major_for_minecraft(minecraft_version)
    if max_major is not None:
        return max_major
    return min_major


def java_preset_to_major(preset: str, minecraft_version: str) -> int | None:
    preset = (preset or "").strip().lower()

    if preset in ("", "auto", "portable", "recommended"):
        return recommended_java_major_for_minecraft(minecraft_version)
    if preset in ("java8", "8"):
        return 8
    if preset in ("java16", "16"):
        return 16
    if preset in ("java17", "17"):
        return 17
    if preset in ("java21", "21"):
        return 21
    if preset in ("java25", "25"):
        return 25

    return None


def is_java_preset_token(value: str) -> bool:
    return (value or "").strip().lower() in {
        "auto", "portable", "recommended", "global", "manual",
        "java8", "java16", "java17", "java21", "java25", "8", "16", "17", "21", "25"
    }


def _safe_int(value, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def normalize_global_launch_settings(settings: dict, config: dict, fallback_max: int | None = None) -> dict:
    default_min = int(config.get("global_ram_min_mb", 512))
    default_max = int(config.get("global_ram_max_mb", config.get("default_ram_mb", 4096)))
    if fallback_max:
        default_max = int(fallback_max)

    ram_min = _safe_int(settings.get("ram_min_mb", settings.get("global_ram_min_mb", default_min)), default_min)
    ram_max = _safe_int(settings.get("ram_max_mb", settings.get("ram_mb", settings.get("global_ram_max_mb", default_max))), default_max)

    ram_min = max(256, min(ram_min, 65536))
    ram_max = max(1024, min(ram_max, 131072))

    if ram_min > ram_max:
        ram_min = min(512, ram_max)

    fullscreen = bool(settings.get("fullscreen", settings.get("global_fullscreen", config.get("global_fullscreen", False))))

    return {
        "ram_min_mb": ram_min,
        "ram_max_mb": ram_max,
        "fullscreen": fullscreen,
    }



class LauncherCore:
    def __init__(
        self,
        root: Path = ROOT,
        instance: Optional[dict] = None,
        log_callback: Optional[Callable[[str], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        console_callback: Optional[Callable[[str], None]] = None,
    ):
        self.root = Path(root).resolve()
        self.config_path = self.root / "config.json"
        self.base_config = self.load_config()
        self.instance = instance or {}
        self.config = self.make_effective_config(self.base_config, self.instance)

        self.log_callback = log_callback
        self.status_callback = status_callback
        self.progress_callback = progress_callback
        self.console_callback = console_callback or log_callback

        self.minecraft_dir = self.abs_path(self.config["game_directory"])
        self.game_dir = self.minecraft_dir
        self.cache_dir = self.abs_path(self.config.get("cache_directory", "data/cache"))
        self.log_path = self.root / "data" / "launcher.log"

        self.minecraft_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> dict:
        if not self.config_path.exists():
            raise LauncherError("Не найден config.json рядом с launcher_core.py")
        return json.loads(self.config_path.read_text(encoding="utf-8"))

    def make_effective_config(self, config: dict, instance: dict) -> dict:
        effective = dict(config)

        if instance:
            effective["instance_id"] = instance.get("id", "")
            effective["instance_name"] = instance.get("name", "StoneLight")
            effective["game_directory"] = instance.get("game_directory") or config.get("game_directory", "data/.minecraft")
            effective["minecraft_version"] = instance.get("minecraft_version") or config.get("minecraft_version")
            effective["version_type"] = instance.get("version_type", "release")
            effective["loader"] = (instance.get("loader") or "vanilla").lower()
            # Важно: для пользовательских сборок пустая версия loader должна оставаться пустой.
            # Иначе Forge/Quilt/NeoForge случайно подхватывали глобальный Fabric Loader 0.19.3.
            effective["fabric_loader_version"] = instance.get("loader_version", "") or ""
            effective["java_preset"] = instance.get("java_preset", "auto") or "auto"
            effective["instance_java_executable"] = instance.get("java_executable", "") or ""
            effective["forge_install_mode"] = instance.get("forge_install_mode", "auto") or "auto"
            effective["server_ip"] = instance.get("server_ip", "")
            effective["server_port"] = str(instance.get("server_port", config.get("server_port", "25565")))
            effective["install_modpack"] = bool(instance.get("install_modpack", False))
            effective["mods_zip_url"] = instance.get("modpack_url", "")
            effective["mods_zip_sha256"] = instance.get("modpack_sha256", "")
            effective["ensure_server_in_list"] = bool(instance.get("ensure_server_in_list", False))
            effective["server_list_name"] = instance.get("server_list_name") or instance.get("name") or "StoneLight"
        else:
            effective["instance_name"] = "StoneLight"
            effective["install_modpack"] = True
            effective["loader"] = (effective.get("loader") or "fabric").lower()

        return effective

    def abs_path(self, path_text: str) -> Path:
        path = Path(path_text)
        if not path.is_absolute():
            path = self.root / path
        return path.resolve()

    def instance_process_key(self) -> str:
        return normalize_console_key(self.minecraft_dir)

    def get_running_process(self) -> subprocess.Popen | None:
        key = self.instance_process_key()
        with RUNNING_GAME_LOCK:
            process = RUNNING_GAME_PROCESSES.get(key)
            if process and process.poll() is None:
                return process
            if process and process.poll() is not None:
                RUNNING_GAME_PROCESSES.pop(key, None)
        return None

    def register_running_process(self, process: subprocess.Popen):
        key = self.instance_process_key()
        with RUNNING_GAME_LOCK:
            RUNNING_GAME_PROCESSES[key] = process

    def unregister_running_process(self, process: subprocess.Popen):
        key = self.instance_process_key()
        with RUNNING_GAME_LOCK:
            current = RUNNING_GAME_PROCESSES.get(key)
            if current is process:
                RUNNING_GAME_PROCESSES.pop(key, None)

    def force_stop_game(self, timeout: float = 5.0) -> str:
        process = self.get_running_process()
        if not process:
            msg = "Запущенный процесс этой сборки не найден."
            self.emit_status(msg)
            return msg

        self.emit_status("Останавливаю запущенную сборку...")
        try:
            process.terminate()
            try:
                process.wait(timeout=timeout)
                msg = "Сборка остановлена."
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=timeout)
                msg = "Сборка принудительно убита."
        except Exception as exc:
            raise LauncherError(f"Не удалось остановить сборку: {exc}") from exc
        finally:
            self.unregister_running_process(process)

        self.emit_status(msg)
        return msg

    def emit_log(self, message: str):
        line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}"
        try:
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def emit_console(self, message: str):
        message = message.rstrip("\n")
        if not message:
            return

        try:
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [GAME] {message}\n")
        except Exception:
            pass

        key = self.instance_process_key()
        _record_console_history(key, message)

        if self.console_callback:
            self.console_callback(message)
        else:
            print(message)

        _broadcast_console(key, message, exclude=self.console_callback)

    def emit_status(self, message: str):
        # Status messages used to go through emit_log() and then status_callback,
        # which made the GUI console show many lines twice. Keep file logging,
        # but call only the status callback for UI output.
        line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}"
        try:
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

        if self.status_callback:
            self.status_callback(message)
        elif not self.log_callback:
            print(message)

    def emit_progress(self, current: int, total: int):
        if self.progress_callback:
            self.progress_callback(current, total)
        elif total > 0:
            percent = current / total * 100
            print(f"\r{percent:5.1f}% [{current}/{total}]", end="", flush=True)

    def portable_java_base_dir(self) -> Path:
        return self.abs_path(self.base_config.get("portable_java_directory", "data/java"))

    def portable_java_dir(self, major: int) -> Path:
        return self.portable_java_base_dir() / f"temurin-{major}"

    def find_java_executable_in_dir(self, directory: Path) -> Path | None:
        directory = Path(directory)
        candidates = list(directory.glob("bin/java.exe")) + list(directory.glob("*/bin/java.exe")) + list(directory.rglob("bin/java.exe"))
        for candidate in candidates:
            if candidate.exists():
                return candidate.resolve()
        return None

    def get_portable_java_executable(self, major: int) -> Path | None:
        return self.find_java_executable_in_dir(self.portable_java_dir(major))

    def adoptium_download_url(self, major: int) -> str:
        # Stable Adoptium API v3 direct binary endpoint. requests follows redirects.
        return f"https://api.adoptium.net/v3/binary/latest/{major}/ga/windows/x64/jdk/hotspot/normal/eclipse"

    def install_portable_java(self, major: int, force_download: bool = False) -> str:
        target_dir = self.portable_java_dir(major)
        existing = self.get_portable_java_executable(major)

        if existing and not force_download:
            self.emit_log(f"Portable Java {major} уже установлена: {existing}")
            return str(existing)

        self.emit_status(f"Скачиваю portable Java {major}...")
        self.portable_java_base_dir().mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        archive_path = self.cache_dir / f"temurin-{major}-windows-x64-jdk.zip"
        self.download_file(self.adoptium_download_url(major), archive_path)

        temp_dir = self.portable_java_base_dir() / f"_temurin_{major}_tmp"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)

        self.emit_status(f"Распаковываю portable Java {major}...")
        try:
            with zipfile.ZipFile(archive_path) as zf:
                zf.extractall(temp_dir)

            java_exe = self.find_java_executable_in_dir(temp_dir)
            if not java_exe:
                raise LauncherError(f"В архиве Java {major} не найден bin/java.exe.")

            java_home = java_exe.parent.parent

            if target_dir.exists():
                shutil.rmtree(target_dir)
            target_dir.parent.mkdir(parents=True, exist_ok=True)

            # Переносим Java home в стабильную папку data/java/temurin-X.
            shutil.move(str(java_home), str(target_dir))

            final_java = self.get_portable_java_executable(major)
            if not final_java:
                raise LauncherError(f"После распаковки Java {major} не найден bin/java.exe.")

            self.emit_status(f"Portable Java {major} установлена.")
            self.emit_log(f"Java {major}: {final_java}")
            return str(final_java)

        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

    def resolve_java_executable(self, java_executable: str) -> str:
        java_executable = (java_executable or "").strip()
        configured_preset = (self.config.get("java_preset") or "auto").strip().lower()
        minecraft_version = self.config.get("minecraft_version", "")
        token = java_executable.lower()

        # Если поле запуска содержит java25/java21/auto и т.п., воспринимаем его как preset,
        # а не как путь к файлу.
        effective_preset = token if is_java_preset_token(token) and token not in ("manual", "global") else configured_preset

        # Явный ручной путь всегда уважаем.
        if java_executable and not is_java_preset_token(token):
            return java_executable

        instance_java = (self.config.get("instance_java_executable") or "").strip()

        if effective_preset == "manual":
            if instance_java:
                return instance_java
            if java_executable and not is_java_preset_token(token):
                return java_executable
            raise LauncherError("Для preset manual нужно указать путь к java.exe/javaw.exe.")

        if effective_preset == "global":
            global_java = self.base_config.get("java_executable") or "java"
            return global_java

        major = java_preset_to_major(effective_preset, minecraft_version)
        if major:
            return self.install_portable_java(major)

        # Последний fallback: используем глобальную Java, но auto должен сюда почти никогда не попадать.
        return self.base_config.get("java_executable", "java")

    def resolve_java_for_check(self, java_executable: str) -> str:
        p = Path(java_executable.strip('"'))
        if p.name.lower() == "javaw.exe":
            candidate = p.with_name("java.exe")
            if candidate.exists():
                return str(candidate)
        return java_executable

    def get_java_major(self, java_executable: str) -> int | None:
        check_executable = self.resolve_java_for_check(java_executable)

        try:
            result = subprocess.run(
                [check_executable, "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )
        except FileNotFoundError as exc:
            raise LauncherError(
                "Java не найдена. Установи Java и укажи путь к java.exe/javaw.exe в лаунчере."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise LauncherError("Проверка Java зависла. Проверь путь к Java.") from exc

        version_text = (result.stderr or "") + (result.stdout or "")
        match = re.search(r'version "(\d+)(?:\.(\d+))?', version_text)

        if not match:
            self.emit_log("Не смог автоматически определить версию Java. Вывод java -version:")
            self.emit_log(version_text.strip() or "<пустой вывод>")
            return None

        first = int(match.group(1))
        second = int(match.group(2) or 0)

        # Java 8 обычно пишет 1.8.0_xxx.
        if first == 1 and second:
            return second

        return first

    def check_java(self, java_executable: str):
        self.emit_status("Проверяю Java...")
        major = self.get_java_major(java_executable)

        if major is None:
            return

        self.emit_log(f"Найдена Java {major}")
        if major < 8:
            raise LauncherError("Найдена слишком старая Java. Нужна современная Java.")

    def check_java_compatibility(self, java_executable: str):
        self.check_java(java_executable)

        major = self.get_java_major(java_executable)
        if major is None:
            return

        minecraft_version = self.config.get("minecraft_version", "")
        min_major, max_major, label = required_java_major_for_minecraft(minecraft_version)

        if min_major is not None and major < min_major:
            raise LauncherError(
                f"Для Minecraft {minecraft_version} нужна {label}, а выбрана Java {major}.\\n"
                "Укажи правильный java.exe в настройках этой сборки."
            )

        if max_major is not None and major > max_major:
            raise LauncherError(
                f"Для Minecraft {minecraft_version} нужна именно {label}, а выбрана Java {major}.\\n\\n"
                "Старый Forge/Minecraft не запускается на новых Java и может падать с ошибкой:\\n"
                "ClassCastException: AppClassLoader cannot be cast to URLClassLoader\\n\\n"
                "Решение: в настройках этой сборки укажи java.exe от Java 8."
            )

    def sha256_file(self, path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    def download_file(self, url: str, destination: Path):
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp_destination = destination.with_suffix(destination.suffix + ".download")

        self.emit_status(f"Скачиваю файл: {destination.name}...")
        with requests.get(url, stream=True, timeout=60) as response:
            response.raise_for_status()
            total = int(response.headers.get("content-length", "0"))
            downloaded = 0

            with temp_destination.open("wb") as file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    file.write(chunk)
                    downloaded += len(chunk)
                    self.emit_progress(downloaded, total)

        temp_destination.replace(destination)
        self.emit_log("Скачивание завершено.")

    def get_modpack_archive(self, force_download: bool = False) -> Path:
        url = self.config.get("mods_zip_url", "")
        if not url:
            raise LauncherError("У этой сборки не указан архив модов.")

        zip_name = Path(url).name or "mods.zip"
        local_zip = self.root / zip_name
        cache_zip = self.cache_dir / zip_name
        expected_hash = self.config.get("mods_zip_sha256")

        if local_zip.exists() and not force_download:
            self.emit_log(f"Использую локальный архив модов: {local_zip.name}")
            source_zip = local_zip
        else:
            source_zip = cache_zip
            needs_download = force_download or not source_zip.exists()

            if source_zip.exists() and expected_hash and not force_download:
                actual_hash = self.sha256_file(source_zip)
                needs_download = actual_hash.lower() != expected_hash.lower()
                if needs_download:
                    self.emit_log("Кэшированный архив модов устарел или повреждён.")

            if needs_download:
                self.download_file(url, source_zip)

        if expected_hash:
            actual_hash = self.sha256_file(source_zip)
            if actual_hash.lower() != expected_hash.lower():
                raise LauncherError(
                    "SHA256 архива модов не совпал.\n"
                    f"Ожидалось: {expected_hash}\n"
                    f"Получено:   {actual_hash}"
                )

        return source_zip

    def extract_modpack_safely(self, archive_path: Path) -> int:
        mods_dir = self.game_dir / "mods"
        temp_root = self.game_dir / "_mods_update_tmp"
        backup_dir = self.game_dir / "mods_backup_previous"

        if temp_root.exists():
            shutil.rmtree(temp_root)
        temp_root.mkdir(parents=True)

        self.emit_status("Проверяю и распаковываю сборку...")
        try:
            with zipfile.ZipFile(archive_path) as zf:
                bad_file = zf.testzip()
                if bad_file:
                    raise LauncherError(f"Архив модов повреждён: {bad_file}")
                zf.extractall(temp_root)

            root_jars = list(temp_root.glob("*.jar"))
            nested_mods = temp_root / "mods"
            if not root_jars and nested_mods.exists() and list(nested_mods.glob("*.jar")):
                source_dir = nested_mods
            else:
                source_dir = temp_root

            jar_count = len(list(source_dir.glob("*.jar")))
            if jar_count == 0:
                raise LauncherError("В архиве модов не найдено .jar-файлов.")

            if backup_dir.exists():
                shutil.rmtree(backup_dir)

            if mods_dir.exists():
                shutil.move(str(mods_dir), str(backup_dir))

            mods_dir.mkdir(parents=True, exist_ok=True)

            try:
                for item in source_dir.iterdir():
                    target = mods_dir / item.name
                    if item.is_dir():
                        shutil.copytree(item, target)
                    else:
                        shutil.copy2(item, target)
            except Exception:
                if mods_dir.exists():
                    shutil.rmtree(mods_dir)
                if backup_dir.exists():
                    shutil.move(str(backup_dir), str(mods_dir))
                raise

            if not self.config.get("keep_mods_backup", True) and backup_dir.exists():
                shutil.rmtree(backup_dir)

            self.emit_log(f"Сборка модов установлена. Jar-файлов: {jar_count}")
            return jar_count

        finally:
            if temp_root.exists():
                shutil.rmtree(temp_root)

    def ensure_modpack(self, force_download: bool = False) -> int:
        if not self.config.get("install_modpack", True):
            mods_dir = self.game_dir / "mods"
            mods_dir.mkdir(parents=True, exist_ok=True)
            self.emit_log("У этой пользовательской сборки нет официального модпака для автообновления.")
            return 0

        archive = self.get_modpack_archive(force_download=force_download)
        return self.extract_modpack_safely(archive)

    def is_legacy_forge_instance(self) -> bool:
        loader = (self.config.get("loader") or "vanilla").lower()
        version = (self.config.get("minecraft_version") or "").lower()
        return loader == "forge" and (
            version.startswith("1.7") or
            version.startswith("1.8") or
            version.startswith("1.9") or
            version.startswith("1.10") or
            version.startswith("1.11") or
            version.startswith("1.12")
        )

    def vanilla_version_dir(self, minecraft_version: str) -> Path:
        return self.minecraft_dir / "versions" / minecraft_version

    def vanilla_jar_path(self, minecraft_version: str) -> Path:
        return self.vanilla_version_dir(minecraft_version) / f"{minecraft_version}.jar"

    def validate_vanilla_jar(self, minecraft_version: str) -> tuple[bool, str]:
        jar_path = self.vanilla_jar_path(minecraft_version)

        if not jar_path.exists():
            return False, f"vanilla jar не найден: {jar_path}"

        try:
            size = jar_path.stat().st_size
        except Exception as exc:
            return False, f"не удалось проверить размер jar: {exc}"

        if size < 1024 * 1024:
            return False, f"vanilla jar слишком маленький: {size} bytes"

        try:
            with zipfile.ZipFile(jar_path) as zf:
                bad = zf.testzip()
                if bad:
                    return False, f"zip test failed: {bad}"

                class_entries = [
                    info for info in zf.infolist()
                    if info.filename.endswith(".class") and info.file_size > 0
                ]
                if len(class_entries) < 1000:
                    return False, f"слишком мало class-файлов в jar: {len(class_entries)}"

        except Exception as exc:
            return False, f"jar не читается как zip: {exc}"

        return True, "OK"

    def repair_vanilla_version(self, minecraft_version: str):
        version_dir = self.vanilla_version_dir(minecraft_version)
        if version_dir.exists():
            backup = version_dir.with_name(f"{minecraft_version}_broken_backup")
            try:
                if backup.exists():
                    shutil.rmtree(backup)
                shutil.move(str(version_dir), str(backup))
                self.emit_log(f"Старая папка vanilla версии перемещена в backup: {backup}")
            except Exception as exc:
                self.emit_log(f"Не удалось переместить папку версии в backup, удаляю напрямую: {exc}")
                shutil.rmtree(version_dir, ignore_errors=True)

        self.emit_status(f"Повторно скачиваю clean vanilla Minecraft {minecraft_version}...")
        minecraft_launcher_lib.install.install_minecraft_version(
            minecraft_version,
            str(self.minecraft_dir),
            callback=self._callback_dict()
        )

        ok, reason = self.validate_vanilla_jar(minecraft_version)
        if not ok:
            raise LauncherError(
                f"После повторной загрузки vanilla jar всё ещё выглядит повреждённым.\n"
                f"Версия: {minecraft_version}\n"
                f"Причина: {reason}\n"
                "Попробуй удалить папку сборки или проверить интернет/антивирус."
            )

        self.emit_status(f"Clean vanilla Minecraft {minecraft_version} готов.")

    def ensure_clean_vanilla_for_legacy_forge(self):
        if not self.is_legacy_forge_instance():
            return

        minecraft_version = self.config["minecraft_version"]
        ok, reason = self.validate_vanilla_jar(minecraft_version)

        if ok:
            self.emit_log(f"vanilla jar {minecraft_version} выглядит корректным.")
            return

        self.emit_log(
            f"vanilla jar {minecraft_version} выглядит повреждённым или неполным: {reason}. "
            "Запускаю repair перед стартом legacy Forge."
        )
        self.repair_vanilla_version(minecraft_version)

    def ensure_legacy_forge_json_jar_field(self, version_id: str):
        """
        Some manually installed old Forge profiles may rely on launcher behavior
        that adds the inherited vanilla client jar. If the Forge JSON does not
        expose the vanilla jar correctly, custom launchers can start Forge
        without the vanilla client jar in classpath, which leads to the classic
        EntityOcelot/ClassPatchManager "vanilla jar may be corrupt" crash.
        """
        if not self.is_legacy_forge_instance():
            return

        minecraft_version = self.config["minecraft_version"]
        version_json = self.minecraft_dir / "versions" / version_id / f"{version_id}.json"

        if not version_json.exists():
            self.emit_log(f"Forge version json не найден для проверки jar-поля: {version_json}")
            return

        try:
            data = json.loads(version_json.read_text(encoding="utf-8"))
        except Exception as exc:
            self.emit_log(f"Не удалось прочитать Forge version json: {exc}")
            return

        changed = False

        if data.get("jar") != minecraft_version:
            data["jar"] = minecraft_version
            changed = True

        if not data.get("inheritsFrom"):
            data["inheritsFrom"] = minecraft_version
            changed = True

        if changed:
            backup = version_json.with_suffix(".json.bak")
            try:
                if not backup.exists():
                    shutil.copy2(version_json, backup)
            except Exception:
                pass

            version_json.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            self.emit_log(f"Forge version json обновлён: jar/inheritsFrom -> {minecraft_version}")

    def version_json_path(self, version_id: str) -> Path:
        return self.minecraft_dir / "versions" / version_id / f"{version_id}.json"

    def load_version_json(self, version_id: str) -> dict | None:
        path = self.version_json_path(version_id)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            self.emit_log(f"Не удалось прочитать version json {path}: {exc}")
            return None

    def version_json_chain(self, version_id: str) -> list[tuple[str, dict]]:
        result: list[tuple[str, dict]] = []
        seen: set[str] = set()

        def add(vid: str):
            if not vid or vid in seen:
                return
            seen.add(vid)
            data = self.load_version_json(vid)
            if not data:
                return
            parent = data.get("inheritsFrom")
            if parent:
                add(parent)
            result.append((vid, data))

        add(version_id)
        return result

    def maven_artifact_path_from_name(self, name: str) -> str | None:
        parts = (name or "").split(":")
        if len(parts) < 3:
            return None

        group, artifact, version = parts[0], parts[1], parts[2]
        classifier = parts[3] if len(parts) >= 4 else ""

        filename = f"{artifact}-{version}"
        if classifier:
            filename += f"-{classifier}"
        filename += ".jar"

        return "/".join([group.replace(".", "/"), artifact, version, filename])

    def default_maven_base_for_library(self, name: str) -> str:
        group = (name or "").split(":")[0].lower()
        if "minecraftforge" in group or group.startswith("cpw.mods") or group.startswith("net.minecraftforge"):
            return "https://maven.minecraftforge.net/"
        return "https://libraries.minecraft.net/"

    def is_library_allowed_on_windows(self, lib: dict) -> bool:
        rules = lib.get("rules")
        if not rules:
            return True

        allowed = False
        for rule in rules:
            action = rule.get("action")
            os_rule = rule.get("os")

            matches = True
            if isinstance(os_rule, dict):
                os_name = os_rule.get("name")
                if os_name and os_name != "windows":
                    matches = False

            if matches:
                allowed = action == "allow"

        return allowed

    def legacy_library_artifact(self, lib: dict) -> tuple[Path, str | None, str] | None:
        if not self.is_library_allowed_on_windows(lib):
            return None

        name = lib.get("name") or ""
        if not name:
            return None

        # Natives распаковываются отдельно в ensure_legacy_natives(), в classpath их не добавляем.
        if lib.get("natives"):
            return None

        downloads = lib.get("downloads") or {}
        artifact = downloads.get("artifact") if isinstance(downloads, dict) else None

        path_text = None
        url = None

        if isinstance(artifact, dict):
            path_text = artifact.get("path")
            url = artifact.get("url")

        if not path_text:
            path_text = self.maven_artifact_path_from_name(name)

        if not path_text:
            return None

        if not url:
            base = lib.get("url") or self.default_maven_base_for_library(name)
            if not base.endswith("/"):
                base += "/"
            url = base + path_text.replace("\\", "/")

        return self.minecraft_dir / "libraries" / Path(path_text), url, name

    def ensure_legacy_version_libraries(self, version_id: str) -> list[Path]:
        """
        Старый Forge 1.7.10 иногда стартует с mainClass net.minecraft.launchwrapper.Launch,
        но command builder не добавляет launchwrapper и другие legacy-библиотеки в classpath.
        Здесь мы читаем Forge JSON + inheritsFrom vanilla JSON, докачиваем библиотеки и
        возвращаем список jar, которые нужно принудительно добавить в classpath.
        """
        if not self.is_legacy_forge_instance():
            return []

        artifacts: list[tuple[Path, str | None, str]] = []
        seen_paths: set[str] = set()

        for vid, data in self.version_json_chain(version_id):
            for lib in data.get("libraries") or []:
                item = self.legacy_library_artifact(lib)
                if not item:
                    continue
                path, url, name = item
                key = str(path).lower()
                if key in seen_paths:
                    continue
                seen_paths.add(key)
                artifacts.append(item)

        # Hard fallback specifically for Forge 1.7.10/legacy LaunchWrapper.
        # The exact file is present in Mojang libraries; if JSON parsing missed it, add it.
        launchwrapper_candidates = [
            ("net.minecraft:launchwrapper:1.12", "net/minecraft/launchwrapper/1.12/launchwrapper-1.12.jar"),
            ("net.minecraft:launchwrapper:1.11", "net/minecraft/launchwrapper/1.11/launchwrapper-1.11.jar"),
        ]
        for name, rel in launchwrapper_candidates:
            path = self.minecraft_dir / "libraries" / Path(rel)
            if str(path).lower() not in seen_paths:
                artifacts.append((path, "https://libraries.minecraft.net/" + rel, name))
                seen_paths.add(str(path).lower())

        ensured: list[Path] = []
        launchwrapper_ok = False

        for path, url, name in artifacts:
            try:
                if not path.exists() or path.stat().st_size <= 0:
                    if not url:
                        self.emit_log(f"Legacy library пропущена, нет URL: {name}")
                        continue
                    self.emit_log(f"Скачиваю legacy library: {name}")
                    self.download_file(url, path)

                if path.exists() and path.stat().st_size > 0:
                    ensured.append(path.resolve())

                    if "launchwrapper" in name.lower() or "launchwrapper" in path.name.lower():
                        try:
                            with zipfile.ZipFile(path) as zf:
                                if "net/minecraft/launchwrapper/Launch.class" in zf.namelist():
                                    launchwrapper_ok = True
                                    self.emit_log(f"LaunchWrapper найден: {path.name}")
                        except Exception as exc:
                            self.emit_log(f"LaunchWrapper jar не читается: {path} ({exc})")

            except Exception as exc:
                self.emit_log(f"Не удалось подготовить legacy library {name}: {exc}")

        if not launchwrapper_ok:
            raise LauncherError(
                "Forge 1.7.10 требует LaunchWrapper, но лаунчер не смог найти/скачать "
                "net.minecraft.launchwrapper.Launch.\n"
                "Попробуй нажать Repair или проверь доступ к libraries.minecraft.net."
            )

        return ensured

    def expected_legacy_guava_path(self) -> Path | None:
        version = (self.config.get("minecraft_version") or "").lower()

        # Minecraft/Forge 1.7.10 expects Guava 17.0.
        if version.startswith("1.7"):
            return self.minecraft_dir / "libraries" / "com" / "google" / "guava" / "guava" / "17.0" / "guava-17.0.jar"

        # Minecraft 1.8.x–1.11.x normally uses Guava 17.0/21.0 depending on exact version,
        # but we only force the known broken case for now.
        return None

    def ensure_expected_legacy_guava(self) -> Path | None:
        guava_path = self.expected_legacy_guava_path()
        if not guava_path:
            return None

        if not guava_path.exists() or guava_path.stat().st_size <= 0:
            rel = guava_path.relative_to(self.minecraft_dir / "libraries").as_posix()
            url = "https://libraries.minecraft.net/" + rel
            self.emit_log(f"Скачиваю совместимую Guava для legacy Forge: {guava_path.name}")
            self.download_file(url, guava_path)

        if not guava_path.exists() or guava_path.stat().st_size <= 0:
            raise LauncherError(f"Не удалось подготовить совместимую Guava: {guava_path}")

        return guava_path.resolve()

    def is_guava_jar_path(self, entry: str) -> bool:
        normalized = str(entry).replace("\\", "/").lower()
        return "/com/google/guava/guava/" in normalized and normalized.endswith(".jar")

    def patch_legacy_guava_conflict(self, classpath_entries: list[str]) -> list[str]:
        """
        Forge 1.7.10 fails with:
        NoSuchMethodError: com.google.common.io.CharSource.readLines(LineProcessor)
        when a wrong Guava version is earlier in classpath.

        For 1.7.x we force guava-17.0.jar first and remove other Guava jars
        from the explicit legacy-patched classpath.
        """
        expected = self.ensure_expected_legacy_guava()
        if not expected:
            return classpath_entries

        expected_str = str(expected)
        expected_norm = expected_str.lower()

        cleaned: list[str] = []
        removed: list[str] = []

        for entry in classpath_entries:
            if self.is_guava_jar_path(entry):
                try:
                    norm = str(Path(entry).resolve()).lower()
                except Exception:
                    norm = str(entry).lower()

                if norm == expected_norm:
                    continue

                removed.append(str(entry))
                continue

            cleaned.append(entry)

        # Guava 17.0 must be very early, before Forge/FML tries to initialize transformers.
        cleaned.insert(0, expected_str)

        if removed:
            self.emit_log(
                "Legacy Forge Guava patch: удалены конфликтующие Guava jar: "
                + ", ".join(Path(x).name for x in removed)
            )
        self.emit_log(f"Legacy Forge Guava patch: первой в classpath поставлена {expected.name}")

        return cleaned

    def patch_legacy_forge_classpath(self, command: list[str], version_id: str | None = None) -> list[str]:
        """
        Hard fallback for legacy Forge:
        - ensure clean vanilla client jar is present in classpath;
        - ensure old LaunchWrapper/libs from Forge JSON + inherited vanilla JSON are present.
        """
        if not self.is_legacy_forge_instance():
            return command

        minecraft_version = self.config["minecraft_version"]
        vanilla_jar = self.vanilla_jar_path(minecraft_version).resolve()

        ok, reason = self.validate_vanilla_jar(minecraft_version)
        if not ok:
            self.emit_log(f"Classpath patch: vanilla jar не прошёл проверку: {reason}")
            self.repair_vanilla_version(minecraft_version)

        patched = list(command)
        cp_index = None
        for i, part in enumerate(patched):
            if part in ("-cp", "-classpath", "--class-path") and i + 1 < len(patched):
                cp_index = i + 1
                break

        if cp_index is None:
            self.emit_log("Classpath patch: не нашёл -cp/-classpath в команде запуска.")
            return patched

        separator = os.pathsep
        entries = [entry for entry in patched[cp_index].split(separator) if entry]

        required_entries: list[Path] = [vanilla_jar]
        if version_id:
            try:
                required_entries.extend(self.ensure_legacy_version_libraries(version_id))
            except Exception as exc:
                if isinstance(exc, LauncherError):
                    raise
                self.emit_log(f"Не удалось подготовить legacy библиотеки: {exc}")

        normalized = {str(Path(entry).resolve()).lower() for entry in entries if entry}
        added = 0

        # Добавляем в начало, чтобы LaunchWrapper/Forge patcher гарантированно видел нужные jar.
        for required in reversed(required_entries):
            required_str = str(required.resolve())
            if required_str.lower() not in normalized and required.exists():
                entries.insert(0, required_str)
                normalized.add(required_str.lower())
                added += 1

        entries = self.patch_legacy_guava_conflict(entries)
        patched[cp_index] = separator.join(entries)

        if added:
            self.emit_log(f"Legacy Forge classpath patch: добавлено jar-файлов: {added}")
        else:
            self.emit_log("Legacy Forge classpath patch: все нужные jar уже есть в classpath.")

        if str(vanilla_jar).lower() in normalized:
            self.emit_log("Legacy Forge classpath patch: vanilla jar есть в classpath.")

        return patched


    def write_debug_launch_command(self, command: list[str], version_id: str):
        try:
            debug_dir = self.cache_dir / "debug_commands"
            debug_dir.mkdir(parents=True, exist_ok=True)
            debug_file = debug_dir / f"launch_{version_id}.cmd"

            def q(arg: str) -> str:
                arg = str(arg)
                if not arg:
                    return '""'
                if any(ch in arg for ch in ' &()[]{}^=;!+,`~"'):
                    return '"' + arg.replace('"', '\\"') + '"'
                return '"' + arg + '"' if " " in arg else arg

            debug_file.write_text(
                "@echo off\r\n"
                f"cd /d \"{self.minecraft_dir}\"\r\n"
                + " ".join(q(part) for part in command)
                + "\r\npause\r\n",
                encoding="utf-8"
            )
            self.emit_log(f"Debug команда запуска сохранена: {debug_file}")
        except Exception as exc:
            self.emit_log(f"Не удалось сохранить debug команду запуска: {exc}")

    def legacy_natives_dir(self, minecraft_version: str) -> Path:
        return self.minecraft_dir / "versions" / minecraft_version / f"{minecraft_version}-natives-stonelight"

    def extract_native_jar(self, jar_path: Path, destination: Path):
        if not jar_path.exists():
            return 0

        count = 0
        with zipfile.ZipFile(jar_path) as zf:
            for info in zf.infolist():
                name = info.filename.replace("\\", "/")
                lower = name.lower()

                if info.is_dir():
                    continue
                if lower.startswith("meta-inf/"):
                    continue
                if not (
                    lower.endswith(".dll") or
                    lower.endswith(".so") or
                    lower.endswith(".dylib") or
                    lower.endswith(".jnilib")
                ):
                    continue

                target = destination / Path(name).name
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
                count += 1

        return count

    def ensure_legacy_natives(self) -> Path | None:
        if not self.is_legacy_forge_instance():
            return None

        minecraft_version = self.config["minecraft_version"]
        natives_dir = self.legacy_natives_dir(minecraft_version)
        natives_dir.mkdir(parents=True, exist_ok=True)

        existing_lwjgl = natives_dir / "lwjgl64.dll"
        existing_lwjgl32 = natives_dir / "lwjgl.dll"

        if existing_lwjgl.exists() or existing_lwjgl32.exists():
            self.emit_log(f"Legacy natives уже готовы: {natives_dir}")
            return natives_dir

        self.emit_log(f"Распаковываю legacy natives в: {natives_dir}")

        libraries_dir = self.minecraft_dir / "libraries"
        native_jars = sorted(libraries_dir.rglob("*natives-windows*.jar"))

        extracted = 0
        for jar_path in native_jars:
            try:
                count = self.extract_native_jar(jar_path, natives_dir)
                if count:
                    extracted += count
                    self.emit_log(f"Extract natives: {jar_path.name} ({count})")
            except Exception as exc:
                self.emit_log(f"Не удалось распаковать natives из {jar_path}: {exc}")

        if not (existing_lwjgl.exists() or existing_lwjgl32.exists()):
            # На всякий случай ещё пробуем искать jar по имени lwjgl-platform, даже если glob выше не сработал.
            for jar_path in libraries_dir.rglob("lwjgl-platform-*-natives-windows.jar"):
                try:
                    count = self.extract_native_jar(jar_path, natives_dir)
                    if count:
                        extracted += count
                        self.emit_log(f"Extract LWJGL natives: {jar_path.name} ({count})")
                except Exception as exc:
                    self.emit_log(f"Не удалось распаковать LWJGL natives из {jar_path}: {exc}")

        if not (existing_lwjgl.exists() or existing_lwjgl32.exists()):
            raise LauncherError(
                "Не удалось подготовить LWJGL natives для legacy Forge.\n"
                f"Ожидался файл lwjgl64.dll или lwjgl.dll в:\n{natives_dir}\n\n"
                "Нажми «Обновить / установить» или Repair, чтобы перескачать библиотеки."
            )

        self.emit_log(f"Legacy natives готовы: {natives_dir} ({extracted} файлов распаковано)")
        return natives_dir

    def patch_legacy_natives_path(self, command: list[str]) -> list[str]:
        if not self.is_legacy_forge_instance():
            return command

        natives_dir = self.ensure_legacy_natives()
        if not natives_dir:
            return command

        natives_str = str(natives_dir.resolve())
        patched = list(command)

        # Ищем существующий -Djava.library.path=...
        for i, part in enumerate(patched):
            if part.startswith("-Djava.library.path="):
                current = part.split("=", 1)[1]
                entries = [entry for entry in current.split(os.pathsep) if entry]
                normalized = {str(Path(entry).resolve()).lower() for entry in entries if entry}
                if natives_str.lower() not in normalized:
                    entries.insert(0, natives_str)
                    patched[i] = "-Djava.library.path=" + os.pathsep.join(entries)
                    self.emit_log(f"Legacy natives patch: добавлен java.library.path: {natives_dir}")
                else:
                    self.emit_log("Legacy natives patch: java.library.path уже содержит legacy natives.")
                return patched

        # Если аргумента вообще нет, добавляем сразу после java.exe и до остальных JVM аргументов.
        insert_at = 1 if patched else 0
        patched.insert(insert_at, "-Djava.library.path=" + natives_str)
        self.emit_log(f"Legacy natives patch: создан java.library.path: {natives_dir}")
        return patched


    def install_minecraft_and_loader(self, java_executable: str) -> str:
        loader = (self.config.get("loader") or "vanilla").lower()
        minecraft_version = self.config["minecraft_version"]
        loader_version = self.config.get("fabric_loader_version", "") or ""

        if loader == "vanilla":
            return self.install_vanilla(minecraft_version)

        # Fabric/Quilt/NeoForge work better through the new unified mod_loader API.
        if loader in ("fabric", "quilt", "neoforge"):
            return self.install_unified_mod_loader(minecraft_version, loader, loader_version, java_executable)

        # Forge still needs special handling because old Forge versions and installers are quirky.
        if loader == "forge":
            return self.install_forge(minecraft_version, loader_version, java_executable)

        raise LauncherError(f"Пока не поддерживается loader: {loader}")

    def _callback_dict(self):
        progress_state = {"max": 0}

        def set_status(status):
            self.emit_status(str(status))

        def set_max(maximum):
            progress_state["max"] = int(maximum or 0)

        def set_progress(value):
            maximum = progress_state.get("max", 0)
            if maximum > 0:
                self.emit_progress(int(value or 0), maximum)

        return {
            "setStatus": set_status,
            "setProgress": set_progress,
            "setMax": set_max,
        }

    def install_vanilla(self, minecraft_version: str) -> str:
        callback = self._callback_dict()
        self.emit_status(f"Устанавливаю/проверяю Minecraft {minecraft_version}...")
        minecraft_launcher_lib.install.install_minecraft_version(
            minecraft_version,
            str(self.minecraft_dir),
            callback=callback
        )
        return minecraft_version

    def install_unified_mod_loader(self, minecraft_version: str, loader: str, loader_version: str, java_executable: str) -> str:
        callback = self._callback_dict()
        self.emit_status(f"Устанавливаю/проверяю Minecraft {minecraft_version}...")
        minecraft_launcher_lib.install.install_minecraft_version(
            minecraft_version,
            str(self.minecraft_dir),
            callback=callback
        )

        self.emit_status(f"Устанавливаю/проверяю {loader} для Minecraft {minecraft_version}...")
        try:
            mod_loader = minecraft_launcher_lib.mod_loader.get_mod_loader(loader)
        except Exception as exc:
            raise LauncherError(f"Модлоадер {loader} недоступен в текущей версии minecraft-launcher-lib.") from exc

        try:
            if not loader_version:
                loader_version = mod_loader.get_latest_loader_version(minecraft_version)
                self.emit_log(f"Выбрана последняя версия {loader}: {loader_version}")

            installed = mod_loader.install(
                minecraft_version,
                str(self.minecraft_dir),
                loader_version=loader_version,
                callback=callback,
                java=java_executable
            )

            if installed:
                self.emit_log(f"Будет запускаться версия: {installed}")
                return installed

            installed = mod_loader.get_installed_version(minecraft_version, loader_version)
            self.emit_log(f"Будет запускаться версия: {installed}")
            return installed
        except Exception as exc:
            raise LauncherError(
                f"Не удалось установить {loader} {loader_version or '(latest)'} для Minecraft {minecraft_version}.\n"
                f"Причина: {exc}"
            ) from exc

    def _extract_bad_checksum_path(self, error_text: str) -> Path | None:
        # minecraft-launcher-lib often raises:
        # File <path> has the wrong checksum (expected ... got ...)
        match = re.search(r"File\s+(.+?)\s+has the wrong checksum", error_text, re.IGNORECASE | re.DOTALL)
        if not match:
            return None

        raw_path = match.group(1).strip().strip("'\"")
        if not raw_path:
            return None

        try:
            path = Path(raw_path)
            # Safety: only delete files inside this instance's minecraft directory.
            if path.exists() and self.minecraft_dir in path.resolve().parents:
                return path
        except Exception:
            return None

        return None

    def _install_forge_once(self, forge_version: str, java_executable: str):
        callback = self._callback_dict()
        minecraft_launcher_lib.forge.install_forge_version(
            forge_version,
            str(self.minecraft_dir),
            callback=callback,
            java=java_executable
        )

    def resolve_forge_version(self, minecraft_version: str, loader_version: str) -> str:
        if loader_version:
            forge_version = loader_version
        else:
            forge_version = minecraft_launcher_lib.forge.find_forge_version(minecraft_version)

        if not forge_version:
            raise LauncherError(f"Не удалось подобрать Forge для Minecraft {minecraft_version}.")

        if not minecraft_launcher_lib.forge.is_forge_version_valid(forge_version):
            raise LauncherError(f"Некорректная версия Forge: {forge_version}")

        return forge_version

    def get_expected_forge_installed_version(self, minecraft_version: str, forge_version: str) -> str | None:
        try:
            return minecraft_launcher_lib.forge.forge_to_installed_version(forge_version)
        except Exception:
            pass

        # Fallback для старых Forge, если forge_to_installed_version недоступен/не справился.
        if forge_version.startswith(minecraft_version + "-"):
            build = forge_version[len(minecraft_version) + 1:]
            return f"{minecraft_version}-forge-{build}"

        return None

    def find_existing_forge_install(self, minecraft_version: str, forge_version: str) -> str | None:
        expected = self.get_expected_forge_installed_version(minecraft_version, forge_version)
        if expected:
            expected_json = self.minecraft_dir / "versions" / expected / f"{expected}.json"
            if expected_json.exists():
                return expected

        try:
            installed = minecraft_launcher_lib.utils.get_installed_versions(str(self.minecraft_dir))
        except Exception:
            installed = []

        forge_tail = forge_version
        if forge_tail.startswith(minecraft_version + "-"):
            forge_tail = forge_tail[len(minecraft_version) + 1:]

        for item in installed:
            version_id = item.get("id", "")
            lowered = version_id.lower()
            if minecraft_version.lower() in lowered and "forge" in lowered:
                if forge_version.lower() in lowered or forge_tail.lower() in lowered:
                    return version_id

        return None

    def install_forge(self, minecraft_version: str, loader_version: str, java_executable: str) -> str:
        self.emit_status(f"Устанавливаю/проверяю Minecraft {minecraft_version}...")
        minecraft_launcher_lib.install.install_minecraft_version(
            minecraft_version,
            str(self.minecraft_dir),
            callback=self._callback_dict()
        )
        self.ensure_clean_vanilla_for_legacy_forge()

        self.emit_status(f"Устанавливаю/проверяю Forge для Minecraft {minecraft_version}...")

        forge_version = self.resolve_forge_version(minecraft_version, loader_version)

        existing = self.find_existing_forge_install(minecraft_version, forge_version)
        if existing:
            self.emit_log(f"Forge уже установлен вручную/ранее. Будет запускаться версия: {existing}")
            return existing

        if not minecraft_launcher_lib.forge.supports_automatic_install(forge_version):
            existing = self.find_existing_forge_install(minecraft_version, forge_version)
            if existing:
                self.emit_log(f"Forge уже установлен вручную. Будет запускаться версия: {existing}")
                return existing

            mode = (self.config.get("forge_install_mode") or "auto").lower()
            if mode in ("manual", "auto_or_manual", "manual_only"):
                raise LauncherError(
                    f"Forge {forge_version} требует ручной установки.\n"
                    "Нажми «Ручной Forge Installer», выбери Install client и укажи папку этой сборки."
                )

            raise LauncherError(
                f"Forge {forge_version} не поддерживает автоматическую установку через minecraft-launcher-lib.\n"
                "В настройках сборки переключи Forge-режим на «Ручной/старый Forge» "
                "и нажми «Ручной Forge Installer»."
            )

        last_error = None
        for attempt in range(2):
            try:
                self._install_forge_once(forge_version, java_executable)
                installed = self.find_existing_forge_install(minecraft_version, forge_version)
                if installed:
                    self.emit_log(f"Будет запускаться версия: {installed}")
                    return installed

                expected = self.get_expected_forge_installed_version(minecraft_version, forge_version)
                if expected:
                    self.emit_log(f"Будет запускаться версия: {expected}")
                    return expected

                return self.find_installed_version_by_loader(minecraft_version, "forge", forge_version)
            except Exception as exc:
                last_error = exc
                error_text = str(exc)
                bad_path = self._extract_bad_checksum_path(error_text)

                if attempt == 0 and bad_path:
                    self.emit_log(f"Обнаружена битая/устаревшая зависимость Forge, удаляю и пробую ещё раз: {bad_path}")
                    try:
                        bad_path.unlink()
                    except Exception as unlink_exc:
                        self.emit_log(f"Не удалось удалить файл: {unlink_exc}")
                    continue

                if "wrong checksum" in error_text.lower():
                    raise LauncherError(
                        f"Не удалось установить Forge {forge_version} для Minecraft {minecraft_version}: checksum не совпал.\n"
                        "Лаунчер уже попробовал удалить битую зависимость и повторить установку. "
                        "Если ошибка повторяется, вероятно, Forge/библиотека ожидают другой файл зависимости.\n"
                        f"Подробности: {error_text}"
                    ) from exc

                raise LauncherError(
                    f"Не удалось установить Forge {forge_version} для Minecraft {minecraft_version}.\n"
                    f"Причина: {error_text}"
                ) from exc

        raise LauncherError(f"Не удалось установить Forge {forge_version}: {last_error}")

    def ensure_launcher_profiles_json(self):
        """
        Old Forge installers refuse to install into a clean custom instance unless
        launcher_profiles.json exists. A minimal launcher profile is enough.
        """
        profiles_path = self.minecraft_dir / "launcher_profiles.json"
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        profile_id = "StoneLightLauncher"
        profile_name = self.config.get("instance_name") or "StoneLight Instance"
        minecraft_version = self.config.get("minecraft_version") or "unknown"

        if profiles_path.exists():
            try:
                data = json.loads(profiles_path.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    data = {}
            except Exception:
                backup = profiles_path.with_suffix(".json.bak")
                try:
                    shutil.copy2(profiles_path, backup)
                    self.emit_log(f"Старый launcher_profiles.json не читается, создан backup: {backup.name}")
                except Exception:
                    pass
                data = {}
        else:
            data = {}

        profiles = data.get("profiles")
        if not isinstance(profiles, dict):
            profiles = {}

        profiles[profile_id] = {
            "name": profile_name,
            "type": "custom",
            "created": profiles.get(profile_id, {}).get("created", now),
            "lastUsed": now,
            "lastVersionId": minecraft_version,
            "gameDir": str(self.minecraft_dir)
        }

        data["profiles"] = profiles
        data["selectedProfile"] = profile_id
        data.setdefault("clientToken", str(uuid.uuid4()))
        data.setdefault("authenticationDatabase", {})
        data.setdefault("launcherVersion", {
            "name": self.config.get("launcher_name", "StoneLight Launcher"),
            "format": 21
        })

        profiles_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        self.emit_log(f"Создан/обновлён launcher_profiles.json для Forge Installer: {profiles_path}")

    def forge_installer_url(self, forge_version: str) -> str:
        return f"https://maven.minecraftforge.net/net/minecraftforge/forge/{forge_version}/forge-{forge_version}-installer.jar"

    def get_forge_installer_jar(self, forge_version: str) -> Path:
        installers_dir = self.cache_dir / "forge_installers"
        installers_dir.mkdir(parents=True, exist_ok=True)
        installer_path = installers_dir / f"forge-{forge_version}-installer.jar"

        if installer_path.exists() and installer_path.stat().st_size > 0:
            self.emit_log(f"Использую кэшированный Forge Installer: {installer_path.name}")
            return installer_path

        self.emit_status(f"Скачиваю Forge Installer {forge_version}...")
        self.download_file(self.forge_installer_url(forge_version), installer_path)
        return installer_path

    def javaw_for_gui_process(self, java_executable: str) -> str:
        java_executable = (java_executable or "java").strip().strip('"')
        path = Path(java_executable)
        if path.name.lower() == "java.exe":
            javaw = path.with_name("javaw.exe")
            if javaw.exists():
                return str(javaw)
        return java_executable

    def create_forge_installer_cmd(self, forge_version: str, java_executable: str, installer_path: Path) -> Path:
        helpers_dir = self.cache_dir / "forge_installers"
        helpers_dir.mkdir(parents=True, exist_ok=True)

        helper_path = helpers_dir / f"run_forge_{forge_version}_installer.cmd"
        java_path = self.javaw_for_gui_process(java_executable)

        helper_text = (
            "@echo off\r\n"
            "cd /d \"%~dp0\"\r\n"
            "echo Starting Forge Installer...\r\n"
            f"echo Java: {java_path}\r\n"
            f"echo Installer: {installer_path}\r\n"
            f"echo Target Minecraft dir: {self.minecraft_dir}\r\n"
            f"\"{java_path}\" -jar \"{installer_path}\"\r\n"
            "echo.\r\n"
            "echo Forge Installer process finished or failed.\r\n"
            "pause\r\n"
        )

        helper_path.write_text(helper_text, encoding="ascii", errors="ignore")
        return helper_path

    def launch_forge_installer_jar(self, forge_version: str, java_executable: str) -> subprocess.Popen:
        installer_path = self.get_forge_installer_jar(forge_version)
        installer_java = self.javaw_for_gui_process(java_executable)
        helper_path = self.create_forge_installer_cmd(forge_version, java_executable, installer_path)

        self.emit_status("Открываю окно Forge Installer...")
        self.emit_log(f"Forge Installer jar: {installer_path}")
        self.emit_log(f"Java для установщика: {installer_java}")
        self.emit_log(f"Fallback .cmd для ручного запуска: {helper_path}")

        # Важно: для GUI-установщика НЕ используем STARTF_USESHOWWINDOW/SW_HIDE.
        # В v0.5.10 это могло скрывать само окно Forge Installer.
        # javaw.exe не создаёт пустую консоль, а GUI-окно остаётся видимым.
        process = subprocess.Popen(
            [installer_java, "-jar", str(installer_path)],
            cwd=str(self.minecraft_dir),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True
        )
        return process

    def run_forge_installer_manual(self, java_executable: str) -> str | None:
        java_executable = self.resolve_java_executable(java_executable)
        self.check_java_compatibility(java_executable)
        minecraft_version = self.config["minecraft_version"]
        forge_version = self.resolve_forge_version(
            minecraft_version,
            self.config.get("fabric_loader_version", "") or ""
        )

        self.emit_status(f"Подготовка ручного Forge Installer: {forge_version}")
        self.emit_log(f"Папка сборки для установки Forge: {self.minecraft_dir}")
        self.emit_log("В Forge Installer выбери: Install client.")
        self.emit_log("Путь установки должен быть именно папкой сборки выше, а не обычной .minecraft.")

        self.ensure_config_dirs()
        self.ensure_launcher_profiles_json()

        # Установим vanilla-часть заранее, чтобы папка сборки была полноценной.
        minecraft_launcher_lib.install.install_minecraft_version(
            minecraft_version,
            str(self.minecraft_dir),
            callback=self._callback_dict()
        )

        already = self.find_existing_forge_install(minecraft_version, forge_version)
        if already:
            self.emit_status(f"Forge уже установлен: {already}")
            return already

        try:
            self.launch_forge_installer_jar(forge_version, java_executable)
        except Exception as exc:
            raise LauncherError(
                f"Не удалось запустить ручной Forge Installer для {forge_version}.\n"
                f"Причина: {exc}"
            ) from exc

        self.emit_status(r"Forge Installer запущен. Если окно не появилось, открой fallback .cmd из data\cache\forge_installers. После установки нажми «Проверить Forge» или «Играть».")
        self.emit_log(
            "Лаунчер больше не ждёт закрытия Forge Installer, чтобы GUI не зависал. "
            "Установи Forge в открывшемся окне, затем вернись в лаунчер."
        )
        return None

    def check_forge_installed(self) -> str | None:
        minecraft_version = self.config["minecraft_version"]
        forge_version = self.resolve_forge_version(
            minecraft_version,
            self.config.get("fabric_loader_version", "") or ""
        )

        installed = self.find_existing_forge_install(minecraft_version, forge_version)
        if installed:
            self.emit_status(f"Forge найден: {installed}")
            return installed

        self.emit_status(f"Forge {forge_version} не найден в этой сборке.")
        self.emit_log(f"Ожидаемая папка сборки: {self.minecraft_dir}")
        return None

    def find_installed_version_by_loader(self, minecraft_version: str, loader: str, loader_version: str) -> str:
        installed = minecraft_launcher_lib.utils.get_installed_versions(str(self.minecraft_dir))
        ids = [v["id"] for v in installed]
        for version_id in ids:
            lowered = version_id.lower()
            if loader.lower() in lowered and minecraft_version.lower() in lowered:
                if not loader_version or loader_version.lower() in lowered:
                    return version_id

        raise LauncherError(
            "Не смог определить ID установленной версии.\n"
            "Установленные версии:\n" + "\n".join(f" - {i}" for i in ids)
        )

    def ensure_config_dirs(self):
        folders = ["config", "resourcepacks", "shaderpacks", "screenshots"]
        loader = (self.config.get("loader") or "vanilla").lower()
        if loader != "vanilla":
            folders.insert(0, "mods")
        for name in folders:
            (self.game_dir / name).mkdir(parents=True, exist_ok=True)

    def ensure_server_list(self):
        if not self.config.get("ensure_server_in_list", False):
            return

        server_ip = (self.config.get("server_ip") or "").strip()
        if not server_ip:
            return

        server_name = self.config.get("server_list_name") or self.config.get("instance_name") or "StoneLight"
        self.emit_status("Проверяю список серверов Minecraft...")
        ensure_server_in_list(
            self.game_dir,
            server_name,
            server_ip,
            log=self.emit_log
        )

    def offline_uuid(self, username: str) -> str:
        return uuid.uuid3(uuid.NAMESPACE_DNS, "OfflinePlayer:" + username).hex

    def apply_fullscreen_preference(self, fullscreen: bool):
        """
        Applies global fullscreen/windowed preference through options.txt.
        This is more reliable across old and new Minecraft versions than
        relying only on launch arguments.
        """
        options_path = self.game_dir / "options.txt"
        options_path.parent.mkdir(parents=True, exist_ok=True)

        lines = []
        if options_path.exists():
            try:
                lines = options_path.read_text(encoding="utf-8", errors="replace").splitlines()
            except Exception:
                lines = []

        value = "true" if fullscreen else "false"
        updated = False
        new_lines = []

        for line in lines:
            if line.startswith("fullscreen:"):
                new_lines.append(f"fullscreen:{value}")
                updated = True
            else:
                new_lines.append(line)

        if not updated:
            new_lines.append(f"fullscreen:{value}")

        options_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        self.emit_log(f"Global launch setting: fullscreen={value}")


    def build_auth_options(self, account: dict | None, fallback_username: str) -> dict:
        account = account or {}
        account_type = account.get("type", "offline")

        if account_type == "microsoft":
            username = (account.get("username") or fallback_username or "").strip()
            uuid_value = (account.get("uuid") or "").replace("-", "").strip()
            access_token = account.get("access_token") or ""

            if not username or not uuid_value or not access_token:
                raise LauncherError("Лицензионный аккаунт неполный. Выполни Microsoft-вход заново.")

            return {
                "username": username,
                "uuid": uuid_value,
                "token": access_token,
            }

        username = (account.get("username") or fallback_username or "Player").strip()
        return {
            "username": username,
            "uuid": self.offline_uuid(username),
            "token": "0",
        }


    def launch_game(self, username: str, ram_mb: int, java_executable: str, version_id: str, account: dict | None = None):
        username = username.strip() or (account or {}).get("username", "Player")

        global_launch = normalize_global_launch_settings(load_user_settings(), self.base_config, fallback_max=ram_mb)
        ram_min_mb = global_launch["ram_min_mb"]
        ram_max_mb = global_launch["ram_max_mb"]
        fullscreen = global_launch["fullscreen"]

        self.apply_fullscreen_preference(fullscreen)
        self.emit_log(f"Global launch memory: Xms={ram_min_mb}M, Xmx={ram_max_mb}M")

        auth_options = self.build_auth_options(account, username)

        options = {
            "username": auth_options["username"],
            "uuid": auth_options["uuid"],
            "token": auth_options["token"],
            "executablePath": java_executable,
            "defaultExecutablePath": java_executable,
            "jvmArguments": [
                f"-Xmx{ram_max_mb}M",
                f"-Xms{ram_min_mb}M",
            ],
            "launcherName": self.config.get("launcher_name", "StoneLight Launcher"),
            "launcherVersion": self.config.get("launcher_version", "0.5.24"),
            "gameDirectory": str(self.game_dir),
            "customResolution": True,
            "resolutionWidth": str(self.config.get("resolution_width", "1280")),
            "resolutionHeight": str(self.config.get("resolution_height", "720")),
        }

        server_ip = (self.config.get("server_ip") or "").strip()
        if server_ip:
            options["server"] = server_ip
            options["port"] = str(self.config.get("server_port", "25565"))

        self.emit_status("Формирую команду запуска...")
        self.ensure_legacy_forge_json_jar_field(version_id)

        command = minecraft_launcher_lib.command.get_minecraft_command(
            version_id,
            str(self.minecraft_dir),
            options
        )
        command = self.patch_legacy_forge_classpath(command, version_id)
        command = self.patch_legacy_natives_path(command)
        self.write_debug_launch_command(command, version_id)

        existing_process = self.get_running_process()
        if existing_process:
            raise LauncherError("Эта сборка уже запущена. Используй «Остановить», если процесс завис.")

        self.emit_status("Запускаю Minecraft...")
        self.emit_console("=== Minecraft process starting ===")

        creationflags = 0
        if os.name == "nt":
            # Важно: CREATE_NO_WINDOW убирает пустую консоль java.exe,
            # но не должен скрывать LWJGL-окно Minecraft.
            # Не используем STARTF_USESHOWWINDOW/SW_HIDE для игры:
            # на старом Forge/LWJGL это может спрятать само окно Minecraft.
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            self.emit_log("Windows launch: CREATE_NO_WINDOW включён, SW_HIDE отключён.")

        process = subprocess.Popen(
            command,
            cwd=str(self.minecraft_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            errors="replace",
            bufsize=1,
            creationflags=creationflags
        )

        self.register_running_process(process)
        threading.Thread(target=self._read_process_output, args=(process,), daemon=True).start()
        self.emit_status("Minecraft запущен.")
        return process

    def _read_process_output(self, process: subprocess.Popen):
        try:
            if process.stdout:
                for line in process.stdout:
                    self.emit_console(line)
            code = process.wait()
            self.emit_console(f"=== Minecraft process exited with code {code} ===")
        except Exception as exc:
            self.emit_console(f"=== Ошибка чтения вывода Minecraft: {exc} ===")
        finally:
            self.unregister_running_process(process)

    def repair_instance(self, java_executable: str):
        java_executable = self.resolve_java_executable(java_executable)
        self.check_java_compatibility(java_executable)
        self.ensure_config_dirs()

        minecraft_version = self.config["minecraft_version"]

        if self.is_legacy_forge_instance():
            self.repair_vanilla_version(minecraft_version)
            installed_version = self.check_forge_installed()
            if installed_version:
                self.ensure_legacy_forge_json_jar_field(installed_version)
                self.ensure_legacy_version_libraries(installed_version)
                self.ensure_expected_legacy_guava()
            self.ensure_legacy_natives()
            self.emit_status("Legacy Forge repair завершён.")
            return

        version_dir = self.vanilla_version_dir(minecraft_version)
        if version_dir.exists():
            backup = version_dir.with_name(f"{minecraft_version}_repair_backup")
            if backup.exists():
                shutil.rmtree(backup)
            shutil.move(str(version_dir), str(backup))
            self.emit_log(f"Папка версии перемещена в backup: {backup}")

        minecraft_launcher_lib.install.install_minecraft_version(
            minecraft_version,
            str(self.minecraft_dir),
            callback=self._callback_dict()
        )
        self.emit_status("Repair сборки завершён.")

    def update_only(self, java_executable: str, force_download: bool = True):
        java_executable = self.resolve_java_executable(java_executable)
        self.check_java_compatibility(java_executable)
        self.ensure_config_dirs()
        self.ensure_modpack(force_download=force_download)
        self.ensure_server_list()
        version_id = self.install_minecraft_and_loader(java_executable)
        self.emit_status(f"Сборка обновлена/установлена. Версия запуска: {version_id}")

    def run_full(self, username: str, ram_mb: int, java_executable: str, force_modpack_download: bool = False, account: dict | None = None):
        java_executable = self.resolve_java_executable(java_executable)
        self.check_java_compatibility(java_executable)
        self.ensure_config_dirs()
        self.ensure_modpack(force_download=force_modpack_download)
        self.ensure_server_list()
        version_id = self.install_minecraft_and_loader(java_executable)
        self.launch_game(username, ram_mb, java_executable, version_id, account=account)


def load_user_settings() -> dict:
    if USER_SETTINGS_PATH.exists():
        try:
            return json.loads(USER_SETTINGS_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_user_settings(settings: dict):
    USER_SETTINGS_PATH.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8")


def get_minecraft_versions(include_snapshots: bool = True, limit: int | None = None) -> list[str]:
    versions = minecraft_launcher_lib.utils.get_version_list()
    result = []
    for item in versions:
        version_id = item.get("id")
        version_type = item.get("type", "")
        if not version_id:
            continue
        if not include_snapshots and version_type != "release":
            continue
        result.append(version_id)
        if limit and len(result) >= limit:
            break
    return result


def get_latest_versions() -> dict:
    return minecraft_launcher_lib.utils.get_latest_version()


def get_available_mod_loaders() -> list[str]:
    base = ["vanilla", "fabric", "forge", "quilt", "neoforge"]
    result = []
    for item in base:
        if item not in result:
            result.append(item)
    return result


def get_loader_versions(loader: str, minecraft_version: str, stable_only: bool = False, automatic_only: bool = True) -> list[str]:
    loader = (loader or "").strip().lower()
    minecraft_version = (minecraft_version or "").strip()

    if loader in ("", "vanilla"):
        return []

    try:
        if loader == "forge":
            values = minecraft_launcher_lib.forge.list_forge_versions()
            if minecraft_version:
                values = [v for v in values if str(v).startswith(minecraft_version + "-")]
            if automatic_only:
                values = [v for v in values if minecraft_launcher_lib.forge.supports_automatic_install(v)]
            return values

        if loader in ("fabric", "quilt", "neoforge"):
            mod_loader = minecraft_launcher_lib.mod_loader.get_mod_loader(loader)
            try:
                return list(mod_loader.get_loader_versions(minecraft_version, stable_only))
            except TypeError:
                return list(mod_loader.get_loader_versions(minecraft_version))

        mod_loader = minecraft_launcher_lib.mod_loader.get_mod_loader(loader)
        return list(mod_loader.get_loader_versions(minecraft_version, stable_only))
    except Exception:
        # Deprecated module fallback for Fabric/Quilt loader lists.
        try:
            if loader == "fabric":
                versions = minecraft_launcher_lib.fabric.get_all_loader_versions()
                return [str(v.get("version", "")) for v in versions if v.get("version")]
            if loader == "quilt":
                versions = minecraft_launcher_lib.quilt.get_all_loader_versions()
                return [str(v.get("version", "")) for v in versions if v.get("version")]
        except Exception:
            pass
        return []
