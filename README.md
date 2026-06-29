# StoneLight Launcher v0.5.36

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


## v0.5.36

Deeper localization pass:

- more small grey helper comments translated
- Microsoft callback browser page localized
- textbox/status output translated through the UI localization layer
- more dynamic UI fragments translated
