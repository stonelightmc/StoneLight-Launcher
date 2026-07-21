# StoneLight Launcher 0.6.x Web UI Architecture

## Stable base

The web shell is built on top of the stable `v0.5.75` Python core.

```text
web_ui/
    HTML / CSS / JavaScript
          |
          v
launcher_api.py
          |
          v
launcher_core.py / accounts.py / instances.py / updater.py
```

JavaScript is responsible only for presentation and user interaction. Python
remains the source of truth for accounts, instance metadata, launching,
installing, updates and filesystem access.

## v0.6.66 scope

Working in the first prototype:

- pywebview desktop shell
- layout based on the approved numbered sketch
- real instance tiles from `instances.json`
- instance selection
- account / Java / global launch summaries
- Play / Install / Stop callbacks through the existing Python core
- optional official StoneLight instance
- theme and language switching without rebuilding the window
- custom tile context menu
- status, progress and expandable log drawer
- classic CustomTkinter UI fallback

Reserved for later versions:

- creating/editing instances inside the web shell
- Microsoft login inside the web shell
- Modrinth catalog
- CurseForge catalog and modpack import
- full instance settings page
- self-update UI polish

## Security boundary

Remote Modrinth or CurseForge pages must not be loaded into the same trusted
document that has access to `window.pywebview.api`. Future integrations should
use Python HTTP clients and render local launcher-owned UI.


## v0.6.66 shell polish

- launcher branding remains in the hero header instead of the menu bar
- selected instance is secondary information below the launcher title
- account summary is no longer duplicated in the hero
- duplicate Add Instance toolbar button removed
- tile context menu closes on outside click, scroll, resize, tab switch, window blur and Escape
- instance API reserves an optional `icon` metadata field for a later icon picker


## v0.6.66 bridge/runtime hotfix

- desktop mode waits for `pywebviewready` before requesting state
- mock instance data is available only in a normal browser preview
- first run creates `data/`, cache, instances, instance-icons and launcher log
- empty JSON state is created without silently adding the official instance
- metadata-only StoneLight records from older classic builds are treated as an install offer
- state inspection no longer constructs `LauncherCore` and therefore has no filesystem side effects


## v0.6.66 local URL hotfix

Edge WebView may treat a query string appended to a local `file://` URL as part
of the requested file path. The desktop marker now uses the URL fragment
`#desktop=1`, which does not change the local file path.


## v0.6.66 internal HTTP transport

The shell now uses the relative `web_ui/index.html` entrypoint served by
pywebview's built-in local HTTP server. Public bridge methods are explicitly
registered with `window.expose`. The frontend considers the bridge ready only
when `get_app_state` is callable.
