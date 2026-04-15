from __future__ import annotations

import json
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    generation_dir = project_root / "generation"
    generated_dir = project_root / "generated" / "runtime"
    generated_dir.mkdir(parents=True, exist_ok=True)

    prefabs = load_json(project_root / "prefabs.json").get("prefabs", [])
    jumpclip = load_json(generation_dir / "jumpclip_runs.json")
    recraft = load_json(generation_dir / "recraft_manifest.json").get("assets", [])
    audio = load_json(generation_dir / "audio_manifest.json").get("assets", [])

    fps = int(jumpclip.get("_notes", {}).get("fps", 24))
    jobs = jumpclip.get("jobs", [])

    jumpclip_index = {job["name"]: job for job in jobs}
    visual_index = {asset["name"]: asset for asset in recraft}
    audio_index = {asset["name"]: asset for asset in audio}

    actors = []
    encounters = []
    cues = []

    for prefab in prefabs:
        role = prefab.get("role")
        prefab_id = prefab.get("id", "")
        outputs = prefab.get("generated_outputs", [])

        animation_jobs = []
        visual_assets = []
        audio_assets = []

        for output in outputs:
            if output.startswith("generated/jumpclip/"):
                job_name = output.split("/")[-1]
                if job_name in jumpclip_index:
                    job = jumpclip_index[job_name]
                    animation_jobs.append(
                        {
                            "job": job_name,
                            "frames": int(job.get("frames", 0)),
                            "fps": fps,
                            "duration_seconds": round(int(job.get("frames", 0)) / float(fps), 4),
                            "prompt": job.get("prompt", ""),
                            "out_dir": output,
                        }
                    )
            elif output.startswith("assets/visual/"):
                asset_name = Path(output).stem
                if asset_name in visual_index:
                    visual_assets.append(
                        {
                            "name": asset_name,
                            "path": output,
                            "prompt": visual_index[asset_name].get("prompt", ""),
                            "size": [visual_index[asset_name].get("w", 0), visual_index[asset_name].get("h", 0)],
                            "transparent": bool(visual_index[asset_name].get("transparent_background", False)),
                        }
                    )
                else:
                    visual_assets.append({"name": asset_name, "path": output})
            elif output.startswith("assets/audio/"):
                asset_name = Path(output).stem
                if asset_name in audio_index:
                    audio_assets.append(
                        {
                            "name": asset_name,
                            "path": output,
                            "prompt": audio_index[asset_name].get("prompt", ""),
                            "duration_seconds": audio_index[asset_name].get("duration_seconds", 0),
                        }
                    )
                else:
                    audio_assets.append({"name": asset_name, "path": output})

        node = {
            "id": prefab_id,
            "name": prefab.get("name"),
            "combat_pattern": prefab.get("combat_pattern", ""),
            "visual_assets": visual_assets,
            "audio_assets": audio_assets,
            "animation_jobs": animation_jobs,
        }

        if role == "actor" and prefab_id.startswith("sparkle-tier"):
            node["outfit_tier"] = int(prefab.get("outfit_tier", 0))
            node["dress_charge_threshold"] = int(prefab.get("dress_charge_threshold", 0))
            actors.append(node)
        elif role == "actor" and prefab_id.startswith("litemite-archetype"):
            node["archetype_index"] = int(prefab.get("archetype_index", 0))
            node["tail_segments"] = int(prefab.get("tail_segments", 0))
            node["swarm_count"] = int(prefab.get("swarm_count", 0))
            node["orbit_speed"] = float(prefab.get("orbit_speed", 1.0))
            encounters.append(node)
        elif role == "trigger":
            node["lane_index"] = int(prefab.get("lane_index", -1))
            node["cue_form"] = int(prefab.get("cue_form", -1))
            cues.append(node)

    actors.sort(key=lambda x: x.get("outfit_tier", 0))
    encounters.sort(key=lambda x: x.get("archetype_index", 0))
    cues.sort(key=lambda x: x.get("lane_index", 99))

    runtime_pack = {
        "pack_name": "dress-sparle-runtime-animation-pack",
        "pack_version": 1,
        "frame_rate": fps,
        "actors": actors,
        "encounters": encounters,
        "cues": cues,
        "jumpclip_job_count": len(jobs),
        "recraft_asset_count": len(recraft),
        "audio_asset_count": len(audio),
    }

    archetype_map = {
        encounter["id"]: {
            "archetype_index": encounter.get("archetype_index", 0),
            "pattern": encounter.get("combat_pattern", ""),
            "phase_timeline": [
                {"phase": "intro", "beats": 8},
                {"phase": "pressure", "beats": 16},
                {"phase": "lock_window", "beats": 8},
                {"phase": "resolution", "beats": 8},
            ],
            "animation_jobs": [job["job"] for job in encounter.get("animation_jobs", [])],
        }
        for encounter in encounters
    }

    (generated_dir / "dress_sparle_runtime_pack.json").write_text(
        json.dumps(runtime_pack, indent=2), encoding="utf-8"
    )
    (generated_dir / "combat_pattern_book.json").write_text(
        json.dumps(archetype_map, indent=2), encoding="utf-8"
    )

    print(f"Wrote {(generated_dir / 'dress_sparle_runtime_pack.json')}")
    print(f"Wrote {(generated_dir / 'combat_pattern_book.json')}")


if __name__ == "__main__":
    main()
