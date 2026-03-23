import argparse
import json
import math
import random
import struct
import time
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

MODE_INTERVALS = {
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "locrian": [0, 1, 3, 5, 6, 8, 10],
    "aeolian": [0, 2, 3, 5, 7, 8, 10],
    "phrygian-dominant": [0, 1, 4, 5, 7, 8, 10],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "double-harmonic": [0, 1, 4, 5, 7, 8, 11],
    "harmonic-minor": [0, 2, 3, 5, 7, 8, 11],
    "whole-half diminished": [0, 2, 3, 5, 6, 8, 9],
    "lydian-augmented": [0, 2, 4, 6, 8, 9, 11],
}

REGISTER_OCTAVES = {
    "low": 2,
    "mid": 4,
    "high": 5,
    "full": 3,
}


def midi_to_hz(midi_note: int) -> float:
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


def mode_note_hz(root: str, mode: str, degree: int, octave: int) -> float:
    root_offset = ROOT_NOTES.get(root, 0)
    intervals = MODE_INTERVALS.get(mode, MODE_INTERVALS["aeolian"])
    midi_note = 12 * (octave + 1) + root_offset + intervals[degree % len(intervals)]
    return midi_to_hz(midi_note)


def clamp_sample(value: float) -> int:
    if value > 32767.0:
        return 32767
    if value < -32768.0:
        return -32768
    return int(value)


def oscillator_sample(waveform: str, phase: float, time_point: float) -> float:
    frac = phase - math.floor(phase)
    if waveform == "triangle":
        return 2.0 * abs(2.0 * frac - 1.0) - 1.0
    if waveform == "saw":
        return 2.0 * frac - 1.0
    if waveform == "pulse":
        return 1.0 if frac < 0.24 else -1.0
    if waveform == "organ":
        base = math.sin(2.0 * math.pi * frac)
        return 0.62 * base + 0.26 * math.sin(4.0 * math.pi * frac) + 0.12 * math.sin(6.0 * math.pi * frac)
    if waveform == "bow":
        vibrato = 0.005 * math.sin(2.0 * math.pi * 5.2 * time_point)
        bowed = math.sin(2.0 * math.pi * (frac + vibrato))
        return 0.72 * bowed + 0.28 * math.sin(4.0 * math.pi * frac)
    if waveform == "bell":
        decay = math.exp(-2.8 * (frac % 1.0))
        return decay * (0.75 * math.sin(2.0 * math.pi * frac) + 0.25 * math.sin(6.0 * math.pi * frac))
    if waveform == "noise":
        return random.uniform(-1.0, 1.0)
    if waveform == "input":
        noise = random.uniform(-1.0, 1.0)
        return 0.65 * noise + 0.35 * math.sin(2.0 * math.pi * time_point * 93.0)
    return math.sin(2.0 * math.pi * frac)


def articulation_envelope(articulation: str, position: float, event_label: str) -> float:
    accent = 1.15 if event_label in {"duel", "victory", "defeat", "phase"} else 1.0
    if articulation in {"drone", "sustain", "pressure", "bed", "reactive"}:
        return accent * (0.82 + 0.18 * math.sin(2.0 * math.pi * position))
    if articulation in {"pulse", "chop", "ostinato"}:
        gate = 1.0 if (position % 0.25) < 0.13 else 0.0
        return accent * gate
    if articulation in {"summon", "breath", "choral", "accent"}:
        local = position % 0.5
        return accent * max(0.0, 1.0 - local * 1.8)
    return accent


def layer_degrees(role: str) -> list[int]:
    if role == "pulse":
        return [0, 4, 2, 4, 0, 5, 3, 4]
    if role == "lead":
        return [0, 2, 4, 6, 4, 2, 1, 3]
    return [0]


def render_layer(layer: dict[str, object], sample_rate: int, duration: float, event_label: str) -> tuple[list[int], list[int]]:
    frames = int(sample_rate * duration)
    waveform = str(layer.get("waveform", "triangle"))
    role = str(layer.get("role", "drone"))
    root = str(layer.get("root", "C"))
    mode = str(layer.get("mode", "aeolian"))
    register = str(layer.get("register", "mid"))
    articulation = str(layer.get("articulation", "drone"))
    gain = float(layer.get("gain", 0.1))
    pan = float(layer.get("pan", 0.0))
    octave = REGISTER_OCTAVES.get(register, 4)
    degrees = layer_degrees(role)
    left: list[int] = []
    right: list[int] = []
    phase = 0.0
    for frame in range(frames):
        time_point = frame / sample_rate
        phrase_index = int((time_point / 0.25) if role in {"pulse", "lead"} else 0)
        degree = degrees[phrase_index % len(degrees)]
        frequency = mode_note_hz(root, mode, degree, octave)
        if role == "drone":
            frequency *= 0.5
        phase += frequency / sample_rate
        env = articulation_envelope(articulation, time_point, event_label)
        sample = oscillator_sample(waveform, phase, time_point)
        amplitude = sample * gain * env * 12000.0
        left.append(clamp_sample(amplitude * (1.0 - max(0.0, pan))))
        right.append(clamp_sample(amplitude * (1.0 + min(0.0, pan))))
    return left, right


def write_wave(path: Path, left: list[int], right: list[int], sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        frames = bytearray()
        for l_sample, r_sample in zip(left, right):
            frames += struct.pack("<hh", l_sample, r_sample)
        handle.writeframes(bytes(frames))


def mix_layers(layer_buffers: list[tuple[list[int], list[int]]]) -> tuple[list[int], list[int]]:
    if not layer_buffers:
        return [0], [0]
    frame_count = len(layer_buffers[0][0])
    left = [0] * frame_count
    right = [0] * frame_count
    for layer_left, layer_right in layer_buffers:
        for index in range(frame_count):
            left[index] = clamp_sample(left[index] + layer_left[index])
            right[index] = clamp_sample(right[index] + layer_right[index])
    return left, right


def render_state(payload: dict[str, object], out_dir: Path, sample_rate: int, duration: float) -> dict[str, object]:
    decision = payload.get("decision", {})
    layers = decision.get("layers", [])
    event_label = str(decision.get("event_label", "none"))
    rendered_layers = []
    layer_buffers = []
    for layer in layers:
        role = str(layer.get("role", "layer"))
        left, right = render_layer(layer, sample_rate, duration, event_label)
        write_wave(out_dir / f"current_{role}.wav", left, right, sample_rate)
        rendered_layers.append(role)
        layer_buffers.append((left, right))
    mix_left, mix_right = mix_layers(layer_buffers)
    write_wave(out_dir / "current_mix.wav", mix_left, mix_right, sample_rate)
    report = {
        "rendered_at": time.time(),
        "sample_rate": sample_rate,
        "duration": duration,
        "layer_count": len(rendered_layers),
        "rendered_layers": rendered_layers,
        "scene": decision.get("scene_label", "unknown"),
        "event": event_label,
        "last_tts": decision.get("last_tts", ""),
    }
    (out_dir / "renderer_state.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    with (out_dir / "renderer_events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(report) + "\n")
    return report


def load_json(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Render AIASMR layer plans into external WAV previews")
    parser.add_argument("--state", type=Path, default=Path(__file__).resolve().parents[1] / "reports" / "aiasmr" / "aiasmr_state.json")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[1] / "reports" / "aiasmr" / "render")
    parser.add_argument("--sample-rate", type=int, default=22050)
    parser.add_argument("--duration", type=float, default=1.8)
    parser.add_argument("--poll", type=float, default=0.25)
    parser.add_argument("--idle-exit-seconds", type=float, default=5.0)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    last_state_mtime = -1.0
    last_render_time = 0.0
    rendered_once = False
    while True:
        if args.state.exists():
            state_mtime = args.state.stat().st_mtime
            if state_mtime != last_state_mtime:
                payload = load_json(args.state)
                if payload is not None:
                    report = render_state(payload, args.out_dir, args.sample_rate, args.duration)
                    print(json.dumps(report, indent=2))
                    last_state_mtime = state_mtime
                    last_render_time = time.time()
                    rendered_once = True
                    if args.once:
                        return 0
        if rendered_once and not args.once and time.time() - last_render_time >= args.idle_exit_seconds:
            return 0
        time.sleep(args.poll)


if __name__ == "__main__":
    raise SystemExit(main())