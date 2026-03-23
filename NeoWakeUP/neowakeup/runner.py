#!/usr/bin/env python3
"""Shared NeoWakeUP QAIJockey runner."""

import argparse
import json
import sys
import time
from pathlib import Path

from neowakeup.directive_bridge import DirectiveBridge
from neowakeup.qaijockey.platforms import create_session
from neowakeup.qaijockey.profiles import BUILTIN_PROFILES, load_profile

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = ROOT.parent
KAIJU_ROOT = WORKSPACE_ROOT / "KaijuGaiden"

DEFAULT_ROM = str(KAIJU_ROOT / "dist" / "kaijugaiden.gb")
DEFAULT_OUT = str(KAIJU_ROOT / "dist" / "qaijockey_run.avi")
DEFAULT_SKILL = 0.75
DEFAULT_TARGET_WINS = 3
DEFAULT_SPEED = 1
DEFAULT_MAX_FRAMES = 108_000
DEFAULT_GENOME_FILE = str(ROOT / "state" / "qaijockey_genome.json")
DEFAULT_INPUT_LOG = str(ROOT / "state" / "qaijockey_inputs.jsonl")
DEFAULT_PLANETARY_STATE = str(ROOT / "state" / "planetary_mind.json")
DEFAULT_BACKEND = "pyboy"
DEFAULT_DESKTOP_POLL_HZ = 60.0
DEFAULT_PROFILE = "kaijugaiden"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="NeoWakeUP QAIJockey runner", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--rom", default=DEFAULT_ROM, help="Path to the .gb ROM file")
    p.add_argument("--backend", choices=["pyboy", "desktop"], default=DEFAULT_BACKEND, help="Emulator integration backend")
    p.add_argument("--profile", default=DEFAULT_PROFILE, help=f"Game profile name or module path (built-ins: {', '.join(sorted(BUILTIN_PROFILES))})")
    p.add_argument("--skill", type=float, default=DEFAULT_SKILL, metavar="[0.0-1.0]", help="Base skill")
    p.add_argument("--target-wins", type=int, default=DEFAULT_TARGET_WINS, help="Stop after this many boss victories")
    p.add_argument("--out", default=DEFAULT_OUT, help="AVI output path")
    p.add_argument("--speed", type=int, default=DEFAULT_SPEED, help="Emulation speed multiplier")
    p.add_argument("--headless", action="store_true", help="Run without a display window")
    p.add_argument("--max-frames", type=int, default=DEFAULT_MAX_FRAMES, help="Hard frame cap")
    p.add_argument("--no-record", action="store_true", help="Skip AVI recording")
    p.add_argument("--status-every", type=int, default=300, help="Print status every N frames")
    p.add_argument("--genome-file", default=DEFAULT_GENOME_FILE, help="JSON file used to load/save evolving genome state")
    p.add_argument("--input-log", default=DEFAULT_INPUT_LOG, help="JSONL file for immediate per-input learning logs")
    p.add_argument("--no-input-log", action="store_true", help="Disable immediate input logging")
    p.add_argument("--stress-delay-ms", type=float, default=0.0, help="Artificial think delay inside the AI loop")
    p.add_argument("--stress-jitter-ms", type=float, default=0.0, help="Random extra think delay")
    p.add_argument("--tune-window", type=int, default=12, help="Recent outcomes used for win-rate tuning")
    p.add_argument("--planetary-state", default=DEFAULT_PLANETARY_STATE, help="Planetary state JSON used to bias QAIJockey via directive bridging")
    p.add_argument("--no-planetary-bridge", action="store_true", help="Disable planetary directive bridging")
    p.add_argument("--emulator", help="Desktop backend: emulator executable to launch")
    p.add_argument("--window-title", help="Desktop backend: attach to a visible emulator window title substring")
    p.add_argument("--desktop-keymap", help="Desktop backend: button mapping such as a=z,b=x,left=left,right=right,up=up,down=down,select=backspace,start=enter")
    p.add_argument("--desktop-poll-hz", type=float, default=DEFAULT_DESKTOP_POLL_HZ, help="Desktop backend: frame polling rate")
    p.add_argument("--desktop-launch-args", help="Desktop backend: extra space-separated arguments passed after the ROM path")
    p.add_argument("--desktop-no-focus", action="store_true", help="Desktop backend: do not refocus the emulator window during the run")
    return p.parse_args()


def _check_deps(record: bool, backend: str) -> None:
    missing = []
    try:
        import numpy  # noqa: F401
    except ImportError:
        missing.append("numpy")
    if backend == "pyboy":
        try:
            import pyboy  # noqa: F401
        except ImportError:
            missing.append("pyboy")
    if record:
        try:
            import cv2  # noqa: F401
        except ImportError:
            missing.append("opencv-python")
    if missing:
        print("[ERR] Missing packages:", ", ".join(missing), file=sys.stderr)
        print("      Run: pip install", " ".join(missing), file=sys.stderr)
        sys.exit(1)


def pil_to_shades(pil_img):
    import numpy as np

    grey = pil_img.convert("L")
    arr = np.frombuffer(grey.tobytes(), dtype=np.uint8).reshape(144, 160)
    shades = np.empty_like(arr, dtype=np.uint8)
    shades[arr > 192] = 0
    shades[(arr > 128) & (arr <= 192)] = 1
    shades[(arr > 48) & (arr <= 128)] = 2
    shades[arr <= 48] = 3
    return shades


def main() -> None:
    args = parse_args()
    if not (0.0 <= args.skill <= 1.0):
        print("[ERR] --skill must be in range 0.0-1.0", file=sys.stderr)
        sys.exit(1)

    rom_path = Path(args.rom)
    if not rom_path.exists():
        print(f"[ERR] ROM not found: {rom_path}", file=sys.stderr)
        sys.exit(1)

    if args.backend == "desktop" and not args.emulator and not args.window_title:
        print("[ERR] Desktop backend requires --emulator to launch or --window-title to attach.", file=sys.stderr)
        sys.exit(1)

    record = not args.no_record
    _check_deps(record, args.backend)

    from neowakeup.qaijockey.jockey import QAIJockey
    from neowakeup.qaijockey.persistence import GenomeStore, ImmediateInputLogger
    from neowakeup.qaijockey.recorder import AVIRecorder
    profile = load_profile(args.profile)

    print(f"[QAI] ROM     : {rom_path}")
    print(f"[QAI] Backend : {args.backend}")
    print(f"[QAI] Profile : {profile.name}")
    if args.backend == "pyboy":
        window = "null" if args.headless else "SDL2"
        print(f"[QAI] Window  : {window}")
        print(f"[QAI] Speed   : {args.speed}x")
    else:
        print(f"[QAI] Window  : {args.window_title or '<launched emulator window>'}")
        print(f"[QAI] PollHz  : {args.desktop_poll_hz:.1f}")
    print(f"[QAI] Skill   : {args.skill:.2f}")
    print(f"[QAI] Target  : {args.target_wins} win(s)")
    print(f"[QAI] Stress  : {args.stress_delay_ms:.1f}ms + jitter {args.stress_jitter_ms:.1f}ms")

    session = create_session(
        backend=args.backend,
        rom_path=rom_path,
        headless=args.headless,
        speed=args.speed,
        emulator_path=args.emulator,
        window_title=args.window_title,
        desktop_keymap=args.desktop_keymap,
        desktop_poll_hz=args.desktop_poll_hz,
        desktop_launch_args=args.desktop_launch_args,
        desktop_focus_window=not args.desktop_no_focus,
    )

    genome_store = GenomeStore(args.genome_file)
    learning_state = genome_store.load()
    input_logger = None if args.no_input_log else ImmediateInputLogger(args.input_log)
    directive_bridge = None if args.no_planetary_bridge else DirectiveBridge(args.planetary_state)

    jockey = QAIJockey(
        session,
        profile=profile,
        skill=args.skill,
        stress_delay_ms=args.stress_delay_ms,
        stress_jitter_ms=args.stress_jitter_ms,
        input_logger=input_logger,
        tune_window=args.tune_window,
    )
    if learning_state is not None and jockey.import_learning_state(learning_state):
        print(f"[QAI] Genome  : loaded from {args.genome_file}")
    else:
        print("[QAI] Genome  : fresh population")
    if input_logger is not None:
        print(f"[QAI] Log     : {args.input_log}")
    if directive_bridge is not None:
        directive_bridge.apply_to_qai(jockey)
        print(f"[QAI] Bridge  : {args.planetary_state}")

    recorder = None
    if record:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        recorder = AVIRecorder(str(out_path), fps=60, scale=3)
        print(f"[REC] Output  : {out_path}")
    else:
        print("[REC] Recording disabled (--no-record)")

    print("[QAI] Starting...  (Ctrl+C to stop early)\n")
    frame_n = 0
    last_status = 0
    t_start = time.perf_counter()

    try:
        while frame_n < args.max_frames:
            if directive_bridge is not None and frame_n % 60 == 0:
                directive_bridge.apply_to_qai(jockey)
            running = session.step()
            if not running:
                print("[QAI] Emulator quit.")
                break
            pil_img = session.capture_frame()
            gs = jockey.tick(pil_to_shades(pil_img))
            if recorder is not None:
                recorder.write_pil(pil_img)
            if args.status_every > 0 and frame_n - last_status >= args.status_every:
                st = jockey.stats
                elapsed = time.perf_counter() - t_start
                fps_actual = frame_n / max(elapsed, 0.001)
                print(
                    f"  f={frame_n:7d}  phase={gs.phase:<11s}  W={st['wins']}  L={st['losses']}  "
                    f"skill={st['effective_skill']:.3f}  wr={st['win_rate']:.2f}  stress={st['stress']:.2f}  "
                    f"pred={st['anticipation']}f  social={st['social_rivalry']:.2f}/{st['social_dominance']:.2f}  "
                    f"threat={st['threat']:.2f}  lag={st['reaction_lag']}->{st['comp_lag']}f  "
                    f"{profile.format_status(gs)}  fps~{fps_actual:.0f}"
                )
                last_status = frame_n
            if jockey.wins >= args.target_wins:
                print(f"\n[QAI] {args.target_wins} win(s) reached - run complete!")
                break
            frame_n += 1
    except KeyboardInterrupt:
        print("\n[QAI] Interrupted by user.")
    finally:
        genome_store.save(jockey.export_learning_state())
        if input_logger is not None:
            input_logger.close()
        if recorder is not None:
            recorder.close()
        session.close()
        elapsed = time.perf_counter() - t_start
        st = jockey.stats
        fps_real = frame_n / max(elapsed, 0.001)
        print(
            f"\n[QAI] ---- Run summary ----------------------------------------\n"
            f"      Frames  : {st['frame']}\n"
            f"      Wins    : {st['wins']}\n"
            f"      Losses  : {st['losses']}\n"
            f"      Skill   : {st['effective_skill']:.4f} (base={st['base_skill']:.2f}, avg_ms={st['avg_frame_ms']:.2f})\n"
            f"      WinRate : {st['win_rate']:.4f} (inputs={st['inputs_logged']}, gens={st['genome_generation']})\n"
            f"      Stress  : {st['stress']:.4f} (acute={st['acute_stress']:.4f}, pred={st['anticipation']}f, threat={st['threat']:.4f})\n"
            f"      Social  : rivalry={st['social_rivalry']:.3f} fear={st['social_fear']:.3f} dominance={st['social_dominance']:.3f}\n"
            f"      Genome  : pred={st['genome_predictive']:.3f} react={st['genome_reactive']:.3f} courage={st['genome_courage']:.3f}\n"
            f"      Wall    : {elapsed:.1f}s ({fps_real:.0f} fps effective)\n"
        )
        if recorder is not None:
            print(f"      Video   : {args.out}")
        print(f"      Genome  : {args.genome_file}")
        if not args.no_input_log:
            print(f"      Log     : {args.input_log}")