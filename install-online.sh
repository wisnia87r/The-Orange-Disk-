#!/bin/bash

# ==============================================================================
# THE ORANGE DISK - ONLINE INSTALLER
# ==============================================================================
# This script automatically downloads and installs the latest stable release
# from GitHub, ensuring users always get the most recent version.
#
# What this script does:
# 1. Downloads the latest release from GitHub
# 2. Extracts the files to a temporary directory
# 3. Runs the main installation script
# 4. Cleans up temporary files

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# --- Configuration ---
GITHUB_REPO="wisnia87r/The-Orange-Disk-"
API_URL="https://api.github.com/repos/$GITHUB_REPO/releases/latest"
TMP_DIR="/tmp/the_orange_disk_install_$$"
# --- End Configuration ---

echo -e "${GREEN}=========================================="
echo "The Orange Disk - Online Installer"
echo -e "==========================================${NC}"
echo ""

# --- STEP 1: Check for required tools ---
echo -e "${GREEN}Step 1: Checking for required tools...${NC}"

# Check if curl is available (for downloading)
if ! command -v curl &> /dev/null; then
    echo -e "${RED}ERROR: 'curl' is required but not found.${NC}"
    echo "Please install curl and try again."
    exit 1
fi

# Check if unzip is available (for extracting)
if ! command -v unzip &> /dev/null; then
    echo -e "${RED}ERROR: 'unzip' is required but not found.${NC}"
    echo "Please install unzip and try again."
    exit 1
fi

# Check if jq is available (for parsing GitHub API response)
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}WARNING: 'jq' is not installed. Attempting to install it...${NC}"

    # Try to install jq automatically
    if command -v pacman &> /dev/null; then
        # Steam Deck / Arch Linux
        echo "Detected Arch-based system. Installing jq..."
        if [ -f "/etc/os-release" ] && grep -q "steamdeck" /etc/os-release; then
            # Steam Deck specific
            sudo steamos-readonly disable
            sudo pacman -S jq --noconfirm --needed
            sudo steamos-readonly enable
        else
            sudo pacman -S jq --noconfirm --needed
        fi
    elif command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        echo "Detected Debian-based system. Installing jq..."
        sudo apt-get update && sudo apt-get install -y jq
    elif command -v dnf &> /dev/null; then
        # Fedora
        echo "Detected Fedora-based system. Installing jq..."
        sudo dnf install -y jq
    else
        echo -e "${RED}ERROR: Could not install 'jq' automatically.${NC}"
        echo "Please install it manually and try again."
        exit 1
    fi

    # Verify jq was installed
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}ERROR: Failed to install 'jq'.${NC}"
        exit 1
    fi

    echo -e "${GREEN}jq installed successfully!${NC}"
fi

echo -e "${GREEN}All required tools are available.${NC}"
echo ""

# --- STEP 2: Download the latest release from GitHub ---
echo -e "${GREEN}Step 2: Downloading the latest release from GitHub...${NC}"

# Get the download URL for the latest release ZIP file
echo "Fetching release information from GitHub..."
ZIP_URL=$(curl -s $API_URL | jq -r ".zipball_url")

if [ -z "$ZIP_URL" ] || [ "$ZIP_URL" == "null" ]; then
    echo -e "${RED}ERROR: Could not find the latest release information.${NC}"
    echo "Please check:"
    echo "  1. Your internet connection"
    echo "  2. That the repository exists: https://github.com/$GITHUB_REPO"
    echo "  3. That there is at least one release published"
    exit 1
fi

echo "Downloading from: $ZIP_URL"
echo "This may take a moment..."

# Download the release ZIP file
curl -L "$ZIP_URL" -o "$TMP_DIR.zip" || {
    echo -e "${RED}ERROR: Download failed.${NC}"
    echo "Please check your internet connection and try again."
    exit 1
}

echo -e "${GREEN}Download complete!${NC}"
echo ""

# --- STEP 3: Extract the downloaded files ---
echo -e "${GREEN}Step 3: Extracting files...${NC}"

# Create temporary directory
mkdir -p "$TMP_DIR"

# Extract the ZIP file
unzip -q "$TMP_DIR.zip" -d "$TMP_DIR" || {
    echo -e "${RED}ERROR: Failed to extract files.${NC}"
    rm -rf "$TMP_DIR" "$TMP_DIR.zip"
    exit 1
}

# GitHub release ZIPs have an extra folder inside, we need to move it
# Use wildcard to match any folder name inside the archive
EXTRACTED_DIR=$(find "$TMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1)
if [ -z "$EXTRACTED_DIR" ]; then
    echo -e "${RED}ERROR: Unexpected archive structure.${NC}"
    rm -rf "$TMP_DIR" "$TMP_DIR.zip"
    exit 1
fi

mv "$EXTRACTED_DIR" "$TMP_DIR/app"
rm "$TMP_DIR.zip"

echo -e "${GREEN}Files extracted successfully!${NC}"
echo ""

# --- STEP 4: Run the main installer ---
echo -e "${GREEN}Step 4: Running the main installation script...${NC}"
echo ""
echo "=========================================="
echo "Starting Installation"
echo "=========================================="
echo ""

# Change to the extracted directory
cd "$TMP_DIR/app" || {
    echo -e "${RED}ERROR: Cannot access extracted files.${NC}"
    rm -rf "$TMP_DIR"
    exit 1
}

# Make the installer executable
chmod +x install.sh

# Run the main installer
./install.sh

# Store the exit code
INSTALL_EXIT_CODE=$?

# --- STEP 5: Cleanup ---
echo ""
echo -e "${GREEN}Step 5: Cleaning up temporary files...${NC}"
rm -rf "$TMP_DIR"

# Check if installation was successful
if [ $INSTALL_EXIT_CODE -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo -e "${GREEN}Installation Complete!${NC}"
    echo "=========================================="
    echo ""
    echo "The Orange Disk has been successfully installed!"
    echo ""
    echo "Next steps:"
    echo "  1. Launch Steam"
    echo "  2. Find 'The Orange Disk Playstation Edition' in your library"
    echo "  3. Insert a PS1 or PS2 disc and enjoy!"
    echo ""
else
    echo ""
    echo "=========================================="
    echo -e "${RED}Installation Failed${NC}"
    echo "=========================================="
    echo ""
    echo "The installation did not complete successfully."
    echo "Please check the error messages above."
    echo ""
    echo "For help, visit: https://github.com/$GITHUB_REPO/issues"
    echo ""
fi

exit $INSTALL_EXIT_CODE
