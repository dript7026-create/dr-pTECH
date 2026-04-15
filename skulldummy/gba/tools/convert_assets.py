#!/usr/bin/env python3
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageOps


ROOT = Path(__file__).resolve().parents[1]
ANDROID_RES = ROOT.parent / "android" / "app" / "src" / "main" / "res" / "drawable-nodpi"
OUT_DIR = ROOT / "build" / "gba_assets"
HEADER = OUT_DIR / "skulldummy_assets.h"
SOURCE = OUT_DIR / "skulldummy_assets.c"

SCREEN_W = 240
SCREEN_H = 160
SCREEN_PIXELS = SCREEN_W * SCREEN_H
SPRITE_W = 64
SPRITE_H = 64
SPRITE_PIXELS = SPRITE_W * SPRITE_H
ICON_W = 24
ICON_H = 24
ICON_PIXELS = ICON_W * ICON_H
TRANSPARENT = 0x8000


def fit_cover(image: Image.Image, size, centering=(0.5, 0.5)):
    return ImageOps.fit(image, size, method=Image.Resampling.NEAREST, centering=centering)


def fit_contain(image: Image.Image, size, fill):
    canvas = Image.new(image.mode, size, fill)
    source = image.copy()
    source.thumbnail(size, Image.Resampling.NEAREST)
    left = (size[0] - source.width) // 2
    top = (size[1] - source.height) // 2
    canvas.paste(source, (left, top), source if "A" in source.getbands() else None)
    return canvas


def to_bgr555(red: int, green: int, blue: int) -> int:
    r5 = (red * 31) // 255
    g5 = (green * 31) // 255
    b5 = (blue * 31) // 255
    return r5 | (g5 << 5) | (b5 << 10)


def trim_visible_bounds(image: Image.Image) -> Image.Image:
    if "A" not in image.getbands():
        return image
    bounds = image.getchannel("A").getbbox()
    if not bounds:
        return image
    return image.crop(bounds)


def background_samples(image: Image.Image):
    width, height = image.size
    return [
        image.getpixel((0, 0)),
        image.getpixel((width - 1, 0)),
        image.getpixel((0, height - 1)),
        image.getpixel((width - 1, height - 1)),
    ]


def is_background(pixel, samples):
    red, green, blue, alpha = pixel
    if alpha < 24:
        return True
    for sample in samples:
        sr, sg, sb, sa = sample
        if sa < 24:
            continue
        if abs(red - sr) + abs(green - sg) + abs(blue - sb) <= 54:
            return True
    return False


def encode_bitmap(image: Image.Image):
    pixels = []
    for py in range(image.height):
        for px in range(image.width):
            red, green, blue = image.getpixel((px, py))
            pixels.append(to_bgr555(red, green, blue))
    return pixels


def encode_transparent(image: Image.Image):
    image = trim_visible_bounds(image)
    image = fit_contain(image, (SPRITE_W, SPRITE_H), (0, 0, 0, 0))
    samples = background_samples(image)
    pixels = []
    for py in range(image.height):
        for px in range(image.width):
            pixel = image.getpixel((px, py))
            if is_background(pixel, samples):
                pixels.append(TRANSPARENT)
            else:
                pixels.append(to_bgr555(pixel[0], pixel[1], pixel[2]))
    return pixels


def tint_overlay(image: Image.Image, color, opacity: float):
    overlay = Image.new("RGBA", image.size, (*color, int(255 * opacity)))
    return Image.alpha_composite(image, overlay)


def compose_background(variant: int):
    variant_specs = [
        {
            "centers": ((0.50, 0.42), (0.56, 0.50), (0.48, 0.58)),
            "alphas": (255, 220, 188),
            "color": 1.08,
            "brightness": 1.00,
            "contrast": 1.06,
            "tint": (18, 28, 40),
            "tint_mix": 0.08,
            "bands": [((0, 0, SCREEN_W, 34), (10, 14, 22, 26)), ((0, 116, SCREEN_W, SCREEN_H), (32, 16, 12, 34))],
        },
        {
            "centers": ((0.34, 0.48), (0.42, 0.56), (0.62, 0.44)),
            "alphas": (244, 204, 172),
            "color": 0.72,
            "brightness": 0.90,
            "contrast": 1.18,
            "tint": (88, 42, 16),
            "tint_mix": 0.16,
            "bands": [((0, 0, SCREEN_W, 28), (22, 16, 10, 28)), ((0, 102, SCREEN_W, SCREEN_H), (76, 28, 14, 42))],
        },
        {
            "centers": ((0.68, 0.40), (0.58, 0.48), (0.36, 0.60)),
            "alphas": (232, 192, 220),
            "color": 0.92,
            "brightness": 0.76,
            "contrast": 1.24,
            "tint": (12, 68, 96),
            "tint_mix": 0.18,
            "bands": [((0, 0, SCREEN_W, 42), (8, 22, 46, 34)), ((0, 94, SCREEN_W, SCREEN_H), (4, 12, 24, 56))],
        },
    ]
    spec = variant_specs[variant % len(variant_specs)]
    base = Image.new("RGBA", (SCREEN_W, SCREEN_H), (0, 0, 0, 255))
    layers = [
        Image.open(ANDROID_RES / "blunin_bg_layer_1.png").convert("RGBA"),
        Image.open(ANDROID_RES / "blunin_bg_layer_2.png").convert("RGBA"),
        Image.open(ANDROID_RES / "blunin_bg_layer_3.png").convert("RGBA"),
    ]
    for layer, alpha, center in zip(layers, spec["alphas"], spec["centers"]):
        fitted = fit_cover(layer, (SCREEN_W, SCREEN_H), centering=center)
        fitted.putalpha(alpha)
        base.alpha_composite(fitted)

    base = tint_overlay(base, spec["tint"], spec["tint_mix"])
    draw = ImageDraw.Draw(base)
    for bounds, color in spec["bands"]:
        draw.rectangle(bounds, fill=color)

    rgb = base.convert("RGB")
    rgb = ImageEnhance.Color(rgb).enhance(spec["color"])
    rgb = ImageEnhance.Brightness(rgb).enhance(spec["brightness"])
    rgb = ImageEnhance.Contrast(rgb).enhance(spec["contrast"])
    return encode_bitmap(rgb)


def extract_strip_frame(name: str, frame_count: int, frame_index: int):
    image = Image.open(ANDROID_RES / name).convert("RGBA")
    cell_w = max(1, image.width // frame_count)
    safe_index = max(0, min(frame_count - 1, frame_index))
    frame = image.crop((safe_index * cell_w, 0, safe_index * cell_w + cell_w, image.height))
    return encode_transparent(frame)


def extract_icon(name: str):
    image = Image.open(ANDROID_RES / name).convert("RGBA")
    image = fit_contain(trim_visible_bounds(image), (ICON_W, ICON_H), (0, 0, 0, 0))
    samples = background_samples(image)
    pixels = []
    for py in range(image.height):
        for px in range(image.width):
            pixel = image.getpixel((px, py))
            if is_background(pixel, samples):
                pixels.append(TRANSPARENT)
            else:
                pixels.append(to_bgr555(pixel[0], pixel[1], pixel[2]))
    return pixels


def write_array(handle, symbol_name, values, chunk=12):
    handle.write(f"const uint16_t {symbol_name}[{len(values)}] = {{\n")
    for index in range(0, len(values), chunk):
        chunk_values = values[index:index + chunk]
        handle.write("    " + ", ".join(f"0x{value:04x}" for value in chunk_values) + ",\n")
    handle.write("};\n\n")


def write_frame_set(handle, symbol_name, frames, pixel_count, chunk=12):
    handle.write(f"const uint16_t {symbol_name}[{len(frames)}][{pixel_count}] = {{\n")
    for frame in frames:
        handle.write("    {\n")
        for index in range(0, len(frame), chunk):
            chunk_values = frame[index:index + chunk]
            handle.write("        " + ", ".join(f"0x{value:04x}" for value in chunk_values) + ",\n")
        handle.write("    },\n")
    handle.write("};\n\n")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    backgrounds = [compose_background(variant) for variant in range(3)]
    idle_frames = [extract_strip_frame("blunin_idle_sheet.png", 10, index) for index in (0, 2, 4, 5, 7, 9)]
    walk_frames = [extract_strip_frame("blunin_walk_sheet.png", 16, index) for index in (0, 3, 6, 9, 12, 15)]
    attack_frames = [extract_strip_frame("blunin_attack_sheet.png", 53, index) for index in (0, 8, 16, 24, 36, 48)]
    relic_icon = extract_icon("skull_relic_1.png")

    HEADER.write_text(
        "#ifndef SKULLDUMMY_ASSETS_H\n"
        "#define SKULLDUMMY_ASSETS_H\n\n"
        "#include <stdint.h>\n\n"
        "#define SKULLDUMMY_SCREEN_W 240\n"
        "#define SKULLDUMMY_SCREEN_H 160\n"
        "#define SKULLDUMMY_SCREEN_PIXELS 38400\n"
        "#define SKULLDUMMY_BG_COUNT 3\n"
        "#define SKULLDUMMY_SPRITE_W 64\n"
        "#define SKULLDUMMY_SPRITE_H 64\n"
        "#define SKULLDUMMY_SPRITE_PIXELS 4096\n"
        "#define SKULLDUMMY_BOSS_FRAME_COUNT 6\n"
        "#define SKULLDUMMY_ICON_W 24\n"
        "#define SKULLDUMMY_ICON_H 24\n"
        "#define SKULLDUMMY_ICON_PIXELS 576\n"
        "#define SKULLDUMMY_TRANSPARENT_COLOR 0x8000\n\n"
        "extern const uint16_t skulldummy_backgrounds[SKULLDUMMY_BG_COUNT][SKULLDUMMY_SCREEN_PIXELS];\n"
        "extern const uint16_t skulldummy_blunin_idle[SKULLDUMMY_BOSS_FRAME_COUNT][SKULLDUMMY_SPRITE_PIXELS];\n"
        "extern const uint16_t skulldummy_blunin_walk[SKULLDUMMY_BOSS_FRAME_COUNT][SKULLDUMMY_SPRITE_PIXELS];\n"
        "extern const uint16_t skulldummy_blunin_attack[SKULLDUMMY_BOSS_FRAME_COUNT][SKULLDUMMY_SPRITE_PIXELS];\n"
        "extern const uint16_t skulldummy_relic_icon[SKULLDUMMY_ICON_PIXELS];\n\n"
        "#endif\n",
        encoding="ascii",
    )

    with SOURCE.open("w", encoding="ascii", newline="\n") as handle:
        handle.write('#include "skulldummy_assets.h"\n\n')
        write_frame_set(handle, "skulldummy_backgrounds", backgrounds, SCREEN_PIXELS)
        write_frame_set(handle, "skulldummy_blunin_idle", idle_frames, SPRITE_PIXELS)
        write_frame_set(handle, "skulldummy_blunin_walk", walk_frames, SPRITE_PIXELS)
        write_frame_set(handle, "skulldummy_blunin_attack", attack_frames, SPRITE_PIXELS)
        write_array(handle, "skulldummy_relic_icon", relic_icon)


if __name__ == "__main__":
    main()