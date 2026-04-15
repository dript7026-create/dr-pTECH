from __future__ import annotations

import argparse
import ctypes
import importlib
import json
import math
import subprocess
import sys
import tkinter as tk
from ctypes import wintypes
from pathlib import Path
from tkinter import ttk

try:
    from PIL import Image, ImageDraw, ImageFont, ImageTk
except Exception:
    Image = None
    ImageDraw = None
    ImageFont = None
    ImageTk = None

try:
    import winsound
except Exception:
    winsound = None

try:
    from dodo_engine3d import DODO_SHADER_MANIFEST, DodoPseudo3DEngine
except Exception:
    DODO_SHADER_MANIFEST = None
    DodoPseudo3DEngine = None


VISUAL_ASSET_SPECS = [
    ('badge', 'Launcher Badge', (220, 220)),
    ('background', 'Background', (360, 220)),
    ('shell_frame', 'Shell Frame', (360, 220)),
    ('runtime_panel', 'Runtime Panel', (320, 180)),
    ('report_panel', 'Report Panel', (320, 180)),
    ('runtime_cards', 'Runtime Cards', (320, 180)),
    ('toolbar_icons', 'Toolbar Icons', (320, 160)),
    ('report_panels', 'Report Panels', (320, 160)),
    ('splash', 'Launch Splash', (360, 220)),
]

INPUT_ASSET_SPECS = [
    ('controller_diagram', 'Controller Diagram', (340, 220)),
    ('buttons', 'Button Atlas', (320, 180)),
    ('status_widgets', 'Status Widgets', (320, 180)),
    ('input_hints', 'Input Hints', (320, 180)),
    ('cursor_pack', 'Cursor Pack', (260, 160)),
    ('scene_hierarchy', 'Scene Hierarchy', (320, 180)),
    ('material_cards', 'Material Cards', (320, 180)),
    ('timeline_strips', 'Timeline Strips', (320, 180)),
    ('world_map_widgets', 'World Map Widgets', (320, 180)),
]

TITLE_MENU_NODES: dict[str, dict[str, object]] = {
    'root': {
        'title': 'Title Screen',
        'theme': 'root',
        'subtitle': 'Three doors only. Pick a path and descend.',
        'summary': 'The opening surface stays sparse: one hero scene, one current menu, one live status readout.',
        'options': [
            {'label': 'Start Game', 'kind': 'node', 'target': 'start_game', 'description': 'Move into runtime and play-facing entry points.'},
            {'label': 'Tutorial', 'kind': 'node', 'target': 'tutorial_hub', 'description': 'Enter guided onboarding, controls, and intro support.'},
            {'label': 'Settings', 'kind': 'node', 'target': 'settings_hub', 'description': 'Open visuals, tools, and system maintenance branches.'},
        ],
    },
    'start_game': {
        'title': 'Start Game',
        'theme': 'start_game',
        'subtitle': 'Keep the first decision narrow.',
        'summary': 'Play-facing entry paths branch away from the title instead of sharing space with tools and reports.',
        'options': [
            {'label': 'New Run', 'kind': 'node', 'target': 'new_run', 'description': 'Move toward direct play starts and first-step entry.'},
            {'label': 'Progress Route', 'kind': 'node', 'target': 'stage_flow', 'description': 'Open pass progression and runtime contract branches.'},
            {'label': 'Theater Route', 'kind': 'node', 'target': 'runtime_theater', 'description': 'Open showcase, viewport, and live scene routes.'},
        ],
    },
    'new_run': {
        'title': 'New Run',
        'theme': 'start_game',
        'subtitle': 'One more step before launch.',
        'summary': 'Starting play is now a child room with only three concrete run-entry choices.',
        'options': [
            {'label': 'Launch Demo', 'kind': 'action', 'target': 'launch_bango_demo', 'description': 'Start the external Bango executable.'},
            {'label': 'Tutorial Scene', 'kind': 'tab', 'target': 'Tutorial Sim', 'description': 'Open the current tutorial simulation scene.'},
            {'label': 'Illusion 3D', 'kind': 'tab', 'target': 'Illusion 3D', 'description': 'Open the DODO viewport directly from the title stack.'},
        ],
    },
    'stage_flow': {
        'title': 'Stage Flow',
        'theme': 'start_game',
        'subtitle': 'Three progression views, no cross-noise.',
        'summary': 'This branch keeps progression inspection separate from direct launch and showcase staging.',
        'options': [
            {'label': 'Runtime Feed', 'kind': 'node', 'target': 'runtime_feed', 'description': 'Inspect current runtime handoff data.'},
            {'label': 'Pass Gallery', 'kind': 'node', 'target': 'pass_gallery', 'description': 'Review pass cards and focus tools.'},
            {'label': 'Contract Room', 'kind': 'node', 'target': 'contract_room', 'description': 'Inspect the hybrid runtime contract.'},
        ],
    },
    'runtime_feed': {
        'title': 'Runtime Feed',
        'theme': 'start_game',
        'subtitle': 'The live runtime data room.',
        'summary': 'This room keeps only the most direct progression-state destinations.',
        'options': [
            {'label': 'PlayNOW', 'kind': 'tab', 'target': 'PlayNOW', 'description': 'Inspect runtime pass content and current handoff data.'},
            {'label': 'Pipeline Overview', 'kind': 'tab', 'target': 'Pipeline Overview', 'description': 'Open the pipeline overview screen.'},
            {'label': 'Pipeline Verify', 'kind': 'tab', 'target': 'Pipeline Verify', 'description': 'Open the current verification screen.'},
        ],
    },
    'pass_gallery': {
        'title': 'Pass Gallery',
        'theme': 'start_game',
        'subtitle': 'A room for pass review only.',
        'summary': 'Pass-specific inspection is separated from general runtime and showcase routing.',
        'options': [
            {'label': 'Pass Cards', 'kind': 'tab', 'target': 'Pass Cards', 'description': 'Review pass cards and focus cues.'},
            {'label': 'BangoNOW Showcase', 'kind': 'tab', 'target': 'BangoNOW Showcase', 'description': 'Open the concept runtime gallery.'},
            {'label': 'Illusion 3D', 'kind': 'tab', 'target': 'Illusion 3D', 'description': 'Open the DODO viewport for scene focus.'},
        ],
    },
    'contract_room': {
        'title': 'Contract Room',
        'theme': 'start_game',
        'subtitle': 'Systems behind progression.',
        'summary': 'Contract and showcase data are grouped here rather than attached directly to the start screen.',
        'options': [
            {'label': 'Hybrid Runtime', 'kind': 'tab', 'target': 'Hybrid Runtime', 'description': 'Inspect the runtime contract that binds concept to scene.'},
            {'label': 'Pipeline Overview', 'kind': 'tab', 'target': 'Pipeline Overview', 'description': 'Read the compact pipeline state overview.'},
            {'label': 'Credits', 'kind': 'tab', 'target': 'Credits', 'description': 'Open package, bundle, and execution metadata.'},
        ],
    },
    'runtime_theater': {
        'title': 'Runtime Theater',
        'theme': 'start_game',
        'subtitle': 'Three live scene doors.',
        'summary': 'Live rendering, showcase staging, and tutorial scene playback each get a dedicated branch exit.',
        'options': [
            {'label': 'Viewport Stage', 'kind': 'tab', 'target': 'Illusion 3D', 'description': 'Open the DODO viewport.'},
            {'label': 'Showcase Hall', 'kind': 'tab', 'target': 'BangoNOW Showcase', 'description': 'Inspect the concept runtime gallery.'},
            {'label': 'Tutorial Stage', 'kind': 'tab', 'target': 'Tutorial Sim', 'description': 'Open the current tutorial simulation output.'},
        ],
    },
    'tutorial_hub': {
        'title': 'Tutorial',
        'theme': 'tutorial_hub',
        'subtitle': 'Onboarding stays parental too.',
        'summary': 'Tutorial access splits into simulation, control teaching, and story framing rather than a single catch-all panel.',
        'options': [
            {'label': 'Guided Start', 'kind': 'node', 'target': 'guided_start', 'description': 'Move into tutorial start choices and live onboarding routes.'},
            {'label': 'Control Primer', 'kind': 'node', 'target': 'control_primer', 'description': 'Open controller and input-reference branches.'},
            {'label': 'Story Briefing', 'kind': 'node', 'target': 'story_briefing', 'description': 'Open tutorial state, prompts, and atmosphere routes.'},
        ],
    },
    'guided_start': {
        'title': 'Guided Start',
        'theme': 'tutorial_hub',
        'subtitle': 'Three simple onboarding entries.',
        'summary': 'Tutorial start actions live in their own room rather than on the hub itself.',
        'options': [
            {'label': 'Run Tutorial', 'kind': 'action', 'target': 'run_tutorial_sim', 'description': 'Execute the tutorial completion simulation.'},
            {'label': 'Tutorial Scene', 'kind': 'tab', 'target': 'Tutorial Sim', 'description': 'Open the tutorial scene output.'},
            {'label': 'Controller State', 'kind': 'tab', 'target': 'Controller', 'description': 'Open live controller polling and bindings.'},
        ],
    },
    'control_primer': {
        'title': 'Control Primer',
        'theme': 'tutorial_hub',
        'subtitle': 'Inputs split into three simple doors.',
        'summary': 'Controller state, visual prompts, and input atlases are intentionally separated for calmer reading.',
        'options': [
            {'label': 'Controller State', 'kind': 'tab', 'target': 'Controller', 'description': 'Open live controller polling and bindings.'},
            {'label': 'Input Assets', 'kind': 'tab', 'target': 'Input Assets', 'description': 'Open diagrams, widget atlases, and material strips.'},
            {'label': 'Visual Guides', 'kind': 'tab', 'target': 'Visual Assets', 'description': 'Open the display-side guide panels.'},
        ],
    },
    'story_briefing': {
        'title': 'Story Briefing',
        'theme': 'tutorial_hub',
        'subtitle': 'Tutorial context without tool spill.',
        'summary': 'Prompt stack, simulation state, and archive references stay in a dedicated story room.',
        'options': [
            {'label': 'Tutorial Sim', 'kind': 'tab', 'target': 'Tutorial Sim', 'description': 'Read the generated tutorial state and prompt stack.'},
            {'label': 'Credits', 'kind': 'tab', 'target': 'Credits', 'description': 'Open project and package notes.'},
            {'label': 'Visual Assets', 'kind': 'tab', 'target': 'Visual Assets', 'description': 'Open the display-side guide panels.'},
        ],
    },
    'settings_hub': {
        'title': 'Settings',
        'theme': 'settings_hub',
        'subtitle': 'Maintenance lives behind its own doorway.',
        'summary': 'Settings is a parent branch for shell refresh, build tools, and archive/reference browsing.',
        'options': [
            {'label': 'Shell Room', 'kind': 'node', 'target': 'shell_room', 'description': 'Open shell refresh and return controls.'},
            {'label': 'System Tools', 'kind': 'node', 'target': 'system_tools', 'description': 'Open build and validation actions.'},
            {'label': 'Archive Browser', 'kind': 'node', 'target': 'archive_browser', 'description': 'Open credits and asset archive branches.'},
        ],
    },
    'shell_room': {
        'title': 'Shell Room',
        'theme': 'settings_hub',
        'subtitle': 'Shell-only operations.',
        'summary': 'Basic shell maintenance and return paths live here instead of cluttering the title root.',
        'options': [
            {'label': 'Refresh Shell', 'kind': 'action', 'target': 'refresh_state', 'description': 'Reload launcher state and theme assets.'},
            {'label': 'Title Screen', 'kind': 'action', 'target': 'title_menu_home', 'description': 'Return to the root title menu.'},
            {'label': 'Illusion 3D', 'kind': 'tab', 'target': 'Illusion 3D', 'description': 'Jump into the live viewport from shell maintenance.'},
        ],
    },
    'system_tools': {
        'title': 'System Tools',
        'theme': 'settings_hub',
        'subtitle': 'Three maintenance actions per screen.',
        'summary': 'Validation and build operations are grouped into a small, predictable maintenance branch.',
        'options': [
            {'label': 'Verify Pipeline', 'kind': 'action', 'target': 'verify_pipeline', 'description': 'Run the end-to-end manifest verification pass.'},
            {'label': 'Build Showcase', 'kind': 'action', 'target': 'build_bangonow_showcase', 'description': 'Rebuild the live showcase scene.'},
            {'label': 'Build Runtime', 'kind': 'action', 'target': 'build_hybrid_runtime', 'description': 'Rebuild the hybrid runtime profile.'},
        ],
    },
    'archive_browser': {
        'title': 'Archive Browser',
        'theme': 'settings_hub',
        'subtitle': 'Reference screens get their own branch.',
        'summary': 'Credits and asset archives are separated from play and maintenance paths so the title flow stays narrow.',
        'options': [
            {'label': 'Visual Assets', 'kind': 'tab', 'target': 'Visual Assets', 'description': 'Browse generated launcher artwork and panels.'},
            {'label': 'Input Assets', 'kind': 'tab', 'target': 'Input Assets', 'description': 'Browse control and material reference sheets.'},
            {'label': 'Credits', 'kind': 'tab', 'target': 'Credits', 'description': 'Open manifests, bundle metadata, and execution notes.'},
        ],
    },
}


ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

_bango_paths = importlib.import_module('bango_integration_paths')
resolve_bango_asset_root = _bango_paths.resolve_bango_asset_root
resolve_bango_project_root = _bango_paths.resolve_bango_project_root
resolve_idloadint_dir = _bango_paths.resolve_idloadint_dir
resolve_playnow_finalstage_path = _bango_paths.resolve_playnow_finalstage_path
resolve_playnow_runtime_path = _bango_paths.resolve_playnow_runtime_path
build_tick_gnosis_frame = importlib.import_module('tick_gnosis').build_tick_gnosis_frame

GENERATED_DIR = ROOT / 'generated'
DODO_THEME_PATH = GENERATED_DIR / 'dodogame_gui' / 'theme.json'
HYBRID_RUNTIME_PATH = GENERATED_DIR / 'dodogame_hybrid_runtime.json'
DODO_MANIFEST_SUMMARY_PATH = GENERATED_DIR / 'dodogame_gui_asset_summary.json'
ORB_BANGO_DEMO_PATH = WORKSPACE_ROOT / 'ORBEngine' / 'bango_unchained_bangopatoot_demo.exe'
DODO_ENGINE_PREVIEW_PATH = GENERATED_DIR / 'dodogame_gui' / 'dodo_engine_preview.png'
DODO_TITLE_GLB_PREVIEW_PATH = GENERATED_DIR / 'dodogame_gui' / 'splash' / 'dodo_title_glb_preview.png'
DODO_TITLE_SCENE_PATH = GENERATED_DIR / 'dodogame_gui' / 'splash' / 'dodo_title_hero_scene.json'
DODO_PASS_PREVIEW_DIR = GENERATED_DIR / 'dodogame_gui' / 'pass_previews'
DODO_PASS_REBUILD_REPORT_DIR = GENERATED_DIR / 'dodogame_gui' / 'pass_rebuild_reports'
BANGONOW_SHOWCASE_PATH = GENERATED_DIR / 'dodogame_bangonow_showcase.json'
BANGO_PIPELINE_VERIFY_PATH = GENERATED_DIR / 'dodogame_bango_pipeline_verification.json'
DODO_WINDOWS_BUNDLE_MANIFEST_PATH = GENERATED_DIR / 'windows_bundle' / 'dodogame_windows_bundle.json'

XINPUT_GAMEPAD_DPAD_UP = 0x0001
XINPUT_GAMEPAD_DPAD_DOWN = 0x0002
XINPUT_GAMEPAD_DPAD_LEFT = 0x0004
XINPUT_GAMEPAD_DPAD_RIGHT = 0x0008
XINPUT_GAMEPAD_START = 0x0010
XINPUT_GAMEPAD_BACK = 0x0020
XINPUT_GAMEPAD_LEFT_THUMB = 0x0040
XINPUT_GAMEPAD_RIGHT_THUMB = 0x0080
XINPUT_GAMEPAD_LEFT_SHOULDER = 0x0100
XINPUT_GAMEPAD_RIGHT_SHOULDER = 0x0200
XINPUT_GAMEPAD_A = 0x1000
XINPUT_GAMEPAD_B = 0x2000
XINPUT_GAMEPAD_X = 0x4000
XINPUT_GAMEPAD_Y = 0x8000

BUTTON_NAMES = [
    ('DPadUp', XINPUT_GAMEPAD_DPAD_UP),
    ('DPadDown', XINPUT_GAMEPAD_DPAD_DOWN),
    ('DPadLeft', XINPUT_GAMEPAD_DPAD_LEFT),
    ('DPadRight', XINPUT_GAMEPAD_DPAD_RIGHT),
    ('Start', XINPUT_GAMEPAD_START),
    ('Back', XINPUT_GAMEPAD_BACK),
    ('LeftThumb', XINPUT_GAMEPAD_LEFT_THUMB),
    ('RightThumb', XINPUT_GAMEPAD_RIGHT_THUMB),
    ('LB', XINPUT_GAMEPAD_LEFT_SHOULDER),
    ('RB', XINPUT_GAMEPAD_RIGHT_SHOULDER),
    ('A', XINPUT_GAMEPAD_A),
    ('B', XINPUT_GAMEPAD_B),
    ('X', XINPUT_GAMEPAD_X),
    ('Y', XINPUT_GAMEPAD_Y),
]

TITLE_BRANCH_THEMES = {
    'root': {'accent': '#d0aa73', 'text': '#f7edd4', 'muted': '#d8c39d', 'overlay': (38, 26, 18, 64)},
    'start_game': {'accent': '#d88b3c', 'text': '#fff2de', 'muted': '#f0c78f', 'overlay': (72, 38, 16, 76)},
    'tutorial_hub': {'accent': '#8cb091', 'text': '#eff7f0', 'muted': '#c9e0cc', 'overlay': (22, 48, 34, 72)},
    'settings_hub': {'accent': '#6de3c8', 'text': '#eefaf8', 'muted': '#b3ece1', 'overlay': (18, 40, 42, 74)},
}

TITLE_SCENE_PROFILES = {
    'root': {'orbit': 0.58, 'elevation': 0.17, 'shader_mix': 0.96, 'motion_orbit': 0.08, 'motion_elevation': 0.03, 'tagline': 'threshold foyer'},
    'start_game': {'orbit': 0.84, 'elevation': 0.15, 'shader_mix': 0.98, 'motion_orbit': 0.06, 'motion_elevation': 0.025, 'tagline': 'ember route'},
    'tutorial_hub': {'orbit': 0.34, 'elevation': 0.19, 'shader_mix': 0.9, 'motion_orbit': 0.05, 'motion_elevation': 0.02, 'tagline': 'green room guidance'},
    'settings_hub': {'orbit': 1.12, 'elevation': 0.13, 'shader_mix': 0.88, 'motion_orbit': 0.04, 'motion_elevation': 0.018, 'tagline': 'calibration chamber'},
}


class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ('wButtons', wintypes.WORD),
        ('bLeftTrigger', ctypes.c_ubyte),
        ('bRightTrigger', ctypes.c_ubyte),
        ('sThumbLX', ctypes.c_short),
        ('sThumbLY', ctypes.c_short),
        ('sThumbRX', ctypes.c_short),
        ('sThumbRY', ctypes.c_short),
    ]


class XINPUT_STATE(ctypes.Structure):
    _fields_ = [('dwPacketNumber', wintypes.DWORD), ('Gamepad', XINPUT_GAMEPAD)]


class XInputPoller:
    def __init__(self) -> None:
        self._dll = None
        for library_name in ('xinput1_4.dll', 'xinput1_3.dll', 'xinput9_1_0.dll'):
            try:
                self._dll = ctypes.WinDLL(library_name)
                break
            except OSError:
                continue
        self.available = self._dll is not None
        if self.available:
            self._dll.XInputGetState.argtypes = [wintypes.DWORD, ctypes.POINTER(XINPUT_STATE)]
            self._dll.XInputGetState.restype = wintypes.DWORD

    def poll(self) -> dict:
        if not self.available:
            return {'connected': False, 'reason': 'XInput DLL not available'}
        state = XINPUT_STATE()
        result = self._dll.XInputGetState(0, ctypes.byref(state))
        if result != 0:
            return {'connected': False, 'reason': f'XInput error {result}'}
        buttons = [name for name, mask in BUTTON_NAMES if state.Gamepad.wButtons & mask]
        return {
            'connected': True,
            'packet': int(state.dwPacketNumber),
            'buttons': buttons,
            'left_trigger': int(state.Gamepad.bLeftTrigger),
            'right_trigger': int(state.Gamepad.bRightTrigger),
            'left_stick': {'x': int(state.Gamepad.sThumbLX), 'y': int(state.Gamepad.sThumbLY)},
            'right_stick': {'x': int(state.Gamepad.sThumbRX), 'y': int(state.Gamepad.sThumbRY)},
        }


def load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding='utf-8'))


def load_display_font(size: int, *, bold: bool = False):
    if ImageFont is None:
        return None
    candidates = ['C:/Windows/Fonts/segoeuib.ttf', 'C:/Windows/Fonts/trebucbd.ttf', 'C:/Windows/Fonts/consola.ttf'] if bold else ['C:/Windows/Fonts/segoeui.ttf', 'C:/Windows/Fonts/trebuc.ttf', 'C:/Windows/Fonts/consola.ttf']
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def run_command(command: list[str]) -> tuple[int, str, str]:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    return result.returncode, result.stdout, result.stderr


def resolve_existing_path(raw_path: object) -> Path | None:
    if not raw_path:
        return None
    path = Path(str(raw_path))
    return path if path.exists() else None


def collect_asset_manifest_preview_paths(asset_manifest_path: object, limit: int = 3) -> list[str]:
    manifest_path = resolve_existing_path(asset_manifest_path)
    if manifest_path is None:
        return []
    manifest_payload = load_json(manifest_path)
    if not isinstance(manifest_payload, dict):
        return []

    roots: list[Path] = []
    output_root = resolve_existing_path(manifest_payload.get('output_root'))
    asset_root = resolve_existing_path(manifest_payload.get('asset_root'))
    if output_root is not None:
        roots.append(output_root)
    if asset_root is not None and asset_root not in roots:
        roots.append(asset_root)
    roots.append(manifest_path.parent)

    previews: list[str] = []
    seen: set[str] = set()
    for asset in manifest_payload.get('assets', []):
        if not isinstance(asset, dict):
            continue
        raw_out = asset.get('out')
        if not raw_out:
            continue
        out_path = Path(str(raw_out))
        candidates = [out_path] if out_path.is_absolute() else [root / out_path for root in roots]
        for candidate in candidates:
            if candidate.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.webp'}:
                continue
            if not candidate.exists():
                continue
            candidate_value = candidate.as_posix()
            if candidate_value in seen:
                continue
            seen.add(candidate_value)
            previews.append(candidate_value)
            if len(previews) >= limit:
                return previews
    return previews


def load_pass_rebuild_report(pass_label: str) -> dict | None:
    report_path = DODO_PASS_REBUILD_REPORT_DIR / f'{pass_label}.json'
    report = load_json(report_path)
    return report if isinstance(report, dict) else None


def build_bango_pipeline_overview(state: dict) -> dict:
    package = state.get('bangonow_package') if isinstance(state.get('bangonow_package'), dict) else {}
    showcase = state.get('bangonow_showcase') if isinstance(state.get('bangonow_showcase'), dict) else {}
    playnow_runtime = state.get('playnow_runtime') if isinstance(state.get('playnow_runtime'), dict) else {}
    playnow_finalstage = state.get('playnow_finalstage') if isinstance(state.get('playnow_finalstage'), dict) else {}
    verification = state.get('pipeline_verification') if isinstance(state.get('pipeline_verification'), dict) else {}
    summary = state.get('bangonow_summary') if isinstance(state.get('bangonow_summary'), dict) else {}
    runtime_passes = [entry.get('pass_label') for entry in playnow_runtime.get('passes', []) if isinstance(entry, dict) and entry.get('pass_label')]
    showcase_entries = showcase.get('scene_entries', []) if isinstance(showcase.get('scene_entries'), list) else []
    showcase_passes = sorted(
        {
            entry.get('metadata', {}).get('pass_label')
            for entry in showcase_entries
            if isinstance(entry, dict)
            and isinstance(entry.get('metadata'), dict)
            and entry.get('metadata', {}).get('pass_label')
        }
    )
    artifacts = package.get('artifacts', {}) if isinstance(package.get('artifacts'), dict) else {}
    return {
        'package': {
            'playable_ready': package.get('playable_ready'),
            'requested_passes': package.get('requested_passes', []),
            'selected_build_targets': package.get('selected_build_targets', []),
            'artifact_count': len(artifacts),
            'manifest_sources': package.get('manifests', {}),
        },
        'runtime': {
            'pass_labels': runtime_passes,
            'pass_count': len(runtime_passes),
            'player': playnow_runtime.get('player', {}),
            'engine_handoffs': playnow_runtime.get('engine_handoffs', {}),
        },
        'showcase': {
            'scene_name': showcase.get('showcase_name'),
            'scene_entry_count': len(showcase_entries),
            'represented_passes': showcase_passes,
            'camera': showcase.get('camera', {}),
            'pipeline': showcase.get('pipeline', {}),
        },
        'finalstage': {
            'engine_manifests': playnow_finalstage.get('engine_manifests', {}),
            'windows_delivery': playnow_finalstage.get('windows_delivery', {}),
            'gameplay_contract': playnow_finalstage.get('gameplay_contract', {}),
        },
        'artifacts': {
            name: {
                'platform': payload.get('platform'),
                'exists': payload.get('exists'),
                'staged_path': payload.get('staged_path'),
            }
            for name, payload in artifacts.items()
            if isinstance(payload, dict)
        },
        'verification': verification or {'overall_status': 'missing'},
        'summary_runs': sorted(summary.get('runs', {}).keys()) if isinstance(summary.get('runs'), dict) else [],
    }


def build_pass_records(state: dict) -> list[dict]:
    playnow_runtime = state.get('playnow_runtime') if isinstance(state.get('playnow_runtime'), dict) else {}
    showcase = state.get('bangonow_showcase') if isinstance(state.get('bangonow_showcase'), dict) else {}
    verification = state.get('pipeline_verification') if isinstance(state.get('pipeline_verification'), dict) else {}
    per_pass = verification.get('per_pass', {}) if isinstance(verification.get('per_pass'), dict) else {}
    showcase_entries = showcase.get('scene_entries', []) if isinstance(showcase.get('scene_entries'), list) else []
    showcase_by_pass: dict[str, list[dict]] = {}
    for entry in showcase_entries:
        if not isinstance(entry, dict):
            continue
        metadata = entry.get('metadata', {}) if isinstance(entry.get('metadata'), dict) else {}
        pass_label = metadata.get('pass_label')
        if not pass_label:
            continue
        showcase_by_pass.setdefault(str(pass_label), []).append(entry)

    records: list[dict] = []
    for index, entry in enumerate(playnow_runtime.get('passes', [])):
        if not isinstance(entry, dict):
            continue
        pass_label = str(entry.get('pass_label', f'pass_{index}'))
        pass_entries = showcase_by_pass.get(pass_label, [])
        pass_card_entry = next((item for item in pass_entries if isinstance(item, dict) and str(item.get('id', '')).startswith('pass_card_')), None)
        positions = [item.get('position', [0.0, 0.0, 0.0]) for item in pass_entries if isinstance(item.get('position'), list) and len(item.get('position')) >= 3]
        average_x = sum(float(pos[0]) for pos in positions) / len(positions) if positions else 0.0
        average_z = sum(float(pos[2]) for pos in positions) / len(positions) if positions else 11.5
        verify_entry = per_pass.get(pass_label, {}) if isinstance(per_pass.get(pass_label), dict) else {}
        status = str(verify_entry.get('status', 'pass' if pass_entries else 'warn'))
        display_label = str(pass_card_entry.get('label')) if isinstance(pass_card_entry, dict) and pass_card_entry.get('label') else pass_label
        preview_image_path = pass_card_entry.get('image_path') if isinstance(pass_card_entry, dict) else None
        live_preview_path = DODO_PASS_PREVIEW_DIR / f'{pass_label}.png'
        live_preview = live_preview_path.as_posix() if live_preview_path.exists() else None
        thumbnail_paths = []
        for candidate in [live_preview, preview_image_path, *collect_asset_manifest_preview_paths(entry.get('asset_manifest'), limit=3)]:
            if not candidate:
                continue
            candidate_value = str(candidate)
            if candidate_value not in thumbnail_paths:
                thumbnail_paths.append(candidate_value)
        rebuild_report = load_pass_rebuild_report(pass_label)
        records.append(
            {
                'pass_label': pass_label,
                'display_label': display_label,
                'asset_count': entry.get('asset_count'),
                'asset_manifest': entry.get('asset_manifest'),
                'graphics_load_in_ready': verify_entry.get('graphics_load_in_ready'),
                'feature_complete': verify_entry.get('feature_complete'),
                'status': status,
                'showcase_entry_count': len(pass_entries),
                'preview_image_path': preview_image_path,
                'live_preview_image_path': live_preview,
                'thumbnail_paths': thumbnail_paths[:4],
                'rebuild_report': rebuild_report,
                'focus_hint': {
                    'x': round(average_x, 3),
                    'z': round(average_z, 3),
                    'orbit': round(0.56 + max(-0.9, min(0.9, average_x / 10.0)) * 0.7, 3),
                },
                'details': verify_entry or {'runtime': entry, 'showcase_entry_count': len(pass_entries)},
                'runtime': entry,
            }
        )
    return records


class BitmapFontRenderer:
    def __init__(self, atlas_json: Path) -> None:
        self.metadata = load_json(atlas_json) if atlas_json.exists() else None
        self.atlas_image = None
        self.tk_image = None
        if Image is not None and self.metadata:
            atlas_path = Path(self.metadata['atlas'])
            if not atlas_path.is_absolute():
                atlas_path = atlas_json.parent / atlas_path.name
            if atlas_path.exists():
                self.atlas_image = Image.open(atlas_path).convert('RGBA')

    def render_text(self, text: str, scale: int = 1):
        if Image is None or ImageTk is None or not self.metadata or self.atlas_image is None:
            return None
        glyphs = self.metadata['glyphs']
        cell_width = int(self.metadata['cell_width'])
        cell_height = int(self.metadata['cell_height'])
        width = max(1, len(text) * cell_width * scale)
        height = max(1, cell_height * scale)
        canvas = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        for index, character in enumerate(text.upper()):
            frame = glyphs.get(character) or glyphs.get(' ')
            if not frame:
                continue
            crop = self.atlas_image.crop((frame['x'], frame['y'], frame['x'] + frame['w'], frame['y'] + frame['h']))
            if scale != 1:
                crop = crop.resize((frame['w'] * scale, frame['h'] * scale), Image.Resampling.NEAREST)
            canvas.alpha_composite(crop, (index * cell_width * scale, 0))
        self.tk_image = ImageTk.PhotoImage(canvas)
        return self.tk_image


class DodoGameApp:
    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        self.master.title('Bango: Unchained - Bango&Patoot | DODOGame')
        self.master.geometry('1320x860')
        self.master.configure(bg='#182019')
        self.status_var = tk.StringVar(value='Ready.')
        self.controller_var = tk.StringVar(value='Controller polling idle.')
        self.poller = XInputPoller()
        self.state = self.collect_state()
        self.images: dict[str, object] = {}
        self.tab_frames: dict[str, tk.Widget] = {}
        self.asset_preview_labels: dict[str, tuple[tk.Label, tk.Label]] = {}
        self.font_renderers = self.load_font_renderers()
        showcase_path = BANGONOW_SHOWCASE_PATH if BANGONOW_SHOWCASE_PATH.exists() else None
        self.engine = DodoPseudo3DEngine(width=560, height=320, scene_manifest_path=showcase_path) if DodoPseudo3DEngine is not None else None
        self.title_engine = DodoPseudo3DEngine(width=920, height=540, scene_manifest_path=DODO_TITLE_SCENE_PATH if DODO_TITLE_SCENE_PATH.exists() else showcase_path) if DodoPseudo3DEngine is not None else None
        self.viewport_image_label: tk.Label | None = None
        self.viewport_stats_text: tk.Text | None = None
        self.title_hero_image_label: tk.Label | None = None
        self.title_menu_subheading: tk.Label | None = None
        self.title_menu_info: tk.Label | None = None
        self.title_status_label: tk.Label | None = None
        self.title_flavor_label: tk.Label | None = None
        self.notebook: ttk.Notebook | None = None
        self.title_tab: tk.Frame | None = None
        self.title_menu_heading: tk.Label | None = None
        self.title_menu_frame: tk.Frame | None = None
        self.title_menu_stack: list[str] = ['root']
        self.title_menu_selected_index = 0
        self.title_menu_buttons: list[tk.Button] = []
        self.title_scene_time = 0.0
        self.title_transition_phase = 0.0
        self.title_transition_note = 'threshold foyer'
        self.title_music_active = False
        self.title_last_buttons: set[str] = set()
        self.title_trigger_state = {'bango_trigger': 0.0, 'patoot_trigger': 0.0}
        self.title_gesture_state = {'bango': 'idle watch', 'patoot': 'idle amuse'}
        self.viewport_tab: tk.Frame | None = None
        self.pass_cards_frame: tk.Frame | None = None
        self.pass_detail_text: tk.Text | None = None
        self.viewport_orbit_var = tk.DoubleVar(value=0.58)
        self.viewport_elevation_var = tk.DoubleVar(value=0.22)
        self.viewport_shader_var = tk.DoubleVar(value=0.88)
        self.viewport_time = 0.0
        self.viewport_running = True
        self.master.protocol('WM_DELETE_WINDOW', self._on_close)
        self.master.bind('<Up>', lambda _event: self._title_menu_move(-1))
        self.master.bind('<Down>', lambda _event: self._title_menu_move(1))
        self.master.bind('<Left>', lambda _event: self.title_menu_back())
        self.master.bind('<BackSpace>', lambda _event: self.title_menu_back())
        self.master.bind('<Escape>', lambda _event: self.title_menu_back())
        self.master.bind('<Return>', lambda _event: self._activate_selected_title_option())
        self.master.bind('<space>', lambda _event: self._activate_selected_title_option())

        self._build_header()
        self._build_controls()
        self._build_tabs()
        self.refresh_views()
        self._poll_controller()
        self._tick_title_scene()
        self._tick_viewport()
        self._sync_title_audio()

    def collect_state(self) -> dict:
        asset_root = resolve_bango_asset_root()
        bango_project_root = resolve_bango_project_root()
        idloadint_dir = resolve_idloadint_dir(asset_root)
        bangonow_summary_path = asset_root / 'generated' / 'bangonow' / 'bangonow_run_summary.json'
        bangonow_package_path = asset_root / 'generated' / 'bangonow' / 'playable_package' / 'bangonow_playable_package.json'
        tutorial_spec = load_json(idloadint_dir / 'tutorial_demo_spec.json')
        hybrid_runtime = load_json(HYBRID_RUNTIME_PATH)
        playnow_runtime = load_json(resolve_playnow_runtime_path(asset_root))
        playnow_finalstage = load_json(resolve_playnow_finalstage_path(asset_root))
        bangonow_showcase = load_json(BANGONOW_SHOWCASE_PATH)
        prompt_count = len(tutorial_spec.get('prompts', [])) if isinstance(tutorial_spec, dict) else 0
        wave_count = len(tutorial_spec.get('waves', [])) if isinstance(tutorial_spec, dict) else 0
        tick_gnosis = build_tick_gnosis_frame(
            'dodogame-hybrid-launcher',
            tick=prompt_count + wave_count,
            frame_delta_ms=16.667,
            entity_count=max(1, prompt_count + wave_count + 1),
            energy_total=float(prompt_count * 12 + wave_count * 18),
            camera_motion=0.24,
            input_pressure=0.38,
            recursion_depth=2.3,
        )
        state = {
            'asset_root': str(asset_root),
            'theme': load_json(DODO_THEME_PATH),
            'hybrid_runtime': hybrid_runtime,
            'dodogame_windows_bundle': load_json(DODO_WINDOWS_BUNDLE_MANIFEST_PATH),
            'manifest_summary': load_json(DODO_MANIFEST_SUMMARY_PATH),
            'playnow_runtime': playnow_runtime,
            'playnow_finalstage': playnow_finalstage,
            'tutorial_sim': load_json(asset_root / 'generated' / 'playnow' / 'tutorial_completion_simulation.json'),
            'tutorial_spec': tutorial_spec,
            'bango_project_root': str(bango_project_root),
            'tick_gnosis': tick_gnosis,
            'orb_bango_demo': {'path': str(ORB_BANGO_DEMO_PATH), 'exists': ORB_BANGO_DEMO_PATH.exists()},
            'bangonow_showcase': bangonow_showcase,
            'bangonow_summary': load_json(bangonow_summary_path),
            'bangonow_package': load_json(bangonow_package_path),
            'pipeline_verification': load_json(BANGO_PIPELINE_VERIFY_PATH),
        }
        state['pipeline_overview'] = build_bango_pipeline_overview(state)
        state['pass_records'] = build_pass_records(state)
        return state

    def load_font_renderers(self) -> dict[str, BitmapFontRenderer]:
        theme = load_json(DODO_THEME_PATH)
        if not isinstance(theme, dict):
            return {}
        fonts = theme.get('fonts', {})
        renderers: dict[str, BitmapFontRenderer] = {}
        for name, json_path in fonts.items():
            path = Path(json_path)
            if not path.is_absolute():
                path = ROOT / json_path
            renderers[name] = BitmapFontRenderer(path)
        return renderers

    def _build_header(self) -> None:
        self.header = tk.Canvas(self.master, height=132, bg='#182019', highlightthickness=0)
        self.header.pack(fill='x', padx=16, pady=(16, 8))
        self.header.create_rectangle(8, 10, 1296, 124, fill='#263126', outline='#c39b65', width=3)
        self._render_header_splash()
        self.header.create_rectangle(22, 18, 448, 114, fill='#101511', outline='#d2b07c', width=2)
        self.header.create_text(46, 96, text='Integrated Bango title surface with launch, runtime, and pipeline state in one front-door view.', fill='#cbd5c7', anchor='w', font=('Segoe UI', 10))
        self._render_header_fonts()

    def _render_header_splash(self) -> None:
        theme = self.state.get('theme') if isinstance(self.state, dict) else None
        splash_path = self._resolve_theme_path(theme.get('splash')) if isinstance(theme, dict) else None
        if Image is not None and ImageTk is not None and splash_path is not None and splash_path.exists():
            splash = Image.open(splash_path).convert('RGBA')
            splash = splash.resize((1288, 114), Image.Resampling.LANCZOS)
            overlay = Image.new('RGBA', splash.size, (9, 12, 9, 58))
            splash = Image.alpha_composite(splash, overlay)
            photo = ImageTk.PhotoImage(splash)
            self.images['header_splash'] = photo
            self.header.create_image(10, 10, image=photo, anchor='nw')
            return
        self.header.create_rectangle(10, 12, 1294, 122, fill='#2a3429', outline='')

    def _render_header_fonts(self) -> None:
        stone = self.font_renderers.get('stone')
        bone = self.font_renderers.get('bone')
        if stone:
            image = stone.render_text('DODOGAME', scale=2)
            if image is not None:
                self.images['stone_header'] = image
                self.header.create_image(44, 26, image=image, anchor='nw')
        else:
            self.header.create_text(44, 34, text='DODOGame', fill='#f7edd4', anchor='w', font=('Segoe UI', 30, 'bold'))
        if bone:
            image = bone.render_text('BANGO AND PATOOT TITLE HERO', scale=1)
            if image is not None:
                self.images['bone_subtitle'] = image
                self.header.create_image(46, 66, image=image, anchor='nw')
        else:
            self.header.create_text(46, 72, text='Bango: Unchained - Bango&Patoot', fill='#d8c39d', anchor='w', font=('Segoe UI', 12, 'bold'))

    def _build_controls(self) -> None:
        controls = tk.Frame(self.master, bg='#182019')
        controls.pack(fill='x', padx=16, pady=(0, 8))
        buttons = [
            ('Title', self.show_title_tab),
            ('Menu Back', self.title_menu_back),
            ('Refresh', self.refresh_state),
        ]
        for label, callback in buttons:
            tk.Button(controls, text=label, command=callback, bg='#334330', fg='#f7edd4', activebackground='#476245', relief='flat', padx=12, pady=8).pack(side='left', padx=(0, 8))
        tk.Label(controls, textvariable=self.status_var, bg='#182019', fg='#9dd49f', font=('Segoe UI', 10)).pack(side='left', padx=12)
        tk.Label(controls, textvariable=self.controller_var, bg='#182019', fg='#d8c39d', font=('Segoe UI', 10)).pack(side='right')

    def _build_tabs(self) -> None:
        style = ttk.Style(self.master)
        style.layout('Tabless.TNotebook.Tab', [])
        notebook = ttk.Notebook(self.master, style='Tabless.TNotebook')
        self.notebook = notebook
        notebook.pack(fill='both', expand=True, padx=16, pady=(0, 16))
        self._add_title_surface_tab(notebook, 'Title')
        self.overview_text = self._add_text_tab(notebook, 'Pipeline Overview')
        self.verify_text = self._add_text_tab(notebook, 'Pipeline Verify')
        self._add_passes_tab(notebook, 'Pass Cards')
        self.runtime_text = self._add_text_tab(notebook, 'Hybrid Runtime')
        self._add_viewport_tab(notebook, 'Illusion 3D')
        self.showcase_text = self._add_text_tab(notebook, 'BangoNOW Showcase')
        self.playnow_text = self._add_text_tab(notebook, 'PlayNOW')
        self.tutorial_text = self._add_text_tab(notebook, 'Tutorial Sim')
        self.controller_text = self._add_text_tab(notebook, 'Controller')
        self.visual_assets_frame = self._add_asset_tab(notebook, 'Visual Assets', VISUAL_ASSET_SPECS)
        self.input_assets_frame = self._add_asset_tab(notebook, 'Input Assets', INPUT_ASSET_SPECS)
        self.credits_text = self._add_text_tab(notebook, 'Credits')

    def _add_viewport_tab(self, notebook: ttk.Notebook, label: str) -> None:
        frame = tk.Frame(notebook, bg='#111611')
        self.viewport_tab = frame
        self.tab_frames[label] = frame
        notebook.add(frame, text=label)
        frame.grid_columnconfigure(0, weight=3)
        frame.grid_columnconfigure(1, weight=2)
        frame.grid_rowconfigure(0, weight=1)

        viewport_card = tk.Frame(frame, bg='#192019', highlightbackground='#4b5c49', highlightthickness=1)
        viewport_card.grid(row=0, column=0, sticky='nsew', padx=(8, 4), pady=8)
        tk.Label(viewport_card, text='DODO 3D Shader Viewport', bg='#192019', fg='#f7edd4', anchor='w', font=('Segoe UI', 10, 'bold')).pack(fill='x', padx=8, pady=(8, 4))
        self.viewport_image_label = tk.Label(viewport_card, bg='#0f140f', text='Renderer unavailable', fg='#d8c39d')
        self.viewport_image_label.pack(fill='both', expand=True, padx=8, pady=(4, 8))

        controls = tk.Frame(frame, bg='#192019', highlightbackground='#4b5c49', highlightthickness=1)
        controls.grid(row=0, column=1, sticky='nsew', padx=(4, 8), pady=8)
        tk.Label(controls, text='Viewport Controls', bg='#192019', fg='#f7edd4', anchor='w', font=('Segoe UI', 10, 'bold')).pack(fill='x', padx=8, pady=(8, 6))
        self._add_scale(controls, 'Orbit', self.viewport_orbit_var, 0.0, 6.28)
        self._add_scale(controls, 'Elevation', self.viewport_elevation_var, -0.3, 0.7)
        self._add_scale(controls, 'Shader Mix', self.viewport_shader_var, 0.2, 1.0)
        button_row = tk.Frame(controls, bg='#192019')
        button_row.pack(fill='x', padx=8, pady=(6, 8))
        tk.Button(button_row, text='Render Now', command=lambda: self._refresh_viewport(force=True), bg='#334330', fg='#f7edd4', relief='flat', padx=10, pady=6).pack(side='left', padx=(0, 8))
        tk.Button(button_row, text='Pause/Run', command=self.toggle_viewport_animation, bg='#334330', fg='#f7edd4', relief='flat', padx=10, pady=6).pack(side='left', padx=(0, 8))
        tk.Button(button_row, text='Export PNG', command=self.export_viewport_preview, bg='#334330', fg='#f7edd4', relief='flat', padx=10, pady=6).pack(side='left')
        self.viewport_stats_text = tk.Text(controls, wrap='word', bg='#111611', fg='#dce7da', insertbackground='#dce7da', relief='flat', height=18, font=('Cascadia Mono', 9))
        self.viewport_stats_text.pack(fill='both', expand=True, padx=8, pady=(0, 8))

    def _add_scale(self, parent: tk.Widget, label: str, variable: tk.DoubleVar, minimum: float, maximum: float) -> None:
        tk.Label(parent, text=label, bg='#192019', fg='#d8c39d', anchor='w', font=('Segoe UI', 9)).pack(fill='x', padx=8)
        tk.Scale(parent, variable=variable, from_=minimum, to=maximum, resolution=0.01, orient='horizontal', bg='#192019', fg='#dce7da', troughcolor='#314031', highlightthickness=0, command=lambda _value: self._refresh_viewport(force=True)).pack(fill='x', padx=8, pady=(0, 4))

    def _add_text_tab(self, notebook: ttk.Notebook, label: str) -> tk.Text:
        frame = tk.Frame(notebook, bg='#111611')
        self.tab_frames[label] = frame
        notebook.add(frame, text=label)
        text = tk.Text(frame, wrap='word', bg='#111611', fg='#dce7da', insertbackground='#dce7da', relief='flat', font=('Cascadia Mono', 10))
        text.pack(fill='both', expand=True)
        return text

    def _add_passes_tab(self, notebook: ttk.Notebook, label: str) -> None:
        frame = tk.Frame(notebook, bg='#111611')
        self.tab_frames[label] = frame
        notebook.add(frame, text=label)
        toolbar = tk.Frame(frame, bg='#111611')
        toolbar.pack(fill='x', padx=8, pady=(8, 4))
        tk.Label(toolbar, text='Pass Controls', bg='#111611', fg='#f7edd4', font=('Segoe UI', 10, 'bold')).pack(side='left')
        self.pass_cards_frame = tk.Frame(frame, bg='#111611')
        self.pass_cards_frame.pack(fill='x', padx=8, pady=(0, 6))
        self.pass_detail_text = tk.Text(frame, wrap='word', bg='#111611', fg='#dce7da', insertbackground='#dce7da', relief='flat', font=('Cascadia Mono', 10))
        self.pass_detail_text.pack(fill='both', expand=True, padx=8, pady=(0, 8))

    def _add_title_surface_tab(self, notebook: ttk.Notebook, label: str) -> None:
        frame = tk.Frame(notebook, bg='#111611')
        self.title_tab = frame
        self.tab_frames[label] = frame
        notebook.add(frame, text=label)
        frame.grid_columnconfigure(0, weight=5)
        frame.grid_columnconfigure(1, weight=3)
        frame.grid_rowconfigure(0, weight=4)
        frame.grid_rowconfigure(1, weight=3)

        image_card = tk.Frame(frame, bg='#192019', highlightbackground='#4b5c49', highlightthickness=1)
        image_card.grid(row=0, column=0, rowspan=2, sticky='nsew', padx=(8, 4), pady=8)
        tk.Label(image_card, text='Bango Title Surface', bg='#192019', fg='#f7edd4', anchor='w', font=('Segoe UI', 11, 'bold')).pack(fill='x', padx=10, pady=(10, 4))
        self.title_hero_image_label = tk.Label(image_card, bg='#0f140f', text='Title splash unavailable', fg='#d8c39d')
        self.title_hero_image_label.pack(fill='both', expand=True, padx=10, pady=(4, 10))

        action_card = tk.Frame(frame, bg='#192019', highlightbackground='#4b5c49', highlightthickness=1)
        action_card.grid(row=0, column=1, sticky='nsew', padx=(4, 8), pady=(8, 4))
        tk.Label(action_card, text='Menu', bg='#192019', fg='#f7edd4', anchor='w', font=('Segoe UI', 11, 'bold')).pack(fill='x', padx=10, pady=(10, 6))
        self.title_menu_heading = tk.Label(action_card, text='Title Screen', bg='#192019', fg='#f7edd4', anchor='w', font=('Segoe UI', 13, 'bold'))
        self.title_menu_heading.pack(fill='x', padx=10, pady=(0, 2))
        self.title_menu_subheading = tk.Label(action_card, text='Three doors only. Pick a path and descend.', bg='#192019', fg='#d8c39d', anchor='w', justify='left', wraplength=360, font=('Segoe UI', 9))
        self.title_menu_subheading.pack(fill='x', padx=10, pady=(0, 6))
        nav_row = tk.Frame(action_card, bg='#192019')
        nav_row.pack(fill='x', padx=10, pady=(0, 6))
        tk.Button(nav_row, text='Back', command=self.title_menu_back, bg='#2a3328', fg='#f7edd4', activebackground='#476245', relief='flat', padx=10, pady=6).pack(side='left', padx=(0, 6))
        tk.Button(nav_row, text='Home', command=self.title_menu_home, bg='#2a3328', fg='#f7edd4', activebackground='#476245', relief='flat', padx=10, pady=6).pack(side='left')
        self.title_menu_frame = tk.Frame(action_card, bg='#192019')
        self.title_menu_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        self.title_menu_info = tk.Label(action_card, text='', bg='#192019', fg='#b9c8b7', anchor='w', justify='left', wraplength=360, font=('Segoe UI', 9))
        self.title_menu_info.pack(fill='x', padx=10, pady=(0, 10))
        self._render_title_menu()

        detail_card = tk.Frame(frame, bg='#192019', highlightbackground='#4b5c49', highlightthickness=1)
        detail_card.grid(row=1, column=1, sticky='nsew', padx=(4, 8), pady=(4, 8))
        tk.Label(detail_card, text='Scene Pulse', bg='#192019', fg='#f7edd4', anchor='w', font=('Segoe UI', 11, 'bold')).pack(fill='x', padx=10, pady=(10, 4))
        self.title_status_label = tk.Label(detail_card, bg='#111611', fg='#dce7da', anchor='nw', justify='left', wraplength=332, padx=10, pady=10, font=('Segoe UI', 9))
        self.title_status_label.pack(fill='x', padx=10, pady=(0, 8))
        tk.Label(detail_card, text='Mood Read', bg='#192019', fg='#f7edd4', anchor='w', font=('Segoe UI', 11, 'bold')).pack(fill='x', padx=10, pady=(0, 4))
        self.title_flavor_label = tk.Label(detail_card, bg='#111611', fg='#d8c39d', anchor='nw', justify='left', wraplength=332, padx=10, pady=10, font=('Segoe UI', 9))
        self.title_flavor_label.pack(fill='both', expand=True, padx=10, pady=(0, 10))

    def _add_asset_tab(self, notebook: ttk.Notebook, label: str, specs: list[tuple[str, str, tuple[int, int]]]) -> tk.Frame:
        frame = tk.Frame(notebook, bg='#111611')
        self.tab_frames[label] = frame
        notebook.add(frame, text=label)
        columns = 3
        for column in range(columns):
            frame.grid_columnconfigure(column, weight=1)
        for index, (asset_key, title, _) in enumerate(specs):
            card = tk.Frame(frame, bg='#192019', highlightbackground='#4b5c49', highlightthickness=1)
            card.grid(row=index // columns, column=index % columns, sticky='nsew', padx=8, pady=8)
            heading = tk.Label(card, text=title, bg='#192019', fg='#f7edd4', anchor='w', font=('Segoe UI', 10, 'bold'))
            heading.pack(fill='x', padx=8, pady=(8, 4))
            image_label = tk.Label(card, bg='#0f140f', width=40, height=12)
            image_label.pack(fill='both', expand=True, padx=8, pady=4)
            caption = tk.Label(card, text=asset_key, bg='#192019', fg='#b9c8b7', wraplength=280, justify='left', anchor='w', font=('Segoe UI', 8))
            caption.pack(fill='x', padx=8, pady=(2, 8))
            self.asset_preview_labels[asset_key] = (image_label, caption)
        return frame

    def _write_text(self, widget: tk.Text, payload: object) -> None:
        widget.delete('1.0', 'end')
        widget.insert('1.0', json.dumps(payload, indent=2))

    def refresh_views(self) -> None:
        self._refresh_title_surface()
        self._write_text(self.overview_text, self.state.get('pipeline_overview') or {'status': 'missing'})
        self._write_text(self.verify_text, self.state.get('pipeline_verification') or {'status': 'missing'})
        self._write_text(self.runtime_text, self.state.get('hybrid_runtime') or {'status': 'missing'})
        self._write_text(self.showcase_text, self.state.get('bangonow_showcase') or {'status': 'missing'})
        self._write_text(self.playnow_text, self.state.get('playnow_runtime') or {'status': 'missing'})
        self._write_text(self.tutorial_text, self.state.get('tutorial_sim') or {'status': 'missing', 'tutorial_spec': self.state.get('tutorial_spec')})
        credits_payload = {
            'dodogame_gui_manifest_summary': self.state.get('manifest_summary') or {'status': 'missing'},
            'playnow_finalstage': self.state.get('playnow_finalstage') or {'status': 'missing'},
            'dodogame_windows_bundle': self.state.get('dodogame_windows_bundle') or {'status': 'missing'},
            'bangonow_package': self.state.get('bangonow_package') or {'status': 'missing'},
            'tick_gnosis': self.state.get('tick_gnosis') or {'status': 'missing'},
            'orb_bango_demo': self.state.get('orb_bango_demo') or {'status': 'missing'},
            'credit_execution_note': 'Live Recraft execution is available through the shared runner and still requires RECRAFT_API_KEY in the active environment.',
        }
        self._write_text(self.credits_text, credits_payload)
        self._refresh_pass_cards()
        self._refresh_asset_previews()
        self._refresh_viewport(force=True)

    def _refresh_title_surface(self) -> None:
        if self.title_hero_image_label is None:
            return
        theme = self.state.get('theme') if isinstance(self.state, dict) else None
        splash_path = self._resolve_theme_path(theme.get('splash')) if isinstance(theme, dict) else None
        splash_metadata = load_json(splash_path.with_suffix('.json')) if splash_path is not None and splash_path.exists() else None
        glb_preview_path = None
        if isinstance(splash_metadata, dict) and splash_metadata.get('glb_preview'):
            glb_preview_path = resolve_existing_path(splash_metadata.get('glb_preview'))
        if glb_preview_path is None and DODO_TITLE_GLB_PREVIEW_PATH.exists():
            glb_preview_path = DODO_TITLE_GLB_PREVIEW_PATH
        showcase = self.state.get('bangonow_showcase') if isinstance(self.state.get('bangonow_showcase'), dict) else {}
        pipeline = self.state.get('pipeline_overview') if isinstance(self.state.get('pipeline_overview'), dict) else {}
        verification = self.state.get('pipeline_verification') if isinstance(self.state.get('pipeline_verification'), dict) else {}
        hybrid_runtime = self.state.get('hybrid_runtime') if isinstance(self.state.get('hybrid_runtime'), dict) else {}
        preview_report = load_json(DODO_ENGINE_PREVIEW_PATH.with_suffix('.json'))
        preview_stats = preview_report.get('stats', {}) if isinstance(preview_report, dict) else {}
        runtime_state = preview_stats.get('runtime_state', {}) if isinstance(preview_stats, dict) else {}
        runtime_payload = {
            'title_surface': 'integrated',
            'scene_name': showcase.get('showcase_name'),
            'scene_entries': len(showcase.get('scene_entries', [])) if isinstance(showcase.get('scene_entries'), list) else 0,
            'pipeline_status': verification.get('overall_status', 'unknown'),
            'requested_passes': showcase.get('pipeline', {}).get('requested_passes', []) if isinstance(showcase.get('pipeline'), dict) else [],
            'runtime_state': runtime_state or {'status': 'preview not generated yet'},
            'runtime_contract': {
                'label': hybrid_runtime.get('label'),
                'renderer_backend': hybrid_runtime.get('renderer_backend'),
                'runtime_scene_version': hybrid_runtime.get('concept_art_translation', {}).get('runtime_scene_version') if isinstance(hybrid_runtime.get('concept_art_translation'), dict) else None,
            },
            'overview': pipeline.get('showcase', {}) if isinstance(pipeline.get('showcase'), dict) else {},
        }
        self._refresh_title_live_frame(runtime_payload, splash_path, glb_preview_path, splash_metadata)
        if self.title_status_label is not None:
            active_threshold = runtime_state.get('active_threshold') or 'hushfall_hum'
            self.title_status_label.configure(text=f"Scene: {runtime_payload.get('scene_name') or 'title tableau'}\nThreshold: {active_threshold}\nBango gesture: {self.title_gesture_state.get('bango', 'idle watch')}\nPatoot gesture: {self.title_gesture_state.get('patoot', 'idle amuse')}\nRenderer: {runtime_payload.get('runtime_contract', {}).get('renderer_backend') or 'DODO'}")
        if self.title_flavor_label is not None:
            character_direction = splash_metadata.get('character_direction', {}) if isinstance(splash_metadata, dict) else {}
            bango_direction = character_direction.get('bango', 'concept basis') if isinstance(character_direction, dict) else 'concept basis'
            patoot_direction = character_direction.get('patoot', 'companion basis') if isinstance(character_direction, dict) else 'companion basis'
            trigger_line = f"LT {int(self.title_trigger_state.get('bango_trigger', 0.0) * 100):02d}% drives Bango arm-leg lurches | RT {int(self.title_trigger_state.get('patoot_trigger', 0.0) * 100):02d}% drives Patoot assist flares"
            self.title_flavor_label.configure(text=f"Bango: {bango_direction}.\nPatoot: {patoot_direction}.\nScore direction: ritual percussion, industrial drone, broken choir, reed tones, hive hum.\n{trigger_line}")
        self._render_title_menu()

    def _refresh_title_live_frame(self, runtime_payload: dict, splash_path: Path | None, glb_preview_path: Path | None, splash_metadata: dict | None) -> None:
        if self.title_hero_image_label is None:
            return
        frame = None
        if self.title_engine is not None and ImageTk is not None and Image is not None:
            self.title_engine.set_runtime_overrides(self.title_trigger_state)
            profile = self._current_title_scene_profile()
            orbit = float(profile['orbit']) + math.sin(self.title_scene_time * 0.14) * float(profile['motion_orbit'])
            elevation = float(profile['elevation']) + math.sin(self.title_scene_time * 0.09) * float(profile['motion_elevation'])
            image, stats = self.title_engine.render_preview(orbit=orbit, elevation=elevation, shader_mix=float(profile['shader_mix']), time_s=self.title_scene_time)
            frame = self._compose_title_overlay_image(image, stats)
        if frame is None:
            preview_path = glb_preview_path or splash_path
            preview = self._load_preview_image(preview_path, (920, 520), 'title_hero') if preview_path is not None else None
            if preview is not None:
                self.title_hero_image_label.configure(image=preview, text='')
            else:
                self.title_hero_image_label.configure(image='', text='Title splash unavailable', fg='#d8c39d')
            return
        photo = ImageTk.PhotoImage(frame)
        self.images['title_live_scene'] = photo
        self.title_hero_image_label.configure(image=photo, text='')

    def _compose_title_overlay_image(self, image, stats: dict):
        if Image is None or ImageDraw is None:
            return image
        theme = self._current_title_theme()
        composed = image.convert('RGBA')
        overlay = Image.new('RGBA', composed.size, theme['overlay'])
        composed = Image.alpha_composite(composed, overlay)
        draw = ImageDraw.Draw(composed, 'RGBA')
        title_font = load_display_font(44, bold=True)
        subtitle_font = load_display_font(18, bold=False)
        meta_font = load_display_font(16, bold=False)
        accent = theme['accent']
        mist_top = composed.height - 168
        draw.polygon(((0, composed.height), (0, mist_top + 24), (210, mist_top - 6), (472, mist_top + 18), (760, mist_top - 22), (composed.width, mist_top + 16), (composed.width, composed.height)), fill=(12, 18, 15, 84))
        draw.line((44, mist_top - 12, 316, mist_top - 12), fill=accent, width=3)
        draw.text((52, mist_top - 96), 'UNDERHIVE NOCTURNE', fill=theme['muted'], font=subtitle_font)
        draw.text((48, mist_top - 52), 'BANGO: UNCHAINED', fill=(26, 18, 12, 140), font=title_font, stroke_width=6, stroke_fill=(26, 18, 12, 140))
        draw.text((48, mist_top - 52), 'BANGO: UNCHAINED', fill='#f7edd4', font=title_font, stroke_width=2, stroke_fill=accent)
        draw.text((54, mist_top + 10), 'tutorial yard vigil / fur-feather-fluid proxy / drifting drones', fill='#f2d7a6', font=meta_font)
        draw.text((54, mist_top + 34), f"route {self.title_transition_note}  |  faces {stats.get('faces_drawn', 0)}  |  scripted {stats.get('scripted_entries', 0)}", fill=theme['muted'], font=meta_font)
        if self.title_transition_phase > 0.0:
            veil = int(180 * min(1.0, self.title_transition_phase))
            bar = int((composed.width * 0.5) * min(1.0, self.title_transition_phase))
            draw.rectangle((0, 0, bar, composed.height), fill=(6, 9, 8, veil))
            draw.rectangle((composed.width - bar, 0, composed.width, composed.height), fill=(6, 9, 8, veil))
            draw.line((bar + 8, 0, bar + 8, composed.height), fill=accent, width=3)
            draw.line((composed.width - bar - 8, 0, composed.width - bar - 8, composed.height), fill=accent, width=3)
        return composed

    def _get_title_menu_node(self, node_id: str | None = None) -> dict[str, object]:
        node_key = node_id or (self.title_menu_stack[-1] if self.title_menu_stack else 'root')
        node = TITLE_MENU_NODES.get(node_key)
        return node if isinstance(node, dict) else TITLE_MENU_NODES['root']

    def _current_title_theme(self) -> dict[str, object]:
        node = self._get_title_menu_node()
        theme_key = str(node.get('theme', 'root'))
        return TITLE_BRANCH_THEMES.get(theme_key, TITLE_BRANCH_THEMES['root'])

    def _current_title_scene_profile(self) -> dict[str, object]:
        node = self._get_title_menu_node()
        theme_key = str(node.get('theme', 'root'))
        return TITLE_SCENE_PROFILES.get(theme_key, TITLE_SCENE_PROFILES['root'])

    def _trigger_title_transition(self, note: str) -> None:
        self.title_transition_phase = 1.0
        self.title_transition_note = note

    def _render_title_menu(self) -> None:
        if self.title_menu_frame is None or self.title_menu_heading is None or self.title_menu_subheading is None or self.title_menu_info is None:
            return
        for child in self.title_menu_frame.winfo_children():
            child.destroy()
        self.title_menu_buttons = []
        node = self._get_title_menu_node()
        theme = self._current_title_theme()
        self.title_menu_heading.configure(text=str(node.get('title', 'Title Screen')))
        self.title_menu_heading.configure(fg=theme['text'])
        self.title_menu_subheading.configure(text=str(node.get('subtitle', '')))
        self.title_menu_subheading.configure(fg=theme['muted'])
        options = node.get('options', []) if isinstance(node.get('options'), list) else []
        self.title_menu_selected_index = min(self.title_menu_selected_index, max(0, len(options[:3]) - 1))
        for index, option in enumerate(options[:3]):
            if not isinstance(option, dict):
                continue
            text_block = str(option.get('label', 'Option'))
            description = str(option.get('description', ''))
            button = tk.Button(
                self.title_menu_frame,
                text=f'{text_block}\n{description}' if description else text_block,
                command=lambda option_index=index, payload=option: self._select_and_activate_title_option(option_index, payload),
                bg='#232c22',
                fg=theme['text'],
                activebackground='#476245',
                relief='flat',
                padx=12,
                pady=10,
                anchor='w',
                justify='left',
                wraplength=320,
            )
            button.bind('<Enter>', lambda _event, option_index=index: self._set_title_selection(option_index))
            button.pack(fill='x', pady=4)
            self.title_menu_buttons.append(button)
        breadcrumb = ' > '.join(str(TITLE_MENU_NODES.get(node_id, {}).get('title', node_id)).upper() for node_id in self.title_menu_stack)
        summary = str(node.get('summary', ''))
        self.title_menu_info.configure(text=f'{breadcrumb}\n\n{summary}')
        self.title_menu_info.configure(fg=theme['muted'])
        self._update_title_menu_focus()

    def _set_title_selection(self, index: int) -> None:
        self.title_menu_selected_index = index
        self._update_title_menu_focus()

    def _title_menu_move(self, delta: int) -> None:
        if not self._is_title_active() or not self.title_menu_buttons:
            return
        self.title_menu_selected_index = (self.title_menu_selected_index + delta) % len(self.title_menu_buttons)
        self._update_title_menu_focus()

    def _update_title_menu_focus(self) -> None:
        theme = self._current_title_theme()
        pulse = 0.65 + (math.sin(self.title_scene_time * 2.1) + 1.0) * 0.175
        for index, button in enumerate(self.title_menu_buttons):
            if index == self.title_menu_selected_index:
                button.configure(bg=theme['accent'], fg='#111611', activebackground=theme['accent'], activeforeground='#111611')
            else:
                dim_bg = '#223126' if pulse < 0.8 else '#26372a'
                button.configure(bg=dim_bg, fg=theme['text'], activebackground=theme['accent'], activeforeground='#111611')

    def _select_and_activate_title_option(self, index: int, option: dict[str, object]) -> None:
        self._set_title_selection(index)
        self._activate_title_menu_option(option)

    def _activate_selected_title_option(self) -> None:
        if not self._is_title_active():
            return
        options = self._get_title_menu_node().get('options', [])
        if not isinstance(options, list) or not options:
            return
        option = options[min(self.title_menu_selected_index, len(options) - 1)]
        if isinstance(option, dict):
            self._activate_title_menu_option(option)

    def _activate_title_menu_option(self, option: dict[str, object]) -> None:
        kind = str(option.get('kind', 'node'))
        target = option.get('target')
        if kind == 'node':
            self._push_title_menu_node(str(target))
            return
        if kind == 'tab':
            self.navigate_to_tab(str(target))
            return
        if kind == 'action':
            action_map = {
                'launch_bango_demo': self.launch_bango_demo,
                'run_tutorial_sim': self.run_tutorial_sim,
                'refresh_state': self.refresh_state,
                'title_menu_home': self.title_menu_home,
                'verify_pipeline': self.verify_pipeline,
                'build_bangonow_showcase': self.build_bangonow_showcase,
                'build_hybrid_runtime': self.build_hybrid_runtime,
            }
            callback = action_map.get(str(target))
            if callback is not None:
                callback()

    def _push_title_menu_node(self, node_id: str) -> None:
        if node_id not in TITLE_MENU_NODES:
            self.status_var.set(f'Menu node unavailable: {node_id}.')
            return
        self.title_menu_stack.append(node_id)
        self.title_menu_selected_index = 0
        target_title = str(TITLE_MENU_NODES[node_id].get('title', node_id))
        self._trigger_title_transition(target_title.lower())
        self._render_title_menu()
        self.status_var.set(f'Opened {target_title} menu.')

    def title_menu_back(self) -> None:
        if len(self.title_menu_stack) > 1:
            self.title_menu_stack.pop()
            parent_title = str(self._get_title_menu_node().get('title', 'parent room'))
            self._trigger_title_transition(f'back to {parent_title.lower()}')
            self._render_title_menu()
            self.status_var.set('Returned to parent menu.')
        else:
            self.show_title_tab()

    def title_menu_home(self) -> None:
        self.title_menu_stack = ['root']
        self.title_menu_selected_index = 0
        self._trigger_title_transition('threshold foyer')
        self._render_title_menu()
        self.status_var.set('Returned to title root menu.')

    def _is_title_active(self) -> bool:
        if self.notebook is None or self.title_tab is None:
            return False
        return self.notebook.select() == str(self.title_tab)

    def navigate_to_tab(self, label: str) -> None:
        frame = self.tab_frames.get(label)
        if frame is None or self.notebook is None:
            self.status_var.set(f'View unavailable: {label}.')
            return
        self.notebook.select(frame)
        self._sync_title_audio()
        self.status_var.set(f'Opened {label}.')

    def focus_viewport_tab(self) -> None:
        self.navigate_to_tab('Illusion 3D')
        self._refresh_viewport(force=True)
        self.status_var.set('Viewport tab focused.')

    def show_title_tab(self) -> None:
        self.title_menu_home()
        self.navigate_to_tab('Title')
        self.master.focus_set()

    def _refresh_pass_cards(self) -> None:
        if self.pass_cards_frame is None or self.pass_detail_text is None:
            return
        for child in self.pass_cards_frame.winfo_children():
            child.destroy()
        pass_records = self.state.get('pass_records', []) if isinstance(self.state.get('pass_records'), list) else []
        if not pass_records:
            tk.Label(self.pass_cards_frame, text='No PlayNOW passes available.', bg='#111611', fg='#d8c39d').pack(anchor='w')
            self._write_text(self.pass_detail_text, {'status': 'missing', 'reason': 'No pass records were derived from the current runtime state.'})
            return
        for record in pass_records:
            status = str(record.get('status', 'pass'))
            colors = {
                'pass': ('#314a34', '#9dd49f'),
                'warn': ('#5a4a24', '#f0d28a'),
                'fail': ('#5a2e2e', '#ef9a9a'),
            }
            bg, fg = colors.get(status, ('#314a34', '#dce7da'))
            card = tk.Frame(self.pass_cards_frame, bg='#192019', highlightbackground=bg, highlightthickness=2, width=212)
            card.pack(side='left', fill='y', padx=(0, 8), pady=4)
            card.pack_propagate(False)
            header = tk.Frame(card, bg='#192019')
            header.pack(fill='x', padx=8, pady=(8, 4))
            tk.Label(header, text=str(record.get('pass_label', 'pass')).upper(), bg='#192019', fg=fg, font=('Segoe UI', 8, 'bold')).pack(anchor='w')
            tk.Label(card, text=str(record.get('display_label', record.get('pass_label', 'pass'))), bg='#192019', fg='#f7edd4', wraplength=188, justify='left', anchor='w', font=('Segoe UI', 10, 'bold')).pack(anchor='w', padx=8)
            image_label = tk.Label(card, bg='#0f140f', width=188, height=104, relief='flat')
            image_label.pack(fill='x', padx=8, pady=(6, 6))
            preview_path = record.get('live_preview_image_path') or record.get('preview_image_path')
            preview = None
            if preview_path:
                preview = self._load_preview_image(Path(str(preview_path)), (188, 104), f"pass_card::{record.get('pass_label')}")
            if preview is not None:
                image_label.configure(image=preview, text='')
            else:
                image_label.configure(image='', text='No preview', fg='#c9b38b')
            thumb_row = tk.Frame(card, bg='#192019')
            thumb_row.pack(fill='x', padx=8, pady=(0, 6))
            thumbnail_paths = record.get('thumbnail_paths', []) if isinstance(record.get('thumbnail_paths'), list) else []
            for thumb_index, thumb_path in enumerate(thumbnail_paths[:3]):
                thumb_label = tk.Label(thumb_row, bg='#0f140f', width=56, height=32, relief='flat')
                thumb_label.pack(side='left', padx=(0 if thumb_index == 0 else 4, 0))
                thumb = self._load_preview_image(Path(str(thumb_path)), (56, 32), f"pass_thumb::{record.get('pass_label')}::{thumb_index}")
                if thumb is not None:
                    thumb_label.configure(image=thumb, text='')
                else:
                    thumb_label.configure(text='thumb', fg='#c9b38b')
            summary = tk.Frame(card, bg='#192019')
            summary.pack(fill='x', padx=8, pady=(0, 4))
            tk.Label(summary, text=f"assets {record.get('asset_count')}", bg='#192019', fg='#dce7da', font=('Segoe UI', 8)).pack(anchor='w')
            tk.Label(summary, text=f"gfx {'ready' if record.get('graphics_load_in_ready') else 'check'} | feature {'complete' if record.get('feature_complete') else 'partial'}", bg='#192019', fg=fg, font=('Segoe UI', 8)).pack(anchor='w')
            tk.Label(summary, text=f"scene entries {record.get('showcase_entry_count')}", bg='#192019', fg='#b9c8b7', font=('Segoe UI', 8)).pack(anchor='w')
            rebuild_report = record.get('rebuild_report') if isinstance(record.get('rebuild_report'), dict) else {}
            rebuild_status = rebuild_report.get('status') or 'not-run'
            rebuild_stamp = rebuild_report.get('completed_at') or 'pending'
            tk.Label(summary, text=f"rebuild {rebuild_status} | {rebuild_stamp}", bg='#192019', fg='#c9b38b', font=('Segoe UI', 8)).pack(anchor='w')
            row = tk.Frame(card, bg='#192019')
            row.pack(fill='x', padx=8, pady=(4, 8))
            tk.Button(row, text='Inspect', command=lambda label=record.get('pass_label'): self.inspect_pass(str(label), focus=False), bg='#334330', fg='#f7edd4', relief='flat', padx=8, pady=4).pack(side='left', padx=(0, 6))
            tk.Button(row, text='Focus', command=lambda label=record.get('pass_label'): self.inspect_pass(str(label), focus=True), bg='#415541', fg='#f7edd4', relief='flat', padx=8, pady=4).pack(side='left')
            tk.Button(card, text='Rebuild Selected Pass', command=lambda label=record.get('pass_label'): self.rebuild_pass(str(label)), bg='#6a4b2b', fg='#f7edd4', relief='flat', padx=8, pady=6).pack(fill='x', padx=8, pady=(0, 8))
        self.inspect_pass(str(pass_records[0].get('pass_label')), focus=False)

    def inspect_pass(self, pass_label: str, focus: bool = False) -> None:
        pass_records = self.state.get('pass_records', []) if isinstance(self.state.get('pass_records'), list) else []
        record = next((item for item in pass_records if item.get('pass_label') == pass_label), None)
        if self.pass_detail_text is not None:
            payload = record or {'status': 'missing', 'pass_label': pass_label}
            if record is not None:
                payload = dict(record)
                payload['rebuild_report'] = record.get('rebuild_report') or {'status': 'not-run'}
            self._write_text(self.pass_detail_text, payload)
        if focus and record is not None:
            orbit = float(record.get('focus_hint', {}).get('orbit', self.viewport_orbit_var.get()))
            self.viewport_orbit_var.set(orbit)
            self.viewport_elevation_var.set(0.2)
            self.viewport_shader_var.set(0.9)
            if self.notebook is not None and self.viewport_tab is not None:
                self.notebook.select(self.viewport_tab)
            self._refresh_viewport(force=True)
            self.status_var.set(f'Viewport focused toward {pass_label}.')

    def rebuild_pass(self, pass_label: str) -> None:
        command = [sys.executable, str(ROOT / 'tools' / 'rebuild_bango_pass.py'), '--pass-label', pass_label]
        self._run_tool(command, self.playnow_text, f'Bango pass {pass_label} rebuilt and launcher state refreshed.')

    def _resolve_theme_path(self, theme_value: str | None) -> Path | None:
        if not theme_value:
            return None
        path = Path(theme_value)
        if path.is_absolute():
            return path
        return ROOT / theme_value

    def _load_preview_image(self, path: Path, max_size: tuple[int, int], image_key: str):
        if Image is None or ImageTk is None or not path.exists():
            return None
        image = Image.open(path).convert('RGBA')
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        self.images[image_key] = photo
        return photo

    def _refresh_asset_previews(self) -> None:
        theme = self.state.get('theme')
        if not isinstance(theme, dict):
            return
        for asset_key, _, max_size in VISUAL_ASSET_SPECS + INPUT_ASSET_SPECS:
            widgets = self.asset_preview_labels.get(asset_key)
            if not widgets:
                continue
            image_label, caption = widgets
            asset_path = self._resolve_theme_path(theme.get(asset_key))
            if asset_path is None:
                image_label.configure(image='', text='Missing asset', fg='#c9b38b')
                caption.configure(text=f'{asset_key}\nmissing')
                continue
            preview = self._load_preview_image(asset_path, max_size, asset_key)
            if preview is not None:
                image_label.configure(image=preview, text='')
            else:
                image_label.configure(image='', text='Preview unavailable', fg='#c9b38b')
            caption.configure(text=f'{asset_key}\n{asset_path}')

    def refresh_state(self) -> None:
        self.state = self.collect_state()
        self.font_renderers = self.load_font_renderers()
        if self.engine is not None and BANGONOW_SHOWCASE_PATH.exists():
            self.engine.load_scene_manifest(BANGONOW_SHOWCASE_PATH)
        if self.title_engine is not None:
            title_scene = DODO_TITLE_SCENE_PATH if DODO_TITLE_SCENE_PATH.exists() else (BANGONOW_SHOWCASE_PATH if BANGONOW_SHOWCASE_PATH.exists() else None)
            if title_scene is not None:
                self.title_engine.load_scene_manifest(title_scene)
        self.header.destroy()
        self._build_header()
        self.refresh_views()
        self._sync_title_audio()
        self.status_var.set('DODOGame state refreshed.')

    def build_manifest(self) -> None:
        self._run_tool([sys.executable, str(ROOT / 'tools' / 'build_dodogame_gui_asset_manifest.py')], self.credits_text, 'DODOGame GUI manifest rebuilt.')

    def build_bangonow_showcase(self) -> None:
        self._run_tool([sys.executable, str(ROOT / 'tools' / 'build_bangonow_showcase.py')], self.showcase_text, 'BangoNOW showcase scene rebuilt.')

    def generate_assets(self) -> None:
        self._run_tool([sys.executable, str(ROOT / 'tools' / 'generate_dodogame_placeholder_assets.py')], self.runtime_text, 'Local DODOGame placeholder assets regenerated.')

    def run_recraft_pass(self) -> None:
        self._run_tool([sys.executable, str(ROOT / 'tools' / 'run_dodogame_recraft_pass.py')], self.credits_text, 'DODOGame live Recraft pass finished.')

    def build_hybrid_runtime(self) -> None:
        self._run_tool([sys.executable, str(ROOT / 'tools' / 'build_dodo_hybrid_runtime.py')], self.runtime_text, 'Hybrid runtime profile rebuilt.')

    def refresh_playnow(self) -> None:
        asset_root = resolve_bango_asset_root()
        bango_project_root = resolve_bango_project_root()
        command = [
            sys.executable,
            str(bango_project_root / 'tools' / 'run_playnow.py'),
            '--asset-root',
            str(asset_root),
            '--pass-label',
            'dodogame',
            '--skip-autorig',
        ]
        self._run_tool(command, self.playnow_text, 'PlayNOW runtime manifest refreshed for DODOGame.')

    def run_bangonow_batch(self) -> None:
        bango_project_root = resolve_bango_project_root()
        command = [sys.executable, str(bango_project_root / 'tools' / 'run_bangonow.py')]
        self._run_tool(command, self.playnow_text, 'BangoNOW batch orchestration completed.')

    def verify_pipeline(self) -> None:
        command = [sys.executable, str(ROOT / 'tools' / 'validate_bango_pipeline.py')]
        self._run_tool(command, self.verify_text, 'Bango pipeline verification refreshed.')

    def launch_bango_demo(self) -> None:
        if not ORB_BANGO_DEMO_PATH.exists():
            self.status_var.set('Bango tutorial demo executable is missing. Build ORBEngine first.')
            return
        subprocess.Popen([str(ORB_BANGO_DEMO_PATH)], cwd=str(ORB_BANGO_DEMO_PATH.parent))
        self.status_var.set('Launched Bango: Unchained - Bango&Patoot demo.')

    def run_tutorial_sim(self) -> None:
        bango_root = resolve_bango_project_root()
        command = [sys.executable, str(bango_root / 'tools' / 'simulate_bango_tutorial_completion.py')]
        self._run_tool(command, self.tutorial_text, 'Tutorial simulation completed.')

    def toggle_viewport_animation(self) -> None:
        self.viewport_running = not self.viewport_running
        self.status_var.set('DODO viewport animation running.' if self.viewport_running else 'DODO viewport animation paused.')
        if self.viewport_running:
            self._tick_viewport()

    def export_viewport_preview(self) -> None:
        if self.engine is None:
            self.status_var.set('DODO renderer unavailable. Pillow may be missing.')
            return
        payload = self.engine.write_preview(
            DODO_ENGINE_PREVIEW_PATH,
            orbit=float(self.viewport_orbit_var.get()),
            elevation=float(self.viewport_elevation_var.get()),
            shader_mix=float(self.viewport_shader_var.get()),
            time_s=self.viewport_time,
        )
        if self.viewport_stats_text is not None:
            self._write_text(self.viewport_stats_text, payload)
        self.status_var.set(f'DODO preview exported to {DODO_ENGINE_PREVIEW_PATH.name}.')

    def _refresh_viewport(self, force: bool = False) -> None:
        if self.viewport_image_label is None or self.viewport_stats_text is None:
            return
        if self.engine is None or ImageTk is None:
            payload = {
                'status': 'unavailable',
                'reason': 'Pillow or the DODO engine module could not be loaded.',
                'shader_manifest': DODO_SHADER_MANIFEST,
            }
            self._write_text(self.viewport_stats_text, payload)
            self.viewport_image_label.configure(image='', text='Renderer unavailable', fg='#d8c39d')
            return
        image, stats = self.engine.render_preview(
            orbit=float(self.viewport_orbit_var.get()),
            elevation=float(self.viewport_elevation_var.get()),
            shader_mix=float(self.viewport_shader_var.get()),
            time_s=self.viewport_time,
        )
        preview = ImageTk.PhotoImage(image)
        self.images['dodo_engine_viewport'] = preview
        self.viewport_image_label.configure(image=preview, text='')
        payload = {
            'stats': stats,
            'runtime': self.engine.describe_runtime(),
            'scene': self.state.get('bangonow_showcase') or {},
            'live_uniforms': {
                'orbit': round(float(self.viewport_orbit_var.get()), 3),
                'elevation': round(float(self.viewport_elevation_var.get()), 3),
                'shader_mix': round(float(self.viewport_shader_var.get()), 3),
                'time_s': round(self.viewport_time, 3),
            },
        }
        self._write_text(self.viewport_stats_text, payload)
        if force:
            self.status_var.set('DODO 3D viewport refreshed.')

    def _tick_viewport(self) -> None:
        if self.viewport_running:
            self.viewport_time += 0.08
            orbit = float(self.viewport_orbit_var.get()) + 0.015
            if orbit > 6.28:
                orbit -= 6.28
            self.viewport_orbit_var.set(orbit)
            self._refresh_viewport(force=False)
            self.master.after(80, self._tick_viewport)

    def _run_tool(self, command: list[str], widget: tk.Text, success_message: str) -> None:
        returncode, stdout, stderr = run_command(command)
        payload: object
        if stdout:
            try:
                payload = json.loads(stdout)
            except json.JSONDecodeError:
                payload = {'stdout': stdout, 'stderr': stderr, 'returncode': returncode}
        else:
            payload = {'stderr': stderr, 'returncode': returncode}
        self._write_text(widget, payload)
        self.refresh_state()
        self.status_var.set(success_message if returncode == 0 else f'Command failed with {returncode}.')

    def _poll_controller(self) -> None:
        snapshot = self.poller.poll()
        if snapshot.get('connected'):
            left_trigger = int(snapshot.get('left_trigger', 0)) if isinstance(snapshot.get('left_trigger'), int) else 0
            right_trigger = int(snapshot.get('right_trigger', 0)) if isinstance(snapshot.get('right_trigger'), int) else 0
            self._update_title_trigger_state(left_trigger, right_trigger)
            self.controller_var.set(f'Controller connected. LT {left_trigger:03d} | RT {right_trigger:03d}')
        else:
            self._update_title_trigger_state(0, 0)
            self.controller_var.set(snapshot.get('reason', 'Controller unavailable.'))
        if self._is_title_active() and snapshot.get('connected'):
            buttons = set(snapshot.get('buttons', [])) if isinstance(snapshot.get('buttons'), list) else set()
            pressed = buttons - self.title_last_buttons
            left_stick = snapshot.get('left_stick', {}) if isinstance(snapshot.get('left_stick'), dict) else {}
            left_y = int(left_stick.get('y', 0)) if isinstance(left_stick.get('y', 0), int) else 0
            if 'DPadUp' in pressed:
                self._title_menu_move(-1)
            if 'DPadDown' in pressed:
                self._title_menu_move(1)
            if left_y >= 18000:
                self._title_menu_move(-1)
            elif left_y <= -18000:
                self._title_menu_move(1)
            if 'A' in pressed or 'Start' in pressed:
                self._activate_selected_title_option()
            if 'B' in pressed or 'Back' in pressed:
                self.title_menu_back()
            if 'LB' in pressed:
                self.title_menu_back()
            if 'RB' in pressed:
                self.title_menu_home()
            self.title_last_buttons = buttons
        else:
            self.title_last_buttons = set()
        self._write_text(self.controller_text, snapshot)
        self.master.after(120, self._poll_controller)

    def _update_title_trigger_state(self, left_trigger: int, right_trigger: int) -> None:
        left_value = max(0.0, min(1.0, left_trigger / 255.0))
        right_value = max(0.0, min(1.0, right_trigger / 255.0))
        self.title_trigger_state = {
            'bango_trigger': round(left_value, 4),
            'patoot_trigger': round(right_value, 4),
        }
        self.title_gesture_state = {
            'bango': 'guardian flourish' if left_value >= 0.72 else ('curious shuffle' if left_value >= 0.2 else 'idle watch'),
            'patoot': 'crest flare' if right_value >= 0.72 else ('toe shuffle' if right_value >= 0.2 else 'idle amuse'),
        }

    def _tick_title_scene(self) -> None:
        self.title_scene_time += 0.08
        self.title_transition_phase = max(0.0, self.title_transition_phase - 0.08)
        if self._is_title_active():
            self._refresh_title_surface()
        else:
            self._update_title_menu_focus()
        self.master.after(90, self._tick_title_scene)

    def _sync_title_audio(self) -> None:
        if winsound is None:
            return
        theme = self.state.get('theme') if isinstance(self.state, dict) else None
        raw_path = theme.get('title_music') if isinstance(theme, dict) else None
        music_path = self._resolve_theme_path(raw_path) if raw_path else None
        if self._is_title_active() and music_path is not None and music_path.exists():
            if not self.title_music_active:
                winsound.PlaySound(str(music_path), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP | winsound.SND_NODEFAULT)
                self.title_music_active = True
        elif self.title_music_active:
            winsound.PlaySound(None, 0)
            self.title_music_active = False

    def _on_close(self) -> None:
        if winsound is not None and self.title_music_active:
            winsound.PlaySound(None, 0)
        self.master.destroy()


def main() -> int:
    parser = argparse.ArgumentParser(description='DODOGame hybrid launcher')
    parser.add_argument('--dump-state', action='store_true')
    parser.add_argument('--render-engine-preview', type=Path)
    parser.add_argument('--orbit', type=float)
    parser.add_argument('--elevation', type=float)
    parser.add_argument('--shader-mix', type=float)
    args = parser.parse_args()
    if args.render_engine_preview:
        if DodoPseudo3DEngine is None:
            print(json.dumps({'status': 'unavailable', 'reason': 'Pillow or dodo_engine3d import failure'}, indent=2))
            return 1
        showcase_path = BANGONOW_SHOWCASE_PATH if BANGONOW_SHOWCASE_PATH.exists() else None
        engine = DodoPseudo3DEngine(width=560, height=320, scene_manifest_path=showcase_path)
        preview_kwargs = {'scene_manifest_path': showcase_path}
        if args.orbit is not None:
            preview_kwargs['orbit'] = args.orbit
        if args.elevation is not None:
            preview_kwargs['elevation'] = args.elevation
        if args.shader_mix is not None:
            preview_kwargs['shader_mix'] = args.shader_mix
        payload = engine.write_preview(args.render_engine_preview, **preview_kwargs)
        print(json.dumps(payload, indent=2))
        return 0
    if args.dump_state:
        asset_root = resolve_bango_asset_root()
        idloadint_dir = resolve_idloadint_dir(asset_root)
        payload = {
            'theme': load_json(DODO_THEME_PATH),
            'hybrid_runtime': load_json(HYBRID_RUNTIME_PATH),
            'playnow_runtime': load_json(resolve_playnow_runtime_path(asset_root)),
            'playnow_finalstage': load_json(resolve_playnow_finalstage_path(asset_root)),
            'tutorial_sim': load_json(asset_root / 'generated' / 'playnow' / 'tutorial_completion_simulation.json'),
            'tutorial_spec': load_json(idloadint_dir / 'tutorial_demo_spec.json'),
            'bangonow_showcase': load_json(BANGONOW_SHOWCASE_PATH),
            'dodo_renderer': DodoPseudo3DEngine(width=560, height=320, scene_manifest_path=BANGONOW_SHOWCASE_PATH if BANGONOW_SHOWCASE_PATH.exists() else None).describe_runtime() if DodoPseudo3DEngine is not None else None,
        }
        print(json.dumps(payload, indent=2))
        return 0
    root = tk.Tk()
    ttk.Style().theme_use('default')
    DodoGameApp(root)
    root.mainloop()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
