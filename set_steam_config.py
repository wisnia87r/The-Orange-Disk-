#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import pathlib
import shutil
import zlib
import json

try:
    from vdf import binary_load, binary_dump
except ImportError:
    print("[Py] ERROR: Module 'vdf' is not installed.", flush=True)
    sys.exit(1)

# --- Configuration ---
APP_NAME = "The Orange Disk Playstation Edition"
INSTALL_DIR = pathlib.Path(__file__).parent.resolve()
LAUNCHER_PATH = INSTALL_DIR / "launcher.sh"
ASSETS_DIR = INSTALL_DIR / "assets"
ICON_PATH = ASSETS_DIR / "icons" / "icon.png"

IMAGE_TARGETS = {
    ASSETS_DIR / "artwork" / "hero.png": "{app_id}_hero.png",
    ASSETS_DIR / "artwork" / "vertical_capsule.png": "{app_id}p.png",
    ASSETS_DIR / "artwork" / "capsule.png": "{app_id}.png"
}

# --- Helper Functions ---
def log(message):
    """Print a log message with a prefix."""
    print(f"[Py] {message}", flush=True)

def calculate_app_id(exe_path, app_name):
    """Calculate Steam AppID for a non-Steam game.

    Steam uses CRC32 hash of the executable path + app name to generate unique IDs.
    The result is OR'd with 0x80000000 to mark it as a non-Steam game.
    """
    log(f"  - Calculating AppID for Exe='{exe_path}' and AppName='{app_name}'")
    combined_string = str(exe_path) + app_name
    crc = zlib.crc32(combined_string.encode('utf-8'))
    return (crc | 0x80000000)

def find_steam_user_id():
    """Find the Steam user ID by looking in the userdata directory.

    Returns the most recently modified user directory (usually the active user).
    """
    log("Searching for Steam user ID...")
    userdata_path = pathlib.Path.home() / ".local/share/Steam/userdata"
    if not userdata_path.exists():
        log("  - CRITICAL ERROR: Steam userdata folder not found.")
        return None
    user_dirs = [d for d in userdata_path.iterdir() if d.is_dir() and d.name.isdigit() and d.name != "0"]
    if not user_dirs:
        log("  - CRITICAL ERROR: No user folders found.")
        return None
    latest_user_dir = max(user_dirs, key=lambda d: d.stat().st_mtime)
    log(f"  - Found user ID: {latest_user_dir.name}")
    return latest_user_dir.name

# --- Main Function ---
def main():
    """Main function that adds The Orange Disk to Steam as a non-Steam game.

    This function:
    1. Finds the Steam user ID
    2. Calculates a unique AppID for the application
    3. Adds/updates the shortcut in shortcuts.vdf
    4. Copies artwork to Steam's grid folder
    """
    log("--- Starting Steam configuration ---")
    
    user_id = find_steam_user_id()
    if not user_id:
        sys.exit(1)

    # Step 1: Add/update the shortcut
    log("Step 1: Modifying shortcuts.vdf file.")
    unsigned_app_id = calculate_app_id(LAUNCHER_PATH, APP_NAME)
    # Steam's VDF format uses signed 32-bit integers, so we need to convert
    signed_app_id = unsigned_app_id - 4294967296 if unsigned_app_id > 2147483647 else unsigned_app_id
    log(f"  - AppID (unsigned): {unsigned_app_id}")
    log(f"  - AppID (signed): {signed_app_id}")

    shortcuts_vdf_path = pathlib.Path.home() / f".local/share/Steam/userdata/{user_id}/config/shortcuts.vdf"
    # Create the shortcut data structure that Steam expects
    new_shortcut_data = {
        'AppName': APP_NAME,                    # Name shown in Steam library
        'Exe': str(LAUNCHER_PATH),              # Path to the launcher script
        'StartDir': str(INSTALL_DIR),           # Working directory when launched
        'LaunchOptions': "",                    # Additional command-line arguments
        'Icon': str(ICON_PATH) if ICON_PATH.exists() else "",  # Icon path
        'IsHidden': 0,                          # 0 = visible in library
        'AllowDesktopConfig': 1,                # Allow Steam Input configuration
        'AllowOverlay': 1,                      # Allow Steam overlay
        'OpenVR': 0,                            # Not a VR game
        'tags': {},                             # User-defined tags/categories
        'AppId': signed_app_id                  # Unique identifier
    }
    
    # Load existing shortcuts or create new structure
    shortcuts_data = {'shortcuts': {}}
    if shortcuts_vdf_path.exists():
        try:
            with open(shortcuts_vdf_path, 'rb') as f: shortcuts_data = binary_load(f)
        except Exception as e:
            log(f"  - WARNING: Cannot read shortcuts.vdf: {e}")
            
    # Remove any existing entry for this app (to avoid duplicates)
    # Then add our shortcut at the end
    clean_shortcuts = {str(i): s for i, s in enumerate([sc for sc in shortcuts_data.get('shortcuts', {}).values() if sc.get('AppName') != APP_NAME])}
    new_index = str(len(clean_shortcuts))
    clean_shortcuts[new_index] = new_shortcut_data
    shortcuts_data['shortcuts'] = clean_shortcuts

    # Write the updated shortcuts back to the file
    try:
        with open(shortcuts_vdf_path, 'wb') as f: binary_dump(shortcuts_data, f)
        log("  - SUCCESS: Shortcuts file saved successfully.")
    except Exception as e:
        log(f"  - CRITICAL ERROR writing shortcuts.vdf: {e}")
        sys.exit(1)

    # Step 2: Copy artwork to Steam's grid folder
    # Steam looks for artwork files named with the AppID in the grid folder
    log("Step 2: Copying artwork to /grid/ folder.")
    grid_dir = pathlib.Path.home() / f".local/share/Steam/userdata/{user_id}/config/grid"
    grid_dir.mkdir(parents=True, exist_ok=True)
    log(f"  - Target directory: {grid_dir}")

    # Copy each artwork file with the correct naming convention
    # Steam expects: {AppID}.png (grid), {AppID}p.png (vertical), {AppID}_hero.png (hero)
    for key, target_name_template in IMAGE_TARGETS.items():
        source_path = pathlib.Path(key)
        if source_path.exists():
            target_name = target_name_template.format(app_id=unsigned_app_id)
            target_path = grid_dir / target_name
            try:
                shutil.copy(source_path, target_path)
                log(f"  - Copied '{source_path.name}' -> '{target_name}'")
            except Exception as e:
                log(f"  - ERROR copying '{source_path.name}': {e}")
        else:
            log(f"  - SKIPPED: File '{source_path}' does not exist.")
            
    log("\n--- Configuration completed successfully! ---")

if __name__ == "__main__":
    main()
