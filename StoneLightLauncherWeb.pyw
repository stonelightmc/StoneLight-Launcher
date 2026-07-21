from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

from app_paths import app_root, bundled_path, ensure_runtime_files


def _show_error(title: str, text: str):
    try:
        from tkinter import messagebox
        messagebox.showerror(title, text)
    except Exception:
        print(text, file=sys.stderr)


def _resolve_icon_path(root: Path, config: dict) -> Path | None:
    icon_value = str(config.get("window_icon") or "assets/stonelight_launcher.ico").strip()
    if not icon_value:
        return None

    candidates = []
    icon_path = Path(icon_value)
    if icon_path.is_absolute():
        candidates.append(icon_path)
    else:
        candidates.append(root / icon_path)
        candidates.append(bundled_path(icon_value))

    for candidate in candidates:
        try:
            if candidate and candidate.exists() and candidate.is_file():
                return candidate
        except Exception:
            continue
    return None


def _set_windows_app_identity(app_id: str = "StoneLight.Launcher") -> None:
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass


def _window_hwnd(window) -> int:
    native = getattr(window, "native", None)
    if native is None:
        return 0

    for attr in ("Handle", "handle", "hwnd", "_hwnd"):
        try:
            value = getattr(native, attr, None)
            if value is None:
                continue
            if callable(value):
                value = value()
            if hasattr(value, "ToInt64"):
                return int(value.ToInt64())
            if hasattr(value, "ToInt32"):
                return int(value.ToInt32())
            return int(value)
        except Exception:
            continue
    return 0


def _apply_windows_window_icon(window, icon_path: Path | None) -> None:
    if not sys.platform.startswith("win") or not icon_path:
        return

    try:
        import ctypes
        user32 = ctypes.windll.user32
        hwnd = _window_hwnd(window)
        if not hwnd:
            return

        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x0010
        LR_DEFAULTSIZE = 0x0040
        WM_SETICON = 0x0080
        ICON_SMALL = 0
        ICON_BIG = 1

        hicon_big = user32.LoadImageW(None, str(icon_path), IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE)
        hicon_small = user32.LoadImageW(None, str(icon_path), IMAGE_ICON, 16, 16, LR_LOADFROMFILE)

        if hicon_big:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_big)
        if hicon_small:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_small)
    except Exception:
        pass


def main():
    ensure_runtime_files()

    if "--classic" in sys.argv:
        import launcher_gui
        launcher_gui.main()
        return

    try:
        import webview
        from launcher_api import LauncherWebAPI

        root = app_root()
        config_path = root / "config.json"
        import json
        config = json.loads(config_path.read_text(encoding="utf-8"))
        icon_path = _resolve_icon_path(root, config)
        _set_windows_app_identity()

        ui_path = root / "web_ui" / "index.html"
        if not ui_path.exists():
            bundled = bundled_path("web_ui/index.html")
            ui_path = bundled if bundled.exists() else ui_path
        if not ui_path.exists():
            raise FileNotFoundError(f"Не найден web UI: {ui_path}")
        if not ui_path.is_file():
            raise FileNotFoundError(f"Web UI path is not a file: {ui_path}")

        # Serve the trusted local UI through pywebview's internal HTTP server.
        # Relative URLs are the supported path for static assets and the JS bridge.
        os.chdir(root)
        desktop_url = "web_ui/index.html?v=0.6.66#desktop=1"

        api = LauncherWebAPI()
        window_kwargs = {
            "title": f"StoneLight Launcher v{config.get('launcher_version', '0.6.66')}",
            "url": desktop_url,
            "width": int(config.get("web_ui_width", 1280)),
            "height": int(config.get("web_ui_height", 800)),
            "min_size": (
                int(config.get("web_ui_min_width", 1080)),
                int(config.get("web_ui_min_height", 700)),
            ),
            "background_color": "#0b1118",
            "text_select": True,
        }

        try:
            import inspect
            if icon_path and "icon" in inspect.signature(webview.create_window).parameters:
                window_kwargs["icon"] = str(icon_path)
        except Exception:
            pass

        window = webview.create_window(**window_kwargs)
        api.bind_window(window)

        window.expose(
            api.get_app_state,
            api.get_instance_window_data,
            api.open_instance_subfolder,
            api.list_instance_folder,
            api.set_folder_file_enabled,
            api.delete_folder_file,
            api.get_screenshot_data,
            api.copy_screenshot_path,
            api.list_instance_mods,
            api.set_mod_enabled,
            api.delete_instance_mod,
            api.get_account_manager_data,
            api.start_microsoft_login,
            api.get_microsoft_login_status,
            api.add_microsoft_account,
            api.add_offline_account,
            api.delete_account,
            api.refresh_selected_account,
            api.get_instance_editor_data,
            api.get_instance_icon_pack,
            api.set_instance_icon,
            api.search_modrinth,
            api.get_modrinth_filter_options,
            api.install_modrinth_project,
            api.check_modrinth_modpack_update,
            api.apply_modrinth_modpack_update,
            api.open_external_url,
            api.get_minecraft_version_options,
            api.get_loader_version_options,
            api.create_instance,
            api.update_instance,
            api.delete_instance,
            api.select_instance,
            api.select_account,
            api.set_preference,
            api.get_launch_settings_data,
            api.save_launch_settings,
            api.open_instance_folder,
            api.open_log,
            api.open_github,
            api.open_classic_ui,
            api.install_official,
            api.apply_launcher_update,
            api.apply_official_update,
            api.run_action,
        )

        def on_loaded():
            _apply_windows_window_icon(window, icon_path)
            api._append_startup_log(
                f"Web UI loaded through internal HTTP server: {window.get_current_url()}"
            )

        window.events.loaded += on_loaded

        webview.start(
            debug="--debug-web" in sys.argv,
            private_mode=False,
            http_server=True,
            storage_path=str(root / "data" / "webview" / "0_6_66"),
        )
    except Exception:
        details = traceback.format_exc()
        _show_error(
            "StoneLight Launcher",
            "Не удалось запустить новую web-оболочку.\n\n"
            "Запусти StoneLightLauncherClassic.cmd для классического интерфейса.\n\n"
            + details[-1800:],
        )
        raise


if __name__ == "__main__":
    main()
