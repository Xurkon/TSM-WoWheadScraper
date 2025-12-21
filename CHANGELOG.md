# CHANGELOG - TSM-WoWheadScraper

## [3.4.19] - 2024-12-21
### Fixed
- **Import Button for Manual IDs**: Fixed issue where the "Import to TSM" button remained disabled after pasting item IDs. The button now correctly enables when manual IDs are added or removed.

---

## [3.4.18] - 2024-12-20
### Added
- **Linux/Wine/Bottles Compatibility**: Added detection for Wine/Proton/Bottles environments. Config and logs are now stored locally in an `appdata/` folder when running under Wine to avoid path mapping issues.
- **Crash Logging**: Added automatic `crash_log.txt` generation for unhandled exceptions. Includes full stack trace, environment info, and Wine detection status to help diagnose issues on Linux.

### Fixed
- Fixed potential crashes when `APPDATA` environment variable is not properly set under Wine.

---

## [3.4.17] - 2024-12-18
### Changed
- Removed "Bind on Pickup (BoP)" filter option to simplify scraping and avoid missing tradeable items due to complex Wowhead filter logic.

## [3.4.16] - 2024-12-18
### Fixed
- Fixed an issue where the WoWhead scraper would return 0 items for small categories or filtered results (e.g., BoE Crossbows on Classic).
- Relaxed item detection thresholds in `wowhead_scraper.py` to correctly identify small item arrays.
- Enhanced JSON parsing for Wowhead JS objects to handle unquoted keys in various formats.
- Improved regex fallback matching (Strategy 2) to handle `WH.Gatherer.addData` and non-standard object structures.
- Updated application version to 3.4.16.

## [3.4.15] - 2024-12-18
### Fixed
- Fixed critical `NameError` in `lua_writer.py` when verifying group existence.
- Corrected version display in GUI.
- Synced `lua_writer.py` changes with TSMItemScraper.
- Updated application version to 3.4.15.

## [3.4.14] - 2024-12-18
### Added
- Improved visibility for TSM 2.8 groups on Project Ascension (TSM Scraper).

### Fixed
- Improved handling of TSM 2.8 group tree status.
- Finalized TSM 2.8 visibility fixes for Ascension.

## [3.4.13] - 2024-12-18
### Fixed
- Improved `groupTreeStatus` handling for Ascension TSM (TSM 2.8).
- Added `_ensure_group_tree_status_ascension` to ensure groups are visible in the sidebar.
- Fixed regex bug in `ensure_group_exists` that failed on paths with backticks.
- Fixed malformed Lua formatting in `_ensure_group_exists_ascension`.
- Updated GUI to accurately check group existence against loaded TSM data instead of UI registry.
