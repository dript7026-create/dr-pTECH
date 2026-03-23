from __future__ import annotations

import json
from pathlib import Path


def _write_json(path: Path, payload: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return str(path)


def write_blendnow_txtur_bundle(output_dir: str | Path, config: dict) -> dict:
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    sheet = config["sheet"]
    rig = config["rig"]
    project_name = config["nomenclature"]["project"]
    visual_analysis = sheet.get("visual_analysis", {})
    reconstruction_contract = sheet.get("reconstruction_contract", {})
    clipstudio_contract = config.get("clipstudio", {})
    conversion_plan = {
        "project_name": project_name,
        "toolchain": {"trial": "TxTUR", "vip": "BlendNow"},
        "lift_plan": [
            {
                "asset_id": config["nomenclature"]["subject"],
                "source_path": sheet.get("polished_atlas_path", sheet["atlas_path"]),
                "extrusion_depth": 0.14,
                "frame_count": len(sheet["frames"]),
                "vision_summary": visual_analysis.get("polished_atlas", {}),
                "dense_mesh_obj": reconstruction_contract.get("dense_mesh_obj"),
                "polygon_target": 10000,
                "depth_layer_count": 140,
            }
        ],
        "scene_plan": [
            {"scene_id": "bango_showcase", "location": "blendnow_stage", "first_frame": 1, "last_frame": 360}
        ],
        "reconstruction_contract": reconstruction_contract,
    }
    import_spec = {
        "project_name": project_name,
        "toolchain": {"trial": "TxTUR", "vip": "BlendNow"},
        "materials": [
            {
                "name": "bango_sheet_polish",
                "shader": "txtur_projection_bsdf",
                "roughness": 0.68,
                "normal_strength": 0.32,
                "bump_map": reconstruction_contract.get("bump_map"),
                "fiber_map": reconstruction_contract.get("fiber_map"),
                "elasticity_map": reconstruction_contract.get("elasticity_map"),
            }
        ],
        "rig_plan": [
            {
                "asset_id": config["nomenclature"]["subject"],
                "armature": rig["name"],
                "root_bone": rig["bones"][0]["name"],
            }
        ],
        "mesh_wiring": {
            "rig_name": rig["name"],
            "bone_count": len(rig.get("bones", [])),
            "rig_mapping": reconstruction_contract.get("rig_mapping"),
            "mesh_contract": reconstruction_contract.get("mesh_contract"),
            "high_poly_contract": reconstruction_contract.get("high_poly_contract"),
            "dense_mesh_obj": reconstruction_contract.get("dense_mesh_obj"),
            "weighting_strategy": "reconstruction_guided_envelope_then_rig_binding",
        },
        "texture_mapping": {
            "primary_atlas": sheet.get("polished_atlas_path", sheet.get("atlas_path")),
            "surface_contract": reconstruction_contract.get("surface_contract"),
            "depth_map": reconstruction_contract.get("depth_map"),
            "normal_map": reconstruction_contract.get("normal_map"),
            "bump_map": reconstruction_contract.get("bump_map"),
            "fiber_map": reconstruction_contract.get("fiber_map"),
            "elasticity_map": reconstruction_contract.get("elasticity_map"),
            "volume_layers": reconstruction_contract.get("volume_layers"),
            "source_brush_suite": clipstudio_contract.get("brush_suite", {}),
            "polish_stage": sheet.get("polish_payload", {}),
            "uv_policy": "derive stable UV islands from reconstruction sections and preserve readable material boundaries",
        },
        "nodecraft": {
            "nodes": [
                {"id": "bango_root", "position": [0.0, 0.0, 0.0], "scale": 1.0},
                {"id": "stage_anchor", "position": [0.0, -2.4, 0.0], "scale": 2.0},
            ],
            "links": [
                {"from": "bango_root", "to": "stage_anchor", "type": "presentation", "thickness": 0.12}
            ],
        },
        "vision_contract": {
            "mode": "readAIpolish_graphical_visual_read",
            "source_summary": visual_analysis.get("source_sheet", {}),
            "atlas_summary": visual_analysis.get("polished_atlas", {}),
        },
    }
    modeling_contract = {
        "project_name": project_name,
        "asset_id": config["nomenclature"]["subject"],
        "mesh_contract": reconstruction_contract.get("mesh_contract"),
        "high_poly_contract": reconstruction_contract.get("high_poly_contract"),
        "dense_mesh_obj": reconstruction_contract.get("dense_mesh_obj"),
        "rig_mapping": reconstruction_contract.get("rig_mapping"),
        "keypose_intake": reconstruction_contract.get("keypose_intake"),
        "modeling_rule": "BlendNOW uses reconstruction-derived sections as the baseline for blockout, retopo planning, rig envelope ownership, and later runtime proxy mesh generation.",
    }
    texture_contract = {
        "project_name": project_name,
        "asset_id": config["nomenclature"]["subject"],
        "surface_contract": reconstruction_contract.get("surface_contract"),
        "primary_atlas": sheet.get("polished_atlas_path", sheet.get("atlas_path")),
        "depth_map": reconstruction_contract.get("depth_map"),
        "normal_map": reconstruction_contract.get("normal_map"),
        "bump_map": reconstruction_contract.get("bump_map"),
        "fiber_map": reconstruction_contract.get("fiber_map"),
        "elasticity_map": reconstruction_contract.get("elasticity_map"),
        "volume_layers": reconstruction_contract.get("volume_layers"),
        "visual_intelligence": visual_analysis.get("polished_atlas", {}),
        "brush_suite": clipstudio_contract.get("brush_suite", {}),
        "mapping_rule": "BlendNOW texture mapping must preserve Clip Studio-authored silhouette and readAIpolish-separated material readability before engine export.",
    }
    animation_contract = {
        "project_name": project_name,
        "asset_id": config["nomenclature"]["subject"],
        "pose_registry": clipstudio_contract.get("pose_registry"),
        "pose_entries": clipstudio_contract.get("pose_entries", []),
        "timeline_scripting": clipstudio_contract.get("timeline_scripting", {}),
        "runtime_inbetween_constraints": reconstruction_contract.get("runtime_inbetween_constraints"),
        "physics_defaults": clipstudio_contract.get("physics_inbetween_defaults", {}),
        "animation_rule": "Clip Studio keyframes and script metadata remain authored upstream, BlendNOW packages them, and the runtime applies only bounded physics-guided inbetweening for secondary motion and settling.",
    }
    engine_integration = {
        "project_name": project_name,
        "asset_id": config["nomenclature"]["subject"],
        "delivery_targets": clipstudio_contract.get("delivery_targets", []),
        "playnow_role": "authoring_to_runtime_handoff",
        "runtime_targets": ["DoENGINE", "PlayNOW", "DODOplayNOW", "ORBEngine", "IllusionCanvas", "idLoadINT"],
        "integration_rule": "BlendNOW exports both graphical assets and authoring-side script or physics contracts so the two tutorial slices and later full-game runtime consume one coherent bundle.",
    }
    visual_intelligence = {
        "project_name": project_name,
        "toolchain": {"trial": "TxTUR", "vip": "BlendNow", "visual_reader": "readAIpolish"},
        "asset_id": config["nomenclature"]["subject"],
        "source_sheet": visual_analysis.get("source_sheet"),
        "keyed_atlas": visual_analysis.get("keyed_atlas"),
        "polished_atlas": visual_analysis.get("polished_atlas"),
        "frames": visual_analysis.get("frames", []),
        "interpretation": {
            "goal": "Provide machine-readable graphical understanding to support BlendNOW scene lift and downstream PlayNOW runtime staging.",
            "readable_frame_count": len(visual_analysis.get("frames", [])),
            "dominant_frame": max(
                visual_analysis.get("frames", []),
                key=lambda frame: frame.get("analysis", {}).get("alpha_coverage", 0.0),
                default=None,
            ),
        },
    }
    conversion_path = output_root / "BlendNow_TxTUR_conversion_plan.json"
    import_path = output_root / "BlendNow_TxTUR_import_spec.json"
    visual_path = output_root / "BlendNow_TxTUR_visual_intelligence.json"
    modeling_path = output_root / "BlendNow_TxTUR_modeling_contract.json"
    texture_path = output_root / "BlendNow_TxTUR_texture_mapping_contract.json"
    animation_path = output_root / "BlendNow_TxTUR_animation_contract.json"
    engine_path = output_root / "BlendNow_TxTUR_engine_integration.json"
    return {
        "conversion_plan": _write_json(conversion_path, conversion_plan),
        "import_spec": _write_json(import_path, import_spec),
        "visual_intelligence": _write_json(visual_path, visual_intelligence),
        "modeling_contract": _write_json(modeling_path, modeling_contract),
        "texture_mapping_contract": _write_json(texture_path, texture_contract),
        "animation_contract": _write_json(animation_path, animation_contract),
        "engine_integration": _write_json(engine_path, engine_integration),
    }
