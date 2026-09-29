# StoneLight Launcher 1.0.0

## Release status

This is the first 1.0.0 release source package for StoneLight Launcher.

## Highlights

- Web UI launcher flow with instance management.
- Official StoneLight instance support.
- Custom user instances.
- Microsoft and offline account support.
- Per-instance console.
- mclo.gs upload for `latest.log`.
- Launcher log cleanup and UTF-8 friendly logging.
- Modrinth integration.
- CurseForge integration through the StoneLight CurseForge backend.
- CurseForge manual-download handling for projects that block third-party distribution.
- Modpack update support.
- User content update system for custom instances:
  - inventory of mods, resource packs and shader packs;
  - known source tracking;
  - Modrinth update preview/apply;
  - CurseForge update preview/apply;
  - source discovery for unknown files;
  - selectable/excluded items;
  - Minecraft version migration preview;
  - atomic migration when there are no blockers.

## Backend requirement

For full CurseForge source discovery, the StoneLight CurseForge backend should be
updated to at least:

```text
0.5.5
```

Required endpoint:

```text
POST /api/v1/cf/fingerprints
```

Older backend versions can still serve search and download-url operations, but
CurseForge fingerprint source discovery will not work.

## Safety notes

- Files with unknown source are not replaced automatically.
- CurseForge files without available `downloadUrl` are marked as manual.
- Excluded files are left physically in the instance folder.
- Migration is blocked by incompatible, unknown, manual-required, modified or
  error items unless the user excludes them from the operation.
- Excluded files may still be incompatible with the target Minecraft version and
  should be reviewed manually.

## Build notes

This package is intended as a release source snapshot. Build executable packages
from this source if needed.
