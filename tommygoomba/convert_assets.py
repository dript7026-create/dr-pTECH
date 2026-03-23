"""
convert_assets.py

Convert PNG assets into GBDK-compatible 2bpp tile arrays and write a C file.

Usage:
  python convert_assets.py assets/*.png --output tiles.c

This script produces safe ASCII C output and a companion length symbol.
"""

from PIL import Image
import sys, os, glob, re
import argparse


def pixel_to_index(px):
    # px is (r,g,b)
    lum = (px[0]*299 + px[1]*587 + px[2]*114) // 1000
    if lum > 200:
        return 0
    if lum > 120:
        return 1
    if lum > 60:
        return 2
    return 3


def tile_bytes(img):
    # expects img 8x8
    out = []
    for y in range(8):
        bit0 = 0
        bit1 = 0
        for x in range(8):
            px = img.getpixel((x, y))
            if isinstance(px, int):
                # single channel
                idx = (px & 0x03)
            else:
                idx = pixel_to_index(px) & 0x03
            # GBDK 2bpp stores bitplane per row, left pixel -> MSB (7-x)
            bit0 |= ((idx & 1) << (7 - x))
            bit1 |= (((idx >> 1) & 1) << (7 - x))
        out.append(bit0 & 0xFF)
        out.append(bit1 & 0xFF)
    return out


def sanitize_var(name):
    # create a valid C identifier
    var = re.sub(r'[^0-9a-zA-Z_]', '_', name)
    if re.match(r'^[0-9]', var):
        var = '_' + var
    return var


def process_image(path):
    img = Image.open(path).convert('RGB')
    name = os.path.splitext(os.path.basename(path))[0]
    w, h = img.size
    tiles = []
    for ty in range(0, h, 8):
        for tx in range(0, w, 8):
            tile = img.crop((tx, ty, tx + 8, ty + 8))
            tiles.extend(tile_bytes(tile))
    return name, tiles


def write_c_file(output_path, images_data):
    with open(output_path, 'w', encoding='ascii') as f:
        f.write('/* Auto-generated tiles C file - safe ASCII output */\n')
        f.write('#include <stdint.h>\n\n')
        for name, data in images_data:
            var = sanitize_var(name)
            f.write('/* {}: {} bytes, {} tiles */\n'.format(name, len(data), len(data) // 16))
            f.write(f'const uint8_t {var}_tiles[] = {{\n')
            for i, b in enumerate(data):
                if i % 16 == 0:
                    f.write('    ')
                f.write(f'0x{b:02X}')
                if i != len(data) - 1:
                    f.write(',')
                if i % 16 == 15:
                    f.write('\n')
                else:
                    f.write(' ')
            if len(data) % 16 != 0:
                f.write('\n')
            f.write('};\n')
            f.write(f'const unsigned int {var}_tiles_len = {len(data)};\n\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='*', help='input PNG files or glob')
    parser.add_argument('--output', '-o', required=True, help='output C file')
    args = parser.parse_args()

    files = args.files if args.files else glob.glob('assets/*.png')
    images = []
    for f in files:
        if not os.path.exists(f):
            print(f'Warning: {f} not found, skipping', file=sys.stderr)
            continue
        name, data = process_image(f)
        images.append((name, data))

    if not images:
        print('No images processed.', file=sys.stderr)
        return

    write_c_file(args.output, images)


if __name__ == '__main__':
    main()
