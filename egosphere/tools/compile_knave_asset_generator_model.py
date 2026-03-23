import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT / "pipeline" / "projects" / "knave_prototype"
PROFILE_PATH = PROJECT_ROOT / "knave_asset_advancement_profile.json"
MODEL_PATH = PROJECT_ROOT / "knave_asset_generator_model.json"
GAME_PROJECT_PATH = PROJECT_ROOT / "game_project.json"
NOTES_PATH = PROJECT_ROOT / "KNAVE_PIPELINE_NOTES.md"


ADVANCEMENT_AXES = [
    {
        "name": "silhouette_readability",
        "baseline": "single-weight medieval action silhouettes with limited faction distinction",
        "advanced": "hero, rival, elite, and boss silhouettes that read immediately at gameplay scale with asymmetry and role-specific profile breaks",
        "mutation_bias": "shape_language",
    },
    {
        "name": "material_storytelling",
        "baseline": "flat armor and cloth treatment with sparse surface storytelling",
        "advanced": "layered materials that signal rank, weathering, ritual use, and combat history without collapsing readability",
        "mutation_bias": "surface_memory",
    },
    {
        "name": "animation_density",
        "baseline": "limited idle, move, attack, and hit coverage",
        "advanced": "expanded anticipation, follow-through, guard states, finishers, and combat recovery frames with clean timing bands",
        "mutation_bias": "motion_clarity",
    },
    {
        "name": "environment_depth",
        "baseline": "single-plane combat spaces and low parallax contrast",
        "advanced": "foreground-midground-backdrop separation with traversal cues, light wells, and combat readability lanes",
        "mutation_bias": "spatial_stack",
    },
    {
        "name": "fx_legibility",
        "baseline": "generic flashes and trails with little combat taxonomy",
        "advanced": "distinct weapon, spell, guard-break, and finisher FX families that communicate outcome before impact resolves",
        "mutation_bias": "signal_intensity",
    },
    {
        "name": "ui_authorship",
        "baseline": "functional dark-fantasy interface motifs",
        "advanced": "premium interface systems with authored hierarchy, diegetic ornament restraint, and clean command-state separation",
        "mutation_bias": "ux_cadence",
    },
]


ASSET_BLUEPRINTS = [
    {
        "id": "knave_player_turnaround",
        "category": "character",
        "usage": "player",
        "output": "authoring/clipstudio/sprites/knave_player_turnaround.png",
        "planned_credits": 100,
        "dimensions": [1024, 1024],
        "component_tags": ["hero", "turnaround", "armor", "cloth"],
        "baseline_focus": ["silhouette_readability", "material_storytelling"],
        "advanced_focus": ["silhouette_readability", "material_storytelling", "ui_authorship"],
        "role_prompt": "original dark-fantasy knave hero turnaround board with front, side, rear, and three-quarter pose coverage for premium production art",
    },
    {
        "id": "knave_player_motion_suite",
        "category": "character",
        "usage": "player",
        "output": "authoring/clipstudio/sprites/knave_player_motion_suite.png",
        "planned_credits": 100,
        "dimensions": [1024, 512],
        "component_tags": ["hero", "movement", "combat", "animation"],
        "baseline_focus": ["animation_density"],
        "advanced_focus": ["animation_density", "silhouette_readability"],
        "role_prompt": "original premium action spritesheet panel for a knave protagonist covering idle, walk, sprint, dodge, leap, and recovery beats",
    },
    {
        "id": "knave_player_guard_suite",
        "category": "character",
        "usage": "player",
        "output": "authoring/clipstudio/sprites/knave_player_guard_suite.png",
        "planned_credits": 100,
        "dimensions": [1024, 512],
        "component_tags": ["hero", "guard", "parry", "stance"],
        "baseline_focus": ["animation_density", "fx_legibility"],
        "advanced_focus": ["animation_density", "fx_legibility", "material_storytelling"],
        "role_prompt": "original combat guard and parry suite for a knave action hero with premium stance readability and authored impact anticipation",
    },
    {
        "id": "knave_player_finisher_suite",
        "category": "character",
        "usage": "player",
        "output": "authoring/clipstudio/sprites/knave_player_finisher_suite.png",
        "planned_credits": 100,
        "dimensions": [1024, 512],
        "component_tags": ["hero", "finisher", "cinematic", "combat"],
        "baseline_focus": ["animation_density", "fx_legibility"],
        "advanced_focus": ["animation_density", "fx_legibility", "environment_depth"],
        "role_prompt": "original premium finisher sequence panel for a knave action hero with dramatic but gameplay-readable combat staging",
    },
    {
        "id": "knave_enemy_duelist_sheet",
        "category": "character",
        "usage": "enemy",
        "output": "authoring/clipstudio/sprites/knave_enemy_duelist_sheet.png",
        "planned_credits": 100,
        "dimensions": [1024, 512],
        "component_tags": ["enemy", "duelist", "elite"],
        "baseline_focus": ["silhouette_readability"],
        "advanced_focus": ["silhouette_readability", "animation_density"],
        "role_prompt": "original elite duelist enemy sheet for a premium knave prototype with stance-driven attack language and authored faction silhouette",
    },
    {
        "id": "knave_enemy_lancer_sheet",
        "category": "character",
        "usage": "enemy",
        "output": "authoring/clipstudio/sprites/knave_enemy_lancer_sheet.png",
        "planned_credits": 100,
        "dimensions": [1024, 512],
        "component_tags": ["enemy", "lancer", "reach"],
        "baseline_focus": ["silhouette_readability", "animation_density"],
        "advanced_focus": ["silhouette_readability", "animation_density", "material_storytelling"],
        "role_prompt": "original long-reach lancer enemy sheet for a knave prototype, tuned for distance pressure and clear attack telegraphing",
    },
    {
        "id": "knave_enemy_hexcaster_sheet",
        "category": "character",
        "usage": "enemy",
        "output": "authoring/clipstudio/sprites/knave_enemy_hexcaster_sheet.png",
        "planned_credits": 100,
        "dimensions": [1024, 512],
        "component_tags": ["enemy", "caster", "ritual"],
        "baseline_focus": ["fx_legibility"],
        "advanced_focus": ["fx_legibility", "silhouette_readability", "material_storytelling"],
        "role_prompt": "original ritual hexcaster enemy sheet for a premium knave build with readable spell silhouettes and authored casting posture",
    },
    {
        "id": "knave_enemy_bulwark_sheet",
        "category": "character",
        "usage": "enemy",
        "output": "authoring/clipstudio/sprites/knave_enemy_bulwark_sheet.png",
        "planned_credits": 100,
        "dimensions": [1024, 512],
        "component_tags": ["enemy", "bulwark", "heavy"],
        "baseline_focus": ["material_storytelling"],
        "advanced_focus": ["material_storytelling", "silhouette_readability", "animation_density"],
        "role_prompt": "original heavy bulwark enemy sheet for a knave prototype with weighty armor storytelling and readable shield mechanics",
    },
    {
        "id": "knave_boss_regent_sheet",
        "category": "character",
        "usage": "boss",
        "output": "authoring/clipstudio/sprites/knave_boss_regent_sheet.png",
        "planned_credits": 100,
        "dimensions": [1536, 768],
        "component_tags": ["boss", "regent", "phase"],
        "baseline_focus": ["silhouette_readability", "material_storytelling"],
        "advanced_focus": ["silhouette_readability", "material_storytelling", "animation_density", "fx_legibility"],
        "role_prompt": "original premium boss key sheet for a knave regent antagonist with multi-phase posture changes and prestige encounter authorship",
    },
    {
        "id": "knave_companion_sheet",
        "category": "character",
        "usage": "ally",
        "output": "authoring/clipstudio/sprites/knave_companion_sheet.png",
        "planned_credits": 100,
        "dimensions": [1024, 512],
        "component_tags": ["ally", "companion", "ranger"],
        "baseline_focus": ["silhouette_readability"],
        "advanced_focus": ["silhouette_readability", "material_storytelling", "animation_density"],
        "role_prompt": "original ally companion sheet for a knave prototype, with premium support-readability and ranged traversal personality",
    },
    {
        "id": "knave_rival_huntress_sheet",
        "category": "character",
        "usage": "rival",
        "output": "authoring/clipstudio/sprites/knave_rival_huntress_sheet.png",
        "planned_credits": 100,
        "dimensions": [1024, 512],
        "component_tags": ["rival", "hunter", "pursuer"],
        "baseline_focus": ["silhouette_readability", "animation_density"],
        "advanced_focus": ["silhouette_readability", "animation_density", "material_storytelling"],
        "role_prompt": "original rival huntress sheet for a knave prototype with a distinctive pursuit identity, pursuit stance, and authored duel language",
    },
    {
        "id": "knave_ui_hud_suite",
        "category": "ui",
        "usage": "ui",
        "output": "authoring/clipstudio/sprites/knave_ui_hud_suite.png",
        "planned_credits": 100,
        "dimensions": [1024, 512],
        "component_tags": ["ui", "hud", "status"],
        "baseline_focus": ["ui_authorship"],
        "advanced_focus": ["ui_authorship", "fx_legibility"],
        "role_prompt": "original premium HUD suite for a dark-fantasy knave action game with crystal-clear status hierarchy and restrained ornament",
    },
    {
        "id": "knave_fx_weapon_suite",
        "category": "fx",
        "usage": "fx",
        "output": "authoring/clipstudio/sprites/knave_fx_weapon_suite.png",
        "planned_credits": 100,
        "dimensions": [1024, 512],
        "component_tags": ["fx", "weapon", "impact"],
        "baseline_focus": ["fx_legibility"],
        "advanced_focus": ["fx_legibility", "animation_density"],
        "role_prompt": "original premium weapon FX suite for a knave prototype covering slashes, guard sparks, break impacts, and finisher bursts",
    },
    {
        "id": "knave_fx_magic_suite",
        "category": "fx",
        "usage": "fx",
        "output": "authoring/clipstudio/sprites/knave_fx_magic_suite.png",
        "planned_credits": 100,
        "dimensions": [1024, 512],
        "component_tags": ["fx", "magic", "ritual"],
        "baseline_focus": ["fx_legibility"],
        "advanced_focus": ["fx_legibility", "environment_depth"],
        "role_prompt": "original premium ritual and spell FX suite for a knave prototype with authored shapes for curse, ward, and burst effects",
    },
    {
        "id": "knave_keep_tiles_sheet",
        "category": "environment",
        "usage": "tileset",
        "output": "authoring/clipstudio/tiles/knave_keep_tiles_sheet.png",
        "planned_credits": 100,
        "dimensions": [1024, 1024],
        "component_tags": ["environment", "keep", "stone"],
        "baseline_focus": ["environment_depth"],
        "advanced_focus": ["environment_depth", "material_storytelling"],
        "role_prompt": "original premium keep tileset sheet for a knave prototype with authored traversal reads, combat lanes, and stonewear storytelling",
    },
    {
        "id": "knave_crypt_tiles_sheet",
        "category": "environment",
        "usage": "tileset",
        "output": "authoring/clipstudio/tiles/knave_crypt_tiles_sheet.png",
        "planned_credits": 100,
        "dimensions": [1024, 1024],
        "component_tags": ["environment", "crypt", "burial"],
        "baseline_focus": ["environment_depth", "material_storytelling"],
        "advanced_focus": ["environment_depth", "material_storytelling", "fx_legibility"],
        "role_prompt": "original premium crypt tileset sheet for a knave prototype with layered gloom, readable pathing, and burial-rite environmental storytelling",
    },
    {
        "id": "knave_forest_tiles_sheet",
        "category": "environment",
        "usage": "tileset",
        "output": "authoring/clipstudio/tiles/knave_forest_tiles_sheet.png",
        "planned_credits": 100,
        "dimensions": [1024, 1024],
        "component_tags": ["environment", "forest", "ruin"],
        "baseline_focus": ["environment_depth"],
        "advanced_focus": ["environment_depth", "silhouette_readability", "material_storytelling"],
        "role_prompt": "original premium ruined forest tileset sheet for a knave prototype with traversal wayfinding, light wells, and combat silhouette support",
    },
    {
        "id": "knave_companion_portrait",
        "category": "portrait",
        "usage": "portrait",
        "output": "authoring/clipstudio/portraits/knave_companion_portrait.png",
        "planned_credits": 100,
        "dimensions": [1024, 1024],
        "component_tags": ["portrait", "ally", "dialogue"],
        "baseline_focus": ["material_storytelling"],
        "advanced_focus": ["material_storytelling", "silhouette_readability"],
        "role_prompt": "original premium dialogue portrait of the knave companion with expressive but production-safe dark-fantasy authorship",
    },
    {
        "id": "knave_rival_portrait",
        "category": "portrait",
        "usage": "portrait",
        "output": "authoring/clipstudio/portraits/knave_rival_portrait.png",
        "planned_credits": 100,
        "dimensions": [1024, 1024],
        "component_tags": ["portrait", "rival", "dialogue"],
        "baseline_focus": ["material_storytelling", "silhouette_readability"],
        "advanced_focus": ["material_storytelling", "silhouette_readability", "ui_authorship"],
        "role_prompt": "original premium dialogue portrait of the knave rival huntress with authored tension and prestige production finish",
    },
    {
        "id": "knave_keyart_panel",
        "category": "cinematic",
        "usage": "cinematic",
        "output": "authoring/clipstudio/sprites/knave_keyart_panel.png",
        "planned_credits": 100,
        "dimensions": [1536, 1024],
        "component_tags": ["keyart", "cinematic", "marketing"],
        "baseline_focus": ["environment_depth", "material_storytelling"],
        "advanced_focus": ["environment_depth", "material_storytelling", "silhouette_readability", "ui_authorship"],
        "role_prompt": "original premium key art panel for a knave prototype showing hero, rival, and boss pressure in a traversal-aware dark-fantasy composition",
    },
]


COMMON_APPENDIX = (
    "Design intent: original premium dark-fantasy action asset for a knave prototype, not derivative of any specific existing title, "
    "favor authored silhouettes, premium production finish, gameplay readability, restrained ornament, and worldbuilding continuity."
)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def axis_by_name(name: str) -> dict:
    for axis in ADVANCEMENT_AXES:
        if axis["name"] == name:
            return axis
    raise KeyError(name)


def compile_prompt(blueprint: dict) -> str:
    baseline = [axis_by_name(name)["baseline"] for name in blueprint["baseline_focus"]]
    advanced = [axis_by_name(name)["advanced"] for name in blueprint["advanced_focus"]]
    tags = ", ".join(blueprint["component_tags"])
    return (
        f"{blueprint['role_prompt']}, component tags: {tags}, baseline profile: {'; '.join(baseline)}, "
        f"advancement profile: {'; '.join(advanced)}, {COMMON_APPENDIX}"
    )


def compile_designer_component(blueprint: dict) -> dict:
    mutation_axes = [axis_by_name(name)["mutation_bias"] for name in blueprint["advanced_focus"]]
    progression_score = len(blueprint["advanced_focus"]) / max(1, len(ADVANCEMENT_AXES))
    godai_weights = {
        "pressure": round(0.85 + progression_score * 0.3, 3),
        "mercy": round(1.15 - progression_score * 0.2, 3),
        "novelty": round(1.0 + progression_score * 0.25, 3),
    }
    return {
        "asset_id": blueprint["id"],
        "category": blueprint["category"],
        "usage": blueprint["usage"],
        "output": blueprint["output"],
        "planned_credits": blueprint["planned_credits"],
        "dimensions": blueprint["dimensions"],
        "component_tags": blueprint["component_tags"],
        "compiled_prompt": compile_prompt(blueprint),
        "mutation_axes": mutation_axes,
        "progression_score": round(progression_score, 3),
        "baseline_axes": blueprint["baseline_focus"],
        "advanced_axes": blueprint["advanced_focus"],
        "godai_weights": godai_weights,
        "evolution_hooks": {
            "early_pass": blueprint["baseline_focus"],
            "late_pass": blueprint["advanced_focus"],
            "stability_rule": "never sacrifice silhouette readability for ornament",
        },
    }


def build_advancement_profile() -> dict:
    return {
        "project_name": "KnavePrototype",
        "profile_version": "2026-03-15.knave.advance.v1",
        "baseline_profile_name": "knave_general_profile",
        "advanced_profile_name": "knave_advanced_profile",
        "axes": ADVANCEMENT_AXES,
        "non_copying_rule": "Use original authored combinations and generalized advancement deltas only. Do not directly imitate or reproduce any prior asset set.",
        "advancement_summary": {
            "from": "functional readable dark-fantasy asset language",
            "to": "premium authored asset language with expanded motion, richer materials, clearer combat taxonomy, and stronger environmental depth",
        },
    }


def build_game_project(components: list[dict]) -> dict:
    sprite_assets = []
    tile_assets = []
    portrait_assets = []
    for component in components:
        asset = {
            "id": component["asset_id"],
            "path": component["output"],
            "usage": component["usage"],
            "material_profile": "default_sprite_material",
            "generator_component": component["component_tags"],
        }
        if component["category"] == "environment":
            asset["tile_w"] = 64
            asset["tile_h"] = 64
            asset["semantic_tags"] = component["component_tags"]
            asset["material_profile"] = "terrain_story_material"
            tile_assets.append(asset)
        elif component["category"] == "portrait":
            asset["precache"] = False
            portrait_assets.append(asset)
        else:
            asset["frames"] = 8 if component["category"] != "boss" else 12
            asset["collider"] = {"shape": "capsule", "radius": 0.3, "height": 1.7}
            if component["usage"] == "fx":
                asset["collider"] = {"shape": "sphere", "radius": 0.05, "height": 0.05}
                asset["material_profile"] = "spell_signal_material"
            elif component["usage"] == "ui":
                asset["material_profile"] = "ui_inkglass_material"
            elif component["usage"] == "boss":
                asset["material_profile"] = "boss_regalia_material"
            sprite_assets.append(asset)

    return {
        "project_name": "KnavePrototype",
        "seed": "KNAVE-PROTOTYPE-ADV-20260315",
        "integrations": {
            "godai": {
                "mode": "asset_direction_conductor",
                "difficulty_floor": 0.92,
                "difficulty_ceiling": 1.42,
                "designer_bias": "premium original dark-fantasy readability",
                "evolution_targets": [axis["name"] for axis in ADVANCEMENT_AXES],
            }
        },
        "authoring": {
            "clipstudio": {
                "canvas": {"width": 4096, "height": 4096, "layers": 18},
                "timeline_fps": 12,
                "export_profile": {"color_mode": "rgba", "naming": "asset_id", "slice_method": "layer_group"},
                "layers": [
                    {"name": "bg_depth", "blend_mode": "normal", "visible": True},
                    {"name": "characters", "blend_mode": "normal", "visible": True},
                    {"name": "fx", "blend_mode": "screen", "visible": True},
                    {"name": "ui", "blend_mode": "normal", "visible": True},
                    {"name": "collision_guides", "blend_mode": "multiply", "visible": False},
                ],
                "script_symbols": ["KnaveSpawn", "RivalGate", "BossThreshold", "GodAIConductorAnchor"],
                "symbol_bindings": [
                    {"symbol": "KnaveSpawn", "asset_id": "knave_player_turnaround", "role": "player_spawn"},
                    {"symbol": "RivalGate", "asset_id": "knave_rival_huntress_sheet", "role": "rival_encounter"},
                    {"symbol": "BossThreshold", "asset_id": "knave_boss_regent_sheet", "role": "boss_encounter"},
                    {"symbol": "GodAIConductorAnchor", "asset_id": "knave_keyart_panel", "role": "godai_style_anchor"},
                ],
                "frame_tags": [
                    {"tag": "keep_entry", "frame": 0, "scene_id": "ruined_keep_entry"},
                    {"tag": "crypt_descent", "frame": 36, "scene_id": "burial_crypt_descent"},
                ],
                "hitboxes": [
                    {"symbol": "KnaveSpawn", "frame": 0, "x": 10, "y": 8, "w": 28, "h": 44, "kind": "hurtbox"},
                    {"symbol": "BossThreshold", "frame": 0, "x": 0, "y": 0, "w": 64, "h": 96, "kind": "trigger"},
                ],
                "script_bindings": [
                    {"name": "begin_keep_pressure", "event": "room_enter", "target_symbol": "GodAIConductorAnchor", "command": "evaluate_asset_pressure:ruined_keep_entry"},
                    {"name": "spawn_rival", "event": "rival_intro", "target_symbol": "RivalGate", "command": "open_encounter:knave_rival_huntress"},
                ],
            },
            "blender": {
                "scale": 0.1,
                "extrusion_depth": 0.1,
                "rig_profile": "paperdoll_humanoid",
                "material_profiles": [
                    {"name": "default_sprite_material", "shader": "toon_principled", "roughness": 0.7, "normal_strength": 0.18},
                    {"name": "terrain_story_material", "shader": "trim_sheet", "roughness": 0.62, "normal_strength": 0.3},
                    {"name": "spell_signal_material", "shader": "emissive_layered", "roughness": 0.2, "normal_strength": 0.1},
                    {"name": "ui_inkglass_material", "shader": "flat_glass", "roughness": 0.15, "normal_strength": 0.0},
                    {"name": "boss_regalia_material", "shader": "toon_principled", "roughness": 0.55, "normal_strength": 0.28},
                ],
                "rig_overrides": [
                    {"asset_id": "knave_player_motion_suite", "armature": "knave_hero", "root_bone": "hips"},
                    {"asset_id": "knave_boss_regent_sheet", "armature": "knave_boss", "root_bone": "pelvis"},
                ],
                "nodecraft_graphs": [
                    {
                        "name": "knave_world_stack",
                        "nodes": [
                            {"id": "foreground", "position": [0.0, 0.0, 0.0], "scale": 1.0},
                            {"id": "midground", "position": [8.0, 0.0, -2.0], "scale": 1.0},
                            {"id": "backdrop", "position": [16.0, 0.0, -5.0], "scale": 1.0},
                        ],
                        "links": [
                            {"from": "foreground", "to": "midground", "type": "LINKAGE_CHAIN", "thickness": 0.4},
                            {"from": "midground", "to": "backdrop", "type": "LINKAGE_LATTICE", "thickness": 0.3},
                        ],
                    }
                ],
                "scene_build": [
                    {"scene_id": "ruined_keep_entry", "collection": "keep", "world_mesh": "knave_keep_mesh"},
                    {"scene_id": "burial_crypt_descent", "collection": "crypt", "world_mesh": "knave_crypt_mesh"},
                    {"scene_id": "forest_of_oaths", "collection": "forest", "world_mesh": "knave_forest_mesh"},
                ],
            },
            "idtech2": {
                "module_name": "g_knaveprototype",
                "asset_root": "baseq2/knaveprototype",
                "autofactor_prefix": "knaveproto",
                "precache_groups": [
                    {
                        "group_name": "sound",
                        "entries": [
                            {"alias": "knave_guard_ping", "path": "sound/knaveproto/guard_ping.wav", "asset_type": "sound"},
                            {"alias": "knave_regent_roar", "path": "sound/knaveproto/regent_roar.wav", "asset_type": "sound"},
                        ],
                    }
                ],
                "system_dispatch": {
                    "knave_combat_system": {"init_fn": "knave_combat_init", "tick_fn": "knave_combat_tick"},
                    "knave_rival_system": {"init_fn": "knave_rival_init", "tick_fn": "knave_rival_tick"},
                    "knave_godai_system": {"init_fn": "knave_godai_init", "tick_fn": "knave_godai_tick"},
                },
                "bootstrap": {"entry_scene": "ruined_keep_entry", "precache_phase": "game_init", "spawn_phase": "level_load"},
            },
        },
        "assets": {
            "tilesets": tile_assets,
            "sprites": sprite_assets,
            "portraits": portrait_assets,
        },
        "gameplay": {
            "scenes": [
                {"id": "ruined_keep_entry", "scene_type": "exploration", "location": "knave_keep", "timeline_frames": [0, 48], "triggers": [{"id": "rival_intro", "frame": 12, "event": "rival_intro", "target": "knave_rival"}]},
                {"id": "burial_crypt_descent", "scene_type": "combat", "location": "knave_crypt", "timeline_frames": [49, 96], "triggers": [{"id": "boss_gate", "frame": 70, "event": "boss_intro", "target": "knave_regent"}]},
                {"id": "forest_of_oaths", "scene_type": "exploration", "location": "knave_forest", "timeline_frames": [97, 144], "triggers": [{"id": "godai_rebalance", "frame": 120, "event": "room_enter", "target": "knave_player"}]},
            ],
            "entities": [
                {"id": "knave_player", "classname": "knave_player", "asset_id": "knave_player_motion_suite", "spawn": [128, 80, 0], "logic_components": ["controllable", "stamina", "godai_subject"]},
                {"id": "knave_rival", "classname": "knave_rival", "asset_id": "knave_rival_huntress_sheet", "spawn": [640, 84, 0], "logic_components": ["duelist_ai", "rival_tracker"]},
                {"id": "knave_regent", "classname": "knave_regent", "asset_id": "knave_boss_regent_sheet", "spawn": [1280, 96, 0], "logic_components": ["boss_logic", "phase_controller", "godai_pressure_anchor"]},
            ],
            "systems": [
                {"name": "knave_combat_system", "priority": 10, "lifecycle": ["init", "tick", "shutdown"]},
                {"name": "knave_rival_system", "priority": 20, "lifecycle": ["init", "tick"]},
                {"name": "knave_godai_system", "priority": 30, "lifecycle": ["init", "tick"]},
            ],
        },
        "targets": {"clipstudio_bundle": "clipstudio_bundle", "blender_bundle": "blender_bundle", "idtech2_bundle": "idtech2_bundle"},
    }


def build_model(profile: dict, components: list[dict]) -> dict:
    return {
        "project_name": "KnavePrototype",
        "model_name": "AssetGeneratorDesignerImageCompiler",
        "model_version": "2026-03-15.knave.compiler.v1",
        "profile": profile,
        "designer_components": components,
        "realtime_evolution_profile": {
            "state_inputs": [
                "godai_pressure",
                "novelty_score",
                "material_entropy",
                "motion_density",
                "ui_clarity_index",
            ],
            "mutation_policy": {
                "promote": ["silhouette_readability", "animation_density", "environment_depth"],
                "stabilize": ["ui_authorship", "material_storytelling"],
                "forbid": ["direct_style_copying", "ornament_over_readability"],
            },
            "convergence_rule": "advance premium authorship while preserving gameplay legibility and original visual language",
        },
        "godai_integration": {
            "conductor": "symbolic_godai_asset_direction",
            "omens": ["steady hush", "predator surge", "mercy drift", "regal eclipse"],
            "pressure_bands": [0.92, 1.0, 1.18, 1.35],
            "designer_bias": "original triple-A-target dark-fantasy asset authorship",
        },
    }


def write_notes(profile: dict, model: dict) -> None:
    lines = [
        "# Knave Prototype Asset Generator Notes",
        "",
        "This project was created because no direct `Knave_prototype` or `Asset Generator` source tree existed in the workspace.",
        "The pipeline therefore defines an explicit baseline profile, an advanced delta profile, and a symbolic godAI-driven evolution model.",
        "",
        "## Advancement Axes",
    ]
    for axis in profile["axes"]:
        lines.append(f"- {axis['name']}: {axis['advanced']}")
    lines.extend([
        "",
        "## Model Intent",
        "- Compile designer-image components into Recraft-ready prompts.",
        "- Preserve original authorship and prohibit direct copying.",
        "- Use godAI pressure/mercy/novelty weights to guide real-time evolution decisions.",
        f"- Component count: {len(model['designer_components'])}",
        "",
    ])
    NOTES_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ensure_dir(PROJECT_ROOT)
    components = [compile_designer_component(blueprint) for blueprint in ASSET_BLUEPRINTS]
    profile = build_advancement_profile()
    model = build_model(profile, components)
    game_project = build_game_project(components)

    PROFILE_PATH.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    MODEL_PATH.write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")
    GAME_PROJECT_PATH.write_text(json.dumps(game_project, indent=2) + "\n", encoding="utf-8")
    write_notes(profile, model)

    summary = {
        "project_root": str(PROJECT_ROOT),
        "component_count": len(components),
        "allocated_credits": sum(component["planned_credits"] for component in components),
        "files": [str(PROFILE_PATH), str(MODEL_PATH), str(GAME_PROJECT_PATH), str(NOTES_PATH)],
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())