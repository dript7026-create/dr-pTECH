from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import argparse
from collections import deque
from pathlib import Path

from PIL import Image


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from tools.DropLoop import DropLoopController, DropLoopMetrics, DropLoopPolicy


ROOT = Path(__file__).resolve().parent.parent
ASSET_ROOT = Path(os.environ.get("BANGO_ASSET_ROOT", str(ROOT))).expanduser()
PLUGIN_ROOT = ROOT.parent / "drIpTECHBlenderPlug-Ins" / "TxTUR"
CLIPSTUDIO_PLUGIN_ROOT = WORKSPACE_ROOT / "drIpTech_ClipStudio_Plug-Ins"
SOURCE_SHEET = ROOT / "assets" / "charactersheets" / "bangopatoot_asset_graphical_charactersheet_bango_fouranglestpose_0001.png"
RIG_JSON = ROOT / "rigs" / "entity_rigs.json"
BLENDER_SCRIPT = PLUGIN_ROOT / "bango_sheet_autorig_blender.py"
OUTPUT_DIR = ASSET_ROOT / "generated" / "blender_bango_autorig"
IDLOADINT_OUTPUT_DIR = ASSET_ROOT / "generated" / "idLoadINT_bundle"
BLENDER_EXE = Path(r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe")
FRAME_LABELS = ["front", "left", "right", "rear"]
POSE_REGISTRY = ROOT / "pose_imports" / "imported_pose_registry.json"


def _import_local_module(module_path: Path, name: str):
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not import {name} from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


READAIPOLISH = _import_local_module(WORKSPACE_ROOT / "readAIpolish" / "graphics_polish_ai.py", "readaipolish_graphics_polish_ai")
BLENDNOW_CORE = _import_local_module(PLUGIN_ROOT / "BlendNow_core.py", "blendnow_core")
IDLOADINT_BUILDER = _import_local_module(ROOT / "tools" / "build_idLoadINT_bundle.py", "build_idloadint_bundle")
ASSET_RECONSTRUCTION = _import_local_module(ROOT / "tools" / "analyze_asset_reconstruction.py", "analyze_asset_reconstruction")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def resolve_source_sheet(source_sheet: str | None) -> Path:
    explicit_path = source_sheet or os.environ.get("BANGO_SOURCE_SHEET")
    candidate = Path(explicit_path).expanduser() if explicit_path else SOURCE_SHEET
    if not candidate.exists():
        raise FileNotFoundError(f"Source sheet not found at {candidate}")
    return candidate


def parse_nomenclature(path: Path) -> dict:
    tokens = path.stem.split("_")
    if len(tokens) < 7:
        raise ValueError(f"Unexpected asset naming shape: {path.name}")
    return {
        "filename": path.name,
        "project": tokens[0],
        "scope": tokens[1],
        "medium": tokens[2],
        "artifact_type": tokens[3],
        "subject": tokens[4],
        "variant": "_".join(tokens[5:-1]),
        "revision": tokens[-1],
        "protocol": "[project]_[scope]_[medium]_[artifact_type]_[subject]_[variant]_[revision].[ext]",
    }


def color_distance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    return math.sqrt(sum((float(a[i]) - float(b[i])) ** 2 for i in range(3)))


def key_out_background(frame: Image.Image, tolerance: float = 24.0) -> Image.Image:
    rgba = frame.convert("RGBA")
    width, height = rgba.size
    pixels = rgba.load()
    background_samples = [pixels[0, 0], pixels[width - 1, 0], pixels[0, height - 1], pixels[width - 1, height - 1]]
    background = tuple(int(sum(sample[i] for sample in background_samples) / len(background_samples)) for i in range(4))
    visited = set()
    queue = deque([(0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)])

    while queue:
        x, y = queue.popleft()
        if (x, y) in visited or not (0 <= x < width and 0 <= y < height):
            continue
        visited.add((x, y))
        pixel = pixels[x, y]
        if color_distance(pixel, background) > tolerance:
            continue
        pixels[x, y] = (pixel[0], pixel[1], pixel[2], 0)
        queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return rgba


def frame_bbox(frame: Image.Image) -> tuple[int, int, int, int] | None:
    return frame.getchannel("A").getbbox()


def build_row_profile(frame: Image.Image) -> dict:
    alpha = frame.getchannel("A")
    width, height = frame.size
    rows = []
    for y in range(height):
        xs = [x for x in range(width) if alpha.getpixel((x, y)) > 0]
        if xs:
            rows.append({"y": y, "min_x": min(xs), "max_x": max(xs), "width": max(xs) - min(xs) + 1})
        else:
            rows.append({"y": y, "min_x": None, "max_x": None, "width": 0})
    return {"height": height, "width": width, "rows": rows}


def prepare_sheet_inputs(source_sheet: Path) -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frames_dir = OUTPUT_DIR / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    image = Image.open(source_sheet).convert("RGBA")
    sheet_width, sheet_height = image.size
    frame_width = sheet_width // 4
    prepared_frames = []
    atlas = Image.new("RGBA", image.size, (0, 0, 0, 0))

    for index, label in enumerate(FRAME_LABELS):
        frame = image.crop((index * frame_width, 0, (index + 1) * frame_width, sheet_height))
        keyed = key_out_background(frame)
        atlas.alpha_composite(keyed, (index * frame_width, 0))
        frame_path = frames_dir / f"bangopatoot_asset_graphical_charactersheet_bango_{label}_0001.png"
        keyed.save(frame_path)
        prepared_frames.append({
            "label": label,
            "path": str(frame_path),
            "bbox": frame_bbox(keyed),
            "profile": build_row_profile(keyed),
            "size": [keyed.width, keyed.height],
        })

    atlas_path = OUTPUT_DIR / "bangopatoot_asset_graphical_charactersheet_bango_fouranglestpose_keyed_0001.png"
    atlas.save(atlas_path)
    polished_payload = READAIPOLISH.polish_asset_path(atlas_path)
    visual_analysis = {
        "source_sheet": READAIPOLISH.analyze_visual_asset_path(source_sheet),
        "keyed_atlas": READAIPOLISH.analyze_visual_asset_path(atlas_path),
        "polished_atlas": READAIPOLISH.analyze_visual_asset_path(polished_payload["target"]),
        "frames": [
            {
                "label": frame["label"],
                "path": frame["path"],
                "analysis": READAIPOLISH.analyze_visual_asset_path(frame["path"]),
            }
            for frame in prepared_frames
        ],
    }
    reconstruction_dir = OUTPUT_DIR / "reconstruction" / "bango_sheet"
    rig_lookup = ASSET_RECONSTRUCTION.build_rig_lookup(load_json(RIG_JSON))
    ASSET_RECONSTRUCTION.analyze(
        Path(polished_payload["target"]),
        "bango_sheet_polished_atlas",
        "player",
        "Bango",
        reconstruction_dir,
        rig_lookup,
    )
    reconstruction_contract = {
        "output_dir": str(reconstruction_dir),
        "mesh_contract": str(reconstruction_dir / "mesh_contract.json"),
        "high_poly_contract": str(reconstruction_dir / "high_poly_contract.json"),
        "dense_mesh_obj": str(reconstruction_dir / "dense_shell_10000.obj"),
        "surface_contract": str(reconstruction_dir / "surface_contract.json"),
        "rig_mapping": str(reconstruction_dir / "rig_mapping.json"),
        "keypose_intake": str(reconstruction_dir / "keypose_intake.json"),
        "runtime_inbetween_constraints": str(reconstruction_dir / "runtime_inbetween_constraints.json"),
        "depth_map": str(reconstruction_dir / "depth_map.png"),
        "normal_map": str(reconstruction_dir / "normal_map.png"),
        "bump_map": str(reconstruction_dir / "bump_map.png"),
        "fiber_map": str(reconstruction_dir / "fiber_map.png"),
        "elasticity_map": str(reconstruction_dir / "elasticity_map.png"),
        "curvature_map": str(reconstruction_dir / "curvature_map.png"),
        "volume_layers": str(reconstruction_dir / "volume_layers_140.json"),
        "volume_layers_preview": str(reconstruction_dir / "volume_layers_140_preview.png"),
        "region_preview": str(reconstruction_dir / "region_map_preview.png"),
    }
    return {
        "sheet_path": str(source_sheet),
        "atlas_path": str(atlas_path),
        "polished_atlas_path": polished_payload["target"],
        "polish_payload": polished_payload,
        "visual_analysis": visual_analysis,
        "reconstruction_contract": reconstruction_contract,
        "sheet_size": [sheet_width, sheet_height],
        "frame_width": frame_width,
        "frames": prepared_frames,
    }


def build_3ddpg_genome(nomenclature: dict, sheet: dict, rig: dict, clipstudio_contract: dict) -> dict:
    source_summary = sheet.get("visual_analysis", {}).get("source_sheet", {}).get("analysis", {})
    polished_summary = sheet.get("visual_analysis", {}).get("polished_atlas", {}).get("analysis", {})
    reconstruction_contract = sheet.get("reconstruction_contract", {})
    return {
        "format": "3DDPG",
        "version": "2026-03-14.autocreate",
        "title": "3D Design Profile Genome",
        "nomenclature": nomenclature,
        "genetic_intent": {
            "source_modality": "four-angle raster character sheet",
            "subject": nomenclature.get("subject"),
            "variant": nomenclature.get("variant"),
            "automation_goal": "Translate 2D character-sheet semantics into a Blender-ready mesh, rig, texture, and export profile.",
        },
        "genotype": {
            "frame_order": FRAME_LABELS,
            "sheet_dimensions": sheet.get("sheet_size"),
            "frame_width": sheet.get("frame_width"),
            "silhouette_balance_score": polished_summary.get("silhouette_balance_score"),
            "readable_fill_ratio": polished_summary.get("readable_fill_ratio"),
            "dominant_palette": polished_summary.get("dominant_palette"),
            "rig_identity": {
                "name": rig.get("name"),
                "bone_count": len(rig.get("bones", [])),
                "root_bone": rig.get("bones", [{}])[0].get("name"),
            },
        },
        "phenotype_targets": {
            "mesh_profile": {
                "strategy": "reconstruction-guided autoblockout",
                "mesh_contract": reconstruction_contract.get("mesh_contract"),
                "rig_mapping": reconstruction_contract.get("rig_mapping"),
                "keypose_intake": reconstruction_contract.get("keypose_intake"),
            },
            "texture_profile": {
                "primary_atlas": sheet.get("polished_atlas_path"),
                "surface_contract": reconstruction_contract.get("surface_contract"),
                "source_luminance": source_summary.get("mean_luminance"),
                "polished_luminance": polished_summary.get("mean_luminance"),
            },
            "animation_profile": {
                "pose_registry": clipstudio_contract.get("pose_registry"),
                "physics_defaults": clipstudio_contract.get("physics_inbetween_defaults"),
                "runtime_inbetween_constraints": reconstruction_contract.get("runtime_inbetween_constraints"),
            },
        },
        "automation_expression": {
            "unfolding_stages": [
                "graphical_visual_read",
                "background_keying",
                "per-frame row-profile extraction",
                "reconstruction contract derivation",
                "BlendNow conversion-plan export",
                "Blender autorig autoblockout",
                "glb and blend delivery",
            ],
            "ingestion_contract": {
                "blender_script": str(BLENDER_SCRIPT),
                "blendnow_bundle_dir": str(OUTPUT_DIR),
                "delivery_targets": clipstudio_contract.get("delivery_targets", []),
            },
        },
    }


def build_clipstudio_contract() -> dict:
    pose_entries = []
    if POSE_REGISTRY.exists():
        registry = load_json(POSE_REGISTRY)
        if isinstance(registry, list):
            pose_entries = [entry for entry in registry if str(entry.get("entity", "")).lower() == "bango"]
    return {
        "plugin_root": str(CLIPSTUDIO_PLUGIN_ROOT),
        "feature_summary": str(CLIPSTUDIO_PLUGIN_ROOT / "ClipStudioPaint_Plugin_Feature_Summary.txt"),
        "brush_suite": {
            "implementation": str(CLIPSTUDIO_PLUGIN_ROOT / "ClipStudioPixelBrushSuite.c"),
            "header": str(CLIPSTUDIO_PLUGIN_ROOT / "ClipStudioPixelBrushSuite.h"),
            "bridge_header": str(CLIPSTUDIO_PLUGIN_ROOT / "pipeline_bridge" / "ClipStudioPipelineBridge.h"),
        },
        "brush_features": [
            "standard_pixel_brush",
            "watercolor_brush",
            "oil_brush",
            "airbrush",
            "charcoal_pastel_brush",
            "feathered_brush",
            "translayer_gradation",
        ],
        "timeline_scripting": {
            "script_symbol_binding": ["tie_script_to_symbol", "tie_script_to_button", "tie_script_to_frame"],
            "keyframe_interpolation": "ai_inbetween_frames",
            "status": "prototype_host_bridge_with_runtime_contract",
        },
        "pose_registry": str(POSE_REGISTRY),
        "pose_entries": pose_entries,
        "physics_inbetween_defaults": {
            "method": "physics_hint",
            "stiffness": max((float(entry.get("inbetween", {}).get("stiffness", 0.0)) for entry in pose_entries), default=0.62),
            "damping": max((float(entry.get("inbetween", {}).get("damping", 0.0)) for entry in pose_entries), default=0.27),
            "overshoot": max((float(entry.get("inbetween", {}).get("overshoot", 0.0)) for entry in pose_entries), default=0.11),
            "gravity_bias": max((float(entry.get("inbetween", {}).get("gravity_bias", 0.0)) for entry in pose_entries), default=0.34),
        },
        "delivery_targets": ["tutorial_prototype", "tutorial_final_preview", "full_game_first_class_delivery"],
    }


def build_config(source_sheet: Path) -> Path:
    nomenclature = parse_nomenclature(source_sheet)
    sheet = prepare_sheet_inputs(source_sheet)
    rigs = load_json(RIG_JSON)
    bango_rig = next(skeleton for skeleton in rigs["skeletons"] if skeleton["entity"].lower() == "bango")
    clipstudio_contract = build_clipstudio_contract()
    blendnow_bundle = BLENDNOW_CORE.write_blendnow_txtur_bundle(OUTPUT_DIR, {"nomenclature": nomenclature, "sheet": sheet, "rig": bango_rig, "clipstudio": clipstudio_contract})
    genome_path = OUTPUT_DIR / "bangopatoot_asset_3dprofilegenome_bango_autocreate_0001.3ddpg"
    save_json(genome_path, build_3ddpg_genome(nomenclature, sheet, bango_rig, clipstudio_contract))
    config = {
        "nomenclature": nomenclature,
        "sheet": sheet,
        "rig": bango_rig,
        "clipstudio": clipstudio_contract,
        "3ddpg": {
            "path": str(genome_path),
            "format": "3DDPG",
            "role": "autocreate_ingestion_genome",
        },
        "toolchain": {
            "trial": {"sheet_lift": "TxTUR", "pipeline_addon": "DripCraft", "translator": "idTech2 integration"},
            "vip": {"sheet_lift": "BlendNow", "translator": "idLoadINT"},
            "clipstudio_bridge": "readAIpolish",
        },
        "outputs": {
            "blend": str(OUTPUT_DIR / "bangopatoot_asset_3dmodel_bango_riggedautoblockout_0001.blend"),
            "render": str(OUTPUT_DIR / "bangopatoot_asset_render_bango_riggedautoblockout_0001.png"),
            "glb": str(OUTPUT_DIR / "bangopatoot_asset_3dmodel_bango_riggedautoblockout_0001.glb"),
        },
        "blendnow": blendnow_bundle,
        "animation_plan": IDLOADINT_BUILDER.ANIMATION_NAMES,
        "notes": {
            "frame_order_assumption": FRAME_LABELS,
            "texture_mapping_mode": "dominant-normal atlas projection using front, left, right, and rear frames",
            "geometry_mode": "rig-driven automated blockout from character-sheet row profiles",
            "graphical_visual_read_stage": "readAIpolish visual analysis applied before BlendNow conversion-plan export",
            "integration_scope": "Clip Studio authored keyframes and script metadata feed BlendNOW, then PlayNOW, then the tutorial slices and later full-game runtime outputs.",
        },
    }
    config_path = OUTPUT_DIR / "bangopatoot_asset_3dmodel_bango_riggedautoblockout_0001.config.json"
    save_json(config_path, config)
    return config_path


def run_blender(config_path: Path) -> subprocess.CompletedProcess:
    if not BLENDER_EXE.exists():
        raise FileNotFoundError(f"Blender not found at {BLENDER_EXE}")
    if not BLENDER_SCRIPT.exists():
        raise FileNotFoundError(f"Blender automation script not found at {BLENDER_SCRIPT}")
    command = [str(BLENDER_EXE), "--background", "--python", str(BLENDER_SCRIPT), "--", str(config_path)]
    return subprocess.run(command, check=False, capture_output=True, text=True)


def summarize_result(result: subprocess.CompletedProcess | None, error: Exception | None) -> str:
    if error is not None:
        return f"exception: {error}"
    if result is None:
        return "no process result"
    return f"returncode={result.returncode}"


def build_metrics(attempt: int, result: subprocess.CompletedProcess | None, error: Exception | None) -> DropLoopMetrics:
    if error is not None:
        return DropLoopMetrics(
            decay_factor=min(1.0, 0.42 + attempt * 0.12),
            datastream_integrity=0.45,
            concurrency_load=0.28,
            electrical_stress=0.34,
            cycle_frequency_hz=max(0.5, 2.2 - attempt * 0.25),
        )
    stderr = (result.stderr if result is not None else "") or ""
    returncode = result.returncode if result is not None else 1
    has_warning = "warning" in stderr.lower()
    has_traceback = "traceback" in stderr.lower()
    return DropLoopMetrics(
        decay_factor=min(1.0, 0.10 * attempt + (0.18 if has_traceback else 0.0)),
        datastream_integrity=0.98 if returncode == 0 and not has_warning else 0.90 if returncode == 0 else 0.55,
        concurrency_load=0.14 + 0.05 * attempt,
        electrical_stress=0.12 + (0.12 if has_warning else 0.0) + (0.18 if returncode != 0 else 0.0),
        cycle_frequency_hz=max(0.5, 3.0 - attempt * 0.35),
    )


def repair_pipeline_state(
    attempt: int,
    decision,
    result: subprocess.CompletedProcess | None,
    error: Exception | None,
) -> None:
    repair_report = {
        "attempt": attempt,
        "repair_required": True,
        "offset_seconds": decision.offset_seconds,
        "risk_score": decision.risk_score,
        "stability_score": decision.stability_score,
        "rationale": decision.rationale,
        "result_summary": summarize_result(result, error),
    }
    save_json(OUTPUT_DIR / "cycle_repair_report.json", repair_report)


def run_blender_with_cycle_control(config_path: Path) -> tuple[subprocess.CompletedProcess | None, dict]:
    controller = DropLoopController[subprocess.CompletedProcess](
        DropLoopPolicy(max_attempts=3, base_offset_seconds=0.08, max_offset_seconds=0.55, repair_cooldown_scale=0.28)
    )
    result, report = controller.run(
        operation=lambda attempt: run_blender(config_path),
        metrics_provider=build_metrics,
        success_evaluator=lambda completed: completed.returncode == 0,
        repair_action=repair_pipeline_state,
        sleep_fn=lambda seconds: None,
        result_summarizer=summarize_result,
    )
    return result, report.to_dict()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate BlendNow autoblockout assets from a Bango character sheet.")
    parser.add_argument("--source-sheet", help="Optional override path to a four-angle Bango character sheet PNG.")
    args = parser.parse_args()

    source_sheet = resolve_source_sheet(args.source_sheet)
    config_path = build_config(source_sheet)
    result, cycle_report = run_blender_with_cycle_control(config_path)
    if result is None:
        raise RuntimeError("Blender did not produce a process result.")
    (OUTPUT_DIR / "blender_stdout.log").write_text(result.stdout, encoding="utf-8")
    (OUTPUT_DIR / "blender_stderr.log").write_text(result.stderr, encoding="utf-8")
    save_json(OUTPUT_DIR / "DropLoop_report.json", cycle_report)
    idloadint_bundle = IDLOADINT_BUILDER.build_idloadint_bundle(
        ROOT,
        IDLOADINT_OUTPUT_DIR,
        Path(OUTPUT_DIR / "bangopatoot_asset_3dmodel_bango_riggedautoblockout_0001.blend"),
        Path(OUTPUT_DIR / "bangopatoot_asset_3dmodel_bango_riggedautoblockout_0001.glb"),
    )
    print(json.dumps({
        "source_sheet": str(source_sheet),
        "3ddpg": str(OUTPUT_DIR / "bangopatoot_asset_3dprofilegenome_bango_autocreate_0001.3ddpg"),
        "config": str(config_path),
        "stdout_log": str(OUTPUT_DIR / "blender_stdout.log"),
        "stderr_log": str(OUTPUT_DIR / "blender_stderr.log"),
        "DropLoop_report": str(OUTPUT_DIR / "DropLoop_report.json"),
        "idLoadINT_manifest": idloadint_bundle["manifest"],
        "returncode": result.returncode,
    }, indent=2))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())