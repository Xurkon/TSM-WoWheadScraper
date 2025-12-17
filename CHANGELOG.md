# TSM Wowhead Scraper - Changelog

**Created by [Xurkon](https://github.com/Xurkon)**

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

- **Refresh Button**: Click 🔄 to reload SavedVariables file after `/reload` in WoW
- **Version Display**: Window title now shows version number

### Bug Fixes

- **Fixed Group Detection**: Properly parses groups from SavedVariables files
- **Fixed Config Loading**: Config/log paths now resolve correctly for compiled exe

---

## [v3.3.0] - 2025-12-14

### New Features

- **Manual Item IDs**: Add/remove specific item IDs with single entry, paste list, or remove mode
- **4-Column UI Layout**: Options | Categories | Results | Groups for better workflow
- **Draggable Column Resize**: Drag dividers between columns to customize widths

---

## [v3.2.0] - 2025-12-12

### New Features

- **Bind Type Filter**: Filter items by BoE, BoP, BoU, BoA, Quest, Warbound, or No Binding
- **Auto-Create Default Groups**: Generate 145 TSM groups matching Wowhead categories
- **Group Management**: Right-click groups for Rename, Add Sub-Group, Delete
- **Profile Management**: Store and switch between up to 5 TSM profiles
- **Copy Log**: 📋 button copies current session log to clipboard

### Bug Fixes

- **Fixed Delete Group**: Properly removes groups with nested structures
- **Improved Group Hierarchy**: Better display of nested group structure

---

## [v2.1.3] - 2025-12-10

### New Features

- **Recipe Categories**: Added 9 recipe categories for all professions

### Improvements

- **GUI**: Category headers now auto-select all items when clicked

---

## [v2.0.0] - 2025-12-08

### Major Update - Modern GUI Overhaul

- **New UI**: Complete rewrite using CustomTkinter for a modern look
- **Category Browser**: Select specific item types to scrape (Weapons, Armor, etc.)
- **TSM Groups**: Browse your TSM group hierarchy directly in the sidebar
- **Theme Editor**: 4 built-in themes + custom color customization
- **One-Click Import**: Directly updates TradeSkillMaster.lua SavedVariables
- **Auto-Backup**: Creates backup before every import operation
