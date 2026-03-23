#!/usr/bin/env python3
"""Generate the WialWohm Recraft asset manifest (195 sheets).

Run:
    python generate_wialwohm_manifest.py

Writes wialwohm_manifest.json in the same directory.
"""

import json, os, pathlib

OUTDIR = "../../ORBEngine/assets/wial_wohm"
MANIFEST = []

# --------------------------------------------------------------------------- #
# Style constants
# --------------------------------------------------------------------------- #
STYLE_CREATURE = (
    "dark fantasy creature concept art sheet, painterly style, muted earth "
    "tones with bioluminescent teal and amber accents, wet organic textures, "
    "Lovecraftian ooze-punk aesthetic, multiple sprite poses on transparent "
    "background, game asset sheet"
)
STYLE_NAV = (
    "first-person dungeon view, Shadowgate-style, dark atmospheric perspective, "
    "painterly digital art, moody lighting with volumetric fog, "
    "game navigation panel"
)
STYLE_FX = (
    "game visual effect sprite sheet, dark fantasy, glowing particle effects, "
    "transparent background, pixel-painterly hybrid style, animation frames "
    "arranged in a grid"
)
STYLE_ENV_FX = (
    "small ambient environmental effect animation sheet, dark fantasy, "
    "subtle atmospheric particles, transparent background, animation strip"
)
STYLE_FARM = (
    "top-down farm and agriculture map tile sheet, dark fantasy pastoral, "
    "muted greens and browns with bioluminescent crop glow, painterly game art"
)
STYLE_FOOD = (
    "cooking ingredient and prepared dish icon sheet, dark fantasy style, "
    "rich warm tones, painterly food art, game inventory icons arranged in grid"
)
STYLE_ENEMY = (
    "dark fantasy enemy creature concept art sheet, Lovecraftian horror, "
    "wet organic textures, bioluminescent accents, multiple poses, "
    "game sprite sheet on dark background"
)

def add(name, prompt, w, h, subdir, filename):
    MANIFEST.append({
        "name": name,
        "prompt": prompt,
        "w": w,
        "h": h,
        "out": f"{OUTDIR}/{subdir}/{filename}"
    })

# =========================================================================== #
# 1. EGG STATE WIAL (1 sheet)
# =========================================================================== #
add(
    "wial_egg",
    f"A mysterious bioluminescent egg nestled in dark organic matter, pulsing "
    f"with inner teal and amber light, translucent shell showing a curled "
    f"creature silhouette within, multiple angles and glow states in a sprite "
    f"sheet grid layout. {STYLE_CREATURE}",
    1024, 1024, "wials", "wial_egg_state.png"
)

# =========================================================================== #
# 2. WIAL EVOLUTIONS (12 sheets: 3 tiers × 4 branches)
# =========================================================================== #
BRANCHES = [
    ("marsh",  "amphibian marsh creature, webbed limbs, mossy shell plates, swamp bioluminescence"),
    ("tide",   "aquatic tide creature, sleek fins, coral-encrusted armor, deep-sea glow"),
    ("ember",  "volcanic ember creature, cracked magma skin, smoldering vents, fire-glow eyes"),
    ("shade",  "shadowy void creature, wispy tendrils, dark mist exoskeleton, spectral purple glow"),
]
TIERS = [
    ("sprout", "small juvenile form, curious expression, compact body"),
    ("surge",  "muscular adolescent form, aggressive stance, evolved appendages and armor plates"),
    ("apex",   "towering final evolution, majestic and terrifying, full armor and weapons, alpha predator"),
]
for ti, (tier_name, tier_desc) in enumerate(TIERS, 1):
    for bi, (branch_name, branch_desc) in enumerate(BRANCHES, 1):
        idx = (ti - 1) * 4 + bi
        add(
            f"wial_t{ti}_{branch_name}",
            f"Wial evolution tier {ti} ({tier_name}), {branch_name} branch: "
            f"{branch_desc}, {tier_desc}. Full character sprite sheet with "
            f"idle, walk, attack, hurt, and special poses. {STYLE_CREATURE}",
            1024, 1024, "wials", f"wial_tier{ti}_{branch_name}.png"
        )

# =========================================================================== #
# 3. COMBAT ANIMATION FX (25 sheets)
# =========================================================================== #
COMBAT_FX = [
    "melee slash arc, teal energy blade trail",
    "heavy slam shockwave, ground crack radial burst",
    "claw swipe triple strike, amber claw marks",
    "bite attack with dripping ooze particles",
    "tail whip sweep, circular motion blur",
    "projectile launch, bioluminescent orb forming and firing",
    "projectile impact explosion, teal and amber sparks",
    "shield block ripple, hexagonal energy barrier flash",
    "parry spark burst, metallic clang energy ring",
    "dodge afterimage trail, translucent ghost copies",
    "critical hit starburst, screen-flash radial lines",
    "poison cloud expanding, green miasma particles",
    "fire breath cone, ember and smoke plume",
    "ice crystal formation, frost spike eruption",
    "lightning chain arc, branching electric bolts",
    "heal pulse ring, warm amber glow expanding outward",
    "buff aura shimmer, rising golden particles",
    "debuff curse spiral, descending purple vortex",
    "stagger stun stars, orbiting daze symbols",
    "death dissolve, creature breaking into glowing ash",
    "summon circle, arcane glyphs rotating and glowing",
    "ground eruption, tentacles bursting from floor",
    "sonic screech wave, concentric distortion rings",
    "shadow teleport, dark mist implode and explode",
    "ultimate burst, massive radial energy nova with debris",
]
for i, desc in enumerate(COMBAT_FX, 1):
    add(
        f"combat_fx_{i:02d}",
        f"Combat animation effect: {desc}. 6-frame animation grid "
        f"arranged in rows on square canvas. {STYLE_FX}",
        1024, 1024, "combat_fx", f"combat_fx_{i:02d}.png"
    )

# =========================================================================== #
# 4. NAVIGATION SHEETS (70 total across 6 environment types)
# =========================================================================== #
NAV_ENVS = [
    ("gloom_caverns",   "dark wet limestone caverns, dripping stalactites, phosphorescent fungus on walls, underground river mist", 12),
    ("sunken_temple",   "submerged ancient temple, barnacle-crusted stone columns, faded murals, waterlogged corridors lit by eerie green light", 12),
    ("mausoleum",       "decrepit stone mausoleum, cracked sarcophagi along walls, cobwebs, faded inscriptions, dim candle glow", 12),
    ("sewer",           "industrial sewer tunnels, rusted pipes and grates, flowing murky water, chain-link fences, flickering utility lights", 12),
    ("frost_cavern",    "frozen ice cavern, crystalline walls, icicle formations, pale blue ambient glow, frost-covered stone floor", 11),
    ("cyber_tunnels",   "cyberpunk maintenance tunnels, exposed wiring and conduits, neon signage, holographic graffiti, steam vents", 11),
]
NAV_VIEWS = [
    ("corridor_forward",    "straight corridor stretching ahead, walls converging to a distant vanishing point"),
    ("t_intersection",      "T-shaped intersection, corridor branching left and right with a wall ahead"),
    ("left_turn",           "corridor turning sharply to the left, right wall visible ahead"),
    ("right_turn",          "corridor turning sharply to the right, left wall visible ahead"),
    ("dead_end",            "dead end with ornate wall detail, no passage forward"),
    ("stairs_down",         "stone staircase descending into deeper darkness"),
    ("stairs_up",           "stone staircase ascending toward faint light above"),
    ("door_closed",         "massive closed door or gate blocking the passage, ornate carvings"),
    ("door_open",           "doorway standing open revealing a chamber beyond, light spilling through"),
    ("large_chamber",       "vast open chamber with high ceiling, pillars, and distant walls"),
    ("narrow_passage",      "tight narrow passage barely wide enough to squeeze through"),
    ("special_feature",     "unique environmental feature: altar, machine, or anomaly in a small room"),
]
for env_name, env_desc, count in NAV_ENVS:
    for vi in range(count):
        view_name, view_desc = NAV_VIEWS[vi]
        add(
            f"nav_{env_name}_{view_name}",
            f"First-person navigation view: {view_desc}. Environment: {env_desc}. "
            f"Dark atmospheric lighting, detailed wall and floor textures. {STYLE_NAV}",
            1344, 768, f"navigation/{env_name}", f"{env_name}_{view_name}.png"
        )

# =========================================================================== #
# 5. ENEMY SHEETS (30)
# =========================================================================== #
ENEMIES = [
    # Gloom Caverns enemies (6)
    ("cave_crawler",       "blind cave-crawling arthropod, many legs, pale chitinous shell, antennae"),
    ("fungal_shambler",    "shambling humanoid covered in bioluminescent fungi, spore clouds"),
    ("rock_mimic",         "stone-textured ambush predator disguised as cave wall, gaping maw"),
    ("crystal_bat",        "large bat with crystalline wing membranes, sonic shriek pose"),
    ("cave_leech",         "giant leech-like creature coiled on ceiling, dripping saliva"),
    ("stalactite_horror",  "creature fused with stalactites, dropping from above, sharp limbs"),
    # Sunken Temple enemies (5)
    ("drowned_priest",     "waterlogged undead temple priest, tattered robes, barnacle-crusted staff"),
    ("temple_guardian",    "stone golem statue animated by ancient magic, crumbling but powerful"),
    ("eel_swarm",          "writhing mass of electric eels forming a humanoid shape"),
    ("coral_knight",       "armored warrior encrusted with living coral, sword and shield"),
    ("abyssal_idol",       "floating animated temple idol, multiple arms, glowing sigil eye"),
    # Mausoleum enemies (5)
    ("crypt_wraith",       "translucent ghost emerging from sarcophagus, skeletal features"),
    ("bone_collector",     "hunched creature assembling itself from scattered bones"),
    ("tomb_spider",        "massive spider nesting in coffins, wrapped corpse decorations"),
    ("embalmer",           "tall gaunt figure with surgical tools, preservation jars on belt"),
    ("death_moth",         "giant moth with skull-pattern wings, hypnotic dust trail"),
    # Sewer enemies (5)
    ("sludge_rat",         "oversized mutant rat dripping with toxic sludge, glowing eyes"),
    ("pipe_wurm",          "segmented worm creature emerging from broken pipe, acid drool"),
    ("grate_lurker",       "flattened predator squeezing through floor grates, extending claws"),
    ("sewer_cultist",      "hooded humanoid cultist in waders, rusted ritual blade"),
    ("bile_toad",          "bloated toxic toad, inflating throat sac, projectile venom"),
    # Frost Cavern enemies (5)
    ("frost_elemental",    "humanoid ice formation, jagged crystal limbs, freezing aura"),
    ("snow_stalker",       "white-furred predator, camouflaged, pouncing pose"),
    ("ice_wraith",         "spectral figure trailing frozen mist, blue ethereal glow"),
    ("glacier_beetle",     "armored beetle with ice-encrusted shell, ramming horn"),
    ("frozen_revenant",    "ancient warrior preserved in ice, cracking free, ice-blade weapon"),
    # Cyber Tunnel enemies (4)
    ("haywire_drone",      "malfunctioning maintenance drone, sparking, erratic laser eye"),
    ("wire_phantom",       "humanoid shape formed from tangled wires and cables, electrified"),
    ("neon_slime",         "glowing neon-colored slime creature, absorbing light around it"),
    ("rogue_mech",         "small bipedal security mech, damaged plating, targeting laser"),
]
for i, (enemy_name, enemy_desc) in enumerate(ENEMIES, 1):
    add(
        f"enemy_{enemy_name}",
        f"Enemy creature: {enemy_desc}. Full character sprite sheet with idle, "
        f"patrol, attack, hurt, and death poses arranged in rows. {STYLE_ENEMY}",
        1024, 1024, "enemies", f"enemy_{i:02d}_{enemy_name}.png"
    )

# =========================================================================== #
# 6. AMBIENT FX (6 sheets)
# =========================================================================== #
AMBIENT_FX = [
    ("rain_drip",    "rain drops and dripping water animation, vertical streaks and splash rings"),
    ("fog_drift",    "drifting fog wisps and mist tendrils, slowly curling and dissipating"),
    ("fireflies",    "floating bioluminescent firefly particles, pulsing teal and amber dots"),
    ("dust_motes",   "floating dust particles in a light shaft, slow drift and sparkle"),
    ("shimmer",      "wet surface light shimmer and caustic reflections, rippling patterns"),
    ("drip_ooze",    "viscous ooze dripping from ceiling, stretching and pooling on floor"),
]
for i, (fx_name, fx_desc) in enumerate(AMBIENT_FX, 1):
    add(
        f"ambient_{fx_name}",
        f"Ambient environmental effect: {fx_desc}. 8-frame animation grid "
        f"layout, transparent background. {STYLE_ENV_FX}",
        1024, 1024, "ambient_fx", f"ambient_{i:02d}_{fx_name}.png"
    )

# =========================================================================== #
# 7. FARM NAVIGATION & AGRICULTURE (17 sheets)
# =========================================================================== #
FARM_SHEETS = [
    ("farm_overview_spring",  "overhead farm overview in spring, fresh green crops sprouting, irrigation channels flowing, small buildings"),
    ("farm_overview_summer",  "overhead farm overview in summer, lush mature crops, golden sunlight, buzzing insects"),
    ("farm_overview_autumn",  "overhead farm overview in autumn, harvest-ready fields, amber and orange foliage, wind"),
    ("farm_overview_winter",  "overhead farm overview in winter, dormant brown fields, frost patterns, snow dusting"),
    ("crop_field_planting",   "close-up crop field view during planting phase, tilled soil rows, seed holes, hand tools"),
    ("crop_field_growing",    "close-up crop field with growing plants, green shoots at various stages, support stakes"),
    ("crop_field_harvest",    "close-up crop field ready for harvest, ripe bioluminescent fruits and vegetables"),
    ("crop_field_fallow",     "close-up fallow field, bare soil recovering, scattered old stalks and compost"),
    ("barn_interior",         "rustic barn interior, hay bales, tool racks, stored harvest crates, warm light"),
    ("greenhouse",            "glass greenhouse with exotic glowing plants, humidity condensation, grow lights"),
    ("storage_cellar",        "underground storage cellar, barrels and jars of preserved food, cool stone walls"),
    ("mill_exterior",         "water-powered grain mill building, turning wheel, sacks of flour, stone foundation"),
    ("irrigation_source",     "natural spring water source feeding irrigation channels, valve controls, pipes"),
    ("irrigation_channels",   "network of irrigation channels between crop rows, flowing water, sluice gates"),
    ("aqueduct_system",       "elevated aqueduct carrying water across the farm, stone arches, moss-covered"),
    ("farm_path_main",        "main dirt path through the farm, cart tracks, fences, signposts to areas"),
    ("farm_path_orchard",     "winding path through a dark orchard, bioluminescent fruit trees, fallen leaves"),
]
for i, (farm_name, farm_desc) in enumerate(FARM_SHEETS, 1):
    add(
        f"farm_{farm_name}",
        f"Farm tile sheet: {farm_desc}. Dark fantasy pastoral aesthetic with "
        f"bioluminescent accents. {STYLE_FARM}",
        1024, 1024, "farm", f"farm_{i:02d}_{farm_name}.png"
    )

# =========================================================================== #
# 8. COOKING & FOOD (34 sheets)
# =========================================================================== #
COOKING_SHEETS = [
    # Raw ingredients (10)
    ("raw_roots",        "assorted raw root vegetables, dark earthy tones, bioluminescent tubers"),
    ("raw_mushrooms",    "variety of wild mushrooms, glowing caps, spore-dusted stems"),
    ("raw_fish",         "fresh caught fish and eels, iridescent scales, wet sheen"),
    ("raw_meat",         "cuts of dark game meat, marbled textures, bone-in portions"),
    ("raw_grains",       "harvested grain sheaves and loose kernels, golden and dark varieties"),
    ("raw_herbs",        "bundles of fresh herbs, aromatic leaves, flowering tops"),
    ("raw_fruits",       "bioluminescent fruits, translucent skin showing glowing flesh"),
    ("raw_eggs",         "various creature eggs, speckled shells, different sizes"),
    ("raw_spices",       "ground and whole spices in small bowls, colorful powders"),
    ("raw_honey",        "jars and combs of dark amber honey, dripping viscosity"),
    # Cooking processes (10)
    ("station_campfire",  "open campfire cooking station, spit roast, hanging pot, flame glow"),
    ("station_cauldron",  "large iron cauldron on stone hearth, bubbling stew, steam rising"),
    ("station_oven",      "clay brick oven with glowing coals, bread rising inside"),
    ("station_smoker",    "wooden smoker rack with hanging meats and fish, aromatic smoke"),
    ("station_fermenter", "fermentation crocks and barrels, bubbling lids, aging process"),
    ("station_mortar",    "stone mortar and pestle, grinding spices, powder dust cloud"),
    ("station_cutting",   "wooden cutting board with knife, sliced ingredients, juice pooling"),
    ("station_drying",    "drying rack with herbs and mushrooms, air-dried preservation"),
    ("station_mixing",    "mixing bowl with whisk, batter and dough being worked"),
    ("station_plating",   "plating station with arranged dishes, garnish tools, serving presentation"),
    # Prepared dishes (10)
    ("dish_stew",         "hearty dark stew in stone bowl, chunks of meat and vegetables, steam"),
    ("dish_roast",        "roasted whole creature on platter, crispy skin, root vegetable garnish"),
    ("dish_bread",        "freshly baked dark bread loaf, crusty exterior, steaming interior"),
    ("dish_pie",          "deep dish meat and mushroom pie, golden crust, filling visible"),
    ("dish_soup",         "clear broth soup in wooden bowl, floating herbs and egg"),
    ("dish_salad",        "bioluminescent leaf salad with fruit and nut garnish, edible flowers"),
    ("dish_porridge",     "thick grain porridge with honey drizzle and berry compote"),
    ("dish_skewers",      "grilled meat and vegetable skewers, char marks, dipping sauce"),
    ("dish_dumplings",    "steamed dumplings in bamboo basket, savory filling visible"),
    ("dish_cake",         "layered dark celebration cake, bioluminescent frosting and fruit topping"),
    # Special/rare recipes (4)
    ("rare_elixir",       "glowing magical elixir in crystal vial, swirling particles, healing potion"),
    ("rare_feast",        "grand feast spread across a long table, multiple dishes, goblets, candles"),
    ("rare_preserved",    "collection of rare preserved delicacies in ornate jars, wax-sealed, labeled"),
    ("rare_wial_treat",   "special Wial creature treat, custom-crafted food that boosts evolution, glowing"),
]
for i, (food_name, food_desc) in enumerate(COOKING_SHEETS, 1):
    add(
        f"food_{food_name}",
        f"Food and cooking icon sheet: {food_desc}. Grid of icons showing the "
        f"item from multiple angles or states. {STYLE_FOOD}",
        1024, 1024, "cooking", f"food_{i:02d}_{food_name}.png"
    )

# =========================================================================== #
# Write manifest
# =========================================================================== #
out_path = pathlib.Path(__file__).parent / "wialwohm_manifest.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(MANIFEST, f, indent=2, ensure_ascii=False)

print(f"Wrote {len(MANIFEST)} entries to {out_path}")

# Category summary
categories = {}
for entry in MANIFEST:
    parts = entry["out"].split("/")
    cat = parts[4] if len(parts) > 4 else "root"
    categories[cat] = categories.get(cat, 0) + 1
for cat, count in sorted(categories.items()):
    print(f"  {cat}: {count}")
