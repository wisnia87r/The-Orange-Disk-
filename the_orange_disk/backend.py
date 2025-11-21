# -*- coding: utf-8 -*-

# This file contains the backend logic for system interactions.

import os
import subprocess
import time
import shutil
import re
import requests # Nowa biblioteka
from .config import TRANSLATIONS, STEAMGRIDDB_API_KEY

def log(msg):
    print(f"[BACKEND] {msg}")

# --- SteamGridDB API Functions ---

def search_game_on_steamgriddb(game_name):
    """Searches for a game on SteamGridDB and returns its ID."""
    if not STEAMGRIDDB_API_KEY or STEAMGRIDDB_API_KEY == "YOUR_API_KEY_HERE":
        raise Exception("SteamGridDB API Key is missing in config.py!")
    
    log(f"Searching for game '{game_name}' on SteamGridDB...")
    headers = {'Authorization': f'Bearer {STEAMGRIDDB_API_KEY}'}

    # URL encode the game name to handle special characters and spaces
    from urllib.parse import quote
    encoded_game_name = quote(game_name)
    url = f"https://www.steamgriddb.com/api/v2/search/autocomplete/{encoded_game_name}"

    response = requests.get(url, headers=headers)
    response.raise_for_status() # Raise an exception for bad status codes
    
    data = response.json()
    if not data.get('success') or not data.get('data'):
        raise Exception(f"Game '{game_name}' not found on SteamGridDB.")
        
    game_id = data['data'][0]['id'] # Take the first result
    log(f"Found Game ID: {game_id}")
    return game_id

def get_artwork_from_steamgriddb(game_id):
    """
    Get artwork URLs for all types from SteamGridDB.

    Args:
        game_id (int): SteamGridDB game ID

    Returns:
        dict: Dictionary containing lists of artwork for each type:
            - grids: Horizontal library capsules (920x430, 460x215)
            - grids_vertical: Vertical library capsules (600x900)
            - heroes: Large banners at top of game page
            - logos: Game logos (transparent PNGs)
            - icons: Small icons for list view

    Each artwork item contains URL, thumbnail, dimensions, and style information.
    """
    log(f"Fetching all artwork types for game ID {game_id}...")
    headers = {'Authorization': f'Bearer {STEAMGRIDDB_API_KEY}'}

    # Initialize the artwork data structure
    artwork_data = {
        'grids': [],           # Horizontal library capsules (920x430, 460x215)
        'grids_vertical': [],  # Vertical library capsules (600x900)
        'heroes': [],          # Large banners at top of game page
        'logos': [],           # Game logos (transparent PNGs)
        'icons': []            # Small icons
    }

    # Define API endpoints for each artwork type
    # Note: The 'grids' endpoint returns both horizontal and vertical grids,
    # which we'll separate based on their dimensions
    endpoints = {
        'grids': f"https://www.steamgriddb.com/api/v2/grids/game/{game_id}",
        'heroes': f"https://www.steamgriddb.com/api/v2/heroes/game/{game_id}",
        'logos': f"https://www.steamgriddb.com/api/v2/logos/game/{game_id}",
        'icons': f"https://www.steamgriddb.com/api/v2/icons/game/{game_id}"
    }

    # Fetch artwork from each endpoint
    for art_type, url in endpoints.items():
        try:
            # Make API request with timeout
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('success') and data.get('data'):
                # Process each artwork item
                for item in data['data']:
                    # Create artwork item with all metadata
                    artwork_item = {
                        'url': item['url'],                          # Full-size image URL
                        'thumb': item.get('thumb', item['url']),     # Thumbnail URL
                        'width': item.get('width', 0),               # Image width in pixels
                        'height': item.get('height', 0),             # Image height in pixels
                        'style': item.get('style', 'alternate')      # Art style (official, alternate, etc.)
                    }

                    # Special handling for grids: separate horizontal and vertical based on dimensions
                    if art_type == 'grids':
                        width = artwork_item['width']
                        height = artwork_item['height']
                        # Vertical grids are taller than wide (e.g., 600x900)
                        # Horizontal grids are wider than tall (e.g., 920x430, 460x215)
                        if height > width:
                            artwork_data['grids_vertical'].append(artwork_item)
                        else:
                            artwork_data['grids'].append(artwork_item)
                    else:
                        artwork_data[art_type].append(artwork_item)

                # Log how many items we found
                if art_type == 'grids':
                    log(f"  Found {len(artwork_data['grids'])} horizontal grids and {len(artwork_data['grids_vertical'])} vertical grids")
                else:
                    log(f"  Found {len(artwork_data[art_type])} {art_type}")
        except Exception as e:
            log(f"  Could not fetch {art_type}: {e}")

    return artwork_data

# --- System Interaction Functions (no changes below) ---

def is_sandboxed():
    return os.path.exists("/.flatpak-info")

def run_host_command(cmd_list, check=True):
    if is_sandboxed():
        final_cmd = ["flatpak-spawn", "--host"] + cmd_list
    else:
        final_cmd = cmd_list
    log(f"EXEC: {' '.join(final_cmd)}")
    result = subprocess.run(final_cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        log(f"!!! COMMAND ERROR (Code {result.returncode}) !!!")
        log(f"STDERR: {result.stderr.strip()}")
        if check:
            raise subprocess.CalledProcessError(result.returncode, final_cmd, result.stdout, result.stderr)
    return result

def force_unmount(drive_path):
    if not drive_path: return
    log(f"Attempting to unmount drive {drive_path}...")
    try:
        run_host_command(["udisksctl", "unmount", "-b", drive_path], check=False)
    except Exception:
        try:
            run_host_command(["umount", "-l", drive_path], check=False)
        except Exception as e2:
            log(f"All unmount attempts failed: {e2}")
    time.sleep(1)

def get_drive_device_path():
    possible_paths = ["/dev/sr0", "/dev/sr1", "/dev/cdrom", "/dev/dvd"]
    for path in possible_paths:
        cmd = ["test", "-e", path]
        if is_sandboxed():
            cmd = ["flatpak-spawn", "--host"] + cmd
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            log(f"Optical drive found at: {path}")
            return path
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    return None

def check_drive_permissions(drive_path):
    if not drive_path: return False
    log("--- Verifying Permissions ---")
    try:
        run_host_command(["test", "-w", drive_path], check=True)
        cmd = """
        count=0
        for dev in /dev/sg*; do
            if [ -e "$dev" ]; then
                count=$((count+1))
                if [ ! -w "$dev" ]; then exit 1; fi
            fi
        done
        if [ "$count" -eq 0 ]; then exit 1; fi
        """
        run_host_command(["sh", "-c", cmd], check=True)
        log("Permissions: OK")
        return True
    except subprocess.CalledProcessError:
        log("Permissions: MISSING")
        return False

def run_sudo_command(command_str, password):
    full_command = f"echo '{password}' | sudo -S {command_str}"
    if is_sandboxed():
        cmd_list = ["flatpak-spawn", "--host", "sh", "-c", full_command]
    else:
        cmd_list = ["sh", "-c", full_command]
    log(f"SUDO: {command_str}")
    result = subprocess.run(cmd_list, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        log(f"SUDO ERROR: {result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, cmd_list, result.stdout, result.stderr)
    return result

def get_emudeck_rom_path(console):
    paths = [
        os.path.expanduser(f"~/Emulation/roms/{console}"),
        f"/run/media/mmcblk0p1/Emulation/roms/{console}",
        os.path.expanduser(f"~/Games/{console}"),
        os.path.expanduser("~/Documents")
    ]
    for path in paths:
        if os.path.exists(path): return path
    default_path = os.path.expanduser(f"~/Documents/{console.upper()}_Rips")
    os.makedirs(default_path, exist_ok=True)
    return default_path

def check_tool_installed(tool_name):
    log(f"Checking for tool: {tool_name}")
    if is_sandboxed():
        try:
            subprocess.run(["flatpak-spawn", "--host", "which", tool_name], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except:
            return False
    else:
        return shutil.which(tool_name) is not None

def find_appimage(name_contains):
    log(f"Scanning for AppImage containing: {name_contains}")
    app_dir = "/home/deck/Applications/"
    name_lower = name_contains.lower()
    if not os.path.exists(app_dir): return None
    try:
        for filename in os.listdir(app_dir):
            if name_lower in filename.lower() and filename.lower().endswith(".appimage"):
                found_path = os.path.join(app_dir, filename)
                log(f"Found AppImage: {found_path}")
                return found_path
    except Exception as e:
        log(f"Error while scanning {app_dir}: {e}")
    return None

def get_disc_info(drive_path):
    if not check_tool_installed("isoinfo"):
        raise Exception(TRANSLATIONS["TOOL_NOT_FOUND"]["EN"].format(tool='isoinfo'))
    force_unmount(drive_path)
    log("Getting disc details (isoinfo -d)...")
    result_details = run_host_command(["isoinfo", "-d", "-i", drive_path])
    details_output = result_details.stdout
    volume_size_sectors = 0
    match_sectors = re.search(r"Volume size is:\s*(\d+)", details_output)
    if match_sectors:
        volume_size_sectors = int(match_sectors.group(1))
    log("Getting file list (isoinfo -l)...")
    try:
        result_files = run_host_command(["isoinfo", "-l", "-i", drive_path])
        file_list_upper = result_files.stdout.upper()
    except Exception:
        file_list_upper = ""
    return volume_size_sectors, file_list_upper

def detect_disc_type(volume_size_sectors, file_list_upper):
    """
    Detect the type of PlayStation disc based on size and file contents.

    Args:
        volume_size_sectors (int): Size of the disc in sectors
        file_list_upper (str): Uppercase file listing from the disc

    Returns:
        str: Disc type - "PS2_DVD", "PS2_CD", or "PS1_CD"

    Detection logic:
    - Discs larger than 500,000 sectors are PS2 DVDs
    - Discs with "IOP" in the file list are PS2 CDs
    - Everything else is assumed to be PS1 CDs
    """
    log(f"Analyzing disc data: Size={volume_size_sectors} sectors.")
    if volume_size_sectors > 500000:
        return "PS2_DVD"
    if "IOP" in file_list_upper:
        return "PS2_CD"
    return "PS1_CD"
