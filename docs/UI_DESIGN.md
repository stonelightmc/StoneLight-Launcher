# UI Design

StoneLight Launcher v0.6.66 starts a modernized UI pass.

## Changes

- Main window now uses a two-column dashboard:
  - Instances
  - Accounts
- Status/log block was moved up and compacted so it stays visible under the main buttons.
- Rounded cards use larger radii.
- Buttons, inputs, combos, text boxes and tabs have more modern rounded styling.
- UI fonts prefer `Segoe UI Variable` with fallback to `Segoe UI`.
- A small theme-colored accent bar was added to the header.
- Existing color themes are still respected.

## Notes

CustomTkinter does not provide native real gradients or advanced animations for all widgets. These can be added later through canvas-based custom widgets without changing launcher functionality.


## v0.6.66

Layout fixes:

- Main dashboard buttons in `Instances` and `Accounts` were changed from 4 narrow columns to wider 2-column rows.
- Account policy text was moved below the offline nickname row.
- Instance info row was moved lower after the second button row.
- Tab buttons in instance windows no longer use accent color as selected background. This avoids unreadable text because `CTkTabview` uses one text color for all tab buttons.


## v0.6.66

Fix pass for instance windows:

- Instance window title now uses localization:
  - `Instance: name`
  - `Збірка: name`
  - `Жинақ: name`
- Instance account selector now explicitly displays the localized `No accounts` placeholder when no accounts exist.
- Tab buttons are forced to stable neutral theme colors, so switching tabs no longer makes them unexpectedly darker.


## v0.6.66

Tab color and destructive button pass:

- `CTkTabview` and its internal `CTkSegmentedButton` are patched so tab buttons keep the current theme accent color after clicking/switching.
- Selected and unselected tab states use the same accent color; hover uses `accent_hover`.
- Destructive buttons now use theme-aware `danger`, `danger_hover`, and `danger_text` colors:
  - delete instance
  - delete account
  - stop game


## v0.6.66

Fix pass after v0.5.36 testing:

- Active tab is visible again:
  - selected tab uses `accent`
  - inactive tabs use `accent_hover`
- Tabs remain bright/readable after switching because CustomTkinter styling is reapplied.
- Destructive buttons are now directly restyled after creation:
  - delete instance
  - delete account
  - stop game


## v0.6.66

Custom instance tab bar:

- The internal `CTkTabview` segmented buttons are hidden.
- A separate custom tab bar made of normal `CTkButton` widgets is used above the page container.
- Active tab uses `accent`.
- Inactive tabs use `secondary`.
- This makes the active tab clearly visible and avoids CustomTkinter segmented-button color glitches.


## v0.6.66

Files tab folder navigation redesign:

- `mods`, `resourcepacks`, `shaderpacks`, `config`, `screenshots` buttons now use the same active/inactive visual logic as custom tabs.
- Active folder button uses `accent`.
- Inactive folder buttons use `secondary`.
- This makes the selected folder clearly visible in the instance window.


## v0.6.66

Icon buttons pass:

- Added lightweight Unicode icons to major action buttons.
- Added icons to custom instance tabs.
- Added folder-specific icons to Files tab navigation:
  - mods
  - resourcepacks
  - shaderpacks
  - config
  - screenshots
- Icons are embedded in button text to avoid external PNG/SVG assets and packaging issues.


## v0.6.66

Main window status block visibility fix:

- Main window default height increased to `1120x940`.
- Minimum height increased to prevent the bottom status/log card from being clipped.
- The update-check button was moved into the main action row instead of taking a separate second row.
- Status/log card is now compact and fixed-height:
  - log box height reduced
  - status card no longer stretches below the window edge
- Main dashboard vertical padding was slightly reduced.


## v0.6.66

Main action row and danger-button fixes:

- The `Check updates` button was shortened to `Updates` for all localizations.
- The main local install/reinstall button now uses the shorter `Install` label.
- `Install` no longer duplicates the remote GitHub update-check action for the official StoneLight instance.
- `configure(state=...)` no longer injects default accent colors into buttons.
- Danger buttons are restyled after busy-state transitions.

## v0.6.66 StoneLight Dashboard UI

Merged the v0.5.65 dashboard redesign into the current technical branch based on v0.5.68.

```text
- branded header with StoneLight cube logo
- splash screen at startup
- dashboard-style cards with borders and stronger hierarchy
- primary Play button
- live status chips for Ready / Minecraft / Loader / Java
- visible decorative StoneLight watermark in the status area
- fixed duplicated GitHub button label
- keeps v0.5.68 loader metadata fixes
```

## v0.6.66 Instance Dashboard UI

Visual polish pass:

```text
- removed the watermark from the main status card
- made the main Play button taller and gave it more breathing room
- restyled the instance window header with the StoneLight logo, border and accent line
- restyled the instance TabView as a dashboard panel
- restyled launch info cards in the instance window
- made the instance-window Play button primary and larger
- grouped instance launch actions into a dashboard action card
```

## v0.6.66 Button polish

```text
- fixed primary Play button being compacted back to normal height
- switched button font helper to Segoe UI Variable Display with safe fallbacks
- added subtle height-only hover effect for CTkButton widgets
- increased vertical spacing around Build and Account card button rows
- kept width unchanged on hover to avoid grid jitter
```

## v0.6.66 Button hover rollback

```text
- removed height-changing hover animation
- kept Segoe UI Variable Display button font
- kept larger primary Play button
- kept increased spacing between button rows
- hover now relies on normal CustomTkinter hover colors and optional hand cursor
```

Reason: changing widget height on hover forces Tk grid to recalculate row heights, which can shift button rows, card borders and lower UI blocks.

## v0.6.66 Stable button grid

```text
- dashboard button columns use uniform grid columns, so width stays stable when language changes
- Build card left/right button columns are equal
- Account card columns are aligned the same way
- button text is centered and the grid controls width
- instance-window header accent line starts after the logo and no longer overlaps it
- instance window minimum width increased to reduce field overflow risk
```

## v0.6.66 UI symmetry and soft refresh

```text
- Kazakh Play labels are detected as primary Play buttons, so their height stays correct
- Account delete button moved under Refresh License and uses the same width
- Instance launch action row now uses three equal-width buttons
- Forge helper row also uses three equal-width buttons
- Language/theme rebuild uses a tiny alpha fade to feel less abrupt
```

## v0.6.66 Smoother soft refresh

```text
- language/theme switching now fades out to about 72% alpha before rebuilding
- widget tree rebuild happens while the window is dimmed
- a short redraw pause is added before fade-in
- fade-in is slower and smoother than v0.5.74
- refresh is guarded so multiple theme/language changes cannot overlap
```

This is still limited by CustomTkinter/Tk: the UI is rebuilt, not recolored in-place.
