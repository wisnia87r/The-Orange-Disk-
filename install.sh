#!/bin/bash

# ==============================================================================
# THE ORANGE DISK - INSTALLER SCRIPT
# ==============================================================================
# This script installs The Orange Disk application and sets up Steam integration.
# It handles dependencies, file synchronization, and Steam configuration.

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# --- Configuration ---
INSTALL_DIR="$HOME/Applications/TheOrangeDisk"
LOG_FILE="$INSTALL_DIR/install.log"
VENV_DIR="$INSTALL_DIR/venv"
SYSTEM_PYTHON_BIN="/usr/bin/python3"
VENV_PYTHON_BIN="$VENV_DIR/bin/python3"
VENV_PIP_BIN="$VENV_DIR/bin/pip"
CONFIG_SCRIPT="set_steam_config.py"
# --- End Configuration ---

# Prepare logging - all output will be saved to install.log
mkdir -p "$INSTALL_DIR"
> "$LOG_FILE"
exec &> >(tee -a "$LOG_FILE")

log() {
    echo "[Install.sh] $(date +'%H:%M:%S'): $1"
}

echo "--- The Orange Disk Installer ---"
log "Starting installation."

# Step 1: Synchronize project files to installation directory
log "Step 1: Synchronizing project files."
SOURCE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

log "Using rsync to create a complete copy in '$INSTALL_DIR'..."
# This is the key command that copies all files:
# -a: archive mode (preserves permissions, timestamps, etc.)
# --delete: removes files in destination that don't exist in source
# --exclude: skips git files, IDE files, and temporary files
rsync -a --delete "$SOURCE_DIR/" "$INSTALL_DIR/" --exclude ".git" --exclude ".idea" --exclude "*.swp"

# From now on, we work ONLY in the installation directory
cd "$INSTALL_DIR" || { log "CRITICAL ERROR: Cannot change to installation directory '$INSTALL_DIR'."; exit 1; }
log "Working in directory: $(pwd)"

# Step 2: Check if Steam is running and close it if necessary
# Steam must be closed to modify shortcuts.vdf file
if pgrep -x "steam" > /dev/null; then
    log "Detected running Steam process. Closing..."
    steam -shutdown
    while pgrep -x "steam" > /dev/null; do echo -n "."; sleep 1; done
    log "Steam has been closed."
else
    log "Steam is not running. Good."
fi

# Step 3: Check for required system tools
log "Step 3: Checking for required system tools..."
MISSING_TOOLS=()

# Check for required disc reading tools
if ! command -v isoinfo &> /dev/null; then
    MISSING_TOOLS+=("cdrkit (provides isoinfo)")
fi
if ! command -v cdrdao &> /dev/null; then
    MISSING_TOOLS+=("cdrdao")
fi
if ! command -v dd &> /dev/null; then
    MISSING_TOOLS+=("dd (coreutils)")
fi

# If tools are missing, ask for sudo password to install them
if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
    echo ""
    echo "=========================================="
    echo "Missing Required Tools"
    echo "=========================================="
    echo ""
    echo "The following tools are required for disc reading and ripping:"
    for tool in "${MISSING_TOOLS[@]}"; do
        echo "  - $tool"
    done
    echo ""
    echo "These tools are needed to:"
    echo "  - Read disc information (isoinfo)"
    echo "  - Rip PS1 games in BIN/CUE format (cdrdao)"
    echo "  - Rip PS2 games in ISO format (dd)"
    echo ""
    echo "The installer will now install these tools using sudo."
    echo "You will be asked for your password (default on Steam Deck: no password, just press Enter)"
    echo ""
    read -s -p "Enter your sudo password (or press Enter if no password): " SUDO_PASSWORD
    echo ""

    log "Installing missing tools with sudo..."

    # Function to run sudo commands
    run_sudo() {
        if [ -z "$SUDO_PASSWORD" ]; then
            sudo "$@"
        else
            echo "$SUDO_PASSWORD" | sudo -S "$@"
        fi
    }

    # On Steam Deck, we need to disable read-only filesystem
    if [ -f "/etc/os-release" ] && grep -q "steamdeck" /etc/os-release; then
        log "Detected Steam Deck - disabling read-only filesystem..."
        run_sudo steamos-readonly disable

        # Initialize pacman keys if needed
        if [ ! -d "/etc/pacman.d/gnupg" ]; then
            log "Initializing pacman keys..."
            run_sudo pacman-key --init
            run_sudo pacman-key --populate archlinux holo
        fi

        # Install the tools
        log "Installing cdrdao and cdrkit..."
        run_sudo pacman -S cdrdao cdrkit --noconfirm --needed

        # Re-enable read-only filesystem
        log "Re-enabling read-only filesystem..."
        run_sudo steamos-readonly enable
    else
        # On other Linux systems, try to install with package manager
        log "Installing tools on non-Steam Deck system..."
        if command -v apt-get &> /dev/null; then
            run_sudo apt-get update
            run_sudo apt-get install -y cdrdao genisoimage coreutils
        elif command -v pacman &> /dev/null; then
            run_sudo pacman -S cdrdao cdrkit --noconfirm --needed
        elif command -v dnf &> /dev/null; then
            run_sudo dnf install -y cdrdao genisoimage coreutils
        else
            echo -e "${RED}ERROR: Could not detect package manager. Please install cdrdao and cdrkit manually.${NC}"
            exit 1
        fi
    fi

    log "System tools installed successfully."

    # After installing tools, set up permissions for optical drive access
    echo ""
    echo "Setting up optical drive permissions..."
    echo "This allows the application to read from your USB optical drive."
    echo ""

    # Load the sg module (SCSI generic driver needed for cdrdao)
    log "Loading SCSI generic driver module..."
    run_sudo modprobe sg

    # Add user to optical and disk groups
    log "Adding user to optical and disk groups..."
    run_sudo usermod -a -G optical,disk $USER

    # Set permissions on /dev/sg* devices (needed for cdrdao)
    log "Setting permissions on SCSI generic devices..."
    run_sudo sh -c 'chmod 666 /dev/sg* 2>/dev/null || true'

    echo -e "${GREEN}Permissions configured successfully.${NC}"
    echo ""
    echo "NOTE: You may need to log out and log back in for group changes to take effect."
    echo "      The application will also request permissions when you first use it."
    echo ""
else
    log "All required system tools are already installed."
fi

# Step 4: Install Python dependencies in a virtual environment
# This ensures the app has all required libraries without affecting system Python
log "Step 4: Installing/updating Python dependencies..."
if [ ! -d "$VENV_DIR" ]; then
    log "Creating new virtual environment in '$VENV_DIR'..."
    "$SYSTEM_PYTHON_BIN" -m venv "$VENV_DIR"
fi
log "Installing pygame, vdf, and requests to '$VENV_DIR'..."
"$VENV_PIP_BIN" install --upgrade pygame vdf requests
log "Making shell scripts executable..."
chmod +x ./*.sh

# Step 5: Configure SteamGridDB API Key (Optional)
log "Step 5: Configuring SteamGridDB API Key (optional)..."
echo ""
echo "=========================================="
echo "SteamGridDB API Key Setup (Optional)"
echo "=========================================="
echo ""
echo "SteamGridDB allows automatic download of game artwork (covers, banners, logos)."
echo "This makes your ripped games look professional in Steam."
echo ""
echo "To use this feature, you need a FREE API key from:"
echo "https://www.steamgriddb.com/profile/preferences/api"
echo ""
echo "If you don't have an API key yet, you can:"
echo "  1. Press Enter to skip this step (you can add it later)"
echo "  2. Or visit the website above, create an account, and get your key"
echo ""
read -p "Enter your SteamGridDB API key (or press Enter to skip): " API_KEY

if [ -n "$API_KEY" ]; then
    log "Configuring API key..."
    # Update the config.py file with the API key
    CONFIG_FILE="$INSTALL_DIR/the_orange_disk/config.py"
    if [ -f "$CONFIG_FILE" ]; then
        # Use sed to replace the API key line
        sed -i "s/STEAMGRIDDB_API_KEY = \"YOUR_API_KEY_HERE\"/STEAMGRIDDB_API_KEY = \"$API_KEY\"/" "$CONFIG_FILE"
        echo -e "${GREEN}API key configured successfully!${NC}"
        log "API key has been set."
    else
        log "WARNING: config.py not found, skipping API key configuration."
    fi
else
    log "Skipping API key configuration."
    echo "You can add your API key later by editing:"
    echo "$INSTALL_DIR/the_orange_disk/config.py"
    echo ""
fi

# Step 6: Configure Steam integration
# This adds The Orange Disk as a non-Steam game with artwork
log "Step 6: Running Steam configuration script..."
"$VENV_PYTHON_BIN" "./$CONFIG_SCRIPT"

# Step 7: Installation complete
log "Step 7: Finishing up."
log "--- INSTALLATION COMPLETE! ---"
echo ""
echo "=========================================="
echo -e "${GREEN}Installation Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Launch Steam"
echo "  2. Find 'The Orange Disk Playstation Edition' in your library"
echo "  3. Insert a PS1 or PS2 disc and enjoy!"
echo ""
if [ -z "$API_KEY" ]; then
    echo "Note: You skipped SteamGridDB setup. To enable artwork features later:"
    echo "  Edit: $INSTALL_DIR/the_orange_disk/config.py"
    echo "  See: https://www.steamgriddb.com/profile/preferences/api"
    echo ""
fi
echo "If you encounter any issues, check the log file:"
echo "  $LOG_FILE"
echo ""

exit 0
