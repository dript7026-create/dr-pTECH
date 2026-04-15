from __future__ import annotations

import argparse
import json
import math
import struct
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "audio" / "audio_manifest.json"
DEFAULT_OUT_DIR = ROOT / "audio" / "generated"

ROOT_NOTES = {
    "C": 0,
    "Db": 1,
    "D": 2,
    "Eb": 3,
    "E": 4,
    "F": 5,
    "Gb": 6,
    "G": 7,
    "Ab": 8,
    "A": 9,
    "Bb": 10,
    "B": 11,
}

MODES = {
    "aeolian": [0, 2, 3, 5, 7, 8, 10],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
}


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def midi_to_hz(midi_note: int) -> float:
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


def note_hz(root: str, mode: str, degree: int, octave: int) -> float:
    scale = MODES[mode]
    interval = scale[degree % len(scale)]
    midi = 12 * (octave + 1) + ROOT_NOTES[root] + interval
    return midi_to_hz(midi)


def osc(waveform: str, phase: float) -> float:
    frac = phase - math.floor(phase)
    if waveform == "triangle":
        return 2.0 * abs(2.0 * frac - 1.0) - 1.0
    if waveform == "saw":
        return 2.0 * frac - 1.0
    if waveform == "pulse":
        return 1.0 if frac < 0.32 else -1.0
    if waveform == "organ":
        return 0.62 * math.sin(2.0 * math.pi * frac) + 0.22 * math.sin(4.0 * math.pi * frac) + 0.16 * math.sin(6.0 * math.pi * frac)
    if waveform == "felt":
        return 0.78 * math.sin(2.0 * math.pi * frac) + 0.16 * math.sin(4.0 * math.pi * frac + 0.18) + 0.06 * math.sin(6.0 * math.pi * frac)
    if waveform == "reed":
        return 0.58 * math.sin(2.0 * math.pi * frac) + 0.20 * math.sin(4.0 * math.pi * frac + 0.24) + 0.14 * math.sin(6.0 * math.pi * frac + 0.10) + 0.08 * math.sin(8.0 * math.pi * frac)
    if waveform == "warm":
        return 0.56 * math.sin(2.0 * math.pi * frac) + 0.27 * math.sin(4.0 * math.pi * frac) + 0.11 * math.sin(6.0 * math.pi * frac) + 0.06 * math.sin(8.0 * math.pi * frac)
    if waveform == "noise":
        seed = math.sin(phase * 12.9898) * 43758.5453
        return (seed - math.floor(seed)) * 2.0 - 1.0
    return math.sin(2.0 * math.pi * frac)


def soft_clip(sample: float) -> float:
    return math.tanh(sample * 1.4)


def one_pole(state: float, target: float, amount: float) -> float:
    return state + (target - state) * clamp(amount, 0.0, 1.0)


def pulse_env(step_phase: float, attack: float, sustain: float, release: float) -> float:
    if step_phase < attack:
        return step_phase / max(attack, 0.0001)
    if step_phase < sustain:
        return 1.0
    if step_phase >= release:
        return 0.0
    return 1.0 - ((step_phase - sustain) / max(release - sustain, 0.0001))


def to_pcm(value: float) -> int:
    value = clamp(value, -1.0, 1.0)
    return int(value * 32767.0)


def from_pcm(value: int) -> float:
    return float(value) / 32767.0


def analyze_stereo_frames(stereo_frames: list[tuple[int, int]]) -> dict[str, float]:
    if not stereo_frames:
        return {"peak": 0.0, "rms": 0.0}
    peak = 0.0
    accum = 0.0
    count = 0
    for left, right in stereo_frames:
        lf = abs(from_pcm(left))
        rf = abs(from_pcm(right))
        peak = max(peak, lf, rf)
        accum += lf * lf + rf * rf
        count += 2
    rms = math.sqrt(accum / max(count, 1))
    return {"peak": peak, "rms": rms}


def normalize_stereo_frames(stereo_frames: list[tuple[int, int]], target_peak: float = 0.92) -> list[tuple[int, int]]:
    if not stereo_frames:
        return stereo_frames
    stats = analyze_stereo_frames(stereo_frames)
    peak = stats["peak"]
    if peak <= 0.0001:
        return stereo_frames
    gain = min(1.0, target_peak / peak)
    if gain >= 0.9999:
        return stereo_frames

    normalized: list[tuple[int, int]] = []
    for left, right in stereo_frames:
        normalized.append((to_pcm(from_pcm(left) * gain), to_pcm(from_pcm(right) * gain)))
    return normalized


def write_wave(path: Path, stereo_frames: list[tuple[int, int]], sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        frame_bytes = bytearray()
        for left, right in stereo_frames:
            frame_bytes += struct.pack("<hh", left, right)
        handle.writeframes(bytes(frame_bytes))


def render_music_track(track: dict[str, object], sample_rate: int) -> list[tuple[int, int]]:
    bpm = int(track["tempo"])
    steps_per_bar = 8
    total_steps = int(track["bars"]) * steps_per_bar
    seconds_per_step = 60.0 / bpm / 2.0
    total_frames = int(total_steps * seconds_per_step * sample_rate)

    root = str(track["root"])
    mode = str(track["mode"])
    lead_degrees = [int(value) for value in track["degrees"]]
    bass_degrees = [int(value) for value in track["bass"]]
    waveform = str(track["waveform"])
    pad_waveform = str(track["pad_waveform"])
    energy = float(track["energy"])
    darkness = float(track["darkness"])

    lead_phase = 0.0
    pad_phase = 0.0
    bass_phase = 0.0
    low_l = 0.0
    low_r = 0.0
    stereo: list[tuple[int, int]] = []

    for frame in range(total_frames):
        time_point = frame / sample_rate
        step = int(time_point / seconds_per_step)
        step_phase = (time_point / seconds_per_step) % 1.0
        lead_degree = lead_degrees[step % len(lead_degrees)]
        pad_degree = lead_degrees[(step // 2) % len(lead_degrees)]
        bass_degree = bass_degrees[(step // 2) % len(bass_degrees)]

        lead_freq = note_hz(root, mode, lead_degree, 4)
        pad_freq = note_hz(root, mode, pad_degree, 3)
        bass_freq = note_hz(root, mode, bass_degree, 2)

        lead_phase += lead_freq / sample_rate
        pad_phase += pad_freq / sample_rate
        bass_phase += bass_freq / sample_rate

        lead_env = pulse_env(step_phase, 0.08, 0.62, 0.98)
        pad_env = 0.74 + 0.14 * math.sin(2.0 * math.pi * (time_point / (seconds_per_step * 6.0)))
        lead = osc(waveform, lead_phase) * lead_env * (0.12 + energy * 0.08)
        pad = osc(pad_waveform, pad_phase) * pad_env * (0.10 + darkness * 0.06)
        bass = soft_clip(osc("warm", bass_phase) * (1.25 + darkness * 0.25)) * (0.22 + energy * 0.08)

        percussion = 0.0
        if step % 2 == 0:
            burst = 1.0 - step_phase
            kick = osc("organ", time_point * (48.0 + energy * 8.0)) * 0.22
            brush = osc("noise", time_point * 1600.0) * 0.04
            percussion = soft_clip((kick + brush) * burst)

        shimmer = osc("noise", time_point * (lead_freq * 0.25 + 1.0)) * 0.02 * (0.4 + darkness)

        mix_l = (lead * 0.82 + pad * 0.78 + bass + percussion + shimmer) * 0.56
        mix_r = (lead * 0.78 + pad * 0.84 + bass + percussion + shimmer) * 0.56

        low_l = one_pole(low_l, mix_l, 0.12 - energy * 0.02)
        low_r = one_pole(low_r, mix_r, 0.12 - energy * 0.02)
        stereo.append((to_pcm(soft_clip(low_l * 1.08)), to_pcm(soft_clip(low_r * 1.08))))

    return stereo


def render_sfx(item: dict[str, object], sample_rate: int) -> list[tuple[int, int]]:
    waveform = str(item["waveform"])
    duration = float(item["duration"])
    pitch = float(item["pitch"])
    sweep = float(item["sweep"])
    drive = float(item["drive"])
    total_frames = int(sample_rate * duration)
    phase = 0.0
    low_l = 0.0
    low_r = 0.0
    stereo: list[tuple[int, int]] = []

    for frame in range(total_frames):
        time_point = frame / sample_rate
        norm = time_point / max(duration, 0.0001)
        env = (1.0 - norm)
        env *= env
        frequency = pitch * (1.0 + (sweep - 1.0) * norm)
        phase += frequency / sample_rate

        transient = osc(waveform, phase) * (0.76 + drive * 0.72)
        body = osc("organ", phase * 0.5) * (0.14 + drive * 0.08)
        grit = osc("noise", time_point * (frequency + 17.0)) * (0.05 + drive * 0.08)
        sample = soft_clip((transient + body + grit) * env)

        low_l = one_pole(low_l, sample, 0.16)
        low_r = one_pole(low_r, sample * 0.96, 0.16)
        stereo.append((to_pcm(low_l * 0.92), to_pcm(low_r * 0.88)))

    return stereo


def write_coverage(manifest: dict[str, object], out_dir: Path) -> Path:
    lines = ["# Armored Gear: Fly Slight Audio Coverage", "", "## Music", ""]
    for track in manifest["music_tracks"]:
        lines.append(f"- {track['id']}: {track['trigger']}")
    lines.extend(["", "## SFX", ""])
    for item in manifest["sfx"]:
        lines.append(f"- {item['id']}: {item['trigger']}")
    coverage_path = out_dir / "AUDIO_COVERAGE.md"
    coverage_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return coverage_path


def generate(manifest_path: Path, out_dir: Path, sample_rate: int) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, object] = {
        "generator": manifest["generator"],
        "version": manifest["version"],
        "music": [],
        "sfx": [],
        "audio_pass": {
            "name": "updated_mastering_pass",
            "target_peak": 0.92,
        },
    }

    for track in manifest["music_tracks"]:
        frames = render_music_track(track, sample_rate)
        frames = normalize_stereo_frames(frames, target_peak=0.92)
        metrics = analyze_stereo_frames(frames)
        path = out_dir / "music" / f"{track['id']}.wav"
        write_wave(path, frames, sample_rate)
        report["music"].append(
            {
                "id": track["id"],
                "path": str(path),
                "frames": len(frames),
                "trigger": track["trigger"],
                "peak": round(metrics["peak"], 6),
                "rms": round(metrics["rms"], 6),
            }
        )

    for item in manifest["sfx"]:
        frames = render_sfx(item, sample_rate)
        frames = normalize_stereo_frames(frames, target_peak=0.92)
        metrics = analyze_stereo_frames(frames)
        path = out_dir / "sfx" / f"{item['id']}.wav"
        write_wave(path, frames, sample_rate)
        report["sfx"].append(
            {
                "id": item["id"],
                "path": str(path),
                "frames": len(frames),
                "trigger": item["trigger"],
                "peak": round(metrics["peak"], 6),
                "rms": round(metrics["rms"], 6),
            }
        )

    coverage_path = write_coverage(manifest, out_dir)
    report["coverage"] = str(coverage_path)

    pass_report_path = out_dir / "AUDIO_PASS_REPORT.json"
    pass_report = {
        "music_tracks": len(report["music"]),
        "sfx_items": len(report["sfx"]),
        "target_peak": report["audio_pass"]["target_peak"],
        "max_music_peak": max((item["peak"] for item in report["music"]), default=0.0),
        "max_sfx_peak": max((item["peak"] for item in report["sfx"]), default=0.0),
    }
    pass_report_path.write_text(json.dumps(pass_report, indent=2), encoding="utf-8")
    report["audio_pass_report"] = str(pass_report_path)

    report_path = out_dir / "generated_manifest.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    report["manifest"] = str(report_path)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Armored Gear: Fly Slight placeholder audio assets.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--sample-rate", type=int, default=22050)
    parser.add_argument(
        "--updated-pass",
        action="store_true",
        help="Enable updated mastering and reporting pass (default behavior in this generator).",
    )
    args = parser.parse_args()

    report = generate(args.manifest, args.out_dir, args.sample_rate)
    print(json.dumps({
        "music": len(report["music"]),
        "sfx": len(report["sfx"]),
        "coverage": report["coverage"],
        "manifest": report["manifest"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())