# UI Design

StoneLight Launcher v0.5.34 starts a modernized UI pass.

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


## v0.5.34

Layout fixes:

- Main dashboard buttons in `Instances` and `Accounts` were changed from 4 narrow columns to wider 2-column rows.
- Account policy text was moved below the offline nickname row.
- Instance info row was moved lower after the second button row.
- Tab buttons in instance windows no longer use accent color as selected background. This avoids unreadable text because `CTkTabview` uses one text color for all tab buttons.
