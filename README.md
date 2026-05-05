# mslug-rom-extractor

mslug-rom-extractor is a Python script to extract MAME compatible rom archives from the Dotemu releases of Metal Slug 1, 2 & X.

## How does it work?

This script manipulates the files at `GAME_DIR/resources/game` to convert them from a format optimized for Dotemu's emulator to the original Neo-Geo binaries. Specific file manipulations are documented in the script's source code. All of this was achieved after some light Reverse Engineering of the emulator.

## Supported Games

Dotemu's windows releases (Available in Steam & GOG) of:

* Metal Slug 1
* Metal Slug 2
* Metal Slug X

## Unsupported Games

Metal Slug 3 ROM extraction is NOT SUPPORTED.

Dotemu’s release modifies the game program code to remove any Neo-SMA depency. MAME Expects SMA encrypted program code and a dump of the contents of the SMA chip in the original game cartridge (green.neo-sma). This means that:

* The 68k program included (mslug3_game_m68k) is not a direct match to the original PRG ROMs (256-pg1.p1/pg2.p2) and would require heavy reconstruction.
* The Neo-SMA protection chip data (green.neo-sma) is completely absent from the files.

As a result, a valid MAME-compatible ROM set cannot be reconstructed from these files alone.

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

