from __future__ import annotations

import argparse
import json
from pathlib import Path


HEADER_NAME = 'bango_asset_bootstrap.h'
SOURCE_NAME = 'bango_asset_bootstrap.c'


def load_registry(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def build_header() -> str:
    return """#ifndef BANGO_ASSET_BOOTSTRAP_H
#define BANGO_ASSET_BOOTSTRAP_H

typedef struct BangoGeneratedAssetDef {
    const char *asset_id;
    const char *category;
    const char *path;
    const char *generation_mode;
} BangoGeneratedAssetDef;

extern const BangoGeneratedAssetDef g_bango_generated_assets[];
extern const int g_bango_generated_asset_count;

void Bango_RegisterGeneratedAssets(void);
const BangoGeneratedAssetDef *Bango_FindGeneratedAsset(const char *asset_id);

#endif
"""


def build_source(registry: dict) -> str:
    lines = [
        '#include "g_local.h"',
        '#include "bango_asset_bootstrap.h"',
        '',
        '#include <string.h>',
        '',
        'const BangoGeneratedAssetDef g_bango_generated_assets[] = {',
    ]
    for asset in registry.get('assets', []):
        lines.append(
            '    {'
            f' "{asset["asset_id"]}", "{asset["category"]}", "{asset["asset_root"]}", "{asset.get("generation_mode", "packed_master")}" '
            '},'
        )
    lines.extend(
        [
            '};',
            f'const int g_bango_generated_asset_count = {len(registry.get("assets", []))};',
            '',
            'void Bango_RegisterGeneratedAssets(void) {',
            '#ifdef BANGO_Q2_RUNTIME_LINKED',
            '    gi.dprintf("Bango generated asset bootstrap loaded: %d assets.\\n", g_bango_generated_asset_count);',
            '#endif',
            '}',
            '',
            'const BangoGeneratedAssetDef *Bango_FindGeneratedAsset(const char *asset_id) {',
            '    int i;',
            '    if (!asset_id) return NULL;',
            '    for (i = 0; i < g_bango_generated_asset_count; ++i) {',
            '        if (strcmp(g_bango_generated_assets[i].asset_id, asset_id) == 0) return &g_bango_generated_assets[i];',
            '    }',
            '    return NULL;',
            '}',
            '',
        ]
    )
    return '\n'.join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description='Build idTech2 bootstrap code from the generated Bango registry')
    parser.add_argument('--registry', required=True, type=Path)
    parser.add_argument('--out-dir', required=True, type=Path)
    args = parser.parse_args()

    registry = load_registry(args.registry)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    header_path = args.out_dir / HEADER_NAME
    source_path = args.out_dir / SOURCE_NAME
    header_path.write_text(build_header(), encoding='utf-8')
    source_path.write_text(build_source(registry), encoding='utf-8')
    print(json.dumps({'header': str(header_path), 'source': str(source_path), 'asset_count': registry.get('asset_count', 0)}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())