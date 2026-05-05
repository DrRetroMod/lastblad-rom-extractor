# Python script to convert dotemu's neogeo ports to mame romset files

import shutil
import sys
import os
import zipfile
import hashlib
import argparse
from pathlib import Path
import json

#----------------- Command line argument parsing --------------------------------

# work path setup function
def make_paths(input_dir, output_dir):
    def ipath(file):
        return os.path.join(input_dir, file)
    def opath(file):
        return os.path.join(output_dir, file)
    return ipath, opath

parser = argparse.ArgumentParser(prog='mslug-rom-extractor',
                                 description="Script to extract MAME compatible rom files from Dotemu's releases of Metal Slug 1,2 & X (3 NOT SUPPORTED)")
parser.add_argument("game_dir", help="Directory that matches STEAMFOLDER/steamapps/common/GAME_TO_EXTRACT/resources/game")
parser.add_argument("-o", "--output_dir", help="Directory to output final rom files")
parser.add_argument("--output_bios", help="Extract also included bios files (Not enough for most emulators)", 
                    action="store_true")
args = parser.parse_args()

# setup ipath and opath functions

input_dir = args.game_dir
if (args.output_dir == None):
    output_dir = os.path.join(args.game_dir, "output")
else:
    output_dir = args.output_dir
os.makedirs(output_dir, exist_ok=True) # Create output dir
ipath, opath = make_paths(input_dir, output_dir)

#----------------- Individual game configurations  ------------------------------

GAME_CONFIG = {
        'mslug' : {
          'game_output_files' : {
              '000-10.10' : '5992277debadeb64d1c1c64b0a92d9293eaf7e4a',
              '201-c1.c1' : '7b045d1a48980cb1a140699011cb1a3d4acdc4d1',  
              '201-c2.c2' : 'cb7254b885989223bba597b8ff0972dfa5957816',
              '201-c3.c3' : '0a7a27d603d1bb2520b5570ebf5b34a106e255a6',  
              '201-c4.c4' : '4e94fda8ee63abf0f92afe08060a488546e5c280',
              '201-m1.m1' : 'fd75bd15aed30266a8b3775f276f997af57d1c06',  
              '201-p1.p1' : 'b888993dbb7e9f0a28a01d7d2e1da00ef9cf6f38',  
              '201-s1.s1' : '550b53628daec9f1e1e11a398854092d90f9505a',  
              '201-v1.v1' : 'cd076928468ad6bcc5f19f88cb843ecb5e660681',
              '201-v2.v2' : '5f79ea9286d22ed208128f9c31ca75552ce08b57' 
           },
          'game_input_files' : {
              "mslug_adpcm"     : "d03f0c513cf5b76ae6193f619eb0b08d435e243a",
              "mslug_game_m68k" : "411d5560f4f4c13862edf72ee42cc5f3ce083778",
              "mslug_game_sfix" : "1ac856f3408e203fe41bd27a808b95b217151066",
              "mslug_game_z80"  : "fd75bd15aed30266a8b3775f276f997af57d1c06",
              "mslug_tiles"     : "20952ebe31d50b21308cd66783624b76e9715d89",
              "mslug_zoom_table": "5992277debadeb64d1c1c64b0a92d9293eaf7e4a"
           },
          'bios_input_files' : {
              "mslug_bios_m68k" : "5c6bba07d2ec8ac95776aa3511109f5e1e2e92eb",
              "mslug_bios_sfix" : "3d9c878d6d8e5d47fe58dfbdee31aed5c5b23360",
           },
          'bios_output_files' : {
              "sp-u2.sp1" : "5c6bba07d2ec8ac95776aa3511109f5e1e2e92eb",
              "sfix.sfix" : "fd4a618cdcdbf849374f0a50dd8efe9dbab706c3"
           },
          'crom_size' : 4194304
        },
        'mslug2' : {
          'game_output_files' : {
              '000-10.10' : '5992277debadeb64d1c1c64b0a92d9293eaf7e4a',
              '241-c1.c1' : '4549926f5054ee6aa7689cf920be0327e3908a50',  
              '241-c2.c2' : '1e5475cfab129c77acc610f09369ca42ba5aafa5',
              '241-c3.c3' : 'a4319b48004e723f81a980887678e3e296049a53',  
              '241-c4.c4' : '1499316fb381775218d897b81a6a0c3465d1a37c',
              '241-m1.m1' : 'f8a1551cebcb91e416f30f50581feed7f72899e9',  
              '241-p1.p1' : '5a6aba482cac588a6c2c51179c95b487c6e11899',  
              '241-p2.sp2' : 'fcf34b8c6e37774741542393b963635412484a27',  
              '241-s1.s1' : '2dc38b7dfd3ff14f64d5c0733c510b6bb8c692d0',  
              '241-v1.v1' : '80597707f1fe115eed1941bb0701fc00790ad504',
              '241-v2.v2' : 'b4b4ddc680836ed55942c66d7dfe756314e02211' 
           },
          'game_input_files' : {
              "mslug2_adpcm"     : "dd60bf9ec16af8718d698effb1eb48cb928fe267",
              "mslug2_game_m68k" : "322e503e8323e8516861b58270311ac853104408",
              "mslug2_game_sfix" : "13b05fc7fe48eb58f9836d817e9d90481c6229bd",
              "mslug2_game_z80"  : "f8a1551cebcb91e416f30f50581feed7f72899e9",
              "mslug2_tiles"     : "b83649b6075534a67651e68695c49f24e253589e",
              "mslug2_zoom_table": "5992277debadeb64d1c1c64b0a92d9293eaf7e4a"
           },
          'bios_input_files' : {
              "mslug2_bios_m68k" : "5c6bba07d2ec8ac95776aa3511109f5e1e2e92eb",
              "mslug2_bios_sfix" : "3d9c878d6d8e5d47fe58dfbdee31aed5c5b23360",
           },
          'bios_output_files' : {
              "sp-u2.sp1" : "5c6bba07d2ec8ac95776aa3511109f5e1e2e92eb",
              "sfix.sfix" : "fd4a618cdcdbf849374f0a50dd8efe9dbab706c3"
           },
          'crom_size' : 8388608
         },
        'mslugx' : {
          'game_output_files' : {
              '000-10.10' : '5992277debadeb64d1c1c64b0a92d9293eaf7e4a',
              '250-c1.c1' : 'c3e8a8ccdac0f8bddc4c3413277626532405fae2',  
              '250-c2.c2' : '554f600a3aa09c16c13c625299b087a79d0d15c5',
              '250-c3.c3' : 'c56646c62387bc1439d46610258c755beb8d7dd8',  
              '250-c4.c4' : '31be8ea2498001f68ce4b06b8b90acbf2dcab6af',
              '250-c5.c5' : 'd41069856df990a1a99d39fb263c8303389d5475',
              '250-c6.c6' : '39be66287696829d243fb71b3fb8b7dc2bc3298f',
              '250-m1.m1' : '55769bad4860f64ef53a333e0da9e073db483d6a',  
              '250-p1.p1' : '4c19f2e9824e606178ac1c9d4b0516fbaa625035',  
              '250-p2.ep1' : '18aaa7a3ba8da99f78c430e9be69ccde04bc04d9',  
              '250-s1.s1' : '2cc392ecde5d5afb28ddbaa1030552b48571dcfb',  
              '250-v1.v1' : 'ebfcc67204ff9677cf7972fd5b6b7faabf07280c',
              '250-v2.v2' : '526c42ca9a388f7435569400e2f132e2724c71ff',
              '250-v3.v3' : '45979d1edb1fc774a415d9386f98d7cb252a2043' 
           },
          'game_input_files' : {
              "mslugx_adpcm"     : "e948707d450db2a6dfbf9b0ec1f116c78c89567d",
              "mslugx_game_m68k" : "fc1f885977206bacfd011b5bbf1874b605a9442f",
              "mslugx_game_sfix" : "992726dae161b328163e4acbb532b2db74d55142",
              "mslugx_game_z80"  : "55769bad4860f64ef53a333e0da9e073db483d6a",
              "mslugx_tiles"     : "6bf05ae0a85e6d59aa3c8c11bf0367d43b6b066e",
              "mslugx_zoom_table": "5992277debadeb64d1c1c64b0a92d9293eaf7e4a"
           },
          'bios_input_files' : {
              "mslugx_bios_m68k" : "5c6bba07d2ec8ac95776aa3511109f5e1e2e92eb",
              "mslugx_bios_sfix" : "3d9c878d6d8e5d47fe58dfbdee31aed5c5b23360",
           },
          'bios_output_files' : {
              "sp-u2.sp1" : "5c6bba07d2ec8ac95776aa3511109f5e1e2e92eb",
              "sfix.sfix" : "fd4a618cdcdbf849374f0a50dd8efe9dbab706c3"
           },
          'crom_size' : 8388608,
          '250-p1.p1_patch': '250-p1.p1.json'
        },
        'mslug3' : "NOT SUPPORTED!"
        # More games go here
}

#----------------- File operation functions ------------------------------

def detect_game(gamedir): # Detect game in supplied dir and return game string
    files = [f.name.lower() for f in Path(gamedir).iterdir() if f.is_file()]
    for game in ["mslug2", "mslug3", "mslugx", "mslug"]:
        if any(game in f for f in files):
            return game
    return None

def sha1sum(path): #Get sha1sum of a single file
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def hashcheck(filehash_dict): # Compare file hashes with dictionary
    for f,h in filehash_dict.items():
        th = sha1sum(f)
        if th != h:
            print("invalid checksum for file " + f)
            print("expected hash: " + h)
            print("calculated hash: " + th)
            print("Halting execution")
            sys.exit(1)
    print("checksum checks passed")

def copy_bare(infile, outfile): # Copy file as is with output name
    shutil.copy(infile, outfile) 
    print(outfile, "extracted")

def patch(file, patchf): # Apply patch from json file
    with open(patchf, "r", encoding="utf-8") as f:
        patch = json.load(f)
    with open(file, "r+b") as f:
        for p in sorted(patch["patches"], key=lambda x: x["offset"]):
            f.seek(p["offset"])
            original=f.read(1)[0]
            if original != p["old"]:
                sys.exit(f"Unexpected byte {original} in {p['offset']}. Haulting script")
            f.seek(p["offset"])
            print(p["offset"])
            f.write(bytes([p["new"]]))
    print(file, "patched")

def tiles_reencode(infile, octbl, crom_size): # Reencode from dotemu tile format to neogeo char rom format
    # WARNING: octbl (output crom table) must contain files in order!
    print("starting tile re-encoding, this may take a while!")
    outa=bytearray()
    outb=bytearray()
    def coltoneogeo(col):
        for row in col: # for each row in dotemu column
            bp0, bp1, bp2, bp3 = 0, 0, 0, 0
            px=bytearray()
            for b in row: # extract pixel from nibbles (low nib first)
                lnib = b & 0x0f
                hnib = b >> 4
                px.append(lnib)
                px.append(hnib)
            for p in range(0,8): # Generate bitplane row bytes
                bp0 |= (px[p] & 1) << (7 - p)
                bp1 |= ((px[p] >> 1) & 1) << (7 - p)
                bp2 |= ((px[p] >> 2) & 1) << (7 - p)
                bp3 |= ((px[p] >> 3) & 1) << (7 - p)
            outa.append(bp0) # bp0 & 1 alternation on odd chr roms
            outa.append(bp1)
            outb.append(bp2) # bp2 & 3 alternation on even chr roms
            outb.append(bp3)
    with open(infile, 'rb') as f:
        data = f.read()
    if len(data) != len(octbl) * crom_size:
        print('len(data):', len(data))
        print('len(octbl):',len(octbl), '*crom_size', len(octbl) * crom_size)
        sys.exit("Haulting script, input file does not match output crom files")
    for tile in range(0,len(data),128):
        lcol, rcol = [],[]
        brow=[]
        for byte in range(0,128):
            if ((byte // 4) % 2 == 0): # arrange dotemu bytes into neogeo blocks
                brow.append(data[tile+byte])
                if (len(brow) == 4):
                    lcol.append(brow[:]) # spr blocks 3 & 4
                    brow.clear() 
            else:
                brow.append(data[tile+byte])
                if (len(brow) == 4):
                    rcol.append(brow[:]) # spr blocks 1 & 2
                    brow.clear()
        coltoneogeo(rcol)
        coltoneogeo(lcol)
        print('tile', tile // 128, 'of' , len(data) // 128, 
              end='\r', flush=True) 
    print()
    # split into C1/C3/... and C2/C4/... (NeoGeo ROM layout)
    for i in range(0, len(octbl) // 2):
        with open(octbl[i*2], 'wb') as co, open(octbl[i*2+1], 'wb') as ce:
            co.write(outa[i * crom_size: (i+1) * crom_size])
            ce.write(outb[i * crom_size: (i+1) * crom_size])
        print(octbl[i], "extracted")
        print(octbl[i+1], "extracted")

def m68k_reencode(infile, outfile): # Reencode banking of code from dotemu to neogeo
    size = os.path.getsize(infile)
    half = size // 2
    with open(infile, 'rb') as f, open(outfile, 'wb') as out:
        f.seek(half)
        out.write(f.read())
        f.seek(0)
        out.write(f.read(half))
    print(outfile, "extracted")

def m68k_split(infile,outf1,outf2): # split game_game_m68k into p1 and p2 roms
    with open(infile, 'rb') as f, open(outf1, 'wb') as p1, open(outf2, 'wb') as p2:
        p1_size = 1048576 # p1 size in bytes
        f.seek(0)
        p1.write(f.read(p1_size))
        f.seek(p1_size)
        p2.write(f.read())
    print(outf1, "extracted")
    print(outf2, "extracted")

def sfix_reencode(infile, outfile): # Reencode sfix tile format from dotemu to neogeo
    with open(infile,'rb') as f:
        data = f.read()
    #
    # reorganize every 32 byte group as follows:
    # cdab cdab -> aaaa aaaa
    # cdab cdab -> bbbb bbbb
    # cdab cdab -> cccc cccc
    # cdab cdab -> dddd dddd
    #
    output = bytearray()
    buffer = bytearray() # 32 byte array
    for i in range(0,32):
        buffer.append(0)
    for i in range(0, len(data), 32):
        for j in range(0,8):
            buffer[0+j] = data[i+j*4+2]
            buffer[8+j] = data[i+j*4+3]
            buffer[16+j] = data[i+j*4]
            buffer[24+j] = data[i+j*4+1]
        output.extend(buffer)
    with open(outfile,'wb') as f:
        f.write(output)
    print(outfile, "extracted")

def adpcm_reencode(infile, ovtbl): # Split adpcm rom merge to rom files
    # WARNING: ovtbl (output vx file table) must contain files in order!
    # split files can be less than max_chunk_size (last file will usually be smaller)
    max_chunk_size = 4194304
    chunks = []
    with open(infile, 'rb') as f:
        for i in range(len(ovtbl)):
            chunks.append(f.read(max_chunk_size))
    for i in range(len(ovtbl)):
        with open(ovtbl[i], 'wb') as out:
            out.write(chunks[i])
        print(ovtbl[i], "extracted")

def zip_make(zipname, file_list): # Make zip archive from output rom files
    with zipfile.ZipFile(zipname, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for f in file_list:
            z.write(f, arcname=os.path.basename(f))

# ------------------- Game specific operations ----------------------------------

def mslug_process(cfg, biosf):
    hashcheck({ipath(k) : v for k,v in cfg['game_input_files'].items()})
    copy_bare(ipath('mslug_zoom_table'), 
              opath('000-10.10'))
    copy_bare(ipath('mslug_game_z80'), 
              opath('201-m1.m1'))
    m68k_reencode(ipath('mslug_game_m68k'), 
                  opath('201-p1.p1'))
    adpcm_reencode(ipath('mslug_adpcm'), 
                  [opath('201-v1.v1'), 
                  opath('201-v2.v2')])
    sfix_reencode(ipath('mslug_game_sfix'), 
                  opath('201-s1.s1'))
    tiles_reencode(ipath('mslug_tiles'), 
                  [opath('201-c1.c1'), 
                  opath('201-c2.c2'), 
                  opath('201-c3.c3'), 
                  opath('201-c4.c4')],
                  cfg['crom_size'])
    hashcheck({opath(k) : v for k,v in cfg['game_output_files'].items()})
    zip_make(opath('mslug.zip'), 
             [opath(f) for f in cfg['game_output_files']])
    if biosf:
        hashcheck({ipath(k) : v for k,v in cfg['bios_input_files'].items()})
        copy_bare(ipath('mslug_bios_m68k'), 
                  opath('sp-u2.sp1'))
        sfix_reencode(ipath('mslug_bios_sfix'), 
                      opath('sfix.sfix'))
        hashcheck({opath(k) : v for k,v in cfg['bios_output_files'].items()})

def mslug2_process(cfg, biosf):
    hashcheck({ipath(k) : v for k,v in cfg['game_input_files'].items()})
    copy_bare(ipath('mslug2_zoom_table'), 
              opath('000-10.10'))
    copy_bare(ipath('mslug2_game_z80'), 
              opath('241-m1.m1'))
    m68k_split(ipath('mslug2_game_m68k'), 
               opath('241-p1.p1'),
               opath('241-p2.sp2'))
    adpcm_reencode(ipath('mslug2_adpcm'), 
                   [opath('241-v1.v1'), 
                   opath('241-v2.v2')])
    sfix_reencode(ipath('mslug2_game_sfix'), 
                  opath('241-s1.s1'))
    tiles_reencode(ipath('mslug2_tiles'), 
                   [opath('241-c1.c1'), 
                   opath('241-c2.c2'), 
                   opath('241-c3.c3'), 
                   opath('241-c4.c4')],
                   cfg['crom_size'])
    hashcheck({opath(k) : v for k,v in cfg['game_output_files'].items()})
    zip_make(opath('mslug2.zip'), 
             [opath(f) for f in cfg['game_output_files']])
    if biosf:
        hashcheck({ipath(k) : v for k,v in cfg['bios_input_files'].items()})
        copy_bare(ipath('mslug2_bios_m68k'), 
                  opath('sp-u2.sp1'))
        sfix_reencode(ipath('mslug2_bios_sfix'), 
                      opath('sfix.sfix'))
        hashcheck({opath(k) : v for k,v in cfg['bios_output_files'].items()})

def mslugx_process(cfg, biosf):
    hashcheck({ipath(k) : v for k,v in cfg['game_input_files'].items()})
    copy_bare(ipath('mslugx_zoom_table'), 
              opath('000-10.10'))
    copy_bare(ipath('mslugx_game_z80'), 
              opath('250-m1.m1'))
    m68k_split(ipath('mslugx_game_m68k'), 
               opath('250-p1.p1'),
               opath('250-p2.ep1'))
    patch(opath('250-p1.p1'),cfg['250-p1.p1_patch'])
    adpcm_reencode(ipath('mslugx_adpcm'), 
                   [opath('250-v1.v1'), 
                    opath('250-v2.v2'),
                    opath('250-v3.v3')])
    sfix_reencode(ipath('mslugx_game_sfix'), 
                  opath('250-s1.s1'))
    tiles_reencode(ipath('mslugx_tiles'), 
                   [opath('250-c1.c1'), 
                   opath('250-c2.c2'), 
                   opath('250-c3.c3'), 
                   opath('250-c4.c4'),
                   opath('250-c5.c5'),
                   opath('250-c6.c6')],
                   cfg['crom_size'])
    hashcheck({opath(k) : v for k,v in cfg['game_output_files'].items()})
    zip_make(opath('mslugx.zip'), 
             [opath(f) for f in cfg['game_output_files']])
    if biosf:
        hashcheck({ipath(k) : v for k,v in cfg['bios_input_files'].items()})
        copy_bare(ipath('mslugx_bios_m68k'), 
                  opath('sp-u2.sp1'))
        sfix_reencode(ipath('mslugx_bios_sfix'), 
                      opath('sfix.sfix'))
        hashcheck({opath(k) : v for k,v in cfg['bios_output_files'].items()})

def mslug3_process(cfg, biosf):
    print("Metal Slug 3 extraction is NOT supported.")
    print("Reason:")
    print("- Program ROMs (P1/P2) are modified to bypass Neo-SMA protection")
    print("- green.neo-sma is not present in the game files")
    print("Result: a valid MAME ROM set cannot be reconstructed from this release.")
    sys.exit(1)

GAME_HANDLERS = {
        'mslug' : mslug_process,
        'mslug2': mslug2_process,
        'mslugx': mslugx_process,
        'mslug3': mslug3_process
        }

#---------------------- Begin Execution ---------------------


game = detect_game(input_dir)
if game not in GAME_CONFIG:
    print("no compatible game detected")
    exit()

print(f"Detected game: {game}")
GAME_HANDLERS[game](GAME_CONFIG[game],args.output_bios)
print("Extraction completed successfully.")
