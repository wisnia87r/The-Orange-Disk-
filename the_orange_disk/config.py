# -*- coding: utf-8 -*-

# This file contains all the configuration constants for the application.
import os

# --- File Paths ---
# Path to the configuration file where user settings (like language) are stored.
CONFIG_PATH = os.path.expanduser("~/.the_orange_disk.conf")

# --- Internationalization (i18n) System ---
TRANSLATIONS = {
    # Main Menu
    "PLAY_GAME": {"PL": "GRAJ Z PŁYTĄ", "EN": "PLAY FROM DISC"},
    "RIP_DISC": {"PL": "ZGRAJ PŁYTĘ (Kopia)", "EN": "RIP DISC (Backup)"},
    "HOW_TO_USE": {"PL": "Instrukcja", "EN": "How to Use"},
    "ABOUT": {"PL": "O twórcy", "EN": "About"},
    "SETTINGS": {"PL": "Ustawienia", "EN": "Settings"},
    "EXIT": {"PL": "WYJŚCIE", "EN": "EXIT"},

    # Footer
    "SELECT": {"PL": "Wybierz", "EN": "Select"},
    "BACK_FOOTER": {"PL": "Wyjście", "EN": "Back"},

    # How to Use Screen
    "HOW_TO_TITLE": {"PL": "INSTRUKCJA UŻYTKOWANIA", "EN": "HOW TO USE"},
    "HOW_TO_PLAY": {"PL": "GRAJ Z PŁYTĄ: Uruchamia grę bezpośrednio z napędu.", "EN": "PLAY FROM DISC: Launches the game directly from the drive."},
    "HOW_TO_RIP": {"PL": "ZGRAJ PŁYTĘ: Tworzy cyfrową kopię (backup) gry na dysku.", "EN": "RIP DISC: Creates a digital backup of your game on the disk."},
    "HOW_TO_SETTINGS": {"PL": "USTAWIENIA: Zmień język interfejsu.", "EN": "SETTINGS: Change the interface language."},
    "HOW_TO_EXIT": {"PL": "WYJŚCIE: Zamyka aplikację.", "EN": "EXIT: Closes the application."},

    # About Screen
    "ABOUT_TITLE": {"PL": "O TWÓRCY", "EN": "ABOUT"},
    "ABOUT_CREATED_BY": {"PL": "Stworzone przez: wisnia87r", "EN": "Created by: wisnia87r"},

    # Settings Screen
    "SETTINGS_LANGUAGE_PL": {"PL": "Język: Polski", "EN": "Language: Polish"},
    "SETTINGS_LANGUAGE_EN": {"PL": "Język: Angielski", "EN": "Language: English"},
    "SETTINGS_BACK": {"PL": "Powrót", "EN": "Back"},

    # System Messages & Prompts
    "DRIVE_NOT_FOUND_PROMPT": {"PL": "Włóż napęd USB z płytą...", "EN": "Insert USB drive with disc..."},
    "PERMS_REQUIRED": {"PL": "Wymagane uprawnienia. Hasło SUDO:", "EN": "Admin permissions required. SUDO Password:"},
    "FIXING_PERMS": {"PL": "Naprawianie uprawnień...", "EN": "Fixing permissions..."},
    "READY_CHECKING_TOOLS": {"PL": "Gotowe! Sprawdzam narzędzia...", "EN": "Done! Checking tools..."},
    "TOOL_NOT_FOUND": {"PL": "Brak '{tool}'. Hasło SUDO:", "EN": "Missing '{tool}'. SUDO Password:"},
    "INSTALLING_TOOL": {"PL": "Instalacja '{tool}'...", "EN": "Installing '{tool}'..."},
    "ALL_READY": {"PL": "Wszystko gotowe!", "EN": "All ready!"},
    "REPAIR_OK_LAUNCHING": {"PL": "Naprawa OK. Uruchamiam wykrywanie gry...", "EN": "Repair OK. Detecting game..."},
    "REPAIR_OK_RIPPING": {"PL": "Naprawa OK. Uruchamiam proces zgrywania...", "EN": "Repair OK. Starting rip process..."},
    "INSTALL_OK_LAUNCHING": {"PL": "Instalacja OK. Uruchamiam wykrywanie gry...", "EN": "Install OK. Detecting game..."},
    "INSTALL_OK_RIPPING": {"PL": "Instalacja OK. Uruchamiam proces zgrywania...", "EN": "Install OK. Starting rip process..."},
    "INSTALL_ERROR": {"PL": "Błąd instalacji: {e}", "EN": "Installation error: {e}"},
    "GAME_NAME_PROMPT": {"PL": "Nazwa gry:", "EN": "Game Name:"},
    "DETECTING_DISC": {"PL": "Wykrywanie płyty...", "EN": "Detecting disc..."},
    "DISC_TYPE_UNKNOWN": {"PL": "Nie rozpoznano płyty.", "EN": "Disc not recognized."},
    "RIP_PSX_NO_CDRDAO": {"PL": "Błąd krytyczny: Brak cdrdao dla PS1.", "EN": "Critical Error: cdrdao missing for PS1 rip."},
    "RIP_STARTING": {"PL": "Zgrywanie: {game_name}", "EN": "Ripping: {game_name}"},
    "RIP_PROGRESS_START": {"PL": "Rozpoczynanie...", "EN": "Starting..."},
    "RIP_PROGRESS_TIME": {"PL": "Czas: {curr_m:02d}:{curr_s:02d} / {total_m:02d}:{total_s:02d}", "EN": "Time: {curr_m:02d}:{curr_s:02d} / {total_m:02d}:{total_s:02d}"},
    "RIP_PROGRESS_SIZE": {"PL": "{curr_mb} MB / {total_mb} MB", "EN": "{curr_mb} MB / {total_mb} MB"},
    "RIP_FINALIZING": {"PL": "Finalizowanie...", "EN": "Finalizing..."},
    "RIP_ERROR_SMALL_FILE": {"PL": "Plik wynikowy zbyt mały lub nie istnieje.", "EN": "Resulting file is too small or missing."},
    "RIP_SUCCESS": {"PL": "Gotowe!\n{save_path}", "EN": "Done!\n{save_path}"},
    "RIP_ERROR_CONSOLE": {"PL": "Błąd (szczegóły w konsoli).", "EN": "Error (see console for details)."},
    "RIP_CLEANUP": {"PL": "Czyszczenie po anulowaniu...", "EN": "Cleaning up after cancellation..."},
    "DRIVE_NOT_FOUND_ERROR": {"PL": "Włóż napęd USB z płytą,\naby aktywować tę opcję.", "EN": "Insert USB drive with disc\nto enable this option."},
    "STARTING_PS1": {"PL": "Start: DuckStation (PS1)", "EN": "Start: DuckStation (PS1)"},
    "STARTING_PS2": {"PL": "Start: PCSX2 ({disc_type})", "EN": "Start: PCSX2 ({disc_type})"},
    "LAUNCH_ERROR_UNKNOWN": {"PL": "Nie rozpoznano płyty (UNKNOWN).", "EN": "Disc not recognized (UNKNOWN)."},
    "THREAD_ERROR": {"PL": "!!! KRYTYCZNY BŁĄD WĄTKU: {e}", "EN": "!!! CRITICAL THREAD ERROR: {e}"},
    "GAME_OVER": {"PL": "Koniec gry.", "EN": "Game finished."},
    "APPIMAGE_NOT_FOUND": {"PL": "Nie znaleziono AppImage dla: {name}", "EN": "AppImage not found for: {name}"},
    "LOADING_BG_ERROR": {"PL": "BŁĄD ładowania tła: {e}", "EN": "ERROR loading background: {e}"},
    "FONT_ERROR": {"PL": "Nie znaleziono czcionki 'sans', używam domyślnej.", "EN": "Font 'sans' not found, using default."},

    # Boot Animation
    "BOOT_TITLE": {"PL": "The Orange Disk", "EN": "The Orange Disk"},
    "BOOT_SUBTITLE": {"PL": "Playstation Edition", "EN": "Playstation Edition"},
    "BOOT_SKIP": {"PL": "Pomijanie animacji startowej...", "EN": "Skipping boot animation..."},

    # GUI States
    "LOADING_TITLE": {"PL": "PRACUJĘ...", "EN": "LOADING..."},
    "CANCEL_BUTTON": {"PL": "Anuluj", "EN": "Cancel"},
    "SUCCESS_TITLE": {"PL": "SUKCES", "EN": "SUCCESS"},
    "ERROR_TITLE": {"PL": "BŁĄD", "EN": "ERROR"},
    "CONFIRM_BUTTON": {"PL": "Naciśnij KRZYŻYK (A)", "EN": "Press CROSS (A)"},
}

# --- UI Colors & Constants ---
BLACK = (0, 0, 0)
PS2_VOID_DARK = (10, 10, 30)
PS2_VOID_LIGHT = (20, 20, 60)
PS2_TEXT = (200, 200, 220)
PS2_TEXT_BRIGHT = (255, 255, 255)
PS2_SHADOW = (5, 5, 10)
PS1_ORANGE = (255, 160, 0)
PS1_GREEN = (0, 200, 100)
PS1_RED = (220, 50, 50)
PS1_BLUE = (80, 80, 220)
PS1_PINK = (220, 80, 220)
GRAYED_OUT = (80, 80, 90)

# The application is rendered to an internal surface and then scaled up.
INTERNAL_WIDTH = 1280
INTERNAL_HEIGHT = 800
