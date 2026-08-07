# CurseForge backend integration — local Stage 2 snapshot

This is a local development snapshot based on StoneLight Launcher 0.6.71.
It is not intended as a GitHub release yet.

## Included changes

- CurseForge API key is not stored in the launcher.
- Launcher uses the StoneLight backend/proxy endpoints:
  - `https://stonelight-api.serveminecraft.net`
  - `https://stonelight-api.duckdns.org`
- Added fallback backend URL support.
- Added compact CurseForge client methods in `launcher_api.py`.
- Added a CurseForge tab to the web UI.
- Added project search, project page opening, and individual file install entry points.
- CurseForge modpack import is intentionally left for a later stage.

## Important local testing note

`StoneLightLauncherWeb.pyw` now uses a cache-busted web UI URL:

```text
web_ui/index.html?v=<launcher_version>-cf-stage2&transport=webview#desktop=1
```

This avoids WebView2 showing an older cached copy of `index.html` during local testing.

## Recommended test flow

```powershell
setup.cmd
py -m py_compile launcher_api.py StoneLightLauncherWeb.pyw
.\StoneLightLauncher.cmd
```

Then select a Fabric/Forge/NeoForge/Quilt instance and open the `CurseForge` tab.
Try searches such as:

```text
jei
sodium
journeymap
```

Modpack import is not supported in this stage.
