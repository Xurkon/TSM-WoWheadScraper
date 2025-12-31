# Retail Wowhead Scraping Support

Implement cross-server compatibility for the TSM Item Scraper by adding support for scraping items from `wowhead.com/wow/retail` in addition to the existing `db.ascension.gg` support.

## Background

The TSM Scraper currently supports:

- **Project Ascension** (`db.ascension.gg`) - fully functional
- **Wowhead Classic/WotLK** (`wowhead.com/wotlk`) - basic framework exists in `wowhead_scraper.py`

The user wants to add **Retail Wowhead** support (`wowhead.com/wow`) to enable backwards/forwards compatibility for TSM data across different WoW versions.

### Key Differences: Retail vs Classic

| Aspect | Classic/WotLK | Retail |
|--------|---------------|--------|
| URL Base | `/wotlk/item=ID` | `/item=ID` |
| Item Strings | `item:ID:0:0:0:0:0:0` | `i:ID` or `i:ID::BONUS1:BONUS2...` |
| TSM Groups | Backtick (`) delimiter | Backtick (`) delimiter |

---

## Proposed Changes

### 1. Scraper Module

#### [MODIFY] [wowhead_scraper.py](file:///c:/Ascension%20Launcher/resources/client/TSMItemScraper/tsm_scraper/wowhead_scraper.py)

- Add a `game_version` parameter to `WowheadScraper.__init__()` with options: `'wotlk'`, `'classic'`, `'retail'`
- Update `BASE_URL` to be dynamic based on game version:
  - wotlk: `https://www.wowhead.com/wotlk`
  - classic: `https://www.wowhead.com/classic`
  - retail: `https://www.wowhead.com` (no suffix)
- Update URL patterns in `scrape_category()` for retail structure
- Add retail-specific item class/subclass mappings (some differ from Classic)

---

### 2. Lua Parser

#### [MODIFY] [lua_parser.py](file:///c:/Ascension%20Launcher/resources/client/TSMItemScraper/tsm_scraper/lua_parser.py)

- Update `parse_items()` regex to handle both formats:
  - Classic: `[\"item:12345:0:0:0:0:0:0\"]`
  - Retail: `[\"i:12345\"]` or `[\"i:12345::4786:6652:1492\"]`
- Update `get_item_id()` to extract ID from both formats
- Add `is_retail_format()` helper method

---

### 3. GUI Integration

#### [MODIFY] [gui_modern.py](file:///c:/Ascension%20Launcher/resources/client/TSMItemScraper/gui_modern.py)

- Update `on_server_changed()` to:
  - Store selected server in instance variable
  - Remove "Coming Soon" message for Wowhead options
  - Initialize the appropriate scraper based on selection
- Update `start_scrape()` to use the correct scraper based on server selection
- Add logic to detect and suggest appropriate server based on loaded TSM file format

---

### 4. Categories

#### [MODIFY] [categories.json](file:///c:/Ascension%20Launcher/resources/client/TSMItemScraper/config/categories.json)

- Ensure category definitions work for retail item types
- Add any retail-specific categories if needed (e.g., Dragonflight gear)

---

## Verification Plan

### Automated Testing

Since no existing test suite was found, I'll create a simple test script:

```bash
cd "c:\Ascension Launcher\resources\client\TSMItemScraper"

# Test 1: Retail Wowhead single item lookup
python -c "from tsm_scraper.wowhead_scraper import WowheadScraper; s = WowheadScraper(game_version='retail'); item = s.get_item(220140); print(f'Item: {item.name if item else \"Not found\"}' if item else 'Failed')"

# Test 2: Retail Wowhead category scrape
python -c "from tsm_scraper.wowhead_scraper import WowheadScraper; s = WowheadScraper(game_version='retail'); items = s.scrape_weapons('dagger', limit=5); print(f'Found {len(items)} daggers')"

# Test 3: Lua parser with retail format
python -c "from tsm_scraper.lua_parser import TSMLuaParser; p = TSMLuaParser(r'c:\Program Files (x86)\World of Warcraft\_retail_\WTF\Account\50109546#1\SavedVariables\TradeSkillMaster.lua'); p.load(); p.parse_items(); print(f'Parsed {len(p.items)} items, {len(p.groups)} groups')"
```

### Manual Verification

1. **Launch GUI**: Run `python gui_modern.py`
2. **Select "Wowhead (Retail)"** from the Database Server dropdown
3. **Verify no "Coming Soon" message** appears
4. **Select a category** (e.g., Daggers) and click Scrape
5. **Verify items are scraped** from retail Wowhead
6. **Load retail TSM file** and verify it parses correctly
7. **Change server selection** and verify categories update appropriately

---

> [!IMPORTANT]
> The retail Wowhead site structure may differ from Classic. I'll need to test the actual HTML/JS parsing during implementation and adjust selectors as needed.
