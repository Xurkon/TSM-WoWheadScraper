# Changelog

## [3.4.15] - 2025-12-18
### Fixed
- Fixed critical `NameError` in `lua_writer.py` when verifying group existence.
- Corrected version display in GUI.

## [3.4.14] - 2025-12-18
### Fixed
- Fixed critical bug where `cleanup_ui_state` was wiping newly added `groupTreeStatus` entries.
- Added missing profile keys (`groupTreeCollapsedStatus`, `isBankui`, `moveImportedItems`) for TSM 2.8 structural integrity.
- Updated default group operation to `"AlwaysUndercut"` for better out-of-the-box functionality.
- Improved profile replenishment logic for fresh TSM profiles.

## [3.4.13] - 2025-12-18
### Fixed
- Improved `groupTreeStatus` handling for Ascension TSM (TSM 2.8).
- Added `_ensure_group_tree_status_ascension` to ensure groups are visible in the sidebar.
- Fixed regex bug in `ensure_group_exists` that failed on paths with backticks.
- Fixed malformed Lua formatting in `_ensure_group_exists_ascension`.
- Updated GUI to accurately check group existence against loaded TSM data instead of UI registry.
