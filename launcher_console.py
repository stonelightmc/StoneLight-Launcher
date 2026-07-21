from accounts import add_or_update_offline_account, get_selected_account, load_accounts, select_account, validate_offline_username
from instances import get_selected_instance, instance_label, load_instances, select_instance
from launcher_core import LauncherCore, load_user_settings, save_user_settings


def choose_account() -> str:
    data = load_accounts()
    accounts = data.get("accounts", [])

    if accounts:
        print("Аккаунты:")
        for i, acc in enumerate(accounts, start=1):
            marker = "*" if data.get("selected_account_id") == acc.get("id") else " "
            print(f"{i}. {marker} {acc.get('username')} [offline]")

        choice = input("Номер аккаунта или новый ник: ").strip()

        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(accounts):
                acc = accounts[index]
                select_account(acc["id"])
                return acc["username"]

        if choice:
            data, _ = add_or_update_offline_account(choice)
            acc = get_selected_account(data)
            return acc["username"]

        acc = get_selected_account(data)
        if acc:
            return acc["username"]

    username = input("Новый offline-ник: ").strip() or "StoneLightPlayer"
    ok, message = validate_offline_username(username)
    if not ok:
        raise ValueError(message)

    data, _ = add_or_update_offline_account(username)
    acc = get_selected_account(data)
    return acc["username"]


def choose_instance(config: dict) -> dict:
    data = load_instances(config)
    instances = data.get("instances", [])

    print("Сборки:")
    for i, inst in enumerate(instances, start=1):
        marker = "*" if data.get("selected_instance_id") == inst.get("id") else " "
        print(f"{i}. {marker} {instance_label(inst)}")

    choice = input("Номер сборки или Enter для выбранной: ").strip()

    if choice.isdigit():
        index = int(choice) - 1
        if 0 <= index < len(instances):
            inst = instances[index]
            select_instance(config, inst["id"])
            return inst

    inst = get_selected_instance(data)
    if inst:
        return inst

    raise ValueError("Нет доступных сборок.")


def main():
    settings = load_user_settings()
    temp_core = LauncherCore()
    config = temp_core.base_config

    instance = choose_instance(config)
    username = choose_account()

    ram_text = input(f"RAM МБ [{settings.get('ram_mb', config.get('default_ram_mb', 4096))}]: ").strip()
    ram_mb = int(ram_text or settings.get("ram_mb", config.get("default_ram_mb", 4096)))

    java_executable = input(f"Java [{settings.get('java_executable', config.get('java_executable', 'java'))}]: ").strip()
    if not java_executable:
        java_executable = settings.get("java_executable", config.get("java_executable", "java"))

    save_user_settings({
        "username": username,
        "ram_mb": ram_mb,
        "java_executable": java_executable,
        "selected_instance_id": instance.get("id", ""),
    })

    core = LauncherCore(instance=instance)
    core.run_full(username, ram_mb, java_executable)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nОтменено.")
    except Exception as exc:
        print("\nОшибка:")
        print(exc)
        print("\nЕсли не понятно, скинь мне весь вывод консоли или файл data/launcher.log.")
        raise
