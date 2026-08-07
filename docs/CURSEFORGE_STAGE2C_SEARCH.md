# CurseForge Stage 2c search ranking

This local snapshot improves CurseForge search behavior.

## Why

CurseForge search can return projects that only mention the query in the description, especially when strict `gameVersion` and `loader` filters are applied. For example, searching `sodium` could show Sodium add-ons or unrelated projects before the actual Sodium project.

## What changed

The launcher now performs two backend searches:

1. broad text search by query and project type;
2. strict compatibility search with Minecraft version and loader.

Results are merged and locally ranked so exact title/slug matches are shown first while compatible results still receive a score bonus.

The install step still checks for a compatible file before downloading. If a top search result exists but has no compatible file for the selected instance, installation will show a clear error instead of downloading the wrong file.

## Backend URLs

- https://stonelight-api.serveminecraft.net
- https://stonelight-api.duckdns.org
