# TSM Item Scraper - Changelog

**Created by [Xurkon](https://github.com/Xurkon)**

## [v3.4.1] - 2025-12-16

### Bug Fixes

- **Fixed Pane Position Memory**: Column divider positions now properly saved and restored across sessions

---

## [v3.4.0] - 2025-12-16

### New Features

- **Window Position Memory**: App remembers window position and size across sessions
- **Collapsible Groups**: Click any group with items to expand/collapse and see items inside
  - Expand All / Collapse All buttons in groups panel header
  - Items displayed with checkboxes for selection
- **Ctrl+Click Multi-Selection**: Ctrl+click groups to select multiple for bulk operations
- **Move Groups**: Right-click → Move Group to relocate groups to new parents
- **Remove Selected Items**: In remove mode with no IDs entered, removes checked items from groups
- **Bulk Operations**: Delete or move multiple selected groups at once

---

## [v3.3.5] - 2025-12-16

### New Features

- **Refresh Button**: Added 🔄 button to reload TSM SavedVariables file without restarting
  - Click after `/reload` in WoW to see newly created groups
  - Located next to the profile dropdown

---

## [v3.3.4] - 2025-12-16

### Bug Fixes

- **Fixed Ascension Group Detection**: Groups without backticks (like 'testing') now properly detected
  - Parser now looks inside `profiles.Default.groups` section for Ascension TSM format
  - Filters out operation names (Mailing, Auctioning, etc.)

---

## [v3.3.3] - 2025-12-16

### Bug Fixes

- **Fixed Config Loading for Compiled Exe**: Config and log paths now correctly resolve when running from PyInstaller-built executable
  - Uses `sys.executable` parent directory when frozen instead of `__file__`

---

## [v3.3.2] - 2025-12-16

### Bug Fixes

- **Fixed SavedVariables Detection**: Updated default path to Ascension client location
- **Fixed Default Groups Not Writing**: Added proper Ascension TSM format support
  - Detects `AscensionTSMDB` vs `TradeSkillMasterDB` format automatically
  - Groups now insert into correct `profiles.Default.groups` section for Ascension
  - Maintains backwards compatibility with Retail TSM format

---

## [v3.3.1] - 2025-12-16

### Bug Fixes

- **Fixed Manual Item ID Import**: Manual IDs now properly import to TSM and remove from TSM
  - Manual add IDs require a selected group from the right sidebar
  - Manual remove IDs completely delete items from SavedVariables
  - Status counters clear after successful import
  - Improved error messaging when no group is selected

### Changes

- **Removed Legacy GUI**: Deleted `gui.py` in favor of modern CustomTkinter interface

---

## [v3.3.0] - 2025-12-14

### New Features

- **Manual Item IDs**: Add or remove specific item IDs from import
  - Single ID entry with Add button
  - Paste List for bulk ID input
  - Remove Mode toggle for excluding items
  - Status counters showing added/removed counts
- **4-Column UI Layout**: Reorganized interface for better usability
  - Column 1: Options (Database, Format, Bind Filter, Manual IDs, TSM File)
  - Column 2: Scrape Categories (moved from left sidebar)
  - Column 3: Scrape Results & Log
  - Column 4: TSM Groups
- **Draggable Column Resize**: Drag dividers between columns to resize
  - Smooth ghost-line dragging
  - Minimum sizes to prevent columns from collapsing

---

## [v3.2.0] - 2025-12-13

### New Features (Merged from TSM-WoWheadScraper)

- **Bind Type Filter**: Full dropdown filter for item binding types (BoE, BoP, BoU, BoA, Quest, Warbound, No Binding)
- **Auto-Create Default Groups**: "✨ Create Default Groups" button generates 145 TSM groups from category hierarchy
- **Group Management**: Right-click any group for context menu (Rename, Add Sub-Group, Delete)
- **Profile Management**: Store and switch between up to 5 TSM SavedVariables profiles
- **Copy Log Button**: 📋 button copies current session log to clipboard
- **Improved Group Hierarchy Display**: Better visual distinction between levels

### Bug Fixes

- **Fixed Delete Group**: Brace-counting algorithm properly handles nested structures
- **Fixed Delete Items**: Items correctly removed when selecting "No" to "Keep Items?"
- **Fixed Create Default Groups**: Groups properly save for both WotLK and retail TSM formats
- **Fixed Rename Group**: Verified working with special characters in group names

### Note

Unlike TSM-WoWheadScraper, this version **retains full support for private servers**:

- Project Ascension (db.ascension.gg)
- Turtle WoW (database.turtle-wow.org)

---

## [v2.1.3] - 2025-12-11

### Added

- **Recipe Categories**: Added 9 recipe categories (Alchemy, Blacksmithing, Cooking, Enchanting, Engineering, First Aid, Jewelcrafting, Leatherworking, Tailoring).
- **Additional Consumables**: Added Bandage and Scroll categories.
- **GUI Category Checkboxes**: Category group headers (⚔ Weapons, ⚗ Consumables, etc.) are now checkboxes that auto-select all items in the category when clicked.

### Fixed

- **Wowhead Subclass Filtering**: Fixed critical bug where consumable/trade goods categories were returning all items instead of filtering by subclass.
  - Elixirs now correctly return 93 items instead of 911 (all consumables).
  - Added `CATEGORY_URL_MAP` with pretty URLs for all categories (weapons, consumables, trade goods, gems, recipes).
  - Added `scrape_by_name()` method for unified category scraping using server-side filtered URLs.
- **Small Category Scraping**: Lowered array detection threshold from 5000 to 500 chars to catch small categories like First Aid recipes (11 items).
- **GUI Wowhead Integration**: Fixed `on_server_changed` to properly assign `WowheadScraper` to `self.scraper`.
- **Category Collapse/Expand**: Fixed expand behavior to properly place items after header frame.

## [v2.1.2] - 2025-12-11

- **Fixed:** Compiled executable using `gui_modern.py` correctly instead of the legacy `gui.py`. The interface is now the correct Modern/CustomTkinter version.

## [v2.1.1] - 2025-12-11

- **Fixed:** Resolved Wowhead scraping for Retail, Cataclysm, and MoP by updating CSS selectors.
- **Fixed:** Resolved Ascension DB scraping by switching to the XML API endpoint (HTML was blocking requests).
- **Fixed:** Verified cross-server compatibility for all 8 supported game versions.

## [v2.1.0] - 2025-12-11

### Cross-Server Scraping Support

- **Database Server Selection**: Fully functional for all options:
  - Project Ascension (`db.ascension.gg`)
  - Turtle WoW (`database.turtle-wow.org`) - *TSM backport coming soon*
  - Wowhead WotLK (`wowhead.com/wotlk`)
  - Wowhead TBC (`wowhead.com/tbc`)
  - Wowhead Classic Era (`classic.wowhead.com`)
  - Wowhead Cata (`wowhead.com/cata`)
  - Wowhead MoP Classic (`wowhead.com/mop-classic`)
  - Wowhead Retail (`www.wowhead.com`)

- **TSM Format Selection**: New dropdown to control output format:
  - **WotLK 3.3.5a**: Uses `item:ID:0:0:0:0:0:0` format
  - **Retail (Official TSM)**: Uses `i:ID` format for retail TSM

### Documentation & Build

- **Compiled Executable**: Added standalone `TSM Scraper.exe` build using PyInstaller.
- **GitHub Documentation**: Created modern `README.MD` and `docs/index.html` (GitHub Pages) matching PA-TradeSkillMaster style.
- **API Fixes**: Standardized `get_item` method in `AscensionDBScraper` for consistent cross-server testing.

- **Cross-Version Import Workflow**: Scrape from any Wowhead version and import into any TSM format (e.g., scrape Classic Era items from Wowhead and import into Ascension)

### Bug Fixes

- **Fixed dialog cut-off issue**: `ThemedMessageBox` now auto-sizes height (220-500px) based on message length, ensuring Yes/No buttons are always visible

### Technical Changes

- Added `WowheadScraper` class with `game_version` parameter (`retail`, `wotlk`, `classic`)
- Updated `lua_parser.py` to handle both Classic (`item:ID:...`) and Retail (`i:ID`) formats
- Added `is_retail_format()` and `get_format_type()` helper methods
- Added `on_format_changed()` handler for TSM format selection
- Removed "Coming Soon" message from server selection

---

## [v2.0.0] - 2025-12-10

### Selective Category Import

- Scrape results now display checkboxes for each category
- Categories with NEW items are checked by default
- Uncheck categories to exclude them from import
- Validation: warns if no categories selected or no new items in selection

#### Smart Group Auto-Selection

- After scraping, automatically detects matching TSM group
- Highlights selected group with cyan background
- Attempts to scroll to selected group in list
- Falls back to showing "Target group (will be created)" if group doesn't exist

#### Themed Message Dialogs

- Created `ThemedMessageBox` class for styled popups
- Replaced all `messagebox` calls with themed versions
- Dialogs now match the application theme colors

#### Font Size Controls

- Added font size properties to Theme dataclass:
  - `font_size_header` (default: 14px)
  - `font_size_label` (default: 12px)
  - `font_size_body` (default: 11px)
  - `font_size_small` (default: 10px)
  - `font_size_tiny` (default: 9px)
- Added font size sliders to Theme Editor (Settings → scroll down)

### Improvements

#### Import Workflow

- Import confirmation now shows selected target group name
- Success message updated: "If WoW is running, restart it to see changes"
- Added safety check with friendly message when trying to import without scraping
- **Multi-category import**: When importing multiple categories with different target groups, shows list of each category and its destination group

#### Group Selection

- TSM groups in right sidebar are now clickable buttons
- Selected group is visually highlighted
- Shows "Selected:" label with current target group

### Bug Fixes

- Fixed header spanning all 3 columns in new layout
- Fixed references to removed `results_text` widget
- Fixed auto-select to run even with 0 new items found

### Technical Changes

- Added `group_buttons_registry` for tracking group button widgets
- Added `results_checkboxes` dict for tracking result category selections
- Renamed `create_sidebar` to `create_left_sidebar`
- Added `create_center_panel` and `create_right_sidebar` methods
- Added helper methods:
  - `update_results_with_checkboxes()`
  - `get_selected_import_categories()`
  - `highlight_group_button()`
  - `scroll_to_group_button()`
  - `auto_select_scrape_group()`
  - `select_import_group()`
  - `on_server_changed()`
