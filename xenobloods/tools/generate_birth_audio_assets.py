from __future__ import annotations

import json
import math
import struct
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIO_ROOT = ROOT / "assets" / "audio"
MUSIC_DIR = AUDIO_ROOT / "music"
SFX_DIR = AUDIO_ROOT / "sfx"
MANIFEST_PATH = AUDIO_ROOT / "generated_manifest.json"
SAMPLE_RATE = 44_100


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def soft_clip(sample: float) -> float:
    return math.tanh(sample * 1.45)


def to_pcm(sample: float) -> int:
    return int(clamp(sample, -1.0, 1.0) * 32767.0)


def noise(seed: float) -> float:
    value = math.sin(seed * 12.9898) * 43758.5453
    return (value - math.floor(value)) * 2.0 - 1.0


def write_wave(path: Path, frames: list[tuple[int, int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        payload = bytearray()
        for left, right in frames:
            payload += struct.pack("<hh", left, right)
        handle.writeframes(bytes(payload))


def render_birth_music(duration: float = 12.0) -> list[tuple[int, int]]:
    total_frames = int(duration * SAMPLE_RATE)
    frames: list[tuple[int, int]] = []
    low_l = 0.0
    low_r = 0.0
    for index in range(total_frames):
        time_point = index / SAMPLE_RATE
        swell = 0.52 + 0.48 * math.sin(time_point * 0.82)
        drone = (
            math.sin(2.0 * math.pi * 55.0 * time_point)
            + 0.52 * math.sin(2.0 * math.pi * 82.4 * time_point + 0.2)
            + 0.28 * math.sin(2.0 * math.pi * 110.0 * time_point + 0.46)
        ) * (0.22 + swell * 0.14)
        brass = (
            math.sin(2.0 * math.pi * 73.4 * time_point + 0.08)
            + 0.44 * math.sin(2.0 * math.pi * 146.8 * time_point + 0.4)
            + 0.18 * math.sin(2.0 * math.pi * 220.2 * time_point + 0.12)
        ) * (0.18 + 0.06 * math.sin(time_point * 1.7))
        pulse_phase = time_point % 0.78
        pulse_env = max(0.0, 1.0 - pulse_phase / 0.22) ** 2
        heartbeat = math.sin(2.0 * math.pi * (40.0 + 18.0 * pulse_env) * time_point) * pulse_env * 0.24
        rasp_env = 0.35 + 0.65 * math.sin(time_point * 0.37 + 1.1) ** 2
        rasp = noise(time_point * 820.0) * rasp_env * 0.06
        scrape = math.sin(2.0 * math.pi * (310.0 + 28.0 * math.sin(time_point * 0.9)) * time_point) * noise(time_point * 12.0) * 0.03
        sample = soft_clip(drone + brass + heartbeat + rasp + scrape)
        pan_l = 0.92 + 0.08 * math.sin(time_point * 0.21)
        pan_r = 0.92 + 0.08 * math.cos(time_point * 0.18)
        low_l = low_l + (sample * pan_l - low_l) * 0.12
        low_r = low_r + (sample * pan_r - low_r) * 0.12
        frames.append((to_pcm(low_l), to_pcm(low_r)))
    return frames


def render_birth_stage(duration: float = 0.78) -> list[tuple[int, int]]:
    total_frames = int(duration * SAMPLE_RATE)
    frames: list[tuple[int, int]] = []
    for index in range(total_frames):
        time_point = index / SAMPLE_RATE
        env = max(0.0, 1.0 - time_point / duration)
        lift = min(1.0, time_point / 0.18)
        brass = (
            math.sin(2.0 * math.pi * 185.0 * time_point)
            + 0.4 * math.sin(2.0 * math.pi * 246.0 * time_point + 0.16)
        ) * env * (0.18 + lift * 0.24)
        rind = noise(time_point * 930.0) * env * 0.12
        crack = math.sin(2.0 * math.pi * 62.0 * time_point) * env * 0.22
        sample = soft_clip(brass + rind + crack)
        frames.append((to_pcm(sample * 0.94), to_pcm(sample * 0.88)))
    return frames


def render_birth_fail(duration: float = 0.62) -> list[tuple[int, int]]:
    total_frames = int(duration * SAMPLE_RATE)
    frames: list[tuple[int, int]] = []
    for index in range(total_frames):
        time_point = index / SAMPLE_RATE
        env = max(0.0, 1.0 - time_point / duration)
        fall = 188.0 - 72.0 * (time_point / duration)
        brass = math.sin(2.0 * math.pi * fall * time_point) * env * 0.28
        wet = noise(time_point * 710.0) * env * 0.15
        sample = soft_clip(brass + wet)
        frames.append((to_pcm(sample * 0.86), to_pcm(sample * 0.92)))
    return frames


def render_birth_complete(duration: float = 1.18) -> list[tuple[int, int]]:
    total_frames = int(duration * SAMPLE_RATE)
    frames: list[tuple[int, int]] = []
    for index in range(total_frames):
        time_point = index / SAMPLE_RATE
        env = max(0.0, 1.0 - time_point / duration)
        rise = min(1.0, time_point / 0.3)
        brass = (
            math.sin(2.0 * math.pi * 220.0 * time_point)
            + 0.46 * math.sin(2.0 * math.pi * 277.0 * time_point + 0.12)
            + 0.32 * math.sin(2.0 * math.pi * 330.0 * time_point + 0.3)
        ) * env * (0.22 + rise * 0.26)
        burst = noise(time_point * 1100.0) * max(0.0, 1.0 - time_point / 0.24) * 0.18
        under = math.sin(2.0 * math.pi * 66.0 * time_point) * env * 0.18
        sample = soft_clip(brass + burst + under)
        frames.append((to_pcm(sample * 0.96), to_pcm(sample * 0.9)))
    return frames


def relative_manifest_path(path: Path) -> str:
    return str(path.relative_to(ROOT.parent)).replace("/", "\\")


def upsert(items: list[dict], entry: dict) -> None:
    for index, item in enumerate(items):
        if item.get("id") == entry.get("id"):
            items[index] = entry
            return
    items.append(entry)


def main() -> None:
    music_path = MUSIC_DIR / "birth_brass_horror.wav"
    sfx_stage_path = SFX_DIR / "birth_stage.wav"
    sfx_fail_path = SFX_DIR / "birth_fail.wav"
    sfx_complete_path = SFX_DIR / "birth_complete.wav"

    write_wave(music_path, render_birth_music())
    write_wave(sfx_stage_path, render_birth_stage())
    write_wave(sfx_fail_path, render_birth_fail())
    write_wave(sfx_complete_path, render_birth_complete())

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    upsert(
        manifest["music"],
        {
            "id": "birth_brass_horror",
            "path": relative_manifest_path(music_path),
            "frames": int(12.0 * SAMPLE_RATE),
        },
    )
    upsert(
        manifest["sfx"],
        {
            "id": "birth_stage",
            "path": relative_manifest_path(sfx_stage_path),
            "frames": int(0.78 * SAMPLE_RATE),
            "type": "birth",
        },
    )
    upsert(
        manifest["sfx"],
        {
            "id": "birth_fail",
            "path": relative_manifest_path(sfx_fail_path),
            "frames": int(0.62 * SAMPLE_RATE),
            "type": "birth",
        },
    )
    upsert(
        manifest["sfx"],
        {
            "id": "birth_complete",
            "path": relative_manifest_path(sfx_complete_path),
            "frames": int(1.18 * SAMPLE_RATE),
            "type": "birth",
        },
    )
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()