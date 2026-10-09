# StoneLight Launcher 1.0.3

## Icon Pack Refresh

This release includes the latest StoneLight instance icon pack refresh.

## Changed

- Replaced the bundled instance icon pack with the newly generated 256×256 PNG pack.
- Icon files are normalized:
  - transparent canvas;
  - trimmed source content;
  - centered content;
  - 232×232 safe content area;
  - 256×256 output size.
- `web_ui/assets/instance_icons/manifest.json` now points to PNG icons.

## Included from previous hotfixes

- 1.0.2 SSL/certifi hotfix for packaged `.exe` builds.
- 1.0.1 custom instance clone hotfix.

## Notes

- This is a visual/content update plus the previous SSL fix.
- Rebuild the `.exe` from this source before testing the packaged launcher.
