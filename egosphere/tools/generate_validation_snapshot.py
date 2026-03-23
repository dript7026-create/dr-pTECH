import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_command(command: list[str]) -> str:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def extract_last_json_block(text: str) -> dict:
    decoder = json.JSONDecoder()
    candidate = None
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            obj, end = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if text[index + end :].strip() == "":
            candidate = obj
    if candidate is None:
        raise ValueError("Could not locate trailing JSON block in command output")
    return candidate


def to_relative_path(path_str: str) -> str:
    path = Path(path_str)
    try:
        relative = path.resolve().relative_to(ROOT.resolve())
        return relative.as_posix()
    except Exception:
        return path_str.replace("\\", "/")


def parse_smoke_summary(output: str) -> dict:
    match = re.search(
        r"smoke-test ok: (?P<name>.+?) \[(?P<archetype>.+?)\] threat=(?P<threat>[0-9.]+) pressure=(?P<pressure>[0-9.]+) combo=(?P<combo>[0-9.]+) mercy=(?P<mercy>[0-9.]+) ambition=(?P<ambition>[0-9.]+) engagements=(?P<engagements>[0-9]+)",
        output,
    )
    if match is None:
        raise ValueError("Could not parse smoke test summary")
    return {
        "rival_name": match.group("name"),
        "archetype": match.group("archetype"),
        "threat": float(match.group("threat")),
        "pressure": float(match.group("pressure")),
        "combo": float(match.group("combo")),
        "mercy": float(match.group("mercy")),
        "ambition": float(match.group("ambition")),
        "engagements": int(match.group("engagements")),
    }


def parse_demo_summary(output: str) -> dict:
    rival_match = re.search(
        r"rival after load:\s+(?P<name>.+?) \[(?P<archetype>.+?)\] threat=(?P<threat>[0-9.]+) pressure=(?P<pressure>[0-9.]+) combo=(?P<combo>[0-9.]+) mercy=(?P<mercy>[0-9.]+) ambition=(?P<ambition>[0-9.]+) engagements=(?P<engagements>[0-9]+)",
        output,
    )
    planner_match = re.search(
        r"reloaded planner: states=(?P<states>[0-9]+) actions=(?P<actions>[0-9]+) replay_capacity=(?P<replay>[0-9]+)",
        output,
    )
    resonance_match = re.search(
        r"reloaded resonance: familiarity=(?P<familiarity>[0-9.]+) reciprocity=(?P<reciprocity>[0-9.]+) tension=(?P<tension>[0-9.]+) permeability=(?P<permeability>[0-9.]+)",
        output,
    )
    narrative_match = re.search(
        r"narrative field: active=(?P<active>[0-9]+) revelation=(?P<revelation>[0-9.]+) alliance=(?P<alliance>[0-9.]+) rupture=(?P<rupture>[0-9.]+) ending=(?P<ending>[0-9.]+) omen=(?P<omen>[0-9.]+)",
        output,
    )
    if None in (rival_match, planner_match, resonance_match, narrative_match):
        raise ValueError("Could not parse demo runtime summary")
    return {
        "final_rival_name": rival_match.group("name"),
        "archetype": rival_match.group("archetype"),
        "threat": float(rival_match.group("threat")),
        "pressure": float(rival_match.group("pressure")),
        "combo": float(rival_match.group("combo")),
        "mercy": float(rival_match.group("mercy")),
        "ambition": float(rival_match.group("ambition")),
        "engagements": int(rival_match.group("engagements")),
        "reloaded_planner_states": int(planner_match.group("states")),
        "reloaded_planner_actions": int(planner_match.group("actions")),
        "replay_capacity": int(planner_match.group("replay")),
        "resonance": {
            "familiarity": float(resonance_match.group("familiarity")),
            "reciprocity": float(resonance_match.group("reciprocity")),
            "tension": float(resonance_match.group("tension")),
            "permeability": float(resonance_match.group("permeability")),
        },
        "narrative_field": {
            "active": int(narrative_match.group("active")),
            "revelation": float(narrative_match.group("revelation")),
            "alliance": float(narrative_match.group("alliance")),
            "rupture": float(narrative_match.group("rupture")),
            "ending": float(narrative_match.group("ending")),
            "omen": float(narrative_match.group("omen")),
        },
    }


def build_snapshot(python_exe: str) -> dict:
    smoke_output = run_command(["make", "smoke-test"])
    suite_output = run_command([python_exe, str(ROOT / "tools" / "validate_pipeline.py"), "--suite", "all"])
    run_command(["make", "all"])
    demo_output = run_command([str(ROOT / "demo.exe")])

    smoke_summary = parse_smoke_summary(smoke_output)
    suite_summary = extract_last_json_block(suite_output)
    demo_summary = parse_demo_summary(demo_output)

    sample_result = next(item for item in suite_summary["results"] if item.get("project") == "sample")
    pertinence_result = next(item for item in suite_summary["results"] if item.get("project") == "pertinence")

    return {
        "prepared_date": datetime.now().strftime("%Y-%m-%d"),
        "prepared_at": datetime.now().astimezone().isoformat(),
        "repository": "egosphere",
        "review_scope": [
            "core gameplay cognition module",
            "full pipeline validation suite",
            "Pertinence Tribunal scaled example",
            "demo runtime save/load snapshot",
        ],
        "core_module": {
            "command": "make smoke-test",
            "status": "passed",
            "summary": smoke_summary,
        },
        "validation_suite": {
            "command": f"{python_exe.replace('\\', '/')} tools/validate_pipeline.py --suite all",
            "status": "passed",
            "sample": {
                "project_name": sample_result["project_name"],
                "system_count": sample_result["system_count"],
                "entity_count": sample_result["entity_count"],
                "precache_count": sample_result["precache_count"],
                "pipeline_output": {
                    key: to_relative_path(value)
                    for key, value in sample_result["pipeline_output"].items()
                },
            },
            "pertinence": {
                "build_output": {
                    "project_root": to_relative_path(pertinence_result["build_output"]["project_root"]),
                    "sprite_assets": pertinence_result["build_output"]["sprite_assets"],
                    "tilesets": pertinence_result["build_output"]["tilesets"],
                    "portraits": pertinence_result["build_output"]["portraits"],
                    "fx_assets": pertinence_result["build_output"]["fx_assets"],
                    "recraft_requests": pertinence_result["build_output"]["recraft_requests"],
                    "recraft_budget_units": pertinence_result["build_output"]["recraft_budget_units"],
                },
                "asset_checks": {
                    "png_assets_checked": pertinence_result["png_assets_checked"],
                    "png_transparency_failures": len(pertinence_result["png_transparency_failures"]),
                },
                "blender_report": {
                    "mode": pertinence_result["blender_report"]["mode"],
                    "scene_count": pertinence_result["blender_report"]["scene_count"],
                    "lift_count": pertinence_result["blender_report"]["lift_count"],
                },
                "idtech_summary": pertinence_result["idtech_summary"],
                "recraft_manifest": {
                    "path": to_relative_path(pertinence_result["recraft_manifest"]["path"]),
                    "api_key_present": pertinence_result["recraft_manifest"]["api_key_present"],
                },
            },
        },
        "demo_runtime": {
            "command": ".\\demo.exe",
            "status": "passed",
            "summary": demo_summary,
        },
        "review_notes": [
            "Historical Pertinence contact-sheet review folders are empty in the current repository snapshot.",
            "Legacy markdown lint issues exist in some generated docs but do not block the validated code and bundle outputs.",
            "This snapshot is intended for review, not final production signoff.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-dir", required=True)
    parser.add_argument("--python-exe", default="python")
    args = parser.parse_args()

    snapshot = build_snapshot(args.python_exe)
    output_path = Path(args.review_dir) / "VALIDATION_SNAPSHOT.json"
    output_path.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(str(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())