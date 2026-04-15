from __future__ import annotations

import json
import importlib
import math
import struct
import sys
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = ROOT.parent
OUTPUT_DIR = ROOT / 'generated' / 'dodogame_gui'
FONT_DIR = OUTPUT_DIR / 'fonts'
THEME_PATH = OUTPUT_DIR / 'theme.json'

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / 'apps') not in sys.path:
    sys.path.insert(0, str(ROOT / 'apps'))

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


def load_json_if_exists(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding='utf-8'))


def resolve_title_asset_root() -> Path:
    from bango_integration_paths import resolve_bango_asset_root

    asset_root = resolve_bango_asset_root()
    if (asset_root / 'generated').exists():
        return asset_root
    return WORKSPACE_ROOT / 'bango-patoot_3DS'


def resolve_title_runtime_payload(asset_root: Path) -> dict:
    from bango_integration_paths import resolve_playnow_runtime_path

    candidate_paths = [
        resolve_playnow_runtime_path(asset_root),
        WORKSPACE_ROOT / 'bango-patoot_3DS' / 'generated' / 'playnow' / 'playnow_runtime_manifest.json',
    ]
    for candidate in candidate_paths:
        payload = load_json_if_exists(candidate)
        if isinstance(payload, dict):
            return payload
    return {}


def resolve_title_player_glb(runtime_payload: dict) -> Path | None:
    preferred_passes = ('tutorial_final_preview', 'dodogame', 'tutorial32')
    passes = runtime_payload.get('passes', []) if isinstance(runtime_payload.get('passes'), list) else []
    for label in preferred_passes:
        for entry in passes:
            if not isinstance(entry, dict) or entry.get('pass_label') != label:
                continue
            value = entry.get('player_glb')
            if value and Path(str(value)).exists():
                return Path(str(value))
    player = runtime_payload.get('player') if isinstance(runtime_payload.get('player'), dict) else {}
    value = player.get('glb')
    if value and Path(str(value)).exists():
        return Path(str(value))
    return None


def collect_title_reference_images(asset_root: Path) -> list[Path]:
    candidates = [
        asset_root / 'generated' / 'recraft_polished',
        WORKSPACE_ROOT / 'bango-patoot_3DS' / 'generated' / 'recraft_polished',
    ]
    polished_root = next((path for path in candidates if path.exists()), None)
    if polished_root is None:
        return []
    ordered_names = [
        'bango_turnaround_sheet_01_readAIpolish.png',
        'bango_keypose_sheet_03_readAIpolish.png',
        'patoot_turnaround_sheet_01_readAIpolish.png',
        'patoot_keypose_sheet_03_readAIpolish.png',
    ]
    return [polished_root / name for name in ordered_names if (polished_root / name).exists()]


def write_title_hero_scene(scene_path: Path, player_glb: Path, reference_images: list[Path]) -> None:
    scene_entries: list[dict] = [
        {
            'id': 'title_tutorial_stage',
            'kind': 'mesh',
            'loader': 'builtin',
            'mesh': 'tutorial_stage',
            'position': [0.0, -0.05, 10.6],
            'rotation': [0.0, 0.12, 0.0],
            'scale': 1.42,
            'label': 'Tutorial Shrine Yard',
            'scripts': [
                {'type': 'pulse', 'amplitude': 0.02, 'speed': 0.36},
                {'type': 'channel_follow', 'channel': 'relay_resonance', 'y_amplitude': 0.05, 'rotation_y': 0.03, 'scale_amplitude': 0.01},
            ],
        },
        {
            'id': 'title_gate_left',
            'kind': 'mesh',
            'loader': 'builtin',
            'mesh': 'arch',
            'position': [-4.1, -0.82, 12.2],
            'rotation': [0.16, 0.28, 0.0],
            'scale': 1.18,
            'label': 'Tutorial Gate Left',
            'scripts': [{'type': 'bob', 'amplitude': 0.05, 'speed': 0.52}, {'type': 'sway', 'rotation_y': 0.05, 'speed': 0.4}],
        },
        {
            'id': 'title_gate_right',
            'kind': 'mesh',
            'loader': 'builtin',
            'mesh': 'arch',
            'position': [4.2, -0.8, 12.4],
            'rotation': [0.14, -0.32, 0.0],
            'scale': 1.24,
            'label': 'Tutorial Gate Right',
            'scripts': [{'type': 'bob', 'amplitude': 0.06, 'speed': 0.56}, {'type': 'sway', 'rotation_y': 0.06, 'speed': 0.44}],
        },
        {
            'id': 'title_signal_spire',
            'kind': 'mesh',
            'loader': 'builtin',
            'mesh': 'spire',
            'position': [-0.24, 0.12, 14.4],
            'rotation': [0.0, 0.48, 0.0],
            'scale': 1.12,
            'label': 'Signal Spire',
            'scripts': [
                {'type': 'spin', 'speed': 0.03},
                {'type': 'channel_follow', 'channel': 'pressure_wave', 'y_amplitude': 0.14, 'scale_amplitude': 0.04, 'rotation_y': 0.08},
            ],
        },
        {
            'id': 'title_bango_glb',
            'kind': 'mesh',
            'loader': 'glb',
            'mesh': player_glb.as_posix(),
            'position': [0.6, -1.46, 8.2],
            'rotation': [0.0, 0.84, 0.0],
            'scale': 2.46,
            'label': 'Bango Tutorial Idle',
            'metadata': {'design_basis': 'concept-artbook-with-childfriendly-wide-eyed-deviation'},
            'scripts': [
                {'type': 'bob', 'amplitude': 0.035, 'speed': 0.48},
                {'type': 'sway', 'rotation_x': 0.04, 'rotation_y': 0.1, 'rotation_z': 0.025, 'speed': 0.42},
                {'type': 'channel_follow', 'channel': 'bango_trigger', 'rotation_y': 0.08, 'rotation_z': 0.04, 'y_amplitude': 0.04, 'scale_amplitude': 0.012},
                {'type': 'accent_burst', 'channel': 'bango_trigger', 'speed': 0.16, 'curve': 11.0, 'rotation_y': 0.28, 'rotation_z': 0.08, 'y_amplitude': 0.05, 'scale_amplitude': 0.018},
            ],
        },
        {
            'id': 'title_patoot_companion',
            'kind': 'mesh',
            'loader': 'builtin',
            'mesh': 'patoot',
            'position': [2.1, -1.04, 7.8],
            'rotation': [0.08, -0.74, 0.0],
            'scale': 0.86,
            'label': 'Patoot Idle Amusement',
            'metadata': {'design_basis': 'concept-artbook-wide-eyed-companion'},
            'scripts': [
                {'type': 'orbit', 'radius': 0.18, 'speed': 0.42, 'anchor': [2.1, -1.04, 7.8]},
                {'type': 'bob', 'amplitude': 0.08, 'speed': 1.24},
                {'type': 'sway', 'rotation_x': 0.06, 'rotation_y': 0.18, 'rotation_z': 0.08, 'speed': 1.18},
                {'type': 'channel_follow', 'channel': 'patoot_trigger', 'rotation_y': 0.16, 'rotation_z': 0.12, 'x_amplitude': -0.06, 'y_amplitude': 0.05, 'scale_amplitude': 0.02},
                {'type': 'accent_burst', 'channel': 'patoot_trigger', 'speed': 0.34, 'curve': 12.0, 'rotation_y': 0.5, 'rotation_z': 0.28, 'x_amplitude': -0.1, 'y_amplitude': 0.08, 'scale_amplitude': 0.04},
            ],
        },
        {
            'id': 'title_pouch_fluid_a',
            'kind': 'mesh',
            'loader': 'builtin',
            'mesh': 'pouch_fluid',
            'position': [1.86, -0.98, 7.54],
            'rotation': [0.04, -0.12, 0.08],
            'scale': 0.44,
            'label': 'Patoot Pouch Fluid',
            'metadata': {'design_basis': 'stylized-fluid-proxy'},
            'scripts': [
                {'type': 'bob', 'amplitude': 0.05, 'speed': 1.32},
                {'type': 'drift', 'amplitude_x': 0.03, 'amplitude_y': 0.015, 'amplitude_z': 0.02, 'speed': 1.08},
                {'type': 'channel_follow', 'channel': 'patoot_trigger', 'x_amplitude': -0.05, 'y_amplitude': 0.06, 'rotation_y': 0.14, 'scale_amplitude': 0.08},
                {'type': 'channel_follow', 'channel': 'ooze_surge', 'y_amplitude': 0.05, 'rotation_z': 0.08, 'scale_amplitude': 0.05},
            ],
        },
        {
            'id': 'title_pouch_fluid_b',
            'kind': 'mesh',
            'loader': 'builtin',
            'mesh': 'pouch_fluid',
            'position': [2.28, -0.92, 7.66],
            'rotation': [0.0, 0.22, -0.04],
            'scale': 0.34,
            'label': 'Patoot Pouch Fluid Echo',
            'metadata': {'design_basis': 'stylized-fluid-proxy'},
            'scripts': [
                {'type': 'bob', 'amplitude': 0.04, 'speed': 1.58},
                {'type': 'drift', 'amplitude_x': 0.02, 'amplitude_y': 0.02, 'amplitude_z': 0.03, 'speed': 1.22},
                {'type': 'channel_follow', 'channel': 'patoot_trigger', 'x_amplitude': -0.04, 'y_amplitude': 0.05, 'rotation_y': 0.12, 'scale_amplitude': 0.06},
                {'type': 'channel_follow', 'channel': 'ooze_surge', 'y_amplitude': 0.04, 'rotation_z': 0.06, 'scale_amplitude': 0.04},
            ],
        },
        {
            'id': 'title_drone_left',
            'kind': 'mesh',
            'loader': 'builtin',
            'mesh': 'drone',
            'position': [-2.84, 1.18, 9.94],
            'rotation': [0.08, 0.28, 0.0],
            'scale': 0.46,
            'label': 'Hover Drone Left',
            'metadata': {'design_basis': 'tutorial-yard-hover-drone'},
            'scripts': [
                {'type': 'orbit', 'radius': 0.42, 'speed': 0.24, 'anchor': [-2.84, 1.18, 9.94]},
                {'type': 'bob', 'amplitude': 0.11, 'speed': 0.98},
                {'type': 'sway', 'rotation_y': 0.18, 'rotation_z': 0.08, 'speed': 1.16},
                {'type': 'channel_follow', 'channel': 'relay_resonance', 'y_amplitude': 0.08, 'rotation_y': 0.18, 'scale_amplitude': 0.08},
                {'type': 'accent_burst', 'channel': 'fracture_pulse', 'speed': 0.28, 'rotation_y': 0.34, 'y_amplitude': 0.08, 'scale_amplitude': 0.06},
            ],
        },
        {
            'id': 'title_drone_right',
            'kind': 'mesh',
            'loader': 'builtin',
            'mesh': 'drone',
            'position': [3.08, 1.34, 10.28],
            'rotation': [0.02, -0.42, 0.04],
            'scale': 0.42,
            'label': 'Hover Drone Right',
            'metadata': {'design_basis': 'tutorial-yard-hover-drone'},
            'scripts': [
                {'type': 'orbit', 'radius': 0.36, 'speed': -0.22, 'anchor': [3.08, 1.34, 10.28]},
                {'type': 'bob', 'amplitude': 0.09, 'speed': 1.06},
                {'type': 'sway', 'rotation_y': 0.16, 'rotation_z': 0.1, 'speed': 1.24},
                {'type': 'channel_follow', 'channel': 'relay_resonance', 'y_amplitude': 0.06, 'rotation_y': 0.16, 'scale_amplitude': 0.06},
                {'type': 'accent_burst', 'channel': 'fracture_pulse', 'speed': 0.24, 'rotation_y': -0.28, 'y_amplitude': 0.06, 'scale_amplitude': 0.05},
            ],
        },
        {
            'id': 'title_drone_overwatch',
            'kind': 'mesh',
            'loader': 'builtin',
            'mesh': 'drone',
            'position': [0.34, 1.88, 11.54],
            'rotation': [0.0, 0.6, 0.0],
            'scale': 0.36,
            'label': 'Hover Drone Overwatch',
            'metadata': {'design_basis': 'tutorial-yard-hover-drone'},
            'scripts': [
                {'type': 'orbit', 'radius': 0.28, 'speed': 0.18, 'anchor': [0.34, 1.88, 11.54]},
                {'type': 'bob', 'amplitude': 0.07, 'speed': 0.84},
                {'type': 'channel_follow', 'channel': 'pressure_wave', 'y_amplitude': 0.12, 'rotation_y': 0.18, 'scale_amplitude': 0.05},
                {'type': 'accent_burst', 'channel': 'stall_decay', 'speed': 0.12, 'rotation_y': 0.24, 'y_amplitude': 0.04, 'scale_amplitude': 0.03},
            ],
        },
        {
            'id': 'title_pedestal',
            'kind': 'mesh',
            'loader': 'builtin',
            'mesh': 'pedestal',
            'position': [0.74, -1.42, 8.32],
            'rotation': [0.0, 0.18, 0.0],
            'scale': 1.04,
            'label': 'Shrine Marker',
            'scripts': [{'type': 'pulse', 'amplitude': 0.03, 'speed': 1.4}],
        },
    ]
    billboard_positions = [(-5.6, -0.28, 11.9), (5.66, -0.26, 12.1)]
    for index, image_path in enumerate(reference_images[:2]):
        x_pos, y_pos, z_pos = billboard_positions[index]
        scene_entries.append(
            {
                'id': f'title_ref_{index}',
                'kind': 'billboard',
                'position': [x_pos, y_pos, z_pos],
                'width': 170,
                'height': 248,
                'image_path': image_path.as_posix(),
                'label': '',
                'tint': [222, 198, 154],
                'scripts': [{'type': 'sway', 'rotation_y': 0.08, 'speed': 0.22 + index * 0.04}],
            }
        )
    scene_payload = {
        'showcase_name': 'Bango Tutorial Title Tableau',
        'scene_version': '2026-03-27.title-tutorial-tableau-rich',
        'camera': {'orbit': 0.58, 'elevation': 0.18, 'focus_z': 9.2},
        'concept_translation': {
            'art_direction': ['horned-prehistoric', 'soot-blackened-civic-infrastructure', 'brass-devotional-machinery', 'hive-geometry', 'childfriendly-wide-eyed', 'fur-feather-fluid-proxy'],
            'erp_sequencer': {
                'thresholds': ['hushfall_hum', 'ritual_dread', 'companion_alert', 'witchcoil_lurch'],
                'patoot_attack': 'crest flare, toe shuffle, sudden assist burst',
                'neural_map': 'title scene tutorial yard sync',
            },
        },
        'scene_entries': scene_entries,
    }
    scene_path.parent.mkdir(parents=True, exist_ok=True)
    scene_path.write_text(json.dumps(scene_payload, indent=2) + '\n', encoding='utf-8')


def render_title_glb_preview(size: tuple[int, int], asset_root: Path, player_glb: Path, reference_images: list[Path]) -> tuple[Path | None, dict]:
    try:
        DodoPseudo3DEngine = importlib.import_module('dodo_engine3d').DodoPseudo3DEngine
    except Exception:
        DodoPseudo3DEngine = None

    metadata = {
        'asset_root': str(asset_root),
        'player_glb': str(player_glb),
        'reference_images': [str(path) for path in reference_images],
    }
    if DodoPseudo3DEngine is None:
        metadata['glb_render_status'] = 'renderer-unavailable'
        return None, metadata
    scene_path = OUTPUT_DIR / 'splash' / 'dodo_title_hero_scene.json'
    preview_path = OUTPUT_DIR / 'splash' / 'dodo_title_glb_preview.png'
    write_title_hero_scene(scene_path, player_glb, reference_images)
    engine = DodoPseudo3DEngine(width=size[0], height=size[1], scene_manifest_path=scene_path)
    payload = engine.write_preview(preview_path, orbit=0.58, elevation=0.18, shader_mix=0.94, time_s=2.1, scene_manifest_path=scene_path)
    metadata['glb_render_status'] = 'ok'
    metadata['glb_scene_manifest'] = str(scene_path)
    metadata['glb_preview'] = str(preview_path)
    metadata['glb_render_stats'] = payload.get('stats') if isinstance(payload, dict) else None
    return preview_path, metadata


def paste_reference_card(image: Image.Image, source_path: Path, *, box: tuple[int, int, int, int], title: str, accent: str) -> None:
    x0, y0, x1, y1 = box
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(box, radius=24, fill=(17, 20, 17, 212), outline=accent, width=3)
    if source_path.exists():
        card_image = Image.open(source_path).convert('RGBA')
        card_image.thumbnail((x1 - x0 - 24, y1 - y0 - 62), Image.Resampling.LANCZOS)
        card_x = x0 + ((x1 - x0) - card_image.width) // 2
        card_y = y0 + 16
        image.alpha_composite(card_image, (card_x, card_y))
    draw.rounded_rectangle((x0 + 12, y1 - 44, x1 - 12, y1 - 12), radius=12, fill=(10, 12, 10, 180), outline=None)
    draw.text((x0 + 20, y1 - 38), title, fill='#f2e4c5', font=load_font(18))


def draw_art_deco_border(draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    copper = '#d4ab72'
    shadow = '#47321f'
    draw.rounded_rectangle((18, 18, width - 18, height - 18), radius=30, outline=copper, width=5)
    draw.rounded_rectangle((34, 34, width - 34, height - 34), radius=24, outline=shadow, width=2)
    corner_patterns = [
        ((42, 42), (150, 42), (110, 78), (78, 122), (42, 150)),
        ((width - 42, 42), (width - 150, 42), (width - 110, 78), (width - 78, 122), (width - 42, 150)),
        ((42, height - 42), (150, height - 42), (110, height - 78), (78, height - 122), (42, height - 150)),
        ((width - 42, height - 42), (width - 150, height - 42), (width - 110, height - 78), (width - 78, height - 122), (width - 42, height - 150)),
    ]
    for points in corner_patterns:
        draw.line(points, fill=copper, width=4)
    for index in range(11):
        x_pos = 196 + index * 84
        draw.line((x_pos, 24, x_pos, 46), fill='#87613f', width=2)
        draw.line((x_pos, height - 24, x_pos, height - 46), fill='#87613f', width=2)


def draw_gothic_arches(draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    arch_color = (32, 39, 31, 176)
    highlight = (102, 82, 57, 112)
    for x_pos, base_width, top_y in ((146, 162, 112), (width - 146, 172, 96), (width // 2 + 40, 228, 74)):
        draw.rounded_rectangle((x_pos - base_width // 2, 120, x_pos + base_width // 2, height - 86), radius=26, fill=arch_color, outline=highlight, width=3)
        draw.polygon(((x_pos - base_width // 2, 124), (x_pos, top_y), (x_pos + base_width // 2, 124), (x_pos + base_width // 2 - 26, 124), (x_pos, top_y + 34), (x_pos - base_width // 2 + 26, 124)), fill=arch_color, outline=highlight)
        draw.line((x_pos, top_y + 22, x_pos, height - 86), fill=(74, 62, 48, 90), width=2)


def draw_ooze_drips(draw: ImageDraw.ImageDraw, width: int) -> None:
    drips = [
        (628, 0, 42, 118), (692, 0, 26, 84), (742, 0, 36, 136), (820, 0, 24, 92),
        (1018, 0, 44, 126), (1098, 0, 32, 94), (1172, 0, 50, 148),
    ]
    for x_pos, y_pos, half_width, depth in drips:
        draw.rounded_rectangle((x_pos - half_width, y_pos, x_pos + half_width, depth), radius=18, fill=(74, 120, 76, 154), outline=(134, 190, 122, 102), width=2)
        draw.ellipse((x_pos - half_width - 6, depth - 26, x_pos + half_width + 6, depth + 16), fill=(108, 168, 112, 166), outline=(175, 226, 160, 88))
    draw.rectangle((width - 520, 0, width, 26), fill=(68, 108, 70, 120))


def draw_techno_erp_overlay(draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    circuit = '#6de3c8'
    warning = '#d56f52'
    grid = '#27433f'
    for x_pos in range(648, width - 36, 54):
        draw.line((x_pos, 84, x_pos, height - 84), fill=grid, width=1)
    for y_pos in range(92, height - 50, 44):
        draw.line((624, y_pos, width - 34, y_pos), fill=grid, width=1)

    trace_points = [(706, 590), (770, 540), (816, 556), (866, 486), (932, 470), (984, 396), (1040, 404), (1098, 306), (1168, 286)]
    draw.line(trace_points, fill=warning, width=6, joint='curve')
    for x_pos, y_pos in trace_points:
        draw.ellipse((x_pos - 8, y_pos - 8, x_pos + 8, y_pos + 8), fill='#f6e0c5', outline=warning, width=3)

    threshold_box = (902, 454, 1238, 654)
    draw.rounded_rectangle(threshold_box, radius=24, fill=(15, 18, 17, 194), outline='#d4ab72', width=3)
    draw.text((926, 478), 'ERP PRESSURE SEQUENCER', fill='#f6e6c8', font=load_font(24))
    draw.text((926, 514), 'Tier build from dread anticipation', fill='#98e4d0', font=load_font(18))
    thresholds = [
        ('TIER I', 548, '#86c6b8'),
        ('TIER II', 578, '#d4ab72'),
        ('QTE FRACTURE', 608, '#d56f52'),
        ('STALL / JUMPSCARE', 638, '#f2e2c7'),
    ]
    for label, y_pos, color in thresholds:
        draw.line((926, y_pos, 1188, y_pos), fill=color, width=2)
        draw.text((1198, y_pos - 10), label, fill=color, font=load_font(16))

    neural_points = [(696, 192), (740, 168), (794, 182), (850, 152), (904, 170), (958, 148), (1012, 172), (1066, 158)]
    draw.line(neural_points, fill=circuit, width=3, joint='curve')
    for x_pos, y_pos in neural_points:
        draw.ellipse((x_pos - 6, y_pos - 6, x_pos + 6, y_pos + 6), fill='#10241f', outline=circuit, width=2)
    draw.text((676, 116), 'NEURAL CIRCUIT MAP', fill='#98e4d0', font=load_font(22))
    draw.text((678, 142), 'synaptic route pressure binds movement, threat, and Patoot timing', fill='#d9f3ec', font=load_font(16))

    status_box = (644, 602, 874, 674)
    draw.rounded_rectangle(status_box, radius=18, fill=(16, 18, 17, 190), outline='#6de3c8', width=2)
    draw.text((662, 618), 'STATUS QUEUE', fill='#d9f3ec', font=load_font(18))
    draw.text((662, 646), 'jumpscare interrupt  |  slowdown stall  |  synaptic reroute', fill='#98e4d0', font=load_font(15))


def make_title_music(path: Path) -> None:
    sample_rate = 22050
    duration_s = 14.0
    frame_count = int(sample_rate * duration_s)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        for index in range(frame_count):
            time_s = index / sample_rate
            hushfall = math.sin(2.0 * math.pi * 55.0 * time_s)
            drone = math.sin(2.0 * math.pi * 82.4 * time_s + math.sin(time_s * 0.35) * 0.7)
            reed = math.sin(2.0 * math.pi * 220.0 * time_s + math.sin(time_s * 1.2) * 0.16)
            choir = math.sin(2.0 * math.pi * 164.8 * time_s) * math.sin(time_s * 0.45)
            hive = math.sin(2.0 * math.pi * 410.0 * time_s) * 0.18 + math.sin(2.0 * math.pi * 612.0 * time_s) * 0.08
            percussion = 0.0
            beat_phase = (time_s * 1.55) % 1.0
            if beat_phase < 0.07:
                percussion = math.sin(2.0 * math.pi * 110.0 * time_s) * (1.0 - beat_phase / 0.07)
            lurch_phase = (time_s * 0.22) % 1.0
            lurch = max(0.0, math.sin(2.0 * math.pi * lurch_phase)) ** 8
            sample = (
                hushfall * 0.28
                + drone * 0.34
                + reed * 0.14
                + choir * 0.12
                + hive * 0.08
                + percussion * 0.12
                + lurch * 0.05
            )
            envelope = 0.86 + math.sin(time_s * 0.18) * 0.08
            value = int(max(-32767, min(32767, sample * envelope * 18200)))
            wav.writeframesraw(struct.pack('<h', value))


def make_bango_title_splash(path: Path, size: tuple[int, int]) -> None:
    width, height = size
    asset_root = resolve_title_asset_root()
    runtime_payload = resolve_title_runtime_payload(asset_root)
    player_glb = resolve_title_player_glb(runtime_payload)
    reference_images = collect_title_reference_images(asset_root)
    metadata = {
        'asset_root': str(asset_root),
        'runtime_pass_labels': [entry.get('pass_label') for entry in runtime_payload.get('passes', []) if isinstance(entry, dict)],
        'player_glb': str(player_glb) if player_glb else None,
        'reference_images': [str(path) for path in reference_images],
        'composition_mode': 'glb-plus-recraft-plus-vector-pose',
    }

    image = Image.new('RGBA', size, '#121611')
    draw = ImageDraw.Draw(image)

    for row in range(height):
        t = row / max(1, height - 1)
        red = int(18 + (78 - 18) * (1.0 - t * 0.65))
        green = int(22 + (62 - 22) * (1.0 - t * 0.2))
        blue = int(17 + (39 - 17) * (1.0 - t * 0.85))
        draw.line((0, row, width, row), fill=(red, green, blue, 255))

    for index in range(7):
        inset = 90 + index * 22
        color = (215, 144 - index * 8, 68 - index * 3, 28)
        draw.ellipse((width - 580 - inset, 40 - inset * 0.08, width - 40 + inset, height + 220), outline=color, width=5)

    draw_art_deco_border(draw, width, height)
    draw_gothic_arches(draw, width, height)
    draw_ooze_drips(draw, width)

    draw.polygon(((0, height), (0, height - 210), (180, height - 300), (430, height - 220), (700, height - 360), (1040, height - 250), (width, height - 320), (width, height)), fill='#1b241c')
    draw.polygon(((0, height), (0, height - 160), (220, height - 240), (520, height - 200), (780, height - 300), (1100, height - 210), (width, height - 250), (width, height)), fill='#253127')

    if player_glb is not None:
        glb_preview_path, glb_metadata = render_title_glb_preview(size, asset_root, player_glb, reference_images)
        metadata.update(glb_metadata)
        if glb_preview_path is not None and glb_preview_path.exists():
            glb_preview = Image.open(glb_preview_path).convert('RGBA')
            glb_preview = glb_preview.resize(size, Image.Resampling.LANCZOS)
            image = Image.blend(image, glb_preview, 0.76)
            draw = ImageDraw.Draw(image)

    draw.ellipse((68, 46, 604, 650), fill=(14, 18, 15, 92), outline=(227, 191, 129, 44), width=2)

    if reference_images:
        paste_reference_card(image, reference_images[0], box=(110, 250, 330, 480), title='Bango Turnaround', accent='#d8b477')
    if len(reference_images) > 1:
        paste_reference_card(image, reference_images[1], box=(348, 294, 558, 500), title='Bango Keypose', accent='#95b88d')
    if len(reference_images) > 2:
        paste_reference_card(image, reference_images[2], box=(120, 496, 292, 646), title='Patoot Turnaround', accent='#d8b477')
    if len(reference_images) > 3:
        paste_reference_card(image, reference_images[3], box=(308, 520, 474, 652), title='Patoot Keypose', accent='#95b88d')

    draw = ImageDraw.Draw(image)
    strap_points = [(808, 286), (972, 236), (980, 256), (822, 316)]
    draw.polygon(strap_points, fill='#e6ca87')
    draw.line((820, 304, 972, 248), fill='#84693d', width=5)

    pouch = [(764, 326), (848, 292), (914, 314), (954, 374), (932, 468), (842, 492), (752, 452), (720, 382)]
    draw.polygon(pouch, fill='#526b47')
    draw.polygon(((768, 334), (804, 306), (872, 298), (924, 320), (946, 366), (934, 392), (880, 372), (818, 360), (764, 366)), fill='#7fa06f')
    draw.arc((760, 314, 946, 484), start=222, end=334, fill='#2a3726', width=4)

    draw.ellipse((778, 214, 900, 334), fill='#dac6a6')
    draw.ellipse((798, 172, 838, 228), fill='#c7a36a')
    draw.ellipse((842, 168, 882, 226), fill='#c7a36a')
    draw.ellipse((802, 252, 826, 276), fill='#261c16')
    draw.ellipse((846, 248, 870, 272), fill='#261c16')
    draw.ellipse((810, 260, 820, 270), fill='#fff9e6')
    draw.ellipse((854, 256, 864, 266), fill='#fff9e6')
    draw.rounded_rectangle((826, 270, 840, 284), radius=6, fill='#916c46')
    draw.arc((808, 274, 866, 308), start=18, end=164, fill='#3b2920', width=4)

    draw_techno_erp_overlay(draw, width, height)

    title_font = load_font(64)
    subtitle_font = load_font(24)
    caption_font = load_font(18)
    for offset, color in ((4, '#2b1b12'), (2, '#6e4a2f')):
        draw.text((126 + offset, 120 + offset), 'BANGO: UNCHAINED', fill=color, font=title_font)
    draw.text((126, 120), 'BANGO: UNCHAINED', fill='#f7eed7', font=title_font)
    draw.text((132, 196), 'Underhive Nocturne title tableau', fill='#98e4d0', font=subtitle_font)
    draw.text((132, 226), 'ritual percussion, industrial drone, broken choir, and hive hum', fill='#f2d7a6', font=caption_font)
    draw.line((126, 278, 468, 278), fill='#d8b477', width=3)
    draw.text((130, 294), 'Bango and Patoot stand in the tutorial shrine yard, wide-eyed but unbroken.', fill='#f4ead4', font=subtitle_font)
    draw.text((132, 326), 'Their idle read is affectionate vigilance, not comic relief.', fill='#d7c6a1', font=caption_font)
    draw.text((130, 620), 'HORNS LOW  |  CREST LIFT  |  HUSHFALL HUM', fill='#f2e2c7', font=caption_font)
    draw.text((132, 646), 'occasional body lurches and companion bursts ride the tension loop', fill='#98e4d0', font=caption_font)

    metadata['splash_output'] = str(path)
    metadata['vector_overlay'] = {
        'elements': ['strap', 'pouch', 'patoot_head'],
        'pose': 'left_shoulder_pouch_peek',
    }
    metadata['art_direction'] = ['art-deco', 'gothic', 'ooze-punk', 'horror-techno']
    metadata['character_direction'] = {
        'bango': 'concept-artbook basis with small childfriendly wide-eyed deviation',
        'patoot': 'concept-artbook basis with affectionate alert posture and playful idle motion',
        'title_space': 'tutorial shrine yard / guided opening gameplay space',
    }
    metadata['erp_sequencer'] = {
        'definition': 'psychic pressure buildup from anticipating an advantaged peer-threat that can fracture into sudden gameplay interruptions',
        'thresholds': ['tier_i', 'tier_ii', 'qte_fracture', 'stall_jumpscare'],
        'player_interruptions': ['quick_time_event', 'game_slowdown_stall', 'status_queue_event'],
        'neural_map': 'temporary synaptic routing overlays bind Bango and Patoot pathways to environment circuits',
        'patoot_attack': 'precisely timed ovular sac vomit burst',
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    path.with_suffix('.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')


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
        output_path = OUTPUT_DIR / relative_path
        if asset_name == 'splash':
            make_bango_title_splash(output_path, size)
        elif asset_name in {'shell_frame', 'runtime_panel', 'report_panel'}:
            make_panel(output_path, size, fill, outline, title)
        else:
            make_labeled_asset(output_path, size, fill, outline, title, subtitle)

    make_badge(OUTPUT_DIR / 'dodogame_badge.png')
    make_title_music(OUTPUT_DIR / 'splash' / 'dodo_title_theme.wav')
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
        'title_music': str(OUTPUT_DIR / 'splash' / 'dodo_title_theme.wav'),
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
