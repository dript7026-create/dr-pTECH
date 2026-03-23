#!/usr/bin/env python3
"""
Simple atlas packer for uniform tiles using Pillow.

Usage:
  python tools/generate_atlas.py --input assets/tiles --out assets/atlas.png --meta assets/atlas.json --tile 32

This script arranges all PNG files in the input directory into a grid atlas.
"""
import os
import sys
import argparse
from math import ceil, sqrt
from PIL import Image

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--meta", required=True)
    p.add_argument("--tile", type=int, default=32)
    args = p.parse_args()

    files = [f for f in os.listdir(args.input) if f.lower().endswith('.png')]
    files.sort()
    if not files:
        print('No PNG files found in', args.input)
        return 1

    tile = args.tile
    count = len(files)
    cols = int(ceil(sqrt(count)))
    rows = int(ceil(count / cols))

    atlas_w = cols * tile
    atlas_h = rows * tile
    atlas = Image.new('RGBA', (atlas_w, atlas_h), (0,0,0,0))

    frames = {}
    for i, fname in enumerate(files):
        img = Image.open(os.path.join(args.input, fname)).convert('RGBA')
        # resize or pad if different size
        if img.width != tile or img.height != tile:
            img = img.resize((tile, tile), Image.NEAREST)
        col = i % cols
        row = i // cols
        x = col * tile
        y = row * tile
        atlas.paste(img, (x, y), img)
        key = os.path.splitext(fname)[0]
        frames[key] = { 'x': x, 'y': y, 'w': tile, 'h': tile }

    atlas.save(args.out)

    import json
    meta = { 'tile_w': tile, 'tile_h': tile, 'cols': cols, 'rows': rows, 'frames': frames }
    with open(args.meta, 'w', encoding='utf-8') as mf:
        json.dump(meta, mf, indent=2)

    print('Written', args.out, 'and', args.meta)
    return 0

if __name__ == '__main__':
    sys.exit(main())
