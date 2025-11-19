# The Orange Disk - Playstation Edition

![Hero Image](assets/artwork/hero.png)

**The Orange Disk** is a full-screen, console-like application for the Steam Deck (and other Linux-based handhelds) that allows you to manage and play your physical PlayStation 1 and PlayStation 2 game discs.

It provides a simple, controller-friendly interface to play games directly from an external USB optical drive or to create digital backups (`.iso` or `.bin/.cue`) on your device.

## Project Status

This is an early development version created by a passionate hobbyist in their free time. While fully functional for PS1 and PS2 discs, please consider it a work in progress.

Future support for other disc-based consoles may be considered if there is enough community interest and as time and resources permit. Your feedback and contributions are highly appreciated!

## Features

- **Play Directly from Disc**: Launch PS1 (DuckStation) or PS2 (PCSX2) games directly from the disc.
- **Rip Your Games**: Create 1:1 backups of your games, saving them directly into the EmuDeck folder structure.
- **Automatic Detection**: The app automatically detects the disc type (PS1 CD, PS2 CD, PS2 DVD) and required emulators.
- **Controller-First Interface**: Designed from the ground up for gamepad navigation.
- **Multi-Language Support**: Includes English and Polish translations.
- **Fully Automated Installation**: A single script handles dependencies and sets up the Steam shortcut with all artwork.

## Requirements

- **EmuDeck**: **This is a mandatory requirement.** The application is designed to work with the emulators (DuckStation, PCSX2) and folder structure provided by [EmuDeck](https://www.emudeck.com/). Ripped games are saved directly to EmuDeck's `roms` directory.
- **External USB Optical Drive**: A compatible USB CD/DVD/Blu-ray drive is required to read game discs.

## Installation (Easy Method)

1.  **Download the Installer**: Go to the [**Releases**](https://github.com/wisnia87r/The-Orange-Disk-/releases) page on the right and download the `install-online.sh` file from the latest release.
2.  **Open a Terminal**: **Do not double-click the file.** Instead, open the application launcher and start a terminal (Konsole).
3.  **Navigate to the File's Location**: Use the `cd` command to go to the folder where you saved the file. For example:
    ```bash
    cd ~/Desktop
    ```
4.  **Run the Installer from the Terminal**: Type the following two commands, pressing Enter after each one:
    ```bash
    # This first command makes the script executable
    chmod +x install-online.sh

    # This second command runs the script
    ./install-online.sh
    ```
5.  **Follow the On-Screen Instructions**: The script will download the latest version of the application and run the main installer. After it's done, you can close the terminal.
6.  **Launch Steam**: Start Steam. The shortcut "The Orange Disk Playstation Edition" will be in your library, fully configured.

## ❤️ Support the Project

If you find this application useful and want to support its development, you can buy me a coffee! Every donation is highly appreciated and helps motivate further improvements.

-   **[Sponsor on GitHub](https://github.com/sponsors/wisnia87r)
-   **[Buy me a coffee on Ko-fi](https://ko-fi.com/wisnia87r)

## How to Use

- **Navigate** the menu with the D-Pad or Analog Stick.
- **Select** an option with the **Cross (A)** button.
- **Go Back** with the **Circle (B)** button.

The main menu provides the following options:
- **PLAY FROM DISC**: Launches the game currently in the drive.
- **RIP DISC**: Creates a digital backup of the game. You will be prompted to enter a name for the game.
- **How to Use**: Displays a brief instruction screen.
- **About**: Shows creator information.
- **Settings**: Allows you to change the application language.
- **EXIT**: Closes the application.

## Contributing

This project is open-source and contributions are welcome! If you'd like to help, you can:

-   Report bugs or suggest features in the [Issues](https://github.com/wisnia87r/The-Orange-Disk-/issues) section.
-   Fork the repository and submit a pull request with your improvements.
-   Help translate the application into other languages by editing the `config.py` file.

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
