from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = ROOT.parent
OUTPUT_PATH = ROOT / 'generated' / 'dodogame_hybrid_runtime.json'
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

_bango_paths = importlib.import_module('bango_integration_paths')
resolve_bango_asset_root = _bango_paths.resolve_bango_asset_root
resolve_idloadint_dir = _bango_paths.resolve_idloadint_dir
resolve_playnow_dir = _bango_paths.resolve_playnow_dir
resolve_playnow_finalstage_path = _bango_paths.resolve_playnow_finalstage_path
resolve_playnow_runtime_path = _bango_paths.resolve_playnow_runtime_path
build_tick_gnosis_frame = importlib.import_module('tick_gnosis').build_tick_gnosis_frame


DODO_SHADER_PROGRAM = {
    'backend': 'python-pillow-cpu-raster',
    'look': 'illusioncanvas-pseudo3d',
    'asset_loaders': ['builtin', 'obj', 'glb', 'billboard', 'scene-manifest'],
    'script_capabilities': ['spin', 'bob', 'pulse', 'orbit'],
    'passes': [
        {'id': 'sky-dome-gradient', 'label': 'Sky Dome Gradient', 'role': 'Establish the amber-jade atmosphere before geometry is drawn.'},
        {'id': 'floor-warp-grid', 'label': 'Floor Warp Grid', 'role': 'Project the curved horizon plane that sells the IllusionCanvas pseudo-3D feel.'},
        {'id': 'lambert-rim-band', 'label': 'Lambert Rim Band', 'role': 'Apply directional light, rim light, and stepped palette bands to 3D faces.'},
        {'id': 'fog-and-aerial-perspective', 'label': 'Fog And Aerial Perspective', 'role': 'Compress distant contrast so far geometry sits in painterly haze.'},
        {'id': 'scanline-canvas-grain', 'label': 'Scanline Canvas Grain', 'role': 'Add analog scanline drift, grain, and vignette for the tactile shell finish.'},
    ],
    'uniforms': {
        'fog_density': 0.26,
        'rim_power': 2.4,
        'scanline_intensity': 0.18,
        'palette_steps': 5,
        'floor_curvature': 0.16,
    },
}


def read_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding='utf-8'))


def build_runtime(asset_root: Path) -> dict:
    playnow_manifest = resolve_playnow_runtime_path(asset_root)
    finalstage_manifest = resolve_playnow_finalstage_path(asset_root)
    idloadint_dir = resolve_idloadint_dir(asset_root)
    playnow_dir = resolve_playnow_dir(asset_root)
    tutorial_spec = idloadint_dir / 'tutorial_demo_spec.json'
    playnow = read_json(playnow_manifest)
    tutorial = read_json(tutorial_spec)
    finalstage = read_json(finalstage_manifest)
    prompt_count = len(tutorial.get('prompts', [])) if isinstance(tutorial, dict) else 0
    wave_count = len(tutorial.get('waves', [])) if isinstance(tutorial, dict) else 0
    tick_gnosis = build_tick_gnosis_frame(
        'dodogame-hybrid-runtime',
        tick=prompt_count + wave_count,
        frame_delta_ms=16.667,
        entity_count=max(1, prompt_count + wave_count + 1),
        energy_total=float(prompt_count * 10 + wave_count * 21),
        camera_motion=0.3,
        input_pressure=0.42,
        recursion_depth=2.4,
    )
    return {
        'runtime_id': 'dodogame-orb-do-hybrid',
        'label': 'Bango: Unchained - Bango&Patoot Hybrid Runtime',
        'asset_root': str(asset_root),
        'renderer_philosophy': 'Use ORBEngine for recursive pseudo-3D space presentation, DoENGINE for orchestration/input/telemetry, IllusionCanvas for manifest and perception interoperability, and TickGnosis for frame-buffer relativity moderation.',
        'renderer_backend': DODO_SHADER_PROGRAM['backend'],
        'protocol_contract': finalstage.get('protocol_contract') if isinstance(finalstage, dict) else None,
        'shader_program': DODO_SHADER_PROGRAM,
        'tick_gnosis': tick_gnosis,
        'render_stages': [
            {'id': 'stage_01_scene_ingest', 'label': 'Scene Ingest', 'owner': 'DoENGINE', 'description': 'Load game profile, PlayNOW handoff, authored metadata, and deterministic runtime configuration.'},
            {'id': 'stage_02_space_graph', 'label': 'Recursive Space Graph', 'owner': 'ORBEngine', 'description': 'Resolve parent/child space graph, scale remagnification, and pseudo-3D layer traversal.'},
            {'id': 'stage_03_full3d_proxy', 'label': 'Full 3D Proxy', 'owner': 'DODO3D', 'description': 'Apply mesh-aware transforms, collision anchors, sockets, and authored depth metrics for high-fidelity actors and setpieces.'},
            {'id': 'stage_04_pseudo3d_composite', 'label': 'Pseudo-3D Composite', 'owner': 'DODO3D', 'description': 'Blend billboard, floor warp, volumetric fog, top-cap projection, and asset-backed overlay passes.'},
            {'id': 'stage_05_tick_gnosis', 'label': 'TickGnosis Frame Moderation', 'owner': 'TickGnosis', 'description': 'Moderate mitigation, modulation, and consensus render time against the atomic-anchor coherency baseline.'},
            {'id': 'stage_06_ui_telemetry', 'label': 'UI + Telemetry', 'owner': 'DoENGINE', 'description': 'Present DODOGame shell UI, controller diagnostics, simulation state, and trace-safe runtime metrics.'},
            {'id': 'stage_07_tutorial_staging', 'label': 'PlayNOW Staging', 'owner': 'PlayNOW', 'description': 'Attach tutorial/runtime manifests, player bundle references, and test-automation handoff metadata.'},
        ],
        'controller_profiles': [
            {
                'profile_id': 'bango-xinput-full',
                'label': 'Bango Full XInput',
                'device_class': 'xinput',
                'bindings': [
                    {'actionId': 'move', 'label': 'Move', 'inputs': ['left_stick'], 'gameplayContext': 'Traversal'},
                    {'actionId': 'camera', 'label': 'Camera', 'inputs': ['right_stick'], 'gameplayContext': 'View'},
                    {'actionId': 'jump', 'label': 'Jump (tap B)', 'inputs': ['B'], 'gameplayContext': 'Traversal'},
                    {'actionId': 'crouch_slide', 'label': 'Crouch or Slide', 'inputs': ['A'], 'gameplayContext': 'Traversal'},
                    {'actionId': 'sprint', 'label': 'Sprint (hold B)', 'inputs': ['B'], 'gameplayContext': 'Traversal'},
                    {'actionId': 'light_attack', 'label': 'Light Attack', 'inputs': ['LB'], 'gameplayContext': 'Combat'},
                    {'actionId': 'heavy_attack', 'label': 'Heavy Attack', 'inputs': ['RT'], 'gameplayContext': 'Combat'},
                    {'actionId': 'block', 'label': 'Block', 'inputs': ['LeftThumb'], 'gameplayContext': 'Combat'},
                    {'actionId': 'parry', 'label': 'Parry', 'inputs': ['RightThumb'], 'gameplayContext': 'Combat'},
                    {'actionId': 'ability_wheel', 'label': 'Ability Wheel', 'inputs': ['LT', 'right_stick'], 'gameplayContext': 'Ability'},
                    {'actionId': 'face_x', 'label': 'Face X', 'inputs': ['X'], 'gameplayContext': 'Generic'},
                    {'actionId': 'face_y', 'label': 'Face Y', 'inputs': ['Y'], 'gameplayContext': 'Generic'},
                    {'actionId': 'menu', 'label': 'Menu', 'inputs': ['Start'], 'gameplayContext': 'System'},
                    {'actionId': 'back', 'label': 'Back', 'inputs': ['Back'], 'gameplayContext': 'System'},
                    {'actionId': 'dpad', 'label': 'Directional Pad', 'inputs': ['DPadUp', 'DPadDown', 'DPadLeft', 'DPadRight'], 'gameplayContext': 'UI'},
                    {'actionId': 'bumper_right', 'label': 'Right Bumper', 'inputs': ['RB'], 'gameplayContext': 'Modifier'},
                ],
            }
        ],
        'games': [
            {
                'gameId': 'bango-patoot',
                'label': 'Bango: Unchained - Bango&Patoot',
                'renderMode': 'full3d-pseudo3d-hybrid',
                'playnowManifest': str(playnow_manifest),
                'playnowFinalstage': str(finalstage_manifest),
                'tutorialSpec': str(tutorial_spec),
                'orbExecutable': str(WORKSPACE_ROOT / 'ORBEngine' / 'bango_unchained_bangopatoot_demo.exe'),
                'controllerProfileId': 'bango-xinput-full',
                'supports': ['3DS runtime target', 'Windows preview target', 'idTech2 module target', 'PlayNOW tutorial staging', 'TickGnosis-guided frame moderation'],
            },
            {
                'gameId': 'generic-hybrid-game',
                'label': 'Generic Hybrid Game Template',
                'renderMode': 'full3d-pseudo3d-hybrid',
                'controllerProfileId': 'bango-xinput-full',
                'supports': ['recursive pseudo-3D spaces', 'full-3D proxy actors', 'manifest-driven content ingest', 'deterministic simulation'],
            },
        ],
        'engine_manifests': {
            'doengine_backbone': str(playnow_dir / 'playnow_doengine_backbone.json'),
            'illusionviunow': str(playnow_dir / 'illusionviunow_runtime.json'),
            'orbitnow': str(playnow_dir / 'orbitnow_runtime.json'),
            'dodoplaynow': str(playnow_dir / 'dodoplaynow_runtime.json'),
        },
        'playnow_status': {
            'manifest_exists': playnow_manifest.exists(),
            'finalstage_exists': finalstage_manifest.exists(),
            'tutorial_exists': tutorial_spec.exists(),
            'passes': len(playnow.get('passes', [])) if isinstance(playnow, dict) else 0,
            'prompt_count': len(tutorial.get('prompts', [])) if isinstance(tutorial, dict) else 0,
        },
        'preview_artifacts': {
            'viewport_png': str(ROOT / 'generated' / 'dodogame_gui' / 'dodo_engine_preview.png'),
            'viewport_report': str(ROOT / 'generated' / 'dodogame_gui' / 'dodo_engine_preview.json'),
            'bangonow_showcase': str(ROOT / 'generated' / 'dodogame_bangonow_showcase.json'),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Build DODOGame hybrid runtime profile')
    parser.add_argument('--asset-root', type=Path)
    args = parser.parse_args()

    asset_root = args.asset_root.resolve() if args.asset_root else resolve_bango_asset_root()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    runtime = build_runtime(asset_root)
    OUTPUT_PATH.write_text(json.dumps(runtime, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'runtime_profile': str(OUTPUT_PATH), 'asset_root': str(asset_root), 'playnow_manifest_exists': resolve_playnow_runtime_path(asset_root).exists()}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
