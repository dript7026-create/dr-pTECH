from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = TOOLS_DIR.parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

try:
    game_pipeline = importlib.import_module("game_pipeline")
except ImportError:
    game_pipeline = importlib.import_module("egosphere.tools.game_pipeline")

hope_asset_synthesis = importlib.import_module("egosphere.tools.hope_asset_synthesis")
hope_framework = importlib.import_module("egosphere.tools.hope_framework")

synthesize_audio_asset = hope_asset_synthesis.synthesize_audio_asset
synthesize_animation_asset = hope_asset_synthesis.synthesize_animation_asset
synthesize_ecology_asset = hope_asset_synthesis.synthesize_ecology_asset
synthesize_image_asset = hope_asset_synthesis.synthesize_image_asset
synthesize_material_asset = hope_asset_synthesis.synthesize_material_asset
synthesize_mesh_asset = hope_asset_synthesis.synthesize_mesh_asset
synthesize_physics_asset = hope_asset_synthesis.synthesize_physics_asset
synthesize_structure_asset = hope_asset_synthesis.synthesize_structure_asset
synthesize_anim_state_machine_asset = hope_asset_synthesis.synthesize_anim_state_machine_asset
synthesize_vfx_asset = hope_asset_synthesis.synthesize_vfx_asset
synthesize_interaction_asset = hope_asset_synthesis.synthesize_interaction_asset
synthesize_hitbox_asset = hope_asset_synthesis.synthesize_hitbox_asset

CosmicProfile = hope_framework.CosmicProfile
KinshipHubProfile = hope_framework.KinshipHubProfile
MeshProfile = hope_framework.MeshProfile
MatterProfile = hope_framework.MatterProfile
PhysicsProfile = hope_framework.PhysicsProfile
PipelineProfile = hope_framework.PipelineProfile
PlatformTargetProfile = hope_framework.PlatformTargetProfile
evaluate_hope_frame = hope_framework.evaluate_hope_frame


DEFAULT_TRANSLATION_PROFILE = {
    "art_export": "synthesis_board",
    "blender": "mesh_growth_lattice",
    "engine": "runtime_bundle_projection",
}

ASSET_TYPE_SINGULAR = {
    "tilesets": "tileset",
    "sprites": "sprite",
    "portraits": "portrait",
    "meshes": "mesh",
    "structures": "structure",
    "materials": "material",
    "physics_rigs": "physics_rig",
    "animations": "animation",
    "ecology": "ecology",
    "audio": "audio",
    "anim_state_machines": "anim_state_machine",
    "vfx_descriptors": "vfx_descriptor",
    "interaction_graphs": "interaction_graph",
    "hitbox_manifests": "hitbox_manifest",
}


def load_seed(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict | list) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _singular_asset_type(asset_type: str) -> str:
    return ASSET_TYPE_SINGULAR.get(asset_type, asset_type[:-1] if asset_type.endswith("s") else asset_type)


def slugify(value: str) -> str:
    lowered = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return lowered or "seed"


def _generation_root(project_slug: str) -> str:
    return f"generation/{project_slug}"


def _build_mesh_profile(cell: dict, default_complexity: float) -> MeshProfile:
    scene_scale = float(cell.get("scene_scale", 1.0))
    character_count = int(cell.get("character_count", 5))
    return MeshProfile(
        name=slugify(cell["name"]),
        triangle_count=int(95000 * scene_scale + character_count * 18000 + default_complexity * 42000),
        material_count=max(4, int(5 + scene_scale * 4 + default_complexity * 3)),
        skin_joint_count=max(18, int(22 + character_count * 3 + default_complexity * 10)),
        deformer_count=max(1, int(cell.get("interaction_zones", 2) * 0.7 + scene_scale * 2)),
        lod_levels=max(3, int(3 + scene_scale)),
    )


def _build_physics_profile(cell: dict, default_complexity: float) -> PhysicsProfile:
    scene_scale = float(cell.get("scene_scale", 1.0))
    interaction_zones = int(cell.get("interaction_zones", 2))
    movement = float(cell.get("movement_speed", 0.9))
    return PhysicsProfile(
        dynamic_bodies=max(12, int(18 * scene_scale + interaction_zones * 6)),
        contact_pairs=max(28, int(55 * scene_scale + interaction_zones * 18 + default_complexity * 24)),
        solver_iterations=max(8, int(8 + default_complexity * 3 + scene_scale * 2)),
        interaction_density=min(1.0, 0.22 + interaction_zones * 0.08 + default_complexity * 0.16),
        movement_speed=movement,
    )


def _build_pipeline_profile(cell: dict, default_complexity: float) -> PipelineProfile:
    scene_scale = float(cell.get("scene_scale", 1.0))
    interaction_zones = int(cell.get("interaction_zones", 2))
    return PipelineProfile(
        draw_calls=max(220, int(260 * scene_scale + interaction_zones * 70 + default_complexity * 180)),
        upload_mb=round(10.0 * scene_scale + default_complexity * 12.0 + interaction_zones * 1.8, 3),
        frame_buffer_variance=min(1.0, 0.08 + default_complexity * 0.22 + scene_scale * 0.07),
        queue_depth=max(2, int(2 + scene_scale * 2 + default_complexity * 3)),
        present_jitter=min(1.0, 0.05 + default_complexity * 0.12 + interaction_zones * 0.015),
    )


def _build_cosmic_profile(cell: dict, global_spec: dict) -> CosmicProfile:
    recursion = int(global_spec.get("recursion_depth", 3))
    causality_links = int(global_spec.get("causality_links", 12))
    reality_cells = int(global_spec.get("reality_cells", 10))
    scene_scale = float(cell.get("scene_scale", 1.0))
    return CosmicProfile(
        reality_cells=max(4, int(reality_cells * scene_scale)),
        recursion_depth=max(1, recursion + int(cell.get("recursion_bias", 0))),
        causality_links=max(4, causality_links + int(cell.get("interaction_zones", 2) * 2)),
        event_density=min(1.0, 0.2 + float(cell.get("scene_scale", 1.0)) * 0.12 + float(cell.get("event_density", 0.22))),
    )


def _build_kinship_profile(family: dict, cell: dict) -> KinshipHubProfile:
    members = family.get("members", [])
    bond_density = float(family.get("bond_density", 0.66))
    soul_sync = float(family.get("soul_sync", 0.7))
    refuge_bias = float(cell.get("sanctuary_bias", 0.0))
    refuge_demand = max(0.0, float(cell.get("scene_scale", 1.0)) * 0.16 + float(cell.get("interaction_zones", 2)) * 0.04 - refuge_bias)
    return KinshipHubProfile(
        member_count=max(1, len(members)),
        bond_density=min(1.0, bond_density),
        soul_sync=min(1.0, soul_sync),
        refuge_demand=min(1.0, refuge_demand),
    )


def _build_matter_profile(seed: dict, cell: dict) -> MatterProfile:
    global_matter = seed.get("matter", {})
    return MatterProfile(
        solid_density=min(1.0, max(0.0, float(cell.get("solid_density", global_matter.get("solid_density", 0.48))))),
        liquid_flow=min(1.0, max(0.0, float(cell.get("liquid_flow", global_matter.get("liquid_flow", 0.36))))),
        gas_diffusion=min(1.0, max(0.0, float(cell.get("gas_diffusion", global_matter.get("gas_diffusion", 0.28))))),
        fluid_turbulence=min(1.0, max(0.0, float(cell.get("fluid_turbulence", global_matter.get("fluid_turbulence", 0.22))))),
        reactive_volume=max(16, int(cell.get("reactive_volume", global_matter.get("reactive_volume", 48)))),
    )


def _build_platform_contract(seed: dict) -> dict:
    spec = seed.get("platforms", {})
    target_specs = spec.get(
        "targets",
        [
            {
                "name": "host",
                "input_latency_ms": 8.0,
                "present_budget_ms": 16.67,
                "render_scale": 1.0,
                "handheld_bias": 0.22,
                "sensor_channels": 1,
                "volumetric_support": 0.72,
                "causality_feedback": 0.64,
            }
        ],
    )
    targets = []
    for target_spec in target_specs:
        target = PlatformTargetProfile(
            name=target_spec["name"],
            input_latency_ms=float(target_spec.get("input_latency_ms", 8.0)),
            present_budget_ms=float(target_spec.get("present_budget_ms", 16.67)),
            render_scale=float(target_spec.get("render_scale", 1.0)),
            handheld_bias=float(target_spec.get("handheld_bias", 0.25)),
            sensor_channels=int(target_spec.get("sensor_channels", 1)),
            volumetric_support=float(target_spec.get("volumetric_support", 0.5)),
            causality_feedback=float(target_spec.get("causality_feedback", 0.5)),
        )
        targets.append(target)
    primary_target = spec.get("primary_target", targets[0].name if targets else "host")
    return {
        "schema": "hope_platform_contract/v1",
        "primary_target": primary_target,
        "targets": [
            {
                "name": target.name,
                "input_latency_ms": target.input_latency_ms,
                "present_budget_ms": target.present_budget_ms,
                "render_scale": target.render_scale,
                "handheld_bias": target.handheld_bias,
                "sensor_channels": target.sensor_channels,
                "volumetric_support": target.volumetric_support,
                "causality_feedback": target.causality_feedback,
            }
            for target in targets
        ],
    }


def _primary_target_profile(platform_contract: dict) -> PlatformTargetProfile:
    primary_name = platform_contract["primary_target"]
    target = next((item for item in platform_contract["targets"] if item["name"] == primary_name), platform_contract["targets"][0])
    return PlatformTargetProfile(
        name=target["name"],
        input_latency_ms=float(target["input_latency_ms"]),
        present_budget_ms=float(target["present_budget_ms"]),
        render_scale=float(target["render_scale"]),
        handheld_bias=float(target["handheld_bias"]),
        sensor_channels=int(target["sensor_channels"]),
        volumetric_support=float(target["volumetric_support"]),
        causality_feedback=float(target["causality_feedback"]),
    )


def _build_causality_profile(seed: dict, cell: dict, target: PlatformTargetProfile, matter: MatterProfile, hope: dict) -> dict[str, float]:
    spec = seed.get("causality", {})
    return {
        "input_pressure": round(min(1.0, max(0.0, float(cell.get("input_pressure", spec.get("input_pressure", 0.58))))), 4),
        "entity_feedback": round(min(1.0, max(0.0, float(cell.get("entity_feedback", spec.get("entity_feedback", 0.54))))), 4),
        "render_reactivity": round(min(1.0, max(0.0, float(cell.get("render_reactivity", spec.get("render_reactivity", 0.68))))), 4),
            "volumetric_bias": round(min(
                1.0,
                max(0.0, (matter.liquid_flow + matter.gas_diffusion + matter.fluid_turbulence) / 3.0 * 0.55 + target.volumetric_support * 0.45)
            ), 4),
            "affordance_span": round(min(
                1.0,
                max(0.0, float(cell.get("affordance_span", spec.get("affordance_span", 0.5))) + float(hope.get("theta", 0.0)) * 0.08)
            ), 4),
    }


def _build_scene_assets(project_slug: str, cell_slug: str, family_members: list[dict]) -> dict[str, list[dict]]:
    root = _generation_root(project_slug)
    tilesets = [
        {
            "id": f"{cell_slug}_tileset",
            "path": f"{root}/tilesets/{cell_slug}_tileset.png",
            "tile_w": 32,
            "tile_h": 32,
            "semantic_tags": [cell_slug, "walkable", "setpiece"],
            "usage": "world_tileset",
            "material_profile": f"{cell_slug}_world_material",
        }
    ]
    sprites = [
        {
            "id": f"{cell_slug}_player_avatar",
            "path": f"{root}/sprites/{cell_slug}_player_avatar.png",
            "frames": 10,
            "usage": "player",
            "material_profile": f"{cell_slug}_hero_material",
            "collider": {"shape": "capsule", "radius": 0.33, "height": 1.78},
        },
        {
            "id": f"{cell_slug}_world_anchor",
            "path": f"{root}/sprites/{cell_slug}_world_anchor.png",
            "frames": 6,
            "usage": "world_anchor",
            "material_profile": f"{cell_slug}_world_material",
            "collider": {"shape": "box", "width": 1.4, "height": 2.2, "depth": 1.4},
        },
    ]
    portraits = []
    meshes = [
        {
            "id": f"{cell_slug}_terrain_mesh",
            "path": f"{root}/meshes/{cell_slug}_terrain_mesh.obj",
            "usage": "terrain",
            "generator": "hope_mesh_synthesis",
        },
        {
            "id": f"{cell_slug}_sanctuary_mesh",
            "path": f"{root}/meshes/{cell_slug}_sanctuary_mesh.obj",
            "usage": "sanctuary",
            "generator": "hope_mesh_synthesis",
        },
    ]
    structures = [
        {
            "id": f"{cell_slug}_gateway_arch",
            "path": f"{root}/structures/{cell_slug}_gateway_arch.obj",
            "usage": "architecture",
            "generator": "hope_structure_synthesis",
        },
        {
            "id": f"{cell_slug}_ritual_prop",
            "path": f"{root}/structures/{cell_slug}_ritual_prop.obj",
            "usage": "prop",
            "generator": "hope_structure_synthesis",
        },
    ]
    materials = [
        {
            "id": f"{cell_slug}_world_material",
            "path": f"{root}/materials/{cell_slug}_world_material.json",
            "usage": "world",
            "generator": "hope_material_synthesis",
        },
        {
            "id": f"{cell_slug}_hero_material",
            "path": f"{root}/materials/{cell_slug}_hero_material.json",
            "usage": "hero",
            "generator": "hope_material_synthesis",
        },
    ]
    physics_rigs = [
        {
            "id": f"{cell_slug}_movement_rig",
            "path": f"{root}/physics/{cell_slug}_movement_rig.json",
            "usage": "movement",
            "generator": "hope_physics_synthesis",
        }
    ]
    animations = [
        {
            "id": f"{cell_slug}_player_motion",
            "path": f"{root}/animations/{cell_slug}_player_motion.json",
            "usage": "movement",
            "generator": "hope_animation_synthesis",
        },
        {
            "id": f"{cell_slug}_anchor_pulse",
            "path": f"{root}/animations/{cell_slug}_anchor_pulse.json",
            "usage": "ambient",
            "generator": "hope_animation_synthesis",
        },
    ]
    audio = [
        {
            "id": f"{cell_slug}_ambience",
            "path": f"{root}/audio/{cell_slug}_ambience.wav",
            "usage": "ambience",
            "generator": "hope_audio_synthesis",
        }
    ]
    ecology = [
        {
            "id": f"{cell_slug}_population",
            "path": f"{root}/ecology/{cell_slug}_population.json",
            "usage": "population",
            "generator": "hope_ecology_synthesis",
        }
    ]
    entity_ids = [f"{cell_slug}_player", f"{cell_slug}_anchor"] + [
        f"{cell_slug}_{slugify(m['name'])}_sprite" for m in family_members
    ]
    anim_state_machines = [
        {
            "id": f"{cell_slug}_player_asm",
            "path": f"{root}/anim_state_machines/{cell_slug}_player_asm.json",
            "usage": "player",
            "generator": "hope_anim_state_machine_synthesis",
        },
        {
            "id": f"{cell_slug}_anchor_asm",
            "path": f"{root}/anim_state_machines/{cell_slug}_anchor_asm.json",
            "usage": "world_anchor",
            "generator": "hope_anim_state_machine_synthesis",
        },
    ]
    vfx_descriptors = [
        {
            "id": f"{cell_slug}_vfx",
            "path": f"{root}/vfx/{cell_slug}_vfx.json",
            "usage": "scene",
            "generator": "hope_vfx_synthesis",
        }
    ]
    interaction_graphs = [
        {
            "id": f"{cell_slug}_interaction_graph",
            "path": f"{root}/interaction/{cell_slug}_interaction_graph.json",
            "usage": "scene",
            "entity_ids": entity_ids,
            "generator": "hope_interaction_synthesis",
        }
    ]
    hitbox_manifests = [
        {
            "id": f"{cell_slug}_hitbox_manifest",
            "path": f"{root}/hitboxes/{cell_slug}_hitbox_manifest.json",
            "usage": "scene",
            "entity_ids": entity_ids,
            "generator": "hope_hitbox_synthesis",
        }
    ]
    for member in family_members:
        member_slug = slugify(member["name"])
        sprites.append(
            {
                "id": f"{cell_slug}_{member_slug}_sprite",
                "path": f"{root}/sprites/{cell_slug}_{member_slug}.png",
                "frames": 6,
                "usage": "family_member",
                "material_profile": f"{cell_slug}_hero_material",
                "collider": {"shape": "capsule", "radius": 0.3, "height": 1.7},
            }
        )
        portraits.append(
            {
                "id": f"{cell_slug}_{member_slug}_portrait",
                "path": f"{root}/portraits/{cell_slug}_{member_slug}.png",
                "usage": "dialogue",
                "precache": False,
            }
        )
        anim_state_machines.append(
            {
                "id": f"{cell_slug}_{member_slug}_asm",
                "path": f"{root}/anim_state_machines/{cell_slug}_{member_slug}_asm.json",
                "usage": "family_member",
                "generator": "hope_anim_state_machine_synthesis",
            }
        )
    return {
        "tilesets": tilesets,
        "sprites": sprites,
        "portraits": portraits,
        "meshes": meshes,
        "structures": structures,
        "materials": materials,
        "physics_rigs": physics_rigs,
        "animations": animations,
        "ecology": ecology,
        "audio": audio,
        "anim_state_machines": anim_state_machines,
        "vfx_descriptors": vfx_descriptors,
        "interaction_graphs": interaction_graphs,
        "hitbox_manifests": hitbox_manifests,
    }


def _merge_assets(asset_groups: list[dict[str, list[dict]]]) -> dict[str, list[dict]]:
    merged: dict[str, list[dict]] = {}
    for group in asset_groups:
        for key, items in group.items():
            merged.setdefault(key, []).extend(items)
    return merged


def _build_authoring(seed: dict, project_slug: str, scenes: list[dict], systems: list[dict]) -> dict:
    canvas = seed.get("authoring", {}).get("canvas", {"width": 2048, "height": 2048, "layers": 18})
    mood_layers = [{"name": "reality_field", "blend_mode": "normal", "visible": True}, {"name": "sanctuary_glow", "blend_mode": "screen", "visible": True}, {"name": "causality_guides", "blend_mode": "multiply", "visible": False}]
    symbols = ["HopePlayerStart", "KinshipHubAnchor", "SoulNetBridge", "RealityCellGate"]
    return {
        "art_export": {
            "canvas": canvas,
            "timeline_fps": int(seed.get("authoring", {}).get("timeline_fps", 12)),
            "export_profile": {
                "color_mode": "rgba",
                "naming": "asset_id",
                "slice_method": "layer_group",
                "synthesis_mode": "reality_field",
            },
            "layers": mood_layers,
            "script_symbols": symbols,
            "symbol_bindings": [
                {"symbol": "HopePlayerStart", "asset_id": f"{slugify(seed['world']['cells'][0]['name'])}_player_avatar", "role": "player_spawn"},
                {"symbol": "KinshipHubAnchor", "asset_id": f"{slugify(seed['world']['cells'][0]['name'])}_sanctuary_mesh", "role": "kinship_hub"},
                {"symbol": "SoulNetBridge", "asset_id": f"{slugify(seed['world']['cells'][0]['name'])}_world_anchor", "role": "resonance_bridge"},
            ],
            "frame_tags": [{"tag": f"enter_{scene['id']}", "frame": scene["timeline_frames"][0], "scene_id": scene["id"]} for scene in scenes],
            "hitboxes": [{"symbol": "HopePlayerStart", "frame": 0, "x": 6, "y": 4, "w": 20, "h": 30, "kind": "hurtbox"}],
            "script_bindings": [
                {"name": "open_reality_gate", "event": f"enter_{scenes[0]['id']}", "target_symbol": "RealityCellGate", "command": f"prime_scene:{scenes[0]['id']}"},
                {"name": "kinship_realign", "event": f"enter_{scenes[-1]['id']}", "target_symbol": "KinshipHubAnchor", "command": f"stabilize_scene:{scenes[-1]['id']}"},
            ],
        },
        "blender": {
            "scale": 0.1,
            "extrusion_depth": 0.09,
            "lift_mode": "synthesis_depth_card",
            "rig_profile": "hope_humanoid",
            "material_profiles": [
                {"name": "hope_world_material", "shader": "toon_principled", "roughness": 0.72, "normal_strength": 0.22},
                {"name": "hope_sanctuary_material", "shader": "emissive_layered", "roughness": 0.48, "normal_strength": 0.16},
            ],
            "rig_overrides": [],
            "nodecraft_graphs": [
                {"name": f"{project_slug}_reality_graph", "nodes": [{"id": scene["id"], "position": [index * 8.0, 0.0, 0.0], "scale": 1.0}] , "links": []} for index, scene in enumerate(scenes)
            ],
            "scene_build": [{"scene_id": scene["id"], "collection": scene["id"], "world_mesh": f"{slugify(scene['location'])}_terrain_mesh"} for scene in scenes],
            "structure_layout": [{"scene_id": scene["id"], "structure_ids": [f"{scene['id']}_gateway_arch", f"{scene['id']}_ritual_prop"]} for scene in scenes],
        },
        "engine": {
            "module_name": f"g_{project_slug}",
            "asset_root": f"baseq2/{project_slug}",
            "autofactor_prefix": project_slug,
            "precache_groups": [
                {
                    "group_name": "sound",
                    "entries": [
                        {"alias": f"{project_slug}_ambient", "path": f"sound/{project_slug}/ambient_loop.wav", "asset_type": "sound"},
                        {"alias": f"{project_slug}_sanctuary", "path": f"sound/{project_slug}/sanctuary_loop.wav", "asset_type": "sound"},
                    ],
                }
            ],
            "system_dispatch": {system["name"]: {"init_fn": f"{system['name']}_init", "tick_fn": f"{system['name']}_tick"} for system in systems},
            "bootstrap": {"entry_scene": scenes[0]["id"], "precache_phase": "game_init", "spawn_phase": "level_load"},
        },
    }


def compile_world_seed(seed: dict) -> dict:
    project_name = seed["project_name"]
    project_slug = slugify(project_name)
    world = seed["world"]
    family = seed.get("family_hub", {"members": []})
    default_complexity = float(seed.get("generation", {}).get("complexity_bias", 0.45))
    platform_contract = _build_platform_contract(seed)
    primary_target = _primary_target_profile(platform_contract)

    scenes = []
    entities = []
    scene_asset_groups = []
    synthesis_cells = []

    for index, cell in enumerate(world["cells"]):
        cell_slug = slugify(cell["name"])
        mesh = _build_mesh_profile(cell, default_complexity)
        physics = _build_physics_profile(cell, default_complexity)
        pipeline = _build_pipeline_profile(cell, default_complexity)
        cosmic = _build_cosmic_profile(cell, world)
        kinship = _build_kinship_profile(family, cell)
        matter = _build_matter_profile(seed, cell)
        hope = evaluate_hope_frame(mesh, physics, pipeline, cosmic, kinship, matter=matter, target=primary_target)
        causality = _build_causality_profile(seed, cell, primary_target, matter, hope.to_dict())

        scenes.append(
            {
                "id": cell_slug,
                "scene_type": cell.get("scene_type", "exploration"),
                "location": cell_slug,
                "timeline_frames": [index * 64, index * 64 + 63],
                "triggers": [
                    {"id": f"{cell_slug}_prime", "frame": index * 64, "event": "scene_enter", "target": f"{cell_slug}_anchor"},
                    {"id": f"{cell_slug}_hope_rebalance", "frame": index * 64 + 24, "event": "hope_rebalance", "target": f"{cell_slug}_anchor"},
                ],
                "matter": {
                    "solid_density": matter.solid_density,
                    "liquid_flow": matter.liquid_flow,
                    "gas_diffusion": matter.gas_diffusion,
                    "fluid_turbulence": matter.fluid_turbulence,
                    "reactive_volume": matter.reactive_volume,
                },
                "causality": causality,
                "targeting": {
                    "primary_target": platform_contract["primary_target"],
                    "supported_targets": [item["name"] for item in platform_contract["targets"]],
                },
                "hope": hope.to_dict(),
            }
        )
        entities.extend(
            [
                {
                    "id": f"{cell_slug}_player",
                    "classname": "hope_player",
                    "asset_id": f"{cell_slug}_player_avatar",
                    "spawn": [128 + index * 32, 64, 0],
                    "logic_components": ["controllable", "hope_subject", "egosphere_agent", "movement_body", "input_affordance_shaper", "render_feedback_agent"],
                },
                {
                    "id": f"{cell_slug}_anchor",
                    "classname": "hope_world_anchor",
                    "asset_id": f"{cell_slug}_world_anchor",
                    "spawn": [384 + index * 64, 96, 0],
                    "logic_components": ["reality_anchor", "godai_subject", "streaming_gate", "causality_router"],
                },
                {
                    "id": f"{cell_slug}_population_anchor",
                    "classname": "hope_population_anchor",
                    "asset_id": f"{cell_slug}_population",
                    "spawn": [448 + index * 64, 112, 0],
                    "logic_components": ["ecology_population", "egosphere_agent", "habitat_memory", "artisapien_pressure_field"],
                },
            ]
        )
        scene_asset_groups.append(_build_scene_assets(project_slug, cell_slug, family.get("members", [])))
        synthesis_cells.append({
            "cell_id": cell_slug,
            "scene_type": cell.get("scene_type", "exploration"),
            "cell_source": cell,
            "mesh_profile": mesh.__dict__,
            "physics_profile": physics.__dict__,
            "pipeline_profile": pipeline.__dict__,
            "cosmic_profile": cosmic.__dict__,
            "kinship_profile": kinship.__dict__,
            "matter_profile": matter.__dict__,
            "causality_profile": causality,
            "hope_result": hope.to_dict(),
        })

    family_slug = slugify(family.get("name", "kinship_hub"))
    entities.append(
        {
            "id": family_slug,
            "classname": "kinship_hub",
            "asset_id": f"{slugify(world['cells'][0]['name'])}_sanctuary_mesh",
            "spawn": [96, 96, 0],
            "logic_components": ["kinship_hub", "soul_network_anchor", "hope_sanctuary"],
        }
    )
    systems = [
        {"name": "hope_world_system", "priority": 10, "lifecycle": ["init", "tick", "shutdown"]},
        {"name": "hope_ecology_system", "priority": 15, "lifecycle": ["init", "tick"]},
        {"name": "hope_matter_system", "priority": 18, "lifecycle": ["init", "tick"]},
        {"name": "hope_streaming_system", "priority": 20, "lifecycle": ["init", "tick"]},
        {"name": "hope_physics_system", "priority": 30, "lifecycle": ["init", "tick"]},
        {"name": "hope_causality_system", "priority": 35, "lifecycle": ["init", "tick"]},
        {"name": "hope_interaction_system", "priority": 37, "lifecycle": ["init", "tick"]},
        {"name": "hope_hitbox_system", "priority": 38, "lifecycle": ["init", "tick"]},
        {"name": "hope_vfx_system", "priority": 39, "lifecycle": ["init", "tick"]},
        {"name": "egosphere_resonance_system", "priority": 40, "lifecycle": ["init", "tick"]},
        {"name": "egosphere_entity_influence_system", "priority": 45, "lifecycle": ["init", "tick"]},
        {"name": "godai_conductor_system", "priority": 50, "lifecycle": ["init", "tick"]},
        {"name": "kinship_hub_system", "priority": 60, "lifecycle": ["init", "tick"]},
        {"name": "open_arms_sanctuary_system", "priority": 70, "lifecycle": ["init", "tick"]},
    ]
    assets = _merge_assets(scene_asset_groups)

    project = {
        "project_name": project_name,
        "seed": seed.get("seed", "HOPE-SYNTHESIS"),
        "translation_profile": dict(DEFAULT_TRANSLATION_PROFILE),
        "authoring": _build_authoring(seed, project_slug, scenes, systems),
        "assets": assets,
        "gameplay": {"scenes": scenes, "entities": entities, "systems": systems},
        "runtime": {
            "entry_scene": scenes[0]["id"],
            "system_graph": [
                "reality_cell_system",
                "ecology_state_system",
                "kinship_hub_system",
                "input_causality_system",
                "matter_state_system",
                "entity_influence_system",
                "sanctuary_state_system",
                "hope_controller_system",
                "streaming_system",
                "physics_system",
                "interaction_graph_system",
                "hitbox_resolution_system",
                "vfx_dispatch_system",
                "presentation_system",
                "frame_reality_system",
                "scene_transition_system",
                "preview_loop_system",
            ],
        },
        "platform_contract": platform_contract,
        "targets": {
            "art_bundle": "art_bundle",
            "blender_bundle": "blender_bundle",
            "engine_bundle": "engine_bundle",
        },
        "synthesis": {
            "framework": "HOPE",
            "expansion": "Hierarchical Operations and Predictive Ecology",
            "world_seed": world,
            "family_hub": family,
            "platform_contract": platform_contract,
            "cells": synthesis_cells,
            "generation_contract": {
                "mesh": "hope_mesh_synthesis",
                "materials": "hope_material_synthesis",
                "physics": "hope_physics_synthesis",
                "structure": "hope_structure_synthesis",
                "animation": "hope_animation_synthesis",
                "ecology": "hope_ecology_synthesis",
                "audio": "hope_audio_synthesis",
                "matter": "hope_matter_synthesis",
                "causality": "hope_causality_synthesis",
                "platform": "hope_platform_contract",
                "world": "hope_reality_synthesis",
                "anim_state_machine": "hope_anim_state_machine_synthesis",
                "vfx": "hope_vfx_synthesis",
                "interaction": "hope_interaction_synthesis",
                "hitbox": "hope_hitbox_synthesis",
            },
        },
    }
    return project


def _resolve_asset_path(out_root: Path, asset_path: str) -> Path:
    asset = Path(asset_path)
    if asset.is_absolute():
        return asset
    return out_root / asset


def _cell_context_for_asset(project: dict, item_id: str) -> dict:
    synthesis = project.get("synthesis", {})
    cells = {cell["cell_id"]: cell for cell in synthesis.get("cells", [])}
    matched_id = ""
    for cell_id in cells:
        if item_id.startswith(cell_id) and len(cell_id) > len(matched_id):
            matched_id = cell_id
    if matched_id:
        return cells[matched_id]
    first_cell = next(iter(cells.values()), None)
    return first_cell or {
        "cell_id": "default",
        "scene_type": "exploration",
        "hope_result": {},
    }


def materialize_generation_assets(project: dict, out_root: Path) -> Path:
    assets_root = out_root / "generation"
    manifest_entries = []

    for asset_type, items in project["assets"].items():
        singular_type = _singular_asset_type(asset_type)
        for item in items:
            path = _resolve_asset_path(out_root, item["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            cell = _cell_context_for_asset(project, item["id"])
            hope = cell.get("hope_result", {})
            family = hope.get("family_hub_signal", {})
            scene_type = cell.get("scene_type", "exploration")
            usage = item.get("usage", singular_type)

            if singular_type in {"tileset", "sprite", "portrait"}:
                synthesize_image_asset(
                    path,
                    asset_id=item["id"],
                    asset_type=singular_type,
                    usage=usage,
                    scene_type=scene_type,
                    hope=hope,
                    family=family,
                )
            elif singular_type == "mesh":
                synthesize_mesh_asset(path, asset_id=item["id"], usage=usage, hope=hope, family=family)
            elif singular_type == "structure":
                synthesize_structure_asset(path, asset_id=item["id"], usage=usage, scene_type=scene_type, hope=hope, family=family)
            elif singular_type == "material":
                synthesize_material_asset(path, asset_id=item["id"], usage=usage, hope=hope, family=family)
            elif singular_type == "physics_rig":
                synthesize_physics_asset(path, asset_id=item["id"], usage=usage, hope=hope, family=family)
            elif singular_type == "animation":
                synthesize_animation_asset(path, asset_id=item["id"], usage=usage, scene_type=scene_type, hope=hope, family=family)
            elif singular_type == "ecology":
                synthesize_ecology_asset(path, asset_id=item["id"], usage=usage, scene_type=scene_type, hope=hope, family=family)
            elif singular_type == "audio":
                synthesize_audio_asset(path, asset_id=item["id"], usage=usage, scene_type=scene_type, hope=hope, family=family)
            elif singular_type == "anim_state_machine":
                synthesize_anim_state_machine_asset(path, asset_id=item["id"], usage=usage, scene_type=scene_type, hope=hope, family=family)
            elif singular_type == "vfx_descriptor":
                synthesize_vfx_asset(path, asset_id=item["id"], usage=usage, scene_type=scene_type, hope=hope, family=family)
            elif singular_type == "interaction_graph":
                synthesize_interaction_asset(path, asset_id=item["id"], usage=usage, scene_type=scene_type, hope=hope, family=family, entity_ids=item.get("entity_ids", []))
            elif singular_type == "hitbox_manifest":
                synthesize_hitbox_asset(path, asset_id=item["id"], usage=usage, scene_type=scene_type, hope=hope, family=family, entity_ids=item.get("entity_ids", []))
            else:
                path.write_text(item.get("id", "generated_asset"), encoding="utf-8")

            manifest_entries.append(
                {
                    "id": item["id"],
                    "asset_type": singular_type,
                    "path": str(path),
                    "generator": item.get("generator", "hope_synthesis"),
                    "scene_type": scene_type,
                    "usage": usage,
                }
            )

    manifest_path = assets_root / "generation_manifest.json"
    write_json(
        manifest_path,
        {
            "project_name": project["project_name"],
            "framework": project["synthesis"]["framework"],
            "asset_count": len(manifest_entries),
            "assets": manifest_entries,
        },
    )
    return manifest_path


def export_runtime_contract(project: dict, out_path: Path) -> Path:
    platform_contract = project.get("platform_contract", {"primary_target": "host", "targets": []})
    primary_name = platform_contract.get("primary_target", "host")
    targets = platform_contract.get("targets", [])
    primary_target = next((item for item in targets if item.get("name") == primary_name), targets[0] if targets else {"name": "host"})
    entry_scene_id = project.get("runtime", {}).get("entry_scene")
    scenes = project.get("gameplay", {}).get("scenes", [])
    entry_scene = next((scene for scene in scenes if scene.get("id") == entry_scene_id), scenes[0] if scenes else {})
    hope = entry_scene.get("hope", {})
    matter = entry_scene.get("matter", {})
    causality = entry_scene.get("causality", {})
    payload = {
        "project_name": project.get("project_name"),
        "primary_target": primary_name,
        "runtime": {
            "entry_scene": entry_scene_id,
            "system_graph": project.get("runtime", {}).get("system_graph", []),
        },
        "targets": targets,
        "bridgeTargetName": primary_target.get("name", primary_name),
        "bridgeInputLatencyMs": primary_target.get("input_latency_ms", 8.0),
        "bridgePresentBudgetMs": primary_target.get("present_budget_ms", 16.67),
        "bridgeRenderScale": primary_target.get("render_scale", 1.0),
        "bridgeHandheldBias": primary_target.get("handheld_bias", 0.25),
        "bridgeSensorChannels": primary_target.get("sensor_channels", 1),
        "bridgeVolumetricSupport": primary_target.get("volumetric_support", 0.5),
        "bridgeCausalityFeedback": primary_target.get("causality_feedback", 0.5),
        "bridgeSceneId": entry_scene.get("id", "entry"),
        "bridgeSceneType": entry_scene.get("scene_type", "exploration"),
        "bridgeMatterSolidDensity": matter.get("solid_density", hope.get("matter_plan", {}).get("solid_retention", 0.42)),
        "bridgeMatterLiquidFlow": matter.get("liquid_flow", hope.get("matter_plan", {}).get("liquid_responsiveness", 0.34)),
        "bridgeMatterGasDiffusion": matter.get("gas_diffusion", hope.get("matter_plan", {}).get("gas_resonance", 0.28)),
        "bridgeMatterFluidTurbulence": matter.get("fluid_turbulence", hope.get("matter_plan", {}).get("fluid_turbulence", 0.22)),
        "bridgeMatterReactiveVolume": matter.get("reactive_volume", 48),
        "bridgeInputPressure": causality.get("input_pressure", hope.get("causality_plan", {}).get("input_to_simulation", 0.5)),
        "bridgeEntityFeedback": causality.get("entity_feedback", hope.get("causality_plan", {}).get("entity_affordance_feedback", 0.5)),
        "bridgeRenderReactivity": causality.get("render_reactivity", hope.get("causality_plan", {}).get("simulation_to_render", 0.5)),
        "bridgeVolumetricBias": causality.get("volumetric_bias", hope.get("causality_plan", {}).get("volumetric_reactivity", 0.5)),
        "bridgeAffordanceSpan": causality.get("affordance_span", hope.get("causality_plan", {}).get("entity_affordance_feedback", 0.5)),
        "bridgeHopeTheta": hope.get("theta", 0.0),
        "bridgeHopeClogRisk": hope.get("clog_risk", 0.0),
        "bridgeHopePredictiveShare": hope.get("predictive_share", 0.0),
        "bridgeHopeAdaptiveShare": hope.get("adaptive_share", 0.0),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(out_path, payload)
    return out_path


def transpile(seed_path: Path, out_path: Path) -> Path:
    project = compile_world_seed(load_seed(seed_path))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(out_path, project)
    return out_path


def build(seed_path: Path, out_root: Path) -> Path:
    out_root.mkdir(parents=True, exist_ok=True)
    canonical = out_root / "game_project.generated.json"
    transpile(seed_path, canonical)
    project = load_seed(canonical)
    manifest_path = materialize_generation_assets(project, out_root)
    runtime_contract_path = export_runtime_contract(project, out_root / "runtime" / "hope_runtime_contract.json")
    project.setdefault("synthesis", {})["materialized_assets_manifest"] = str(manifest_path)
    project.setdefault("runtime", {})["runtime_contract"] = str(runtime_contract_path)
    write_json(canonical, project)
    game_pipeline.build(canonical, out_root)
    return canonical


def main() -> int:
    parser = argparse.ArgumentParser(description="Synthesis-first HOPE world compiler")
    sub = parser.add_subparsers(dest="command", required=True)

    transpile_parser = sub.add_parser("transpile", help="Compile a synthesis world seed into a canonical project manifest")
    transpile_parser.add_argument("--project", required=True, type=Path)
    transpile_parser.add_argument("--out", required=True, type=Path)

    build_parser = sub.add_parser("build", help="Compile and build bundles from a synthesis world seed")
    build_parser.add_argument("--project", required=True, type=Path)
    build_parser.add_argument("--out", required=True, type=Path)

    export_runtime_parser = sub.add_parser("export-runtime", help="Compile a synthesis world seed and emit the Kaiju/HOPE runtime contract")
    export_runtime_parser.add_argument("--project", required=True, type=Path)
    export_runtime_parser.add_argument("--out", required=True, type=Path)

    args = parser.parse_args()
    if args.command == "transpile":
        output = transpile(args.project, args.out)
        print(json.dumps({"canonical_project": str(output)}, indent=2))
        return 0
    if args.command == "build":
        output = build(args.project, args.out)
        print(json.dumps({"canonical_project": str(output)}, indent=2))
        return 0
    if args.command == "export-runtime":
        project = compile_world_seed(load_seed(args.project))
        output = export_runtime_contract(project, args.out)
        print(json.dumps({"runtime_contract": str(output)}, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())