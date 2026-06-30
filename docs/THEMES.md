# Themes

StoneLight Launcher v0.5.54 includes the first visual theme system.

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


## v0.5.54 additional themes

### Laconic

```text
window:        #0f141b
panel:         #171d26
panel_strong:  #202834
input:         #111821
text:          #eef3f8
muted:         #9aa8b8
line:          #2c3644
accent:        #f2b45a
accent_hover:  #e39a35
```

### Neon

```text
window:        #070912
panel:         #101426
panel_strong:  #171c33
input:         #0b1020
text:          #f2f7ff
muted:         #8da0c2
line:          #273152
accent:        #00e5ff
accent_hover:  #8a5cff
danger:        #ff3b8d
```

### Retro Future

```text
window:        #1a1026
panel:         #261936
panel_strong:  #332046
input:         #21152f
text:          #fff1dc
muted:         #c9a9b8
line:          #4a315f
accent:        #ff9f45
accent_hover:  #ff6f3c
danger:        #ff5c7a
```


## v0.5.54 palette revision

### Laconic revised

Laconic is now a pastel minimal theme instead of another dark graphite theme.

```text
window:        #f4f1ec
panel:         #fbf8f2
panel_strong:  #ffffff
input:         #f0ece4
text:          #2f3440
muted:         #7c8792
line:          #d7d0c5
accent:        #8fb8a8
accent_hover:  #7aa895
```

### Retro Future revised

Retro Future keeps the purple synthwave background, but the main button color is now magenta with cyan hover to make it visually different from Dark/Light/StoneLight orange themes.

```text
window:        #1a1026
panel:         #261936
panel_strong:  #332046
input:         #21152f
text:          #fff1dc
muted:         #c9a9b8
line:          #4a315f
accent:        #ff4fd8
accent_hover:  #00d4ff
danger:        #ff6b8a
```


## v0.5.54 destructive button colors

Each theme now has its own destructive/warning color pair:

```text
Light:        #d65f45 / #b94b34
Dark:         #ff6b4a / #e95032
Laconic:      #c96f5d / #ad5949
Neon:         #ff2d95 / #ff174f
Retro Future: #ff3d6e / #ff7a00
```

Used for actions such as deleting instances/accounts and force-stopping the game.
