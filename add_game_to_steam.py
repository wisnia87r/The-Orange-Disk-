#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Add individual PS1/PS2 games to Steam with proper emulator configuration
"""

import sys
import pathlib
import shutil
import zlib
import os

try:
    from vdf import binary_load, binary_dump
    from PIL import Image
except ImportError:
    print("[AddGame] ERROR: Module 'vdf' is not installed.", flush=True)
    sys.exit(1)

def log(message):
    print(f"[AddGame] {message}", flush=True)

def calculate_app_id(exe_path, app_name):
    """Calculate Steam AppID for a non-Steam game"""
    combined_string = str(exe_path) + app_name
    crc = zlib.crc32(combined_string.encode('utf-8'))
    return (crc | 0x80000000)

def find_steam_user_id():
    """Find the most recently used Steam user ID"""
    log("Finding Steam user ID...")
    userdata_path = pathlib.Path.home() / ".local/share/Steam/userdata"
    if not userdata_path.exists():
        log("  ERROR: Steam userdata folder not found.")
        return None
    user_dirs = [d for d in userdata_path.iterdir() if d.is_dir() and d.name.isdigit() and d.name != "0"]
    if not user_dirs:
        log("  ERROR: No user folders found.")
        return None
    latest_user_dir = max(user_dirs, key=lambda d: d.stat().st_mtime)
    log(f"  Found user ID: {latest_user_dir.name}")
    return latest_user_dir.name

def find_appimage(name):
    """Find an AppImage in common locations"""
    search_paths = [
        pathlib.Path.home() / "Applications",
        pathlib.Path.home() / ".local/share/applications",
        pathlib.Path("/opt"),
    ]
    for base_path in search_paths:
        if base_path.exists():
            for file in base_path.rglob("*.AppImage"):
                if name.lower() in file.name.lower():
                    return str(file)
    return None

def detect_emulator_for_rom(rom_path):
    """Detect which emulator to use based on ROM file extension"""
    rom_path = pathlib.Path(rom_path)
    ext = rom_path.suffix.lower()

    if ext == ".bin" or ext == ".cue":
        # PS1 game - use DuckStation
        log("  Detected PS1 game (DuckStation)")
        appimage = find_appimage("DuckStation")
        if appimage:
            return f'"{appimage}"', appimage
        return '"flatpak" "run" "org.duckstation.DuckStation"', "flatpak"
    elif ext == ".iso":
        # Could be PS1 or PS2, assume PS2 for .iso - use PCSX2
        log("  Detected PS2 game (PCSX2)")
        appimage = find_appimage("PCSX2")
        if appimage:
            return f'"{appimage}"', appimage
        return '"flatpak" "run" "net.pcsx2.PCSX2"', "flatpak"
    else:
        log(f"  WARNING: Unknown ROM format: {ext}")
        return None, None

def add_game_to_steam(game_name, rom_path, artwork_grid=None, artwork_grid_vertical=None, artwork_hero=None, artwork_logo=None, artwork_icon=None):
    """Add a game to Steam shortcuts with proper emulator configuration and multiple artwork types"""
    log(f"--- Adding game to Steam: {game_name} ---")

    # Validate inputs
    rom_path = pathlib.Path(rom_path)
    if not rom_path.exists():
        log(f"ERROR: ROM file not found: {rom_path}")
        return False

    # Validate artwork paths
    artwork_paths = {
        'grid': pathlib.Path(artwork_grid) if artwork_grid else None,
        'grid_vertical': pathlib.Path(artwork_grid_vertical) if artwork_grid_vertical else None,
        'hero': pathlib.Path(artwork_hero) if artwork_hero else None,
        'logo': pathlib.Path(artwork_logo) if artwork_logo else None,
        'icon': pathlib.Path(artwork_icon) if artwork_icon else None
    }

    # Check which artwork files exist
    for art_type, path in list(artwork_paths.items()):
        if path and not path.exists():
            log(f"WARNING: {art_type} artwork file not found: {path}")
            artwork_paths[art_type] = None

    # Find Steam user
    user_id = find_steam_user_id()
    if not user_id:
        return False

    # Detect emulator
    launch_options, exe_path = detect_emulator_for_rom(rom_path)
    if not launch_options:
        log("ERROR: Could not determine emulator for this ROM")
        return False

    log(f"  ROM: {rom_path}")
    log(f"  Emulator: {exe_path}")
    log(f"  Launch options: {launch_options}")

    # Calculate AppID
    unsigned_app_id = calculate_app_id(exe_path, game_name)
    signed_app_id = unsigned_app_id - 4294967296 if unsigned_app_id > 2147483647 else unsigned_app_id
    log(f"  AppID (unsigned): {unsigned_app_id}")
    log(f"  AppID (signed): {signed_app_id}")

    # Load or create shortcuts.vdf
    shortcuts_vdf_path = pathlib.Path.home() / f".local/share/Steam/userdata/{user_id}/config/shortcuts.vdf"
    shortcuts_data = {'shortcuts': {}}

    if shortcuts_vdf_path.exists():
        try:
            with open(shortcuts_vdf_path, 'rb') as f:
                shortcuts_data = binary_load(f)
        except Exception as e:
            log(f"  WARNING: Could not read shortcuts.vdf: {e}")

    # Remove any existing shortcut with the same name
    clean_shortcuts = {
        str(i): s for i, s in enumerate([
            sc for sc in shortcuts_data.get('shortcuts', {}).values()
            if sc.get('AppName') != game_name
        ])
    }

    # Create new shortcut entry
    new_index = str(len(clean_shortcuts))

    # Set icon path if icon artwork is available
    icon_path = ""
    if artwork_paths.get('icon'):
        # Use the source icon path (will be copied to grid folder later)
        icon_path = str(artwork_paths['icon'])

    new_shortcut_data = {
        'AppName': game_name,
        'Exe': f'"{exe_path}"',
        'StartDir': str(rom_path.parent),
        'LaunchOptions': f'"{rom_path}"',
        'icon': icon_path,  # Note: lowercase 'icon' is correct for Steam
        'IsHidden': 0,
        'AllowDesktopConfig': 1,
        'AllowOverlay': 1,
        'OpenVR': 0,
        'tags': {},
        'AppId': signed_app_id
    }

    clean_shortcuts[new_index] = new_shortcut_data
    shortcuts_data['shortcuts'] = clean_shortcuts

    # Save shortcuts.vdf
    try:
        shortcuts_vdf_path.parent.mkdir(parents=True, exist_ok=True)
        with open(shortcuts_vdf_path, 'wb') as f:
            binary_dump(shortcuts_data, f)
        log("  SUCCESS: Shortcut added to Steam")
    except Exception as e:
        log(f"  ERROR: Could not save shortcuts.vdf: {e}")
        return False

    # Copy artwork if provided
    if any(artwork_paths.values()):
        log("  Copying artwork...")
        grid_dir = pathlib.Path.home() / f".local/share/Steam/userdata/{user_id}/config/grid"
        grid_dir.mkdir(parents=True, exist_ok=True)

        # Steam artwork file naming conventions
        artwork_mapping = {
            'grid': [
                (f"{unsigned_app_id}.png", "Grid (horizontal capsule)")
            ],
            'grid_vertical': [
                (f"{unsigned_app_id}p.png", "Grid (vertical capsule)")
            ],
            'hero': [
                (f"{unsigned_app_id}_hero.png", "Hero (banner)")
            ],
            'logo': [
                (f"{unsigned_app_id}_logo.png", "Logo")
            ],
            'icon': [
                (f"{unsigned_app_id}_icon.png", "Icon")
            ]
        }

        for art_type, source_path in artwork_paths.items():
            if source_path:
                for target_name, description in artwork_mapping[art_type]:
                    target_path = grid_dir / target_name
                    try:
                        shutil.copy(source_path, target_path)
                        log(f"    - Copied {description}: {target_name}")
                    except Exception as e:
                        log(f"    - ERROR copying {description}: {e}")

                # Special handling for icons: resize to small PNG for Steam Desktop
                if art_type == 'icon':
                    try:
                        # Steam Desktop needs a small icon PNG (128x128 or 256x256)
                        # Replace the large PNG with a resized version
                        img = Image.open(source_path)
                        # Convert to RGBA if needed
                        if img.mode != 'RGBA':
                            img = img.convert('RGBA')

                        # Resize to 256x256 for better quality
                        img_resized = img.resize((256, 256), Image.Resampling.LANCZOS)

                        # Overwrite the icon PNG with resized version
                        icon_png_path = grid_dir / f"{unsigned_app_id}_icon.png"
                        img_resized.save(icon_png_path, format='PNG', optimize=True)
                        log(f"    - Resized icon to 256x256: {unsigned_app_id}_icon.png")

                        # Also create ICO format for additional compatibility
                        ico_path = grid_dir / f"{unsigned_app_id}_icon.ico"
                        img.save(ico_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
                        log(f"    - Created ICO format: {unsigned_app_id}_icon.ico")
                    except Exception as e:
                        log(f"    - WARNING: Could not process icon: {e}")

    log("--- Game added successfully! ---")
    return True

def main():
    if len(sys.argv) < 3:
        print("Usage: add_game_to_steam.py <game_name> <rom_path> [artwork_grid] [artwork_grid_vertical] [artwork_hero] [artwork_logo] [artwork_icon]")
        sys.exit(1)

    game_name = sys.argv[1]
    rom_path = sys.argv[2]
    artwork_grid = sys.argv[3] if len(sys.argv) > 3 else None
    artwork_grid_vertical = sys.argv[4] if len(sys.argv) > 4 else None
    artwork_hero = sys.argv[5] if len(sys.argv) > 5 else None
    artwork_logo = sys.argv[6] if len(sys.argv) > 6 else None
    artwork_icon = sys.argv[7] if len(sys.argv) > 7 else None

    success = add_game_to_steam(game_name, rom_path, artwork_grid, artwork_grid_vertical, artwork_hero, artwork_logo, artwork_icon)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
