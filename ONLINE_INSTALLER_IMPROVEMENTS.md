# Online Installer Improvements

## Summary
The `install-online.sh` script has been completely rewritten with English comments, better error handling, and automatic dependency installation.

## ✅ What Was Fixed

### 1. **Language Translation**
**Before**: All comments and messages were in Polish
**After**: Everything is now in English for international users

### 2. **Automatic Dependency Installation**
**Before**: Script would fail if `jq` was missing
**After**:
- Checks for required tools: `curl`, `unzip`, `jq`
- Automatically installs `jq` if missing
- Supports multiple package managers (pacman, apt, dnf)
- Handles Steam Deck's read-only filesystem

### 3. **Better Error Handling**
**Before**: Generic error messages
**After**:
- Clear, specific error messages
- Helpful suggestions for fixing issues
- Proper exit codes
- Cleanup on failure

### 4. **Improved User Feedback**
**Before**: Minimal progress information
**After**:
- Step-by-step progress indicators
- Clear success/failure messages
- Helpful next steps after installation
- Link to GitHub issues for support

## 📋 Installation Flow

### Step 1: Check for Required Tools
```bash
# Checks for:
- curl (for downloading)
- unzip (for extracting)
- jq (for parsing GitHub API)

# If jq is missing, automatically installs it
```

### Step 2: Download Latest Release
```bash
# Fetches release info from GitHub API
# Downloads the latest stable release ZIP
# Shows download progress
```

### Step 3: Extract Files
```bash
# Extracts to temporary directory
# Handles GitHub's nested folder structure
# Validates extraction success
```

### Step 4: Run Main Installer
```bash
# Changes to extracted directory
# Makes install.sh executable
# Runs the main installation script
# Captures exit code for error handling
```

### Step 5: Cleanup
```bash
# Removes temporary files
# Shows final success/failure message
# Provides next steps or troubleshooting info
```

## 🔧 Technical Improvements

### Automatic jq Installation
```bash
if ! command -v jq &> /dev/null; then
    echo "WARNING: 'jq' is not installed. Attempting to install it..."

    if command -v pacman &> /dev/null; then
        # Steam Deck / Arch Linux
        if grep -q "steamdeck" /etc/os-release; then
            sudo steamos-readonly disable
            sudo pacman -S jq --noconfirm --needed
            sudo steamos-readonly enable
        else
            sudo pacman -S jq --noconfirm --needed
        fi
    elif command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        sudo apt-get update && sudo apt-get install -y jq
    elif command -v dnf &> /dev/null; then
        # Fedora
        sudo dnf install -y jq
    fi
fi
```

### Better Archive Extraction
```bash
# Old way: Used wildcard that could fail
mv "$TMP_DIR"/*/ "$TMP_DIR/app"

# New way: Finds the actual directory
EXTRACTED_DIR=$(find "$TMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1)
if [ -z "$EXTRACTED_DIR" ]; then
    echo "ERROR: Unexpected archive structure."
    exit 1
fi
mv "$EXTRACTED_DIR" "$TMP_DIR/app"
```

### Exit Code Handling
```bash
# Run installer and capture exit code
./install.sh
INSTALL_EXIT_CODE=$?

# Cleanup
rm -rf "$TMP_DIR"

# Show appropriate message based on result
if [ $INSTALL_EXIT_CODE -eq 0 ]; then
    echo "Installation Complete!"
else
    echo "Installation Failed"
    echo "For help, visit: https://github.com/$GITHUB_REPO/issues"
fi

exit $INSTALL_EXIT_CODE
```

## 📚 User-Facing Changes

### Before:
```
--- The Orange Disk - Inteligentny Instalator Online ---

Krok 1: Wyszukiwanie najnowszego wydania na GitHub...
BŁĄD KRYTYCZNY: Programy 'curl' i 'jq' są wymagane...
```

### After:
```
==========================================
The Orange Disk - Online Installer
==========================================

Step 1: Checking for required tools...
WARNING: 'jq' is not installed. Attempting to install it...
Detected Arch-based system. Installing jq...
jq installed successfully!
All required tools are available.

Step 2: Downloading the latest release from GitHub...
Fetching release information from GitHub...
Downloading from: https://api.github.com/...
This may take a moment...
Download complete!

Step 3: Extracting files...
Files extracted successfully!

Step 4: Running the main installation script...
==========================================
Starting Installation
==========================================
[... main installer runs ...]

Step 5: Cleaning up temporary files...

==========================================
Installation Complete!
==========================================

The Orange Disk has been successfully installed!

Next steps:
  1. Launch Steam
  2. Find 'The Orange Disk Playstation Edition' in your library
  3. Insert a PS1 or PS2 disc and enjoy!
```

## 🎯 Benefits

### For Users:
- ✅ Clear, English messages
- ✅ Automatic dependency installation
- ✅ Better error messages with solutions
- ✅ Progress indicators
- ✅ Helpful next steps

### For Developers:
- ✅ Well-commented code
- ✅ Proper error handling
- ✅ Exit code propagation
- ✅ Easy to maintain
- ✅ Follows best practices

### For Support:
- ✅ Clear error messages reduce support requests
- ✅ Link to GitHub issues for help
- ✅ Logs show exactly what failed
- ✅ Users can troubleshoot themselves

## 🔒 Security

### What Requires Sudo:
- Installing `jq` package (only if missing)
- On Steam Deck: Disabling/enabling read-only filesystem

### What Doesn't Require Sudo:
- Downloading files
- Extracting archives
- Running the main installer (it will ask for sudo when needed)

## 🧪 Testing

Tested scenarios:
- [x] Fresh installation with all tools present
- [x] Installation with missing jq (auto-install)
- [x] Installation on Steam Deck
- [x] Installation on Debian/Ubuntu
- [x] Installation on Fedora
- [x] Network failure handling
- [x] Invalid GitHub repository
- [x] Extraction failure
- [x] Main installer failure

## 📝 Files Modified

1. **install-online.sh**
   - Translated all comments to English
   - Added automatic jq installation
   - Improved error handling
   - Better user feedback
   - Proper exit code handling

2. **README.md**
   - Updated installation instructions
   - Added troubleshooting for jq
   - Explained what online installer does
   - Added manual installation fallback

## 🎉 Result

The online installer is now:
- **Professional** - Clear, English messages
- **Robust** - Handles missing dependencies
- **User-friendly** - Helpful error messages
- **Maintainable** - Well-documented code
- **International** - Ready for global users

Users can now install The Orange Disk with a single command, and the installer will handle everything automatically!
