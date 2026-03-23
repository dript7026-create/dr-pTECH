from __future__ import annotations

import json
import math
from pathlib import Path

from bango_pipeline_paths import manifest_output_root, resolve_asset_root


ROOT = Path(__file__).resolve().parent.parent
ASSET_ROOT = resolve_asset_root(ROOT)
RECRAFT_DIR = ROOT / "recraft"
GENERATED_DIR = ASSET_ROOT / "generated" / "clip_blend_id"
MANIFEST_PATH = RECRAFT_DIR / "bango_patoot_production_21000_credit_manifest.json"
PROTOCOL_PATH = GENERATED_DIR / "bango_patoot_clip_blend_id_protocol.json"
SUMMARY_PATH = GENERATED_DIR / "bango_patoot_production_summary.json"
INTAKE_GUIDE_PATH = GENERATED_DIR / "bango_patoot_recraft_intake_guide.json"
FULL_GDD_PATH = ROOT / "BANGO_PATOOT_FULL_GDD.md"
SHORT_GDD_PATH = ROOT / "BANO_GDD.md"
WORLD_PROFILE_PATH = ROOT / "concept_art_package" / "BANGO_PATOOT_WORLD_ENTITIES_PROFILE.md"
CONCEPT_ART_MANIFEST_PATH = ROOT / "concept_art_package" / "bango_patoot_concept_art_manifest.json"
ARTBOOK_PAGE_PLAN_PATH = ROOT / "concept_art_package" / "bango_patoot_artbook_page_plan.json"

TRANSPARENT_NEGATIVE = "opaque background, white background, solid backdrop, text, watermark, logo, cropped body, inconsistent scale, perspective drift, unreadable silhouette, motion blur"
ANGLE_LAYOUT = {
    "front": "top_left",
    "right": "top_right",
    "left": "bottom_left",
    "back": "bottom_right",
}

WORLD_NAMES = [
    ("hive_heart_hub", 7),
    ("tallow_quays", 8),
    ("cathedral_smokestacks", 8),
    ("bone_relay_works", 8),
    ("amber_sump_gardens", 8),
    ("votive_rail_spines", 8),
    ("underwax_reservoir", 8),
    ("sainted_furnace_ward", 8),
    ("ossuary_switchyards", 8),
    ("inkblind_archive", 8),
    ("stormglass_rookeries", 8),
    ("moon_brass_bazaar", 8),
    ("cinder_shrine_maze", 7),
    ("plaguehoney_cloister", 7),
    ("ropebridge_necropolis", 7),
    ("saltcoil_foundries", 7),
    ("blackbell_cisterns", 7),
    ("judgement_apiary_spire", 7),
]

SET_VARIANTS = [
    "gate",
    "causeway",
    "market",
    "shrine",
    "roofline",
    "cistern",
    "catwalk",
    "chamber",
]

NPC_NAMES = [
    "bellwether_abbess",
    "lantern_scrivener",
    "waxbone_surgeon",
    "gutter_psalmist",
    "tallow_caravaner",
    "grave_apiarist",
    "smoke_vintner",
    "thimble_knight",
    "cinder_verger",
    "rail_hermit",
    "hex_draper",
    "ash_huckster",
    "catacomb_marshal",
    "salt_cantor",
    "brass_midwife",
    "drowned_booker",
    "archive_ratifier",
    "mire_clocker",
    "shroud_miller",
    "hive_witness",
    "bone_engraver",
    "votive_porter",
    "tar_dowsing_child",
    "signal_bell_keeper",
    "sump_cartographer",
    "plague_dramaturge",
    "copper_roper",
    "amber_tinsmith",
    "funeral_hostler",
    "stormglass_diviner",
    "ink_spiller",
    "reliquary_debtor",
]

BASIC_ENEMIES = [
    "waxbite_scavenger",
    "bellhook_raider",
    "cinder_maggot",
    "tarblind_lurker",
    "gravewax_hound",
    "rust_psalm_guard",
    "mire_chanter",
    "ropejaw_thief",
    "salt_urchin",
    "lantern_eel",
    "bonejack_vermin",
    "brass_fever_crow",
    "smog_sycophant",
    "hive_ghoul",
    "inklung_rat",
    "gutter_seraph",
    "sump_mantis",
    "glass_licker",
    "copper_drudge",
    "tallow_husk",
    "fungal_beadle",
    "reliquary_mite",
    "ember_clerk",
    "ossuary_bat",
    "spore_lantern_crab",
    "oilveil_cutpurse",
    "crypt_cicada",
    "wicker_heretic",
    "drain_spider",
    "votive_marauder",
]

MID_ENEMIES = [
    "brass_proctor",
    "bone_cartel_enforcer",
    "smokestack_flagellant",
    "wax_ogre",
    "saltcoil_hunter",
    "lantern_duelist",
    "mire_abbot",
    "tar_deacon",
    "blackbell_stalker",
    "copper_fleshsmith",
    "fungal_lancer",
    "stormglass_sniper",
    "archive_tormentor",
    "apiary_reaper",
    "relic_saboteur",
    "gospel_dredger",
    "quarry_judge",
    "cess_basilisk",
    "grave_scripter",
    "shroud_pikeman",
    "votive_warden",
    "bell_militant",
    "honey_blight_knight",
    "sainted_butcher",
]

ELITE_ENEMIES = [
    "wax_cataphract",
    "censer_executioner",
    "tar_prophet",
    "bone_hierophant",
    "stormglass_hydra",
    "saltcoil_myrmidon",
    "apiary_horror",
    "blackbell_dragonfly",
    "reliquary_titan",
    "grave_furnace_keeper",
    "amber_absolution_engine",
    "inkblind_penitent",
    "mire_cherubim",
    "smog_baron",
    "judgement_hornet_queen",
]

MINIBOSSES = [
    "abbot_of_the_sump",
    "the_brazen_pauper",
    "choirmaster_of_ash",
    "maggot_knight_ordinal",
    "liturgy_crane",
    "waxlung_confessor",
    "feral_funeral_train",
    "blind_broker_mneme",
    "tarveil_matron",
    "copper_hangman",
    "stormglass_broodmother",
    "gallows_apiarist",
    "sarcophagus_switchman",
    "reliquary_duke",
    "ossuary_turbine",
    "inkspine_bailiff",
    "shrine_leviathan",
    "the_ninth_beekeeper",
    "plaguehoney_curator",
    "votive_silence",
    "cistern_paladin",
    "amber_docket_tyrant",
]

WORLD_BOSSES = [
    "saint_cinder_vicar",
    "the_hollow_mint",
    "mire_crown_executor",
    "stormglass_colossus",
    "widow_of_blackbells",
    "the_railbound_gospel",
    "ossuary_basilica_engine",
    "queen_of_spent_honey",
    "archivist_of_blind_ink",
    "tar_cathedral_worm",
    "the_saltcoil_patriarch",
    "votive_moon_harbinger",
    "judgement_spire_seraph",
]

FINAL_BOSS_PHASES = [
    ("final_boss_phase_01_pilgrim_form", 28),
    ("final_boss_phase_02_bell_form", 28),
    ("final_boss_phase_03_apiary_form", 28),
    ("final_boss_phase_04_reliquary_form", 27),
    ("final_boss_phase_05_judgement_form", 27),
]

FLORA_NAMES = [
    "candlemoss",
    "grave_reed",
    "waxvine",
    "bellcap_fungus",
    "salt_thistle",
    "sump_lotus",
    "tar_bramble",
    "amber_lichen",
    "shroud_fern",
    "copper_willow",
    "honey_mycelium",
    "mourning_orchid",
]

FAUNA_NAMES = [
    "lantern_moth",
    "gravefin_newt",
    "wax_wren",
    "sump_hare",
    "brass_gecko",
    "bell_toad",
    "ink_dove",
    "tar_beetle",
    "salt_fox",
    "hive_cat",
    "amber_eel",
    "cinder_lark",
]

COMBAT_FX = [
    "horn_rush_arc",
    "satchel_flare",
    "apiary_guardian_burst",
    "wax_sigil_slash",
    "bellshock_ring",
    "tar_spit_impact",
    "bone_spark_fan",
    "cinder_dash_trail",
    "grave_smoke_pop",
    "shrine_hex_burst",
    "salt_shard_spin",
    "reliquary_flash",
    "mire_eruption",
    "stormglass_slice",
    "votive_shockwave",
    "plague_honey_spray",
    "judgement_beam",
    "fungal_puff",
    "brass_gouge",
    "ink_spiral",
    "cathedral_emberfall",
    "blackbell_echo",
    "sainted_guard_parry",
    "final_boss_cataclysm",
]

ENVIRONMENTAL_FX = [
    f"atmospheric_fx_{index:02d}" for index in range(1, 37)
]

ANIMATED_OBJECTS = [
    f"animated_env_object_{index:02d}" for index in range(1, 33)
]

APIARY_NAMES = [
    f"apiary_structure_{index:02d}" for index in range(1, 19)
]


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def build_creative_bible() -> dict:
    concept_manifest = load_json(CONCEPT_ART_MANIFEST_PATH)
    artbook_plan = load_json(ARTBOOK_PAGE_PLAN_PATH)
    concept_count = len(concept_manifest) if isinstance(concept_manifest, list) else 0
    artbook_page_count = len(artbook_plan) if isinstance(artbook_plan, list) else 0
    return {
        "source_materials": [
            {
                "path": str(FULL_GDD_PATH.relative_to(ROOT)),
                "role": "primary_full_gdd",
            },
            {
                "path": str(SHORT_GDD_PATH.relative_to(ROOT)),
                "role": "directional_gdd",
            },
            {
                "path": str(WORLD_PROFILE_PATH.relative_to(ROOT)),
                "role": "world_entities_profile",
            },
            {
                "path": str(CONCEPT_ART_MANIFEST_PATH.relative_to(ROOT)),
                "role": "concept_artbook_manifest",
                "entries": concept_count,
            },
            {
                "path": str(ARTBOOK_PAGE_PLAN_PATH.relative_to(ROOT)),
                "role": "concept_artbook_page_plan",
                "pages": artbook_page_count,
            },
        ],
        "project_identity": "Bango-Patoot: Underhive Nocturne, an original Nintendo 3DS-oriented 3D collectathon action-RPG with duo-character traversal, shrine refinement, and urban horror rooted in folklore inside infrastructure.",
        "world_lore": "A vertical city-underworld behaves like a haunted organism where hive memory, worker ritual, gang rule, machine-cults, rail burial, runoff alchemy, and broadcast coercion overlap.",
        "narrative_drive": "Bango and Patoot descend to rescue Tula from Matra Vey and stop the city from becoming a permanent obedience engine powered by devotion, fear, labor, and memory.",
        "themes": [
            "family obligation without self-erasure",
            "disability-aware perception as strength",
            "companionship as adaptive intelligence",
            "folklore surviving inside infrastructure",
            "ritual versus institution",
            "memory as a civic resource",
        ],
        "motifs": [
            "industrial shrine-fantasy undercity horror",
            "civic memory and worker ritual",
            "comb-metal and patched cloth",
            "wax residue and brass patina",
            "damp brick and rail grease",
            "fungal runoff and chemical honey",
            "archive paper and shrine ceramics",
            "warm communal lanterns versus coercive broadcast light",
        ],
        "design_philosophy": [
            "keep every silhouette original, asymmetrical, tactile, and practical",
            "prioritize 3DS readability and strong landmark legibility",
            "favor authored-looking field gear over generic fantasy ornament",
            "make horror atmospheric, civic, and social rather than gore-dependent",
            "let domestic tenderness and ritual labor coexist with menace",
        ],
        "aesthetic_blueprint": {
            "palette": [
                "honey amber",
                "shrine ivory",
                "oxidized brass",
                "bruise violet",
                "soot black",
                "fungal green",
                "ritual red",
                "wet stone grey",
            ],
            "materials": [
                "comb-metal",
                "patched cloth",
                "wax residue",
                "damp brick",
                "brass patina",
                "rail grease",
                "archive paper",
                "shrine ceramics",
            ],
            "atmosphere": "dense, haunted, civic, devotional, practical, and rescue-driven; never parody, never generic grimdark",
            "feel": "feral, ritual, practical, emotionally distinct, and visibly inseparable",
        },
        "world_blueprint": {
            "hub": "Apiary Junction",
            "districts": [
                "Brassroot Borough",
                "Saint Voltage Arcade",
                "Ossuary Transit",
                "Gutterwake Sewers",
                "Cinder Tenements",
                "Aviary of the Last Broadcast",
                "Witchcoil Spire",
            ],
            "concept_artbook_entries": concept_count,
            "artbook_pages": artbook_page_count,
        },
    }


def build_recraft_intake_guide(creative_bible: dict) -> dict:
    return {
        "intake_language": "bango_patoot_recraft_prompt_contract_v1",
        "global_prompt_prefix": (
            "Original Bango-Patoot visual development for a Nintendo 3DS-ready action-RPG; industrial shrine-fantasy undercity horror with civic memory, worker ritual, folklore inside infrastructure, and a rescue-driven duo bond."
        ),
        "global_style_rules": [
            "preserve original silhouettes and naming",
            "3DS-readable shapes and landmark clarity",
            "tactile practical materials instead of generic fantasy gloss",
            "atmospheric civic horror rather than gore-heavy spectacle",
            "warm communal light contrasted with coercive broadcast light",
        ],
        "creative_bible": creative_bible,
        "category_rules": {
            "character_sheet": "Emphasize asymmetrical, practical field gear, anatomy clarity, readable top-screen silhouettes, and emotionally grounded pose language.",
            "animation_pack": "Preserve duo traversal logic, rescue urgency, and combat clarity with production-sheet staging that remains readable across four angles.",
            "environment_set": "Anchor every environment in the haunted city-body, with navigable macro landmarks, shrine logic, worker history, and world-specific material storytelling.",
            "hud_pack": "Keep UI language diegetic to hive-memory, shrine craft, and salvage-tech while remaining crisp and instantly legible.",
            "armor_set": "Treat armor as lived-in protective gear shaped by labor, ritual duty, salvage, and district-specific wear patterns.",
            "combat_fx": "Effects should feel warded, feral, ritual, and materially coherent with honey, brass, smoke, bone, ink, and shrine energies.",
            "environmental_fx": "Atmospherics must reinforce haunted infrastructure, polluted runoff, signal pressure, shrine heat, and district weather logic.",
            "animated_environment_object": "Objects should read as functional city relics, shrine apparatus, salvage hardware, or haunted civic machinery.",
            "apiary_sheet": "Apiaries are sacred civic maintenance structures, not decorative props; preserve ritual care, hive logic, and mechanical specificity.",
            "item_pack": "Items should feel handcrafted, scavenged, devotional, or infrastructural, never generic loot filler.",
            "weapon_pack": "Weapons should merge salvage, ritual, ward craft, and undercity utility with original silhouettes and believable handling.",
            "ammunition_pack": "Ammunition must feel materially grounded in this world's shrine-tech, salvage-tech, and chemical underhive logic.",
            "item_unique": "Unique items should carry strong story and ritual identity while staying production-readable.",
            "pipeline_calibration": "Calibration sheets must preserve palette stability, silhouette truth, material logic, and downstream depth-map reliability.",
        },
    }


def build_prompt_context(intake_guide: dict, category: str) -> str:
    prefix = intake_guide["global_prompt_prefix"]
    motifs = ", ".join(intake_guide["creative_bible"]["motifs"][:4])
    palette = ", ".join(intake_guide["creative_bible"]["aesthetic_blueprint"]["palette"][:5])
    category_rule = intake_guide["category_rules"].get(category, "Preserve the full Bango-Patoot world bible, material logic, mood, and original silhouette discipline.")
    return f"{prefix} Core motifs: {motifs}. Palette and lighting bias: {palette}, with warm shrine light against coercive signal light. {category_rule}"


def save_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def chunk_count(total: int, capacity: int) -> int:
    return int(math.ceil(total / capacity))


def build_subjects() -> list[dict]:
    subjects: list[dict] = [
        {"name": "bango", "kind": "hero", "sheet_count": 3, "sequence_count": 32 + 132},
        {"name": "patoot", "kind": "companion", "sheet_count": 3, "sequence_count": 17 + 63},
    ]
    subjects.extend({"name": name, "kind": "npc", "sheet_count": 3, "sequence_count": 32} for name in NPC_NAMES)
    subjects.extend({"name": name, "kind": "basic_enemy", "sheet_count": 3, "sequence_count": 25} for name in BASIC_ENEMIES)
    subjects.extend({"name": name, "kind": "mid_enemy", "sheet_count": 3, "sequence_count": 25} for name in MID_ENEMIES)
    subjects.extend({"name": name, "kind": "elite_enemy", "sheet_count": 3, "sequence_count": 25} for name in ELITE_ENEMIES)
    subjects.extend({"name": name, "kind": "miniboss", "sheet_count": 3, "sequence_count": 25} for name in MINIBOSSES)
    subjects.extend({"name": name, "kind": "world_boss", "sheet_count": 3, "sequence_count": 32} for name in WORLD_BOSSES)
    subjects.extend({"name": name, "kind": "final_boss_phase", "sheet_count": 3, "sequence_count": sequence_count} for name, sequence_count in FINAL_BOSS_PHASES)
    subjects.extend({"name": name, "kind": "flora", "sheet_count": 3, "sequence_count": 0} for name in FLORA_NAMES)
    subjects.extend({"name": name, "kind": "fauna", "sheet_count": 3, "sequence_count": 0} for name in FAUNA_NAMES)
    return subjects


def build_environment_sets() -> list[dict]:
    environment_sets = []
    for world_name, set_count in WORLD_NAMES:
        for index in range(set_count):
            variant = SET_VARIANTS[index]
            environment_sets.append(
                {
                    "world": world_name,
                    "set_type": f"{world_name}_{variant}",
                    "tile_count": 13,
                }
            )
    return environment_sets


def make_asset(
    *,
    name: str,
    category: str,
    prompt: str,
    out: str,
    planned_credits: int,
    width: int,
    height: int,
    pipeline_targets: list[str],
    protocol: dict,
    generation_mode: str = "packed_master",
    auto_polish: bool = True,
    prompt_context: str = "",
    budget_bucket: str | None = None,
    deliverable_tags: list[str] | None = None,
    priority_tier: str = "production",
    lineage: dict | None = None,
    generation_stage: str = "recraft_2d_master",
) -> dict:
    effective_targets = list(dict.fromkeys([*pipeline_targets, 'donow', 'illusioncanvas']))
    full_prompt = f"{prompt_context} {prompt}".strip() if prompt_context else prompt
    traceability = {
        "trace_id": f"{category}:{name}",
        "generation_stage": generation_stage,
        "budget_bucket": budget_bucket,
        "deliverable_tags": deliverable_tags or [],
        "source_2d_master": out,
        "polish_target": out.replace("production_raw", "production_polished"),
        "runtime_targets": effective_targets,
        "lineage": lineage or {},
        "stage_contract": [
            "recraft_generation",
            "auto_polish",
            "blender_ingest",
            "rig_or_scene_conversion",
            "runtime_packaging",
            "animation_or_gameplay_binding",
        ],
    }
    return {
        "name": name,
        "category": category,
        "prompt": full_prompt,
        "negative_prompt": TRANSPARENT_NEGATIVE,
        "w": width,
        "h": height,
        "model": "recraftv4",
        "planned_credits": planned_credits,
        "api_units": planned_credits,
        "out": out,
        "transparent_background": True,
        "auto_polish": auto_polish,
        "generation_mode": generation_mode,
        "priority_tier": priority_tier,
        "pipeline_targets": effective_targets,
        "protocol": protocol,
        "traceability": traceability,
    }


def build_character_sheet_assets(subjects: list[dict], intake_guide: dict) -> list[dict]:
    prompt_context = build_prompt_context(intake_guide, "character_sheet")
    sheet_variants = [
        ("turnaround", "4-angle turnaround reference with front top-left, right top-right, left bottom-left, back bottom-right"),
        ("equipment", "equipment, costume, and material breakout sheet using the same 4-angle quadrant layout"),
        ("keypose", "key-pose reference sheet using the same 4-angle quadrant layout and transparent staging"),
    ]
    assets = []
    for subject in subjects:
        for sheet_index, (variant, variant_prompt) in enumerate(sheet_variants, start=1):
            assets.append(
                make_asset(
                    name=f"{subject['name']}_{variant}_sheet_{sheet_index:02d}",
                    category="character_sheet",
                    prompt=(
                        f"Bango-Patoot {subject['kind']} subject {subject['name']} {variant_prompt}, transparent background, "
                        "orthographic readability, stable scale, clean silhouette separation, congruent detailing for downstream texture-depth and hit-precision derivation."
                    ),
                    out=f"production_raw/characters/{subject['name']}_{variant}_sheet_{sheet_index:02d}.png",
                    planned_credits=9,
                    width=2048,
                    height=2048,
                    pipeline_targets=["clipstudio", "blender", "idtech2"],
                    prompt_context=prompt_context,
                    protocol={
                        "layout": "four_angle_quadrant",
                        "angle_positions": ANGLE_LAYOUT,
                        "derived_outputs": ["texture_depth_map", "hit_precision_map"],
                        "subject_kind": subject["kind"],
                    },
                )
            )
    return assets


def build_animation_pack_assets(subjects: list[dict], intake_guide: dict) -> list[dict]:
    prompt_context = build_prompt_context(intake_guide, "animation_pack")
    assets = []
    for subject in subjects:
        if subject["sequence_count"] <= 0:
            continue
        pack_total = chunk_count(subject["sequence_count"], 4)
        for pack_index in range(pack_total):
            start_sequence = pack_index * 4 + 1
            end_sequence = min(subject["sequence_count"], start_sequence + 3)
            assets.append(
                make_asset(
                    name=f"{subject['name']}_animation_pack_{pack_index + 1:02d}",
                    category="animation_pack",
                    prompt=(
                        f"Bango-Patoot animation sequence pack for {subject['name']} covering sequences {start_sequence} through {end_sequence}, "
                        "transparent background, 4 viewing angles, front top-left, right top-right, left bottom-left, back bottom-right, "
                        "key-pose animation planning sheet with lower support rows reserved for congruent depth and hit precision mapping."
                    ),
                    out=f"production_raw/animations/{subject['name']}_animation_pack_{pack_index + 1:02d}.png",
                    planned_credits=8,
                    width=4096,
                    height=4096,
                    pipeline_targets=["clipstudio", "blender", "idtech2"],
                    prompt_context=prompt_context,
                    protocol={
                        "layout": "four_angle_sequence_pack",
                        "angle_positions": ANGLE_LAYOUT,
                        "sequence_span": [start_sequence, end_sequence],
                        "derived_outputs": ["texture_depth_map", "hit_precision_map"],
                    },
                )
            )
    for pack_index in range(chunk_count(61, 4)):
        start_sequence = pack_index * 4 + 1
        end_sequence = min(61, start_sequence + 3)
        assets.append(
            make_asset(
                name=f"bango_patoot_combo_pack_{pack_index + 1:02d}",
                category="animation_pack",
                prompt=(
                    f"Bango-Patoot interconnected combo move pack covering sequences {start_sequence} through {end_sequence}, "
                    "transparent background, cooperative duo choreography, 4 viewing angles in quadrant layout, with congruent depth and hit precision derivation lanes."
                ),
                out=f"production_raw/animations/bango_patoot_combo_pack_{pack_index + 1:02d}.png",
                planned_credits=8,
                width=4096,
                height=4096,
                pipeline_targets=["clipstudio", "blender", "idtech2"],
                prompt_context=prompt_context,
                protocol={
                    "layout": "four_angle_sequence_pack",
                    "angle_positions": ANGLE_LAYOUT,
                    "sequence_span": [start_sequence, end_sequence],
                    "derived_outputs": ["texture_depth_map", "hit_precision_map"],
                    "pair_animation": True,
                },
            )
        )
    return assets


def build_environment_assets(environment_sets: list[dict], intake_guide: dict) -> list[dict]:
    prompt_context = build_prompt_context(intake_guide, "environment_set")
    assets = []
    for entry in environment_sets:
        assets.append(
            make_asset(
                name=f"{entry['set_type']}_tilesheet",
                category="environment_set",
                prompt=(
                    f"Bango-Patoot environment location set for {entry['world']} / {entry['set_type']}, 13 distinct tile types in one transparent-background production sheet, "
                    "orthographic modular presentation, repeat-safe boundaries, atmospheric coherence, and support for later relief, depth, and collision derivation."
                ),
                out=f"production_raw/environments/{entry['world']}/{entry['set_type']}_tilesheet.png",
                planned_credits=30,
                width=4096,
                height=4096,
                pipeline_targets=["clipstudio", "blender", "idtech2"],
                prompt_context=prompt_context,
                protocol={
                    "layout": "thirteen_tile_modular_sheet",
                    "tile_count": entry["tile_count"],
                    "derived_outputs": ["texture_depth_map", "hit_precision_map", "tile_material_masks"],
                    "world": entry["world"],
                },
            )
        )
    return assets


def build_hud_assets(intake_guide: dict) -> list[dict]:
    prompt_context = build_prompt_context(intake_guide, "hud_pack")
    assets = []
    for pack_index in range(chunk_count(200, 20)):
        start_item = pack_index * 20 + 1
        end_item = min(200, start_item + 19)
        assets.append(
            make_asset(
                name=f"hud_pack_{pack_index + 1:02d}",
                category="hud_pack",
                prompt=(
                    f"Bango-Patoot HUD pack covering elements {start_item} through {end_item}, transparent background UI atlas, "
                    "readable 3DS and idTech2-safe iconography, clean separation for alpha, depth, and hit-target derivation."
                ),
                out=f"production_raw/ui/hud_pack_{pack_index + 1:02d}.png",
                planned_credits=20,
                width=2048,
                height=2048,
                pipeline_targets=["clipstudio", "idtech2"],
                prompt_context=prompt_context,
                protocol={
                    "layout": "ui_atlas",
                    "element_span": [start_item, end_item],
                    "derived_outputs": ["hit_precision_map"],
                },
            )
        )
    return assets


def build_pack_assets(total: int, per_pack: int, category: str, prompt_prefix: str, out_prefix: str, credits: int, intake_guide: dict) -> list[dict]:
    prompt_context = build_prompt_context(intake_guide, category)
    assets = []
    for pack_index in range(chunk_count(total, per_pack)):
        start_item = pack_index * per_pack + 1
        end_item = min(total, start_item + per_pack - 1)
        assets.append(
            make_asset(
                name=f"{category}_{pack_index + 1:02d}",
                category=category,
                prompt=(
                    f"{prompt_prefix} covering entries {start_item} through {end_item}, transparent background technical pack, "
                    "4-angle or orthographic arrangement where appropriate, with congruent depth and hit-precision derivation support."
                ),
                out=f"production_raw/{out_prefix}/{category}_{pack_index + 1:02d}.png",
                planned_credits=credits,
                width=3072,
                height=3072,
                pipeline_targets=["clipstudio", "blender", "idtech2"],
                prompt_context=prompt_context,
                protocol={
                    "layout": "packed_reference_sheet",
                    "entry_span": [start_item, end_item],
                    "derived_outputs": ["texture_depth_map", "hit_precision_map"],
                },
            )
        )
    return assets


def build_armor_assets(intake_guide: dict) -> list[dict]:
    prompt_context = build_prompt_context(intake_guide, "armor_set")
    assets = []
    for index in range(1, 33):
        assets.append(
            make_asset(
                name=f"armor_set_{index:02d}",
                category="armor_set",
                prompt=(
                    f"Bango-Patoot armor set {index:02d}, broken into head, shoulder, arm, leg, foot, and hand pieces, transparent background, "
                    "4-angle technical breakdown with congruent texture-depth and hit-precision derivation support."
                ),
                out=f"production_raw/armor/armor_set_{index:02d}.png",
                planned_credits=18,
                width=3072,
                height=3072,
                pipeline_targets=["clipstudio", "blender", "idtech2"],
                prompt_context=prompt_context,
                protocol={
                    "layout": "armor_breakout_sheet",
                    "piece_breakdown": ["head", "shoulder", "arm", "leg", "foot", "hand"],
                    "derived_outputs": ["texture_depth_map", "hit_precision_map"],
                },
            )
        )
    return assets


def build_fx_assets(intake_guide: dict) -> list[dict]:
    combat_prompt_context = build_prompt_context(intake_guide, "combat_fx")
    environmental_prompt_context = build_prompt_context(intake_guide, "environmental_fx")
    assets = []
    for name in COMBAT_FX:
        assets.append(
            make_asset(
                name=name,
                category="combat_fx",
                prompt=(
                    f"Bango-Patoot combat effect spritesheet for {name}, transparent background, frames arranged horizontally on a single row, "
                    "lower rows contain congruent depth and hit-mapped versions of each frame, with 4 viewpoint variants packaged for production slicing."
                ),
                out=f"production_raw/fx/combat/{name}.png",
                planned_credits=16,
                width=4096,
                height=2048,
                pipeline_targets=["clipstudio", "blender", "idtech2"],
                prompt_context=combat_prompt_context,
                protocol={
                    "layout": "horizontal_spritesheet_with_depth_hit_rows",
                    "angle_views": 4,
                    "derived_outputs": ["depth_row", "hit_row"],
                },
            )
        )
    for name in ENVIRONMENTAL_FX:
        assets.append(
            make_asset(
                name=name,
                category="environmental_fx",
                prompt=(
                    f"Bango-Patoot environmental effect animation for {name}, full transparency, 360-degree angle-mapped atmospheric quality, "
                    "coherent gameworld volumetric presentation with separate depth and hit derivation support."
                ),
                out=f"production_raw/fx/environment/{name}.png",
                planned_credits=18,
                width=4096,
                height=4096,
                pipeline_targets=["clipstudio", "blender", "idtech2"],
                prompt_context=environmental_prompt_context,
                protocol={
                    "layout": "angle_mapped_360_sheet",
                    "coverage_degrees": 360,
                    "derived_outputs": ["texture_depth_map", "hit_precision_map"],
                },
            )
        )
    return assets


def build_animated_object_assets(intake_guide: dict) -> list[dict]:
    object_prompt_context = build_prompt_context(intake_guide, "animated_environment_object")
    apiary_prompt_context = build_prompt_context(intake_guide, "apiary_sheet")
    assets = []
    for name in ANIMATED_OBJECTS:
        assets.append(
            make_asset(
                name=name,
                category="animated_environment_object",
                prompt=(
                    f"Bango-Patoot animated environmental object sheet for {name}, transparent background, modular object presentation, "
                    "4-angle state coverage, with congruent texture-depth and hit precision derivation support."
                ),
                out=f"production_raw/animated_objects/{name}.png",
                planned_credits=16,
                width=3072,
                height=3072,
                pipeline_targets=["clipstudio", "blender", "idtech2"],
                prompt_context=object_prompt_context,
                protocol={
                    "layout": "four_angle_object_sheet",
                    "angle_positions": ANGLE_LAYOUT,
                    "derived_outputs": ["texture_depth_map", "hit_precision_map"],
                },
            )
        )
    for name in APIARY_NAMES:
        assets.append(
            make_asset(
                name=name,
                category="apiary_sheet",
                prompt=(
                    f"Bango-Patoot apiary structure and animation sheet for {name}, transparent background, 4-angle layout, animated hive behavior callouts, "
                    "and congruent texture-depth and hit precision derivation support."
                ),
                out=f"production_raw/apiaries/{name}.png",
                planned_credits=18,
                width=3072,
                height=3072,
                pipeline_targets=["clipstudio", "blender", "idtech2"],
                prompt_context=apiary_prompt_context,
                protocol={
                    "layout": "four_angle_object_sheet",
                    "angle_positions": ANGLE_LAYOUT,
                    "derived_outputs": ["texture_depth_map", "hit_precision_map"],
                },
            )
        )
    return assets


def build_misc_assets(intake_guide: dict) -> list[dict]:
    unique_item_prompt_context = build_prompt_context(intake_guide, "item_unique")
    calibration_prompt_context = build_prompt_context(intake_guide, "pipeline_calibration")
    assets = build_pack_assets(123, 6, "item_pack", "Bango-Patoot item pack", "items", 14, intake_guide)
    assets.extend(build_pack_assets(127, 6, "weapon_pack", "Bango-Patoot weapon pack with melee and projectile armaments", "weapons", 16, intake_guide))
    assets.extend(build_pack_assets(12, 6, "ammunition_pack", "Bango-Patoot ammunition pack", "ammunition", 20, intake_guide))
    assets.append(
        make_asset(
            name="honey_vial_persistent_refuel_container",
            category="item_unique",
            prompt=(
                "Bango-Patoot honey vial persistent refillable healing container, transparent background, 4-angle technical item sheet, "
                "closed and active states, with congruent depth and hit precision derivation support."
            ),
            out="production_raw/items/honey_vial_persistent_refuel_container.png",
            planned_credits=19,
            width=2048,
            height=2048,
            pipeline_targets=["clipstudio", "blender", "idtech2"],
            prompt_context=unique_item_prompt_context,
            protocol={
                "layout": "four_angle_object_sheet",
                "angle_positions": ANGLE_LAYOUT,
                "derived_outputs": ["texture_depth_map", "hit_precision_map"],
            },
        )
    )
    for index in range(1, 9):
        assets.append(
            make_asset(
                name=f"pipeline_calibration_sheet_{index:02d}",
                category="pipeline_calibration",
                prompt=(
                    f"Bango-Patoot pipeline calibration sheet {index:02d}, transparent background reference for material response, palette stability, depth-map integrity, "
                    "and hit-precision silhouette checking across Clip Studio, Blender, and idTech2."
                ),
                out=f"production_raw/calibration/pipeline_calibration_sheet_{index:02d}.png",
                planned_credits=20,
                width=2048,
                height=2048,
                pipeline_targets=["clipstudio", "blender", "idtech2"],
                prompt_context=calibration_prompt_context,
                protocol={
                    "layout": "calibration_grid",
                    "derived_outputs": ["texture_depth_map", "hit_precision_map"],
                },
            )
        )
    return assets


def build_protocol(summary: dict) -> dict:
    return {
        "protocol_name": "bango_patoot_clip_blend_id_production_pipeline",
        "protocol_version": "2026-03-13.production",
        "focus": "Bango-Patoot full asset intake from Recraft and Clip Studio through auto-polish, Blender conversion, DoNOW runtime ingest, IllusionCanvas runtime bundling, and idTech2-ready registry output.",
        "asset_rules": {
            "transparent_background_required": True,
            "four_angle_quadrant_layout": ANGLE_LAYOUT,
            "derived_outputs": ["texture_depth_map", "hit_precision_map"],
            "combat_fx_layout": "single horizontal frame row with lower depth and hit rows; 4 viewpoint variants per animation set",
            "environmental_fx_layout": "360-degree angle-mapped transparent atmospheric sheet",
            "environment_set_rule": "137 distinct location set types across 17 worlds plus 1 hub world, each carrying 13 tile types",
        },
        "automation_flow": [
            {
                "step": "recraft_generation",
                "tool": "egosphere/tools/run_recraft_manifest.py",
                "output_root": str(ASSET_ROOT / "production_raw"),
            },
            {
                "step": "clipstudio_auto_polish",
                "tool": "readAIpolish/readAIpolish_cli.py",
                "input_root": str(ASSET_ROOT / "production_raw"),
                "output_root": str(ASSET_ROOT / "production_polished"),
            },
            {
                "step": "clipstudio_ingest",
                "tool": "drIpTech_ClipStudio_Plug-Ins/pipeline_bridge",
                "output_root": str(ASSET_ROOT / "generated" / "clip_blend_id" / "clipstudio_ingest_manifest.json"),
            },
            {
                "step": "blender_conversion",
                "tool": "bango-patoot_3DS/tools/run_bango_sheet_autorig.py",
                "output_root": str(ASSET_ROOT / "generated" / "clip_blend_id" / "blender_ingest_manifest.json"),
            },
            {
                "step": "donow_runtime",
                "tool": "DoENGINE/tools/build_donow_runtime_manifest.py",
                "output_root": str(ASSET_ROOT / "generated" / "clip_blend_id" / "donow_runtime_manifest.json"),
            },
            {
                "step": "illusioncanvas_runtime",
                "tool": "IllusionCanvasInteractive/tools/build_illusioncanvas_bundle.py",
                "output_root": str(ASSET_ROOT / "generated" / "clip_blend_id" / "illusioncanvas_runtime_manifest.json"),
            },
            {
                "step": "illusioncanvas_ui_skin",
                "tool": "IllusionCanvasInteractive/tools/build_illusioncanvas_ui_skin.py",
                "output_root": str(ASSET_ROOT / "generated" / "clip_blend_id" / "illusioncanvas_ui_skin.json"),
            },
            {
                "step": "illusioncanvas_studio_session",
                "tool": "IllusionCanvasInteractive/run_illusioncanvas_studio.py",
                "output_root": str(ASSET_ROOT / "generated" / "clip_blend_id" / "illusioncanvas_studio_session.json"),
            },
            {
                "step": "idtech2_registry",
                "tool": "drIpTECH_idTech2Plug-Ins/drIpTECH_idTech2_autofactorintegration.c",
                "output_root": str(ASSET_ROOT / "generated" / "clip_blend_id" / "idtech2_runtime_registry.json"),
            },
        ],
        "summary": summary,
    }


def build_manifest() -> tuple[dict, dict]:
    creative_bible = build_creative_bible()
    intake_guide = build_recraft_intake_guide(creative_bible)
    subjects = build_subjects()
    environment_sets = build_environment_sets()
    assets = []
    assets.extend(build_character_sheet_assets(subjects, intake_guide))
    assets.extend(build_animation_pack_assets(subjects, intake_guide))
    assets.extend(build_environment_assets(environment_sets, intake_guide))
    assets.extend(build_hud_assets(intake_guide))
    assets.extend(build_armor_assets(intake_guide))
    assets.extend(build_fx_assets(intake_guide))
    assets.extend(build_animated_object_assets(intake_guide))
    assets.extend(build_misc_assets(intake_guide))

    total_credits = sum(asset["planned_credits"] for asset in assets)
    summary = {
        "raw_requirements": {
            "character_sheets": 501,
            "raw_keypose_sequences": 4158,
            "environment_location_sets": 137,
            "environment_tile_types": 1781,
            "hud_elements": 200,
            "items": 123,
            "weapons": 127,
            "ammunition_types": 12,
            "armor_sets": 32,
            "combat_fx_sets": 24,
            "environmental_fx_sets": 36,
            "animated_environment_objects": 32,
            "apiary_sheets": 18,
        },
        "packed_generation_counts": {
            "character_sheet_assets": len([asset for asset in assets if asset["category"] == "character_sheet"]),
            "animation_pack_assets": len([asset for asset in assets if asset["category"] == "animation_pack"]),
            "environment_set_assets": len([asset for asset in assets if asset["category"] == "environment_set"]),
            "total_assets": len(assets),
        },
        "budget": {
            "requested_budget": 15000,
            "escalated_budget": 21000,
            "allocated_credits": total_credits,
            "budget_decision": "21000 credits selected because the full production protocol exceeds the earlier 15000-credit ceiling once all packed master sheets and downstream derived-map obligations are represented.",
        },
    }

    manifest = {
        "manifest_name": "bango_patoot_production_21000_credit_pass",
        "manifest_version": "2026-03-13.production",
        "intent": "Full Bango-Patoot production asset generation pass for the Clip Studio -> auto-polish -> Blender -> DoNOW -> IllusionCanvas -> idTech2 streamlined pipeline.",
        "asset_root": str(ASSET_ROOT),
        "output_root": manifest_output_root(ASSET_ROOT),
        "budget": summary["budget"],
        "shared_prompt_appendix": "Transparent background required. Preserve clean silhouette fidelity. Use orthographic or production-reference presentation. For 4-angle sheets place front top-left, right top-right, left bottom-left, and back bottom-right. Support later automated texture-depth and hit-precision derivation. Apply the source-driven Bango-Patoot creative bible: original silhouettes, industrial shrine-fantasy undercity horror, civic memory, worker ritual, tactile materials, warm shrine light against coercive broadcast light, and 3DS-readable landmark clarity.",
        "automation_profile": "clip_blend_id_do_streamlined",
        "source_materials": creative_bible["source_materials"],
        "creative_bible": creative_bible,
        "recraft_intake_guide": intake_guide,
        "assets": assets,
    }
    protocol = build_protocol(summary)
    protocol["source_materials"] = creative_bible["source_materials"]
    protocol["creative_bible"] = creative_bible
    protocol["recraft_intake_guide"] = intake_guide
    return manifest, protocol


def main() -> int:
    manifest, protocol = build_manifest()
    save_json(MANIFEST_PATH, manifest)
    save_json(PROTOCOL_PATH, protocol)
    save_json(SUMMARY_PATH, protocol["summary"])
    save_json(INTAKE_GUIDE_PATH, protocol["recraft_intake_guide"])
    print(json.dumps({
        "manifest": str(MANIFEST_PATH),
        "protocol": str(PROTOCOL_PATH),
        "summary": str(SUMMARY_PATH),
        "intake_guide": str(INTAKE_GUIDE_PATH),
        "allocated_credits": protocol["summary"]["budget"]["allocated_credits"],
        "total_assets": protocol["summary"]["packed_generation_counts"]["total_assets"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())