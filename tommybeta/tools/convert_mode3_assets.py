#!/usr/bin/env python3
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
RECRAFT = ROOT / "assets" / "recraft"
OUT_DIR = ROOT / "build" / "gba_assets"
HEADER = OUT_DIR / "tommybeta_mode3_assets.h"
SOURCE = OUT_DIR / "tommybeta_mode3_assets.c"
SCREEN_W = 240
SCREEN_H = 160
PIXELS = SCREEN_W * SCREEN_H
SPRITE_W = 64
SPRITE_H = 64
SPRITE_PIXELS = SPRITE_W * SPRITE_H
SUPPORT_FRAME_COUNT = 8
ICON_W = 24
ICON_H = 24
ICON_PIXELS = ICON_W * ICON_H
FX_W = 32
FX_H = 32
FX_PIXELS = FX_W * FX_H
PROP_W = 32
PROP_H = 32
PROP_PIXELS = PROP_W * PROP_H
TERRAIN_FRAME_COUNT = 8
CRITTER_W = 16
CRITTER_H = 16
CRITTER_PIXELS = CRITTER_W * CRITTER_H
HUD_W = 240
HUD_H = 32
HUD_PIXELS = HUD_W * HUD_H
INTRO_PANEL_COUNT = 5
TRANSPARENT = 0x8000


def fit_cover(image: Image.Image, size):
    return ImageOps.fit(image, size, method=Image.Resampling.NEAREST, centering=(0.5, 0.5))


def fit_contain(image: Image.Image, size, fill):
    canvas = Image.new(image.mode, size, fill)
    source = image.copy()
    source.thumbnail(size, Image.Resampling.NEAREST)
    left = (size[0] - source.width) // 2
    top = (size[1] - source.height) // 2
    canvas.paste(source, (left, top))
    return canvas


def sanitize(name: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in name.lower())


def to_bgr555(red: int, green: int, blue: int) -> int:
    r5 = (red * 31) // 255
    g5 = (green * 31) // 255
    b5 = (blue * 31) // 255
    return r5 | (g5 << 5) | (b5 << 10)


def background_samples(image: Image.Image):
    width, height = image.size
    return [
        image.getpixel((0, 0)),
        image.getpixel((width - 1, 0)),
        image.getpixel((0, height - 1)),
        image.getpixel((width - 1, height - 1)),
    ]


def trim_visible_bounds(image: Image.Image) -> Image.Image:
    if "A" not in image.getbands():
        return image
    alpha = image.getchannel("A")
    bounds = alpha.getbbox()
    if not bounds:
        return image
    return image.crop(bounds)


def is_background(pixel, samples, alpha_only=False):
    red, green, blue, alpha = pixel
    if alpha < 24:
        return True
    if alpha_only:
        return False
    for sample in samples:
        if len(sample) > 3 and sample[3] < 24:
            continue
        score = abs(red - sample[0]) + abs(green - sample[1]) + abs(blue - sample[2])
        if score <= 54:
            return True
    return False


def fit_bitmap(path: Path, size=(SCREEN_W, SCREEN_H)):
    image = Image.open(path).convert("RGB")
    image = fit_cover(image, size)
    pixels = []
    for py in range(size[1]):
        for px in range(size[0]):
            red, green, blue = image.getpixel((px, py))
            pixels.append(to_bgr555(red, green, blue))
    return pixels


def existing_path(*paths: Path) -> Path:
    for path in paths:
        if path.exists():
            return path
    return paths[0]


def blank_frame(width, height, transparent=False):
    color = TRANSPARENT if transparent else 0
    return [color] * (width * height)


def render_frame(frame: Image.Image, out_size, transparent=True):
    alpha_only = False
    if transparent and "A" in frame.getbands():
        alpha_only = frame.getchannel("A").getextrema()[0] < 255
        frame = trim_visible_bounds(frame)
    fill = (0, 0, 0, 0) if transparent else (0, 0, 0, 255)
    frame = fit_contain(frame, out_size, fill)
    samples = background_samples(frame)
    pixels = []
    for py in range(out_size[1]):
        for px in range(out_size[0]):
            pixel = frame.getpixel((px, py))
            if transparent and is_background(pixel, samples, alpha_only=alpha_only):
                pixels.append(TRANSPARENT)
            else:
                pixels.append(to_bgr555(pixel[0], pixel[1], pixel[2]))
    return pixels


def crop_sheet(path: Path, cols: int, rows: int, indices, out_size, transparent=True):
    if not path.exists():
        return [blank_frame(out_size[0], out_size[1], transparent=transparent) for _ in indices]

    image = Image.open(path).convert("RGBA")
    cell_w = max(1, image.width // cols)
    cell_h = max(1, image.height // rows)
    frames = []
    for index in indices:
        left = (index % cols) * cell_w
        top = (index // cols) * cell_h
        frame = image.crop((left, top, left + cell_w, top + cell_h))
        frames.append(render_frame(frame, out_size, transparent=transparent))
    return frames


def crop_strip(path: Path, frame_count: int, indices, out_size, transparent=True):
    if not path.exists():
        return [blank_frame(out_size[0], out_size[1], transparent=transparent) for _ in indices]

    image = Image.open(path).convert("RGBA")
    cell_w = max(1, image.width // frame_count)
    frames = []
    for index in indices:
        safe_index = max(0, min(frame_count - 1, index))
        left = safe_index * cell_w
        frame = image.crop((left, 0, left + cell_w, image.height))
        frames.append(render_frame(frame, out_size, transparent=transparent))
    return frames


def crop_strip_frame(path: Path, frame_count: int, index: int, out_size, transparent=True):
    return crop_strip(path, frame_count, [index], out_size, transparent=transparent)[0]


def fit_strip_frame(path: Path, frame_count: int, index: int, size=(SCREEN_W, SCREEN_H)):
    if not path.exists():
        return blank_frame(size[0], size[1])
    image = Image.open(path).convert("RGB")
    cell_w = max(1, image.width // frame_count)
    safe_index = max(0, min(frame_count - 1, index))
    frame = image.crop((safe_index * cell_w, 0, safe_index * cell_w + cell_w, image.height))
    frame = fit_cover(frame, size)
    pixels = []
    for py in range(size[1]):
        for px in range(size[0]):
            red, green, blue = frame.getpixel((px, py))
            pixels.append(to_bgr555(red, green, blue))
    return pixels


def load_frame_specs(specs, out_size, transparent=True):
    return [
        crop_strip_frame(path, frame_count, index, out_size, transparent=transparent)
        for path, frame_count, index in specs
    ]


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
    quadrant_paths = sorted((RECRAFT / "quadrants").glob("quadrant_*.png"))
    if not quadrant_paths:
        quadrant_paths = sorted((RECRAFT / "quadrants").glob("*.png"))
    if not quadrant_paths:
        raise SystemExit("No TommyBeta Recraft PNG assets found to convert.")
    quadrant_paths = quadrant_paths[:10]

    ui_dir = RECRAFT / "ui"
    char_dir = RECRAFT / "characters"
    env_dir = RECRAFT / "environment"
    fx_dir = RECRAFT / "fx"
    cinematic_dir = RECRAFT / "cinematics"

    fullscreen = {
        "quadrants": [(sanitize(path.stem), path) for path in quadrant_paths],
        "logo_splash": existing_path(
            ui_dir / "logo_splash_polished.png",
            ui_dir / "driptech_logo_splash.png",
        ),
        "title_menu": existing_path(
            ui_dir / "title_menu_polished.png",
            ui_dir / "title_menu_sheet.png",
        ),
        "menu_endings": ui_dir / "ingame_menu_and_endscreens_sheet.png",
        "state_menu": ui_dir / "state_menu_sheet.png",
        "pause_window": ui_dir / "pause_window_templates_sheet.png",
        "codex_screen": ui_dir / "codex_sheet.png",
        "fall_intro": existing_path(
            cinematic_dir / "fall_intro_polished.png",
            cinematic_dir / "tommy_fall_intro_sheet.png",
        ),
        "victory_screen": ui_dir / "victory_screen.png",
        "defeat_screen": ui_dir / "defeat_screen.png",
        "intro_strips": [cinematic_dir / f"intro_cinematic_sheet_{index:02d}.png" for index in range(1, 9)],
    }

    intro_panel_specs = [(0, 0), (1, 4), (3, 8), (5, 12), (7, 15)]
    terrain_specs = [
        (env_dir / "canopy_tiles_sheet.png", 4, 0),
        (env_dir / "river_tiles_sheet.png", 4, 0),
        (env_dir / "ruin_gate_tiles_sheet.png", 4, 0),
        (env_dir / "bog_tiles_sheet.png", 4, 0),
        (env_dir / "root_bridge_tiles_sheet.png", 4, 0),
        (env_dir / "temple_night_tiles_sheet.png", 4, 0),
        (env_dir / "edge_gate_portal_checkpoint_sheet.png", 8, 0),
        (env_dir / "puzzle_and_healing_objects_sheet.png", 8, 0),
    ]
    terrain_frames = load_frame_specs(terrain_specs, (PROP_W, PROP_H), transparent=True)

    sprite_sets = {
        "tommy_idle": crop_strip(char_dir / "tommy_idle_sheet.png", 4, [0, 1, 2, 3], (SPRITE_W, SPRITE_H)),
        "tommy_bite": crop_strip(char_dir / "tommy_bite_combo_sheet.png", 3, [0, 1, 2], (SPRITE_W, SPRITE_H)),
        "tommy_special": load_frame_specs([
            (char_dir / "tommy_charge_dash_sheet.png", 4, 1),
            (char_dir / "tommy_sky_chomp_sheet.png", 4, 1),
            (char_dir / "tommy_tail_cyclone_sheet.png", 4, 1),
            (char_dir / "tommy_ember_spit_sheet.png", 4, 1),
            (char_dir / "tommy_iron_gut_slam_sheet.png", 4, 1),
            (char_dir / "tommy_phantom_pounce_sheet.png", 4, 1),
            (char_dir / "tommy_hunger_howl_sheet.png", 4, 1),
            (char_dir / "tommy_crownbreaker_sheet.png", 8, 3),
        ], (SPRITE_W, SPRITE_H)),
        "tommy_support": load_frame_specs([
            (char_dir / "tommy_land_sheet.png", 4, 0),
            (char_dir / "tommy_hurt_stun_sheet.png", 4, 0),
            (char_dir / "tommy_hurt_stun_sheet.png", 4, 1),
            (cinematic_dir / "tommy_fall_intro_sheet.png", 8, 2),
            (char_dir / "tommy_heal_sheet.png", 4, 0),
            (char_dir / "tommy_heal_sheet.png", 4, 1),
            (char_dir / "tommy_victory_sheet.png", 4, 1),
            (char_dir / "tommy_death_sheet.png", 4, 2),
        ], (SPRITE_W, SPRITE_H)),
        "mareaou_idle": load_frame_specs([
            (char_dir / "mareaou_idle_sheet.png", 4, 0),
            (char_dir / "mareaou_idle_sheet.png", 4, 1),
            (char_dir / "mareaou_stalk_sheet.png", 4, 1),
            (char_dir / "mareaou_stalk_sheet.png", 4, 2),
        ], (SPRITE_W, SPRITE_H)),
        "mareaou_attack": crop_strip(char_dir / "mareaou_attack_combo_a_sheet.png", 4, [0, 1, 2, 3], (SPRITE_W, SPRITE_H))
        + crop_strip(char_dir / "mareaou_attack_combo_b_sheet.png", 3, [0, 1, 2], (SPRITE_W, SPRITE_H)),
        "mareaou_support": load_frame_specs([
            (char_dir / "mareaou_guard_parry_sheet.png", 4, 0),
            (char_dir / "mareaou_guard_parry_sheet.png", 4, 1),
            (char_dir / "mareaou_dodge_sheet.png", 4, 1),
            (char_dir / "mareaou_dodge_sheet.png", 4, 2),
            (char_dir / "mareaou_hurt_stun_sheet.png", 4, 0),
            (char_dir / "mareaou_hurt_stun_sheet.png", 4, 1),
            (char_dir / "mareaou_heal_sheet.png", 4, 1),
            (char_dir / "mareaou_taunt_sheet.png", 4, 1),
        ], (SPRITE_W, SPRITE_H)),
        "special_icons": crop_strip(ui_dir / "special_icon_sheet.png", 8, list(range(8)), (ICON_W, ICON_H)),
        "combo_icons": crop_strip(ui_dir / "status_icon_sheet.png", 8, [0, 1, 2, 3], (ICON_W, ICON_H)),
        "ambience": crop_strip(fx_dir / "ambience_fx_sheet.png", 4, [0, 1, 2, 3], (ICON_W, ICON_H)),
        "combat_basic": crop_strip(fx_dir / "combat_fx_basic_sheet.png", 3, [0, 1, 2], (FX_W, FX_H)),
        "combat_special": load_frame_specs([
            (fx_dir / "charge_dash_fx_sheet.png", 4, 1),
            (fx_dir / "sky_chomp_fx_sheet.png", 4, 1),
            (fx_dir / "tail_cyclone_fx_sheet.png", 4, 1),
            (fx_dir / "ember_spit_fx_sheet.png", 4, 1),
            (fx_dir / "iron_gut_slam_fx_sheet.png", 4, 1),
            (fx_dir / "phantom_pounce_fx_sheet.png", 4, 1),
            (fx_dir / "hunger_howl_fx_sheet.png", 4, 1),
            (fx_dir / "crownbreaker_fx_sheet.png", 4, 1),
        ], (FX_W, FX_H)),
        "props": crop_strip(env_dir / "environmental_objects_sheet_a.png", 8, [0, 1, 2, 3], (PROP_W, PROP_H)),
        "critters": crop_strip(env_dir / "roaming_creatures_sheet.png", 4, [0, 1, 2, 3], (CRITTER_W, CRITTER_H)),
        "terrain_overlays": terrain_frames,
    }
    hud_panel_path = ui_dir / "tommy_hud_sheet.png"
    hud_panel = fit_bitmap(hud_panel_path, (HUD_W, HUD_H)) if hud_panel_path.exists() else blank_frame(HUD_W, HUD_H)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    quadrant_names = [name for name, _ in fullscreen["quadrants"]]
    quadrant_bitmaps = [fit_bitmap(path) for _, path in fullscreen["quadrants"]]
    fallback_bitmap = quadrant_bitmaps[0]
    logo_bitmap = fit_bitmap(fullscreen["logo_splash"]) if fullscreen["logo_splash"].exists() else fallback_bitmap
    title_bitmap = fit_bitmap(fullscreen["title_menu"]) if fullscreen["title_menu"].exists() else fallback_bitmap
    menu_bitmap = fit_bitmap(fullscreen["menu_endings"]) if fullscreen["menu_endings"].exists() else fallback_bitmap
    state_menu_bitmap = fit_bitmap(fullscreen["state_menu"]) if fullscreen["state_menu"].exists() else menu_bitmap
    pause_window_bitmap = fit_bitmap(fullscreen["pause_window"]) if fullscreen["pause_window"].exists() else state_menu_bitmap
    codex_bitmap = fit_bitmap(fullscreen["codex_screen"]) if fullscreen["codex_screen"].exists() else state_menu_bitmap
    fall_bitmap = fit_bitmap(fullscreen["fall_intro"]) if fullscreen["fall_intro"].exists() else fallback_bitmap
    victory_bitmap = fit_bitmap(fullscreen["victory_screen"]) if fullscreen["victory_screen"].exists() else fallback_bitmap
    defeat_bitmap = fit_bitmap(fullscreen["defeat_screen"]) if fullscreen["defeat_screen"].exists() else fallback_bitmap
    intro_panel_bitmaps = [
        fit_strip_frame(fullscreen["intro_strips"][strip_index], 16, frame_index)
        for strip_index, frame_index in intro_panel_specs
    ]
    have_intro_panels = all(fullscreen["intro_strips"][strip_index].exists() for strip_index, _ in intro_panel_specs)
    have_victory = fullscreen["victory_screen"].exists()
    have_defeat = fullscreen["defeat_screen"].exists()

    with HEADER.open("w", encoding="utf-8") as handle:
        handle.write("#ifndef TOMMYBETA_MODE3_ASSETS_H\n")
        handle.write("#define TOMMYBETA_MODE3_ASSETS_H\n\n")
        handle.write("#include <stdint.h>\n\n")
        handle.write(f"#define TOMMYBETA_SCREEN_W {SCREEN_W}\n")
        handle.write(f"#define TOMMYBETA_SCREEN_H {SCREEN_H}\n")
        handle.write(f"#define TOMMYBETA_SCREEN_PIXELS {PIXELS}\n")
        handle.write(f"#define TOMMYBETA_QUADRANT_COUNT {len(quadrant_names)}\n")
        handle.write(f"#define TOMMYBETA_HAVE_LOGO_SPLASH {1 if fullscreen['logo_splash'].exists() else 0}\n")
        handle.write(f"#define TOMMYBETA_HAVE_TITLE_MENU {1 if fullscreen['title_menu'].exists() else 0}\n")
        handle.write(f"#define TOMMYBETA_HAVE_ENDINGS {1 if fullscreen['menu_endings'].exists() else 0}\n")
        handle.write(f"#define TOMMYBETA_HAVE_STATE_MENU {1 if fullscreen['state_menu'].exists() else 0}\n")
        handle.write(f"#define TOMMYBETA_HAVE_PAUSE_WINDOW {1 if fullscreen['pause_window'].exists() else 0}\n")
        handle.write(f"#define TOMMYBETA_HAVE_CODEX_SCREEN {1 if fullscreen['codex_screen'].exists() else 0}\n")
        handle.write(f"#define TOMMYBETA_HAVE_FALL_INTRO {1 if fullscreen['fall_intro'].exists() else 0}\n")
        handle.write(f"#define TOMMYBETA_HAVE_INTRO_PANELS {1 if have_intro_panels else 0}\n")
        handle.write(f"#define TOMMYBETA_HAVE_VICTORY_SCREEN {1 if have_victory else 0}\n")
        handle.write(f"#define TOMMYBETA_HAVE_DEFEAT_SCREEN {1 if have_defeat else 0}\n")
        handle.write(f"#define TOMMYBETA_INTRO_PANEL_COUNT {INTRO_PANEL_COUNT}\n")
        handle.write(f"#define TOMMYBETA_TRANSPARENT_COLOR 0x{TRANSPARENT:04x}\n")
        handle.write(f"#define TOMMYBETA_SPRITE_W {SPRITE_W}\n")
        handle.write(f"#define TOMMYBETA_SPRITE_H {SPRITE_H}\n")
        handle.write(f"#define TOMMYBETA_SPRITE_PIXELS {SPRITE_PIXELS}\n")
        handle.write(f"#define TOMMYBETA_SUPPORT_FRAME_COUNT {SUPPORT_FRAME_COUNT}\n")
        handle.write(f"#define TOMMYBETA_ICON_W {ICON_W}\n")
        handle.write(f"#define TOMMYBETA_ICON_H {ICON_H}\n")
        handle.write(f"#define TOMMYBETA_ICON_PIXELS {ICON_PIXELS}\n")
        handle.write(f"#define TOMMYBETA_FX_W {FX_W}\n")
        handle.write(f"#define TOMMYBETA_FX_H {FX_H}\n")
        handle.write(f"#define TOMMYBETA_FX_PIXELS {FX_PIXELS}\n")
        handle.write(f"#define TOMMYBETA_PROP_W {PROP_W}\n")
        handle.write(f"#define TOMMYBETA_PROP_H {PROP_H}\n")
        handle.write(f"#define TOMMYBETA_PROP_PIXELS {PROP_PIXELS}\n")
        handle.write(f"#define TOMMYBETA_TERRAIN_OVERLAY_COUNT {TERRAIN_FRAME_COUNT}\n")
        handle.write(f"#define TOMMYBETA_CRITTER_W {CRITTER_W}\n")
        handle.write(f"#define TOMMYBETA_CRITTER_H {CRITTER_H}\n")
        handle.write(f"#define TOMMYBETA_CRITTER_PIXELS {CRITTER_PIXELS}\n")
        handle.write(f"#define TOMMYBETA_HUD_W {HUD_W}\n")
        handle.write(f"#define TOMMYBETA_HUD_H {HUD_H}\n")
        handle.write(f"#define TOMMYBETA_HUD_PIXELS {HUD_PIXELS}\n\n")
        handle.write("extern const uint16_t tommybeta_quadrant_bitmaps[TOMMYBETA_QUADRANT_COUNT][TOMMYBETA_SCREEN_PIXELS];\n")
        handle.write("extern const uint16_t tommybeta_logo_splash_bitmap[TOMMYBETA_SCREEN_PIXELS];\n")
        handle.write("extern const uint16_t tommybeta_title_menu_bitmap[TOMMYBETA_SCREEN_PIXELS];\n")
        handle.write("extern const uint16_t tommybeta_menu_endings_bitmap[TOMMYBETA_SCREEN_PIXELS];\n")
        handle.write("extern const uint16_t tommybeta_state_menu_bitmap[TOMMYBETA_SCREEN_PIXELS];\n")
        handle.write("extern const uint16_t tommybeta_pause_window_bitmap[TOMMYBETA_SCREEN_PIXELS];\n")
        handle.write("extern const uint16_t tommybeta_codex_bitmap[TOMMYBETA_SCREEN_PIXELS];\n")
        handle.write("extern const uint16_t tommybeta_fall_intro_bitmap[TOMMYBETA_SCREEN_PIXELS];\n")
        handle.write("extern const uint16_t tommybeta_intro_panel_bitmaps[TOMMYBETA_INTRO_PANEL_COUNT][TOMMYBETA_SCREEN_PIXELS];\n")
        handle.write("extern const uint16_t tommybeta_victory_screen_bitmap[TOMMYBETA_SCREEN_PIXELS];\n")
        handle.write("extern const uint16_t tommybeta_defeat_screen_bitmap[TOMMYBETA_SCREEN_PIXELS];\n")
        handle.write("extern const char *const tommybeta_quadrant_names[TOMMYBETA_QUADRANT_COUNT];\n")
        handle.write("extern const uint16_t tommybeta_tommy_idle_frames[4][TOMMYBETA_SPRITE_PIXELS];\n")
        handle.write("extern const uint16_t tommybeta_tommy_bite_frames[3][TOMMYBETA_SPRITE_PIXELS];\n")
        handle.write("extern const uint16_t tommybeta_tommy_special_frames[8][TOMMYBETA_SPRITE_PIXELS];\n")
        handle.write("extern const uint16_t tommybeta_tommy_support_frames[TOMMYBETA_SUPPORT_FRAME_COUNT][TOMMYBETA_SPRITE_PIXELS];\n")
        handle.write("extern const uint16_t tommybeta_mareaou_idle_frames[4][TOMMYBETA_SPRITE_PIXELS];\n")
        handle.write("extern const uint16_t tommybeta_mareaou_attack_frames[7][TOMMYBETA_SPRITE_PIXELS];\n")
        handle.write("extern const uint16_t tommybeta_mareaou_support_frames[TOMMYBETA_SUPPORT_FRAME_COUNT][TOMMYBETA_SPRITE_PIXELS];\n")
        handle.write("extern const uint16_t tommybeta_special_icon_frames[8][TOMMYBETA_ICON_PIXELS];\n")
        handle.write("extern const uint16_t tommybeta_combo_icon_frames[4][TOMMYBETA_ICON_PIXELS];\n")
        handle.write("extern const uint16_t tommybeta_ambience_frames[4][TOMMYBETA_ICON_PIXELS];\n")
        handle.write("extern const uint16_t tommybeta_combat_basic_fx_frames[3][TOMMYBETA_FX_PIXELS];\n")
        handle.write("extern const uint16_t tommybeta_combat_special_fx_frames[8][TOMMYBETA_FX_PIXELS];\n")
        handle.write("extern const uint16_t tommybeta_prop_frames[4][TOMMYBETA_PROP_PIXELS];\n")
        handle.write("extern const uint16_t tommybeta_critter_frames[4][TOMMYBETA_CRITTER_PIXELS];\n")
        handle.write("extern const uint16_t tommybeta_terrain_overlay_frames[TOMMYBETA_TERRAIN_OVERLAY_COUNT][TOMMYBETA_PROP_PIXELS];\n")
        handle.write("extern const uint16_t tommybeta_hud_panel_bitmap[TOMMYBETA_HUD_PIXELS];\n\n")
        handle.write("#endif\n")

    with SOURCE.open("w", encoding="utf-8") as handle:
        handle.write('#include "tommybeta_mode3_assets.h"\n\n')
        write_frame_set(handle, "tommybeta_quadrant_bitmaps", quadrant_bitmaps, PIXELS)
        handle.write("const char *const tommybeta_quadrant_names[TOMMYBETA_QUADRANT_COUNT] = {\n")
        for name in quadrant_names:
            handle.write(f'    "{name}",\n')
        handle.write("};\n\n")
        write_array(handle, "tommybeta_logo_splash_bitmap", logo_bitmap)
        write_array(handle, "tommybeta_title_menu_bitmap", title_bitmap)
        write_array(handle, "tommybeta_menu_endings_bitmap", menu_bitmap)
        write_array(handle, "tommybeta_state_menu_bitmap", state_menu_bitmap)
        write_array(handle, "tommybeta_pause_window_bitmap", pause_window_bitmap)
        write_array(handle, "tommybeta_codex_bitmap", codex_bitmap)
        write_array(handle, "tommybeta_fall_intro_bitmap", fall_bitmap)
        write_frame_set(handle, "tommybeta_intro_panel_bitmaps", intro_panel_bitmaps, PIXELS)
        write_array(handle, "tommybeta_victory_screen_bitmap", victory_bitmap)
        write_array(handle, "tommybeta_defeat_screen_bitmap", defeat_bitmap)
        write_frame_set(handle, "tommybeta_tommy_idle_frames", sprite_sets["tommy_idle"], SPRITE_PIXELS)
        write_frame_set(handle, "tommybeta_tommy_bite_frames", sprite_sets["tommy_bite"], SPRITE_PIXELS)
        write_frame_set(handle, "tommybeta_tommy_special_frames", sprite_sets["tommy_special"], SPRITE_PIXELS)
        write_frame_set(handle, "tommybeta_tommy_support_frames", sprite_sets["tommy_support"], SPRITE_PIXELS)
        write_frame_set(handle, "tommybeta_mareaou_idle_frames", sprite_sets["mareaou_idle"], SPRITE_PIXELS)
        write_frame_set(handle, "tommybeta_mareaou_attack_frames", sprite_sets["mareaou_attack"], SPRITE_PIXELS)
        write_frame_set(handle, "tommybeta_mareaou_support_frames", sprite_sets["mareaou_support"], SPRITE_PIXELS)
        write_frame_set(handle, "tommybeta_special_icon_frames", sprite_sets["special_icons"], ICON_PIXELS)
        write_frame_set(handle, "tommybeta_combo_icon_frames", sprite_sets["combo_icons"], ICON_PIXELS)
        write_frame_set(handle, "tommybeta_ambience_frames", sprite_sets["ambience"], ICON_PIXELS)
        write_frame_set(handle, "tommybeta_combat_basic_fx_frames", sprite_sets["combat_basic"], FX_PIXELS)
        write_frame_set(handle, "tommybeta_combat_special_fx_frames", sprite_sets["combat_special"], FX_PIXELS)
        write_frame_set(handle, "tommybeta_prop_frames", sprite_sets["props"], PROP_PIXELS)
        write_frame_set(handle, "tommybeta_critter_frames", sprite_sets["critters"], CRITTER_PIXELS)
        write_frame_set(handle, "tommybeta_terrain_overlay_frames", sprite_sets["terrain_overlays"], PROP_PIXELS)
        write_array(handle, "tommybeta_hud_panel_bitmap", hud_panel)

    print(f"Wrote {HEADER}")
    print(f"Wrote {SOURCE}")
    print(f"Quadrants available: {len(quadrant_names)}")
    print(f"Optional logo: {fullscreen['logo_splash'].exists()}, title: {fullscreen['title_menu'].exists()}, endings: {fullscreen['menu_endings'].exists()}, state menu: {fullscreen['state_menu'].exists()}, pause window: {fullscreen['pause_window'].exists()}, codex: {fullscreen['codex_screen'].exists()}, fall intro: {fullscreen['fall_intro'].exists()}, intro panels: {have_intro_panels}")
    print(f"Optional victory: {have_victory}, defeat: {have_defeat}")
    print("Sprite, support, HUD, terrain, repass, ambience, and combat FX frames exported.")


if __name__ == "__main__":
    main()