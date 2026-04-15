from __future__ import annotations

import json
from pathlib import Path

from .models import AnimationSpec, DesignDirective, LearningInfluence


def load_learning_influence(path: Path) -> LearningInfluence:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return LearningInfluence(**payload)


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _as_float(mapping: dict[str, object], key: str, default: float = 0.0) -> float:
    value = mapping.get(key, default)
    if value is None:
        return default
    return float(value)


def _blend(base: float, target: float | None, weight: float, minimum: float, maximum: float) -> float:
    if target is None:
        return clamp(base, minimum, maximum)
    return clamp((base * (1.0 - weight)) + (float(target) * weight), minimum, maximum)


def _dominant_godai(godai: dict[str, float]) -> str | None:
    if not godai:
        return None
    return max(godai, key=lambda key: float(godai.get(key, 0.0)))


def _godai_style_bias(godai: dict[str, float]) -> dict[str, float]:
    dominant = _dominant_godai(godai)
    if dominant == "earth":
        return {
            "silhouette_emphasis": 1.45,
            "texture_detail": 0.46,
            "outline_weight": 1.36,
            "accessory_density": 0.42,
            "tracing_bias": 0.18,
        }
    if dominant == "water":
        return {
            "silhouette_emphasis": 1.18,
            "texture_detail": 0.58,
            "outline_weight": 1.02,
            "accessory_density": 0.46,
            "tracing_bias": 0.34,
        }
    if dominant == "fire":
        return {
            "silhouette_emphasis": 1.34,
            "texture_detail": 0.54,
            "outline_weight": 1.18,
            "accessory_density": 0.5,
            "tracing_bias": 0.22,
        }
    if dominant == "wind":
        return {
            "silhouette_emphasis": 1.28,
            "texture_detail": 0.34,
            "outline_weight": 1.08,
            "accessory_density": 0.36,
            "tracing_bias": 0.12,
        }
    if dominant == "void":
        return {
            "silhouette_emphasis": 1.22,
            "texture_detail": 0.64,
            "outline_weight": 0.96,
            "accessory_density": 0.44,
            "tracing_bias": 0.62,
        }
    return {}


def _godai_motion_bias(godai: dict[str, float]) -> dict[str, float]:
    dominant = _dominant_godai(godai)
    if dominant == "earth":
        return {
            "silhouette_bias": 1.18,
            "squash_stretch": 0.1,
            "impact": 0.58,
            "lift_scale": 0.84,
        }
    if dominant == "water":
        return {
            "silhouette_bias": 1.06,
            "squash_stretch": 0.2,
            "impact": 0.34,
            "lift_scale": 1.06,
        }
    if dominant == "fire":
        return {
            "silhouette_bias": 1.14,
            "squash_stretch": 0.22,
            "impact": 0.88,
            "lift_scale": 1.0,
        }
    if dominant == "wind":
        return {
            "silhouette_bias": 1.2,
            "squash_stretch": 0.18,
            "impact": 0.44,
            "lift_scale": 1.18,
        }
    if dominant == "void":
        return {
            "silhouette_bias": 1.12,
            "squash_stretch": 0.12,
            "impact": 0.52,
            "lift_scale": 1.08,
        }
    return {}


def apply_learning_to_design(directive: DesignDirective, influence: LearningInfluence, weight: float) -> DesignDirective:
    if weight <= 0.0:
        return directive
    style_signals = {**_godai_style_bias(influence.godai), **influence.style_signals}
    learned_style_family = style_signals.get("style_family")
    style_family = directive.style_family
    if isinstance(learned_style_family, str) and weight >= 0.5 and directive.art_preset is None:
        style_family = learned_style_family
    return DesignDirective(
        art_preset=directive.art_preset,
        style_family=style_family,
        silhouette_emphasis=_blend(directive.silhouette_emphasis, style_signals.get("silhouette_emphasis"), weight, 0.8, 2.5),
        texture_detail=_blend(directive.texture_detail, style_signals.get("texture_detail"), weight, 0.0, 1.0),
        palette_limit=int(round(_blend(float(directive.palette_limit), style_signals.get("palette_limit"), weight, 2.0, 64.0))),
        shading_bands=int(round(_blend(float(directive.shading_bands), style_signals.get("shading_bands"), weight, 1.0, 8.0))),
        outline_weight=_blend(directive.outline_weight, style_signals.get("outline_weight"), weight, 0.5, 3.0),
        accessory_density=_blend(directive.accessory_density, style_signals.get("accessory_density"), weight, 0.0, 1.0),
        cel_shading=_blend(directive.cel_shading, style_signals.get("cel_shading"), weight, 0.0, 1.0),
        tracing_bias=_blend(directive.tracing_bias, style_signals.get("tracing_bias"), weight, 0.0, 1.0),
    )


def apply_learning_to_animation(spec: AnimationSpec, influence: LearningInfluence, weight: float) -> AnimationSpec:
    if weight <= 0.0:
        return spec
    motion_signals = {**_godai_motion_bias(influence.godai), **influence.motion_signals}
    preferred_tags = motion_signals.get("preferred_key_pose_tags")
    silhouette_bias = _blend(spec.silhouette_bias, motion_signals.get("motion_silhouette_bias", motion_signals.get("silhouette_bias")), weight, 0.8, 2.0)
    squash_stretch = _blend(spec.squash_stretch, motion_signals.get("motion_squash_stretch", motion_signals.get("squash_stretch")), weight, 0.0, 0.5)
    impact = _blend(spec.impact, motion_signals.get("motion_impact", motion_signals.get("impact")), weight, 0.0, 1.2)
    lift_scale = _blend(spec.lift_scale, motion_signals.get("motion_lift", motion_signals.get("lift_scale")), weight, 0.5, 1.6)
    if isinstance(preferred_tags, list):
        tags = {str(item) for item in preferred_tags}
        if "airborne_extension" in tags or "landing_catch" in tags:
            lift_scale = clamp(lift_scale + (0.08 * weight), 0.5, 1.6)
        if "impact_contact" in tags or "twist_release" in tags:
            impact = clamp(impact + (0.08 * weight), 0.0, 1.2)
        if "ritual_hold" in tags:
            squash_stretch = clamp(squash_stretch - (0.04 * weight), 0.0, 0.5)
    return AnimationSpec(
        name=spec.name,
        frame_count=spec.frame_count,
        motion=spec.motion,
        silhouette_bias=silhouette_bias,
        squash_stretch=squash_stretch,
        impact=impact,
        lift_scale=lift_scale,
    )


def summarize_learning_influence(influence: LearningInfluence | None, weight: float) -> dict | None:
    if influence is None:
        return None
    return {
        "subject": influence.subject,
        "weight": weight,
        "godai": {key: _as_float(influence.godai, key) for key in sorted(influence.godai)},
        "style_signals": influence.style_signals,
        "motion_signals": influence.motion_signals,
    }