# Themes

StoneLight Launcher v0.5.30 includes the first visual theme system.

## Themes

```text
Dark
Light
```

The selected theme is stored in:

```text
user_settings.json
```

## Palette

The palette is inspired by the StoneLight website CSS variables.

Light theme:

```text
background: #fff7ea / #f4e6d2
panel:      #fffaf1 / #ffffff
text:       #2d2118
muted:      #6b5747
accent:     #ffb347 / #f47c38
```

Dark theme:

```text
background: #0b1118 / #111a25
panel:      #151c27 / #1c2533
text:       #edf3ff
muted:      #9fb0c8
accent:     #ffb347 / #ff8c42
```

## Implementation

The launcher uses `customtkinter` appearance mode plus tuple colors for light/dark theme-aware widgets.
