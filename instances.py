import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INSTANCES_PATH = ROOT / "instances.json"

INSTANCE_NAME_RE = re.compile(r"^[A-Za-zА-Яа-яЁёІіЇїЄєҐґ0-9 _.-]{2,32}$")


def slugify_instance_name(name: str) -> str:
    name = (name or "").strip()
    translit = {
        "а": "a", "б": "b", "в": "v", "г": "g", "ґ": "g", "д": "d", "е": "e", "є": "ye",
        "ё": "e", "ж": "zh", "з": "z", "и": "i", "і": "i", "ї": "yi", "й": "y",
        "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
        "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "c", "ч": "ch",
        "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    }

    result = []
    for ch in name.lower():
        if ch in translit:
            result.append(translit[ch])
        elif ch.isalnum():
            result.append(ch)
        elif ch in " _.-":
            result.append("_")

    slug = "".join(result)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or f"instance_{int(time.time())}"


def validate_instance_name(name: str) -> tuple[bool, str]:
    name = (name or "").strip()

    if not name:
        return False, "Название сборки не может быть пустым."

    if not INSTANCE_NAME_RE.match(name):
        return False, "Название сборки: 2-32 символа, буквы/цифры/пробел/._-."

    return True, ""


def ensure_unique_instance_name(data: dict, name: str, current_id: str | None = None):
    normalized_name = (name or "").strip().casefold()
    slug = slugify_instance_name(name)

    for inst in data.get("instances", []):
        if current_id and inst.get("id") == current_id:
            continue

        existing_name = (inst.get("name") or "").strip().casefold()
        existing_slug = slugify_instance_name(inst.get("name") or "")

        if existing_name == normalized_name:
            raise ValueError(f"Сборка с названием «{name}» уже существует.")

        if existing_slug == slug:
            raise ValueError(
                f"Название «{name}» даёт ту же папку/ID, что и сборка «{inst.get('name', '')}». "
                "Выбери другое название."
            )


def instance_label(instance: dict) -> str:
    loader = instance.get("loader", "vanilla")
    mc = instance.get("minecraft_version", "?")
    suffix = "официальная" if instance.get("locked") else "пользовательская"
    return f"{instance.get('name', 'Instance')}  [{mc} / {loader} / {suffix}]"


def default_official_instance(config: dict) -> dict:
    return {
        "id": "stonelight",
        "name": "StoneLight",
        "locked": True,
        "official": True,
        "game_directory": "data/instances/StoneLight/.minecraft",
        "minecraft_version": config.get("minecraft_version", "26.1.2"),
        "version_type": "release",
        "loader": config.get("loader", "fabric"),
        "loader_version": config.get("fabric_loader_version", "0.19.3"),
        "java_preset": "auto",
        "java_executable": "",
        "ram_mb": int(config.get("default_ram_mb", 4096)),
        "forge_install_mode": "auto",
        "install_modpack": True,
        "modpack_url": config.get("mods_zip_url", ""),
        "modpack_sha256": config.get("mods_zip_sha256", ""),
        "server_ip": config.get("server_ip", "stonelight.apexmc.co"),
        "server_port": str(config.get("server_port", "25565")),
        "ensure_server_in_list": True,
        "server_list_name": config.get("server_list_name", "StoneLight"),
    }


def normalize_instance(inst: dict, config: dict) -> dict | None:
    if not isinstance(inst, dict):
        return None

    inst_id = inst.get("id", "")
    if not inst_id:
        return None

    if inst_id == "stonelight":
        official = default_official_instance(config)
        # Официальная сборка защищена от смены версии/loader/модпака,
        # но пользовательские параметры запуска должны сохраняться.
        for key in (
            "java_preset", "java_executable", "ram_mb",
            "server_ip", "server_port", "ensure_server_in_list", "server_list_name"
        ):
            if key in inst:
                official[key] = inst[key]
        return official

    name = (inst.get("name") or "").strip()
    ok, _ = validate_instance_name(name)
    if not ok:
        return None

    loader = (inst.get("loader") or "vanilla").strip().lower()
    if loader in ("none", "no", "без", "без модлоадера"):
        loader = "vanilla"

    mc_version = inst.get("minecraft_version") or config.get("minecraft_version", "26.1.2")
    version_type = inst.get("version_type") or "release"

    return {
        "id": inst_id,
        "name": name,
        "locked": bool(inst.get("locked", False)),
        "official": bool(inst.get("official", False)),
        "game_directory": inst.get("game_directory") or f"data/instances/{slugify_instance_name(name)}/.minecraft",
        "minecraft_version": mc_version,
        "version_type": version_type,
        "loader": loader,
        "loader_version": inst.get("loader_version", ""),
        "java_preset": inst.get("java_preset", "auto"),
        "java_executable": inst.get("java_executable", ""),
        "ram_mb": int(inst.get("ram_mb", config.get("default_ram_mb", 4096)) or config.get("default_ram_mb", 4096)),
        "forge_install_mode": inst.get("forge_install_mode", "auto"),
        "install_modpack": bool(inst.get("install_modpack", False)),
        "modpack_url": inst.get("modpack_url", ""),
        "modpack_sha256": inst.get("modpack_sha256", ""),
        "server_ip": inst.get("server_ip", ""),
        "server_port": str(inst.get("server_port", "25565")),
        "ensure_server_in_list": bool(inst.get("ensure_server_in_list", False)),
        "server_list_name": inst.get("server_list_name", name),
    }


def default_instances_data(config: dict) -> dict:
    official = default_official_instance(config)
    return {
        "selected_instance_id": official["id"],
        "instances": [official]
    }


def load_instances(config: dict) -> dict:
    if not INSTANCES_PATH.exists():
        data = default_instances_data(config)
        save_instances(data)
        return data

    try:
        data = json.loads(INSTANCES_PATH.read_text(encoding="utf-8"))
    except Exception:
        data = default_instances_data(config)
        save_instances(data)
        return data

    if not isinstance(data, dict):
        data = default_instances_data(config)

    raw_instances = data.get("instances")
    if not isinstance(raw_instances, list):
        raw_instances = []

    official = default_official_instance(config)
    cleaned = []
    seen = set()
    official_inserted = False

    for raw in raw_instances:
        inst = normalize_instance(raw, config)
        if not inst:
            continue

        if inst["id"] == "stonelight":
            if not official_inserted:
                cleaned.append(official)
                seen.add("stonelight")
                official_inserted = True
            continue

        if inst["id"] in seen:
            continue

        seen.add(inst["id"])
        cleaned.append(inst)

    if not official_inserted:
        cleaned.insert(0, official)

    selected = data.get("selected_instance_id", "")
    if not selected or selected not in {i["id"] for i in cleaned}:
        selected = "stonelight"

    result = {
        "selected_instance_id": selected,
        "instances": cleaned
    }
    save_instances(result)
    return result


def save_instances(data: dict):
    INSTANCES_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def find_instance_by_id(data: dict, instance_id: str) -> dict | None:
    for inst in data.get("instances", []):
        if inst.get("id") == instance_id:
            return inst
    return None


def find_instance_by_label(data: dict, label: str) -> dict | None:
    for inst in data.get("instances", []):
        if instance_label(inst) == label:
            return inst
    return None


def get_selected_instance(data: dict) -> dict | None:
    selected_id = data.get("selected_instance_id", "")
    if selected_id:
        found = find_instance_by_id(data, selected_id)
        if found:
            return found
    instances = data.get("instances", [])
    return instances[0] if instances else None


def select_instance(config: dict, instance_id: str) -> dict:
    data = load_instances(config)
    if find_instance_by_id(data, instance_id):
        data["selected_instance_id"] = instance_id
        save_instances(data)
    return data


def create_custom_instance(config: dict, name: str, minecraft_version: str, loader: str = "vanilla", loader_version: str = "", version_type: str = "release") -> tuple[dict, str]:
    name = (name or "").strip()
    ok, message = validate_instance_name(name)
    if not ok:
        raise ValueError(message)

    minecraft_version = (minecraft_version or "").strip()
    if not minecraft_version:
        raise ValueError("Укажи версию Minecraft.")

    loader = (loader or "vanilla").strip().lower()
    if loader in ("none", "no", "без", "без модлоадера"):
        loader = "vanilla"

    data = load_instances(config)
    ensure_unique_instance_name(data, name)
    slug = slugify_instance_name(name)
    instance_id = slug

    existing_ids = {inst["id"] for inst in data.get("instances", [])}
    if instance_id in existing_ids:
        raise ValueError(f"Сборка с ID «{instance_id}» уже существует. Выбери другое название.")

    instance = {
        "id": instance_id,
        "name": name,
        "locked": False,
        "official": False,
        "game_directory": f"data/instances/{slug}/.minecraft",
        "minecraft_version": minecraft_version,
        "version_type": version_type or "release",
        "loader": loader,
        "loader_version": loader_version.strip(),
        "java_preset": "auto",
        "java_executable": "",
        "ram_mb": int(config.get("default_ram_mb", 4096)),
        "forge_install_mode": "auto",
        "install_modpack": False,
        "modpack_url": "",
        "modpack_sha256": "",
        "server_ip": "",
        "server_port": "25565",
        "ensure_server_in_list": False,
        "server_list_name": name,
    }

    data["instances"].append(instance)
    data["selected_instance_id"] = instance_id
    save_instances(data)
    return data, "Сборка создана."


def update_instance(config: dict, instance_id: str, updates: dict) -> tuple[dict, str]:
    data = load_instances(config)
    inst = find_instance_by_id(data, instance_id)
    if not inst:
        raise ValueError("Сборка не найдена.")

    if "name" in updates:
        name = (updates.get("name") or "").strip()
        ok, message = validate_instance_name(name)
        if not ok:
            raise ValueError(message)
        ensure_unique_instance_name(data, name, current_id=instance_id)

    if inst.get("locked"):
        allowed_locked = {
            "server_ip", "server_port", "ensure_server_in_list", "server_list_name",
            "java_preset", "java_executable", "ram_mb"
        }
        for key in updates:
            if key not in allowed_locked:
                raise ValueError("Официальную сборку StoneLight нельзя редактировать через это окно.")

    for key, value in updates.items():
        inst[key] = value

    save_instances(data)
    return data, "Сборка обновлена."


def delete_instance(config: dict, instance_id: str) -> tuple[dict, str]:
    data = load_instances(config)
    inst = find_instance_by_id(data, instance_id)

    if not inst:
        return data, "Сборка не найдена."

    if inst.get("locked"):
        raise ValueError("Официальную сборку StoneLight нельзя удалить из лаунчера.")

    data["instances"] = [i for i in data["instances"] if i.get("id") != instance_id]

    if data.get("selected_instance_id") == instance_id:
        data["selected_instance_id"] = "stonelight"

    save_instances(data)
    return data, "Сборка удалена."
