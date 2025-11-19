#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This script is the single source of truth for configuring Steam.
# It performs all necessary actions while Steam is closed.

import sys
import pathlib
import shutil
import zlib
import json

try:
    import vdf
except ImportError:
    print("[Py] Błąd: Moduł 'vdf' nie jest zainstalowany.", flush=True)
    sys.exit(1)

# --- Configuration ---
APP_NAME = "The Orange Disk Playstation Edition"
INSTALL_DIR = pathlib.Path(__file__).parent.resolve()
LAUNCHER_PATH = INSTALL_DIR / "launcher.sh"
ASSETS_DIR = INSTALL_DIR / "assets"
ICON_PATH = ASSETS_DIR / "icons" / "icon.png"

IMAGE_TARGETS = {
    "hero": ASSETS_DIR / "artwork" / "hero.png",
    "grid": ASSETS_DIR / "artwork" / "vertical_capsule.png",
    "logo": ASSETS_DIR / "artwork" / "capsule.png"
}

# --- Helper Functions ---

def log(message):
    """Prints a message to stdout for the main install log."""
    print(f"[Py] {message}", flush=True)

def calculate_app_id(exe_path, app_name):
    """Calculates the shortcut AppID using the CRC32 algorithm."""
    log(f"  - Calculating AppID with Exe='{exe_path}' and AppName='{app_name}'")
    combined_string = str(exe_path) + app_name
    crc = zlib.crc32(combined_string.encode('utf-8'))
    return (crc | 0x80000000)

def find_steam_user_id():
    """Finds the most recently used Steam user ID."""
    log("Searching for Steam user ID...")
    userdata_path = pathlib.Path.home() / ".local/share/Steam/userdata"
    if not userdata_path.exists():
        log("  - CRITICAL: Steam userdata directory not found.")
        return None
    user_dirs = [d for d in userdata_path.iterdir() if d.is_dir() and d.name.isdigit() and d.name != "0"]
    if not user_dirs:
        log("  - CRITICAL: No user directories found in userdata.")
        return None
    
    latest_user_dir = max(user_dirs, key=lambda d: d.stat().st_mtime)
    log(f"  - Found user ID: {latest_user_dir.name}")
    return latest_user_dir.name

# --- Main Execution ---

def main():
    log("--- Rozpoczęcie konfiguracji Steam (metoda offline) ---")
    
    # Krok 1: Znajdź ID użytkownika
    user_id = find_steam_user_id()
    if not user_id:
        sys.exit(1)

    # Krok 2: Oblicz AppID
    log("Krok 2: Obliczanie AppID.")
    unsigned_app_id = calculate_app_id(LAUNCHER_PATH, APP_NAME)
    signed_app_id = unsigned_app_id - 4294967296 if unsigned_app_id > 2147483647 else unsigned_app_id
    log(f"  - AppID (unsigned, dla nazw plików): {unsigned_app_id}")
    log(f"  - AppID (signed, dla shortcuts.vdf): {signed_app_id}")

    # Krok 3: Zaktualizuj plik shortcuts.vdf
    log("Krok 3: Modyfikacja pliku shortcuts.vdf.")
    shortcuts_vdf_path = pathlib.Path.home() / f".local/share/Steam/userdata/{user_id}/config/shortcuts.vdf"
    log(f"  - Ścieżka do pliku: {shortcuts_vdf_path}")

    new_shortcut_data = {
        'AppName': APP_NAME, 'Exe': str(LAUNCHER_PATH), 'StartDir': str(INSTALL_DIR),
        'LaunchOptions': "", 'Icon': str(ICON_PATH) if ICON_PATH.exists() else "", 'IsHidden': 0, 
        'AllowDesktopConfig': 1, 'AllowOverlay': 1, 'OpenVR': 0, 'tags': {}, 'AppId': signed_app_id
    }
    
    shortcuts_data = {'shortcuts': {}}
    if shortcuts_vdf_path.exists():
        try:
            with open(shortcuts_vdf_path, 'rb') as f: shortcuts_data = vdf.binary_load(f)
            log("  - Odczytano istniejący plik shortcuts.vdf.")
        except Exception as e:
            log(f"  - OSTRZEŻENIE: Nie można odczytać shortcuts.vdf, zostanie nadpisany. Błąd: {e}")
            
    clean_shortcuts = {
        str(i): s for i, s in enumerate(
            [sc for sc in shortcuts_data.get('shortcuts', {}).values() if sc.get('AppName') != APP_NAME]
        )
    }
    new_index = str(len(clean_shortcuts))
    clean_shortcuts[new_index] = new_shortcut_data
    shortcuts_data['shortcuts'] = clean_shortcuts
    log(f"  - Przygotowano nowy wpis dla '{APP_NAME}' na pozycji {new_index}.")

    try:
        with open(shortcuts_vdf_path, 'wb') as f: vdf.binary_dump(shortcuts_data, f)
        log("  - SUKCES: Plik skrótów został pomyślnie zapisany.")
    except Exception as e:
        log(f"  - KRYTYCZNY BŁĄD zapisu shortcuts.vdf: {e}")
        sys.exit(1)

    # Krok 4: Skopiuj grafiki
    log("Krok 4: Kopiowanie grafik do folderu /grid/.")
    grid_dir = pathlib.Path.home() / f".local/share/Steam/userdata/{user_id}/config/grid"
    grid_dir.mkdir(parents=True, exist_ok=True)
    log(f"  - Katalog docelowy: {grid_dir}")

    for art_type, source_path in IMAGE_TARGETS.items():
        if source_path.exists():
            target_name = f"{unsigned_app_id}{'_hero' if art_type == 'hero' else ('p' if art_type == 'grid' else '')}.png"
            target_path = grid_dir / target_name
            try:
                shutil.copy(source_path, target_path)
                log(f"  - Skopiowano '{source_path.name}' -> '{target_name}'")
            except Exception as e:
                log(f"  - BŁĄD podczas kopiowania '{source_path.name}': {e}")
        else:
            log(f"  - POMINIĘTO: Plik '{source_path.name}' nie istnieje.")
            
    log("\n--- Konfiguracja zakończona pomyślnie! ---")

if __name__ == "__main__":
    main()
