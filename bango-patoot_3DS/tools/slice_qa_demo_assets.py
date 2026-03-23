from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = ROOT / "recraft" / "bango_patoot_qa_demo_manifest.json"
DEFAULT_SOURCE_ROOT = ROOT / "generated"
DEFAULT_EXPORT_ROOT = ROOT / "generated" / "qa_demo_runtime_exports"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def alpha_bbox(image: Image.Image):
    return image.getchannel("A").getbbox()


def fit_to_canvas(image: Image.Image, target_w: int, target_h: int) -> Image.Image:
    rgba = image.convert("RGBA")
    bbox = alpha_bbox(rgba)
    if bbox is None:
        return Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))

    cropped = rgba.crop(bbox)
    scale = min((target_w - 2) / max(1, cropped.width), (target_h - 2) / max(1, cropped.height))
    resized = cropped.resize(
        (max(1, int(round(cropped.width * scale))), max(1, int(round(cropped.height * scale)))),
        Image.Resampling.NEAREST,
    )
    canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    offset_x = (target_w - resized.width) // 2
    offset_y = target_h - resized.height - 1
    canvas.alpha_composite(resized, (offset_x, offset_y))
    return canvas


def alpha_square_portrait(image: Image.Image, target_size: int) -> Image.Image:
    rgba = image.convert("RGBA")
    bbox = alpha_bbox(rgba)
    if bbox is None:
        return Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))

    left, top, right, bottom = bbox
    width = right - left
    height = bottom - top
    side = max(width, height)
    center_x = (left + right) * 0.5
    center_y = top + height * 0.35
    crop_left = int(round(center_x - side * 0.5))
    crop_top = int(round(center_y - side * 0.5))
    crop_right = crop_left + side
    crop_bottom = crop_top + side

    crop_left = max(0, crop_left)
    crop_top = max(0, crop_top)
    crop_right = min(rgba.width, crop_right)
    crop_bottom = min(rgba.height, crop_bottom)
    square = rgba.crop((crop_left, crop_top, crop_right, crop_bottom))
    return square.resize((target_size, target_size), Image.Resampling.NEAREST)


def export_variant(crop: Image.Image, export_root: Path, base_name: str, export_def: dict) -> None:
    mode = export_def["mode"]
    name = export_def["name"]
    if mode == "raw":
        out_image = crop
    elif mode == "fit":
        width, height = export_def["size"]
        out_image = fit_to_canvas(crop, int(width), int(height))
    elif mode == "alpha_square_portrait":
        width, _ = export_def["size"]
        out_image = alpha_square_portrait(crop, int(width))
    else:
        raise ValueError(f"Unsupported export mode: {mode}")

    ensure_dir(export_root)
    out_path = export_root / f"{base_name}__{name}.png"
    out_image.save(out_path)


def crop_cell(image: Image.Image, grid: dict, row: int, col: int) -> Image.Image:
    cell_width = int(grid["cell_width"])
    cell_height = int(grid["cell_height"])
    left = col * cell_width
    top = row * cell_height
    return image.crop((left, top, left + cell_width, top + cell_height))


def process_uniform_grid(asset: dict, image: Image.Image, export_root: Path) -> int:
    count = 0
    grid = asset["slice_plan"]["grid"]
    for cell in asset["slice_plan"]["cells"]:
        crop = crop_cell(image, grid, int(cell["row"]), int(cell["col"]))
        for export_def in cell["exports"]:
            export_variant(crop, export_root / asset["category"] / asset["name"], cell["name"], export_def)
            count += 1
    return count


def process_uniform_grid_auto(asset: dict, image: Image.Image, export_root: Path) -> int:
    count = 0
    grid = asset["slice_plan"]["grid"]
    cols = int(grid["cols"])
    rows = int(grid["rows"])
    exports = asset["slice_plan"]["auto_exports"]
    for row in range(rows):
        for col in range(cols):
            crop = crop_cell(image, grid, row, col)
            if alpha_bbox(crop) is None:
                continue
            base_name = f"cell_r{row:02d}_c{col:02d}"
            for export_def in exports:
                export_variant(crop, export_root / asset["category"] / asset["name"], base_name, export_def)
                count += 1
    return count


def write_manual_template(asset: dict, export_root: Path) -> None:
    template_path = export_root / "_manual_templates" / f"{asset['name']}.regions.template.json"
    ensure_dir(template_path.parent)
    template = {
        "asset": asset["name"],
        "category": asset["category"],
        "canvas": asset["slice_plan"]["canvas"],
        "template_outputs": asset["slice_plan"].get("template_outputs", []),
        "regions": [],
    }
    template_path.write_text(json.dumps(template, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Slice generated QA demo masters into runtime exports or manual slice templates.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--export-root", type=Path, default=DEFAULT_EXPORT_ROOT)
    args = parser.parse_args()

    manifest = load_json(args.manifest)
    sliced = 0
    missing = 0
    manual_templates = 0

    for asset in manifest.get("assets", []):
        relative_source = Path(asset["out"])
        source_path = args.source_root / relative_source
        mode = asset["slice_plan"]["mode"]

        if mode == "manual-regions":
            write_manual_template(asset, args.export_root)
            manual_templates += 1
            if not source_path.exists():
                continue
            continue

        if not source_path.exists():
            missing += 1
            print(f"[MISSING] {source_path}")
            continue

        image = Image.open(source_path).convert("RGBA")
        if mode == "uniform-grid":
            sliced += process_uniform_grid(asset, image, args.export_root)
        elif mode == "uniform-grid-auto":
            sliced += process_uniform_grid_auto(asset, image, args.export_root)
        else:
            raise ValueError(f"Unsupported slice mode: {mode}")

    print(f"Generated {sliced} runtime exports.")
    print(f"Wrote {manual_templates} manual slice templates.")
    if missing:
        print(f"Skipped {missing} assets because source masters were not present under {args.source_root}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())