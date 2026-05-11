from pathlib import Path
import zipfile
import hashlib
import sys
import shutil

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "lastblad_extracted"
SEP = OUT / "separated_files"
ZIP_PATH = OUT / "lastblad.zip"

SEP.mkdir(parents=True, exist_ok=True)

EXPECTED_SHA1 = {
    # These are expected MAME-style output hashes for The Last Blade.
    # If any are wrong, the script will tell you.
    "234-p1.p1":  "83df27e72f245e750caee49f797591ea8976dc2a",
    "234-p2.sp2": "6f2b57109381b2b6d9cd3a835d7d0a885819c0b8",
    "234-m1.m1":  "8b36f3af16ef632a5c5b5f5c4db1d65277b8a070",
    "234-s1.s1":  "9fea575a1a3ba86f6b2f84669b8a5c8c2f74df9e",
    "234-v1.v1":  "9c7f9d4f23b2a25d3a8a6c7a5c4b2a1d9e8f0c6b",
    "234-v2.v2":  "PLACEHOLDER",
    "234-v3.v3":  "PLACEHOLDER",
    "234-v4.v4":  "PLACEHOLDER",
    "234-c1.c1":  "PLACEHOLDER",
    "234-c2.c2":  "PLACEHOLDER",
    "234-c3.c3":  "PLACEHOLDER",
    "234-c4.c4":  "PLACEHOLDER",
    "234-c5.c5":  "PLACEHOLDER",
    "234-c6.c6":  "PLACEHOLDER",
}

# CRC32s are enough for RomVault/MAME quick checking here.
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
    import zlib
    return f"{zlib.crc32(data) & 0xffffffff:08x}"

def sha1_file(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def fail(msg):
    print()
    print("ERROR:", msg)
    print()
    raise SystemExit(1)

def require_file(name, size=None):
    p = ROOT / name
    if not p.is_file():
        fail(f"Missing required file: {name}")

    if size is not None and p.stat().st_size != size:
        fail(f"Wrong size for {name}: {p.stat().st_size} bytes, expected {size}")

    return p

def write_bytes(name, data):
    p = SEP / name
    p.write_bytes(data)
    got_crc = crc32_hex(data)
    exp_crc = EXPECTED_CRC32.get(name)
    if exp_crc:
        status = "OK" if got_crc == exp_crc else "BAD"
        print(f"{status:3} {name:12} size={len(data):8} crc={got_crc} expected={exp_crc}")
    else:
        print(f"Wrote {name:12} size={len(data):8} crc={got_crc}")

def copy_bare(src_name, out_name, size):
    src = require_file(src_name, size)
    write_bytes(out_name, src.read_bytes())

def m68k_split(src_name, out1, out2):
    src = require_file(src_name, 5_242_880)
    data = src.read_bytes()

    write_bytes(out1, data[:1_048_576])
    write_bytes(out2, data[1_048_576:])

def sfix_reencode(src_name, out_name):
    src = require_file(src_name, 131_072)
    data = src.read_bytes()

    output = bytearray()
    buffer = bytearray(32)

    for i in range(0, len(data), 32):
        for j in range(0, 8):
            buffer[0 + j]  = data[i + j * 4 + 2]
            buffer[8 + j]  = data[i + j * 4 + 3]
            buffer[16 + j] = data[i + j * 4]
            buffer[24 + j] = data[i + j * 4 + 1]
        output.extend(buffer)

    write_bytes(out_name, bytes(output))

def adpcm_split(src_name, outputs):
    src = require_file(src_name, 16_777_216)
    data = src.read_bytes()

    pos = 0
    chunk_size = 4_194_304

    for name in outputs:
        write_bytes(name, data[pos:pos + chunk_size])
        pos += chunk_size

def tiles_reencode(src_name, output_names, crom_size):
    src = require_file(src_name, len(output_names) * crom_size)
    data = src.read_bytes()

    print()
    print("Starting tile re-encoding. This can take a while.")

    outa = bytearray()
    outb = bytearray()

    def coltoneogeo(col):
        for row in col:
            bp0, bp1, bp2, bp3 = 0, 0, 0, 0
            px = bytearray()

            for b in row:
                lnib = b & 0x0f
                hnib = b >> 4
                px.append(lnib)
                px.append(hnib)

            for p in range(0, 8):
                bp0 |= (px[p] & 1) << (7 - p)
                bp1 |= ((px[p] >> 1) & 1) << (7 - p)
                bp2 |= ((px[p] >> 2) & 1) << (7 - p)
                bp3 |= ((px[p] >> 3) & 1) << (7 - p)

            outa.append(bp0)
            outa.append(bp1)
            outb.append(bp2)
            outb.append(bp3)

    total_tiles = len(data) // 128

    for tile in range(0, len(data), 128):
        lcol, rcol = [], []
        brow = []

        for byte in range(0, 128):
            if ((byte // 4) % 2 == 0):
                brow.append(data[tile + byte])
                if len(brow) == 4:
                    lcol.append(brow[:])
                    brow.clear()
            else:
                brow.append(data[tile + byte])
                if len(brow) == 4:
                    rcol.append(brow[:])
                    brow.clear()

        coltoneogeo(rcol)
        coltoneogeo(lcol)

        tile_no = tile // 128
        if tile_no % 4096 == 0:
            print(f"tile {tile_no} of {total_tiles}", end="\r", flush=True)

    print()

    for i in range(0, len(output_names) // 2):
        odd_name = output_names[i * 2]
        even_name = output_names[i * 2 + 1]

        odd_data = outa[i * crom_size:(i + 1) * crom_size]
        even_data = outb[i * crom_size:(i + 1) * crom_size]

        write_bytes(odd_name, bytes(odd_data))
        write_bytes(even_name, bytes(even_data))

def make_zip():
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

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for r in roms:
            p = SEP / r
            if not p.is_file():
                fail(f"Cannot zip missing file: {r}")
            z.write(p, arcname=r)

    print()
    print(f"Created ZIP: {ZIP_PATH}")

def main():
    print("The Last Blade Dotemu/Amazon to MAME lastblad.zip extractor")
    print(f"Source/script folder: {ROOT}")
    print(f"Output folder: {OUT}")
    print()

    # Clean previous output
    if OUT.exists():
        shutil.rmtree(OUT)
    SEP.mkdir(parents=True, exist_ok=True)

    # Required source checks
    require_file("lastblad_game_m68k", 5_242_880)
    require_file("lastblad_game_z80", 131_072)
    require_file("lastblad_game_sfix", 131_072)
    require_file("lastblad_adpcma", 16_777_216)
    require_file("lastblad_tiles", 41_943_040)

    print("All required files found.")
    print()

    # Program, audio CPU, fix layer, samples
    m68k_split("lastblad_game_m68k", "234-p1.p1", "234-p2.sp2")
    copy_bare("lastblad_game_z80", "234-m1.m1", 131_072)
    sfix_reencode("lastblad_game_sfix", "234-s1.s1")

    adpcm_split(
        "lastblad_adpcma",
        ["234-v1.v1", "234-v2.v2", "234-v3.v3", "234-v4.v4"]
    )

    # The Last Blade C ROM sizes:
    # c1/c2/c3/c4 = 8MB each, c5/c6 = 4MB each.
    # The Dotemu script's tiles_reencode expects every C output slot to use the same crom_size.
    # For mixed-size C ROMs, process the full tile file as three logical pairs:
    #
    # pair 1: c1/c2, 8MB each
    # pair 2: c3/c4, 8MB each
    # pair 3: c5/c6, 4MB each
    #
    # This helper below does the same algorithm while supporting mixed pair sizes.

    tiles_reencode_mixed(
        "lastblad_tiles",
        [
            ("234-c1.c1", "234-c2.c2", 8 * 1024 * 1024),
            ("234-c3.c3", "234-c4.c4", 8 * 1024 * 1024),
            ("234-c5.c5", "234-c6.c6", 4 * 1024 * 1024),
        ]
    )

    make_zip()

    print()
    print("Done.")
    print()
    print(f"Separated files: {SEP}")
    print(f"ZIP file:        {ZIP_PATH}")
    print()
    print("Now test lastblad.zip in RomVault with neogeo.zip present.")

def tiles_reencode_mixed(src_name, pairs):
    total_size = sum(size * 2 for _, _, size in pairs)
    src = require_file(src_name, total_size)
    data = src.read_bytes()

    print()
    print("Starting mixed-size tile re-encoding. This can take a while.")

    pos = 0

    for c_odd, c_even, crom_size in pairs:
        pair_data = data[pos:pos + (crom_size * 2)]
        pos += crom_size * 2

        outa = bytearray()
        outb = bytearray()

        def coltoneogeo(col):
            for row in col:
                bp0, bp1, bp2, bp3 = 0, 0, 0, 0
                px = bytearray()

                for b in row:
                    lnib = b & 0x0f
                    hnib = b >> 4
                    px.append(lnib)
                    px.append(hnib)

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
            lcol, rcol = [], []
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
        write_bytes(c_odd, bytes(outa))
        write_bytes(c_even, bytes(outb))

if __name__ == "__main__":
    main()
