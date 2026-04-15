from __future__ import annotations

import base64
import json
import math
import struct
import zlib
from pathlib import Path


DEFAULT_MATERIAL_LIBRARY = {
    'stone': {'name': 'stone', 'color': [168, 132, 92]},
    'amber': {'name': 'amber', 'color': [203, 148, 92]},
    'jade': {'name': 'jade', 'color': [96, 132, 116]},
    'bone': {'name': 'bone', 'color': [228, 210, 176]},
    'shadow': {'name': 'shadow', 'color': [110, 87, 71]},
}


def parse_obj_geometry(path: Path) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int]] = []
    for raw_line in path.read_text(encoding='utf-8', errors='ignore').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('v '):
            _, x, y, z = line.split()[:4]
            vertices.append((float(x), float(y), float(z)))
            continue
        if not line.startswith('f '):
            continue
        indices: list[int] = []
        for part in line.split()[1:]:
            head = part.split('/')[0]
            if head:
                indices.append(int(head) - 1)
        if len(indices) < 3:
            continue
        for start in range(1, len(indices) - 1):
            faces.append((indices[0], indices[start], indices[start + 1]))
    if not vertices or not faces:
        raise ValueError(f'OBJ geometry was empty or invalid: {path}')
    return vertices, faces


def _pack_records(format_string: str, records: list[tuple[int, ...]]) -> str:
    raw = b''.join(struct.pack(format_string, *record) for record in records)
    return base64.b64encode(zlib.compress(raw, level=9)).decode('ascii')


def _unpack_records(format_string: str, count: int, encoded: str) -> list[tuple[int, ...]]:
    raw = zlib.decompress(base64.b64decode(encoded))
    stride = struct.calcsize(format_string)
    return [struct.unpack_from(format_string, raw, index * stride) for index in range(count)]


def _build_fold_phase(vertex: tuple[float, float, float]) -> float:
    x, y, z = vertex
    return math.atan2(z, x) + y * 0.35


def encode_wavefold_payload(
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, int, int]],
    *,
    name: str,
    default_material: str = 'stone',
    position_step: float = 0.01,
    fold_step: float = 0.02,
    wave_space: dict | None = None,
) -> dict:
    material_record = DEFAULT_MATERIAL_LIBRARY.get(default_material, DEFAULT_MATERIAL_LIBRARY['stone'])
    vertex_records: list[tuple[int, int, int, int]] = []
    face_records: list[tuple[int, int, int, int, int]] = []
    for vertex in vertices:
        fold_phase = _build_fold_phase(vertex)
        vertex_records.append(
            (
                int(round(vertex[0] / position_step)),
                int(round(vertex[1] / position_step)),
                int(round(vertex[2] / position_step)),
                int(round(fold_phase / fold_step)),
            )
        )
    for face in faces:
        face_records.append((int(face[0]), int(face[1]), int(face[2]), 0, 0))
    return {
        'schema': 'wavefold_geometry/v1',
        'name': name,
        'encoding': 'base64+zlib',
        'position_step': position_step,
        'fold_step': fold_step,
        'vertex_pack': {
            'format': '<hhhh',
            'count': len(vertex_records),
            'data': _pack_records('<hhhh', vertex_records),
        },
        'face_pack': {
            'format': '<HHHBB',
            'count': len(face_records),
            'data': _pack_records('<HHHBB', face_records),
        },
        'materials': [material_record],
        'wave_space': wave_space or {
            'axis': 'y',
            'amplitude': 0.24,
            'frequency': 1.35,
            'phase_bias': 0.0,
            'inward_bias': 0.18,
            'premium_feature': 'wavefold.pro',
        },
    }


def write_wavefold_payload(payload: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')


def encode_obj_to_wavefold(input_path: Path, output_path: Path, *, name: str | None = None, default_material: str = 'stone', wave_space: dict | None = None) -> dict:
    vertices, faces = parse_obj_geometry(input_path)
    payload = encode_wavefold_payload(
        vertices,
        faces,
        name=name or input_path.stem,
        default_material=default_material,
        wave_space=wave_space,
    )
    write_wavefold_payload(payload, output_path)
    return payload


def load_wavefold_payload(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(payload, dict) or payload.get('schema') != 'wavefold_geometry/v1':
        raise ValueError(f'Unsupported WaveFold payload: {path}')
    return payload


def decode_wavefold_payload(payload: dict, *, premium_enabled: bool = False, capability_limits: dict | None = None) -> dict:
    position_step = float(payload.get('position_step', 0.01))
    fold_step = float(payload.get('fold_step', 0.02))
    capability_limits = capability_limits or {}
    vertex_pack = payload['vertex_pack']
    face_pack = payload['face_pack']
    materials = payload.get('materials', [])
    if not isinstance(materials, list) or not materials:
        materials = [DEFAULT_MATERIAL_LIBRARY['stone']]
    wave_space = dict(payload.get('wave_space', {}))
    required_feature = str(wave_space.get('premium_feature', '')).strip()
    amplitude = float(wave_space.get('amplitude', 0.18))
    inward_bias = float(wave_space.get('inward_bias', 0.12))
    frequency = float(wave_space.get('frequency', 1.0))
    phase_bias = float(wave_space.get('phase_bias', 0.0))
    axis = str(wave_space.get('axis', 'y')).lower()
    if required_feature and not premium_enabled:
        amplitude = min(amplitude, float(capability_limits.get('fallback_fold_amplitude', 0.08)))
        inward_bias = min(inward_bias, float(capability_limits.get('fallback_inward_bias', 0.05)))
    if premium_enabled and 'max_fold_amplitude' in capability_limits:
        amplitude = min(amplitude, float(capability_limits['max_fold_amplitude']))

    decoded_vertices: list[tuple[float, float, float]] = []
    for x_q, y_q, z_q, phase_q in _unpack_records(str(vertex_pack['format']), int(vertex_pack['count']), str(vertex_pack['data'])):
        x = x_q * position_step
        y = y_q * position_step
        z = z_q * position_step
        phase = phase_q * fold_step + phase_bias
        axis_value = y if axis == 'y' else x if axis == 'x' else z
        wave = math.sin(axis_value * frequency + phase) * amplitude
        radial_x = x
        radial_z = z
        radial_length = math.sqrt(radial_x * radial_x + radial_z * radial_z)
        if radial_length > 1e-6:
            inward_scale = inward_bias * (0.55 + 0.45 * math.cos(axis_value * frequency + phase))
            x -= (radial_x / radial_length) * inward_scale
            z -= (radial_z / radial_length) * inward_scale
        if axis == 'x':
            x += wave
        elif axis == 'z':
            z += wave
        else:
            y += wave
        decoded_vertices.append((x, y, z))

    decoded_faces: list[dict] = []
    for a, b, c, material_index, _reserved in _unpack_records(str(face_pack['format']), int(face_pack['count']), str(face_pack['data'])):
        material = materials[min(int(material_index), len(materials) - 1)]
        decoded_faces.append(
            {
                'indices': (int(a), int(b), int(c)),
                'color': tuple(int(channel) for channel in material.get('color', [168, 132, 92])),
                'material': str(material.get('name', 'stone')),
            }
        )
    return {
        'name': str(payload.get('name', 'wavefold_mesh')),
        'vertices': decoded_vertices,
        'faces': decoded_faces,
        'wave_space': {
            'required_feature': required_feature,
            'premium_enabled': premium_enabled,
            'axis': axis,
            'amplitude': amplitude,
            'frequency': frequency,
            'inward_bias': inward_bias,
        },
    }
