import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
FRAME_MANIFEST = ROOT / "innsmouth_island_frame_pair_expansion_manifest.json"
TILE_MANIFEST = ROOT / "innsmouth_island_tiles_skybox_pair_expansion_manifest.json"
FRAME_FINAL_DIR = (ROOT / "../../ORBEngine/assets/innsmouth_island/frame_pair_expansion/final").resolve()
FRAME_PRECISION_DIR = (ROOT / "../../ORBEngine/assets/innsmouth_island/frame_pair_expansion/precision").resolve()
TILE_FINAL_DIR = (ROOT / "../../ORBEngine/assets/innsmouth_island/tiles_skybox_pair_expansion/final").resolve()
TILE_PRECISION_DIR = (ROOT / "../../ORBEngine/assets/innsmouth_island/tiles_skybox_pair_expansion/precision").resolve()
REPORT_PATH = ROOT / "innsmouth_island_pair_congruence_report_v1.json"
FRAME_REROLL_PATH = ROOT / "innsmouth_island_frame_pair_reroll_manifest_v1.json"
TILE_REROLL_PATH = ROOT / "innsmouth_island_tiles_skybox_pair_reroll_manifest_v1.json"


def load_manifest(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def alpha_points(path: Path):
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        return set(), None
    pixels = alpha.load()
    width, height = alpha.size
    points = set()
    for y in range(height):
        row_offset = y * width
        for x in range(width):
            if pixels[x, y] > 0:
                points.add(row_offset + x)
    return points, bbox


def bbox_delta(first, second):
    if first is None or second is None:
        return 999999
    return sum(abs(a - b) for a, b in zip(first, second))


def pair_key_from_name(name: str):
    if name.endswith("_final_v1"):
        return name[:-9]
    if name.endswith("_precision_v1"):
        return name[:-13]
    return name


def collect_pairs(final_dir: Path, precision_dir: Path):
    finals = {pair_key_from_name(path.stem): path for path in final_dir.rglob("*_final_v1.png")}
    precisions = {pair_key_from_name(path.stem): path for path in precision_dir.rglob("*_precision_v1.png")}
    keys = sorted(set(finals) & set(precisions))
    return [(key, finals[key], precisions[key]) for key in keys]


def evaluate_pair(pair_key: str, final_path: Path, precision_path: Path):
    final_points, final_bbox = alpha_points(final_path)
    precision_points, precision_bbox = alpha_points(precision_path)
    union = len(final_points | precision_points)
    intersection = len(final_points & precision_points)
    final_area = len(final_points)
    precision_area = len(precision_points)
    iou = 1.0 if union == 0 else intersection / union
    coverage_delta = 0.0 if max(final_area, precision_area) == 0 else abs(final_area - precision_area) / max(final_area, precision_area)
    delta = bbox_delta(final_bbox, precision_bbox)
    flagged = iou < 0.88 or coverage_delta > 0.18 or delta > 32
    return {
        "pair_key": pair_key,
        "final": str(final_path),
        "precision": str(precision_path),
        "iou": round(iou, 5),
        "coverage_delta": round(coverage_delta, 5),
        "bbox_delta_px": delta,
        "flagged": flagged,
    }


def build_reroll_manifest(source_manifest, flagged_pair_keys):
    reroll_items = []
    flagged = set(flagged_pair_keys)
    for item in source_manifest:
        if item.get("pair_group") in flagged:
            reroll_items.append(item)
    return reroll_items


def summarize(results):
    flagged = [result for result in results if result["flagged"]]
    return {
        "pair_count": len(results),
        "flagged_count": len(flagged),
        "flagged_pair_keys": [result["pair_key"] for result in flagged],
        "worst_iou": min((result["iou"] for result in results), default=1.0),
        "max_bbox_delta_px": max((result["bbox_delta_px"] for result in results), default=0),
        "max_coverage_delta": max((result["coverage_delta"] for result in results), default=0.0),
    }


def main():
    frame_results = [evaluate_pair(pair_key, final_path, precision_path) for pair_key, final_path, precision_path in collect_pairs(FRAME_FINAL_DIR, FRAME_PRECISION_DIR)]
    tile_results = [evaluate_pair(pair_key, final_path, precision_path) for pair_key, final_path, precision_path in collect_pairs(TILE_FINAL_DIR, TILE_PRECISION_DIR)]

    frame_summary = summarize(frame_results)
    tile_summary = summarize(tile_results)

    frame_manifest = load_manifest(FRAME_MANIFEST)
    tile_manifest = load_manifest(TILE_MANIFEST)
    frame_reroll_manifest = build_reroll_manifest(frame_manifest, frame_summary["flagged_pair_keys"])
    tile_reroll_manifest = build_reroll_manifest(tile_manifest, tile_summary["flagged_pair_keys"])

    report = {
        "frame_pairs": frame_summary,
        "tile_pairs": tile_summary,
        "frame_pair_details": frame_results,
        "tile_pair_details": tile_results,
        "thresholds": {
            "min_iou": 0.88,
            "max_coverage_delta": 0.18,
            "max_bbox_delta_px": 32,
        },
    }

    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    FRAME_REROLL_PATH.write_text(json.dumps(frame_reroll_manifest, indent=2), encoding="utf-8")
    TILE_REROLL_PATH.write_text(json.dumps(tile_reroll_manifest, indent=2), encoding="utf-8")

    print(f"frame_pairs={frame_summary['pair_count']} flagged={frame_summary['flagged_count']}")
    print(f"tile_pairs={tile_summary['pair_count']} flagged={tile_summary['flagged_count']}")
    print(f"report={REPORT_PATH}")
    print(f"frame_reroll_manifest={FRAME_REROLL_PATH}")
    print(f"tile_reroll_manifest={TILE_REROLL_PATH}")


if __name__ == "__main__":
    main()