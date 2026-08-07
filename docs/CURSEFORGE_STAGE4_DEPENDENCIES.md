# CurseForge Stage 4 dependencies

This local source snapshot adds automatic installation of required CurseForge dependencies.

## Changes

- When installing a CurseForge mod, the launcher reads the selected file's `dependencies`.
- Required dependencies (`relationType = 3`) are installed automatically.
- Dependencies are resolved for the same selected instance, Minecraft version and mod loader.
- Nested required dependencies are supported up to a safe depth limit.
- Dependency cycles are skipped.
- Already installed CurseForge projects are detected through `.stonelight_sources.json`.
- The UI toast/log can show how many dependencies were installed.

## Not included yet

- Optional dependency selection.
- User confirmation dialog listing dependencies before install.
- Dependency management/removal.
- Modrinth duplicate/dependency improvements.
- CurseForge modpacks.
