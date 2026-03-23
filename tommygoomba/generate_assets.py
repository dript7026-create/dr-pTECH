from PIL import Image, ImageDraw
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), 'assets')
os.makedirs(OUT_DIR, exist_ok=True)

def make_tile(name, size=(8,8), color=(0,0,0), bg=(255,255,255)):
    img = Image.new('RGB', size, bg)
    draw = ImageDraw.Draw(img)
    w,h = size
    # Simple silhouette placeholder: centered square with rounded-ish shape
    draw.rectangle([1,1,w-2,h-2], fill=color)
    img.save(os.path.join(OUT_DIR, f"{name}.png"))

def make_sprite(name, size=(16,16), color=(0,0,0), bg=(255,255,255)):
    img = Image.new('RGB', size, bg)
    draw = ImageDraw.Draw(img)
    w,h = size
    # simple head+body silhouette
    draw.ellipse([2,0,13,11], fill=color)
    draw.rectangle([4,9,11,15], fill=color)
    img.save(os.path.join(OUT_DIR, f"{name}.png"))

def make_background(name, size=(160,144), color=(180,220,255)):
    img = Image.new('RGB', size, color)
    draw = ImageDraw.Draw(img)
    # add simple ground
    draw.rectangle([0,112,160,144], fill=(100,200,120))
    img.save(os.path.join(OUT_DIR, f"{name}.png"))

def make_hud_head(name, size=(24,24), color=(0,0,0), bg=(255,255,255)):
    img = Image.new('RGB', size, bg)
    draw = ImageDraw.Draw(img)
    draw.ellipse([2,2,size[0]-3,size[1]-3], fill=color)
    img.save(os.path.join(OUT_DIR, f"{name}.png"))

def main():
    print('Generating placeholder assets into', OUT_DIR)
    make_tile('tile_grass')
    make_tile('tile_block', color=(80,80,80))
    make_sprite('tommy_sprite')
    make_sprite('enemy_sprite', color=(120,0,0))
    make_background('bg_day')
    make_hud_head('hud_tommy')
    print('Done')

if __name__ == '__main__':
    main()
