#!/bin/bash

# ==============================================================================
# THE ORANGE DISK - DIAGNOSTIC LAUNCHER (V2.0)
# ==============================================================================
# Ten launcher używa absolutnych ścieżek i tworzy plik logu, aby zapewnić
# niezawodne uruchomienie i łatwą diagnostykę.

# Ustalenie absolutnej ścieżki do katalogu, w którym znajduje się skrypt
INSTALL_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
LOG_FILE="$INSTALL_DIR/launcher.log"
PYTHON_EXEC="$INSTALL_DIR/venv/bin/python3"

# Czyszczenie starego logu przy starcie
echo "--- The Orange Disk Launcher Log ---" > "$LOG_FILE"
echo "Time: $(date)" >> "$LOG_FILE"
echo "Install Dir: $INSTALL_DIR" >> "$LOG_FILE"
echo "Python Exec: $PYTHON_EXEC" >> "$LOG_FILE"

# Sprawdzenie, czy interpreter Pythona istnieje
if [ ! -f "$PYTHON_EXEC" ]; then
    echo "BŁĄD KRYTYCZNY: Nie znaleziono interpretera Python w '$PYTHON_EXEC'!" >> "$LOG_FILE"
    exit 1
fi

echo "Uruchamianie aplikacji jako modułu..." >> "$LOG_FILE"

# Uruchomienie aplikacji, przekierowując cały output (stdout i stderr) do pliku logu
"$PYTHON_EXEC" -m the_orange_disk >> "$LOG_FILE" 2>&1

echo "Aplikacja zakończyła działanie." >> "$LOG_FILE"
