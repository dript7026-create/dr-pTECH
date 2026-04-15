from __future__ import annotations

import argparse
import json
import math
import struct
import wave
from pathlib import Path


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
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "phrygian-dominant": [0, 1, 4, 5, 7, 8, 10],
    "enigmatic": [0, 1, 4, 6, 8, 10, 11],
}

WAVEFORMS = {"sine", "triangle", "saw", "pulse", "organ", "noise", "felt", "reed", "warm", "bowed", "mallet"}


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def midi_to_hz(midi_note: int) -> float:
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


def note_hz(root: str, mode: str, degree: int, octave: int) -> float:
    interval = MODES[mode][degree % len(MODES[mode])]
    midi = 12 * (octave + 1) + ROOT_NOTES[root] + interval
    return midi_to_hz(midi)


def osc(waveform: str, phase: float) -> float:
    frac = phase - math.floor(phase)
    if waveform == "triangle":
        return 2.0 * abs(2.0 * frac - 1.0) - 1.0
    if waveform == "saw":
        return 2.0 * frac - 1.0
    if waveform == "pulse":
        return 1.0 if frac < 0.28 else -1.0
    if waveform == "organ":
        return 0.66 * math.sin(2.0 * math.pi * frac) + 0.22 * math.sin(4.0 * math.pi * frac) + 0.12 * math.sin(6.0 * math.pi * frac)
    if waveform == "felt":
        return 0.78 * math.sin(2.0 * math.pi * frac) + 0.16 * math.sin(4.0 * math.pi * frac + 0.18) + 0.06 * math.sin(6.0 * math.pi * frac)
    if waveform == "reed":
        return 0.58 * math.sin(2.0 * math.pi * frac) + 0.22 * math.sin(4.0 * math.pi * frac + 0.22) + 0.14 * math.sin(6.0 * math.pi * frac + 0.09) + 0.06 * math.sin(8.0 * math.pi * frac)
    if waveform == "warm":
        return 0.56 * math.sin(2.0 * math.pi * frac) + 0.27 * math.sin(4.0 * math.pi * frac) + 0.11 * math.sin(6.0 * math.pi * frac) + 0.06 * math.sin(8.0 * math.pi * frac)
    if waveform == "bowed":
        return 0.66 * math.sin(2.0 * math.pi * frac) + 0.22 * math.sin(4.0 * math.pi * frac + 0.35) + 0.08 * math.sin(6.0 * math.pi * frac + 0.12) + 0.04 * math.sin(10.0 * math.pi * frac)
    if waveform == "mallet":
        return 0.74 * math.sin(2.0 * math.pi * frac) + 0.18 * math.sin(6.0 * math.pi * frac) + 0.08 * math.sin(10.0 * math.pi * frac)
    if waveform == "noise":
        seed = math.sin(phase * 12.9898) * 43758.5453
        return (seed - math.floor(seed)) * 2.0 - 1.0
    return math.sin(2.0 * math.pi * frac)


def soft_clip(sample: float) -> float:
    return math.tanh(sample * 1.42)


def one_pole(state: float, target: float, amount: float) -> float:
    return state + (target - state) * clamp(amount, 0.0, 1.0)


def pulse_env(step_phase: float, attack: float, release: float, sustain: float) -> float:
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


def write_wave(path: Path, stereo: list[tuple[int, int]], sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        frames = bytearray()
        for left, right in stereo:
            frames += struct.pack("<hh", left, right)
        handle.writeframes(bytes(frames))


def render_music_track(track: dict, motifs: dict, sample_rate: int) -> list[tuple[int, int]]:
    bpm = track["tempo"]
    steps_per_pattern = 16
    total_steps = track["loop_patterns"] * steps_per_pattern
    seconds_per_step = 60.0 / bpm / 4.0
    total_frames = int(total_steps * seconds_per_step * sample_rate)
    primary = motifs[track["primary_motif"]]
    secondary = motifs.get(track.get("secondary_motif"))
    lead_phase = 0.0
    pad_phase = 0.0
    bass_phase = 0.0
    low_l = 0.0
    low_r = 0.0
    stereo: list[tuple[int, int]] = []

    for frame in range(total_frames):
        time_point = frame / sample_rate
        step = int(time_point / seconds_per_step)
        local_step = step % steps_per_pattern
        pattern = step // steps_per_pattern
        step_phase = (time_point / seconds_per_step) % 1.0
        synth_degree = primary["degrees"][(local_step // 2 + pattern) % len(primary["degrees"])]
        bass_degree = primary["degrees"][(local_step // 4 + pattern) % len(primary["degrees"])]
        lead_freq = note_hz(primary["root"], primary["mode"], synth_degree, 4)
        pad_freq = note_hz(primary["root"], primary["mode"], synth_degree, 3)
        bass_freq = note_hz(primary["root"], primary["mode"], bass_degree, 1)
        lead_phase += lead_freq / sample_rate
        pad_phase += pad_freq / sample_rate
        bass_phase += bass_freq / sample_rate

        lead_env = pulse_env(step_phase, 0.06, 0.94, 0.62)
        pad_env = 0.72 + 0.18 * math.sin(2.0 * math.pi * (time_point / (seconds_per_step * 8.0)))
        lead = osc("reed", lead_phase) * lead_env * (0.12 + track["energy"] * 0.06) * track["emphasis"]
        pad = osc("organ", pad_phase) * pad_env * (0.14 + track["darkness"] * 0.08)
        bass = soft_clip(osc("bowed", bass_phase) * (1.4 + track["darkness"] * 0.4)) * (0.30 + track["energy"] * 0.08)
        sub = math.sin(2.0 * math.pi * (bass_phase * 0.5 - math.floor(bass_phase * 0.5))) * (0.12 + track["darkness"] * 0.06)

        if secondary is not None:
            mold_degree = secondary["degrees"][(local_step // 2 + pattern) % len(secondary["degrees"])]
            mold_freq = note_hz(secondary["root"], secondary["mode"], mold_degree, 2)
            pad += osc("warm", time_point * mold_freq) * (0.06 + track["darkness"] * 0.08)

        hit_gate = 1.0 if local_step in {0, 4, 8, 12} else 0.0
        perc = 0.0
        if hit_gate > 0.0:
            burst = 1.0 - step_phase
            kick = osc("sine", time_point * (46.0 + track["darkness"] * 6.0)) * 0.28
            brush = osc("noise", time_point * 1800.0) * 0.06
            perc = soft_clip((kick + brush) * burst)

        mix_l = (lead * 0.82 + pad * 0.78 + bass + sub + perc) * 0.54
        mix_r = (lead * 0.78 + pad * 0.84 + bass + sub + perc) * 0.54
        filter_amount = 0.11 - (0.02 * track["energy"])
        low_l = one_pole(low_l, mix_l, filter_amount)
        low_r = one_pole(low_r, mix_r, filter_amount)
        stereo.append((to_pcm(clamp(soft_clip(low_l * 1.1), -0.95, 0.95)), to_pcm(clamp(soft_clip(low_r * 1.1), -0.95, 0.95))))
    return stereo


def render_sfx(item: dict, sample_rate: int) -> list[tuple[int, int]]:
    waveform = item["waveform"] if item["waveform"] in WAVEFORMS else "sine"
    duration = float(item["duration"])
    frames = int(sample_rate * duration)
    pitch = float(item["pitch"])
    drive = float(item["drive"])
    stereo: list[tuple[int, int]] = []
    low_l = 0.0
    low_r = 0.0
    for frame in range(frames):
        time_point = frame / sample_rate
        env = max(0.0, 1.0 - time_point / duration)
        sweep = pitch * (1.0 - 0.22 * time_point / duration)
        base = osc(waveform, time_point * sweep)
        if waveform == "noise":
            base = osc("noise", time_point * (pitch + 1.0))
        body = osc("bowed", time_point * max(38.0, pitch * 0.45)) * (0.18 + drive * 0.10)
        click = osc("mallet", time_point * (pitch * 1.35)) * 0.08
        pulse = osc("organ", time_point * max(22.0, pitch * 0.2)) * 0.06
        sample = soft_clip(base * (0.78 + drive * 0.72) + body + click + pulse) * env
        low_l = one_pole(low_l, sample, 0.14)
        low_r = one_pole(low_r, sample * 0.97, 0.14)
        stereo.append((to_pcm(clamp(low_l * 0.92, -0.95, 0.95)), to_pcm(clamp(low_r * 0.88, -0.95, 0.95))))
    return stereo


def build_sfx_items(manifest: dict) -> list[dict]:
    items = list(manifest.get("base_sfx", []))
    actions = manifest["combat_matrix"]["actions"]
    lanes = manifest["combat_matrix"]["lanes"]
    timing_buckets = manifest["combat_matrix"]["timing_buckets"]
    qualities = manifest["combat_matrix"]["qualities"]
    action_profiles = manifest["combat_matrix"]["action_profiles"]
    lane_profiles = manifest["combat_matrix"]["lane_profiles"]
    quality_profiles = manifest["combat_matrix"]["quality_profiles"]
    timing_profiles = manifest["combat_matrix"]["timing_profiles"]

    for action in actions:
        action_profile = action_profiles[action]
        for lane in lanes:
            lane_profile = lane_profiles[lane]
            items.append(
                {
                    "id": f"prompt_{action}_{lane}",
                    "type": "prompt",
                    "waveform": action_profile["waveform"],
                    "pitch": action_profile["pitch"] + lane_profile["pitch_offset"],
                    "duration": 0.16 + lane_profile["duration_offset"],
                    "drive": 0.18 + action_profile["drive_offset"],
                }
            )
            for quality in qualities:
                quality_profile = quality_profiles[quality]
                for timing in timing_buckets:
                    timing_profile = timing_profiles[timing]
                    items.append(
                        {
                            "id": f"resolve_{action}_{lane}_{quality}_{timing}",
                            "type": "resolve",
                            "waveform": quality_profile.get("waveform", action_profile["waveform"]),
                            "pitch": action_profile["pitch"] + lane_profile["pitch_offset"] + quality_profile["pitch_offset"] + timing_profile["pitch_offset"],
                            "duration": 0.18 + lane_profile["duration_offset"] + quality_profile["duration_offset"] + timing_profile["duration_offset"],
                            "drive": 0.20 + action_profile["drive_offset"] + quality_profile["drive_offset"],
                        }
                    )
    return items


def generate(manifest_path: Path, out_dir: Path, sample_rate: int) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    motifs = manifest["leitmotifs"]
    report = {
        "generator": manifest["generator"],
        "version": manifest["version"],
        "passes": manifest["passes"],
        "music": [],
        "sfx": [],
    }

    for track in manifest["music_tracks"]:
        stereo = render_music_track(track, motifs, sample_rate)
        path = out_dir / "music" / f"{track['id']}.wav"
        write_wave(path, stereo, sample_rate)
        report["music"].append({"id": track["id"], "path": str(path), "frames": len(stereo)})

    for item in build_sfx_items(manifest):
        stereo = render_sfx(item, sample_rate)
        path = out_dir / "sfx" / f"{item['id']}.wav"
        write_wave(path, stereo, sample_rate)
        report["sfx"].append({"id": item["id"], "path": str(path), "frames": len(stereo), "type": item["type"]})

    report_path = out_dir / "generated_manifest.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate XenoBloods placeholder audio from an AIASMR prompt series")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--sample-rate", type=int, default=22050)
    args = parser.parse_args()

    report = generate(args.manifest, args.out_dir, args.sample_rate)
    print(json.dumps({"music": len(report["music"]), "sfx": len(report["sfx"]), "manifest": str(args.out_dir / "generated_manifest.json")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())