import os
import queue
import threading
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox
import tkinter as tk

import customtkinter as ctk
import i18n

from accounts import (
    account_label,
    add_or_update_offline_account,
    add_or_update_microsoft_account,
    delete_account,
    ensure_initial_account,
    find_account_by_label,
    get_selected_account,
    has_licensed_account,
    load_accounts,
    refresh_microsoft_account,
    select_account,
    validate_offline_username,
)
from instances import (
    create_custom_instance,
    delete_instance,
    find_instance_by_id,
    find_instance_by_label,
    get_selected_instance,
    instance_label,
    load_instances,
    select_instance,
    update_instance,
)
from launcher_core import (
    LauncherCore,
    LauncherError,
    ROOT,
    get_available_mod_loaders,
    get_loader_versions,
    get_minecraft_versions,
    recommended_java_major_for_minecraft,
    suggest_java_for_minecraft,
    get_console_key_for_instance,
    get_console_history,
    register_console_listener,
    unregister_console_listener,
    load_user_settings,
    save_user_settings,
    normalize_global_launch_settings,
)


APP_TITLE = "StoneLight Launcher v0.5.32"
JAVA_PRESET_VALUES = ["auto", "global", "java8", "java16", "java17", "java21", "java25", "manual"]

GITHUB_URL = "https://github.com/stonelightmc/StoneLight-Launcher"

THEME_NAMES = {
    "dark": "Dark",
    "light": "Light",
    "laconic": "Laconic",
    "neon": "Neon",
    "retro_future": "Retro Future",
}

# Base palette inspired by StoneLight website CSS variables:
# light: #fff7ea / #f4e6d2 / #2d2118 / #6b5747 / #ffb347 / #f47c38
# dark:  #0b1118 / #111a25 / #edf3ff / #9fb0c8 / #ffb347 / #ff8c42
# Extra themes:
# laconic      - pastel minimal UI with sage accent
# neon         - dark cyber/arcade palette
# retro_future - synthwave purple UI with magenta/cyan buttons
THEME_PALETTE = {
    "light": {
        "appearance": "light",
        "window": "#fff7ea",
        "panel": "#fffaf1",
        "panel_strong": "#ffffff",
        "input": "#fffaf1",
        "text": "#2d2118",
        "muted": "#6b5747",
        "line": "#d8c0a8",
        "accent": "#ffb347",
        "accent_hover": "#f47c38",
        "accent_text": "#3c1f08",
        "secondary": "#f4e6d2",
        "secondary_hover": "#ead5bb",
        "danger": "#e9625f",
        "danger_hover": "#d94a46",
    },
    "dark": {
        "appearance": "dark",
        "window": "#0b1118",
        "panel": "#151c27",
        "panel_strong": "#1c2533",
        "input": "#111a25",
        "text": "#edf3ff",
        "muted": "#9fb0c8",
        "line": "#2e3b4c",
        "accent": "#ffb347",
        "accent_hover": "#ff8c42",
        "accent_text": "#3c1f08",
        "secondary": "#263244",
        "secondary_hover": "#314052",
        "danger": "#ff6b6b",
        "danger_hover": "#e05252",
    },
    "laconic": {
        "appearance": "light",
        "window": "#f4f1ec",
        "panel": "#fbf8f2",
        "panel_strong": "#ffffff",
        "input": "#f0ece4",
        "text": "#2f3440",
        "muted": "#7c8792",
        "line": "#d7d0c5",
        "accent": "#8fb8a8",
        "accent_hover": "#7aa895",
        "accent_text": "#11251f",
        "secondary": "#e8e1d7",
        "secondary_hover": "#dcd4c8",
        "danger": "#d97878",
        "danger_hover": "#c86161",
    },
    "neon": {
        "appearance": "dark",
        "window": "#070912",
        "panel": "#101426",
        "panel_strong": "#171c33",
        "input": "#0b1020",
        "text": "#f2f7ff",
        "muted": "#8da0c2",
        "line": "#273152",
        "accent": "#00e5ff",
        "accent_hover": "#8a5cff",
        "accent_text": "#020812",
        "secondary": "#1b2340",
        "secondary_hover": "#26315a",
        "danger": "#ff3b8d",
        "danger_hover": "#d92e76",
    },
    "retro_future": {
        "appearance": "dark",
        "window": "#1a1026",
        "panel": "#261936",
        "panel_strong": "#332046",
        "input": "#21152f",
        "text": "#fff1dc",
        "muted": "#c9a9b8",
        "line": "#4a315f",
        "accent": "#ff4fd8",
        "accent_hover": "#00d4ff",
        "accent_text": "#17001a",
        "secondary": "#3a2850",
        "secondary_hover": "#4b3466",
        "danger": "#ff6b8a",
        "danger_hover": "#e14f70",
    },
}


def normalize_theme(theme: str | None) -> str:
    theme = (theme or "dark").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "dark": "dark",
        "night": "dark",
        "темная": "dark",
        "тёмная": "dark",
        "light": "light",
        "day": "light",
        "светлая": "light",
        "laconic": "laconic",
        "minimal": "laconic",
        "лаконичная": "laconic",
        "лаконічна": "laconic",
        "лаконикалық": "laconic",
        "neon": "neon",
        "неон": "neon",
        "retro": "retro_future",
        "retro_future": "retro_future",
        "retro_futurism": "retro_future",
        "ретро_футуризм": "retro_future",
    }
    return aliases.get(theme, theme if theme in THEME_PALETTE else "dark")


def theme_pair(name: str):
    # CustomTkinter tuple colors are chosen by appearance mode only.
    # For extra dark-mode themes, use the active custom theme for both tuple sides.
    current = normalize_theme(globals().get("_ACTIVE_THEME", "dark"))
    if current in ("dark", "light"):
        return (THEME_PALETTE["light"][name], THEME_PALETTE["dark"][name])
    value = THEME_PALETTE[current][name]
    return (value, value)


def theme_label(theme: str | None = None) -> str:
    return tr(THEME_NAMES.get(normalize_theme(theme), "Dark"))


def theme_code_from_label(label: str | None) -> str:
    label = (label or "").strip()
    for code, raw_label in THEME_NAMES.items():
        if label in (raw_label, tr(raw_label)):
            return code
    return normalize_theme(label)


def apply_ctk_theme(theme: str | None):
    theme = normalize_theme(theme)
    globals()["_ACTIVE_THEME"] = theme
    ctk.set_appearance_mode(THEME_PALETTE[theme]["appearance"])


def apply_theme_to_window(window):
    try:
        window.configure(fg_color=theme_pair("window"))
    except Exception:
        pass


def is_transparent(value) -> bool:
    return isinstance(value, str) and value.lower() == "transparent"


def style_kwargs(cls_name: str, kwargs: dict) -> dict:
    kwargs = dict(kwargs)

    # Preserve intentionally transparent layout helper frames.
    if kwargs.get("fg_color") is not None and is_transparent(kwargs.get("fg_color")):
        return kwargs

    if cls_name in ("CTkFrame", "CTkToplevel"):
        kwargs.setdefault("fg_color", theme_pair("panel"))
        kwargs.setdefault("border_color", theme_pair("line"))
        kwargs.setdefault("border_width", 1)
    elif cls_name == "CTkTabview":
        kwargs.setdefault("fg_color", theme_pair("panel"))
        kwargs.setdefault("border_color", theme_pair("line"))
        kwargs.setdefault("segmented_button_fg_color", theme_pair("secondary"))
        kwargs.setdefault("segmented_button_selected_color", theme_pair("accent"))
        kwargs.setdefault("segmented_button_selected_hover_color", theme_pair("accent_hover"))
        kwargs.setdefault("segmented_button_unselected_color", theme_pair("secondary"))
        kwargs.setdefault("segmented_button_unselected_hover_color", theme_pair("secondary_hover"))
        kwargs.setdefault("text_color", theme_pair("text"))
    elif cls_name in ("CTkEntry", "CTkComboBox", "CTkTextbox"):
        kwargs.setdefault("fg_color", theme_pair("input"))
        kwargs.setdefault("border_color", theme_pair("line"))
        kwargs.setdefault("text_color", theme_pair("text"))
        if cls_name == "CTkComboBox":
            kwargs.setdefault("button_color", theme_pair("secondary"))
            kwargs.setdefault("button_hover_color", theme_pair("secondary_hover"))
            kwargs.setdefault("dropdown_fg_color", theme_pair("panel_strong"))
            kwargs.setdefault("dropdown_hover_color", theme_pair("secondary"))
            kwargs.setdefault("dropdown_text_color", theme_pair("text"))
    elif cls_name == "CTkButton":
        if kwargs.get("fg_color") == "#444":
            kwargs["fg_color"] = theme_pair("secondary")
            kwargs.setdefault("hover_color", theme_pair("secondary_hover"))
            kwargs.setdefault("text_color", theme_pair("text"))
        elif kwargs.get("fg_color") == "#7a1f1f":
            kwargs["fg_color"] = theme_pair("danger")
            kwargs["hover_color"] = theme_pair("danger_hover")
            kwargs.setdefault("text_color", "#ffffff")
        else:
            kwargs.setdefault("fg_color", theme_pair("accent"))
            kwargs.setdefault("hover_color", theme_pair("accent_hover"))
            kwargs.setdefault("text_color", theme_pair("accent_text"))

    if kwargs.get("text_color") in ("#bdbdbd", "#a9a9a9"):
        kwargs["text_color"] = theme_pair("muted")
    elif kwargs.get("text_color") == "#ffffff":
        kwargs["text_color"] = theme_pair("text")

    if kwargs.get("border_color") in ("#444", "#555"):
        kwargs["border_color"] = theme_pair("line")

    return kwargs



def tr(text: str | None) -> str | None:
    return i18n.tr(text)


def patch_i18n_widgets():
    def patch_text_widget(cls):
        if getattr(cls, "_stonelight_i18n_patched", False):
            return

        original_init = cls.__init__
        original_configure = cls.configure
        cls_name = cls.__name__

        def patched_init(self, *args, **kwargs):
            if "text" in kwargs:
                kwargs["text"] = tr(kwargs["text"])
            if "placeholder_text" in kwargs:
                kwargs["placeholder_text"] = tr(kwargs["placeholder_text"])
            kwargs = style_kwargs(cls_name, kwargs)
            original_init(self, *args, **kwargs)

        def patched_configure(self, *args, **kwargs):
            if "text" in kwargs:
                kwargs["text"] = tr(kwargs["text"])
            if "placeholder_text" in kwargs:
                kwargs["placeholder_text"] = tr(kwargs["placeholder_text"])
            kwargs = style_kwargs(cls_name, kwargs)
            return original_configure(self, *args, **kwargs)

        cls.__init__ = patched_init
        cls.configure = patched_configure
        cls._stonelight_i18n_patched = True

    for widget_cls in (
        ctk.CTkLabel,
        ctk.CTkButton,
        ctk.CTkCheckBox,
        ctk.CTkEntry,
        ctk.CTkFrame,
        ctk.CTkTabview,
    ):
        patch_text_widget(widget_cls)

    if not getattr(ctk.CTkComboBox, "_stonelight_i18n_patched", False):
        original_combo_init = ctk.CTkComboBox.__init__
        original_combo_configure = ctk.CTkComboBox.configure
        original_combo_set = ctk.CTkComboBox.set

        def translate_combo_values(values):
            if isinstance(values, (list, tuple)):
                return [tr(v) if isinstance(v, str) else v for v in values]
            return values

        def patched_combo_init(self, *args, **kwargs):
            if "values" in kwargs:
                kwargs["values"] = translate_combo_values(kwargs["values"])
            kwargs = style_kwargs("CTkComboBox", kwargs)
            original_combo_init(self, *args, **kwargs)

        def patched_combo_configure(self, *args, **kwargs):
            if "values" in kwargs:
                kwargs["values"] = translate_combo_values(kwargs["values"])
            kwargs = style_kwargs("CTkComboBox", kwargs)
            return original_combo_configure(self, *args, **kwargs)

        def patched_combo_set(self, value):
            if isinstance(value, str):
                value = tr(value)
            return original_combo_set(self, value)

        ctk.CTkComboBox.__init__ = patched_combo_init
        ctk.CTkComboBox.configure = patched_combo_configure
        ctk.CTkComboBox.set = patched_combo_set
        ctk.CTkComboBox._stonelight_i18n_patched = True

    if not getattr(ctk.CTkTextbox, "_stonelight_i18n_patched", False):
        original_textbox_init = ctk.CTkTextbox.__init__
        original_textbox_configure = ctk.CTkTextbox.configure
        original_textbox_insert = ctk.CTkTextbox.insert

        def patched_textbox_init(self, *args, **kwargs):
            kwargs = style_kwargs("CTkTextbox", kwargs)
            original_textbox_init(self, *args, **kwargs)

        def patched_textbox_configure(self, *args, **kwargs):
            kwargs = style_kwargs("CTkTextbox", kwargs)
            return original_textbox_configure(self, *args, **kwargs)

        def patched_textbox_insert(self, index, text, *args, **kwargs):
            if isinstance(text, str):
                text = tr(text)
            return original_textbox_insert(self, index, text, *args, **kwargs)

        ctk.CTkTextbox.__init__ = patched_textbox_init
        ctk.CTkTextbox.configure = patched_textbox_configure
        ctk.CTkTextbox.insert = patched_textbox_insert
        ctk.CTkTextbox._stonelight_i18n_patched = True

    if not getattr(messagebox, "_stonelight_i18n_patched", False):
        original_showerror = messagebox.showerror
        original_showinfo = messagebox.showinfo
        original_askyesno = messagebox.askyesno

        def showerror(title, message, *args, **kwargs):
            return original_showerror(title, tr(str(message)), *args, **kwargs)

        def showinfo(title, message, *args, **kwargs):
            return original_showinfo(title, tr(str(message)), *args, **kwargs)

        def askyesno(title, message, *args, **kwargs):
            return original_askyesno(title, tr(str(message)), *args, **kwargs)

        messagebox.showerror = showerror
        messagebox.showinfo = showinfo
        messagebox.askyesno = askyesno
        messagebox._stonelight_i18n_patched = True


patch_i18n_widgets()


def safe_os_startfile(path: Path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    os.startfile(path)


class SelectableListDialog(ctk.CTkToplevel):
    def __init__(self, parent, title: str, items: list[str], on_select, filter_placeholder: str = "Фильтр"):
        super().__init__(parent)
        self.parent = parent
        self.items = items or []
        self.filtered_items = list(self.items)
        self.on_select = on_select

        self.title(title)
        self.geometry("520x560")
        self.transient(parent)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, padx=16, pady=(16, 10), sticky="w"
        )

        self.filter_entry = ctk.CTkEntry(self, placeholder_text=filter_placeholder)
        self.filter_entry.grid(row=1, column=0, padx=16, pady=4, sticky="ew")
        self.filter_entry.bind("<KeyRelease>", lambda e: self.apply_filter())

        self.info_label = ctk.CTkLabel(self, text="", text_color="#bdbdbd")
        self.info_label.grid(row=2, column=0, padx=16, pady=(0, 8), sticky="w")

        list_frame = ctk.CTkFrame(self)
        list_frame.grid(row=3, column=0, padx=16, pady=8, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)

        self.listbox = tk.Listbox(
            list_frame,
            activestyle="dotbox",
            exportselection=False,
            bg="#1f1f1f",
            fg="#ffffff",
            selectbackground="#1f6aa5",
            selectforeground="#ffffff",
            highlightthickness=1,
            highlightbackground="#4a4a4a",
            relief="flat"
        )
        self.listbox.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)

        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=8)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        self.listbox.bind("<Double-Button-1>", lambda e: self.select_current())

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=4, column=0, padx=16, pady=(8, 16), sticky="ew")
        bottom.grid_columnconfigure((0, 1), weight=1)

        self.select_button = ctk.CTkButton(bottom, text="Выбрать", command=self.select_current)
        self.select_button.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        self.cancel_button = ctk.CTkButton(bottom, text="Отмена", fg_color="#444", command=self.destroy)
        self.cancel_button.grid(row=0, column=1, padx=(8, 0), sticky="ew")

        self.apply_filter()

    def apply_filter(self):
        query = self.filter_entry.get().strip().lower()
        if query:
            self.filtered_items = [v for v in self.items if query in v.lower()]
        else:
            self.filtered_items = list(self.items)

        self.listbox.delete(0, "end")
        for item in self.filtered_items:
            self.listbox.insert("end", item)

        if self.filtered_items:
            self.listbox.selection_set(0)
            self.listbox.activate(0)

        self.info_label.configure(text=f"Всего: {len(self.items)}. Показано: {len(self.filtered_items)}.")

    def select_current(self):
        selection = self.listbox.curselection()
        if not selection:
            if self.filtered_items:
                value = self.filtered_items[0]
            else:
                messagebox.showerror("StoneLight Launcher", "Ничего не выбрано.")
                return
        else:
            value = self.listbox.get(selection[0])

        if self.on_select:
            self.on_select(value)
        self.destroy()


class VersionPickerDialog(ctk.CTkToplevel):
    def __init__(self, parent, initial_version: str = "", include_snapshots: bool = True, on_select=None):
        super().__init__(parent)
        self.parent = parent
        self.initial_version = initial_version
        self.include_snapshots = include_snapshots
        self.on_select = on_select
        self.all_versions = []

        self.title(tr("Выбор версии Minecraft"))
        self.geometry("520x560")
        self.transient(parent)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(self, text="Выбор версии Minecraft", font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, padx=16, pady=(16, 10), sticky="w"
        )

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=1, column=0, padx=16, pady=4, sticky="ew")
        top.grid_columnconfigure(0, weight=1)

        self.filter_entry = ctk.CTkEntry(top, placeholder_text="Фильтр, например: 1.20.4 или 24w")
        self.filter_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.filter_entry.bind("<KeyRelease>", lambda e: self.apply_filter())

        self.reload_button = ctk.CTkButton(top, text="Обновить список", width=130, command=self.load_versions)
        self.reload_button.grid(row=0, column=1, sticky="e")

        self.info_label = ctk.CTkLabel(self, text="Загрузка списка версий...", text_color="#bdbdbd")
        self.info_label.grid(row=2, column=0, padx=16, pady=(0, 8), sticky="w")

        list_frame = ctk.CTkFrame(self)
        list_frame.grid(row=3, column=0, padx=16, pady=8, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)

        self.listbox = tk.Listbox(
            list_frame,
            activestyle="dotbox",
            exportselection=False,
            bg="#1f1f1f",
            fg="#ffffff",
            selectbackground="#1f6aa5",
            selectforeground="#ffffff",
            highlightthickness=1,
            highlightbackground="#4a4a4a",
            relief="flat"
        )
        self.listbox.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)

        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=8)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        self.listbox.bind("<Double-Button-1>", lambda e: self.select_current())

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=4, column=0, padx=16, pady=(8, 16), sticky="ew")
        bottom.grid_columnconfigure((0, 1), weight=1)

        self.select_button = ctk.CTkButton(bottom, text="Выбрать", command=self.select_current)
        self.select_button.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        self.cancel_button = ctk.CTkButton(bottom, text="Отмена", fg_color="#444", command=self.destroy)
        self.cancel_button.grid(row=0, column=1, padx=(8, 0), sticky="ew")

        self.load_versions()

    def load_versions(self):
        self.reload_button.configure(state="disabled")
        self.info_label.configure(text="Загрузка списка версий...")
        self.listbox.delete(0, "end")
        self.listbox.insert("end", "Загрузка...")

        def worker():
            try:
                versions = get_minecraft_versions(include_snapshots=self.include_snapshots, limit=None)
                self.after(0, lambda: self.apply_loaded_versions(versions))
            except Exception as exc:
                self.after(0, lambda: self.show_error(exc))

        threading.Thread(target=worker, daemon=True).start()

    def apply_loaded_versions(self, versions):
        self.all_versions = versions or []
        self.reload_button.configure(state="normal")

        # Не вставляем текущую версию в поле фильтра.
        # Иначе список сразу сужается до одного пункта, что выглядит как баг.
        self.filter_entry.delete(0, "end")
        self.apply_filter()
        self.select_initial_version()

    def apply_filter(self):
        query = self.filter_entry.get().strip().lower()
        if query:
            filtered = [v for v in self.all_versions if query in v.lower()]
        else:
            filtered = list(self.all_versions)

        self.listbox.delete(0, "end")
        for item in filtered:
            self.listbox.insert("end", item)

        if filtered:
            self.listbox.selection_set(0)
            self.listbox.activate(0)

        suffix = "включая снапшоты" if self.include_snapshots else "только release"
        self.info_label.configure(text=f"Всего версий: {len(self.all_versions)}. Показано: {len(filtered)}. Режим: {suffix}.")

    def select_initial_version(self):
        if not self.initial_version:
            return

        try:
            index = self.all_versions.index(self.initial_version)
        except ValueError:
            return

        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(index)
        self.listbox.activate(index)
        self.listbox.see(index)

    def select_current(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showerror("StoneLight Launcher", "Версия не выбрана.")
            return
        value = self.listbox.get(selection[0])
        if value == "Загрузка...":
            return
        if self.on_select:
            self.on_select(value)
        self.destroy()

    def show_error(self, exc):
        self.reload_button.configure(state="normal")
        self.info_label.configure(text=f"Не удалось загрузить версии: {exc}")


class MicrosoftLoginDialog(ctk.CTkToplevel):
    CALLBACK_HOST = "localhost"
    CALLBACK_PORT = 8765
    CALLBACK_PATH = "/callback"

    def __init__(self, app):
        super().__init__(app)
        apply_theme_to_window(self)
        self.app = app
        self.title(tr("Вход Microsoft / Minecraft"))
        self.geometry("820x600")
        self.minsize(760, 560)
        self.transient(app)
        self.grab_set()
        self.lift()
        self.focus_force()

        self.login_state = None
        self.code_verifier = None
        self.callback_server = None
        self.callback_thread = None
        self.received_redirect_url = ""

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(9, weight=1)

        ctk.CTkLabel(
            self,
            text="Вход в лицензионный Microsoft/Minecraft аккаунт",
            font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, columnspan=3, padx=18, pady=(18, 8), sticky="w")

        note = (
            "Пароль в лаунчер не вводится: вход выполняется в браузере Microsoft. "
            "После успешного входа лаунчер автоматически примет ответ через локальный callback."
        )
        ctk.CTkLabel(self, text=note, text_color="#bdbdbd", wraplength=760, justify="left").grid(
            row=1, column=0, columnspan=3, padx=18, pady=(0, 12), sticky="ew"
        )

        ctk.CTkLabel(self, text="Client ID").grid(row=2, column=0, padx=18, pady=6, sticky="w")
        self.client_id_entry = ctk.CTkEntry(self)
        self.client_id_entry.grid(row=2, column=1, columnspan=2, padx=18, pady=6, sticky="ew")
        self.client_id_entry.insert(0, self.app.settings.get("microsoft_client_id", self.app.config.get("microsoft_client_id", "")))

        ctk.CTkLabel(self, text="Redirect URI").grid(row=3, column=0, padx=18, pady=6, sticky="w")
        self.redirect_entry = ctk.CTkEntry(self)
        self.redirect_entry.grid(row=3, column=1, padx=18, pady=6, sticky="ew")
        self.redirect_entry.insert(
            0,
            self.app.settings.get(
                "microsoft_redirect_uri",
                self.app.config.get("microsoft_redirect_uri", "http://localhost:8765/callback")
            )
        )

        self.reset_redirect_button = ctk.CTkButton(
            self,
            text="Вернуть localhost:8765",
            width=170,
            command=self.reset_redirect_uri
        )
        self.reset_redirect_button.grid(row=3, column=2, padx=(0, 18), pady=6, sticky="ew")

        self.open_button = ctk.CTkButton(self, text="1. Открыть вход Microsoft", command=self.open_login)
        self.open_button.grid(row=4, column=0, columnspan=3, padx=18, pady=(12, 8), sticky="ew")

        ctk.CTkLabel(
            self,
            text="Резервный ручной режим: вставь redirect URL сюда, если автоперехват не сработал"
        ).grid(row=5, column=0, columnspan=3, padx=18, pady=(8, 4), sticky="w")

        manual_row = ctk.CTkFrame(self, fg_color="transparent")
        manual_row.grid(row=6, column=0, columnspan=3, padx=18, pady=6, sticky="ew")
        manual_row.grid_columnconfigure(0, weight=1)

        self.redirect_url_entry = ctk.CTkEntry(manual_row, placeholder_text="http://localhost:8765/callback?code=...&state=...")
        self.redirect_url_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.redirect_url_entry.bind("<Control-v>", lambda _e: self.paste_redirect_url())
        self.redirect_url_entry.bind("<Control-V>", lambda _e: self.paste_redirect_url())
        self.redirect_url_entry.bind("<Button-3>", self.show_paste_menu)

        self.paste_button = ctk.CTkButton(manual_row, text="Вставить", width=110, command=self.paste_redirect_url)
        self.paste_button.grid(row=0, column=1, padx=(0, 8))

        self.complete_button = ctk.CTkButton(manual_row, text="Завершить вручную", width=170, command=self.complete_login)
        self.complete_button.grid(row=0, column=2)

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=7, column=0, columnspan=3, padx=18, pady=8, sticky="ew")
        buttons.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(buttons, text="Закрыть", fg_color="#444", command=self.destroy).grid(row=0, column=0, columnspan=2, sticky="ew")

        self.status_box = ctk.CTkTextbox(self, height=190)
        self.status_box.grid(row=9, column=0, columnspan=3, padx=18, pady=(8, 18), sticky="nsew")
        self.status_box.insert(
            "end",
            "Готово. Нажми «Открыть вход Microsoft». Локальный callback будет запущен автоматически.\n"
        )
        self.status_box.configure(state="disabled")

        self.protocol("WM_DELETE_WINDOW", self.close)

    def reset_redirect_uri(self):
        self.redirect_entry.delete(0, "end")
        self.redirect_entry.insert(0, "http://localhost:8765/callback")

    def log(self, text: str):
        self.status_box.configure(state="normal")
        self.status_box.insert("end", text.rstrip() + "\n")
        self.status_box.see("end")
        self.status_box.configure(state="disabled")

    def auth_config(self):
        client_id = self.client_id_entry.get().strip()
        redirect_uri = self.redirect_entry.get().strip() or "http://localhost:8765/callback"
        client_secret = self.app.config.get("microsoft_client_secret", "") or None

        if not client_id:
            raise LauncherError("Не указан Microsoft Azure App Client ID.")

        self.app.settings["microsoft_client_id"] = client_id
        self.app.settings["microsoft_redirect_uri"] = redirect_uri
        save_user_settings(self.app.settings)

        return client_id, redirect_uri, client_secret

    def paste_redirect_url(self):
        try:
            text = self.clipboard_get()
            self.redirect_url_entry.configure(state="normal")
            self.redirect_url_entry.delete(0, "end")
            self.redirect_url_entry.insert(0, text.strip())
            return "break"
        except Exception as exc:
            messagebox.showerror("StoneLight Launcher", f"Не удалось вставить из буфера: {exc}")
            return "break"

    def show_paste_menu(self, event):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Вставить", command=self.paste_redirect_url)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
        return "break"

    def start_callback_server(self, redirect_uri: str):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        from urllib.parse import urlparse

        parsed = urlparse(redirect_uri)
        host = parsed.hostname or self.CALLBACK_HOST
        port = parsed.port or self.CALLBACK_PORT
        path = parsed.path or self.CALLBACK_PATH

        if host not in ("localhost", "127.0.0.1"):
            raise LauncherError("Автоперехват поддерживает только localhost redirect URI.")

        self.stop_callback_server()

        dialog = self

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

                full_url = f"http://localhost:8765/callback:{port}{self.path}"
                html_lang = i18n.get_language()
                html_title = tr("Вход завершён")
                html_text = tr("Можно вернуться в StoneLight Launcher. Это окно браузера можно закрыть.")
                html = f"""
<!doctype html>
<html lang="{html_lang}">
<head><meta charset="utf-8"><title>StoneLight Launcher</title></head>
<body style="font-family: sans-serif; padding: 32px;">
<h2>{html_title}</h2>
<p>{html_text}</p>
</body>
</html>
"""
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html.encode("utf-8"))
                dialog.after(0, lambda: dialog.on_callback_received(full_url))

        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), CallbackHandler)
        except OSError as exc:
            raise LauncherError(
                f"Не удалось запустить локальный callback-сервер на порту {port}. "
                f"Возможно, порт занят или заблокирован. Детали: {exc}"
            )

        self.callback_server = server
        self.callback_thread = threading.Thread(target=server.serve_forever, daemon=True)
        self.callback_thread.start()

        return f"http://localhost:8765/callback:{port}{path}"

    def stop_callback_server(self):
        if self.callback_server:
            try:
                self.callback_server.shutdown()
            except Exception:
                pass
            try:
                self.callback_server.server_close()
            except Exception:
                pass
            self.callback_server = None
            self.callback_thread = None

    def open_login(self):
        try:
            import minecraft_launcher_lib.microsoft_account as microsoft_account

            client_id, redirect_uri, _secret = self.auth_config()
            callback_uri = self.start_callback_server(redirect_uri)

            login_url, state, code_verifier = microsoft_account.get_secure_login_data(client_id, redirect_uri)
            self.login_state = state
            self.code_verifier = code_verifier

            webbrowser.open(login_url)
            self.log(f"Локальный callback запущен: {callback_uri}")
            self.log("Открыт браузер Microsoft login.")
            self.log("После входа лаунчер должен завершить авторизацию автоматически.")
        except Exception as exc:
            self.stop_callback_server()
            messagebox.showerror("StoneLight Launcher", str(exc))
            self.log(f"Ошибка: {exc}")

    def on_callback_received(self, redirected_url: str):
        if self.received_redirect_url:
            return

        self.received_redirect_url = redirected_url
        self.redirect_url_entry.configure(state="normal")
        self.redirect_url_entry.delete(0, "end")
        self.redirect_url_entry.insert(0, redirected_url)
        self.log("Получен callback от Microsoft. Завершаю вход...")
        self.complete_login(auto=True)

    def complete_login(self, auto: bool = False):
        try:
            import minecraft_launcher_lib.microsoft_account as microsoft_account

            client_id, redirect_uri, client_secret = self.auth_config()
            redirected_url = self.received_redirect_url or self.redirect_url_entry.get().strip()

            if not redirected_url:
                raise LauncherError("Нет redirect URL. Повтори вход или вставь URL вручную.")

            if not self.code_verifier:
                raise LauncherError("Сначала нажми «Открыть вход Microsoft», чтобы создать secure login session.")

            auth_code = microsoft_account.parse_auth_code_url(redirected_url, self.login_state)

            try:
                response = microsoft_account.complete_login(client_id, client_secret, redirect_uri, auth_code, self.code_verifier)
            except TypeError:
                response = microsoft_account.complete_login(client_id, redirect_uri, auth_code, self.code_verifier)

            self.stop_callback_server()

            self.app.accounts_data, info = add_or_update_microsoft_account(response)
            self.app.refresh_accounts_ui()
            self.app.append_log(info + f" {response.get('name', '')}")
            self.log(info)
            self.log(f"Добавлен аккаунт: {response.get('name', '')}")
            messagebox.showinfo("StoneLight Launcher", f"{info}\n{response.get('name', '')}")
            self.destroy()
        except Exception as exc:
            if not auto:
                self.stop_callback_server()
            messagebox.showerror("StoneLight Launcher", str(exc))
            self.log(f"Ошибка завершения входа: {exc}")

    def close(self):
        self.stop_callback_server()
        self.destroy()


class GlobalLaunchSettingsDialog(ctk.CTkToplevel):
    def __init__(self, app):
        super().__init__(app)
        apply_theme_to_window(self)
        self.app = app
        self.title(tr("Глобальные настройки запуска"))
        self.geometry("540x330")
        self.resizable(False, False)
        self.transient(app)
        self.grab_set()
        self.lift()
        self.focus_force()

        self.grid_columnconfigure(1, weight=1)

        current = normalize_global_launch_settings(app.settings, app.config)

        ctk.CTkLabel(
            self,
            text="Глобальные настройки запуска",
            font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, columnspan=2, padx=18, pady=(18, 12), sticky="w")

        note = (
            "Эти параметры применяются ко всем сборкам без исключения, "
            "включая официальную StoneLight-сборку."
        )
        ctk.CTkLabel(self, text=note, text_color="#bdbdbd", wraplength=480, justify="left").grid(
            row=1, column=0, columnspan=2, padx=18, pady=(0, 12), sticky="ew"
        )

        ctk.CTkLabel(self, text="Минимум RAM, МБ").grid(row=2, column=0, padx=18, pady=8, sticky="w")
        self.ram_min_entry = ctk.CTkEntry(self)
        self.ram_min_entry.grid(row=2, column=1, padx=18, pady=8, sticky="ew")
        self.ram_min_entry.insert(0, str(current["ram_min_mb"]))

        ctk.CTkLabel(self, text="Максимум RAM, МБ").grid(row=3, column=0, padx=18, pady=8, sticky="w")
        self.ram_max_entry = ctk.CTkEntry(self)
        self.ram_max_entry.grid(row=3, column=1, padx=18, pady=8, sticky="ew")
        self.ram_max_entry.insert(0, str(current["ram_max_mb"]))

        self.fullscreen_var = ctk.BooleanVar(value=bool(current["fullscreen"]))
        self.fullscreen_check = ctk.CTkCheckBox(
            self,
            text="Запускать Minecraft в полноэкранном режиме",
            variable=self.fullscreen_var
        )
        self.fullscreen_check.grid(row=4, column=0, columnspan=2, padx=18, pady=(10, 8), sticky="w")

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=5, column=0, columnspan=2, padx=18, pady=(18, 18), sticky="ew")
        buttons.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(buttons, text="Сохранить", command=self.save).grid(row=0, column=0, padx=(0, 8), sticky="ew")
        ctk.CTkButton(buttons, text="Отмена", fg_color="#444", command=self.destroy).grid(row=0, column=1, padx=(8, 0), sticky="ew")

    def save(self):
        try:
            ram_min = int(self.ram_min_entry.get().strip())
            ram_max = int(self.ram_max_entry.get().strip())
        except Exception:
            messagebox.showerror("StoneLight Launcher", "RAM должен быть числом, например 512 и 4096.")
            return

        if ram_min < 256:
            messagebox.showerror("StoneLight Launcher", "Минимум RAM не должен быть меньше 256 МБ.")
            return
        if ram_max < 1024:
            messagebox.showerror("StoneLight Launcher", "Максимум RAM не должен быть меньше 1024 МБ.")
            return
        if ram_min > ram_max:
            messagebox.showerror("StoneLight Launcher", "Минимум RAM не может быть больше максимума.")
            return
        if ram_max > 131072:
            messagebox.showerror("StoneLight Launcher", "Максимум RAM выглядит слишком большим. Проверь значение.")
            return

        self.app.settings.update({
            "ram_min_mb": ram_min,
            "ram_max_mb": ram_max,
            "ram_mb": ram_max,
            "fullscreen": bool(self.fullscreen_var.get()),
        })
        save_user_settings(self.app.settings)
        self.app.refresh_global_launch_summary()

        for win in list(self.app.instance_windows.values()):
            if win and win.winfo_exists():
                win.refresh_all()

        self.destroy()


class CreateInstanceDialog(ctk.CTkToplevel):
    def __init__(self, app):
        super().__init__(app)
        apply_theme_to_window(self)
        self.app = app
        self.title(tr("Создать сборку"))
        self.geometry("590x470")
        self.resizable(False, False)
        self.transient(app)
        self.grab_set()
        self.lift()
        self.focus_force()

        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Новая сборка", font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, columnspan=3, padx=18, pady=(18, 12), sticky="w"
        )

        ctk.CTkLabel(self, text="Название").grid(row=1, column=0, padx=18, pady=8, sticky="w")
        self.name_entry = ctk.CTkEntry(self, placeholder_text="Например: Test Fabric")
        self.name_entry.grid(row=1, column=1, columnspan=2, padx=18, pady=8, sticky="ew")

        ctk.CTkLabel(self, text="Minecraft").grid(row=2, column=0, padx=18, pady=8, sticky="w")
        self.version_combo = ctk.CTkComboBox(self, values=[
            self.app.config.get("minecraft_version", "26.1.2"),
            "1.20.4", "1.20.1", "1.19.4", "1.19.2"
        ])
        self.version_combo.grid(row=2, column=1, padx=(18, 8), pady=8, sticky="ew")
        self.version_combo.set(self.app.config.get("minecraft_version", "26.1.2"))

        self.pick_version_button = ctk.CTkButton(self, text="Выбрать", width=120, command=self.pick_version)
        self.pick_version_button.grid(row=2, column=2, padx=(8, 18), pady=8, sticky="ew")

        self.include_snapshots_var = ctk.BooleanVar(value=False)
        self.include_snapshots_check = ctk.CTkCheckBox(
            self,
            text="Показывать снапшоты",
            variable=self.include_snapshots_var
        )
        self.include_snapshots_check.grid(row=3, column=1, columnspan=2, padx=18, pady=4, sticky="w")

        ctk.CTkLabel(self, text="Модлоадер").grid(row=4, column=0, padx=18, pady=8, sticky="w")
        loader_values = get_available_mod_loaders()
        self.loader_combo = ctk.CTkComboBox(self, values=loader_values, command=lambda _: self.on_loader_changed())
        self.loader_combo.grid(row=4, column=1, columnspan=2, padx=18, pady=8, sticky="ew")
        self.loader_combo.set("vanilla")

        ctk.CTkLabel(self, text="Версия loader").grid(row=5, column=0, padx=18, pady=8, sticky="w")
        self.loader_version_combo = ctk.CTkComboBox(self, values=[""], state="normal")
        self.loader_version_combo.grid(row=5, column=1, padx=(18, 8), pady=8, sticky="ew")
        self.loader_version_combo.set("")

        self.load_loader_versions_button = ctk.CTkButton(
            self,
            text="Загрузить",
            width=120,
            command=self.load_loader_versions
        )
        self.load_loader_versions_button.grid(row=5, column=2, padx=(8, 18), pady=8, sticky="ew")

        self.info_label = ctk.CTkLabel(
            self,
            text="Пустая сборка создаётся без модпака. Для vanilla список версий loader не нужен.",
            text_color="#bdbdbd",
            wraplength=520,
            justify="left"
        )
        self.info_label.grid(row=6, column=0, columnspan=3, padx=18, pady=(10, 8), sticky="ew")

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=7, column=0, columnspan=3, padx=18, pady=(16, 18), sticky="ew")
        buttons.grid_columnconfigure((0, 1), weight=1)

        self.create_button = ctk.CTkButton(buttons, text="Создать", command=self.create)
        self.create_button.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        self.cancel_button = ctk.CTkButton(buttons, text="Отмена", fg_color="#444", command=self.destroy)
        self.cancel_button.grid(row=0, column=1, padx=(8, 0), sticky="ew")

        self.on_loader_changed()

    def pick_version(self):
        VersionPickerDialog(
            self,
            initial_version=self.version_combo.get().strip(),
            include_snapshots=self.include_snapshots_var.get(),
            on_select=self.apply_version
        )

    def apply_version(self, value: str):
        self.version_combo.set(value)

    def on_loader_changed(self):
        loader = (self.loader_combo.get() or "vanilla").strip().lower()
        if loader == "vanilla":
            self.loader_version_combo.configure(values=[""], state="disabled")
            self.loader_version_combo.set("")
            self.load_loader_versions_button.configure(state="disabled")
        else:
            self.loader_version_combo.configure(state="normal")
            self.load_loader_versions_button.configure(state="normal")

    def load_loader_versions(self):
        loader = (self.loader_combo.get() or "").strip().lower()
        minecraft_version = self.version_combo.get().strip()

        if loader in ("", "vanilla"):
            self.info_label.configure(text="Для vanilla модлоадер не нужен.")
            return

        self.load_loader_versions_button.configure(state="disabled")
        self.info_label.configure(text=f"Загружаю версии {loader} для Minecraft {minecraft_version}...")

        def worker():
            versions = get_loader_versions(loader, minecraft_version, stable_only=False)
            self.after(0, lambda: self.apply_loader_versions(loader, minecraft_version, versions))

        threading.Thread(target=worker, daemon=True).start()

    def apply_loader_versions(self, loader, minecraft_version, versions):
        self.load_loader_versions_button.configure(state="normal")
        if versions:
            self.loader_version_combo.configure(values=versions)
            self.loader_version_combo.set(versions[0])
            self.info_label.configure(text=f"Найдено версий {loader}: {len(versions)} для Minecraft {minecraft_version}. Выбери нужную в открытом списке.")

            def choose(value):
                self.loader_version_combo.set(value)

            SelectableListDialog(
                self,
                f"Версии {loader} для {minecraft_version}",
                versions,
                choose,
                filter_placeholder="Фильтр версии loader"
            )
        else:
            self.loader_version_combo.configure(values=[""])
            self.loader_version_combo.set("")
            self.info_label.configure(
                text=f"Не найдено автоматически поддерживаемых версий {loader} для Minecraft {minecraft_version}. "
                     f"Можно оставить поле пустым: лаунчер попробует взять последнюю доступную, если loader это поддерживает."
            )

    def create(self):
        name = self.name_entry.get().strip()
        minecraft_version = self.version_combo.get().strip()
        loader = self.loader_combo.get().strip().lower() or "vanilla"
        loader_version = self.loader_version_combo.get().strip()
        version_type = "snapshot" if self.include_snapshots_var.get() else "release"

        try:
            self.app.instances_data, info = create_custom_instance(
                self.app.config,
                name,
                minecraft_version,
                loader,
                loader_version,
                version_type
            )
            self.app.refresh_instances_ui()
            self.app.append_log(f"{info} {name}")
            self.destroy()
        except Exception as exc:
            messagebox.showerror("StoneLight Launcher", str(exc))


class InstanceWindow(ctk.CTkToplevel):
    def __init__(self, app, instance_id: str):
        super().__init__(app)
        apply_theme_to_window(self)
        self.app = app
        self.instance_id = instance_id
        self.queue = queue.Queue()
        self.worker_thread = None

        self.instance = self.reload_instance()
        self.title(f"Сборка: {self.instance.get('name', 'Instance')}")
        self.geometry("1120x860")
        self.minsize(1000, 780)
        self.transient(app)
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)
        self.after(500, lambda: self.attributes("-topmost", False))

        self.build_ui()
        self.refresh_all()
        self.subscribe_console_history()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.poll_queue()

    def reload_instance(self):
        self.app.instances_data = load_instances(self.app.config)
        instance = find_instance_by_id(self.app.instances_data, self.instance_id)
        if not instance:
            raise LauncherError("Сборка не найдена.")
        return instance

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, corner_radius=18)
        header.grid(row=0, column=0, padx=18, pady=(18, 10), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(header, text="", font=ctk.CTkFont(size=26, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=18, pady=(16, 0), sticky="w")

        self.subtitle_label = ctk.CTkLabel(header, text="", text_color="#bdbdbd")
        self.subtitle_label.grid(row=1, column=0, padx=18, pady=(0, 16), sticky="w")

        self.tabs = ctk.CTkTabview(self, corner_radius=18)
        self.tabs.grid(row=1, column=0, padx=18, pady=(8, 18), sticky="nsew")

        self.tab_launch_name = tr("Запуск")
        self.tab_files_name = tr("Папки")
        self.tab_settings_name = tr("Настройки")
        self.tab_console_name = tr("Консоль")

        self.tab_launch = self.tabs.add(self.tab_launch_name)
        self.tab_files = self.tabs.add(self.tab_files_name)
        self.tab_settings = self.tabs.add(self.tab_settings_name)
        self.tab_console = self.tabs.add(self.tab_console_name)

        self.build_launch_tab()
        self.build_files_tab()
        self.build_settings_tab()
        self.build_console_tab()

    def build_launch_tab(self):
        tab = self.tab_launch
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(tab, text="Аккаунт").grid(row=0, column=0, padx=14, pady=(14, 6), sticky="w")
        self.account_combo = ctk.CTkComboBox(tab, values=[], command=self.on_account_selected)
        self.account_combo.grid(row=0, column=1, columnspan=2, padx=14, pady=(14, 6), sticky="ew")

        ctk.CTkLabel(
            tab,
            text="Параметры запуска",
            font=ctk.CTkFont(size=20, weight="bold")
        ).grid(row=1, column=0, columnspan=3, padx=14, pady=(10, 4), sticky="w")

        self.launch_cards = ctk.CTkFrame(tab, fg_color="transparent")
        self.launch_cards.grid(row=2, column=0, columnspan=3, padx=10, pady=(0, 4), sticky="ew")
        self.launch_cards.grid_columnconfigure((0, 1, 2), weight=1)

        self.build_card = self.create_info_card(self.launch_cards, "Сборка", row=0, column=0)
        self.global_card = self.create_info_card(self.launch_cards, "Глобальные параметры", row=0, column=1)
        self.java_card = self.create_info_card(self.launch_cards, "Java сборки", row=0, column=2)

        info = (
            "Память и полноэкранный режим задаются глобально для всех сборок. "
            "Java, Minecraft и модлоадер меняются на вкладке «Настройки»."
        )
        ctk.CTkLabel(tab, text=info, text_color="#bdbdbd", wraplength=980, justify="left").grid(
            row=3, column=0, columnspan=3, padx=14, pady=(0, 8), sticky="w"
        )

        actions = ctk.CTkFrame(tab, fg_color="transparent")
        actions.grid(row=4, column=0, columnspan=3, padx=14, pady=(8, 10), sticky="ew")
        actions.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.play_button = ctk.CTkButton(actions, text="Играть", height=40, command=self.on_play)
        self.play_button.grid(row=0, column=0, padx=(0, 6), pady=(0, 6), sticky="ew")

        self.update_button = ctk.CTkButton(actions, text="Обновить", height=40, command=self.on_update)
        self.update_button.grid(row=0, column=1, padx=6, pady=(0, 6), sticky="ew")

        self.stop_button = ctk.CTkButton(actions, text="Остановить", height=40, fg_color="#7a1f1f", hover_color="#9b2929", command=self.on_stop_game)
        self.stop_button.grid(row=0, column=2, padx=6, pady=(0, 6), sticky="ew")

        self.open_folder_button = ctk.CTkButton(actions, text="Папка сборки", height=40, command=self.open_game_folder)
        self.open_folder_button.grid(row=0, column=3, padx=(6, 0), pady=(0, 6), sticky="ew")

        # Forge-only row. It is hidden for non-Forge instances.
        self.repair_button = ctk.CTkButton(actions, text="Repair", height=38, command=self.on_repair)
        self.repair_button.grid(row=1, column=0, padx=(0, 6), pady=(4, 0), sticky="ew")

        self.manual_forge_button = ctk.CTkButton(actions, text="Forge Installer", height=38, command=self.on_manual_forge)
        self.manual_forge_button.grid(row=1, column=1, padx=6, pady=(4, 0), sticky="ew")

        self.check_forge_button = ctk.CTkButton(actions, text="Проверить Forge", height=38, command=self.on_check_forge)
        self.check_forge_button.grid(row=1, column=2, padx=6, pady=(4, 0), sticky="ew")

        self.status_label = ctk.CTkLabel(tab, text="Готово.", anchor="w")
        self.status_label.grid(row=5, column=0, columnspan=3, padx=14, pady=(4, 2), sticky="ew")

        self.progress = ctk.CTkProgressBar(tab)
        self.progress.grid(row=6, column=0, columnspan=3, padx=14, pady=(2, 8), sticky="ew")
        self.progress.set(0)

        ctk.CTkLabel(
            tab,
            text="Вывод игры появляется во вкладке «Консоль». Для полного вывода лучше указывать java.exe, а не javaw.exe.",
            text_color="#bdbdbd",
            wraplength=980,
            justify="left"
        ).grid(row=7, column=0, columnspan=3, padx=14, pady=(0, 8), sticky="w")

        self.refresh_launch_info()
        self.refresh_manual_forge_button()

    def create_info_card(self, parent, title: str, row: int, column: int, columnspan: int = 1):
        card = ctk.CTkFrame(parent, corner_radius=14)
        card.grid(row=row, column=column, columnspan=columnspan, padx=6, pady=6, sticky="nsew")
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=15, weight="bold")
        ).grid(row=0, column=0, columnspan=2, padx=12, pady=(10, 4), sticky="w")

        card.value_labels = {}
        return card

    def set_card_rows(self, card, rows: list[tuple[str, str]]):
        for child in list(card.winfo_children()):
            info = child.grid_info()
            if int(info.get("row", 0)) > 0:
                child.destroy()

        card.value_labels = {}
        for idx, (label, value) in enumerate(rows, start=1):
            ctk.CTkLabel(card, text=label, text_color="#a9a9a9").grid(
                row=idx, column=0, padx=(12, 8), pady=2, sticky="w"
            )
            value_label = ctk.CTkLabel(
                card,
                text=value,
                text_color="#ffffff",
                anchor="w",
                justify="left",
                wraplength=260
            )
            value_label.grid(row=idx, column=1, padx=(0, 12), pady=2, sticky="ew")
            card.value_labels[label] = value_label

        ctk.CTkLabel(card, text="").grid(
            row=len(rows) + 1, column=0, columnspan=2, padx=12, pady=(0, 6), sticky="w"
        )

    def build_files_tab(self):
        tab = self.tab_files
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        buttons = ctk.CTkFrame(tab, fg_color="transparent")
        buttons.grid(row=0, column=0, columnspan=2, padx=16, pady=(18, 8), sticky="ew")
        buttons.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self.folder_buttons = {}
        folder_defs = [
            ("mods", "mods"),
            ("resourcepacks", "resourcepacks"),
            ("shaderpacks", "shaderpacks"),
            ("config", "config"),
            ("screenshots", "screenshots"),
        ]

        for i, (folder, label) in enumerate(folder_defs):
            button = ctk.CTkButton(buttons, text=label, command=lambda f=folder: self.show_folder(f))
            button.grid(row=0, column=i, padx=5, sticky="ew")
            self.folder_buttons[folder] = button

        self.folder_label = ctk.CTkLabel(tab, text="Выбери папку выше.", anchor="w")
        self.folder_label.grid(row=1, column=0, columnspan=2, padx=16, pady=(8, 4), sticky="ew")

        self.files_box = ctk.CTkTextbox(tab)
        self.files_box.grid(row=2, column=0, columnspan=2, padx=16, pady=(4, 12), sticky="nsew")
        self.files_box.configure(state="disabled")

        bottom = ctk.CTkFrame(tab, fg_color="transparent")
        bottom.grid(row=3, column=0, columnspan=2, padx=16, pady=(0, 16), sticky="ew")
        bottom.grid_columnconfigure((0, 1), weight=1)

        self.open_selected_folder_button = ctk.CTkButton(bottom, text="Открыть выбранную папку", command=self.open_current_folder)
        self.open_selected_folder_button.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        self.refresh_files_button = ctk.CTkButton(bottom, text="Обновить список", command=self.refresh_current_folder)
        self.refresh_files_button.grid(row=0, column=1, padx=(8, 0), sticky="ew")

        self.current_folder = "mods"

    def build_settings_tab(self):
        tab = self.tab_settings
        tab.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(tab, text="Настройки сборки", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, columnspan=3, padx=16, pady=(18, 8), sticky="w"
        )

        ctk.CTkLabel(tab, text="Название").grid(row=1, column=0, padx=16, pady=8, sticky="w")
        self.name_entry = ctk.CTkEntry(tab)
        self.name_entry.grid(row=1, column=1, columnspan=2, padx=16, pady=8, sticky="ew")

        ctk.CTkLabel(tab, text="Minecraft").grid(row=2, column=0, padx=16, pady=8, sticky="w")
        self.mc_entry = ctk.CTkEntry(tab)
        self.mc_entry.grid(row=2, column=1, padx=(16, 8), pady=8, sticky="ew")

        self.pick_mc_button = ctk.CTkButton(tab, text="Выбрать", width=110, command=self.pick_settings_version)
        self.pick_mc_button.grid(row=2, column=2, padx=(8, 16), pady=8, sticky="ew")

        ctk.CTkLabel(tab, text="Loader").grid(row=3, column=0, padx=16, pady=8, sticky="w")
        self.loader_combo = ctk.CTkComboBox(tab, values=get_available_mod_loaders(), command=lambda _: self.on_settings_loader_changed())
        self.loader_combo.grid(row=3, column=1, columnspan=2, padx=16, pady=8, sticky="ew")

        ctk.CTkLabel(tab, text="Loader version").grid(row=4, column=0, padx=16, pady=8, sticky="w")
        self.loader_version_combo = ctk.CTkComboBox(tab, values=[""])
        self.loader_version_combo.grid(row=4, column=1, padx=(16, 8), pady=8, sticky="ew")

        self.load_loader_versions_button = ctk.CTkButton(tab, text="Загрузить", width=110, command=self.load_settings_loader_versions)
        self.load_loader_versions_button.grid(row=4, column=2, padx=(8, 16), pady=8, sticky="ew")

        ctk.CTkLabel(tab, text="Forge mode").grid(row=5, column=0, padx=16, pady=8, sticky="w")
        self.forge_mode_combo = ctk.CTkComboBox(tab, values=["auto", "manual"])
        self.forge_mode_combo.grid(row=5, column=1, columnspan=2, padx=16, pady=8, sticky="ew")

        ctk.CTkLabel(tab, text="Java preset").grid(row=6, column=0, padx=16, pady=8, sticky="w")
        self.java_preset_combo = ctk.CTkComboBox(
            tab,
            values=JAVA_PRESET_VALUES,
            command=lambda _: self.on_settings_java_changed()
        )
        self.java_preset_combo.grid(row=6, column=1, columnspan=2, padx=16, pady=8, sticky="ew")

        ctk.CTkLabel(tab, text="Java этой сборки").grid(row=7, column=0, padx=16, pady=8, sticky="w")
        java_instance_row = ctk.CTkFrame(tab, fg_color="transparent")
        java_instance_row.grid(row=7, column=1, columnspan=2, padx=16, pady=8, sticky="ew")
        java_instance_row.grid_columnconfigure(0, weight=1)

        self.instance_java_entry = ctk.CTkEntry(java_instance_row, placeholder_text="auto = скачать/использовать portable Java")
        self.instance_java_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.instance_java_entry.bind("<FocusOut>", lambda _e: self.sync_settings_java_to_instance())
        self.instance_java_entry.bind("<Return>", lambda _e: self.sync_settings_java_to_instance())
        self.instance_java_button = ctk.CTkButton(java_instance_row, text="Выбрать", width=110, command=self.browse_instance_java)
        self.instance_java_button.grid(row=0, column=1, sticky="e")

        java_buttons = ctk.CTkFrame(tab, fg_color="transparent")
        java_buttons.grid(row=8, column=1, columnspan=2, padx=16, pady=(0, 8), sticky="ew")
        java_buttons.grid_columnconfigure((0, 1), weight=1)
        self.install_recommended_java_button = ctk.CTkButton(java_buttons, text="Установить рекомендуемую Java", command=self.on_install_recommended_java)
        self.install_recommended_java_button.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.install_preset_java_button = ctk.CTkButton(java_buttons, text="Установить выбранный preset", command=self.on_install_preset_java)
        self.install_preset_java_button.grid(row=0, column=1, padx=(8, 0), sticky="ew")

        self.java_hint_label = ctk.CTkLabel(tab, text="", text_color="#bdbdbd", wraplength=740, justify="left")
        self.java_hint_label.grid(row=9, column=1, columnspan=2, padx=16, pady=(0, 8), sticky="w")

        ctk.CTkLabel(tab, text="Server IP").grid(row=10, column=0, padx=16, pady=8, sticky="w")
        self.server_entry = ctk.CTkEntry(tab)
        self.server_entry.grid(row=10, column=1, columnspan=2, padx=16, pady=8, sticky="ew")

        self.ensure_server_var = ctk.BooleanVar(value=False)
        self.ensure_server_check = ctk.CTkCheckBox(tab, text="Добавлять сервер в servers.dat", variable=self.ensure_server_var)
        self.ensure_server_check.grid(row=11, column=1, columnspan=2, padx=16, pady=8, sticky="w")

        self.save_settings_button = ctk.CTkButton(tab, text="Сохранить настройки сборки", command=self.save_instance_settings)
        self.save_settings_button.grid(row=12, column=1, columnspan=2, padx=16, pady=(18, 8), sticky="ew")

        self.settings_note = ctk.CTkLabel(tab, text="", text_color="#bdbdbd", wraplength=740, justify="left")
        self.settings_note.grid(row=13, column=0, columnspan=3, padx=16, pady=8, sticky="w")

    def build_console_tab(self):
        tab = self.tab_console
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.grid(row=0, column=0, padx=16, pady=(18, 8), sticky="ew")
        top.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(top, text="Очистить", command=self.clear_console).grid(row=0, column=0, padx=(0, 8), sticky="ew")
        ctk.CTkButton(top, text="Открыть launcher.log", command=self.open_log).grid(row=0, column=1, padx=8, sticky="ew")
        ctk.CTkButton(top, text="Открыть папку logs", command=self.open_mc_logs).grid(row=0, column=2, padx=(8, 0), sticky="ew")

        self.console_box = ctk.CTkTextbox(tab)
        self.console_box.grid(row=1, column=0, padx=16, pady=(4, 16), sticky="nsew")
        self.console_box.insert("end", "Консоль сборки готова.\n")
        self.console_box.configure(state="disabled")

    def subscribe_console_history(self):
        self.console_key = get_console_key_for_instance(self.instance)
        register_console_listener(self.console_key, self.push_console)
        history = get_console_history(self.console_key, limit=500)
        if history:
            self.append_console("--- История вывода запущенной сборки ---")
            for line in history:
                self.append_console(line)

    def on_close(self):
        try:
            if hasattr(self, "console_key"):
                unregister_console_listener(self.console_key, self.push_console)
        except Exception:
            pass
        self.destroy()

    def render_java_value_for_instance(self) -> str:
        preset = (self.instance.get("java_preset") or "auto").strip().lower()
        if preset == "auto":
            return "auto"
        if preset.startswith("java"):
            return preset
        if preset == "manual":
            return self.instance.get("java_executable", "")
        if preset == "global":
            return self.app.settings.get("java_executable", self.app.config.get("java_executable", "java"))
        return self.instance.get("java_executable", "") or "auto"

    def refresh_all(self):
        self.instance = self.reload_instance()
        self.refresh_launch_info()
        self.refresh_manual_forge_button()

        self.title_label.configure(text=self.instance.get("name", "Instance"))
        subtitle = f"Minecraft {self.instance.get('minecraft_version')} • {self.instance.get('loader', 'vanilla')}"
        if self.instance.get("loader_version"):
            subtitle += f" {self.instance.get('loader_version')}"
        if self.instance.get("server_ip"):
            subtitle += f" • {self.instance.get('server_ip')}"
        self.subtitle_label.configure(text=subtitle)

        self.refresh_accounts()
        self.refresh_settings()
        self.show_folder(self.current_folder)

    def refresh_accounts(self):
        self.app.accounts_data = load_accounts()
        accounts = self.app.accounts_data.get("accounts", [])
        labels = [account_label(acc) for acc in accounts]
        self.account_combo.configure(values=labels or [tr("Нет аккаунтов")])
        selected = get_selected_account(self.app.accounts_data)
        if selected:
            self.account_combo.set(account_label(selected))
        elif labels:
            self.account_combo.set(labels[0])

    def get_settings_java_values(self) -> tuple[str, str]:
        preset = self.java_preset_combo.get().strip().lower() or "auto"
        if preset not in JAVA_PRESET_VALUES:
            preset = "auto"

        java_path = self.instance_java_entry.get().strip()
        if preset != "manual":
            java_path = ""

        return preset, java_path

    def on_settings_java_changed(self):
        self.on_java_preset_changed()
        self.sync_settings_java_to_instance()

    def sync_settings_java_to_instance(self):
        if getattr(self, "_refreshing_settings", False) or getattr(self, "_syncing_java_settings", False):
            return

        preset, java_path = self.get_settings_java_values()
        current_preset = (self.instance.get("java_preset") or "auto").strip().lower()
        current_path = self.instance.get("java_executable", "") or ""

        if preset == current_preset and java_path == current_path:
            return

        self._syncing_java_settings = True
        try:
            self.app.instances_data, _info = update_instance(
                self.app.config,
                self.instance["id"],
                {
                    "java_preset": preset,
                    "java_executable": java_path,
                }
            )
            self.instance = self.reload_instance()
            self.app.refresh_instances_ui()
            self.refresh_launch_info()
        except Exception as exc:
            messagebox.showerror("StoneLight Launcher", str(exc))
        finally:
            self._syncing_java_settings = False

    def refresh_settings(self):
        self._refreshing_settings = True
        self.name_entry.configure(state="normal")
        self.mc_entry.configure(state="normal")
        self.loader_combo.configure(state="normal")
        self.loader_version_combo.configure(state="normal")
        self.pick_mc_button.configure(state="normal")
        self.load_loader_versions_button.configure(state="normal")
        self.save_settings_button.configure(state="normal")

        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, self.instance.get("name", ""))

        self.mc_entry.delete(0, "end")
        self.mc_entry.insert(0, self.instance.get("minecraft_version", ""))

        self.loader_combo.set(self.instance.get("loader", "vanilla"))

        self.loader_version_combo.configure(values=[self.instance.get("loader_version", "")])
        self.loader_version_combo.set(self.instance.get("loader_version", ""))

        self.forge_mode_combo.set(self.instance.get("forge_install_mode", "auto"))

        self.java_preset_combo.set(self.instance.get("java_preset", "auto"))

        self.instance_java_entry.delete(0, "end")
        self.instance_java_entry.insert(0, self.instance.get("java_executable", ""))

        self.update_java_hint()
        self.on_java_preset_changed()

        self.server_entry.delete(0, "end")
        self.server_entry.insert(0, self.instance.get("server_ip", ""))

        self.ensure_server_var.set(bool(self.instance.get("ensure_server_in_list", False)))

        locked = bool(self.instance.get("locked"))
        state = "disabled" if locked else "normal"
        self.name_entry.configure(state=state)
        self.mc_entry.configure(state=state)
        self.loader_combo.configure(state=state)
        self.pick_mc_button.configure(state=state)
        self.forge_mode_combo.configure(state=state)
        # Java-настройки разрешены даже для защищённой официальной сборки:
        # защищены версия, loader и модпак, но не выбор Java.
        self.java_preset_combo.configure(state="normal")
        self.instance_java_entry.configure(state="normal")
        self.instance_java_button.configure(state="normal")
        self.install_recommended_java_button.configure(state="normal")
        self.install_preset_java_button.configure(state="normal")
        self.save_settings_button.configure(state="normal")

        if locked:
            self.settings_note.configure(text="Официальная сборка StoneLight защищена от редактирования версии, loader и модпака.")
        else:
            self.settings_note.configure(text="После смены версии/loader нажми «Обновить / установить», чтобы скачать Minecraft и установить модлоадер.")

        self.on_settings_loader_changed(locked=locked)
        self.refresh_manual_forge_button()
        self._refreshing_settings = False

    def is_forge_instance(self) -> bool:
        return (self.instance.get("loader") or "vanilla").lower() == "forge"

    def refresh_manual_forge_button(self):
        if not all(hasattr(self, name) for name in ("repair_button", "manual_forge_button", "check_forge_button")):
            return

        if self.is_forge_instance():
            self.repair_button.grid(row=1, column=0, padx=(0, 6), pady=(4, 0), sticky="ew")
            self.manual_forge_button.grid(row=1, column=1, padx=6, pady=(4, 0), sticky="ew")
            self.check_forge_button.grid(row=1, column=2, padx=6, pady=(4, 0), sticky="ew")
            self.repair_button.configure(state="normal")
            self.manual_forge_button.configure(state="normal")
            self.check_forge_button.configure(state="normal")
        else:
            self.repair_button.grid_remove()
            self.manual_forge_button.grid_remove()
            self.check_forge_button.grid_remove()

    def on_account_selected(self, label: str):
        account = find_account_by_label(self.app.accounts_data, label)
        if account:
            self.app.accounts_data = select_account(account["id"])

    def browse_java(self):
        # Java меняется на вкладке «Настройки».
        self.tabs.set(getattr(self, "tab_settings_name", tr("Настройки")))
        self.browse_instance_java()

    def browse_instance_java(self):
        filetypes = [
            ("Java executable", "java.exe javaw.exe"),
            ("Executable", "*.exe"),
            ("All files", "*.*")
        ]
        path = filedialog.askopenfilename(title="Выбери java.exe или javaw.exe для этой сборки", filetypes=filetypes)
        if path:
            self.instance_java_entry.delete(0, "end")
            self.instance_java_entry.insert(0, path)

    def global_launch_settings_rows(self) -> list[tuple[str, str]]:
        settings = normalize_global_launch_settings(self.app.settings, self.app.config)
        mode = "Полноэкранный" if settings["fullscreen"] else "Оконный"
        return [
            ("RAM", f"{settings['ram_min_mb']}–{settings['ram_max_mb']} МБ"),
            ("Режим", mode),
        ]

    def instance_java_rows(self) -> list[tuple[str, str]]:
        preset = (self.instance.get("java_preset") or "auto").strip().lower()
        version = self.instance.get("minecraft_version", "")
        recommendation = suggest_java_for_minecraft(version)

        if preset == "manual":
            java_text = self.instance.get("java_executable", "") or "не выбран"
        elif preset == "global":
            java_text = self.app.settings.get("java_executable", self.app.config.get("java_executable", "java"))
        elif preset == "auto":
            java_text = "Автоматически по версии Minecraft"
        else:
            java_text = preset

        return [
            ("Preset", preset),
            ("Используется", java_text),
            ("Рекомендация", recommendation.replace("Рекомендуется: ", "")),
        ]

    def refresh_launch_info(self):
        if not hasattr(self, "build_card"):
            return

        loader = self.instance.get("loader", "vanilla")
        loader_version = self.instance.get("loader_version", "")
        loader_text = loader if not loader_version else f"{loader} {loader_version}"

        self.set_card_rows(self.build_card, [
            ("Название", self.instance.get("name", "")),
            ("Minecraft", self.instance.get("minecraft_version", "")),
            ("Loader", loader_text),
        ])
        self.set_card_rows(self.global_card, self.global_launch_settings_rows())
        self.set_card_rows(self.java_card, self.instance_java_rows())

    def read_launch_form(self):
        label = self.account_combo.get()
        account = find_account_by_label(self.app.accounts_data, label) or get_selected_account(self.app.accounts_data)
        if not account:
            raise LauncherError("Нет выбранного аккаунта. Войди в лицензионный Microsoft/Minecraft аккаунт.")

        username = account.get("username", "").strip()

        if account.get("type") == "offline":
            ok, message = validate_offline_username(username)
            if not ok:
                raise LauncherError(message)
        elif account.get("type") != "microsoft":
            raise LauncherError("Неизвестный тип аккаунта.")

        global_settings = normalize_global_launch_settings(self.app.settings, self.app.config)
        ram_mb = int(global_settings["ram_max_mb"])

        preset = (self.instance.get("java_preset") or "auto").strip().lower()
        java_text = self.instance.get("java_executable", "")

        if preset in ("auto", "java8", "java16", "java17", "java21", "java25"):
            java_executable = preset
        elif preset == "manual":
            java_executable = java_text
        elif preset == "global":
            java_executable = self.app.settings.get("java_executable", self.app.config.get("java_executable", "java"))
        else:
            java_executable = java_text or "auto"

        self.app.settings.update({
            "username": username,
            "selected_account_id": account.get("id", ""),
            "selected_instance_id": self.instance.get("id", ""),
        })
        save_user_settings(self.app.settings)
        select_account(account["id"])
        select_instance(self.app.config, self.instance["id"])

        return username, ram_mb, java_executable, account

    def set_busy(self, busy: bool):
        state = "disabled" if busy else "normal"
        for widget in [self.play_button, self.update_button, self.open_folder_button]:
            widget.configure(state=state)

        if self.is_forge_instance():
            for widget in [self.repair_button, self.manual_forge_button, self.check_forge_button]:
                widget.configure(state=state)
        if hasattr(self, "stop_button"):
            self.stop_button.configure(state="normal")
        if hasattr(self, "install_recommended_java_button"):
            self.install_recommended_java_button.configure(state=state)
            self.install_preset_java_button.configure(state=state)

        if not busy:
            self.refresh_manual_forge_button()

    def start_worker(self, target, done_message: str):
        if self.worker_thread and self.worker_thread.is_alive():
            messagebox.showwarning("StoneLight Launcher", "Уже выполняется задача.")
            return

        try:
            username, ram_mb, java_executable, account = self.read_launch_form()
        except Exception as exc:
            messagebox.showerror("StoneLight Launcher", str(exc))
            return

        self.set_busy(True)
        self.progress.set(0)
        self.tabs.set(getattr(self, "tab_console_name", tr("Консоль")))

        def wrapper():
            try:
                core = LauncherCore(
                    instance=self.instance,
                    log_callback=self.push_console,
                    status_callback=self.push_status,
                    progress_callback=self.push_progress,
                    console_callback=self.push_console
                )
                launch_account = account
                if launch_account.get("type") == "microsoft":
                    client_id, redirect_uri, client_secret = self.app.get_microsoft_auth_config()
                    self.app.accounts_data, _info = refresh_microsoft_account(launch_account["id"], client_id, redirect_uri, client_secret)
                    launch_account = get_selected_account(self.app.accounts_data) or launch_account

                target(core, username, ram_mb, java_executable, launch_account)
                self.queue.put(("done", done_message))
            except Exception as exc:
                self.queue.put(("error", str(exc)))

        self.worker_thread = threading.Thread(target=wrapper, daemon=True)
        self.worker_thread.start()

    def on_stop_game(self):
        try:
            core = LauncherCore(
                instance=self.instance,
                log_callback=self.push_console,
                status_callback=self.push_status,
                console_callback=self.push_console,
            )
            message = core.force_stop_game()
            self.append_console(message)
        except Exception as exc:
            messagebox.showerror("StoneLight Launcher", str(exc))

    def on_play(self):
        self.start_worker(
            lambda core, username, ram_mb, java, account: core.run_full(username, ram_mb, java, force_modpack_download=False, account=account),
            "Minecraft запущен."
        )

    def on_update(self):
        self.start_worker(
            lambda core, username, ram_mb, java, account: core.update_only(java, force_download=True),
            "Сборка обновлена/установлена."
        )

    def on_repair(self):
        self.start_worker(
            lambda core, username, ram_mb, java, account: core.repair_instance(java),
            "Repair завершён."
        )

    def on_manual_forge(self):
        if (self.instance.get("loader") or "vanilla").lower() != "forge":
            messagebox.showinfo("StoneLight Launcher", "Ручной установщик нужен только для Forge-сборок.")
            return

        game_dir = self.get_game_dir()
        message = (
            "Сейчас откроется Forge Installer.\n\n"
            "В нём выбери Install client и укажи папку сборки:\n\n"
            f"{game_dir}\n\n"
            "Лаунчер заранее создаст launcher_profiles.json, чтобы старый Forge принял папку.\n"
            "После установки в открывшемся окне нажми «Проверить Forge» или «Играть»."
        )
        if not messagebox.askyesno("Ручной Forge Installer", message):
            return

        self.start_worker(
            lambda core, username, ram_mb, java, account: core.run_forge_installer_manual(java),
            "Forge Installer запущен. Заверши установку в его окне, затем нажми «Проверить Forge»."
        )

    def on_check_forge(self):
        if (self.instance.get("loader") or "vanilla").lower() != "forge":
            messagebox.showinfo("StoneLight Launcher", "Проверка Forge нужна только для Forge-сборок.")
            return

        self.start_worker(
            lambda core, username, ram_mb, java, account: core.check_forge_installed(),
            "Проверка Forge завершена."
        )

    def push_console(self, message: str):
        self.queue.put(("console", message))

    def push_status(self, message: str):
        self.queue.put(("status", message))

    def push_progress(self, current: int, total: int):
        self.queue.put(("progress", current, total))

    def poll_queue(self):
        try:
            while True:
                event = self.queue.get_nowait()
                kind = event[0]

                if kind == "console":
                    self.append_console(event[1])
                elif kind == "status":
                    self.status_label.configure(text=event[1])
                    self.append_console(event[1])
                elif kind == "progress":
                    current, total = event[1], event[2]
                    if total > 0:
                        self.progress.set(max(0, min(1, current / total)))
                elif kind == "done":
                    self.set_busy(False)
                    self.progress.set(1)
                    self.append_console(event[1])
                elif kind == "java_installed":
                    self.set_busy(False)
                    self.progress.set(1)
                    java_path, major = event[1], event[2]
                    self.instance_java_entry.configure(state="normal")
                    self.instance_java_entry.delete(0, "end")
                    self.instance_java_entry.insert(0, java_path)
                    self.java_preset_combo.set(f"java{major}")
                    self.save_instance_settings()
                    self.append_console(f"Portable Java {major} установлена и сохранена для сборки: {java_path}")
                elif kind == "error":
                    self.set_busy(False)
                    self.progress.set(0)
                    messagebox.showerror("StoneLight Launcher", event[1])
                    self.append_console("ОШИБКА: " + event[1])
        except queue.Empty:
            pass

        self.after(100, self.poll_queue)

    def append_console(self, message: str):
        self.console_box.configure(state="normal")
        self.console_box.insert("end", str(message).rstrip() + "\n")
        self.console_box.see("end")
        self.console_box.configure(state="disabled")

    def clear_console(self):
        self.console_box.configure(state="normal")
        self.console_box.delete("1.0", "end")
        self.console_box.configure(state="disabled")

    def get_game_dir(self) -> Path:
        return ROOT / self.instance.get("game_directory", "data/instances/Unknown/.minecraft")

    def ensure_folder(self, folder_name: str) -> Path:
        game_dir = self.get_game_dir()
        path = game_dir / folder_name
        path.mkdir(parents=True, exist_ok=True)
        return path

    def show_folder(self, folder_name: str):
        self.current_folder = folder_name
        path = self.ensure_folder(folder_name)
        self.folder_label.configure(text=str(path))

        items = []
        try:
            for child in sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
                mark = "[DIR]" if child.is_dir() else "     "
                size = "" if child.is_dir() else f"  {child.stat().st_size // 1024} KB"
                items.append(f"{mark} {child.name}{size}")
        except Exception as exc:
            items.append(f"Ошибка чтения папки: {exc}")

        if not items:
            items = ["Папка пустая."]

        self.files_box.configure(state="normal")
        self.files_box.delete("1.0", "end")
        self.files_box.insert("end", "\n".join(items))
        self.files_box.configure(state="disabled")

    def refresh_current_folder(self):
        self.show_folder(self.current_folder)

    def open_current_folder(self):
        safe_os_startfile(self.ensure_folder(self.current_folder))

    def open_game_folder(self):
        game_dir = self.get_game_dir()
        game_dir.mkdir(parents=True, exist_ok=True)
        safe_os_startfile(game_dir)

    def open_log(self):
        log_path = ROOT / "data" / "launcher.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        if not log_path.exists():
            log_path.write_text("", encoding="utf-8")
        os.startfile(log_path)

    def open_mc_logs(self):
        safe_os_startfile(self.ensure_folder("logs"))

    def pick_settings_version(self):
        VersionPickerDialog(
            self,
            initial_version=self.mc_entry.get().strip(),
            include_snapshots=True,
            on_select=self.apply_settings_version
        )

    def apply_settings_version(self, value: str):
        self.mc_entry.delete(0, "end")
        self.mc_entry.insert(0, value)
        self.update_java_hint()

    def update_java_hint(self):
        version = self.mc_entry.get().strip() if hasattr(self, "mc_entry") else self.instance.get("minecraft_version", "")
        hint = suggest_java_for_minecraft(version)
        self.java_hint_label.configure(text=f"Рекомендация для {version or 'версии'}: {hint}. Preset auto скачает/использует portable Java в data/java.")

    def on_java_preset_changed(self):
        preset = self.java_preset_combo.get().strip().lower() if hasattr(self, "java_preset_combo") else "auto"
        if preset in ("auto", "java8", "java16", "java17", "java21", "java25"):
            self.instance_java_entry.configure(state="disabled")
            self.instance_java_button.configure(state="disabled")
        else:
            locked = bool(self.instance.get("locked"))
            self.instance_java_entry.configure(state="disabled" if locked else "normal")
            self.instance_java_button.configure(state="disabled" if locked else "normal")

    def get_selected_java_major_for_install(self, recommended: bool):
        version = self.mc_entry.get().strip() or self.instance.get("minecraft_version", "")
        if recommended:
            return recommended_java_major_for_minecraft(version)

        preset = self.java_preset_combo.get().strip().lower()
        if preset == "java8":
            return 8
        if preset == "java16":
            return 16
        if preset == "java17":
            return 17
        if preset == "java21":
            return 21
        if preset == "java25":
            return 25
        if preset == "auto":
            return recommended_java_major_for_minecraft(version)

        return None

    def install_java_worker(self, major: int):
        if not major:
            messagebox.showerror("StoneLight Launcher", "Для этого preset нельзя определить версию Java.")
            return

        self.tabs.set(getattr(self, "tab_console_name", tr("Консоль")))
        self.set_busy(True)
        self.progress.set(0)

        def wrapper():
            try:
                core = LauncherCore(
                    instance=self.instance,
                    log_callback=self.push_console,
                    status_callback=self.push_status,
                    progress_callback=self.push_progress,
                    console_callback=self.push_console
                )
                java_path = core.install_portable_java(major)
                self.queue.put(("java_installed", java_path, major))
            except Exception as exc:
                self.queue.put(("error", str(exc)))

        self.worker_thread = threading.Thread(target=wrapper, daemon=True)
        self.worker_thread.start()

    def on_install_recommended_java(self):
        self.install_java_worker(self.get_selected_java_major_for_install(recommended=True))

    def on_install_preset_java(self):
        self.install_java_worker(self.get_selected_java_major_for_install(recommended=False))

    def on_settings_loader_changed(self, *_args, locked=False):
        loader = (self.loader_combo.get() or "vanilla").strip().lower()
        if loader == "vanilla":
            self.loader_version_combo.configure(values=[""], state="disabled")
            self.loader_version_combo.set("")
            self.load_loader_versions_button.configure(state="disabled")
            self.forge_mode_combo.configure(state="disabled")
        else:
            self.loader_version_combo.configure(state="normal")
            if loader == "forge":
                self.forge_mode_combo.configure(state="normal" if not locked else "disabled")
            else:
                self.forge_mode_combo.configure(state="disabled")
            if not locked:
                self.load_loader_versions_button.configure(state="normal")

        if locked:
            self.loader_version_combo.configure(state="disabled")
            self.load_loader_versions_button.configure(state="disabled")
            self.forge_mode_combo.configure(state="disabled")

        if loader == "vanilla":
            self.folder_buttons["mods"].configure(state="disabled")
        else:
            self.folder_buttons["mods"].configure(state="normal")

        # Показываем Forge-служебные кнопки только для Forge-сборок.
        if hasattr(self, "repair_button"):
            temp_loader = self.instance.get("loader", "vanilla")
            self.instance["loader"] = loader
            self.refresh_manual_forge_button()
            self.instance["loader"] = temp_loader

    def load_settings_loader_versions(self):
        loader = (self.loader_combo.get() or "").strip().lower()
        minecraft_version = self.mc_entry.get().strip()

        if loader in ("", "vanilla"):
            self.settings_note.configure(text="Для vanilla модлоадер не нужен.")
            return

        self.load_loader_versions_button.configure(state="disabled")
        self.settings_note.configure(text=f"Загружаю версии {loader} для Minecraft {minecraft_version}...")

        def worker():
            automatic_only = not (loader == "forge" and self.forge_mode_combo.get().strip().lower() == "manual")
            versions = get_loader_versions(loader, minecraft_version, stable_only=False, automatic_only=automatic_only)
            self.after(0, lambda: self.apply_settings_loader_versions(loader, minecraft_version, versions))

        threading.Thread(target=worker, daemon=True).start()

    def apply_settings_loader_versions(self, loader, minecraft_version, versions):
        self.load_loader_versions_button.configure(state="normal")
        if versions:
            self.loader_version_combo.configure(values=versions)
            self.loader_version_combo.set(versions[0])
            self.settings_note.configure(text=f"Найдено версий {loader}: {len(versions)} для Minecraft {minecraft_version}. Выбери нужную в открытом списке.")

            def choose(value):
                self.loader_version_combo.set(value)

            SelectableListDialog(
                self,
                f"Версии {loader} для {minecraft_version}",
                versions,
                choose,
                filter_placeholder="Фильтр версии loader"
            )
        else:
            self.loader_version_combo.configure(values=[""])
            self.loader_version_combo.set("")
            self.settings_note.configure(
                text=f"Не найдено автоматически поддерживаемых версий {loader} для Minecraft {minecraft_version}. "
                     f"Можно оставить поле пустым: лаунчер попробует взять последнюю доступную, если loader это поддерживает."
            )

    def save_instance_settings(self):
        self.sync_settings_java_to_instance()
        if self.instance.get("locked"):
            updates = {
                "java_preset": self.java_preset_combo.get().strip().lower() or "auto",
                "java_executable": self.instance_java_entry.get().strip(),
                "server_ip": self.server_entry.get().strip(),
                "ensure_server_in_list": bool(self.ensure_server_var.get()),
                "server_list_name": self.instance.get("name", "StoneLight"),
            }
        else:
            updates = {
                "name": self.name_entry.get().strip(),
                "minecraft_version": self.mc_entry.get().strip(),
                "loader": self.loader_combo.get().strip().lower() or "vanilla",
                "loader_version": self.loader_version_combo.get().strip(),
                "java_preset": self.java_preset_combo.get().strip().lower() or "auto",
                "java_executable": self.instance_java_entry.get().strip(),
                "forge_install_mode": self.forge_mode_combo.get().strip().lower() or "auto",
                "server_ip": self.server_entry.get().strip(),
                "ensure_server_in_list": bool(self.ensure_server_var.get()),
                "server_list_name": self.name_entry.get().strip(),
            }

        try:
            self.app.instances_data, info = update_instance(self.app.config, self.instance["id"], updates)
            self.instance = self.reload_instance()
            self.refresh_all()
            self.app.refresh_instances_ui()
            self.app.refresh_global_launch_summary()
            self.append_console(info)
        except Exception as exc:
            messagebox.showerror("StoneLight Launcher", str(exc))


class StoneLightLauncherApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(APP_TITLE)
        self.geometry("1040x880")
        self.minsize(960, 800)

        ctk.set_default_color_theme("blue")

        self.ui_queue = queue.Queue()
        self.worker_thread = None
        self.instance_windows = {}
        self._syncing_launch_settings = False
        self.settings = load_user_settings()
        self.config = LauncherCore().base_config
        i18n.set_language(self.settings.get("language", self.config.get("language", "en")))
        self.current_theme = normalize_theme(self.settings.get("theme", self.config.get("theme", "dark")))
        apply_ctk_theme(self.current_theme)
        apply_theme_to_window(self)

        self.instances_data = load_instances(self.config)
        self.accounts_data = ensure_initial_account()

        self.build_ui()
        self.refresh_instances_ui()
        self.refresh_accounts_ui()
        self.poll_queue()

    def build_ui(self):
        apply_theme_to_window(self)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        header = ctk.CTkFrame(self, corner_radius=18)
        header.grid(row=0, column=0, padx=18, pady=(18, 10), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        title = ctk.CTkLabel(
            header,
            text="StoneLight Launcher",
            font=ctk.CTkFont(size=30, weight="bold")
        )
        title.grid(row=0, column=0, padx=18, pady=(16, 0), sticky="w")

        self.subtitle = ctk.CTkLabel(header, text="", text_color="#bdbdbd")
        self.subtitle.grid(row=1, column=0, padx=18, pady=(0, 16), sticky="w")

        header_tools = ctk.CTkFrame(header, fg_color="transparent")
        header_tools.grid(row=0, column=1, rowspan=2, padx=18, pady=14, sticky="e")
        header_tools.grid_columnconfigure(1, weight=1)

        self.language_label = ctk.CTkLabel(header_tools, text="Language")
        self.language_label.grid(row=0, column=0, padx=(0, 8), pady=(0, 8), sticky="e")

        self.language_combo = ctk.CTkComboBox(
            header_tools,
            values=list(i18n.LANGUAGE_NAMES.values()),
            width=155,
            command=self.on_language_changed
        )
        self.language_combo.grid(row=0, column=1, pady=(0, 8), sticky="ew")
        self.language_combo.set(i18n.language_label(i18n.get_language()))

        self.theme_label = ctk.CTkLabel(header_tools, text="Theme")
        self.theme_label.grid(row=1, column=0, padx=(0, 8), pady=(0, 8), sticky="e")

        self.theme_combo = ctk.CTkComboBox(
            header_tools,
            values=[theme_label(code) for code in ("dark", "light", "laconic", "neon", "retro_future")],
            width=155,
            command=self.on_theme_changed
        )
        self.theme_combo.grid(row=1, column=1, pady=(0, 8), sticky="ew")
        self.theme_combo.set(theme_label(self.current_theme))

        self.github_button = ctk.CTkButton(
            header_tools,
            text="Open GitHub",
            width=155,
            command=self.open_github
        )
        self.github_button.grid(row=2, column=0, columnspan=2, sticky="ew")

        instance_frame = ctk.CTkFrame(self, corner_radius=18)
        instance_frame.grid(row=1, column=0, padx=18, pady=8, sticky="ew")
        instance_frame.grid_columnconfigure(1, weight=1)
        instance_frame.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(
            instance_frame,
            text="Сборка",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, columnspan=4, padx=16, pady=(16, 8), sticky="w")

        ctk.CTkLabel(instance_frame, text="Выбранная").grid(row=1, column=0, padx=16, pady=8, sticky="w")
        self.instance_combo = ctk.CTkComboBox(
            instance_frame,
            values=[],
            command=self.on_instance_selected
        )
        self.instance_combo.grid(row=1, column=1, columnspan=3, padx=16, pady=8, sticky="ew")

        self.open_instance_button = ctk.CTkButton(
            instance_frame,
            text="Открыть окно сборки",
            command=self.on_open_instance_window
        )
        self.open_instance_button.grid(row=2, column=0, padx=16, pady=(8, 16), sticky="ew")

        self.create_instance_button = ctk.CTkButton(
            instance_frame,
            text="Создать сборку",
            command=self.on_create_instance
        )
        self.create_instance_button.grid(row=2, column=1, padx=8, pady=(8, 16), sticky="ew")

        self.delete_instance_button = ctk.CTkButton(
            instance_frame,
            text="Удалить сборку",
            fg_color="#7a1f1f",
            hover_color="#9b2929",
            command=self.on_delete_instance
        )
        self.delete_instance_button.grid(row=2, column=2, padx=8, pady=(8, 16), sticky="ew")

        self.open_instance_folder_button = ctk.CTkButton(
            instance_frame,
            text="Папка",
            command=self.on_open_instance_folder
        )
        self.open_instance_folder_button.grid(row=2, column=3, padx=(8, 16), pady=(8, 16), sticky="ew")

        self.instance_info = ctk.CTkLabel(
            instance_frame,
            text="",
            text_color="#a9a9a9",
            anchor="w"
        )
        self.instance_info.grid(row=3, column=0, columnspan=4, padx=16, pady=(0, 16), sticky="ew")

        account_frame = ctk.CTkFrame(self, corner_radius=18)
        account_frame.grid(row=2, column=0, padx=18, pady=8, sticky="ew")
        account_frame.grid_columnconfigure(1, weight=1)
        account_frame.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(
            account_frame,
            text="Аккаунт",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, columnspan=4, padx=16, pady=(16, 8), sticky="w")

        ctk.CTkLabel(account_frame, text="Выбранный").grid(row=1, column=0, padx=16, pady=8, sticky="w")
        self.account_combo = ctk.CTkComboBox(
            account_frame,
            values=[],
            command=self.on_account_selected
        )
        self.account_combo.grid(row=1, column=1, columnspan=3, padx=16, pady=8, sticky="ew")

        self.microsoft_login_button = ctk.CTkButton(
            account_frame,
            text="Войти Microsoft",
            command=self.on_microsoft_login
        )
        self.microsoft_login_button.grid(row=2, column=0, padx=16, pady=(8, 8), sticky="ew")

        self.refresh_license_button = ctk.CTkButton(
            account_frame,
            text="Обновить лицензию",
            command=self.on_refresh_microsoft
        )
        self.refresh_license_button.grid(row=2, column=1, padx=8, pady=(8, 8), sticky="ew")

        self.delete_account_button = ctk.CTkButton(
            account_frame,
            text="Удалить аккаунт",
            fg_color="#7a1f1f",
            hover_color="#9b2929",
            command=self.on_delete_account
        )
        self.delete_account_button.grid(row=2, column=2, columnspan=2, padx=(8, 16), pady=(8, 8), sticky="ew")

        ctk.CTkLabel(account_frame, text="Offline-ник").grid(row=3, column=0, padx=16, pady=(8, 16), sticky="w")
        self.new_account_entry = ctk.CTkEntry(account_frame, placeholder_text="Доступно после входа в лицензионный аккаунт")
        self.new_account_entry.grid(row=3, column=1, padx=(16, 8), pady=(8, 16), sticky="ew")

        self.add_account_button = ctk.CTkButton(
            account_frame,
            text="Добавить offline",
            command=self.on_add_account
        )
        self.add_account_button.grid(row=3, column=2, padx=8, pady=(8, 16), sticky="ew")

        self.account_policy_label = ctk.CTkLabel(
            account_frame,
            text="Offline-аккаунты разрешены только после входа хотя бы в один лицензионный аккаунт.",
            text_color="#bdbdbd",
            wraplength=260,
            justify="left"
        )
        self.account_policy_label.grid(row=3, column=3, padx=(8, 16), pady=(8, 16), sticky="w")

        form = ctk.CTkFrame(self, corner_radius=18)
        form.grid(row=3, column=0, padx=18, pady=8, sticky="ew")
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            form,
            text="Java выбранной сборки",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, columnspan=3, padx=16, pady=(16, 8), sticky="w")

        ctk.CTkLabel(form, text="Java preset").grid(row=1, column=0, padx=16, pady=8, sticky="w")
        self.java_preset_combo = ctk.CTkComboBox(form, values=JAVA_PRESET_VALUES, command=lambda _: self.on_main_java_preset_changed())
        self.java_preset_combo.grid(row=1, column=1, columnspan=2, padx=16, pady=8, sticky="ew")

        ctk.CTkLabel(form, text="Java").grid(row=2, column=0, padx=16, pady=8, sticky="w")
        java_row = ctk.CTkFrame(form, fg_color="transparent")
        java_row.grid(row=2, column=1, columnspan=2, padx=16, pady=8, sticky="ew")
        java_row.grid_columnconfigure(0, weight=1)

        self.java_entry = ctk.CTkEntry(java_row)
        self.java_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.java_entry.bind("<FocusOut>", lambda _e: self.sync_main_launch_settings_to_instance(validate=False))
        self.java_entry.bind("<Return>", lambda _e: self.sync_main_launch_settings_to_instance(validate=True))

        self.browse_java_button = ctk.CTkButton(java_row, text="Выбрать", width=100, command=self.browse_java)
        self.browse_java_button.grid(row=0, column=1, sticky="e")

        self.global_summary_label = ctk.CTkLabel(form, text="", text_color="#bdbdbd", anchor="w")
        self.global_summary_label.grid(row=3, column=0, columnspan=2, padx=16, pady=(8, 16), sticky="ew")

        self.global_settings_button = ctk.CTkButton(
            form,
            text="Глобальные настройки запуска",
            width=210,
            command=self.on_global_launch_settings
        )
        self.global_settings_button.grid(row=3, column=2, padx=16, pady=(8, 16), sticky="e")

        actions = ctk.CTkFrame(self, corner_radius=18)
        actions.grid(row=4, column=0, padx=18, pady=6, sticky="ew")
        actions.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.play_button = ctk.CTkButton(
            actions,
            text="Играть выбранную",
            height=40,
            command=self.on_play
        )
        self.play_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.update_button = ctk.CTkButton(
            actions,
            text="Обновить / установить",
            height=40,
            command=self.on_update
        )
        self.update_button.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.stop_button = ctk.CTkButton(
            actions,
            text="Остановить",
            height=40,
            fg_color="#7a1f1f",
            hover_color="#9b2929",
            command=self.on_stop_game
        )
        self.stop_button.grid(row=0, column=2, padx=10, pady=10, sticky="ew")

        self.open_log_button = ctk.CTkButton(
            actions,
            text="Открыть лог",
            height=40,
            command=self.open_log
        )
        self.open_log_button.grid(row=0, column=3, padx=10, pady=10, sticky="ew")

        status_frame = ctk.CTkFrame(self, corner_radius=18)
        status_frame.grid(row=5, column=0, padx=18, pady=(8, 18), sticky="nsew")
        status_frame.grid_columnconfigure(0, weight=1)
        status_frame.grid_rowconfigure(2, weight=1)

        self.status_label = ctk.CTkLabel(status_frame, text="Готов к запуску.", anchor="w")
        self.status_label.grid(row=0, column=0, padx=16, pady=(14, 4), sticky="ew")

        self.progress = ctk.CTkProgressBar(status_frame)
        self.progress.grid(row=1, column=0, padx=16, pady=(4, 10), sticky="ew")
        self.progress.set(0)

        self.log_box = ctk.CTkTextbox(status_frame, height=140)
        self.log_box.grid(row=2, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self.log_box.insert("end", "Добро пожаловать в StoneLight Launcher v0.5.32\n")
        self.log_box.configure(state="disabled")

    def open_github(self):
        webbrowser.open(self.config.get("github_url", GITHUB_URL))

    def on_language_changed(self, label: str):
        language = i18n.language_code_from_label(label)
        self.settings["language"] = language
        save_user_settings(self.settings)
        i18n.set_language(language)

        for win in list(self.instance_windows.values()):
            try:
                if win and win.winfo_exists():
                    win.destroy()
            except Exception:
                pass
        self.instance_windows = {}

        for child in list(self.winfo_children()):
            child.destroy()

        self.build_ui()
        self.refresh_instances_ui()
        self.refresh_accounts_ui()
        self.append_log("Language changed.")

    def on_theme_changed(self, label: str):
        theme = theme_code_from_label(label)
        self.current_theme = theme
        self.settings["theme"] = theme
        save_user_settings(self.settings)
        apply_ctk_theme(theme)
        apply_theme_to_window(self)

        for win in list(self.instance_windows.values()):
            try:
                if win and win.winfo_exists():
                    win.destroy()
            except Exception:
                pass
        self.instance_windows = {}

        for child in list(self.winfo_children()):
            child.destroy()

        self.build_ui()
        self.refresh_instances_ui()
        self.refresh_accounts_ui()
        self.append_log("Theme changed.")

    def get_global_launch_settings(self) -> dict:
        return normalize_global_launch_settings(self.settings, self.config)

    def refresh_global_launch_summary(self):
        if not hasattr(self, "global_summary_label"):
            return
        current = self.get_global_launch_settings()
        mode = tr("полноэкранный") if current["fullscreen"] else tr("оконный")
        template = tr("Глобально для всех сборок: RAM {min}–{max} МБ, режим: {mode}.")
        self.global_summary_label.configure(
            text=template.format(min=current["ram_min_mb"], max=current["ram_max_mb"], mode=mode)
        )

    def on_global_launch_settings(self):
        GlobalLaunchSettingsDialog(self)

    def render_java_value_for_instance(self, instance: dict) -> str:
        preset = (instance.get("java_preset") or "auto").strip().lower()
        if preset == "auto":
            return "auto"
        if preset.startswith("java"):
            return preset
        if preset == "manual":
            return instance.get("java_executable", "")
        if preset == "global":
            return self.settings.get("java_executable", self.config.get("java_executable", "java"))
        return instance.get("java_executable", "") or "auto"

    def refresh_launch_settings_ui(self):
        instance = self.get_selected_instance(silent=True) if hasattr(self, "instance_combo") else None
        if not instance or not hasattr(self, "java_preset_combo"):
            return

        self._syncing_launch_settings = True
        try:
            preset = (instance.get("java_preset") or "auto").strip().lower()
            if preset not in JAVA_PRESET_VALUES:
                preset = "auto"

            self.java_preset_combo.set(preset)
            self.java_entry.configure(state="normal")
            self.java_entry.delete(0, "end")
            self.java_entry.insert(0, self.render_java_value_for_instance(instance))
            self.on_main_java_preset_changed(save=False)
            self.refresh_global_launch_summary()
        finally:
            self._syncing_launch_settings = False

    def on_main_java_preset_changed(self, save=True):
        preset = self.java_preset_combo.get().strip().lower() if hasattr(self, "java_preset_combo") else "auto"
        if preset in ("auto", "java8", "java16", "java17", "java21", "java25", "global"):
            self.java_entry.configure(state="disabled")
            self.browse_java_button.configure(state="disabled")
        else:
            self.java_entry.configure(state="normal")
            self.browse_java_button.configure(state="normal")

        if save and not getattr(self, "_syncing_launch_settings", False):
            self.sync_main_launch_settings_to_instance(validate=False)

    def sync_main_launch_settings_to_instance(self, validate=False):
        if getattr(self, "_syncing_launch_settings", False):
            return self.get_selected_instance(silent=True)

        instance = self.get_selected_instance(silent=True)
        if not instance:
            return None

        preset = self.java_preset_combo.get().strip().lower() or "auto"
        if preset not in JAVA_PRESET_VALUES:
            preset = "auto"

        java_text = self.java_entry.get().strip()
        instance_java_executable = java_text if preset == "manual" else ""

        self._syncing_launch_settings = True
        try:
            self.instances_data, _info = update_instance(
                self.config,
                instance["id"],
                {
                    "java_preset": preset,
                    "java_executable": instance_java_executable,
                }
            )
            self.instances_data = select_instance(self.config, instance["id"])
            updated = find_instance_by_id(self.instances_data, instance["id"]) or instance

            self.settings.update({
                "selected_instance_id": instance.get("id", ""),
            })
            save_user_settings(self.settings)

            self.refresh_instances_ui()

            existing = self.instance_windows.get(instance["id"])
            if existing and existing.winfo_exists():
                existing.refresh_all()

            return updated
        finally:
            self._syncing_launch_settings = False

    def refresh_header(self):
        instance = self.get_selected_instance(silent=True)
        if not instance:
            self.subtitle.configure(text="Minecraft / Loader")
            self.instance_info.configure(text="")
            return

        text = (
            f"{instance.get('name')} • "
            f"Minecraft {instance.get('minecraft_version')} • "
            f"{instance.get('loader', 'vanilla')}"
        )
        if instance.get("loader_version"):
            text += f" {instance.get('loader_version')}"
        if instance.get("server_ip"):
            text += f" • {instance.get('server_ip')}"
        self.subtitle.configure(text=text)

        if instance.get("official"):
            info = tr("StoneLight: модпак + сервер в списке + защита от удаления")
        elif instance.get("loader") == "vanilla":
            info = tr("Пустая vanilla-сборка")
        else:
            info = tr("Пустая сборка с loader: {loader}").format(loader=instance.get("loader"))
        self.instance_info.configure(text=info)

    def refresh_instances_ui(self):
        self.instances_data = load_instances(self.config)
        instances = self.instances_data.get("instances", [])
        labels = [instance_label(inst) for inst in instances]

        if not labels:
            self.instance_combo.configure(values=["Нет сборок"])
            self.instance_combo.set("Нет сборок")
            self.refresh_header()
            return

        selected = get_selected_instance(self.instances_data) or instances[0]
        selected_label = instance_label(selected)

        self.instance_combo.configure(values=labels)
        self.instance_combo.set(selected_label)
        self.refresh_header()
        self.refresh_launch_settings_ui()
        self.refresh_global_launch_summary()

    def get_selected_instance(self, silent=False):
        label = self.instance_combo.get()
        instance = find_instance_by_label(self.instances_data, label)
        if instance:
            return instance

        instance = get_selected_instance(self.instances_data)
        if instance:
            return instance

        if silent:
            return None
        raise LauncherError("Нет выбранной сборки.")

    def on_instance_selected(self, label: str):
        instance = find_instance_by_label(self.instances_data, label)
        if not instance:
            return

        self.instances_data = select_instance(self.config, instance["id"])
        self.refresh_instances_ui()

    def on_open_instance_window(self):
        try:
            instance = self.get_selected_instance()
            existing = self.instance_windows.get(instance["id"])
            if existing and existing.winfo_exists():
                existing.focus()
                return

            win = InstanceWindow(self, instance["id"])
            self.instance_windows[instance["id"]] = win
        except Exception as exc:
            messagebox.showerror("StoneLight Launcher", str(exc))

    def on_create_instance(self):
        CreateInstanceDialog(self)

    def on_delete_instance(self):
        try:
            instance = self.get_selected_instance()
        except Exception as exc:
            messagebox.showerror("StoneLight Launcher", str(exc))
            return

        if instance.get("locked"):
            messagebox.showerror("StoneLight Launcher", "Официальную сборку StoneLight нельзя удалить.")
            return

        if not messagebox.askyesno("StoneLight Launcher", f"Удалить сборку {instance.get('name')} из списка? Папка на диске не удаляется."):
            return

        try:
            self.instances_data, info = delete_instance(self.config, instance["id"])
            self.refresh_instances_ui()
            self.append_log(info)
        except Exception as exc:
            messagebox.showerror("StoneLight Launcher", str(exc))

    def on_open_instance_folder(self):
        try:
            instance = self.get_selected_instance()
            game_dir = ROOT / instance.get("game_directory", "data/instances/Unknown/.minecraft")
            game_dir.mkdir(parents=True, exist_ok=True)
            for name in ["mods", "config", "resourcepacks", "shaderpacks"]:
                (game_dir / name).mkdir(parents=True, exist_ok=True)
            os.startfile(game_dir)
        except Exception as exc:
            messagebox.showerror("StoneLight Launcher", f"Не удалось открыть папку сборки: {exc}")

    def refresh_accounts_ui(self):
        self.accounts_data = load_accounts()
        accounts = self.accounts_data.get("accounts", [])
        labels = [account_label(acc) for acc in accounts]
        licensed = has_licensed_account(self.accounts_data)

        if not labels:
            self.account_combo.configure(values=[tr("Нет аккаунтов")])
            self.account_combo.set(tr("Нет аккаунтов"))
            self.new_account_entry.delete(0, "end")
            self.new_account_entry.configure(state="disabled")
            self.add_account_button.configure(state="disabled")
            return

        selected = get_selected_account(self.accounts_data) or accounts[0]
        selected_label = account_label(selected)

        self.account_combo.configure(values=labels)
        self.account_combo.set(selected_label)

        self.new_account_entry.configure(state="normal" if licensed else "disabled")
        self.add_account_button.configure(state="normal" if licensed else "disabled")

        self.new_account_entry.delete(0, "end")
        if selected.get("type") == "offline":
            self.new_account_entry.insert(0, selected.get("username", ""))

    def get_selected_account(self):
        label = self.account_combo.get()
        account = find_account_by_label(self.accounts_data, label)
        if account:
            return account

        account = get_selected_account(self.accounts_data)
        if account:
            return account

        raise LauncherError("Нет выбранного аккаунта. Войди в лицензионный Microsoft/Minecraft аккаунт.")

    def on_account_selected(self, label: str):
        account = find_account_by_label(self.accounts_data, label)
        if not account:
            return

        self.accounts_data = select_account(account["id"])
        self.new_account_entry.delete(0, "end")
        if account.get("type") == "offline":
            self.new_account_entry.insert(0, account.get("username", ""))

    def on_microsoft_login(self):
        MicrosoftLoginDialog(self)

    def get_microsoft_auth_config(self):
        client_id = self.settings.get("microsoft_client_id", self.config.get("microsoft_client_id", "")).strip()
        redirect_uri = self.settings.get("microsoft_redirect_uri", self.config.get("microsoft_redirect_uri", "http://localhost:8765/callback")).strip() or "http://localhost:8765/callback"
        client_secret = self.config.get("microsoft_client_secret", "") or None
        if not client_id:
            raise LauncherError("Не указан Microsoft Azure App Client ID. Нажми «Войти Microsoft» и укажи Client ID.")
        return client_id, redirect_uri, client_secret

    def on_refresh_microsoft(self):
        try:
            account = self.get_selected_account()
            if account.get("type") != "microsoft":
                messagebox.showinfo("StoneLight Launcher", "Обновление нужно только для лицензионных Microsoft-аккаунтов.")
                return

            client_id, redirect_uri, client_secret = self.get_microsoft_auth_config()
            self.accounts_data, info = refresh_microsoft_account(account["id"], client_id, redirect_uri, client_secret)
            self.refresh_accounts_ui()
            self.append_log(info)
        except Exception as exc:
            messagebox.showerror("StoneLight Launcher", str(exc))

    def on_add_account(self):
        username = self.new_account_entry.get().strip()
        ok, message = validate_offline_username(username)

        if not ok:
            messagebox.showerror("StoneLight Launcher", message)
            return

        try:
            self.accounts_data, info = add_or_update_offline_account(username)
            self.refresh_accounts_ui()
            self.append_log(info + f" {username}")
        except Exception as exc:
            messagebox.showerror("StoneLight Launcher", str(exc))

    def on_delete_account(self):
        try:
            account = self.get_selected_account()
        except Exception as exc:
            messagebox.showerror("StoneLight Launcher", str(exc))
            return

        username = account.get("username", "")
        if not messagebox.askyesno("StoneLight Launcher", f"Удалить аккаунт {username}?"):
            return

        self.accounts_data, info = delete_account(account["id"])
        self.refresh_accounts_ui()
        self.append_log(info)

    def browse_java(self):
        filetypes = [
            ("Java executable", "java.exe javaw.exe"),
            ("Executable", "*.exe"),
            ("All files", "*.*")
        ]
        path = filedialog.askopenfilename(title="Выбери java.exe или javaw.exe", filetypes=filetypes)
        if path:
            self.java_preset_combo.set("manual")
            self.on_main_java_preset_changed(save=False)
            self.java_entry.configure(state="normal")
            self.java_entry.delete(0, "end")
            self.java_entry.insert(0, path)
            self.sync_main_launch_settings_to_instance(validate=False)

    def read_form(self):
        self.sync_main_launch_settings_to_instance(validate=True)
        instance = self.get_selected_instance()
        account = self.get_selected_account()
        username = account.get("username", "").strip()

        if account.get("type") == "offline":
            ok, message = validate_offline_username(username)
            if not ok:
                raise LauncherError(message)
        elif account.get("type") != "microsoft":
            raise LauncherError("Неизвестный тип аккаунта.")

        global_settings = normalize_global_launch_settings(self.settings, self.config)
        ram_mb = int(global_settings["ram_max_mb"])

        java_preset = self.java_preset_combo.get().strip().lower() or "auto"
        java_text = self.java_entry.get().strip()
        if java_preset in ("auto", "java8", "java16", "java17", "java21", "java25"):
            java_executable = java_preset
            instance_java_executable = ""
        elif java_preset == "manual":
            java_executable = java_text
            instance_java_executable = java_text
        elif java_preset == "global":
            java_executable = self.settings.get("java_executable", self.config.get("java_executable", "java"))
            instance_java_executable = ""
        else:
            java_executable = java_text or "auto"
            instance_java_executable = java_text

        return username, ram_mb, java_executable, account, instance, java_preset, instance_java_executable

    def save_form(self, username, ram_mb, java_executable, account, instance, java_preset, instance_java_executable):
        self.settings.update({
            "username": username,
            "selected_account_id": account.get("id", ""),
            "selected_instance_id": instance.get("id", ""),
        })
        save_user_settings(self.settings)

        if account.get("id"):
            select_account(account["id"])
            self.accounts_data = load_accounts()

        if instance.get("id"):
            self.instances_data = select_instance(self.config, instance["id"])
            self.instances_data, _ = update_instance(
                self.config,
                instance["id"],
                {"java_preset": java_preset, "java_executable": instance_java_executable}
            )
            updated = find_instance_by_id(self.instances_data, instance["id"]) or instance
            self.refresh_instances_ui()
            existing = self.instance_windows.get(instance["id"])
            if existing and existing.winfo_exists():
                existing.refresh_all()
            return updated

        return instance

    def set_busy(self, busy: bool):
        state = "disabled" if busy else "normal"
        for widget in [
            self.play_button, self.update_button, self.add_account_button, self.delete_account_button,
            self.browse_java_button, self.java_preset_combo, self.account_combo, self.instance_combo, self.create_instance_button,
            self.delete_instance_button, self.open_instance_button, self.open_instance_folder_button, self.global_settings_button
        ]:
            widget.configure(state=state)
        if hasattr(self, "stop_button"):
            self.stop_button.configure(state="normal")
        if not busy:
            self.on_main_java_preset_changed()

    def push_log(self, message: str):
        self.ui_queue.put(("log", message))

    def push_status(self, message: str):
        self.ui_queue.put(("status", message))

    def push_progress(self, current: int, total: int):
        self.ui_queue.put(("progress", current, total))

    def poll_queue(self):
        try:
            while True:
                event = self.ui_queue.get_nowait()
                kind = event[0]

                if kind == "log":
                    self.append_log(event[1])
                elif kind == "status":
                    self.status_label.configure(text=event[1])
                    self.append_log(event[1])
                elif kind == "progress":
                    current, total = event[1], event[2]
                    if total > 0:
                        self.progress.set(max(0, min(1, current / total)))
                elif kind == "done":
                    self.set_busy(False)
                    self.progress.set(1)
                    self.append_log(event[1])
                elif kind == "error":
                    self.set_busy(False)
                    self.progress.set(0)
                    messagebox.showerror("StoneLight Launcher", event[1])
                    self.append_log("ОШИБКА: " + event[1])
        except queue.Empty:
            pass

        self.after(100, self.poll_queue)

    def append_log(self, message: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", str(message).rstrip() + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def start_worker(self, target, done_message: str):
        if self.worker_thread and self.worker_thread.is_alive():
            messagebox.showwarning("StoneLight Launcher", "Уже выполняется задача.")
            return

        try:
            username, ram_mb, java_executable, account, instance, java_preset, instance_java_executable = self.read_form()
            instance = self.save_form(username, ram_mb, java_executable, account, instance, java_preset, instance_java_executable)
        except Exception as exc:
            messagebox.showerror("StoneLight Launcher", str(exc))
            return

        self.set_busy(True)
        self.progress.set(0)

        def wrapper():
            try:
                core = LauncherCore(
                    instance=instance,
                    log_callback=self.push_log,
                    status_callback=self.push_status,
                    progress_callback=self.push_progress,
                    console_callback=self.push_log
                )
                launch_account = account
                if launch_account.get("type") == "microsoft":
                    client_id, redirect_uri, client_secret = self.get_microsoft_auth_config()
                    self.accounts_data, _info = refresh_microsoft_account(launch_account["id"], client_id, redirect_uri, client_secret)
                    launch_account = get_selected_account(self.accounts_data) or launch_account

                target(core, username, ram_mb, java_executable, launch_account)
                self.ui_queue.put(("done", done_message))
            except Exception as exc:
                self.ui_queue.put(("error", str(exc)))

        self.worker_thread = threading.Thread(target=wrapper, daemon=True)
        self.worker_thread.start()

    def on_stop_game(self):
        try:
            instance = self.get_selected_instance()
            core = LauncherCore(
                instance=instance,
                log_callback=self.push_log,
                status_callback=self.push_status,
                console_callback=self.push_log,
            )
            message = core.force_stop_game()
            self.append_log(message)
        except Exception as exc:
            messagebox.showerror("StoneLight Launcher", str(exc))

    def on_play(self):
        self.start_worker(
            lambda core, username, ram_mb, java, account: core.run_full(username, ram_mb, java, force_modpack_download=False, account=account),
            "Minecraft запущен."
        )

    def on_update(self):
        self.start_worker(
            lambda core, username, ram_mb, java, account: core.update_only(java, force_download=True),
            "Сборка обновлена/установлена."
        )

    def open_log(self):
        log_path = ROOT / "data" / "launcher.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        if not log_path.exists():
            log_path.write_text("", encoding="utf-8")

        try:
            os.startfile(log_path)
        except Exception as exc:
            messagebox.showerror("StoneLight Launcher", f"Не удалось открыть лог: {exc}")


if __name__ == "__main__":
    app = StoneLightLauncherApp()
    app.mainloop()
