import argparse
import json
from pathlib import Path


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_project(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict | list) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def flatten_assets(project: dict) -> list[dict]:
    assets = []
    for asset_type, items in project["assets"].items():
        singular_type = asset_type[:-1] if asset_type.endswith("s") else asset_type
        for item in items:
            asset = dict(item)
            asset.setdefault("asset_type", singular_type)
            assets.append(asset)
    return assets


def normalize_systems(project: dict) -> list[dict]:
    systems = []
    dispatch = project["authoring"]["idtech2"].get("system_dispatch", {})
    for index, item in enumerate(project["gameplay"]["systems"]):
        if isinstance(item, str):
            system = {"name": item}
        else:
            system = dict(item)
        system.setdefault("priority", index)
        system.setdefault("lifecycle", ["init", "tick"])
        system.setdefault("init_fn", dispatch.get(system["name"], {}).get("init_fn", f"{system['name']}_init"))
        system.setdefault("tick_fn", dispatch.get(system["name"], {}).get("tick_fn", f"{system['name']}_tick"))
        systems.append(system)
    return systems


def collect_precache_entries(project: dict) -> list[dict]:
    assets = flatten_assets(project)
    precache = []
    for asset in assets:
        if asset.get("precache", True):
            precache.append(
                {
                    "alias": asset["id"],
                    "path": asset["path"],
                    "asset_type": asset["asset_type"],
                }
            )
    for group in project["authoring"]["idtech2"].get("precache_groups", []):
        for entry in group.get("entries", []):
            precache.append(
                {
                    "alias": entry["alias"],
                    "path": entry["path"],
                    "asset_type": entry.get("asset_type", group.get("group_name", "generic")),
                }
            )
    return precache


def generate_blender_ingest_script(project: dict) -> str:
    project_name = project["project_name"]
    return "\n".join(
        [
            '"""Generated Blender ingest helper for the drIpTECH pipeline."""',
            "",
            "from __future__ import annotations",
            "",
            "import json",
            "from pathlib import Path",
            "",
            "try:",
            "    import bpy  # type: ignore",
            "except ImportError:",
            "    bpy = None",
            "",
            "",
            "def load_bundle(bundle_path: str | Path) -> dict:",
            "    bundle_file = Path(bundle_path)",
            "    return json.loads(bundle_file.read_text(encoding=\"utf-8\"))",
            "",
            "",
            "def ensure_collection(name: str):",
            "    if bpy is None:",
            "        return None",
            "    collection = bpy.data.collections.get(name)",
            "    if collection is None:",
            "        collection = bpy.data.collections.new(name)",
            "        bpy.context.scene.collection.children.link(collection)",
            "    return collection",
            "",
            "",
            "def build_scene(bundle_path: str | Path) -> dict:",
            "    payload = load_bundle(bundle_path)",
            "    report = {\"project_name\": payload[\"project_name\"], \"created_objects\": []}",
            "    if bpy is None:",
            "        report[\"mode\"] = \"dry-run\"",
            "        report[\"scene_count\"] = len(payload.get(\"world_plan\", {}).get(\"scenes\", []))",
            "        report[\"lift_count\"] = len(payload.get(\"lift_plan\", []))",
            "        return report",
            "",
            f"    root = ensure_collection(\"{project_name}_pipeline\")",
            "    for scene in payload.get(\"world_plan\", {}).get(\"scenes\", []):",
            "        empty = bpy.data.objects.new(scene[\"id\"], None)",
            "        empty.empty_display_type = \"PLAIN_AXES\"",
            "        empty.location = (0.0, 0.0, 0.0)",
            "        root.objects.link(empty)",
            "        report[\"created_objects\"].append(scene[\"id\"])",
            "",
            "    for lift in payload.get(\"lift_plan\", []):",
            "        mesh = bpy.data.meshes.new(f\"{lift['asset_id']}_mesh\")",
            "        obj = bpy.data.objects.new(lift[\"asset_id\"], mesh)",
            "        root.objects.link(obj)",
            "        obj[\"source_path\"] = lift[\"source_path\"]",
            "        obj[\"extrusion_depth\"] = lift[\"extrusion_depth\"]",
            "        if lift.get(\"depth_map_path\"):",
            "            obj[\"depth_map_path\"] = lift[\"depth_map_path\"]",
            "        if lift.get(\"normal_map_path\"):",
            "            obj[\"normal_map_path\"] = lift[\"normal_map_path\"]",
            "        obj[\"lift_mode\"] = lift.get(\"lift_mode\", \"depth_card\")",
            "        report[\"created_objects\"].append(lift[\"asset_id\"])",
            "",
            "    report[\"mode\"] = \"bpy\"",
            "    return report",
            "",
            "",
            "if __name__ == \"__main__\":",
            "    import argparse",
            "",
            "    parser = argparse.ArgumentParser(description=\"Ingest a drIpTECH Blender conversion bundle\")",
            "    parser.add_argument(\"bundle\", type=Path)",
            "    args = parser.parse_args()",
            "    print(json.dumps(build_scene(args.bundle), indent=2))",
        ]
    )


def build_clipstudio_bundle(project: dict, out_dir: Path) -> Path:
    ensure_dir(out_dir)
    clip = project["authoring"]["clipstudio"]
    assets = flatten_assets(project)
    payload = {
        "project_name": project["project_name"],
        "seed": project["seed"],
        "translation_profile": project.get("translation_profile", {}),
        "canvas": clip["canvas"],
        "export_profile": clip.get("export_profile", {"color_mode": "rgba", "naming": "asset_id"}),
        "assets": assets,
        "depth_cards": clip.get("depth_cards", []),
        "layers": clip.get("layers", []),
        "scenes": project["gameplay"]["scenes"],
        "script_symbols": clip.get("script_symbols", []),
        "symbol_bindings": clip.get("symbol_bindings", []),
        "frame_tags": clip.get("frame_tags", []),
        "hitboxes": clip.get("hitboxes", []),
        "script_bindings": clip.get("script_bindings", []),
        "export_notes": [
            "Author 2D art, timeline triggers, and visual-script bindings in Clip Studio Paint.",
            "Each asset path is treated as a source-of-truth authoring reference.",
            "Gameplay symbols should match downstream Blender and idTech2 entity IDs where possible."
        ]
    }
    target = out_dir / "clipstudio_export.json"
    write_json(target, payload)

    runtime_manifest = out_dir / "clipstudio_runtime_manifest.json"
    write_json(
        runtime_manifest,
        {
            "project_name": project["project_name"],
            "timeline_fps": clip.get("timeline_fps", 12),
            "symbol_bindings": clip.get("symbol_bindings", []),
            "script_bindings": clip.get("script_bindings", []),
            "scene_events": [scene.get("triggers", []) for scene in project["gameplay"]["scenes"]],
            "hitboxes": clip.get("hitboxes", []),
        },
    )
    return target


def build_blender_bundle(project: dict, clipstudio_bundle: Path, out_dir: Path) -> Path:
    ensure_dir(out_dir)
    blender = project["authoring"]["blender"]
    lift_plan = []
    for sprite in project["assets"]["sprites"]:
        lift_plan.append(
            {
                "asset_id": sprite["id"],
                "source_path": sprite["path"],
                "frames": sprite.get("frames", 1),
                "usage": sprite.get("usage", "generic"),
                "extrusion_depth": blender.get("extrusion_depth", 0.08),
                "depth_map_path": sprite.get("depth_map"),
                "normal_map_path": sprite.get("normal_map"),
                "lift_mode": sprite.get("lift_mode", blender.get("lift_mode", "depth_card")),
                "rig_profile": blender.get("rig_profile", "paperdoll_humanoid"),
                "material_profile": sprite.get("material_profile", "default_sprite_material"),
                "collider": sprite.get("collider", {"shape": "capsule"}),
            }
        )
    world_plan = {
        "seed": project["seed"],
        "tilesets": project["assets"]["tilesets"],
        "scenes": project["gameplay"]["scenes"],
        "entities": project["gameplay"]["entities"],
        "nodecraft_enabled": True,
        "scale": blender.get("scale", 0.1),
        "clipstudio_bundle": str(clipstudio_bundle),
        "scene_build": blender.get("scene_build", []),
    }
    payload = {
        "project_name": project["project_name"],
        "translation_profile": project.get("translation_profile", {}),
        "lift_plan": lift_plan,
        "world_plan": world_plan,
        "animation_plan": [
            {
                "asset_id": sprite["id"],
                "frame_count": sprite.get("frames", 1),
                "fps": project["authoring"]["clipstudio"].get("timeline_fps", 12),
            }
            for sprite in project["assets"]["sprites"]
        ],
        "material_profiles": blender.get("material_profiles", []),
        "rig_plan": blender.get("rig_overrides", []),
        "nodecraft_graphs": blender.get("nodecraft_graphs", []),
    }
    target = out_dir / "blender_conversion.json"
    write_json(target, payload)

    ingest_script = out_dir / "blender_ingest.py"
    ingest_script.write_text(generate_blender_ingest_script(project), encoding="utf-8")
    return target


def generate_idtech2_header(project: dict) -> str:
    guards = f"{project['project_name'].upper()}_PIPELINE_AUTOGEN_H".replace("-", "_")
    prefix = project["authoring"]["idtech2"]["autofactor_prefix"]
    systems = normalize_systems(project)
    declared_functions = []
    lines = [
        f"#ifndef {guards}",
        f"#define {guards}",
        "",
        "typedef struct DriptechPipelineAsset {",
        "    const char *id;",
        "    const char *path;",
        "    const char *type;",
        "    const char *usage;",
        "} DriptechPipelineAsset;",
        "",
        "typedef struct DriptechPipelinePrecache {",
        "    const char *alias;",
        "    const char *path;",
        "    const char *type;",
        "} DriptechPipelinePrecache;",
        "",
        "typedef void (*DriptechPipelineSystemFn)(void);",
        "",
        "typedef struct DriptechPipelineDispatch {",
        "    const char *system_name;",
        "    DriptechPipelineSystemFn init_fn;",
        "    DriptechPipelineSystemFn tick_fn;",
        "} DriptechPipelineDispatch;",
        "",
        "typedef struct DriptechPipelineSpawn {",
        "    const char *id;",
        "    const char *classname;",
        "    const char *asset_id;",
        "    int x;",
        "    int y;",
        "    int z;",
        "} DriptechPipelineSpawn;",
        "",
    ]
    for system in systems:
        for function_name in (system["init_fn"], system["tick_fn"]):
            if function_name not in declared_functions:
                declared_functions.append(function_name)
                lines.append(f"void {function_name}(void);")
    if declared_functions:
        lines.append("")
    lines.extend(
        [
            f"extern const DriptechPipelineAsset {prefix}_assets[];",
            f"extern const int {prefix}_asset_count;",
            f"extern const DriptechPipelinePrecache {prefix}_precache[];",
            f"extern const int {prefix}_precache_count;",
            f"extern const char *{prefix}_systems[];",
            f"extern const int {prefix}_system_count;",
            f"extern const DriptechPipelineDispatch {prefix}_dispatch[];",
            f"extern const int {prefix}_dispatch_count;",
            f"extern const DriptechPipelineSpawn {prefix}_spawns[];",
            f"extern const int {prefix}_spawn_count;",
            "",
            f"void {prefix}_register_precache(void (*callback)(const char *alias, const char *path, const char *type));",
            f"void {prefix}_register_spawns(void (*callback)(const DriptechPipelineSpawn *spawn));",
            f"const DriptechPipelineDispatch *{prefix}_find_dispatch(const char *system_name);",
            "",
            "#endif",
            "",
        ]
    )
    return "\n".join(lines)


def generate_idtech2_source(project: dict) -> str:
    prefix = project["authoring"]["idtech2"]["autofactor_prefix"]
    systems = normalize_systems(project)
    entities = project["gameplay"]["entities"]
    assets = flatten_assets(project)
    precache = collect_precache_entries(project)
    lines = [
        '#include "g_driptech_pipeline_autogen.h"',
        "",
        "#include <stddef.h>",
        "#include <string.h>",
        "",
        f"const DriptechPipelineAsset {prefix}_assets[] = {{",
    ]
    for asset in assets:
        lines.append(
            "    {"
            f' "{asset["id"]}", "{asset["path"]}", "{asset["asset_type"]}", "{asset.get("usage", asset["asset_type"])}" '
            "},"
        )
    lines.extend(
        [
            "};",
            f"const int {prefix}_asset_count = {len(assets)};",
            "",
            f"const DriptechPipelinePrecache {prefix}_precache[] = {{",
        ]
    )
    for entry in precache:
        lines.append(
            "    {"
            f' "{entry["alias"]}", "{entry["path"]}", "{entry["asset_type"]}" '
            "},"
        )
    lines.extend(
        [
            "};",
            f"const int {prefix}_precache_count = {len(precache)};",
            "",
            f"const char *{prefix}_systems[] = {{",
        ]
    )
    for system in systems:
        lines.append(f'    "{system["name"]}",')
    lines.extend(
        [
            "};",
            f"const int {prefix}_system_count = {len(systems)};",
            "",
            f"const DriptechPipelineDispatch {prefix}_dispatch[] = {{",
        ]
    )
    for system in systems:
        lines.append(
            "    {"
            f' "{system["name"]}", {system["init_fn"]}, {system["tick_fn"]} '
            "},"
        )
    lines.extend(
        [
            "};",
            f"const int {prefix}_dispatch_count = {len(systems)};",
            "",
            f"const DriptechPipelineSpawn {prefix}_spawns[] = {{",
        ]
    )
    for entity in entities:
        spawn = entity.get("spawn", [0, 0, 0])
        lines.append(
            "    {"
            f' "{entity["id"]}", "{entity["classname"]}", "{entity.get("asset_id", entity.get("classname", ""))}", {spawn[0]}, {spawn[1]}, {spawn[2]} '
            "},"
        )
    lines.extend(
        [
            "};",
            f"const int {prefix}_spawn_count = {len(entities)};",
            "",
            f"void {prefix}_register_precache(void (*callback)(const char *alias, const char *path, const char *type)) {{",
            "    int i;",
            "    if (!callback) return;",
            f"    for (i = 0; i < {prefix}_precache_count; ++i) {{",
            f"        callback({prefix}_precache[i].alias, {prefix}_precache[i].path, {prefix}_precache[i].type);",
            "    }",
            "}",
            "",
            f"void {prefix}_register_spawns(void (*callback)(const DriptechPipelineSpawn *spawn)) {{",
            "    int i;",
            "    if (!callback) return;",
            f"    for (i = 0; i < {prefix}_spawn_count; ++i) {{",
            f"        callback(&{prefix}_spawns[i]);",
            "    }",
            "}",
            "",
            f"const DriptechPipelineDispatch *{prefix}_find_dispatch(const char *system_name) {{",
            "    int i;",
            "    if (!system_name) return NULL;",
            f"    for (i = 0; i < {prefix}_dispatch_count; ++i) {{",
            f"        if (strcmp({prefix}_dispatch[i].system_name, system_name) == 0) {{",
            f"            return &{prefix}_dispatch[i];",
            "        }",
            "    }",
            "    return NULL;",
            "}",
            "",
        ]
    )
    return "\n".join(lines)


def build_idtech2_bundle(project: dict, blender_bundle: Path, out_dir: Path) -> Path:
    ensure_dir(out_dir)
    idtech2 = project["authoring"]["idtech2"]
    systems = normalize_systems(project)
    precache = collect_precache_entries(project)
    assets = flatten_assets(project)
    payload = {
        "project_name": project["project_name"],
        "translation_profile": project.get("translation_profile", {}),
        "module_name": idtech2["module_name"],
        "asset_root": idtech2["asset_root"],
        "assets": assets,
        "precache": precache,
        "systems": systems,
        "entities": project["gameplay"]["entities"],
        "source_blender_bundle": str(blender_bundle),
        "autofactor_prefix": idtech2["autofactor_prefix"],
        "bootstrap": idtech2.get("bootstrap", {}),
    }
    manifest_path = out_dir / "idtech2_manifest.json"
    write_json(manifest_path, payload)

    header_path = out_dir / "g_driptech_pipeline_autogen.h"
    source_path = out_dir / "g_driptech_pipeline_autogen.c"
    header_path.write_text(generate_idtech2_header(project), encoding="utf-8")
    source_path.write_text(generate_idtech2_source(project), encoding="utf-8")
    return manifest_path


def build(project_path: Path, out_root: Path) -> None:
    project = load_project(project_path)
    clip_dir = out_root / project["targets"]["clipstudio_bundle"]
    blender_dir = out_root / project["targets"]["blender_bundle"]
    id_dir = out_root / project["targets"]["idtech2_bundle"]

    clip_bundle = build_clipstudio_bundle(project, clip_dir)
    blender_bundle = build_blender_bundle(project, clip_bundle, blender_dir)
    id_bundle = build_idtech2_bundle(project, blender_bundle, id_dir)

    summary = {
        "project": project["project_name"],
        "clipstudio_bundle": str(clip_bundle),
        "blender_bundle": str(blender_bundle),
        "idtech2_bundle": str(id_bundle),
    }
    print(json.dumps(summary, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="drIpTECH cross-tool game pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    build_parser = sub.add_parser("build", help="Build all pipeline bundles from a project manifest")
    build_parser.add_argument("--project", required=True, type=Path)
    build_parser.add_argument("--out", required=True, type=Path)

    args = parser.parse_args()
    if args.command == "build":
        build(args.project, args.out)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())