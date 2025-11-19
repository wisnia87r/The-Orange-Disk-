# -*- coding: utf-8 -*-

# This file contains the backend logic for system interactions,
# such as running host commands, checking permissions, and detecting hardware.

import os
import subprocess
import time
import shutil
import re
from .config import TRANSLATIONS # Import from a local module

# --- Logging Utility ---
# (Assuming a 'log' function is available from the main app module,
# but for independence, a simple print can be a fallback)
def log(msg):
    print(f"[BACKEND] {msg}")

# --- System Interaction Functions ---

def is_sandboxed():
    """Checks if the application is running inside a Flatpak sandbox."""
    return os.path.exists("/.flatpak-info")

def run_host_command(cmd_list, check=True):
    """
    Runs a command on the host system, breaking out of the Flatpak
    sandbox if necessary.
    """
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
    """Aggressively tries to unmount the optical drive."""
    if not drive_path: return
    log(f"Attempting to unmount drive {drive_path}...")
    try:
        run_host_command(["udisksctl", "unmount", "-b", drive_path], check=False)
        log(f"Unmounted {drive_path} via udisksctl (or it was already unmounted).")
    except Exception as e:
        log(f"udisksctl failed ({e}), falling back to 'umount -l'...")
        try:
            run_host_command(["umount", "-l", drive_path], check=False)
            log(f"Unmounted {drive_path} via 'umount -l' (or it was already unmounted).")
        except Exception as e2:
            log(f"All unmount attempts failed: {e2}")
    time.sleep(1)

def get_drive_device_path():
    """Checks common device paths for an optical drive."""
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
    """Checks if the user has read/write permissions for the drive."""
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
    """Executes a command with sudo."""
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
    """Finds the most likely ROM path for a given console."""
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
    """Checks if a command-line tool is available."""
    log(f"Checking for tool: {tool_name}")
    if is_sandboxed():
        try:
            subprocess.run(["flatpak-spawn", "--host", "which", tool_name], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            log(f"Tool {tool_name}: OK")
            return True
        except:
            log(f"Tool {tool_name}: MISSING")
            return False
    else:
        found = shutil.which(tool_name) is not None
        log(f"Tool {tool_name}: {'OK' if found else 'MISSING'}")
        return found

def find_appimage(name_contains):
    """Scans for an AppImage file."""
    log(f"Scanning for AppImage containing: {name_contains}")
    app_dir = "/home/deck/Applications/"
    name_lower = name_contains.lower()

    if not os.path.exists(app_dir):
        log(f"Error: Directory {app_dir} does not exist.")
        return None

    try:
        for filename in os.listdir(app_dir):
            if name_lower in filename.lower() and filename.lower().endswith(".appimage"):
                found_path = os.path.join(app_dir, filename)
                log(f"Found AppImage: {found_path}")
                return found_path
    except Exception as e:
        log(f"Error while scanning {app_dir}: {e}")

    log(f"AppImage not found for: {name_contains}")
    return None

def get_disc_info(drive_path):
    """Retrieves disc volume size and file list."""
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
        log(f"Detected volume size: {volume_size_sectors} sectors.")
    else:
        log("Warning: Could not read disc volume size.")

    log("Getting file list (isoinfo -l)...")
    try:
        result_files = run_host_command(["isoinfo", "-l", "-i", drive_path])
        file_list_upper = result_files.stdout.upper()
        log("Successfully retrieved file list.")
    except Exception as e:
        log(f"Could not get file list: {e}")
        file_list_upper = ""

    return volume_size_sectors, file_list_upper

def detect_disc_type(volume_size_sectors, file_list_upper):
    """Analyzes disc info to determine its type."""
    log(f"Analyzing disc data: Size={volume_size_sectors} sectors.")
    if volume_size_sectors > 500000:
        log("-> Conclusion: Size > 500k sectors. This is a PS2_DVD.")
        return "PS2_DVD"
    log("-> Conclusion: Size indicates a CD. Checking for 'IOP' in file list...")
    if "IOP" in file_list_upper:
        log("-> Found 'IOP' in file list. This is a PS2_CD.")
        return "PS2_CD"
    log("-> 'IOP' not found. Assuming this is a PS1_CD.")
    return "PS1_CD"
