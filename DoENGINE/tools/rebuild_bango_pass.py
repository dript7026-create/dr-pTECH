from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

_bango_paths = __import__('bango_integration_paths')
resolve_bango_asset_root = _bango_paths.resolve_bango_asset_root
resolve_bango_project_root = _bango_paths.resolve_bango_project_root
resolve_playnow_runtime_path = _bango_paths.resolve_playnow_runtime_path

PREVIEW_OUTPUT = ROOT / 'generated' / 'dodogame_gui' / 'dodo_engine_preview.png'
PASS_PREVIEW_DIR = ROOT / 'generated' / 'dodogame_gui' / 'pass_previews'
PASS_REPORT_DIR = ROOT / 'generated' / 'dodogame_gui' / 'pass_rebuild_reports'
SHOWCASE_PATH = ROOT / 'generated' / 'dodogame_bangonow_showcase.json'


def load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding='utf-8'))


def run_command(command: list[str]) -> dict:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    return {
        'command': ' '.join(command),
        'returncode': result.returncode,
        'stdout': result.stdout,
        'stderr': result.stderr,
    }


def focus_orbit_for_pass(pass_label: str) -> float:
    showcase = load_json(SHOWCASE_PATH)
    if not isinstance(showcase, dict):
        return 0.58
    scene_entries = showcase.get('scene_entries', []) if isinstance(showcase.get('scene_entries'), list) else []
    positions: list[list[float]] = []
    for entry in scene_entries:
        if not isinstance(entry, dict):
            continue
        metadata = entry.get('metadata', {}) if isinstance(entry.get('metadata'), dict) else {}
        if metadata.get('pass_label') != pass_label:
            continue
        position = entry.get('position')
        if isinstance(position, list) and len(position) >= 3:
            positions.append(position)
    if not positions:
        return 0.58
    average_x = sum(float(position[0]) for position in positions) / len(positions)
    return round(0.56 + max(-0.9, min(0.9, average_x / 10.0)) * 0.7, 3)


def pass_asset_manifest(playnow_runtime: dict, pass_label: str) -> str | None:
    for entry in playnow_runtime.get('passes', []):
        if not isinstance(entry, dict):
            continue
        if entry.get('pass_label') == pass_label:
            value = entry.get('asset_manifest')
            return str(value) if value else None
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description='Rebuild a selected BangoNOW pass and refresh DODO-facing generated state.')
    parser.add_argument('--pass-label', required=True)
    parser.add_argument('--asset-root', type=Path)
    args = parser.parse_args()

    pass_label = args.pass_label.strip()
    allowed = {'humble', 'combat16', 'tutorial32', 'tutorial_final_preview', 'dodogame'}
    if pass_label not in allowed:
        raise SystemExit(f'Unsupported pass label: {pass_label}')

    asset_root = args.asset_root.resolve() if args.asset_root else resolve_bango_asset_root()
    bango_project_root = resolve_bango_project_root()
    playnow_runtime = load_json(resolve_playnow_runtime_path(asset_root))
    if not isinstance(playnow_runtime, dict):
        playnow_runtime = {'passes': []}

    playnow_command = [
        sys.executable,
        str(bango_project_root / 'tools' / 'run_playnow.py'),
        '--asset-root',
        str(asset_root),
        '--pass-label',
        pass_label,
    ]
    asset_manifest = pass_asset_manifest(playnow_runtime, pass_label)
    if asset_manifest:
        playnow_command.extend(['--asset-manifest', asset_manifest])
    if pass_label == 'dodogame':
        playnow_command.append('--skip-autorig')

    PASS_PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    PASS_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    pass_preview_output = PASS_PREVIEW_DIR / f'{pass_label}.png'
    pass_preview_json = PASS_PREVIEW_DIR / f'{pass_label}.json'
    focus_orbit = focus_orbit_for_pass(pass_label)

    steps = {
        'playnow': run_command(playnow_command),
        'showcase': run_command([sys.executable, str(ROOT / 'tools' / 'build_bangonow_showcase.py')]),
        'hybrid_runtime': run_command([sys.executable, str(ROOT / 'tools' / 'build_dodo_hybrid_runtime.py')]),
        'windows_bundle': run_command([sys.executable, str(ROOT / 'tools' / 'build_dodo_windows_bundle.py'), '--asset-root', str(asset_root)]),
        'pipeline_verify': run_command([sys.executable, str(ROOT / 'tools' / 'validate_bango_pipeline.py')]),
        'preview': run_command([sys.executable, str(ROOT / 'apps' / 'dodogame.py'), '--render-engine-preview', str(PREVIEW_OUTPUT)]),
        'pass_preview': run_command([
            sys.executable,
            str(ROOT / 'apps' / 'dodogame.py'),
            '--render-engine-preview',
            str(pass_preview_output),
            '--orbit',
            str(focus_orbit),
            '--elevation',
            '0.2',
            '--shader-mix',
            '0.9',
        ]),
    }
    worst_code = max(step.get('returncode', 0) for step in steps.values())
    pass_preview_payload = None
    if pass_preview_output.exists() and 'stdout' in steps['pass_preview']:
        try:
            pass_preview_payload = json.loads(steps['pass_preview']['stdout'])
        except json.JSONDecodeError:
            pass_preview_payload = load_json(pass_preview_output.with_suffix('.json'))
        if isinstance(pass_preview_payload, dict):
            pass_preview_json.write_text(json.dumps(pass_preview_payload, indent=2), encoding='utf-8')
    status = 'pass' if worst_code == 0 else 'fail'
    payload = {
        'pass_label': pass_label,
        'asset_root': str(asset_root),
        'status': status,
        'completed_at': datetime.now(timezone.utc).isoformat(),
        'pass_preview_output': str(pass_preview_output),
        'pass_preview_report': str(pass_preview_json),
        'focus_orbit': focus_orbit,
        'pass_preview_payload': pass_preview_payload,
        'steps': steps,
    }
    report_path = PASS_REPORT_DIR / f'{pass_label}.json'
    report_path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(json.dumps(payload, indent=2))
    return worst_code


if __name__ == '__main__':
    raise SystemExit(main())