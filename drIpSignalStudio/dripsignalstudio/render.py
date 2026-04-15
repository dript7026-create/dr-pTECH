"""Local render helpers for drIpSignalStudio preview assets."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageFont

from .model import AdDraft, CampaignPlan


APP_ROOT = Path(__file__).resolve().parents[1]
GENERATED_ROOT = APP_ROOT / "generated"
PREVIEW_ROOT = GENERATED_ROOT / "previews"
FRAME_SIZE = (540, 960)
FRAME_COUNT = 12
FRAME_RATE = 6


def _load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = []
    if bold:
        candidates.extend([
            "C:/Windows/Fonts/georgiab.ttf",
            "C:/Windows/Fonts/trebucbd.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ])
    else:
        candidates.extend([
            "C:/Windows/Fonts/georgia.ttf",
            "C:/Windows/Fonts/trebuc.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ])
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def _slug(text: str) -> str:
    cleaned = [ch.lower() if ch.isalnum() else "-" for ch in text]
    slug = "".join(cleaned)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "draft"


def _digest(plan: CampaignPlan, draft: AdDraft) -> str:
    payload = {
        "profile": asdict(plan.profile),
        "signals": asdict(plan.signals),
        "draft": asdict(draft),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _scene_payloads(draft: AdDraft) -> list[dict]:
    return [
        {
            "kicker": draft.slot_label,
            "headline": draft.hook,
            "body": draft.short_script[0],
        },
        {
            "kicker": draft.render_assets.get("format_bias", draft.slot_label),
            "headline": draft.creative_angle,
            "body": " ".join(draft.short_script[1:3]),
        },
        {
            "kicker": "visual direction",
            "headline": draft.visual_direction[0],
            "body": " | ".join(draft.visual_direction[1:4]),
        },
        {
            "kicker": "call to action",
            "headline": draft.call_to_action,
            "body": draft.caption,
        },
    ]


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> str:
    words = text.split()
    if not words:
        return ""
    lines = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        box = draw.multiline_textbbox((0, 0), trial, font=font, spacing=6)
        if box[2] - box[0] <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return "\n".join(lines)


def _background(draw: ImageDraw.ImageDraw, frame_index: int, draft: AdDraft) -> None:
    width, height = FRAME_SIZE
    progress = frame_index / max(1, FRAME_COUNT - 1)
    amber = (232, 98, 44)
    gold = (243, 181, 74)
    graphite = (25, 22, 30)
    paper = (247, 239, 228)

    for y in range(height):
        mix = y / height
        color = (
            int(graphite[0] * (1 - mix) + amber[0] * mix * 0.55),
            int(graphite[1] * (1 - mix) + gold[1] * mix * 0.42),
            int(graphite[2] * (1 - mix) + paper[2] * mix * 0.18),
        )
        draw.line((0, y, width, y), fill=color)

    for band in range(6):
        offset = (band * 120 + int(progress * 180) + len(draft.slot_key) * 9) % (width + 220) - 220
        band_color = (255, 255, 255, 34 + band * 8)
        draw.rounded_rectangle((offset, 80 + band * 130, offset + 240, 132 + band * 130), radius=24, fill=band_color)

    arc_radius = 120 + int(progress * 90)
    center_x = width - 86
    center_y = 124 + int(math.sin(progress * math.pi) * 28)
    draw.ellipse((center_x - arc_radius, center_y - arc_radius, center_x + arc_radius, center_y + arc_radius), outline=(255, 244, 220, 90), width=5)
    draw.ellipse((42, height - 230, 262, height - 10), fill=(243, 181, 74, 42), outline=(255, 255, 255, 55), width=3)


def _render_frame(draft: AdDraft, frame_index: int, output_path: Path) -> None:
    image = Image.new("RGBA", FRAME_SIZE, (19, 15, 18, 255))
    draw = ImageDraw.Draw(image, "RGBA")
    _background(draw, frame_index, draft)

    kicker_font = _load_font(22)
    headline_font = _load_font(42, bold=True)
    body_font = _load_font(24)
    tag_font = _load_font(18, bold=True)

    scenes = _scene_payloads(draft)
    scene = scenes[min(len(scenes) - 1, int((frame_index / FRAME_COUNT) * len(scenes)))]

    panel_left = 34
    panel_top = 78
    panel_right = FRAME_SIZE[0] - 34
    panel_bottom = FRAME_SIZE[1] - 180
    draw.rounded_rectangle((panel_left, panel_top, panel_right, panel_bottom), radius=34, fill=(250, 245, 237, 215), outline=(255, 255, 255, 80), width=2)

    draw.text((58, 112), scene["kicker"].upper(), font=kicker_font, fill=(111, 65, 39, 255), spacing=6)
    wrapped_headline = _wrap_text(draw, scene["headline"], headline_font, max_width=panel_right - panel_left - 56)
    draw.multiline_text((58, 160), wrapped_headline, font=headline_font, fill=(28, 18, 22, 255), spacing=8)

    wrapped_body = _wrap_text(draw, scene["body"], body_font, max_width=panel_right - panel_left - 56)
    draw.multiline_text((58, 410), wrapped_body, font=body_font, fill=(53, 40, 47, 255), spacing=8)

    footer_y = FRAME_SIZE[1] - 134
    tag_x = 42
    for tag in draft.hashtags[:3]:
        box = draw.textbbox((0, 0), tag, font=tag_font)
        width = box[2] - box[0] + 22
        draw.rounded_rectangle((tag_x, footer_y, tag_x + width, footer_y + 34), radius=16, fill=(255, 248, 238, 180), outline=(255, 255, 255, 80))
        draw.text((tag_x + 11, footer_y + 8), tag, font=tag_font, fill=(90, 50, 34, 255))
        tag_x += width + 8

    cta_font = _load_font(26, bold=True)
    cta_text = draft.call_to_action.upper()
    cta_box = draw.textbbox((0, 0), cta_text, font=cta_font)
    cta_width = cta_box[2] - cta_box[0] + 28
    draw.rounded_rectangle((FRAME_SIZE[0] - cta_width - 36, footer_y - 4, FRAME_SIZE[0] - 36, footer_y + 42), radius=22, fill=(232, 98, 44, 255))
    draw.text((FRAME_SIZE[0] - cta_width - 22, footer_y + 7), cta_text, font=cta_font, fill=(255, 255, 255, 255))

    image.convert("RGB").save(output_path, format="PNG")


def _encode_video(frames_dir: Path, video_path: Path) -> bool:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        return False

    command = [
        ffmpeg,
        "-y",
        "-framerate",
        str(FRAME_RATE),
        "-i",
        str(frames_dir / "frame_%02d.png"),
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(video_path),
    ]
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    return video_path.exists()


def ensure_render_assets(plan: CampaignPlan, draft: AdDraft) -> dict:
    preview_id = f"{_slug(draft.slot_key)}-{_digest(plan, draft)}"
    preview_dir = PREVIEW_ROOT / preview_id
    frames_dir = preview_dir / "frames"
    poster_path = preview_dir / "poster.png"
    video_path = preview_dir / "preview.mp4"

    preview_dir.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)

    if not poster_path.exists():
        for frame_index in range(FRAME_COUNT):
            _render_frame(draft, frame_index, frames_dir / f"frame_{frame_index:02d}.png")
        shutil.copyfile(frames_dir / "frame_06.png", poster_path)

    mode = "poster-only"
    if not video_path.exists():
        if _encode_video(frames_dir, video_path):
            mode = "mp4-preview"
    elif video_path.exists():
        mode = "mp4-preview"

    return {
        "mode": mode,
        "preview_id": preview_id,
        "poster_path": f"/generated/previews/{preview_id}/poster.png",
        "video_path": f"/generated/previews/{preview_id}/preview.mp4" if video_path.exists() else None,
        "frame_count": FRAME_COUNT,
        "frame_rate": FRAME_RATE,
        "format_bias": next((part for part in [draft.slot_label, draft.slot_key] if part), draft.slot_key),
    }


def enrich_plan_with_renders(plan: CampaignPlan) -> CampaignPlan:
    for draft in plan.drafts:
        draft.render_assets = ensure_render_assets(plan, draft)
    return plan


def resolve_generated_asset(request_path: str) -> Path | None:
    if not request_path.startswith("/generated/"):
        return None
    candidate = (APP_ROOT / request_path.lstrip("/")).resolve()
    try:
        candidate.relative_to(GENERATED_ROOT.resolve())
    except ValueError:
        return None
    if not candidate.exists() or not candidate.is_file():
        return None
    return candidate