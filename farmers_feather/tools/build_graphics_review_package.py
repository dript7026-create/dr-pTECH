from __future__ import annotations

import argparse
import json
import re
import struct
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_MAIN = ROOT / "src" / "main.c"
PACKAGE_DIR = ROOT / "review_package"
IMAGE_DIR = PACKAGE_DIR / "images"
PAGE_DIR = PACKAGE_DIR / "pages"
BOOK_PATH = PACKAGE_DIR / "FarmersFeather_graphics_review.ecbmps"
LEDGER_PATH = PACKAGE_DIR / "graphics_asset_ledger.json"
DEFAULT_COMPILER = ROOT.parent / "ecbmps_ccp_studio" / "build" / "ecbmps_compiler.exe"

PAGE_IMAGE_SIZE = (640, 480)
PALETTE = [
    (232, 248, 216),
    (160, 192, 128),
    (88, 120, 96),
    (24, 32, 40),
]
PAPER = (240, 235, 224)
INK = (42, 42, 42)
FRAME = (128, 118, 104)
PANEL = (224, 217, 204)
ACCENT = (92, 116, 84)

SPRITE_LABELS = {
    0: "farmer_idle",
    1: "farmer_rake",
    2: "daemon_kin",
    3: "daemon_of_famine",
}

TILE_DESCRIPTIONS = {
    "TILE_WATER": "Outer void water and hard edge moat.",
    "TILE_SAND": "Beach ring and unstable outer-rim floor.",
    "TILE_GRASS": "Default walkable field tile.",
    "TILE_SOIL": "Tilled or fertile soil patch.",
    "TILE_CROP": "Growing crop state.",
    "TILE_RIPE": "Harvest-ready crop state.",
    "TILE_TREE": "Wood source and solid obstacle.",
    "TILE_ROCK": "Solid hazard and rim clutter.",
    "TILE_SITE": "Unbuilt settlement site.",
    "TILE_HUT": "Built settlement shelter.",
    "TILE_FEATHER": "MoonFeather-ready settlement.",
    "TILE_SHRINE": "Hidden shrine reseed point.",
    "TILE_CRATER": "Impact marker and boss vulnerability tile.",
    "TILE_BAR0": "Empty bar segment for HUD meters.",
    "TILE_BAR1": "Quarter bar segment.",
    "TILE_BAR2": "Mid bar segment.",
    "TILE_BAR3": "Full bar segment.",
    "TILE_HEART_FULL": "Filled heart HUD icon.",
    "TILE_HEART_EMPTY": "Empty heart HUD icon.",
    "TILE_WOOD_ICON": "Wood resource HUD icon.",
    "TILE_BLANK": "Blank HUD spacer tile.",
    "TILE_MOON0": "Moon phase 0 icon.",
    "TILE_MOON1": "Moon phase 1 icon.",
    "TILE_MOON2": "Moon phase 2 icon.",
    "TILE_MOON3": "Moon phase 3 icon.",
    "TILE_MOON4": "Moon phase 4 icon.",
    "TILE_MOON5": "Moon phase 5 icon.",
    "TILE_MOON6": "Moon phase 6 icon.",
    "TILE_MOON7": "Moon phase 7 icon and boss threshold.",
    "TILE_SEED_ICON": "Seed/save-state HUD marker.",
}


def extract_array(source: str, name: str) -> list[int]:
    match = re.search(rf"static const unsigned char {name}\[\] = \{{(.*?)\}};", source, re.S)
    if not match:
        raise RuntimeError(f"Missing array: {name}")
    return [int(token, 0) for token in re.findall(r"0x[0-9A-Fa-f]+|\d+", match.group(1))]


def extract_tile_names(source: str) -> dict[int, str]:
    names: dict[int, str] = {}
    for name, value in re.findall(r"#define\s+(TILE_[A-Z0-9_]+)\s+(\d+)u", source):
        names[int(value)] = name
    return names


def decode_2bpp_tile(tile_bytes: list[int]) -> list[list[int]]:
    pixels: list[list[int]] = []
    for row in range(8):
        low = tile_bytes[row * 2]
        high = tile_bytes[row * 2 + 1]
        row_pixels: list[int] = []
        for bit in range(7, -1, -1):
            color = ((high >> bit) & 1) << 1
            color |= (low >> bit) & 1
            row_pixels.append(color)
        pixels.append(row_pixels)
    return pixels


def chunk_tiles(raw_bytes: list[int]) -> list[list[list[int]]]:
    if len(raw_bytes) % 16 != 0:
        raise RuntimeError("Tile data is not a multiple of 16 bytes")
    return [decode_2bpp_tile(raw_bytes[index:index + 16]) for index in range(0, len(raw_bytes), 16)]


def make_canvas(width: int, height: int, color: tuple[int, int, int]) -> bytearray:
    return bytearray(bytes(color) * (width * height))


def set_pixel(canvas: bytearray, width: int, height: int, x: int, y: int, color: tuple[int, int, int]) -> None:
    if x < 0 or y < 0 or x >= width or y >= height:
        return
    offset = (y * width + x) * 3
    canvas[offset:offset + 3] = bytes(color)


def fill_rect(canvas: bytearray, width: int, height: int, left: int, top: int, rect_w: int, rect_h: int, color: tuple[int, int, int]) -> None:
    for y in range(top, top + rect_h):
        for x in range(left, left + rect_w):
            set_pixel(canvas, width, height, x, y, color)


def draw_rect(canvas: bytearray, width: int, height: int, left: int, top: int, rect_w: int, rect_h: int, color: tuple[int, int, int]) -> None:
    for x in range(left, left + rect_w):
        set_pixel(canvas, width, height, x, top, color)
        set_pixel(canvas, width, height, x, top + rect_h - 1, color)
    for y in range(top, top + rect_h):
        set_pixel(canvas, width, height, left, y, color)
        set_pixel(canvas, width, height, left + rect_w - 1, y, color)


DIGITS = {
    "0": ["111", "101", "101", "101", "111"],
    "1": ["010", "110", "010", "010", "111"],
    "2": ["111", "001", "111", "100", "111"],
    "3": ["111", "001", "111", "001", "111"],
    "4": ["101", "101", "111", "001", "001"],
    "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"],
    "7": ["111", "001", "010", "010", "010"],
    "8": ["111", "101", "111", "101", "111"],
    "9": ["111", "101", "111", "001", "111"],
}


def draw_number(canvas: bytearray, width: int, height: int, x: int, y: int, value: int, color: tuple[int, int, int], scale: int = 2) -> None:
    cursor_x = x
    for char in str(value):
        pattern = DIGITS[char]
        for row, bits in enumerate(pattern):
            for col, bit in enumerate(bits):
                if bit != "1":
                    continue
                fill_rect(canvas, width, height, cursor_x + col * scale, y + row * scale, scale, scale, color)
        cursor_x += (len(pattern[0]) + 1) * scale


def blit_tile(canvas: bytearray, width: int, height: int, tile_pixels: list[list[int]], x: int, y: int, scale: int) -> None:
    for row_index, row in enumerate(tile_pixels):
        for col_index, color_index in enumerate(row):
            fill_rect(
                canvas,
                width,
                height,
                x + col_index * scale,
                y + row_index * scale,
                scale,
                scale,
                PALETTE[color_index],
            )


def write_bmp(path: Path, width: int, height: int, canvas: bytearray) -> None:
    row_stride = width * 3
    padding = (4 - (row_stride % 4)) % 4
    image_size = (row_stride + padding) * height
    file_size = 14 + 40 + image_size
    header = bytearray()
    header.extend(b"BM")
    header.extend(struct.pack("<I", file_size))
    header.extend(b"\x00\x00\x00\x00")
    header.extend(struct.pack("<I", 54))
    header.extend(struct.pack("<IiiHHIIiiII", 40, width, height, 1, 24, 0, image_size, 2835, 2835, 0, 0))

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(header)
        for row in range(height - 1, -1, -1):
            start = row * row_stride
            rgb_row = canvas[start:start + row_stride]
            bgr = bytearray()
            for offset in range(0, len(rgb_row), 3):
                red = rgb_row[offset]
                green = rgb_row[offset + 1]
                blue = rgb_row[offset + 2]
                bgr.extend((blue, green, red))
            bgr.extend(b"\x00" * padding)
            handle.write(bgr)


def render_tile_page(tiles: list[list[list[int]]], indices: list[int], columns: int, output_path: Path) -> None:
    width, height = PAGE_IMAGE_SIZE
    canvas = make_canvas(width, height, PAPER)
    fill_rect(canvas, width, height, 18, 18, width - 36, height - 36, PANEL)
    draw_rect(canvas, width, height, 18, 18, width - 36, height - 36, FRAME)
    cell_w = 110
    cell_h = 96
    scale = 6
    origin_x = 42
    origin_y = 44
    for position, tile_index in enumerate(indices):
        row = position // columns
        column = position % columns
        left = origin_x + column * cell_w
        top = origin_y + row * cell_h
        fill_rect(canvas, width, height, left, top, 88, 76, PAPER)
        draw_rect(canvas, width, height, left, top, 88, 76, FRAME)
        blit_tile(canvas, width, height, tiles[tile_index], left + 20, top + 10, scale)
        draw_number(canvas, width, height, left + 30, top + 64, tile_index, INK, scale=3)
    write_bmp(output_path, width, height, canvas)


def make_screen(fill_tile: int) -> list[list[int]]:
    return [[fill_tile for _ in range(20)] for _ in range(18)]


def build_mock_screens() -> list[list[list[int]]]:
    meadow = make_screen(2)
    for x in range(1, 19, 5):
        meadow[2][x] = 6
        meadow[13][(x + 2) % 20] = 6
    meadow[8][9] = 8
    meadow[8][10] = 3
    meadow[9][9] = 3
    meadow[9][10] = 4

    settlement = make_screen(2)
    for y in range(5, 13):
        settlement[y][4] = 3
        settlement[y][15] = 3
    settlement[8][9] = 9
    settlement[8][10] = 10
    settlement[10][8] = 4
    settlement[10][9] = 5
    settlement[10][10] = 4
    settlement[11][9] = 5
    settlement[4][3] = 6
    settlement[12][16] = 6

    shrine = make_screen(2)
    for x in range(0, 20):
        shrine[0][x] = 3
        shrine[17][x] = 3
    for y in range(0, 18):
        shrine[y][0] = 3
        shrine[y][19] = 3
    shrine[8][9] = 11
    shrine[8][10] = 11
    shrine[9][9] = 11
    shrine[9][10] = 11
    shrine[6][6] = 6
    shrine[11][13] = 6

    rim = make_screen(1)
    for y in range(0, 18):
        for x in range(0, 20):
            if x in {0, 19} or y in {0, 17}:
                rim[y][x] = 0
            elif (x + y) % 5 == 0:
                rim[y][x] = 7
            elif (x * 3 + y * 2) % 7 == 0:
                rim[y][x] = 12
    rim[8][9] = 12
    rim[8][10] = 12
    rim[9][9] = 7
    rim[9][10] = 7

    return [meadow, settlement, shrine, rim]


def blit_mock_screen(canvas: bytearray, width: int, height: int, tiles: list[list[list[int]]], screen: list[list[int]], left: int, top: int) -> None:
    draw_rect(canvas, width, height, left - 4, top - 4, 168, 152, FRAME)
    for tile_y, row in enumerate(screen):
        for tile_x, tile_index in enumerate(row):
            blit_tile(canvas, width, height, tiles[tile_index], left + tile_x * 8, top + tile_y * 8, 1)


def render_composition_page(tiles: list[list[list[int]]], output_path: Path) -> None:
    width, height = PAGE_IMAGE_SIZE
    canvas = make_canvas(width, height, PAPER)
    fill_rect(canvas, width, height, 18, 18, width - 36, height - 36, PANEL)
    draw_rect(canvas, width, height, 18, 18, width - 36, height - 36, FRAME)
    positions = [(40, 40), (240, 40), (40, 224), (240, 224)]
    for panel_number, (screen, position) in enumerate(zip(build_mock_screens(), positions), start=1):
        blit_mock_screen(canvas, width, height, tiles, screen, position[0], position[1])
        draw_number(canvas, width, height, position[0] + 136, position[1] + 124, panel_number, ACCENT, scale=3)
    write_bmp(output_path, width, height, canvas)


def build_ledger(tile_names: dict[int, str]) -> dict[str, object]:
    bg_entries = []
    for index in range(30):
        name = tile_names[index]
        bg_entries.append(
            {
                "index": index,
                "name": name,
                "description": TILE_DESCRIPTIONS.get(name, "Embedded background tile."),
            }
        )
    sprite_entries = []
    for index in range(4):
        sprite_entries.append(
            {
                "index": index,
                "name": SPRITE_LABELS[index],
                "description": "Embedded sprite tile used by the player or hostile entities.",
            }
        )
    return {
        "source": str(SRC_MAIN.relative_to(ROOT)),
        "background_tiles": bg_entries,
        "sprite_tiles": sprite_entries,
        "book": str(BOOK_PATH.relative_to(ROOT)),
    }


def write_pages(tile_names: dict[int, str]) -> list[str]:
    page1 = """Farmer's Feather Graphics Review\n\nThis ECBMPS book is built directly from the live embedded tile data in src/main.c.\n\nContents:\n- Background terrain and interaction tiles\n- HUD bars, icons, and moon phase tiles\n- Player, DaemonKin, and Daemon of Famine sprites\n- Four mock gameplay compositions that show how the current art is used in context\n\nCounts:\n- 30 background tiles\n- 4 sprite tiles\n- 1 procedural composition board\n"""
    page2_lines = [
        "World Tile Atlas",
        "",
        "Tiles 0-12 cover the navigable world, structures, and impact states.",
        "",
    ]
    for index in range(13):
        name = tile_names[index]
        page2_lines.append(f"{index:02d} {name}: {TILE_DESCRIPTIONS[name]}")

    page3_lines = [
        "HUD and System Tile Atlas",
        "",
        "Tiles 13-29 support status bars, hearts, resources, moon phases, and save-state hints.",
        "",
    ]
    for index in range(13, 30):
        name = tile_names[index]
        page3_lines.append(f"{index:02d} {name}: {TILE_DESCRIPTIONS[name]}")

    page4_lines = [
        "Sprite Tile Atlas",
        "",
        "The current ROM embeds four sprite tiles:",
        "",
    ]
    for index in range(4):
        page4_lines.append(f"{index:02d} {SPRITE_LABELS[index]}")

    page5 = """Composition Board\n\nPanel 1: meadow traversal with trees, soil, and an unbuilt settlement site.\nPanel 2: built settlement loop with MoonFeather-ready hut and crop states.\nPanel 3: shrine chamber composition used for the reseed action.\nPanel 4: hostile rim composition showing sand, water, rock, and crater pressure.\n\nThese are review mockups assembled from the exact embedded tiles, not new painted concept art.\n"""

    page6 = """Extraction Notes\n\n- Source file: src/main.c\n- Arrays extracted: bg_tiles, sprite_tiles\n- Rendering path: tools/build_graphics_review_package.py\n- Output ledger: review_package/graphics_asset_ledger.json\n\nThis package is meant to freeze the current Game Boy visual language before a larger art pass.\n"""

    page_texts = {
        "page001.txt": page1,
        "page002.txt": "\n".join(page2_lines) + "\n",
        "page003.txt": "\n".join(page3_lines) + "\n",
        "page004.txt": "\n".join(page4_lines) + "\n",
        "page005.txt": page5,
        "page006.txt": page6,
    }
    PAGE_DIR.mkdir(parents=True, exist_ok=True)
    for name, content in page_texts.items():
        (PAGE_DIR / name).write_text(content, encoding="utf-8")
    return [name for name in sorted(page_texts.keys())]


def render_review_assets() -> tuple[list[str], list[str]]:
    source = SRC_MAIN.read_text(encoding="utf-8")
    tile_names = extract_tile_names(source)
    bg_tiles = chunk_tiles(extract_array(source, "bg_tiles"))
    sprite_tiles = chunk_tiles(extract_array(source, "sprite_tiles"))

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    terrain_path = IMAGE_DIR / "page002_world_tiles.bmp"
    hud_path = IMAGE_DIR / "page003_hud_tiles.bmp"
    sprite_path = IMAGE_DIR / "page004_sprite_tiles.bmp"
    composition_path = IMAGE_DIR / "page005_composition_board.bmp"

    render_tile_page(bg_tiles, list(range(0, 13)), 4, terrain_path)
    render_tile_page(bg_tiles, list(range(13, 30)), 5, hud_path)
    render_tile_page(sprite_tiles, list(range(0, 4)), 4, sprite_path)
    render_composition_page(bg_tiles, composition_path)

    ledger = build_ledger(tile_names)
    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
    LEDGER_PATH.write_text(json.dumps(ledger, indent=2), encoding="utf-8")

    page_files = write_pages(tile_names)
    combined_pages = [
        str(PAGE_DIR / "page001.txt"),
        f"{PAGE_DIR / 'page002.txt'}+{terrain_path}",
        f"{PAGE_DIR / 'page003.txt'}+{hud_path}",
        f"{PAGE_DIR / 'page004.txt'}+{sprite_path}",
        f"{PAGE_DIR / 'page005.txt'}+{composition_path}",
        str(PAGE_DIR / "page006.txt"),
    ]
    return page_files, combined_pages


def compile_book(page_args: list[str], compiler_path: Path) -> None:
    if not compiler_path.exists():
        raise FileNotFoundError(f"Missing ECBMPS compiler: {compiler_path}")
    command = [str(compiler_path), "-o", str(BOOK_PATH), "-t", "Farmer's Feather Graphics Review", "-a", "GitHub Copilot"] + page_args
    subprocess.run(command, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Farmer's Feather graphics review package.")
    parser.add_argument("--skip-compile", action="store_true", help="Render the review package without compiling the ECBMPS book.")
    parser.add_argument("--compiler", type=Path, default=DEFAULT_COMPILER, help="Override the path to ecbmps_compiler.exe.")
    args = parser.parse_args()

    _, page_args = render_review_assets()
    if not args.skip_compile:
        compile_book(page_args, args.compiler)
    print(json.dumps({
        "package_dir": str(PACKAGE_DIR),
        "book": str(BOOK_PATH),
        "ledger": str(LEDGER_PATH),
        "compiled": not args.skip_compile,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())