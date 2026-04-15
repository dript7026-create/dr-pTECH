from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets" / "generated"


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "backgrounds": _build_plane_backgrounds(),
        "navigation": _build_navigation_assets(),
        "battle_stages": _build_battle_stages(),
        "portraits": _build_lifecycle_portraits(),
        "actors": _build_actor_cards(),
        "ui": _build_ui_assets(),
        "controller": _build_controller_assets(),
        "prototype_pack": _build_prototype_pack_manifest(),
        "asset_index": _build_asset_index(),
    }
    manifest_path = ASSET_DIR / "prototype_gameplay_asset_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Generated gameplay prototype assets in {ASSET_DIR}")


def _build_plane_backgrounds() -> list[str]:
    return [
        make_background("bg_land.png", (1280, 720), (60, 10, 18), (18, 7, 9), (210, 42, 50), (255, 180, 130), "LAND", "Blood is life, currency, and thought.", "veins"),
        make_background("bg_up.png", (1280, 720), (26, 52, 92), (7, 14, 36), (236, 216, 130), (196, 245, 255), "UP", "The tetrarch domain beneath Gramatos.", "glyphs"),
        make_background("bg_low.png", (1280, 720), (26, 34, 38), (8, 10, 14), (80, 118, 150), (164, 188, 214), "LOW", "Sorrow, confusion, and drowned memory.", "silt"),
        make_background("bg_ether.png", (1280, 720), (10, 18, 44), (5, 7, 16), (95, 140, 255), (220, 255, 255), "ETHER", "Pure energy threading the shrines.", "currents"),
    ]


def _build_navigation_assets() -> list[str]:
    return [
        make_land_zone_map("nav_land_zone_map.png", (1280, 720)),
        make_plane_room_card("nav_up_tetrarch_hall.png", (1280, 720), "UP INCURSION", (26, 52, 92), (236, 216, 130), ["tetrach discourse", "judgment lane", "instant smite risk"]),
        make_plane_room_card("nav_low_curgz_channel.png", (1280, 720), "LOW CHANNEL", (24, 32, 36), (120, 170, 210), ["curgz triad", "beam routing", "gravity collapse"]),
    ]


def _build_battle_stages() -> list[str]:
    return [
        make_battle_stage("battle_stage_land.png", (1280, 720), "LAND DUEL STAGE", (48, 12, 18), (230, 98, 92), (255, 216, 180)),
        make_battle_stage("battle_stage_up.png", (1280, 720), "UP VERDICT STAGE", (24, 46, 88), (242, 218, 140), (208, 246, 255)),
        make_battle_stage("battle_stage_low.png", (1280, 720), "LOW CURGZ STAGE", (20, 28, 34), (110, 152, 214), (182, 214, 238)),
        make_depth_overlay("battle_depth_overlay.png", (1280, 720)),
        make_timing_ring("combat_timing_ring.png", (512, 512)),
        make_telegraph_strip("combat_telegraph_glyphs.png", (960, 180)),
        make_battle_storyboard("battle_exchange_storyboard.png", (1280, 720), "STANDARD ENCOUNTER EXCHANGE"),
        make_battle_storyboard("boss_realtime_flow.png", (1280, 720), "BOSS REALTIME FLOW"),
    ]


def _build_lifecycle_portraits() -> list[str]:
    return [
        make_portrait("portrait_landborne.png", (640, 640), "landborne"),
        make_portrait("portrait_gourd_infant.png", (640, 640), "gourd_infant"),
        make_portrait("portrait_etheric.png", (640, 640), "etheric"),
        make_state_card("life_state_landborne.png", (720, 420), "LANDBORNE", (82, 18, 32), ["blood-backed life force", "navigation and combat", "eye-lock encounter start"]),
        make_state_card("life_state_gourd_infant.png", (720, 420), "GOURD INFANT", (166, 122, 60), ["rebirth pressure loop", "rupture and hatch", "fragile but spiritually dense"]),
        make_state_card("life_state_etheric.png", (720, 420), "ETHERIC CURRENT", (88, 146, 255), ["pure energy routing", "shrine traversal", "plane-selection state"]),
    ]


def _build_actor_cards() -> list[str]:
    outputs = []
    actor_specs = [
        ("npc_tetrarch_opal.png", "OPAL TETRARCH", (60, 78, 124), (236, 216, 130), "tetrarch"),
        ("npc_tetrarch_auditor.png", "AUDITOR SAL", (42, 64, 110), (224, 244, 255), "tetrarch"),
        ("npc_tetrarch_verdict.png", "VERDICT CHORISTER", (30, 86, 124), (202, 242, 255), "tetrarch"),
        ("enemy_scarab_child.png", "SCARAB CHILD", (52, 18, 20), (198, 212, 238), "scarab"),
        ("enemy_lattice_ward.png", "LATTICE WARD", (40, 40, 52), (214, 226, 255), "lattice"),
        ("boss_lahgroid_card.png", "LAHGROID HIEROPHANT", (28, 24, 34), (208, 218, 242), "lahgroid"),
        ("curgz_alpha.png", "CURGZ ALPHA", (18, 30, 42), (132, 196, 255), "curgz"),
        ("curgz_beta.png", "CURGZ BETA", (22, 36, 48), (154, 206, 255), "curgz"),
        ("curgz_gamma.png", "CURGZ GAMMA", (16, 28, 36), (174, 220, 255), "curgz"),
    ]
    for filename, title, top, accent, kind in actor_specs:
        outputs.append(make_actor_card(filename, (640, 640), title, top, accent, kind))
    outputs.append(make_dialogue_danger_strip("up_dialogue_danger_strip.png", (960, 180)))
    outputs.append(make_curgz_puzzle_sheet("low_curgz_puzzle_sheet.png", (960, 320)))
    return outputs


def _build_ui_assets() -> list[str]:
    return [
        make_logo("logo_xenobloods.png", (900, 260)),
        make_panel("hud_panel.png", (480, 280)),
        make_button_strip("button_strip.png", (960, 180)),
        make_mode_panel("hud_navigation.png", (520, 300), "NAVIGATION", ["metroidvania traversal", "eye-lock encounter flow", "life-state movement gate"]),
        make_mode_panel("hud_dialogue.png", (520, 300), "UP DIALOGUE", ["spoken gambits", "noncombat danger", "smite-on-failure tension"]),
        make_mode_panel("hud_battle.png", (520, 300), "BATTLE SCENE", ["shrinking read window", "foreground-mid-background staging", "precision dodge block parry attack"]),
        make_mode_panel("hud_low_puzzle.png", (520, 300), "LOW CURGZ", ["redirect currents", "refractor and resistor routing", "gravity-collapse puzzle combat"]),
    ]


def _build_controller_assets() -> list[str]:
    return [
        make_controller_layout("xbox_series_controller_layout.png", (1280, 720)),
        make_controller_prompt_strip("xbox_button_prompts.png", (960, 180)),
    ]


def _build_prototype_pack_manifest() -> dict:
    return {
        "prototype_scope": {
            "life_states": ["gourd_infant", "landborne", "etheric_current"],
            "planes": ["up", "land", "low", "ether"],
            "land_enemy_types": ["scarab_child_acolyte", "lattice_ward"],
            "boss": "lahgroid_hierophant",
            "up_npcs": ["opal_tetrarch", "auditor_sal", "verdict_chorister"],
            "low_curgz": ["curgz_alpha", "curgz_beta", "curgz_gamma"],
        },
        "encounter_flow": [
            "Land navigation uses sparse enemy placement and eye-lock triggers to start contact races.",
            "Collision can award preemptive damage on a precisely timed attack confirm.",
            "Standard battles transition into cinematic turn exchanges with shrinking nontext read windows.",
            "Boss battles stay real-time and use the full controller across foreground, midground, and background staging.",
            "Up relies on dialogue-pressure assets and smite-risk UI rather than physical combat.",
            "Low relies on curgz energy-routing puzzle-combat in navigation space.",
        ],
        "xbox_series_controller": {
            "left_stick": "navigation movement, collision race steering, dialogue topic drift, low current aim",
            "right_stick": "depth lane bias, camera nudge, battle scene framing",
            "a": "commit attack, confirm dialogue card, resolve rupture/hatch",
            "b": "dodge, cancel, recoil reset",
            "x": "block, energy redirect, gourd interact",
            "y": "parry, interject, high-risk dialogue gambit",
            "lb": "shift toward foreground lane, target cycle left",
            "rb": "shift toward background lane, target cycle right",
            "lt": "eye-lock, aim, conversation focus hold",
            "rt": "ranged release, blood burn burst, directed energy feed",
            "dpad_up": "view life-state panel",
            "dpad_left": "dialogue card or utility selection",
            "dpad_right": "dialogue card or ranged selection",
            "dpad_down": "gourd or shrine quick action",
            "view": "prototype zone schematic and encounter read",
            "menu": "pause and state summary",
        },
    }


def _build_asset_index() -> dict[str, dict[str, str]]:
    return {
        "logo.main": {"section": "ui", "file": "logo_xenobloods.png"},
        "scene.land.navigation": {"section": "navigation", "file": "nav_land_zone_map.png"},
        "scene.up.dialogue": {"section": "navigation", "file": "nav_up_tetrarch_hall.png"},
        "scene.low.puzzle": {"section": "navigation", "file": "nav_low_curgz_channel.png"},
        "scene.land.battle": {"section": "battle_stages", "file": "battle_stage_land.png"},
        "scene.up.battle": {"section": "battle_stages", "file": "battle_stage_up.png"},
        "scene.low.battle": {"section": "battle_stages", "file": "battle_stage_low.png"},
        "battle.timing_ring": {"section": "battle_stages", "file": "combat_timing_ring.png"},
        "battle.storyboard": {"section": "battle_stages", "file": "battle_exchange_storyboard.png"},
        "battle.boss_flow": {"section": "battle_stages", "file": "boss_realtime_flow.png"},
        "portrait.landborne": {"section": "portraits", "file": "portrait_landborne.png"},
        "portrait.gourd_infant": {"section": "portraits", "file": "portrait_gourd_infant.png"},
        "portrait.etheric_current": {"section": "portraits", "file": "portrait_etheric.png"},
        "state.landborne": {"section": "portraits", "file": "life_state_landborne.png"},
        "state.gourd_infant": {"section": "portraits", "file": "life_state_gourd_infant.png"},
        "state.etheric_current": {"section": "portraits", "file": "life_state_etheric.png"},
        "actor.opal_tetrarch": {"section": "actors", "file": "npc_tetrarch_opal.png"},
        "actor.auditor_sal": {"section": "actors", "file": "npc_tetrarch_auditor.png"},
        "actor.verdict_chorister": {"section": "actors", "file": "npc_tetrarch_verdict.png"},
        "actor.scarab_child_acolyte": {"section": "actors", "file": "enemy_scarab_child.png"},
        "actor.lattice_ward": {"section": "actors", "file": "enemy_lattice_ward.png"},
        "actor.lahgroid_hierophant": {"section": "actors", "file": "boss_lahgroid_card.png"},
        "actor.curgz_alpha": {"section": "actors", "file": "curgz_alpha.png"},
        "actor.curgz_beta": {"section": "actors", "file": "curgz_beta.png"},
        "actor.curgz_gamma": {"section": "actors", "file": "curgz_gamma.png"},
        "support.up.dialogue": {"section": "actors", "file": "up_dialogue_danger_strip.png"},
        "support.low.puzzle": {"section": "actors", "file": "low_curgz_puzzle_sheet.png"},
        "panel.navigation": {"section": "ui", "file": "hud_navigation.png"},
        "panel.dialogue": {"section": "ui", "file": "hud_dialogue.png"},
        "panel.battle": {"section": "ui", "file": "hud_battle.png"},
        "panel.low": {"section": "ui", "file": "hud_low_puzzle.png"},
        "controller.layout": {"section": "controller", "file": "xbox_series_controller_layout.png"},
        "controller.prompts": {"section": "controller", "file": "xbox_button_prompts.png"},
    }


def make_background(filename: str, size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int], accent: tuple[int, int, int], detail: tuple[int, int, int], title: str, subtitle: str, motif: str) -> str:
    width, height = size
    image = Image.new("RGBA", size, (0, 0, 0, 255))
    draw = ImageDraw.Draw(image)
    for y in range(height):
        draw.line((0, y, width, y), fill=lerp_rgb(top, bottom, y / max(1, height - 1)))

    if motif == "veins":
        for index in range(22):
            x = 40 + index * 58
            draw.line((x, height, x + 80, height * 0.35), fill=(*accent, 80), width=5)
            draw.line((x + 80, height * 0.35, x + 120, 120), fill=(*detail, 60), width=2)
    elif motif == "glyphs":
        for index in range(12):
            x = 70 + index * 95
            draw.rounded_rectangle((x, 80, x + 48, 420), radius=12, outline=(*detail, 120), width=3)
            draw.line((x + 24, 80, x + 24, 420), fill=(*accent, 130), width=2)
    elif motif == "silt":
        for index in range(80):
            x = (index * 73) % width
            y = 110 + (index * 47) % (height - 180)
            draw.ellipse((x, y, x + 18, y + 12), fill=(*detail, 38))
    elif motif == "currents":
        for index in range(18):
            x = 40 + index * 68
            draw.arc((x, 120, x + 280, 520), start=215, end=340, fill=(*detail, 110), width=4)
            draw.arc((x + 20, 150, x + 260, 500), start=215, end=340, fill=(*accent, 100), width=2)

    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((width * 0.54, 90, width * 0.9, height * 0.68), fill=(*accent, 110))
    image = Image.alpha_composite(image, glow.filter(ImageFilter.GaussianBlur(radius=54)))

    draw = ImageDraw.Draw(image)
    draw.text((80, 64), title, font=_font(88), fill=(245, 243, 240, 255))
    draw.text((84, 154), subtitle, font=_font(28), fill=(220, 224, 235, 235))
    draw.rounded_rectangle((70, 560, 1210, 650), radius=28, fill=(8, 10, 14, 140), outline=(*detail, 100), width=2)
    draw.text((98, 586), "Prototype visual shell background", font=_font(24), fill=(245, 245, 250, 225))
    return _save(image, filename)


def make_land_zone_map(filename: str, size: tuple[int, int]) -> str:
    width, height = size
    image = Image.new("RGBA", size, (18, 8, 10, 255))
    draw = ImageDraw.Draw(image)
    for y in range(height):
        draw.line((0, y, width, y), fill=lerp_rgb((46, 12, 14), (15, 8, 10), y / max(1, height - 1)))
    sectors = [
        ((90, 120, 360, 260), "gourdwake"),
        ((410, 130, 700, 290), "veinmarket"),
        ((760, 150, 1080, 320), "crossing"),
        ((220, 360, 520, 560), "forge"),
        ((640, 390, 1120, 610), "boss_gate"),
    ]
    for rect, label in sectors:
        draw.rounded_rectangle(rect, radius=24, fill=(44, 18, 22, 220), outline=(240, 124, 110, 120), width=3)
        draw.text((rect[0] + 18, rect[1] + 18), label.upper(), font=_font(28), fill=(246, 236, 228, 255))
    for start, end in [((360, 190), (410, 200)), ((700, 210), (760, 230)), ((480, 290), (440, 360)), ((700, 280), (760, 390))]:
        draw.line((start, end), fill=(255, 192, 160, 180), width=8)
        draw.ellipse((end[0] - 8, end[1] - 8, end[0] + 8, end[1] + 8), fill=(255, 232, 192, 220))
    for point in [(280, 200), (540, 205), (840, 245), (390, 470), (910, 470)]:
        draw.ellipse((point[0] - 18, point[1] - 18, point[0] + 18, point[1] + 18), fill=(22, 12, 16, 255), outline=(255, 214, 188, 220), width=3)
        draw.ellipse((point[0] - 8, point[1] - 8, point[0] + 8, point[1] + 8), fill=(255, 124, 110, 255))
    draw.text((80, 44), "VEINMARKET PROTOTYPE ZONE", font=_font(56), fill=(248, 242, 238, 255))
    draw.text((82, 108), "Sparse enemy placement and eye-lock encounters route the player through one full Land district.", font=_font(26), fill=(232, 220, 214, 240))
    return _save(image, filename)


def make_plane_room_card(filename: str, size: tuple[int, int], title: str, top: tuple[int, int, int], accent: tuple[int, int, int], bullets: list[str]) -> str:
    image = Image.new("RGBA", size, (*top, 255))
    draw = ImageDraw.Draw(image)
    for y in range(size[1]):
        draw.line((0, y, size[0], y), fill=lerp_rgb(top, (8, 10, 16), y / max(1, size[1] - 1)))
    draw.rounded_rectangle((72, 72, size[0] - 72, size[1] - 72), radius=42, fill=(10, 14, 20, 180), outline=(*accent, 140), width=3)
    draw.text((112, 108), title, font=_font(58), fill=(246, 246, 244, 255))
    y = 204
    for bullet in bullets:
        draw.ellipse((116, y + 12, 132, y + 28), fill=(*accent, 255))
        draw.text((154, y), bullet.upper(), font=_font(30), fill=(236, 240, 244, 240))
        y += 84
    return _save(image, filename)


def make_battle_stage(filename: str, size: tuple[int, int], title: str, back: tuple[int, int, int], accent: tuple[int, int, int], detail: tuple[int, int, int]) -> str:
    image = Image.new("RGBA", size, (*back, 255))
    draw = ImageDraw.Draw(image)
    for y in range(size[1]):
        draw.line((0, y, size[0], y), fill=lerp_rgb(back, (6, 8, 12), y / max(1, size[1] - 1)))
    draw.polygon([(0, 560), (360, 420), (780, 720), (0, 720)], fill=(12, 14, 18, 255))
    draw.polygon([(420, 0), (1280, 0), (1280, 210), (910, 250)], fill=(*accent, 90))
    draw.polygon([(930, 0), (1280, 0), (1280, 720), (1000, 720), (880, 420)], fill=(18, 20, 26, 220))
    draw.rectangle((0, 510, 1280, 720), fill=(10, 12, 18, 200))
    for x in [210, 470, 760, 1040]:
        draw.line((x, 180, x, 622), fill=(*detail, 120), width=3)
    draw.text((72, 52), title, font=_font(54), fill=(245, 242, 236, 255))
    draw.text((76, 118), "Foreground, midground, and background lanes are explicit for cinematic turn staging.", font=_font(24), fill=(228, 232, 236, 220))
    draw.text((88, 624), "FOREGROUND", font=_font(22), fill=(255, 220, 188, 220))
    draw.text((518, 514), "MIDGROUND", font=_font(22), fill=(255, 220, 188, 220))
    draw.text((930, 262), "BACKGROUND", font=_font(22), fill=(255, 220, 188, 220))
    return _save(image, filename)


def make_depth_overlay(filename: str, size: tuple[int, int]) -> str:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 520, size[0], size[1]), fill=(16, 18, 20, 160))
    draw.rectangle((0, 300, size[0], 520), fill=(16, 22, 30, 90))
    draw.rectangle((0, 0, size[0], 300), fill=(30, 38, 48, 46))
    draw.line((0, 520, size[0], 520), fill=(255, 210, 170, 180), width=3)
    draw.line((0, 300, size[0], 300), fill=(220, 236, 255, 120), width=2)
    return _save(image, filename)


def make_timing_ring(filename: str, size: tuple[int, int]) -> str:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    cx = size[0] // 2
    cy = size[1] // 2
    draw.ellipse((44, 44, size[0] - 44, size[1] - 44), outline=(244, 244, 244, 90), width=14)
    draw.arc((44, 44, size[0] - 44, size[1] - 44), start=-90, end=24, fill=(255, 112, 98, 220), width=22)
    draw.arc((76, 76, size[0] - 76, size[1] - 76), start=16, end=72, fill=(112, 196, 255, 220), width=18)
    draw.arc((108, 108, size[0] - 108, size[1] - 108), start=88, end=124, fill=(252, 228, 132, 220), width=18)
    draw.ellipse((cx - 18, cy - 18, cx + 18, cy + 18), fill=(245, 245, 246, 220))
    return _save(image, filename)


def make_telegraph_strip(filename: str, size: tuple[int, int]) -> str:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    glyphs = [((255, 112, 98), "slash"), ((96, 184, 255), "wave"), ((252, 220, 116), "guard"), ((208, 152, 255), "burst")]
    x = 26
    for color, kind in glyphs:
        draw.rounded_rectangle((x, 24, x + 206, 156), radius=28, fill=(18, 20, 26, 235), outline=(*color, 140), width=3)
        if kind == "slash":
            draw.polygon([(x + 40, 122), (x + 86, 54), (x + 122, 86), (x + 92, 138)], fill=(*color, 255))
        elif kind == "wave":
            draw.arc((x + 34, 44, x + 164, 132), start=200, end=340, fill=(*color, 255), width=8)
            draw.arc((x + 64, 62, x + 188, 142), start=200, end=340, fill=(*color, 220), width=8)
        elif kind == "guard":
            draw.polygon([(x + 104, 44), (x + 154, 78), (x + 134, 138), (x + 74, 138), (x + 54, 78)], fill=(*color, 255))
        else:
            draw.ellipse((x + 70, 48, x + 138, 116), outline=(*color, 255), width=8)
            draw.line((x + 138, 82, x + 176, 82), fill=(*color, 255), width=6)
            draw.line((x + 104, 116, x + 104, 148), fill=(*color, 255), width=6)
            draw.line((x + 34, 82, x + 70, 82), fill=(*color, 255), width=6)
            draw.line((x + 104, 18, x + 104, 48), fill=(*color, 255), width=6)
        x += 232
    return _save(image, filename)


def make_portrait(filename: str, size: tuple[int, int], form: str) -> str:
    width, height = size
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((12, 12, width - 12, height - 12), radius=32, fill=(10, 14, 18, 255), outline=(190, 200, 220, 80), width=3)

    if form == "landborne":
        draw.ellipse((170, 90, 470, 410), fill=(92, 18, 32, 255))
        draw.rounded_rectangle((210, 240, 430, 560), radius=96, fill=(120, 28, 36, 255))
        draw.rectangle((218, 284, 422, 420), fill=(34, 16, 22, 210))
        draw.ellipse((250, 180, 292, 220), fill=(255, 236, 226, 255))
        draw.ellipse((348, 180, 390, 220), fill=(255, 236, 226, 255))
        draw.line((320, 204, 340, 228), fill=(240, 120, 110, 255), width=6)
        draw.arc((260, 236, 380, 300), start=18, end=164, fill=(244, 198, 198, 255), width=6)
        draw.text((58, 538), "LANDBORNE VESSEL", font=_font(28), fill=(244, 238, 235, 255))
    elif form == "gourd_infant":
        draw.ellipse((112, 90, 530, 560), outline=(242, 226, 165, 255), width=8, fill=(104, 60, 24, 110))
        draw.ellipse((170, 148, 470, 508), fill=(196, 150, 78, 140))
        draw.ellipse((224, 206, 418, 416), fill=(238, 214, 196, 245))
        draw.ellipse((276, 244, 320, 286), fill=(44, 20, 16, 210))
        draw.ellipse((344, 244, 388, 286), fill=(44, 20, 16, 210))
        draw.arc((274, 312, 388, 380), start=20, end=160, fill=(120, 40, 36, 230), width=4)
        for crack in range(6):
            offset = crack * 34
            draw.line((300 + offset // 6, 116 + offset, 320 + offset // 7, 138 + offset), fill=(255, 240, 196, 210), width=2)
        draw.text((58, 538), "GOURD INFANT", font=_font(28), fill=(245, 237, 215, 255))
    else:
        for ring in range(10):
            inset = 58 + ring * 18
            draw.ellipse((inset, inset, width - inset, height - inset), outline=(120, 190, 255, max(20, 160 - ring * 14)), width=3)
        draw.arc((160, 120, 480, 510), start=210, end=18, fill=(220, 248, 255, 255), width=10)
        draw.arc((120, 160, 520, 540), start=35, end=178, fill=(114, 170, 255, 255), width=8)
        draw.ellipse((272, 252, 368, 348), fill=(230, 252, 255, 225))
        draw.text((58, 538), "ETHERIC CURRENT", font=_font(28), fill=(224, 242, 255, 255))

    return _save(image, filename)


def make_state_card(filename: str, size: tuple[int, int], title: str, accent: tuple[int, int, int], bullets: list[str]) -> str:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    for y in range(size[1]):
        draw.line((0, y, size[0], y), fill=lerp_rgb((10, 12, 18), (18, 24, 36), y / max(1, size[1] - 1)))
    draw.ellipse((30, 38, 210, 218), outline=(*accent, 140), width=5)
    draw.ellipse((58, 66, 182, 190), outline=(*accent, 80), width=3)
    draw.text((252, 40), title, font=_font(44), fill=(246, 246, 244, 255))
    draw.line((250, 98, size[0] - 46, 98), fill=(*accent, 160), width=3)
    y = 126
    for bullet in bullets:
        draw.line((258, y + 22, 282, y + 22), fill=(*accent, 255), width=4)
        draw.text((300, y), bullet.upper(), font=_font(24), fill=(232, 236, 244, 240))
        y += 78
    return _save(image, filename)


def make_actor_card(filename: str, size: tuple[int, int], title: str, top: tuple[int, int, int], accent: tuple[int, int, int], kind: str) -> str:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    for y in range(size[1]):
        draw.line((0, y, size[0], y), fill=lerp_rgb(top, (8, 10, 14), y / max(1, size[1] - 1)))
    if kind == "tetrarch":
        draw.arc((168, 94, 472, 378), start=198, end=342, fill=(255, 248, 220, 180), width=8)
        draw.polygon([(320, 92), (420, 176), (382, 336), (258, 336), (220, 176)], fill=(*accent, 220), outline=(12, 14, 18))
        draw.line((320, 176, 320, 430), fill=(255, 248, 220, 230), width=8)
        draw.line((118, 498, 522, 498), fill=(*accent, 110), width=2)
    elif kind == "scarab":
        draw.polygon([(186, 156), (320, 96), (454, 156), (428, 414), (212, 414)], fill=(16, 18, 22, 255), outline=(*accent, 160))
        draw.polygon([(320, 180), (388, 210), (328, 252)], fill=(*accent, 255))
        draw.line((132, 492, 516, 492), fill=(*accent, 100), width=2)
    elif kind == "lattice":
        draw.rectangle((214, 140, 426, 468), fill=(24, 28, 36, 255), outline=(*accent, 180), width=3)
        draw.line((320, 140, 320, 468), fill=(*accent, 255), width=8)
        draw.line((214, 304, 426, 304), fill=(*accent, 255), width=8)
        draw.line((126, 500, 514, 500), fill=(*accent, 100), width=2)
    elif kind == "lahgroid":
        draw.polygon([(148, 206), (254, 122), (450, 138), (532, 204), (420, 278), (320, 258), (252, 330)], fill=(20, 22, 28, 255), outline=(*accent, 180))
        draw.line((320, 258, 392, 442), fill=(*accent, 255), width=5)
        draw.ellipse((376, 430, 430, 484), fill=(*accent, 180), outline=(16, 18, 24))
        draw.line((122, 500, 518, 500), fill=(*accent, 100), width=2)
    else:
        draw.ellipse((176, 164, 470, 446), outline=(*accent, 180), width=8, fill=(10, 14, 18, 150))
        draw.line((470, 306, 554, 306), fill=(*accent, 220), width=6)
        draw.line((410, 186, 456, 118), fill=(*accent, 220), width=6)
        draw.line((246, 204, 176, 152), fill=(*accent, 220), width=6)
        draw.line((246, 408, 176, 462), fill=(*accent, 220), width=6)
        draw.line((412, 424, 458, 492), fill=(*accent, 220), width=6)
        draw.line((124, 498, 516, 498), fill=(*accent, 100), width=2)
    draw.text((42, 542), title, font=_font(30), fill=(245, 244, 240, 255))
    return _save(image, filename)


def make_dialogue_danger_strip(filename: str, size: tuple[int, int]) -> str:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    for index, alpha in enumerate([70, 110, 150, 210]):
        x0 = 32 + index * 226
        draw.rounded_rectangle((x0, 44, x0 + 180, 136), radius=22, fill=(12, 16, 24, 235), outline=(236, 216, 130, 120), width=2)
        draw.rectangle((x0 + 24, 78, x0 + 156, 100), fill=(236, 216, 130, alpha))
    return _save(image, filename)


def make_curgz_puzzle_sheet(filename: str, size: tuple[int, int]) -> str:
    image = Image.new("RGBA", size, (10, 14, 18, 240))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((10, 10, size[0] - 10, size[1] - 10), radius=32, outline=(154, 206, 255, 120), width=3)
    nodes = [(120, 160), (280, 96), (440, 190), (620, 104), (790, 154)]
    for x, y in nodes:
        draw.ellipse((x - 28, y - 28, x + 28, y + 28), outline=(154, 206, 255, 220), width=4, fill=(16, 18, 24, 255))
    for start, end in zip(nodes, nodes[1:]):
        draw.line((start, end), fill=(132, 196, 255, 190), width=8)
    draw.polygon([(260, 86), (304, 96), (260, 106)], fill=(244, 236, 188, 255))
    draw.rectangle((594, 78, 646, 130), outline=(244, 236, 188, 255), width=4)
    draw.text((48, 34), "CURGZ ENERGY ROUTING", font=_font(32), fill=(244, 246, 250, 255))
    return _save(image, filename)


def make_logo(filename: str, size: tuple[int, int]) -> str:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 8, size[0] - 8, size[1] - 8), radius=44, fill=(12, 10, 18, 220), outline=(255, 120, 140, 120), width=3)
    draw.text((54, 42), "XENOBLOODS", font=_font(108), fill=(248, 242, 236, 255))
    draw.text((62, 154), "A prototype blood-and-soul shell", font=_font(32), fill=(220, 225, 236, 225))
    return _save(image, filename)


def make_panel(filename: str, size: tuple[int, int]) -> str:
    image = Image.new("RGBA", size, (8, 10, 14, 214))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((2, 2, size[0] - 2, size[1] - 2), radius=24, outline=(216, 226, 245, 90), width=2)
    draw.text((22, 18), "PLAYER STATE", font=_font(30), fill=(245, 246, 250, 255))
    for index in range(4):
        y = 78 + index * 42
        draw.rounded_rectangle((18, y, size[0] - 18, y + 28), radius=14, fill=(24, 28, 34, 255))
    return _save(image, filename)


def make_button_strip(filename: str, size: tuple[int, int]) -> str:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    labels = ["Spill Blood", "Die", "Enter Ether", "Descend", "Struggle", "Hatch", "Encounter"]
    x = 14
    for label in labels:
        width = 122 if len(label) < 9 else 154
        draw.rounded_rectangle((x, 40, x + width, 122), radius=24, fill=(108, 24, 38, 235), outline=(255, 192, 188, 110), width=2)
        draw.text((x + 18, 66), label, font=_font(24), fill=(247, 243, 238, 255))
        x += width + 16
    return _save(image, filename)


def make_mode_panel(filename: str, size: tuple[int, int], title: str, lines: list[str]) -> str:
    image = Image.new("RGBA", size, (8, 10, 14, 214))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((2, 2, size[0] - 2, size[1] - 2), radius=24, outline=(216, 226, 245, 90), width=2)
    draw.text((24, 20), title, font=_font(30), fill=(245, 246, 250, 255))
    y = 88
    for line in lines:
        draw.rounded_rectangle((18, y, size[0] - 18, y + 48), radius=14, fill=(22, 26, 34, 255))
        draw.text((32, y + 10), line.upper(), font=_font(22), fill=(232, 238, 246, 225))
        y += 62
    return _save(image, filename)


def make_controller_layout(filename: str, size: tuple[int, int]) -> str:
    image = Image.new("RGBA", size, (10, 12, 16, 255))
    draw = ImageDraw.Draw(image)
    draw.text((56, 44), "XBOX SERIES CONTROLLER PROFILE", font=_font(50), fill=(246, 246, 242, 255))
    body = [(420, 164), (344, 230), (284, 396), (346, 582), (472, 620), (808, 620), (936, 582), (1000, 396), (936, 230), (860, 164)]
    draw.polygon(body, fill=(28, 32, 40, 255), outline=(214, 224, 244, 120))
    draw.ellipse((460, 250, 590, 380), fill=(20, 24, 30, 255), outline=(214, 224, 244, 80))
    draw.ellipse((700, 250, 830, 380), fill=(20, 24, 30, 255), outline=(214, 224, 244, 80))
    draw.ellipse((756, 194, 808, 246), fill=(72, 146, 255, 255))
    draw.ellipse((812, 140, 864, 192), fill=(248, 88, 92, 255))
    draw.ellipse((868, 194, 920, 246), fill=(244, 210, 96, 255))
    draw.ellipse((812, 248, 864, 300), fill=(102, 210, 126, 255))
    draw.rectangle((362, 224, 422, 244), fill=(214, 224, 244, 180))
    draw.rectangle((382, 204, 402, 264), fill=(214, 224, 244, 180))
    draw.rounded_rectangle((594, 202, 646, 228), radius=12, fill=(214, 224, 244, 160))
    draw.rounded_rectangle((662, 202, 714, 228), radius=12, fill=(214, 224, 244, 160))
    callouts = [
        ((170, 170), "LT: eye-lock, aim, focus hold"),
        ((170, 232), "LB: foreground shift or left cycle"),
        ((170, 294), "LEFT STICK: navigate, race, steer currents"),
        ((170, 356), "DPAD: state, dialogue, gourd, utility"),
        ((170, 418), "VIEW: zone schematic"),
        ((860, 170), "RT: ranged release and blood burst"),
        ((860, 232), "RB: background shift or right cycle"),
        ((860, 294), "Y: parry or dialogue gambit"),
        ((860, 356), "X: block or redirect energy"),
        ((860, 418), "B: dodge or cancel"),
        ((860, 480), "A: attack or confirm"),
    ]
    for (x, y), label in callouts:
        draw.text((x, y), label.upper(), font=_font(19), fill=(236, 240, 246, 228))
    draw.text((430, 664), "Battle scenes use full-pad depth shifts and timing reads; bosses stay fully real-time.", font=_font(22), fill=(214, 224, 242, 220))
    return _save(image, filename)


def make_battle_storyboard(filename: str, size: tuple[int, int], title: str) -> str:
    image = Image.new("RGBA", size, (10, 12, 18, 255))
    draw = ImageDraw.Draw(image)
    draw.text((54, 44), title, font=_font(48), fill=(246, 244, 240, 255))
    panel_w = 268
    x = 50
    panels = [
        ("READY", (244, 210, 110)),
        ("DASH", (96, 184, 255)),
        ("CLASH", (255, 112, 98)),
        ("PUNISH", (130, 220, 154)),
    ]
    for label, color in panels:
        draw.rounded_rectangle((x, 140, x + panel_w, 600), radius=28, fill=(18, 20, 28, 255), outline=(*color, 150), width=3)
        draw.text((x + 28, 166), label, font=_font(30), fill=(246, 244, 240, 255))
        draw.line((x + 46, 510, x + 190, 260), fill=(*color, 220), width=10)
        draw.ellipse((x + 170, 240, x + 228, 298), fill=(*color, 255))
        draw.ellipse((x + 70, 468, x + 118, 516), outline=(236, 240, 244, 220), width=4)
        draw.rectangle((x + 48, 548, x + 220, 560), fill=(236, 240, 244, 120))
        x += panel_w + 24
    return _save(image, filename)


def make_controller_prompt_strip(filename: str, size: tuple[int, int]) -> str:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    prompts = [((102, 210, 126), "A"), ((248, 88, 92), "B"), ((72, 146, 255), "X"), ((244, 210, 96), "Y")]
    x = 36
    for color, label in prompts:
        draw.rounded_rectangle((x, 44, x + 180, 136), radius=30, fill=(16, 18, 24, 235), outline=(*color, 140), width=3)
        draw.ellipse((x + 26, 62, x + 82, 118), fill=(*color, 255))
        draw.text((x + 45, 70), label, font=_font(24), fill=(14, 18, 24, 255))
        draw.text((x + 98, 72), "READY", font=_font(22), fill=(240, 244, 248, 230))
        x += 218
    return _save(image, filename)


def lerp_rgb(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int, int]:
    return (int(a[0] + (b[0] - a[0]) * t), int(a[1] + (b[1] - a[1]) * t), int(a[2] + (b[2] - a[2]) * t), 255)


def _font(size: int):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _save(image: Image.Image, filename: str) -> str:
    path = ASSET_DIR / filename
    image.save(path)
    return str(path)


if __name__ == "__main__":
    main()