from __future__ import annotations

from .models import DesignDirective, DesignProfile


STYLE_KEYWORDS = {
    "8bit": "8bit",
    "8-bit": "8bit",
    "nes": "8bit",
    "gameboy": "8bit",
    "16bit": "16bit",
    "16-bit": "16bit",
    "snes": "16bit",
    "genesis": "16bit",
    "hd2d": "hd2d",
    "hd-2d": "hd2d",
    "bitmap": "bitmap-traced",
    "traced": "bitmap-traced",
    "cel": "cel-shaded-2.5d",
    "cel-shaded": "cel-shaded-2.5d",
    "2.5d": "cel-shaded-2.5d",
    "cg": "cel-shaded-2.5d",
}


STYLE_PRESETS = {
    "8bit": {
        "palette_limit": 8,
        "shading_bands": 2,
        "outline_weight": 1.45,
        "texture_detail": 0.22,
        "accessory_density": 0.35,
        "cel_shading": 0.0,
        "tracing_bias": 0.0,
        "silhouette_emphasis": 1.45,
    },
    "16bit": {
        "palette_limit": 16,
        "shading_bands": 3,
        "outline_weight": 1.25,
        "texture_detail": 0.42,
        "accessory_density": 0.45,
        "cel_shading": 0.1,
        "tracing_bias": 0.15,
        "silhouette_emphasis": 1.28,
    },
    "hd2d": {
        "palette_limit": 24,
        "shading_bands": 3,
        "outline_weight": 1.05,
        "texture_detail": 0.58,
        "accessory_density": 0.58,
        "cel_shading": 0.28,
        "tracing_bias": 0.35,
        "silhouette_emphasis": 1.18,
    },
    "bitmap-traced": {
        "palette_limit": 32,
        "shading_bands": 4,
        "outline_weight": 1.12,
        "texture_detail": 0.72,
        "accessory_density": 0.62,
        "cel_shading": 0.24,
        "tracing_bias": 0.78,
        "silhouette_emphasis": 1.16,
    },
    "cel-shaded-2.5d": {
        "palette_limit": 36,
        "shading_bands": 4,
        "outline_weight": 0.96,
        "texture_detail": 0.64,
        "accessory_density": 0.6,
        "cel_shading": 0.86,
        "tracing_bias": 0.56,
        "silhouette_emphasis": 1.2,
    },
}


ART_DIRECTION_PRESETS = {
    "retro-arcade": {
        "style_family": "8bit",
        "silhouette_emphasis": 1.72,
        "texture_detail": 0.16,
        "palette_limit": 8,
        "outline_weight": 1.8,
        "accessory_density": 0.2,
        "tracing_bias": 0.0,
    },
    "snes-rpg": {
        "style_family": "16bit",
        "silhouette_emphasis": 1.4,
        "texture_detail": 0.36,
        "palette_limit": 16,
        "outline_weight": 1.3,
        "accessory_density": 0.42,
        "tracing_bias": 0.08,
    },
    "hd2d-rpg": {
        "style_family": "hd2d",
        "silhouette_emphasis": 1.26,
        "texture_detail": 0.56,
        "palette_limit": 22,
        "outline_weight": 1.1,
        "accessory_density": 0.54,
        "tracing_bias": 0.28,
        "cel_shading": 0.22,
    },
    "cel-brawler": {
        "style_family": "cel-shaded-2.5d",
        "silhouette_emphasis": 1.34,
        "texture_detail": 0.74,
        "palette_limit": 28,
        "outline_weight": 0.92,
        "accessory_density": 0.68,
        "tracing_bias": 0.72,
        "cel_shading": 1.0,
    },
    "space-shooter": {
        "style_family": "16bit",
        "silhouette_emphasis": 1.52,
        "texture_detail": 0.3,
        "palette_limit": 14,
        "outline_weight": 1.4,
        "accessory_density": 0.34,
        "tracing_bias": 0.06,
        "cel_shading": 0.08,
    },
    "soulslike-action": {
        "style_family": "bitmap-traced",
        "silhouette_emphasis": 1.3,
        "texture_detail": 0.82,
        "palette_limit": 26,
        "outline_weight": 1.08,
        "accessory_density": 0.72,
        "tracing_bias": 0.8,
        "cel_shading": 0.2,
    },
}


def classify_style_family(prompt: str) -> str:
    text = prompt.lower()
    for keyword, family in STYLE_KEYWORDS.items():
        if keyword in text:
            return family
    if "pixel" in text:
        return "16bit"
    return "hd2d"


def _prompt_weight(text: str, keywords: tuple[str, ...]) -> float:
    return 1.0 if any(keyword in text for keyword in keywords) else 0.0


def design_sprite_direction(prompt: str, profile: DesignProfile, overrides: dict | None = None) -> DesignDirective:
    text = prompt.lower()
    overrides = overrides or {}
    art_preset = overrides.get("art_preset")
    preset_overrides = ART_DIRECTION_PRESETS.get(art_preset, {}) if art_preset else {}
    family = overrides.get("style_family") or preset_overrides.get("style_family") or classify_style_family(prompt)
    preset = STYLE_PRESETS[family]

    silhouette_push = _prompt_weight(text, ("distinct silhouette", "readable silhouette", "heroic silhouette", "bold silhouette", "iconic"))
    detail_push = _prompt_weight(text, ("ornate", "detailed", "texture", "filigree", "cosmetic", "fine detail"))
    economy_push = _prompt_weight(text, ("minimal", "simple", "flat", "low detail", "clean"))

    silhouette_emphasis = preset["silhouette_emphasis"] + (profile.silhouette_coverage * 0.25) + (silhouette_push * 0.18)
    texture_detail = min(1.0, max(0.12, preset["texture_detail"] + (detail_push * 0.18) - (economy_push * 0.16)))
    accessory_density = min(1.0, max(0.15, preset["accessory_density"] + (detail_push * 0.15) - (economy_push * 0.12)))
    outline_weight = max(0.75, preset["outline_weight"] + ((profile.line_weight_profile.get("heavy", 0.0) - profile.line_weight_profile.get("thin", 0.0)) * 0.8))
    palette_limit = max(6, min(48, int(preset["palette_limit"] + (detail_push * 4) - (economy_push * 2))))

    if overrides.get("silhouette_emphasis") is not None:
        silhouette_emphasis = max(0.8, float(overrides["silhouette_emphasis"]))
    elif preset_overrides.get("silhouette_emphasis") is not None:
        silhouette_emphasis = max(0.8, float(preset_overrides["silhouette_emphasis"]))
    if overrides.get("texture_detail") is not None:
        texture_detail = min(1.0, max(0.0, float(overrides["texture_detail"])))
    elif preset_overrides.get("texture_detail") is not None:
        texture_detail = min(1.0, max(0.0, float(preset_overrides["texture_detail"])))
    if overrides.get("palette_limit") is not None:
        palette_limit = max(2, min(64, int(overrides["palette_limit"])))
    elif preset_overrides.get("palette_limit") is not None:
        palette_limit = max(2, min(64, int(preset_overrides["palette_limit"])))
    if overrides.get("outline_weight") is not None:
        outline_weight = max(0.5, min(3.0, float(overrides["outline_weight"])))
    elif preset_overrides.get("outline_weight") is not None:
        outline_weight = max(0.5, min(3.0, float(preset_overrides["outline_weight"])))
    if overrides.get("accessory_density") is not None:
        accessory_density = min(1.0, max(0.0, float(overrides["accessory_density"])))
    elif preset_overrides.get("accessory_density") is not None:
        accessory_density = min(1.0, max(0.0, float(preset_overrides["accessory_density"])))
    cel_shading = float(preset["cel_shading"])
    if overrides.get("cel_shading") is not None:
        cel_shading = min(1.0, max(0.0, float(overrides["cel_shading"])))
    elif preset_overrides.get("cel_shading") is not None:
        cel_shading = min(1.0, max(0.0, float(preset_overrides["cel_shading"])))
    tracing_bias = float(preset["tracing_bias"])
    if overrides.get("tracing_bias") is not None:
        tracing_bias = min(1.0, max(0.0, float(overrides["tracing_bias"])))
    elif preset_overrides.get("tracing_bias") is not None:
        tracing_bias = min(1.0, max(0.0, float(preset_overrides["tracing_bias"])))

    return DesignDirective(
        art_preset=art_preset,
        style_family=family,
        silhouette_emphasis=silhouette_emphasis,
        texture_detail=texture_detail,
        palette_limit=palette_limit,
        shading_bands=int(preset["shading_bands"]),
        outline_weight=outline_weight,
        accessory_density=accessory_density,
        cel_shading=cel_shading,
        tracing_bias=tracing_bias,
    )