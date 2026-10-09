# StoneLight Launcher 1.0.5

## Hotfix

This release fixes the icon picker after switching the bundled instance icon
pack from SVG to PNG.

## Fixed

- `INSTANCE_ICON_PACK` still contained old `.svg` URLs even though the bundled
  files were replaced with `.png`.
- The instance tiles could recover through their fallback, but the icon picker
  still displayed broken images.
- The bundled icon pack URLs now point directly to PNG files.
- Legacy saved `.svg` icon URLs are normalized to matching `.png` URLs.
- The icon picker now has the same SVG→PNG fallback and letter fallback as
  instance tiles.

## Included

- 1.0.4 icon asset synchronization hotfix.
- 1.0.3 icon pack refresh.
- 1.0.2 SSL/certifi hotfix.
- 1.0.1 clone hotfix.
