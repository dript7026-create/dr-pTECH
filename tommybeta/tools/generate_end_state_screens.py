#!/usr/bin/env python3
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parents[1]
RECRAFT = ROOT / "assets" / "recraft"
UI_DIR = RECRAFT / "ui"
CINEMATIC_DIR = RECRAFT / "cinematics"
QUADRANT_DIR = RECRAFT / "quadrants"
SCREEN_SIZE = (240, 160)


def pixel_fit(image: Image.Image, size) -> Image.Image:
    return ImageOps.fit(image, size, method=Image.Resampling.NEAREST, centering=(0.5, 0.5))


def load_image(path: Path, fallback_color):
    if path.exists():
        return Image.open(path).convert("RGBA")
    return Image.new("RGBA", SCREEN_SIZE, fallback_color)


def screen_fit(image: Image.Image) -> Image.Image:
    return pixel_fit(image, SCREEN_SIZE)


def crop_banner(image: Image.Image, row: int, rows: int, size=(208, 44)) -> Image.Image:
    band_h = max(1, image.height // rows)
    top = min(image.height - band_h, row * band_h)
    return pixel_fit(image.crop((0, top, image.width, top + band_h)), size)


def crop_cell(image: Image.Image, cols: int, rows: int, index: int) -> Image.Image:
    cell_w = max(1, image.width // cols)
    cell_h = max(1, image.height // rows)
    left = (index % cols) * cell_w
    top = (index // cols) * cell_h
    return image.crop((left, top, left + cell_w, top + cell_h))


def crop_horizontal_cell(image: Image.Image, cols: int, index: int) -> Image.Image:
    cell_w = max(1, image.width // cols)
    left = min(max(0, index), cols - 1) * cell_w
    return image.crop((left, 0, left + cell_w, image.height))


def layer_mix(*layers) -> Image.Image:
    canvas = screen_fit(layers[0]).convert("RGBA")
    for image, alpha in layers[1:]:
        overlay = screen_fit(image).convert("RGBA")
        overlay.putalpha(int(255 * alpha))
        canvas.alpha_composite(overlay)
    return canvas


def add_atmosphere(canvas: Image.Image, accent, edge_alpha: int, stripe_alpha: int) -> Image.Image:
    overlay = Image.new("RGBA", SCREEN_SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle((0, 0, SCREEN_SIZE[0], 18), fill=(6, 8, 10, edge_alpha))
    draw.rectangle((0, SCREEN_SIZE[1] - 26, SCREEN_SIZE[0], SCREEN_SIZE[1]), fill=(5, 7, 9, edge_alpha + 20))
    draw.rectangle((0, 0, 18, SCREEN_SIZE[1]), fill=(5, 7, 9, edge_alpha // 2))
    draw.rectangle((SCREEN_SIZE[0] - 18, 0, SCREEN_SIZE[0], SCREEN_SIZE[1]), fill=(5, 7, 9, edge_alpha // 2))
    draw.rectangle((0, 20, SCREEN_SIZE[0], 24), fill=(*accent, 210))
    draw.rectangle((0, SCREEN_SIZE[1] - 24, SCREEN_SIZE[0], SCREEN_SIZE[1] - 20), fill=(*accent, 168))
    for y in range(28, SCREEN_SIZE[1] - 28, 7):
        draw.line((18, y, SCREEN_SIZE[0] - 18, y), fill=(255, 255, 255, stripe_alpha), width=1)
    return Image.alpha_composite(canvas, overlay)


def add_focus_window(canvas: Image.Image, box, accent, fill_alpha: int) -> Image.Image:
    overlay = Image.new("RGBA", SCREEN_SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle(box, radius=14, fill=(8, 11, 14, fill_alpha), outline=(*accent, 255), width=3)
    inner = (box[0] + 8, box[1] + 8, box[2] - 8, box[3] - 8)
    draw.rounded_rectangle(inner, radius=10, fill=(255, 255, 255, 18), outline=(255, 255, 255, 28), width=1)
    return Image.alpha_composite(canvas, overlay)


def add_chip(draw: ImageDraw.ImageDraw, box, text: str, accent):
    draw.rounded_rectangle(box, radius=8, fill=(9, 12, 14, 214), outline=(*accent, 255), width=2)
    draw.text((box[0] + 10, box[1] + 6), text, fill=(255, 255, 255, 255))


def add_inset_art(canvas: Image.Image, image: Image.Image, box, accent):
    inset = pixel_fit(image.convert("RGBA"), (box[2] - box[0], box[3] - box[1]))
    border = Image.new("RGBA", SCREEN_SIZE, (0, 0, 0, 0))
    border.alpha_composite(inset, (box[0], box[1]))
    draw = ImageDraw.Draw(border)
    draw.rounded_rectangle(box, radius=12, outline=(*accent, 220), width=2)
    draw.rounded_rectangle((box[0] + 4, box[1] + 4, box[2] - 4, box[3] - 4), radius=8, outline=(255, 255, 255, 26), width=1)
    return Image.alpha_composite(canvas, border)


def save_image(image: Image.Image, path: Path) -> None:
    image.save(path)
    print(f"Wrote {path}")


def make_logo_screen(logo_source: Image.Image, title_menu: Image.Image, quadrant: Image.Image) -> Image.Image:
    canvas = layer_mix(quadrant, (title_menu, 0.34), (logo_source, 0.18))
    canvas = add_atmosphere(canvas, (64, 168, 188), 126, 18)
    canvas = add_focus_window(canvas, (18, 22, 222, 136), (112, 216, 228), 176)
    canvas = add_inset_art(canvas, crop_banner(logo_source, 0, 3, size=(168, 52)), (36, 34, 204, 86), (112, 216, 228))
    draw = ImageDraw.Draw(canvas)
    add_chip(draw, (28, 98, 110, 122), "PRESENTS", (112, 216, 228))
    add_chip(draw, (132, 98, 212, 122), "GBA BUILD", (240, 196, 88))
    draw.text((48, 128), "PRESS A OR START", fill=(238, 244, 248, 255))
    return canvas


def make_title_screen(title_menu: Image.Image, state_menu: Image.Image, throne: Image.Image, endings: Image.Image) -> Image.Image:
    canvas = layer_mix(title_menu, (throne, 0.28), (state_menu, 0.18))
    canvas = add_atmosphere(canvas, (238, 192, 94), 136, 12)
    overlay = Image.new("RGBA", SCREEN_SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle((14, 14, 172, 144), radius=18, fill=(8, 10, 12, 196), outline=(238, 192, 94, 255), width=3)
    draw.rounded_rectangle((176, 18, 226, 142), radius=14, fill=(10, 12, 14, 182), outline=(116, 204, 130, 220), width=2)
    draw.rectangle((28, 42, 158, 44), fill=(238, 192, 94, 210))
    canvas = Image.alpha_composite(canvas, overlay)
    canvas = add_inset_art(canvas, crop_banner(endings, 1, 4, size=(42, 108)), (180, 26, 222, 134), (116, 204, 130))
    draw = ImageDraw.Draw(canvas)
    draw.text((28, 22), "TOMMYBETA", fill=(255, 255, 255, 255))
    draw.text((28, 54), "HUNT THE MASKS", fill=(238, 192, 94, 255))
    draw.text((28, 122), "START NEW RUN  LOAD  DIFFICULTY", fill=(232, 238, 240, 255))
    return canvas


def make_fall_intro(fall_intro: Image.Image, quadrant: Image.Image, accent) -> Image.Image:
    canvas = layer_mix(fall_intro, (quadrant, 0.24))
    canvas = add_atmosphere(canvas, accent, 118, 10)
    canvas = add_focus_window(canvas, (16, 102, 224, 146), accent, 148)
    draw = ImageDraw.Draw(canvas)
    draw.text((34, 112), "ENTRY VECTOR LOCKED", fill=(255, 255, 255, 255))
    draw.text((34, 128), "LANDING INTO THE WILDS", fill=(*accent, 255))
    return canvas


def make_intro_panel(panel: Image.Image, quadrant: Image.Image, accent, chip: str) -> Image.Image:
    canvas = layer_mix(panel, (quadrant, 0.22))
    canvas = add_atmosphere(canvas, accent, 110, 10)
    canvas = add_focus_window(canvas, (8, 10, 232, 150), accent, 36)
    draw = ImageDraw.Draw(canvas)
    add_chip(draw, (16, 18, 68, 40), chip, accent)
    draw.rectangle((18, 132, 222, 136), fill=(*accent, 214))
    return canvas


def make_end_screen(title: str, subtitle: str, accent, overlay_alpha: int, source: Image.Image, support: Image.Image, banner: Image.Image) -> Image.Image:
    canvas = layer_mix(source, (support, 0.26))
    tint = Image.new("RGBA", SCREEN_SIZE, (*accent, overlay_alpha))
    canvas = Image.alpha_composite(canvas, tint)
    canvas = add_atmosphere(canvas, accent, 148, 14)
    canvas = add_focus_window(canvas, (14, 16, 226, 144), accent, 208)
    canvas = add_inset_art(canvas, banner, (18, 24, 222, 66), accent)

    draw = ImageDraw.Draw(canvas)
    add_chip(draw, (28, 76, 90, 100), "STATE", accent)
    draw.text((38, 84), title, fill=(255, 255, 255, 255))
    draw.text((38, 102), subtitle, fill=(236, 236, 236, 255))
    draw.rectangle((28, 122, 212, 124), fill=(*accent, 172))
    draw.text((38, 128), "PRESS A TO RETURN TO MENU", fill=(*accent, 255))
    return canvas


def main() -> None:
    endings = load_image(UI_DIR / "ingame_menu_and_endscreens_sheet.png", (24, 28, 36, 255))
    state_menu = load_image(UI_DIR / "state_menu_sheet.png", (24, 30, 38, 255))
    title_menu = load_image(UI_DIR / "title_menu_sheet.png", (40, 28, 20, 255))
    logo_source = load_image(UI_DIR / "driptech_logo_splash.png", (16, 18, 24, 255))
    fall_intro = load_image(CINEMATIC_DIR / "tommy_fall_intro_sheet.png", (18, 20, 26, 255))

    quadrants = sorted(QUADRANT_DIR.glob("*.png"))
    quadrant_images = [load_image(path, (18, 22, 28, 255)) for path in quadrants]
    while len(quadrant_images) < 8:
        quadrant_images.append(load_image(QUADRANT_DIR / "missing.png", (18, 22, 28, 255)))

    intro_strips = [
        load_image(CINEMATIC_DIR / f"intro_cinematic_sheet_{index:02d}.png", (18, 20, 26, 255))
        for index in range(1, 9)
    ]
    intro_sources = [
        crop_horizontal_cell(intro_strips[0], 16, 0),
        crop_horizontal_cell(intro_strips[1], 16, 4),
        crop_horizontal_cell(intro_strips[3], 16, 8),
        crop_horizontal_cell(intro_strips[5], 16, 12),
        crop_horizontal_cell(intro_strips[7], 16, 15),
    ]

    save_image(make_logo_screen(logo_source, title_menu, quadrant_images[0]), UI_DIR / "logo_splash_polished.png")
    save_image(make_title_screen(title_menu, state_menu, quadrant_images[7], endings), UI_DIR / "title_menu_polished.png")
    save_image(make_fall_intro(fall_intro, quadrant_images[4], (146, 220, 120)), CINEMATIC_DIR / "fall_intro_polished.png")

    intro_accents = [
        (218, 106, 92),
        (224, 178, 84),
        (132, 210, 148),
        (112, 190, 224),
        (184, 142, 232),
    ]
    intro_quadrants = [quadrant_images[7], quadrant_images[6], quadrant_images[4], quadrant_images[5], quadrant_images[1]]
    for index, panel in enumerate(intro_sources, start=1):
        polished = make_intro_panel(panel, intro_quadrants[index - 1], intro_accents[index - 1], f"0{index}")
        save_image(polished, CINEMATIC_DIR / f"intro_story_panel_{index:02d}_polished.png")

    victory = make_end_screen(
        "YOU WIN",
        "ALL EIGHT SPECIALS FINISHED THE HUNT",
        (236, 191, 74),
        58,
        title_menu,
        quadrant_images[7],
        crop_banner(endings, 0, 4),
    )
    defeat = make_end_screen(
        "GAME OVER",
        "THE EMPIRE PUSHED TOMMY BACK",
        (209, 84, 73),
        84,
        state_menu,
        quadrant_images[1],
        crop_banner(endings, 2, 4),
    )

    save_image(victory, UI_DIR / "victory_screen.png")
    save_image(defeat, UI_DIR / "defeat_screen.png")


if __name__ == "__main__":
    main()