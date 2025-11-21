#!/bin/bash

# ==============================================================================
# THE ORANGE DISK - STEAM RESTART HELPER (V1.0)
# ==============================================================================
# Ten skrypt jest uruchamiany w tle, aby bezpiecznie zrestartować Steam
# i skonfigurować nowo dodaną grę.

# --- Konfiguracja ---
INSTALL_DIR="$HOME/Applications/TheOrangeDisk"
LOG_FILE="$INSTALL_DIR/restart.log"
TASK_FILE="$HOME/.the_orange_disk.task"
VENV_PYTHON_BIN="$INSTALL_DIR/venv/bin/python3"
ADD_GAME_SCRIPT="$INSTALL_DIR/add_game_to_steam.py"
# --- Koniec Konfiguracji ---

# Clear LD_PRELOAD to avoid Steam overlay errors
unset LD_PRELOAD

# CRITICAL: Detach completely from parent process (Steam)
# This prevents the script from being killed when Steam closes
setsid bash -c '
# Re-define variables inside the detached process
INSTALL_DIR="'"$INSTALL_DIR"'"
LOG_FILE="'"$LOG_FILE"'"
TASK_FILE="'"$TASK_FILE"'"
VENV_PYTHON_BIN="'"$VENV_PYTHON_BIN"'"
ADD_GAME_SCRIPT="'"$ADD_GAME_SCRIPT"'"

# Przekieruj cały output do dedykowanego pliku logu
> "$LOG_FILE"
exec &> >(tee -a "$LOG_FILE")

log() {
    echo "[Restart Helper] $(date +"%H:%M:%S"): $1"
}

log "--- Uruchomiono pomocnika restartu Steam (odłączony proces) ---"

# Daj głównej aplikacji chwilę na całkowite zamknięcie
sleep 3

# Krok 1: Sprawdź, czy zadanie istnieje
log "DEBUG: Sprawdzanie pliku zadania: $TASK_FILE"
if [ ! -f "$TASK_FILE" ]; then
    log "BŁĄD: Nie znaleziono pliku zadania ($TASK_FILE). Zakończono."
    exit 1
fi
log "Znaleziono plik zadania. Odczytywanie..."
log "DEBUG: Zawartość pliku zadania:"
cat "$TASK_FILE" >> "$LOG_FILE"
source "$TASK_FILE"
log "DEBUG: Zmienne po wczytaniu:"
log "DEBUG:   GAME_NAME='$GAME_NAME'"
log "DEBUG:   ROM_PATH='$ROM_PATH'"
log "DEBUG:   ARTWORK_GRID='$ARTWORK_GRID'"
log "DEBUG:   ARTWORK_GRID_VERTICAL='$ARTWORK_GRID_VERTICAL'"
log "DEBUG:   ARTWORK_HERO='$ARTWORK_HERO'"
log "DEBUG:   ARTWORK_LOGO='$ARTWORK_LOGO'"
log "DEBUG:   ARTWORK_ICON='$ARTWORK_ICON'"

# Krok 2: Wykryj aktualny tryb Steam i zamknij go
log "Sprawdzanie i zamykanie Steam..."
STEAM_ARGS=""

# Check if running in gamepadui/gaming mode
if pgrep -af "steam" 2>/dev/null | grep -qi -- "-gamepadui\|steamdeck\|gamescope"; then
    log "Wykryto tryb Big Picture (gamepadui)."
    STEAM_ARGS="-gamepadui"
else
    log "Tryb: Desktop (lub Steam nie wykryty)."
fi

# Always try to close Steam (in case it is running but not detected)
log "Zamykanie wszystkich procesów Steam..."
log "DEBUG: Uruchamianie pkill..."

# Run pkill commands with timeout - do not use subshell with wait
pkill -9 -i steam 2>/dev/null || true
pkill -9 reaper 2>/dev/null || true
pkill -9 steamwebhelper 2>/dev/null || true
pkill -9 fossilize 2>/dev/null || true

log "DEBUG: Czekanie na całkowite zamknięcie Steam..."
# Wait up to 10 seconds for all Steam processes to die
for i in {1..10}; do
    if ! pgrep -i steam > /dev/null 2>&1 && ! pgrep reaper > /dev/null 2>&1; then
        log "DEBUG: Wszystkie procesy Steam zamknięte po $i sekundach"
        break
    fi
    log "DEBUG: Czekam... ($i/10)"
    sleep 1
done

# Final check
if pgrep -i steam > /dev/null 2>&1 || pgrep reaper > /dev/null 2>&1; then
    log "OSTRZEŻENIE: Niektóre procesy Steam nadal działają!"
    pgrep -a steam >> "$LOG_FILE" 2>&1 || true
    pgrep -a reaper >> "$LOG_FILE" 2>&1 || true
else
    log "Procesy Steam zostały całkowicie zamknięte."
fi

# Extra safety delay
sleep 2

# Krok 4: Wykonaj zadanie (dodaj grę)
log "DEBUG: Rozpoczynam dodawanie gry do Steam..."
log "Uruchamianie skryptu konfiguracyjnego dla gry: '$GAME_NAME'"
log "ROM: $ROM_PATH"
log "Artwork: $ARTWORK_PATH"
log "DEBUG: Python: $VENV_PYTHON_BIN"
log "DEBUG: Script: $ADD_GAME_SCRIPT"
log "DEBUG: Sprawdzanie czy pliki istnieją..."
[ -f "$VENV_PYTHON_BIN" ] && log "DEBUG: Python exists: YES" || log "DEBUG: Python exists: NO"
[ -f "$ADD_GAME_SCRIPT" ] && log "DEBUG: Script exists: YES" || log "DEBUG: Script exists: NO"
[ -f "$ROM_PATH" ] && log "DEBUG: ROM exists: YES" || log "DEBUG: ROM exists: NO"
[ -f "$ARTWORK_PATH" ] && log "DEBUG: Artwork exists: YES" || log "DEBUG: Artwork exists: NO"

log "DEBUG: Uruchamianie skryptu Python..."

# Check shortcuts.vdf before
SHORTCUTS_FILE="$HOME/.local/share/Steam/userdata/79070216/config/shortcuts.vdf"
if [ -f "$SHORTCUTS_FILE" ]; then
    BEFORE_SIZE=$(stat -c%s "$SHORTCUTS_FILE")
    BEFORE_TIME=$(stat -c%Y "$SHORTCUTS_FILE")
    log "DEBUG: shortcuts.vdf przed: rozmiar=$BEFORE_SIZE, czas=$BEFORE_TIME"
else
    log "DEBUG: shortcuts.vdf nie istnieje przed dodaniem"
    BEFORE_SIZE=0
    BEFORE_TIME=0
fi

if "$VENV_PYTHON_BIN" "$ADD_GAME_SCRIPT" "$GAME_NAME" "$ROM_PATH" "$ARTWORK_GRID" "$ARTWORK_GRID_VERTICAL" "$ARTWORK_HERO" "$ARTWORK_LOGO" "$ARTWORK_ICON"; then
    log "Gra została pomyślnie dodana do Steam!"

    # Check shortcuts.vdf after
    sleep 1
    if [ -f "$SHORTCUTS_FILE" ]; then
        AFTER_SIZE=$(stat -c%s "$SHORTCUTS_FILE")
        AFTER_TIME=$(stat -c%Y "$SHORTCUTS_FILE")
        log "DEBUG: shortcuts.vdf po: rozmiar=$AFTER_SIZE, czas=$AFTER_TIME"

        if [ "$AFTER_TIME" -gt "$BEFORE_TIME" ]; then
            log "DEBUG: Plik shortcuts.vdf został zaktualizowany! ✓"
        else
            log "OSTRZEŻENIE: Plik shortcuts.vdf NIE został zaktualizowany!"
        fi
    else
        log "BŁĄD: shortcuts.vdf nie istnieje po dodaniu gry!"
    fi
else
    EXIT_CODE=$?
    log "BŁĄD: Nie udało się dodać gry do Steam (kod: $EXIT_CODE)"
    log "DEBUG: Sprawdzanie ostatnich błędów..."
fi

# Krok 5: Uruchom Steam ponownie
log "DEBUG: Rozpoczynam restart Steam..."
log "==================================================================="
log "GRA '$GAME_NAME' ZOSTAŁA DODANA DO STEAM!"
log "==================================================================="
log ""

# CRITICAL: Wait to ensure shortcuts.vdf is fully written and synced
log "DEBUG: Czekanie 5 sekund na synchronizację plików..."
sleep 5
sync  # Force filesystem sync

log ""
log "==================================================================="
log "GRA ZOSTAŁA DODANA! URUCHAMIANIE STEAM..."
log "==================================================================="

# Additional wait to ensure file system has fully committed changes
log "DEBUG: Dodatkowe opóźnienie przed restartem Steam..."
sleep 3

# Restart Steam
log "Uruchamianie Steam..."
STEAM_SCRIPT="$HOME/.local/share/Steam/steam.sh"

if [ ! -f "$STEAM_SCRIPT" ]; then
    log "BŁĄD: Nie znaleziono skryptu Steam: $STEAM_SCRIPT"
    log "Uruchom Steam ręcznie aby zobaczyć nową grę."
else
    # Launch Steam in background with appropriate mode
    if [ -n "$STEAM_ARGS" ] && [ "$STEAM_ARGS" = "-gamepadui" ]; then
        log "Uruchamianie Steam w trybie Big Picture..."
        nohup "$STEAM_SCRIPT" -gamepadui > /dev/null 2>&1 &
    else
        log "Uruchamianie Steam w trybie Desktop..."
        nohup "$STEAM_SCRIPT" > /dev/null 2>&1 &
    fi

    log "Steam został uruchomiony ponownie!"
    log "Gra '$GAME_NAME' powinna być widoczna w bibliotece Steam."
fi

# Send desktop notification
notify-send "The Orange Disk" "Gra \"$GAME_NAME\" została dodana do Steam!\nSteam został uruchomiony ponownie." -i applications-games 2>/dev/null || true

# Krok 6: Posprzątaj
log "Czyszczenie pliku zadania."
rm -f "$TASK_FILE"

log "--- Zadanie zakończone pomyślnie! ---"
exit 0

' & # End of setsid bash -c block - run in background and detach

# Original script exits immediately, allowing the detached process to continue
exit 0
