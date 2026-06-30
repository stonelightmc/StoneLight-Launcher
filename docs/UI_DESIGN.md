# UI Design

StoneLight Launcher v0.5.53 starts a modernized UI pass.

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


## v0.5.53

Layout fixes:

- Main dashboard buttons in `Instances` and `Accounts` were changed from 4 narrow columns to wider 2-column rows.
- Account policy text was moved below the offline nickname row.
- Instance info row was moved lower after the second button row.
- Tab buttons in instance windows no longer use accent color as selected background. This avoids unreadable text because `CTkTabview` uses one text color for all tab buttons.


## v0.5.53

Fix pass for instance windows:

- Instance window title now uses localization:
  - `Instance: name`
  - `Збірка: name`
  - `Жинақ: name`
- Instance account selector now explicitly displays the localized `No accounts` placeholder when no accounts exist.
- Tab buttons are forced to stable neutral theme colors, so switching tabs no longer makes them unexpectedly darker.


## v0.5.53

Tab color and destructive button pass:

- `CTkTabview` and its internal `CTkSegmentedButton` are patched so tab buttons keep the current theme accent color after clicking/switching.
- Selected and unselected tab states use the same accent color; hover uses `accent_hover`.
- Destructive buttons now use theme-aware `danger`, `danger_hover`, and `danger_text` colors:
  - delete instance
  - delete account
  - stop game


## v0.5.53

Fix pass after v0.5.36 testing:

- Active tab is visible again:
  - selected tab uses `accent`
  - inactive tabs use `accent_hover`
- Tabs remain bright/readable after switching because CustomTkinter styling is reapplied.
- Destructive buttons are now directly restyled after creation:
  - delete instance
  - delete account
  - stop game


## v0.5.53

Custom instance tab bar:

- The internal `CTkTabview` segmented buttons are hidden.
- A separate custom tab bar made of normal `CTkButton` widgets is used above the page container.
- Active tab uses `accent`.
- Inactive tabs use `secondary`.
- This makes the active tab clearly visible and avoids CustomTkinter segmented-button color glitches.


## v0.5.53

Files tab folder navigation redesign:

- `mods`, `resourcepacks`, `shaderpacks`, `config`, `screenshots` buttons now use the same active/inactive visual logic as custom tabs.
- Active folder button uses `accent`.
- Inactive folder buttons use `secondary`.
- This makes the selected folder clearly visible in the instance window.


## v0.5.53

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


## v0.5.53

Main window status block visibility fix:

- Main window default height increased to `1120x940`.
- Minimum height increased to prevent the bottom status/log card from being clipped.
- The update-check button was moved into the main action row instead of taking a separate second row.
- Status/log card is now compact and fixed-height:
  - log box height reduced
  - status card no longer stretches below the window edge
- Main dashboard vertical padding was slightly reduced.


## v0.5.53

Main action row and danger-button fixes:

- The `Check updates` button was shortened to `Updates` for all localizations.
- The main local install/reinstall button now uses the shorter `Install` label.
- `Install` no longer duplicates the remote GitHub update-check action for the official StoneLight instance.
- `configure(state=...)` no longer injects default accent colors into buttons.
- Danger buttons are restyled after busy-state transitions.
