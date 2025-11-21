# Contributing to The Orange Disk

Thank you for your interest in contributing to The Orange Disk! This document provides guidelines and information for contributors.

## Code of Conduct

Be respectful and constructive in all interactions. This is a community project built by enthusiasts for enthusiasts.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- A clear, descriptive title
- Steps to reproduce the problem
- Expected behavior vs actual behavior
- Your system information (Steam Deck model, SteamOS version, etc.)
- Relevant log files from `~/Applications/TheOrangeDisk/install.log`

### Suggesting Features

Feature requests are welcome! Please:
- Check if the feature has already been requested
- Clearly describe the feature and its use case
- Explain why it would be useful to other users

### Code Contributions

1. **Fork the repository** and create a new branch for your feature
2. **Follow the existing code style**:
   - Use descriptive variable and function names
   - Add comments explaining complex logic
   - All comments must be in English
   - Write comments as if explaining to a beginner
3. **Test your changes** on a Steam Deck or similar Linux handheld
4. **Submit a pull request** with:
   - Clear description of changes
   - Why the changes are needed
   - Any testing you've done

## Development Setup

### Prerequisites

- Steam Deck or Linux system with Python 3
- EmuDeck installed (for testing game functionality)
- USB optical drive (for testing disc operations)

### Installation for Development

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/The-Orange-Disk-.git
cd The-Orange-Disk-

# Run the installer
chmod +x install.sh
./install.sh
```

### Project Structure

```
The-Orange-Disk/
├── the_orange_disk/          # Main application package
│   ├── __init__.py           # Package initialization
│   ├── __main__.py           # Entry point
│   ├── app.py                # Main application logic and UI state management
│   ├── backend.py            # System interactions, disc operations, API calls
│   ├── config.py             # Configuration and translations
│   ├── drawing.py            # UI rendering functions
│   └── animations.py         # Visual effects (particles, orbs, etc.)
├── assets/                   # Images and artwork
│   ├── artwork/              # Steam library artwork
│   ├── backgrounds/          # UI backgrounds
│   └── icons/                # Application icons
├── install.sh                # Main installation script
├── launcher.sh               # Application launcher
├── set_steam_config.py       # Steam integration script
└── README.md                 # User documentation
```

### Key Files Explained

- **app.py**: Contains the main `TheOrangeDiskApp` class that manages:
  - UI state machine (boot animation, menu, loading, etc.)
  - User input handling
  - Background workers for disc operations
  - Action queue for thread-safe UI updates

- **backend.py**: System-level operations:
  - Optical drive detection and management
  - Disc reading and ripping
  - SteamGridDB API integration
  - Permission and tool management

- **config.py**: All configuration constants:
  - Application version
  - API keys
  - UI colors and dimensions
  - Translations (English and Polish)

- **drawing.py**: All rendering functions:
  - Each UI state has its own draw function
  - Handles text rendering with shadows
  - Manages animations and visual effects

## Code Style Guidelines

### Python Code

```python
# Good: Descriptive function name with docstring
def search_game_on_steamgriddb(game_name):
    """
    Search for a game on SteamGridDB and return its ID.

    Args:
        game_name (str): Name of the game to search for

    Returns:
        int: SteamGridDB game ID if found

    This function uses the SteamGridDB API to find games.
    You need a free API key from steamgriddb.com
    """
    # Implementation here
    pass

# Bad: Unclear name, no documentation
def sgdb_search(n):
    # What does this do? What is 'n'?
    pass
```

### Comments

```python
# Good: Explains WHY, not just WHAT
# Steam's VDF format uses signed 32-bit integers, so we need to convert
# unsigned values that exceed the max signed int value
signed_app_id = unsigned_app_id - 4294967296 if unsigned_app_id > 2147483647 else unsigned_app_id

# Bad: Just repeats the code
# Convert unsigned to signed
signed_app_id = unsigned_app_id - 4294967296 if unsigned_app_id > 2147483647 else unsigned_app_id
```

### Shell Scripts

```bash
# Good: Clear comments explaining each step
# Step 1: Synchronize project files to installation directory
log "Step 1: Synchronizing project files."
# This is the key command that copies all files:
# -a: archive mode (preserves permissions, timestamps, etc.)
# --delete: removes files in destination that don't exist in source
rsync -a --delete "$SOURCE_DIR/" "$INSTALL_DIR/"

# Bad: No explanation
log "Step 1"
rsync -a --delete "$SOURCE_DIR/" "$INSTALL_DIR/"
```

## Adding Translations

To add a new language:

1. Open `the_orange_disk/config.py`
2. Find the `TRANSLATIONS` dictionary
3. Add your language code to each translation entry:

```python
"PLAY_GAME": {
    "PL": "GRAJ Z PŁYTĄ",
    "EN": "PLAY FROM DISC",
    "ES": "JUGAR DESDE DISCO",  # Add your translation
},
```

4. Update the language selection in the Settings menu

## Testing

Before submitting a pull request, please test:

1. **Installation**: Run `install.sh` on a fresh system
2. **Disc Detection**: Test with PS1 and PS2 discs
3. **Ripping**: Verify disc ripping works correctly
4. **Artwork**: Test SteamGridDB integration (with and without API key)
5. **Steam Integration**: Ensure games appear in Steam library
6. **UI Navigation**: Test all menu options with controller

## Questions?

If you have questions about contributing:
- Open an issue with the "question" label
- Check existing issues and pull requests
- Review the code comments for implementation details

Thank you for helping make The Orange Disk better!
