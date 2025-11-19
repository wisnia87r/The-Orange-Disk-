#!/bin/bash
# ==============================================================================
# STEAMSTATION WRAPPER (WARSTWA POSREDNIA) - WERSJA 50.0
# ==============================================================================
# Używa 'nohup' do uruchomienia Pythona w tle i natychmiastowego wyjścia,
# co pozwala Steamowi myśleć, że aplikacja jest "gotowa" do monitorowania,
# bez zamykania procesu Pythona.

INSTALL_DIR="$HOME/Applications/SteamStation"
PYTHON_BIN="/usr/bin/python3"
SCRIPT_NAME="steamstation.py"

# Nadanie uprawnień wykonania na wszelki wypadek
chmod +x "$INSTALL_DIR/$SCRIPT_NAME"

# Przejście do katalogu roboczego
cd "$INSTALL_DIR" || exit 1

echo "Uruchamianie SteamStation w tle..."

# Używamy nohup, aby uruchomić Pythona, odłączyć go od terminala i sesji Basha,
# i natychmiast zwolnić skrypt Basha. Steam monitoruje tylko nasz launcher.sh,
# który zamyka się natychmiast, a Python pozostaje uruchomiony.
nohup "$PYTHON_BIN" "$INSTALL_DIR/$SCRIPT_NAME" > /dev/null 2>&1 &

echo "Launcher zakończył działanie Basha. Python działa w tle."
# Ten skrypt Basha może się teraz bezpiecznie zakończyć
exit 0
