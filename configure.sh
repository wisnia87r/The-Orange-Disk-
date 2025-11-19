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

# Główna logika
case "$1" in
    add)
        echo -e "${GREEN}--- Zadanie: Dodawanie/Aktualizowanie skrótu ---${NC}"
        if pgrep -x "steam" > /dev/null; then
            echo -e "${RED}BŁĄD: Steam jest uruchomiony. Zamknij go całkowicie i spróbuj ponownie.${NC}"
            exit 1
        fi
        "$VENV_PYTHON_BIN" "$CONFIG_SCRIPT_PY" --add
        echo -e "${GREEN}Sukces. Możesz teraz uruchomić Steam.${NC}"
        ;;
    set-artwork)
        echo -e "${GREEN}--- Zadanie: Ustawianie grafik ---${NC}"
        if ! pgrep -x "steam" > /dev/null; then
            echo -e "${RED}BŁĄD: Steam nie jest uruchomiony. Uruchom go i spróbuj ponownie.${NC}"
            exit 1
        fi
        "$VENV_PYTHON_BIN" "$CONFIG_SCRIPT_PY" --set
        echo -e "${GREEN}Sukces. Zrestartuj Steam, aby zobaczyć zmiany.${NC}"
        ;;
    *)
        echo "Użycie: $0 [opcja]"
        echo "Dostępne opcje:"
        echo "  add          - Dodaje lub aktualizuje skrót w Steam (wymaga zamkniętego klienta)."
        echo "  set-artwork  - Ustawia grafiki dla istniejącego skrótu (wymaga uruchomionego klienta)."
        exit 1
        ;;
esac

exit 0
