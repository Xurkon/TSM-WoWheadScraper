# TSM Wowhead Scraper Walkthrough - v3.4.18

## Latest Changes: Linux/Wine Compatibility

### What Was Implemented

#### 1. Wine/Bottles/Proton Detection

Added `_detect_wine_or_linux()` function in [gui_modern.py](file:///c:/Ascension%20Launcher/resources/client/TSM-WoWheadScraper/gui_modern.py):

- Checks Wine environment variables (`WINEPREFIX`, `WINELOADER`, etc.)
- Detects `/proc/version` (Linux-only file)
- Checks for Wine's Z: drive mappings (`Z:/.wine`, `Z:/home`)

#### 2. Smart Path Fallback

Added `_get_app_data_path()` function:

- **On Windows**: Uses `%APPDATA%\TSM Scraper\`
- **On Wine/Linux**: Uses local `./appdata/` folder in scraper directory
- Tests write access before committing to path
- Graceful fallback if directory creation fails

#### 3. Crash Logging

Added `_write_crash_log()` function:

- Creates `crash_log.txt` in scraper directory on any unhandled exception
- Includes full stack trace, Python version, environment info
- Shows Wine detection status for debugging

---

## Wowhead Scraping Features

### Multi-Version Support

- **Retail**: `https://www.wowhead.com`
- **WotLK**: `https://www.wowhead.com/wotlk`
- **TBC**: `https://www.wowhead.com/tbc`
- **Classic**: `https://www.wowhead.com/classic`
- **Cataclysm**: `https://www.wowhead.com/cata`
- **MoP**: `https://www.wowhead.com/mop`

### Dual-Format Output

- **Classic format**: `item:12345:0:0:0:0:0:0`
- **Retail format**: `i:12345`

---

## File Locations

| Platform | Config | Logs | Crash Log |
|----------|--------|------|-----------|
| **Windows** | `%APPDATA%\TSM Scraper\config\` | `%APPDATA%\TSM Scraper\logs\` | N/A |
| **Linux/Wine** | `./appdata/config/` | `./appdata/logs/` | `./crash_log.txt` |

---

## Files Modified in v3.4.18

- [gui_modern.py](file:///c:/Ascension%20Launcher/resources/client/TSM-WoWheadScraper/gui_modern.py) - Wine detection, crash logging
- [CHANGELOG.md](file:///c:/Ascension%20Launcher/resources/client/TSM-WoWheadScraper/CHANGELOG.md) - Version history
- [README.MD](file:///c:/Ascension%20Launcher/resources/client/TSM-WoWheadScraper/README.MD) - Linux compatibility section
