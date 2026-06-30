# Updates

StoneLight Launcher v0.5.52 adds the first update system.

## Launcher updates

The launcher checks GitHub Releases from:

```text
stonelightmc/StoneLight-Launcher
```

Expected asset:

```text
*GitHub.zip
```

The launcher downloads the update into:

```text
data/updates/
```

Then it creates:

```text
apply_launcher_update.cmd
```

The launcher update is staged because a running launcher should not overwrite its own files directly.

## Official StoneLight build updates

The official modpack update check reads GitHub Releases from:

```text
stonelightmc/stonelightmc.github.io
```

Expected asset pattern:

```text
mods_*.zip
```

If a new modpack URL is found, the launcher can update local `config.json` metadata and run the normal instance update process.

## Safety

The self-update script excludes runtime/user files:

```text
accounts.json
user_settings.json
instances.json
data/
*.log
.git/
```


## v0.5.52 official pre-launch update

When the selected instance is the official `StoneLight` instance, the launcher now checks the official modpack release before launching the game.

Flow:

```text
Play StoneLight
→ check GitHub Releases for mods_*.zip
→ if new archive exists, ask user to update before launch
→ update config.json metadata
→ reload official StoneLight instance
→ run normal install/update process with force modpack download
→ launch the new Minecraft version
```

This is intentionally limited to the official `stonelight` instance and does not affect custom user instances.

The official instance keeps user launch settings such as:

```text
java_preset
java_executable
ram_mb
server settings
```


## v0.5.52

Manual update check behavior:

- Launcher update check always runs.
- Official StoneLight modpack update check runs only when the selected instance is the official `stonelight` instance.
- For custom instances, the official modpack check is skipped and logged.
- The Install button performs only local install/reinstall using current metadata.


## v0.5.52

Update check timeout:

```text
update_check_timeout_seconds = 12
```

If GitHub/update checks do not complete in time, the launcher clears the busy state and writes a localized timeout message.


## v0.5.52 Windows EXE self-update

Self-update is now aware of two launcher package types:

```text
Source/dev package:
StoneLightLauncher_v0_5_xx_GitHub.zip

Windows user package:
StoneLightLauncher_v0_5_xx_Windows.zip
```

When running from source, the launcher still searches for the `GitHub.zip` asset.

When running as a Windows executable, the launcher searches for the `Windows.zip` asset, using:

```json
"launcher_update_windows_asset_keyword": "Windows.zip"
```

The apply script now supports Windows one-folder PyInstaller layout:

```text
StoneLight Launcher/
  StoneLight Launcher.exe
  _internal/
  config.json
  docs/
  assets/
```

It updates `_internal` as well, while preserving user data:

```text
data/
accounts.json
user_settings.json
instances.json
```
