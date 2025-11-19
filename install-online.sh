#!/bin/bash

# ==============================================================================
# THE ORANGE DISK - SMART WEB INSTALLER (V2.0)
# ==============================================================================
# Ten skrypt automatycznie znajduje i pobiera najnowszy oficjalny "Release"
# z GitHuba, zapewniając, że użytkownik zawsze dostaje stabilną wersję.

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# --- Konfiguracja ---
GITHUB_REPO="wisnia87r/The-Orange-Disk-"
API_URL="https://api.github.com/repos/$GITHUB_REPO/releases/latest"
TMP_DIR="/tmp/the_orange_disk_install_$$"
# --- Koniec Konfiguracji ---

echo -e "${GREEN}--- The Orange Disk - Inteligentny Instalator Online ---${NC}"

# --- KROK 1: Znalezienie i pobranie najnowszego wydania ---
echo -e "\n${GREEN}Krok 1: Wyszukiwanie najnowszego wydania na GitHub...${NC}"

# Sprawdź, czy są dostępne wymagane narzędzia
if ! command -v curl &> /dev/null || ! command -v jq &> /dev/null; then
    echo -e "${RED}BŁĄD KRYTYCZNY: Programy 'curl' i 'jq' są wymagane, ale nie zostały znalezione.${NC}"
    echo "Na Steam Decku, możesz je zainstalować po wyłączeniu trybu tylko do odczytu."
    exit 1
fi

# Pobierz URL do pliku .zip z najnowszego wydania
ZIP_URL=$(curl -s $API_URL | jq -r ".zip_url")

if [ -z "$ZIP_URL" ] || [ "$ZIP_URL" == "null" ]; then
    echo -e "${RED}BŁĄD: Nie można było znaleźć informacji o najnowszym wydaniu. Czy na pewno istnieje?${NC}"
    exit 1
fi

echo "Pobieranie najnowszej wersji: $ZIP_URL"
curl -L "$ZIP_URL" -o "$TMP_DIR.zip" || { echo -e "${RED}BŁĄD: Pobieranie nie powiodło się.${NC}"; exit 1; }

echo "Rozpakowywanie plików..."
unzip -q "$TMP_DIR.zip" -d "$TMP_DIR"
# Pliki z release mają dodatkowy folder w środku, musimy go "wyjąć"
# Używamy `*` aby dopasować do dowolnej nazwy folderu wewnątrz archiwum
mv "$TMP_DIR"/*/ "$TMP_DIR/app"
rm "$TMP_DIR.zip"

# --- KROK 2: Uruchomienie głównego instalatora ---
echo -e "\n${GREEN}Krok 2: Uruchamianie głównego instalatora...${NC}"

cd "$TMP_DIR/app" || { echo -e "${RED}BŁĄD: Nie można przejść do folderu z pobranymi plikami.${NC}"; exit 1; }

chmod +x install.sh
./install.sh

# --- KROK 3: Sprzątanie ---
echo -e "\n${GREEN}Krok 3: Sprzątanie plików tymczasowych...${NC}"
rm -rf "$TMP_DIR"

echo -e "\n${GREEN}Wszystko gotowe!${NC}"

exit 0
