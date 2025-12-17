<div align="center">

# TSM Wowhead Scraper

![Version](https://img.shields.io/badge/version-v3.4.1-blue.svg)
![License](https://img.shields.io/github/license/Xurkon/TSM-WoWheadScraper?style=for-the-badge&label=LICENSE&color=2980b9)
![Downloads](https://img.shields.io/github/downloads/Xurkon/TSM-WoWheadScraper/latest/total?style=for-the-badge&label=DOWNLOADS&color=e67e22)
![Python](https://img.shields.io/badge/PYTHON-3.11+-blue?style=for-the-badge&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/PLATFORM-WINDOWS-blue?style=for-the-badge&logo=windows&logoColor=white)

<br/>

**Item Scraping Tool for TradeSkillMaster using Wowhead**

[⬇ **Download Latest**](https://github.com/Xurkon/TSM-WoWheadScraper/releases/latest) &nbsp;&nbsp;•&nbsp;&nbsp; [📂 **View Source**](https://github.com/Xurkon/TSM-WoWheadScraper) &nbsp;&nbsp;•&nbsp;&nbsp; [📖 **Read Documentation**](https://xurkon.github.io/TSM-WoWheadScraper/)

</div>

---

## ✨ Features

### 🌍 Multi-Version Support

Scrape items from **all Wowhead databases**: Retail, WotLK, TBC, Classic Era, Cataclysm, and MoP Classic.

### 📦 Multi-Format Export

Export item strings in **WotLK 3.3.5a** classic format (`item:12345`) or **Retail TSM** format (`i:12345`).

### 🖥️ Modern GUI

Sleek, dark-themed interface with **Theme Editor** (4 built-in themes + custom colors).

### ⚡ One-Click Import

Directly updates your `TradeSkillMaster.lua` SavedVariables file - no copy-paste needed.

### 🔗 Bind Type Filter

Filter items by binding type: **BoE, BoP, BoU, BoA, Quest, Warbound**, or **No Binding** - perfect for building specific TSM groups!

## 📥 Installation

### Option 1: Standalone EXE (Recommended)

1. Download the latest release
2. Run `TSM Scraper.exe`
3. Configure your TSM path and start scraping!

### Option 2: Python Source

1. Clone this repository
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the GUI:

   ```bash
   python gui_modern.py
   ```

## 🔧 Usage

1. **Select Database**: Choose your game version (e.g., `Wowhead (WotLK)`, `Wowhead (Retail)`)
2. **Select Format**: Choose your client version (`WotLK 3.3.5a` or `Retail`)
3. **Enable BoE Filter** (optional): Check the box to only scrape tradeable items
4. **Select Categories**: Check the item types you want (Weapons, Armor, Consumables)
5. **Scrape**: Click the **🔍 Scrape Items** button
6. **Import**: Review new items and click **📥 Import to TSM**

## 📜 Changelog

See [CHANGELOG.md](CHANGELOG.md) for full version history.

### v3.4.1 - Group Management

- **Window Position Memory**: App remembers position and size across sessions
- **Collapsible Groups**: Click to expand groups and view items inside
- **Ctrl+Click Multi-Select**: Select multiple groups for bulk operations
- **Move Groups**: Right-click → Move to relocate groups
- **Remove Selected Items**: Delete checked items directly from groups

### v3.3.5 - Feature Sync

- **Refresh Button**: Click 🔄 to reload SavedVariables after `/reload` in WoW
- **Fixed Group Detection**: Properly parses groups from SavedVariables
- **Config Fix**: Fixed config loading for compiled exe
- **Version Display**: Window title shows version number

### v3.3.0 - UI Overhaul

- **Manual Item IDs**: Add/remove specific item IDs with single entry, paste list, or remove mode
- **4-Column UI Layout**: Options | Categories | Results | Groups for better workflow
- **Draggable Column Resize**: Drag dividers between columns to customize widths

### v3.2.0 - Group & Bug Fixes

- **Fixed Delete Group**: Properly removes groups with nested structures
- **New Feature**: Copy current session log + Improved group hierarchy display

## 👥 Credits

- **Xurkon** - Main Developer
- **Wowhead** - For the comprehensive item databases
- **TradeSkillMaster** - For the amazing addon framework

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.
