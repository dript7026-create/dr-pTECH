import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

try:
    from PIL import Image
except Exception:
    Image = None


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def resolve_output(manifest_path: Path, item: dict) -> Path:
    out_path = Path(item['out'])
    if out_path.is_absolute():
        return out_path
    return (manifest_path.parent / out_path).resolve()


def image_size(path: Path):
    if Image is None or not path.exists():
        return None, None
    with Image.open(path) as img:
        return img.size


def build_package_manifest(manifest_path: Path, items: list[dict]) -> dict:
    packaged = []
    missing = []

    for item in items:
        abs_path = resolve_output(manifest_path, item)
        if not abs_path.exists():
            missing.append({
                'name': item.get('name'),
                'expected_path': str(abs_path)
            })
            continue

        width, height = image_size(abs_path)
        packaged.append({
            'name': item.get('name'),
            'category': item.get('category', ''),
            'entity': item.get('entity', ''),
            'farim_layer': item.get('farim_layer', ''),
            'joint_anchors': item.get('joint_anchors', {}),
            'palette_target': item.get('palette_target', ''),
            'source_manifest_out': item.get('out'),
            'archive_path': f"assets/{item.get('name')}{abs_path.suffix.lower()}",
            'sha256': sha256_of(abs_path),
            'width': width,
            'height': height,
            'size_bytes': abs_path.stat().st_size,
        })

    return {
        'format': 'farim',
        'format_version': '0.1',
        'description': 'Initial SKAZKA Terranova FluidAnimationRealityInteractiveMedia asset bundle.',
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'runtime_note': 'This FARIM package is currently a ZIP-based asset bundle with metadata. It is not yet an encrypted browser runtime.',
        'manifest_source': str(manifest_path),
        'assets': packaged,
        'missing_assets': missing,
    }


def build_anchor_csv(package_manifest: dict) -> str:
    lines = [
        'name,anchor_name,x,y'
    ]
    for asset in package_manifest['assets']:
        anchors = asset.get('joint_anchors', {}) or {}
        for anchor_name, coords in anchors.items():
            if not isinstance(coords, list) or len(coords) != 2:
                continue
            lines.append(f"{asset['name']},{anchor_name},{coords[0]},{coords[1]}")
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    items = json.loads(manifest_path.read_text(encoding='utf-8'))
    package_manifest = build_package_manifest(manifest_path, items)

    with ZipFile(output_path, 'w', compression=ZIP_DEFLATED) as archive:
        archive.writestr('farim_manifest.json', json.dumps(package_manifest, indent=2))
        archive.writestr('runtime_anchors.csv', build_anchor_csv(package_manifest))
        for asset in package_manifest['assets']:
            src = resolve_output(manifest_path, next(item for item in items if item.get('name') == asset['name']))
            archive.write(src, asset['archive_path'])

    print(f"Wrote {output_path}")
    print(f"Packaged assets: {len(package_manifest['assets'])}")
    print(f"Missing assets: {len(package_manifest['missing_assets'])}")


if __name__ == '__main__':
    main()
