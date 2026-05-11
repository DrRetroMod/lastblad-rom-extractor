from pathlib import Path
import zipfile
import shutil
import zlib

ROOT = Path(__file__).resolve().parent

OUT = ROOT / "lastblad_extracted"
TMP_GAME = OUT / "_tmp_game_files"
TMP_BIOS = OUT / "_tmp_bios_files"

GAME_ZIP = OUT / "lastblad.zip"
BIOS_ZIP = OUT / "neogeo.zip"

EXPECTED_CRC32 = {
    "234-s1.s1":  "95561412",
    "234-c1.c1":  "9f7e2bd3",
    "234-c2.c2":  "80623d3c",
    "234-c3.c3":  "91ab1a30",
    "234-c4.c4":  "3d60b037",
    "234-c5.c5":  "1ba80cee",
    "234-c6.c6":  "beafd091",
}

def crc32_hex(data):
    return f"{zlib.crc32(data) & 0xffffffff:08x}"

def fail(msg):
    print()
    print("ERROR:", msg)
    print()
    raise SystemExit(1)

def require_file(name, size=None):
    path = ROOT / name

    if not path.is_file():
        fail(f"Missing required file: {name}")

    if size is not None and path.stat().st_size != size:
        fail(f"Wrong size for {name}: {path.stat().st_size} bytes, expected {size}")

    return path

def write_game_file(name, data):
    path = TMP_GAME / name
    path.write_bytes(data)

    got_crc = crc32_hex(data)
    exp_crc = EXPECTED_CRC32.get(name)

    if exp_crc:
        status = "OK" if got_crc == exp_crc else "BAD"
        print(f"{status:3} {name:12} size={len(data):8} crc={got_crc} expected={exp_crc}")
    else:
        print(f"Wrote {name:12} size={len(data):8} crc={got_crc}")

def write_bios_file(name, data):
    path = TMP_BIOS / name
    path.write_bytes(data)
    print(f"Wrote BIOS {name:12} size={len(data):8} crc={crc32_hex(data)}")

def sfix_reencode_source_bytes(data):
    output = bytearray()
    buffer = bytearray(32)

    for i in range(0, len(data), 32):
        for j in range(0, 8):
            buffer[0 + j]  = data[i + j * 4 + 2]
            buffer[8 + j]  = data[i + j * 4 + 3]
            buffer[16 + j] = data[i + j * 4]
            buffer[24 + j] = data[i + j * 4 + 1]
        output.extend(buffer)

    return bytes(output)

def m68k_split():
    data = require_file("lastblad_game_m68k", 5_242_880).read_bytes()

    write_game_file("234-p1.p1", data[:1_048_576])
    write_game_file("234-p2.sp2", data[1_048_576:])

def copy_m1():
    data = require_file("lastblad_game_z80", 131_072).read_bytes()
    write_game_file("234-m1.m1", data)

def sfix_reencode_game():
    data = require_file("lastblad_game_sfix", 131_072).read_bytes()
    write_game_file("234-s1.s1", sfix_reencode_source_bytes(data))

def adpcm_split():
    data = require_file("lastblad_adpcma", 16_777_216).read_bytes()

    write_game_file("234-v1.v1", data[0:4_194_304])
    write_game_file("234-v2.v2", data[4_194_304:8_388_608])
    write_game_file("234-v3.v3", data[8_388_608:12_582_912])
    write_game_file("234-v4.v4", data[12_582_912:16_777_216])

def tiles_reencode_mixed():
    data = require_file("lastblad_tiles", 41_943_040).read_bytes()

    pairs = [
        ("234-c1.c1", "234-c2.c2", 8 * 1024 * 1024),
        ("234-c3.c3", "234-c4.c4", 8 * 1024 * 1024),
        ("234-c5.c5", "234-c6.c6", 4 * 1024 * 1024),
    ]

    print()
    print("Starting tile re-encoding. This can take a while.")

    pos = 0

    for c_odd, c_even, crom_size in pairs:
        pair_data = data[pos:pos + crom_size * 2]
        pos += crom_size * 2

        outa = bytearray()
        outb = bytearray()

        def coltoneogeo(col):
            for row in col:
                bp0, bp1, bp2, bp3 = 0, 0, 0, 0
                px = bytearray()

                for b in row:
                    px.append(b & 0x0F)
                    px.append(b >> 4)

                for p in range(0, 8):
                    bp0 |= (px[p] & 1) << (7 - p)
                    bp1 |= ((px[p] >> 1) & 1) << (7 - p)
                    bp2 |= ((px[p] >> 2) & 1) << (7 - p)
                    bp3 |= ((px[p] >> 3) & 1) << (7 - p)

                outa.append(bp0)
                outa.append(bp1)
                outb.append(bp2)
                outb.append(bp3)

        total_tiles = len(pair_data) // 128

        for tile in range(0, len(pair_data), 128):
            lcol = []
            rcol = []
            brow = []

            for byte in range(0, 128):
                if ((byte // 4) % 2 == 0):
                    brow.append(pair_data[tile + byte])
                    if len(brow) == 4:
                        lcol.append(brow[:])
                        brow.clear()
                else:
                    brow.append(pair_data[tile + byte])
                    if len(brow) == 4:
                        rcol.append(brow[:])
                        brow.clear()

            coltoneogeo(rcol)
            coltoneogeo(lcol)

            tile_no = tile // 128
            if tile_no % 4096 == 0:
                print(f"{c_odd}/{c_even}: tile {tile_no} of {total_tiles}", end="\r", flush=True)

        print()
        write_game_file(c_odd, bytes(outa))
        write_game_file(c_even, bytes(outb))

def make_game_zip():
    roms = [
        "234-p1.p1",
        "234-p2.sp2",
        "234-m1.m1",
        "234-s1.s1",
        "234-v1.v1",
        "234-v2.v2",
        "234-v3.v3",
        "234-v4.v4",
        "234-c1.c1",
        "234-c2.c2",
        "234-c3.c3",
        "234-c4.c4",
        "234-c5.c5",
        "234-c6.c6",
    ]

    if GAME_ZIP.exists():
        GAME_ZIP.unlink()

    with zipfile.ZipFile(GAME_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name in roms:
            path = TMP_GAME / name
            if not path.is_file():
                fail(f"Cannot zip missing game file: {name}")
            z.write(path, arcname=name)

    print()
    print(f"Created game ZIP: {GAME_ZIP}")

def extract_bios():
    print()
    print("Extracting included NeoGeo BIOS files separately.")

    zoom = require_file("lastblad_zoom_table", 131_072).read_bytes()
    bios_us = require_file("lastblad_bios_m68k", 131_072).read_bytes()
    bios_vs = require_file("lastblad_bios_m68k_jap", 131_072).read_bytes()
    bios_sfix_src = require_file("lastblad_bios_sfix", 131_072).read_bytes()

    write_bios_file("000-lo.lo", zoom)
    write_bios_file("sp-u2.sp1", bios_us)
    write_bios_file("vs-bios.rom", bios_vs)
    write_bios_file("sfix.sfix", sfix_reencode_source_bytes(bios_sfix_src))

    bios_files = [
        "000-lo.lo",
        "sp-u2.sp1",
        "vs-bios.rom",
        "sfix.sfix",
    ]

    if BIOS_ZIP.exists():
        BIOS_ZIP.unlink()

    with zipfile.ZipFile(BIOS_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name in bios_files:
            path = TMP_BIOS / name
            if not path.is_file():
                fail(f"Cannot zip missing BIOS file: {name}")
            z.write(path, arcname=name)

    print()
    print(f"Created BIOS ZIP: {BIOS_ZIP}")

def clean_temp_files():
    if TMP_GAME.exists():
        shutil.rmtree(TMP_GAME)
    if TMP_BIOS.exists():
        shutil.rmtree(TMP_BIOS)

def main():
    print("The Last Blade Amazon/Dotemu extractor")
    print(f"Source/script folder: {ROOT}")
    print(f"Output folder:        {OUT}")
    print()

    if OUT.exists():
        shutil.rmtree(OUT)

    OUT.mkdir(parents=True, exist_ok=True)
    TMP_GAME.mkdir(parents=True, exist_ok=True)
    TMP_BIOS.mkdir(parents=True, exist_ok=True)

    print("Checking required files...")

    require_file("lastblad_game_m68k", 5_242_880)
    require_file("lastblad_game_z80", 131_072)
    require_file("lastblad_game_sfix", 131_072)
    require_file("lastblad_adpcma", 16_777_216)
    require_file("lastblad_tiles", 41_943_040)

    require_file("lastblad_zoom_table", 131_072)
    require_file("lastblad_bios_m68k", 131_072)
    require_file("lastblad_bios_m68k_jap", 131_072)
    require_file("lastblad_bios_sfix", 131_072)

    print("All required files found.")
    print()

    m68k_split()
    copy_m1()
    sfix_reencode_game()
    adpcm_split()
    tiles_reencode_mixed()

    make_game_zip()
    extract_bios()

    clean_temp_files()

    print()
    print("Done.")
    print()
    print("Final output:")
    print(f"  {GAME_ZIP}")
    print(f"  {BIOS_ZIP}")
    print()
    print("Temporary separated files were removed.")

if __name__ == "__main__":
    main()
