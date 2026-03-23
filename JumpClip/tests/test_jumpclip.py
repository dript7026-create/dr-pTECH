from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from jumpclip.analysis import synthesize_design_profile
from jumpclip.models import ReferenceImage, RenderRequest
from jumpclip.render import infer_animation_spec, render_frames, save_sheet


def _make_reference(path: Path) -> None:
    image = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((16, 4, 32, 18), fill=(220, 210, 180, 255))
    draw.rectangle((18, 18, 30, 32), fill=(120, 90, 70, 255))
    draw.line((20, 32, 14, 44), fill=(40, 30, 28, 255), width=2)
    draw.line((28, 32, 34, 44), fill=(40, 30, 28, 255), width=2)
    image.save(path)


def test_profile_and_sheet_generation(tmp_path: Path) -> None:
    ref_path = tmp_path / "ref.png"
    _make_reference(ref_path)
    references = [
        ReferenceImage(
            provider="local",
            identifier="ref",
            title="Ref",
            local_path=str(ref_path),
            tags=["pixel-art", "public-domain"],
        )
    ]
    profile = synthesize_design_profile(references, grid_size=8)
    assert profile.source_count == 1
    assert profile.grid_size == 8
    assert profile.palette

    request = RenderRequest(
        character="test revenant",
        prompt="gothic pixel art, anatomical sketch structure, surreal dali stretch, goya shadows, bosch detail",
        animation=infer_animation_spec("run cycle"),
        canvas_size=48,
        upscale=1,
    )
    frames = render_frames(request, profile)
    assert len(frames) == 8

    out_path = tmp_path / "sheet.png"
    save_sheet(frames, out_path, 1)
    assert out_path.exists()
