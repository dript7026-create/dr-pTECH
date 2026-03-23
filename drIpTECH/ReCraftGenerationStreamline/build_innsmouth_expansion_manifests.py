import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_FILES = {
    "frame_guide": ROOT / "innsmouth_island_frame_pair_pipeline_guide_v1.json",
    "frame_manifest": ROOT / "innsmouth_island_frame_pair_expansion_manifest.json",
    "tile_guide": ROOT / "innsmouth_island_tiles_skybox_pair_pipeline_guide_v1.json",
    "tile_manifest": ROOT / "innsmouth_island_tiles_skybox_pair_expansion_manifest.json",
    "budget_summary": ROOT / "innsmouth_island_expansion_budget_summary_v1.json",
}

API_UNITS_PER_IMAGE = 40
FRAME_IMAGE_SIZE = 1024
TILE_IMAGE_SIZE = 1024
FRAME_OUTPUT_ROOT = "../../ORBEngine/assets/innsmouth_island/frame_pair_expansion"
TILE_OUTPUT_ROOT = "../../ORBEngine/assets/innsmouth_island/tiles_skybox_pair_expansion"

NEGATIVE_PROMPT = (
    "wrong pose, mismatched silhouette, altered costume language, altered camera angle, "
    "extra limbs, scenic poster frame, text, watermark, logo, border, cropped subject, "
    "soft mushy silhouette, rounded posing, contradictory lighting"
)

FRAME_SEQUENCES = [
    {
        "family": "player",
        "sequence_key": "player_light_combo",
        "sequence_label": "Player Light Combo",
        "base_asset_ref": "complete_game/player/innsmouth_player_light_combo_keyframes_v3.png",
        "subject": "fish-man drifter protagonist using Barnacle Shiv stance language",
        "frames": [
            ("f01", "anticipation coil before first slash"),
            ("f02", "first slash contact beat"),
            ("f03", "chain redirect transition"),
            ("f04", "finishing recovery with planted stance"),
        ],
    },
    {
        "family": "player",
        "sequence_key": "player_heavy_combo",
        "sequence_label": "Player Heavy Combo",
        "base_asset_ref": "complete_game/player/innsmouth_player_heavy_combo_keyframes_v3.png",
        "subject": "fish-man drifter protagonist using overcommitted heavy weapon body language",
        "frames": [
            ("f01", "windup torque with rear-foot loading"),
            ("f02", "descending impact arc"),
            ("f03", "full-contact crush beat"),
            ("f04", "exhausted follow-through recovery"),
        ],
    },
    {
        "family": "player",
        "sequence_key": "player_air_dodge",
        "sequence_label": "Player Air And Dodge",
        "base_asset_ref": "complete_game/player/innsmouth_player_air_and_dodge_keyframes_v3.png",
        "subject": "fish-man drifter protagonist traversal body language",
        "frames": [
            ("f01", "jump launch compression release"),
            ("f02", "midair drift apex pose"),
            ("f03", "dodge tuck with lateral snap"),
            ("f04", "landing catch and stabilization"),
        ],
    },
    {
        "family": "enemy",
        "sequence_key": "deep_one_raider_rush",
        "sequence_label": "Deep One Raider Rush",
        "base_asset_ref": "complete_game/enemies/innsmouth_deep_one_raider_action_sheet_v3.png",
        "subject": "Deep One Raider with harpoon feint aggression",
        "frames": [
            ("f01", "stalking lean before acceleration"),
            ("f02", "rush stride extension"),
            ("f03", "harpoon lunge contact"),
            ("f04", "recoil and reset posture"),
        ],
    },
    {
        "family": "enemy",
        "sequence_key": "nightgaunt_glide",
        "sequence_label": "Nightgaunt Glide Dive",
        "base_asset_ref": "complete_game/enemies/innsmouth_nightgaunt_stalker_action_sheet_v3.png",
        "subject": "Nightgaunt Stalker with angular wing geometry",
        "frames": [
            ("f01", "perched compression before launch"),
            ("f02", "glide spread with hard negative space"),
            ("f03", "dive rake strike"),
            ("f04", "post-pass recoil climb"),
        ],
    },
    {
        "family": "enemy",
        "sequence_key": "shoggoth_spring",
        "sequence_label": "Shoggoth Spawn Spring",
        "base_asset_ref": "complete_game/enemies/innsmouth_shoggoth_spawn_action_sheet_v3.png",
        "subject": "Shoggoth Spawn with elastic angular mass breakup",
        "frames": [
            ("f01", "mass compression before leap"),
            ("f02", "airborne spring extension"),
            ("f03", "pseudopod slam impact"),
            ("f04", "ooze recoil settle"),
        ],
    },
    {
        "family": "enemy",
        "sequence_key": "cultist_harpooner_throw",
        "sequence_label": "Cultist Harpooner Throw",
        "base_asset_ref": "complete_game/enemies/innsmouth_cultist_harpooner_action_sheet_v3.png",
        "subject": "Cultist Harpooner in ritual fishing gear",
        "frames": [
            ("f01", "aimed chant stance"),
            ("f02", "harpoon drawback tension"),
            ("f03", "release frame with shoulder snap"),
            ("f04", "knife-backup recovery stance"),
        ],
    },
    {
        "family": "boss",
        "sequence_key": "abyss_prince_phase",
        "sequence_label": "Reptilian Abyss Prince Phase Attack",
        "base_asset_ref": "complete_game/bosses/innsmouth_reptilian_abyss_prince_action_sheet_v3.png",
        "subject": "Reptilian Abyss Prince with regal monstrous spear-and-tail combat language",
        "frames": [
            ("f01", "throne-rise initiation"),
            ("f02", "spear cast extension"),
            ("f03", "tail sweep contact arc"),
            ("f04", "phase recoil with venom flare"),
        ],
    },
    {
        "family": "boss",
        "sequence_key": "jaguar_tyrant_pounce",
        "sequence_label": "Jaguar Eclipse Tyrant Pounce",
        "base_asset_ref": "complete_game/bosses/innsmouth_jaguar_eclipse_tyrant_action_sheet_v3.png",
        "subject": "Jaguar Eclipse Tyrant with brutal predator line-of-action",
        "frames": [
            ("f01", "low stalk crouch"),
            ("f02", "launch burst from eclipse dash"),
            ("f03", "mid-pounce claw fan contact"),
            ("f04", "landing skid and recovery"),
        ],
    },
]

TILE_SPECS = [
    {
        "family": "env_tile",
        "tile_key": "shoreline_brine_stone",
        "tile_label": "Shoreline Brine Stone Tile",
        "base_asset_ref": "complete_game/environment/shoreline_gate_single_v3.png",
        "description": "wet storm-battered shoreline stone with salt seams and foot-safe edges",
    },
    {
        "family": "env_tile",
        "tile_key": "mud_path_rut",
        "tile_label": "Mud Path Rut Tile",
        "base_asset_ref": "complete_game/environment/mud_altar_approach_single_v3.png",
        "description": "deep marsh rut tile with travel-worn mud channels and puddled depressions",
    },
    {
        "family": "env_tile",
        "tile_key": "reef_spike_ground",
        "tile_label": "Reef Spike Ground Tile",
        "base_asset_ref": "complete_game/environment/black_reef_ascent_single_v3.png",
        "description": "jagged reef-ground tile with black coral protrusions and traversal-safe pockets",
    },
    {
        "family": "env_tile",
        "tile_key": "dock_plank_wet",
        "tile_label": "Wet Dock Plank Tile",
        "base_asset_ref": "complete_game/environment/salt_jetty_arch_single_v3.png",
        "description": "waterlogged dock plank tile with warped boards, rope stains, and brine sheen",
    },
    {
        "family": "env_tile",
        "tile_key": "shrine_basin_floor",
        "tile_label": "Shrine Basin Floor Tile",
        "base_asset_ref": "complete_game/environment/shrine_basin_outer_single_v3.png",
        "description": "ritual shrine floor tile with pearl channels and angular basin geometry",
    },
    {
        "family": "env_tile",
        "tile_key": "mangrove_root_bank",
        "tile_label": "Mangrove Root Bank Tile",
        "base_asset_ref": "complete_game/environment/mangrove_spine_mid_single_v3.png",
        "description": "root-choked bank tile with twisted mangrove structure and black-silt seams",
    },
    {
        "family": "env_tile",
        "tile_key": "temple_step_basalt",
        "tile_label": "Temple Step Basalt Tile",
        "base_asset_ref": "complete_game/environment/basalt_stair_entry_single_v3.png",
        "description": "cyclopean basalt temple step tile with eroded corners and angular wear planes",
    },
    {
        "family": "env_tile",
        "tile_key": "eel_hatchery_grate",
        "tile_label": "Eel Hatchery Grate Tile",
        "base_asset_ref": "complete_game/environment/eel_hatchery_bank_single_v3.png",
        "description": "industrial hatchery floor tile with grate channels, slime residue, and hostile footing cues",
    },
    {
        "family": "env_tile",
        "tile_key": "grave_mire_silt",
        "tile_label": "Grave Mire Silt Tile",
        "base_asset_ref": "complete_game/environment/grave_mire_marker_single_v3.png",
        "description": "grave-mire soil tile with silt mounds, shallow sink patches, and bone fragments",
    },
    {
        "family": "env_tile",
        "tile_key": "coral_bridge_segment",
        "tile_label": "Coral Bridge Segment Tile",
        "base_asset_ref": "complete_game/environment/coral_bridge_low_single_v3.png",
        "description": "coral bridge walking tile with reinforced growth ribs and wet traversal seams",
    },
    {
        "family": "env_tile",
        "tile_key": "obsidian_pool_rim",
        "tile_label": "Obsidian Pool Rim Tile",
        "base_asset_ref": "complete_game/environment/obsidian_pool_north_single_v3.png",
        "description": "obsidian ritual pool rim tile with reflective black stone and dangerous inner lip",
    },
    {
        "family": "env_tile",
        "tile_key": "black_reef_jag",
        "tile_label": "Black Reef Jag Tile",
        "base_asset_ref": "complete_game/environment/black_reef_ascent_single_v3.png",
        "description": "steep black reef jag tile with sharp protrusions and narrow foot-plane access",
    },
    {
        "family": "skybox_tile",
        "tile_key": "storm_cloud_mass_a",
        "tile_label": "Storm Cloud Mass Tile A",
        "base_asset_ref": "complete_game/atmosphere/innsmouth_storm_sky_strata_layers_v3.png",
        "description": "storm sky tile with dense cloud mass and torn edge flow suitable for seamless sky assembly",
    },
    {
        "family": "skybox_tile",
        "tile_key": "storm_cloud_mass_b",
        "tile_label": "Storm Cloud Mass Tile B",
        "base_asset_ref": "complete_game/atmosphere/innsmouth_storm_sky_strata_layers_v3.png",
        "description": "secondary storm sky tile with alternate thunderhead breakup for non-repeating skybox cadence",
    },
    {
        "family": "skybox_tile",
        "tile_key": "eclipse_halo_core",
        "tile_label": "Eclipse Halo Core Tile",
        "base_asset_ref": "complete_game/atmosphere/innsmouth_eclipse_moon_and_celestial_layers_v3.png",
        "description": "eclipse-center sky tile with occult halo ring and abyssal luminance logic",
    },
    {
        "family": "skybox_tile",
        "tile_key": "distant_cliff_band",
        "tile_label": "Distant Cliff Band Tile",
        "base_asset_ref": "complete_game/atmosphere/innsmouth_far_horizon_coast_layers_v3.png",
        "description": "far-horizon cliff tile with drowned coast silhouette suitable for seamless skyline banding",
    },
    {
        "family": "skybox_tile",
        "tile_key": "drowned_wharf_silhouette",
        "tile_label": "Drowned Wharf Silhouette Tile",
        "base_asset_ref": "complete_game/atmosphere/innsmouth_beacon_and_distant_vessel_silhouette_layers_v3.png",
        "description": "distant wharf skyline tile with rotted mast and signal-cage silhouette breakup",
    },
    {
        "family": "skybox_tile",
        "tile_key": "occult_star_scar",
        "tile_label": "Occult Star Scar Tile",
        "base_asset_ref": "complete_game/atmosphere/innsmouth_occult_halo_and_eclipse_glow_layers_v3.png",
        "description": "celestial scar tile with occult star rupture and atmospheric glow continuity",
    },
]


def build_frame_guide():
    return {
        "guide_name": "innsmouth_island_frame_pair_pipeline_guide_v1",
        "date": "2026-03-11",
        "purpose": "Paired final-render and depth-hit-precision frame-by-frame expansion guide for complex InnsmouthIsland animations.",
        "budget_target": {
            "max_api_units": 3000,
            "estimated_api_units": len(FRAME_SEQUENCES) * 4 * 2 * API_UNITS_PER_IMAGE,
        },
        "pairing_rules": {
            "required_pair": "Every animation frame must be generated twice: one final in-game render-direction frame and one depth-hit-precision frame.",
            "congruency": [
                "The precision frame must match the final-render frame in pose, camera, silhouette contour, limb spread, weapon angle, and costume breakup.",
                "No precision frame may invent a different line-of-action or omit decorative masses that materially alter hit or dodge readability.",
                "Final and precision outputs must be immediately comparable as congruent frame twins for the same still moment."
            ],
            "precision_requirements": [
                "Depth planes must be more explicit than the final render version.",
                "Hit, hurt, traversal, and weapon-contact silhouettes must be tighter and more legible than decorative overflow.",
                "Anchor-node logic must remain compatible with the Innsmouth dimensional protocol profile."
            ]
        },
        "render_rules": {
            "transparent_background": True,
            "controls": {"transparent_background": True},
            "silhouette": "expressionistic, angular, aggressive, game-readable",
            "camera": "stable gameplay-facing side view with no cinematic angle drift across paired frames",
            "lighting": "single coherent in-game light family across both pair roles"
        },
        "base_asset_policy": "Use the already generated complete_game character sheets as the canonical costume, material, and silhouette baseline.",
        "output_root": FRAME_OUTPUT_ROOT,
    }


def build_tile_guide():
    return {
        "guide_name": "innsmouth_island_tiles_skybox_pair_pipeline_guide_v1",
        "date": "2026-03-11",
        "purpose": "Paired final-render and depth-hit-detection-precision tile expansion guide for InnsmouthIsland environment and skybox tile coverage.",
        "budget_target": {
            "max_api_units": 1500,
            "estimated_api_units": len(TILE_SPECS) * 2 * API_UNITS_PER_IMAGE,
        },
        "pairing_rules": {
            "required_pair": "Every tile is generated twice: one full-detail final render tile and one congruent depth-hit-detection-precision tile.",
            "congruency": [
                "The precision tile must preserve the same major silhouette masses, edge breaks, top-plane boundaries, and walkable contour as the final-render tile.",
                "Skybox precision tiles must preserve skyline and cloud break shapes so stitched assembly matches the final render tile set.",
                "Tile pairs must align edge-to-edge inside the same square footprint without border drift."
            ],
            "tile_boundary_policy": [
                "Tile art should fill the intended tile square rather than drift into scenic poster framing.",
                "Traversal and occlusion boundaries must be explicit in the precision variant.",
                "Skybox tiles must stitch cleanly when repeated or assembled into horizon bands."
            ]
        },
        "render_rules": {
            "transparent_background": False,
            "tile_fill": "full square tile coverage with no external scene framing",
            "lighting": "single coherent in-game light family across tile pairs",
            "surface_logic": "clear top-plane, wall-plane, and hazard-plane separation where applicable"
        },
        "base_asset_policy": "Use the already generated complete_game environment singles and atmosphere layers as the canonical art-direction source.",
        "output_root": TILE_OUTPUT_ROOT,
    }


def build_frame_items():
    items = []
    for sequence in FRAME_SEQUENCES:
        for frame_key, beat in sequence["frames"]:
            pair_group = f"{sequence['sequence_key']}_{frame_key}"
            final_name = f"{pair_group}_final_v1"
            precision_name = f"{pair_group}_precision_v1"
            final_prompt = (
                f"ORBSystems 32-dimensional coherency paired animation frame request for InnsmouthIsland; final in-game render-direction pipeline version; "
                f"transparent background only, isolated alpha render, no opaque backdrop; strict frame-by-frame still for {sequence['sequence_label']} {frame_key}, beat {beat}; "
                f"subject: {sequence['subject']}; use current asset base {sequence['base_asset_ref']} as the canonical costume, material, and silhouette baseline; "
                f"expressionistic angular silhouette, stable gameplay-facing camera, premium in-game readability, no text"
            )
            precision_prompt = (
                f"ORBSystems 32-dimensional coherency paired animation frame request for InnsmouthIsland; depth-hit-precision mapping version strictly congruent to paired final frame {final_name}; "
                f"transparent background only, isolated alpha render, no opaque backdrop; same exact still moment for {sequence['sequence_label']} {frame_key}, beat {beat}; "
                f"subject: {sequence['subject']}; preserve the exact final-render silhouette contour, pose, camera angle, limb spread, weapon angle, and costume breakup from {sequence['base_asset_ref']}; "
                f"make depth planes, hurt-contact silhouette, traversal silhouette, and weapon-contact precision explicit while keeping the outer silhouette congruent, no text"
            )
            common = {
                "prompt_revision": "frame_pair_budget3000_v1",
                "protocol_profile": "innsmouth_island_dimensional_protocol_v1",
                "pass_kind": "frame_pair_expansion",
                "guide_ref": "innsmouth_island_frame_pair_pipeline_guide_v1",
                "family": sequence["family"],
                "sequence_key": sequence["sequence_key"],
                "frame_key": frame_key,
                "pair_group": pair_group,
                "base_asset_ref": sequence["base_asset_ref"],
                "negative_prompt": NEGATIVE_PROMPT,
                "transparent_background": True,
                "controls": {"transparent_background": True},
                "w": FRAME_IMAGE_SIZE,
                "h": FRAME_IMAGE_SIZE,
                "model": "recraftv4",
                "api_units": API_UNITS_PER_IMAGE,
            }
            final_item = dict(common)
            final_item.update({
                "name": final_name,
                "category": "frame_final",
                "pair_role": "final_render",
                "prompt": final_prompt,
                "out": f"{FRAME_OUTPUT_ROOT}/final/{sequence['family']}/{pair_group}_final_v1.png",
            })
            precision_item = dict(common)
            precision_item.update({
                "name": precision_name,
                "category": "frame_precision",
                "pair_role": "depth_hit_precision",
                "paired_variant_of": final_name,
                "prompt": precision_prompt,
                "out": f"{FRAME_OUTPUT_ROOT}/precision/{sequence['family']}/{pair_group}_precision_v1.png",
            })
            items.extend([final_item, precision_item])
    return items


def build_tile_items():
    items = []
    for tile in TILE_SPECS:
        pair_group = tile["tile_key"]
        final_name = f"{pair_group}_final_v1"
        precision_name = f"{pair_group}_precision_v1"
        final_prompt = (
            f"ORBSystems 32-dimensional coherency paired tile request for InnsmouthIsland; final in-game render tile version; full square tile coverage, no scenic poster framing; "
            f"strict tile subject {tile['tile_label']} with {tile['description']}; use current asset base {tile['base_asset_ref']} as canonical art-direction source; "
            f"final-render detail with coherent lighting, clean edge stitchability, and game-ready material breakup, no text"
        )
        precision_prompt = (
            f"ORBSystems 32-dimensional coherency paired tile request for InnsmouthIsland; depth-hit-detection-precision tile version strictly congruent to paired final tile {final_name}; "
            f"same tile footprint and same major silhouette masses for {tile['tile_label']} with {tile['description']}; preserve edge profile and skyline or traversal contour from {tile['base_asset_ref']}; "
            f"make depth planes, walkable regions, collision edges, occlusion boundaries, and stitch seams explicit while remaining visually congruent to the final-render tile, no text"
        )
        common = {
            "prompt_revision": "tile_pair_budget1500_v1",
            "protocol_profile": "innsmouth_island_dimensional_protocol_v1",
            "pass_kind": "tiles_skybox_pair_expansion",
            "guide_ref": "innsmouth_island_tiles_skybox_pair_pipeline_guide_v1",
            "family": tile["family"],
            "tile_key": tile["tile_key"],
            "pair_group": pair_group,
            "base_asset_ref": tile["base_asset_ref"],
            "negative_prompt": NEGATIVE_PROMPT,
            "w": TILE_IMAGE_SIZE,
            "h": TILE_IMAGE_SIZE,
            "model": "recraftv4",
            "api_units": API_UNITS_PER_IMAGE,
        }
        final_item = dict(common)
        final_item.update({
            "name": final_name,
            "category": "tile_final",
            "pair_role": "final_render",
            "prompt": final_prompt,
            "out": f"{TILE_OUTPUT_ROOT}/final/{tile['family']}/{pair_group}_final_v1.png",
        })
        precision_item = dict(common)
        precision_item.update({
            "name": precision_name,
            "category": "tile_precision",
            "pair_role": "depth_hit_precision",
            "paired_variant_of": final_name,
            "prompt": precision_prompt,
            "out": f"{TILE_OUTPUT_ROOT}/precision/{tile['family']}/{pair_group}_precision_v1.png",
        })
        items.extend([final_item, precision_item])
    return items


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main():
    frame_items = build_frame_items()
    tile_items = build_tile_items()
    budget_summary = {
        "date": "2026-03-11",
        "frame_pair_manifest": OUTPUT_FILES["frame_manifest"].name,
        "tile_pair_manifest": OUTPUT_FILES["tile_manifest"].name,
        "frame_items": len(frame_items),
        "frame_estimated_api_units": sum(item["api_units"] for item in frame_items),
        "frame_budget_target": 3000,
        "tile_items": len(tile_items),
        "tile_estimated_api_units": sum(item["api_units"] for item in tile_items),
        "tile_budget_target": 1500,
    }
    write_json(OUTPUT_FILES["frame_guide"], build_frame_guide())
    write_json(OUTPUT_FILES["frame_manifest"], frame_items)
    write_json(OUTPUT_FILES["tile_guide"], build_tile_guide())
    write_json(OUTPUT_FILES["tile_manifest"], tile_items)
    write_json(OUTPUT_FILES["budget_summary"], budget_summary)
    print(f"frame_items={len(frame_items)} frame_units={budget_summary['frame_estimated_api_units']}")
    print(f"tile_items={len(tile_items)} tile_units={budget_summary['tile_estimated_api_units']}")


if __name__ == "__main__":
    main()