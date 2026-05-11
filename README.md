# lastblad-rom-extractor

lastblad-rom-extractor is a Python script to extract MAME compatible rom archives from the Dotemu releases of The Last Blade

## How does it work?

This script manipulates the files at `GAME_DIR/resources/game` to convert them from a format optimized for Dotemu's emulator to the original Neo-Geo binaries. Specific file manipulations are documented in the script's source code. All of this was achieved after some light Reverse Engineering of the emulator.

## Supported Games

Dotemu's windows releases (Available in Amazon Gaming and possibly Steam & GOG?? I am unsure of these last two) of:

* The Last Blade

## BIOS

This script can optionally extract the NEO-GEO BIOS files included in these releases with the `--extract_bios` option. Though MAME (And most emulators) expect a full NEO-GEO BIOS romset (neogeo.zip). These releases only include the MVS US BIOS files.

## Usage

```
usage: mslug-rom-extractor [-h] [-o OUTPUT_DIR] [--output_bios] game_dir

Script to extract MAME compatible rom files from Dotemu's releases of Metal
Slug 1,2 & X (3 NOT SUPPORTED)

positional arguments:
  game_dir              Directory that matches STEAMFOLDER/steamapps/common/GA
                        ME_TO_EXTRACT/resources/game

options:
  -h, --help            show this help message and exit
  -o, --output_dir OUTPUT_DIR
                        Directory to output final rom files
  --output_bios         Extract also included bios files (Not enough for most
                        emulators)
```

## Legal Notice

This project is provided for educational and preservation purposes only.

It does not include any copyrighted game data, ROMs, or BIOS files.

This tool performs format conversion and reconstruction of data already present in the original game files.

To use this tool, you must legally own the original games from which the data is extracted (e.g., purchased through platforms such as Steam or GOG).

This project is not affiliated with, endorsed by, or associated with Dotemu or SNK.

The author does not condone piracy. Users are solely responsible for how they use this software.

