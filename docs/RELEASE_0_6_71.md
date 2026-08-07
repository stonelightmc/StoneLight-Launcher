# StoneLight Launcher v0.6.71

Release-ready build focused on CurseForge integration, modpack management, and final polish.

## Highlights

- CurseForge catalog integration through the StoneLight backend proxy.
- CurseForge content search and installation for:
  - mods;
  - resource packs;
  - shaders;
  - modpacks.
- CurseForge modpack preflight:
  - reads `manifest.json`;
  - shows Minecraft version, loader and file counts;
  - separates automatically downloadable files from manual-required content.
- CurseForge modpack installation:
  - installs into the selected user instance;
  - reconfigures the instance from the CurseForge manifest;
  - copies overrides;
  - downloads available files;
  - keeps manual-required files in a readable report.
- CurseForge modpack update support:
  - update check;
  - update install;
  - safe cleanup of old managed files when hashes still match.
- Unified Modrinth/CurseForge modpack update UI.
- Dependency preview/confirmation flow for catalog installs.
- Physical instance deletion from disk with a localized confirmation modal.
- Instance cloning from the tile context menu, excluding worlds, screenshots and logs.
- Official StoneLight pack config cleanup:
  - removed stale `mods_zip_url` / `mods_zip_sha256` from bundled config;
  - added explicit fallback keys;
  - GitHub Releases discovery remains the source of truth.
- Mojang component download retry/timeout improvements.
- Version picker scroll reset fix.
- Localization and status-message polish for EN/UA/KZ.

## Notes

- Backend remains `StoneLight CurseForge Proxy v0.5.4`.
- No CurseForge API key is stored in the launcher.
- This source package is intended for GitHub upload/release preparation.
- Windows EXE packaging still needs to be built on Windows using the existing build scripts.
