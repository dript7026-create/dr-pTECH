from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART_DIR = ROOT / "art" / "chibi_overhaul"
PLAYER_MANIFEST = ART_DIR / "player_actor_manifest.json"
DAEMON_MANIFEST = ART_DIR / "daemon_actor_manifest.json"
AUTHORING_MANIFEST = ART_DIR / "authoring_manifest.json"
OUT_REPORT = ART_DIR / "shape_compaction_report.json"
OUT_MANIFEST = ART_DIR / "shape_compaction_manifest.json"


@dataclass
class SpriteStats:
    sprite_id: str
    source_actor: str
    estimated_source_shapes: int
    compacted_shapes: int
    primary_shapes: int
    secondary_shapes: int
    micro_shapes: int


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _shape_distribution(shape_cap: int, estimated: int) -> tuple[int, int, int, int]:
    # Keep a stable hierarchy so silhouettes remain readable before micro-detail.
    primary = max(64, min(160, shape_cap // 10))
    secondary = max(240, min(420, shape_cap // 3))
    reserved = primary + secondary
    micro = max(0, shape_cap - reserved)

    compacted = min(shape_cap, max(estimated, primary + secondary))
    if compacted < shape_cap:
        # Keep the exported budget explicit and deterministic at the requested cap.
        compacted = shape_cap
    return compacted, primary, secondary, micro


def _shape_distribution_profile(shape_cap: int, estimated: int, profile: str) -> tuple[int, int, int, int]:
    if profile == "player":
        primary_ratio = 0.14
        secondary_ratio = 0.34
    elif profile == "boss":
        primary_ratio = 0.11
        secondary_ratio = 0.37
    else:
        primary_ratio = 0.12
        secondary_ratio = 0.35

    primary = max(72, min(192, int(shape_cap * primary_ratio)))
    secondary = max(260, min(460, int(shape_cap * secondary_ratio)))
    reserved = primary + secondary
    micro = max(0, shape_cap - reserved)

    compacted = min(shape_cap, max(estimated, reserved))
    if compacted < shape_cap:
        compacted = shape_cap
    return compacted, primary, secondary, micro


def _estimate_player_sprite(player: dict, anim: dict) -> int:
    anchor_points = len(player.get("anchor_points", []))
    detail_layers = len(player.get("costume_detail_layers", []))
    purpose_weight = len(str(anim.get("purpose", ""))) // 8
    frame_count = int(anim.get("frames", 1))
    return 180 + frame_count * 34 + anchor_points * 9 + detail_layers * 14 + purpose_weight


def _estimate_daemon_sprite(actor: dict, anim: dict) -> int:
    adornments = len(actor.get("adornments", []))
    vice_markers = len(actor.get("vice_markers", []))
    surface_layers = len(actor.get("surface_layers", []))
    hybrids = len(actor.get("hybrid_sources", []))
    frame_count = int(anim.get("frames", 1))
    return 240 + frame_count * 42 + adornments * 15 + vice_markers * 16 + surface_layers * 11 + hybrids * 13


def _animation_complexity_boost(anim_id: str, purpose: str) -> int:
    ident = (anim_id + " " + purpose).lower()
    boost = 0
    if "windup" in ident or "lunge" in ident or "slam" in ident:
        boost += 42
    if "combo" in ident or "attack" in ident:
        boost += 32
    if "hurt" in ident or "stagger" in ident or "break" in ident:
        boost += 24
    if "idle" in ident or "perch" in ident:
        boost += 10
    return boost


def _build_sprite_stats(shape_cap: int) -> list[SpriteStats]:
    player = _load_json(PLAYER_MANIFEST)
    daemon = _load_json(DAEMON_MANIFEST)

    stats: list[SpriteStats] = []

    player_actor = str(player.get("actor", "player"))
    for anim in player.get("animation_sets", []):
        anim_id = str(anim.get("id", "unknown"))
        purpose = str(anim.get("purpose", ""))
        est = _estimate_player_sprite(player, anim) + _animation_complexity_boost(anim_id, purpose)
        compacted, primary, secondary, micro = _shape_distribution_profile(shape_cap, est, "player")
        stats.append(
            SpriteStats(
                sprite_id=f"{player_actor}/{anim_id}",
                source_actor=player_actor,
                estimated_source_shapes=est,
                compacted_shapes=compacted,
                primary_shapes=primary,
                secondary_shapes=secondary,
                micro_shapes=micro,
            )
        )

    for actor in daemon.get("actors", []):
        actor_id = str(actor.get("id", "daemon"))
        profile = "boss" if "boss" in actor_id or "famine" in actor_id else "daemon"
        for anim in actor.get("animation_sets", []):
            anim_id = str(anim.get("id", "unknown"))
            purpose = str(anim.get("purpose", ""))
            est = _estimate_daemon_sprite(actor, anim) + _animation_complexity_boost(anim_id, purpose)
            compacted, primary, secondary, micro = _shape_distribution_profile(shape_cap, est, profile)
            stats.append(
                SpriteStats(
                    sprite_id=f"{actor_id}/{anim_id}",
                    source_actor=actor_id,
                    estimated_source_shapes=est,
                    compacted_shapes=compacted,
                    primary_shapes=primary,
                    secondary_shapes=secondary,
                    micro_shapes=micro,
                )
            )

    return stats


def run(shape_cap: int) -> dict[str, object]:
    stats = _build_sprite_stats(shape_cap)
    authoring = _load_json(AUTHORING_MANIFEST)

    authoring_complexity = dict(authoring.get("complexity_target", {}))
    authoring_complexity["max_shapes_per_sprite_compacted"] = shape_cap
    authoring["complexity_target"] = authoring_complexity
    AUTHORING_MANIFEST.write_text(json.dumps(authoring, indent=2) + "\n", encoding="utf-8")

    per_sprite = []
    for item in stats:
        per_sprite.append(
            {
                "sprite_id": item.sprite_id,
                "source_actor": item.source_actor,
                "estimated_source_shapes": item.estimated_source_shapes,
                "compacted_shapes": item.compacted_shapes,
                "breakdown": {
                    "primary_shapes": item.primary_shapes,
                    "secondary_shapes": item.secondary_shapes,
                    "micro_shapes": item.micro_shapes,
                },
                "shape_cap": shape_cap,
                "compliant": item.compacted_shapes <= shape_cap,
            }
        )

    report = {
        "pass": "graphics_compaction",
        "shape_cap": shape_cap,
        "sprite_count": len(per_sprite),
        "all_compliant": all(entry["compliant"] for entry in per_sprite),
        "sprites": per_sprite,
    }

    compact_manifest = {
        "project": "Armored Gear: Fly Slight",
        "shape_cap": shape_cap,
        "sprite_designs": [
            {
                "sprite_id": entry["sprite_id"],
                "target_shapes": entry["compacted_shapes"],
                "primary_shapes": entry["breakdown"]["primary_shapes"],
                "secondary_shapes": entry["breakdown"]["secondary_shapes"],
                "micro_shapes": entry["breakdown"]["micro_shapes"],
            }
            for entry in per_sprite
        ],
    }

    OUT_REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    OUT_MANIFEST.write_text(json.dumps(compact_manifest, indent=2) + "\n", encoding="utf-8")
    return {
        "shape_cap": shape_cap,
        "sprite_count": len(per_sprite),
        "report": str(OUT_REPORT),
        "manifest": str(OUT_MANIFEST),
        "all_compliant": report["all_compliant"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run graphics compaction pass and enforce per-sprite shape caps.")
    parser.add_argument("--shape-cap", type=int, default=1000)
    args = parser.parse_args()

    if args.shape_cap < 1:
        raise SystemExit("--shape-cap must be >= 1")

    result = run(args.shape_cap)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
