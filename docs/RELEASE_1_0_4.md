# StoneLight Launcher 1.0.4

## Hotfix

This release fixes missing/broken instance icons after updating to the new PNG
icon pack.

## Fixed

- Packaged builds could keep an old external `web_ui/assets/instance_icons`
  folder after auto-update.
- The new manifest could then point to PNG files that were not present in the
  installed folder, causing broken images in the icon picker.
- The launcher now synchronizes the bundled `web_ui/assets/instance_icons`
  directory on startup.
- Saved old `.svg` icon URLs now try the matching `.png` file as a fallback in
  instance tiles.

## Safety

Only launcher-owned UI icon assets are synchronized. User data, instances,
accounts, logs and custom instance folders are not touched.

## Included

- 1.0.3 icon pack refresh.
- 1.0.2 SSL/certifi hotfix.
- 1.0.1 clone hotfix.
