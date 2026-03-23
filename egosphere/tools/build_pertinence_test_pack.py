import json
import math
import wave
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT / "pipeline" / "projects" / "pertinence_tribunal"
AUTHORING_ROOT = PROJECT_ROOT / "authoring" / "clipstudio"
SPRITE_ROOT = AUTHORING_ROOT / "sprites"
TILE_ROOT = AUTHORING_ROOT / "tiles"
PORTRAIT_ROOT = AUTHORING_ROOT / "portraits"
SOUND_ROOT = PROJECT_ROOT / "sound" / "pertinence"
MANIFEST_PATH = PROJECT_ROOT / "game_project.json"
RECRAFT_MANIFEST_PATH = PROJECT_ROOT / "recraft_manifest.json"
GDD_PATH = PROJECT_ROOT / "PERTINENCE_TRIBUNAL_GDD.md"
PITCH_PATH = PROJECT_ROOT / "PERTINENCE_TRIBUNAL_PS6_PITCH.md"

TRANSPARENT = (0, 0, 0, 0)

PLAYER_ANIMATIONS = [
    ("idle", 8),
    ("idle_breath", 8),
    ("walk", 8),
    ("run", 8),
    ("sprint_stop", 6),
    ("crouch", 6),
    ("crouch_walk", 6),
    ("ledge_hang", 6),
    ("ledge_climb", 8),
    ("jump_start", 6),
    ("jump_air", 6),
    ("double_jump", 8),
    ("air_dash", 8),
    ("slide", 8),
    ("ladder_climb", 8),
    ("light_attack_1", 8),
    ("light_attack_2", 8),
    ("light_attack_3", 8),
    ("heavy_attack", 10),
    ("charged_slash", 12),
    ("launcher", 10),
    ("aerial_combo", 10),
    ("dodge", 8),
    ("backstep", 8),
    ("block", 6),
    ("parry", 8),
    ("counter_slash", 10),
    ("wall_cling", 6),
    ("wall_jump", 8),
    ("grapple_hook", 10),
    ("dash_slash", 10),
    ("plunge_attack", 10),
    ("heal_focus", 10),
    ("relic_cast", 10),
    ("hit_react", 6),
    ("death", 12),
]

BASIC_ANIMATIONS = [
    ("idle", 8),
    ("walk", 8),
    ("run", 8),
    ("turn", 6),
    ("crouch", 6),
    ("jump", 6),
    ("light_attack", 8),
    ("heavy_attack", 10),
    ("dodge", 8),
    ("block", 6),
    ("parry", 8),
]

LOW_TIER_SKIRMISHER_ANIMATIONS = [
    ("idle", 6),
    ("patrol_walk", 8),
    ("alert_run", 8),
    ("feint", 6),
    ("thrust", 8),
    ("retreat", 6),
    ("sidehop", 6),
    ("lunge", 8),
    ("stagger", 6),
    ("death", 8),
]

LOW_TIER_AMBUSH_ANIMATIONS = [
    ("idle", 6),
    ("creep", 8),
    ("ceiling_drop", 8),
    ("scuttle", 8),
    ("swipe", 8),
    ("poison_spit", 8),
    ("burrow", 8),
    ("evade", 6),
    ("stagger", 6),
    ("death", 8),
]

LOW_TIER_RANGED_ANIMATIONS = [
    ("idle", 6),
    ("patrol_walk", 8),
    ("backpedal", 8),
    ("aim_fire", 10),
    ("reload", 8),
    ("trap_set", 8),
    ("panic_run", 8),
    ("melee_panic", 6),
    ("stagger", 6),
    ("death", 8),
]

LOW_TIER_BRUTE_ANIMATIONS = [
    ("idle", 6),
    ("stomp_walk", 8),
    ("guard_up", 6),
    ("shield_bash", 8),
    ("overhead_slam", 10),
    ("charge", 10),
    ("grab", 8),
    ("roar", 6),
    ("stagger", 6),
    ("death", 8),
]

MID_TIER_DUELIST_ANIMATIONS = [
    ("idle", 6),
    ("walk", 8),
    ("run", 8),
    ("jump", 6),
    ("feint", 6),
    ("light_attack", 8),
    ("heavy_attack", 10),
    ("combo_finisher", 10),
    ("dodge", 8),
    ("block", 6),
    ("parry", 8),
    ("grab", 8),
    ("stagger", 6),
    ("recover", 6),
    ("death", 10),
]

MID_TIER_CASTER_ANIMATIONS = [
    ("idle", 6),
    ("walk", 8),
    ("hover_step", 8),
    ("ward_raise", 8),
    ("projectile_cast", 10),
    ("sigil_drop", 10),
    ("beam_sweep", 12),
    ("teleport", 8),
    ("summon", 10),
    ("panic_dash", 8),
    ("stagger", 6),
    ("death", 10),
]

MID_TIER_SIEGE_ANIMATIONS = [
    ("idle", 6),
    ("deploy_walk", 8),
    ("brace", 6),
    ("aim", 8),
    ("fire_volley", 10),
    ("reload", 10),
    ("backstep", 8),
    ("mine_drop", 8),
    ("shield_turn", 8),
    ("stagger", 6),
    ("collapse", 8),
]

TOP_TIER_ANIMATIONS = [
    ("idle", 8),
    ("walk", 8),
    ("run", 8),
    ("crouch", 6),
    ("jump", 8),
    ("light_attack_1", 8),
    ("light_attack_2", 8),
    ("heavy_attack_1", 10),
    ("heavy_attack_2", 10),
    ("dodge", 8),
    ("block", 6),
    ("parry", 8),
    ("phase_shift", 10),
    ("summon", 12),
    ("projectile_cast", 10),
    ("beam_cleave", 12),
    ("aerial_slam", 10),
    ("ground_spike", 12),
    ("grapple", 8),
    ("roar", 8),
    ("arena_lock", 8),
    ("teleport", 8),
    ("counter_stance", 8),
    ("curse_pulse", 10),
    ("stagger", 6),
    ("recover", 8),
    ("enrage", 10),
    ("death", 12),
    ("finisher", 12),
]

GODULY_INTERACTIONS = [
    ("blessing_offer", 10),
    ("memory_projection", 10),
    ("verdict_gaze", 8),
    ("astral_shift", 10),
    ("halo_flare", 10),
    ("seal_inscription", 10),
    ("lore_reveal", 10),
    ("trial_mark", 8),
    ("time_fold", 10),
    ("departure", 8),
]

LOW_TIER_DEFS = [
    ("ash_censer", "skirmisher", "humanoid"),
    ("mildew_spearman", "skirmisher", "humanoid"),
    ("shrine_urchin", "ambush", "beast"),
    ("gutter_flagellant", "brute", "humanoid"),
    ("vermin_lantern", "ranged", "humanoid"),
    ("docket_hound", "ambush", "beast"),
    ("reed_sapper", "ranged", "humanoid"),
    ("silt_acolyte", "skirmisher", "humanoid"),
    ("briar_monk", "brute", "humanoid"),
    ("tar_crow", "ambush", "beast"),
    ("pale_usher", "ranged", "humanoid"),
    ("mire_hauler", "brute", "humanoid"),
    ("plague_bell", "skirmisher", "beast"),
    ("quill_marauder", "skirmisher", "humanoid"),
    ("writ_leech", "ambush", "beast"),
    ("salt_rustic", "brute", "humanoid"),
    ("veil_skulker", "ambush", "humanoid"),
    ("lantern_broker", "ranged", "humanoid"),
    ("reed_cutthroat", "skirmisher", "humanoid"),
    ("plague_harrier", "ambush", "beast"),
    ("ossuary_porter", "brute", "humanoid"),
    ("tithe_stalker", "ranged", "humanoid"),
    ("marsh_carrion", "ambush", "beast"),
    ("censer_duelist", "skirmisher", "humanoid"),
]

MID_TIER_DEFS = [
    ("ossuary_knight", "duelist", "humanoid"),
    ("marsh_inquisitor", "duelist", "humanoid"),
    ("chain_hierophant", "caster", "humanoid"),
    ("catacomb_duelist", "duelist", "humanoid"),
    ("abbey_ballista", "siege", "humanoid"),
    ("river_herald", "caster", "humanoid"),
    ("gilded_bailiff", "duelist", "humanoid"),
    ("moonlit_chastener", "caster", "humanoid"),
    ("pestilent_warden", "siege", "humanoid"),
    ("ferry_exorcist", "caster", "humanoid"),
    ("brine_archivist", "siege", "humanoid"),
    ("verdict_lancer", "duelist", "humanoid"),
    ("cathedral_chorister", "caster", "humanoid"),
    ("ashen_reliquary", "siege", "humanoid"),
]

TOP_TIER_DEFS = [
    ("sepulchral_judge", "humanoid"),
    ("abbess_of_brine", "humanoid"),
    ("the_sable_notary", "humanoid"),
    ("cathedral_mandible", "beast"),
    ("the_plague_cartographer", "humanoid"),
    ("the_ashen_magistrate", "humanoid"),
    ("the_reed_colossus", "beast"),
]

NPC_NAMES = ["village_elder", "smith_of_brass", "rope_ferryman", "archive_child", "moss_physician", "penitent_poet"]
FAUNA_NAMES = ["reed_fox", "cinder_heron", "salt_toad", "sable_rat", "fen_goat", "mire_owl", "glass_eel", "dusk_stag"]
GODULY_NAMES = [
    "goduly_amber_accord", "goduly_brass_tide", "goduly_cerulean_mercy", "goduly_docket_flame",
    "goduly_ember_refrain", "goduly_fallow_crown", "goduly_gilt_murmur", "goduly_hollow_orbit",
    "goduly_ink_saint", "goduly_jade_resolve", "goduly_knotted_light", "goduly_lantern_grace",
]

LOW_TIER_BY_ARCHETYPE = {
    "skirmisher": LOW_TIER_SKIRMISHER_ANIMATIONS,
    "ambush": LOW_TIER_AMBUSH_ANIMATIONS,
    "ranged": LOW_TIER_RANGED_ANIMATIONS,
    "brute": LOW_TIER_BRUTE_ANIMATIONS,
}

MID_TIER_BY_ARCHETYPE = {
    "duelist": MID_TIER_DUELIST_ANIMATIONS,
    "caster": MID_TIER_CASTER_ANIMATIONS,
    "siege": MID_TIER_SIEGE_ANIMATIONS,
}

FX_ANIMATIONS = [
    ("startup", 6),
    ("burst", 8),
    ("loop", 8),
    ("impact", 8),
    ("trail", 8),
    ("dissipate", 8),
]

FX_DEFS = [
    ("ronin_slash_arc", (236, 222, 180, 255), "combat slash arc"),
    ("heavy_slash_wave", (210, 168, 114, 255), "heavy combat shockwave"),
    ("parry_flash", (242, 247, 255, 255), "parry flash"),
    ("counter_sparks", (255, 214, 118, 255), "counter sparks"),
    ("dodge_afterimage", (150, 182, 220, 220), "afterimage trail"),
    ("wall_jump_dust", (196, 185, 165, 220), "wall jump dust plume"),
    ("plunge_impact", (182, 144, 120, 255), "plunge impact burst"),
    ("relic_cast_ring", (112, 164, 226, 220), "relic cast ring"),
    ("goduly_verdict_seal", (219, 188, 100, 230), "goduly verdict seal"),
    ("ink_sigil_flare", (111, 117, 171, 230), "ink sigil flare"),
    ("plague_spore_burst", (154, 194, 121, 220), "plague spore burst"),
    ("lantern_fire_bloom", (255, 178, 72, 220), "lantern fire bloom"),
    ("rain_splash_sheet", (116, 168, 214, 210), "rain splash effect"),
    ("cinder_wake", (244, 164, 102, 220), "cinder wake effect"),
    ("fog_gate_ripple", (196, 212, 228, 210), "fog gate ripple"),
    ("boss_phase_shift_ring", (184, 118, 188, 230), "boss phase shift ring"),
]

PARALLAX_LAYERS = [
    ("tribunal_sky_dawn", "parallax", (205, 115, 92, 255)),
    ("tribunal_sky_dusk", "parallax", (72, 96, 169, 255)),
    ("salt_forest_canopy", "parallax", (76, 134, 101, 255)),
    ("ossuary_spires", "parallax", (151, 144, 169, 255)),
    ("marsh_mist_depth", "orbengine_depth", (120, 170, 165, 255)),
    ("cathedral_depth_strip", "orbengine_depth", (165, 128, 105, 255)),
    ("reality_render_rain", "fx_overlay", (118, 166, 210, 220)),
    ("moonlit_cinders", "fx_overlay", (226, 191, 105, 220)),
]

PORTRAITS = [
    ("kier_portrait", (194, 86, 76, 255)),
    ("abbess_portrait", (83, 119, 198, 255)),
    ("judge_portrait", (161, 143, 173, 255)),
    ("elder_portrait", (97, 147, 96, 255)),
    ("goduly_portrait", (207, 178, 96, 255)),
    ("boss_portrait", (120, 84, 124, 255)),
]

SOUNDS = ["tribunal_chime", "ronin_step", "parry_spark", "goduly_whisper", "boss_verdict", "marsh_wind"]

ARCS = [
    {
        "title": "Arc I: Ash of the Oath",
        "summary": "Kier returns to the reedbound fief of Hallowfen to investigate plague writs naming rat clans as originators of the continent's wasting blight.",
        "events": [
            ("The Reed Gate", "exploration", "Kier crosses the flood-barrier and learns the tribunal has sealed the ancestral district."),
            ("Salt in the Wells", "combat", "Low-tier bailiffs and censer monks attack as Kier uncovers forged disease ledgers."),
            ("Writ of Cinders", "exploration", "A hidden archive reveals that the accusation predates the plague by generations."),
            ("The Bell Below", "combat", "Kier defeats the Plague Bell pack-master beneath the ferry crypts."),
            ("Ancestral Silt", "exploration", "A Goduly offers a memory shard showing human merchants importing the true contagion."),
        ],
    },
    {
        "title": "Arc II: Litigants of the Fen",
        "summary": "The tribunal's deputies pursue Kier through marsh villages while local houses bargain over truth, fear, and grain routes.",
        "events": [
            ("Fen Market Interdiction", "exploration", "NPC factions react to Kier's reputation as rumors spread through the open-world settlements."),
            ("Ballad of Moss and Iron", "exploration", "The Penitent Poet unlocks a side route into the Salt Forest via a metered verse challenge."),
            ("Abbey Ballista", "combat", "A mid-tier siege keeper turns the canopy paths into a projectile gauntlet."),
            ("Ferryman's Ledger", "exploration", "Travel records prove the plague entered by war-barge from the western principalities."),
            ("Marsh Inquisitor", "combat", "A mounted inquisitor attempts to burn the evidence and brand Kier a heretic."),
            ("Witnesses in Amber", "exploration", "Goduly avatars preserve testimonies in suspended resin, expanding the procedural lore graph."),
        ],
    },
    {
        "title": "Arc III: Cathedral of Rotated Truth",
        "summary": "Kier infiltrates the tribunal cathedral where verdicts are literally carved into shifting architecture and history is rearranged by ritual.",
        "events": [
            ("The Rotating Nave", "exploration", "Pseudo-3D parallax chambers rotate while Kier navigates orbital lifts and hidden judgment shafts."),
            ("Notary Blades", "combat", "Clockwork scribes and top-tier duelist bailiffs guard the chamber of inherited blame."),
            ("The False Origin", "exploration", "A secret mural shows the tribunal needed a foreign culprit to unify the warring fiefdoms."),
            ("Sable Notary", "combat", "Kier duels the Sable Notary, who weaponizes edited memories as phase attacks."),
        ],
    },
    {
        "title": "Arc IV: Godulies in Session",
        "summary": "Cosmic deity avatars descend to test whether Kier seeks justice, vengeance, or simply a replacement lie.",
        "events": [
            ("Amber Accord", "exploration", "The first Goduly demands that Kier reenact the first trial in a memory theater."),
            ("Trial of Mercy", "combat", "Optional duels against mirrored ronin examine how the player treats neutral factions."),
            ("Lantern Grace", "exploration", "Traversing astral reed bridges unlocks parallax reality layers over the main world."),
            ("Verdict Gaze", "combat", "A Goduly interaction sequence becomes a combat test if Kier's reputation falls too low."),
            ("Ink Saint Deposition", "exploration", "The last living plague survivor reveals a state-sponsored coverup."),
            ("Orbit of Hollow Names", "combat", "Twelve deity avatars overlap their arenas in a multi-phase boss council."),
            ("The Open Record", "exploration", "Kier chooses which truths to release, altering final world-state generation."),
        ],
    },
    {
        "title": "Arc V: Tribunal of Pertinence",
        "summary": "The accusation against Kier's ancestors is retried in the ruins of the high court as the entire continent watches the result ripple outward.",
        "events": [
            ("The Continent Listens", "exploration", "Settlements reflect accumulated player reputation, alliances, and witness testimony."),
            ("Sepulchral Judge", "combat", "The high judge enters a souls-like duel phase with summons from every prior arc."),
            ("Cartographer of Blight", "combat", "The final boss remaps the arena using plague routes and cosmic star-lines."),
            ("Pertinence Rendered", "exploration", "Kier delivers a final verdict: absolution, condemnation, or shared culpability."),
            ("After the Record", "exploration", "The world regenerates under the chosen truth, seeding New Game Plus myth variants."),
        ],
    },
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def total_frames(animations: list[tuple[str, int]]) -> int:
    return sum(frame_count for _, frame_count in animations)


def make_sheet(path: Path, base_color: tuple[int, int, int, int], frame_w: int, frame_h: int, animations: list[tuple[str, int]], silhouette: str) -> dict:
    ensure_dir(path.parent)
    columns = min(8, max(frame_count for _, frame_count in animations))
    rows = len(animations)
    image = Image.new("RGBA", (columns * frame_w, rows * frame_h), TRANSPARENT)
    draw = ImageDraw.Draw(image)
    for row, (_, frame_count) in enumerate(animations):
        for column in range(frame_count):
            x0 = column * frame_w
            y0 = row * frame_h
            intensity = 0.72 + 0.28 * ((column + 1) / max(frame_count, 1))
            tint = tuple(min(255, int(channel * intensity)) for channel in base_color[:3]) + (255,)
            accent = tuple(min(255, int(channel * 0.55)) for channel in base_color[:3]) + (220,)
            inset = max(4, frame_w // 8)
            if silhouette == "rat_ronin":
                draw.ellipse((x0 + inset, y0 + inset, x0 + frame_w - inset, y0 + frame_h - inset * 2), fill=tint)
                draw.rectangle((x0 + frame_w * 0.52, y0 + frame_h * 0.18, x0 + frame_w * 0.76, y0 + frame_h * 0.7), fill=accent)
                draw.polygon([(x0 + frame_w * 0.7, y0 + frame_h * 0.25), (x0 + frame_w * 0.95, y0 + frame_h * 0.12), (x0 + frame_w * 0.8, y0 + frame_h * 0.38)], fill=(230, 230, 220, 255))
            elif silhouette == "humanoid":
                draw.rounded_rectangle((x0 + inset, y0 + inset, x0 + frame_w - inset, y0 + frame_h - inset), radius=inset, fill=tint)
                draw.rectangle((x0 + frame_w * 0.35, y0 + frame_h * 0.18, x0 + frame_w * 0.65, y0 + frame_h * 0.78), fill=accent)
            elif silhouette == "beast":
                draw.polygon([(x0 + inset, y0 + frame_h * 0.8), (x0 + frame_w * 0.45, y0 + inset), (x0 + frame_w - inset, y0 + frame_h * 0.75)], fill=tint)
                draw.ellipse((x0 + frame_w * 0.35, y0 + frame_h * 0.25, x0 + frame_w * 0.75, y0 + frame_h * 0.65), fill=accent)
            elif silhouette == "cosmic":
                draw.ellipse((x0 + inset, y0 + inset, x0 + frame_w - inset, y0 + frame_h - inset), fill=tint)
                draw.ellipse((x0 + frame_w * 0.3, y0 + frame_h * 0.3, x0 + frame_w * 0.7, y0 + frame_h * 0.7), fill=TRANSPARENT, outline=(255, 255, 255, 220), width=2)
                draw.line((x0 + frame_w * 0.2, y0 + frame_h * 0.5, x0 + frame_w * 0.8, y0 + frame_h * 0.5), fill=accent, width=3)
            elif silhouette == "effect":
                draw.arc((x0 + inset, y0 + inset, x0 + frame_w - inset, y0 + frame_h - inset), start=20, end=300, fill=tint, width=5)
                draw.arc((x0 + frame_w * 0.2, y0 + frame_h * 0.2, x0 + frame_w * 0.8, y0 + frame_h * 0.8), start=120, end=360, fill=accent, width=4)
                draw.ellipse((x0 + frame_w * 0.42, y0 + frame_h * 0.42, x0 + frame_w * 0.58, y0 + frame_h * 0.58), fill=(255, 255, 255, 190))
            else:
                draw.rectangle((x0 + inset, y0 + inset, x0 + frame_w - inset, y0 + frame_h - inset), fill=tint)
            draw.rectangle((x0 + 1, y0 + 1, x0 + frame_w - 2, y0 + frame_h - 2), outline=(255, 255, 255, 96))
    image.save(path)
    return {"width": image.width, "height": image.height, "alpha": True}


def make_tile_layer(path: Path, base_color: tuple[int, int, int, int], tile_w: int, tile_h: int, columns: int, rows: int) -> dict:
    ensure_dir(path.parent)
    image = Image.new("RGBA", (tile_w * columns, tile_h * rows), TRANSPARENT)
    draw = ImageDraw.Draw(image)
    for row in range(rows):
        for column in range(columns):
            x0 = column * tile_w
            y0 = row * tile_h
            pulse = 0.78 + 0.22 * ((row + column + 1) / (rows + columns))
            tint = tuple(min(255, int(channel * pulse)) for channel in base_color[:3]) + (220,)
            draw.rectangle((x0 + 1, y0 + 1, x0 + tile_w - 2, y0 + tile_h - 2), fill=tint)
            draw.line((x0 + 2, y0 + tile_h - 4, x0 + tile_w - 3, y0 + 3), fill=(255, 255, 255, 72), width=1)
            draw.line((x0 + 2, y0 + 3, x0 + tile_w - 3, y0 + tile_h - 4), fill=(0, 0, 0, 72), width=1)
    image.save(path)
    return {"width": image.width, "height": image.height, "alpha": True}


def make_portrait(path: Path, base_color: tuple[int, int, int, int]) -> dict:
    ensure_dir(path.parent)
    image = Image.new("RGBA", (256, 256), TRANSPARENT)
    draw = ImageDraw.Draw(image)
    draw.ellipse((32, 24, 224, 216), fill=base_color)
    draw.rectangle((72, 152, 184, 230), fill=(base_color[0] // 2, base_color[1] // 2, base_color[2] // 2, 255))
    draw.ellipse((86, 86, 112, 112), fill=(255, 255, 255, 255))
    draw.ellipse((144, 86, 170, 112), fill=(255, 255, 255, 255))
    draw.arc((90, 118, 166, 170), start=20, end=160, fill=(255, 245, 225, 255), width=4)
    image.save(path)
    return {"width": image.width, "height": image.height, "alpha": True}


def make_silent_wav(path: Path, seconds: float = 0.4, sample_rate: int = 22050) -> None:
    ensure_dir(path.parent)
    frame_count = int(seconds * sample_rate)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(b"\x00\x00" * frame_count)


def slug_to_title(slug: str) -> str:
    return slug.replace("_", " ").title()


def entity_prompt(name: str, role: str, color_theme: str, biome: str, animations: list[tuple[str, int]]) -> str:
    animation_names = ", ".join(animation for animation, _ in animations[:6])
    return (
        f"transparent background detailed 2D side-view spritesheet for {slug_to_title(name)}, a {role} in Pertinence: Tribunal; "
        f"distinct silhouette, hand-painted souls-like metroidvania style, wide color range focused on {color_theme}, "
        f"environmental influence from {biome}, include readable key poses for {animation_names}, high detail, no text"
    )


def fx_prompt(name: str, role: str, color_theme: str) -> str:
    return (
        f"transparent background detailed 2D combat and traversal FX spritesheet for {slug_to_title(name)} in Pertinence: Tribunal; "
        f"readable frame-to-frame energy motion for {role}, painterly metroidvania style, coherent with tribunal swamp-cathedral world palette, "
        f"color focus on {color_theme}, no backdrop, no floor, no frame, no text"
    )


def make_sprite_asset(asset_id: str, path: Path, usage: str, base_color: tuple[int, int, int, int], animations: list[tuple[str, int]], silhouette: str, role: str, biome: str) -> dict:
    frame_w = 64 if usage in {"player", "boss", "goduly", "fx"} else 48
    frame_h = 64 if usage in {"player", "boss", "goduly", "fx"} else 48
    make_sheet(path, base_color, frame_w, frame_h, animations, silhouette)
    return {
        "id": asset_id,
        "path": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "frames": total_frames(animations),
        "usage": usage,
        "material_profile": "default_sprite_material" if usage not in {"goduly", "boss"} else "astral_lacquer_material",
        "collider": {"shape": "capsule", "radius": 0.3 if usage == "player" else 0.35, "height": 1.8 if usage == "player" else 1.6},
        "animations": [{"name": name, "frames": frames} for name, frames in animations],
        "visual_theme": color_tuple_to_hex(base_color),
        "role": role,
        "prompt": entity_prompt(asset_id, role, color_tuple_to_hex(base_color), biome, animations),
    }


def make_fx_asset(asset_id: str, path: Path, base_color: tuple[int, int, int, int], role: str) -> dict:
    make_sheet(path, base_color, 64, 64, FX_ANIMATIONS, "effect")
    return {
        "id": asset_id,
        "path": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "frames": total_frames(FX_ANIMATIONS),
        "usage": "fx",
        "material_profile": "astral_lacquer_material",
        "collider": {"shape": "sphere", "radius": 0.05, "height": 0.05},
        "animations": [{"name": name, "frames": frames} for name, frames in FX_ANIMATIONS],
        "visual_theme": color_tuple_to_hex(base_color),
        "role": role,
        "prompt": fx_prompt(asset_id, role, color_tuple_to_hex(base_color)),
    }


def color_tuple_to_hex(color: tuple[int, int, int, int]) -> str:
    return "#%02x%02x%02x" % color[:3]


def build_catalog() -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict]]:
    tilesets = []
    sprites = []
    portraits = []
    fx_assets = []
    recraft_manifest = []

    kier_color = (193, 82, 74, 255)
    kier_path = SPRITE_ROOT / "kier_rat_ronin.png"
    sprites.append(make_sprite_asset("kier_rat_ronin", kier_path, "player", kier_color, PLAYER_ANIMATIONS, "rat_ronin", "rat-man ronin protagonist", "mist-lashed tribunal frontier"))

    for index, (name, archetype, silhouette) in enumerate(LOW_TIER_DEFS):
        color = (108 + (index * 7) % 90, 94 + (index * 5) % 110, 74 + (index * 9) % 120, 255)
        path = SPRITE_ROOT / f"{name}.png"
        sprites.append(make_sprite_asset(name, path, "enemy_low", color, LOW_TIER_BY_ARCHETYPE[archetype], silhouette, f"low-tier {archetype} enemy", "marsh settlements and plague shrines"))

    for index, (name, archetype, silhouette) in enumerate(MID_TIER_DEFS):
        color = (82 + (index * 11) % 120, 108 + (index * 13) % 90, 129 + (index * 17) % 80, 255)
        path = SPRITE_ROOT / f"{name}.png"
        sprites.append(make_sprite_asset(name, path, "enemy_mid", color, MID_TIER_BY_ARCHETYPE[archetype], silhouette, f"mid-tier {archetype} enemy", "cathedral precincts and ash bridges"))

    for index, (name, silhouette) in enumerate(TOP_TIER_DEFS):
        color = (120 + index * 20, 70 + index * 15, 110 + index * 18, 255)
        path = SPRITE_ROOT / f"{name}.png"
        sprites.append(make_sprite_asset(name, path, "boss", color, TOP_TIER_ANIMATIONS, silhouette, "top-tier boss enemy", "trial arenas and reality-render chambers"))

    for index, name in enumerate(NPC_NAMES):
        color = (74 + index * 18, 130 + index * 11, 92 + index * 8, 255)
        path = SPRITE_ROOT / f"{name}.png"
        sprites.append(make_sprite_asset(name, path, "npc", color, BASIC_ANIMATIONS, "humanoid", "civilian or quest NPC", "villages, ferries, and archive quarters"))

    for index, name in enumerate(FAUNA_NAMES):
        color = (86 + index * 16, 100 + index * 12, 58 + index * 14, 255)
        path = SPRITE_ROOT / f"{name}.png"
        sprites.append(make_sprite_asset(name, path, "fauna", color, BASIC_ANIMATIONS, "beast", "ambient fauna", "wetlands, canopy, and cavern margins"))

    goduly_animations = BASIC_ANIMATIONS + GODULY_INTERACTIONS
    for index, name in enumerate(GODULY_NAMES):
        color = (160 + (index * 7) % 90, 132 + (index * 11) % 90, 74 + (index * 13) % 150, 255)
        path = SPRITE_ROOT / f"{name}.png"
        sprites.append(make_sprite_asset(name, path, "goduly", color, goduly_animations, "cosmic", "neutral cosmic deity avatar", "astral tribunal overlays and memory reefs"))

    for name, color, role in FX_DEFS:
        path = SPRITE_ROOT / f"{name}.png"
        fx_assets.append(make_fx_asset(name, path, color, role))

    for name, usage, color in PARALLAX_LAYERS:
        path = TILE_ROOT / f"{name}.png"
        meta = make_tile_layer(path, color, 64, 64, 8, 4)
        tilesets.append(
            {
                "id": name,
                "path": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "tile_w": 64,
                "tile_h": 64,
                "semantic_tags": [usage, "environment", "pertinence_tribunal"],
                "usage": usage,
                "material_profile": "street_prop_material" if usage == "parallax" else "astral_lacquer_material",
                "dimensions": meta,
                "prompt": f"transparent layered environment sheet for {slug_to_title(name)} in Pertinence: Tribunal, rich colors, parallax-ready, pseudo-3D depth cues, distinct silhouette forms, no text",
            }
        )

    for name, color in PORTRAITS:
        path = PORTRAIT_ROOT / f"{name}.png"
        meta = make_portrait(path, color)
        portraits.append(
            {
                "id": name,
                "path": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "usage": "dialogue",
                "precache": False,
                "dimensions": meta,
                "prompt": f"transparent illustrated dialogue portrait for {slug_to_title(name)} in Pertinence: Tribunal, painterly detail, high contrast face, no text",
            }
        )

    for asset in sprites + fx_assets + tilesets + portraits:
        recraft_manifest.append(
            {
                "name": asset["id"],
                "prompt": asset["prompt"],
                "w": 1024,
                "h": 1024,
                "out": asset["path"],
                "api_units": 40,
                "model": "recraftv4",
            }
        )

    return tilesets, sprites, portraits, fx_assets, recraft_manifest


def build_manifest(tilesets: list[dict], sprites: list[dict], portraits: list[dict], fx_assets: list[dict]) -> dict:
    clip_layers = [
        {"name": "bg_parallax", "blend_mode": "normal", "visible": True},
        {"name": "midground_world", "blend_mode": "normal", "visible": True},
        {"name": "character_sprites", "blend_mode": "normal", "visible": True},
        {"name": "fx_combat_impacts", "blend_mode": "screen", "visible": True},
        {"name": "fx_spellcraft", "blend_mode": "screen", "visible": True},
        {"name": "fx_rain_depth", "blend_mode": "screen", "visible": True},
        {"name": "collision_guides", "blend_mode": "multiply", "visible": False},
    ]
    systems = [
        {"name": "ronin_combat_system", "priority": 10, "lifecycle": ["init", "tick", "shutdown"]},
        {"name": "combat_fx_system", "priority": 15, "lifecycle": ["init", "tick"]},
        {"name": "metroidvania_traversal_system", "priority": 20, "lifecycle": ["init", "tick"]},
        {"name": "reputation_judgment_system", "priority": 30, "lifecycle": ["init", "tick"]},
        {"name": "procedural_narrative_system", "priority": 40, "lifecycle": ["init", "tick"]},
        {"name": "goduly_interaction_system", "priority": 50, "lifecycle": ["init", "tick"]},
    ]
    scenes = []
    frame_cursor = 0
    for arc_index, arc in enumerate(ARCS, start=1):
        start = frame_cursor
        for event_index, (title, mode, summary) in enumerate(arc["events"], start=1):
            scenes.append(
                {
                    "id": f"arc_{arc_index}_scene_{event_index}",
                    "scene_type": mode,
                    "location": arc["title"].lower().replace(":", "").replace(" ", "_"),
                    "timeline_frames": [frame_cursor, frame_cursor + 47],
                    "triggers": [
                        {"id": f"arc_{arc_index}_scene_{event_index}_enter", "frame": frame_cursor, "event": f"arc_{arc_index}_scene_start", "target": "kier_player"},
                        {"id": f"arc_{arc_index}_scene_{event_index}_resolve", "frame": frame_cursor + 32, "event": f"arc_{arc_index}_scene_resolve", "target": title.lower().replace(" ", "_")},
                    ],
                    "summary": summary,
                }
            )
            frame_cursor += 48
        scenes.append(
            {
                "id": f"arc_{arc_index}_boss_resolution",
                "scene_type": "combat",
                "location": arc["title"].lower().replace(":", "").replace(" ", "_"),
                "timeline_frames": [start, frame_cursor],
                "triggers": [
                    {"id": f"arc_{arc_index}_boss_intro", "frame": start + 12, "event": "boss_intro", "target": TOP_TIER_DEFS[(arc_index - 1) % len(TOP_TIER_DEFS)][0]},
                    {"id": f"arc_{arc_index}_boss_fall", "frame": frame_cursor - 8, "event": "boss_resolve", "target": "kier_player"},
                ],
            }
        )
        frame_cursor += 48

    entities = [
        {"id": "kier_player", "classname": "player_rat_ronin", "asset_id": "kier_rat_ronin", "spawn": [128, 80, 0], "logic_components": ["controllable", "soulslike_stamina", "reputation_anchor"]},
        {"id": "first_goduly", "classname": "goduly_avatar", "asset_id": GODULY_NAMES[0], "spawn": [960, 120, 0], "logic_components": ["neutral_entity", "dialogue_actor", "ritual_gate"]},
        {"id": "first_boss", "classname": "boss_sepulchral_judge", "asset_id": TOP_TIER_DEFS[0][0], "spawn": [1536, 128, 0], "logic_components": ["boss_logic", "phase_controller"]},
    ]
    for index, (name, _, _) in enumerate(LOW_TIER_DEFS[:8], start=1):
        entities.append({"id": f"low_enemy_{index}", "classname": f"enemy_{name}", "asset_id": name, "spawn": [240 + index * 96, 92, 0], "logic_components": ["patrol", "aggro"]})
    for index, (name, _, _) in enumerate(MID_TIER_DEFS[:5], start=1):
        entities.append({"id": f"mid_enemy_{index}", "classname": f"enemy_{name}", "asset_id": name, "spawn": [820 + index * 128, 104, 0], "logic_components": ["elite_ai", "arena_lock"]})
    for index, name in enumerate(NPC_NAMES[:3], start=1):
        entities.append({"id": f"npc_{index}", "classname": f"npc_{name}", "asset_id": name, "spawn": [140 + index * 220, 88, 0], "logic_components": ["questgiver", "dialogue_actor"]})

    return {
        "project_name": "PertinenceTribunal",
        "seed": "PERTINENCE-TRIBUNAL-PS6-ALPHA",
        "authoring": {
            "clipstudio": {
                "canvas": {"width": 4096, "height": 4096, "layers": 24},
                "timeline_fps": 12,
                "export_profile": {"color_mode": "rgba", "naming": "asset_id", "slice_method": "layer_group"},
                "layers": clip_layers,
                "script_symbols": ["KierSpawn", "VerdictGate", "GodulyAudience", "BossThreshold", "ParallaxDepthShift", "CombatFXRelay"],
                "symbol_bindings": [
                    {"symbol": "KierSpawn", "asset_id": "kier_rat_ronin", "role": "player_spawn"},
                    {"symbol": "VerdictGate", "asset_id": "tribunal_sky_dawn", "role": "world_transition"},
                    {"symbol": "GodulyAudience", "asset_id": GODULY_NAMES[0], "role": "neutral_interaction"},
                    {"symbol": "CombatFXRelay", "asset_id": FX_DEFS[0][0], "role": "combat_fx_anchor"},
                ],
                "frame_tags": [{"tag": scene["id"], "frame": scene["timeline_frames"][0], "scene_id": scene["id"]} for scene in scenes[:12]],
                "hitboxes": [
                    {"symbol": "KierSpawn", "frame": 0, "x": 10, "y": 8, "w": 28, "h": 44, "kind": "hurtbox"},
                    {"symbol": "BossThreshold", "frame": 0, "x": 0, "y": 0, "w": 64, "h": 96, "kind": "trigger"},
                ],
                "script_bindings": [
                    {"name": "open_arc_one", "event": "arc_1_scene_start", "target_symbol": "KierSpawn", "command": "play_dialogue:ash_of_the_oath"},
                    {"name": "invoke_goduly", "event": "arc_4_scene_start", "target_symbol": "GodulyAudience", "command": "spawn_neutral_council"},
                    {"name": "shift_parallax", "event": "arc_3_scene_resolve", "target_symbol": "ParallaxDepthShift", "command": "enable_reality_render"},
                    {"name": "trigger_combat_fx", "event": "boss_intro", "target_symbol": "CombatFXRelay", "command": "spawn_fx:goduly_verdict_seal"},
                ],
            },
            "blender": {
                "scale": 0.1,
                "extrusion_depth": 0.1,
                "rig_profile": "paperdoll_humanoid",
                "material_profiles": [
                    {"name": "default_sprite_material", "shader": "toon_principled", "roughness": 0.75, "normal_strength": 0.18},
                    {"name": "street_prop_material", "shader": "trim_sheet", "roughness": 0.62, "normal_strength": 0.28},
                    {"name": "astral_lacquer_material", "shader": "emissive_layered", "roughness": 0.35, "normal_strength": 0.12},
                ],
                "rig_overrides": [
                    {"asset_id": "kier_rat_ronin", "armature": "ronin_humanoid", "root_bone": "hips"},
                    {"asset_id": TOP_TIER_DEFS[0][0], "armature": "tribunal_boss", "root_bone": "pelvis"},
                ],
                "nodecraft_graphs": [
                    {
                        "name": "tribunal_depth_graph",
                        "nodes": [
                            {"id": "foreground", "position": [0.0, 0.0, 0.0], "scale": 1.0},
                            {"id": "midground", "position": [8.0, 0.0, -2.0], "scale": 1.0},
                            {"id": "backdrop", "position": [16.0, 0.0, -5.0], "scale": 1.0},
                        ],
                        "links": [
                            {"from": "foreground", "to": "midground", "type": "LINKAGE_CHAIN", "thickness": 0.45},
                            {"from": "midground", "to": "backdrop", "type": "LINKAGE_LATTICE", "thickness": 0.35},
                        ],
                    }
                ],
                "scene_build": [
                    {"scene_id": scene["id"], "collection": scene["location"], "world_mesh": f"{scene['location']}_mesh"}
                    for scene in scenes[:10]
                ],
            },
            "idtech2": {
                "module_name": "g_pertinencetribunal",
                "asset_root": "baseq2/pertinencetribunal",
                "autofactor_prefix": "pertinence",
                "precache_groups": [
                    {"group_name": "sound", "entries": [{"alias": name, "path": f"sound/pertinence/{name}.wav", "asset_type": "sound"} for name in SOUNDS]},
                ],
                "system_dispatch": {
                    system["name"]: {"init_fn": f"{system['name']}_init", "tick_fn": f"{system['name']}_tick"}
                    for system in systems
                },
                "bootstrap": {"entry_scene": scenes[0]["id"] if scenes else "arc_1_scene_1", "precache_phase": "game_init", "spawn_phase": "level_load"},
            },
        },
        "assets": {"tilesets": tilesets, "sprites": sprites + fx_assets, "portraits": portraits},
        "gameplay": {"scenes": scenes, "entities": entities, "systems": systems},
        "targets": {"clipstudio_bundle": "clipstudio_bundle", "blender_bundle": "blender_bundle", "idtech2_bundle": "idtech2_bundle"},
    }


def build_gdd(manifest: dict) -> str:
    total_sprite_assets = len(manifest["assets"]["sprites"])
    total_environment_assets = len(manifest["assets"]["tilesets"])
    total_portraits = len(manifest["assets"]["portraits"])
    fx_total = len([asset for asset in manifest["assets"]["sprites"] if asset.get("usage") == "fx"])
    low_total = len(LOW_TIER_DEFS)
    mid_total = len(MID_TIER_DEFS)
    top_total = len(TOP_TIER_DEFS)
    arc_lines = []
    for arc in ARCS:
        arc_lines.append(f"## {arc['title']}")
        arc_lines.append(arc["summary"])
        arc_lines.append("")
        for idx, (title, mode, summary) in enumerate(arc["events"], start=1):
            arc_lines.append(f"{idx}. {title} [{mode}] - {summary}")
        arc_lines.append("")

    return "\n".join(
        [
            "# Pertinence: Tribunal - Game Design Document",
            "",
            "## High Concept",
            "Pertinence: Tribunal is a side-scrolling souls-like metroidvania action-platformer RPG about Kier, a rat-man ronin forced to cross a procedurally recomposed fiefdom and tribunal-state to disprove the myth that his ancestors brought disease to the continent.",
            "",
            "## Aesthetic Direction",
            "- Painterly 2D spritesheets with transparent backgrounds and hard-read silhouettes.",
            "- Dense swamp, cathedral, ossuary, and cosmic courtroom biomes with rich warm-cold palette contrast.",
            "- ORBEngine-style pseudo-3D depth strips, layered parallax, and reality-render overlays for astral transitions.",
            "- Costume language: reed-wrapped ronin cloth, lacquered tribunal armor, salt-eroded stone, moonlit brass, wet ink blacks, and fungal whites.",
            "",
            "## Core Pillars",
            "- Exacting melee combat with block, parry, dodge, and stance commitment.",
            "- Procedural narrative assembly through witness testimony, Goduly interventions, and regional rumor graphs.",
            "- Reputation-driven world response that changes exploration routes, boss context, and available truths.",
            "",
            "## Asset Program",
            f"- Sprite sheets: {total_sprite_assets}",
            f"- Environmental/parallax/depth sheets: {total_environment_assets}",
            f"- Dialogue portraits: {total_portraits}",
            f"- Dedicated combat/traversal/environment FX sheets: {fx_total}",
            "- Seven entity classes: player, low-tier enemy, mid-tier enemy, top-tier enemy, NPC, fauna, and Goduly.",
            "",
            "## Animation Bible",
            "### Kier, the Player Rat-Man Ronin",
            "- Expanded player combat and traversal suite: " + ", ".join(f"{name} ({frames}f)" for name, frames in PLAYER_ANIMATIONS),
            "- Frame plan: anticipation 2f, action 2-4f, recovery 2-4f, silhouette break on each attack apex, sword readable at every key frame.",
            "",
            f"### Low-Tier Enemies ({low_total} types)",
            "- Archetype sets: skirmisher, ambush, ranged, brute.",
            "- Skirmisher set: " + ", ".join(f"{name} ({frames}f)" for name, frames in LOW_TIER_SKIRMISHER_ANIMATIONS),
            "- Ambush set: " + ", ".join(f"{name} ({frames}f)" for name, frames in LOW_TIER_AMBUSH_ANIMATIONS),
            "- Ranged set: " + ", ".join(f"{name} ({frames}f)" for name, frames in LOW_TIER_RANGED_ANIMATIONS),
            "- Brute set: " + ", ".join(f"{name} ({frames}f)" for name, frames in LOW_TIER_BRUTE_ANIMATIONS),
            "- Function: harassment, attrition, environmental pressure, plague-ridden crowd control.",
            "",
            f"### Mid-Tier Enemies ({mid_total} types)",
            "- Archetype sets: duelist, caster, siege.",
            "- Duelist set: " + ", ".join(f"{name} ({frames}f)" for name, frames in MID_TIER_DUELIST_ANIMATIONS),
            "- Caster set: " + ", ".join(f"{name} ({frames}f)" for name, frames in MID_TIER_CASTER_ANIMATIONS),
            "- Siege set: " + ", ".join(f"{name} ({frames}f)" for name, frames in MID_TIER_SIEGE_ANIMATIONS),
            "- Function: gatekeeping traversal checks, mixed melee-ranged pressure, elite arena anchors.",
            "",
            f"### Top-Tier Enemies ({top_total} types)",
            "- Boss set: " + ", ".join(f"{name} ({frames}f)" for name, frames in TOP_TIER_ANIMATIONS),
            "- Function: major bosses with phase changes, summon states, and arena-control attacks.",
            "",
            "### NPC, Fauna, and Goduly",
            "- NPCs and fauna use the basic set: " + ", ".join(f"{name} ({frames}f)" for name, frames in BASIC_ANIMATIONS),
            "- Godulies use the basic set plus interactions: " + ", ".join(f"{name} ({frames}f)" for name, frames in GODULY_INTERACTIONS),
            "- FX sheets use a shared six-stage timing plan: " + ", ".join(f"{name} ({frames}f)" for name, frames in FX_ANIMATIONS),
            "",
            "## Environment Requirements",
            "- Flooded rice terraces, salt forests, ossuary caverns, tribunal cathedrals, archive ferries, and cosmic witness chambers.",
            "- Every exploration zone needs foreground, midground, and backdrop layers plus a depth or reality-render overlay when narrative pressure spikes.",
            "- Environmental sheets must support parallax and pseudo-3D strip extrusion in Blender/ORB-style staging.",
            "",
            "## Narrative Structure",
            *arc_lines,
            "## Technical Test Intent",
            "- Asset pack is organized to validate Clip Studio export metadata, Blender conversion plans, and idTech2 spawn/precache/dispatch generation.",
            "- Placeholder sheets retain transparency and category-specific silhouette language so automated validation can inspect alpha usage and bundle coverage.",
        ]
    )


def build_pitch(manifest: dict) -> str:
    return "\n".join(
        [
            "# Pertinence: Tribunal - PlayStation 6 Pitch",
            "",
            "## Elevator Pitch",
            "Pertinence: Tribunal is a prestige side-scrolling action RPG for PlayStation 6 where a rat-man ronin cuts through a procedural regime of rumor, plague myth, and cosmic jurisprudence in a painterly 2D world staged with depth-rich parallax and ritual pseudo-3D transitions.",
            "",
            "## Why PS6",
            "- Fast streaming supports seamless traversal across dense layered biomes with no scene breaks.",
            "- Hardware overhead enables ornate 2D FX, dynamic lighting passes, and reality-render overlays without sacrificing combat response.",
            "- DualSense successor haptics can map blade deflection, marsh footing, rainfall, and Goduly resonance to player feedback.",
            "",
            "## Audience",
            "- Players of Hollow Knight, Blasphemous, Salt and Sanctuary, Dead Cells, and prestige narrative action RPGs.",
            "- Fans of folklore reinterpretation, factional consequence systems, and skill-heavy melee combat.",
            "",
            "## Differentiators",
            "- A procedural narrative tribunal that reorders testimony, regional rumor, and faction blame on each campaign arc.",
            "- A seven-class entity ecosystem anchored by neutral cosmic Godulies whose presence changes moral framing rather than simple combat balance.",
            "- A visual stack blending hand-painted spritesheets with parallax cathedrals, astral overlays, and pseudo-3D stagecraft.",
            "",
            "## Production Test Deliverables Prepared Here",
            f"- {len(manifest['assets']['sprites'])} spritesheets prepared, including expanded combatants and FX assets.",
            f"- {len(manifest['assets']['tilesets'])} environmental/parallax/depth sheets prepared as transparent test assets.",
            f"- {len(manifest['assets']['portraits'])} dialogue portraits prepared as transparent test assets.",
            "- Full pipeline manifest, Recraft-ready batch plan, and automated end-to-end validation flow.",
        ]
    )


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    for directory in [SPRITE_ROOT, TILE_ROOT, PORTRAIT_ROOT, SOUND_ROOT]:
        ensure_dir(directory)

    tilesets, sprites, portraits, fx_assets, recraft_manifest = build_catalog()
    manifest = build_manifest(tilesets, sprites, portraits, fx_assets)

    for sound_name in SOUNDS:
        make_silent_wav(SOUND_ROOT / f"{sound_name}.wav")

    write_json(MANIFEST_PATH, manifest)
    write_json(RECRAFT_MANIFEST_PATH, recraft_manifest)
    GDD_PATH.write_text(build_gdd(manifest), encoding="utf-8")
    PITCH_PATH.write_text(build_pitch(manifest), encoding="utf-8")

    summary = {
        "project_root": str(PROJECT_ROOT),
        "sprite_assets": len(sprites) + len(fx_assets),
        "tilesets": len(tilesets),
        "portraits": len(portraits),
        "fx_assets": len(fx_assets),
        "recraft_requests": len(recraft_manifest),
        "recraft_budget_units": sum(item["api_units"] for item in recraft_manifest),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())