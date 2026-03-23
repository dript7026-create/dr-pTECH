from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bango_integration_paths import resolve_bango_asset_root, resolve_playnow_dir, resolve_playnow_finalstage_path, resolve_playnow_runtime_path


BUNDLE_ROOT = ROOT / 'generated' / 'windows_bundle'


def run_command(command: list[str]) -> dict:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    return {
        'command': ' '.join(command),
        'returncode': result.returncode,
        'stdout': result.stdout,
        'stderr': result.stderr,
    }


def stage_file(source: Path, destination: Path) -> bool:
    if not source.exists():
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return True


def stage_tree(source: Path, destination: Path) -> bool:
    if not source.exists():
        return False
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description='Build a Windows-launchable DODOGame/DoENGINE bundle')
    parser.add_argument('--asset-root', type=Path)
    args = parser.parse_args()

    asset_root = args.asset_root.resolve() if args.asset_root else resolve_bango_asset_root()
    BUNDLE_ROOT.mkdir(parents=True, exist_ok=True)

    hybrid_runtime = run_command([sys.executable, str(ROOT / 'tools' / 'build_dodo_hybrid_runtime.py'), '--asset-root', str(asset_root)])

    staged = {
        'dodogame_launcher': {
            'source': str(ROOT / 'DODOGame.cmd'),
            'staged_path': str(BUNDLE_ROOT / 'DODOGame.cmd'),
            'exists': stage_file(ROOT / 'DODOGame.cmd', BUNDLE_ROOT / 'DODOGame.cmd'),
        },
        'doengine_studio_launcher': {
            'source': str(ROOT / 'DoENGINEStudio.cmd'),
            'staged_path': str(BUNDLE_ROOT / 'DoENGINEStudio.cmd'),
            'exists': stage_file(ROOT / 'DoENGINEStudio.cmd', BUNDLE_ROOT / 'DoENGINEStudio.cmd'),
        },
        'apps': {
            'source': str(ROOT / 'apps'),
            'staged_path': str(BUNDLE_ROOT / 'apps'),
            'exists': stage_tree(ROOT / 'apps', BUNDLE_ROOT / 'apps'),
        },
        'tools': {
            'source': str(ROOT / 'tools'),
            'staged_path': str(BUNDLE_ROOT / 'tools'),
            'exists': stage_tree(ROOT / 'tools', BUNDLE_ROOT / 'tools'),
        },
        'generated_gui': {
            'source': str(ROOT / 'generated' / 'dodogame_gui'),
            'staged_path': str(BUNDLE_ROOT / 'generated' / 'dodogame_gui'),
            'exists': stage_tree(ROOT / 'generated' / 'dodogame_gui', BUNDLE_ROOT / 'generated' / 'dodogame_gui'),
        },
        'bango_integration_paths': {
            'source': str(ROOT / 'bango_integration_paths.py'),
            'staged_path': str(BUNDLE_ROOT / 'bango_integration_paths.py'),
            'exists': stage_file(ROOT / 'bango_integration_paths.py', BUNDLE_ROOT / 'bango_integration_paths.py'),
        },
        'hybrid_runtime_profile': {
            'source': str(ROOT / 'generated' / 'dodogame_hybrid_runtime.json'),
            'staged_path': str(BUNDLE_ROOT / 'generated' / 'dodogame_hybrid_runtime.json'),
            'exists': stage_file(ROOT / 'generated' / 'dodogame_hybrid_runtime.json', BUNDLE_ROOT / 'generated' / 'dodogame_hybrid_runtime.json'),
        },
        'playnow_runtime_manifest': {
            'source': str(resolve_playnow_runtime_path(asset_root)),
            'staged_path': str(BUNDLE_ROOT / 'playnow' / 'playnow_runtime_manifest.json'),
            'exists': stage_file(resolve_playnow_runtime_path(asset_root), BUNDLE_ROOT / 'playnow' / 'playnow_runtime_manifest.json'),
        },
        'playnow_finalstage_manifest': {
            'source': str(resolve_playnow_finalstage_path(asset_root)),
            'staged_path': str(BUNDLE_ROOT / 'playnow' / 'playnow_finalstage_manifest.json'),
            'exists': stage_file(resolve_playnow_finalstage_path(asset_root), BUNDLE_ROOT / 'playnow' / 'playnow_finalstage_manifest.json'),
        },
        'playnow_manifest_directory': {
            'source': str(resolve_playnow_dir(asset_root)),
            'staged_path': str(BUNDLE_ROOT / 'playnow' / 'manifests'),
            'exists': stage_tree(resolve_playnow_dir(asset_root), BUNDLE_ROOT / 'playnow' / 'manifests'),
        },
    }

    bundle_manifest = {
        'system': 'DODOGame Windows Bundle',
        'asset_root': str(asset_root),
        'bundle_root': str(BUNDLE_ROOT),
        'native_executable_bundler_available': bool(shutil.which('pyinstaller')),
        'hybrid_runtime': hybrid_runtime,
        'launchers': staged,
        'windows_launch_ready': staged['dodogame_launcher']['exists'] and staged['doengine_studio_launcher']['exists'],
    }
    manifest_path = BUNDLE_ROOT / 'dodogame_windows_bundle.json'
    manifest_path.write_text(json.dumps(bundle_manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'path': str(manifest_path), **bundle_manifest}, indent=2))
    return hybrid_runtime.get('returncode', 0)


if __name__ == '__main__':
    raise SystemExit(main())