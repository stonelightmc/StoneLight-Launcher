# StoneLight Launcher v0.6.68

Unofficial Minecraft launcher for the StoneLight community.

## Features

- Official StoneLight instance.
- Separate MultiMC-like instances.
- Vanilla / Fabric / Forge / Quilt / NeoForge support.
- Portable Java manager with presets.
- Global launch settings.
- Legacy Forge fixes for old Minecraft versions.
- Microsoft licensed account login.
- Automatic local Microsoft OAuth callback.
- Language selector:
  - English default
  - Ukrainian
  - Kazakh
- GitHub button on the main window.
- Offline accounts are allowed only after at least one licensed account exists locally.

## GitHub

Repository:

```text
https://github.com/stonelightmc/StoneLight-Launcher
```

## Microsoft login

Client ID:

```text
28e78bd7-fb55-4391-b9dd-5d596a718c65
```

Redirect URI:

```text
http://localhost:8765/callback
```

Client secret is not used and must not be committed.

## Safety

Do not commit:

```text
accounts.json
user_settings.json
instances.json
data/
*.log
```

## Disclaimer

StoneLight Launcher is not affiliated with Microsoft, Mojang Studios, or Minecraft.


## v0.6.68

Deeper localization pass:

- more small grey helper comments translated
- Microsoft callback browser page localized
- textbox/status output translated through the UI localization layer
- more dynamic UI fragments translated


## v0.6.68 — pywebview shell prototype

`StoneLightLauncher.cmd` now launches the new HTML/CSS/JavaScript shell.

The stable CustomTkinter interface is preserved and can be started with:

```text
StoneLightLauncherClassic.cmd
```

New files:

```text
StoneLightLauncherWeb.pyw
bootstrap_web.py
launcher_api.py
web_ui/
StoneLightLauncherWeb.spec
build_windows_web_exe.cmd
```

The official StoneLight instance is optional on a fresh web-shell start. It is
shown as an install offer instead of being silently created/downloaded.
