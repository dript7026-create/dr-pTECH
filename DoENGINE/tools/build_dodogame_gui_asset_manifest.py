from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GENERATED_DIR = ROOT / 'generated'
MANIFEST_PATH = GENERATED_DIR / 'dodogame_gui_recraft_manifest.json'
SUMMARY_PATH = GENERATED_DIR / 'dodogame_gui_asset_summary.json'

DODO_APPENDIX = (
    'Aesthetic philosophy: prehistoric dodo-life desktop shell. Use fossil chalk, marsh jade, ember amber, '
    'basalt slate, museum-label clarity, rounded shell geometry, and tactile explorer-tool readability.'
)


def make_asset(name: str, category: str, prompt: str, out: str, planned_credits: int) -> dict:
    return {
        'name': name,
        'category': category,
        'prompt': prompt,
        'negative_prompt': 'watermark, photo background, illegible text, cluttered perspective, muddy colors, realistic humans, low contrast',
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
    specs = [
        ('dodogame_logo', 'branding', 'DODOGame logo, transparent background, prehistoric dodo-life themed engine launcher mark, fossil tablet silhouette, egg-curve geometry, amber signal accent.', 'dodogame_gui/dodogame_badge.png', 90),
        ('dodo_shell_frame', 'window_frame', 'Standalone DODOGame main window frame, transparent background, basalt shell edges, museum brass insets, readable editor chrome.', 'dodogame_gui/shell_frame.png', 85),
        ('dodo_runtime_panel', 'panels', 'DODOGame runtime panel, transparent background, tactile fossil-lab styling for hybrid runtime, render diagnostics, and controller state.', 'dodogame_gui/shell_panel_runtime.png', 45),
        ('dodo_report_panel', 'panels', 'DODOGame report panel, transparent background, archive-card styling for tutorial reports, PlayNOW traces, and completion summaries.', 'dodogame_gui/shell_panel_report.png', 40),
        ('dodo_button_collection', 'buttons', 'DODOGame button atlas, transparent background, hover, pressed, disabled, call-to-action, and ghost states, prehistoric expedition aesthetic.', 'dodogame_gui/buttons/dodo_button_collection.png', 80),
        ('dodo_status_widgets', 'status_widgets', 'DODOGame status widget atlas, runtime health, pipeline state, build state, tutorial progress, and controller presence indicators.', 'dodogame_gui/widgets/dodo_status_widgets.png', 80),
        ('dodo_toolbar_icons', 'icons', 'DODOGame toolbar icon atlas for render, assets, simulation, PlayNOW, launch, report, and controller tools.', 'dodogame_gui/icons/dodo_toolbar_icons.png', 80),
        ('dodo_environment_backdrop', 'background', 'DODOGame launcher background, transparent-background capable layered swamp museum observatory scene with dodo-era motifs and clean negative space.', 'dodogame_gui/backgrounds/dodo_environment_backdrop.png', 95),
        ('dodo_controller_diagrams', 'controller', 'DODOGame full controller input diagram set, all XInput face buttons, shoulders, triggers, sticks, dpad, start, back, thumb clicks, transparent background.', 'dodogame_gui/controller/dodo_controller_diagrams.png', 85),
        ('dodo_runtime_cards', 'cards', 'DODOGame runtime card atlas for Bango-Patoot profile, generic game profile, ORB pseudo-3D renderer, DoENGINE orchestration, and PlayNOW staging.', 'dodogame_gui/cards/dodo_runtime_cards.png', 85),
        ('dodo_font_stone', 'font', 'Custom uppercase and numeric bitmap font atlas for DODOGame, carved volcanic stone glyphs, alphanumeric only, transparent background, crisp grid alignment.', 'dodogame_gui/fonts/dodo_font_stone.png', 70),
        ('dodo_font_bone', 'font', 'Custom uppercase and numeric bitmap font atlas for DODOGame, polished fossil bone glyphs, alphanumeric only, transparent background, crisp grid alignment.', 'dodogame_gui/fonts/dodo_font_bone.png', 70),
        ('dodo_launch_splash', 'splash', 'DODOGame launch splash illustration, prehistoric dodo-life themed engine portal, transparent background, layered pseudo-3D composition.', 'dodogame_gui/splash/dodo_launch_splash.png', 95),
        ('dodo_notification_pack', 'notifications', 'DODOGame notification, toast, tooltip, and modal shells, transparent background, lab expedition styling.', 'dodogame_gui/notifications/dodo_notification_pack.png', 80),
        ('dodo_report_panels', 'reports', 'DODOGame report viewer frames and document strips, transparent background, archive card and fossil index aesthetic.', 'dodogame_gui/reports/dodo_report_panels.png', 75),
        ('dodo_input_hint_pack', 'hints', 'DODOGame input hint atlas for every controller interaction plus keyboard fallback, transparent background, concise arcade-lab styling.', 'dodogame_gui/hints/dodo_input_hint_pack.png', 70),
        ('dodo_cursor_pack', 'cursor', 'DODOGame cursor and pointer pack, transparent background, beak-tip precision and egg-select states.', 'dodogame_gui/cursor/dodo_cursor_pack.png', 75),
        ('dodo_scene_hierarchy_pack', 'scene_hierarchy', 'DODOGame scene hierarchy atlas for spaces, actors, sockets, recursive pockets, and render stages, transparent background.', 'dodogame_gui/scene_hierarchy/dodo_scene_hierarchy_pack.png', 50),
        ('dodo_material_cards', 'materials', 'DODOGame material and layer cards, transparent background, fossil lab labels, marsh-metal accents, readable asset metadata presentation.', 'dodogame_gui/materials/dodo_material_cards.png', 50),
        ('dodo_timeline_strips', 'timeline', 'DODOGame timeline strips for animation, simulation replay, and tutorial event review, transparent background, clean sequencing cues.', 'dodogame_gui/timeline/dodo_timeline_strips.png', 50),
        ('dodo_world_map_widgets', 'world_map', 'DODOGame world-map widgets for nested spaces, route traces, checkpoints, and pocket-space focus markers, transparent background.', 'dodogame_gui/world_map/dodo_world_map_widgets.png', 50),
    ]
    for name, category, prompt, out, planned_credits in specs:
        assets.append(make_asset(name, category, prompt, out, planned_credits))
    return assets


def main() -> int:
    assets = build_assets()
    allocated = sum(asset['planned_credits'] for asset in assets)
    manifest = {
        'manifest_name': 'dodogame_gui_asset_package_1500_credit_pass',
        'manifest_version': '2026-03-13.dodo_gui',
        'intent': 'DODOGame standalone GUI asset package for the DoENGINE + ORBEngine hybrid runtime.',
        'output_root': '.',
        'budget': {
            'requested_budget': 1500,
            'allocated_credits': allocated,
        },
        'shared_prompt_appendix': DODO_APPENDIX,
        'assets': assets,
    }
    summary = {
        'asset_count': len(assets),
        'allocated_credits': allocated,
        'requested_budget': 1500,
        'philosophy': 'prehistoric dodo-life',
        'custom_fonts': ['dodo_font_stone', 'dodo_font_bone'],
    }
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'manifest': str(MANIFEST_PATH), 'summary': str(SUMMARY_PATH), 'allocated_credits': allocated}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
