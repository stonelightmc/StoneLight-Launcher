# StoneLight Launcher 0.6.x Roadmap

## 0.6.66 — Web shell skeleton

- approved desktop layout
- Python ↔ JavaScript bridge
- real instance cards
- optional official instance
- actions, status and classic fallback

## 0.6.66 — Native web workflows

- create / edit / delete instances in web UI
- Microsoft account login flow
- account manager drawer
- Java and global launch settings dialog
- more detailed operation state handling

## 0.6.66 — Instance details

- folders
- settings
- console
- Forge tools
- import / export

## 0.6.66 — Modrinth

- search
- filters
- project details
- install mods, resource packs and modpacks

## 0.6.66 — CurseForge

- API integration
- project catalog
- modpack import
- dependency handling

## 0.6.66 — Release polish

- updater integration
- diagnostics
- accessibility
- packaging and release migration


## Instance icon picker

Planned for the instance editor stage:

- built-in icon collection
- custom PNG / JPG / WebP import
- tile, hero and instance-details reuse the same icon metadata
- context menu entry for choosing an icon


## v0.6.66 completed

The first native Web UI workflow now covers custom instance creation,
editing and deletion. Account and Java/global managers remain planned for
the next native workflow stage.


## v0.6.66 completed

The Web UI editor now reuses the mature version metadata functions from the
0.5.x core, including the official Forge/Fabric/Quilt/NeoForge sources and
loader-version normalization.


## v0.6.66 completed

The official install offer and version selection UX were cleaned up. Version
metadata still comes from the mature Python core, but the Web UI now displays it
through a controlled picker instead of relying on browser-native datalists.


## v0.6.66 completed

The version pickers were changed to an explicit user action. Official-instance
version controls are visually locked to match the backend protection.


## v0.6.66 completed

Small copy polish after the native instance editor replaced the classic-UI
creation flow in the empty state.


## v0.6.66 completed

The account manager workflow is now native in the Web UI for selection,
offline accounts, deletion and refresh. Microsoft OAuth login remains delegated
to the classic interface until the browser callback flow is migrated.


## v0.6.66 completed

The first native instance window was added. The mods folder now has a simple
toggle manager that preserves disabled mods as `.jar.disabled` files.


## v0.6.66 completed

The instance window became the main instance-management surface. Settings are
embedded, Forge tools were restored, folders gained previews, mods/resource
packs/shader packs can be toggled by renaming, and screenshots now have a
preview/delete workflow.


## v0.6.66 completed

This is a stabilization pass for the v0.6.13 instance window. A stale event
binding was crashing initialization on first open; bindings are now guarded and
the folder/screenshot workflows were polished.


## v0.6.66 completed

Folder-preview scrolling and screenshot tile rendering were stabilized. Thumbnail
generation moved to Python/Pillow, keeping WebView tile images small even when
the original screenshots are around 5 MB.


## v0.6.66 completed

A cache-busting and stabilization pass fixed cases where old WebView scripts or
styles could remain visible after updating builds. Screenshot preview also gained
previous/next navigation.


## v0.6.66 completed

A layout-only stabilization pass for the instance window. The screenshot subtab
now scrolls internally and thumbnails keep a stable tile size.


## v0.6.66 completed

The embedded settings tab gained version picker buttons, and the instance window
layout was compacted further. Folder previews were adjusted so content starts
below the current-folder toolbar.


## v0.6.66 completed

A pure layout hotfix for folder subtabs, folder toolbar overlap and the embedded
settings footer.


## v0.6.66 completed

The logs subtab was converted from a folder preview into an embedded selectable
console, closer to the legacy instance window behavior.


## v0.6.66 completed

The official modpack updater can now fall back to GitHub Release asset discovery
when the exact configured ZIP filename changes.


## v0.6.66 completed

The official instance window now exposes update status and a clear update action,
backed by a small manifest written after official modpack installation.


## v0.6.66 completed

Fixed the missing urllib module access in GitHub Release asset discovery for
official modpack ZIP fallback.


## v0.6.66 completed

Fixed official modpack fallback when a new GitHub Release ZIP has a different
filename and therefore a different checksum than the old configured URL.


## v0.6.66 completed

Reduced noise and false positives in the official update notice. Missing old
manifests are backfilled from current instance metadata, and fallback archive
details no longer keep the user-facing update banner visible.


## v0.6.66 completed

The Web UI account manager gained native Microsoft OAuth login and Crafthead helm
avatars for account rows/cards.


## v0.6.66 completed

A hotfix for Microsoft account login in the Web UI. The button now uses a
non-blocking native web flow and polls login status instead of opening classic UI.


## v0.6.66 completed

First safe stage of the Web UI global launch settings. This stage does not touch
Minecraft graphics options beyond optional fullscreen/window mode.


## v0.6.66 completed

Removed Java from global launch settings. Global settings are now limited to
version-independent launch behavior: RAM and game window settings.


## v0.6.66 completed

Added the first stage of optional Minecraft options.txt settings. The launcher
only applies fields that are explicitly configured by the user.


## v0.6.66 completed

Added graphics profiles and particle amount controls. Presets fill the visible
fields, and manual edits switch the profile to Custom.


## v0.6.66 completed

Added a native Web UI update center for launcher and official instance updates.


## v0.6.66 completed

Adjusted update center logic so launcher updates are always checked, while
official instance updates are only checked after confirming the official
instance is installed.


## v0.6.66 completed

Fixed official update false positives after first install by comparing the latest
release asset with the installed official manifest.
