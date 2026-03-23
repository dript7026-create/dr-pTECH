from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GENERATED_DIR = ROOT / 'generated'
MANIFEST_PATH = GENERATED_DIR / 'doengine_gui_recraft_manifest.json'
SUMMARY_PATH = GENERATED_DIR / 'doengine_gui_asset_summary.json'

MOTION_APPENDIX = (
    'Aesthetic philosophy: MOTION. Use directional momentum, kinetic diagonals, layered underlays, '
    'bold contrast, lucid technical readability, and GUI-ready compositional rhythm.'
)


def make_asset(name: str, category: str, prompt: str, out: str, planned_credits: int = 50) -> dict:
    return {
        'name': name,
        'category': category,
        'prompt': prompt,
        'negative_prompt': 'muddy shapes, low contrast, text blocks, watermark, opaque photo background, perspective clutter, unreadable controls',
        'w': 2048,
        'h': 2048,
        'model': 'recraftv4',
        'planned_credits': planned_credits,
        'api_units': planned_credits,
        'out': out,
        'transparent_background': True,
        'auto_polish': True,
    }


def build_assets() -> list[dict]:
    assets: list[dict] = []
    assets.append(
        make_asset(
            'do9_logo_master',
            'branding',
            'DoENGINE Do9 logo on transparent background, vertically aligned black rectangle with blue lettered Do aligned center-left above the rectangle, green underlay beneath, and a sharp red 9 aligned top-right hanging down past the Do and extending below the rectangle, tapering to a sharp point. Crisp vector-like edges, MOTION aesthetic, GUI master branding asset.',
            'gui_assets/branding/do9_logo_master.png',
        )
    )

    collections = {
        'window_frames': 6,
        'panels': 8,
        'buttons': 10,
        'tabs': 6,
        'status_widgets': 6,
        'timeline_widgets': 4,
        'asset_cards': 4,
        'icons': 8,
        'splash_screens': 2,
        'backgrounds': 3,
        'console_widgets': 2,
    }

    for category, count in collections.items():
        for index in range(1, count + 1):
            assets.append(
                make_asset(
                    f'{category}_{index:02d}',
                    category,
                    f'DoENGINE GUI {category.replace("_", " ")} asset {index:02d}, transparent background, MOTION aesthetic, kinetic directional hierarchy, crisp technical readability, usable for a desktop engine tool.',
                    f'gui_assets/{category}/{category}_{index:02d}.png',
                )
            )

    return assets


def main() -> int:
    assets = build_assets()
    manifest = {
        'manifest_name': 'doengine_gui_asset_package_3000_credit_pass',
        'manifest_version': '2026-03-13.motion_gui',
        'intent': 'Full GUI asset package for the standalone DoENGINE application using the MOTION philosophy.',
        'output_root': '..',
        'budget': {
            'requested_budget': 3000,
            'allocated_credits': sum(asset['planned_credits'] for asset in assets),
        },
        'shared_prompt_appendix': MOTION_APPENDIX,
        'assets': assets,
    }
    summary = {
        'asset_count': len(assets),
        'allocated_credits': manifest['budget']['allocated_credits'],
        'branding_asset': 'do9_logo_master',
        'philosophy': 'MOTION',
    }

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'manifest': str(MANIFEST_PATH), 'summary': str(SUMMARY_PATH), 'allocated_credits': summary['allocated_credits']}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())