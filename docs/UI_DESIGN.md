# UI Design

StoneLight Launcher v0.5.37 starts a modernized UI pass.

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


## v0.5.37

Layout fixes:

- Main dashboard buttons in `Instances` and `Accounts` were changed from 4 narrow columns to wider 2-column rows.
- Account policy text was moved below the offline nickname row.
- Instance info row was moved lower after the second button row.
- Tab buttons in instance windows no longer use accent color as selected background. This avoids unreadable text because `CTkTabview` uses one text color for all tab buttons.


## v0.5.37

Fix pass for instance windows:

- Instance window title now uses localization:
  - `Instance: name`
  - `Збірка: name`
  - `Жинақ: name`
- Instance account selector now explicitly displays the localized `No accounts` placeholder when no accounts exist.
- Tab buttons are forced to stable neutral theme colors, so switching tabs no longer makes them unexpectedly darker.


## v0.5.37

Tab color and destructive button pass:

- `CTkTabview` and its internal `CTkSegmentedButton` are patched so tab buttons keep the current theme accent color after clicking/switching.
- Selected and unselected tab states use the same accent color; hover uses `accent_hover`.
- Destructive buttons now use theme-aware `danger`, `danger_hover`, and `danger_text` colors:
  - delete instance
  - delete account
  - stop game


## v0.5.37

Fix pass after v0.5.36 testing:

- Active tab is visible again:
  - selected tab uses `accent`
  - inactive tabs use `accent_hover`
- Tabs remain bright/readable after switching because CustomTkinter styling is reapplied.
- Destructive buttons are now directly restyled after creation:
  - delete instance
  - delete account
  - stop game
