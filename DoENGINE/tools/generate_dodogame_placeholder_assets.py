from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / 'generated' / 'dodogame_gui'
FONT_DIR = OUTPUT_DIR / 'fonts'
THEME_PATH = OUTPUT_DIR / 'theme.json'

ASSET_LAYOUT = {
    'shell_frame': ('shell_frame.png', (1280, 820), '#223128', '#d0aa73', 'DODOGame Shell', 'Standalone launcher chrome'),
    'runtime_panel': ('shell_panel_runtime.png', (620, 360), '#283229', '#8cb091', 'Hybrid Runtime', 'ORBEngine + DoENGINE render state'),
    'report_panel': ('shell_panel_report.png', (620, 360), '#2d2721', '#d0aa73', 'Tutorial Report', 'Completion summaries and traces'),
    'background': ('backgrounds/dodo_environment_backdrop.png', (1280, 720), '#1b2420', '#5d8d67', 'Dodo Observatory', 'Prehistoric launcher backdrop'),
    'buttons': ('buttons/dodo_button_collection.png', (1024, 512), '#2d3327', '#d0aa73', 'Button Atlas', 'Default, hover, pressed, disabled'),
    'status_widgets': ('widgets/dodo_status_widgets.png', (1024, 512), '#1d2520', '#8cb091', 'Status Widgets', 'Runtime, build, tutorial, controller'),
    'toolbar_icons': ('icons/dodo_toolbar_icons.png', (1024, 512), '#232820', '#d0aa73', 'Toolbar Icons', 'Render, assets, PlayNOW, simulation'),
    'controller_diagram': ('controller/dodo_controller_diagrams.png', (1024, 640), '#20261f', '#d0aa73', 'Controller Diagram', 'Full XInput surface reference'),
    'runtime_cards': ('cards/dodo_runtime_cards.png', (1024, 640), '#21281f', '#8cb091', 'Runtime Cards', 'Bango, generic template, ORB, Do, PlayNOW'),
    'splash': ('splash/dodo_launch_splash.png', (1280, 720), '#1a201b', '#d88b3c', 'Launch Splash', 'Engine portal and expedition tone'),
    'notifications': ('notifications/dodo_notification_pack.png', (1024, 512), '#26221c', '#d0aa73', 'Notifications', 'Toast, modal, tooltip shells'),
    'report_panels': ('reports/dodo_report_panels.png', (1024, 512), '#2b261f', '#d0aa73', 'Report Panels', 'Archive card document surfaces'),
    'input_hints': ('hints/dodo_input_hint_pack.png', (1024, 512), '#1f231d', '#8cb091', 'Input Hints', 'Controller and keyboard prompts'),
    'cursor_pack': ('cursor/dodo_cursor_pack.png', (768, 384), '#191d18', '#d88b3c', 'Cursor Pack', 'Pointer, hover, precision states'),
    'scene_hierarchy': ('scene_hierarchy/dodo_scene_hierarchy_pack.png', (1024, 512), '#20241f', '#8cb091', 'Scene Hierarchy', 'Spaces, actors, sockets, pockets'),
    'material_cards': ('materials/dodo_material_cards.png', (1024, 512), '#25211c', '#d0aa73', 'Material Cards', 'Metadata, layers, material swatches'),
    'timeline_strips': ('timeline/dodo_timeline_strips.png', (1024, 512), '#1e211d', '#8cb091', 'Timeline Strips', 'Replay, animation, tutorial sequencing'),
    'world_map_widgets': ('world_map/dodo_world_map_widgets.png', (1024, 512), '#20251f', '#d0aa73', 'World Map Widgets', 'Nested spaces and route traces'),
}

GLYPHS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789:-/ '
GRID_COLUMNS = 8
CELL_WIDTH = 32
CELL_HEIGHT = 40

STONE_COLORS = {
    'bg': '#14181a',
    'fg': '#e8dcc2',
    'accent': '#a26a2f',
}

BONE_COLORS = {
    'bg': '#1d231e',
    'fg': '#f2ead9',
    'accent': '#5d8d67',
}


def load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        'C:/Windows/Fonts/consola.ttf',
        'C:/Windows/Fonts/lucon.ttf',
        'C:/Windows/Fonts/segoeuib.ttf',
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def make_panel(path: Path, size: tuple[int, int], fill: str, outline: str, title: str) -> None:
    image = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((6, 6, size[0] - 6, size[1] - 6), radius=28, fill=fill, outline=outline, width=4)
    draw.rounded_rectangle((18, 18, size[0] - 18, 88), radius=18, fill=outline)
    draw.text((30, 32), title, fill='#f7f1e6', font=load_font(26))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def make_labeled_asset(path: Path, size: tuple[int, int], fill: str, outline: str, title: str, subtitle: str) -> None:
    image = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 8, size[0] - 8, size[1] - 8), radius=34, fill=fill, outline=outline, width=5)
    draw.rounded_rectangle((26, 26, size[0] - 26, 112), radius=20, fill=outline)
    draw.text((42, 42), title, fill='#f7f1e6', font=load_font(30))
    draw.rounded_rectangle((42, 154, size[0] - 42, size[1] - 42), radius=24, outline='#f3ead6', width=3)
    draw.line((76, size[1] - 92, size[0] - 76, size[1] - 92), fill=outline, width=4)
    draw.text((42, size[1] - 78), subtitle, fill='#efe4c9', font=load_font(20))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def make_badge(path: Path) -> None:
    image = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((36, 90, 476, 452), fill='#7d8b5f', outline='#efd09a', width=10)
    draw.ellipse((136, 136, 376, 376), fill='#1e2320', outline='#efd09a', width=8)
    draw.polygon((224, 74, 284, 74, 332, 182, 176, 182), fill='#d88b3c')
    draw.text((146, 212), 'DODO', fill='#f6edd9', font=load_font(56))
    draw.text((168, 284), 'GAME', fill='#f6edd9', font=load_font(46))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def make_font_atlas(path: Path, metadata_path: Path, palette: dict[str, str]) -> None:
    rows = (len(GLYPHS) + GRID_COLUMNS - 1) // GRID_COLUMNS
    width = GRID_COLUMNS * CELL_WIDTH
    height = rows * CELL_HEIGHT
    image = Image.new('RGBA', (width, height), palette['bg'])
    draw = ImageDraw.Draw(image)
    font = load_font(24)
    metadata = {
        'glyphs': {},
        'cell_width': CELL_WIDTH,
        'cell_height': CELL_HEIGHT,
        'columns': GRID_COLUMNS,
        'atlas': str(path),
    }
    for index, glyph in enumerate(GLYPHS):
        col = index % GRID_COLUMNS
        row = index // GRID_COLUMNS
        x = col * CELL_WIDTH
        y = row * CELL_HEIGHT
        draw.rounded_rectangle((x + 1, y + 1, x + CELL_WIDTH - 2, y + CELL_HEIGHT - 2), radius=8, outline=palette['accent'], width=1)
        bbox = draw.textbbox((0, 0), glyph, font=font)
        glyph_w = bbox[2] - bbox[0]
        glyph_h = bbox[3] - bbox[1]
        draw.text((x + (CELL_WIDTH - glyph_w) / 2, y + (CELL_HEIGHT - glyph_h) / 2 - 2), glyph, fill=palette['fg'], font=font)
        metadata['glyphs'][glyph] = {'x': x, 'y': y, 'w': CELL_WIDTH, 'h': CELL_HEIGHT}
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    metadata_path.write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for asset_name, spec in ASSET_LAYOUT.items():
        relative_path, size, fill, outline, title, subtitle = spec
        if asset_name in {'shell_frame', 'runtime_panel', 'report_panel'}:
            make_panel(OUTPUT_DIR / relative_path, size, fill, outline, title)
        else:
            make_labeled_asset(OUTPUT_DIR / relative_path, size, fill, outline, title, subtitle)

    make_badge(OUTPUT_DIR / 'dodogame_badge.png')
    make_font_atlas(FONT_DIR / 'dodo_font_stone.png', FONT_DIR / 'dodo_font_stone.json', STONE_COLORS)
    make_font_atlas(FONT_DIR / 'dodo_font_bone.png', FONT_DIR / 'dodo_font_bone.json', BONE_COLORS)
    theme = {
        'name': 'dodogame-placeholder-theme',
        'shell_frame': str(OUTPUT_DIR / 'shell_frame.png'),
        'runtime_panel': str(OUTPUT_DIR / 'shell_panel_runtime.png'),
        'report_panel': str(OUTPUT_DIR / 'shell_panel_report.png'),
        'badge': str(OUTPUT_DIR / 'dodogame_badge.png'),
        'background': str(OUTPUT_DIR / 'backgrounds' / 'dodo_environment_backdrop.png'),
        'buttons': str(OUTPUT_DIR / 'buttons' / 'dodo_button_collection.png'),
        'status_widgets': str(OUTPUT_DIR / 'widgets' / 'dodo_status_widgets.png'),
        'toolbar_icons': str(OUTPUT_DIR / 'icons' / 'dodo_toolbar_icons.png'),
        'controller_diagram': str(OUTPUT_DIR / 'controller' / 'dodo_controller_diagrams.png'),
        'runtime_cards': str(OUTPUT_DIR / 'cards' / 'dodo_runtime_cards.png'),
        'splash': str(OUTPUT_DIR / 'splash' / 'dodo_launch_splash.png'),
        'notifications': str(OUTPUT_DIR / 'notifications' / 'dodo_notification_pack.png'),
        'report_panels': str(OUTPUT_DIR / 'reports' / 'dodo_report_panels.png'),
        'input_hints': str(OUTPUT_DIR / 'hints' / 'dodo_input_hint_pack.png'),
        'cursor_pack': str(OUTPUT_DIR / 'cursor' / 'dodo_cursor_pack.png'),
        'scene_hierarchy': str(OUTPUT_DIR / 'scene_hierarchy' / 'dodo_scene_hierarchy_pack.png'),
        'material_cards': str(OUTPUT_DIR / 'materials' / 'dodo_material_cards.png'),
        'timeline_strips': str(OUTPUT_DIR / 'timeline' / 'dodo_timeline_strips.png'),
        'world_map_widgets': str(OUTPUT_DIR / 'world_map' / 'dodo_world_map_widgets.png'),
        'fonts': {
            'stone': str(FONT_DIR / 'dodo_font_stone.json'),
            'bone': str(FONT_DIR / 'dodo_font_bone.json'),
        },
    }
    THEME_PATH.write_text(json.dumps(theme, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'theme': str(THEME_PATH), 'output_dir': str(OUTPUT_DIR)}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
