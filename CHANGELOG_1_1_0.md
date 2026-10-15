# StoneLight Launcher 1.1.0

## Release packaging

- Updated active launcher version values from 1.0.5 to 1.1.0.
- Added Windows File version and Product version metadata (`1.1.0.0`).
- Made the Windows release archive name follow `launcher_version` from `config.json`.
- Added `sign_windows_release.ps1` for SHA-256 Authenticode signing, Certum RFC 3161 timestamping, signature verification, and final ZIP recreation.

## Application

- No functional launcher changes compared with 1.0.5.
