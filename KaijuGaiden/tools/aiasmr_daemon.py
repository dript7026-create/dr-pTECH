import argparse
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path


PROFILE_RE = re.compile(r"\[AIASMR\]\s+sc=(\d+)\s+gn=(\d+)\s+tn=(\d+)\s+pu=(\d+)\s+vc=(\d+)\s+nz=(\d+)")
EVENT_RE = re.compile(r"\[AIASMR-EVENT\]\s+ev=(\d+)\s+val=(\d+)")
TTS_RE = re.compile(r"\[TTS\]\s+sp=(\d+)\s+(.*)")

SCENE_LABELS = {
    0: "splash",
    1: "cinematic",
    2: "title",
    3: "narrative",
    4: "duel",
    5: "combat",
    6: "cypher",
    7: "gameover",
}

VOICE_LABELS = {
    0: "none",
    1: "boss",
    2: "rei",
    3: "chorus",
    4: "system",
}

MODE_TABLE = {
    0: ("phrygian", "C"),
    1: ("locrian", "A"),
    2: ("aeolian", "D"),
    3: ("phrygian-dominant", "B"),
    4: ("dorian", "F"),
    5: ("double-harmonic", "G"),
    6: ("aeolian", "Bb"),
    7: ("harmonic-minor", "Eb"),
    8: ("dorian", "Ab"),
    9: ("whole-half diminished", "Db"),
    10: ("lydian-augmented", "Gb"),
    11: ("harmonic-minor", "E"),
}

EVENT_LABELS = {
    0: "banner",
    1: "choice",
    2: "duel",
    3: "victory",
    4: "defeat",
    5: "phase",
}


@dataclass
class AudioProfile:
    scene: int = 0
    genre: int = 0
    tension: int = 0
    pulse: int = 0
    voice: int = 0
    noise: int = 0


@dataclass
class AudioDecision:
    scene_label: str
    voice_label: str
    mode: str
    root: str
    drone_gain: float
    pulse_gain: float
    lead_gain: float
    noise_gain: float
    mic_blend: float
    speech_rate: float
    speech_pitch: float
    event_label: str
    event_value: int
    last_tts: str
    realtime_synth_ready: bool
    tts_bus_ready: bool
    mic_bus_ready: bool
    instrument_emulation_ready: bool
    updated_at: float
    layers: list[dict[str, object]] = field(default_factory=list)


class AIASMRDaemon:
    def __init__(self, out_dir: Path, verbose: bool = True) -> None:
        self.out_dir = out_dir
        self.verbose = verbose
        self.profile = AudioProfile()
        self.last_event_kind = -1
        self.last_event_value = -1
        self.last_tts = ""
        self.state_path = out_dir / "aiasmr_state.json"
        self.event_log_path = out_dir / "aiasmr_events.jsonl"
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def ingest_line(self, line: str) -> bool:
        line = line.rstrip("\r\n")
        matched = False

        profile_match = PROFILE_RE.search(line)
        if profile_match:
            self.profile = AudioProfile(*(int(group) for group in profile_match.groups()))
            matched = True

        event_match = EVENT_RE.search(line)
        if event_match:
            self.last_event_kind = int(event_match.group(1))
            self.last_event_value = int(event_match.group(2))
            matched = True

        tts_match = TTS_RE.search(line)
        if tts_match:
            self.last_tts = tts_match.group(2).strip()
            matched = True

        if matched:
            self.write_state(line)
        elif self.verbose:
            print(line)
        return matched

    def current_decision(self) -> AudioDecision:
        mode, root = MODE_TABLE.get(self.profile.genre % 12, ("aeolian", "C"))
        tension_norm = self.profile.tension / 15.0
        pulse_norm = self.profile.pulse / 15.0
        noise_norm = self.profile.noise / 15.0
        voice_norm = self.profile.voice / 4.0 if self.profile.voice else 0.0
        drone_gain = round(0.22 + (1.0 - tension_norm) * 0.28, 3)
        pulse_gain = round(0.15 + pulse_norm * 0.45, 3)
        lead_gain = round(0.08 + tension_norm * 0.52, 3)
        noise_gain = round(0.05 + noise_norm * 0.35, 3)
        mic_blend = round(0.0 if self.profile.scene < 4 else min(0.45, 0.1 + noise_norm * 0.4), 3)
        speech_rate = round(0.85 + tension_norm * 0.45 + pulse_norm * 0.15, 3)
        speech_pitch = round(0.9 + voice_norm * 0.25 + (0.05 if self.profile.voice == 1 else 0.0), 3)
        layers = self.layer_stack(root, mode, drone_gain, pulse_gain, lead_gain, noise_gain)
        return AudioDecision(
            scene_label=SCENE_LABELS.get(self.profile.scene, f"scene-{self.profile.scene}"),
            voice_label=VOICE_LABELS.get(self.profile.voice, f"voice-{self.profile.voice}"),
            mode=mode,
            root=root,
            drone_gain=drone_gain,
            pulse_gain=pulse_gain,
            lead_gain=lead_gain,
            noise_gain=noise_gain,
            mic_blend=mic_blend,
            speech_rate=speech_rate,
            speech_pitch=speech_pitch,
            event_label=EVENT_LABELS.get(self.last_event_kind, "none"),
            event_value=self.last_event_value,
            last_tts=self.last_tts,
            realtime_synth_ready=True,
            tts_bus_ready=True,
            mic_bus_ready=mic_blend > 0.0,
            instrument_emulation_ready=True,
            layers=layers,
            updated_at=time.time(),
        )

    def layer_stack(
        self,
        root: str,
        mode: str,
        drone_gain: float,
        pulse_gain: float,
        lead_gain: float,
        noise_gain: float,
    ) -> list[dict[str, object]]:
        scene = self.profile.scene
        voice = self.profile.voice

        if scene in (1, 3, 7):
            drone_instrument = "low_strings"
            drone_waveform = "bow"
            drone_articulation = "sustain"
        elif scene in (4, 5):
            drone_instrument = "distorted_organ"
            drone_waveform = "organ"
            drone_articulation = "pressure"
        else:
            drone_instrument = "sub_bass_pad"
            drone_waveform = "triangle"
            drone_articulation = "drone"

        if scene == 5:
            pulse_instrument = "taiko_gate"
            pulse_waveform = "saw"
            pulse_articulation = "chop"
        elif scene == 6:
            pulse_instrument = "glass_mallet"
            pulse_waveform = "bell"
            pulse_articulation = "ostinato"
        else:
            pulse_instrument = "ritual_organ"
            pulse_waveform = "organ"
            pulse_articulation = "pulse"

        if voice == 1:
            lead_instrument = "glass_bell"
            lead_waveform = "bell"
            lead_articulation = "summon"
        elif voice == 2:
            lead_instrument = "reed_lead"
            lead_waveform = "bow"
            lead_articulation = "breath"
        elif voice == 3:
            lead_instrument = "saw_choir"
            lead_waveform = "saw"
            lead_articulation = "choral"
        else:
            lead_instrument = "pulse_synth"
            lead_waveform = "pulse"
            lead_articulation = "accent"

        layers: list[dict[str, object]] = [
            {
                "role": "drone",
                "instrument": drone_instrument,
                "waveform": drone_waveform,
                "register": "low",
                "gain": drone_gain,
                "pan": -0.15,
                "articulation": drone_articulation,
                "root": root,
                "mode": mode,
            },
            {
                "role": "pulse",
                "instrument": pulse_instrument,
                "waveform": pulse_waveform,
                "register": "mid",
                "gain": pulse_gain,
                "pan": 0.1,
                "articulation": pulse_articulation,
                "root": root,
                "mode": mode,
            },
            {
                "role": "lead",
                "instrument": lead_instrument,
                "waveform": lead_waveform,
                "register": "high",
                "gain": lead_gain,
                "pan": 0.22,
                "articulation": lead_articulation,
                "root": root,
                "mode": mode,
            },
        ]

        if noise_gain > 0.06:
            layers.append(
                {
                    "role": "texture",
                    "instrument": "air_noise",
                    "waveform": "noise",
                    "register": "full",
                    "gain": noise_gain,
                    "pan": 0.0,
                    "articulation": "bed",
                    "root": root,
                    "mode": mode,
                }
            )

        if scene >= 4:
            layers.append(
                {
                    "role": "mic_bus",
                    "instrument": "room_capture",
                    "waveform": "input",
                    "register": "full",
                    "gain": round(0.1 + min(0.35, noise_gain), 3),
                    "pan": 0.0,
                    "articulation": "reactive",
                    "root": root,
                    "mode": mode,
                }
            )

        return layers

    def write_state(self, source_line: str) -> None:
        decision = self.current_decision()
        payload = {
            "profile": asdict(self.profile),
            "decision": asdict(decision),
            "capabilities": {
                "realtime_synth": True,
                "multi_layer": True,
                "instrument_emulation": True,
                "tts": True,
                "mic_input": True,
            },
            "source": source_line,
        }
        self.state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        with self.event_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")
        if self.verbose:
            print(json.dumps(payload, indent=2))


def enqueue_stream(stream, out_queue: "queue.Queue[str]") -> None:
    try:
        for line in iter(stream.readline, ""):
            if not line:
                break
            out_queue.put(line)
    finally:
        stream.close()


def run_subprocess(daemon: AIASMRDaemon, command: list[str]) -> int:
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        text=True,
        bufsize=1,
    )
    assert process.stdout is not None
    out_queue: "queue.Queue[str]" = queue.Queue()
    reader = threading.Thread(target=enqueue_stream, args=(process.stdout, out_queue), daemon=True)
    reader.start()

    while process.poll() is None or not out_queue.empty():
        try:
            line = out_queue.get(timeout=0.1)
        except queue.Empty:
            continue
        daemon.ingest_line(line)

    reader.join(timeout=1.0)
    return int(process.returncode or 0)


def main() -> int:
    parser = argparse.ArgumentParser(description="AIASMR sidecar for Kaiju Gaiden host audio events")
    parser.add_argument("--exe", help="Optional game executable to supervise")
    parser.add_argument("--args", nargs=argparse.REMAINDER, help="Arguments passed to the supervised executable")
    parser.add_argument("--out-dir", default=str(Path(__file__).resolve().parents[1] / "reports" / "aiasmr"))
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    daemon = AIASMRDaemon(Path(args.out_dir), verbose=not args.quiet)

    if args.exe:
        command = [args.exe] + (args.args or [])
        return run_subprocess(daemon, command)

    for line in sys.stdin:
        daemon.ingest_line(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())