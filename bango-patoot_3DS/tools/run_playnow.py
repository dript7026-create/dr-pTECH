from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from bango_pipeline_paths import resolve_asset_root


ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = ROOT.parent
PLAYNOW_DIRNAME = "playnow"
DOENGINE_ROOT = WORKSPACE_ROOT / "DoENGINE"
SPEC_ROOT = ROOT / "specs"
PROTOTYPE_TUTORIAL_SPEC_PATH = SPEC_ROOT / "playnow_tutorial_prototype_spec.json"
FINAL_PREVIEW_TUTORIAL_SPEC_PATH = SPEC_ROOT / "playnow_tutorial_final_preview_spec.json"
TUTORIAL_CONTRACT_PATH = SPEC_ROOT / "playnow_tutorial_duology_contract.json"


def save_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def run_autorig(asset_root: Path) -> dict:
    command = [sys.executable, str(ROOT / "tools" / "run_bango_sheet_autorig.py")]
    env = os.environ.copy()
    env["BANGO_ASSET_ROOT"] = str(asset_root)
    result = subprocess.run(command, capture_output=True, text=True, check=False, env=env)
    return {
        "command": " ".join(command),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def read_json_if_exists(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_blendnow_bundle(asset_root: Path) -> dict:
    config_path = asset_root / "generated" / "blender_bango_autorig" / "bangopatoot_asset_3dmodel_bango_riggedautoblockout_0001.config.json"
    config_payload = read_json_if_exists(config_path)
    if not isinstance(config_payload, dict):
        return {"config": str(config_path), "exists": False}
    blendnow = config_payload.get("blendnow") if isinstance(config_payload.get("blendnow"), dict) else {}
    return {
        "config": str(config_path),
        "exists": True,
        "conversion_plan": blendnow.get("conversion_plan"),
        "import_spec": blendnow.get("import_spec"),
        "visual_intelligence": blendnow.get("visual_intelligence"),
        "modeling_contract": blendnow.get("modeling_contract"),
        "texture_mapping_contract": blendnow.get("texture_mapping_contract"),
        "animation_contract": blendnow.get("animation_contract"),
        "engine_integration": blendnow.get("engine_integration"),
        "clipstudio": config_payload.get("clipstudio"),
        "toolchain": config_payload.get("toolchain"),
        "notes": config_payload.get("notes"),
    }


def build_protocol_contract() -> dict:
    return {
        "name": "four_pronged_mathematical_perfect_expression",
        "status": "encoded_from_current_workspace_contract",
        "note": "The verbatim drip9 protocol text was not present in this workspace, so PlayNOW encodes the operative four-pronged contract as structured runtime data.",
        "prongs": [
            {
                "id": "prong_01_deterministic_manifest_intake",
                "label": "Deterministic Manifest Intake",
                "owner": "DoENGINE / DoNOW",
                "guarantee": "Generated content remains asset-root-aware, manifest-driven, and reproducible across staging and gameplay builds.",
            },
            {
                "id": "prong_02_layered_presentation_interop",
                "label": "Layered Presentation Interop",
                "owner": "IllusiViuNOW / ORBITNOW",
                "guarantee": "IllusionCanvas and ORBEngine-facing manifests remain synchronized with the same PlayNOW runtime handoff.",
            },
            {
                "id": "prong_03_full_proxy_gameplay_delivery",
                "label": "Full Proxy Gameplay Delivery",
                "owner": "BangoNOW / DODOplayNOW",
                "guarantee": "Player bundle, tutorial spec, combat content, and gameplay handoff remain wired into the final hybrid runtime.",
            },
            {
                "id": "prong_04_verified_windows_delivery",
                "label": "Verified Windows Delivery",
                "owner": "PlayNOW Finalstage",
                "guarantee": "Windows launch surface, engine launchers, manifests, and final package references remain staged as one delivery contract.",
            },
        ],
    }


def build_tutorial_library() -> dict:
    return {
        "prototype": str(PROTOTYPE_TUTORIAL_SPEC_PATH),
        "final_preview": str(FINAL_PREVIEW_TUTORIAL_SPEC_PATH),
        "prompt_contract": str(TUTORIAL_CONTRACT_PATH),
    }


def build_engine_handoffs(asset_root: Path, integration_entry: dict, runtime_manifest_path: Path, runtime_manifest: dict) -> dict:
    playnow_dir = asset_root / "generated" / PLAYNOW_DIRNAME
    clip_blend_id_dir = asset_root / "generated" / "clip_blend_id"
    idloadint_dir = asset_root / "generated" / "idLoadINT_bundle"
    protocol_contract = build_protocol_contract()
    expected_windows_preview = ROOT / "BangoPatootWindowsPreview.exe"

    handoff_payloads = {
        "doengine_backbone": {
            "system": "DoENGINE",
            "module": "DoNOW / PlayNOW Backbone",
            "asset_root": str(asset_root),
            "protocol_contract": protocol_contract,
            "donow_manifest": str(clip_blend_id_dir / "donow_runtime_manifest.json"),
            "playnow_runtime_manifest": str(runtime_manifest_path),
            "pipeline_report": integration_entry["pipeline_report"],
            "launcher": str(DOENGINE_ROOT / "DoENGINEStudio.cmd"),
            "load_bearing_surfaces": [
                "manifest-driven ingest",
                "deterministic preload groups",
                "controller-aware runtime review",
                "asset-root-aware generated outputs",
            ],
        },
        "illusionviunow": {
            "system": "IllusiViuNOW",
            "asset_root": str(asset_root),
            "protocol_contract": protocol_contract,
            "runtime_manifest": str(clip_blend_id_dir / "illusioncanvas_runtime_manifest.json"),
            "studio_session": str(clip_blend_id_dir / "illusioncanvas_studio_session.json"),
            "ui_skin": str(clip_blend_id_dir / "illusioncanvas_ui_skin.json"),
            "iig_bundle": str(clip_blend_id_dir / "aridfeihth_illusioncanvas_bundle.iig"),
            "runtime_launcher": str(WORKSPACE_ROOT / "IllusionCanvasInteractive" / "run_illusioncanvas.py"),
            "studio_launcher": str(WORKSPACE_ROOT / "IllusionCanvasInteractive" / "run_illusioncanvas_studio.py"),
        },
        "orbitnow": {
            "system": "ORBITNOW",
            "asset_root": str(asset_root),
            "protocol_contract": protocol_contract,
            "hybrid_runtime_profile": str(DOENGINE_ROOT / "generated" / "dodogame_hybrid_runtime.json"),
            "orbengine_docs": str(WORKSPACE_ROOT / "ORBEngine" / "ORBEngine_ARCHITECTURE.md"),
            "responsibilities": [
                "recursive pseudo-3D space graph",
                "layered composite presentation",
                "full-3D proxy bridge compatibility",
                "DODOGame-hosted gameplay runtime",
            ],
        },
        "dodoplaynow": {
            "system": "DODOplayNOW",
            "asset_root": str(asset_root),
            "protocol_contract": protocol_contract,
            "playnow_runtime_manifest": str(runtime_manifest_path),
            "playnow_pass_manifest": str(playnow_dir / "playnow_dodogame_integration.json"),
            "hybrid_runtime_profile": str(DOENGINE_ROOT / "generated" / "dodogame_hybrid_runtime.json"),
            "launcher": str(DOENGINE_ROOT / "DODOGame.cmd"),
            "tutorial_spec": str(idloadint_dir / "tutorial_demo_spec.json"),
            "enemy_spec": str(idloadint_dir / "nightmaresludgebio_orbs.json"),
            "tutorial_deliverables": integration_entry["tutorial_library"],
            "tutorial_prompt_contract": integration_entry["tutorial_prompt_contract"],
            "blendnow": integration_entry.get("blendnow_bundle"),
            "windows_preview": str(expected_windows_preview),
        },
    }

    finalstage_payload = {
        "system": "PlayNOW Finalstage",
        "asset_root": str(asset_root),
        "protocol_contract": protocol_contract,
        "pass_labels": [entry.get("pass_label") for entry in runtime_manifest.get("passes", [])],
        "engine_manifests": {
            "doengine_backbone": str(playnow_dir / "playnow_doengine_backbone.json"),
            "illusionviunow": str(playnow_dir / "illusionviunow_runtime.json"),
            "orbitnow": str(playnow_dir / "orbitnow_runtime.json"),
            "dodoplaynow": str(playnow_dir / "dodoplaynow_runtime.json"),
        },
        "windows_delivery": {
            "bango_preview_exe": str(expected_windows_preview),
            "dodogame_launcher": str(DOENGINE_ROOT / "DODOGame.cmd"),
            "doengine_studio_launcher": str(DOENGINE_ROOT / "DoENGINEStudio.cmd"),
        },
        "gameplay_contract": {
            "player_blend": integration_entry["player_blend"],
            "player_glb": integration_entry["player_glb"],
            "tutorial_manifest": integration_entry["tutorial_manifest"],
            "tutorial_spec": integration_entry["tutorial_spec"],
            "runtime_tutorial_spec": integration_entry["runtime_tutorial_spec"],
            "enemy_spec": integration_entry["enemy_spec"],
            "tutorial_deliverables": integration_entry["tutorial_library"],
            "tutorial_prompt_contract": integration_entry["tutorial_prompt_contract"],
            "asset_budget": integration_entry.get("asset_budget"),
            "asset_traceability": integration_entry.get("asset_traceability"),
            "blendnow": integration_entry.get("blendnow_bundle"),
        },
    }

    payload_paths = {
        "doengine_backbone": playnow_dir / "playnow_doengine_backbone.json",
        "illusionviunow": playnow_dir / "illusionviunow_runtime.json",
        "orbitnow": playnow_dir / "orbitnow_runtime.json",
        "dodoplaynow": playnow_dir / "dodoplaynow_runtime.json",
        "finalstage": playnow_dir / "playnow_finalstage_manifest.json",
    }

    save_json(payload_paths["doengine_backbone"], handoff_payloads["doengine_backbone"])
    save_json(payload_paths["illusionviunow"], handoff_payloads["illusionviunow"])
    save_json(payload_paths["orbitnow"], handoff_payloads["orbitnow"])
    save_json(payload_paths["dodoplaynow"], handoff_payloads["dodoplaynow"])
    save_json(payload_paths["finalstage"], finalstage_payload)

    return {
        "protocol_contract": protocol_contract,
        "paths": {name: str(path) for name, path in payload_paths.items()},
    }


def resolve_player_paths(asset_root: Path) -> tuple[Path, Path]:
    external_blend = asset_root / "generated" / "blender_bango_autorig" / "bangopatoot_asset_3dmodel_bango_riggedautoblockout_0001.blend"
    external_glb = asset_root / "generated" / "blender_bango_autorig" / "bangopatoot_asset_3dmodel_bango_riggedautoblockout_0001.glb"
    if external_blend.exists():
        return external_blend, external_glb
    repo_blend = ROOT / "generated" / "blender_bango_autorig" / "bangopatoot_asset_3dmodel_bango_riggedautoblockout_0001.blend"
    repo_glb = ROOT / "generated" / "blender_bango_autorig" / "bangopatoot_asset_3dmodel_bango_riggedautoblockout_0001.glb"
    return repo_blend, repo_glb


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PlayNOW integration for Bango tutorial/runtime staging")
    parser.add_argument("--asset-root", type=Path)
    parser.add_argument("--pass-label", type=str, default="default")
    parser.add_argument("--asset-manifest", type=Path)
    parser.add_argument("--skip-autorig", action="store_true")
    args = parser.parse_args()

    asset_root = args.asset_root.resolve() if args.asset_root else resolve_asset_root(ROOT)
    playnow_dir = asset_root / "generated" / PLAYNOW_DIRNAME
    playnow_dir.mkdir(parents=True, exist_ok=True)

    autorig = {"status": "skipped", "reason": "skip_autorig_requested"}
    if not args.skip_autorig:
        autorig = run_autorig(asset_root)

    player_blend, player_glb = resolve_player_paths(asset_root)
    idloadint_dir = asset_root / "generated" / "idLoadINT_bundle"
    pipeline_report_path = asset_root / "generated" / "clip_blend_id" / "pipeline_report.json"
    blendnow_bundle = load_blendnow_bundle(asset_root)
    pass_manifest = read_json_if_exists(args.asset_manifest) if args.asset_manifest else None
    tutorial_library = build_tutorial_library()
    selected_tutorial_spec = FINAL_PREVIEW_TUTORIAL_SPEC_PATH if args.pass_label == "tutorial_final_preview" else PROTOTYPE_TUTORIAL_SPEC_PATH

    integration_entry = {
        "pass_label": args.pass_label,
        "player_blend": str(player_blend),
        "player_glb": str(player_glb),
        "pipeline_report": str(pipeline_report_path),
        "tutorial_manifest": str(idloadint_dir / "idLoadINT_manifest.json"),
        "tutorial_spec": str(selected_tutorial_spec),
        "runtime_tutorial_spec": str(idloadint_dir / "tutorial_demo_spec.json"),
        "enemy_spec": str(idloadint_dir / "nightmaresludgebio_orbs.json"),
        "tutorial_library": tutorial_library,
        "tutorial_prompt_contract": str(TUTORIAL_CONTRACT_PATH),
        "blendnow_bundle": blendnow_bundle,
        "asset_manifest": str(args.asset_manifest) if args.asset_manifest else None,
        "asset_count": len(pass_manifest.get("assets", [])) if isinstance(pass_manifest, dict) else None,
        "asset_budget": pass_manifest.get("budget") if isinstance(pass_manifest, dict) else None,
        "asset_traceability": pass_manifest.get("traceability") if isinstance(pass_manifest, dict) else None,
    }

    runtime_manifest_path = playnow_dir / "playnow_runtime_manifest.json"
    runtime_manifest = read_json_if_exists(runtime_manifest_path)
    if not isinstance(runtime_manifest, dict):
        runtime_manifest = {
            "system": "PlayNOW",
            "asset_root": str(asset_root),
            "passes": [],
        }

    existing_passes = [entry for entry in runtime_manifest.get("passes", []) if entry.get("pass_label") != args.pass_label]
    existing_passes.append(integration_entry)
    runtime_manifest["passes"] = existing_passes
    runtime_manifest["player"] = {
        "blend": str(player_blend),
        "glb": str(player_glb),
    }
    runtime_manifest["autorig"] = autorig

    engine_handoffs = build_engine_handoffs(asset_root, integration_entry, runtime_manifest_path, runtime_manifest)
    runtime_manifest["protocol_contract"] = engine_handoffs["protocol_contract"]
    runtime_manifest["engine_handoffs"] = engine_handoffs["paths"]

    per_pass_path = playnow_dir / f"playnow_{args.pass_label}_integration.json"
    save_json(per_pass_path, integration_entry)
    save_json(runtime_manifest_path, runtime_manifest)

    print(json.dumps({
        "asset_root": str(asset_root),
        "runtime_manifest": str(runtime_manifest_path),
        "pass_manifest": str(per_pass_path),
        "finalstage_manifest": engine_handoffs["paths"]["finalstage"],
        "player_blend": str(player_blend),
        "player_blend_exists": player_blend.exists(),
        "autorig_returncode": autorig.get("returncode"),
    }, indent=2))
    if player_blend.exists():
        return 0
    return 0 if autorig.get("returncode", 0) == 0 or args.skip_autorig else autorig.get("returncode", 1)


if __name__ == "__main__":
    raise SystemExit(main())
