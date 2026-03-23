from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = ROOT.parent
OUTPUT_PATH = ROOT / 'generated' / 'dodogame_bangonow_showcase.json'


def load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding='utf-8'))


def first_existing_path(*candidates: object) -> Path | None:
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(str(candidate))
        if path.exists():
            return path
    return None


def candidate_package_manifests() -> list[Path]:
    roots = [
        WORKSPACE_ROOT / 'bango-patoot_3DS' / 'generated',
        Path('E:/Bango-Patoot assets/test assets/recraft/generated'),
    ]
    matches: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        matches.extend(root.glob('**/bangonow/playable_package/bangonow_playable_package.json'))
    unique = {path.resolve() for path in matches}
    return sorted(unique, key=lambda item: item.stat().st_mtime, reverse=True)


def choose_package_manifest() -> Path:
    for path in candidate_package_manifests():
        payload = load_json(path)
        if isinstance(payload, dict) and payload.get('playable_ready'):
            return path
    raise FileNotFoundError('No playable BangoNOW package manifest was found.')


def collect_preview_images(package_payload: dict) -> list[Path]:
    images: list[Path] = []
    asset_root = Path(str(package_payload.get('asset_root', ROOT)))
    polished_dir = WORKSPACE_ROOT / 'bango-patoot_3DS' / 'generated' / 'recraft_polished'
    if polished_dir.exists():
        images.extend(sorted(polished_dir.glob('*.png'))[:6])
    autorig_dir = asset_root / 'generated' / 'blender_bango_autorig'
    if autorig_dir.exists():
        for name in [
            'bangopatoot_asset_graphical_charactersheet_bango_fouranglestpose_keyed_0001_readAIpolish.png',
            'bangopatoot_asset_render_bango_riggedautoblockout_0001.png',
        ]:
            candidate = autorig_dir / name
            if candidate.exists():
                images.append(candidate)
    return images[:8]


def curved_pass_positions(count: int) -> list[tuple[float, float, float]]:
    if count <= 0:
        return []
    center = (count - 1) / 2.0
    positions: list[tuple[float, float, float]] = []
    for index in range(count):
        offset = index - center
        x = round(offset * 4.8, 3)
        z = round(8.4 + abs(offset) * 1.45, 3)
        yaw = round(-offset * 0.16, 3)
        positions.append((x, z, yaw))
    return positions


def artifact_positions(count: int) -> list[tuple[float, float]]:
    if count <= 0:
        return []
    center = (count - 1) / 2.0
    positions: list[tuple[float, float]] = []
    for index in range(count):
        offset = index - center
        x = round(offset * 3.6, 3)
        z = round(17.0 + abs(offset) * 1.1, 3)
        positions.append((x, z))
    return positions


def build_scene_entries(package_payload: dict, playnow_runtime: dict) -> list[dict]:
    entries: list[dict] = []
    preview_images = collect_preview_images(package_payload)
    passes = playnow_runtime.get('passes', []) if isinstance(playnow_runtime, dict) else []
    pass_positions = curved_pass_positions(len(passes))

    entries.extend(
        [
            {
                'id': 'pipeline_spine',
                'kind': 'mesh',
                'loader': 'builtin',
                'mesh': 'spire',
                'position': [0.0, 0.55, 14.2],
                'rotation': [0.0, 0.68, 0.0],
                'scale': 1.18,
                'label': 'BangoNOW Spine',
                'scripts': [{'type': 'spin', 'speed': 0.06}, {'type': 'pulse', 'amplitude': 0.04, 'speed': 1.1}],
                'metadata': {'role': 'pipeline-spine'},
            },
            {
                'id': 'pipeline_gate_left',
                'kind': 'mesh',
                'loader': 'builtin',
                'mesh': 'arch',
                'position': [-7.6, 0.2, 12.2],
                'rotation': [0.12, 0.26, 0.0],
                'scale': 1.06,
                'label': 'Bango Gate Left',
                'scripts': [{'type': 'bob', 'amplitude': 0.1, 'speed': 0.82}, {'type': 'spin', 'speed': 0.09}],
                'metadata': {'role': 'gate'},
            },
            {
                'id': 'pipeline_gate_right',
                'kind': 'mesh',
                'loader': 'builtin',
                'mesh': 'arch',
                'position': [7.6, 0.15, 12.7],
                'rotation': [0.16, -0.3, 0.0],
                'scale': 1.16,
                'label': 'Bango Gate Right',
                'scripts': [{'type': 'bob', 'amplitude': 0.08, 'speed': 0.94}, {'type': 'spin', 'speed': -0.07}],
                'metadata': {'role': 'gate'},
            },
            {
                'id': 'pipeline_summary_card',
                'kind': 'billboard',
                'position': [-7.9, 2.5, 18.8],
                'width': 460,
                'height': 260,
                'image_path': preview_images[0].as_posix() if preview_images else None,
                'label': f'passes {len(passes)} / artifacts {len(package_payload.get("artifacts", {}))}',
                'tint': [214, 172, 104],
                'scripts': [{'type': 'bob', 'amplitude': 0.11, 'speed': 0.74}],
                'metadata': {
                    'requested_passes': package_payload.get('requested_passes', []),
                    'selected_build_targets': package_payload.get('selected_build_targets', []),
                    'playable_ready': package_payload.get('playable_ready', False),
                },
            },
            {
                'id': 'pipeline_targets_card',
                'kind': 'billboard',
                'position': [7.9, 2.35, 19.6],
                'width': 460,
                'height': 260,
                'image_path': preview_images[1].as_posix() if len(preview_images) > 1 else None,
                'label': 'targets ' + ', '.join(package_payload.get('selected_build_targets', [])[:3]),
                'tint': [132, 176, 146],
                'scripts': [{'type': 'bob', 'amplitude': 0.1, 'speed': 0.88}],
                'metadata': package_payload.get('artifacts', {}),
            },
        ]
    )

    for index, item in enumerate(passes):
        x, z, yaw = pass_positions[index]
        preview_image = preview_images[index % len(preview_images)].as_posix() if preview_images else None
        entries.append(
            {
                'id': f'pass_pedestal_{item.get("pass_label", index)}',
                'kind': 'mesh',
                'loader': 'builtin',
                'mesh': 'pedestal',
                'position': [x, -1.55, z],
                'rotation': [0.0, yaw, 0.0],
                'scale': 0.72,
                'label': f'{item.get("pass_label", "pass")} ({item.get("asset_count", 0)} assets)',
                'scripts': [{'type': 'pulse', 'amplitude': 0.03, 'speed': 1.4 + index * 0.2}],
                'metadata': item,
            }
        )
        entries.append(
            {
                'id': f'pass_card_{item.get("pass_label", index)}',
                'kind': 'billboard',
                'position': [x, 1.35, z],
                'width': 440,
                'height': 260,
                'image_path': preview_image,
                'label': f'{item.get("pass_label", "pass")} pipeline pass',
                'tint': [201, 167, 114],
                'scripts': [{'type': 'bob', 'amplitude': 0.12, 'speed': 0.9 + index * 0.1}],
                'metadata': item,
            }
        )
        entries.append(
            {
                'id': f'pass_orbit_{item.get("pass_label", index)}',
                'kind': 'mesh',
                'loader': 'builtin',
                'mesh': 'shard',
                'position': [x, 0.5, z],
                'rotation': [0.0, yaw, 0.0],
                'scale': 0.44,
                'label': f'{item.get("pass_label", "pass")} token',
                'scripts': [
                    {'type': 'orbit', 'anchor': [x, 0.5, z], 'radius': 1.15 + (index % 2) * 0.18, 'speed': 0.95 + index * 0.12, 'phase': round(index * math.pi / 3.0, 3)},
                    {'type': 'spin', 'speed': 0.36 + index * 0.03},
                ],
                'metadata': {'pass_label': item.get('pass_label', index), 'role': 'pass-orbit-token'},
            }
        )

    player = playnow_runtime.get('player', {}) if isinstance(playnow_runtime, dict) else {}
    pass_glb = next((item.get('player_glb') for item in passes if isinstance(item, dict) and item.get('player_glb')), None)
    player_glb = first_existing_path(player.get('glb'), pass_glb)
    hero_entry = {
        'id': 'bango_proxy_hero',
        'kind': 'mesh',
        'position': [0.0, -0.15, 5.4],
        'rotation': [0.0, 0.12, 0.0],
        'scale': 0.82,
        'label': 'Bango hero runtime mesh',
        'scripts': [{'type': 'spin', 'speed': 0.12}, {'type': 'bob', 'amplitude': 0.07, 'speed': 1.2}],
        'metadata': {'player_glb': player.get('glb') or pass_glb, 'player_blend': player.get('blend')},
    }
    if player_glb is not None:
        hero_entry['loader'] = 'glb'
        hero_entry['mesh'] = player_glb.as_posix()
        hero_entry['rotation'] = [0.0, -0.42, 0.0]
        hero_entry['scale'] = 0.74
    else:
        hero_entry['loader'] = 'builtin'
        hero_entry['mesh'] = 'monolith'
    entries.append(
        hero_entry
    )

    artifact_layout = artifact_positions(len(package_payload.get('artifacts', {})))
    for index, (artifact_name, artifact_payload) in enumerate(package_payload.get('artifacts', {}).items()):
        if index >= len(artifact_layout):
            break
        x, z = artifact_layout[index]
        entries.append(
            {
                'id': f'artifact_{artifact_name}',
                'kind': 'mesh',
                'loader': 'builtin',
                'mesh': 'cube',
                'position': [x, -0.35, z],
                'rotation': [0.1, 0.22 * index, 0.0],
                'scale': 0.66,
                'label': artifact_name,
                'scripts': [{'type': 'spin', 'speed': 0.08 + index * 0.03}],
                'metadata': artifact_payload,
            }
        )
        entries.append(
            {
                'id': f'artifact_card_{artifact_name}',
                'kind': 'billboard',
                'position': [x, 1.7, z],
                'width': 380,
                'height': 210,
                'image_path': None,
                'label': f'{artifact_payload.get("platform", "platform")}: {Path(str(artifact_payload.get("staged_path", artifact_name))).name}',
                'tint': [126, 164, 142],
                'scripts': [{'type': 'bob', 'amplitude': 0.08, 'speed': 1.1 + index * 0.1}],
                'metadata': artifact_payload,
            }
        )

    gallery_start = min(len(preview_images), max(2, len(passes)))
    for index, preview in enumerate(preview_images[gallery_start:], start=0):
        entries.append(
            {
                'id': f'gallery_card_{index + 1}',
                'kind': 'billboard',
                'position': [-8.6 + index * 5.7, 2.1 + (index % 2) * 0.15, 22.0 + index * 1.35],
                'width': 420,
                'height': 280,
                'image_path': preview.as_posix(),
                'label': preview.stem.replace('_', ' '),
                'tint': [186, 146, 98],
                'scripts': [{'type': 'bob', 'amplitude': 0.1, 'speed': 0.95 + index * 0.08}],
                'metadata': {'preview_path': str(preview)},
            }
        )
    return entries


def build_showcase() -> dict:
    package_manifest = choose_package_manifest()
    package_payload = load_json(package_manifest)
    if not isinstance(package_payload, dict):
        raise ValueError(f'Package manifest is not a JSON object: {package_manifest}')
    playnow_runtime_path = Path(str(package_payload.get('manifests', {}).get('playnow_runtime', {}).get('source', '')))
    playnow_runtime = load_json(playnow_runtime_path) if playnow_runtime_path.exists() else {}
    scene = {
        'showcase_name': 'BangoNOW Pipeline Gallery',
        'scene_version': '2026-03-17.dodo-showcase',
        'camera': {'orbit': 0.56, 'elevation': 0.2, 'focus_z': 11.5},
        'source_package_manifest': str(package_manifest),
        'asset_loaders': ['builtin', 'obj', 'glb', 'billboard'],
        'script_capabilities': ['spin', 'bob', 'pulse', 'orbit'],
        'pipeline': {
            'selected_build_targets': package_payload.get('selected_build_targets', []),
            'requested_passes': package_payload.get('requested_passes', []),
            'playable_ready': package_payload.get('playable_ready', False),
            'artifact_count': len(package_payload.get('artifacts', {})),
            'pass_count': len(playnow_runtime.get('passes', [])) if isinstance(playnow_runtime, dict) else 0,
        },
        'scene_entries': build_scene_entries(package_payload, playnow_runtime if isinstance(playnow_runtime, dict) else {}),
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(scene, indent=2) + '\n', encoding='utf-8')
    return {
        'showcase_manifest': str(OUTPUT_PATH),
        'source_package_manifest': str(package_manifest),
        'playnow_runtime': str(playnow_runtime_path) if playnow_runtime_path else None,
        'scene_entry_count': len(scene['scene_entries']),
        'requested_passes': scene['pipeline']['requested_passes'],
        'selected_build_targets': scene['pipeline']['selected_build_targets'],
    }


def main() -> int:
    payload = build_showcase()
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
