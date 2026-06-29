# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

ROOT = Path.cwd()
block_cipher = None

datas = [
    ("config.json", "."),
    ("README.md", "."),
    ("SECURITY.md", "."),
    ("MODS_FOUND.md", "."),
    ("docs", "docs"),
    ("assets", "assets"),
    ("requirements.txt", "."),
]

hiddenimports = [
    "customtkinter",
    "minecraft_launcher_lib",
    "minecraft_launcher_lib.microsoft_account",
    "minecraft_launcher_lib.fabric",
    "minecraft_launcher_lib.forge",
    "minecraft_launcher_lib.quilt",
    "minecraft_launcher_lib.natives",
    "requests",
    "PIL",
    "PIL.Image",
    "PIL.ImageTk",
]

a = Analysis(
    ["StoneLightLauncher.pyw"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter.test", "unittest", "pytest"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="StoneLight Launcher",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "assets" / "stonelight_launcher.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="StoneLight Launcher",
)
