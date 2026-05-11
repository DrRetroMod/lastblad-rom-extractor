# lastblad-rom-extractor

lastblad-rom-extractor is a Python script to extract MAME compatible rom archives from the Dotemu releases of The Last Blade

## How does it work?

This script manipulates the files at `GAME_DIR/resources/game` to convert them from a format optimized for Dotemu's emulator to the original Neo-Geo binaries. Specific file manipulations are documented in the script's source code. All of this was achieved after some light Reverse Engineering of the emulator.

## Supported Games

Dotemu's windows releases (Available in Amazon Gaming and possibly Steam & GOG?? I am unsure of these last two) of:

* The Last Blade

## BIOS

This script will automatically extract the included NEO-GEO BIOS files in these releases. Though MAME (And most emulators) expect a full NEO-GEO BIOS romset (neogeo.zip). These releases only include the MVS US BIOS files.

## Usage

Simple place the two files in the `GAME_DIR/resources/game` folder, and run the 'extract_lastblad.bat' file.
It will create two files, the game file 'lastblad.zip' and the bios file 'neogeo.zip'. I have confiremd that the game file passes RomVaults checks and is a complete version of the game, but Bios fles may still be wanted.

## Legal Notice

This was script was forked and heavily based on terminatorhex's Metal Slug extraction sctipt tool found here: https://github.com/terminatorhex/mslug-rom-extractor

This project is provided for educational and preservation purposes only.

It does not include any copyrighted game data, ROMs, or BIOS files.

This tool performs format conversion and reconstruction of data already present in the original game files.

To use this tool, you must legally own the original games from which the data is extracted (e.g., purchased through platforms such as Steam or GOG).

This project is not affiliated with, endorsed by, or associated with Dotemu or SNK.

The author does not condone piracy. Users are solely responsible for how they use this software.

