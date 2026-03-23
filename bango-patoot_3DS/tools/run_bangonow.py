from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from bango_pipeline_paths import resolve_asset_root
from build_bango_production_asset_program import ANGLE_LAYOUT, build_creative_bible, build_prompt_context, build_recraft_intake_guide, make_asset, save_json


ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = ROOT.parent
TOOLS_ROOT = WORKSPACE_ROOT / ".tools" / "bin"
POLISH_TOOL = WORKSPACE_ROOT / "readAIpolish" / "readAIpolish_cli.py"
DOENGINE_ROOT = WORKSPACE_ROOT / "DoENGINE"
ORBENGINE_ROOT = WORKSPACE_ROOT / "ORBEngine"


def resolve_powershell() -> str:
    for candidate in ("pwsh", "powershell"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise FileNotFoundError("Unable to locate PowerShell. Expected pwsh or powershell in PATH.")


def run_command(command: list[str], *, env: dict[str, str] | None = None) -> dict:
    result = subprocess.run(command, capture_output=True, text=True, check=False, env=env)
    return {
        "command": " ".join(command),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def resolve_windows_env_var(name: str) -> str | None:
    if os.name != "nt":
        return None
    for scope in ("User", "Machine"):
        command = [
            resolve_powershell(),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            f"[Environment]::GetEnvironmentVariable('{name}','{scope}')",
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        value = (result.stdout or "").strip()
        if value:
            return value
    return None


def build_runtime_env(asset_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["BANGO_ASSET_ROOT"] = str(asset_root)
    if not env.get("RECRAFT_API_KEY"):
        recraft_api_key = resolve_windows_env_var("RECRAFT_API_KEY")
        if recraft_api_key:
            env["RECRAFT_API_KEY"] = recraft_api_key
    return env


def run_polish(input_path: Path, output_path: Path, *, env: dict[str, str]) -> dict:
    command = [
        sys.executable,
        str(POLISH_TOOL),
        str(input_path),
        "--out-dir",
        str(output_path),
    ]
    return run_command(command, env=env)


def run_powershell_script(script_path: Path, arguments: list[str] | None = None, *, env: dict[str, str] | None = None) -> dict:
    command = [resolve_powershell(), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_path)]
    if arguments:
        command.extend(arguments)
    return run_command(command, env=env)


def run_powershell_command(command_text: str, *, env: dict[str, str] | None = None) -> dict:
    command = [resolve_powershell(), "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command_text]
    return run_command(command, env=env)


def build_manifest_shell(asset_root: Path, name: str, assets: list[dict], metadata: dict[str, object] | None = None) -> tuple[Path, dict]:
    manifest_dir = asset_root / "generated" / "bangonow" / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"{name}.json"
    manifest = {
        "manifest_name": name,
        "manifest_version": "2026-03-13.bangonow",
        "output_root": str(asset_root),
        "asset_root": str(asset_root),
        "assets": assets,
    }
    if metadata:
        manifest.update(metadata)
    save_json(manifest_path, manifest)
    return manifest_path, manifest


def build_combat16_manifest(asset_root: Path) -> tuple[Path, dict]:
    creative_bible = build_creative_bible()
    intake_guide = build_recraft_intake_guide(creative_bible)
    character_context = build_prompt_context(intake_guide, "character_sheet")
    animation_context = build_prompt_context(intake_guide, "animation_pack")
    fx_context = build_prompt_context(intake_guide, "combat_fx")
    environment_context = build_prompt_context(intake_guide, "environment_set")
    assets = [
        make_asset(name="combat16_bango_turnaround", category="character_sheet", prompt="Bango front-line combat turnaround sheet for a focused combat test arena, transparent background, four-angle readable combat stance presentation.", out="production_raw/bangonow/combat16/combat16_bango_turnaround.png", planned_credits=9, width=2048, height=2048, pipeline_targets=["clipstudio", "blender", "idtech2"], prompt_context=character_context, protocol={"layout": "four_angle_quadrant", "angle_positions": ANGLE_LAYOUT, "derived_outputs": ["texture_depth_map", "hit_precision_map"]}),
        make_asset(name="combat16_bango_light_combo", category="animation_pack", prompt="Bango light combo production pack for a focused combat batch, transparent background, four viewpoints, lower support rows reserved for depth and hit precision.", out="production_raw/bangonow/combat16/combat16_bango_light_combo.png", planned_credits=8, width=4096, height=4096, pipeline_targets=["clipstudio", "blender", "idtech2"], prompt_context=animation_context, protocol={"layout": "four_angle_sequence_pack", "angle_positions": ANGLE_LAYOUT, "sequence_span": [1, 4], "derived_outputs": ["texture_depth_map", "hit_precision_map"]}),
        make_asset(name="combat16_bango_heavy_combo", category="animation_pack", prompt="Bango heavy combo production pack for a focused combat batch, transparent background, four viewpoints, stagger and recovery emphasized.", out="production_raw/bangonow/combat16/combat16_bango_heavy_combo.png", planned_credits=8, width=4096, height=4096, pipeline_targets=["clipstudio", "blender", "idtech2"], prompt_context=animation_context, protocol={"layout": "four_angle_sequence_pack", "angle_positions": ANGLE_LAYOUT, "sequence_span": [5, 8], "derived_outputs": ["texture_depth_map", "hit_precision_map"]}),
        make_asset(name="combat16_bango_parry_block", category="animation_pack", prompt="Bango parry and block production pack for a focused combat batch, transparent background, defensive timing readable from all four views.", out="production_raw/bangonow/combat16/combat16_bango_parry_block.png", planned_credits=8, width=4096, height=4096, pipeline_targets=["clipstudio", "blender", "idtech2"], prompt_context=animation_context, protocol={"layout": "four_angle_sequence_pack", "angle_positions": ANGLE_LAYOUT, "sequence_span": [9, 12], "derived_outputs": ["texture_depth_map", "hit_precision_map"]}),
        make_asset(name="combat16_bango_slide_heal", category="animation_pack", prompt="Bango sprint-slide and honey-vial recovery production pack for a focused combat batch, transparent background, four viewpoints, gameplay readability prioritized.", out="production_raw/bangonow/combat16/combat16_bango_slide_heal.png", planned_credits=8, width=4096, height=4096, pipeline_targets=["clipstudio", "blender", "idtech2"], prompt_context=animation_context, protocol={"layout": "four_angle_sequence_pack", "angle_positions": ANGLE_LAYOUT, "sequence_span": [13, 16], "derived_outputs": ["texture_depth_map", "hit_precision_map"]}),
        make_asset(name="combat16_orb_scout_sheet", category="character_sheet", prompt="Nightmaresludgebio orb scout enemy turnaround sheet, peculiar sludge orb scout, transparent background, four-angle combat readability and hover silhouette clarity.", out="production_raw/bangonow/combat16/combat16_orb_scout_sheet.png", planned_credits=9, width=2048, height=2048, pipeline_targets=["clipstudio", "blender", "idtech2"], prompt_context=character_context, protocol={"layout": "four_angle_quadrant", "angle_positions": ANGLE_LAYOUT, "derived_outputs": ["texture_depth_map", "hit_precision_map"]}),
        make_asset(name="combat16_orb_mire_sheet", category="character_sheet", prompt="Nightmaresludgebio orb mire enemy turnaround sheet, peculiar sludge orb mire, transparent background, four-angle combat readability and hover silhouette clarity.", out="production_raw/bangonow/combat16/combat16_orb_mire_sheet.png", planned_credits=9, width=2048, height=2048, pipeline_targets=["clipstudio", "blender", "idtech2"], prompt_context=character_context, protocol={"layout": "four_angle_quadrant", "angle_positions": ANGLE_LAYOUT, "derived_outputs": ["texture_depth_map", "hit_precision_map"]}),
        make_asset(name="combat16_orb_horror_sheet", category="character_sheet", prompt="Nightmaresludgebio orb horror enemy turnaround sheet, peculiar sludge orb horror, transparent background, four-angle combat readability and hover silhouette clarity.", out="production_raw/bangonow/combat16/combat16_orb_horror_sheet.png", planned_credits=9, width=2048, height=2048, pipeline_targets=["clipstudio", "blender", "idtech2"], prompt_context=character_context, protocol={"layout": "four_angle_quadrant", "angle_positions": ANGLE_LAYOUT, "derived_outputs": ["texture_depth_map", "hit_precision_map"]}),
        make_asset(name="combat16_orb_scout_animation", category="animation_pack", prompt="Peculiar sludge orb scout animation pack with float, attack primary, attack secondary, regen, and death timing, transparent background, four viewpoints.", out="production_raw/bangonow/combat16/combat16_orb_scout_animation.png", planned_credits=8, width=4096, height=4096, pipeline_targets=["clipstudio", "blender", "idtech2"], prompt_context=animation_context, protocol={"layout": "four_angle_sequence_pack", "angle_positions": ANGLE_LAYOUT, "sequence_span": [1, 4], "derived_outputs": ["texture_depth_map", "hit_precision_map"]}),
        make_asset(name="combat16_orb_mire_animation", category="animation_pack", prompt="Peculiar sludge orb mire animation pack with float, attack primary, attack secondary, regen, and death timing, transparent background, four viewpoints.", out="production_raw/bangonow/combat16/combat16_orb_mire_animation.png", planned_credits=8, width=4096, height=4096, pipeline_targets=["clipstudio", "blender", "idtech2"], prompt_context=animation_context, protocol={"layout": "four_angle_sequence_pack", "angle_positions": ANGLE_LAYOUT, "sequence_span": [5, 8], "derived_outputs": ["texture_depth_map", "hit_precision_map"]}),
        make_asset(name="combat16_orb_horror_animation", category="animation_pack", prompt="Peculiar sludge orb horror animation pack with float, attack primary, attack secondary, regen, and death timing, transparent background, four viewpoints.", out="production_raw/bangonow/combat16/combat16_orb_horror_animation.png", planned_credits=8, width=4096, height=4096, pipeline_targets=["clipstudio", "blender", "idtech2"], prompt_context=animation_context, protocol={"layout": "four_angle_sequence_pack", "angle_positions": ANGLE_LAYOUT, "sequence_span": [9, 12], "derived_outputs": ["texture_depth_map", "hit_precision_map"]}),
        make_asset(name="combat16_orb_swarm_arena", category="environment_set", prompt="Focused combat arena for Bango versus nightmaresludgebio orb swarms, transparent background modular battle pod with clear navigable lanes and shrine-tech cover.", out="production_raw/bangonow/combat16/combat16_orb_swarm_arena.png", planned_credits=20, width=4096, height=4096, pipeline_targets=["clipstudio", "blender", "idtech2"], prompt_context=environment_context, protocol={"layout": "thirteen_tile_modular_sheet", "tile_count": 13, "derived_outputs": ["texture_depth_map", "hit_precision_map", "tile_material_masks"]}),
        make_asset(name="combat16_orb_intro_hud", category="hud_pack", prompt="Combat batch HUD atlas for Bango and orb enemy target-readiness, transparent background, lock-on, health, stagger, and warning indicators.", out="production_raw/bangonow/combat16/combat16_orb_intro_hud.png", planned_credits=12, width=2048, height=2048, pipeline_targets=["clipstudio", "idtech2"], prompt_context=build_prompt_context(intake_guide, "hud_pack"), protocol={"layout": "ui_atlas", "element_span": [1, 16], "derived_outputs": ["hit_precision_map"]}),
        make_asset(name="combat16_honey_parry_fx", category="combat_fx", prompt="Combat effects sheet for honey parry flashes, orb impact rings, and shrine-ward hit confirmations, transparent background, horizontal frames with depth and hit rows.", out="production_raw/bangonow/combat16/combat16_honey_parry_fx.png", planned_credits=16, width=4096, height=2048, pipeline_targets=["clipstudio", "blender", "idtech2"], prompt_context=fx_context, protocol={"layout": "horizontal_spritesheet_with_depth_hit_rows", "angle_views": 4, "derived_outputs": ["depth_row", "hit_row"]}),
        make_asset(name="combat16_orb_spawn_fx", category="combat_fx", prompt="Combat effects sheet for nightmaresludgebio orb spawn bursts and mire splash exits, transparent background, horizontal frames with depth and hit rows.", out="production_raw/bangonow/combat16/combat16_orb_spawn_fx.png", planned_credits=16, width=4096, height=2048, pipeline_targets=["clipstudio", "blender", "idtech2"], prompt_context=fx_context, protocol={"layout": "horizontal_spritesheet_with_depth_hit_rows", "angle_views": 4, "derived_outputs": ["depth_row", "hit_row"]}),
        make_asset(name="combat16_orb_pressure_fx", category="combat_fx", prompt="Combat effects sheet for orb pressure waves and corrosive sludge rings, transparent background, horizontal frames with depth and hit rows.", out="production_raw/bangonow/combat16/combat16_orb_pressure_fx.png", planned_credits=16, width=4096, height=2048, pipeline_targets=["clipstudio", "blender", "idtech2"], prompt_context=fx_context, protocol={"layout": "horizontal_spritesheet_with_depth_hit_rows", "angle_views": 4, "derived_outputs": ["depth_row", "hit_row"]}),
    ]
    return build_manifest_shell(asset_root, "bangonow_combat16_manifest", assets)


def build_tutorial32_manifest(asset_root: Path) -> tuple[Path, dict]:
    creative_bible = build_creative_bible()
    intake_guide = build_recraft_intake_guide(creative_bible)
    env_context = build_prompt_context(intake_guide, "environment_set")
    hud_context = build_prompt_context(intake_guide, "hud_pack")
    object_context = build_prompt_context(intake_guide, "animated_environment_object")
    apiary_context = build_prompt_context(intake_guide, "apiary_sheet")
    fx_context = build_prompt_context(intake_guide, "environmental_fx")
    calibration_context = build_prompt_context(intake_guide, "pipeline_calibration")
    assets: list[dict] = []
    room_names = [
        "matrix_grid_spawn_room", "matrix_grid_movement_room", "matrix_grid_camera_room", "matrix_grid_jump_room",
        "matrix_grid_slide_room", "matrix_grid_lockon_room", "matrix_grid_orb_room", "matrix_grid_exit_room",
    ]
    for room_name in room_names:
        assets.append(make_asset(name=room_name, category="environment_set", prompt=f"Introductory tutorial matrix-grid VR room module for {room_name}, transparent background, simulated training geometry, shrine-tech overlays, and crisp 3DS-readable teaching landmarks.", out=f"production_raw/bangonow/tutorial32/{room_name}.png", planned_credits=20, width=4096, height=4096, pipeline_targets=["clipstudio", "blender", "idtech2"], prompt_context=env_context, protocol={"layout": "thirteen_tile_modular_sheet", "tile_count": 13, "derived_outputs": ["texture_depth_map", "hit_precision_map", "tile_material_masks"]}))
    hud_names = ["move_prompt_hud", "camera_prompt_hud", "jump_prompt_hud", "slide_prompt_hud", "combat_prompt_hud", "exit_prompt_hud"]
    for hud_name in hud_names:
        assets.append(make_asset(name=hud_name, category="hud_pack", prompt=f"Tutorial HUD atlas for {hud_name} inside a simulated matrix-grid VR intro room, transparent background, instruction-first readability.", out=f"production_raw/bangonow/tutorial32/{hud_name}.png", planned_credits=12, width=2048, height=2048, pipeline_targets=["clipstudio", "idtech2"], prompt_context=hud_context, protocol={"layout": "ui_atlas", "element_span": [1, 12], "derived_outputs": ["hit_precision_map"]}))
    object_names = ["training_gate", "signal_pylon", "parry_totem", "jump_pad", "slide_barrier", "exit_console"]
    for object_name in object_names:
        assets.append(make_asset(name=object_name, category="animated_environment_object", prompt=f"Tutorial animated object sheet for {object_name} in a simulated matrix-grid VR intro room, transparent background, four-angle state coverage and readable activation states.", out=f"production_raw/bangonow/tutorial32/{object_name}.png", planned_credits=16, width=3072, height=3072, pipeline_targets=["clipstudio", "blender", "idtech2"], prompt_context=object_context, protocol={"layout": "four_angle_object_sheet", "angle_positions": ANGLE_LAYOUT, "derived_outputs": ["texture_depth_map", "hit_precision_map"]}))
    apiary_names = ["tutorial_apiary_beacon_a", "tutorial_apiary_beacon_b", "tutorial_apiary_checkpoint_a", "tutorial_apiary_checkpoint_b"]
    for apiary_name in apiary_names:
        assets.append(make_asset(name=apiary_name, category="apiary_sheet", prompt=f"Tutorial apiary structure sheet for {apiary_name} in a simulated matrix-grid VR intro room, transparent background, ritual maintenance device with clear checkpoint behavior.", out=f"production_raw/bangonow/tutorial32/{apiary_name}.png", planned_credits=18, width=3072, height=3072, pipeline_targets=["clipstudio", "blender", "idtech2"], prompt_context=apiary_context, protocol={"layout": "four_angle_object_sheet", "angle_positions": ANGLE_LAYOUT, "derived_outputs": ["texture_depth_map", "hit_precision_map"]}))
    fx_names = ["grid_boot_fx", "grid_scan_fx", "orb_spawn_tutorial_fx", "checkpoint_bloom_fx"]
    for fx_name in fx_names:
        assets.append(make_asset(name=fx_name, category="environmental_fx", prompt=f"Tutorial atmospheric effect for {fx_name} in a simulated matrix-grid VR intro room, transparent background, training-space volumetrics and readable teaching emphasis.", out=f"production_raw/bangonow/tutorial32/{fx_name}.png", planned_credits=16, width=4096, height=4096, pipeline_targets=["clipstudio", "blender", "idtech2"], prompt_context=fx_context, protocol={"layout": "angle_mapped_360_sheet", "coverage_degrees": 360, "derived_outputs": ["texture_depth_map", "hit_precision_map"]}))
    calibration_names = ["tutorial_calibration_a", "tutorial_calibration_b", "tutorial_calibration_c", "tutorial_calibration_d"]
    for calibration_name in calibration_names:
        assets.append(make_asset(name=calibration_name, category="pipeline_calibration", prompt=f"Tutorial calibration sheet for {calibration_name} to verify matrix-grid VR intro-room material response and silhouette stability across the Bango pipeline.", out=f"production_raw/bangonow/tutorial32/{calibration_name}.png", planned_credits=12, width=2048, height=2048, pipeline_targets=["clipstudio", "blender", "idtech2"], prompt_context=calibration_context, protocol={"layout": "calibration_grid", "derived_outputs": ["texture_depth_map", "hit_precision_map"]}))
    return build_manifest_shell(asset_root, "bangonow_tutorial32_manifest", assets)


def build_tutorial_duology_8000_manifest(asset_root: Path) -> tuple[Path, dict]:
    creative_bible = build_creative_bible()
    intake_guide = build_recraft_intake_guide(creative_bible)
    env_context = build_prompt_context(intake_guide, "environment_set")
    character_context = build_prompt_context(intake_guide, "character_sheet")
    animation_context = build_prompt_context(intake_guide, "animation_pack")
    hud_context = build_prompt_context(intake_guide, "hud_pack")
    object_context = build_prompt_context(intake_guide, "animated_environment_object")
    apiary_context = build_prompt_context(intake_guide, "apiary_sheet")
    fx_context = build_prompt_context(intake_guide, "environmental_fx")
    item_context = build_prompt_context(intake_guide, "item_pack")
    weapon_context = build_prompt_context(intake_guide, "weapon_pack")
    armor_context = build_prompt_context(intake_guide, "armor_set")
    calibration_context = build_prompt_context(intake_guide, "pipeline_calibration")
    assets: list[dict] = []

    budget_totals = {
        "tutorial_duology_current_delivery": 0,
        "forward_buffer_hub_world_tilesets": 0,
        "forward_buffer_weapons_armor": 0,
        "forward_buffer_priority_content": 0,
    }

    def add_asset(*, name: str, category: str, prompt: str, credits: int, width: int, height: int, prompt_context: str, protocol: dict, bucket: str, deliverables: list[str], pipeline_targets: list[str], priority_tier: str, lineage: dict) -> None:
        assets.append(
            make_asset(
                name=name,
                category=category,
                prompt=prompt,
                out=f"production_raw/bangonow/tutorial_duology_8000/{name}.png",
                planned_credits=credits,
                width=width,
                height=height,
                pipeline_targets=pipeline_targets,
                prompt_context=prompt_context,
                protocol=protocol,
                budget_bucket=bucket,
                deliverable_tags=deliverables,
                priority_tier=priority_tier,
                lineage=lineage,
            )
        )
        budget_totals[bucket] += credits

    tutorial_assets = [
        ("prototype_void_corridor", "environment_set", 200, 4096, 4096, env_context, {"layout": "thirteen_tile_modular_sheet", "tile_count": 13, "derived_outputs": ["texture_depth_map", "hit_precision_map", "tile_material_masks"]}, ["tutorial_prototype"], ["clipstudio", "blender", "idtech2"], "core", "Prototype tutorial corridor chamber with bold gradient navigation lanes and exact readability for movement onboarding."),
        ("prototype_movement_gate", "environment_set", 200, 4096, 4096, env_context, {"layout": "thirteen_tile_modular_sheet", "tile_count": 13, "derived_outputs": ["texture_depth_map", "hit_precision_map", "tile_material_masks"]}, ["tutorial_prototype"], ["clipstudio", "blender", "idtech2"], "core", "Prototype tutorial movement gate room with sprint and dodge landmarks and shrine-tech simulator geometry."),
        ("prototype_orb_chamber", "environment_set", 200, 4096, 4096, env_context, {"layout": "thirteen_tile_modular_sheet", "tile_count": 13, "derived_outputs": ["texture_depth_map", "hit_precision_map", "tile_material_masks"]}, ["tutorial_prototype"], ["clipstudio", "blender", "idtech2"], "core", "Prototype tutorial orb lesson room with projectile-clear lanes and coherent depth."),
        ("final_market_corridor", "environment_set", 200, 4096, 4096, env_context, {"layout": "thirteen_tile_modular_sheet", "tile_count": 13, "derived_outputs": ["texture_depth_map", "hit_precision_map", "tile_material_masks"]}, ["tutorial_final_preview"], ["clipstudio", "blender", "idtech2"], "core", "Final tutorial preview market corridor with social-anxiety dread pressure and readable traversal anchors."),
        ("final_marketplace_finish", "environment_set", 200, 4096, 4096, env_context, {"layout": "thirteen_tile_modular_sheet", "tile_count": 13, "derived_outputs": ["texture_depth_map", "hit_precision_map", "tile_material_masks"]}, ["tutorial_final_preview", "marketplace_capture"], ["clipstudio", "blender", "idtech2"], "core", "Final tutorial preview finish arena intended for marketplace screenshots with layered shrine-tech market pocket readability."),
        ("prototype_bango_move_pack", "animation_pack", 200, 4096, 4096, animation_context, {"layout": "four_angle_sequence_pack", "angle_positions": ANGLE_LAYOUT, "sequence_span": [1, 4], "derived_outputs": ["texture_depth_map", "hit_precision_map"]}, ["tutorial_prototype"], ["clipstudio", "blender", "idtech2"], "core", "Bango prototype tutorial movement pack with walk, jump, sprint, and slide for onboarding readability."),
        ("prototype_bango_combat_pack", "animation_pack", 200, 4096, 4096, animation_context, {"layout": "four_angle_sequence_pack", "angle_positions": ANGLE_LAYOUT, "sequence_span": [5, 8], "derived_outputs": ["texture_depth_map", "hit_precision_map"]}, ["tutorial_prototype"], ["clipstudio", "blender", "idtech2"], "core", "Bango prototype tutorial combat pack with light-heavy starter strings and readable frame timing."),
        ("prototype_orb_behavior_pack", "animation_pack", 200, 4096, 4096, animation_context, {"layout": "four_angle_sequence_pack", "angle_positions": ANGLE_LAYOUT, "sequence_span": [9, 12], "derived_outputs": ["texture_depth_map", "hit_precision_map"]}, ["tutorial_prototype", "tutorial_final_preview"], ["clipstudio", "blender", "idtech2"], "core", "Prototype orb-drone shared animation pack with hover, scout fire, mire drag, and horror charge."),
        ("final_bango_combat_pack", "animation_pack", 200, 4096, 4096, animation_context, {"layout": "four_angle_sequence_pack", "angle_positions": ANGLE_LAYOUT, "sequence_span": [13, 16], "derived_outputs": ["texture_depth_map", "hit_precision_map"]}, ["tutorial_final_preview", "marketplace_capture"], ["clipstudio", "blender", "idtech2"], "core", "Bango final tutorial preview combat pack with marketplace-ready light-heavy-parry cadence."),
        ("final_patoot_support_pack", "animation_pack", 200, 4096, 4096, animation_context, {"layout": "four_angle_sequence_pack", "angle_positions": ANGLE_LAYOUT, "sequence_span": [17, 20], "derived_outputs": ["texture_depth_map", "hit_precision_map"]}, ["tutorial_final_preview"], ["clipstudio", "blender", "idtech2"], "core", "Patoot final tutorial preview support animation pack with mitigation, focus assist, and emotional grounding gestures."),
        ("prototype_tutorial_hud", "hud_pack", 200, 2048, 2048, hud_context, {"layout": "ui_atlas", "element_span": [1, 16], "derived_outputs": ["hit_precision_map"]}, ["tutorial_prototype"], ["clipstudio", "idtech2"], "core", "Prototype tutorial HUD atlas for movement and combat onboarding with exact prompt readability."),
        ("final_dread_widgets", "hud_pack", 200, 2048, 2048, hud_context, {"layout": "ui_atlas", "element_span": [17, 32], "derived_outputs": ["hit_precision_map"]}, ["tutorial_final_preview", "marketplace_capture"], ["clipstudio", "idtech2"], "core", "Final tutorial preview HUD atlas for Patoot-heavy support loop and encroaching dread telemetry."),
        ("prototype_spawn_fx", "environmental_fx", 200, 4096, 4096, fx_context, {"layout": "angle_mapped_360_sheet", "coverage_degrees": 360, "derived_outputs": ["texture_depth_map", "hit_precision_map"]}, ["tutorial_prototype"], ["clipstudio", "blender", "idtech2"], "support", "Prototype tutorial atmospheric effect for player spawn, orb wake, and checkpoint bloom."),
        ("final_dread_fx", "environmental_fx", 200, 4096, 4096, fx_context, {"layout": "angle_mapped_360_sheet", "coverage_degrees": 360, "derived_outputs": ["texture_depth_map", "hit_precision_map"]}, ["tutorial_final_preview"], ["clipstudio", "blender", "idtech2"], "support", "Final tutorial preview atmospheric effect for encroaching dread waves with readable pressure cues."),
        ("final_support_fx", "environmental_fx", 200, 4096, 4096, fx_context, {"layout": "angle_mapped_360_sheet", "coverage_degrees": 360, "derived_outputs": ["texture_depth_map", "hit_precision_map"]}, ["tutorial_final_preview"], ["clipstudio", "blender", "idtech2"], "support", "Final tutorial preview atmospheric effect for Patoot mitigation pulses and support-forward readable shielding cues."),
    ]
    for name, category, credits, width, height, context, protocol, deliverables, targets, priority_tier, prompt in tutorial_assets:
        add_asset(name=name, category=category, prompt=prompt, credits=credits, width=width, height=height, prompt_context=context, protocol=protocol, bucket="tutorial_duology_current_delivery", deliverables=deliverables, pipeline_targets=targets, priority_tier=priority_tier, lineage={"source_contract": "specs/playnow_tutorial_duology_contract.json", "runtime_modes": deliverables})

    for name in [
        "apiary_junction_hub_tileset",
        "brassroot_borough_tileset",
        "saint_voltage_arcade_tileset",
        "ossuary_transit_tileset",
        "gutterwake_sewers_tileset",
        "cinder_tenements_tileset",
        "aviary_last_broadcast_tileset",
        "witchcoil_spire_tileset",
        "hub_support_sanctum_tileset",
        "market_finish_landmark_tileset",
    ]:
        add_asset(name=name, category="environment_set", prompt=f"Forward-production full-game environment and tileset set for {name}, modular hub-and-world landmark readability, 3D conversion-safe surfaces, and marketplace-grade spatial silhouette discipline.", credits=250, width=4096, height=4096, prompt_context=env_context, protocol={"layout": "thirteen_tile_modular_sheet", "tile_count": 13, "derived_outputs": ["texture_depth_map", "hit_precision_map", "tile_material_masks"]}, bucket="forward_buffer_hub_world_tilesets", deliverables=["full_game_buffer", "environment_preview"], pipeline_targets=["clipstudio", "blender", "idtech2"], priority_tier="market_finish", lineage={"source_contract": "specs/bango_fullgame_completion_budget_contract.json", "preview_role": "second_tutorial_environment_preview"})

    weapons_armor_assets = [
        ("bango_starter_weapon_pack", "weapon_pack", weapon_context, "Starter weapon pack for Bango with clear handling silhouettes, salvage-shrine material logic, and upgrade-ready modularity."),
        ("bango_guard_weapon_pack", "weapon_pack", weapon_context, "Secondary guard and parry weapon pack for Bango with finish-grade combat readability and defensive silhouettes."),
        ("patoot_support_ward_kit", "weapon_pack", weapon_context, "Patoot support ward kit blending focus tools, mitigation emitters, and companion-forward defensive gear."),
        ("market_finish_armor_set", "armor_set", armor_context, "Marketplace-facing armor set with practical ritual labor wear, readable layering, and finish-grade material breakup."),
        ("hub_guard_armor_set", "armor_set", armor_context, "Hub and world traversal armor set with support-ready silhouettes, salvage-tech closure details, and modular upgrade spacing."),
    ]
    for name, category, context, prompt in weapons_armor_assets:
        add_asset(name=name, category=category, prompt=prompt, credits=200, width=3072, height=3072, prompt_context=context, protocol={"layout": "packed_reference_sheet", "entry_span": [1, 8], "derived_outputs": ["texture_depth_map", "hit_precision_map"]}, bucket="forward_buffer_weapons_armor", deliverables=["full_game_buffer", "combat_readiness"], pipeline_targets=["clipstudio", "blender", "idtech2"], priority_tier="market_finish", lineage={"source_contract": "specs/bango_fullgame_completion_budget_contract.json", "equipment_role": category})

    reserve_assets = [
        ("scout_enemy_finish_sheet", "character_sheet", character_context, 150, 2048, 2048, {"layout": "four_angle_quadrant", "angle_positions": ANGLE_LAYOUT, "derived_outputs": ["texture_depth_map", "hit_precision_map"]}, "Basic-tier scout enemy finish sheet with clear silhouette escalation for the shippable tutorial and full game."),
        ("mire_enemy_finish_sheet", "character_sheet", character_context, 150, 2048, 2048, {"layout": "four_angle_quadrant", "angle_positions": ANGLE_LAYOUT, "derived_outputs": ["texture_depth_map", "hit_precision_map"]}, "Basic-tier mire enemy finish sheet with heavier pressure read and support-safe combat readability."),
        ("horror_enemy_finish_sheet", "character_sheet", character_context, 150, 2048, 2048, {"layout": "four_angle_quadrant", "angle_positions": ANGLE_LAYOUT, "derived_outputs": ["texture_depth_map", "hit_precision_map"]}, "Basic-tier horror enemy finish sheet with escalated dread but fully readable motion silhouettes."),
        ("basic_enemy_swarm_pack", "animation_pack", animation_context, 150, 4096, 4096, {"layout": "four_angle_sequence_pack", "angle_positions": ANGLE_LAYOUT, "sequence_span": [1, 4], "derived_outputs": ["texture_depth_map", "hit_precision_map"]}, "Basic-tier enemy swarm animation pack for the full tutorial enemy class set."),
        ("patoot_support_social_telemetry_hud", "hud_pack", hud_context, 150, 2048, 2048, {"layout": "ui_atlas", "element_span": [1, 12], "derived_outputs": ["hit_precision_map"]}, "HUD atlas for Patoot-heavy support telemetry, calm cues, and overload moderation."),
        ("social_dread_widget_pack", "hud_pack", hud_context, 150, 2048, 2048, {"layout": "ui_atlas", "element_span": [13, 24], "derived_outputs": ["hit_precision_map"]}, "HUD atlas for perpetual encroaching dread, social-anxiety pressure, and recoverable readability gates."),
        ("hub_dialogue_portrait_pack", "item_pack", item_context, 150, 3072, 3072, {"layout": "packed_reference_sheet", "entry_span": [1, 10], "derived_outputs": ["texture_depth_map", "hit_precision_map"]}, "Dialogue portrait and social-space item pack for hub interactions and support-heavy onboarding beats."),
        ("market_collectible_item_pack", "item_pack", item_context, 150, 3072, 3072, {"layout": "packed_reference_sheet", "entry_span": [11, 20], "derived_outputs": ["texture_depth_map", "hit_precision_map"]}, "Collectible item pack for market-finish tutorial rewards, pickups, and equipment upgrade hooks."),
        ("apiary_checkpoint_object_pack", "apiary_sheet", apiary_context, 150, 3072, 3072, {"layout": "four_angle_object_sheet", "angle_positions": ANGLE_LAYOUT, "derived_outputs": ["texture_depth_map", "hit_precision_map"]}, "Apiary checkpoint object pack for support-safe respawn, save, and narrative checkpoint flows."),
        ("runtime_calibration_market_finish", "pipeline_calibration", calibration_context, 150, 2048, 2048, {"layout": "calibration_grid", "derived_outputs": ["texture_depth_map", "hit_precision_map"]}, "Pipeline calibration sheet for finish-grade market tutorial readability, depth stability, and runtime color consistency."),
    ]
    for name, category, context, credits, width, height, protocol, prompt in reserve_assets:
        add_asset(name=name, category=category, prompt=prompt, credits=credits, width=width, height=height, prompt_context=context, protocol=protocol, bucket="forward_buffer_priority_content", deliverables=["full_game_buffer", "basic_enemy_class", "tutorial_extension"], pipeline_targets=["clipstudio", "blender", "idtech2"], priority_tier="priority_buffer", lineage={"source_contract": "specs/bango_fullgame_completion_budget_contract.json", "remaining_pool_total": 1500})

    total_allocated = sum(budget_totals.values())

    return build_manifest_shell(
        asset_root,
        "bangonow_tutorial_duology_8000_manifest",
        assets,
        {
            "budget": {
                "currency": "credits",
                "target_credits": 8000,
                "committed_credits": total_allocated,
                "asset_count": len(assets),
                "allocations": {
                    "tutorial_duology_current_delivery": {
                        "target_credits": 3000,
                        "committed_credits": budget_totals["tutorial_duology_current_delivery"],
                        "purpose": "Ship the playable prototype tutorial and the stronger final-preview tutorial with presentable current content."
                    },
                    "full_game_buffer_total": {
                        "target_credits": 5000,
                        "committed_credits": budget_totals["forward_buffer_hub_world_tilesets"] + budget_totals["forward_buffer_weapons_armor"] + budget_totals["forward_buffer_priority_content"],
                        "purpose": "Buffer ahead into the full Bango-Patoot market-finish game instead of treating the tutorial pass as isolated throwaway work.",
                        "suballocations": {
                            "hub_world_landscapes_tilesets": {
                                "target_credits": 2500,
                                "committed_credits": budget_totals["forward_buffer_hub_world_tilesets"]
                            },
                            "weapons_and_armor": {
                                "target_credits": 1000,
                                "committed_credits": budget_totals["forward_buffer_weapons_armor"]
                            },
                            "remaining_priority_content": {
                                "target_credits": 1500,
                                "committed_credits": budget_totals["forward_buffer_priority_content"],
                                "coverage": ["basic-tier enemy class finish pass", "hub social-space content", "dread/support UI telemetry", "runtime calibration"]
                            }
                        }
                    },
                    "project_remaining_credits": {
                        "total_available_before_pass": 19960,
                        "allocated_in_this_manifest": total_allocated,
                        "remaining_after_this_manifest": 19960 - total_allocated
                    }
                }
            },
            "deliverables": ["tutorial_prototype", "tutorial_final_preview"],
            "manifest_protocol": "playnow_tutorial_duology_v1",
            "budget_contract": "specs/bango_fullgame_completion_budget_contract.json",
            "traceability": {
                "contract": "bango_asset_lineage_v1",
                "goal": "Track every generated 2D sheet forward into polish, Blender ingest, model conversion, animation binding, runtime pack, and tutorial or full-game deliverable usage.",
                "required_asset_fields": ["name", "category", "planned_credits", "out", "pipeline_targets", "traceability.trace_id", "traceability.budget_bucket", "traceability.deliverable_tags", "traceability.lineage"],
                "expected_stage_receipts": ["recraft_generation", "auto_polish", "blender_ingest", "rig_or_scene_conversion", "runtime_packaging", "animation_or_gameplay_binding"],
                "asset_root": str(asset_root),
            },
        },
    )


def run_playnow(asset_root: Path, pass_label: str, manifest_path: Path | None = None, *, skip_autorig: bool = False) -> dict:
    command = [
        sys.executable,
        str(ROOT / "tools" / "run_playnow.py"),
        "--asset-root",
        str(asset_root),
        "--pass-label",
        pass_label,
    ]
    if manifest_path is not None:
        command.extend(["--asset-manifest", str(manifest_path)])
    if skip_autorig:
        command.append("--skip-autorig")
    env = build_runtime_env(asset_root)
    return run_command(command, env=env)


def build_doengine_hybrid_runtime(asset_root: Path, *, env: dict[str, str]) -> dict:
    command = [
        sys.executable,
        str(DOENGINE_ROOT / "tools" / "build_dodo_hybrid_runtime.py"),
        "--asset-root",
        str(asset_root),
    ]
    return run_command(command, env=env)


def build_dodo_windows_bundle(asset_root: Path, *, env: dict[str, str]) -> dict:
    command = [
        sys.executable,
        str(DOENGINE_ROOT / "tools" / "build_dodo_windows_bundle.py"),
        "--asset-root",
        str(asset_root),
    ]
    return run_command(command, env=env)


def build_orb_tutorial_demo(*, env: dict[str, str]) -> dict:
    return run_powershell_script(ORBENGINE_ROOT / "build_tutorial_demo.ps1", env=env)


def parse_targets(raw_targets: str) -> list[str]:
    if raw_targets.strip().lower() == "all":
        return ["3ds", "windows", "idtech2"]
    ordered: list[str] = []
    for item in raw_targets.split(","):
        target = item.strip().lower()
        if not target:
            continue
        if target not in {"3ds", "windows", "idtech2"}:
            raise ValueError(f"Unsupported build target: {target}")
        if target not in ordered:
            ordered.append(target)
    return ordered


def build_playable_targets(targets: list[str], config: str, *, env: dict[str, str]) -> dict:
    if not targets:
        return {"status": "skipped", "reason": "no_targets_requested"}
    return run_powershell_script(
        TOOLS_ROOT / "build-all-platforms.ps1",
        ["-Targets", ",".join(targets), "-Config", config],
        env=env,
    )


def deploy_idtech2_module(mod_name: str, *, env: dict[str, str]) -> dict:
    q2_env = TOOLS_ROOT / "q2sdk-env.ps1"
    deploy_script = TOOLS_ROOT / "bango-idtech2-deploy.ps1"
    command_text = f"& {{ . '{q2_env}'; & '{deploy_script}' -ModName '{mod_name}'; exit $LASTEXITCODE }}"
    return run_powershell_command(command_text, env=env)


def artifact_inventory() -> dict[str, dict[str, object]]:
    return {
        "3dsx": {
            "source": ROOT / "BangoPatoot.3dsx",
            "relative_dest": Path("platforms") / "3ds" / "BangoPatoot.3dsx",
            "platform": "3ds",
        },
        "elf": {
            "source": ROOT / "BangoPatoot.elf",
            "relative_dest": Path("platforms") / "3ds" / "BangoPatoot.elf",
            "platform": "3ds",
        },
        "windows_preview": {
            "source": ROOT / "BangoPatootWindowsPreview.exe",
            "relative_dest": Path("platforms") / "windows" / "BangoPatootWindowsPreview.exe",
            "platform": "windows",
        },
        "idtech2_module": {
            "source": ROOT / "idtech2_mod" / "build" / "real-q2" / "game.dll",
            "relative_dest": Path("platforms") / "idtech2" / "game.dll",
            "platform": "idtech2",
        },
        "dodo_windows_bundle": {
            "source": DOENGINE_ROOT / "generated" / "windows_bundle",
            "relative_dest": Path("platforms") / "windows_engine" / "DODOGameBundle",
            "platform": "windows",
        },
        "orb_tutorial_demo": {
            "source": ORBENGINE_ROOT / "bango_unchained_bangopatoot_demo.exe",
            "relative_dest": Path("platforms") / "windows_engine" / "bango_unchained_bangopatoot_demo.exe",
            "platform": "windows",
        },
    }


def stage_path(source: Path, destination: Path) -> bool:
    if not source.exists():
        return False
    if source.is_dir():
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination)
        return True
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return True


def stage_playable_package(asset_root: Path, summary_path: Path, summary: dict, build_targets: list[str], build_result: dict, deploy_result: dict | None) -> dict:
    package_dir = asset_root / "generated" / "bangonow" / "playable_package"
    package_dir.mkdir(parents=True, exist_ok=True)

    staged_artifacts: dict[str, dict[str, object]] = {}
    for name, metadata in artifact_inventory().items():
        source = metadata["source"]
        destination = package_dir / metadata["relative_dest"]
        exists = stage_path(source, destination)
        staged_artifacts[name] = {
            "platform": metadata["platform"],
            "source": str(source),
            "staged_path": str(destination),
            "exists": exists,
        }

    staged_files = {
        "summary": {
            "source": str(summary_path),
            "staged_path": str(package_dir / "manifests" / summary_path.name),
        },
        "playnow_runtime": {
            "source": str(asset_root / "generated" / "playnow" / "playnow_runtime_manifest.json"),
            "staged_path": str(package_dir / "manifests" / "playnow_runtime_manifest.json"),
        },
        "playnow_finalstage": {
            "source": str(asset_root / "generated" / "playnow" / "playnow_finalstage_manifest.json"),
            "staged_path": str(package_dir / "manifests" / "playnow_finalstage_manifest.json"),
        },
        "doengine_hybrid_runtime": {
            "source": str(DOENGINE_ROOT / "generated" / "dodogame_hybrid_runtime.json"),
            "staged_path": str(package_dir / "manifests" / "dodogame_hybrid_runtime.json"),
        },
        "dodogame_windows_bundle": {
            "source": str(DOENGINE_ROOT / "generated" / "windows_bundle" / "dodogame_windows_bundle.json"),
            "staged_path": str(package_dir / "manifests" / "dodogame_windows_bundle.json"),
        },
    }

    for entry in staged_files.values():
        source = Path(entry["source"])
        destination = Path(entry["staged_path"])
        entry["exists"] = stage_path(source, destination)

    for pass_name, pass_data in summary.get("runs", {}).items():
        if not isinstance(pass_data, dict):
            continue
        manifest_path = pass_data.get("path") or pass_data.get("runtime_manifest") or pass_data.get("pass_manifest")
        if not manifest_path:
            continue
        source = Path(manifest_path)
        if not source.exists():
            continue
        destination = package_dir / "passes" / source.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    package_manifest = {
        "system": "BangoNOW",
        "asset_root": str(asset_root),
        "package_root": str(package_dir),
        "selected_build_targets": build_targets,
        "requested_passes": [name for name in ("humble", "combat16", "tutorial32", "tutorial_final_preview") if name in summary.get("runs", {}) or f"{name}_playnow" in summary.get("runs", {})],
        "build": build_result,
        "deploy": deploy_result,
        "artifacts": staged_artifacts,
        "manifests": staged_files,
        "playable_ready": all(
            staged_artifacts[name]["exists"]
            for name, metadata in artifact_inventory().items()
            if metadata["platform"] in build_targets
        ),
    }
    package_manifest_path = package_dir / "bangonow_playable_package.json"
    save_json(package_manifest_path, package_manifest)
    return {"path": str(package_manifest_path), **package_manifest}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run BangoNOW full batch/integration orchestration")
    parser.add_argument("--asset-root", type=Path)
    parser.add_argument("--humble-limit", type=int, default=4)
    parser.add_argument("--skip-humble", action="store_true")
    parser.add_argument("--skip-combat16", action="store_true")
    parser.add_argument("--skip-tutorial32", action="store_true")
    parser.add_argument("--skip-tutorial-duology-8000", action="store_true")
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--skip-package", action="store_true")
    parser.add_argument("--build-targets", type=str, default="all")
    parser.add_argument("--build-config", type=str, default="Release")
    parser.add_argument("--deploy-idtech2", action="store_true")
    parser.add_argument("--idtech2-mod-name", type=str, default="bango")
    args = parser.parse_args()

    asset_root = args.asset_root.resolve() if args.asset_root else resolve_asset_root(ROOT)
    asset_root.mkdir(parents=True, exist_ok=True)
    env = build_runtime_env(asset_root)
    build_targets = parse_targets(args.build_targets)

    summary: dict[str, object] = {"asset_root": str(asset_root), "runs": {}}

    if not args.skip_humble:
        humble_command = [
            sys.executable,
            str(ROOT / "tools" / "run_bango_clip_blend_id_pipeline.py"),
            "--run-recraft",
            "--run-polish",
            "--limit",
            str(args.humble_limit),
        ]
        summary["runs"]["humble"] = run_command(humble_command, env=env)
        humble_manifest = ROOT / "recraft" / "bango_patoot_production_21000_credit_manifest.json"
        summary["runs"]["humble_playnow"] = run_playnow(asset_root, "humble", humble_manifest)

    if not args.skip_combat16:
        combat_manifest_path, combat_manifest = build_combat16_manifest(asset_root)
        summary["runs"]["combat16_manifest"] = {"path": str(combat_manifest_path), "asset_count": len(combat_manifest["assets"])}
        summary["runs"]["combat16"] = run_command([sys.executable, str(WORKSPACE_ROOT / "egosphere" / "tools" / "run_recraft_manifest.py"), str(combat_manifest_path)], env=env)
        summary["runs"]["combat16_polish"] = run_polish(
            asset_root / "production_raw" / "bangonow" / "combat16",
            asset_root / "production_polished" / "bangonow" / "combat16",
            env=env,
        )
        summary["runs"]["combat16_playnow"] = run_playnow(asset_root, "combat16", combat_manifest_path)

    if not args.skip_tutorial32:
        tutorial_manifest_path, tutorial_manifest = build_tutorial32_manifest(asset_root)
        summary["runs"]["tutorial32_manifest"] = {"path": str(tutorial_manifest_path), "asset_count": len(tutorial_manifest["assets"])}
        summary["runs"]["tutorial32"] = run_command([sys.executable, str(WORKSPACE_ROOT / "egosphere" / "tools" / "run_recraft_manifest.py"), str(tutorial_manifest_path)], env=env)
        summary["runs"]["tutorial32_polish"] = run_polish(
            asset_root / "production_raw" / "bangonow" / "tutorial32",
            asset_root / "production_polished" / "bangonow" / "tutorial32",
            env=env,
        )
        summary["runs"]["tutorial32_playnow"] = run_playnow(asset_root, "tutorial32", tutorial_manifest_path)

    if not args.skip_tutorial_duology_8000:
        tutorial_duology_manifest_path, tutorial_duology_manifest = build_tutorial_duology_8000_manifest(asset_root)
        summary["runs"]["tutorial_duology_8000_manifest"] = {"path": str(tutorial_duology_manifest_path), "asset_count": len(tutorial_duology_manifest["assets"]), "budget": tutorial_duology_manifest.get("budget")}
        summary["runs"]["tutorial_final_preview"] = run_command([sys.executable, str(WORKSPACE_ROOT / "egosphere" / "tools" / "run_recraft_manifest.py"), str(tutorial_duology_manifest_path)], env=env)
        summary["runs"]["tutorial_final_preview_polish"] = run_polish(
            asset_root / "production_raw" / "bangonow" / "tutorial_duology_8000",
            asset_root / "production_polished" / "bangonow" / "tutorial_duology_8000",
            env=env,
        )
        summary["runs"]["tutorial_final_preview_playnow"] = run_playnow(asset_root, "tutorial_final_preview", tutorial_duology_manifest_path)

    summary["runs"]["dodoplaynow"] = run_playnow(asset_root, "dodogame", skip_autorig=True)
    summary["runs"]["doengine_hybrid_runtime"] = build_doengine_hybrid_runtime(asset_root, env=env)
    summary["runs"]["orb_tutorial_demo_build"] = build_orb_tutorial_demo(env=env)

    if args.skip_build:
        summary["runs"]["playable_build"] = {"status": "skipped", "reason": "skip_build_requested", "targets": build_targets}
    else:
        summary["runs"]["playable_build"] = build_playable_targets(build_targets, args.build_config, env=env)

    summary["runs"]["dodo_windows_bundle"] = build_dodo_windows_bundle(asset_root, env=env)

    deploy_result: dict[str, object] | None = None
    if args.deploy_idtech2:
        deploy_result = deploy_idtech2_module(args.idtech2_mod_name, env=env)
        summary["runs"]["idtech2_deploy"] = deploy_result

    summary_path = asset_root / "generated" / "bangonow" / "bangonow_run_summary.json"

    if args.skip_package:
        summary["runs"]["playable_package"] = {"status": "skipped", "reason": "skip_package_requested"}
    else:
        summary["runs"]["playable_package"] = stage_playable_package(
            asset_root,
            summary_path,
            summary,
            build_targets,
            summary["runs"]["playable_build"],
            deploy_result,
        )

    save_json(summary_path, summary)

    if not args.skip_package:
        staged_summary_path = Path(summary["runs"]["playable_package"]["manifests"]["summary"]["staged_path"])
        save_json(staged_summary_path, summary)
        summary["runs"]["playable_package"]["manifests"]["summary"]["exists"] = True
        package_manifest_path = Path(summary["runs"]["playable_package"]["path"])
        save_json(package_manifest_path, summary["runs"]["playable_package"])

    print(json.dumps({"summary": str(summary_path), **summary}, indent=2))

    run_statuses = [entry.get("returncode", 0) for entry in summary["runs"].values() if isinstance(entry, dict) and "returncode" in entry]
    return max(run_statuses, default=0)


if __name__ == "__main__":
    raise SystemExit(main())