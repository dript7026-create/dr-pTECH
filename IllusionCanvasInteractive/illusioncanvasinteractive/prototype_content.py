from __future__ import annotations

from copy import deepcopy


def _object(
    object_id: str,
    object_type: str,
    x: float,
    y: float,
    label: str,
    **extra,
) -> dict:
    result = {
        "id": object_id,
        "type": object_type,
        "x": x,
        "y": y,
        "label": label,
    }
    result.update(extra)
    return result


def _enemy(name: str, x: float, hp: int, aggression: float, armor: float, posture: float, **extra) -> dict:
    result = {
        "name": name,
        "x": x,
        "hp": hp,
        "aggression": aggression,
        "armor": armor,
        "posture": posture,
    }
    result.update(extra)
    return result


def _make_room(
    room_id: str,
    name: str,
    backdrop_asset: str,
    palette: list[str],
    parallax: list[dict],
    objective: str,
    tutorial_tip: str,
    left_exit,
    right_exit,
    *,
    danger: int = 1,
    safe_room: bool = False,
    platforms: list[dict] | None = None,
    hazards: list[dict] | None = None,
    encounter_zones: list[dict] | None = None,
    objects: list[dict] | None = None,
    enemies: list[dict] | None = None,
    popup: dict | None = None,
    rescue: dict | None = None,
) -> dict:
    exits = {}
    if left_exit is not None:
        exits["left"] = left_exit
    if right_exit is not None:
        exits["right"] = right_exit
    return {
        "id": room_id,
        "name": name,
        "safe_room": safe_room,
        "danger": danger,
        "objective": objective,
        "tutorial_tip": tutorial_tip,
        "popup": popup or {
            "template": "tutorial_tip_shell",
            "title": name,
            "text": objective,
        },
        "palette": palette,
        "parallax": parallax,
        "backdrop_asset": backdrop_asset,
        "layout": {
            "platforms": platforms or [{"id": f"{room_id}_floor", "x1": 0, "x2": 100, "y": 0, "color": "#695950"}],
            "hazards": hazards or [],
            "encounter_zones": encounter_zones or [],
            "objects": objects or [],
        },
        "exits": exits,
        "rescue": rescue,
        "enemies": enemies or [],
    }


def build_prototype_expansion() -> dict:
    player_moves = [
        {"id": "salt_cut", "name": "Salt Cut", "input": "X", "category": "ground_combo", "base_power": 1.0, "precision_window": 4, "weapon_points": 1},
        {"id": "rust_hook", "name": "Rust Hook", "input": "X,X", "category": "ground_combo", "base_power": 1.18, "precision_window": 4, "weapon_points": 1},
        {"id": "brass_splitter", "name": "Brass Splitter", "input": "X,X,X", "category": "ground_combo", "base_power": 1.42, "precision_window": 5, "weapon_points": 2},
        {"id": "skiff_step", "name": "Skiff Step", "input": "A+Left/Right", "category": "mobility", "base_power": 0.0, "precision_window": 0, "weapon_points": 0},
        {"id": "dash_slash", "name": "Dash Slash", "input": "Dash+X", "category": "mobility_attack", "base_power": 1.15, "precision_window": 3, "weapon_points": 1},
        {"id": "rising_notch", "name": "Rising Notch", "input": "Up+X", "category": "launcher", "base_power": 1.12, "precision_window": 3, "weapon_points": 1},
        {"id": "aerial_crescent", "name": "Aerial Crescent", "input": "Air+X", "category": "air", "base_power": 1.1, "precision_window": 3, "weapon_points": 1},
        {"id": "dive_keel", "name": "Dive Keel", "input": "Down+Air+X", "category": "air", "base_power": 1.24, "precision_window": 2, "weapon_points": 1},
        {"id": "feint_parry", "name": "Feint Parry", "input": "B then X", "category": "counter", "base_power": 1.35, "precision_window": 2, "weapon_points": 1},
        {"id": "chorus_sweep", "name": "Chorus Sweep", "input": "RB+X", "category": "chorus", "base_power": 0.95, "precision_window": 4, "weapon_points": 1},
        {"id": "burst_relay", "name": "Burst Relay", "input": "Y", "category": "pet_command", "base_power": 1.25, "precision_window": 4, "weapon_points": 0},
        {"id": "anchor_breaker", "name": "Anchor Breaker", "input": "RT+X", "category": "heavy", "base_power": 1.5, "precision_window": 2, "weapon_points": 2},
        {"id": "weave_lunge", "name": "Weave Lunge", "input": "LT+X", "category": "finisher", "base_power": 1.65, "precision_window": 5, "weapon_points": 2},
    ]

    pet_tutorial_moves = [
        {"id": "prism_flick", "name": "Prism Flick", "input": "X", "effect": "quick jab"},
        {"id": "mirror_skate", "name": "Mirror Skate", "input": "A", "effect": "short dash"},
        {"id": "refraction_roll", "name": "Refraction Roll", "input": "B", "effect": "invulnerable curl"},
        {"id": "focus_pulse", "name": "Focus Pulse", "input": "Y", "effect": "stuns tutorial dummy"},
        {"id": "shard_coil", "name": "Shard Coil", "input": "RB", "effect": "trap ring"},
        {"id": "recall_arc", "name": "Recall Arc", "input": "LT", "effect": "returns to Munki anchor"},
    ]

    gear_catalog = [
        {"id": "brass_hookblade", "name": "Brass Hookblade", "slot": "weapon", "power": 0.35, "precision_bonus": 1, "weapon_points": 0},
        {"id": "cobalt_scimitar", "name": "Cobalt Scimitar", "slot": "weapon", "power": 0.55, "precision_bonus": 1, "weapon_points": 0},
        {"id": "dune_falcata", "name": "Dune Falcata", "slot": "weapon", "power": 0.8, "precision_bonus": 2, "weapon_points": 0},
        {"id": "ember_pistol", "name": "Ember Pistol", "slot": "sidearm", "power": 0.4, "precision_bonus": 0, "weapon_points": 0},
        {"id": "glass_buckler", "name": "Glass Buckler", "slot": "offhand", "defense": 0.08},
        {"id": "rift_compass", "name": "Rift Compass", "slot": "relic", "xp_bonus": 0.1},
        {"id": "tea_satchel", "name": "Tea Satchel", "slot": "tool", "tension_relief": 5.0},
        {"id": "dock_chain_boots", "name": "Dock Chain Boots", "slot": "boots", "aerial_control": 0.12},
        {"id": "quartz_gorget", "name": "Quartz Gorget", "slot": "relic", "bond_charge_bonus": 4.0},
        {"id": "pirate_chart", "name": "Pirate Chart Fragment", "slot": "quest", "ship_unlock": True},
        {"id": "domino_key", "name": "Domino Gate Key", "slot": "quest", "gate_bonus": True},
        {"id": "munki_hologem", "name": "Munki Hologem", "slot": "quest", "pet_tutorial": True},
    ]

    enemy_archetypes = [
        {"id": "stair_watcher", "display_name": "Stair Watcher", "xp": 18, "moves": [{"name": "Slate Jab", "damage": 5, "cooldown": 18, "range": 6, "windup": 4}, {"name": "Lantern Bash", "damage": 6, "cooldown": 20, "range": 5, "windup": 5}, {"name": "Riser Snap", "damage": 4, "cooldown": 16, "range": 7, "windup": 3}, {"name": "Guard Tilt", "damage": 3, "cooldown": 22, "range": 4, "windup": 4}, {"name": "Dust Shoulder", "damage": 5, "cooldown": 19, "range": 5, "windup": 4}]},
        {"id": "glass_reaver", "display_name": "Glass Reaver", "xp": 21, "moves": [{"name": "Shard Slice", "damage": 6, "cooldown": 16, "range": 7, "windup": 4}, {"name": "Cleft Step", "damage": 5, "cooldown": 15, "range": 8, "windup": 3}, {"name": "Mirror Rip", "damage": 7, "cooldown": 20, "range": 6, "windup": 5}, {"name": "Brass Elbow", "damage": 4, "cooldown": 17, "range": 5, "windup": 3}, {"name": "Silt Backstep", "damage": 3, "cooldown": 14, "range": 4, "windup": 2}]},
        {"id": "wind_scourer", "display_name": "Wind Scourer", "xp": 20, "moves": [{"name": "Gale Peck", "damage": 4, "cooldown": 14, "range": 8, "windup": 2}, {"name": "Sky Hook", "damage": 6, "cooldown": 18, "range": 7, "windup": 4}, {"name": "Turbine Sweep", "damage": 5, "cooldown": 17, "range": 9, "windup": 3}, {"name": "Slip Draft", "damage": 3, "cooldown": 15, "range": 6, "windup": 2}, {"name": "Needle Gust", "damage": 5, "cooldown": 19, "range": 8, "windup": 4}]},
        {"id": "mirror_eel", "display_name": "Mirror Eel", "xp": 24, "moves": [{"name": "Wet Lash", "damage": 6, "cooldown": 16, "range": 7, "windup": 3}, {"name": "Reflect Coil", "damage": 5, "cooldown": 18, "range": 6, "windup": 4}, {"name": "Prism Bite", "damage": 7, "cooldown": 19, "range": 5, "windup": 4}, {"name": "Current Roll", "damage": 4, "cooldown": 15, "range": 7, "windup": 2}, {"name": "Flood Snap", "damage": 6, "cooldown": 20, "range": 8, "windup": 4}]},
        {"id": "husk_archivist", "display_name": "Husk Archivist", "xp": 26, "moves": [{"name": "Ink Pike", "damage": 6, "cooldown": 18, "range": 8, "windup": 4}, {"name": "Ledger Hammer", "damage": 7, "cooldown": 20, "range": 5, "windup": 5}, {"name": "Dust Sermon", "damage": 4, "cooldown": 16, "range": 7, "windup": 3}, {"name": "Archive Step", "damage": 3, "cooldown": 15, "range": 4, "windup": 2}, {"name": "Spine Arc", "damage": 5, "cooldown": 17, "range": 6, "windup": 3}]},
        {"id": "reliquary_marauder", "display_name": "Reliquary Marauder", "xp": 29, "moves": [{"name": "Hook Lunge", "damage": 7, "cooldown": 18, "range": 7, "windup": 4}, {"name": "Powder Kick", "damage": 5, "cooldown": 16, "range": 6, "windup": 3}, {"name": "Sling Burst", "damage": 6, "cooldown": 17, "range": 9, "windup": 4}, {"name": "Deck Chop", "damage": 8, "cooldown": 21, "range": 5, "windup": 5}, {"name": "Red Wake", "damage": 5, "cooldown": 14, "range": 8, "windup": 2}]},
        {"id": "gate_pikeman", "display_name": "Gate Pikeman", "xp": 31, "moves": [{"name": "Pike Thrust", "damage": 7, "cooldown": 18, "range": 9, "windup": 4}, {"name": "Ferrule Crush", "damage": 6, "cooldown": 17, "range": 6, "windup": 3}, {"name": "Brace Wall", "damage": 4, "cooldown": 22, "range": 4, "windup": 5}, {"name": "Gate Sweep", "damage": 7, "cooldown": 19, "range": 7, "windup": 4}, {"name": "Latch Snap", "damage": 5, "cooldown": 15, "range": 6, "windup": 3}]},
        {"id": "ember_privateer", "display_name": "Ember Privateer", "xp": 34, "moves": [{"name": "Cinder Volley", "damage": 7, "cooldown": 17, "range": 9, "windup": 3}, {"name": "Anchor Sweep", "damage": 8, "cooldown": 20, "range": 7, "windup": 5}, {"name": "Heat Pike", "damage": 6, "cooldown": 18, "range": 8, "windup": 4}, {"name": "Coal Feint", "damage": 4, "cooldown": 15, "range": 5, "windup": 2}, {"name": "Ash Wake", "damage": 7, "cooldown": 16, "range": 8, "windup": 3}]},
    ]

    boss_moves = [
        {"name": "Broadside Sigil", "damage": 10, "cooldown": 20, "range": 10, "windup": 5},
        {"name": "Anchor Halo", "damage": 11, "cooldown": 22, "range": 8, "windup": 6},
        {"name": "Cinder Helm", "damage": 9, "cooldown": 18, "range": 7, "windup": 4},
        {"name": "Gale Tax", "damage": 8, "cooldown": 17, "range": 9, "windup": 3},
        {"name": "Powder Prayer", "damage": 12, "cooldown": 23, "range": 10, "windup": 6},
        {"name": "Hull Crash", "damage": 11, "cooldown": 21, "range": 7, "windup": 5},
        {"name": "Brass Tempest", "damage": 9, "cooldown": 18, "range": 9, "windup": 4},
        {"name": "Privateer Cut", "damage": 10, "cooldown": 19, "range": 6, "windup": 4},
        {"name": "Keel Break", "damage": 12, "cooldown": 24, "range": 8, "windup": 6},
        {"name": "Ashen Vane", "damage": 8, "cooldown": 17, "range": 9, "windup": 3},
        {"name": "Signal Harrow", "damage": 9, "cooldown": 18, "range": 8, "windup": 4},
        {"name": "Reef Charge", "damage": 11, "cooldown": 22, "range": 7, "windup": 5},
        {"name": "Burnished Ram", "damage": 10, "cooldown": 19, "range": 6, "windup": 4},
        {"name": "Smoke Ledger", "damage": 7, "cooldown": 16, "range": 10, "windup": 3},
        {"name": "Domino Wake", "damage": 12, "cooldown": 24, "range": 9, "windup": 6},
        {"name": "Final Broadglass", "damage": 14, "cooldown": 26, "range": 11, "windup": 7},
    ]

    future_move_projection = {
        "base_verbs": 32,
        "weapon_forms": 12,
        "stances": 6,
        "pet_synergy_modifiers": 10,
        "projected_move_count": 32 * 12 * 6 * 10,
    }

    progression_gates = [
        {"id": "quay_domino_gate", "name": "Quay Domino Gate", "rooms": ["ropewalk_harbor", "brass_battery"], "sequence": ["capstan_release", "weight_drop", "mirror_baffle"]},
        {"id": "cistern_domino_gate", "name": "Cistern Domino Gate", "rooms": ["mirror_cistern", "prism_grotto"], "sequence": ["sluice_turn", "glass_rod", "echo_plate"]},
        {"id": "choir_domino_gate", "name": "Choir Domino Gate", "rooms": ["bell_foundry", "chain_lift_annex"], "sequence": ["bell_strike", "counterweight", "choir_latch"]},
        {"id": "switchyard_domino_gate", "name": "Switchyard Domino Gate", "rooms": ["ossuary_switchyard", "cinder_drydock"], "sequence": ["rail_lock", "ember_basin", "lever_spine"]},
        {"id": "boss_domino_gate", "name": "Blackglass Gate", "rooms": ["blackglass_gatehouse", "ashfall_dais"], "sequence": ["signal_mast", "brass_orrery", "final_keel"]},
    ]

    backdrop_palette = {
        "latchspire_refuge_backdrop": ["#4a3a34", "#5a6678", "#b8924f"],
        "choir_stair_backdrop": ["#47362f", "#607086", "#b28557"],
        "glasswind_causeway_backdrop": ["#4d3a30", "#61788a", "#b88f63"],
        "ember_nave_backdrop": ["#4b342f", "#6b7682", "#c29d68"],
    }

    parallax_sets = {
        "latchspire_refuge_backdrop": [{"label": "tower ribs", "x": 18, "parallax": 0.24, "color": "#6d5d54"}, {"label": "dock lamps", "x": 74, "parallax": 0.42, "color": "#748292"}],
        "choir_stair_backdrop": [{"label": "choir struts", "x": 20, "parallax": 0.25, "color": "#725a52"}, {"label": "hanging bells", "x": 78, "parallax": 0.43, "color": "#7a8798"}],
        "glasswind_causeway_backdrop": [{"label": "cable ribs", "x": 22, "parallax": 0.24, "color": "#71584d"}, {"label": "wind mirrors", "x": 79, "parallax": 0.45, "color": "#7c8a98"}],
        "ember_nave_backdrop": [{"label": "pillar shadows", "x": 24, "parallax": 0.24, "color": "#6a544a"}, {"label": "cinder braziers", "x": 82, "parallax": 0.44, "color": "#7f8791"}],
    }

    new_rooms = [
        _make_room("ropewalk_harbor", "Ropewalk Harbor", "latchspire_refuge_backdrop", backdrop_palette["latchspire_refuge_backdrop"], parallax_sets["latchspire_refuge_backdrop"], "Trace the harbor ropes, glimpse the pirate ship silhouette, and begin the first domino gate chain.", "Use E near interactables to release the ropewalk machinery. The anchored ship beyond the ash tide is a cameo and a test-route promise.", None, "latchspire_refuge", danger=1, objects=[_object("capstan_release", "puzzle_switch", 22, 0, "Capstan Release", puzzle_id="quay_domino_gate", sequence_index=0, unlock_gate="quay_domino_gate", event="The first capstan drops a brass tooth into the relay."), _object("chart_cache", "gear_cache", 58, 0, "Pirate Chart Cache", item_id="pirate_chart", event="A chart fragment sketches the ship route through the dunes."), _object("ship_cameo", "ship_console", 84, 0, "Ship Adventure Berth", event="A wind-carved gangplank points toward the ship adventure test.")], enemies=[_enemy("reliquary_marauder", 68, 26, 0.66, 1.2, 40)]),
        _make_room("brass_battery", "Brass Battery", "latchspire_refuge_backdrop", backdrop_palette["latchspire_refuge_backdrop"], parallax_sets["latchspire_refuge_backdrop"], "Kick the battery weight through a chain reaction to power the harbor gate.", "Strike the suspended battery after arming the relay to continue the domino sequence.", "latchspire_refuge", "scribe_gullet", danger=2, objects=[_object("weight_drop", "puzzle_switch", 36, 3, "Battery Weight", puzzle_id="quay_domino_gate", sequence_index=1, unlock_gate="quay_domino_gate", event="The weight swings through the brass rails."), _object("hookblade_chest", "weapon_cache", 63, 0, "Hookblade Locker", item_id="brass_hookblade", event="The locker yields a brass hookblade built for deck duels.")], enemies=[_enemy("stair_watcher", 42, 24, 0.62, 1.1, 38), _enemy("gate_pikeman", 74, 28, 0.68, 1.4, 44)]),
        _make_room("munki_refractionary", "Munki Refractionary", "latchspire_refuge_backdrop", backdrop_palette["latchspire_refuge_backdrop"], parallax_sets["latchspire_refuge_backdrop"], "Optional detour: recover the Munki hologem and enter the projected pet tutorial chamber.", "Rescue the Refraction Munki, then interact with the hologem visualizer to assume SimIAM control and test six pet inputs.", "scribe_gullet", "tutorial_sanctum", danger=1, safe_room=True, objects=[_object("munki_hologem", "gear_cache", 40, 0, "Munki Hologem", item_id="munki_hologem", event="The Munki offers a hologem lens and a tea-steamed lesson."), _object("hologem_visualizer", "hologem_visualizer", 58, 0, "Hologem Refraction Visualizer", pet_id="refraction_munki", event="The Munki projects a refraction arena for pet control drills."), _object("tea_bench", "tea_relief", 76, 0, "Tea Bench", tension_relief=9.0, event="The tea detour settles the roster before the next push.")], rescue={"pet": "refraction_munki", "x": 32, "y": 0}, enemies=[]),
        _make_room("skiff_berth", "Skiff Berth", "latchspire_refuge_backdrop", backdrop_palette["latchspire_refuge_backdrop"], parallax_sets["latchspire_refuge_backdrop"], "Read the desert-pirate ship cameo at close range and unlock a title-menu route to ship tests.", "Interact with the mooring post to mark the ship adventure test on the title menu.", "latchspire_refuge", "ropewalk_harbor", danger=1, objects=[_object("ship_unlock", "ship_console", 54, 0, "Mooring Post", unlocks_mode="ship_adventure_test", event="The mooring post records the ship route for later drills.")], enemies=[_enemy("reliquary_marauder", 78, 26, 0.7, 1.2, 42)]),
        _make_room("aerie_spur", "Aerie Spur", "latchspire_refuge_backdrop", backdrop_palette["latchspire_refuge_backdrop"], parallax_sets["latchspire_refuge_backdrop"], "Taste a brief aerial route over chain lifts and falling sails.", "This room is a short aerial tease. Keep jumps tight and use the dock-chain boots if you find them.", "tutorial_sanctum", "atlas_choir", danger=2, platforms=[{"id": "aerie_floor", "x1": 0, "x2": 24, "y": 0, "color": "#6a5c53"}, {"id": "aerie_lift", "x1": 28, "x2": 52, "y": 4, "color": "#8a7866"}, {"id": "aerie_sail", "x1": 58, "x2": 80, "y": 7, "color": "#a08e79"}, {"id": "aerie_perch", "x1": 84, "x2": 100, "y": 2, "color": "#7b6c5f"}], objects=[_object("dock_chain_boots", "gear_cache", 48, 4, "Dock Chain Boots", item_id="dock_chain_boots", event="The boots give a hint of aerial correction for later routes.")], enemies=[_enemy("wind_scourer", 70, 24, 0.72, 1.15, 36)]),
        _make_room("dust_rail_span", "Dust Rail Span", "glasswind_causeway_backdrop", backdrop_palette["glasswind_causeway_backdrop"], parallax_sets["glasswind_causeway_backdrop"], "Cross a rail bridge while learning how interactable machinery and enemy pressure overlap.", "Toggle the rail latch before the enemy push closes in.", "glasswind_causeway", "mirror_cistern", danger=2, objects=[_object("rail_latch", "puzzle_switch", 41, 0, "Rail Latch", puzzle_id="cistern_domino_gate", sequence_index=0, unlock_gate="cistern_domino_gate", event="The rail latch throws the first cistern domino."), _object("ember_pistol", "weapon_cache", 66, 0, "Signal Locker", item_id="ember_pistol", event="A scorched pistol shows how sidearms alter spacing.")], enemies=[_enemy("glass_reaver", 56, 28, 0.68, 1.3, 42), _enemy("wind_scourer", 78, 24, 0.7, 1.1, 36)]),
        _make_room("prism_grotto", "Prism Grotto", "glasswind_causeway_backdrop", backdrop_palette["glasswind_causeway_backdrop"], parallax_sets["glasswind_causeway_backdrop"], "Work through a reflective flood puzzle before opening the cistern gate.", "This grotto combines movement, switch order, and enemy pressure into a small chain reaction problem.", "mirror_cistern", "reliquary_bazaar", danger=2, objects=[_object("sluice_turn", "puzzle_switch", 24, 0, "Sluice Turn", puzzle_id="cistern_domino_gate", sequence_index=1, unlock_gate="cistern_domino_gate", event="The sluice redirects light and runoff."), _object("glass_rod", "puzzle_switch", 48, 0, "Glass Rod", puzzle_id="cistern_domino_gate", sequence_index=2, unlock_gate="cistern_domino_gate", event="The glass rod sends the final glint into the cistern gate."), _object("quartz_gorget", "gear_cache", 72, 0, "Quartz Gorget", item_id="quartz_gorget", event="The gorget sharpens weave charge gain.")], enemies=[_enemy("mirror_eel", 54, 26, 0.74, 1.25, 44)]),
        _make_room("windlass_quay", "Windlass Quay", "glasswind_causeway_backdrop", backdrop_palette["glasswind_causeway_backdrop"], parallax_sets["glasswind_causeway_backdrop"], "Meet the ship again from the canyon edge and fight across a cable quay.", "The ship cameo returns here as a horizon marker while the quay tests grounded combat spacing.", "reliquary_bazaar", "atlas_choir", danger=3, objects=[_object("windlass_cache", "gear_cache", 32, 0, "Windlass Cache", item_id="cobalt_scimitar", event="A cobalt scimitar broadens the prototype gear read."), _object("ship_view", "ship_console", 80, 0, "Signal Mast", event="The pirate ship cuts between the two mountain powers before fading into dust." )], enemies=[_enemy("reliquary_marauder", 60, 30, 0.75, 1.4, 48), _enemy("glass_reaver", 82, 28, 0.71, 1.25, 42)]),
        _make_room("relay_basin", "Relay Basin", "glasswind_causeway_backdrop", backdrop_palette["glasswind_causeway_backdrop"], parallax_sets["glasswind_causeway_backdrop"], "Solve a rail-and-basin relay that foreshadows the larger switchyard gates.", "Set the basin weight and then escape the closing threat wave.", "glasswind_causeway", "ossuary_switchyard", danger=3, objects=[_object("echo_plate", "puzzle_switch", 52, 0, "Echo Plate", puzzle_id="cistern_domino_gate", sequence_index=3, unlock_gate="cistern_domino_gate", event="The basin relay slams the cistern gate wide."), _object("domino_key", "gear_cache", 78, 0, "Domino Key", item_id="domino_key", event="The key hints that puzzles can gate more than one route.")], enemies=[_enemy("gate_pikeman", 60, 32, 0.78, 1.55, 52)]),
        _make_room("bell_foundry", "Bell Foundry", "choir_stair_backdrop", backdrop_palette["choir_stair_backdrop"], parallax_sets["choir_stair_backdrop"], "Hit the bell in rhythm to start a three-link choir gate puzzle.", "The foundry is a Rube Goldberg room: strike, weight, latch, then run the route before enemies reset the pressure.", "choir_stair", "tutorial_sanctum", danger=2, objects=[_object("bell_strike", "puzzle_switch", 34, 0, "Bell Strike", puzzle_id="choir_domino_gate", sequence_index=0, unlock_gate="choir_domino_gate", event="The bell blast launches the first choir relay."), _object("foundry_cache", "gear_cache", 72, 0, "Foundry Cache", item_id="glass_buckler", event="A glass buckler broadens the defensive build read.")], enemies=[_enemy("stair_watcher", 54, 26, 0.68, 1.2, 40), _enemy("gate_pikeman", 82, 30, 0.72, 1.35, 46)]),
        _make_room("chain_lift_annex", "Chain Lift Annex", "choir_stair_backdrop", backdrop_palette["choir_stair_backdrop"], parallax_sets["choir_stair_backdrop"], "Run a lift sequence under pressure to understand moving-platform cause and effect.", "The annex is still hand-authored, but it gestures toward more kinetic traversal later.", "tutorial_sanctum", "atlas_choir", danger=2, platforms=[{"id": "annex_floor", "x1": 0, "x2": 22, "y": 0, "color": "#6c5c51"}, {"id": "annex_chain", "x1": 28, "x2": 50, "y": 4, "color": "#847564"}, {"id": "annex_lift", "x1": 57, "x2": 76, "y": 6, "color": "#9a8a76"}, {"id": "annex_gate", "x1": 84, "x2": 100, "y": 2, "color": "#766556"}], objects=[_object("counterweight", "puzzle_switch", 42, 4, "Counterweight Brake", puzzle_id="choir_domino_gate", sequence_index=1, unlock_gate="choir_domino_gate", event="The counterweight slides into the lift teeth."), _object("choir_latch", "puzzle_switch", 76, 6, "Choir Latch", puzzle_id="choir_domino_gate", sequence_index=2, unlock_gate="choir_domino_gate", event="The choir gate slams open at the far end." )], enemies=[_enemy("wind_scourer", 64, 30, 0.74, 1.1, 38)]),
        _make_room("abbot_stair", "Abbot Stair", "choir_stair_backdrop", backdrop_palette["choir_stair_backdrop"], parallax_sets["choir_stair_backdrop"], "Climb a narrow procession stair for experience, salvage, and one more gear read.", "This room exists to broaden the novice playtime without changing the main route tone.", "choir_stair", "tutorial_sanctum", danger=2, objects=[_object("abbot_satchel", "gear_cache", 58, 3, "Abbot Satchel", item_id="tea_satchel", event="The satchel underlines how support gear affects tempo.")], enemies=[_enemy("husk_archivist", 70, 28, 0.7, 1.35, 44)]),
        _make_room("pilgrim_skywalk", "Pilgrim Skywalk", "choir_stair_backdrop", backdrop_palette["choir_stair_backdrop"], parallax_sets["choir_stair_backdrop"], "A second brief aerial taste framed by the kingdom on one mountain and the spiritual fief on the other.", "This skywalk is a thematic hinge: desert-pirate frontier between worldly and spiritual powers.", "atlas_choir", "windlass_quay", danger=2, platforms=[{"id": "skywalk_floor", "x1": 0, "x2": 18, "y": 0, "color": "#6a594f"}, {"id": "skywalk_chain", "x1": 24, "x2": 44, "y": 5, "color": "#82705d"}, {"id": "skywalk_banner", "x1": 51, "x2": 68, "y": 8, "color": "#9a866d"}, {"id": "skywalk_perch", "x1": 74, "x2": 100, "y": 3, "color": "#786658"}], objects=[_object("sky_chart", "xp_cache", 60, 8, "Sky Chart", xp_award=14, weapon_points=4, event="The chart lays out a larger movespace for the final game." )], enemies=[_enemy("wind_scourer", 72, 30, 0.76, 1.12, 40)]),
        _make_room("cinder_drydock", "Cinder Drydock", "ember_nave_backdrop", backdrop_palette["ember_nave_backdrop"], parallax_sets["ember_nave_backdrop"], "Push into the dockyard where ember privateers and domino machinery converge.", "The drydock introduces prototype-scale enemy density and interactables in the same room.", "ossuary_switchyard", "blackglass_gatehouse", danger=3, objects=[_object("rail_lock", "puzzle_switch", 28, 0, "Rail Lock", puzzle_id="switchyard_domino_gate", sequence_index=0, unlock_gate="switchyard_domino_gate", event="A switch rail slams into the cinder track."), _object("drydock_cache", "gear_cache", 70, 0, "Drydock Cache", item_id="ember_pistol", event="The cache shows ranged support without displacing melee focus.")], enemies=[_enemy("ember_privateer", 62, 30, 0.78, 1.5, 50), _enemy("gate_pikeman", 82, 30, 0.76, 1.45, 48)]),
        _make_room("scorched_capstan", "Scorched Capstan", "ember_nave_backdrop", backdrop_palette["ember_nave_backdrop"], parallax_sets["ember_nave_backdrop"], "Finish the drydock domino chain under boss-adjacent pressure.", "This room is the strongest example of the cause-and-effect gate series before the final prototype boss.", "cinder_drydock", "blackglass_gatehouse", danger=3, objects=[_object("ember_basin", "puzzle_switch", 44, 0, "Ember Basin", puzzle_id="switchyard_domino_gate", sequence_index=1, unlock_gate="switchyard_domino_gate", event="The ember basin spits cinders into the capstan wheel."), _object("lever_spine", "puzzle_switch", 70, 0, "Lever Spine", puzzle_id="switchyard_domino_gate", sequence_index=2, unlock_gate="switchyard_domino_gate", event="The final spine strike opens the drydock gate.")], enemies=[_enemy("ember_privateer", 56, 30, 0.8, 1.55, 52), _enemy("reliquary_marauder", 82, 28, 0.78, 1.42, 46)]),
        _make_room("blackglass_gatehouse", "Blackglass Gatehouse", "ember_nave_backdrop", backdrop_palette["ember_nave_backdrop"], parallax_sets["ember_nave_backdrop"], "Prime the final prototype gate through one last three-step contraption puzzle.", "This is the last gate room before the prototype boss. Solve the chain and prepare your gear.", "ram_gate", "ashfall_dais", danger=4, objects=[_object("signal_mast", "puzzle_switch", 26, 0, "Signal Mast", puzzle_id="boss_domino_gate", sequence_index=0, unlock_gate="boss_domino_gate", event="The mast swings a mirror beam across the gatehouse."), _object("brass_orrery", "puzzle_switch", 48, 0, "Brass Orrery", puzzle_id="boss_domino_gate", sequence_index=1, unlock_gate="boss_domino_gate", event="The orrery starts the blackglass tumble."), _object("final_keel", "puzzle_switch", 72, 0, "Final Keel", puzzle_id="boss_domino_gate", sequence_index=2, unlock_gate="boss_domino_gate", event="The final keel drops and unlocks the dais beyond.")], enemies=[_enemy("gate_pikeman", 58, 34, 0.82, 1.6, 56), _enemy("ember_privateer", 84, 32, 0.81, 1.58, 54)]),
        _make_room("ashfall_dais", "Ashfall Dais", "ember_nave_backdrop", backdrop_palette["ember_nave_backdrop"], parallax_sets["ember_nave_backdrop"], "Face the prototype final boss in a pressure-heavy relic dock beneath falling ash.", "The Commodore has sixteen named moves in this prototype and expects full use of gear, pets, and timing discipline.", "blackglass_gatehouse", None, danger=5, objects=[_object("boss_cache", "xp_cache", 18, 0, "War Ledger", xp_award=28, weapon_points=10, event="The ledger foreshadows the broader late-game mastery layer.")], enemies=[_enemy("dune_commodore", 72, 180, 0.9, 2.6, 84, boss=True, bond_weave_requirements={"posture_at_most": 20, "requires_chorus": "wind_kite", "requires_rooted": True, "requires_rescued_pets": ["mirror_newt", "latch_spider", "salt_ram", "refraction_munki"]})], popup={"template": "quest_shell", "title": "Ashfall Dais", "text": "The prototype climax frames a desert-pirate boss beneath a reliquary dock, with kingdom stone on one mountain and spiritual lanterns on the other."}),
    ]

    room_overrides = {
        "latchspire_refuge": {
            "backdrop_asset": "latchspire_refuge_backdrop",
            "scene_family": "refuge",
            "scene_index": 1,
            "layout": {
                "objects": [
                    _object("refuge_loadout", "loadout_station", 16, 0, "Roster Rail", event="The rail previews gear, pet, and move planning before departure."),
                    _object("refuge_left_route", "signpost", 8, 0, "Harbor Route", event="Left leads to the harbor ropewalk and the ship cameo."),
                ]
            },
            "exits": {"left": "ropewalk_harbor", "right": "choir_stair"},
        },
        "choir_stair": {
            "backdrop_asset": "choir_stair_backdrop",
            "scene_family": "choir",
            "scene_index": 1,
            "layout": {"objects": [_object("choir_sign", "signpost", 18, 0, "Foundry Spur", event="The foundry branch teaches the first domino gate." )]},
            "exits": {"left": "latchspire_refuge", "right": "glasswind_causeway"},
        },
        "glasswind_causeway": {
            "backdrop_asset": "glasswind_causeway_backdrop",
            "scene_family": "glasswind",
            "scene_index": 1,
            "layout": {"objects": [_object("causeway_sign", "signpost", 18, 0, "Dust Rail Spur", event="An optional rail span opens more combat and gear.") ]},
        },
        "mirror_cistern": {"backdrop_asset": "glasswind_causeway_backdrop", "scene_family": "glasswind", "scene_index": 2},
        "scribe_gullet": {"backdrop_asset": "latchspire_refuge_backdrop", "scene_family": "refuge", "scene_index": 2, "layout": {"objects": [_object("munki_detour", "signpost", 22, 0, "Munki Detour", event="A calm side room offers pet retrieval and hologem training.") ]}, "exits": {"left": "glasswind_causeway", "right": "ossuary_switchyard", "alt_right": "munki_refractionary"}},
        "ossuary_switchyard": {"backdrop_asset": "ember_nave_backdrop", "scene_family": "ember", "scene_index": 1},
        "ember_nave": {"backdrop_asset": "ember_nave_backdrop", "scene_family": "ember", "scene_index": 2},
        "ram_gate": {"backdrop_asset": "ember_nave_backdrop", "scene_family": "ember", "scene_index": 3, "exits": {"left": "ember_nave", "right": {"room": "tutorial_sanctum", "requires": "salt_ram"}, "alt_right": "blackglass_gatehouse"}},
        "tutorial_sanctum": {"backdrop_asset": "choir_stair_backdrop", "scene_family": "choir", "scene_index": 2, "layout": {"objects": [_object("aerial_spur_sign", "signpost", 78, 0, "Aerie Spur", event="A short aerial spur extends the prototype without breaking the main route.")]}},
        "reliquary_bazaar": {"backdrop_asset": "glasswind_causeway_backdrop", "scene_family": "glasswind", "scene_index": 3, "layout": {"objects": [_object("bazaar_shop", "merchant", 40, 0, "Quartermaster Stall", event="The bazaar previews broader gear, tea, and salvage economies.") ]}},
        "atlas_choir": {"backdrop_asset": "choir_stair_backdrop", "scene_family": "choir", "scene_index": 3, "exits": {"left": "reliquary_bazaar", "right": "pilgrim_skywalk"}},
    }

    pet_definitions = [
        {
            "id": "refraction_munki",
            "name": "Refraction Munki",
            "lane": "key",
            "effect": "hologem_shift",
        }
    ]

    return {
        "novice_playtime_hours": [1, 6],
        "player_moves": player_moves,
        "pet_tutorial_moves": pet_tutorial_moves,
        "gear_catalog": gear_catalog,
        "enemy_archetypes": enemy_archetypes,
        "boss_moves": boss_moves,
        "future_move_projection": future_move_projection,
        "progression_gates": progression_gates,
        "room_overrides": room_overrides,
        "new_rooms": new_rooms,
        "additional_pets": pet_definitions,
        "ship_adventure_mode": {
            "title_menu_label": "Ship Adventure Test",
            "description": "Brief desert-pirate ship drill with boost, broadside, brake, and skimming lift.",
            "moves": [
                {"name": "Dune Rudder", "input": "Left Stick", "effect": "turn and drift"},
                {"name": "Skim Lift", "input": "A", "effect": "short aerial rise"},
                {"name": "Broadside", "input": "X", "effect": "port cannon volley"},
                {"name": "Burn Boost", "input": "RT", "effect": "speed burst"},
                {"name": "Anchor Brake", "input": "LT", "effect": "hard stop and pivot"},
            ],
        },
    }


def apply_prototype_expansion(document: dict) -> dict:
    expanded = deepcopy(document)
    prototype = build_prototype_expansion()
    expanded["prototype"] = {
        "estimated_novice_playtime_hours": prototype["novice_playtime_hours"],
        "player_moves": prototype["player_moves"],
        "pet_tutorial_moves": prototype["pet_tutorial_moves"],
        "gear_catalog": prototype["gear_catalog"],
        "enemy_archetypes": prototype["enemy_archetypes"],
        "boss_moves": prototype["boss_moves"],
        "future_move_projection": prototype["future_move_projection"],
        "progression_gates": prototype["progression_gates"],
        "ship_adventure_mode": prototype["ship_adventure_mode"],
        "controller_target": "Xbox Series gamepad",
    }

    expanded["metadata"]["experience_goal"] = (
        "A 1-6 hour novice-friendly prototype pilgrimage through a desert-pirate frontier, mixing hack-slash precision,"
        " optional pet rescue/tutorial detours, gear-driven growth, domino-gated traversal, and a final reliquary dock boss."
    )

    expanded.setdefault("gameplay", {}).setdefault("combat", {})["prototype_move_count"] = len(prototype["player_moves"])
    expanded["gameplay"]["combat"]["enemy_variety_count"] = len(prototype["enemy_archetypes"])
    expanded["gameplay"]["combat"]["boss_move_count"] = len(prototype["boss_moves"])
    expanded["gameplay"]["combat"]["pet_tutorial_move_count"] = len(prototype["pet_tutorial_moves"])
    expanded["gameplay"]["combat"]["future_move_projection"] = prototype["future_move_projection"]["projected_move_count"]
    expanded["gameplay"]["combat"]["supports_xbox_series_gamepad"] = True

    expanded["player"].setdefault("progression", {
        "level": 1,
        "experience": 0,
        "weapon_points": 0,
        "equipped_weapon": "brass_hookblade",
        "equipped_sidearm": "ember_pistol",
        "equipped_relic": "rift_compass",
        "inventory": ["brass_hookblade", "glass_buckler"],
    })

    pet_ids = {pet["id"] for pet in expanded.get("pets", {}).get("definitions", [])}
    for pet in prototype["additional_pets"]:
        if pet["id"] not in pet_ids:
            expanded["pets"]["definitions"].append(pet)

    rooms = []
    for room in expanded["world"]["rooms"]:
        updated = deepcopy(room)
        override = prototype["room_overrides"].get(room["id"], {})
        if "layout" in override:
            updated_layout = deepcopy(updated.get("layout", {}))
            updated_layout.setdefault("platforms", [])
            updated_layout.setdefault("hazards", [])
            updated_layout.setdefault("encounter_zones", [])
            updated_layout.setdefault("objects", [])
            for key, value in override["layout"].items():
                if isinstance(value, list):
                    updated_layout[key] = value
                else:
                    updated_layout[key] = value
            override = {key: value for key, value in override.items() if key != "layout"}
            updated["layout"] = updated_layout
        updated.update(override)
        updated.setdefault("layout", {}).setdefault("objects", [])
        rooms.append(updated)

    rooms.extend(prototype["new_rooms"])
    expanded["world"]["rooms"] = rooms
    return expanded