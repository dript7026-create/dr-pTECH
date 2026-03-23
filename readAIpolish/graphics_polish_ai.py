from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps


RASTER_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}


def _default_output_path(source: Path) -> Path:
    return source.with_name(f"{source.stem}_readAIpolish{source.suffix}")


def _resolve_preview_source(source: Path) -> Path | None:
    preview_candidates = [
        source.with_suffix(".png"),
        source.with_suffix(".jpg"),
        source.parent / f"{source.stem}.png",
    ]
    return next((candidate for candidate in preview_candidates if candidate.exists()), None)


def _alpha_bbox(image: Image.Image) -> list[int] | None:
    bbox = image.getchannel("A").getbbox()
    return list(bbox) if bbox else None


def _dominant_palette(image: Image.Image, limit: int = 5) -> list[dict]:
    quantized = image.convert("RGBA").copy()
    quantized.thumbnail((128, 128))
    palette_image = quantized.convert("P", palette=Image.Palette.ADAPTIVE, colors=min(16, max(limit, 8))).convert("RGBA")
    colors = palette_image.getcolors(maxcolors=128 * 128) or []
    total = sum(count for count, rgba in colors if rgba[3] > 0)
    ranked = sorted(
        ((count, rgba) for count, rgba in colors if rgba[3] > 0),
        key=lambda item: item[0],
        reverse=True,
    )[:limit]
    return [
        {
            "rgba": [int(channel) for channel in rgba],
            "coverage": round(count / total, 4) if total else 0.0,
        }
        for count, rgba in ranked
    ]


def analyze_image(image: Image.Image) -> dict:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    alpha = rgba.getchannel("A")
    alpha_values = list(alpha.getdata())
    opaque_pixels = sum(1 for value in alpha_values if value > 0)
    total_pixels = width * height
    bbox = _alpha_bbox(rgba)

    center_x = 0.0
    center_y = 0.0
    if opaque_pixels:
        weighted_x = 0.0
        weighted_y = 0.0
        total_alpha = 0.0
        for y in range(height):
            for x in range(width):
                pixel_alpha = alpha.getpixel((x, y))
                if pixel_alpha <= 0:
                    continue
                weighted_x += x * pixel_alpha
                weighted_y += y * pixel_alpha
                total_alpha += pixel_alpha
        if total_alpha:
            center_x = weighted_x / total_alpha
            center_y = weighted_y / total_alpha

    grayscale = rgba.convert("L")
    mean_luminance = 0.0
    if total_pixels:
        mean_luminance = sum(grayscale.getdata()) / total_pixels

    edge_map = grayscale.filter(ImageFilter.FIND_EDGES)
    edge_values = list(edge_map.getdata())
    edge_density = sum(1 for value in edge_values if value >= 32) / total_pixels if total_pixels else 0.0

    bbox_width = 0
    bbox_height = 0
    if bbox:
        bbox_width = bbox[2] - bbox[0]
        bbox_height = bbox[3] - bbox[1]

    normalized_center = [round(center_x / width, 4), round(center_y / height, 4)] if width and height else [0.0, 0.0]
    silhouette_balance = round(abs(0.5 - normalized_center[0]) + abs(0.5 - normalized_center[1]), 4)
    aspect_ratio = round(width / height, 4) if height else 0.0
    readable_fill = round((bbox_width * bbox_height) / total_pixels, 4) if bbox and total_pixels else 0.0

    return {
        "size": [width, height],
        "alpha_bbox": bbox,
        "opaque_pixel_count": opaque_pixels,
        "alpha_coverage": round(opaque_pixels / total_pixels, 4) if total_pixels else 0.0,
        "readable_fill_ratio": readable_fill,
        "center_of_mass": [round(center_x, 3), round(center_y, 3)],
        "normalized_center_of_mass": normalized_center,
        "silhouette_balance_score": silhouette_balance,
        "mean_luminance": round(mean_luminance / 255.0, 4),
        "edge_density": round(edge_density, 4),
        "aspect_ratio": aspect_ratio,
        "dominant_palette": _dominant_palette(rgba),
    }


def analyze_visual_asset_path(source_path: str | Path) -> dict:
    source = Path(source_path)
    if not source.exists():
        raise FileNotFoundError(f"Asset not found: {source}")

    if source.suffix.lower() in RASTER_EXTENSIONS:
        return {
            "source": str(source),
            "mode": "raster_visual_read",
            "analysis": analyze_image(Image.open(source)),
        }

    if source.suffix.lower() == ".clip":
        preview_source = _resolve_preview_source(source)
        return {
            "source": str(source),
            "mode": "clip_preview_visual_read",
            "preview_source": str(preview_source) if preview_source else None,
            "analysis": analyze_image(Image.open(preview_source)) if preview_source else None,
            "note": "Visual analysis is performed on a sibling raster preview when native .clip pixel access is unavailable.",
        }

    raise ValueError(f"Unsupported asset type for readAIpolish visual analysis: {source.suffix}")


def polish_image(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    rgb = rgba.convert("RGB")
    base = ImageEnhance.Color(rgb).enhance(1.12)
    local_contrast = ImageEnhance.Contrast(base).enhance(1.18)
    edge_map = local_contrast.filter(ImageFilter.EDGE_ENHANCE_MORE)
    detail_pass = local_contrast.filter(ImageFilter.DETAIL)
    luminance = ImageOps.autocontrast(local_contrast.convert("L"))
    depth_hint = ImageOps.colorize(luminance, black="#26180f", white="#f5d7ab")
    shaded = Image.blend(detail_pass, depth_hint, 0.14)
    articulated = ImageChops.overlay(shaded, edge_map)
    articulated = ImageEnhance.Sharpness(articulated).enhance(1.35)
    articulated = ImageEnhance.Contrast(articulated).enhance(1.08)
    result = articulated.convert("RGBA")
    result.putalpha(alpha)
    return result


def polish_asset_path(source_path: str | Path, output_path: str | Path | None = None) -> dict:
    source = Path(source_path)
    if not source.exists():
        raise FileNotFoundError(f"Asset not found: {source}")

    target = Path(output_path) if output_path else _default_output_path(source)
    target.parent.mkdir(parents=True, exist_ok=True)

    if source.suffix.lower() in RASTER_EXTENSIONS:
        polished = polish_image(Image.open(source))
        polished.save(target)
        return {
            "source": str(source),
            "target": str(target),
            "mode": "raster_polish",
        }

    if source.suffix.lower() == ".clip":
        copied_clip = target
        shutil.copy2(source, copied_clip)
        preview_source = _resolve_preview_source(source)
        preview_target = None
        if preview_source is not None:
            preview_target = copied_clip.with_suffix(".png")
            polished = polish_image(Image.open(preview_source))
            polished.save(preview_target)
        sidecar = copied_clip.with_suffix(".json")
        sidecar.write_text(
            json.dumps(
                {
                    "source_clip": str(source),
                    "copied_clip": str(copied_clip),
                    "preview_source": str(preview_source) if preview_source else None,
                    "preview_target": str(preview_target) if preview_target else None,
                    "mode": "clip_bridge",
                    "note": "Native .clip raster mutation is not implemented here; this bridge preserves the .clip and writes a polished preview when a sibling raster export exists.",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return {
            "source": str(source),
            "target": str(copied_clip),
            "preview_target": str(preview_target) if preview_target else None,
            "sidecar": str(sidecar),
            "mode": "clip_bridge",
        }

    raise ValueError(f"Unsupported asset type for readAIpolish: {source.suffix}")
