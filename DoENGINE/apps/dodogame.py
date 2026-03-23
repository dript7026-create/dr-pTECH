from __future__ import annotations

import argparse
import ctypes
import importlib
import json
import subprocess
import sys
import tkinter as tk
from ctypes import wintypes
from pathlib import Path
from tkinter import ttk

try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None

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


def preview_cli_kwargs(args: argparse.Namespace, scene_manifest_path: Path | None) -> dict:
    return {
        'scene_manifest_path': scene_manifest_path,
        'orbit': float(args.orbit) if args.orbit is not None else 0.5,
        'elevation': float(args.elevation) if args.elevation is not None else 0.2,
        'shader_mix': float(args.shader_mix) if args.shader_mix is not None else 0.85,
    }


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
        self.asset_preview_labels: dict[str, tuple[tk.Label, tk.Label]] = {}
        self.font_renderers = self.load_font_renderers()
        showcase_path = BANGONOW_SHOWCASE_PATH if BANGONOW_SHOWCASE_PATH.exists() else None
        self.engine = DodoPseudo3DEngine(width=560, height=320, scene_manifest_path=showcase_path) if DodoPseudo3DEngine is not None else None
        self.viewport_image_label: tk.Label | None = None
        self.viewport_stats_text: tk.Text | None = None
        self.notebook: ttk.Notebook | None = None
        self.viewport_tab: tk.Frame | None = None
        self.pass_cards_frame: tk.Frame | None = None
        self.pass_detail_text: tk.Text | None = None
        self.viewport_orbit_var = tk.DoubleVar(value=0.58)
        self.viewport_elevation_var = tk.DoubleVar(value=0.22)
        self.viewport_shader_var = tk.DoubleVar(value=0.88)
        self.viewport_time = 0.0
        self.viewport_running = True

        self._build_header()
        self._build_controls()
        self._build_tabs()
        self.refresh_views()
        self._poll_controller()
        self._tick_viewport()

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
        self.header = tk.Canvas(self.master, height=154, bg='#182019', highlightthickness=0)
        self.header.pack(fill='x', padx=16, pady=(16, 8))
        self.header.create_rectangle(8, 10, 1296, 146, fill='#263126', outline='#c39b65', width=3)
        self.header.create_oval(24, 22, 154, 142, fill='#738560', outline='#f0d9a6', width=4)
        self.header.create_text(90, 82, text='DODO', fill='#f7edd4', font=('Segoe UI', 18, 'bold'))
        self.header.create_text(210, 112, text='Hybrid DoENGINE + ORBEngine launcher for Bango: Unchained - Bango&Patoot with TickGnosis-guided runtime telemetry.', fill='#cbd5c7', anchor='w', font=('Segoe UI', 11))
        self._render_header_fonts()

    def _render_header_fonts(self) -> None:
        stone = self.font_renderers.get('stone')
        bone = self.font_renderers.get('bone')
        if stone:
            image = stone.render_text('DODOGAME', scale=2)
            if image is not None:
                self.images['stone_header'] = image
                self.header.create_image(210, 34, image=image, anchor='nw')
                return
        self.header.create_text(210, 42, text='DODOGame', fill='#f7edd4', anchor='w', font=('Segoe UI', 30, 'bold'))
        if bone:
            image = bone.render_text('BANGO PAToot HYBRID', scale=1)
            if image is not None:
                self.images['bone_subtitle'] = image
                self.header.create_image(214, 82, image=image, anchor='nw')
                return
        self.header.create_text(214, 84, text='Bango: Unchained - Bango&Patoot', fill='#d8c39d', anchor='w', font=('Segoe UI', 12, 'bold'))

    def _build_controls(self) -> None:
        controls = tk.Frame(self.master, bg='#182019')
        controls.pack(fill='x', padx=16, pady=(0, 8))
        buttons = [
            ('Refresh', self.refresh_state),
            ('Launch Bango Demo', self.launch_bango_demo),
            ('Run BangoNOW Batch', self.run_bangonow_batch),
            ('Build DODO Manifest', self.build_manifest),
            ('Build BangoNOW Showcase', self.build_bangonow_showcase),
            ('Generate Assets', self.generate_assets),
            ('Run Recraft Pass', self.run_recraft_pass),
            ('Build Hybrid Runtime', self.build_hybrid_runtime),
            ('Refresh PlayNOW', self.refresh_playnow),
            ('Verify Pipeline', self.verify_pipeline),
            ('Run Tutorial Sim', self.run_tutorial_sim),
        ]
        for label, callback in buttons:
            tk.Button(controls, text=label, command=callback, bg='#334330', fg='#f7edd4', activebackground='#476245', relief='flat', padx=12, pady=8).pack(side='left', padx=(0, 8))
        tk.Label(controls, textvariable=self.status_var, bg='#182019', fg='#9dd49f', font=('Segoe UI', 10)).pack(side='left', padx=12)
        tk.Label(controls, textvariable=self.controller_var, bg='#182019', fg='#d8c39d', font=('Segoe UI', 10)).pack(side='right')

    def _build_tabs(self) -> None:
        notebook = ttk.Notebook(self.master)
        self.notebook = notebook
        notebook.pack(fill='both', expand=True, padx=16, pady=(0, 16))
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
        notebook.add(frame, text=label)
        text = tk.Text(frame, wrap='word', bg='#111611', fg='#dce7da', insertbackground='#dce7da', relief='flat', font=('Cascadia Mono', 10))
        text.pack(fill='both', expand=True)
        return text

    def _add_passes_tab(self, notebook: ttk.Notebook, label: str) -> None:
        frame = tk.Frame(notebook, bg='#111611')
        notebook.add(frame, text=label)
        toolbar = tk.Frame(frame, bg='#111611')
        toolbar.pack(fill='x', padx=8, pady=(8, 4))
        tk.Label(toolbar, text='Pass Controls', bg='#111611', fg='#f7edd4', font=('Segoe UI', 10, 'bold')).pack(side='left')
        self.pass_cards_frame = tk.Frame(frame, bg='#111611')
        self.pass_cards_frame.pack(fill='x', padx=8, pady=(0, 6))
        self.pass_detail_text = tk.Text(frame, wrap='word', bg='#111611', fg='#dce7da', insertbackground='#dce7da', relief='flat', font=('Cascadia Mono', 10))
        self.pass_detail_text.pack(fill='both', expand=True, padx=8, pady=(0, 8))

    def _add_asset_tab(self, notebook: ttk.Notebook, label: str, specs: list[tuple[str, str, tuple[int, int]]]) -> tk.Frame:
        frame = tk.Frame(notebook, bg='#111611')
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
        self.header.destroy()
        self._build_header()
        self.refresh_views()
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
            self.controller_var.set('Controller connected.')
        else:
            self.controller_var.set(snapshot.get('reason', 'Controller unavailable.'))
        self._write_text(self.controller_text, snapshot)
        self.master.after(120, self._poll_controller)


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
        preview_kwargs = preview_cli_kwargs(args, showcase_path)
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
