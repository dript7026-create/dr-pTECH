from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent.parent
SHEETS = ROOT / "assets" / "source_sheets"
LOOPS = ROOT / "assets" / "concept_loops"


def transparent_canvas(width: int, height: int) -> Image.Image:
    return Image.new("RGBA", (width, height), (0, 0, 0, 0))


def draw_bango_pose(draw: ImageDraw.ImageDraw, origin_x: int, origin_y: int, angle_index: int, sway: float) -> None:
    primary = (174, 130, 72, 255)
    accent = (230, 206, 128, 255)
    horn = (240, 238, 226, 255)
    shadow = (72, 42, 24, 190)
    dx = [-8, 8, -12, 12][angle_index]
    draw.ellipse((origin_x - 18 + dx, origin_y - 70, origin_x + 18 + dx, origin_y - 24), fill=primary)
    draw.rounded_rectangle((origin_x - 22, origin_y - 18, origin_x + 22, origin_y + 42), 10, fill=primary)
    draw.line((origin_x - 26, origin_y - 6, origin_x - 48, origin_y + 6 + sway), fill=accent, width=6)
    draw.line((origin_x + 26, origin_y - 6, origin_x + 48, origin_y + 6 - sway), fill=accent, width=6)
    draw.line((origin_x - 12, origin_y + 42, origin_x - 16, origin_y + 82 + sway), fill=shadow, width=8)
    draw.line((origin_x + 12, origin_y + 42, origin_x + 16, origin_y + 82 - sway), fill=shadow, width=8)
    draw.line((origin_x - 8 + dx, origin_y - 66, origin_x - 18 + dx, origin_y - 94), fill=horn, width=4)
    draw.line((origin_x + 8 + dx, origin_y - 66, origin_x + 18 + dx, origin_y - 94), fill=horn, width=4)
    draw.line((origin_x - 18, origin_y + 8, origin_x - 42, origin_y + 26), fill=(82, 160, 220, 220), width=3)
    draw.line((origin_x + 18, origin_y + 8, origin_x + 42, origin_y + 26), fill=(82, 160, 220, 220), width=3)


def draw_patoot_pose(draw: ImageDraw.ImageDraw, origin_x: int, origin_y: int, angle_index: int, sway: float) -> None:
    primary = (214, 108, 54, 255)
    accent = (236, 206, 124, 255)
    reptile = (92, 156, 96, 255)
    dx = [-10, 10, -16, 16][angle_index]
    draw.ellipse((origin_x - 12 + dx, origin_y - 64, origin_x + 18 + dx, origin_y - 28), fill=primary)
    draw.rounded_rectangle((origin_x - 18, origin_y - 12, origin_x + 18, origin_y + 34), 8, fill=primary)
    draw.line((origin_x - 14, origin_y + 6, origin_x - 38, origin_y - 6 - sway), fill=reptile, width=5)
    draw.line((origin_x + 14, origin_y + 6, origin_x + 38, origin_y - 6 + sway), fill=reptile, width=5)
    draw.line((origin_x - 10, origin_y + 34, origin_x - 14, origin_y + 82 + sway), fill=accent, width=6)
    draw.line((origin_x + 10, origin_y + 34, origin_x + 14, origin_y + 82 - sway), fill=accent, width=6)
    draw.line((origin_x + 20 + dx, origin_y - 52, origin_x + 42 + dx, origin_y - 48), fill=accent, width=5)
    draw.line((origin_x - 8, origin_y + 26, origin_x - 34, origin_y + 42), fill=(110, 208, 226, 220), width=4)


def write_sheet(name: str, pose_drawer) -> None:
    width, height = 512, 192
    image = transparent_canvas(width, height)
    draw = ImageDraw.Draw(image)
    for idx in range(4):
        pose_drawer(draw, 64 + idx * 128, 104, idx, 0.0)
        draw.text((40 + idx * 128, 156), ["front", "left", "right", "rear"][idx], fill=(255, 255, 255, 220))
    image.save(SHEETS / name)


def write_loop(name: str, pose_drawer, phase_scale: float) -> None:
    frames = []
    for idx in range(6):
        frame = transparent_canvas(192, 192)
        draw = ImageDraw.Draw(frame)
        sway = math.sin((idx / 6.0) * math.tau) * phase_scale
        pose_drawer(draw, 96, 104, idx % 4, sway)
        frames.append(frame)
    frames[0].save(
        LOOPS / name,
        save_all=True,
        append_images=frames[1:],
        duration=100,
        loop=0,
        disposal=2,
        transparency=0,
    )


def main() -> int:
    SHEETS.mkdir(parents=True, exist_ok=True)
    LOOPS.mkdir(parents=True, exist_ok=True)
    write_sheet("bango_tpose_4angle.png", draw_bango_pose)
    write_sheet("patoot_tpose_4angle.png", draw_patoot_pose)
    write_loop("bango_idle_keypose_loop.gif", draw_bango_pose, 8.0)
    write_loop("patoot_strut_keypose_loop.gif", draw_patoot_pose, 10.0)
    print("Generated placeholder PNG and GIF rig assets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())