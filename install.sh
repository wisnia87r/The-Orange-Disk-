#!/bin/bash

# ==============================================================================
# THE ORANGE DISK - INSTALLER (V80.0 - OSTATECZNA POPRAWKA ARGUMENTU)
# ==============================================================================
# Ta wersja naprawia krytyczny błąd braku argumentu przy wywoływaniu
# skryptu konfiguracyjnego.

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# --- Konfiguracja ---
INSTALL_DIR="$HOME/Applications/TheOrangeDisk"
LOG_FILE="$INSTALL_DIR/install.log"
VENV_DIR="$INSTALL_DIR/venv"
SYSTEM_PYTHON_BIN="/usr/bin/python3"
VENV_PYTHON_BIN="$VENV_DIR/bin/python3"
VENV_PIP_BIN="$VENV_DIR/bin/pip"
CONFIG_SCRIPT="set_steam_config.py"
# --- Koniec Konfiguracji ---

# Przygotuj logowanie
mkdir -p "$INSTALL_DIR"
> "$LOG_FILE"
exec &> >(tee -a "$LOG_FILE")

# --- Funkcje pomocnicze ---
log() {
    echo "[Install.sh] $(date +'%H:%M:%S'): $1"
}

# --- Główny skrypt ---
echo "--- The Orange Disk Super-Instalator (v80) ---"
log "Rozpoczęcie instalacji."

# Krok 1: Przygotowanie i aktualizacja plików
log "Krok 1: Przygotowanie i aktualizacja plików."

SOURCE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
if [ "$SOURCE_DIR" != "$INSTALL_DIR" ]; then
    log "Wykryto uruchomienie ze źródła ($SOURCE_DIR). Kopiowanie plików do '$INSTALL_DIR'..."
    rsync -a --delete "$SOURCE_DIR/" "$INSTALL_DIR/" --exclude ".git" --exclude ".idea"
fi

cd "$INSTALL_DIR" || { log "KRYTYCZNY BŁĄD: Nie można przejść do katalogu instalacyjnego '$INSTALL_DIR'."; exit 1; }
log "Pracuję w katalogu: $(pwd)"

# Krok 2: Czyszczenie i weryfikacja Steam
log "Krok 2: Czyszczenie i weryfikacja statusu Steam."
log "Usuwanie starych, potencjalnie konfliktowych skryptów..."
rm -f add_shortcut.py find_and_set_artwork.py set_artwork.sh configure.sh cleanup.sh configure_steam.py

if pgrep -x "steam" > /dev/null; then
    log "Wykryto uruchomiony proces Steam. Zamykanie..."
    steam -shutdown
    while pgrep -x "steam" > /dev/null; do echo -n "."; sleep 1; done
    log "Steam został zamknięty."
else
    log "Steam nie jest uruchomiony. To dobrze."
fi

# Krok 3: Instalacja zależności
log "Krok 3: Instalowanie/aktualizowanie zależności..."
if [ ! -d "$VENV_DIR" ]; then
    log "Tworzenie nowego środowiska wirtualnego..."
    "$SYSTEM_PYTHON_BIN" -m venv "$VENV_DIR"
fi
log "Instalowanie pygame i vdf..."
"$VENV_PIP_BIN" install --upgrade pygame vdf
log "Nadawanie uprawnień wykonywania..."
chmod +x ./*.sh

# Krok 4: Konfiguracja Steam (wszystko w jednym kroku, gdy Steam jest zamknięty)
log "Krok 4: Uruchamianie głównego skryptu konfiguracyjnego z argumentem --add..."
"$VENV_PYTHON_BIN" "./$CONFIG_SCRIPT" --add

# Krok 5: Zakończenie
log "Krok 5: Zakończenie."
log "--- INSTALACJA ZAKOŃCZONA! ---"
echo -e "\n${GREEN}Wszystko gotowe. Uruchom Steam, aby zobaczyć w pełni skonfigurowany skrót.${NC}"
echo "Jeśli nadal występuje problem, prześlij zawartość pliku 'install.log' z folderu '$INSTALL_DIR'."

exit 0
