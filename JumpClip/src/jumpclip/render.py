from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw

from .models import AnimationSpec, DesignProfile, RenderRequest


def infer_animation_spec(animation_name: str) -> AnimationSpec:
    name = animation_name.lower().strip()
    if "run" in name:
        return AnimationSpec(name=animation_name, frame_count=8, motion="run", silhouette_bias=1.15, squash_stretch=0.14, impact=0.35)
    if "attack" in name or "combo" in name:
        return AnimationSpec(name=animation_name, frame_count=8, motion="attack", silhouette_bias=1.2, squash_stretch=0.2, impact=0.72)
    if "jump" in name:
        return AnimationSpec(name=animation_name, frame_count=8, motion="jump", silhouette_bias=1.1, squash_stretch=0.18, impact=0.48)
    return AnimationSpec(name=animation_name, frame_count=6, motion="idle", silhouette_bias=1.0, squash_stretch=0.08, impact=0.18)


def load_profile(path: Path) -> DesignProfile:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return DesignProfile(**payload)


def _hex_to_rgba(color: str) -> tuple[int, int, int, int]:
    color = color.lstrip("#")
    return (int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16), 255)


def _influence_weights(prompt: str) -> dict[str, float]:
    text = prompt.lower()
    return {
        "gothic": 1.0 if "gothic" in text else 0.0,
        "anatomical": 1.0 if "anatom" in text or "davinci" in text or "leonardo" in text else 0.0,
        "surreal": 1.0 if "surreal" in text or "dali" in text else 0.0,
        "goya": 1.0 if "goya" in text else 0.0,
        "bosch": 1.0 if "bosch" in text else 0.0,
        "pixel": 1.0 if "pixel" in text else 0.0,
    }


def _grid_sample(profile: DesignProfile, x_ratio: float, y_ratio: float) -> float:
    grid_x = min(profile.grid_size - 1, max(0, int(x_ratio * profile.grid_size)))
    grid_y = min(profile.grid_size - 1, max(0, int(y_ratio * profile.grid_size)))
    return float(profile.grid_relativities[grid_y][grid_x])


def _pose_offsets(spec: AnimationSpec, frame_index: int) -> dict[str, float]:
    phase = (frame_index / max(1, spec.frame_count)) * math.tau
    if spec.motion == "run":
        return {
            "leg_a": math.sin(phase) * 10,
            "leg_b": math.sin(phase + math.pi) * 10,
            "arm_a": math.sin(phase + math.pi) * 8,
            "arm_b": math.sin(phase) * 8,
            "lift": abs(math.sin(phase)) * 3,
        }
    if spec.motion == "attack":
        windup = math.sin(phase) * 14
        return {
            "leg_a": math.sin(phase * 0.5) * 5,
            "leg_b": math.sin(phase * 0.5 + math.pi) * 5,
            "arm_a": windup,
            "arm_b": -windup * 0.35,
            "lift": max(0.0, math.sin(phase)) * 2,
        }
    if spec.motion == "jump":
        return {
            "leg_a": math.sin(phase + 0.3) * 6,
            "leg_b": math.sin(phase + math.pi + 0.3) * 6,
            "arm_a": math.sin(phase + 1.4) * 7,
            "arm_b": math.sin(phase + math.pi + 1.4) * 7,
            "lift": max(0.0, math.sin(phase)) * 8,
        }
    return {
        "leg_a": math.sin(phase) * 2,
        "leg_b": math.sin(phase + math.pi) * 2,
        "arm_a": math.sin(phase) * 2,
        "arm_b": math.sin(phase + math.pi) * 2,
        "lift": abs(math.sin(phase)) * 1,
    }


def _style_colors(profile: DesignProfile, influences: dict[str, float]) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int], tuple[int, int, int, int]]:
    base = _hex_to_rgba(profile.palette[0] if profile.palette else "#8e6f53")
    accent = _hex_to_rgba(profile.palette[1] if len(profile.palette) > 1 else "#d6c39b")
    shadow = _hex_to_rgba(profile.palette[2] if len(profile.palette) > 2 else "#332b2e")
    if influences["gothic"]:
        shadow = (max(0, shadow[0] - 24), max(0, shadow[1] - 20), max(0, shadow[2] - 14), 255)
    if influences["goya"]:
        shadow = (max(0, shadow[0] - 16), max(0, shadow[1] - 16), max(0, shadow[2] - 16), 255)
    if influences["surreal"]:
        accent = (min(255, accent[0] + 20), accent[1], min(255, accent[2] + 18), 255)
    return base, accent, shadow


def render_frame(request: RenderRequest, profile: DesignProfile, frame_index: int) -> Image.Image:
    size = request.canvas_size
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    influences = _influence_weights(request.prompt)
    base, accent, shadow = _style_colors(profile, influences)
    pose = _pose_offsets(request.animation, frame_index)

    center_x = size * 0.5
    floor_y = size * 0.84 - pose["lift"]
    height_ratio = profile.proportion_profile.get("height_ratio", 0.78)
    width_ratio = profile.proportion_profile.get("width_ratio", 0.3)
    surreal_scale = 1.0 + (0.16 * influences["surreal"])
    gothic_spike = 2 + int(4 * influences["gothic"])
    figure_h = size * min(0.88, max(0.56, height_ratio)) * surreal_scale
    torso_h = figure_h * 0.36
    head_h = figure_h * max(0.13, profile.proportion_profile.get("head_ratio", 0.16))
    leg_h = figure_h * 0.34
    shoulder_w = size * max(0.16, width_ratio) * request.animation.silhouette_bias
    hip_w = shoulder_w * 0.72
    line_thickness = 1 + int(3 * profile.line_weight_profile.get("medium", 0.25))
    if influences["bosch"]:
        line_thickness += 1

    head_top = floor_y - figure_h
    torso_top = head_top + head_h
    hip_y = torso_top + torso_h
    shadow_field = _grid_sample(profile, 0.5, 0.75)

    draw.ellipse(
        (center_x - head_h * 0.4, head_top, center_x + head_h * 0.4, head_top + head_h),
        fill=accent,
        outline=shadow,
        width=line_thickness,
    )

    if influences["gothic"]:
        draw.polygon(
            [
                (center_x, head_top - gothic_spike),
                (center_x - gothic_spike, head_top + gothic_spike),
                (center_x + gothic_spike, head_top + gothic_spike),
            ],
            fill=shadow,
        )

    draw.polygon(
        [
            (center_x - shoulder_w * 0.5, torso_top),
            (center_x + shoulder_w * 0.5, torso_top),
            (center_x + hip_w * 0.5, hip_y),
            (center_x - hip_w * 0.5, hip_y),
        ],
        fill=base,
        outline=shadow,
    )

    arm_y = torso_top + torso_h * 0.18
    leg_y = hip_y
    arm_len = torso_h * 0.95 * (1.0 + 0.1 * influences["surreal"])
    leg_len = leg_h * (1.0 + 0.08 * influences["anatomical"])
    left_arm_end = (center_x - shoulder_w * 0.75 + pose["arm_a"], arm_y + arm_len)
    right_arm_end = (center_x + shoulder_w * 0.75 + pose["arm_b"], arm_y + arm_len)
    left_leg_end = (center_x - hip_w * 0.35 + pose["leg_a"], leg_y + leg_len)
    right_leg_end = (center_x + hip_w * 0.35 + pose["leg_b"], leg_y + leg_len)

    draw.line([(center_x - shoulder_w * 0.42, arm_y), left_arm_end], fill=shadow, width=line_thickness)
    draw.line([(center_x + shoulder_w * 0.42, arm_y), right_arm_end], fill=shadow, width=line_thickness)
    draw.line([(center_x - hip_w * 0.2, leg_y), left_leg_end], fill=shadow, width=line_thickness)
    draw.line([(center_x + hip_w * 0.2, leg_y), right_leg_end], fill=shadow, width=line_thickness)

    if influences["anatomical"]:
        guide = (shadow[0], shadow[1], shadow[2], 160)
        draw.line([(center_x, head_top + head_h), (center_x, floor_y)], fill=guide, width=1)
        draw.line([(center_x - shoulder_w * 0.5, torso_top + torso_h * 0.18), (center_x + shoulder_w * 0.5, torso_top + torso_h * 0.18)], fill=guide, width=1)

    if influences["bosch"]:
        detail_count = 4 + int(8 * shadow_field)
        for detail_index in range(detail_count):
            x = int(center_x - shoulder_w * 0.45 + detail_index * max(2, shoulder_w / max(1, detail_count)))
            y = int(torso_top + 4 + (detail_index % 3) * 5)
            draw.rectangle((x, y, x + 1, y + 1), fill=shadow)

    if influences["goya"]:
        draw.rectangle(
            (center_x - shoulder_w * 0.6, torso_top + torso_h * 0.55, center_x + shoulder_w * 0.6, hip_y + 2),
            fill=(shadow[0], shadow[1], shadow[2], int(80 + shadow_field * 70)),
        )

    if request.animation.motion == "attack":
        sweep_color = (accent[0], accent[1], accent[2], 220)
        draw.arc(
            (center_x - shoulder_w, torso_top - 6, center_x + shoulder_w * 1.7, hip_y + leg_len * 0.2),
            start=-45,
            end=55 + int(50 * request.animation.impact),
            fill=sweep_color,
            width=max(1, line_thickness + 1),
        )

    if request.animation.motion in {"run", "jump"}:
        dust_alpha = 80 + int(120 * abs(math.sin((frame_index / max(1, request.animation.frame_count)) * math.pi)))
        draw.line(
            [(center_x - shoulder_w * 0.5, floor_y + 1), (center_x + shoulder_w * 0.5, floor_y + 1)],
            fill=(base[0], base[1], base[2], dust_alpha),
            width=1,
        )

    return image


def render_frames(request: RenderRequest, profile: DesignProfile) -> list[Image.Image]:
    return [render_frame(request, profile, index) for index in range(request.animation.frame_count)]


def save_sheet(frames: list[Image.Image], out_path: Path, upscale: int) -> Path:
    frame_w, frame_h = frames[0].size
    sheet = Image.new("RGBA", (frame_w * len(frames), frame_h), (0, 0, 0, 0))
    for index, frame in enumerate(frames):
        sheet.paste(frame, (index * frame_w, 0))
    if upscale > 1:
        sheet = sheet.resize((sheet.width * upscale, sheet.height * upscale), Image.Resampling.NEAREST)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)
    return out_path


def save_sequence(frames: list[Image.Image], out_dir: Path, upscale: int) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    for index, frame in enumerate(frames):
        export = frame
        if upscale > 1:
            export = frame.resize((frame.width * upscale, frame.height * upscale), Image.Resampling.NEAREST)
        export.save(out_dir / f"frame_{index:03d}.png")
    return out_dir


def save_gif(frames: list[Image.Image], out_path: Path, upscale: int, duration_ms: int = 90) -> Path:
    exports = []
    for frame in frames:
        export = frame
        if upscale > 1:
            export = frame.resize((frame.width * upscale, frame.height * upscale), Image.Resampling.NEAREST)
        exports.append(export)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    exports[0].save(out_path, save_all=True, append_images=exports[1:], duration=duration_ms, loop=0, disposal=2, transparency=0)
    return out_path
