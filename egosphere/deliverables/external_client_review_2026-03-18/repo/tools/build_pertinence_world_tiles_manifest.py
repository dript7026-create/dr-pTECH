import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT / "pipeline" / "projects" / "pertinence_tribunal"
OUTPUT_MANIFEST = PROJECT_ROOT / "recraft_world_tiles_pass_manifest.json"
OUTPUT_PLAN = PROJECT_ROOT / "WORLD_TILE_PLAN.md"

STYLE_BIBLE = (
    "cohesive 2D side-view metroidvania environment concept tile, hand-painted souls-like world art, "
    "Pertinence: Tribunal visual bible, readable traversal lanes for real-time exploration and real-time combat, "
    "consistent side-view scale, coherent lighting, coherent architectural language, no text"
)

TILE_ROLES = [
    ("skyline_backdrop", "wide atmospheric skyline backdrop establishing the region horizon and weather rhythm"),
    ("far_parallax", "far-distance parallax layer with major silhouettes and long-depth shapes"),
    ("mid_parallax", "mid-distance parallax layer with readable structures and traversal foreshadowing"),
    ("floor_run", "primary walkable floor tile strip for standard traversal and melee combat footing"),
    ("floor_broken", "damaged or interrupted floor tile strip for jumps, drops, and combat spacing variation"),
    ("wall_face", "main wall tile surface with repeatable material logic for full-area construction"),
    ("wall_corner", "inner or outer wall corner transition tile with consistent masonry or timber logic"),
    ("platform_bridge", "elevated bridge or platform tile segment for layered traversal routes"),
    ("gate_arch", "gate, archway, or threshold tile module for chokepoints and route transitions"),
    ("traversal_vertical", "vertical traversal tile setpiece such as ladder shaft, chainwell, or elevator spine"),
    ("hazard_overlay", "combat hazard or weather overlay supporting the region tone while preserving gameplay readability"),
    ("landmark_setpiece", "hero landmark panel anchoring the region identity and route memory"),
]

REGIONS = [
    {
        "id": "hallowfen_borderlands",
        "title": "Hallowfen Borderlands",
        "palette": "peat black, tannin brown, rotten reed gold, damp bone ivory, rusted lantern orange",
        "direction": "flood barriers, reed villages, plague warnings, and leaning timber walkways at the frontier of the accusation",
    },
    {
        "id": "tribunal_causeway",
        "title": "Tribunal Causeway",
        "palette": "cold sandstone, verdict brass, rain slate, signal crimson, fog blue",
        "direction": "monumental bridges, legal statuary, sealed gates, and militarized checkpoints leading toward the capital court",
    },
    {
        "id": "salt_forest_canopy",
        "title": "Salt Forest Canopy",
        "palette": "mineral green, bark umber, lichen silver, ash rose, deep marsh teal",
        "direction": "root bridges, hanging shrines, salt-crusted trunks, canopy ladders, and watch posts woven through giant trees",
    },
    {
        "id": "ferry_crypts",
        "title": "Ferry Crypts",
        "palette": "grave moss, ferry rope brown, candle amber, soaked stone gray, brine black",
        "direction": "submerged catacombs, mooring piers, tomb ferries, bone alcoves, and flood-locked passages beneath the river trade",
    },
    {
        "id": "plague_abbey",
        "title": "Plague Abbey",
        "palette": "smoke ivory, mold green, ceremonial scarlet, weathered oak, incense gold",
        "direction": "diseased cloisters, censor platforms, abbey engines, reliquary halls, and ritual kill-zones for inquisitorial combat",
    },
    {
        "id": "ossuary_depths",
        "title": "Ossuary Depths",
        "palette": "chalk bone, violet shadow, corroded silver, dust beige, moonlit gray",
        "direction": "stacked catacombs, skull columns, burial shafts, broken lifts, and compressive corridors with duel-friendly spacing",
    },
    {
        "id": "archive_vaults",
        "title": "Archive Vaults",
        "palette": "ink black, vellum cream, wax red, brass hinge gold, library umber",
        "direction": "document towers, rotating stacks, chain elevators, ledgers, and evidence chambers built for route recall and secret doors",
    },
    {
        "id": "cathedral_of_rotated_truth",
        "title": "Cathedral of Rotated Truth",
        "palette": "liturgy gold, stained blue, nave stone, blood maroon, judgment white",
        "direction": "rotating nave segments, verdict machinery, suspended chapels, mirrored aisles, and grand dueling terraces",
    },
    {
        "id": "goduly_aether",
        "title": "Goduly Aether",
        "palette": "astral cyan, ember amber, void navy, halo white, sacred jade",
        "direction": "cosmic causeways, prayer orbits, astral bridges, folded reality steps, and ceremonial combat arenas in deity space",
    },
    {
        "id": "pertinence_ruin",
        "title": "Pertinence Ruin",
        "palette": "storm bronze, cinder gray, plague green, broken marble, eclipse violet",
        "direction": "endgame courthouse ruins, torn banners, collapsed verdict platforms, siege scars, and final-route convergences for late-game traversal",
    },
]


def build_manifest() -> list[dict]:
    items = []
    for region in REGIONS:
        for role_name, role_desc in TILE_ROLES:
            asset_id = f"{region['id']}_{role_name}"
            is_overlay = role_name == "hazard_overlay"
            background_rule = (
                "transparent background overlay only, no opaque backdrop, gameplay FX layer" if is_overlay
                else "full environment panel, production-ready world tile concept"
            )
            prompt = (
                f"{STYLE_BIBLE}, {background_rule}, region: {region['title']}, "
                f"visual direction: {region['direction']}, palette emphasis: {region['palette']}, "
                f"asset role: {role_desc}, coherent with the other Pertinence: Tribunal world tiles, "
                f"suitable for interconnected metroidvania world development"
            )
            items.append(
                {
                    "name": asset_id,
                    "prompt": prompt,
                    "w": 1024,
                    "h": 1024,
                    "out": f"authoring/clipstudio/tiles/world_buildout/{asset_id}.png",
                    "api_units": 40,
                    "model": "recraftv4",
                }
            )
    return items


def build_plan(items: list[dict]) -> str:
    total_units = sum(item["api_units"] for item in items)
    lines = [
        "# Pertinence World Tile Pass",
        "",
        f"Total assets: {len(items)}",
        f"Estimated units: {total_units}",
        "",
        "## Regions",
    ]
    for region in REGIONS:
        lines.extend(
            [
                f"### {region['title']}",
                f"- id: {region['id']}",
                f"- palette: {region['palette']}",
                f"- direction: {region['direction']}",
            ]
        )
    lines.extend(
        [
            "",
            "## Tile Roles",
        ]
    )
    for role_name, role_desc in TILE_ROLES:
        lines.append(f"- {role_name}: {role_desc}")
    return "\n".join(lines) + "\n"


def main() -> int:
    PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
    items = build_manifest()
    OUTPUT_MANIFEST.write_text(json.dumps(items, indent=2), encoding="utf-8")
    OUTPUT_PLAN.write_text(build_plan(items), encoding="utf-8")
    print(
        json.dumps(
            {
                "manifest": str(OUTPUT_MANIFEST),
                "plan": str(OUTPUT_PLAN),
                "items": len(items),
                "estimated_units": sum(item["api_units"] for item in items),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())