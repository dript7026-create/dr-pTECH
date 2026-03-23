import argparse
import json
from pathlib import Path

import game_pipeline


DEFAULT_TRANSLATION_PROFILE = {
    "clipstudio": "depth_mapped_2d",
    "blender": "sideways_depth_lift",
    "idtech2": "forward_autofactor",
}


def load_scene(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict | list) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def build_translation_profile(scene: dict) -> dict:
    profile = dict(DEFAULT_TRANSLATION_PROFILE)
    profile.update(scene.get("translation_profile", {}))
    return profile


def build_clipstudio_authoring(scene: dict, translation_profile: dict) -> dict:
    clip = dict(scene.get("bridges", {}).get("clipstudio", {}))
    bindings = scene.get("bindings", {})
    depth_cards = []
    for card in scene.get("assets", {}).get("depth_cards", []):
        depth_cards.append(
            {
                "id": card["id"],
                "color_path": card["color_path"],
                "depth_map": card["depth_map"],
                "normal_map": card.get("normal_map"),
                "layer_group": card.get("layer_group", card["id"]),
                "frames": card.get("frames", 1),
                "usage": card.get("usage", "generic"),
                "depth_channel": card.get("depth_channel", "value"),
                "lift_mode": card.get("lift_mode", "depth_card"),
            }
        )
    return {
        "canvas": scene["canvas"],
        "timeline_fps": clip.get("timeline_fps", 12),
        "export_profile": clip.get(
            "export_profile",
            {
                "color_mode": "rgba",
                "naming": "asset_id",
                "slice_method": "layer_group",
                "depth_map_mode": "grayscale_relief",
            },
        ),
        "layers": clip.get("layers", []),
        "script_symbols": bindings.get("script_symbols", []),
        "symbol_bindings": bindings.get("symbol_bindings", []),
        "frame_tags": bindings.get("frame_tags", []),
        "hitboxes": bindings.get("hitboxes", []),
        "script_bindings": bindings.get("script_bindings", []),
        "depth_cards": depth_cards,
        "translation_mode": translation_profile["clipstudio"],
    }


def build_blender_authoring(scene: dict, translation_profile: dict) -> dict:
    blender = dict(scene.get("bridges", {}).get("blender", {}))
    return {
        "scale": blender.get("scale", 0.1),
        "extrusion_depth": blender.get("extrusion_depth", 0.08),
        "lift_mode": blender.get("lift_mode", "depth_card"),
        "rig_profile": blender.get("rig_profile", "paperdoll_humanoid"),
        "material_profiles": blender.get("material_profiles", []),
        "rig_overrides": blender.get("rig_overrides", []),
        "nodecraft_graphs": blender.get("nodecraft_graphs", []),
        "scene_build": blender.get("scene_build", []),
        "translation_mode": translation_profile["blender"],
    }


def build_idtech2_authoring(scene: dict, translation_profile: dict) -> dict:
    idtech2 = dict(scene.get("bridges", {}).get("idtech2", {}))
    if "module_name" not in idtech2 or "asset_root" not in idtech2 or "autofactor_prefix" not in idtech2:
        raise ValueError("bridges.idtech2 must define module_name, asset_root, and autofactor_prefix")
    return {
        "module_name": idtech2["module_name"],
        "asset_root": idtech2["asset_root"],
        "autofactor_prefix": idtech2["autofactor_prefix"],
        "precache_groups": idtech2.get("precache_groups", []),
        "system_dispatch": idtech2.get("system_dispatch", {}),
        "bootstrap": idtech2.get("bootstrap", {}),
        "translation_mode": translation_profile["idtech2"],
    }


def build_assets(scene: dict) -> dict:
    assets = scene.get("assets", {})
    sprites = []
    for card in assets.get("depth_cards", []):
        sprites.append(
            {
                "id": card["id"],
                "path": card["color_path"],
                "depth_map": card["depth_map"],
                "normal_map": card.get("normal_map"),
                "frames": card.get("frames", 1),
                "usage": card.get("usage", "generic"),
                "material_profile": card.get("material_profile", "default_sprite_material"),
                "lift_mode": card.get("lift_mode", "depth_card"),
                "collider": card.get("collider", {"shape": "capsule"}),
                "precache": card.get("precache", True),
            }
        )
    return {
        "tilesets": assets.get("tilesets", []),
        "sprites": sprites,
        "portraits": assets.get("portraits", []),
    }


def build_targets(scene: dict) -> dict:
    targets = dict(scene.get("targets", {}))
    targets.setdefault("clipstudio_bundle", "clipstudio_bundle")
    targets.setdefault("blender_bundle", "blender_bundle")
    targets.setdefault("idtech2_bundle", "idtech2_bundle")
    return targets


def transpile_scene(scene: dict) -> dict:
    if "project_name" not in scene or "canvas" not in scene:
        raise ValueError("Scene must define project_name and canvas")
    translation_profile = build_translation_profile(scene)
    return {
        "project_name": scene["project_name"],
        "seed": scene.get("seed", "DRIP3D-ALPHA"),
        "driptech_scene_version": scene.get("driptech_scene_version", "1.0"),
        "translation_profile": translation_profile,
        "authoring": {
            "clipstudio": build_clipstudio_authoring(scene, translation_profile),
            "blender": build_blender_authoring(scene, translation_profile),
            "idtech2": build_idtech2_authoring(scene, translation_profile),
        },
        "assets": build_assets(scene),
        "gameplay": {
            "scenes": scene.get("scenes", []),
            "entities": scene.get("entities", []),
            "systems": scene.get("systems", []),
        },
        "targets": build_targets(scene),
    }


def transpile(scene_path: Path, out_path: Path) -> Path:
    scene = load_scene(scene_path)
    canonical = transpile_scene(scene)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(out_path, canonical)
    return out_path


def build(scene_path: Path, out_root: Path) -> None:
    out_root.mkdir(parents=True, exist_ok=True)
    canonical_path = out_root / "game_project.generated.json"
    transpile(scene_path, canonical_path)
    game_pipeline.build(canonical_path, out_root)


def main() -> int:
    parser = argparse.ArgumentParser(description="drIpTECH proprietary scene compiler")
    sub = parser.add_subparsers(dest="command", required=True)

    transpile_parser = sub.add_parser("transpile", help="Convert a drIpTECH scene file into a canonical egosphere manifest")
    transpile_parser.add_argument("--project", required=True, type=Path)
    transpile_parser.add_argument("--out", required=True, type=Path)

    build_parser = sub.add_parser("build", help="Build all bundles from a drIpTECH scene file")
    build_parser.add_argument("--project", required=True, type=Path)
    build_parser.add_argument("--out", required=True, type=Path)

    args = parser.parse_args()
    if args.command == "transpile":
        output = transpile(args.project, args.out)
        print(json.dumps({"canonical_project": str(output)}, indent=2))
        return 0
    if args.command == "build":
        build(args.project, args.out)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
