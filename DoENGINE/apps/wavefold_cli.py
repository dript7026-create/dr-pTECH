from __future__ import annotations

import argparse
import json
from pathlib import Path

from wavefold_format import encode_obj_to_wavefold


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Encode OBJ geometry into WaveFold format.')
    parser.add_argument('input_obj', type=Path, help='Source OBJ mesh path')
    parser.add_argument('output_wavefold', type=Path, help='Destination WaveFold JSON path')
    parser.add_argument('--name', help='Optional mesh name override')
    parser.add_argument('--material', default='stone', help='Default material name')
    parser.add_argument('--axis', default='y', choices=['x', 'y', 'z'], help='Primary fold axis')
    parser.add_argument('--amplitude', type=float, default=0.24, help='Fold amplitude for premium mode')
    parser.add_argument('--frequency', type=float, default=1.35, help='Wave frequency for fold shaping')
    parser.add_argument('--phase-bias', type=float, default=0.0, help='Phase bias in radians')
    parser.add_argument('--inward-bias', type=float, default=0.18, help='Inward radial fold bias')
    parser.add_argument('--premium-feature', default='wavefold.pro', help='Capability feature required for full fold behavior')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = encode_obj_to_wavefold(
        args.input_obj.resolve(),
        args.output_wavefold.resolve(),
        name=args.name,
        default_material=args.material,
        wave_space={
            'axis': args.axis,
            'amplitude': args.amplitude,
            'frequency': args.frequency,
            'phase_bias': args.phase_bias,
            'inward_bias': args.inward_bias,
            'premium_feature': args.premium_feature,
        },
    )
    print(json.dumps({'output': str(args.output_wavefold), 'name': payload['name'], 'schema': payload['schema']}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
