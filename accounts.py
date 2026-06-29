import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ACCOUNTS_PATH = ROOT / "accounts.json"

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,16}$")


def normalize_username(username: str) -> str:
    return (username or "").strip()


def validate_offline_username(username: str) -> tuple[bool, str]:
    username = normalize_username(username)

    if not username:
        return False, "Ник не может быть пустым."

    if not USERNAME_RE.match(username):
        return False, "Ник должен быть 3-16 символов: латиница, цифры и подчёркивание."

    return True, ""


def default_accounts_data() -> dict:
    return {
        "selected_account_id": "",
        "accounts": []
    }


def is_licensed_account(account: dict) -> bool:
    return (account or {}).get("type") == "microsoft"


def has_licensed_account(data: dict | None = None) -> bool:
    data = data or load_accounts()
    return any(is_licensed_account(acc) for acc in data.get("accounts", []))


def normalize_microsoft_account(acc: dict) -> dict | None:
    username = normalize_username(acc.get("username") or acc.get("name") or acc.get("display_name") or "")
    uuid = (acc.get("uuid") or acc.get("minecraft_id") or acc.get("profile_id") or "").replace("-", "").strip()

    if not username or not uuid:
        return None

    account_id = acc.get("id")
    if not account_id or not str(account_id).startswith("microsoft:"):
        account_id = f"microsoft:{uuid}"

    return {
        "id": account_id,
        "type": "microsoft",
        "username": username,
        "display_name": acc.get("display_name") or username,
        "uuid": uuid,
        "access_token": acc.get("access_token", ""),
        "refresh_token": acc.get("refresh_token", ""),
        "skins": acc.get("skins", []),
        "capes": acc.get("capes", []),
    }


def load_accounts() -> dict:
    if not ACCOUNTS_PATH.exists():
        return default_accounts_data()

    try:
        data = json.loads(ACCOUNTS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return default_accounts_data()

    if not isinstance(data, dict):
        return default_accounts_data()

    accounts = data.get("accounts")
    if not isinstance(accounts, list):
        accounts = []

    cleaned = []
    seen_ids = set()

    # Сначала лицензии, потом offline. Это помогает правилу:
    # offline-аккаунты разрешены только при наличии хотя бы одной лицензии.
    normalized = []
    for acc in accounts:
        if isinstance(acc, dict):
            normalized.append(acc)

    for acc in normalized:
        acc_type = acc.get("type", "offline")

        if acc_type == "microsoft":
            account = normalize_microsoft_account(acc)
            if not account:
                continue

            account_id = account["id"]
            if account_id in seen_ids:
                continue

            seen_ids.add(account_id)
            cleaned.append(account)

    license_exists = any(acc.get("type") == "microsoft" for acc in cleaned)

    for acc in normalized:
        acc_type = acc.get("type", "offline")
        if acc_type != "offline":
            continue

        # Важно: offline без лицензии не храним и не показываем.
        if not license_exists:
            continue

        username = normalize_username(acc.get("username", ""))
        ok, _ = validate_offline_username(username)
        if not ok:
            continue

        account_id = acc.get("id") or f"offline:{username.lower()}"
        if account_id in seen_ids:
            continue

        seen_ids.add(account_id)
        cleaned.append({
            "id": account_id,
            "type": "offline",
            "username": username,
            "display_name": acc.get("display_name") or username
        })

    selected = data.get("selected_account_id", "")
    if selected and selected not in seen_ids:
        selected = cleaned[0]["id"] if cleaned else ""

    return {
        "selected_account_id": selected,
        "accounts": cleaned
    }


def save_accounts(data: dict):
    # Дополнительная страховка: если нет лицензии, offline не сохраняем.
    accounts = data.get("accounts", [])
    has_license = any(acc.get("type") == "microsoft" for acc in accounts if isinstance(acc, dict))
    if not has_license:
        accounts = [acc for acc in accounts if isinstance(acc, dict) and acc.get("type") == "microsoft"]
        data["accounts"] = accounts
        if data.get("selected_account_id", "").startswith("offline:"):
            data["selected_account_id"] = accounts[0]["id"] if accounts else ""

    ACCOUNTS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def account_label(account: dict) -> str:
    if account.get("type") == "offline":
        return f"{account.get('username', 'Player')}  [offline]"
    if account.get("type") == "microsoft":
        return f"{account.get('username', 'Player')}  [licensed]"
    return account.get("display_name") or account.get("username") or "Unknown"


def find_account_by_label(data: dict, label: str) -> dict | None:
    for account in data.get("accounts", []):
        if account_label(account) == label:
            return account
    return None


def find_account_by_id(data: dict, account_id: str) -> dict | None:
    for account in data.get("accounts", []):
        if account.get("id") == account_id:
            return account
    return None


def get_selected_account(data: dict) -> dict | None:
    selected_id = data.get("selected_account_id", "")
    if selected_id:
        found = find_account_by_id(data, selected_id)
        if found:
            return found

    accounts = data.get("accounts", [])
    return accounts[0] if accounts else None


def add_or_update_offline_account(username: str) -> tuple[dict, str]:
    username = normalize_username(username)
    ok, message = validate_offline_username(username)
    if not ok:
        raise ValueError(message)

    data = load_accounts()
    if not has_licensed_account(data):
        raise ValueError(
            "Offline-аккаунты можно добавлять только после входа хотя бы в один лицензионный Microsoft/Minecraft аккаунт."
        )

    account_id = f"offline:{username.lower()}"

    for account in data["accounts"]:
        if account.get("id") == account_id:
            account["username"] = username
            account["display_name"] = username
            data["selected_account_id"] = account_id
            save_accounts(data)
            return data, "Offline-аккаунт обновлён."

    data["accounts"].append({
        "id": account_id,
        "type": "offline",
        "username": username,
        "display_name": username
    })
    data["selected_account_id"] = account_id
    save_accounts(data)
    return data, "Offline-аккаунт добавлен."


def add_or_update_microsoft_account(login_response: dict) -> tuple[dict, str]:
    if not isinstance(login_response, dict):
        raise ValueError("Некорректный ответ Microsoft/Minecraft login.")

    username = normalize_username(login_response.get("name", ""))
    uuid = (login_response.get("id", "") or "").replace("-", "").strip()
    access_token = login_response.get("access_token", "")
    refresh_token = login_response.get("refresh_token", "")

    if not username or not uuid or not access_token:
        raise ValueError("Microsoft login не вернул Minecraft-профиль. Проверь, что на аккаунте куплена Minecraft Java Edition.")

    data = load_accounts()
    account_id = f"microsoft:{uuid}"
    new_account = {
        "id": account_id,
        "type": "microsoft",
        "username": username,
        "display_name": username,
        "uuid": uuid,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "skins": login_response.get("skins", []),
        "capes": login_response.get("capes", []),
    }

    for idx, account in enumerate(data["accounts"]):
        if account.get("id") == account_id:
            data["accounts"][idx] = new_account
            data["selected_account_id"] = account_id
            save_accounts(data)
            return data, "Лицензионный аккаунт обновлён."

    data["accounts"].append(new_account)
    data["selected_account_id"] = account_id
    save_accounts(data)
    return data, "Лицензионный аккаунт добавлен."


def refresh_microsoft_account(account_id: str, client_id: str, redirect_uri: str | None = None, client_secret: str | None = None) -> tuple[dict, str]:
    import minecraft_launcher_lib.microsoft_account as microsoft_account

    data = load_accounts()
    account = find_account_by_id(data, account_id)
    if not account or account.get("type") != "microsoft":
        raise ValueError("Выбранный аккаунт не является лицензионным Microsoft-аккаунтом.")

    refresh_token = account.get("refresh_token")
    if not refresh_token:
        raise ValueError("У аккаунта нет refresh token. Выполни вход Microsoft заново.")

    try:
        try:
            response = microsoft_account.complete_refresh(client_id, client_secret or None, redirect_uri, refresh_token)
        except TypeError:
            response = microsoft_account.complete_refresh(client_id, refresh_token)
    except Exception as exc:
        raise ValueError(f"Не удалось обновить Microsoft-сессию. Войди заново. Детали: {exc}")

    updated, _info = add_or_update_microsoft_account(response)
    return updated, "Лицензионный аккаунт обновлён."


def delete_account(account_id: str) -> tuple[dict, str]:
    data = load_accounts()
    account = find_account_by_id(data, account_id)

    if not account:
        return data, "Аккаунт не найден."

    if account.get("type") == "microsoft":
        other_licenses = [
            acc for acc in data["accounts"]
            if acc.get("type") == "microsoft" and acc.get("id") != account_id
        ]
        offline_accounts = [acc for acc in data["accounts"] if acc.get("type") == "offline"]

        if not other_licenses and offline_accounts:
            raise ValueError(
                "Нельзя удалить последний лицензионный аккаунт, пока есть offline-аккаунты. "
                "Сначала удали offline-аккаунты или добавь другой лицензионный аккаунт."
            )

    before = len(data["accounts"])
    data["accounts"] = [acc for acc in data["accounts"] if acc.get("id") != account_id]

    if len(data["accounts"]) == before:
        return data, "Аккаунт не найден."

    if data.get("selected_account_id") == account_id:
        data["selected_account_id"] = data["accounts"][0]["id"] if data["accounts"] else ""

    save_accounts(data)
    return data, "Аккаунт удалён."


def select_account(account_id: str) -> dict:
    data = load_accounts()
    if find_account_by_id(data, account_id):
        data["selected_account_id"] = account_id
        save_accounts(data)
    return data


def ensure_initial_account(username_hint: str = "") -> dict:
    # Важно: больше не создаём StoneLightPlayer по умолчанию.
    # Без лицензии список аккаунтов должен быть пустым.
    return load_accounts()
