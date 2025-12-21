"""
TSM Item Scraper GUI - Modern Edition

A sleek, modern graphical interface using CustomTkinter.
Features rounded corners, smooth animations, and a techy dark theme.
"""

import sys
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))

# Try CustomTkinter first, fall back to tkinter
try:
    import customtkinter as ctk
    from tkinter import messagebox, filedialog, colorchooser
    HAS_CTK = True
except ImportError:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog, colorchooser
    ctk = None
    HAS_CTK = False
    print("CustomTkinter not found. Install with: pip install customtkinter")
    print("Using standard tkinter (less modern look)")

from tsm_scraper.wowhead_scraper import WowheadScraper
from tsm_scraper.lua_parser import TSMLuaParser
from tsm_scraper.lua_writer import TSMLuaWriter
from theme_manager import theme_manager, Theme, COLOR_CATEGORIES

# Load saved theme on startup
theme_manager.load()


# ============================================================================
# Theme Configuration for CustomTkinter
# ============================================================================

def apply_ctk_theme():
    """Apply the current theme to CustomTkinter."""
    if not HAS_CTK:
        return
    
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")


def get_color(name: str) -> str:
    """Get color from theme manager."""
    return theme_manager.get(name)

# ============================================================================
# Constants
# ============================================================================

import os

# Get the correct base path - use exe location when frozen, otherwise script location
if getattr(sys, 'frozen', False):
    # Running as compiled exe
    _BASE_PATH = Path(sys.executable).parent
else:
    # Running as script
    _BASE_PATH = Path(__file__).parent


def _detect_wine_or_linux() -> bool:
    """
    Detect if running under Wine/Bottles/Proton on Linux.
    
    Returns True if:
    - Running on actual Linux (not Wine)
    - Running under Wine/Bottles/Proton
    """
    # Check for actual Linux
    if sys.platform.startswith('linux'):
        return True
    
    # Check for Wine environment variables (set by Wine/Bottles/Proton)
    wine_indicators = [
        'WINEPREFIX',
        'WINELOADER', 
        'WINE',
        'WINEDEBUG',
        'WINESERVER',
    ]
    for indicator in wine_indicators:
        if os.environ.get(indicator):
            return True
    
    # Check if /proc/version mentions wine or bottles (Linux-specific)
    try:
        # This file exists on Linux but not Windows
        if Path('/proc/version').exists():
            return True
    except:
        pass
    
    # Check for .wine folder in standard locations via Z: drive (Wine's root mapping)
    try:
        if Path('Z:/.wine').exists() or Path('Z:/home').exists():
            return True
    except:
        pass
    
    return False


def _get_app_data_path() -> Path:
    """
    Get the appropriate path for config/logs based on OS/environment.
    
    On Windows: Use APPDATA
    On Linux/Wine: Use the scraper's directory (avoids Wine path issues)
    """
    is_wine = _detect_wine_or_linux()
    
    if is_wine:
        # Use local directory to avoid Wine path mapping issues
        local_path = _BASE_PATH / "appdata"
        try:
            local_path.mkdir(parents=True, exist_ok=True)
            # Test write access
            test_file = local_path / ".write_test"
            test_file.touch()
            test_file.unlink()
            return local_path
        except Exception:
            # Fallback to base path if appdata subfolder fails
            return _BASE_PATH
    else:
        # Standard Windows path
        appdata = os.environ.get('APPDATA')
        if appdata:
            return Path(appdata) / "TSM Scraper"
        else:
            # Fallback to home directory
            return Path.home() / "TSM Scraper"


# Determine app data path with Wine/Linux detection
_APP_DATA_PATH = _get_app_data_path()

DEFAULT_TSM_PATH = r"C:\Ascension Launcher\resources\client\WTF\Account\ACCOUNTNAME\SavedVariables\TradeSkillMaster.lua"
CONFIG_PATH = _APP_DATA_PATH / "config" / "gui_config.json"
LOG_PATH = _APP_DATA_PATH / "logs" / "scraper.log"
VERSION = "3.4.18"


# ============================================================================
# Themed Message Dialogs
# ============================================================================

class ThemedMessageBox(ctk.CTkToplevel if HAS_CTK else object):
    """A themed message box using CustomTkinter."""
    
    def __init__(self, parent, title: str, message: str, icon: str = "info", 
                 buttons: list = None, default_button: str = None):
        super().__init__(parent)
        self.result = None
        
        self.title(title)
        
        # Calculate height based on message length - bigger for more content
        # Base height + extra for each ~50 chars of message
        lines = message.count('\n') + 1
        char_lines = len(message) // 40  # Rough estimate of wrapped lines
        extra_height = max(lines, char_lines) * 18
        height = min(500, max(220, 180 + extra_height))  # Clamp between 220-500
        
        self.geometry(f"420x{height}")
        self.resizable(False, False)
        self.configure(fg_color=get_color('bg_dark'))
        
        # Center on parent
        self.transient(parent)
        self.grab_set()
        
        # Icon and message
        icon_map = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "question": "❓"}
        
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=15)
        
        # Icon
        ctk.CTkLabel(
            content,
            text=icon_map.get(icon, "ℹ️"),
            font=ctk.CTkFont(size=32),
            text_color=get_color('accent_primary')
        ).pack(pady=(0, 8))
        
        # Message - use scrollable frame for very long messages
        msg_label = ctk.CTkLabel(
            content,
            text=message,
            font=ctk.CTkFont(size=11),
            text_color=get_color('text_light'),
            wraplength=380,
            justify="center"
        )
        msg_label.pack(pady=(0, 15), fill="x")
        
        # Buttons
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack()
        
        if buttons is None:
            buttons = ["OK"]
        
        for btn_text in buttons:
            is_primary = (btn_text == default_button) or (len(buttons) == 1)
            btn = ctk.CTkButton(
                btn_frame,
                text=btn_text,
                width=80,
                height=32,
                corner_radius=6,
                fg_color=get_color('accent_primary_dark') if is_primary else get_color('bg_light'),
                hover_color=get_color('accent_primary') if is_primary else get_color('bg_hover'),
                text_color=get_color('text_white') if is_primary else get_color('text_light'),
                command=lambda t=btn_text: self._on_button(t)
            )
            btn.pack(side="left", padx=5)
        
        # Handle close button
        self.protocol("WM_DELETE_WINDOW", lambda: self._on_button(None))
        
        # Wait for dialog
        self.wait_window()
    
    def _on_button(self, value):
        self.result = value
        self.destroy()


def themed_askquestion(parent, title: str, message: str) -> bool:
    """Show a themed Yes/No dialog. Returns True for Yes, False for No."""
    dialog = ThemedMessageBox(
        parent, title, message, 
        icon="question", 
        buttons=["Yes", "No"],
        default_button="Yes"
    )
    return dialog.result == "Yes"


def themed_showinfo(parent, title: str, message: str):
    """Show a themed info dialog."""
    ThemedMessageBox(parent, title, message, icon="info", buttons=["OK"])


def themed_showerror(parent, title: str, message: str):
    """Show a themed error dialog."""
    ThemedMessageBox(parent, title, message, icon="error", buttons=["OK"])


def themed_showwarning(parent, title: str, message: str):
    """Show a themed warning dialog."""
    ThemedMessageBox(parent, title, message, icon="warning", buttons=["OK"])

# ============================================================================
# Main Application (CustomTkinter)
# ============================================================================

class TSMScraperApp(ctk.CTk if HAS_CTK else object):
    """Modern TSM Item Scraper GUI using CustomTkinter."""
    
    def __init__(self):
        super().__init__()
        
        apply_ctk_theme()
        
        self.title(f"TSM Wowhead Scraper v{VERSION}")
        self.geometry("1000x750")
        self.minsize(900, 650)
        
        # Configure colors from theme
        self.configure(fg_color=get_color('bg_darkest'))
        
        # Configuration
        self.config = self.load_config()
        self.tsm_path = self.config.get("tsm_path", DEFAULT_TSM_PATH)
        
        # Components
        self.current_server = "Wowhead (Retail)"
        self.current_tsm_format = "retail"  # 'classic' or 'retail'
        self.scraper = WowheadScraper(game_version="retail")
        self.wowhead_scraper = self.scraper  # Same reference for Wowhead
        self.category_vars: Dict[str, ctk.BooleanVar] = {}
        self.scrape_results: Dict[str, dict] = {}
        self.existing_ids: set = set()
        self.group_buttons_registry: Dict[str, ctk.CTkButton] = {}
        
        # Bind type filter options: value -> (bonding_id, description)
        # bonding_id is None for 'All Items', otherwise matches Wowhead's bonding values
        self.BIND_FILTER_OPTIONS = {
            "All Items": (None, "No filter - scrape all items"),
            "Bind on Equip (BoE)": (2, "Tradeable on AH until equipped"),
            "Bind on Use (BoU)": (3, "Bound when consumed/used"),
            "Bind to Account (BoA)": (5, "Account-wide heirlooms"),
            "Quest Items": (4, "Quest-related items"),
            "Warbound": (6, "Warband-shared items (Retail)"),
            "No Binding": (0, "Items with no bind restrictions"),
        }
        self.bind_filter_var = ctk.StringVar(value="All Items")
        
        # Manual Item ID management
        self.manual_add_ids: list = []
        self.manual_remove_ids: list = []
        self.remove_mode_var = ctk.BooleanVar(value=False)
        
        # Group expand/collapse state
        self.group_expand_state: Dict[str, bool] = {}
        self.group_item_checkboxes: Dict[str, ctk.BooleanVar] = {}
        self.selected_groups: set = set()  # For multi-group selection with Ctrl+click
        
        # Build UI
        self.create_layout()
        self.load_tsm_info()
        
        # Restore window position from config
        self.restore_window_position()
        
        # Save window position on close
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def load_config(self) -> dict:
        try:
            if CONFIG_PATH.exists():
                with open(CONFIG_PATH, 'r') as f:
                    config = json.load(f)
                    # Migrate old config format if needed
                    if "profiles" not in config and "tsm_path" in config:
                        config["profiles"] = [config["tsm_path"]]
                    return config
        except:
            pass
        return {}
    
    def save_config(self):
        try:
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            profiles = self.config.get("profiles", [])
            if self.tsm_path and self.tsm_path not in profiles:
                profiles.insert(0, self.tsm_path)
            # Keep only up to 5 profiles
            profiles = profiles[:5]
            self.config["profiles"] = profiles
            self.config["tsm_path"] = self.tsm_path
            with open(CONFIG_PATH, 'w') as f:
                json.dump(self.config, f, indent=2)
        except:
            pass
    
    def restore_window_position(self):
        """Restore window position and size from config."""
        try:
            x = self.config.get("window_x")
            y = self.config.get("window_y")
            width = self.config.get("window_width", 1000)
            height = self.config.get("window_height", 750)
            
            if x is not None and y is not None:
                # Validate position is on screen
                screen_width = self.winfo_screenwidth()
                screen_height = self.winfo_screenheight()
                
                # Ensure window is at least partially visible
                if x < screen_width - 100 and y < screen_height - 100 and x > -width + 100 and y > -height + 100:
                    self.geometry(f"{width}x{height}+{x}+{y}")
                else:
                    self.geometry(f"{width}x{height}")
            else:
                self.geometry(f"{width}x{height}")
        except Exception:
            pass
    
    def save_window_position(self):
        """Save current window position and size to config."""
        try:
            self.config["window_x"] = self.winfo_x()
            self.config["window_y"] = self.winfo_y()
            self.config["window_width"] = self.winfo_width()
            self.config["window_height"] = self.winfo_height()

            # Save paned window sash positions
            if hasattr(self, 'paned'):
                sash_positions = []
                for i in range(3):  # 4 panes = 3 sashes
                    try:
                        pos = self.paned.sash_coord(i)[0]
                        sash_positions.append(pos)
                    except:
                        break
                if sash_positions:
                    self.config["sash_positions"] = sash_positions
        except Exception:
            pass
    
    def restore_sash_positions(self):
        """Restore paned window sash positions from config."""
        try:
            sash_positions = self.config.get("sash_positions", [])
            if sash_positions and hasattr(self, 'paned'):
                for i, pos in enumerate(sash_positions):
                    try:
                        self.paned.sash_place(i, pos, 0)
                    except:
                        break
        except Exception:
            pass

    def on_close(self):
        """Handle window close - save position and exit."""
        self.save_window_position()
        self.save_config()
        self.destroy()
    
    def get_profile_names(self) -> list:
        """Get list of profile display names for dropdown."""
        profiles = self.config.get("profiles", [])
        if self.tsm_path and self.tsm_path not in profiles:
            profiles = [self.tsm_path] + profiles
        # Return just the filename for display, limit to 5
        names = []
        for p in profiles[:5]:
            try:
                names.append(Path(p).name)
            except:
                names.append(p)
        return names if names else ["Select profile..."]
    
    def get_profile_path_by_name(self, name: str) -> str:
        """Get full path for a profile display name."""
        profiles = self.config.get("profiles", [])
        if self.tsm_path and self.tsm_path not in profiles:
            profiles = [self.tsm_path] + profiles
        for p in profiles:
            try:
                if Path(p).name == name:
                    return p
            except:
                pass
        return self.tsm_path
    
    def on_profile_changed(self, selection: str):
        """Handle profile selection change."""
        if selection == "Select profile...":
            return
        
        new_path = self.get_profile_path_by_name(selection)
        if new_path and Path(new_path).exists():
            self.tsm_path = new_path
            self.save_config()
            self.load_tsm_info()
            self.refresh_groups_panel()
            self.log(f"Switched to profile: {selection}", 'success')
        else:
            self.log(f"Profile not found: {selection}", 'error')
    
    def open_tsm_folder(self):
        """Open the TSM SavedVariables folder in file explorer."""
        import subprocess
        import os
        
        try:
            folder = Path(self.tsm_path).parent
            if folder.exists():
                if sys.platform == 'win32':
                    os.startfile(str(folder))
                elif sys.platform == 'darwin':
                    subprocess.run(['open', str(folder)])
                else:
                    subprocess.run(['xdg-open', str(folder)])
                self.log(f"Opened folder: {folder}", 'success')
            else:
                self.log(f"Folder not found: {folder}", 'error')
        except Exception as e:
            self.log(f"Error opening folder: {e}", 'error')
    
    def remove_current_profile(self):
        """Remove the current profile from the dropdown list (doesn't delete the file)."""
        profiles = self.config.get("profiles", [])
        
        if len(profiles) <= 1:
            self.log("Cannot remove the only profile", 'warning')
            return
        
        current_name = self.profile_var.get()
        current_path = self.get_profile_path_by_name(current_name)
        
        if current_path in profiles:
            profiles.remove(current_path)
            self.config["profiles"] = profiles
            
            # Switch to first remaining profile
            if profiles:
                self.tsm_path = profiles[0]
                self.profile_var.set(Path(profiles[0]).name)
            
            self.save_config()
            self.profile_combo.configure(values=self.get_profile_names())
            self.load_tsm_info()
            self.refresh_groups_panel()
            self.log(f"Removed profile: {current_name}", 'success')
    
    def bind_mousewheel_to_scrollable(self, scrollable_frame):
        """
        Bind mouse wheel events to a CTkScrollableFrame so users can scroll with their mouse.
        
        CustomTkinter's scrollable frames don't handle mouse wheel by default when
        hovering over child widgets, so we need to manually bind the events.
        """
        def on_mousewheel(event):
            # Windows uses event.delta, Linux uses event.num
            if event.delta:
                scrollable_frame._parent_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif event.num == 4:  # Linux scroll up
                scrollable_frame._parent_canvas.yview_scroll(-1, "units")
            elif event.num == 5:  # Linux scroll down
                scrollable_frame._parent_canvas.yview_scroll(1, "units")
        
        def bind_to_widget(widget):
            """Recursively bind mousewheel to widget and all children."""
            widget.bind("<MouseWheel>", on_mousewheel, add="+")  # Windows
            widget.bind("<Button-4>", on_mousewheel, add="+")    # Linux scroll up
            widget.bind("<Button-5>", on_mousewheel, add="+")    # Linux scroll down
            for child in widget.winfo_children():
                bind_to_widget(child)
        
        # Bind to the scrollable frame and all its children
        bind_to_widget(scrollable_frame)
        
        # Also bind to the internal canvas
        if hasattr(scrollable_frame, '_parent_canvas'):
            scrollable_frame._parent_canvas.bind("<MouseWheel>", on_mousewheel, add="+")
            scrollable_frame._parent_canvas.bind("<Button-4>", on_mousewheel, add="+")
            scrollable_frame._parent_canvas.bind("<Button-5>", on_mousewheel, add="+")
    
    def create_layout(self):
        """Create the main UI layout with 4 resizable columns using PanedWindow."""
        import tkinter as tk
        
        # Configure main grid - header on top, paned window below
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header bar (full width)
        self.create_header()
        
        # Create horizontal PanedWindow for resizable columns
        # Store reference for panel creation
        self.paned = tk.PanedWindow(
            self,
            orient=tk.HORIZONTAL,
            sashwidth=6,
            sashrelief=tk.FLAT,
            bg=get_color('border_dark'),
            opaqueresize=False
        )
        self.paned.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        
        # Create panels - each returns a tk.Frame wrapper
        left_frame = self.create_left_sidebar_paned()
        cat_frame = self.create_categories_panel_paned()
        center_frame = self.create_center_panel_paned()
        right_frame = self.create_right_sidebar_paned()
        
        # Add panels to PanedWindow with initial widths
        self.paned.add(left_frame, minsize=200, width=240)
        self.paned.add(cat_frame, minsize=160, width=200)
        self.paned.add(center_frame, minsize=200, stretch="always")
        self.paned.add(right_frame, minsize=200, width=260)

        # Restore sash positions after panes are added
        self.after(100, self.restore_sash_positions)
    
    def create_header(self):
        """Create the sleek header bar."""
        header = ctk.CTkFrame(self, fg_color=get_color('bg_dark'), corner_radius=0)
        header.grid(row=0, column=0, columnspan=4, sticky="ew", padx=0, pady=0)
        header.grid_columnconfigure(1, weight=1)
        
        # Logo section
        logo_frame = ctk.CTkFrame(header, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=20, pady=15, sticky="w")
        
        # TSM gold text
        tsm_label = ctk.CTkLabel(
            logo_frame,
            text="TSM",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=get_color('accent_secondary')
        )
        tsm_label.pack(side="left")
        
        # Item Scraper cyan text
        scraper_label = ctk.CTkLabel(
            logo_frame,
            text=" Item Scraper",
            font=ctk.CTkFont(family="Segoe UI", size=24),
            text_color=get_color('accent_primary')
        )
        scraper_label.pack(side="left")
        
        # Right section - Settings button + status
        right_frame = ctk.CTkFrame(header, fg_color="transparent")
        right_frame.grid(row=0, column=1, padx=20, pady=15, sticky="e")
        
        # Settings button with gear icon
        self.settings_btn = ctk.CTkButton(
            right_frame,
            text="🎨 Themes",
            width=100,
            height=32,
            corner_radius=8,
            fg_color=get_color('bg_light'),
            hover_color=get_color('bg_hover'),
            text_color=get_color('text_light'),
            command=self.open_settings
        )
        self.settings_btn.pack(side="right", padx=(10, 0))
        
        # Status label
        self.status_label = ctk.CTkLabel(
            right_frame,
            text="● Ready",
            font=ctk.CTkFont(size=12),
            text_color=get_color('color_success')
        )
        self.status_label.pack(side="right", padx=10)
    
    def create_left_sidebar(self):
        """Create the left sidebar with server selection, file info and options."""
        sidebar = ctk.CTkFrame(
            self,
            width=240,
            fg_color=get_color('bg_medium'),
            corner_radius=0
        )
        sidebar.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)
        
        # Server Selection Section
        server_section = ctk.CTkFrame(sidebar, fg_color="transparent")
        server_section.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        
        ctk.CTkLabel(
            server_section,
            text="🌐 Database Server",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=get_color('accent_primary')
        ).pack(anchor="w")
        
        # Server dropdown
        self.server_var = ctk.StringVar(value="Ascension (db.ascension.gg)")
        self.server_combo = ctk.CTkComboBox(
            server_section,
            variable=self.server_var,
            values=[
                "Ascension (db.ascension.gg)",
                "Turtle WoW",
                "Wowhead (WotLK)",
                "Wowhead (TBC)",
                "Wowhead (Classic Era)",
                "Wowhead (Cata)",
                "Wowhead (MoP Classic)",
                "Wowhead (Retail)",
            ],
            height=28,
            corner_radius=6,
            fg_color=get_color('bg_light'),
            border_color=get_color('border_dark'),
            button_color=get_color('accent_primary_dark'),
            button_hover_color=get_color('accent_primary'),
            dropdown_fg_color=get_color('bg_medium'),
            dropdown_hover_color=get_color('bg_hover'),
            font=ctk.CTkFont(size=10),
            command=self.on_server_changed
        )
        self.server_combo.pack(fill="x", pady=(6, 0))
        
        # TSM Format Selection
        format_section = ctk.CTkFrame(server_section, fg_color="transparent")
        format_section.pack(fill="x", pady=(8, 0))
        
        ctk.CTkLabel(
            format_section,
            text="📝 TSM Format",
            font=ctk.CTkFont(size=11),
            text_color=get_color('text_light')
        ).pack(anchor="w")
        
        self.tsm_format_var = ctk.StringVar(value="WotLK 3.3.5a")
        self.format_combo = ctk.CTkComboBox(
            format_section,
            variable=self.tsm_format_var,
            values=[
                "WotLK 3.3.5a",
                "Retail (Official TSM)",
            ],
            height=26,
            corner_radius=6,
            fg_color=get_color('bg_light'),
            border_color=get_color('border_dark'),
            button_color=get_color('accent_primary_dark'),
            button_hover_color=get_color('accent_primary'),
            dropdown_fg_color=get_color('bg_medium'),
            dropdown_hover_color=get_color('bg_hover'),
            font=ctk.CTkFont(size=10),
            command=self.on_format_changed
        )
        self.format_combo.pack(fill="x", pady=(4, 0))
        
        # Format info label
        self.format_info = ctk.CTkLabel(
            format_section,
            text="item:ID:... format",
            font=ctk.CTkFont(size=9),
            text_color=get_color('text_gray')
        )
        self.format_info.pack(anchor="w", pady=(2, 0))
        
        # Bind Type Filter Section
        bind_frame = ctk.CTkFrame(server_section, fg_color="transparent")
        bind_frame.pack(fill="x", pady=(8, 0))
        
        ctk.CTkLabel(
            bind_frame,
            text="🔗 Bind Filter",
            font=ctk.CTkFont(size=11),
            text_color=get_color('text_light')
        ).pack(anchor="w")
        
        self.bind_combo = ctk.CTkComboBox(
            bind_frame,
            variable=self.bind_filter_var,
            values=list(self.BIND_FILTER_OPTIONS.keys()),
            height=26,
            corner_radius=6,
            fg_color=get_color('bg_light'),
            border_color=get_color('border_dark'),
            button_color=get_color('accent_primary_dark'),
            button_hover_color=get_color('accent_primary'),
            dropdown_fg_color=get_color('bg_medium'),
            dropdown_hover_color=get_color('bg_hover'),
            font=ctk.CTkFont(size=10),
            command=self.on_bind_filter_changed
        )
        self.bind_combo.pack(fill="x", pady=(4, 0))
        
        # Bind filter info label
        self.bind_info = ctk.CTkLabel(
            bind_frame,
            text="No filter - scrape all items",
            font=ctk.CTkFont(size=9),
            text_color=get_color('text_gray')
        )
        self.bind_info.pack(anchor="w", pady=(2, 0))
        
        # Manual Item IDs Section
        manual_frame = ctk.CTkFrame(server_section, fg_color="transparent")
        manual_frame.pack(fill="x", pady=(12, 0))
        
        ctk.CTkLabel(
            manual_frame,
            text="📝 Manual Item IDs",
            font=ctk.CTkFont(size=11),
            text_color=get_color('text_light')
        ).pack(anchor="w")
        
        # Entry row with ID field and Add button
        entry_row = ctk.CTkFrame(manual_frame, fg_color="transparent")
        entry_row.pack(fill="x", pady=(4, 0))
        
        self.manual_id_entry = ctk.CTkEntry(
            entry_row,
            placeholder_text="Enter Item ID",
            height=26,
            corner_radius=6,
            fg_color=get_color('bg_light'),
            border_color=get_color('border_dark'),
            font=ctk.CTkFont(size=10)
        )
        self.manual_id_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.manual_id_entry.bind("<Return>", lambda e: self.add_manual_id())
        
        self.add_id_btn = ctk.CTkButton(
            entry_row,
            text="+ Add",
            width=50,
            height=26,
            corner_radius=6,
            font=ctk.CTkFont(size=10),
            fg_color=get_color('accent_primary'),
            hover_color=get_color('accent_primary_dark'),
            command=self.add_manual_id
        )
        self.add_id_btn.pack(side="right")
        
        # Button row with Paste List and Remove Mode toggle
        btn_row = ctk.CTkFrame(manual_frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=(4, 0))
        
        ctk.CTkButton(
            btn_row,
            text="📋 Paste List",
            width=80,
            height=24,
            corner_radius=4,
            font=ctk.CTkFont(size=9),
            fg_color=get_color('bg_light'),
            hover_color=get_color('bg_hover'),
            command=self.paste_id_list
        ).pack(side="left", padx=(0, 4))
        
        self.remove_mode_cb = ctk.CTkCheckBox(
            btn_row,
            text="Remove Mode",
            variable=self.remove_mode_var,
            font=ctk.CTkFont(size=9),
            fg_color=get_color('color_error'),
            hover_color=get_color('color_error'),
            text_color=get_color('text_light'),
            corner_radius=4,
            height=20,
            command=self.update_manual_id_ui
        )
        self.remove_mode_cb.pack(side="left")
        
        # Status counters
        self.manual_status = ctk.CTkLabel(
            manual_frame,
            text="Added: 0  |  Removed: 0",
            font=ctk.CTkFont(size=9),
            text_color=get_color('text_gray')
        )
        self.manual_status.pack(anchor="w", pady=(2, 0))
        
        # Separator
        sep0 = ctk.CTkFrame(sidebar, height=2, fg_color=get_color('border_dark'))
        sep0.grid(row=1, column=0, sticky="ew", padx=12, pady=8)
        
        # TSM File Section
        file_section = ctk.CTkFrame(sidebar, fg_color="transparent")
        file_section.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 8))
        
        # Header row with folder icon that opens folder
        header_row = ctk.CTkFrame(file_section, fg_color="transparent")
        header_row.pack(fill="x")
        
        folder_btn = ctk.CTkButton(
            header_row,
            text="📁",
            width=24,
            height=24,
            corner_radius=4,
            fg_color="transparent",
            hover_color=get_color('bg_hover'),
            command=self.open_tsm_folder
        )
        folder_btn.pack(side="left")
        
        ctk.CTkLabel(
            header_row,
            text="TSM SavedVariables",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=get_color('accent_primary')
        ).pack(side="left", padx=(4, 0))
        
        # Profile dropdown (stores up to 5 profiles)
        profile_frame = ctk.CTkFrame(file_section, fg_color="transparent")
        profile_frame.pack(fill="x", pady=(6, 0))
        
        self.profile_var = ctk.StringVar(value=Path(self.tsm_path).name if Path(self.tsm_path).exists() else "Select profile...")
        self.profile_combo = ctk.CTkComboBox(
            profile_frame,
            variable=self.profile_var,
            values=self.get_profile_names(),
            height=28,
            corner_radius=6,
            fg_color=get_color('bg_light'),
            border_color=get_color('border_dark'),
            button_color=get_color('accent_primary_dark'),
            button_hover_color=get_color('accent_primary'),
            dropdown_fg_color=get_color('bg_medium'),
            dropdown_hover_color=get_color('bg_hover'),
            font=ctk.CTkFont(size=10),
            command=self.on_profile_changed
        )
        self.profile_combo.pack(side="left", fill="x", expand=True)
        
        browse_btn = ctk.CTkButton(
            profile_frame, text="...", width=32, height=28,
            corner_radius=6,
            fg_color=get_color('bg_light'),
            hover_color=get_color('bg_hover'),
            command=self.browse_tsm_file
        )
        browse_btn.pack(side="right", padx=(2, 0))
        
        # Remove profile button
        remove_btn = ctk.CTkButton(
            profile_frame, text="🗑️", width=28, height=28,
            corner_radius=6,
            fg_color="transparent",
            hover_color=get_color('color_error'),
            command=self.remove_current_profile
        )
        remove_btn.pack(side="right", padx=(2, 0))
        
        # TSM Info label
        self.tsm_info = ctk.CTkLabel(
            file_section,
            text="Loading...",
            font=ctk.CTkFont(size=10),
            text_color=get_color('text_gray')
        )
        self.tsm_info.pack(anchor="w", pady=(4, 0))
        
        # Scrape button at bottom (use weight=1 to push it to bottom)
        sidebar.grid_rowconfigure(3, weight=1)
        action_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        action_frame.grid(row=4, column=0, sticky="sew", padx=12, pady=12)
        
        self.scrape_btn = ctk.CTkButton(
            action_frame,
            text="🔍 Scrape Items",
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=get_color('accent_primary_dark'),
            hover_color=get_color('accent_primary'),
            command=self.start_scrape
        )
        self.scrape_btn.pack(fill="x")
    
    def create_categories_panel(self):
        """Create the categories panel in column 1."""
        panel = ctk.CTkFrame(
            self,
            width=200,
            fg_color=get_color('bg_medium'),
            corner_radius=0
        )
        panel.grid(row=1, column=1, sticky="nsew", padx=0, pady=0)
        panel.grid_propagate(False)
        panel.grid_rowconfigure(1, weight=1)  # Scrollable list
        
        # Categories header
        cat_header = ctk.CTkFrame(panel, fg_color="transparent")
        cat_header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 8))
        
        ctk.CTkLabel(
            cat_header,
            text="📋 Scrape Categories",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=get_color('accent_primary')
        ).pack(side="left")
        
        # Quick select buttons
        quick_frame = ctk.CTkFrame(cat_header, fg_color="transparent")
        quick_frame.pack(side="right")
        
        ctk.CTkButton(
            quick_frame, text="All", width=28, height=18,
            corner_radius=4, font=ctk.CTkFont(size=9),
            fg_color=get_color('bg_light'),
            hover_color=get_color('bg_hover'),
            command=self.select_all
        ).pack(side="left", padx=1)
        
        ctk.CTkButton(
            quick_frame, text="None", width=32, height=18,
            corner_radius=4, font=ctk.CTkFont(size=9),
            fg_color=get_color('bg_light'),
            hover_color=get_color('bg_hover'),
            command=self.deselect_all
        ).pack(side="left", padx=1)
        
        # Scrollable category list
        self.cat_scroll = ctk.CTkScrollableFrame(
            panel,
            fg_color=get_color('bg_light'),
            corner_radius=8
        )
        self.cat_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        self.create_category_list()
        
        # Enable mouse wheel scrolling in the category list
        self.bind_mousewheel_to_scrollable(self.cat_scroll)
    
    def create_center_panel(self):
        """Create the compact center panel with results and log."""
        center = ctk.CTkFrame(self, fg_color=get_color('bg_medium'), corner_radius=0)
        center.grid(row=1, column=2, sticky="nsew", padx=0, pady=0)
        center.grid_columnconfigure(0, weight=1)
        center.grid_rowconfigure(1, weight=1)
        center.grid_rowconfigure(3, weight=0)
        
        # Results header
        header = ctk.CTkFrame(center, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 5))
        
        ctk.CTkLabel(
            header,
            text="📊 Scrape Results",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=get_color('accent_primary')
        ).pack(side="left")
        
        self.results_summary = ctk.CTkLabel(
            header,
            text="Select categories and click Scrape",
            font=ctk.CTkFont(size=10),
            text_color=get_color('text_gray')
        )
        self.results_summary.pack(side="right")
        
        # Results display - scrollable frame with checkboxes
        self.results_scroll = ctk.CTkScrollableFrame(
            center,
            corner_radius=6,
            fg_color=get_color('bg_light'),
            height=150
        )
        self.results_scroll.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 8))
        
        # Initialize results checkbox storage
        self.results_checkboxes: Dict[str, ctk.BooleanVar] = {}
        
        # Enable mouse wheel scrolling in results list
        self.bind_mousewheel_to_scrollable(self.results_scroll)
        
        # Log header
        log_header = ctk.CTkFrame(center, fg_color="transparent")
        log_header.grid(row=2, column=0, sticky="ew", padx=15, pady=(5, 3))
        
        ctk.CTkLabel(
            log_header,
            text="📜 Log",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=get_color('text_gray')
        ).pack(side="left")
        
        # Log folder button
        log_folder_btn = ctk.CTkButton(
            log_header,
            text="📁",
            width=24,
            height=20,
            corner_radius=4,
            fg_color="transparent",
            hover_color=get_color('bg_hover'),
            command=self.open_log_folder
        )
        log_folder_btn.pack(side="left", padx=(6, 0))
        
        # Copy log button
        copy_log_btn = ctk.CTkButton(
            log_header,
            text="📋",
            width=24,
            height=20,
            corner_radius=4,
            fg_color="transparent",
            hover_color=get_color('bg_hover'),
            command=self.copy_log_to_clipboard
        )
        copy_log_btn.pack(side="left", padx=(2, 0))
        
        # Log text (compact)
        self.log_text = ctk.CTkTextbox(
            center,
            height=80,
            corner_radius=6,
            fg_color=get_color('bg_darkest'),
            text_color=get_color('text_gray'),
            font=ctk.CTkFont(family="Consolas", size=9)
        )
        self.log_text.grid(row=3, column=0, sticky="ew", padx=15, pady=(0, 10))
        self.log_text.configure(state="disabled")
        
        # Progress bar
        self.progress = ctk.CTkProgressBar(
            center,
            height=4,
            corner_radius=2,
            fg_color=get_color('bg_dark'),
            progress_color=get_color('accent_primary')
        )
        self.progress.set(0)
    
    def create_right_sidebar(self):
        """Create the right sidebar with TSM groups for import target selection."""
        sidebar = ctk.CTkFrame(
            self,
            width=260,
            fg_color=get_color('bg_medium'),
            corner_radius=0
        )
        sidebar.grid(row=1, column=3, sticky="nsew", padx=0, pady=0)
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(2, weight=1)  # Groups list
        
        # Header
        header = ctk.CTkFrame(sidebar, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        
        ctk.CTkLabel(
            header,
            text="📁 Import Target Group",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=get_color('accent_primary')
        ).pack(side="left")
        
        self.groups_count_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=9),
            text_color=get_color('text_gray')
        )
        self.groups_count_label.pack(side="right")
        
        # Instructions
        ctk.CTkLabel(
            sidebar,
            text="Click a group to select it as import target:",
            font=ctk.CTkFont(size=9),
            text_color=get_color('text_gray')
        ).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 4))
        
        # Groups list (scrollable, clickable)
        self.groups_scroll = ctk.CTkScrollableFrame(
            sidebar,
            fg_color=get_color('bg_light'),
            corner_radius=8
        )
        self.groups_scroll.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 8))
        
        # Enable mouse wheel scrolling in groups list
        self.bind_mousewheel_to_scrollable(self.groups_scroll)
        
        # Selected group display
        selected_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        selected_frame.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 8))
        
        ctk.CTkLabel(
            selected_frame,
            text="Selected:",
            font=ctk.CTkFont(size=10),
            text_color=get_color('text_gray')
        ).pack(anchor="w")
        
        self.selected_group_var = ctk.StringVar(value="(Use default from scraper)")
        self.selected_group_label = ctk.CTkLabel(
            selected_frame,
            textvariable=self.selected_group_var,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=get_color('accent_secondary'),
            wraplength=230
        )
        self.selected_group_label.pack(anchor="w")
        
        # Import button at bottom
        action_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        action_frame.grid(row=4, column=0, sticky="ew", padx=12, pady=12)
        
        self.import_btn = ctk.CTkButton(
            action_frame,
            text="📥 Import to TSM",
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=get_color('accent_secondary_dark'),
            hover_color=get_color('accent_secondary'),
            text_color=get_color('bg_dark'),
            command=self.start_import,
            state="disabled"
        )
        self.import_btn.pack(fill="x")
        
        # Create Default Groups button
        self.create_groups_btn = ctk.CTkButton(
            action_frame,
            text="✨ Create Default Groups",
            height=32,
            corner_radius=8,
            font=ctk.CTkFont(size=11),
            fg_color=get_color('bg_dark'),
            hover_color=get_color('bg_light'),
            text_color=get_color('text_light'),
            border_width=1,
            border_color=get_color('accent_primary'),
            command=self.create_default_groups
        )
        self.create_groups_btn.pack(fill="x", pady=(8, 0))
    
    # =========================================================================
    # PanedWindow-compatible panel methods (use pack layout, return tk.Frame)
    # =========================================================================
    
    def create_left_sidebar_paned(self):
        """Create resizable left sidebar for PanedWindow."""
        import tkinter as tk
        
        # Outer tk.Frame for PanedWindow
        wrapper = tk.Frame(self.paned, bg=get_color('bg_medium'))
        
        # Inner CTk scrollable content
        sidebar = ctk.CTkScrollableFrame(wrapper, fg_color=get_color('bg_medium'), corner_radius=0)
        sidebar.pack(fill="both", expand=True)
        
        # Server Selection Section
        server_section = ctk.CTkFrame(sidebar, fg_color="transparent")
        server_section.pack(fill="x", padx=12, pady=(12, 8))
        
        ctk.CTkLabel(
            server_section,
            text="🌐 Database Server",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=get_color('accent_primary')
        ).pack(anchor="w")
        
        # Server dropdown
        self.server_var = ctk.StringVar(value="Wowhead (Retail)")
        self.server_combo = ctk.CTkComboBox(
            server_section,
            variable=self.server_var,
            values=[
                "Wowhead (Retail)",
                "Wowhead (WotLK)",
                "Wowhead (TBC)",
                "Wowhead (Classic Era)",
                "Wowhead (Cata)",
                "Wowhead (MoP Classic)",
            ],
            height=28,
            corner_radius=6,
            fg_color=get_color('bg_light'),
            border_color=get_color('border_dark'),
            button_color=get_color('accent_primary_dark'),
            button_hover_color=get_color('accent_primary'),
            dropdown_fg_color=get_color('bg_medium'),
            dropdown_hover_color=get_color('bg_hover'),
            font=ctk.CTkFont(size=10),
            command=self.on_server_changed
        )
        self.server_combo.pack(fill="x", pady=(6, 0))
        
        # TSM Format Section
        format_section = ctk.CTkFrame(server_section, fg_color="transparent")
        format_section.pack(fill="x", pady=(8, 0))
        
        ctk.CTkLabel(
            format_section,
            text="📝 TSM Format",
            font=ctk.CTkFont(size=11),
            text_color=get_color('text_light')
        ).pack(anchor="w")
        
        self.tsm_format_var = ctk.StringVar(value="WotLK 3.3.5a")
        self.format_combo = ctk.CTkComboBox(
            format_section,
            variable=self.tsm_format_var,
            values=["WotLK 3.3.5a", "Retail (Official TSM)"],
            height=26,
            corner_radius=6,
            fg_color=get_color('bg_light'),
            border_color=get_color('border_dark'),
            button_color=get_color('accent_primary_dark'),
            button_hover_color=get_color('accent_primary'),
            dropdown_fg_color=get_color('bg_medium'),
            dropdown_hover_color=get_color('bg_hover'),
            font=ctk.CTkFont(size=10),
            command=self.on_format_changed
        )
        self.format_combo.pack(fill="x", pady=(4, 0))
        
        self.format_info = ctk.CTkLabel(
            format_section,
            text="item:ID:... format",
            font=ctk.CTkFont(size=9),
            text_color=get_color('text_gray')
        )
        self.format_info.pack(anchor="w", pady=(2, 0))
        
        # Bind Type Filter Section
        bind_frame = ctk.CTkFrame(server_section, fg_color="transparent")
        bind_frame.pack(fill="x", pady=(8, 0))
        
        ctk.CTkLabel(
            bind_frame,
            text="🔗 Bind Filter",
            font=ctk.CTkFont(size=11),
            text_color=get_color('text_light')
        ).pack(anchor="w")
        
        self.bind_combo = ctk.CTkComboBox(
            bind_frame,
            variable=self.bind_filter_var,
            values=list(self.BIND_FILTER_OPTIONS.keys()),
            height=26,
            corner_radius=6,
            fg_color=get_color('bg_light'),
            border_color=get_color('border_dark'),
            button_color=get_color('accent_primary_dark'),
            button_hover_color=get_color('accent_primary'),
            dropdown_fg_color=get_color('bg_medium'),
            dropdown_hover_color=get_color('bg_hover'),
            font=ctk.CTkFont(size=10),
            command=self.on_bind_filter_changed
        )
        self.bind_combo.pack(fill="x", pady=(4, 0))
        
        self.bind_info = ctk.CTkLabel(
            bind_frame,
            text="No filter - scrape all items",
            font=ctk.CTkFont(size=9),
            text_color=get_color('text_gray')
        )
        self.bind_info.pack(anchor="w", pady=(2, 0))
        
        # Manual Item IDs Section
        manual_frame = ctk.CTkFrame(server_section, fg_color="transparent")
        manual_frame.pack(fill="x", pady=(12, 0))
        
        ctk.CTkLabel(
            manual_frame,
            text="📝 Manual Item IDs",
            font=ctk.CTkFont(size=11),
            text_color=get_color('text_light')
        ).pack(anchor="w")
        
        entry_row = ctk.CTkFrame(manual_frame, fg_color="transparent")
        entry_row.pack(fill="x", pady=(4, 0))
        
        self.manual_id_entry = ctk.CTkEntry(
            entry_row,
            placeholder_text="Enter Item ID",
            height=26,
            corner_radius=6,
            fg_color=get_color('bg_light'),
            border_color=get_color('border_dark'),
            font=ctk.CTkFont(size=10)
        )
        self.manual_id_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.manual_id_entry.bind("<Return>", lambda e: self.add_manual_id())
        
        self.add_id_btn = ctk.CTkButton(
            entry_row,
            text="+ Add",
            width=50,
            height=26,
            corner_radius=6,
            font=ctk.CTkFont(size=10),
            fg_color=get_color('accent_primary'),
            hover_color=get_color('accent_primary_dark'),
            command=self.add_manual_id
        )
        self.add_id_btn.pack(side="right")
        
        btn_row = ctk.CTkFrame(manual_frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=(4, 0))
        
        ctk.CTkButton(
            btn_row,
            text="📋 Paste List",
            width=80,
            height=24,
            corner_radius=4,
            font=ctk.CTkFont(size=9),
            fg_color=get_color('bg_light'),
            hover_color=get_color('bg_hover'),
            command=self.paste_id_list
        ).pack(side="left", padx=(0, 4))
        
        self.remove_mode_cb = ctk.CTkCheckBox(
            btn_row,
            text="Remove Mode",
            variable=self.remove_mode_var,
            font=ctk.CTkFont(size=9),
            fg_color=get_color('color_error'),
            hover_color=get_color('color_error'),
            text_color=get_color('text_light'),
            corner_radius=4,
            height=20,
            command=self.update_manual_id_ui
        )
        self.remove_mode_cb.pack(side="left")
        
        self.manual_status = ctk.CTkLabel(
            manual_frame,
            text="Added: 0  |  Removed: 0",
            font=ctk.CTkFont(size=9),
            text_color=get_color('text_gray')
        )
        self.manual_status.pack(anchor="w", pady=(2, 0))
        
        # Separator
        ctk.CTkFrame(sidebar, height=2, fg_color=get_color('border_dark')).pack(fill="x", padx=12, pady=8)
        
        # TSM File Section
        file_section = ctk.CTkFrame(sidebar, fg_color="transparent")
        file_section.pack(fill="x", padx=12, pady=(0, 8))
        
        header_row = ctk.CTkFrame(file_section, fg_color="transparent")
        header_row.pack(fill="x")
        
        ctk.CTkButton(
            header_row,
            text="📁",
            width=24,
            height=24,
            corner_radius=4,
            fg_color="transparent",
            hover_color=get_color('bg_hover'),
            command=self.open_tsm_folder
        ).pack(side="left")
        
        ctk.CTkLabel(
            header_row,
            text="TSM SavedVariables",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=get_color('accent_primary')
        ).pack(side="left", padx=(4, 0))
        
        profile_frame = ctk.CTkFrame(file_section, fg_color="transparent")
        profile_frame.pack(fill="x", pady=(6, 0))
        
        self.profile_var = ctk.StringVar(value=Path(self.tsm_path).name if Path(self.tsm_path).exists() else "Select profile...")
        self.profile_combo = ctk.CTkComboBox(
            profile_frame,
            variable=self.profile_var,
            values=self.get_profile_names(),
            height=28,
            corner_radius=6,
            fg_color=get_color('bg_light'),
            border_color=get_color('border_dark'),
            button_color=get_color('accent_primary_dark'),
            button_hover_color=get_color('accent_primary'),
            dropdown_fg_color=get_color('bg_medium'),
            dropdown_hover_color=get_color('bg_hover'),
            font=ctk.CTkFont(size=10),
            command=self.on_profile_changed
        )
        self.profile_combo.pack(side="left", fill="x", expand=True)
        
        ctk.CTkButton(
            profile_frame, text="...", width=32, height=28,
            corner_radius=6,
            fg_color=get_color('bg_light'),
            hover_color=get_color('bg_hover'),
            command=self.browse_tsm_file
        ).pack(side="right", padx=(2, 0))
        
        ctk.CTkButton(
            profile_frame, text="🔄", width=28, height=28,
            corner_radius=6,
            fg_color="transparent",
            hover_color=get_color('accent_primary'),
            command=self.refresh_tsm_file
        ).pack(side="right", padx=(2, 0))
        
        ctk.CTkButton(
            profile_frame, text="🗑️", width=28, height=28,
            corner_radius=6,
            fg_color="transparent",
            hover_color=get_color('color_error'),
            command=self.remove_current_profile
        ).pack(side="right", padx=(2, 0))
        
        self.tsm_info = ctk.CTkLabel(
            file_section,
            text="Loading...",
            font=ctk.CTkFont(size=10),
            text_color=get_color('text_gray')
        )
        self.tsm_info.pack(anchor="w", pady=(4, 0))
        
        # Scrape button at bottom
        action_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        action_frame.pack(fill="x", padx=12, pady=12, side="bottom")
        
        self.scrape_btn = ctk.CTkButton(
            action_frame,
            text="🔍 Scrape Items",
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=get_color('accent_primary_dark'),
            hover_color=get_color('accent_primary'),
            command=self.start_scrape
        )
        self.scrape_btn.pack(fill="x")
        
        return wrapper
    
    def create_categories_panel_paned(self):
        """Create resizable categories panel for PanedWindow."""
        import tkinter as tk
        
        wrapper = tk.Frame(self.paned, bg=get_color('bg_medium'))
        
        panel = ctk.CTkFrame(wrapper, fg_color=get_color('bg_medium'), corner_radius=0)
        panel.pack(fill="both", expand=True)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)
        
        # Categories header
        cat_header = ctk.CTkFrame(panel, fg_color="transparent")
        cat_header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 8))
        
        ctk.CTkLabel(
            cat_header,
            text="📋 Scrape Categories",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=get_color('accent_primary')
        ).pack(side="left")
        
        quick_frame = ctk.CTkFrame(cat_header, fg_color="transparent")
        quick_frame.pack(side="right")
        
        ctk.CTkButton(
            quick_frame, text="All", width=28, height=18,
            corner_radius=4, font=ctk.CTkFont(size=9),
            fg_color=get_color('bg_light'),
            hover_color=get_color('bg_hover'),
            command=self.select_all
        ).pack(side="left", padx=1)
        
        ctk.CTkButton(
            quick_frame, text="None", width=32, height=18,
            corner_radius=4, font=ctk.CTkFont(size=9),
            fg_color=get_color('bg_light'),
            hover_color=get_color('bg_hover'),
            command=self.deselect_all
        ).pack(side="left", padx=1)
        
        # Scrollable category list
        self.cat_scroll = ctk.CTkScrollableFrame(
            panel,
            fg_color=get_color('bg_light'),
            corner_radius=8
        )
        self.cat_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        self.create_category_list()
        self.bind_mousewheel_to_scrollable(self.cat_scroll)
        
        return wrapper
    
    def create_center_panel_paned(self):
        """Create resizable center panel for PanedWindow."""
        import tkinter as tk
        
        wrapper = tk.Frame(self.paned, bg=get_color('bg_medium'))
        
        center = ctk.CTkFrame(wrapper, fg_color=get_color('bg_medium'), corner_radius=0)
        center.pack(fill="both", expand=True)
        center.grid_columnconfigure(0, weight=1)
        center.grid_rowconfigure(1, weight=1)
        center.grid_rowconfigure(3, weight=0)
        
        # Results header
        header = ctk.CTkFrame(center, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 5))
        
        ctk.CTkLabel(
            header,
            text="📊 Scrape Results",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=get_color('accent_primary')
        ).pack(side="left")
        
        self.results_summary = ctk.CTkLabel(
            header,
            text="Select categories and click Scrape",
            font=ctk.CTkFont(size=10),
            text_color=get_color('text_gray')
        )
        self.results_summary.pack(side="right")
        
        # Results display
        self.results_scroll = ctk.CTkScrollableFrame(
            center,
            corner_radius=6,
            fg_color=get_color('bg_light'),
            height=150
        )
        self.results_scroll.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 8))
        self.results_checkboxes: Dict[str, ctk.BooleanVar] = {}
        self.bind_mousewheel_to_scrollable(self.results_scroll)
        
        # Log header
        log_header = ctk.CTkFrame(center, fg_color="transparent")
        log_header.grid(row=2, column=0, sticky="ew", padx=15, pady=(5, 3))
        
        ctk.CTkLabel(
            log_header,
            text="📜 Log",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=get_color('text_gray')
        ).pack(side="left")
        
        ctk.CTkButton(
            log_header,
            text="📁",
            width=24,
            height=20,
            corner_radius=4,
            fg_color="transparent",
            hover_color=get_color('bg_hover'),
            command=self.open_log_folder
        ).pack(side="left", padx=(6, 0))
        
        ctk.CTkButton(
            log_header,
            text="📋",
            width=24,
            height=20,
            corner_radius=4,
            fg_color="transparent",
            hover_color=get_color('bg_hover'),
            command=self.copy_log_to_clipboard
        ).pack(side="left", padx=(2, 0))
        
        # Log text
        self.log_text = ctk.CTkTextbox(
            center,
            height=80,
            corner_radius=6,
            fg_color=get_color('bg_darkest'),
            text_color=get_color('text_gray'),
            font=ctk.CTkFont(family="Consolas", size=9)
        )
        self.log_text.grid(row=3, column=0, sticky="ew", padx=15, pady=(0, 10))
        self.log_text.configure(state="disabled")
        
        # Progress bar
        self.progress = ctk.CTkProgressBar(
            center,
            height=4,
            corner_radius=2,
            fg_color=get_color('bg_dark'),
            progress_color=get_color('accent_primary')
        )
        self.progress.set(0)
        
        return wrapper
    
    def create_right_sidebar_paned(self):
        """Create resizable right sidebar for PanedWindow."""
        import tkinter as tk
        
        wrapper = tk.Frame(self.paned, bg=get_color('bg_medium'))
        
        sidebar = ctk.CTkFrame(wrapper, fg_color=get_color('bg_medium'), corner_radius=0)
        sidebar.pack(fill="both", expand=True)
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(3, weight=1)
        
        # Header
        header = ctk.CTkFrame(sidebar, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        
        ctk.CTkLabel(
            header,
            text="📁 Import Target Group",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=get_color('accent_primary')
        ).pack(side="left")
        
        self.groups_count_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=9),
            text_color=get_color('text_gray')
        )
        self.groups_count_label.pack(side="right")
        
        # Expand/Collapse buttons row
        expand_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        expand_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 4))
        
        ctk.CTkButton(
            expand_frame,
            text="▼ Expand All",
            width=80,
            height=22,
            corner_radius=4,
            font=ctk.CTkFont(size=9),
            fg_color=get_color('bg_dark'),
            hover_color=get_color('bg_hover'),
            command=self.expand_all_groups
        ).pack(side="left", padx=(0, 4))
        
        ctk.CTkButton(
            expand_frame,
            text="▶ Collapse All",
            width=80,
            height=22,
            corner_radius=4,
            font=ctk.CTkFont(size=9),
            fg_color=get_color('bg_dark'),
            hover_color=get_color('bg_hover'),
            command=self.collapse_all_groups
        ).pack(side="left")
        
        # Instructions
        ctk.CTkLabel(
            sidebar,
            text="Click a group to select it as import target:",
            font=ctk.CTkFont(size=9),
            text_color=get_color('text_gray')
        ).grid(row=2, column=0, sticky="w", padx=12, pady=(0, 4))
        
        # Groups list
        self.groups_scroll = ctk.CTkScrollableFrame(
            sidebar,
            fg_color=get_color('bg_light'),
            corner_radius=8
        )
        self.groups_scroll.grid(row=3, column=0, sticky="nsew", padx=12, pady=(0, 8))
        self.bind_mousewheel_to_scrollable(self.groups_scroll)
        
        # Selected group display
        selected_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        selected_frame.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 8))
        
        ctk.CTkLabel(
            selected_frame,
            text="Selected:",
            font=ctk.CTkFont(size=10),
            text_color=get_color('text_gray')
        ).pack(anchor="w")
        
        self.selected_group_var = ctk.StringVar(value="(Use default from scraper)")
        self.selected_group_label = ctk.CTkLabel(
            selected_frame,
            textvariable=self.selected_group_var,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=get_color('accent_secondary'),
            wraplength=230
        )
        self.selected_group_label.pack(anchor="w")
        
        # Import button
        action_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        action_frame.grid(row=5, column=0, sticky="ew", padx=12, pady=12)
        
        self.import_btn = ctk.CTkButton(
            action_frame,
            text="📥 Import to TSM",
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=get_color('accent_secondary_dark'),
            hover_color=get_color('accent_secondary'),
            text_color=get_color('bg_dark'),
            command=self.start_import,
            state="disabled"
        )
        self.import_btn.pack(fill="x")
        
        self.create_groups_btn = ctk.CTkButton(
            action_frame,
            text="✨ Create Default Groups",
            height=32,
            corner_radius=8,
            font=ctk.CTkFont(size=11),
            fg_color=get_color('bg_dark'),
            hover_color=get_color('bg_light'),
            text_color=get_color('text_light'),
            border_width=1,
            border_color=get_color('accent_primary'),
            command=self.create_default_groups
        )
        self.create_groups_btn.pack(fill="x", pady=(8, 0))
        
        return wrapper
    
    def refresh_groups_panel(self):
        """Refresh the TSM groups display in the right sidebar - optimized."""
        # Use after_idle to prevent UI blocking during refresh
        self.after_idle(self._do_refresh_groups_panel)

    def _do_refresh_groups_panel(self):
        """Internal method to refresh groups panel."""
        # Clear existing widgets
        for widget in self.groups_scroll.winfo_children():
            widget.destroy()

        # Reset group button registry and item checkboxes
        self.group_buttons_registry = {}
        self.group_item_checkboxes = {}

        try:
            parser = TSMLuaParser(self.tsm_path)
            if not parser.load():
                ctk.CTkLabel(
                    self.groups_scroll,
                    text="Load TSM file first",
                    font=ctk.CTkFont(size=10),
                    text_color=get_color('text_gray')
                ).pack(anchor="w", padx=5, pady=2)
                return
            
            parser.parse_items()
            parser.parse_groups()
            
            # Store parser for item operations
            self.current_parser = parser
            
            # Get hierarchy
            hierarchy = parser.get_group_hierarchy()
            
            # Count items per group
            group_item_counts = {}
            for group in parser.groups:
                count = len(parser.get_items_by_group(group))
                group_item_counts[group] = count
            
            # Display groups hierarchically as clickable buttons
            def add_group_button(group_path: str, indent: int = 0):
                parts = group_path.split('`')
                display_name = parts[-1] if parts else group_path
                item_count = group_item_counts.get(group_path, 0)
                count_str = f" ({item_count})" if item_count > 0 else ""
                
                # Check if group is expanded
                is_expanded = self.group_expand_state.get(group_path, False)
                
                # Visual hierarchy with icons and indentation
                if indent == 0:
                    font_size = 12
                    font_weight = "bold"
                    text_color = get_color('text_light')
                    height = 28
                    bg_color = get_color('bg_dark')
                    left_pad = 2
                elif indent == 1:
                    font_size = 11
                    font_weight = "bold"
                    text_color = get_color('text_light')
                    height = 26
                    bg_color = "transparent"
                    left_pad = 20
                elif indent == 2:
                    font_size = 10
                    font_weight = "normal"
                    text_color = get_color('text_light') if item_count > 0 else get_color('text_gray')
                    height = 22
                    bg_color = "transparent"
                    left_pad = 40
                else:
                    font_size = 9
                    font_weight = "normal"
                    text_color = get_color('text_gray')
                    height = 20
                    bg_color = "transparent"
                    left_pad = 40 + 20 * (indent - 2)
                
                # Check if group has children
                has_children = len(hierarchy.get(group_path, [])) > 0
                has_items = item_count > 0
                can_expand = has_items or has_children

                # Expand/collapse icon
                expand_icon = "▼" if is_expanded else "▶"
                prefix = f"{expand_icon} " if can_expand else "  "
                
                text = f"{prefix}{display_name}{count_str}"
                
                # Create group row frame
                row_frame = ctk.CTkFrame(self.groups_scroll, fg_color="transparent")
                row_frame.pack(anchor="w", fill="x", padx=(left_pad, 2), pady=1)
                
                # Check if this group is in multi-selection
                is_selected = group_path in self.selected_groups
                if is_selected:
                    bg_color = get_color('accent_primary_dark')
                
                btn = ctk.CTkButton(
                    row_frame,
                    text=text,
                    font=ctk.CTkFont(size=font_size, weight=font_weight),
                    text_color=text_color,
                    fg_color=bg_color,
                    hover_color=get_color('bg_hover'),
                    anchor="w",
                    height=height,
                    command=lambda g=group_path: self.on_group_click(g)
                )
                btn.pack(anchor="w", fill="x", expand=True)

                # Bind double-click to toggle expand/collapse
                if can_expand:
                    btn.bind("<Double-Button-1>", lambda e, g=group_path: (e.widget.focus_set(), self.toggle_group_expand(g)))

                # Bind Ctrl+click for multi-selection
                btn.bind("<Control-Button-1>", lambda e, g=group_path: self.toggle_group_selection_multi(g))

                # Bind right-click for context menu
                btn.bind("<Button-3>", lambda e, g=group_path: self.show_group_context_menu(e, g))
                
                # Register button for highlighting
                self.group_buttons_registry[group_path] = btn
                
                # Show items if expanded
                if is_expanded and has_items:
                    items = parser.get_items_by_group(group_path)
                    items_frame = ctk.CTkFrame(self.groups_scroll, fg_color=get_color('bg_medium'))
                    items_frame.pack(anchor="w", fill="x", padx=(left_pad + 20, 2), pady=(0, 4))
                    
                    for item_key in sorted(items)[:50]:  # Limit to 50 items per group
                        item_id = parser.get_item_id(item_key)
                        display_id = f"Item {item_id}" if item_id else item_key
                        
                        item_row = ctk.CTkFrame(items_frame, fg_color="transparent")
                        item_row.pack(anchor="w", fill="x")
                        
                        # Checkbox for item selection (for remove mode)
                        checkbox_key = f"{group_path}|{item_key}"
                        self.group_item_checkboxes[checkbox_key] = ctk.BooleanVar(value=False)
                        
                        cb = ctk.CTkCheckBox(
                            item_row,
                            text=display_id,
                            variable=self.group_item_checkboxes[checkbox_key],
                            font=ctk.CTkFont(size=9),
                            text_color=get_color('text_gray'),
                            fg_color=get_color('accent_primary'),
                            hover_color=get_color('accent_primary_dark'),
                            height=18,
                            checkbox_width=14,
                            checkbox_height=14
                        )
                        cb.pack(anchor="w", padx=4, pady=1)
                    
                    if len(items) > 50:
                        ctk.CTkLabel(
                            items_frame,
                            text=f"... and {len(items) - 50} more items",
                            font=ctk.CTkFont(size=8),
                            text_color=get_color('text_gray')
                        ).pack(anchor="w", padx=4)
                
                # Add children only if expanded (case-insensitive alphabetical order)
                if is_expanded:
                    children = hierarchy.get(group_path, [])
                    for child in sorted(children, key=lambda x: x.lower()):
                        if child != group_path:
                            add_group_button(child, indent + 1)
            
            # Start with root groups (case-insensitive alphabetical order)
            root_groups = sorted(hierarchy.get('', []), key=lambda x: x.lower())
            for root in root_groups:
                add_group_button(root, 0)
            
            total_groups = len(parser.groups)
            self.groups_count_label.configure(text=f"{total_groups} groups")
            
        except Exception as e:
            ctk.CTkLabel(
                self.groups_scroll,
                text=f"Error: {e}",
                font=ctk.CTkFont(size=10),
                text_color=get_color('color_error')
            ).pack(anchor="w", padx=5, pady=2)
    
    def on_group_click(self, group_path: str):
        """Handle click on a group - just select it. Double-click to expand/collapse."""
        self.select_import_group(group_path)
    
    def toggle_group_expand(self, group_path: str):
        """Toggle the expand/collapse state of a group."""
        current_state = self.group_expand_state.get(group_path, False)
        self.group_expand_state[group_path] = not current_state
        self.refresh_groups_panel()
    
    def expand_all_groups(self):
        """Expand all groups to show their items."""
        if not hasattr(self, 'current_parser'):
            return
        for group in self.current_parser.groups:
            if len(self.current_parser.get_items_by_group(group)) > 0:
                self.group_expand_state[group] = True
        self.refresh_groups_panel()
        self.log("Expanded all groups", 'info')
    
    def collapse_all_groups(self):
        """Collapse all groups to hide their items."""
        self.group_expand_state.clear()
        self.refresh_groups_panel()
        self.log("Collapsed all groups", 'info')
    
    def toggle_group_selection_multi(self, group_path: str):
        """Toggle group selection for Ctrl+click multi-selection."""
        if group_path in self.selected_groups:
            self.selected_groups.remove(group_path)
        else:
            self.selected_groups.add(group_path)
        self.refresh_groups_panel()
        self.log(f"Selected {len(self.selected_groups)} group(s)", 'info')
    
    def clear_group_selection(self):
        """Clear all selected groups."""
        self.selected_groups.clear()
        self.refresh_groups_panel()
    
    def select_import_group(self, group_path: str):
        """Select a TSM group as the import target with visual highlighting."""
        # Update the selected group variable
        self.selected_group_var.set(group_path)
        self.log(f"Import target set to: {group_path}", 'cyan')
        
        # Highlight the selected button, unhighlight others
        self.highlight_group_button(group_path)
    
    def highlight_group_button(self, group_path: str):
        """Highlight the selected group button and unhighlight others."""
        if not hasattr(self, 'group_buttons_registry'):
            return
        
        for path, btn in self.group_buttons_registry.items():
            try:
                if path == group_path:
                    # Highlight selected
                    btn.configure(
                        fg_color=get_color('accent_primary_dark'),
                        text_color=get_color('text_white')
                    )
                    # Scroll to show this button
                    self.scroll_to_group_button(btn)
                else:
                    # Reset to normal
                    btn.configure(
                        fg_color="transparent",
                        text_color=get_color('text_light')
                    )
            except:
                pass  # Button may have been destroyed
    
    def scroll_to_group_button(self, button):
        """Scroll the groups panel to show the specified button."""
        try:
            # Find button index in registry
            buttons_list = list(self.group_buttons_registry.values())
            if button not in buttons_list:
                return
            
            btn_index = buttons_list.index(button)
            total_buttons = len(buttons_list)
            
            if total_buttons <= 1:
                return
            
            # Calculate approximate scroll position
            # We want the button to appear in the upper third of the view
            position = max(0, (btn_index - 2)) / max(1, total_buttons - 1)
            position = min(1.0, position)
            
            # Try to scroll using the internal canvas
            self.update_idletasks()
            
            # CTkScrollableFrame internal structure
            if hasattr(self.groups_scroll, '_parent_canvas'):
                self.groups_scroll._parent_canvas.yview_moveto(position)
            elif hasattr(self.groups_scroll, 'yview_moveto'):
                self.groups_scroll.yview_moveto(position)
            else:
                # Look for canvas child
                for widget in self.groups_scroll.winfo_children():
                    if hasattr(widget, 'yview_moveto'):
                        widget.yview_moveto(position)
                        break
        except Exception:
            pass  # Scrolling is optional
    
    def show_group_context_menu(self, event, group_path: str):
        """Show right-click context menu for a group."""
        import tkinter as tk
        
        menu = tk.Menu(self, tearoff=0, bg=get_color('bg_medium'), fg=get_color('text_light'),
                       activebackground=get_color('accent_primary'), activeforeground=get_color('text_white'))
        
        menu.add_command(label="📝 Rename Group", command=lambda: self.rename_group_dialog(group_path))
        menu.add_command(label="➕ Add Sub-Group", command=lambda: self.add_subgroup_dialog(group_path))
        menu.add_command(label="📦 Move Group", command=lambda: self.move_group_dialog(group_path))
        menu.add_separator()
        menu.add_command(label="🗑️ Delete Group", command=lambda: self.delete_group_dialog(group_path))
        
        # If multiple groups selected, show bulk options
        if self.selected_groups:
            menu.add_separator()
            menu.add_command(
                label=f"🗑️ Delete Selected ({len(self.selected_groups)})",
                command=self.delete_selected_groups
            )
            menu.add_command(
                label=f"📦 Move Selected ({len(self.selected_groups)})",
                command=self.move_selected_groups_dialog
            )
            menu.add_command(label="✖️ Clear Selection", command=self.clear_group_selection)
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def rename_group_dialog(self, group_path: str):
        """Show dialog to rename a group."""
        parts = group_path.split('`')
        current_name = parts[-1] if parts else group_path
        
        dialog = ctk.CTkInputDialog(
            text=f"Rename '{current_name}' to:",
            title="Rename Group"
        )
        new_name = dialog.get_input()
        
        if not new_name or new_name == current_name:
            return
        
        # Build new path
        if len(parts) > 1:
            new_path = '`'.join(parts[:-1]) + '`' + new_name
        else:
            new_path = new_name
        
        try:
            from tsm_scraper.lua_writer import TSMLuaWriter
            writer = TSMLuaWriter(self.tsm_path)
            result = writer.rename_group(group_path, new_path)
            
            if result['errors']:
                self.log(f"Error: {result['errors'][0]}", 'error')
                return
            
            self.log(f"Renamed '{current_name}' to '{new_name}' ({result.get('groups_updated', result.get('items_updated', 0))} references updated)", 'success')
            self.refresh_groups_panel()
            
        except Exception as e:
            self.log(f"Rename failed: {e}", 'error')
    
    
    def add_subgroup_dialog(self, parent_path: str):
        """Show dialog to add a sub-group."""
        dialog = ctk.CTkInputDialog(
            text=f"New sub-group name under '{parent_path.split('`')[-1]}':",
            title="Add Sub-Group"
        )
        new_name = dialog.get_input()
        
        if not new_name:
            return
        
        new_path = f"{parent_path}`{new_name}"
        
        try:
            from tsm_scraper.lua_writer import TSMLuaWriter
            writer = TSMLuaWriter(self.tsm_path)
            result = writer.add_groups([new_path])
            
            if result['errors']:
                self.log(f"Error: {result['errors'][0]}", 'error')
                return
            
            if result['added'] > 0:
                self.log(f"Created group: {new_path}", 'success')
                self.refresh_groups_panel()
            else:
                self.log(f"Group already exists: {new_path}", 'warning')
                
        except Exception as e:
            self.log(f"Failed to add group: {e}", 'error')
    
    def delete_group_dialog(self, group_path: str):
        """Show confirmation dialog to delete a group."""
        parts = group_path.split('`')
        group_name = parts[-1] if parts else group_path
        
        # First confirmation - delete group and items
        if not themed_askquestion(
            self,
            "🗑️ Delete Group",
            f"Delete '{group_name}'?\n\n"
            "This will remove the group, all its sub-groups,\n"
            "and ALL ITEMS in those groups.\n\n"
            "A backup will be created before deletion."
        ):
            return
        
        # Ask if they want to keep the items instead
        keep_items = themed_askquestion(
            self,
            "Keep Items?",
            "Do you want to KEEP the items?\n\n"
            "• Yes = Items become uncategorized (not deleted)\n"
            "• No = Items are removed from TSM entirely"
        )
        
        try:
            from tsm_scraper.lua_writer import TSMLuaWriter
            writer = TSMLuaWriter(self.tsm_path)
            result = writer.delete_group(group_path, delete_items=not keep_items)
            
            if result['errors']:
                self.log(f"Error: {result['errors'][0]}", 'error')
                return
            
            msg = f"Deleted '{group_name}'"
            if result['subgroups_removed'] > 0:
                msg += f" (+{result['subgroups_removed']} sub-groups)"
            if result.get('items_removed', 0) > 0:
                msg += f" - {result['items_removed']} items removed"
            elif keep_items:
                msg += " - items kept"
            self.log(msg, 'success')
            self.refresh_groups_panel()
            
        except Exception as e:
            self.log(f"Delete failed: {e}", 'error')
    
    def move_group_dialog(self, group_path: str):
        """Show dialog to move a group to a new parent."""
        parts = group_path.split('`')
        group_name = parts[-1] if parts else group_path
        
        # Get list of all groups as potential targets
        target_groups = ["(Root - Top Level)"]
        if hasattr(self, 'current_parser') and self.current_parser:
            target_groups.extend(sorted(self.current_parser.groups, key=lambda x: x.lower()))
        
        # Show selection dialog
        dialog = ctk.CTkInputDialog(
            text=f"Move '{group_name}' to which parent group?\n\nEnter the full group path (e.g., 'Armor`Cloth')\nor leave empty for root level:",
            title="Move Group"
        )
        new_parent = dialog.get_input()
        
        if new_parent is None:  # Cancelled
            return
        
        new_parent = new_parent.strip()
        
        # Construct new path
        if new_parent:
            new_path = f"{new_parent}`{group_name}"
        else:
            new_path = group_name
        
        if new_path == group_path:
            self.log("Group is already in that location", 'warning')
            return
        
        try:
            writer = TSMLuaWriter(self.tsm_path)
            result = writer.rename_group(group_path, new_path)
            
            if result['errors']:
                self.log(f"Move failed: {result['errors'][0]}", 'error')
                return
            
            self.log(f"Moved '{group_name}' to '{new_path}'", 'success')
            self.refresh_groups_panel()
            
        except Exception as e:
            self.log(f"Move failed: {e}", 'error')
    
    def move_selected_groups_dialog(self):
        """Move all selected groups to a new parent."""
        if not self.selected_groups:
            self.log("No groups selected", 'warning')
            return
        
        dialog = ctk.CTkInputDialog(
            text=f"Move {len(self.selected_groups)} selected groups to which parent?\n\nEnter the full group path (e.g., 'Armor`Cloth')\nor leave empty for root level:",
            title="Move Selected Groups"
        )
        new_parent = dialog.get_input()
        
        if new_parent is None:  # Cancelled
            return
        
        new_parent = new_parent.strip()
        
        try:
            writer = TSMLuaWriter(self.tsm_path)
            moved_count = 0
            
            for group_path in list(self.selected_groups):
                parts = group_path.split('`')
                group_name = parts[-1] if parts else group_path
                
                if new_parent:
                    new_path = f"{new_parent}`{group_name}"
                else:
                    new_path = group_name
                
                if new_path != group_path:
                    result = writer.rename_group(group_path, new_path)
                    if not result['errors']:
                        moved_count += 1
            
            self.log(f"Moved {moved_count} group(s)", 'success')
            self.selected_groups.clear()
            self.refresh_groups_panel()
            
        except Exception as e:
            self.log(f"Move failed: {e}", 'error')
    
    def delete_selected_groups(self):
        """Delete all selected groups."""
        if not self.selected_groups:
            self.log("No groups selected", 'warning')
            return
        
        if not themed_askquestion(
            self,
            "🗑️ Delete Selected Groups",
            f"Delete {len(self.selected_groups)} selected group(s)?\n\nThis will remove groups, sub-groups, and items.\nA backup will be created."
        ):
            return
        
        keep_items = themed_askquestion(
            self,
            "Keep Items?",
            "Keep items (make uncategorized) or delete them?\n\n• Yes = Keep items\n• No = Delete items"
        )
        
        try:
            writer = TSMLuaWriter(self.tsm_path)
            deleted_count = 0
            
            for group_path in list(self.selected_groups):
                result = writer.delete_group(group_path, delete_items=not keep_items)
                if not result['errors']:
                    deleted_count += 1
            
            self.log(f"Deleted {deleted_count} group(s)", 'success')
            self.selected_groups.clear()
            self.refresh_groups_panel()
            
        except Exception as e:
            self.log(f"Delete failed: {e}", 'error')
    
    def auto_select_scrape_group(self):
        """Auto-select the most relevant TSM group based on scrape results."""
        if not self.scrape_results:
            return
        
        # Count which groups have items (use found count, not just new)
        group_counts = {}
        for cat_name, data in self.scrape_results.items():
            tsm_group = data.get('tsm_group', '')
            found_count = data.get('found', 0)
            if found_count > 0 and tsm_group:
                group_counts[tsm_group] = group_counts.get(tsm_group, 0) + found_count
        
        if not group_counts:
            return
        
        # Find the group with most items
        best_group = max(group_counts, key=group_counts.get)
        
        # Find if there's a common parent group
        # e.g., if we scraped multiple weapon types, select "Weapons" parent
        unique_groups = list(group_counts.keys())
        if len(unique_groups) > 1:
            # Check for common parent
            parents = [g.rsplit('`', 1)[0] if '`' in g else '' for g in unique_groups]
            common_parent = parents[0] if len(set(parents)) == 1 and parents[0] else None
            if common_parent and common_parent in self.group_buttons_registry:
                best_group = common_parent
        
        # Select and highlight the group (if it exists in the registry)
        # Check if the group actually EXISTS in the file (using parser groups)
        parser_groups = getattr(self, 'existing_groups', set())
        if not parser_groups and hasattr(self, 'current_parser'):
            parser_groups = set(self.current_parser.groups)
            
        group_exists = best_group in parser_groups
        
        if group_exists:
            self.select_import_group(best_group)
            self.log(f"Auto-selected group: {best_group}", 'cyan')
        else:
            # Group doesn't exist yet, just set it as selected (will be created on import)
            self.selected_group_var.set(best_group)
            self.log(f"Target group (will be created): {best_group}", 'cyan')
    
    def get_user_groups_list(self) -> list:
        """Get list of user's existing TSM groups for dropdown selection."""
        try:
            parser = TSMLuaParser(self.tsm_path)
            if not parser.load():
                return []
            parser.parse_groups()
            return sorted(parser.groups)
        except Exception:
            return []
    
    def on_server_changed(self, selection: str):
        """Handle server/database selection change."""
        server_info = {
            "Wowhead (Retail)": {"url": "www.wowhead.com", "version": "retail"},
            "Wowhead (WotLK)": {"url": "wowhead.com/wotlk", "version": "wotlk"},
            "Wowhead (TBC)": {"url": "wowhead.com/tbc", "version": "tbc"},
            "Wowhead (Classic Era)": {"url": "classic.wowhead.com", "version": "classic"},
            "Wowhead (Cata)": {"url": "wowhead.com/cata", "version": "cata"},
            "Wowhead (MoP Classic)": {"url": "wowhead.com/mop-classic", "version": "mop"},
        }
        
        info = server_info.get(selection, {"url": "www.wowhead.com", "version": "retail"})
        self.log(f"Server changed to: {selection} ({info['url']})", 'cyan')
        
        # Store current selection
        self.current_server = selection
        
        # Use Wowhead scraper with appropriate version
        version = info.get('version', 'retail')
        self.scraper = WowheadScraper(game_version=version)
        self.wowhead_scraper = self.scraper  # Keep reference
        self.log(f"Using Wowhead scraper ({version})", 'cyan')
        
        # Update categories for the selected server
        self.update_categories_for_server()
    
    def update_categories_for_server(self):
        """Update available categories based on selected server."""
        # For now, keep the same categories - they're similar across versions
        # In the future, we could load different category sets per server
        pass
    
    def on_format_changed(self, selection: str):
        """Handle TSM format selection change."""
        format_info = {
            "WotLK 3.3.5a": {
                "format": "classic",
                "item_pattern": "item:ID:...",
                "description": "item:ID:... format"
            },
            "Retail (Official TSM)": {
                "format": "retail", 
                "item_pattern": "i:ID",
                "description": "i:ID format"
            },
        }
        
        info = format_info.get(selection, format_info["WotLK 3.3.5a"])
        self.current_tsm_format = info['format']
        
        # Update format info label
        self.format_info.configure(text=info['description'])
        self.log(f"TSM format set to: {selection} ({info['item_pattern']})", 'cyan')
    
    def on_bind_filter_changed(self, selection: str):
        """Handle bind type filter selection change."""
        bind_id, description = self.BIND_FILTER_OPTIONS.get(selection, (None, "No filter"))
        
        # Update info label
        self.bind_info.configure(text=description)
        
        if bind_id is None:
            self.log(f"Bind filter: All items (no filter)", 'cyan')
        else:
            self.log(f"Bind filter set to: {selection}", 'cyan')
    
    def add_manual_id(self):
        """Add or remove an item ID based on remove mode."""
        id_text = self.manual_id_entry.get().strip()
        
        # If remove mode and no ID entered, try to remove selected items from group
        if self.remove_mode_var.get() and not id_text:
            self.remove_selected_items()
            return
        
        if not id_text:
            return
        
        try:
            item_id = int(id_text)
        except ValueError:
            self.log(f"Invalid item ID: {id_text}", 'error')
            return
        
        if self.remove_mode_var.get():
            # Remove mode
            if item_id not in self.manual_remove_ids:
                self.manual_remove_ids.append(item_id)
                self.log(f"Added {item_id} to remove list", 'warning')
        else:
            # Add mode
            if item_id not in self.manual_add_ids:
                self.manual_add_ids.append(item_id)
                self.log(f"Added {item_id} to import list", 'success')
        
        self.manual_id_entry.delete(0, "end")
        self.update_manual_status()
    
    def remove_selected_items(self):
        """Remove selected items from their groups in the TSM file."""
        if not hasattr(self, 'group_item_checkboxes') or not self.group_item_checkboxes:
            self.log("No items selected to remove. Expand a group and check items first.", 'warning')
            return
        
        # Collect selected items by group
        items_to_remove = {}
        for key, var in self.group_item_checkboxes.items():
            if var.get():
                group_path, item_key = key.split('|', 1)
                if group_path not in items_to_remove:
                    items_to_remove[group_path] = []
                items_to_remove[group_path].append(item_key)
        
        if not items_to_remove:
            self.log("No items selected to remove. Check items in expanded groups first.", 'warning')
            return
        
        total_items = sum(len(items) for items in items_to_remove.values())
        
        # Confirm removal
        if not themed_askquestion(
            self,
            "🗑️ Confirm Removal",
            f"Remove {total_items} selected item(s) from their groups?\n\nThis will modify your TSM SavedVariables file."
        ):
            return
        
        try:
            writer = TSMLuaWriter(self.tsm_path)
            
            # Extract item IDs from item keys
            all_item_ids = []
            for group_path, item_keys in items_to_remove.items():
                for item_key in item_keys:
                    # Extract ID from item key (e.g., "item:12345:0:0:0" -> 12345)
                    if hasattr(self, 'current_parser'):
                        item_id = self.current_parser.get_item_id(item_key)
                        if item_id:
                            all_item_ids.append(item_id)
            
            if not all_item_ids:
                self.log("Could not extract item IDs", 'error')
                return
            
            result = writer.remove_items(all_item_ids)
            
            self.log(f"Removed {result['removed']} item(s) from TSM groups", 'success')
            if result['not_found'] > 0:
                self.log(f"{result['not_found']} item(s) not found in file", 'warning')
            
            self.refresh_groups_panel()
            self.load_tsm_info()
            
        except Exception as e:
            self.log(f"Error removing items: {e}", 'error')
    
    def paste_id_list(self):
        """Open dialog to paste multiple item IDs."""
        dialog = ctk.CTkInputDialog(
            text="Paste item IDs (comma or newline separated):",
            title="Paste Item ID List"
        )
        input_text = dialog.get_input()
        
        if not input_text:
            return
        
        # Parse IDs from input (comma, newline, or space separated)
        import re
        id_strings = re.split(r'[,\s\n]+', input_text.strip())
        
        added_count = 0
        for id_str in id_strings:
            id_str = id_str.strip()
            if not id_str:
                continue
            try:
                item_id = int(id_str)
                if self.remove_mode_var.get():
                    if item_id not in self.manual_remove_ids:
                        self.manual_remove_ids.append(item_id)
                        added_count += 1
                else:
                    if item_id not in self.manual_add_ids:
                        self.manual_add_ids.append(item_id)
                        added_count += 1
            except ValueError:
                continue  # Skip invalid IDs
        
        mode = "remove" if self.remove_mode_var.get() else "add"
        self.log(f"Added {added_count} IDs to {mode} list", 'success' if not self.remove_mode_var.get() else 'warning')
        self.update_manual_status()
    
    def update_manual_id_ui(self):
        """Update UI elements based on remove mode state."""
        if self.remove_mode_var.get():
            self.add_id_btn.configure(
                text="- Remove",
                fg_color=get_color('color_error'),
                hover_color=get_color('color_error')
            )
        else:
            self.add_id_btn.configure(
                text="+ Add",
                fg_color=get_color('accent_primary'),
                hover_color=get_color('accent_primary_dark')
            )
    
    def update_manual_status(self):
        """Update the manual IDs status label and enable import button if manual IDs exist."""
        add_count = len(self.manual_add_ids)
        remove_count = len(self.manual_remove_ids)
        self.manual_status.configure(text=f"Added: {add_count}  |  Removed: {remove_count}")
        
        # Enable import button if there are manual IDs to process
        if add_count > 0 or remove_count > 0:
            self.import_btn.configure(state="normal")
    
    def create_category_list(self):
        """Create category checkboxes grouped by type with collapsible sections."""
        groups = {
            "⚔ Weapons": [],
            "👕 Cloth": [],
            "🦎 Leather": [],
            "⛓ Mail": [],
            "🛡 Plate": [],
            "🔰 Other Armor": [],
            "⚗ Consumables": [],
            "📦 Trade Goods": [],
            "📜 Recipes": [],
            "💎 Other": []
        }
        
        for cat_name, (cat_type, subclass, tsm_group) in self.scraper.ALL_CATEGORIES.items():
            if cat_type == "weapon":
                groups["⚔ Weapons"].append((cat_name, tsm_group))
            elif cat_type == "armor":
                # Separate armor by type
                if cat_name.startswith("cloth_"):
                    groups["👕 Cloth"].append((cat_name, tsm_group))
                elif cat_name.startswith("leather_"):
                    groups["🦎 Leather"].append((cat_name, tsm_group))
                elif cat_name.startswith("mail_"):
                    groups["⛓ Mail"].append((cat_name, tsm_group))
                elif cat_name.startswith("plate_"):
                    groups["🛡 Plate"].append((cat_name, tsm_group))
                else:
                    groups["🔰 Other Armor"].append((cat_name, tsm_group))
            elif cat_type == "consumable":
                groups["⚗ Consumables"].append((cat_name, tsm_group))
            elif cat_type == "trade_goods":
                groups["📦 Trade Goods"].append((cat_name, tsm_group))
            elif cat_type == "recipe":
                groups["📜 Recipes"].append((cat_name, tsm_group))
            else:
                groups["💎 Other"].append((cat_name, tsm_group))
        
        # Store group frames for collapse/expand
        self.group_frames: Dict[str, ctk.CTkFrame] = {}
        self.group_expanded: Dict[str, bool] = {}
        self.group_vars: Dict[str, ctk.BooleanVar] = {}  # For group header checkboxes
        self.group_items: Dict[str, List[str]] = {}  # Track items per group
        self.group_collapse_buttons: Dict[str, ctk.CTkButton] = {}  # To update arrow text
        self.group_header_frames: Dict[str, ctk.CTkFrame] = {}  # To position items after header
        
        for group_name, items in groups.items():
            if not items:
                continue
            
            # Store items for this group
            self.group_items[group_name] = [cat_name for cat_name, _ in items]
            
            # Expand/collapse starts expanded
            self.group_expanded[group_name] = True
            
            # Header row with checkbox and collapse button
            header_frame = ctk.CTkFrame(self.cat_scroll, fg_color="transparent")
            header_frame.pack(fill="x", pady=(8, 2), padx=5)
            self.group_header_frames[group_name] = header_frame
            
            # Collapse/expand button (small arrow)
            collapse_btn = ctk.CTkButton(
                header_frame,
                text="▼",
                width=20,
                height=24,
                font=ctk.CTkFont(size=10),
                fg_color="transparent",
                hover_color=get_color('bg_hover'),
                text_color=get_color('text_gray'),
                command=lambda g=group_name: self.toggle_group(g)
            )
            collapse_btn.pack(side="left")
            self.group_collapse_buttons[group_name] = collapse_btn
            
            # Group checkbox (selects all in group)
            group_var = ctk.BooleanVar()
            self.group_vars[group_name] = group_var
            
            group_cb = ctk.CTkCheckBox(
                header_frame,
                text=f"{group_name} ({len(items)})",
                variable=group_var,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=get_color('accent_primary'),
                hover_color=get_color('accent_primary_dark'),
                text_color=get_color('accent_primary'),
                corner_radius=4,
                height=24,
                command=lambda g=group_name: self.toggle_group_selection(g)
            )
            group_cb.pack(side="left", padx=(2, 0))
            
            # Items container (collapsible)
            items_frame = ctk.CTkFrame(self.cat_scroll, fg_color="transparent")
            items_frame.pack(fill="x", padx=5)
            self.group_frames[group_name] = items_frame
            
            # Create checkboxes for this group
            for cat_name, _ in sorted(items):
                var = ctk.BooleanVar()
                self.category_vars[cat_name] = var
                
                display = cat_name.replace('_', ' ').title()
                cb = ctk.CTkCheckBox(
                    items_frame,
                    text=display,
                    variable=var,
                    font=ctk.CTkFont(size=11),
                    fg_color=get_color('accent_primary'),
                    hover_color=get_color('accent_primary_dark'),
                    text_color=get_color('text_light'),
                    corner_radius=4,
                    height=24
                )
                cb.pack(anchor="w", padx=12, pady=1)
    
    def toggle_group_selection(self, group_name: str):
        """Toggle all items in a group when group header checkbox is clicked."""
        if group_name not in self.group_items:
            return
        
        # Get the group checkbox state
        is_selected = self.group_vars[group_name].get()
        
        # Apply to all items in the group
        for cat_name in self.group_items[group_name]:
            if cat_name in self.category_vars:
                self.category_vars[cat_name].set(is_selected)
    
    def toggle_group(self, group_name: str):
        """Toggle the collapse/expand state of a category group."""
        is_expanded = self.group_expanded.get(group_name, True)
        
        if is_expanded:
            # Collapse - hide the items frame
            self.group_frames[group_name].pack_forget()
            # Update button text to show collapsed state
            self.group_collapse_buttons[group_name].configure(text="▶")
        else:
            # Expand - show the items frame after the header
            header = self.group_header_frames.get(group_name)
            if header:
                self.group_frames[group_name].pack(fill="x", padx=5, after=header)
            else:
                self.group_frames[group_name].pack(fill="x", padx=5)
            self.group_collapse_buttons[group_name].configure(text="▼")
        
        self.group_expanded[group_name] = not is_expanded
    
    def log(self, message: str, level: str = 'info'):
        """Add a log message to GUI and log file."""
        self.log_text.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        color_map = {
            'info': get_color('text_gray'),
            'success': get_color('color_success'),
            'warning': get_color('color_warning'),
            'error': get_color('color_error'),
            'cyan': get_color('accent_primary')
        }
        
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        
        # Write to log file
        try:
            LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(LOG_PATH, 'a', encoding='utf-8') as f:
                f.write(f"[{full_timestamp}] [{level.upper()}] {message}\n")
        except:
            pass
    
    def open_log_folder(self):
        """Open the logs folder in file explorer."""
        import subprocess
        import os
        
        try:
            LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            folder = LOG_PATH.parent
            if sys.platform == 'win32':
                os.startfile(str(folder))
            elif sys.platform == 'darwin':
                subprocess.run(['open', str(folder)])
            else:
                subprocess.run(['xdg-open', str(folder)])
        except Exception as e:
            self.log(f"Error opening log folder: {e}", 'error')
    
    def copy_log_to_clipboard(self):
        """Copy the current session log to clipboard."""
        try:
            # Get text from the log textbox (current session only)
            log_content = self.log_text.get("1.0", "end-1c")
            self.clipboard_clear()
            self.clipboard_append(log_content)
            self.log("Log copied to clipboard", 'success')
        except Exception as e:
            self.log(f"Failed to copy log: {e}", 'error')
    
    def load_tsm_info(self):
        """Load TSM file information."""
        try:
            parser = TSMLuaParser(self.tsm_path)
            if parser.load():
                parser.parse_items()
                parser.parse_groups()
                self.existing_ids = parser.get_existing_item_ids()
                self.existing_groups = set(parser.groups)
                
                self.tsm_info.configure(
                    text=f"✓ {len(parser.items):,} items • {len(parser.groups)} groups",
                    text_color=get_color('color_success')
                )
                self.log(f"Loaded: {len(parser.items):,} items, {len(parser.groups)} groups", 'success')
                
                # Refresh the groups panel in sidebar
                self.refresh_groups_panel()
            else:
                self.tsm_info.configure(
                    text="⚠ Could not load file",
                    text_color=get_color('color_error')
                )
                self.log("Failed to load TSM file", 'error')
        except Exception as e:
            self.tsm_info.configure(
                text="⚠ Error",
                text_color=get_color('color_error')
            )
            self.log(f"Error: {e}", 'error')
    
    def browse_tsm_file(self):
        """Browse for TSM file."""
        path = filedialog.askopenfilename(
            title="Select TradeSkillMaster.lua",
            filetypes=[("Lua files", "*.lua"), ("All files", "*.*")],
            initialdir=Path(self.tsm_path).parent
        )
        if path:
            self.tsm_path = path
            self.save_config()
            # Update profile dropdown with new file
            self.profile_combo.configure(values=self.get_profile_names())
            self.profile_var.set(Path(path).name)
            self.load_tsm_info()
            self.refresh_groups_panel()
            self.log(f"Loaded profile: {Path(path).name}", 'success')
    
    def refresh_tsm_file(self):
        """Refresh/reload the current TSM SavedVariables file."""
        if not Path(self.tsm_path).exists():
            self.log("No TSM file loaded to refresh", 'error')
            return
        
        self.log("Refreshing TSM file...", 'info')
        self.load_tsm_info()
        self.refresh_groups_panel()
        self.log(f"Refreshed: {Path(self.tsm_path).name}", 'success')
    
    def select_all(self):
        for v in self.category_vars.values():
            v.set(True)
    
    def deselect_all(self):
        for v in self.category_vars.values():
            v.set(False)
    
    def start_scrape(self):
        """Start scraping selected categories."""
        selected = [c for c, v in self.category_vars.items() if v.get()]
        if not selected:
            themed_showwarning(self, "⚠️ No Selection", "Please select at least one category.")
            return
        
        self.scrape_btn.configure(state="disabled")
        self.import_btn.configure(state="disabled")
        self.scrape_results.clear()
        
        # Clear results
        for widget in self.results_scroll.winfo_children():
            widget.destroy()
        self.results_checkboxes.clear()
        ctk.CTkLabel(
            self.results_scroll,
            text="Scraping...",
            font=ctk.CTkFont(size=10),
            text_color=get_color('text_gray')
        ).pack(anchor="w", padx=10, pady=10)
        
        threading.Thread(target=self.run_scrape, args=(selected,), daemon=True).start()
    
    def run_scrape(self, categories):
        """Run scraping in background."""
        try:
            # Refresh existing IDs
            parser = TSMLuaParser(self.tsm_path)
            if parser.load():
                parser.parse_items()
                self.existing_ids = parser.get_existing_item_ids()
            
            total_found = 0
            total_new = 0
            results_lines = []
            
            for cat_name in categories:
                cat_info = self.scraper.ALL_CATEGORIES.get(cat_name)
                if not cat_info:
                    continue
                
                cat_type, subclass, tsm_group = cat_info
                
                self.log(f"Scraping {cat_name}...", 'cyan')
                self.after(0, lambda c=cat_name: self.status_label.configure(
                    text=f"● Scraping {c}...",
                    text_color=get_color('accent_primary')
                ))
                
                # Check if using WowheadScraper or Ascension-type scraper
                is_wowhead = isinstance(self.scraper, WowheadScraper)
                
                if is_wowhead:
                    # Use unified scrape_by_name method - uses pretty URLs for proper filtering
                    # Get the selected bind filter
                    filter_selection = self.bind_filter_var.get()
                    bind_id, _ = self.BIND_FILTER_OPTIONS.get(filter_selection, (None, ""))
                    items = self.scraper.scrape_by_name(cat_name, bonding_filter=bind_id)
                    item_ids = [item.id for item in items]
                else:
                    # Use Ascension/TurtleWoW scraper methods
                    class_map = {
                        "weapon": self.scraper.CLASS_WEAPON,
                        "armor": self.scraper.CLASS_ARMOR,
                        "consumable": self.scraper.CLASS_CONSUMABLE,
                        "trade_goods": self.scraper.CLASS_TRADE_GOODS,
                        "recipe": self.scraper.CLASS_RECIPE,
                        "gem": self.scraper.CLASS_GEM,
                        "container": self.scraper.CLASS_CONTAINER,
                        "projectile": self.scraper.CLASS_PROJECTILE,
                    }
                    class_id = class_map.get(cat_type)
                    if class_id is None:
                        continue
                    
                    url = f"{self.scraper.BASE_URL}/?items={class_id}"
                    if subclass is not None:
                        url += f".{subclass}"
                    
                    item_ids = self.scraper.scrape_item_ids_from_page(url)
                new_ids = [i for i in item_ids if i not in self.existing_ids]
                
                self.scrape_results[cat_name] = {
                    'tsm_group': tsm_group,
                    'found': len(item_ids),
                    'new_ids': new_ids
                }
                
                total_found += len(item_ids)
                total_new += len(new_ids)
                
                # Format result line
                display = cat_name.replace('_', ' ').title()
                status = "✓" if new_ids else "—"
                results_lines.append(f"{status} {display:<25} Found: {len(item_ids):>5}   New: {len(new_ids):>5}   → {tsm_group}")
            
            # Update results display with checkboxes
            self.after(0, self.update_results_with_checkboxes)
            
            self.log(f"Complete: {total_found:,} found, {total_new:,} new", 'success')
            
            self.after(0, lambda: self.results_summary.configure(
                text=f"{total_found:,} items found • {total_new:,} new"
            ))
            self.after(0, lambda: self.status_label.configure(
                text="● Scrape complete",
                text_color=get_color('color_success')
            ))
            
            if total_new > 0:
                self.after(0, lambda: self.import_btn.configure(state="normal"))
            
            # Always auto-select the most relevant group based on what was scraped
            self.after(200, self.auto_select_scrape_group)
            
        except Exception as e:
            self.log(f"Error: {e}", 'error')
        finally:
            self.after(0, lambda: self.scrape_btn.configure(state="normal"))
    
    def update_results_display(self, lines):
        """Update the results text display."""
        self.results_text.configure(state="normal")
        self.results_text.delete("1.0", "end")
        
        header = f"{'Status':<7} {'Category':<25} {'Found':>10} {'New':>8}   TSM Group\n"
        header += "─" * 90 + "\n"
        self.results_text.insert("end", header)
        
        for line in lines:
            self.results_text.insert("end", line + "\n")
        
        self.results_text.configure(state="disabled")
    
    def update_results_with_checkboxes(self):
        """Update the results display with checkboxes for each scraped category."""
        # Clear existing checkboxes
        for widget in self.results_scroll.winfo_children():
            widget.destroy()
        self.results_checkboxes.clear()
        
        if not self.scrape_results:
            ctk.CTkLabel(
                self.results_scroll,
                text="No results yet. Select categories and click Scrape.",
                font=ctk.CTkFont(size=10),
                text_color=get_color('text_gray')
            ).pack(anchor="w", padx=10, pady=10)
            return
        
        # Header row
        header = ctk.CTkFrame(self.results_scroll, fg_color="transparent")
        header.pack(fill="x", padx=5, pady=(5, 2))
        
        ctk.CTkLabel(header, text="✓", width=30, font=ctk.CTkFont(size=9, weight="bold"),
                     text_color=get_color('text_gray')).pack(side="left")
        ctk.CTkLabel(header, text="Category", width=100, anchor="w", font=ctk.CTkFont(size=9, weight="bold"),
                     text_color=get_color('text_gray')).pack(side="left", padx=(5, 0))
        ctk.CTkLabel(header, text="Found", width=45, font=ctk.CTkFont(size=9, weight="bold"),
                     text_color=get_color('text_gray')).pack(side="left")
        ctk.CTkLabel(header, text="New", width=45, font=ctk.CTkFont(size=9, weight="bold"),
                     text_color=get_color('text_gray')).pack(side="left")
        ctk.CTkLabel(header, text="TSM Group", anchor="w", font=ctk.CTkFont(size=9, weight="bold"),
                     text_color=get_color('text_gray')).pack(side="left", fill="x", expand=True)
        
        # Create a row for each category
        for cat_name, data in self.scrape_results.items():
            found = data.get('found', 0)
            new_count = len(data.get('new_ids', []))
            tsm_group = data.get('tsm_group', '')
            
            row = ctk.CTkFrame(self.results_scroll, fg_color="transparent")
            row.pack(fill="x", padx=5, pady=1)
            
            # Checkbox (checked by default if there are new items)
            var = ctk.BooleanVar(value=new_count > 0)
            self.results_checkboxes[cat_name] = var
            
            cb = ctk.CTkCheckBox(
                row, text="", variable=var, width=30,
                corner_radius=3, border_width=2,
                fg_color=get_color('accent_primary'),
                hover_color=get_color('accent_primary_dark'),
                border_color=get_color('border_light'),
                checkmark_color=get_color('text_white')
            )
            cb.pack(side="left")
            
            # Category name
            display = cat_name.replace('_', ' ').title()
            ctk.CTkLabel(row, text=display, width=100, anchor="w",
                        font=ctk.CTkFont(size=9),
                        text_color=get_color('text_light')).pack(side="left", padx=(5, 0))
            
            # Found count
            ctk.CTkLabel(row, text=str(found), width=45,
                        font=ctk.CTkFont(size=9),
                        text_color=get_color('text_light')).pack(side="left")
            
            # New count (highlighted if > 0)
            new_color = get_color('color_success') if new_count > 0 else get_color('text_gray')
            ctk.CTkLabel(row, text=str(new_count), width=45,
                        font=ctk.CTkFont(size=9, weight="bold" if new_count > 0 else "normal"),
                        text_color=new_color).pack(side="left")
            
            # TSM Group
            group_display = tsm_group.split('`')[-1] if tsm_group else ""
            ctk.CTkLabel(row, text=f"→ {group_display}", anchor="w",
                        font=ctk.CTkFont(size=8),
                        text_color=get_color('accent_secondary')).pack(side="left", fill="x", expand=True)
    
    def get_selected_import_categories(self) -> dict:
        """Get only the categories that are checked for import."""
        selected = {}
        for cat_name, var in self.results_checkboxes.items():
            if var.get() and cat_name in self.scrape_results:
                selected[cat_name] = self.scrape_results[cat_name]
        return selected
    
    def start_import(self):
        """Start importing to TSM."""
        if not self.scrape_results:
            themed_showinfo(
                self, 
                "No Scrape Results", 
                "Please scrape items first before importing.\n\n"
                "Select categories on the left and click 'Scrape Items'."
            )
            return
        
        # Get only checked categories
        selected_results = self.get_selected_import_categories()
        if not selected_results:
            themed_showinfo(self, "No Categories Selected", "Please check at least one category to import.")
            return
        
        total_new = sum(len(d['new_ids']) for d in selected_results.values())
        if total_new == 0:
            themed_showinfo(self, "Nothing to Import", "All items in selected categories are already in TSM!")
            return
        
        # Get selected target group
        selected_group = self.selected_group_var.get()
        
        # Check if selected results have multiple different target groups
        unique_groups = set(d.get('tsm_group', '') for d in selected_results.values())
        has_multiple_groups = len(unique_groups) > 1
        
        if selected_group == "(Use default from scraper)" or has_multiple_groups:
            # Multiple categories going to their respective groups
            group_list = "\n".join([f"• {cat.replace('_', ' ').title()} → {d['tsm_group'].split('`')[-1]}" 
                                   for cat, d in list(selected_results.items())[:5]])
            if len(selected_results) > 5:
                group_list += f"\n... and {len(selected_results) - 5} more"
            
            if not themed_askquestion(
                self,
                "Confirm Import", 
                f"Import {total_new:,} new items to their respective groups?\n\n{group_list}\n\nThis will update your TradeSkillMaster.lua file."
            ):
                return
            # Force use of default groups
            self.selected_group_var.set("(Use default from scraper)")
        else:
            # Single target group selected
            if not themed_askquestion(
                self,
                "Confirm Import", 
                f"Import {total_new:,} new items to '{selected_group}'?\n\nThis will update your TradeSkillMaster.lua file."
            ):
                return
        
        self.import_btn.configure(state="disabled")
        threading.Thread(target=self.run_import, daemon=True).start()
    
    def run_import(self):
        """Run import in background."""
        try:
            writer = TSMLuaWriter(self.tsm_path)
            total_added = 0
            total_removed = 0

            # Get selected target group (if user picked one)
            selected_group = self.selected_group_var.get()
            use_custom_group = selected_group != "(Use default from scraper)"

            # Process manual remove IDs first
            if self.manual_remove_ids:
                self.log(f"Removing {len(self.manual_remove_ids)} manual IDs...", 'warning')
                remove_result = writer.remove_items(self.manual_remove_ids, dry_run=False)
                total_removed = remove_result['removed']
                self.log(f"✓ Removed {total_removed} items from TSM", 'warning')
                self.manual_remove_ids.clear()
                self.after(0, self.update_manual_status)

            # Process manual add IDs
            if self.manual_add_ids:
                # Manual IDs require a selected group
                if selected_group == "(Use default from scraper)":
                    self.log("Error: Manual IDs require a selected group from the right sidebar", 'error')
                    self.after(0, lambda: themed_showinfo(
                        self,
                        "Group Required",
                        "Please select a target group from the right sidebar before importing manual IDs.\n\nManual IDs don't have auto-categorization, so you must choose where they should go."
                    ))
                else:
                    self.log(f"Importing {len(self.manual_add_ids)} manual IDs to '{selected_group}'...", 'cyan')
                    manual_dict = {item_id: selected_group for item_id in self.manual_add_ids}
                    manual_result = writer.add_items(manual_dict, dry_run=False)
                    total_added += manual_result['added']
                    self.log(f"✓ Imported {manual_result['added']} manual IDs → {selected_group}", 'success')
                    self.manual_add_ids.clear()
                    self.after(0, self.update_manual_status)

            # Import checked categories
            selected_results = self.get_selected_import_categories()

            for cat_name, data in selected_results.items():
                new_ids = data['new_ids']
                if not new_ids:
                    continue

                # Use selected group or default category group
                target_group = selected_group if use_custom_group else data['tsm_group']
                items_dict = {i: target_group for i in new_ids}
                result = writer.add_items(items_dict, dry_run=False)
                total_added += result['added']

                self.log(f"Imported {result['added']} → {target_group}", 'success')

            # Summary message
            summary_parts = []
            if total_added > 0:
                summary_parts.append(f"{total_added:,} items added")
            if total_removed > 0:
                summary_parts.append(f"{total_removed:,} items removed")

            if summary_parts:
                summary = " | ".join(summary_parts)
                self.log(f"✓ Import complete: {summary}", 'success')
                self.after(0, lambda: self.status_label.configure(
                    text=f"● {summary}",
                    text_color=get_color('accent_secondary')
                ))
                self.after(0, self.load_tsm_info)
                self.after(0, lambda: themed_showinfo(self, "Success", f"{summary.capitalize()}!\n\nIf WoW is running, restart it to see changes."))

        except Exception as e:
            self.log(f"Error: {e}", 'error')
        finally:
            self.after(0, lambda: self.import_btn.configure(state="normal"))
    
    def open_settings(self):
        """Open the settings/theme editor dialog."""
        ThemeEditorDialog(self)
    
    def create_default_groups(self):
        """Create default TSM group structure from Wowhead categories."""
        # Warning confirmation
        if not themed_askquestion(
            self,
            "⚠️ Create Default Groups",
            "This feature is intended for EMPTY profiles.\n\n"
            "Creating default groups will ADD 145 new groups to your TSM profile.\n"
            "This won't delete existing groups, but may create duplicates.\n\n"
            "Recommended for new profiles only.\n\n"
            "Continue?"
        ):
            return
        
        try:
            from tsm_scraper.wowhead_scraper import generate_tsm_groups
            from tsm_scraper.lua_writer import TSMLuaWriter
            
            groups = generate_tsm_groups()
            self.log(f"Generated {len(groups)} default groups", 'success')
            
            # Inject directly into TSM SavedVariables
            writer = TSMLuaWriter(self.tsm_path)
            result = writer.add_groups(groups, dry_run=False)
            
            added = result['added']
            skipped = result['skipped']
            
            self.log(f"Added {added} groups, skipped {skipped} existing", 'success')
            
            if result['errors']:
                for error in result['errors']:
                    self.log(f"Error: {error}", 'error')
                themed_showinfo(self, "Error", f"Errors occurred:\n{result['errors']}")
                return
            
            # Refresh the groups panel to show new groups
            self.load_tsm_info()
            
            themed_showinfo(
                self, 
                "✅ Groups Created", 
                f"Successfully created {added} groups!\n\n"
                f"Skipped {skipped} existing groups.\n\n"
                "If WoW is running, restart it to see changes."
            )
            
        except Exception as e:
            self.log(f"Error generating groups: {e}", 'error')
            themed_showinfo(self, "Error", f"Failed to generate groups:\n{e}")
    
    def show_groups_popup(self, groups: list):
        """Show generated groups in a popup window."""
        popup = ctk.CTkToplevel(self)
        popup.title("Generated TSM Groups")
        popup.geometry("500x600")
        popup.configure(fg_color=get_color('bg_dark'))
        
        # Header
        ctk.CTkLabel(
            popup,
            text=f"✨ {len(groups)} Groups Generated",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=get_color('accent_primary')
        ).pack(pady=(15, 5))
        
        ctk.CTkLabel(
            popup,
            text="Copy this text and paste into TSM's group import:",
            font=ctk.CTkFont(size=11),
            text_color=get_color('text_gray')
        ).pack(pady=(0, 10))
        
        # Text area with groups
        text = ctk.CTkTextbox(
            popup,
            font=ctk.CTkFont(family="Consolas", size=10),
            fg_color=get_color('bg_darkest'),
            text_color=get_color('text_light'),
            corner_radius=8
        )
        text.pack(fill="both", expand=True, padx=15, pady=5)
        
        # Format groups as TSM group paths
        group_text = "\n".join(groups)
        text.insert("1.0", group_text)
        
        # Copy button
        def copy_to_clipboard():
            popup.clipboard_clear()
            popup.clipboard_append(group_text)
            copy_btn.configure(text="✓ Copied!")
            popup.after(2000, lambda: copy_btn.configure(text="📋 Copy to Clipboard"))
        
        copy_btn = ctk.CTkButton(
            popup,
            text="📋 Copy to Clipboard",
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=get_color('accent_primary'),
            hover_color=get_color('accent_primary_dark'),
            command=copy_to_clipboard
        )
        copy_btn.pack(pady=15)


# ============================================================================
# Theme Editor Dialog
# ============================================================================

class ThemeEditorDialog(ctk.CTkToplevel if HAS_CTK else object):
    """Modern theme editor dialog with color pickers for every element."""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.parent = parent
        
        self.title("🎨 Theme Editor")
        self.geometry("750x700")
        self.minsize(650, 550)
        self.configure(fg_color=get_color('bg_dark'))
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 750) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 700) // 2
        self.geometry(f"+{x}+{y}")
        
        # Track color entries
        self.color_entries: Dict[str, ctk.CTkEntry] = {}
        self.color_swatches: Dict[str, ctk.CTkButton] = {}
        
        # Build UI
        self.create_widgets()
        self.focus_set()
    
    def create_widgets(self):
        """Build the theme editor UI."""
        # Header
        header = ctk.CTkFrame(self, fg_color=get_color('bg_medium'), corner_radius=8)
        header.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(
            header,
            text="⚙ Theme Editor",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=get_color('accent_primary')
        ).pack(side="left", padx=15, pady=12)
        
        ctk.CTkLabel(
            header,
            text="Customize every color in the application",
            font=ctk.CTkFont(size=12),
            text_color=get_color('text_gray')
        ).pack(side="left", padx=10)
        
        # Theme selection row
        theme_row = ctk.CTkFrame(self, fg_color="transparent")
        theme_row.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(
            theme_row,
            text="Theme:",
            font=ctk.CTkFont(size=13),
            text_color=get_color('text_light')
        ).pack(side="left", padx=(5, 10))
        
        # Theme dropdown
        theme_list = theme_manager.get_theme_list()
        theme_names = [f"{name}" for _, name, _ in theme_list]
        
        self.theme_var = ctk.StringVar(value=theme_manager.current.name)
        self.theme_combo = ctk.CTkComboBox(
            theme_row,
            values=theme_names,
            variable=self.theme_var,
            width=200,
            height=32,
            corner_radius=6,
            fg_color=get_color('bg_light'),
            button_color=get_color('bg_hover'),
            dropdown_fg_color=get_color('bg_medium'),
            command=self.on_theme_selected
        )
        self.theme_combo.pack(side="left", padx=5)
        
        # Theme action buttons
        btn_style = {
            "height": 32,
            "corner_radius": 6,
            "fg_color": get_color('bg_light'),
            "hover_color": get_color('bg_hover'),
            "text_color": get_color('text_light'),
            "font": ctk.CTkFont(size=12)
        }
        
        ctk.CTkButton(
            theme_row, text="💾 Save As...",
            width=100, command=self.save_theme_as, **btn_style
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            theme_row, text="🔄 Reset",
            width=80, command=self.reset_theme, **btn_style
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            theme_row, text="📤 Export",
            width=80, command=self.export_theme, **btn_style
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            theme_row, text="📥 Import",
            width=80, command=self.import_theme, **btn_style
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            theme_row, text="🎲 Random",
            width=80, command=self.randomize_theme, **btn_style
        ).pack(side="left", padx=5)
        
        # Scrollable color editor
        self.colors_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=get_color('bg_medium'),
            corner_radius=8
        )
        self.colors_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        
        self.create_color_editors()
        self.create_font_editors()
        
        # Bottom buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(
            button_frame,
            text="💡 Restart app to apply all theme changes",
            font=ctk.CTkFont(size=11),
            text_color=get_color('text_gray')
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            button_frame,
            text="Close",
            width=100,
            height=36,
            corner_radius=8,
            fg_color=get_color('bg_light'),
            hover_color=get_color('bg_hover'),
            command=self.destroy
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="✨ Apply & Restart",
            width=140,
            height=36,
            corner_radius=8,
            fg_color=get_color('accent_secondary_dark'),
            hover_color=get_color('accent_secondary'),
            text_color=get_color('bg_dark'),
            font=ctk.CTkFont(weight="bold"),
            command=self.apply_and_close
        ).pack(side="right", padx=5)
    
    def create_color_editors(self):
        """Create color pickers for each color property."""
        for category, colors in COLOR_CATEGORIES.items():
            # Category header
            header = ctk.CTkLabel(
                self.colors_scroll,
                text=f"━━ {category} ━━",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=get_color('accent_primary')
            )
            header.pack(anchor="w", pady=(15, 8), padx=10)
            
            for prop_name, display_name in colors:
                current_color = theme_manager.get(prop_name)
                
                row = ctk.CTkFrame(self.colors_scroll, fg_color="transparent")
                row.pack(fill="x", padx=15, pady=3)
                
                # Label
                ctk.CTkLabel(
                    row,
                    text=display_name,
                    width=180,
                    anchor="w",
                    font=ctk.CTkFont(size=12),
                    text_color=get_color('text_light')
                ).pack(side="left")
                
                # Color entry
                entry = ctk.CTkEntry(
                    row,
                    width=100,
                    height=28,
                    corner_radius=4,
                    fg_color=get_color('bg_light'),
                    border_color=get_color('border_dark'),
                    text_color=get_color('text_light'),
                    font=ctk.CTkFont(family="Consolas", size=11)
                )
                entry.insert(0, current_color)
                entry.pack(side="left", padx=5)
                entry.bind('<KeyRelease>', lambda e, n=prop_name: self.on_color_entry_change(n))
                self.color_entries[prop_name] = entry
                
                # Color swatch button (clickable)
                swatch = ctk.CTkButton(
                    row,
                    text="",
                    width=40,
                    height=28,
                    corner_radius=4,
                    fg_color=current_color,
                    hover_color=current_color,
                    border_width=2,
                    border_color=get_color('border_light'),
                    command=lambda n=prop_name: self.pick_color(n)
                )
                swatch.pack(side="left", padx=5)
                self.color_swatches[prop_name] = swatch
    
    def create_font_editors(self):
        """Create font size sliders for different UI elements."""
        # Font size categories
        font_sizes = [
            ("font_size_header", "Header Text", 10, 24),
            ("font_size_label", "Labels", 8, 20),
            ("font_size_body", "Body Text", 8, 18),
            ("font_size_small", "Small Text", 6, 16),
            ("font_size_tiny", "Tiny Text (Groups)", 6, 14),
        ]
        
        # Section header
        header = ctk.CTkLabel(
            self.colors_scroll,
            text="━━ Font Sizes ━━",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=get_color('accent_secondary')
        )
        header.pack(anchor="w", pady=(20, 10), padx=10)
        
        self.font_sliders = {}
        self.font_labels = {}
        
        for prop_name, display_name, min_val, max_val in font_sizes:
            current_size = theme_manager.get(prop_name)
            if current_size is None:
                current_size = 12  # Default
            
            row = ctk.CTkFrame(self.colors_scroll, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=4)
            
            # Label
            ctk.CTkLabel(
                row,
                text=display_name,
                width=140,
                anchor="w",
                font=ctk.CTkFont(size=12),
                text_color=get_color('text_light')
            ).pack(side="left")
            
            # Current value label
            value_label = ctk.CTkLabel(
                row,
                text=f"{current_size}px",
                width=50,
                anchor="e",
                font=ctk.CTkFont(size=11),
                text_color=get_color('accent_primary')
            )
            value_label.pack(side="right", padx=(10, 0))
            self.font_labels[prop_name] = value_label
            
            # Slider
            slider = ctk.CTkSlider(
                row,
                from_=min_val,
                to=max_val,
                number_of_steps=max_val - min_val,
                width=150,
                height=18,
                fg_color=get_color('bg_light'),
                progress_color=get_color('accent_primary_dark'),
                button_color=get_color('accent_primary'),
                button_hover_color=get_color('accent_secondary'),
                command=lambda v, n=prop_name: self.on_font_size_change(n, v)
            )
            slider.set(current_size)
            slider.pack(side="right", padx=5)
            self.font_sliders[prop_name] = slider
    
    def on_font_size_change(self, prop_name: str, value: float):
        """Handle font size slider changes."""
        size = int(value)
        self.font_labels[prop_name].configure(text=f"{size}px")
        theme_manager.set_color(prop_name, size)  # set_color works for any theme prop

    def on_color_entry_change(self, prop_name: str):
        """Handle manual color entry changes."""
        entry = self.color_entries[prop_name]
        value = entry.get().strip()
        
        if self.is_valid_hex(value):
            self.color_swatches[prop_name].configure(fg_color=value, hover_color=value)
            theme_manager.set_color(prop_name, value)
    
    def pick_color(self, prop_name: str):
        """Open color picker for a property."""
        current = self.color_entries[prop_name].get()
        
        result = colorchooser.askcolor(
            color=current,
            title=f"Choose color for {prop_name}",
            parent=self
        )
        
        if result[1]:
            hex_color = result[1]
            entry = self.color_entries[prop_name]
            entry.delete(0, "end")
            entry.insert(0, hex_color)
            self.color_swatches[prop_name].configure(fg_color=hex_color, hover_color=hex_color)
            theme_manager.set_color(prop_name, hex_color)
    
    def is_valid_hex(self, value: str) -> bool:
        """Check if value is a valid hex color."""
        if not value.startswith('#'):
            return False
        if len(value) not in (4, 7):
            return False
        try:
            int(value[1:], 16)
            return True
        except ValueError:
            return False
    
    def on_theme_selected(self, selection: str):
        """Handle theme selection from dropdown."""
        theme_list = theme_manager.get_theme_list()
        for tid, name, is_builtin in theme_list:
            if name == selection:
                # Check if switching to a built-in theme
                if is_builtin and tid != theme_manager.active_theme_id:
                    # Ask if they want fresh preset or current (possibly modified) version
                    result = messagebox.askyesnocancel(
                        "Load Theme",
                        f"Load '{name}' with fresh preset colors?\n\n"
                        f"• Yes = Load original preset colors\n"
                        f"• No = Keep any previous customizations\n"
                        f"• Cancel = Stay on current theme"
                    )
                    if result is None:  # Cancel
                        # Reset dropdown to current theme
                        self.theme_var.set(theme_manager.current.name)
                        return
                    elif result:  # Yes - load fresh
                        theme_manager.reset_theme(tid)
                
                theme_manager.set_theme(tid)
                self.refresh_color_entries()
                break
    
    def refresh_color_entries(self):
        """Refresh all color entries from current theme."""
        for prop_name, entry in self.color_entries.items():
            current = theme_manager.get(prop_name)
            entry.delete(0, "end")
            entry.insert(0, current)
            self.color_swatches[prop_name].configure(fg_color=current, hover_color=current)
    
    def save_theme_as(self):
        """Save current colors as a new named theme."""
        dialog = ctk.CTkInputDialog(
            text="Enter a name for your theme:",
            title="Save Theme"
        )
        name = dialog.get_input()
        
        if name:
            theme_id = theme_manager.create_custom_theme(name, theme_manager.active_theme_id)
            theme_manager.set_theme(theme_id)
            self.refresh_theme_dropdown()
            messagebox.showinfo("Saved", f"Theme '{name}' saved successfully!")
    
    def reset_theme(self):
        """Reset current theme to default preset values."""
        theme_name = theme_manager.current.name
        is_builtin = theme_manager.current.builtin
        
        if is_builtin:
            msg = f"Reset '{theme_name}' to its original preset colors?\n\nThis will undo all your customizations."
        else:
            msg = f"Delete custom theme '{theme_name}' and switch to TSM Dark?"
        
        if messagebox.askyesno("Reset Theme", msg):
            if is_builtin:
                theme_manager.reset_theme()
            else:
                theme_manager.delete_theme(theme_manager.active_theme_id)
                theme_manager.set_theme("tsm_dark")
                self.refresh_theme_dropdown()
            self.refresh_color_entries()
            messagebox.showinfo("Reset", f"Theme reset to defaults!")
    
    def export_theme(self):
        """Export current theme to a JSON file."""
        path = filedialog.asksaveasfilename(
            title="Export Theme",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            parent=self
        )
        if path:
            if theme_manager.export_theme(theme_manager.active_theme_id, Path(path)):
                messagebox.showinfo("Exported", f"Theme exported to {path}")
            else:
                messagebox.showerror("Error", "Failed to export theme")
    
    def import_theme(self):
        """Import a theme from a JSON file."""
        path = filedialog.askopenfilename(
            title="Import Theme",
            filetypes=[("JSON files", "*.json")],
            parent=self
        )
        if path:
            theme_id = theme_manager.import_theme(Path(path))
            if theme_id:
                theme_manager.set_theme(theme_id)
                self.refresh_theme_dropdown()
                self.refresh_color_entries()
                messagebox.showinfo("Imported", "Theme imported successfully!")
            else:
                messagebox.showerror("Error", "Failed to import theme")
    
    def randomize_theme(self):
        """Generate random colors for the current theme."""
        import random
        import colorsys
        
        def random_color() -> str:
            """Generate a random hex color."""
            return f"#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}"
        
        def random_dark_color() -> str:
            """Generate a random dark color for backgrounds."""
            h = random.random()
            s = random.uniform(0.1, 0.3)
            v = random.uniform(0.05, 0.25)
            r, g, b = colorsys.hsv_to_rgb(h, s, v)
            return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
        
        def random_light_color() -> str:
            """Generate a random light color for text."""
            h = random.random()
            s = random.uniform(0, 0.2)
            v = random.uniform(0.7, 1.0)
            r, g, b = colorsys.hsv_to_rgb(h, s, v)
            return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
        
        def random_accent_color() -> str:
            """Generate a random vibrant accent color."""
            h = random.random()
            s = random.uniform(0.7, 1.0)
            v = random.uniform(0.8, 1.0)
            r, g, b = colorsys.hsv_to_rgb(h, s, v)
            return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
        
        def darker_variant(hex_color: str) -> str:
            """Create a darker version of a color."""
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            return f"#{int(r*0.7):02x}{int(g*0.7):02x}{int(b*0.7):02x}"
        
        # Generate a cohesive random theme
        # Base dark colors (all using same hue for cohesion)
        base_hue = random.random()
        
        # Backgrounds - gradient from darkest to lightest
        for i, prop in enumerate(["bg_darkest", "bg_dark", "bg_medium", "bg_light", "bg_hover", "bg_selected"]):
            s = random.uniform(0.1, 0.3)
            v = 0.05 + (i * 0.05)  # Gradual lightening
            r, g, b = colorsys.hsv_to_rgb(base_hue, s, v)
            color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
            theme_manager.set_color(prop, color)
        
        # Borders
        theme_manager.set_color("border_dark", random_dark_color())
        theme_manager.set_color("border_light", random_dark_color())
        
        # Text - light colors
        theme_manager.set_color("text_white", "#ffffff")
        theme_manager.set_color("text_light", random_light_color())
        theme_manager.set_color("text_gray", "#888888")
        theme_manager.set_color("text_dark", "#666666")
        
        # Accents - vibrant colors
        accent1 = random_accent_color()
        accent2 = random_accent_color()
        theme_manager.set_color("accent_primary", accent1)
        theme_manager.set_color("accent_primary_dark", darker_variant(accent1))
        theme_manager.set_color("accent_secondary", accent2)
        theme_manager.set_color("accent_secondary_dark", darker_variant(accent2))
        
        # Status colors - keep recognizable
        theme_manager.set_color("color_success", random_accent_color())
        theme_manager.set_color("color_success_dark", "#00aa00")
        theme_manager.set_color("color_warning", random_accent_color())
        theme_manager.set_color("color_error", f"#{random.randint(200,255):02x}{random.randint(0,80):02x}{random.randint(0,80):02x}")
        
        # Item quality - randomize
        theme_manager.set_color("quality_epic", random_accent_color())
        theme_manager.set_color("quality_rare", random_accent_color())
        theme_manager.set_color("quality_uncommon", random_accent_color())
        theme_manager.set_color("quality_common", "#ffffff")
        
        self.refresh_color_entries()
        theme_manager.save()
    
    def refresh_theme_dropdown(self):
        """Refresh the theme dropdown with current themes."""
        theme_list = theme_manager.get_theme_list()
        theme_names = [name for _, name, _ in theme_list]
        self.theme_combo.configure(values=theme_names)
        self.theme_var.set(theme_manager.current.name)
    
    def apply_and_close(self):
        """Save theme and close, prompting for restart."""
        theme_manager.save()
        if messagebox.askyesno(
            "Restart Required",
            "Theme saved! Restart the application now to see all changes?"
        ):
            self.destroy()
            self.parent.destroy()
            import subprocess
            subprocess.Popen([sys.executable, __file__])
        else:
            self.destroy()


# ============================================================================
# Main Entry Point
# ============================================================================

def _write_crash_log(exc_type, exc_value, exc_traceback):
    """Write crash information to a log file for debugging."""
    import traceback
    from datetime import datetime
    
    crash_log_path = _BASE_PATH / "crash_log.txt"
    
    try:
        with open(crash_log_path, 'a', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write(f"CRASH REPORT - {datetime.now().isoformat()}\n")
            f.write("=" * 60 + "\n\n")
            
            # Environment info
            f.write("=== Environment ===\n")
            f.write(f"Python Version: {sys.version}\n")
            f.write(f"Platform: {sys.platform}\n")
            f.write(f"Frozen: {getattr(sys, 'frozen', False)}\n")
            f.write(f"Base Path: {_BASE_PATH}\n")
            f.write(f"App Data Path: {_APP_DATA_PATH}\n")
            f.write(f"Wine Detected: {_detect_wine_or_linux()}\n")
            f.write(f"WINEPREFIX: {os.environ.get('WINEPREFIX', 'Not set')}\n")
            f.write(f"APPDATA: {os.environ.get('APPDATA', 'Not set')}\n")
            f.write(f"HOME: {os.environ.get('HOME', 'Not set')}\n\n")
            
            # Exception info
            f.write("=== Exception ===\n")
            f.write(f"Type: {exc_type.__name__}\n")
            f.write(f"Message: {exc_value}\n\n")
            
            # Full traceback
            f.write("=== Traceback ===\n")
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
            f.write("\n\n")
        
        print(f"\n[CRASH] Error logged to: {crash_log_path}")
        print(f"Please send this file when reporting bugs.\n")
        
    except Exception as log_error:
        print(f"Failed to write crash log: {log_error}")


def main():
    if not HAS_CTK:
        print("Warning: CustomTkinter not installed. For the best experience, run:")
        print("  pip install customtkinter")
        print()
    
    # Set up global exception handler for crash logging
    def global_exception_handler(exc_type, exc_value, exc_traceback):
        # Write to crash log
        _write_crash_log(exc_type, exc_value, exc_traceback)
        # Also print to console
        import traceback
        traceback.print_exception(exc_type, exc_value, exc_traceback)
    
    sys.excepthook = global_exception_handler
    
    try:
        app = TSMScraperApp()
        app.mainloop()
    except Exception as e:
        # Catch any uncaught exceptions and log them
        import traceback
        _write_crash_log(type(e), e, e.__traceback__)
        raise


if __name__ == "__main__":
    main()
