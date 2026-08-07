# CurseForge Stage 3 install

This local source snapshot fixes and improves CurseForge content installation.

## Changes

- Fixed `LauncherWebAPI object has no attribute _set_busy`.
- The CurseForge install button now passes the compatible file id selected during search.
- The backend installs the same compatible file shown in the card when possible.
- Downloaded files are written to the correct instance folder:
  - mods -> `mods/`
  - resource packs -> `resourcepacks/`
  - shaders -> `shaderpacks/`
- The existing CurseForge hash check is kept.
- Duplicate protection was added:
  - if the same file is already present and hash/source record matches, the launcher returns `already_installed`;
  - if a file with the same name exists but is not known/matching, installation is blocked to avoid overwriting user files.
- Installed CurseForge files are recorded in `.stonelight_sources.json`.

## Not included yet

- Dependency installation.
- CurseForge modpack manifest support.
- Similar duplicate protection for Modrinth installs.
