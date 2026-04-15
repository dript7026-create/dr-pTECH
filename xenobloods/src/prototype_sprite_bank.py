from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SPRITE_BANK_DIR = ROOT / "assets" / "generated" / "sprite_bank"
METADATA_PATH = SPRITE_BANK_DIR / "sprite_bank.json"
FRAME_SIZE = 128


def ensure_sprite_bank(force: bool = False) -> dict:
    if force or not METADATA_PATH.exists():
        return build_sprite_bank(force=True)
    return json.loads(METADATA_PATH.read_text(encoding="utf-8"))


def build_sprite_bank(force: bool = False) -> dict:
    SPRITE_BANK_DIR.mkdir(parents=True, exist_ok=True)

    sprite_specs = {
        "ishtasha": {
            "label": "Ishtasha botanical spider",
            "animations": {
                "idle": 4,
                "run": 6,
                "stalk": 4,
                "crawl": 4,
                "jump": 4,
                "land": 4,
                "dash": 5,
                "light_attack": 5,
                "heavy_attack": 5,
                "block": 4,
                "dodge": 5,
                "parry": 5,
                "surge": 6,
                "hit": 4,
            },
            "renderer": _draw_ishtasha,
        },
        "scarab_child": {
            "label": "Scarab child plague acolyte",
            "animations": {
                "idle": 4,
                "transition": 4,
                "attack": 5,
                "block": 4,
                "dodge": 4,
                "feint": 4,
                "recoil": 5,
                "death": 6,
                "hit": 4,
            },
            "renderer": _draw_scarab_child,
        },
        "lattice_ward": {
            "label": "Lattice ward sentinel",
            "animations": {
                "idle": 4,
                "transition": 4,
                "attack": 4,
                "block": 4,
                "flare": 4,
                "recoil": 5,
                "death": 6,
                "hit": 4,
            },
            "renderer": _draw_lattice_ward,
        },
        "lahgroid": {
            "label": "Lahgroid hierophant",
            "animations": {
                "idle": 4,
                "transition": 4,
                "attack": 5,
                "block": 4,
                "dodge": 4,
                "feint": 4,
                "recoil": 5,
                "death": 6,
                "hit": 4,
            },
            "renderer": _draw_lahgroid,
        },
    }

    metadata = {"frame_size": FRAME_SIZE, "sprites": {}}
    for sprite_id, spec in sprite_specs.items():
        sprite_dir = SPRITE_BANK_DIR / sprite_id
        sprite_dir.mkdir(parents=True, exist_ok=True)
        animation_meta = {}
        for animation, frame_count in spec["animations"].items():
            frame_paths = []
            for frame_index in range(frame_count):
                file_name = f"{animation}_{frame_index:02d}.png"
                absolute_path = sprite_dir / file_name
                if force or not absolute_path.exists():
                    image = Image.new("RGBA", (FRAME_SIZE, FRAME_SIZE), (0, 0, 0, 0))
                    draw = ImageDraw.Draw(image, "RGBA")
                    spec["renderer"](draw, animation, frame_index, frame_count)
                    image.save(absolute_path)
                frame_paths.append(str(absolute_path.relative_to(ROOT)).replace("\\", "/"))
            animation_meta[animation] = frame_paths
        metadata["sprites"][sprite_id] = {
            "label": spec["label"],
            "animations": animation_meta,
        }

    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def _draw_ishtasha(draw: ImageDraw.ImageDraw, animation: str, frame_index: int, frame_count: int) -> None:
    phase = frame_index / max(1, frame_count)
    sway = math.sin(phase * math.tau)
    stride = _stride(animation, phase)
    lean = _lean(animation, phase)
    torso_x = 64 + lean * 6
    torso_y = 64 - abs(stride) * 3
    articulation = 1.0 + (0.55 if animation in {"light_attack", "heavy_attack", "dodge", "parry"} else 0.22)
    if animation == "stalk":
        torso_y += 8
        torso_x -= 4 * math.sin(phase * math.pi)
    elif animation == "crawl":
        torso_y += 16
        torso_x += stride * 10
        articulation += 0.35
    elif animation == "jump":
        torso_y -= 18 * math.sin(phase * math.pi)
        articulation += 0.22
    elif animation == "land":
        torso_y += 10 * math.sin(phase * math.pi)
    elif animation == "dash":
        torso_x += 14 * math.sin(phase * math.pi)
        articulation += 0.48
    elif animation == "surge":
        torso_x += 18 * math.sin(phase * math.pi)
        torso_y -= 6 * math.sin(phase * math.pi)
        articulation += 0.4

    _shadow(draw, torso_x, 104, 34, 8, (26, 10, 6, 70))
    _arachnid_legs(draw, torso_x, torso_y + 10, stride, (44, 14, 22, 255), (126, 186, 76, 220), hair=True, articulation=articulation)
    _undershade(draw, torso_x, torso_y + 12, 22, 14, (20, 6, 12, 150))
    _vine_veins(draw, torso_x, torso_y + 6, sway)
    _body_gradient(draw, torso_x, torso_y, 18, 26, (44, 96, 38, 255), (140, 32, 28, 255))
    _volume_rimlight(draw, torso_x + 4, torso_y - 1, 14, 22, (188, 232, 134, 110))
    _abdomen_gloss(draw, torso_x + 2, torso_y + 10, 16, 15, (244, 226, 178, 66))
    _leaf_cluster(draw, torso_x, torso_y - 2, sway)
    _pauldrons(draw, torso_x, torso_y - 6, (176, 156, 74, 255), (98, 68, 24, 255))
    _human_head(draw, torso_x + lean * 2, torso_y - 26, animation == "hit", feral=0.85 if animation in {"heavy_attack", "parry", "hit"} else 0.58)
    _hook_arm(draw, torso_x + 16, torso_y - 2, animation, phase)
    _off_arm(draw, torso_x - 12, torso_y, animation, phase)
    if animation == "jump":
        _speed_shards(draw, torso_x - 20, torso_y + 18, phase, (168, 196, 112, 86))
    if animation == "dash":
        _speed_shards(draw, torso_x - 38, torso_y - 2, phase, (236, 218, 132, 148))
        _speed_shards(draw, torso_x - 18, torso_y + 14, phase, (182, 224, 108, 110))
    if animation == "crawl":
        _ground_scratch(draw, torso_x, torso_y + 30, phase, (92, 128, 82, 120))
    if animation == "stalk":
        _creep_glow(draw, torso_x + 12, torso_y - 6, phase, (170, 220, 132, 80))
    if animation == "surge":
        _slash_arc(draw, torso_x + 34, torso_y - 4, "heavy_attack", phase, color=(244, 228, 168, 186))
        _speed_shards(draw, torso_x - 28, torso_y + 4, phase, (220, 204, 126, 132))
    if animation == "parry":
        _parry_flash(draw, torso_x + 30, torso_y - 4, phase, (226, 244, 160, 180))
    if animation == "dodge":
        _speed_shards(draw, torso_x - 28, torso_y - 8, phase, (224, 196, 92, 130))
    if animation in {"light_attack", "heavy_attack"}:
        _slash_arc(draw, torso_x + 30, torso_y - 2, animation, phase)


def _draw_scarab_child(draw: ImageDraw.ImageDraw, animation: str, frame_index: int, frame_count: int) -> None:
    phase = frame_index / max(1, frame_count)
    stride = _stride(animation, phase)
    lean = _lean(animation, phase)
    if animation == "transition":
        lean = -0.7 + math.sin(phase * math.pi) * 0.9
    elif animation == "recoil":
        lean = -1.8 * math.sin(phase * math.pi)
    elif animation == "death":
        lean = -1.6 - phase * 1.6
    center_x = 64 + lean * 5
    center_y = 68 - abs(stride) * 2 + (8 * phase if animation == "death" else 0)

    _shadow(draw, center_x, 103, 24, 7, (16, 16, 18, 65))
    _scarab_feet(draw, center_x, center_y + 22, stride, (68, 52, 30, 255))
    _hooded_body(draw, center_x, center_y, 18, 24, (42, 34, 28, 255), (120, 92, 54, 255))
    _scarab_shell(draw, center_x, center_y - 2, (94, 74, 34, 255), (162, 126, 58, 240))
    _plague_mask(draw, center_x + lean * 2, center_y - 18, (210, 198, 162, 255), eye_glow=(190, 224, 92, 230), tilt=phase * 0.75 if animation == "death" else (0.45 if animation == "recoil" else 0.0))
    _robe_arms(draw, center_x, center_y + 2, animation, phase, (98, 72, 40, 255))
    if animation == "attack":
        _slash_arc(draw, center_x - 10, center_y - 4, "light_attack", phase, mirrored=True, color=(186, 214, 106, 180))
    if animation == "dodge":
        _speed_shards(draw, center_x + 20, center_y - 10, phase, (160, 194, 100, 110))
    if animation == "feint":
        _creep_glow(draw, center_x - 4, center_y - 8, phase, (208, 232, 128, 70))
        _speed_shards(draw, center_x + 10, center_y - 2, phase, (198, 214, 106, 90))
    if animation == "transition":
        _impact_burst(draw, center_x, center_y - 2, phase, (188, 224, 116, 110))
    if animation == "recoil":
        _impact_burst(draw, center_x - 18, center_y - 8, phase, (240, 222, 144, 160))
    if animation == "death":
        _falling_motes(draw, center_x - 8, center_y + 2, phase, (186, 220, 112, 120))


def _draw_lattice_ward(draw: ImageDraw.ImageDraw, animation: str, frame_index: int, frame_count: int) -> None:
    phase = frame_index / max(1, frame_count)
    pulse = 0.5 + 0.5 * math.sin(phase * math.tau)
    if animation == "transition":
        pulse = 0.25 + 0.75 * phase
    center_x = 64 + (-12 * math.sin(phase * math.pi) if animation == "recoil" else 0)
    center_y = 60 + (10 * phase if animation == "death" else 0)

    _shadow(draw, center_x, 102, 28, 8, (10, 22, 24, 70))
    for ring in range(3):
        offset = ring * 10
        alpha = int(80 + pulse * 70 - ring * 18)
        wobble = 0
        if animation == "recoil":
            wobble = int((2 - ring) * math.sin(phase * math.pi) * 8)
        if animation == "death":
            wobble = int((ring + 1) * phase * 10)
        draw.rounded_rectangle(
            (center_x - 20 - offset - wobble, center_y - 14 - offset, center_x + 20 + offset + wobble, center_y + 14 + offset),
            radius=16,
            outline=(58, 170, 154, max(40, alpha)),
            width=3,
        )
    draw.polygon(
        [(center_x, center_y - 34), (center_x + 22, center_y), (center_x, center_y + 34), (center_x - 22, center_y)],
        fill=(44, 126, 118, 225),
        outline=(180, 224, 210, 250),
    )
    draw.ellipse((center_x - 6, center_y - 6, center_x + 6, center_y + 6), fill=(238, 244, 220, 250))
    if animation == "attack":
        _parry_flash(draw, center_x, center_y, phase, (166, 244, 222, 170))
    if animation == "block":
        _shield_hex(draw, center_x, center_y + 2, phase)
    if animation == "flare":
        _impact_burst(draw, center_x, center_y, phase, (178, 242, 230, 140))
        _creep_glow(draw, center_x, center_y - 8, phase, (164, 224, 214, 84))
    if animation == "recoil":
        _impact_burst(draw, center_x - 14, center_y - 2, phase, (190, 246, 228, 160))
    if animation == "death":
        _falling_motes(draw, center_x, center_y + 8, phase, (162, 238, 220, 130))


def _draw_lahgroid(draw: ImageDraw.ImageDraw, animation: str, frame_index: int, frame_count: int) -> None:
    phase = frame_index / max(1, frame_count)
    sway = math.sin(phase * math.tau)
    lean = _lean(animation, phase) * 0.8
    if animation == "transition":
        lean = math.sin(phase * math.pi) * 0.6
    elif animation == "recoil":
        lean = -1.5 * math.sin(phase * math.pi)
    elif animation == "death":
        lean = -1.4 - phase * 1.4
    center_x = 64 + lean * 7
    center_y = 62 + (10 * phase if animation == "death" else 0)

    _shadow(draw, center_x, 104, 30, 9, (20, 8, 20, 80))
    _hooded_body(draw, center_x, center_y + 10, 22, 28, (34, 18, 40, 255), (122, 48, 58, 255))
    _scarab_shell(draw, center_x, center_y + 8, (86, 24, 34, 255), (176, 78, 62, 230))
    _plague_mask(draw, center_x + sway * 2, center_y - 16, (224, 206, 184, 255), eye_glow=(238, 196, 78, 235), beak_length=20, tilt=phase if animation == "death" else (0.35 if animation == "recoil" else 0.0))
    _crown_vines(draw, center_x, center_y - 28, sway)
    _robe_arms(draw, center_x, center_y + 10, animation, phase, (130, 46, 48, 255), span=24)
    if animation == "attack":
        _slash_arc(draw, center_x + 24, center_y + 2, "heavy_attack", phase, color=(244, 142, 96, 170))
    if animation == "dodge":
        _speed_shards(draw, center_x - 20, center_y - 6, phase, (220, 114, 84, 120))
    if animation == "block":
        _shield_hex(draw, center_x, center_y + 8, phase, color=(214, 138, 116, 160))
    if animation == "feint":
        _creep_glow(draw, center_x + 6, center_y - 14, phase, (246, 170, 112, 86))
        _speed_shards(draw, center_x + 10, center_y - 2, phase, (228, 130, 92, 100))
    if animation == "transition":
        _impact_burst(draw, center_x, center_y - 18, phase, (228, 146, 104, 120))
    if animation == "recoil":
        _impact_burst(draw, center_x - 20, center_y - 8, phase, (246, 166, 118, 160))
    if animation == "death":
        _falling_motes(draw, center_x - 4, center_y + 4, phase, (246, 154, 106, 130))


def _stride(animation: str, phase: float) -> float:
    if animation in {"run", "dash", "surge", "dodge", "attack", "light_attack", "heavy_attack", "feint"}:
        return math.sin(phase * math.tau * 1.5)
    if animation in {"crawl", "jump", "land"}:
        return math.sin(phase * math.tau * 1.1) * 0.68
    return math.sin(phase * math.tau) * 0.25


def _lean(animation: str, phase: float) -> float:
    if animation == "stalk":
        return -0.4 + 0.2 * math.sin(phase * math.tau)
    if animation == "crawl":
        return -1.2 + 0.6 * math.sin(phase * math.tau)
    if animation == "jump":
        return 0.6 * math.sin(phase * math.pi)
    if animation == "land":
        return -0.5 * math.sin(phase * math.pi)
    if animation == "dash":
        return 2.2 * math.sin(phase * math.pi)
    if animation == "surge":
        return 1.6 * math.sin(phase * math.pi)
    if animation in {"light_attack", "attack"}:
        return 1.4 * math.sin(phase * math.pi)
    if animation == "heavy_attack":
        return 2.0 * math.sin(phase * math.pi)
    if animation == "block":
        return -0.6
    if animation == "parry":
        return 0.8 * math.sin(phase * math.pi)
    if animation == "dodge":
        return -1.8 * math.sin(phase * math.pi)
    if animation == "hit":
        return -0.9 * math.sin(phase * math.pi)
    return 0.2 * math.sin(phase * math.tau)


def _shadow(draw: ImageDraw.ImageDraw, center_x: float, center_y: float, radius_x: float, radius_y: float, color: tuple[int, int, int, int]) -> None:
    draw.ellipse((center_x - radius_x, center_y - radius_y, center_x + radius_x, center_y + radius_y), fill=color)


def _body_gradient(draw: ImageDraw.ImageDraw, center_x: float, center_y: float, radius_x: float, radius_y: float, top: tuple[int, int, int, int], bottom: tuple[int, int, int, int]) -> None:
    bands = 12
    for band in range(bands):
        mix = band / max(1, bands - 1)
        color = tuple(int(top[index] * (1.0 - mix) + bottom[index] * mix) for index in range(4))
        inset_y = band * 1.4
        draw.ellipse(
            (
                center_x - radius_x + band * 0.6,
                center_y - radius_y + inset_y,
                center_x + radius_x - band * 0.6,
                center_y + radius_y - inset_y * 0.45,
            ),
            fill=color,
        )


def _vine_veins(draw: ImageDraw.ImageDraw, center_x: float, center_y: float, sway: float) -> None:
    for offset in (-8, -3, 4, 9):
        points = []
        for step in range(5):
            x = center_x + offset + math.sin(step * 0.9 + sway) * 3
            y = center_y - 14 + step * 8
            points.append((x, y))
        draw.line(points, fill=(184, 42, 32, 220), width=2)


def _leaf_cluster(draw: ImageDraw.ImageDraw, center_x: float, center_y: float, sway: float) -> None:
    leaves = [(-14, -10), (-4, -16), (10, -12), (16, -2)]
    for index, (offset_x, offset_y) in enumerate(leaves):
        tilt = sway * (index + 1) * 1.4
        draw.polygon(
            [
                (center_x + offset_x, center_y + offset_y),
                (center_x + offset_x + 7 + tilt, center_y + offset_y - 4),
                (center_x + offset_x + 12, center_y + offset_y + 5),
                (center_x + offset_x + 2 - tilt, center_y + offset_y + 10),
            ],
            fill=(214, 188, 72, 230),
            outline=(122, 82, 18, 220),
        )


def _pauldrons(draw: ImageDraw.ImageDraw, center_x: float, center_y: float, outer: tuple[int, int, int, int], inner: tuple[int, int, int, int]) -> None:
    for offset in (-16, 16):
        draw.pieslice((center_x + offset - 10, center_y - 4, center_x + offset + 10, center_y + 12), start=180, end=360, fill=outer, outline=inner)
        draw.pieslice((center_x + offset - 7, center_y - 1, center_x + offset + 7, center_y + 10), start=180, end=360, fill=inner)


def _human_head(draw: ImageDraw.ImageDraw, center_x: float, center_y: float, struck: bool, feral: float = 0.6) -> None:
    skin = (210, 178, 142, 255) if not struck else (188, 148, 130, 255)
    shadow = (118, 74, 68, 188)
    draw.ellipse((center_x - 10, center_y - 12, center_x + 10, center_y + 10), fill=skin, outline=(72, 36, 28, 255))
    draw.pieslice((center_x - 10, center_y - 12, center_x + 10, center_y + 10), start=110, end=250, fill=shadow)
    draw.polygon([(center_x - 13, center_y - 11), (center_x + 13, center_y - 11), (center_x + 10, center_y + 7), (center_x - 8, center_y + 7)], fill=(32, 48, 26, 214))
    cheek_sink = int(feral * 4)
    draw.polygon([(center_x - 7, center_y + 2), (center_x - 1, center_y + 5 + cheek_sink), (center_x - 6, center_y + 7)], fill=(98, 50, 44, 180))
    draw.polygon([(center_x + 7, center_y + 2), (center_x + 1, center_y + 5 + cheek_sink), (center_x + 6, center_y + 7)], fill=(98, 50, 44, 180))
    draw.line([(center_x, center_y - 1), (center_x - 1, center_y + 4)], fill=(92, 48, 38, 200), width=1)
    draw.arc((center_x - 7, center_y + 1, center_x + 7, center_y + 9), start=8, end=172, fill=(92, 22, 24, 255), width=2)
    draw.line([(center_x - 4, center_y + 6), (center_x - 2, center_y + 7), (center_x, center_y + 6), (center_x + 2, center_y + 7), (center_x + 4, center_y + 6)], fill=(236, 222, 196, 220), width=1)
    draw.ellipse((center_x - 6, center_y - 2, center_x - 2, center_y + 1), fill=(12, 12, 12, 255))
    draw.ellipse((center_x + 2, center_y - 2, center_x + 6, center_y + 1), fill=(12, 12, 12, 255))
    draw.line([(center_x - 7, center_y - 5), (center_x - 2, center_y - 7)], fill=(84, 46, 38, 220), width=1)
    draw.line([(center_x + 2, center_y - 7), (center_x + 7, center_y - 5)], fill=(84, 46, 38, 220), width=1)


def _hook_arm(draw: ImageDraw.ImageDraw, center_x: float, center_y: float, animation: str, phase: float) -> None:
    reach = 10
    if animation in {"light_attack", "heavy_attack"}:
        reach += 18 * math.sin(phase * math.pi)
    elif animation == "block":
        reach -= 4
    elbow = (center_x + 8, center_y + 2)
    wrist = (center_x + reach, center_y - 4 - phase * 6)
    draw.line([(center_x - 4, center_y - 2), elbow, wrist], fill=(78, 42, 32, 255), width=4)
    draw.arc((wrist[0] - 14, wrist[1] - 10, wrist[0] + 10, wrist[1] + 14), start=300, end=120, fill=(216, 214, 170, 255), width=4)


def _off_arm(draw: ImageDraw.ImageDraw, center_x: float, center_y: float, animation: str, phase: float) -> None:
    guard_y = center_y - 2
    if animation == "block":
        guard_y -= 12
    elif animation == "parry":
        guard_y -= 16 * math.sin(phase * math.pi)
    draw.line([(center_x - 4, center_y - 2), (center_x - 12, center_y + 8), (center_x - 18, guard_y)], fill=(72, 40, 30, 255), width=4)


def _arachnid_legs(
    draw: ImageDraw.ImageDraw,
    center_x: float,
    center_y: float,
    stride: float,
    leg_color: tuple[int, int, int, int],
    highlight: tuple[int, int, int, int],
    hair: bool = False,
    articulation: float = 1.0,
) -> None:
    spreads = [(-30, -16), (-34, -4), (-34, 8), (-28, 20), (30, -16), (34, -4), (34, 8), (28, 20)]
    for index, (offset_x, offset_y) in enumerate(spreads):
        direction = -1 if index < 4 else 1
        kick = stride * (index % 2 * 2 - 1) * (4 + articulation * 2)
        hip = (center_x + direction * 12, center_y + offset_y * 0.15)
        knee = (center_x + offset_x * 0.34, center_y + offset_y * 0.34 - kick)
        shin = (center_x + offset_x * 0.72, center_y + offset_y * 0.68 + kick * 0.2)
        foot = (center_x + offset_x, center_y + offset_y + 18 + kick)
        draw.line([hip, knee, shin, foot], fill=leg_color, width=3)
        draw.line([hip, knee, shin, foot], fill=highlight, width=1)
        draw.ellipse((knee[0] - 2, knee[1] - 2, knee[0] + 2, knee[1] + 2), fill=(62, 18, 24, 220))
        draw.ellipse((shin[0] - 2, shin[1] - 2, shin[0] + 2, shin[1] + 2), fill=(62, 18, 24, 220))
        if hair:
            for branch in (0.28, 0.62):
                px = shin[0] * (1.0 - branch) + foot[0] * branch
                py = shin[1] * (1.0 - branch) + foot[1] * branch
                draw.line([(px, py), (px + direction * 4, py - 3)], fill=(188, 214, 98, 160), width=1)


def _undershade(draw: ImageDraw.ImageDraw, center_x: float, center_y: float, radius_x: float, radius_y: float, color: tuple[int, int, int, int]) -> None:
    draw.ellipse((center_x - radius_x, center_y - radius_y, center_x + radius_x, center_y + radius_y), fill=color)


def _volume_rimlight(draw: ImageDraw.ImageDraw, center_x: float, center_y: float, radius_x: float, radius_y: float, color: tuple[int, int, int, int]) -> None:
    draw.arc((center_x - radius_x, center_y - radius_y, center_x + radius_x, center_y + radius_y), start=250, end=60, fill=color, width=3)


def _abdomen_gloss(draw: ImageDraw.ImageDraw, center_x: float, center_y: float, radius_x: float, radius_y: float, color: tuple[int, int, int, int]) -> None:
    draw.arc((center_x - radius_x, center_y - radius_y, center_x + radius_x, center_y + radius_y), start=215, end=305, fill=color, width=4)


def _impact_burst(draw: ImageDraw.ImageDraw, center_x: float, center_y: float, phase: float, color: tuple[int, int, int, int]) -> None:
    radius = 10 + phase * 14
    for angle in range(0, 360, 45):
        radians = math.radians(angle)
        inner = (center_x + math.cos(radians) * (radius * 0.4), center_y + math.sin(radians) * (radius * 0.4))
        outer = (center_x + math.cos(radians) * radius, center_y + math.sin(radians) * radius)
        draw.line([inner, outer], fill=color, width=2)


def _falling_motes(draw: ImageDraw.ImageDraw, center_x: float, center_y: float, phase: float, color: tuple[int, int, int, int]) -> None:
    for index in range(5):
        drift = (index - 2) * 7
        y = center_y + phase * (10 + index * 4)
        draw.ellipse((center_x + drift - 2, y - 2, center_x + drift + 2, y + 2), fill=color)


def _ground_scratch(draw: ImageDraw.ImageDraw, center_x: float, center_y: float, phase: float, color: tuple[int, int, int, int]) -> None:
    for index in range(3):
        offset = index * 10 + phase * 6
        draw.line([(center_x - 20 - offset, center_y + 4), (center_x - 6 - offset, center_y - 2)], fill=color, width=2)


def _creep_glow(draw: ImageDraw.ImageDraw, center_x: float, center_y: float, phase: float, color: tuple[int, int, int, int]) -> None:
    radius = 8 + math.sin(phase * math.tau) * 4
    draw.ellipse((center_x - radius, center_y - radius, center_x + radius, center_y + radius), outline=color, width=2)


def _parry_flash(draw: ImageDraw.ImageDraw, center_x: float, center_y: float, phase: float, color: tuple[int, int, int, int]) -> None:
    radius = 8 + math.sin(phase * math.pi) * 18
    draw.ellipse((center_x - radius, center_y - radius, center_x + radius, center_y + radius), outline=color, width=3)
    draw.line([(center_x - radius, center_y), (center_x + radius, center_y)], fill=color, width=2)
    draw.line([(center_x, center_y - radius), (center_x, center_y + radius)], fill=color, width=2)


def _speed_shards(draw: ImageDraw.ImageDraw, center_x: float, center_y: float, phase: float, color: tuple[int, int, int, int]) -> None:
    for index in range(4):
        offset = index * 8 + phase * 10
        draw.polygon(
            [(center_x - offset, center_y - 6), (center_x - offset - 12, center_y), (center_x - offset, center_y + 6)],
            fill=color,
        )


def _slash_arc(
    draw: ImageDraw.ImageDraw,
    center_x: float,
    center_y: float,
    animation: str,
    phase: float,
    mirrored: bool = False,
    color: tuple[int, int, int, int] = (244, 212, 152, 170),
) -> None:
    radius = 18 + phase * (26 if animation == "heavy_attack" else 18)
    start, end = (220, 340) if not mirrored else (20, 140)
    draw.arc((center_x - radius, center_y - radius, center_x + radius, center_y + radius), start=start, end=end, fill=color, width=4)


def _hooded_body(
    draw: ImageDraw.ImageDraw,
    center_x: float,
    center_y: float,
    radius_x: float,
    radius_y: float,
    top: tuple[int, int, int, int],
    bottom: tuple[int, int, int, int],
) -> None:
    for band in range(10):
        mix = band / 9
        color = tuple(int(top[index] * (1.0 - mix) + bottom[index] * mix) for index in range(4))
        draw.polygon(
            [
                (center_x - radius_x + band * 0.6, center_y - radius_y + band),
                (center_x + radius_x - band * 0.6, center_y - radius_y + band),
                (center_x + radius_x + 10 - band, center_y + radius_y),
                (center_x - radius_x - 10 + band, center_y + radius_y),
            ],
            fill=color,
        )


def _scarab_shell(draw: ImageDraw.ImageDraw, center_x: float, center_y: float, base: tuple[int, int, int, int], shine: tuple[int, int, int, int]) -> None:
    draw.ellipse((center_x - 16, center_y - 10, center_x + 16, center_y + 14), fill=base, outline=(30, 20, 18, 255))
    draw.arc((center_x - 10, center_y - 8, center_x + 12, center_y + 10), start=210, end=340, fill=shine, width=3)
    draw.line([(center_x, center_y - 8), (center_x, center_y + 12)], fill=(24, 18, 18, 220), width=2)


def _plague_mask(
    draw: ImageDraw.ImageDraw,
    center_x: float,
    center_y: float,
    color: tuple[int, int, int, int],
    eye_glow: tuple[int, int, int, int],
    beak_length: int = 14,
    tilt: float = 0.0,
) -> None:
    drift_x = tilt * 6
    drift_y = tilt * 4
    draw.ellipse((center_x - 10 + drift_x, center_y - 10 + drift_y, center_x + 10 + drift_x, center_y + 10 + drift_y), fill=color, outline=(76, 56, 40, 255))
    draw.polygon([(center_x + 2 + drift_x, center_y - 2 + drift_y), (center_x + beak_length + drift_x, center_y + 2 + drift_y), (center_x + 2 + drift_x, center_y + 6 + drift_y)], fill=(164, 144, 120, 255), outline=(88, 64, 42, 255))
    draw.ellipse((center_x - 5 + drift_x, center_y - 3 + drift_y, center_x - 1 + drift_x, center_y + 1 + drift_y), fill=eye_glow)
    draw.ellipse((center_x + 1 + drift_x, center_y - 3 + drift_y, center_x + 5 + drift_x, center_y + 1 + drift_y), fill=eye_glow)


def _robe_arms(
    draw: ImageDraw.ImageDraw,
    center_x: float,
    center_y: float,
    animation: str,
    phase: float,
    color: tuple[int, int, int, int],
    span: int = 18,
) -> None:
    lift = 0
    if animation in {"attack", "light_attack", "heavy_attack"}:
        lift = int(16 * math.sin(phase * math.pi))
    elif animation == "block":
        lift = 10
    left = [(center_x - 6, center_y - 2), (center_x - span, center_y + 8 - lift), (center_x - span - 6, center_y + 24 - lift)]
    right = [(center_x + 6, center_y - 2), (center_x + span, center_y + 8 - lift), (center_x + span + 6, center_y + 24 - lift)]
    draw.line(left, fill=color, width=6)
    draw.line(right, fill=color, width=6)


def _scarab_feet(draw: ImageDraw.ImageDraw, center_x: float, center_y: float, stride: float, color: tuple[int, int, int, int]) -> None:
    for offset in (-14, -6, 6, 14):
        draw.line([(center_x + offset, center_y), (center_x + offset * 1.3, center_y + 12 + stride * 2)], fill=color, width=3)


def _crown_vines(draw: ImageDraw.ImageDraw, center_x: float, center_y: float, sway: float) -> None:
    for offset in (-16, -6, 6, 16):
        draw.line(
            [
                (center_x + offset, center_y),
                (center_x + offset + sway * 2, center_y - 10),
                (center_x + offset + sway * 4, center_y - 18),
            ],
            fill=(198, 124, 72, 210),
            width=3,
        )
        draw.polygon(
            [
                (center_x + offset + sway * 4, center_y - 22),
                (center_x + offset + 5 + sway * 4, center_y - 16),
                (center_x + offset + sway * 4, center_y - 10),
                (center_x + offset - 5 + sway * 4, center_y - 16),
            ],
            fill=(214, 168, 90, 210),
        )


def _shield_hex(draw: ImageDraw.ImageDraw, center_x: float, center_y: float, phase: float, color: tuple[int, int, int, int] = (174, 228, 214, 150)) -> None:
    radius = 18 + math.sin(phase * math.pi) * 4
    points = []
    for index in range(6):
        angle = math.pi / 6 + index * math.pi / 3
        points.append((center_x + math.cos(angle) * radius, center_y + math.sin(angle) * radius))
    draw.polygon(points, outline=color, width=3)
