# CurseForge Stage 2b Hotfix

This source snapshot fixes the Stage 2 UI bridge exposure issue.

## Fix

`StoneLightLauncherWeb.pyw` now exposes these CurseForge methods to pywebview and browser fallback:

- `get_curseforge_settings`
- `save_curseforge_api_key`
- `search_curseforge`
- `get_curseforge_project_files`
- `get_curseforge_download_url`
- `install_curseforge_project`

Without this, the UI tab is visible but search fails with:

```text
Python API method is unavailable: search_curseforge
```
