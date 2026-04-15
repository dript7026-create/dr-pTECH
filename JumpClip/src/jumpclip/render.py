from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw

from .analysis import synthesize_design_profile
from .designer import design_sprite_direction
from .learning import apply_learning_to_animation, apply_learning_to_design, load_learning_influence, summarize_learning_influence
from .models import AnimationSpec, DesignDirective, DesignProfile, RenderRequest
from .reference_sources import load_manifest
from . import depth_layers


def request_design_overrides(request: RenderRequest) -> dict:
    return {
        "art_preset": request.art_preset,
        "style_family": request.style_family,
        "silhouette_emphasis": request.silhouette_emphasis,
        "texture_detail": request.texture_detail,
        "palette_limit": request.palette_limit,
        "cel_shading": request.cel_shading,
        "outline_weight": request.outline_weight,
        "accessory_density": request.accessory_density,
        "tracing_bias": request.tracing_bias,
    }


def request_motion_overrides(request: RenderRequest) -> dict:
    return {
        "silhouette_bias": request.motion_silhouette_bias,
        "squash_stretch": request.motion_squash_stretch,
        "impact": request.motion_impact,
        "lift_scale": request.motion_lift,
    }


def resolve_learning_weight(request: RenderRequest) -> float:
    if request.learning_weight is None:
        return 1.0
    return max(0.0, min(1.0, float(request.learning_weight)))


def resolve_learning_influence(request: RenderRequest):
    if not request.learning_profile:
        return None
    return load_learning_influence(Path(request.learning_profile))


def resolve_render_plan(request: RenderRequest, profile: DesignProfile) -> tuple[AnimationSpec, DesignDirective, dict | None]:
    learning = resolve_learning_influence(request)
    learning_weight = resolve_learning_weight(request)
    animation = request.animation
    directive = design_sprite_direction(request.prompt, profile, overrides=request_design_overrides(request))
    if learning is not None:
        animation = apply_learning_to_animation(animation, learning, learning_weight)
        directive = apply_learning_to_design(directive, learning, learning_weight)
    return animation, directive, summarize_learning_influence(learning, learning_weight)


def apply_motion_overrides(spec: AnimationSpec, overrides: dict | None = None) -> AnimationSpec:
    overrides = overrides or {}
    return AnimationSpec(
        name=spec.name,
        frame_count=spec.frame_count,
        motion=spec.motion,
        silhouette_bias=float(overrides.get("silhouette_bias") if overrides.get("silhouette_bias") is not None else spec.silhouette_bias),
        squash_stretch=float(overrides.get("squash_stretch") if overrides.get("squash_stretch") is not None else spec.squash_stretch),
        impact=float(overrides.get("impact") if overrides.get("impact") is not None else spec.impact),
        lift_scale=float(overrides.get("lift_scale") if overrides.get("lift_scale") is not None else spec.lift_scale),
    )


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


def load_profile_input(path: Path, grid_size: int = 12, download_dir: Path | None = None) -> DesignProfile:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "references" in payload:
        references = load_manifest(path)
        return synthesize_design_profile(references, grid_size=grid_size, download_dir=download_dir)
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


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _silhouette_archetype(prompt: str, profile: DesignProfile) -> str:
    text = prompt.lower()
    tags = {tag.lower() for tag in profile.tags}
    if _contains_any(text, ("lahgroid", "manticore", "serpent", "feathered", "lantern", "hovering drones", "shoulder cannon")):
        return "lahgroid"
    if _contains_any(text, ("scarab", "beetle", "plague doctor", "hooded child", "scarab child")) or ({"scarab", "beetle"}.intersection(tags) and _contains_any(text, ("child", "hood", "mask", "acolyte"))):
        return "scarab-child"
    if _contains_any(text, ("spider", "arachnid", "botanical spider", "multi-leg")):
        return "arachnid"
    if "multi-leg" in tags and _contains_any(text, ("humanoid", "ritual", "scout")) and not _contains_any(text, ("boss", "serpent", "manticore", "lantern", "cannon", "drones")):
        return "arachnid"
    return "default"


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


def _variant_seed(request: RenderRequest) -> int:
    digest = hashlib.sha1(f"{request.character}|{request.prompt}|{request.animation.name}".encode("utf-8")).digest()
    return int.from_bytes(digest[:2], "big")


def _mix_color(left: tuple[int, int, int, int], right: tuple[int, int, int, int], weight: float) -> tuple[int, int, int, int]:
    return (
        int((left[0] * (1.0 - weight)) + (right[0] * weight)),
        int((left[1] * (1.0 - weight)) + (right[1] * weight)),
        int((left[2] * (1.0 - weight)) + (right[2] * weight)),
        255,
    )


def _apply_palette_finish(image: Image.Image, directive: DesignDirective) -> Image.Image:
    alpha = image.getchannel("A")
    rgb = image.convert("RGB")
    quantized = rgb.quantize(
        colors=directive.palette_limit,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.FLOYDSTEINBERG if directive.style_family == "8bit" else Image.Dither.NONE,
    ).convert("RGBA")
    quantized.putalpha(alpha)
    return quantized


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _movement_vector(pose: dict[str, float]) -> tuple[float, float, float]:
    vx = (pose["arm_a"] - pose["arm_b"]) * 0.8 + (pose["leg_a"] - pose["leg_b"]) * 0.6
    vy = pose["lift"] * 1.4 + (abs(pose["arm_a"]) + abs(pose["arm_b"])) * 0.05
    mag = math.sqrt((vx * vx) + (vy * vy))
    if mag <= 1e-6:
        return 0.0, -1.0, 0.0
    return vx / mag, vy / mag, mag


def _apply_pi_spiral_detail(
    image: Image.Image,
    directive: DesignDirective,
    profile: DesignProfile,
    pose: dict[str, float],
    geometry: dict[str, float],
    accent: tuple[int, int, int, int],
    shadow: tuple[int, int, int, int],
) -> None:
    detail_level = _clamp(directive.texture_detail, 0.0, 1.0)
    max_quality = _clamp(
        (profile.silhouette_coverage * 0.5) + (directive.silhouette_emphasis * 0.35) + ((1.0 - profile.edge_density) * 0.15),
        0.2,
        1.8,
    )
    attention = _clamp((detail_level * math.pi) / max(0.001, max_quality * math.pi), 0.0, 1.0)
    if attention <= 0.02:
        return

    flow_x, flow_y, flow_mag = _movement_vector(pose)
    flow_angle = math.atan2(flow_y, flow_x)
    phi = (1.0 + math.sqrt(5.0)) * 0.5
    pix = image.load()
    width, height = image.size

    center_x = geometry["center_x"]
    head_top = geometry["head_top"]
    head_h = max(2.0, geometry["head_h"])
    torso_top = geometry["torso_top"]
    torso_h = max(2.0, geometry["torso_h"])
    hip_y = geometry["hip_y"]
    floor_y = geometry["floor_y"]
    shoulder_w = max(2.0, geometry["shoulder_w"])
    hip_w = max(2.0, geometry["hip_w"])
    leg_h = max(2.0, geometry["leg_h"])

    regions = [
        ("head", center_x, head_top + (head_h * 0.5), head_h * 0.75, head_h * 0.95, 0.95),
        ("torso", center_x, torso_top + (torso_h * 0.5), shoulder_w * 1.05, torso_h, 1.2),
        ("hip", center_x, hip_y + (leg_h * 0.12), hip_w * 1.15, leg_h * 0.55, 0.85),
        ("leg_l", center_x - (hip_w * 0.34), hip_y + (leg_h * 0.58), hip_w * 0.5, leg_h * 0.9, 0.65),
        ("leg_r", center_x + (hip_w * 0.34), hip_y + (leg_h * 0.58), hip_w * 0.5, leg_h * 0.9, 0.65),
        ("arm_l", center_x - (shoulder_w * 0.72), torso_top + (torso_h * 0.6), shoulder_w * 0.45, torso_h * 0.85, 0.58),
        ("arm_r", center_x + (shoulder_w * 0.72), torso_top + (torso_h * 0.6), shoulder_w * 0.45, torso_h * 0.85, 0.58),
    ]

    for _name, cx, cy, rw, rh, weight in regions:
        region_area = max(4.0, rw * rh)
        budget = int((region_area / math.pi) * attention * weight * 0.06)
        if budget <= 0:
            continue
        lead_bias = _clamp(flow_mag / 8.0, 0.0, 1.0)
        for sample_index in range(budget):
            t = (sample_index + 1) / max(1, budget)
            theta = (2.0 * math.pi * t * phi) + flow_angle
            spiral_radius = pow(t, 1.0 / phi)
            dx = math.cos(theta) * (rw * 0.5) * spiral_radius
            dy = math.sin(theta) * (rh * 0.5) * spiral_radius
            px = int(round(cx + dx + (flow_x * lead_bias * rw * 0.18)))
            py = int(round(cy + dy + (flow_y * lead_bias * rh * 0.18)))
            if px < 0 or py < 0 or px >= width or py >= height:
                continue

            cur_r, cur_g, cur_b, cur_a = pix[px, py]
            flow_alignment = (dx * flow_x) + (dy * flow_y)

            if flow_alignment >= 0.0:
                # Add detail on leading edges of movement.
                mix = 0.35 + (0.45 * attention)
                out_r = int((cur_r * (1.0 - mix)) + (accent[0] * mix))
                out_g = int((cur_g * (1.0 - mix)) + (accent[1] * mix))
                out_b = int((cur_b * (1.0 - mix)) + (accent[2] * mix))
                out_a = max(cur_a, int(140 + (100 * attention)))
                pix[px, py] = (out_r, out_g, out_b, out_a)
            elif cur_a > 0:
                # Remove detail from trailing edges to keep silhouette clean.
                alpha_drop = int(24 + (42 * attention))
                out_a = max(0, cur_a - alpha_drop)
                out_r = int((cur_r * 0.72) + (shadow[0] * 0.28))
                out_g = int((cur_g * 0.72) + (shadow[1] * 0.28))
                out_b = int((cur_b * 0.72) + (shadow[2] * 0.28))
                pix[px, py] = (out_r, out_g, out_b, out_a)


def _apply_depth_layer_system(
    image: Image.Image,
    pose: dict[str, float],
    directive: DesignDirective,
    profile: DesignProfile,
    geometry: dict[str, float],
) -> Image.Image:
    """Apply 100-layer depth rendering with ragdoll physics influence and frame interpolation."""
    try:
        # Create ragdoll skeleton
        skeleton = depth_layers.create_ragdoll_skeleton()
        
        # Build layer configurations for all 100 layers
        pose_offsets = {
            "arm_a": pose.get("arm_a", 0.0),
            "arm_b": pose.get("arm_b", 0.0),
            "leg_a": pose.get("leg_a", 0.0),
            "leg_b": pose.get("leg_b", 0.0),
            "lift": pose.get("lift", 0.0),
        }
        
        layer_configs = depth_layers.build_all_layer_configs(pose_offsets, total_layers=100)
        
        # Render each layer with progressive silhouette reduction
        depth_layer_images = []
        physics_cfg = depth_layers.PhysicsConfig(
            gravity=0.18,
            damping=0.92,
            joint_stiffness=0.75,
        )
        
        # Update ragdoll state based on animation pose
        skeleton = depth_layers.update_ragdoll_frame(skeleton, pose_offsets, physics_cfg)
        
        for cfg in layer_configs:
            try:
                layer = depth_layers.render_depth_layer(
                    image,
                    cfg,
                    skeleton,
                    geometry,
                    prev_frame=None,
                )
                depth_layer_images.append(layer)
            except Exception:
                # Skip problematic layers
                continue
        
        # Composite all layers onto base image
        if depth_layer_images:
            result = depth_layers.composite_depth_layers(
                image,
                depth_layer_images,
                blend_mode="over",
            )
            return result
        
        return image
        
    except Exception:
        # Graceful fallback: return original image if depth system fails
        return image


def _draw_accessories(
    draw: ImageDraw.ImageDraw,
    directive: DesignDirective,
    seed: int,
    center_x: float,
    torso_top: float,
    hip_y: float,
    shoulder_w: float,
    head_top: float,
    head_h: float,
    accent: tuple[int, int, int, int],
    shadow: tuple[int, int, int, int],
) -> None:
    if directive.accessory_density < 0.28:
        return
    variant = seed % 4
    if variant == 0:
        draw.polygon(
            [
                (center_x - shoulder_w * 0.62, torso_top + 4),
                (center_x - shoulder_w * 0.95, hip_y - 2),
                (center_x - shoulder_w * 0.25, hip_y - 1),
            ],
            fill=(shadow[0], shadow[1], shadow[2], 210),
        )
    elif variant == 1:
        draw.rectangle((center_x + shoulder_w * 0.18, torso_top + 3, center_x + shoulder_w * 0.56, hip_y - 2), fill=(accent[0], accent[1], accent[2], 190))
    elif variant == 2:
        draw.polygon(
            [
                (center_x, head_top - 2),
                (center_x - head_h * 0.55, head_top + head_h * 0.2),
                (center_x + head_h * 0.55, head_top + head_h * 0.2),
            ],
            fill=accent,
        )
    else:
        draw.ellipse((center_x - shoulder_w * 0.2, torso_top + 5, center_x + shoulder_w * 0.2, torso_top + 10), outline=accent, width=1)


def _draw_texture_details(
    draw: ImageDraw.ImageDraw,
    directive: DesignDirective,
    center_x: float,
    torso_top: float,
    hip_y: float,
    shoulder_w: float,
    shadow: tuple[int, int, int, int],
    accent: tuple[int, int, int, int],
) -> None:
    if directive.texture_detail < 0.3:
        return
    detail_count = 2 + int(8 * directive.texture_detail)
    for detail_index in range(detail_count):
        x = int(center_x - shoulder_w * 0.45 + detail_index * max(2, shoulder_w / max(1, detail_count)))
        y = int(torso_top + 4 + (detail_index % 4) * 4)
        y0 = min(y, int(hip_y - 4))
        y1 = max(y0, min(int(hip_y - 3), y + 1))
        color = shadow if detail_index % 2 == 0 else accent
        if y0 <= y1:
            draw.rectangle((x, y0, x + 1, y1), fill=(color[0], color[1], color[2], 190))


def _draw_cel_shading(
    draw: ImageDraw.ImageDraw,
    directive: DesignDirective,
    center_x: float,
    torso_top: float,
    hip_y: float,
    shoulder_w: float,
    base: tuple[int, int, int, int],
    accent: tuple[int, int, int, int],
    shadow: tuple[int, int, int, int],
) -> None:
    if directive.cel_shading <= 0.0:
        return
    mid = _mix_color(base, shadow, min(0.55, 0.25 + directive.cel_shading * 0.25))
    rim = _mix_color(accent, (255, 255, 255, 255), min(0.45, directive.cel_shading * 0.35))
    draw.polygon(
        [
            (center_x - shoulder_w * 0.45, torso_top + 2),
            (center_x + shoulder_w * 0.32, torso_top + 2),
            (center_x + shoulder_w * 0.18, hip_y - 2),
            (center_x - shoulder_w * 0.28, hip_y - 2),
        ],
        fill=(mid[0], mid[1], mid[2], 180),
    )
    draw.line([(center_x + shoulder_w * 0.42, torso_top + 2), (center_x + shoulder_w * 0.26, hip_y - 2)], fill=(rim[0], rim[1], rim[2], 220), width=1)


def _draw_arachnid_features(
    draw: ImageDraw.ImageDraw,
    center_x: float,
    head_top: float,
    head_h: float,
    torso_top: float,
    hip_y: float,
    floor_y: float,
    shoulder_w: float,
    base: tuple[int, int, int, int],
    accent: tuple[int, int, int, int],
    shadow: tuple[int, int, int, int],
    line_thickness: int,
) -> None:
    draw.polygon(
        [
            (center_x, head_top - head_h * 0.16),
            (center_x - shoulder_w * 0.34, head_top + head_h * 0.34),
            (center_x - shoulder_w * 0.2, torso_top + 3),
            (center_x + shoulder_w * 0.2, torso_top + 3),
            (center_x + shoulder_w * 0.34, head_top + head_h * 0.34),
        ],
        fill=shadow,
    )
    draw.polygon(
        [
            (center_x - shoulder_w * 0.16, head_top + head_h * 0.22),
            (center_x + shoulder_w * 0.06, head_top + head_h * 0.18),
            (center_x + shoulder_w * 0.18, head_top + head_h * 0.54),
            (center_x - shoulder_w * 0.08, head_top + head_h * 0.62),
        ],
        fill=accent,
        outline=shadow,
    )
    draw.line(
        [
            (center_x - shoulder_w * 0.1, head_top + head_h * 0.48),
            (center_x + shoulder_w * 0.1, head_top + head_h * 0.48),
        ],
        fill=(255, 255, 255, 210),
        width=1,
    )
    draw.polygon(
        [
            (center_x - shoulder_w * 0.26, torso_top + 1),
            (center_x + shoulder_w * 0.26, torso_top + 1),
            (center_x + shoulder_w * 0.18, hip_y + 2),
            (center_x - shoulder_w * 0.18, hip_y + 2),
        ],
        fill=base,
        outline=shadow,
    )
    draw.polygon(
        [
            (center_x - shoulder_w * 0.44, torso_top + 4),
            (center_x + shoulder_w * 0.44, torso_top + 4),
            (center_x + shoulder_w * 0.58, floor_y - 2),
            (center_x - shoulder_w * 0.58, floor_y - 2),
        ],
        fill=(shadow[0], shadow[1], shadow[2], 224),
        outline=shadow,
    )
    limb_starts = [torso_top + 5, torso_top + 10, hip_y - 1, hip_y + 3]
    limb_reaches = [0.96, 1.12, 1.24, 1.36]
    for start_y, reach in zip(limb_starts, limb_reaches):
        left_joint = (center_x - shoulder_w * 0.68, start_y + 4)
        right_joint = (center_x + shoulder_w * 0.68, start_y + 4)
        left_tip = (center_x - shoulder_w * reach, min(floor_y - 1, start_y + 9))
        right_tip = (center_x + shoulder_w * reach, min(floor_y - 1, start_y + 9))
        draw.line([(center_x - shoulder_w * 0.22, start_y), left_joint, left_tip], fill=shadow, width=max(1, line_thickness - 1))
        draw.line([(center_x + shoulder_w * 0.22, start_y), right_joint, right_tip], fill=shadow, width=max(1, line_thickness - 1))
    draw.ellipse((center_x - shoulder_w * 0.62, torso_top + 2, center_x - shoulder_w * 0.28, torso_top + 9), fill=accent, outline=shadow, width=1)
    draw.ellipse((center_x + shoulder_w * 0.28, torso_top + 2, center_x + shoulder_w * 0.62, torso_top + 9), fill=accent, outline=shadow, width=1)
    draw.polygon(
        [
            (center_x + shoulder_w * 0.12, hip_y + 2),
            (center_x + shoulder_w * 0.5, hip_y + 6),
            (center_x + shoulder_w * 0.62, floor_y - 6),
            (center_x + shoulder_w * 0.28, floor_y - 4),
        ],
        fill=(base[0], base[1], base[2], 205),
        outline=shadow,
    )


def _draw_scarab_child_features(
    draw: ImageDraw.ImageDraw,
    center_x: float,
    head_top: float,
    head_h: float,
    torso_top: float,
    hip_y: float,
    floor_y: float,
    shoulder_w: float,
    accent: tuple[int, int, int, int],
    shadow: tuple[int, int, int, int],
    line_thickness: int,
) -> None:
    hood_width = shoulder_w * 0.82
    draw.polygon(
        [
            (center_x, head_top - head_h * 0.18),
            (center_x - hood_width * 0.55, head_top + head_h * 0.38),
            (center_x - hood_width * 0.38, torso_top + 2),
            (center_x + hood_width * 0.38, torso_top + 2),
            (center_x + hood_width * 0.55, head_top + head_h * 0.38),
        ],
        fill=shadow,
    )
    draw.polygon(
        [
            (center_x + head_h * 0.08, head_top + head_h * 0.42),
            (center_x + head_h * 0.44, head_top + head_h * 0.56),
            (center_x + head_h * 0.12, head_top + head_h * 0.68),
        ],
        fill=accent,
        outline=shadow,
    )
    draw.polygon(
        [
            (center_x - shoulder_w * 0.48, torso_top + 5),
            (center_x + shoulder_w * 0.48, torso_top + 5),
            (center_x + shoulder_w * 0.72, floor_y - 2),
            (center_x - shoulder_w * 0.72, floor_y - 2),
        ],
        fill=(shadow[0], shadow[1], shadow[2], 220),
        outline=shadow,
    )
    draw.ellipse((center_x - shoulder_w * 0.82, torso_top + 4, center_x - shoulder_w * 0.4, torso_top + 10), fill=accent, outline=shadow, width=1)
    draw.ellipse((center_x + shoulder_w * 0.4, torso_top + 4, center_x + shoulder_w * 0.82, torso_top + 10), fill=accent, outline=shadow, width=1)
    draw.rectangle((center_x + shoulder_w * 0.32, hip_y - 2, center_x + shoulder_w * 0.55, hip_y + 5), fill=(accent[0], accent[1], accent[2], 180), outline=shadow, width=max(1, line_thickness - 1))


def _draw_lahgroid_features(
    draw: ImageDraw.ImageDraw,
    center_x: float,
    head_top: float,
    head_h: float,
    torso_top: float,
    hip_y: float,
    floor_y: float,
    shoulder_w: float,
    base: tuple[int, int, int, int],
    accent: tuple[int, int, int, int],
    shadow: tuple[int, int, int, int],
    line_thickness: int,
) -> None:
    head_center_x = center_x - shoulder_w * 0.08
    head_bottom = head_top + head_h * 0.98
    draw.polygon(
        [
            (head_center_x - head_h * 0.22, head_top + 1),
            (head_center_x - head_h * 0.44, head_top + head_h * 0.2),
            (head_center_x - head_h * 0.38, head_top + head_h * 0.72),
            (head_center_x + head_h * 0.04, head_bottom),
            (head_center_x + head_h * 0.4, head_top + head_h * 0.58),
            (head_center_x + head_h * 0.34, head_top + head_h * 0.08),
        ],
        fill=accent,
        outline=shadow,
    )
    draw.polygon(
        [
            (head_center_x + head_h * 0.05, head_top + head_h * 0.12),
            (center_x + shoulder_w * 0.28, head_top + head_h * 0.08),
            (center_x + shoulder_w * 0.42, head_top + head_h * 0.24),
            (center_x + shoulder_w * 0.14, head_top + head_h * 0.5),
        ],
        fill=(accent[0], accent[1], accent[2], 230),
        outline=shadow,
    )
    draw.polygon(
        [
            (center_x - shoulder_w * 0.48, head_top + head_h * 0.16),
            (center_x - shoulder_w * 0.22, head_top + head_h * 0.02),
            (center_x - shoulder_w * 0.02, torso_top + 3),
            (center_x - shoulder_w * 0.38, torso_top + 6),
        ],
        fill=(base[0], base[1], base[2], 220),
        outline=shadow,
    )
    draw.polygon(
        [
            (head_center_x - head_h * 0.04, head_top + head_h * 0.78),
            (head_center_x + head_h * 0.12, head_top + head_h * 0.78),
            (center_x + shoulder_w * 0.08, torso_top + 3),
            (center_x - shoulder_w * 0.1, torso_top + 4),
        ],
        fill=shadow,
    )
    draw.polygon(
        [
            (center_x - shoulder_w * 0.42, torso_top + 2),
            (center_x + shoulder_w * 0.42, torso_top + 2),
            (center_x + shoulder_w * 0.28, hip_y),
            (center_x - shoulder_w * 0.18, hip_y + 1),
        ],
        fill=base,
        outline=shadow,
    )
    draw.polygon(
        [
            (center_x - shoulder_w * 0.14, hip_y - 1),
            (center_x + shoulder_w * 0.24, hip_y - 1),
            (center_x + shoulder_w * 0.16, floor_y - 2),
            (center_x - shoulder_w * 0.24, floor_y - 1),
        ],
        fill=(shadow[0], shadow[1], shadow[2], 222),
        outline=shadow,
    )
    draw.polygon(
        [
            (center_x - shoulder_w * 0.14, hip_y + 2),
            (center_x - shoulder_w * 0.34, hip_y + 5),
            (center_x - shoulder_w * 0.42, floor_y - 7),
            (center_x - shoulder_w * 0.3, floor_y - 2),
            (center_x - shoulder_w * 0.26, hip_y + 4),
        ],
        fill=(accent[0], accent[1], accent[2], 226),
        outline=shadow,
    )
    draw.line(
        [
            (center_x - shoulder_w * 0.38, torso_top + 4),
            (center_x - shoulder_w * 0.46, hip_y - 2),
            (center_x - shoulder_w * 0.5, hip_y + 5),
        ],
        fill=shadow,
        width=max(1, line_thickness - 1),
    )
    draw.line(
        [
            (center_x - shoulder_w * 0.14, torso_top + 6),
            (center_x - shoulder_w * 0.48, torso_top + 10),
            (center_x - shoulder_w * 0.6, torso_top + 13),
        ],
        fill=accent,
        width=max(1, line_thickness - 1),
    )
    draw.line(
        [
            (center_x + shoulder_w * 0.12, torso_top + 6),
            (center_x + shoulder_w * 0.3, torso_top + 10),
            (center_x + shoulder_w * 0.38, torso_top + 12),
        ],
        fill=accent,
        width=max(1, line_thickness - 1),
    )
    draw.line(
        [
            (center_x - shoulder_w * 0.3, torso_top + 8),
            (center_x - shoulder_w * 0.46, hip_y + 7),
        ],
        fill=shadow,
        width=max(1, line_thickness - 1),
    )
    draw.ellipse((center_x - shoulder_w * 0.54, hip_y + 4, center_x - shoulder_w * 0.34, hip_y + 11), fill=accent, outline=shadow, width=1)
    draw.line(
        [
            (center_x + shoulder_w * 0.02, torso_top + 9),
            (center_x + shoulder_w * 0.16, hip_y + 6),
            (center_x + shoulder_w * 0.08, floor_y - 3),
        ],
        fill=accent,
        width=1,
    )
    draw.ellipse((center_x - 2, floor_y - 6, center_x + 4, floor_y), fill=accent, outline=shadow, width=1)
    draw.rectangle((center_x + shoulder_w * 0.2, torso_top + 4, center_x + shoulder_w * 0.36, torso_top + 10), fill=accent, outline=shadow, width=1)
    draw.rectangle((center_x + shoulder_w * 0.36, torso_top + 5, center_x + shoulder_w * 0.46, torso_top + 8), fill=shadow)
    drone_centers = [
        (center_x + shoulder_w * 0.44, head_top + head_h * 0.2),
        (center_x + shoulder_w * 0.52, head_top + head_h * 0.42),
        (center_x + shoulder_w * 0.4, torso_top + 3),
    ]
    for drone_x, drone_y in drone_centers:
        draw.line([(drone_x - 3, drone_y), (drone_x + 3, drone_y)], fill=accent, width=1)
        draw.line([(drone_x, drone_y - 3), (drone_x, drone_y + 3)], fill=accent, width=1)
        draw.rectangle((drone_x - 1, drone_y - 1, drone_x + 1, drone_y + 1), fill=shadow)


def render_frame(
    request: RenderRequest,
    profile: DesignProfile,
    frame_index: int,
    animation: AnimationSpec | None = None,
    directive: DesignDirective | None = None,
) -> Image.Image:
    size = request.canvas_size
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    influences = _influence_weights(request.prompt)
    directive = directive or design_sprite_direction(request.prompt, profile, overrides=request_design_overrides(request))
    animation = animation or request.animation
    base, accent, shadow = _style_colors(profile, influences)
    pose = _pose_offsets(animation, frame_index)
    pose["lift"] *= max(0.0, animation.lift_scale)
    variant_seed = _variant_seed(request)
    phase = (frame_index / max(1, animation.frame_count)) * math.tau
    squash_wave = math.sin(phase)
    archetype = _silhouette_archetype(request.prompt, profile)

    center_x = size * 0.5
    floor_y = size * 0.84 - pose["lift"]
    height_ratio = profile.proportion_profile.get("height_ratio", 0.78)
    width_ratio = profile.proportion_profile.get("width_ratio", 0.3)
    surreal_scale = 1.0 + (0.16 * influences["surreal"])
    gothic_spike = 2 + int(4 * influences["gothic"])
    stretch_factor = 1.0 + (request.animation.squash_stretch * squash_wave * 0.35)
    width_factor = 1.0 - (request.animation.squash_stretch * squash_wave * 0.18)
    figure_h = size * min(0.88, max(0.56, height_ratio)) * surreal_scale * max(0.75, stretch_factor)
    torso_h = figure_h * 0.36
    head_h = figure_h * max(0.13, profile.proportion_profile.get("head_ratio", 0.16))
    leg_h = figure_h * 0.34
    shoulder_w = size * max(0.16, width_ratio) * animation.silhouette_bias * directive.silhouette_emphasis * max(0.75, width_factor)
    hip_w = shoulder_w * 0.72

    if archetype == "arachnid":
        figure_h *= 0.9
        torso_h = figure_h * 0.38
        head_h *= 0.72
        shoulder_w *= 0.82
        hip_w *= 0.76
        leg_h *= 0.86
    elif archetype == "scarab-child":
        figure_h *= 0.88
        torso_h = figure_h * 0.34
        head_h *= 1.05
        shoulder_w *= 0.94
        hip_w *= 0.92
    elif archetype == "lahgroid":
        figure_h *= 0.76
        torso_h = figure_h * 0.38
        head_h *= 0.62
        shoulder_w *= 0.68
        hip_w *= 0.8
        leg_h *= 0.66
        center_x = size * 0.5

    line_thickness = 1 + int((3 * profile.line_weight_profile.get("medium", 0.25)) * directive.outline_weight)
    if influences["bosch"]:
        line_thickness += 1

    head_top = floor_y - figure_h
    torso_top = head_top + head_h
    hip_y = torso_top + torso_h
    shadow_field = _grid_sample(profile, 0.5, 0.75)

    head_width = head_h * 0.4
    if archetype == "scarab-child":
        head_width = head_h * 0.34
    elif archetype == "lahgroid":
        head_width = head_h * 0.28
    elif archetype == "arachnid":
        head_width = head_h * 0.3

    if archetype == "lahgroid":
        pass
    elif archetype == "scarab-child":
        draw.ellipse(
            (center_x - head_width * 0.72, head_top + 1, center_x + head_width * 0.42, head_top + head_h * 0.92),
            fill=accent,
            outline=shadow,
            width=line_thickness,
        )
        draw.polygon(
            [
                (center_x, head_top - 2),
                (center_x - shoulder_w * 0.42, torso_top + 2),
                (center_x + shoulder_w * 0.42, torso_top + 2),
            ],
            fill=shadow,
        )
        draw.polygon(
            [
                (center_x - shoulder_w * 0.34, torso_top),
                (center_x + shoulder_w * 0.34, torso_top),
                (center_x + hip_w * 0.55, floor_y - 3),
                (center_x - hip_w * 0.55, floor_y - 3),
            ],
            fill=base,
            outline=shadow,
        )
    elif archetype == "arachnid":
        pass
    else:
        draw.ellipse(
            (center_x - head_width, head_top, center_x + head_width, head_top + head_h),
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

    if archetype == "arachnid":
        _draw_arachnid_features(draw, center_x, head_top, head_h, torso_top, hip_y, floor_y, shoulder_w, base, accent, shadow, line_thickness)
    elif archetype == "scarab-child":
        _draw_scarab_child_features(draw, center_x, head_top, head_h, torso_top, hip_y, floor_y, shoulder_w, accent, shadow, line_thickness)
    elif archetype == "lahgroid":
        _draw_lahgroid_features(draw, center_x, head_top, head_h, torso_top, hip_y, floor_y, shoulder_w, base, accent, shadow, line_thickness)

    _draw_accessories(draw, directive, variant_seed, center_x, torso_top, hip_y, shoulder_w, head_top, head_h, accent, shadow)
    _draw_cel_shading(draw, directive, center_x, torso_top, hip_y, shoulder_w, base, accent, shadow)

    arm_y = torso_top + torso_h * 0.18
    leg_y = hip_y
    arm_len = torso_h * 0.95 * (1.0 + 0.1 * influences["surreal"]) * (1.0 + animation.impact * 0.08)
    leg_len = leg_h * (1.0 + 0.08 * influences["anatomical"])
    left_arm_end = (center_x - shoulder_w * 0.75 + pose["arm_a"], arm_y + arm_len)
    right_arm_end = (center_x + shoulder_w * 0.75 + pose["arm_b"], arm_y + arm_len)
    left_leg_end = (center_x - hip_w * 0.35 + pose["leg_a"], leg_y + leg_len)
    right_leg_end = (center_x + hip_w * 0.35 + pose["leg_b"], leg_y + leg_len)

    if archetype == "lahgroid":
        draw.line([(center_x - shoulder_w * 0.56, arm_y), (left_arm_end[0] - shoulder_w * 0.18, left_arm_end[1] - 2)], fill=shadow, width=line_thickness)
        draw.line([(center_x + shoulder_w * 0.54, arm_y + 1), (right_arm_end[0] + shoulder_w * 0.08, right_arm_end[1] - 4)], fill=shadow, width=line_thickness)
        draw.line([(center_x - hip_w * 0.38, leg_y + 1), (center_x - shoulder_w * 0.6 + pose["leg_a"], leg_y + leg_len * 0.82)], fill=shadow, width=line_thickness)
        draw.line([(center_x + hip_w * 0.32, leg_y + 1), (center_x + shoulder_w * 0.52 + pose["leg_b"], leg_y + leg_len * 0.84)], fill=shadow, width=line_thickness)
    else:
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

    _draw_texture_details(draw, directive, center_x, torso_top, hip_y, shoulder_w, shadow, accent)

    if influences["goya"]:
        draw.rectangle(
            (center_x - shoulder_w * 0.6, torso_top + torso_h * 0.55, center_x + shoulder_w * 0.6, hip_y + 2),
            fill=(shadow[0], shadow[1], shadow[2], int(80 + shadow_field * 70)),
        )

    if animation.motion == "attack" and archetype != "lahgroid":
        sweep_color = (accent[0], accent[1], accent[2], 220)
        draw.arc(
            (center_x - shoulder_w, torso_top - 6, center_x + shoulder_w * 1.7, hip_y + leg_len * 0.2),
            start=-45,
            end=55 + int(50 * animation.impact),
            fill=sweep_color,
            width=max(1, line_thickness + 1),
        )

    if animation.motion in {"run", "jump"}:
        dust_alpha = 80 + int((120 + (animation.impact * 40)) * abs(math.sin((frame_index / max(1, animation.frame_count)) * math.pi)))
        draw.line(
            [(center_x - shoulder_w * 0.5, floor_y + 1), (center_x + shoulder_w * 0.5, floor_y + 1)],
            fill=(base[0], base[1], base[2], dust_alpha),
            width=1,
        )

This
        {
            "center_x": center_x,
            "head_top": head_top,
            "head_h": head_h,
            "torso_top": torso_top,
            "torso_h": torso_h,
            "hip_y": hip_y,
            "floor_y": floor_y,
            "shoulder_w": shoulder_w,
            "hip_w": hip_w,
            "leg_h": leg_h,
        },
    )

    return _apply_palette_finish(image, directive)


def render_frames(request: RenderRequest, profile: DesignProfile) -> list[Image.Image]:
    animation, directive, _learning = resolve_render_plan(request, profile)
    return [render_frame(request, profile, index, animation=animation, directive=directive) for index in range(animation.frame_count)]


def sheet_layout(frame_count: int, frame_width: int, frame_height: int, max_sheet_width: int | None = None, columns: int | None = None) -> dict[str, int]:
    if columns is None:
        if max_sheet_width is None:
            columns = frame_count
        else:
            columns = max(1, min(frame_count, max_sheet_width // max(1, frame_width)))
    columns = max(1, min(frame_count, columns))
    rows = max(1, math.ceil(frame_count / columns))
    return {
        "columns": columns,
        "rows": rows,
        "sheet_width": frame_width * columns,
        "sheet_height": frame_height * rows,
    }


def save_sheet(frames: list[Image.Image], out_path: Path, upscale: int, columns: int | None = None) -> Path:
    frame_w, frame_h = frames[0].size
    layout = sheet_layout(len(frames), frame_w, frame_h, columns=columns)
    sheet = Image.new("RGBA", (layout["sheet_width"], layout["sheet_height"]), (0, 0, 0, 0))
    for index, frame in enumerate(frames):
        x = (index % layout["columns"]) * frame_w
        y = (index // layout["columns"]) * frame_h
        sheet.paste(frame, (x, y))
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
