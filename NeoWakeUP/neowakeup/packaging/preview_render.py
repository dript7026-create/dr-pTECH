from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from ..planetary.network import Directive, PlanetaryMindNetwork, PlanetaryMindStore


ROOT = Path(__file__).resolve().parents[2]
ASSET_ROOT = ROOT / "assets" / "recraft"
OUT_DIR = ROOT / "public_preview"


def _open(path: Path) -> Image.Image | None:
    if not path.exists():
        return None
    return Image.open(path).convert("RGBA")


def _fit(image: Image.Image, max_w: int, max_h: int) -> Image.Image:
    scale = min(max_w / max(image.width, 1), max_h / max(image.height, 1))
    return image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))), Image.LANCZOS)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    canvas = Image.new("RGBA", (1380, 860), (10, 18, 24, 255))
    bg = _open(ASSET_ROOT / "gui_pass_300" / "panels" / "control_panel_background.png")
    if bg is not None:
        canvas.alpha_composite(bg.resize((1380, 860), Image.LANCZOS))
    overlay = _open(ASSET_ROOT / "gui_pass_300_corrective" / "network" / "node_map_overlay.png") or _open(ASSET_ROOT / "gui_pass_300" / "network" / "node_map_overlay.png")
    if overlay is not None:
        canvas.alpha_composite(overlay.resize((1380, 860), Image.LANCZOS))

    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    draw.rounded_rectangle((18, 18, 360, 842), radius=18, fill=(12, 24, 31, 220), outline=(46, 90, 108, 255), width=2)
    brand = _open(ASSET_ROOT / "gui_pass_300_corrective" / "branding" / "brand_mark_set.png") or _open(ASSET_ROOT / "gui_pass_300" / "branding" / "brand_mark_set.png")
    if brand is not None:
        brand = _fit(brand, 300, 120)
        canvas.alpha_composite(brand, (34, 30))

    planet = _open(ASSET_ROOT / "gui_pass_600" / "planet" / "planetary_mind_planet_core.png")
    if planet is not None:
        planet = _fit(planet, 260, 260)
        canvas.alpha_composite(planet, (720 - planet.width // 2, 410 - planet.height // 2))
    streams = _open(ASSET_ROOT / "gui_pass_600" / "network" / "network_channel_streams.png")
    if streams is not None:
        streams = _fit(streams, 760, 500)
        canvas.alpha_composite(streams, (690 - streams.width // 2, 400 - streams.height // 2))

    network = PlanetaryMindNetwork(seed=7)
    network.bootstrap()
    report = network.solve(Directive())
    region_items = list(report["regions"].items())[:6]
    icons = _open(ASSET_ROOT / "gui_pass_600" / "icons" / "humanoid_mind_icons_set_a.png")
    icon_frames = []
    if icons is not None:
        frame_w = icons.width // 5
        for i in range(5):
            icon_frames.append(icons.crop((i * frame_w, 0, min(icons.width, (i + 1) * frame_w), icons.height)))
    import math
    cx, cy, orbit = 920, 410, 240
    for idx, (region_id, data) in enumerate(region_items):
        angle = (idx / max(len(region_items), 1)) * math.pi * 2.0
        rx = int(cx + orbit * math.cos(angle))
        ry = int(cy + orbit * math.sin(angle))
        draw.line((cx, cy, rx, ry), fill=(63, 127, 137, 255), width=3)
        if icon_frames:
            icon = _fit(icon_frames[idx % len(icon_frames)], 74, 74)
            canvas.alpha_composite(icon, (rx - icon.width // 2, ry - icon.height // 2))
        draw.text((rx - 10, ry + 44), region_id, font=font, fill=(230, 255, 248, 255))

    draw.text((58, 190), "NeoWakeUP Control Hub", font=font, fill=(230, 255, 248, 255))
    draw.text((58, 226), "Prompt: Stabilize exchange while preserving novelty", font=font, fill=(180, 223, 220, 255))
    draw.text((58, 276), "Directive Sliders", font=font, fill=(230, 255, 248, 255))
    for index, line in enumerate(["Novelty 0.70", "Equity 0.70", "Resilience 0.70", "Speed 0.60"]):
        draw.text((58, 312 + index * 34), line, font=font, fill=(180, 223, 220, 255))
    draw.text((58, 474), f"Planetary coherence {report['planetary_coherence']:.3f}", font=font, fill=(230, 255, 248, 255))
    draw.text((58, 510), f"Exchange {report['exchange']:.3f}", font=font, fill=(180, 223, 220, 255))
    draw.text((58, 546), f"Volatility {report['volatility']:.3f}", font=font, fill=(180, 223, 220, 255))
    draw.text((58, 582), f"Solution {report['solution_score']:.3f}", font=font, fill=(180, 223, 220, 255))

    screenshot_path = OUT_DIR / "neowakeup_control_hub_preview.png"
    canvas.save(screenshot_path)
    (OUT_DIR / "preview_metadata.json").write_text(json.dumps({"preview": str(screenshot_path), "report": report}, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote preview to {screenshot_path}")