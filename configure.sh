#!/bin/bash

# ==============================================================================
# THE ORANGE DISK - MANUAL CONFIGURATOR (V70.0)
# ==============================================================================
# Ten skrypt pozwala na ręczne zarządzanie skrótem i grafikami w Steam.

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# --- Konfiguracja ---
INSTALL_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
VENV_PYTHON_BIN="$INSTALL_DIR/venv/bin/python3"
# Używamy naszego ostatniego, sprawdzonego skryptu konfiguracyjnego
CONFIG_SCRIPT_PY="set_steam_config.py" 
# --- Koniec Konfiguracji ---

# Sprawdzenie, czy Python venv istnieje
if [ ! -f "$VENV_PYTHON_BIN" ]; then
    echo -e "${RED}BŁĄD: Środowisko wirtualne nie istnieje. Uruchom najpierw 'install.sh'.${NC}"
    exit 1
fi

# Main logic
case "$1" in
    add)
        echo -e "${GREEN}--- Task: Adding/Updating shortcut ---${NC}"
        if pgrep -x "steam" > /dev/null; then
            echo -e "${RED}ERROR: Steam is running. Close it completely and try again.${NC}"
            exit 1
        fi
        "$VENV_PYTHON_BIN" "$CONFIG_SCRIPT_PY" --add
        echo -e "${GREEN}Success. You can now launch Steam.${NC}"
        ;;
    set-artwork)
        echo -e "${GREEN}--- Task: Setting artwork ---${NC}"
        if ! pgrep -x "steam" > /dev/null; then
            echo -e "${RED}ERROR: Steam is not running. Launch it and try again.${NC}"
            exit 1
        fi
        "$VENV_PYTHON_BIN" "$CONFIG_SCRIPT_PY" --set
        echo -e "${GREEN}Success. Restart Steam to see changes.${NC}"
        ;;
    *)
        echo "Usage: $0 [option]"
        echo "Available options:"
        echo "  add          - Adds or updates the shortcut in Steam (requires Steam to be closed)."
        echo "  set-artwork  - Sets artwork for existing shortcut (requires Steam to be running)."
        exit 1
        ;;
esac

exit 0
