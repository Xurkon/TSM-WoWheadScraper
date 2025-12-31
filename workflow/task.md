# TSM Scraper - Cross-Server Support

## Current Task: Implement Retail Wowhead Scraping

### Planning

- [x] Review previous conversation exports
- [x] Explore current project structure
- [x] Analyze existing scrapers (`wowhead_scraper.py`, `ascension_scraper.py`)
- [x] Check `lua_parser.py` for retail item format support
- [x] Examine GUI server selection functionality
- [x] Create implementation plan for retail Wowhead support

### Implementation

- [x] Update `wowhead_scraper.py` to support retail URLs
- [x] Enhance `lua_parser.py` to handle retail item string formats (`i:ID::BONUSES`)
- [x] Wire up server selection in GUI to use correct scraper
- [x] Add TSM format selection (Retail/Classic) separate from database dropdown
- [x] Update changelog
- [x] Test retail item scraping

### Bug Fixes

- [x] Fix `ThemedMessageBox` dialog cut-off (auto-size height based on content)

### Documentation & Build

- [x] Compile `TSM Scraper.exe` with PyInstaller
- [x] Create `README.MD` matching PA-TradeSkillMaster style
- [x] Create `docs/index.html` for GitHub Pages
- [x] Update CHANGELOG.md

### Verification

- [x] Test scraping individual retail items
- [x] Test scraping retail item categories
- [x] Verify GUI server selection functionality

### Release & Debugging

- [x] Fix Wowhead Retail scraping (H1 selector change)
- [x] Fix Ascension DB scraping (Switch to XML API)
- [x] Verify all 8 database sources
- [x] Recompile with Modern GUI (`gui_modern.py`)
- [x] Create GitHub Release v2.1.2
- [x] Handover to user for final repo management
