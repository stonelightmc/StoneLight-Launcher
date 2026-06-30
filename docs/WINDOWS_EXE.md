# Windows EXE build

v0.5.52 adds Windows executable packaging support.

## Build

On Windows, run:

```bat
build_windows_exe.cmd
```

The script creates:

```text
dist\StoneLight Launcher\StoneLight Launcher.exe
```

## Why one-folder EXE, not one-file EXE?

StoneLight Launcher stores user data and game files next to the launcher:

```text
accounts.json
user_settings.json
instances.json
data/
```

A one-folder PyInstaller build keeps these paths predictable and is much safer for self-updates.

## Publishing

For GitHub Releases, zip the whole folder:

```text
dist\StoneLight Launcher
```

Recommended release asset name:

```text
StoneLightLauncher_v0_5_50_Windows.zip
```

The old source archive can still be published as:

```text
StoneLightLauncher_v0_5_50_GitHub.zip
```


## v0.5.52 config/runtime-file fix

PyInstaller one-folder builds may place bundled data under `_internal`.
The launcher expects writable files next to the `.exe`, so v0.5.52 adds two protections:

1. `build_windows_exe.cmd` copies these files next to the exe after build:

```text
config.json
requirements.txt
README.md
SECURITY.md
MODS_FOUND.md
docs/
assets/
```

2. At runtime, `app_paths.ensure_runtime_files()` copies missing bundled resources from `_internal` to the exe folder on first launch.


## v0.5.52 self-update note

For executable releases, publish the built folder as:

```text
StoneLightLauncher_v0_5_52_Windows.zip
```

The ZIP should contain the whole folder:

```text
StoneLight Launcher/
  StoneLight Launcher.exe
  _internal/
  config.json
  docs/
  assets/
```

The executable launcher will prefer the `Windows.zip` release asset for self-updates.
