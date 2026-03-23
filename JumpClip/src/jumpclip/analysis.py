from __future__ import annotations

from collections import Counter
from pathlib import Path

import numpy as np
import requests
from PIL import Image

from .models import DesignProfile, ReferenceImage


def _download_reference(reference: ReferenceImage, download_dir: Path) -> Path:
    if reference.local_path:
        return Path(reference.local_path)
    if not reference.image_url:
        raise ValueError(f"Reference {reference.identifier} has no image URL")
    download_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(reference.image_url).suffix or ".png"
    target = download_dir / f"{reference.provider}_{reference.identifier}{suffix}"
    if not target.exists():
        response = requests.get(reference.image_url, timeout=60)
        response.raise_for_status()
        target.write_bytes(response.content)
    reference.local_path = str(target)
    return target


def _load_rgba(path: Path) -> np.ndarray:
    image = Image.open(path).convert("RGBA")
    return np.array(image)


def _alpha_mask(rgba: np.ndarray) -> np.ndarray:
    alpha = rgba[:, :, 3]
    luminance = np.mean(rgba[:, :, :3], axis=2)
    return (alpha > 16) | (luminance < 235)


def _edge_density(rgba: np.ndarray) -> float:
    gray = np.mean(rgba[:, :, :3].astype(np.float32), axis=2)
    grad_y = np.abs(np.diff(gray, axis=0, prepend=gray[0:1, :]))
    grad_x = np.abs(np.diff(gray, axis=1, prepend=gray[:, 0:1]))
    edges = grad_x + grad_y
    return float(np.mean(edges > 18.0))


def _quantized_palette(rgba: np.ndarray, color_count: int = 6) -> list[str]:
    image = Image.fromarray(rgba, mode="RGBA").convert("P", palette=Image.Palette.ADAPTIVE, colors=color_count).convert("RGBA")
    pixels = np.array(image)[:, :, :3].reshape(-1, 3)
    counter = Counter(tuple(int(channel) for channel in pixel) for pixel in pixels)
    return ["#%02x%02x%02x" % rgb for rgb, _ in counter.most_common(color_count)]


def _proportion_profile(mask: np.ndarray) -> dict[str, float]:
    ys, xs = np.where(mask)
    if len(xs) == 0 or len(ys) == 0:
        return {
            "height_ratio": 0.8,
            "width_ratio": 0.35,
            "head_ratio": 0.16,
            "torso_ratio": 0.38,
            "leg_ratio": 0.46,
        }
    h, w = mask.shape
    min_x, max_x = xs.min(), xs.max()
    min_y, max_y = ys.min(), ys.max()
    occupied_height = max(1, max_y - min_y + 1)
    occupied_width = max(1, max_x - min_x + 1)
    row_sum = mask[min_y:max_y + 1, min_x:max_x + 1].sum(axis=1)
    head_rows = max(1, int(occupied_height * 0.18))
    torso_rows = max(1, int(occupied_height * 0.38))
    return {
        "height_ratio": occupied_height / float(h),
        "width_ratio": occupied_width / float(w),
        "head_ratio": float(np.mean(row_sum[:head_rows])) / max(1.0, occupied_width),
        "torso_ratio": float(np.mean(row_sum[head_rows:head_rows + torso_rows])) / max(1.0, occupied_width),
        "leg_ratio": float(np.mean(row_sum[head_rows + torso_rows:])) / max(1.0, occupied_width),
    }


def _line_weight_profile(rgba: np.ndarray) -> dict[str, float]:
    gray = np.mean(rgba[:, :, :3].astype(np.float32), axis=2)
    grad_y = np.abs(np.diff(gray, axis=0, prepend=gray[0:1, :]))
    grad_x = np.abs(np.diff(gray, axis=1, prepend=gray[:, 0:1]))
    edge_map = grad_x + grad_y
    return {
        "thin": float(np.mean((edge_map > 8.0) & (edge_map <= 20.0))),
        "medium": float(np.mean((edge_map > 20.0) & (edge_map <= 42.0))),
        "heavy": float(np.mean(edge_map > 42.0)),
    }


def _grid_relativities(rgba: np.ndarray, grid_size: int) -> list[list[float]]:
    h, w, _ = rgba.shape
    cell_h = max(1, h // grid_size)
    cell_w = max(1, w // grid_size)
    relativity = []
    gray = np.mean(rgba[:, :, :3].astype(np.float32), axis=2)
    alpha = rgba[:, :, 3].astype(np.float32) / 255.0
    for y in range(grid_size):
        row = []
        for x in range(grid_size):
            y0 = y * cell_h
            x0 = x * cell_w
            y1 = h if y == grid_size - 1 else min(h, (y + 1) * cell_h)
            x1 = w if x == grid_size - 1 else min(w, (x + 1) * cell_w)
            cell_gray = gray[y0:y1, x0:x1]
            cell_alpha = alpha[y0:y1, x0:x1]
            coverage = float(np.mean(cell_alpha))
            darkness = 1.0 - float(np.mean(cell_gray)) / 255.0
            row.append((coverage * 0.65) + (darkness * 0.35))
        relativity.append(row)
    return relativity


def synthesize_design_profile(
    references: list[ReferenceImage],
    grid_size: int = 12,
    download_dir: Path | None = None,
) -> DesignProfile:
    if not references:
        raise ValueError("At least one reference is required")

    palette_counter = Counter()
    edge_densities = []
    silhouette_coverages = []
    proportion_profiles = []
    line_profiles = []
    all_grids = []
    provider_set = set()
    tag_set = set()

    for reference in references:
        if not reference.local_path:
            if download_dir is None:
                raise ValueError("download_dir is required when references do not have local_path values")
            path = _download_reference(reference, download_dir)
        else:
            path = Path(reference.local_path)
        rgba = _load_rgba(path)
        mask = _alpha_mask(rgba)
        palette_counter.update(_quantized_palette(rgba))
        edge_densities.append(_edge_density(rgba))
        silhouette_coverages.append(float(np.mean(mask)))
        proportion_profiles.append(_proportion_profile(mask))
        line_profiles.append(_line_weight_profile(rgba))
        all_grids.append(_grid_relativities(rgba, grid_size))
        provider_set.add(reference.provider)
        tag_set.update(tag for tag in reference.tags if tag)

    avg_proportions = {
        key: float(np.mean([profile[key] for profile in proportion_profiles]))
        for key in proportion_profiles[0]
    }
    avg_lines = {
        key: float(np.mean([profile[key] for profile in line_profiles]))
        for key in line_profiles[0]
    }
    avg_grid = np.mean(np.array(all_grids, dtype=np.float32), axis=0).tolist()

    return DesignProfile(
        grid_size=grid_size,
        palette=[color for color, _ in palette_counter.most_common(6)],
        silhouette_coverage=float(np.mean(silhouette_coverages)),
        edge_density=float(np.mean(edge_densities)),
        proportion_profile=avg_proportions,
        line_weight_profile=avg_lines,
        grid_relativities=avg_grid,
        providers=sorted(provider_set),
        tags=sorted(tag_set),
        source_count=len(references),
    )
