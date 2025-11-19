#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import pathlib
import subprocess
try:
    import vdf
except ImportError:
    print("Błąd: Moduł 'vdf' nie jest zainstalowany.")
    sys.exit(1)

# --- Konfiguracja ---
APP_NAME = "SteamStation PS edition"
INSTALL_DIR = pathlib.Path(__file__).parent.resolve()

IMAGE_FILES = {
    "hero": INSTALL_DIR / "hero.png",
    "grid": INSTALL_DIR / "vertical_capsule.png",
    "logo": INSTALL_DIR / "capsule.png"
}
# --- Koniec Konfiguracji ---

def find_steam_user_id():
    userdata_path = pathlib.Path.home() / ".local/share/Steam/userdata"
    if not userdata_path.exists(): return None
    user_dirs = [d for d in userdata_path.iterdir() if d.is_dir() and d.name.isdigit() and d.name != "0"]
    if not user_dirs: return None
    return max(user_dirs, key=lambda d: d.stat().st_mtime).name

def main():
    print("--- Konfiguracja grafik po pierwszym uruchomieniu ---")
    user_id = find_steam_user_id()
    if not user_id:
        print("Nie znaleziono ID użytkownika Steam.")
        sys.exit(1)

    localconfig_path = pathlib.Path.home() / f".local/share/Steam/userdata/{user_id}/config/localconfig.vdf"
    app_id = None
    
    if localconfig_path.exists():
        try:
            with open(localconfig_path, 'r', encoding='utf-8') as f: config_data = vdf.load(f)
            apps = config_data.get('UserLocalConfigStore', {}).get('Software', {}).get('Valve', {}).get('Steam', {}).get('apps', {})
            for aid, adata in apps.items():
                if adata.get('AppName') == APP_NAME:
                    app_id = aid
                    break
        except Exception:
            print("Ostrzeżenie: Nie udało się odczytać localconfig.vdf.")

    if not app_id:
        print("Nie udało się znaleźć AppID. Upewnij się, że Steam jest w pełni uruchomiony.")
        sys.exit(1)
        
    print(f"Znaleziono AppID: {app_id}")

    for art_type, image_path in IMAGE_FILES.items():
        if image_path.exists():
            command = ["steam", f"-set-custom-image", str(app_id), str(image_path), art_type]
            print(f"Ustawianie grafiki '{art_type}'...")
            try:
                subprocess.run(command, check=True, capture_output=True, text=True, timeout=20)
                print(f"  - Sukces.")
            except Exception as e:
                print(f"  - BŁĄD: {e}")
        else:
            print(f"  - Pominięto: Plik '{image_path.name}' nie istnieje.")
            
    # Utwórz plik-flagę, aby ta konfiguracja nie uruchomiła się ponownie
    (INSTALL_DIR / ".configured").touch()
    print("\nKonfiguracja zakończona. Grafiki zostały ustawione.")

if __name__ == "__main__":
    main()
