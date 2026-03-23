#!/usr/bin/env python3
"""Process generated assets: copy pre-images, repalette to Game Boy 4-shade, and
convert post-repaletted images into GBDK tile data (C array) saved to
`tommybeta/src/sprites.generated.c`.

Usage:
  python process_assets.py --src ../tommygoomba/assets --out ../tommybeta/assets

This script does not call Recraft; run `tommygoomba/recraft_generate.py --yes` first to produce images.
"""
from pathlib import Path
import argparse
import shutil
from PIL import Image
import math

GB_PALETTE = [(0,0,0),(85,85,85),(170,170,170),(255,255,255)]

def nearest_palette_index(rgb, palette):
    r,g,b = rgb
    best_i = 0
    best_d = None
    for i,(pr,pg,pb) in enumerate(palette):
        d = (r-pr)**2 + (g-pg)**2 + (b-pb)**2
        if best_d is None or d < best_d:
            best_d = d; best_i = i
    return best_i

def quantize_to_gb(img):
    # convert to RGBA then map pixels to nearest GB palette index
    img = img.convert('RGBA')
    w,h = img.size
    out = Image.new('P', (w,h))
    # build flat palette
    flat = []
    for c in GB_PALETTE:
        flat.extend(c)
    while len(flat) < 768:
        flat.extend((0,0,0))
    out.putpalette(flat)
    # map pixels
    pixels = img.load()
    out_px = out.load()
    for y in range(h):
        for x in range(w):
            r,g,b,a = pixels[x,y]
            # if transparent, treat as 0
            if a < 128:
                out_px[x,y] = 0
            else:
                out_px[x,y] = nearest_palette_index((r,g,b), GB_PALETTE)
    return out

def image_to_gb_tiles(img):
    # Input: PIL Image in 'P' mode indexed to 0..3 per pixel
    w,h = img.size
    px = img.load()
    tiles = []
    for ty in range(0, h, 8):
        for tx in range(0, w, 8):
            # single 8x8 tile
            tile_bytes = []
            for row in range(8):
                y = ty + row
                if y >= h:
                    lsb = 0; msb = 0
                else:
                    lsb = 0; msb = 0
                    for col in range(8):
                        x = tx + col
                        if x >= w:
                            v = 0
                        else:
                            v = px[x,y]
                        bit0 = v & 1
                        bit1 = (v >> 1) & 1
                        lsb = (lsb << 1) | bit0
                        msb = (msb << 1) | bit1
                tile_bytes.append(lsb & 0xFF)
                tile_bytes.append(msb & 0xFF)
            tiles.append(tile_bytes)
    return tiles

def write_c_array(tiles, out_path):
    # Flatten tiles into bytes and write C array
    total_tiles = len(tiles)
    flat = []
    for t in tiles:
        flat.extend(t)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('/* Generated sprite tile data: {} tiles */\n'.format(total_tiles))
        f.write('#include <stdint.h>\n')
        f.write('const unsigned char sprites_generated[] = {\n')
        for i, b in enumerate(flat):
            if i % 12 == 0:
                f.write('    ')
            f.write('0x%02x,' % b)
            if i % 12 == 11:
                f.write('\n')
            else:
                f.write(' ')
        if len(flat) % 12 != 0:
            f.write('\n')
        f.write('};\n')
        f.write('#define NUM_SPRITE_TILES %d\n' % total_tiles)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--src', default='../tommygoomba/assets')
    p.add_argument('--out', default='../tommybeta/assets')
    args = p.parse_args()

    src = (Path(__file__).parent / args.src).resolve()
    out = (Path(__file__).parent / args.out).resolve()
    pre_dir = out / 'pre'
    post_dir = out / 'post'
    pre_dir.mkdir(parents=True, exist_ok=True)
    post_dir.mkdir(parents=True, exist_ok=True)

    imgs = list(src.glob('*.png'))
    if not imgs:
        print('No images found in', src)
        return 2

    all_tiles = []
    for pimg in imgs:
        name = pimg.stem
        print('Processing', name)
        dest_pre = pre_dir / pimg.name
        shutil.copyfile(pimg, dest_pre)
        img = Image.open(pimg).convert('RGBA')
        post = quantize_to_gb(img)
        dest_post = post_dir / f'{name}_gb.png'
        post.save(dest_post)
        # convert to tiles and append
        tiles = image_to_gb_tiles(post)
        all_tiles.extend(tiles)

    # write generated C
    out_c = Path(__file__).parent / '..' / 'src' / 'sprites.generated.c'
    out_c = out_c.resolve()
    write_c_array(all_tiles, out_c)
    # write header to indicate generated sprites present
    hdr = out_c.with_suffix('.h')
    with open(hdr, 'w', encoding='utf-8') as f:
        f.write('#define HAVE_GENERATED_SPRITES 1\n')
    print('Wrote', out_c)
    print('Wrote', hdr)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
