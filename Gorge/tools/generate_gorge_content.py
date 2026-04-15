from __future__ import annotations

import json
import math
import wave
from array import array
from dataclasses import dataclass
from pathlib import Path
from random import Random

from PIL import Image, ImageDraw


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GENERATED_ROOT = PROJECT_ROOT / "generated"
CARD_ROOT = GENERATED_ROOT / "cards"
AUDIO_ROOT = GENERATED_ROOT / "audio"
HEADER_PATH = PROJECT_ROOT / "src" / "generated" / "gorge_content.h"
MANIFEST_PATH = GENERATED_ROOT / "gorge_manifest.json"
TITLE_LOGO_PATH = GENERATED_ROOT / "gorge_title_logo.png"

CARD_W = 120
CARD_H = 168
SAMPLE_RATE = 22050

FAMILY_NAMES = ["Gaolite", "Jeurgren", "Fallows", "Jools", "Gaorg"]
ROLE_NAMES = ["Striker", "Bulwark", "Oracle", "Harrier", "Conduit", "Brood"]
INSTINCT_NAMES = ["Balance", "Rush", "Shell", "Trick"]
ABILITY_NAMES = [
    "Emberheart",
    "Tideglass",
    "Shellscript",
    "Canopy Veil",
    "Vault Memory",
    "Snare Hunger",
    "Chorus Root",
    "Rift Quarry",
]
TECHNIQUE_NAMES = ["Cleave", "Torrent", "Prism", "Briar", "Quarry", "Volt", "Leech", "Ruin"]
HABITAT_NAMES = ["Kiln", "Flood", "Canopy", "Vault"]

FAMILY_COLORS = {
    0: ((240, 92, 88), (255, 202, 168), (116, 36, 30)),
    1: ((96, 210, 248), (214, 244, 255), (32, 82, 118)),
    2: ((164, 220, 98), (240, 255, 194), (70, 104, 34)),
    3: ((252, 220, 88), (255, 248, 214), (132, 96, 28)),
    4: ((198, 126, 255), (244, 226, 255), (92, 54, 144)),
}

VARIANT_SUFFIXES = ["Spark", "Maw", "Thread", "Bore"]
EVOLUTION_SUFFIXES = [("Prime", "Flux"), ("Crest", "Howl"), ("Spire", "Wake"), ("Bloom", "Ruin")]
DECK_REWARD_CARDS = [12, 24, 48]

DECKS = [
    {
        "name": "Ashrail",
        "theme": "coal rail trenches and furnace sidings",
        "accent": (158, 70, 62),
        "boss_title": "Rail Warden",
        "relic_name": "Ashrail Brand",
        "route": (0, 0),
        "pressure": 1,
    },
    {
        "name": "Brineshard",
        "theme": "salt docks and tidal scrapyards",
        "accent": (78, 134, 168),
        "boss_title": "Salt Archivist",
        "relic_name": "Brine Prism",
        "route": (0, 1),
        "pressure": 1,
    },
    {
        "name": "Cindercoil",
        "theme": "smoke pipes and ember cisterns",
        "accent": (196, 110, 56),
        "boss_title": "Coil Forger",
        "relic_name": "Cinder Dynamo",
        "route": (0, 2),
        "pressure": 1,
    },
    {
        "name": "Mireglass",
        "theme": "bog mirrors and algae towers",
        "accent": (66, 150, 116),
        "boss_title": "Bog Mirror",
        "relic_name": "Mire Glass",
        "route": (1, 0),
        "pressure": 2,
    },
    {
        "name": "Voltfen",
        "theme": "sparking levees and cable marshes",
        "accent": (228, 196, 64),
        "boss_title": "Fen Marshal",
        "relic_name": "Fen Dynamo",
        "route": (1, 1),
        "pressure": 2,
    },
    {
        "name": "Gravesilt",
        "theme": "catacomb washways and drowned stone",
        "accent": (114, 108, 138),
        "boss_title": "Crypt Ferrier",
        "relic_name": "Gravesilt Husk",
        "route": (1, 2),
        "pressure": 2,
    },
    {
        "name": "Chromeburrow",
        "theme": "buried machine warrens and iron dust",
        "accent": (112, 130, 144),
        "boss_title": "Burrow Tuner",
        "relic_name": "Chrome Lattice",
        "route": (1, 3),
        "pressure": 2,
    },
    {
        "name": "Fathomyard",
        "theme": "sunken depots and rope gantries",
        "accent": (90, 132, 184),
        "boss_title": "Yard Diver",
        "relic_name": "Fathom Cable",
        "route": (2, 0),
        "pressure": 3,
    },
    {
        "name": "Giltreef",
        "theme": "ornate sewer reefs and lamp slime",
        "accent": (202, 170, 84),
        "boss_title": "Lamp Regent",
        "relic_name": "Gilt Lantern",
        "route": (2, 1),
        "pressure": 3,
    },
    {
        "name": "Slablight",
        "theme": "quarry shrines and sodium courtyards",
        "accent": (196, 188, 120),
        "boss_title": "Courtyard Judge",
        "relic_name": "Slab Halo",
        "route": (2, 2),
        "pressure": 3,
    },
    {
        "name": "Rustwake",
        "theme": "derelict piers and oxidized culverts",
        "accent": (172, 92, 74),
        "boss_title": "Wake Reaver",
        "relic_name": "Rust Harrow",
        "route": (2, 3),
        "pressure": 3,
    },
    {
        "name": "Mothclasp",
        "theme": "velvet attics and powder tunnels",
        "accent": (170, 116, 196),
        "boss_title": "Velvet Binder",
        "relic_name": "Moth Screen",
        "route": (3, 0),
        "pressure": 4,
    },
    {
        "name": "Thornfoundry",
        "theme": "vine foundries and root-fed smokestacks",
        "accent": (104, 152, 78),
        "boss_title": "Root Smith",
        "relic_name": "Thorn Graft",
        "route": (3, 1),
        "pressure": 4,
    },
    {
        "name": "Duskquarry",
        "theme": "evening pits and haunted slab roads",
        "accent": (120, 116, 148),
        "boss_title": "Dusk Surveyor",
        "relic_name": "Quarry Rift",
        "route": (3, 2),
        "pressure": 4,
    },
]

SONG_EVENTS = {
    "title": [
        (262, 392, 8, 5, 0, 14), (330, 494, 8, 5, 0, 14), (392, 523, 9, 5, 0, 14), (330, 494, 8, 5, 0, 14),
        (440, 659, 9, 5, 1, 14), (392, 523, 8, 5, 0, 14), (330, 494, 8, 5, 0, 14), (294, 440, 7, 4, 0, 14),
    ],
    "world": [
        (220, 330, 7, 4, 0, 16), (247, 370, 7, 4, 0, 16), (277, 415, 7, 4, 0, 16), (247, 370, 7, 4, 0, 16),
        (196, 294, 6, 4, 0, 16), (220, 330, 7, 4, 0, 16), (247, 370, 7, 4, 1, 16), (185, 277, 6, 4, 0, 16),
    ],
    "battle": [
        (196, 294, 9, 6, 2, 10), (220, 330, 9, 6, 0, 10), (247, 370, 9, 6, 2, 10), (262, 392, 9, 6, 0, 10),
        (220, 330, 8, 5, 2, 10), (247, 370, 9, 6, 0, 10), (294, 440, 9, 6, 2, 10), (262, 392, 9, 6, 0, 10),
        (330, 494, 9, 6, 2, 10), (294, 440, 9, 6, 0, 10),
    ],
    "victory": [
        (392, 523, 9, 6, 0, 12), (494, 659, 9, 6, 0, 12), (523, 784, 10, 6, 0, 12), (659, 988, 10, 6, 1, 24),
    ],
    "defeat": [
        (262, 330, 7, 4, 1, 14), (220, 294, 6, 4, 2, 14), (196, 262, 6, 4, 3, 18), (164, 220, 5, 3, 3, 24),
    ],
}

SFX_EVENTS = {
    "menu_move": [(660, 0, 9, 0, 0, 8)],
    "card_draw": [(540, 0, 10, 0, 0, 10), (720, 0, 8, 0, 0, 6)],
    "hit_land": [(340, 0, 11, 0, 2, 14)],
    "miss": [(240, 0, 7, 0, 1, 12)],
    "coupling": [(880, 660, 10, 6, 0, 18)],
    "evolve": [(740, 988, 10, 6, 0, 12), (988, 1318, 10, 6, 0, 18)],
    "reward": [(720, 960, 10, 6, 0, 16), (880, 1174, 10, 6, 0, 22)],
    "guard": [(420, 0, 8, 0, 0, 8), (320, 0, 7, 0, 1, 10)],
    "pulse": [(840, 640, 10, 6, 0, 10), (920, 720, 11, 6, 2, 12)],
    "status": [(280, 0, 8, 0, 3, 12)],
}


@dataclass
class CardRecord:
    id: int
    deck_id: int
    card_kind: int
    family: int
    stage: int
    habitat_mask: int
    role: int
    instinct: int
    ability: int
    technique: int
    degree: int
    angle: int
    cut: int
    range: int
    flow: int
    arc: int
    gauge: int
    hit_points: int
    patience_threshold: int
    speed: int
    power: int
    evolve_a: int
    evolve_b: int
    name: str
    flavor: str


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def c_string(text: str) -> str:
    return json.dumps(text)


def hex_color(color: tuple[int, int, int]) -> str:
    return "#%02X%02X%02X" % color


def card_index(deck_id: int, local_index: int) -> int:
    return deck_id * 52 + local_index


def deck_code(name: str) -> str:
    return name[:2].upper()


def habitat_slot_from_mask(mask: int) -> int:
    if mask <= 0:
        return 0
    return max(0, mask.bit_length() - 1)


def generate_cards() -> tuple[list[CardRecord], list[dict[str, object]]]:
    cards: list[CardRecord] = []
    deck_manifest: list[dict[str, object]] = []

    for deck_id, deck in enumerate(DECKS):
        deck_cards: list[CardRecord] = []
        local_index = 0

        for family in range(3):
            for variant in range(4):
                base_local = local_index
                evolve_a_local = 12 + family * 8 + variant * 2
                evolve_b_local = evolve_a_local + 1
                habitat_mask = 1 << ((variant + family + deck_id) % 4)
                role = (deck_id + family * 2 + variant) % len(ROLE_NAMES)
                instinct = (deck_id + family + variant) % len(INSTINCT_NAMES)
                ability = (deck_id + family + variant * 2) % len(ABILITY_NAMES)
                technique = (deck_id * 2 + family * 3 + variant) % len(TECHNIQUE_NAMES)
                deck_cards.append(
                    CardRecord(
                        id=card_index(deck_id, base_local),
                        deck_id=deck_id,
                        card_kind=0,
                        family=family,
                        stage=0,
                        habitat_mask=habitat_mask,
                        role=role,
                        instinct=instinct,
                        ability=ability,
                        technique=technique,
                        degree=4 + ((deck_id + variant + family) % 4),
                        angle=5 + ((deck_id + variant * 2 + family) % 4),
                        cut=4 + ((deck_id + family * 3 + variant) % 4),
                        range=4 + ((deck_id + variant + family) % 5),
                        flow=5 + ((deck_id + family + variant) % 4),
                        arc=4 + ((deck_id + family * 2 + variant) % 4),
                        gauge=4 + ((deck_id + variant * 3 + family) % 4),
                        hit_points=22 + family * 3 + variant * 2 + deck["pressure"],
                        patience_threshold=14 + family * 2 + variant + deck["pressure"],
                        speed=4 + ((family + variant + deck_id) % 5),
                        power=5 + ((family * 2 + variant + deck_id) % 5),
                        evolve_a=card_index(deck_id, evolve_a_local),
                        evolve_b=card_index(deck_id, evolve_b_local),
                        name=f"{deck['name']} {FAMILY_NAMES[family]} {VARIANT_SUFFIXES[variant]}",
                        flavor=f"A {ROLE_NAMES[role].lower()} {FAMILY_NAMES[family].lower()} breed from the {deck['theme']}.",
                    )
                )
                local_index += 1

        for family in range(3):
            for variant in range(4):
                for branch in range(2):
                    habitat_mask = 1 << ((variant + family + branch + deck_id) % 4)
                    base_value = 6 + family + branch
                    evo_name = EVOLUTION_SUFFIXES[variant][branch]
                    role = (deck_id + family * 3 + variant + branch) % len(ROLE_NAMES)
                    instinct = (deck_id + family + variant + branch * 2) % len(INSTINCT_NAMES)
                    ability = (deck_id + family * 2 + variant + branch) % len(ABILITY_NAMES)
                    technique = (deck_id + family + variant * 3 + branch) % len(TECHNIQUE_NAMES)
                    deck_cards.append(
                        CardRecord(
                            id=card_index(deck_id, local_index),
                            deck_id=deck_id,
                            card_kind=0,
                            family=family,
                            stage=1,
                            habitat_mask=habitat_mask,
                            role=role,
                            instinct=instinct,
                            ability=ability,
                            technique=technique,
                            degree=base_value + ((deck_id + variant) % 4),
                            angle=base_value + 1 + ((deck_id + family) % 3),
                            cut=base_value + ((deck_id + branch + variant) % 3),
                            range=base_value + ((deck_id + branch) % 4),
                            flow=base_value + ((variant + family + branch) % 3),
                            arc=base_value + ((deck_id + family * 2 + branch) % 3),
                            gauge=base_value + ((deck_id + variant * 2 + branch) % 3),
                            hit_points=30 + family * 4 + variant * 2 + branch * 2 + deck["pressure"],
                            patience_threshold=18 + family * 2 + variant + branch + deck["pressure"],
                            speed=6 + ((family + variant + branch + deck_id) % 5),
                            power=7 + ((family * 2 + variant + branch + deck_id) % 5),
                            evolve_a=-1,
                            evolve_b=-1,
                            name=f"{deck['name']} {FAMILY_NAMES[family]} {VARIANT_SUFFIXES[variant]} {evo_name}",
                            flavor=f"An advanced {ROLE_NAMES[role].lower()} line awakened by {HABITAT_NAMES[(variant + branch) % 4].lower()} coupling.",
                        )
                    )
                    local_index += 1

        for habitat_index in range(16):
            family = 3 if habitat_index < 8 else 4
            slot = habitat_index % 4
            habitat_mask = 1 << slot
            deck_cards.append(
                CardRecord(
                    id=card_index(deck_id, local_index),
                    deck_id=deck_id,
                    card_kind=1 if family == 3 else 2,
                    family=family,
                    stage=0,
                    habitat_mask=habitat_mask,
                    role=slot % len(ROLE_NAMES),
                    instinct=slot % len(INSTINCT_NAMES),
                    ability=(slot + (0 if family == 3 else 4)) % len(ABILITY_NAMES),
                    technique=slot % len(TECHNIQUE_NAMES),
                    degree=0,
                    angle=0,
                    cut=0,
                    range=0,
                    flow=0,
                    arc=0,
                    gauge=0,
                    hit_points=0,
                    patience_threshold=0,
                    speed=0,
                    power=0,
                    evolve_a=-1,
                    evolve_b=-1,
                    name=f"{deck['name']} {FAMILY_NAMES[family]} {HABITAT_NAMES[slot]} {1 + habitat_index // 4}",
                    flavor=(
                        f"{'Stabilizing' if family == 3 else 'Aggressive'} habitat field for the {deck['theme']}."
                    ),
                )
            )
            local_index += 1

        cards.extend(deck_cards)
        deck_manifest.append(
            {
                "id": deck_id,
                "name": deck["name"],
                "theme": deck["theme"],
                "accent": hex_color(deck["accent"]),
                "boss_title": deck["boss_title"],
                "relic_name": deck["relic_name"],
                "route": {"row": deck["route"][0], "col": deck["route"][1]},
                "pressure": deck["pressure"],
                "reward_cards": DECK_REWARD_CARDS,
            }
        )

    return cards, deck_manifest


def bg_gradient(draw: ImageDraw.ImageDraw, width: int, height: int, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> None:
    for y in range(height):
        ratio = y / max(1, height - 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3))
        draw.line((0, y, width, y), fill=color)


def draw_gaolite(draw: ImageDraw.ImageDraw, x: int, y: int, size: int, palette: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]], variant: int, stage: int) -> None:
    base, light, dark = palette
    draw.polygon([(x, y + size), (x + size // 2, y), (x + size, y + size)], fill=dark)
    draw.polygon([(x + size // 2, y + 4), (x + size - 6, y + size), (x + 6, y + size)], fill=base)
    draw.rectangle((x + size // 3, y + size // 3, x + size // 3 + 10 + stage * 3, y + size + 10), fill=light)
    spike = 4 + variant + stage * 2
    for index in range(spike):
        sx = x + 8 + index * (size - 16) // max(1, spike - 1)
        draw.polygon([(sx - 4, y + size // 2), (sx, y + size // 2 - 10 - stage * 2), (sx + 4, y + size // 2)], fill=light)


def draw_jeurgren(draw: ImageDraw.ImageDraw, x: int, y: int, size: int, palette: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]], variant: int, stage: int) -> None:
    base, light, dark = palette
    draw.ellipse((x + 8, y + 20, x + size - 8, y + size), fill=base)
    draw.pieslice((x, y + 4, x + size, y + size + 8), 210, 330, fill=dark)
    draw.ellipse((x + size // 2 - 10, y + 24, x + size // 2 + 10, y + 44), fill=light)
    wing = 18 + variant * 3 + stage * 4
    draw.polygon([(x + 16, y + size // 2), (x - wing, y + size // 2 - 10), (x + 8, y + size - 2)], fill=light)
    draw.polygon([(x + size - 16, y + size // 2), (x + size + wing, y + size // 2 - 12), (x + size - 8, y + size - 4)], fill=light)


def draw_fallows(draw: ImageDraw.ImageDraw, x: int, y: int, size: int, palette: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]], variant: int, stage: int) -> None:
    base, light, dark = palette
    draw.rectangle((x + 18, y + 18, x + size - 18, y + size - 10), fill=base)
    draw.ellipse((x + 26, y + 6, x + size - 26, y + 34), fill=light)
    stem_h = 16 + stage * 6
    for branch in range(4 + variant):
        bx = x + 10 + branch * (size - 20) // (3 + variant)
        draw.polygon([(bx, y + size - 10), (bx + 5, y + size + stem_h), (bx + 10, y + size - 10)], fill=dark)
    draw.rectangle((x + size // 2 - 6, y - 4 - stage * 6, x + size // 2 + 6, y + 20), fill=dark)


def draw_habitat(draw: ImageDraw.ImageDraw, x: int, y: int, size: int, palette: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]], family: int, habitat_slot: int) -> None:
    base, light, dark = palette
    if family == 3:
        draw.rectangle((x + 8, y + size // 2, x + size - 8, y + size - 8), fill=base)
        draw.polygon([(x + 12, y + size // 2), (x + size // 2, y + 10), (x + size - 12, y + size // 2)], fill=light)
        draw.rectangle((x + size // 2 - 8, y + size // 2 + 10, x + size // 2 + 8, y + size - 18), fill=dark)
    else:
        draw.ellipse((x + 12, y + 18, x + size - 12, y + size - 14), fill=base)
        draw.rectangle((x + 22, y + 12, x + size - 22, y + size - 24), fill=light)
        draw.rectangle((x + 18 + habitat_slot * 4, y + 24, x + 28 + habitat_slot * 4, y + size - 28), fill=dark)


def draw_card_art(card: CardRecord, output_path: Path) -> None:
    deck = DECKS[card.deck_id]
    accent = deck["accent"]
    palette = FAMILY_COLORS[card.family]
    image = Image.new("RGB", (CARD_W, CARD_H), (12, 12, 16))
    draw = ImageDraw.Draw(image)
    bg_gradient(draw, CARD_W, CARD_H, tuple(int(accent[i] * 0.45) for i in range(3)), (14, 16, 22))
    draw.rectangle((8, 8, CARD_W - 8, CARD_H - 8), fill=(22, 24, 32))
    draw.rectangle((12, 12, CARD_W - 12, 30), fill=accent)
    draw.rectangle((12, 32, CARD_W - 12, 110), fill=(30, 32, 42))
    draw.rectangle((12, 112, CARD_W - 12, CARD_H - 12), fill=(18, 20, 28))
    draw.rectangle((12, 112, CARD_W - 12, 126), fill=(40, 42, 54))

    art_x = 22
    art_y = 38
    art_size = 72
    if card.card_kind == 0:
        variant = card.id % 4
        if card.family == 0:
            draw_gaolite(draw, art_x, art_y, art_size, palette, variant, card.stage)
        elif card.family == 1:
            draw_jeurgren(draw, art_x, art_y, art_size, palette, variant, card.stage)
        else:
            draw_fallows(draw, art_x, art_y, art_size, palette, variant, card.stage)
    else:
        draw_habitat(draw, art_x, art_y, art_size, palette, card.family, habitat_slot_from_mask(card.habitat_mask))

    draw.text((16, 16), f"{deck_code(deck['name'])} {deck['boss_title'][:9]}", fill=(248, 244, 236))
    draw.text((CARD_W - 28, 16), f"T{deck['pressure']}", fill=(248, 244, 236))
    draw.text((16, 116), card.name[:17], fill=(242, 236, 228))
    if card.card_kind == 0:
        line_a = f"{ROLE_NAMES[card.role]} {INSTINCT_NAMES[card.instinct]}"
        line_b = ABILITY_NAMES[card.ability]
        line_c = f"{TECHNIQUE_NAMES[card.technique]} HP{card.hit_points}"
        line_d = f"PT{card.patience_threshold} SP{card.speed} PW{card.power}"
        draw.text((16, 130), line_a[:18], fill=palette[1])
        draw.text((16, 142), line_b[:18], fill=(226, 220, 210))
        draw.text((16, 154), line_c[:18], fill=(236, 214, 182))
        draw.text((16, 164), line_d[:18], fill=(214, 212, 204))
    else:
        slot = habitat_slot_from_mask(card.habitat_mask)
        line_a = f"{FAMILY_NAMES[card.family]} {HABITAT_NAMES[slot]}"
        line_b = "Stabilize" if card.family == 3 else "Amplify"
        line_c = deck["relic_name"]
        draw.text((16, 130), line_a[:18], fill=palette[1])
        draw.text((16, 142), line_b[:18], fill=(226, 220, 210))
        draw.text((16, 154), line_c[:18], fill=(236, 214, 182))

    ensure_dir(output_path.parent)
    image.save(output_path)


def build_card_sheets(cards: list[CardRecord]) -> None:
    for deck_id, deck in enumerate(DECKS):
        sheet = Image.new("RGB", (CARD_W * 13, CARD_H * 4), (10, 10, 14))
        for local_index in range(52):
            cx = (local_index % 13) * CARD_W
            cy = (local_index // 13) * CARD_H
            card = cards[card_index(deck_id, local_index)]
            card_path = CARD_ROOT / deck["name"].lower() / f"{local_index:02d}_{card.name.replace(' ', '_').lower()}.png"
            with Image.open(card_path) as image:
                sheet.paste(image, (cx, cy))
        sheet.save(CARD_ROOT / f"{deck['name'].lower()}_sheet.png")


def square_wave(freq: float, duration: float, volume: float) -> array:
    total = max(1, int(duration * SAMPLE_RATE))
    samples = array("f", [0.0]) * total
    phase = 0.0
    for index in range(total):
        phase += freq / SAMPLE_RATE
        if phase >= 1.0:
            phase -= 1.0
        samples[index] = volume if phase < 0.5 else -volume
    return samples


def noise_burst(duration: float, volume: float, pitch: int) -> array:
    total = max(1, int(duration * SAMPLE_RATE))
    samples = array("f", [0.0]) * total
    rng = Random(pitch * 97 + total)
    for index in range(total):
        env = math.exp(-(index / SAMPLE_RATE) * (18.0 - pitch))
        samples[index] = rng.uniform(-volume, volume) * env
    return samples


def write_stereo_wav(path: Path, left: array, right: array) -> None:
    frames = array("h")
    ensure_dir(path.parent)
    for index in range(len(left)):
        l = int(clamp(left[index], -1.0, 1.0) * 32767.0)
        r = int(clamp(right[index], -1.0, 1.0) * 32767.0)
        frames.append(l)
        frames.append(r)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(frames.tobytes())


def render_event_sequence(events: list[tuple[int, int, int, int, int, int]], out_path: Path) -> float:
    left = array("f")
    right = array("f")
    for hz_a, hz_b, vol_a, vol_b, noise_pitch, frames in events:
        duration = frames / 60.0
        a = square_wave(hz_a, duration, vol_a / 16.0) if hz_a else array("f", [0.0]) * max(1, int(duration * SAMPLE_RATE))
        b = square_wave(hz_b, duration, vol_b / 16.0) if hz_b else array("f", [0.0]) * len(a)
        n = noise_burst(duration, 0.10, noise_pitch) if noise_pitch else array("f", [0.0]) * len(a)
        for index in range(len(a)):
            left.append(a[index] * 0.75 + b[index] * 0.28 + n[index] * 0.24)
            right.append(a[index] * 0.28 + b[index] * 0.75 + n[index] * 0.24)
    write_stereo_wav(out_path, left, right)
    return len(left) / SAMPLE_RATE


def write_title_logo() -> None:
    image = Image.new("RGB", (320, 96), (12, 10, 14))
    draw = ImageDraw.Draw(image)
    bg_gradient(draw, 320, 96, (44, 16, 18), (10, 12, 18))
    for offset in range(10):
        x = 12 + offset * 28
        height = 20 + (offset % 3) * 6
        draw.polygon([(x, 28), (x + 12, 10), (x + 24, 28), (x + 12, 28 + height)], fill=(128 + offset * 8, 24, 28))
    for offset in range(12):
        x = 12 + offset * 24
        draw.ellipse((x, 8 + (offset % 2) * 4, x + 18, 24 + (offset % 2) * 4), fill=(180 + offset * 3, 26, 32))
    draw.rectangle((14, 56, 306, 58), fill=(210, 70, 54))
    draw.text((18, 24), "GORGE", fill=(244, 74, 58))
    draw.text((18, 44), "ELEMENTAL CARD SPECTRUMS", fill=(248, 232, 214))
    draw.text((18, 68), "TACTICAL MONSTER-CARD CIRCUITS", fill=(214, 184, 166))
    image.save(TITLE_LOGO_PATH)


def emit_header(cards: list[CardRecord], decks: list[dict[str, object]]) -> None:
    lines: list[str] = []
    lines.append("#ifndef GORGE_GENERATED_CONTENT_H\n")
    lines.append("#define GORGE_GENERATED_CONTENT_H\n\n")

    lines.append(f"static const GorgeDeckDef g_gorge_decks[GORGE_DECK_COUNT] = {{\n")
    for deck in decks:
        reward = ", ".join(str(value) for value in deck["reward_cards"])
        lines.append(
            "    {"
            f"{deck['id']}, {deck['route']['row']}, {deck['route']['col']}, {deck['pressure']}, "
            f"{c_string(deck['name'])}, {c_string(deck['theme'])}, {c_string(deck['boss_title'])}, {c_string(deck['relic_name'])}, "
            f"{{{reward}}}"
            "},\n"
        )
    lines.append("};\n\n")

    lines.append(f"static const GorgeCardDef g_gorge_cards[GORGE_TOTAL_CARDS] = {{\n")
    for card in cards:
        lines.append(
            "    {"
            f"{card.id}, {card.deck_id}, {card.card_kind}, {card.family}, {card.stage}, {card.habitat_mask}, "
            f"{card.role}, {card.instinct}, {card.ability}, {card.technique}, "
            f"{card.degree}, {card.angle}, {card.cut}, {card.range}, {card.flow}, {card.arc}, {card.gauge}, "
            f"{card.hit_points}, {card.patience_threshold}, {card.speed}, {card.power}, {card.evolve_a}, {card.evolve_b}, "
            f"{c_string(card.name)}, {c_string(card.flavor)}"
            "},\n"
        )
    lines.append("};\n\n")

    for song_name, events in SONG_EVENTS.items():
        lines.append(f"static const GorgeSongEvent g_gorge_song_{song_name}_events[] = {{\n")
        for event in events:
            lines.append(f"    {{{event[0]}, {event[1]}, {event[2]}, {event[3]}, {event[4]}, {event[5]}}},\n")
        lines.append("};\n\n")

    lines.append(f"static const GorgeSongDef g_gorge_songs[GORGE_SONG_COUNT] = {{\n")
    lines.append("    {\"title\", g_gorge_song_title_events, sizeof(g_gorge_song_title_events) / sizeof(g_gorge_song_title_events[0])},\n")
    lines.append("    {\"world\", g_gorge_song_world_events, sizeof(g_gorge_song_world_events) / sizeof(g_gorge_song_world_events[0])},\n")
    lines.append("    {\"battle\", g_gorge_song_battle_events, sizeof(g_gorge_song_battle_events) / sizeof(g_gorge_song_battle_events[0])},\n")
    lines.append("    {\"victory\", g_gorge_song_victory_events, sizeof(g_gorge_song_victory_events) / sizeof(g_gorge_song_victory_events[0])},\n")
    lines.append("    {\"defeat\", g_gorge_song_defeat_events, sizeof(g_gorge_song_defeat_events) / sizeof(g_gorge_song_defeat_events[0])},\n")
    lines.append("};\n\n")

    lines.append("#endif\n")
    ensure_dir(HEADER_PATH.parent)
    HEADER_PATH.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    cards, decks = generate_cards()

    ensure_dir(CARD_ROOT)
    ensure_dir(AUDIO_ROOT)

    for card in cards:
        deck_name = DECKS[card.deck_id]["name"].lower()
        filename = f"{card.id % 52:02d}_{card.name.replace(' ', '_').lower()}.png"
        draw_card_art(card, CARD_ROOT / deck_name / filename)

    build_card_sheets(cards)
    write_title_logo()

    audio_manifest = {"songs": [], "sfx": []}
    for song_name, events in SONG_EVENTS.items():
        duration = render_event_sequence(events, AUDIO_ROOT / f"{song_name}.wav")
        audio_manifest["songs"].append({"name": song_name, "duration_seconds": round(duration, 2)})
    for sfx_name, events in SFX_EVENTS.items():
        duration = render_event_sequence(events, AUDIO_ROOT / f"{sfx_name}.wav")
        audio_manifest["sfx"].append({"name": sfx_name, "duration_seconds": round(duration, 2)})

    emit_header(cards, decks)

    MANIFEST_PATH.write_text(
        json.dumps(
            {
                "project": "Gorge: Elemental Card Spectrums",
                "deck_count": len(DECKS),
                "cards_per_deck": 52,
                "total_cards": len(cards),
                "creature_cards_per_deck": 36,
                "habitat_cards_per_deck": 16,
                "roles": ROLE_NAMES,
                "instincts": INSTINCT_NAMES,
                "abilities": ABILITY_NAMES,
                "techniques": TECHNIQUE_NAMES,
                "title_logo": str(TITLE_LOGO_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "audio": audio_manifest,
                "decks": decks,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Generated {len(cards)} cards across {len(DECKS)} decks")
    print(f"Generated {len(SONG_EVENTS)} songs and {len(SFX_EVENTS)} sfx previews")
    print(f"Wrote runtime header: {HEADER_PATH}")
    print(f"Wrote manifest: {MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())