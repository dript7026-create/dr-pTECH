from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

_bango_paths = __import__('bango_integration_paths')
resolve_bango_asset_root = _bango_paths.resolve_bango_asset_root
resolve_playnow_runtime_path = _bango_paths.resolve_playnow_runtime_path
resolve_playnow_finalstage_path = _bango_paths.resolve_playnow_finalstage_path

SHOWCASE_PATH = ROOT / 'generated' / 'dodogame_bangonow_showcase.json'
HYBRID_RUNTIME_PATH = ROOT / 'generated' / 'dodogame_hybrid_runtime.json'
WINDOWS_BUNDLE_PATH = ROOT / 'generated' / 'windows_bundle' / 'dodogame_windows_bundle.json'
OUTPUT_PATH = ROOT / 'generated' / 'dodogame_bango_pipeline_verification.json'


def load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding='utf-8'))


def make_check(check_id: str, status: str, message: str, **details: object) -> dict:
    payload = {'id': check_id, 'status': status, 'message': message}
    if details:
        payload['details'] = details
    return payload


def existing_path_map(paths: dict[str, object]) -> dict[str, dict[str, object]]:
    mapped: dict[str, dict[str, object]] = {}
    for key, raw_path in paths.items():
        path = Path(str(raw_path)) if raw_path else None
        mapped[key] = {
            'path': str(path) if path else None,
            'exists': bool(path and path.exists()),
        }
    return mapped


def summarize_status(values: list[str]) -> str:
    if 'fail' in values:
        return 'fail'
    if 'warn' in values:
        return 'warn'
    return 'pass'


def validate(asset_root: Path) -> dict:
    package_path = asset_root / 'generated' / 'bangonow' / 'playable_package' / 'bangonow_playable_package.json'
    summary_path = asset_root / 'generated' / 'bangonow' / 'bangonow_run_summary.json'
    playnow_runtime_path = resolve_playnow_runtime_path(asset_root)
    playnow_finalstage_path = resolve_playnow_finalstage_path(asset_root)

    package = load_json(package_path)
    summary = load_json(summary_path)
    playnow_runtime = load_json(playnow_runtime_path)
    playnow_finalstage = load_json(playnow_finalstage_path)
    showcase = load_json(SHOWCASE_PATH)
    hybrid_runtime = load_json(HYBRID_RUNTIME_PATH)
    windows_bundle = load_json(WINDOWS_BUNDLE_PATH)

    checks: list[dict] = []

    required_files = {
        'package_manifest': package_path,
        'summary_manifest': summary_path,
        'playnow_runtime': playnow_runtime_path,
        'playnow_finalstage': playnow_finalstage_path,
        'showcase_manifest': SHOWCASE_PATH,
        'hybrid_runtime': HYBRID_RUNTIME_PATH,
        'windows_bundle': WINDOWS_BUNDLE_PATH,
    }
    file_status = existing_path_map(required_files)
    missing_files = [name for name, data in file_status.items() if not data['exists']]
    checks.append(
        make_check(
            'required_files',
            'pass' if not missing_files else 'fail',
            'Required Bango and DODO manifest files are present.' if not missing_files else 'Some required Bango or DODO manifest files are missing.',
            files=file_status,
        )
    )

    runtime_pass_labels = [entry.get('pass_label') for entry in playnow_runtime.get('passes', [])] if isinstance(playnow_runtime, dict) else []
    runtime_passes = [entry for entry in playnow_runtime.get('passes', []) if isinstance(entry, dict)] if isinstance(playnow_runtime, dict) else []
    package_requested_passes = package.get('requested_passes', []) if isinstance(package, dict) else []
    missing_requested_passes = [label for label in package_requested_passes if label not in runtime_pass_labels]
    checks.append(
        make_check(
            'runtime_pass_coverage',
            'pass' if not missing_requested_passes else 'fail',
            'PlayNOW runtime covers every requested BangoNOW package pass.' if not missing_requested_passes else 'PlayNOW runtime is missing requested package passes.',
            runtime_passes=runtime_pass_labels,
            requested_passes=package_requested_passes,
            missing=missing_requested_passes,
        )
    )

    package_playable_ready = bool(isinstance(package, dict) and package.get('playable_ready'))
    staged_artifacts = package.get('artifacts', {}) if isinstance(package, dict) and isinstance(package.get('artifacts'), dict) else {}
    missing_artifacts = [name for name, payload in staged_artifacts.items() if isinstance(payload, dict) and not payload.get('exists')]
    checks.append(
        make_check(
            'playable_package_ready',
            'pass' if package_playable_ready and not missing_artifacts else 'warn',
            'Playable package is marked ready and staged artifacts exist.' if package_playable_ready and not missing_artifacts else 'Playable package is not fully ready or some staged artifacts are missing.',
            playable_ready=package_playable_ready,
            missing_artifacts=missing_artifacts,
        )
    )

    showcase_source_ok = False
    showcase_scene_entries = showcase.get('scene_entries', []) if isinstance(showcase, dict) else []
    represented_passes = sorted(
        {
            entry.get('metadata', {}).get('pass_label')
            for entry in showcase_scene_entries
            if isinstance(entry, dict) and isinstance(entry.get('metadata'), dict) and entry.get('metadata', {}).get('pass_label')
        }
    )
    if isinstance(showcase, dict):
        showcase_source_ok = str(showcase.get('source_package_manifest')) == str(package_path)

    showcase_by_pass: dict[str, list[dict]] = {}
    for entry in showcase_scene_entries:
        if not isinstance(entry, dict):
            continue
        metadata = entry.get('metadata', {}) if isinstance(entry.get('metadata'), dict) else {}
        pass_label = metadata.get('pass_label')
        if not pass_label:
            continue
        showcase_by_pass.setdefault(str(pass_label), []).append(entry)

    per_pass: dict[str, dict] = {}
    pass_graphics_statuses: list[str] = []
    pass_feature_statuses: list[str] = []
    missing_graphics_passes: list[str] = []
    incomplete_feature_passes: list[str] = []
    missing_integration_passes: list[str] = []
    summary_key_aliases = {
        'humble': 'humble_playnow',
        'combat16': 'combat16_playnow',
        'tutorial32': 'tutorial32_playnow',
        'tutorial_final_preview': 'tutorial_final_preview_playnow',
        'dodogame': 'dodoplaynow',
    }
    checks.append(
        make_check(
            'showcase_runtime_alignment',
            'pass' if showcase_source_ok and sorted(runtime_pass_labels) == represented_passes else 'warn',
            'Showcase manifest points at the current playable package and represents the runtime pass set.' if showcase_source_ok and sorted(runtime_pass_labels) == represented_passes else 'Showcase manifest and runtime pass representation are partially out of sync.',
            showcase_source=str(showcase.get('source_package_manifest')) if isinstance(showcase, dict) else None,
            package_manifest=str(package_path),
            represented_passes=represented_passes,
            runtime_passes=sorted(runtime_pass_labels),
        )
    )

    for pass_entry in runtime_passes:
        pass_label = str(pass_entry.get('pass_label', 'unknown'))
        showcase_entries = showcase_by_pass.get(pass_label, [])
        entry_ids = {str(item.get('id')) for item in showcase_entries if isinstance(item, dict) and item.get('id')}
        card_entries = [item for item in showcase_entries if isinstance(item, dict) and str(item.get('id', '')).startswith('pass_card_')]
        card_images = existing_path_map({str(index): item.get('image_path') for index, item in enumerate(card_entries) if item.get('image_path')})
        missing_card_images = [payload['path'] for payload in card_images.values() if not payload['exists']]
        has_required_scene_shapes = any(item.startswith('pass_pedestal_') for item in entry_ids) and any(item.startswith('pass_card_') for item in entry_ids) and any(item.startswith('pass_orbit_') for item in entry_ids)
        graphics_status = 'pass' if has_required_scene_shapes and not missing_card_images else 'warn'
        if graphics_status != 'pass':
            missing_graphics_passes.append(pass_label)
        pass_graphics_statuses.append(graphics_status)

        required_paths = {
            'integration_manifest': asset_root / 'generated' / 'playnow' / f'playnow_{pass_label}_integration.json',
            'player_blend': pass_entry.get('player_blend'),
            'player_glb': pass_entry.get('player_glb'),
            'pipeline_report': pass_entry.get('pipeline_report'),
            'tutorial_manifest': pass_entry.get('tutorial_manifest'),
            'tutorial_spec': pass_entry.get('tutorial_spec'),
            'enemy_spec': pass_entry.get('enemy_spec'),
        }
        if pass_entry.get('runtime_tutorial_spec'):
            required_paths['runtime_tutorial_spec'] = pass_entry.get('runtime_tutorial_spec')
        if pass_entry.get('asset_manifest'):
            required_paths['asset_manifest'] = pass_entry.get('asset_manifest')
        path_status = existing_path_map(required_paths)
        missing_required_paths = [name for name, payload in path_status.items() if not payload['exists']]
        if not path_status.get('integration_manifest', {}).get('exists'):
            missing_integration_passes.append(pass_label)

        feature_status = 'pass'
        feature_notes: list[str] = []
        if missing_required_paths:
            feature_status = 'warn'
            feature_notes.append('missing_required_paths')
        if pass_label == 'tutorial_final_preview':
            if not isinstance(pass_entry.get('asset_budget'), dict) or not isinstance(pass_entry.get('asset_traceability'), dict):
                feature_status = 'warn'
                feature_notes.append('missing_budget_or_traceability')
            blendnow = pass_entry.get('blendnow_bundle', {}) if isinstance(pass_entry.get('blendnow_bundle'), dict) else {}
            if not blendnow.get('exists'):
                feature_status = 'warn'
                feature_notes.append('missing_blendnow_bundle')
        elif pass_label in {'combat16', 'tutorial32', 'humble'}:
            if not pass_entry.get('asset_manifest') or not pass_entry.get('asset_count'):
                feature_status = 'warn'
                feature_notes.append('missing_manifest_or_asset_count')
        pass_feature_statuses.append(feature_status)
        if feature_status != 'pass':
            incomplete_feature_passes.append(pass_label)

        per_pass[pass_label] = {
            'status': summarize_status([graphics_status, feature_status]),
            'graphics_load_in_ready': graphics_status == 'pass',
            'feature_complete': feature_status == 'pass',
            'scene_entry_count': len(showcase_entries),
            'scene_entry_ids': sorted(entry_ids),
            'missing_card_images': missing_card_images,
            'required_paths': path_status,
            'missing_required_paths': missing_required_paths,
            'notes': feature_notes,
            'asset_count': pass_entry.get('asset_count'),
            'asset_manifest': pass_entry.get('asset_manifest'),
        }

    checks.append(
        make_check(
            'pass_graphics_load_in',
            summarize_status(pass_graphics_statuses),
            'Every PlayNOW pass has showcase geometry, billboard load-in, and pass card coverage.' if not missing_graphics_passes else 'Some PlayNOW passes are missing showcase load-in coverage or pass card graphics.',
            missing=missing_graphics_passes,
            per_pass={key: {'graphics_load_in_ready': value['graphics_load_in_ready'], 'missing_card_images': value['missing_card_images']} for key, value in per_pass.items()},
        )
    )

    checks.append(
        make_check(
            'pass_feature_completion',
            summarize_status(pass_feature_statuses),
            'Per-pass Bango feature payloads are coherent and complete for current runtime delivery.' if not incomplete_feature_passes else 'Some PlayNOW passes are missing expected feature-completion inputs.',
            incomplete=incomplete_feature_passes,
            per_pass={key: {'feature_complete': value['feature_complete'], 'missing_required_paths': value['missing_required_paths'], 'notes': value['notes']} for key, value in per_pass.items()},
        )
    )

    finalstage_paths = playnow_finalstage.get('engine_manifests', {}) if isinstance(playnow_finalstage, dict) and isinstance(playnow_finalstage.get('engine_manifests'), dict) else {}
    finalstage_status = existing_path_map(finalstage_paths)
    missing_finalstage = [name for name, payload in finalstage_status.items() if not payload['exists']]
    checks.append(
        make_check(
            'finalstage_engine_handoffs',
            'pass' if not missing_finalstage else 'fail',
            'Finalstage references all engine handoff manifests.' if not missing_finalstage else 'Finalstage is missing one or more engine handoff manifests.',
            engine_manifests=finalstage_status,
            missing=missing_finalstage,
        )
    )

    player = playnow_runtime.get('player', {}) if isinstance(playnow_runtime, dict) and isinstance(playnow_runtime.get('player'), dict) else {}
    player_paths = existing_path_map({'blend': player.get('blend'), 'glb': player.get('glb')})
    missing_player_assets = [name for name, payload in player_paths.items() if not payload['exists']]
    checks.append(
        make_check(
            'player_bundle_assets',
            'pass' if not missing_player_assets else 'warn',
            'PlayNOW player bundle references both blend and GLB assets.' if not missing_player_assets else 'PlayNOW player bundle is missing one or more referenced assets.',
            player_assets=player_paths,
        )
    )

    hybrid_preview_paths = hybrid_runtime.get('preview_artifacts', {}) if isinstance(hybrid_runtime, dict) and isinstance(hybrid_runtime.get('preview_artifacts'), dict) else {}
    preview_status = existing_path_map(hybrid_preview_paths)
    missing_previews = [name for name, payload in preview_status.items() if not payload['exists']]
    checks.append(
        make_check(
            'hybrid_preview_artifacts',
            'pass' if not missing_previews else 'warn',
            'Hybrid runtime preview artifacts exist.' if not missing_previews else 'Hybrid runtime preview artifacts are incomplete.',
            preview_artifacts=preview_status,
        )
    )

    summary_runs = sorted(summary.get('runs', {}).keys()) if isinstance(summary, dict) and isinstance(summary.get('runs'), dict) else []
    expected_run_keys = list(summary_key_aliases.values()) + ['playable_package']
    missing_summary_runs = [name for name in expected_run_keys if name not in summary_runs]
    summary_status = 'pass' if not missing_integration_passes else 'warn'
    checks.append(
        make_check(
            'summary_run_coverage',
            summary_status,
            'Live pass integration manifests cover the full BangoNOW runtime set; summary gaps are advisory only.' if not missing_integration_passes else 'Some runtime passes do not have corresponding integration manifests staged under PlayNOW.',
            present=summary_runs,
            missing=missing_summary_runs,
            missing_integration_manifests=missing_integration_passes,
        )
    )

    status_rank = {'pass': 0, 'warn': 1, 'fail': 2}
    overall_status = 'pass'
    for check in checks:
        if status_rank[check['status']] > status_rank[overall_status]:
            overall_status = check['status']

    report = {
        'overall_status': overall_status,
        'asset_root': str(asset_root),
        'package_manifest': str(package_path),
        'summary_manifest': str(summary_path),
        'runtime_passes': runtime_pass_labels,
        'showcase_scene_entry_count': len(showcase_scene_entries),
        'per_pass': per_pass,
        'checks': checks,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate BangoNOW -> PlayNOW -> DODO pipeline coherence for the launcher.')
    parser.add_argument('--asset-root', type=Path)
    args = parser.parse_args()
    asset_root = args.asset_root.resolve() if args.asset_root else resolve_bango_asset_root()
    report = validate(asset_root)
    print(json.dumps(report, indent=2))
    return 0 if report['overall_status'] != 'fail' else 1


if __name__ == '__main__':
    raise SystemExit(main())