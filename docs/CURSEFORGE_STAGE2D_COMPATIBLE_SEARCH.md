# CurseForge Stage 2d compatible search

This local source snapshot improves the CurseForge tab after Stage 2c.

## Changes

- CurseForge search now verifies that each displayed project has a compatible file for the selected instance.
- Projects without a compatible file for the selected Minecraft version / loader are hidden from search results.
- Empty search no longer sends an invalid request to the backend; the UI asks the user to enter a project name.
- The extra `Open page` button was removed from CurseForge cards. The project title remains clickable and opens the CurseForge project page.
- Cards can show the selected compatible file name in the metadata line.

## Current limitation

Browsing all CurseForge projects without a query is still not implemented. This should be added later together with proper filters/categories.
