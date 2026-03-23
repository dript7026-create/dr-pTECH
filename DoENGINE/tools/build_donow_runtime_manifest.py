from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def classify_runtime_bucket(category: str) -> str:
    mapping = {
        'character_sheet': 'actors',
        'animation_pack': 'animation_streams',
        'environment_set': 'world_tiles',
        'hud_pack': 'ui',
        'combat_fx': 'effects',
        'environmental_fx': 'effects',
        'armor_set': 'equipment',
        'weapon_pack': 'equipment',
        'item_pack': 'equipment',
        'ammunition_pack': 'equipment',
        'animated_environment_object': 'interactive_world',
        'apiary_sheet': 'interactive_world',
    }
    return mapping.get(category, 'support')


def build_donow_manifest(source_manifest: dict) -> dict:
    assets = source_manifest.get('assets', [])
    entries = []
    for asset in assets:
        if 'donow' not in asset.get('pipeline_targets', []):
            continue
        entries.append(
            {
                'asset_id': asset['name'],
                'category': asset['category'],
                'runtime_bucket': classify_runtime_bucket(asset['category']),
                'source_path': asset['out'],
                'immediate_ready': True,
                'derived_outputs': asset.get('protocol', {}).get('derived_outputs', []),
                'generation_mode': asset.get('generation_mode', 'packed_master'),
            }
        )

    return {
        'engine_name': 'DoENGINE',
        'module_name': 'DoNOW',
        'protocol_contract': {
            'name': 'four_pronged_mathematical_perfect_expression',
            'status': 'encoded_from_current_workspace_contract',
            'prongs': [
                'deterministic_manifest_intake',
                'layered_presentation_interop',
                'full_proxy_gameplay_delivery',
                'verified_windows_delivery',
            ],
        },
        'project_name': source_manifest.get('manifest_name', 'bango_patoot_stream'),
        'stream_name': 'clip_blend_id_donow_stream',
        'asset_root': source_manifest.get('asset_root') or source_manifest.get('output_root'),
        'entry_count': len(entries),
        'backbone': {
            'load_bearing': True,
            'support_surfaces': ['actors', 'animation_streams', 'world_tiles', 'ui', 'effects', 'interactive_world'],
            'gameplay_ready': True,
        },
        'immediate_functionality': {
            'boot_scene': 'hive_heart_hub',
            'preload_groups': [
                {'name': 'hero_bootstrap', 'runtime_buckets': ['actors', 'animation_streams', 'ui']},
                {'name': 'world_bootstrap', 'runtime_buckets': ['world_tiles', 'interactive_world', 'effects']},
                {'name': 'equipment_bootstrap', 'runtime_buckets': ['equipment', 'support']},
            ],
            'startup_actions': [
                'mount actor packages',
                'mount HUD and input layers',
                'mount world tile and FX layers',
                'bind animation and equipment registries',
            ],
        },
        'entries': entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Build a DoNOW runtime manifest from a clip-blend-id source manifest')
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()

    manifest = build_donow_manifest(load_manifest(args.source))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'out': str(args.out), 'entry_count': manifest['entry_count']}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())