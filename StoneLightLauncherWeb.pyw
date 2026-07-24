from __future__ import annotations

import os
import sys
import traceback
import json
import mimetypes
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from app_paths import app_root, bundled_path, ensure_runtime_files


BROWSER_FALLBACK_IDLE_TIMEOUT = 180
BROWSER_FALLBACK_METHODS = {
    "get_app_state",
    "get_instance_window_data",
    "open_instance_subfolder",
    "list_instance_folder",
    "set_folder_file_enabled",
    "delete_folder_file",
    "get_screenshot_data",
    "copy_screenshot_path",
    "list_instance_mods",
    "set_mod_enabled",
    "delete_instance_mod",
    "get_account_manager_data",
    "start_microsoft_login",
    "get_microsoft_login_status",
    "add_microsoft_account",
    "add_offline_account",
    "delete_account",
    "refresh_selected_account",
    "get_instance_editor_data",
    "get_instance_icon_pack",
    "set_instance_icon",
    "search_modrinth",
    "get_modrinth_filter_options",
    "install_modrinth_project",
    "check_modrinth_modpack_update",
    "apply_modrinth_modpack_update",
    "open_external_url",
    "get_minecraft_version_options",
    "get_loader_version_options",
    "create_instance",
    "update_instance",
    "delete_instance",
    "select_instance",
    "select_account",
    "set_preference",
    "get_launch_settings_data",
    "save_launch_settings",
    "open_instance_folder",
    "open_log",
    "open_github",
    "open_classic_ui",
    "install_official",
    "apply_launcher_update",
    "apply_official_update",
    "run_action",
}


def _show_error(title: str, text: str):
    try:
        from tkinter import messagebox
        messagebox.showerror(title, text)
    except Exception:
        print(text, file=sys.stderr)


def _show_info(title: str, text: str):
    try:
        from tkinter import messagebox
        messagebox.showinfo(title, text)
    except Exception:
        print(text)


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


class BrowserBridgeWindow:
    """Tiny pywebview-compatible event sink for browser fallback mode."""

    def __init__(self):
        self._events: list[dict] = []
        self._event_id = 0
        self._lock = threading.Lock()
        self.last_poll = time.time()

    def evaluate_js(self, script: str):
        marker = "window.StoneLightBridge.receive("
        if marker not in script:
            return None

        try:
            start = script.index(marker) + len(marker)
            end = script.rfind(");")
            if end <= start:
                return None
            args_text = script[start:end]
            event_text, payload_text = args_text.split(",", 1)
            event_name = json.loads(event_text.strip())
            payload = json.loads(payload_text.strip())
        except Exception:
            return None

        with self._lock:
            self._event_id += 1
            self._events.append({
                "id": self._event_id,
                "event": event_name,
                "payload": payload,
            })
            if len(self._events) > 500:
                del self._events[:-500]
        return None

    def events_since(self, after: int) -> list[dict]:
        self.last_poll = time.time()
        with self._lock:
            return [item for item in self._events if int(item.get("id", 0)) > after]


def _serve_browser_fallback(root: Path, config: dict, reason: str = "") -> int:
    from launcher_api import LauncherWebAPI

    ui_root = root / "web_ui"
    if not ui_root.exists():
        bundled = bundled_path("web_ui")
        ui_root = bundled if bundled.exists() else ui_root

    if not ui_root.exists():
        raise FileNotFoundError(f"Не найден web UI: {ui_root}")

    api = LauncherWebAPI()
    bridge_window = BrowserBridgeWindow()
    api.bind_window(bridge_window)

    class Handler(BaseHTTPRequestHandler):
        server_version = "StoneLightLauncherBrowserFallback/0.6.69"

        def log_message(self, format, *args):
            return

        def _write_json(self, status: int, payload: dict):
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            parsed = urlparse(self.path)
            path = unquote(parsed.path or "/")

            if path == "/api/events":
                try:
                    query = parsed.query or ""
                    after = 0
                    for part in query.split("&"):
                        if part.startswith("after="):
                            after = int(part.split("=", 1)[1] or 0)
                    self._write_json(200, {"ok": True, "events": bridge_window.events_since(after)})
                except Exception as exc:
                    self._write_json(500, {"ok": False, "error": str(exc)})
                return

            if path in {"", "/"}:
                path = "/web_ui/index.html"

            if path.startswith("/web_ui/"):
                relative = path.removeprefix("/web_ui/")
                target = (ui_root / relative).resolve()
                try:
                    if not str(target).startswith(str(ui_root.resolve())):
                        raise PermissionError("Invalid path")
                    if not target.exists() or not target.is_file():
                        self.send_error(404)
                        return
                    content = target.read_bytes()
                    mime = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
                    self.send_response(200)
                    self.send_header("Content-Type", f"{mime}; charset=utf-8" if mime.startswith("text/") or mime.endswith("javascript") else mime)
                    self.send_header("Content-Length", str(len(content)))
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    self.wfile.write(content)
                except Exception as exc:
                    self.send_error(500, str(exc))
                return

            self.send_error(404)

        def do_POST(self):
            parsed = urlparse(self.path)
            if parsed.path != "/api/call":
                self.send_error(404)
                return

            try:
                length = int(self.headers.get("Content-Length") or "0")
                payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                method = str(payload.get("method") or "").strip()
                args = payload.get("args") or []
                if not isinstance(args, list):
                    args = []

                if method not in BROWSER_FALLBACK_METHODS:
                    raise ValueError(f"API method is not allowed: {method}")

                func = getattr(api, method, None)
                if not callable(func):
                    raise ValueError(f"API method is unavailable: {method}")

                bridge_window.last_poll = time.time()
                result = func(*args)
                self._write_json(200, {"ok": True, "result": result})
            except Exception as exc:
                self._write_json(500, {
                    "ok": False,
                    "error": str(exc),
                    "details": traceback.format_exc()[-1800:],
                })

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = int(httpd.server_address[1])
    url = f"http://127.0.0.1:{port}/web_ui/index.html?v={config.get('launcher_version', '0.6.69')}&transport=browser#desktop=1"

    api._append_startup_log(f"Browser fallback started at {url}")
    if reason:
        api._append_startup_log("WebView failure reason: " + reason[-1200:])

    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    webbrowser.open(url)

    if reason:
        _show_info(
            "StoneLight Launcher",
            "Встроенная WebView-оболочка не запустилась на этом ПК.\n\n"
            "Лаунчер открыт в обычном браузере в резервном режиме.\n"
            "Это временный обход проблемы pythonnet/Python.Runtime.dll.\n\n"
            "Не закрывай процесс лаунчера, пока пользуешься браузерным окном."
        )

    try:
        while True:
            time.sleep(5)
            if time.time() - bridge_window.last_poll > BROWSER_FALLBACK_IDLE_TIMEOUT:
                api._append_startup_log("Browser fallback idle timeout reached; exiting.")
                break
    finally:
        try:
            httpd.shutdown()
        except Exception:
            pass
        try:
            httpd.server_close()
        except Exception:
            pass

    return 0


def _run_webview(root: Path, config: dict, icon_path: Path | None) -> None:
    import webview
    from launcher_api import LauncherWebAPI

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
    desktop_url = "web_ui/index.html?v=0.6.69#desktop=1"

    api = LauncherWebAPI()
    window_kwargs = {
        "title": f"StoneLight Launcher v{config.get('launcher_version', '0.6.69')}",
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

    for method_name in sorted(BROWSER_FALLBACK_METHODS):
        method = getattr(api, method_name, None)
        if callable(method):
            window.expose(method)

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
        storage_path=str(root / "data" / "webview" / "0_6_69"),
    )


def main():
    ensure_runtime_files()
    root = app_root()

    if "--classic" in sys.argv:
        import launcher_gui
        launcher_gui.main()
        return

    config_path = root / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    icon_path = _resolve_icon_path(root, config)
    _set_windows_app_identity()

    if "--browser" in sys.argv:
        _serve_browser_fallback(root, config, "Browser mode was requested explicitly.")
        return

    try:
        _run_webview(root, config, icon_path)
    except Exception:
        details = traceback.format_exc()
        if config.get("browser_fallback_enabled", True):
            try:
                _serve_browser_fallback(root, config, details)
                return
            except Exception:
                details += "\n\nBrowser fallback also failed:\n" + traceback.format_exc()

        _show_error(
            "StoneLight Launcher",
            "Не удалось запустить новую web-оболочку.\n\n"
            "Запусти StoneLightLauncherClassic.cmd для классического интерфейса.\n\n"
            + details[-1800:],
        )
        raise


if __name__ == "__main__":
    main()
