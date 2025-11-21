# Changelog

All notable changes to The Orange Disk will be documented in this file.

## [1.2.0] - 2024

### Added
- **SteamGridDB Integration**: Automatic artwork download for ripped games
  - Support for multiple artwork types (grids, heroes, logos, icons)
  - Interactive artwork selection interface
  - Configurable API key setup during installation
- **Comprehensive Documentation**:
  - Detailed README with setup instructions
  - CONTRIBUTING.md for developers
  - Beginner-friendly code comments throughout
- **Installation Improvements**:
  - **Automatic dependency installation**: Installer checks for and installs required tools (`cdrdao`, `cdrkit`)
  - **Sudo password handling**: Clear explanation of why sudo is needed and what it's used for
  - **Permission setup**: Automatically configures optical drive access permissions
  - Interactive SteamGridDB API key configuration
  - Better error messages and user guidance
  - Improved Steam Deck compatibility checks
  - Support for multiple Linux distributions (Arch, Debian, Fedora)

### Changed
- **All comments translated to English** for better international collaboration
- **Code documentation improved** with detailed docstrings and explanations
- **Installation script enhanced** with step-by-step progress indicators
- **API key handling** - gracefully handles missing keys without breaking functionality

### Fixed
- **Settings menu bug**: Fixed issue where no buttons worked in the Settings menu
- **Navigation bugs**: Fixed HOW_TO and ABOUT screens not responding to back button
- Progress bar now updates correctly during disc ripping
- Games are properly added to Steam with correct emulator configuration
- Artwork is preserved during Steam restart process
- Steam shutdown process no longer hangs
- Missing system dependencies are now automatically detected and installed

### Technical Details
- Removed Polish comments and replaced with English
- Added comprehensive docstrings to all functions
- Improved error handling and user feedback
- Better separation of concerns in code architecture
- Installer now checks for required system tools before running
- Automatic detection of package manager (pacman, apt, dnf)
- Proper handling of Steam Deck's read-only filesystem
- Added input event handling for all UI states

## [1.0.0] - Initial Release

### Features
- Play PS1 and PS2 games directly from disc
- Rip games to digital backups (ISO/BIN format)
- Automatic disc type detection
- Controller-friendly interface
- Multi-language support (English, Polish)
- Steam integration with automatic shortcut creation
- EmuDeck integration for seamless emulator support
