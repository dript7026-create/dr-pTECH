from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = ROOT.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from apps.dodo_engine3d import DodoPseudo3DEngine


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')


def resolve_path(base: Path, value: object) -> Path | None:
    if not value:
        return None
    candidate = Path(str(value))
    if candidate.is_absolute():
        return candidate
    return (base / candidate).resolve()


def load_bridge_module(path: Path):
    if str(path.parent) not in sys.path:
        sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Unable to load gameplay bridge: {path}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DodoGameProject:
    def __init__(self, profile_path: Path) -> None:
        self.profile_path = profile_path.resolve()
        self.profile = read_json(self.profile_path)
        self.package_path = resolve_path(self.profile_path.parent, self.profile.get('game_package_manifest'))
        self.package = read_json(self.package_path) if self.package_path and self.package_path.exists() else {}
        self.bindings = self.package.get('gameplay_bindings', {}) if isinstance(self.package.get('gameplay_bindings', {}), dict) else {}
        self.scene_manifest_path = resolve_path(self.profile_path.parent, self.profile.get('scene_manifest'))
        if self.scene_manifest_path is None and self.package:
            self.scene_manifest_path = resolve_path(self.package_path.parent, self.package.get('scene_manifest'))
        if self.scene_manifest_path is None:
            raise FileNotFoundError(f'No scene manifest declared for {self.profile_path}')
        self.engine = DodoPseudo3DEngine(scene_manifest_path=self.scene_manifest_path)
        self.bridge = self._load_bridge()
        self.gameplay_state = self._load_initial_gameplay_state()
        self._refresh_engine_state()

    def _load_bridge(self):
        bridge_path = None
        factory_name = 'create_bridge'
        if isinstance(self.package.get('gameplay_bridge'), dict):
            bridge_path = resolve_path(self.package_path.parent, self.package['gameplay_bridge'].get('path'))
            factory_name = str(self.package['gameplay_bridge'].get('factory', factory_name))
        elif self.profile.get('gameplay_bridge'):
            bridge_path = resolve_path(self.profile_path.parent, self.profile.get('gameplay_bridge'))
        if bridge_path is None or not bridge_path.exists():
            return None
        module = load_bridge_module(bridge_path)
        factory = getattr(module, factory_name, None)
        if factory is None:
            raise AttributeError(f'Gameplay bridge factory {factory_name} not found in {bridge_path}')
        return factory(self.package or self.profile)

    def _load_initial_gameplay_state(self) -> dict:
        default_save_path = self.default_save_path
        if default_save_path is not None and default_save_path.exists():
            payload = read_json(default_save_path)
            if isinstance(payload.get('gameplay_state'), dict):
                return dict(payload['gameplay_state'])
        if self.bridge is not None and hasattr(self.bridge, 'create_initial_state'):
            return dict(self.bridge.create_initial_state())
        return {}

    @property
    def default_preview_path(self) -> Path:
        preview_dir = self.profile_path.parent / 'previews'
        return preview_dir / f"{self.profile.get('game_id', self.profile_path.parent.name)}_preview.png"

    @property
    def default_demo_save_dir(self) -> Path:
        return self.profile_path.parent / 'saves' / 'demo'

    @property
    def default_save_path(self) -> Path | None:
        if self.package_path is not None and self.package.get('default_save_path'):
            return resolve_path(self.package_path.parent, self.package.get('default_save_path'))
        if self.profile.get('default_save_path'):
            return resolve_path(self.profile_path.parent, self.profile.get('default_save_path'))
        return None

    def _build_runtime_overrides(self, gameplay_state: dict | None = None) -> dict:
        if self.bridge is not None and hasattr(self.bridge, 'build_runtime_overrides'):
            return dict(self.bridge.build_runtime_overrides(gameplay_state or self.gameplay_state, self.bindings))
        return {}

    def _build_bridge_scene_state(self, gameplay_state: dict | None = None) -> dict | None:
        if self.bridge is not None and hasattr(self.bridge, 'build_scene_state'):
            return dict(self.bridge.build_scene_state(gameplay_state or self.gameplay_state, self.bindings))
        return None

    def _refresh_engine_state(self) -> None:
        bridge_scene_state = self._build_bridge_scene_state()
        if bridge_scene_state:
            self.engine.apply_scene_state(bridge_scene_state)
        self.engine.set_runtime_overrides(self._build_runtime_overrides())

    def describe(self) -> dict:
        return {
            'game_id': self.profile.get('game_id'),
            'title': self.profile.get('title'),
            'scene_manifest': str(self.scene_manifest_path),
            'game_package_manifest': str(self.package_path) if self.package_path else None,
            'default_save_path': str(self.default_save_path) if self.default_save_path else None,
            'gameplay_bridge_loaded': self.bridge is not None,
            'registered_bindings': len(self.bindings),
            'bridge_supports_demo_states': bool(self.bridge is not None and hasattr(self.bridge, 'build_demo_states')),
            'bridge_supports_scene_state': bool(self.bridge is not None and hasattr(self.bridge, 'build_scene_state')),
            'runtime': self.engine.describe_runtime(),
        }

    def export_save_state(self) -> dict:
        self._refresh_engine_state()
        return {
            'save_version': 'doengine.game-state.v1',
            'game_id': self.profile.get('game_id'),
            'game_profile_manifest': str(self.profile_path),
            'game_package_manifest': str(self.package_path) if self.package_path else None,
            'scene_state': self.engine.export_scene_state(),
            'gameplay_state': self.gameplay_state,
            'runtime_overrides': self._build_runtime_overrides(),
        }

    def load_save_state(self, save_path: Path) -> dict:
        payload = read_json(save_path)
        scene_state = payload.get('scene_state')
        gameplay_state = payload.get('gameplay_state')
        if isinstance(gameplay_state, dict):
            self.gameplay_state = dict(gameplay_state)
        if isinstance(scene_state, dict):
            self.engine.apply_scene_state(scene_state)
        self._refresh_engine_state()
        return payload

    def _build_save_payload(self, gameplay_state: dict) -> dict:
        runtime_overrides = self._build_runtime_overrides(gameplay_state)
        engine = DodoPseudo3DEngine(scene_manifest_path=self.scene_manifest_path)
        bridge_scene_state = self._build_bridge_scene_state(gameplay_state)
        if bridge_scene_state:
            engine.apply_scene_state(bridge_scene_state)
        engine.set_runtime_overrides(runtime_overrides)
        return {
            'save_version': 'doengine.game-state.v1',
            'game_id': self.profile.get('game_id'),
            'game_profile_manifest': str(self.profile_path),
            'game_package_manifest': str(self.package_path) if self.package_path else None,
            'scene_state': engine.export_scene_state(),
            'gameplay_state': gameplay_state,
            'runtime_overrides': runtime_overrides,
        }

    def save(self, save_path: Path | None = None) -> Path:
        output_path = save_path or self.default_save_path
        if output_path is None:
            raise FileNotFoundError(f'No save path configured for {self.profile_path}')
        write_json(output_path, self.export_save_state())
        return output_path

    def write_preview(self, output_path: Path | None = None) -> Path:
        target_path = output_path or self.default_preview_path
        self._refresh_engine_state()
        self.engine.write_preview(target_path)
        return target_path

    def export_demo_saves(self, output_dir: Path | None = None) -> dict:
        if self.bridge is None or not hasattr(self.bridge, 'build_demo_states'):
            raise RuntimeError(f'No demo-state bridge available for {self.profile_path}')
        target_dir = output_dir or self.default_demo_save_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        stages = []
        for index, entry in enumerate(self.bridge.build_demo_states(), start=1):
            if not isinstance(entry, dict):
                continue
            stage_id = str(entry.get('save_name', f'demo_stage_{index:02d}'))
            gameplay_state = entry.get('gameplay_state')
            if not isinstance(gameplay_state, dict):
                continue
            save_path = target_dir / f'{stage_id}.json'
            write_json(save_path, self._build_save_payload(gameplay_state))
            stages.append({'id': stage_id, 'label': str(entry.get('label', stage_id)), 'save_path': str(save_path)})
        manifest_path = target_dir / 'demo_manifest.json'
        write_json(
            manifest_path,
            {
                'game_id': self.profile.get('game_id'),
                'title': self.profile.get('title'),
                'stage_count': len(stages),
                'stages': stages,
            },
        )
        return {'output_dir': str(target_dir), 'demo_manifest': str(manifest_path), 'stage_count': len(stages), 'stages': stages}


def main() -> int:
    parser = argparse.ArgumentParser(description='Load and save a standalone DoENGINE game project package.')
    parser.add_argument('--game-profile', type=Path, required=True)
    parser.add_argument('--describe', action='store_true')
    parser.add_argument('--load-save', type=Path)
    parser.add_argument('--save-state', type=Path, nargs='?', const=Path(''))
    parser.add_argument('--write-preview', type=Path, nargs='?', const=Path(''))
    parser.add_argument('--export-demo-saves', type=Path, nargs='?', const=Path(''))
    args = parser.parse_args()

    project = DodoGameProject(args.game_profile)
    if args.load_save is not None:
        project.load_save_state(args.load_save.resolve())
    result: dict[str, object] = {}
    if args.describe:
        result['project'] = project.describe()
    if args.save_state is not None:
        save_path = args.save_state.resolve() if str(args.save_state) else None
        result['saved_state'] = str(project.save(save_path))
    if args.write_preview is not None:
        preview_path = args.write_preview.resolve() if str(args.write_preview) else None
        result['preview'] = str(project.write_preview(preview_path))
    if args.export_demo_saves is not None:
        demo_dir = args.export_demo_saves.resolve() if str(args.export_demo_saves) else None
        result['demo_saves'] = project.export_demo_saves(demo_dir)
    if not result:
        result = project.describe()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())