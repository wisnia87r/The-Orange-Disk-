#!/bin/bash

# ==============================================================================
# THE ORANGE DISK - WEB INSTALLER (V1.0)
# ==============================================================================
# Ten skrypt pobiera najnowszą wersję aplikacji z GitHub, a następnie
# uruchamia główny instalator.

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# --- Konfiguracja ---
GITHUB_REPO="wisnia87r/The-Orange-Disk-"
REPO_URL="https://github.com/$GITHUB_REPO.git"
ZIP_URL="https://github.com/$GITHUB_REPO/archive/refs/heads/main.zip"
TMP_DIR="/tmp/the_orange_disk_install_$$" # Używamy unikalnego folderu tymczasowego
# --- Koniec Konfiguracji ---

echo -e "${GREEN}--- The Orange Disk - Instalator Online ---${NC}"
echo "Ten skrypt pobierze i zainstaluje najnowszą wersję aplikacji."

# --- KROK 1: Pobieranie plików ---
echo -e "\n${GREEN}Krok 1: Pobieranie najnowszej wersji z GitHub...${NC}"

# Metoda 1: Użyj 'git', jeśli jest dostępny (najlepsza metoda)
if command -v git &> /dev/null; then
    echo "Znaleziono 'git'. Klonowanie repozytorium..."
    git clone --depth 1 "$REPO_URL" "$TMP_DIR" || {
        echo -e "${RED}BŁĄD: Klonowanie repozytorium nie powiodło się. Sprawdź połączenie z internetem.${NC}"
        exit 1
    }
# Metoda 2: Użyj 'curl' lub 'wget' jako fallback
else
    echo "Nie znaleziono 'git'. Próba pobrania archiwum .zip..."
    if ! command -v unzip &> /dev/null; then
        echo -e "${RED}BŁĄD KRYTYCZNY: Program 'unzip' jest wymagany, ale nie został znaleziony.${NC}"
        exit 1
    fi

    if command -v curl &> /dev/null; then
        curl -L "$ZIP_URL" -o "$TMP_DIR.zip" || { echo -e "${RED}BŁĄD: Pobieranie za pomocą curl nie powiodło się.${NC}"; exit 1; }
    elif command -v wget &> /dev/null; then
        wget "$ZIP_URL" -O "$TMP_DIR.zip" || { echo -e "${RED}BŁĄD: Pobieranie za pomocą wget nie powiodło się.${NC}"; exit 1; }
    else
        echo -e "${RED}BŁĄD KRYTYCZNY: Nie znaleziono ani 'git', ani 'curl', ani 'wget'. Nie można pobrać plików.${NC}"
        exit 1
    fi

    echo "Rozpakowywanie plików..."
    unzip -q "$TMP_DIR.zip" -d /tmp
    # Przenieś rozpakowany folder do naszej docelowej lokalizacji tymczasowej
    mv "/tmp/The-Orange-Disk--main" "$TMP_DIR"
    # Posprzątaj plik .zip
    rm "$TMP_DIR.zip"
fi

# --- KROK 2: Uruchomienie głównego instalatora ---
echo -e "\n${GREEN}Krok 2: Uruchamianie głównego instalatora...${NC}"

cd "$TMP_DIR" || { echo -e "${RED}BŁĄD: Nie można przejść do folderu z pobranymi plikami.${NC}"; exit 1; }

# Upewnij się, że główny instalator jest wykonywalny
chmod +x install.sh

# Uruchom główny instalator
./install.sh

# --- KROK 3: Sprzątanie ---
echo -e "\n${GREEN}Krok 3: Sprzątanie plików tymczasowych...${NC}"
rm -rf "$TMP_DIR"

echo -e "\n${GREEN}Wszystko gotowe!${NC}"

exit 0
