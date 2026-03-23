from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RECRAFT_DIR = ROOT / "recraft"


def save_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def build_environment_manifest() -> dict:
    tiles = [
        ("brass_cobbles_clean", "Polished brass cobblestone tile with readable grout rhythm, slight soot edge wear, top-down technical surface sample."),
        ("brass_cobbles_wet", "Rain-dark brass cobblestone tile with reflective dampness, readable grout, no perspective."),
        ("wax_brick_wall", "Honey-wax brick surface tile, compressed hive masonry, readable seams and wax buildup."),
        ("crypt_stone_large", "Large crypt stone slab tile, damp mineral wear, subtle cracks, even repeat boundaries."),
        ("crypt_stone_small", "Small chiseled crypt stone tile, tight repeat-safe edges, damp underhive grit."),
        ("sewer_moss_grate", "Metal grate surface partly overtaken by green moss and damp fungal bloom, top-down tile sample."),
        ("rusted_plate_floor", "Rusted machine plate floor tile with bolt heads and maintenance seams, repeat-safe."),
        ("wax_resin_planks", "Dark resin plank floor tile with wax drips, shrine maintenance walkway sample."),
        ("ash_flagstone", "Ash-coated flagstone tile, cinder tenement paving, muted mineral breakup."),
        ("fungal_silt_ground", "Fungal silt ground tile, soft damp soil, small spores and root threads."),
        ("bone_inlay_stone", "Stone tile with subtle bone inlay channels, ritual walkway, readable from distance."),
        ("apiary_hex_pavers", "Hex-pattern apiary paver tile, brass and wax hybrid, strict repeat edges."),
        ("machine_conduit_floor", "Industrial conduit floor tile, inset cable channels and maintenance panels."),
        ("catwalk_mesh_floor", "Painted steel catwalk mesh tile, readable structural pattern, top-down sample."),
        ("salt_streak_concrete", "Weathered concrete tile with salt streaks, drain residue, and repeat-safe borders."),
        ("mural_ceramic_fragments", "Cracked ceramic tile with faint shrine mural fragments, repeat-safe distribution."),
        ("obsidian_shard_ground", "Dark shard-strewn obsidian ground tile, dangerous footing, readable silhouette contrast."),
        ("ivy_brass_lattice", "Brass lattice floor overtaken by vine growth, top-down environmental surface tile."),
        ("tar_blackened_brick", "Tar-blackened brick surface tile with oily sheen and ember staining."),
        ("wet_ropewood_deck", "Ropewood deck tile with soaked wood grain and fixed plank cadence."),
        ("beeswax_mosaic", "Beeswax shrine mosaic tile, geometric sacred pattern, crisp top-down read."),
        ("storm_drain_grit", "Storm drain grit tile with pebbles, runoff sediment, and iron stains."),
        ("chalk_sigil_floor", "Chalk-sigil floor tile, occult markings over stone, repeat-safe edge treatment."),
        ("copper_pipe_crossing", "Copper pipe crossing floor tile with embedded pipe sleeves and maintenance grime."),
        ("lantern_glass_fragments", "Glass-littered underhive floor tile with lantern fragments and dusted reflections."),
    ]
    assets = []
    for name, prompt in tiles:
        assets.append({
            "name": name,
            "category": "world_surface_tile",
            "prompt": prompt,
            "negative_prompt": "perspective, scene background, wall angle, text, logo, watermark, blur, painterly smear, crop",
            "w": 128,
            "h": 128,
            "api_units": 40,
            "model": "recraftv4",
            "out": f"environment_tiles/{name}.png",
            "runtime_target": "repeat-safe terrain surface tile",
            "surface_contract": {
                "repeat_safe": True,
                "top_down": True,
                "material_mask_ready": True,
                "height_hint_ready": True,
                "albedo_readable": True,
            },
        })
    return {
        "manifest_name": "bango_patoot_environment_surface_tiles",
        "manifest_version": "2026-03-12.rendering_world_pass",
        "intent": "1000-credit Recraft pass for 128x128 environmental surface tiles mapped across the demo world's polygonal landmass.",
        "budget": {"unit_cost": 40, "asset_count": len(assets), "total_credits": 1000},
        "shared_prompt_appendix": "Top-down orthographic material tile sample only. No scene framing. Repeat-safe on all four edges. High readability after nearest-neighbor downsample. Keep macro pattern stable and avoid perspective.",
        "integration_targets": [
            "Polygonal terrain material mapping",
            "World-space slope-based surface assignment",
            "Preview and 3DS palette reduction testing",
        ],
        "assets": assets,
    }


def build_bango_manifest() -> dict:
    assets = [
        {
            "name": "bango_turnaround_tpose_4view",
            "prompt": "Bango turnaround master sheet in T-pose, front, left profile, right profile, and rear view, transparent background, stable baseline, orthographic presentation, technical character reference.",
            "w": 2048,
            "h": 768,
            "runtime_target": "4-view rig and model reference master",
        },
        {
            "name": "bango_surface_albedo_tiles",
            "prompt": "Bango material tile sheet containing clean fur, leather, brass, horn, cloth, and wax detail swatches for polygonal model texturing, transparent or neutral presentation.",
            "w": 1024,
            "h": 1024,
            "runtime_target": "material albedo reference atlas",
        },
        {
            "name": "bango_surface_height_masks",
            "prompt": "Bango material height and relief hint atlas matching the albedo tile regions for fur, leather, brass, horn, cloth, and wax surfaces.",
            "w": 1024,
            "h": 1024,
            "runtime_target": "height-mask atlas reference",
        },
        {
            "name": "bango_surface_material_masks",
            "prompt": "Bango material mask atlas with clean separations for fur, leather, brass, horn, cloth, and wax regions, made for later texture projection and rigged model surfacing.",
            "w": 1024,
            "h": 1024,
            "runtime_target": "material-id atlas reference",
        },
        {
            "name": "bango_idle_keyposes",
            "prompt": "Bango idle keypose sheet, orthographic presentation, transparent background, readable shoulder and head motion arcs, stable feet baseline.",
            "w": 1536,
            "h": 768,
            "runtime_target": "idle keypose intake",
        },
        {
            "name": "bango_locomotion_keyposes",
            "prompt": "Bango locomotion keypose sheet for walk-run cycle, clean readable contact, down, passing, and high positions, orthographic technical presentation.",
            "w": 2048,
            "h": 768,
            "runtime_target": "locomotion keypose intake",
        },
        {
            "name": "bango_attack_keyposes",
            "prompt": "Bango combat keypose sheet for horn-rush and melee chaining, transparent background, readable torso twist and leg drive, technical animation reference.",
            "w": 2048,
            "h": 768,
            "runtime_target": "combat keypose intake",
        },
        {
            "name": "bango_recovery_keyposes",
            "prompt": "Bango dodge, recovery, and hit-react keypose sheet, orthographic, transparent background, stable silhouette for inbetween planning.",
            "w": 1536,
            "h": 768,
            "runtime_target": "recovery keypose intake",
        },
        {
            "name": "bango_expression_heads",
            "prompt": "Bango expression turnaround heads and facial material study, front, profile, and three-quarter neutralized to orthographic readability for model detailing.",
            "w": 1536,
            "h": 768,
            "runtime_target": "head detail reference",
        },
        {
            "name": "bango_accessories_sheet",
            "prompt": "Bango gear and accessory technical sheet, harness, buckles, horn bands, bracers, satchel, and shrine tokens, transparent background, modeling reference.",
            "w": 1536,
            "h": 768,
            "runtime_target": "accessory model and texture reference",
        },
    ]
    for asset in assets:
        asset.update({
            "category": "bango_character_asset",
            "negative_prompt": "perspective scene, background environment, text, watermark, blur, painterly smear, cropped body, inconsistent proportions",
            "api_units": 50,
            "model": "recraftv4",
            "out": f"bango_assets/{asset['name']}.png",
            "integration_role": [
                "bango model reference",
                "texture authoring reference",
                "animation keypose intake",
                "inbetween validation input",
            ],
        })
    return {
        "manifest_name": "bango_character_500_credit_pass",
        "manifest_version": "2026-03-12.bango_character_pass",
        "intent": "500-credit Recraft pass exclusively for Bango character art, model surfacing, turnarounds, and keypose reference.",
        "budget": {"unit_cost": 50, "asset_count": len(assets), "total_credits": 500},
        "shared_prompt_appendix": "Orthographic or effectively orthographic technical character presentation. Transparent background. Stable baseline. Full silhouette preserved. Readable small-scale material separation. Suitable for later rig tracing, mesh blockout, and keypose translation.",
        "assets": assets,
    }


def main() -> int:
    save_json(RECRAFT_DIR / "bango_patoot_environment_surface_tiles_manifest.json", build_environment_manifest())
    save_json(RECRAFT_DIR / "bango_character_500_credit_manifest.json", build_bango_manifest())
    print("Wrote rendering pass manifests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())