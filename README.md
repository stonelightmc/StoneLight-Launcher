# StoneLight Launcher v0.5.24

Unofficial Minecraft launcher for the StoneLight community.

## Features

- Official StoneLight instance.
- Separate MultiMC-like instances.
- Vanilla / Fabric / Forge / Quilt / NeoForge support.
- Portable Java manager with presets.
- Global launch settings.
- Legacy Forge fixes for old Minecraft versions.
- Microsoft licensed account login.
- Offline accounts are allowed only after at least one licensed account exists locally.

## Microsoft login

The launcher already includes the StoneLight Azure Application Client ID:

```text
28e78bd7-fb55-4391-b9dd-5d596a718c65
```

Redirect URI:

```text
http://localhost
```

Client secret is not used and must not be committed.

See:

```text
docs/MICROSOFT_LOGIN.md
```

## First run

Run:

```text
StoneLightLauncher.cmd
```

or debug mode:

```text
StoneLightLauncher_debug.cmd
```

The first run installs required Python packages into a local `.venv`.

## Requirements

- Windows 10/11
- Python 3.11+
- Internet access to Microsoft, Mojang/Minecraft, Java provider, and modpack sources.

## GitHub safety

Do not commit:

```text
accounts.json
user_settings.json
instances.json
data/
*.log
```

These are already listed in `.gitignore`.

## Disclaimer

StoneLight Launcher is not affiliated with Microsoft, Mojang Studios, or Minecraft.
