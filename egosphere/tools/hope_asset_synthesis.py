from __future__ import annotations

import hashlib
import json
import math
import random
import struct
import wave
import zlib
from pathlib import Path


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _seed_for(*parts: object) -> int:
    digest = hashlib.sha256("::".join(str(part) for part in parts).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def _write_chunk(handle, chunk_type: bytes, data: bytes) -> None:
    handle.write(struct.pack(">I", len(data)))
    handle.write(chunk_type)
    handle.write(data)
    crc = zlib.crc32(chunk_type)
    crc = zlib.crc32(data, crc)
    handle.write(struct.pack(">I", crc & 0xFFFFFFFF))


def write_png(path: Path, width: int, height: int, rows: list[bytes]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(b"\x89PNG\r\n\x1a\n")
        ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
        _write_chunk(handle, b"IHDR", ihdr)
        raw = b"".join(b"\x00" + row for row in rows)
        _write_chunk(handle, b"IDAT", zlib.compress(raw, level=9))
        _write_chunk(handle, b"IEND", b"")


def _scene_palette(scene_type: str, hope: dict, family: dict) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
    sanctuary = float(family.get("sanctuary_strength", 0.3))
    theta = float(hope.get("theta", 0.2))
    pressure = float(hope.get("clog_risk", 0.3))
    if scene_type == "sanctuary":
        base = (int(110 + sanctuary * 70), int(125 + sanctuary * 60), int(145 + sanctuary * 65))
        accent = (int(200 - theta * 30), int(170 + sanctuary * 50), int(120 + sanctuary * 80))
        shadow = (50, 66, int(86 + pressure * 24))
    elif scene_type == "ritual_traverse":
        base = (int(82 + sanctuary * 40), int(88 + pressure * 28), int(122 + sanctuary * 46))
        accent = (int(166 + sanctuary * 45), int(136 + theta * 40), int(190 - pressure * 38))
        shadow = (44, 40, 76)
    else:
        base = (int(86 + pressure * 60), int(76 + theta * 44), int(102 + sanctuary * 30))
        accent = (int(186 + theta * 30), int(120 + pressure * 48), int(100 + sanctuary * 26))
        shadow = (48, 38, int(56 + pressure * 42))
    return base, accent, shadow


def synthesize_image_asset(
    path: Path,
    *,
    asset_id: str,
    asset_type: str,
    usage: str,
    scene_type: str,
    hope: dict,
    family: dict,
) -> None:
    rng = random.Random(_seed_for(asset_id, usage, scene_type))
    width, height = {
        "tileset": (128, 128),
        "sprite": (64, 64),
        "portrait": (96, 96),
    }.get(asset_type, (64, 64))
    base, accent, shadow = _scene_palette(scene_type, hope, family)
    theta = float(hope.get("theta", 0.0))
    sanctuary = float(family.get("sanctuary_strength", 0.25))
    misalignment = float(hope.get("frame_buffer_misalignment", 0.0))

    rows: list[bytes] = []
    for y in range(height):
        row = bytearray()
        for x in range(width):
            nx = x / max(width - 1, 1)
            ny = y / max(height - 1, 1)
            wave_term = math.sin((nx + ny + theta) * math.pi * (2.0 + sanctuary))
            glow = 0.5 + 0.5 * math.sin((nx * 3.0 + ny * 2.0 + misalignment * 1.7) * math.pi)
            r = int(base[0] * (1 - ny) + shadow[0] * ny + accent[0] * 0.18 * glow)
            g = int(base[1] * (1 - nx * 0.4) + shadow[1] * nx * 0.4 + accent[1] * 0.16 * glow)
            b = int(base[2] * (0.7 + 0.3 * glow) + accent[2] * 0.12 * wave_term)

            if asset_type == "tileset":
                tile_grid = ((x // 16) + (y // 16)) % 2
                trim = 26 if tile_grid else -8
                r += trim
                g += trim // 2
                b += trim
            elif asset_type == "sprite":
                center_x = (x - width / 2) / (width / 2)
                center_y = (y - height / 2) / (height / 2)
                silhouette = center_x * center_x * (1.0 + sanctuary) + center_y * center_y * 1.8
                if silhouette < 0.62:
                    r = int(accent[0] * 0.9 + 20 * glow)
                    g = int(accent[1] * 0.86 + 16 * glow)
                    b = int(accent[2] * 0.8 + 12 * glow)
                if usage == "world_anchor" and abs(center_x) < 0.12:
                    r = min(255, r + 46)
                    g = min(255, g + 30)
                    b = min(255, b + 58)
                if usage == "family_member" and center_y < -0.18 and abs(center_x) < 0.3:
                    r = min(255, r + 30)
                    g = min(255, g + 18)
            elif asset_type == "portrait":
                halo = math.hypot(nx - 0.5, ny - 0.43)
                if halo < 0.34:
                    r = int(accent[0] * (1.08 - halo))
                    g = int(accent[1] * (1.03 - halo * 0.6))
                    b = int(accent[2] * (1.08 - halo * 0.75))
                if 0.42 < ny < 0.5 and 0.3 < nx < 0.7:
                    r = min(255, r + 24)
                    g = min(255, g + 16)

            noise = rng.randint(-4, 4)
            row.extend(
                bytes(
                    [
                        _clamp(r + noise, 0, 255),
                        _clamp(g + noise, 0, 255),
                        _clamp(b + noise, 0, 255),
                        255,
                    ]
                )
            )
        rows.append(bytes(row))
    write_png(path, width, height, rows)


def synthesize_mesh_asset(path: Path, *, asset_id: str, usage: str, hope: dict, family: dict) -> None:
    rng = random.Random(_seed_for(asset_id, usage))
    complexity = float(hope.get("complexity_index", 20.0))
    sanctuary = float(family.get("sanctuary_strength", 0.2))
    theta = float(hope.get("theta", 0.15))
    grid = 8 if usage == "terrain" else 6
    amplitude = 0.12 + complexity / 240.0 - sanctuary * 0.04
    if usage == "sanctuary":
        amplitude *= 0.4

    lines = [f"o {asset_id}"]
    for z in range(grid):
        for x in range(grid):
            fx = x / (grid - 1)
            fz = z / (grid - 1)
            radial = math.hypot(fx - 0.5, fz - 0.5)
            if usage == "terrain":
                y = math.sin(fx * math.pi * 2.0 + theta) * amplitude + math.cos(fz * math.pi * 1.5) * amplitude * 0.6
            else:
                y = max(0.0, (0.45 - radial) * (0.6 + sanctuary * 0.7)) + math.sin((fx + fz) * math.pi) * 0.02
            y += rng.uniform(-0.01, 0.01)
            lines.append(f"v {fx - 0.5:.4f} {y:.4f} {fz - 0.5:.4f}")
            lines.append(f"vt {fx:.4f} {fz:.4f}")
            lines.append("vn 0.0 1.0 0.0")

    for z in range(grid - 1):
        for x in range(grid - 1):
            a = z * grid + x + 1
            b = a + 1
            c = a + grid
            d = c + 1
            lines.append(f"f {a}/{a}/{a} {c}/{c}/{c} {b}/{b}/{b}")
            lines.append(f"f {b}/{b}/{b} {c}/{c}/{c} {d}/{d}/{d}")

    if usage == "sanctuary":
        arch_start = grid * grid + 1
        lines.extend(
            [
                "v -0.2 0.0 -0.08",
                "v 0.2 0.0 -0.08",
                "v 0.2 0.34 -0.08",
                "v -0.2 0.34 -0.08",
                "v -0.2 0.0 0.08",
                "v 0.2 0.0 0.08",
                "v 0.2 0.34 0.08",
                "v -0.2 0.34 0.08",
            ]
        )
        lines.extend(["vt 0 0", "vt 1 0", "vt 1 1", "vt 0 1"] * 2)
        lines.extend(["vn 0 1 0"] * 8)
        lines.extend(
            [
                f"f {arch_start}/{arch_start}/{arch_start} {arch_start + 1}/{arch_start + 1}/{arch_start + 1} {arch_start + 2}/{arch_start + 2}/{arch_start + 1}",
                f"f {arch_start}/{arch_start}/{arch_start} {arch_start + 2}/{arch_start + 2}/{arch_start + 1} {arch_start + 3}/{arch_start + 3}/{arch_start + 1}",
            ]
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def synthesize_structure_asset(path: Path, *, asset_id: str, usage: str, scene_type: str, hope: dict, family: dict) -> None:
    rng = random.Random(_seed_for(asset_id, usage, scene_type, "structure"))
    theta = float(hope.get("theta", 0.2))
    sanctuary = float(family.get("sanctuary_strength", 0.25))
    scale = 0.7 + sanctuary * 0.45 + theta * 0.18
    is_architecture = usage == "architecture"

    if is_architecture:
        width = 0.9 * scale
        height = 1.2 * scale + sanctuary * 0.5
        depth = 0.28 * scale
        lines = [
            f"o {asset_id}",
            f"v {-width:.4f} 0.0000 {-depth:.4f}",
            f"v {width:.4f} 0.0000 {-depth:.4f}",
            f"v {width:.4f} {height:.4f} {-depth:.4f}",
            f"v {-width:.4f} {height:.4f} {-depth:.4f}",
            f"v {-width:.4f} 0.0000 {depth:.4f}",
            f"v {width:.4f} 0.0000 {depth:.4f}",
            f"v {width:.4f} {height:.4f} {depth:.4f}",
            f"v {-width:.4f} {height:.4f} {depth:.4f}",
            f"v 0.0000 {height + 0.35 * scale:.4f} 0.0000",
        ]
        lines.extend(["vt 0 0", "vt 1 0", "vt 1 1", "vt 0 1"] * 3)
        lines.extend(["vn 0 1 0"] * 10)
        lines.extend(
            [
                "f 1/1/1 2/2/1 3/3/1",
                "f 1/1/1 3/3/1 4/4/1",
                "f 5/1/1 6/2/1 7/3/1",
                "f 5/1/1 7/3/1 8/4/1",
                "f 4/1/1 3/2/1 9/3/1",
                "f 8/1/1 7/2/1 9/3/1",
            ]
        )
    else:
        radius = 0.22 * scale
        height = 0.35 * scale + sanctuary * 0.08
        lines = [f"o {asset_id}"]
        for step in range(8):
            angle = (math.pi * 2.0 * step) / 8.0
            x = math.cos(angle) * radius
            z = math.sin(angle) * radius
            lines.append(f"v {x:.4f} 0.0000 {z:.4f}")
            lines.append(f"v {x * 0.72:.4f} {height + rng.uniform(-0.03, 0.03):.4f} {z * 0.72:.4f}")
        lines.extend(["vt 0 0", "vt 1 0", "vt 1 1", "vt 0 1"] * 4)
        lines.extend(["vn 0 1 0"] * 16)
        for step in range(0, 16, 2):
            next_step = (step + 2) % 16
            lines.append(f"f {step + 1}/{step + 1}/{step + 1} {next_step + 1}/{next_step + 1}/{next_step + 1} {step + 2}/{step + 2}/{step + 2}")
        lines.append("v 0.0000 0.5200 0.0000")
        lines.extend(["vt 0.5 0.5", "vn 0 1 0"])

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def synthesize_material_asset(path: Path, *, asset_id: str, usage: str, hope: dict, family: dict) -> None:
    sanctuary = float(family.get("sanctuary_strength", 0.3))
    pressure = float(hope.get("clog_risk", 0.2))
    theta = float(hope.get("theta", 0.15))
    payload = {
        "id": asset_id,
        "usage": usage,
        "shader_family": "hope_layered_surface",
        "base_roughness": round(_clamp(0.42 + pressure * 0.24 - sanctuary * 0.12, 0.18, 0.88), 4),
        "emissive_gain": round(_clamp(0.08 + sanctuary * 0.42 - pressure * 0.06, 0.0, 0.7), 4),
        "detail_frequency": round(_clamp(0.4 + theta * 0.35 + pressure * 0.18, 0.25, 1.0), 4),
        "resonance_band": round(_clamp(family.get("resonance_relief", 0.2), 0.0, 1.0), 4),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def synthesize_physics_asset(path: Path, *, asset_id: str, usage: str, hope: dict, family: dict) -> None:
    solver_scale = float(hope.get("physics_plan", {}).get("solver_scale", 1.0))
    interaction_gate = float(hope.get("physics_plan", {}).get("interaction_gate", 1.0))
    payload = {
        "id": asset_id,
        "usage": usage,
        "solver_scale": round(solver_scale, 4),
        "interaction_gate": round(interaction_gate, 4),
        "movement_cushion": round(float(hope.get("physics_plan", {}).get("movement_cushion", 0.0)), 4),
        "sanctuary_bias": round(float(family.get("sanctuary_strength", 0.0)), 4),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def synthesize_audio_asset(path: Path, *, asset_id: str, usage: str, scene_type: str, hope: dict, family: dict) -> None:
    seed = _seed_for(asset_id, usage, scene_type)
    rng = random.Random(seed)
    sample_rate = 22050
    duration = 1.2
    frame_count = int(sample_rate * duration)
    sanctuary = float(family.get("sanctuary_strength", 0.25))
    pressure = float(hope.get("clog_risk", 0.2))
    theta = float(hope.get("theta", 0.15))
    base_freq = 220.0 + sanctuary * 90.0 + theta * 40.0
    pulse_freq = 0.4 + pressure * 1.3
    overtone = 330.0 + pressure * 110.0 if scene_type != "sanctuary" else 275.0 + sanctuary * 70.0

    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        frames = bytearray()
        for index in range(frame_count):
            t = index / sample_rate
            envelope = 0.65 + 0.35 * math.sin(t * math.pi * pulse_freq)
            drone = math.sin(2.0 * math.pi * base_freq * t)
            shimmer = 0.45 * math.sin(2.0 * math.pi * overtone * t + theta)
            breath = 0.14 * math.sin(2.0 * math.pi * (base_freq * 0.5) * t)
            noise = (rng.random() - 0.5) * 0.08 * pressure
            sample = (drone * 0.48 + shimmer * 0.28 + breath + noise) * envelope
            sample *= 0.42 + sanctuary * 0.12
            sample = max(-1.0, min(1.0, sample))
            frames.extend(struct.pack("<h", int(sample * 32767)))
        handle.writeframes(frames)


def synthesize_animation_asset(path: Path, *, asset_id: str, usage: str, scene_type: str, hope: dict, family: dict) -> None:
    theta = float(hope.get("theta", 0.15))
    sanctuary = float(family.get("sanctuary_strength", 0.22))
    tail_ms = float(hope.get("worst_case_tail_ms", 24.0))
    frame_count = 8 if usage == "movement" else 6
    cadence = max(8, min(18, int(10 + theta * 6 - sanctuary * 2)))
    amplitude = round(0.12 + theta * 0.22 + sanctuary * 0.08, 4)
    payload = {
        "id": asset_id,
        "usage": usage,
        "scene_type": scene_type,
        "fps": cadence,
        "frame_count": frame_count,
        "tail_influence_ms": round(tail_ms, 4),
        "channels": {
            "root_x": [round(math.sin((index / frame_count) * math.pi * 2.0) * amplitude, 4) for index in range(frame_count)],
            "root_y": [round(abs(math.sin((index / frame_count) * math.pi)) * amplitude * 0.42, 4) for index in range(frame_count)],
            "breath": [round(0.2 + sanctuary * 0.18 + math.cos(index * 0.7) * 0.04, 4) for index in range(frame_count)],
        },
        "events": [
            {"frame": 0, "name": "anticipate"},
            {"frame": frame_count // 2, "name": "resolve"},
            {"frame": frame_count - 1, "name": "recover"},
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def synthesize_ecology_asset(path: Path, *, asset_id: str, usage: str, scene_type: str, hope: dict, family: dict) -> None:
    pressure = float(hope.get("clog_risk", 0.2))
    theta = float(hope.get("theta", 0.15))
    sanctuary = float(family.get("sanctuary_strength", 0.22))
    resonance = float(family.get("resonance_relief", 0.2))
    if scene_type == "sanctuary":
        archetypes = ["caretaker", "listener", "lantern_keeper"]
    elif scene_type == "ritual_traverse":
        archetypes = ["bridge_witness", "echo_runner", "threshold_bird"]
    else:
        archetypes = ["forge_watcher", "shard_beast", "ash_mender"]
    count = max(2, min(6, int(2 + pressure * 3 + theta * 2 - sanctuary)))
    population = []
    for index in range(count):
        archetype = archetypes[index % len(archetypes)]
        population.append(
            {
                "id": f"{asset_id}_{index}",
                "archetype": archetype,
                "temperament": round(_clamp(0.28 + pressure * 0.42 + index * 0.04 - sanctuary * 0.18, 0.0, 1.0), 4),
                "curiosity": round(_clamp(0.34 + theta * 0.36 + resonance * 0.18 - index * 0.03, 0.0, 1.0), 4),
                "kinship_affinity": round(_clamp(0.26 + sanctuary * 0.46 + resonance * 0.22, 0.0, 1.0), 4),
            }
        )
    payload = {
        "id": asset_id,
        "usage": usage,
        "scene_type": scene_type,
        "population": population,
        "spawn_budget": count,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def synthesize_anim_state_machine_asset(
    path: Path,
    *,
    asset_id: str,
    usage: str,
    scene_type: str,
    hope: dict,
    family: dict,
) -> None:
    theta = float(hope.get("theta", 0.15))
    sanctuary = float(family.get("sanctuary_strength", 0.22))
    tail_ms = float(hope.get("worst_case_tail_ms", 24.0))
    blend_ms_base = round(max(40.0, min(180.0, 80.0 + theta * 60.0 - sanctuary * 30.0)), 1)

    if usage == "player":
        states = [
            {"id": "idle", "animation_id": f"{asset_id}_idle", "loop": True, "priority": 0, "interruptions": ["walk", "run", "attack", "hurt"]},
            {"id": "walk", "animation_id": f"{asset_id}_walk", "loop": True, "priority": 10, "interruptions": ["idle", "run", "attack", "hurt"]},
            {"id": "run", "animation_id": f"{asset_id}_run", "loop": True, "priority": 15, "interruptions": ["idle", "walk", "attack", "hurt"]},
            {"id": "attack", "animation_id": f"{asset_id}_attack", "loop": False, "priority": 30, "interruptions": ["hurt"]},
            {"id": "hurt", "animation_id": f"{asset_id}_hurt", "loop": False, "priority": 40, "interruptions": ["recover"]},
            {"id": "recover", "animation_id": f"{asset_id}_recover", "loop": False, "priority": 20, "interruptions": ["idle", "walk"]},
            {"id": "dead", "animation_id": f"{asset_id}_dead", "loop": False, "priority": 50, "interruptions": []},
        ]
        transitions = [
            {"from_state": "idle", "to_state": "walk", "condition": "input:move", "blend_ms": blend_ms_base},
            {"from_state": "idle", "to_state": "run", "condition": "input:run_hold", "blend_ms": round(blend_ms_base * 0.8, 1)},
            {"from_state": "walk", "to_state": "idle", "condition": "input:still", "blend_ms": blend_ms_base},
            {"from_state": "walk", "to_state": "run", "condition": "input:run_hold", "blend_ms": round(blend_ms_base * 0.6, 1)},
            {"from_state": "run", "to_state": "walk", "condition": "input:run_release", "blend_ms": blend_ms_base},
            {"from_state": "idle", "to_state": "attack", "condition": "input:attack", "blend_ms": round(blend_ms_base * 0.5, 1)},
            {"from_state": "walk", "to_state": "attack", "condition": "input:attack", "blend_ms": round(blend_ms_base * 0.5, 1)},
            {"from_state": "attack", "to_state": "idle", "condition": "anim:complete", "blend_ms": blend_ms_base},
            {"from_state": "any", "to_state": "hurt", "condition": "event:damage_received", "blend_ms": round(blend_ms_base * 0.3, 1)},
            {"from_state": "hurt", "to_state": "recover", "condition": "anim:complete", "blend_ms": round(blend_ms_base * 0.5, 1)},
            {"from_state": "recover", "to_state": "idle", "condition": "anim:complete", "blend_ms": blend_ms_base},
            {"from_state": "any", "to_state": "dead", "condition": "flag:hp_zero", "blend_ms": round(blend_ms_base * 0.4, 1)},
        ]
        entry_state = "idle"
    elif usage == "world_anchor":
        states = [
            {"id": "idle", "animation_id": f"{asset_id}_idle", "loop": True, "priority": 0, "interruptions": ["pulse", "react"]},
            {"id": "pulse", "animation_id": f"{asset_id}_pulse", "loop": False, "priority": 20, "interruptions": ["react", "deactivate"]},
            {"id": "react", "animation_id": f"{asset_id}_react", "loop": False, "priority": 30, "interruptions": ["deactivate"]},
            {"id": "deactivate", "animation_id": f"{asset_id}_deactivate", "loop": False, "priority": 40, "interruptions": []},
        ]
        transitions = [
            {"from_state": "idle", "to_state": "pulse", "condition": "event:anchor_pulse", "blend_ms": blend_ms_base},
            {"from_state": "pulse", "to_state": "idle", "condition": "anim:complete", "blend_ms": blend_ms_base},
            {"from_state": "idle", "to_state": "react", "condition": "event:player_proximity", "blend_ms": round(blend_ms_base * 0.6, 1)},
            {"from_state": "react", "to_state": "idle", "condition": "anim:complete", "blend_ms": blend_ms_base},
            {"from_state": "any", "to_state": "deactivate", "condition": "flag:scene_exit", "blend_ms": round(blend_ms_base * 0.5, 1)},
        ]
        entry_state = "idle"
    else:
        states = [
            {"id": "idle", "animation_id": f"{asset_id}_idle", "loop": True, "priority": 0, "interruptions": ["walk", "interact", "gesture"]},
            {"id": "walk", "animation_id": f"{asset_id}_walk", "loop": True, "priority": 10, "interruptions": ["idle", "interact"]},
            {"id": "interact", "animation_id": f"{asset_id}_interact", "loop": False, "priority": 25, "interruptions": ["gesture"]},
            {"id": "gesture", "animation_id": f"{asset_id}_gesture", "loop": False, "priority": 20, "interruptions": ["idle"]},
            {"id": "rest", "animation_id": f"{asset_id}_rest", "loop": True, "priority": 5, "interruptions": ["idle", "walk"]},
        ]
        transitions = [
            {"from_state": "idle", "to_state": "walk", "condition": "ai:path_active", "blend_ms": blend_ms_base},
            {"from_state": "walk", "to_state": "idle", "condition": "ai:path_done", "blend_ms": blend_ms_base},
            {"from_state": "idle", "to_state": "interact", "condition": "event:player_dialogue", "blend_ms": round(blend_ms_base * 0.6, 1)},
            {"from_state": "interact", "to_state": "idle", "condition": "anim:complete", "blend_ms": blend_ms_base},
            {"from_state": "idle", "to_state": "gesture", "condition": "timer:idle_timeout", "blend_ms": round(blend_ms_base * 0.7, 1)},
            {"from_state": "gesture", "to_state": "idle", "condition": "anim:complete", "blend_ms": blend_ms_base},
            {"from_state": "idle", "to_state": "rest", "condition": "flag:rest_zone", "blend_ms": round(blend_ms_base * 1.2, 1)},
            {"from_state": "rest", "to_state": "idle", "condition": "event:rest_interrupt", "blend_ms": blend_ms_base},
        ]
        entry_state = "idle"

    payload = {
        "id": asset_id,
        "usage": usage,
        "scene_type": scene_type,
        "entry_state": entry_state,
        "theta_influence": round(theta, 4),
        "sanctuary_influence": round(sanctuary, 4),
        "blend_ms_base": blend_ms_base,
        "tail_influence_ms": round(tail_ms, 4),
        "states": states,
        "transitions": transitions,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def synthesize_vfx_asset(
    path: Path,
    *,
    asset_id: str,
    usage: str,
    scene_type: str,
    hope: dict,
    family: dict,
) -> None:
    theta = float(hope.get("theta", 0.15))
    sanctuary = float(family.get("sanctuary_strength", 0.22))
    pressure = float(hope.get("clog_risk", 0.2))
    resonance = float(family.get("resonance_relief", 0.2))
    base, accent, _ = _scene_palette(scene_type, hope, family)
    alpha = min(255, int(180 + sanctuary * 50))

    def rgba(t: tuple[int, int, int], intensity: float = 1.0) -> dict:
        return {
            "r": min(255, int(t[0] * intensity)),
            "g": min(255, int(t[1] * intensity)),
            "b": min(255, int(t[2] * intensity)),
            "a": alpha,
        }

    effects = [
        {
            "id": f"{asset_id}_hit_impact",
            "trigger": "event:hit_contact",
            "shape": "burst",
            "particle_count": max(4, int(8 + pressure * 12)),
            "color": rgba(accent, 0.95),
            "duration_ms": round(max(80.0, 120.0 + pressure * 80.0 - sanctuary * 30.0), 1),
            "radius": round(0.3 + pressure * 0.2, 3),
            "intensity": round(_clamp(0.6 + pressure * 0.3 + theta * 0.1, 0.3, 1.0), 4),
            "layer": "vfx_overlay",
            "fade_out": True,
        },
        {
            "id": f"{asset_id}_hit_flash",
            "trigger": "event:damage_received",
            "shape": "screen_flash",
            "particle_count": 0,
            "color": rgba(accent, 1.0),
            "duration_ms": round(max(40.0, 60.0 + pressure * 40.0), 1),
            "radius": 0.0,
            "intensity": round(_clamp(0.4 + pressure * 0.4, 0.2, 0.9), 4),
            "layer": "vfx_screen",
            "fade_out": True,
        },
        {
            "id": f"{asset_id}_movement_trail",
            "trigger": "flag:movement_active",
            "shape": "ribbon",
            "particle_count": max(3, int(4 + theta * 4 - sanctuary * 1.5)),
            "color": rgba(base, 0.7),
            "duration_ms": round(max(60.0, 80.0 + theta * 40.0), 1),
            "radius": round(0.12 + theta * 0.06, 3),
            "intensity": round(_clamp(0.25 + theta * 0.2 - sanctuary * 0.08, 0.1, 0.6), 4),
            "layer": "vfx_mid",
            "fade_out": True,
        },
        {
            "id": f"{asset_id}_ambient_glow",
            "trigger": "continuous",
            "shape": "radial_pulse",
            "particle_count": 0,
            "color": rgba(accent, 0.8),
            "duration_ms": round(800.0 + sanctuary * 400.0, 1),
            "radius": round(0.6 + sanctuary * 0.4, 3),
            "intensity": round(_clamp(0.12 + sanctuary * 0.24 + resonance * 0.1, 0.05, 0.5), 4),
            "layer": "vfx_background",
            "fade_out": False,
        },
        {
            "id": f"{asset_id}_anchor_pulse_ring",
            "trigger": "event:anchor_pulse",
            "shape": "ring_expand",
            "particle_count": 0,
            "color": rgba(accent, 0.85),
            "duration_ms": round(max(200.0, 300.0 + sanctuary * 200.0), 1),
            "radius": round(1.0 + sanctuary * 0.8, 3),
            "intensity": round(_clamp(0.35 + sanctuary * 0.3 + resonance * 0.15, 0.1, 0.8), 4),
            "layer": "vfx_mid",
            "fade_out": True,
        },
    ]

    if scene_type == "sanctuary":
        effects.append({
            "id": f"{asset_id}_sanctuary_shimmer",
            "trigger": "continuous",
            "shape": "particle_field",
            "particle_count": max(6, int(10 + sanctuary * 8)),
            "color": rgba(accent, 0.9),
            "duration_ms": round(1200.0 + sanctuary * 600.0, 1),
            "radius": round(1.8 + sanctuary * 0.9, 3),
            "intensity": round(_clamp(0.2 + sanctuary * 0.3, 0.1, 0.6), 4),
            "layer": "vfx_background",
            "fade_out": False,
        })

    payload = {
        "id": asset_id,
        "usage": usage,
        "scene_type": scene_type,
        "effect_count": len(effects),
        "effects": effects,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def synthesize_interaction_asset(
    path: Path,
    *,
    asset_id: str,
    usage: str,
    scene_type: str,
    hope: dict,
    family: dict,
    entity_ids: list,
) -> None:
    theta = float(hope.get("theta", 0.15))
    sanctuary = float(family.get("sanctuary_strength", 0.22))
    pressure = float(hope.get("clog_risk", 0.2))
    resonance = float(family.get("resonance_relief", 0.2))
    affordance_span = float(hope.get("causality_plan", {}).get("entity_affordance_feedback", 0.5))
    interaction_gate = float(hope.get("physics_plan", {}).get("interaction_gate", 1.0))

    player_ids = [e for e in entity_ids if e.endswith("_player")]
    anchor_ids = [e for e in entity_ids if e.endswith("_anchor") and not e.endswith("_population_anchor")]
    npc_ids = [e for e in entity_ids if e not in player_ids and e not in anchor_ids]

    interaction_pairs = []

    for p_id in player_ids:
        for a_id in anchor_ids:
            interaction_pairs.append({
                "agent": p_id,
                "target": a_id,
                "interaction_type": "activate",
                "condition": f"proximity:{round(1.2 + interaction_gate * 0.4, 2)}",
                "outcome": [
                    {"action": "fire_event", "target": a_id, "event": "anchor_pulse"},
                    {"action": "fire_event", "target": "world", "event": "hope_rebalance"},
                ],
                "range": round(1.2 + interaction_gate * 0.4, 3),
                "cooldown_ms": round(max(400.0, 600.0 - affordance_span * 200.0), 1),
                "priority": 10,
            })
        for n_id in npc_ids:
            interaction_pairs.append({
                "agent": p_id,
                "target": n_id,
                "interaction_type": "dialogue",
                "condition": f"proximity:{round(0.9 + sanctuary * 0.3, 2)} and event:interact_pressed",
                "outcome": [
                    {"action": "fire_event", "target": n_id, "event": "player_dialogue"},
                    {"action": "fire_event", "target": "world", "event": "kinship_contact"},
                ],
                "range": round(0.9 + sanctuary * 0.3, 3),
                "cooldown_ms": round(max(800.0, 1200.0 - sanctuary * 400.0), 1),
                "priority": 20,
            })
        interaction_pairs.append({
            "agent": p_id,
            "target": "scene_gate",
            "interaction_type": "traverse",
            "condition": "proximity:0.7 and flag:gate_unlocked",
            "outcome": [
                {"action": "transition_scene", "target": "next_scene"},
                {"action": "fire_event", "target": "world", "event": "scene_exit"},
            ],
            "range": 0.7,
            "cooldown_ms": 0,
            "priority": 5,
        })

    affordance_zones = []
    for a_id in anchor_ids:
        affordance_zones.append({
            "zone_id": f"{a_id}_zone",
            "entity_id": a_id,
            "radius": round(1.4 + sanctuary * 0.4 + interaction_gate * 0.3, 3),
            "affordances": [
                {"type": "activate", "input": "interact_press", "cost": round(max(0.0, 0.08 - sanctuary * 0.04), 4), "cooldown_ms": round(max(300.0, 500.0 - affordance_span * 200.0), 1)},
                {"type": "observe", "input": "auto", "cost": 0.0, "cooldown_ms": 0},
            ],
        })
    for n_id in npc_ids:
        affordance_zones.append({
            "zone_id": f"{n_id}_zone",
            "entity_id": n_id,
            "radius": round(0.9 + sanctuary * 0.3, 3),
            "affordances": [
                {"type": "dialogue", "input": "interact_press", "cost": 0.0, "cooldown_ms": round(max(600.0, 1000.0 - sanctuary * 300.0), 1)},
                {"type": "kinship_affirm", "input": "auto", "cost": round(max(0.0, 0.04 - resonance * 0.03), 4), "cooldown_ms": round(max(500.0, 2000.0 - resonance * 500.0), 1)},
            ],
        })

    trigger_responses = [
        {
            "trigger_id": f"{asset_id}_scene_enter",
            "event": "scene_enter",
            "condition": "always",
            "response_chain": [
                {"action": "activate_all_anchors"},
                {"action": "fire_event", "target": "world", "event": "hope_rebalance"},
                {"action": "spawn_ecology_population"},
            ],
        },
        {
            "trigger_id": f"{asset_id}_hope_rebalance",
            "event": "hope_rebalance",
            "condition": f"theta_above:{round(theta * 0.8, 3)}",
            "response_chain": [
                {"action": "fire_event", "target": "world", "event": "causality_update"},
                {"action": "update_interaction_weights", "delta": round(affordance_span * 0.1, 4)},
            ],
        },
        {
            "trigger_id": f"{asset_id}_damage_response",
            "event": "damage_received",
            "condition": "flag:player_alive",
            "response_chain": [
                {"action": "fire_event", "target": "player", "event": "hurt_state"},
                {"action": "apply_knockback", "force": round(1.2 + pressure * 0.8, 3)},
                {"action": "fire_event", "target": "world", "event": "ecology_react"},
            ],
        },
    ]

    payload = {
        "id": asset_id,
        "usage": usage,
        "scene_type": scene_type,
        "entity_ids": entity_ids,
        "interaction_pair_count": len(interaction_pairs),
        "interaction_pairs": interaction_pairs,
        "affordance_zone_count": len(affordance_zones),
        "affordance_zones": affordance_zones,
        "trigger_response_count": len(trigger_responses),
        "trigger_responses": trigger_responses,
        "affordance_span": round(affordance_span, 4),
        "interaction_gate": round(interaction_gate, 4),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def synthesize_hitbox_asset(
    path: Path,
    *,
    asset_id: str,
    usage: str,
    scene_type: str,
    hope: dict,
    family: dict,
    entity_ids: list,
) -> None:
    theta = float(hope.get("theta", 0.15))
    sanctuary = float(family.get("sanctuary_strength", 0.22))
    pressure = float(hope.get("clog_risk", 0.2))
    interaction_gate = float(hope.get("physics_plan", {}).get("interaction_gate", 1.0))

    collision_layers = {
        "player": ["world_geometry", "enemy", "trigger", "pickup"],
        "enemy": ["world_geometry", "player", "trigger"],
        "player_attack": ["enemy", "world_geometry"],
        "enemy_attack": ["player"],
        "trigger": ["player"],
        "world_geometry": ["player", "enemy"],
        "pickup": ["player"],
        "vfx": [],
    }

    player_ids = [e for e in entity_ids if e.endswith("_player")]
    anchor_ids = [e for e in entity_ids if e.endswith("_anchor") and not e.endswith("_population_anchor")]
    npc_ids = [e for e in entity_ids if e not in player_ids and e not in anchor_ids]

    entity_hitboxes = []

    for entity_id in player_ids:
        attack_range = round(0.55 + interaction_gate * 0.2 + theta * 0.1, 3)
        hurtbox_h = round(1.6 + sanctuary * 0.08, 3)
        damage_base = max(8, int(10 + theta * 12 + pressure * 6))
        entity_hitboxes.append({
            "entity_id": entity_id,
            "collision_layer": "player",
            "states": {
                "idle": {
                    "hurtboxes": [{"x": 0.0, "y": 0.0, "w": 0.5, "h": hurtbox_h, "shape": "capsule"}],
                    "hitboxes": [],
                },
                "walk": {
                    "hurtboxes": [{"x": 0.0, "y": 0.0, "w": 0.48, "h": hurtbox_h, "shape": "capsule"}],
                    "hitboxes": [],
                },
                "run": {
                    "hurtboxes": [{"x": 0.0, "y": 0.0, "w": 0.44, "h": round(hurtbox_h * 0.95, 3), "shape": "capsule"}],
                    "hitboxes": [],
                },
                "attack": {
                    "hurtboxes": [{"x": 0.0, "y": 0.0, "w": 0.5, "h": hurtbox_h, "shape": "capsule"}],
                    "hitboxes": [{"x": round(attack_range * 0.5, 3), "y": 0.6, "w": attack_range, "h": 0.6, "shape": "box", "collision_layer": "player_attack"}],
                    "attack_windows": [{
                        "start_frame": 2,
                        "end_frame": 5,
                        "damage": damage_base,
                        "knockback": {"x": round(1.4 + pressure * 0.6, 3), "y": round(0.4 + pressure * 0.2, 3)},
                        "stagger_ms": round(max(120.0, 160.0 + pressure * 80.0), 1),
                        "hit_stop_ms": round(max(40.0, 60.0 + theta * 20.0), 1),
                    }],
                },
                "hurt": {
                    "hurtboxes": [{"x": 0.0, "y": 0.0, "w": 0.52, "h": hurtbox_h, "shape": "capsule"}],
                    "hitboxes": [],
                },
                "dead": {
                    "hurtboxes": [{"x": 0.0, "y": -0.5, "w": 1.0, "h": 0.6, "shape": "box"}],
                    "hitboxes": [],
                },
                "recover": {
                    "hurtboxes": [
                        {"x": 0.0, "y": 0.0, "w": 0.5, "h": hurtbox_h, "shape": "capsule"},
                        {"x": 0.0, "y": 0.0, "w": 0.7, "h": round(hurtbox_h + 0.1, 3), "shape": "capsule", "invincible": True},
                    ],
                    "hitboxes": [],
                },
            },
        })

    for entity_id in anchor_ids:
        entity_hitboxes.append({
            "entity_id": entity_id,
            "collision_layer": "trigger",
            "states": {
                "idle": {
                    "hurtboxes": [],
                    "hitboxes": [{"x": 0.0, "y": 0.5, "w": round(1.2 + sanctuary * 0.4, 3), "h": 2.0, "shape": "capsule", "collision_layer": "trigger"}],
                },
                "pulse": {
                    "hurtboxes": [],
                    "hitboxes": [{"x": 0.0, "y": 0.5, "w": round(1.8 + sanctuary * 0.6, 3), "h": 2.0, "shape": "capsule", "collision_layer": "trigger"}],
                },
                "react": {
                    "hurtboxes": [],
                    "hitboxes": [{"x": 0.0, "y": 0.5, "w": round(1.4 + sanctuary * 0.5, 3), "h": 2.0, "shape": "capsule", "collision_layer": "trigger"}],
                },
                "deactivate": {
                    "hurtboxes": [],
                    "hitboxes": [],
                },
            },
        })

    for entity_id in npc_ids:
        entity_hitboxes.append({
            "entity_id": entity_id,
            "collision_layer": "trigger",
            "states": {
                "idle": {
                    "hurtboxes": [{"x": 0.0, "y": 0.0, "w": 0.44, "h": 1.55, "shape": "capsule"}],
                    "hitboxes": [{"x": 0.0, "y": 0.5, "w": round(0.9 + sanctuary * 0.3, 3), "h": 1.4, "shape": "capsule", "collision_layer": "trigger"}],
                },
                "walk": {
                    "hurtboxes": [{"x": 0.0, "y": 0.0, "w": 0.44, "h": 1.55, "shape": "capsule"}],
                    "hitboxes": [{"x": 0.0, "y": 0.5, "w": 0.7, "h": 1.2, "shape": "capsule", "collision_layer": "trigger"}],
                },
                "interact": {
                    "hurtboxes": [{"x": 0.0, "y": 0.0, "w": 0.44, "h": 1.55, "shape": "capsule"}],
                    "hitboxes": [{"x": 0.0, "y": 0.5, "w": round(1.1 + sanctuary * 0.4, 3), "h": 1.6, "shape": "capsule", "collision_layer": "trigger"}],
                },
                "gesture": {
                    "hurtboxes": [{"x": 0.0, "y": 0.0, "w": 0.44, "h": 1.55, "shape": "capsule"}],
                    "hitboxes": [{"x": 0.0, "y": 0.5, "w": 0.9, "h": 1.4, "shape": "capsule", "collision_layer": "trigger"}],
                },
                "rest": {
                    "hurtboxes": [{"x": 0.0, "y": -0.4, "w": 0.55, "h": 0.8, "shape": "box"}],
                    "hitboxes": [{"x": 0.0, "y": -0.2, "w": round(0.8 + sanctuary * 0.2, 3), "h": 1.0, "shape": "box", "collision_layer": "trigger"}],
                },
            },
        })

    payload = {
        "id": asset_id,
        "usage": usage,
        "scene_type": scene_type,
        "entity_ids": entity_ids,
        "collision_layers": collision_layers,
        "entity_count": len(entity_hitboxes),
        "entity_hitboxes": entity_hitboxes,
        "spatial_grid": {
            "cell_size": round(max(1.0, 2.0 - pressure * 0.5), 2),
            "layers": list(collision_layers.keys()),
            "interaction_range_hint": round(max(0.7, 1.4 * interaction_gate), 3),
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")