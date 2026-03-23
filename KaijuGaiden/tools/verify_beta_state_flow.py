import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


REQUIRED_SCENES = {0, 1, 2, 3, 4, 5, 6}


def run_verification(root: Path, python_exe: str, exe: Path, timeout: int, stage_limit: int, out_dir: Path) -> dict[str, object]:
    daemon = root / "tools" / "aiasmr_daemon.py"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["KAIJU_AUTOPLAY"] = "1"
    env["KAIJU_AUTOPLAY_STAGE_LIMIT"] = str(stage_limit)
    command = [python_exe, str(daemon), "--quiet", "--out-dir", str(out_dir), "--exe", str(exe)]
    completed = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True, timeout=timeout, check=True)
    events_path = out_dir / "aiasmr_events.jsonl"
    state_path = out_dir / "aiasmr_state.json"
    if not events_path.exists() or not state_path.exists():
        raise FileNotFoundError("Verification run did not emit AIASMR report files")
    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    scenes_seen = {int(item["profile"]["scene"]) for item in events}
    event_labels = sorted({str(item["decision"]["event_label"]) for item in events if str(item["decision"]["event_label"]) != "none"})
    tts_lines = [str(item["decision"].get("last_tts", "")) for item in events if str(item["decision"].get("last_tts", ""))]
    missing_scenes = sorted(REQUIRED_SCENES - scenes_seen)
    return {
        "exit_code": completed.returncode,
        "event_count": len(events),
        "scenes_seen": sorted(scenes_seen),
        "missing_scenes": missing_scenes,
        "event_labels": event_labels,
        "tts_samples": tts_lines[:8],
        "state_path": str(state_path),
        "events_path": str(events_path),
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Verify Kaiju Gaiden host beta state flow under AIASMR autoplay supervision")
    parser.add_argument("--python", default=str(root.parents[0] / ".venv" / "Scripts" / "python.exe"))
    parser.add_argument("--exe", default=str(root / "kaijugaiden_sdl_console.exe"))
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--stage-limit", type=int, default=1)
    parser.add_argument("--out-dir", default=str(root / "reports" / "aiasmr_verify"))
    args = parser.parse_args()

    python_exe = args.python if Path(args.python).exists() else sys.executable
    report = run_verification(root, python_exe, Path(args.exe), args.timeout, args.stage_limit, Path(args.out_dir))
    print(json.dumps(report, indent=2))
    return 1 if report["missing_scenes"] else 0


if __name__ == "__main__":
    raise SystemExit(main())