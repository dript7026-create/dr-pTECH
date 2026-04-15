from __future__ import annotations

from dataclasses import replace
import io
import json
from argparse import Namespace
from pathlib import Path

from PIL import Image, ImageDraw

from jumpclip.analysis import synthesize_design_profile
from jumpclip.cli import command_bundle, command_bundle_batch, command_render
from jumpclip.designer import design_sprite_direction
from jumpclip.integration import stage_bundle_for_game
from jumpclip.models import ReferenceImage, RenderRequest
from jumpclip.render import _silhouette_archetype, apply_motion_overrides, infer_animation_spec, render_frames, save_sheet


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


def test_render_command_accepts_manifest_input(tmp_path: Path) -> None:
    ref_path = tmp_path / "ref.png"
    _make_reference(ref_path)
    manifest_path = tmp_path / "refs.json"
    manifest_path.write_text(
        json.dumps(
            {
                "references": [
                    {
                        "provider": "local",
                        "identifier": "ref",
                        "title": "Ref",
                        "local_path": str(ref_path),
                        "tags": ["pixel-art", "public-domain"],
                    }
                ],
                "count": 1,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    out_path = tmp_path / "sheet.png"
    args = Namespace(
        profile=str(manifest_path),
        character="manifest revenant",
        animation="run cycle",
        prompt="gothic pixel art, anatomical sketch structure",
        out=str(out_path),
        format="sheet",
        canvas_size=48,
        upscale=1,
        grid_size=8,
        download_dir="",
    )

    exit_code = command_render(args)

    assert exit_code == 0
    assert out_path.exists()


def test_render_command_accepts_remote_manifest_input(tmp_path: Path, monkeypatch) -> None:
    image = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((8, 4, 24, 28), fill=(190, 150, 110, 255))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    class FakeResponse:
        def __init__(self, content: bytes) -> None:
            self.content = content

        def raise_for_status(self) -> None:
            return None

    def fake_get(url: str, timeout: int) -> FakeResponse:
        assert url == "https://example.test/ref.png"
        assert timeout == 60
        return FakeResponse(buffer.getvalue())

    monkeypatch.setattr("jumpclip.analysis.requests.get", fake_get)

    manifest_path = tmp_path / "remote_refs.json"
    manifest_path.write_text(
        json.dumps(
            {
                "references": [
                    {
                        "provider": "openverse",
                        "identifier": "remote-ref",
                        "title": "Remote Ref",
                        "image_url": "https://example.test/ref.png",
                        "tags": ["pixel-art"],
                    }
                ],
                "count": 1,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    out_path = tmp_path / "remote_sheet.png"
    cache_dir = tmp_path / "cache"
    args = Namespace(
        profile=str(manifest_path),
        character="remote revenant",
        animation="jump arc",
        prompt="gothic pixel art courier",
        out=str(out_path),
        format="sheet",
        canvas_size=48,
        upscale=1,
        grid_size=8,
        download_dir=str(cache_dir),
    )

    exit_code = command_render(args)

    assert exit_code == 0
    assert out_path.exists()
    assert (cache_dir / "openverse_remote-ref.png").exists()


def test_bundle_command_emits_game_pipeline_metadata(tmp_path: Path) -> None:
    ref_path = tmp_path / "bundle_ref.png"
    _make_reference(ref_path)
    profile = synthesize_design_profile(
        [
            ReferenceImage(
                provider="local",
                identifier="bundle-ref",
                title="Bundle Ref",
                local_path=str(ref_path),
                tags=["pixel-art", "public-domain"],
            )
        ],
        grid_size=8,
    )
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(profile.to_dict(), indent=2), encoding="utf-8")
    pipeline_path = tmp_path / "pipeline.json"
    pipeline_path.write_text(
        json.dumps(
            {
                "pipeline_name": "test-engine",
                "engine": "unit-test",
                "target_frame_size": 48,
                "pixels_per_unit": 24,
                "frame_duration_ms": 70,
                "max_sheet_width": 96,
                "emit_preview_gif": True,
                "emit_frame_sequence": True,
                "emit_visual_regression": True,
                "emitters": ["generic", "unity", "godot", "aseprite"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / "bundle"
    args = Namespace(
        profile=str(profile_path),
        character="bundle revenant",
        animation="run cycle",
        prompt="gothic pixel art with anatomical sketch structure",
        out_dir=str(out_dir),
        pipeline=str(pipeline_path),
        canvas_size=None,
        upscale=None,
        grid_size=8,
        download_dir="",
    )

    exit_code = command_bundle(args)

    assert exit_code == 0
    metadata = json.loads((out_dir / "metadata.json").read_text(encoding="utf-8"))
    assert (out_dir / "atlas.png").exists()
    assert (out_dir / "profile.json").exists()
    assert (out_dir / "preview.gif").exists()
    assert (out_dir / "frames" / "frame_000.png").exists()
    assert (out_dir / "visual_regression.png").exists()
    assert (out_dir / "visual_regression.json").exists()
    assert (out_dir / "visual_regression.html").exists()
    assert (out_dir / "unity_import.json").exists()
    assert (out_dir / "godot_spriteframes.json").exists()
    assert (out_dir / "aseprite.json").exists()
    assert metadata["pipeline"]["pipeline_name"] == "test-engine"
    assert metadata["atlas"]["columns"] == 2
    assert metadata["animation"]["frame_count"] == 8
    assert metadata["frames"][0]["duration_ms"] == 70
    assert metadata["designer"]["style_family"] == "16bit"


def test_bundle_batch_command_exports_multiple_jobs(tmp_path: Path) -> None:
    ref_path = tmp_path / "batch_ref.png"
    _make_reference(ref_path)
    manifest_path = tmp_path / "refs.json"
    manifest_path.write_text(
        json.dumps(
            {
                "references": [
                    {
                        "provider": "local",
                        "identifier": "batch-ref",
                        "title": "Batch Ref",
                        "local_path": str(ref_path),
                        "tags": ["pixel-art", "public-domain"],
                    }
                ],
                "count": 1,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    batch_manifest_path = tmp_path / "bundle_batch.json"
    batch_manifest_path.write_text(
        json.dumps(
            {
                "profile": str(manifest_path),
                "jobs": [
                    {
                        "name": "run-cycle",
                        "character": "batch revenant",
                        "animation": "run cycle",
                        "prompt": "8bit gothic pixel hero with readable silhouette",
                        "grid_size": 8,
                    },
                    {
                        "name": "attack-combo",
                        "character": "batch revenant",
                        "animation": "attack combo",
                        "prompt": "cel-shaded 2.5d bitmap traced fighter with cosmetic fine detail",
                        "grid_size": 8,
                        "style_family": "cel-shaded-2.5d",
                        "texture_detail": 0.95,
                        "cel_shading": 1.0,
                        "outline_weight": 0.9,
                        "accessory_density": 0.78,
                        "tracing_bias": 0.86,
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    pipeline_path = tmp_path / "pipeline.json"
    pipeline_path.write_text(
        json.dumps(
            {
                "pipeline_name": "batch-engine",
                "emitters": ["generic", "unity"],
                "target_frame_size": 48,
                "max_sheet_width": 96,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / "batch_out"

    exit_code = command_bundle_batch(
        Namespace(
            batch_manifest=str(batch_manifest_path),
            out_dir=str(out_dir),
            pipeline=str(pipeline_path),
        )
    )

    assert exit_code == 0
    assert (out_dir / "run-cycle" / "atlas.png").exists()
    assert (out_dir / "run-cycle" / "unity_import.json").exists()
    assert (out_dir / "attack-combo" / "atlas.png").exists()
    attack_metadata = json.loads((out_dir / "attack-combo" / "metadata.json").read_text(encoding="utf-8"))
    assert attack_metadata["designer"]["style_family"] == "cel-shaded-2.5d"
    assert attack_metadata["designer"]["texture_detail"] == 0.95
    assert attack_metadata["designer"]["cel_shading"] == 1.0
    assert attack_metadata["designer"]["outline_weight"] == 0.9
    assert attack_metadata["designer"]["accessory_density"] == 0.78
    assert attack_metadata["designer"]["tracing_bias"] == 0.86


def test_designer_distinguishes_style_spectrum(tmp_path: Path) -> None:
    ref_path = tmp_path / "style_ref.png"
    _make_reference(ref_path)
    profile = synthesize_design_profile(
        [
            ReferenceImage(
                provider="local",
                identifier="style-ref",
                title="Style Ref",
                local_path=str(ref_path),
                tags=["pixel-art"],
            )
        ],
        grid_size=8,
    )

    eight_bit = design_sprite_direction("8bit gothic courier with readable silhouette", profile)
    cel = design_sprite_direction("cel-shaded 2.5d bitmap traced knight with cosmetic fine detail", profile)

    assert eight_bit.style_family == "8bit"
    assert eight_bit.palette_limit <= 12
    assert eight_bit.silhouette_emphasis > cel.silhouette_emphasis - 0.3
    assert cel.style_family == "bitmap-traced"
    assert cel.texture_detail > eight_bit.texture_detail
    assert cel.cel_shading > eight_bit.cel_shading


def test_named_art_preset_applies_expected_style_family(tmp_path: Path) -> None:
    ref_path = tmp_path / "preset_ref.png"
    _make_reference(ref_path)
    profile = synthesize_design_profile(
        [
            ReferenceImage(
                provider="local",
                identifier="preset-ref",
                title="Preset Ref",
                local_path=str(ref_path),
                tags=["pixel-art"],
            )
        ],
        grid_size=8,
    )

    directive = design_sprite_direction("clean courier", profile, overrides={"art_preset": "retro-arcade"})

    assert directive.art_preset == "retro-arcade"
    assert directive.style_family == "8bit"
    assert directive.palette_limit == 8
    assert directive.outline_weight == 1.8


def test_new_genre_presets_cover_space_shooter_and_soulslike(tmp_path: Path) -> None:
    ref_path = tmp_path / "genre_ref.png"
    _make_reference(ref_path)
    profile = synthesize_design_profile(
        [
            ReferenceImage(
                provider="local",
                identifier="genre-ref",
                title="Genre Ref",
                local_path=str(ref_path),
                tags=["pixel-art"],
            )
        ],
        grid_size=8,
    )

    shooter = design_sprite_direction("clean craft silhouette", profile, overrides={"art_preset": "space-shooter"})
    soulslike = design_sprite_direction("fallen knight duel", profile, overrides={"art_preset": "soulslike-action"})

    assert shooter.art_preset == "space-shooter"
    assert shooter.style_family == "16bit"
    assert shooter.palette_limit == 14
    assert soulslike.art_preset == "soulslike-action"
    assert soulslike.style_family == "bitmap-traced"
    assert soulslike.texture_detail > shooter.texture_detail


def test_bundle_command_respects_explicit_designer_overrides(tmp_path: Path) -> None:
    ref_path = tmp_path / "override_ref.png"
    _make_reference(ref_path)
    profile = synthesize_design_profile(
        [
            ReferenceImage(
                provider="local",
                identifier="override-ref",
                title="Override Ref",
                local_path=str(ref_path),
                tags=["pixel-art"],
            )
        ],
        grid_size=8,
    )
    profile_path = tmp_path / "override_profile.json"
    profile_path.write_text(json.dumps(profile.to_dict(), indent=2), encoding="utf-8")
    out_dir = tmp_path / "override_bundle"

    exit_code = command_bundle(
        Namespace(
            profile=str(profile_path),
            character="override revenant",
            animation="run cycle",
            prompt="8bit courier",
            out_dir=str(out_dir),
            pipeline="",
            canvas_size=48,
            upscale=1,
            grid_size=8,
            download_dir="",
            style_family="bitmap-traced",
            art_preset=None,
            silhouette_emphasis=1.9,
            texture_detail=0.88,
            palette_limit=28,
            cel_shading=0.7,
            outline_weight=1.7,
            accessory_density=0.66,
            tracing_bias=0.58,
            motion_silhouette_bias=None,
            motion_squash_stretch=None,
            motion_impact=None,
            motion_lift=None,
        )
    )

    assert exit_code == 0
    metadata = json.loads((out_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["designer"]["style_family"] == "bitmap-traced"
    assert metadata["designer"]["silhouette_emphasis"] == 1.9
    assert metadata["designer"]["texture_detail"] == 0.88
    assert metadata["designer"]["palette_limit"] == 28
    assert metadata["designer"]["cel_shading"] == 0.7
    assert metadata["designer"]["outline_weight"] == 1.7
    assert metadata["designer"]["accessory_density"] == 0.66
    assert metadata["designer"]["tracing_bias"] == 0.58


def test_motion_styling_overrides_change_frame_output(tmp_path: Path) -> None:
    ref_path = tmp_path / "motion_ref.png"
    _make_reference(ref_path)
    profile = synthesize_design_profile(
        [
            ReferenceImage(
                provider="local",
                identifier="motion-ref",
                title="Motion Ref",
                local_path=str(ref_path),
                tags=["pixel-art"],
            )
        ],
        grid_size=8,
    )
    base_spec = infer_animation_spec("attack combo")
    override_spec = apply_motion_overrides(
        base_spec,
        {"impact": 0.96, "squash_stretch": 0.3, "lift_scale": 1.2, "silhouette_bias": 1.35},
    )
    base_request = RenderRequest(
        character="motion revenant",
        prompt="duelist staging",
        animation=base_spec,
        canvas_size=48,
        upscale=1,
    )
    override_request = replace(
        base_request,
        animation=override_spec,
        motion_silhouette_bias=1.35,
        motion_squash_stretch=0.3,
        motion_impact=0.96,
        motion_lift=1.2,
    )

    base_frames = render_frames(base_request, profile)
    override_frames = render_frames(override_request, profile)

    assert base_frames[1].tobytes() != override_frames[1].tobytes()


def test_prompt_archetype_rendering_breaks_out_of_generic_oval(tmp_path: Path) -> None:
    ref_path = tmp_path / "archetype_ref.png"
    _make_reference(ref_path)
    profile = synthesize_design_profile(
        [
            ReferenceImage(
                provider="local",
                identifier="archetype-ref",
                title="Archetype Ref",
                local_path=str(ref_path),
                tags=["humanoid", "multi-leg", "ritual"],
            )
        ],
        grid_size=8,
    )
    base_request = RenderRequest(
        character="courier",
        prompt="clean courier silhouette",
        animation=infer_animation_spec("attack combo"),
        canvas_size=64,
        upscale=1,
    )
    lahgroid_request = RenderRequest(
        character="Lahgroid hierophant",
        prompt="soulslike-action Lahgroid boss, reptilian serpent feathered manticore humanoid in a robe, lantern on a chain, shoulder cannon, hovering drones, readable boss silhouette",
        animation=infer_animation_spec("attack combo"),
        canvas_size=64,
        upscale=1,
        art_preset="soulslike-action",
    )

    base_frame = render_frames(base_request, profile)[0]
    lahgroid_frame = render_frames(lahgroid_request, profile)[0]
    base_bbox = base_frame.getbbox()
    lahgroid_bbox = lahgroid_frame.getbbox()

    assert base_bbox is not None
    assert lahgroid_bbox is not None

    base_alpha = base_frame.getchannel("A")
    lahgroid_alpha = lahgroid_frame.getchannel("A")
    base_edge_pixels = 0
    edge_pixels = 0
    for x in list(range(0, 10)) + list(range(54, 64)):
        for y in range(14, 56):
            if base_alpha.getpixel((x, y)) > 0:
                base_edge_pixels += 1
            if lahgroid_alpha.getpixel((x, y)) > 0:
                edge_pixels += 1
    assert edge_pixels > base_edge_pixels + 20


def test_lahgroid_prompt_overrides_multi_leg_profile_tags(tmp_path: Path) -> None:
    ref_path = tmp_path / "lahgroid_ref.png"
    _make_reference(ref_path)
    profile = synthesize_design_profile(
        [
            ReferenceImage(
                provider="local",
                identifier="lahgroid-ref",
                title="Lahgroid Ref",
                local_path=str(ref_path),
                tags=["humanoid", "multi-leg", "ritual"],
            )
        ],
        grid_size=8,
    )

    archetype = _silhouette_archetype(
        "soulslike-action Lahgroid boss, reptilian serpent feathered manticore humanoid in a robe, lantern on a chain, shoulder cannon, hovering drones, readable boss silhouette",
        profile,
    )

    assert archetype == "lahgroid"


def test_batch_templates_expand_into_jobs(tmp_path: Path) -> None:
    ref_path = tmp_path / "template_ref.png"
    _make_reference(ref_path)
    manifest_path = tmp_path / "template_refs.json"
    manifest_path.write_text(
        json.dumps(
            {
                "references": [
                    {
                        "provider": "local",
                        "identifier": "template-ref",
                        "title": "Template Ref",
                        "local_path": str(ref_path),
                        "tags": ["pixel-art"],
                    }
                ],
                "count": 1,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    batch_manifest_path = tmp_path / "templated_batch.json"
    batch_manifest_path.write_text(
        json.dumps(
            {
                "profile": str(manifest_path),
                "design_templates": {
                    "shooter": {
                        "art_preset": "space-shooter",
                        "style_family": "16bit",
                        "palette_limit": 12,
                    }
                },
                "motion_templates": {
                    "strafe": {
                        "motion_silhouette_bias": 1.25,
                        "motion_lift": 0.6,
                    }
                },
                "jobs": [
                    {
                        "name": "templated-ship",
                        "character": "templated ship",
                        "animation": "run cycle",
                        "prompt": "space shooter craft",
                        "design_template": "shooter",
                        "motion_template": "strafe"
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / "templated_out"

    exit_code = command_bundle_batch(
        Namespace(
            batch_manifest=str(batch_manifest_path),
            out_dir=str(out_dir),
            pipeline="",
        )
    )

    assert exit_code == 0
    metadata = json.loads((out_dir / "templated-ship" / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["designer"]["art_preset"] == "space-shooter"
    assert metadata["designer"]["palette_limit"] == 12
    assert metadata["animation"]["lift_scale"] == 0.6


def test_stage_bundle_for_game_writes_link_manifest(tmp_path: Path) -> None:
    game_root = tmp_path / "game"
    game_root.mkdir()
    centerpiece = game_root / "src" / "main_scene.cpp"
    centerpiece.parent.mkdir(parents=True)
    centerpiece.write_text("// centerpiece\n", encoding="utf-8")

    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    (bundle_dir / "atlas.png").write_bytes(b"png")
    (bundle_dir / "profile.json").write_text("{}", encoding="utf-8")
    (bundle_dir / "metadata.json").write_text(
        json.dumps(
            {
                "animation": {"name": "run cycle"},
                "designer": {"style_family": "16bit"},
                "pipeline": {"pipeline_name": "test-pipeline"},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (bundle_dir / "unity_import.json").write_text("{}", encoding="utf-8")

    result = stage_bundle_for_game(game_root, centerpiece, bundle_dir)

    assert result["manifest_path"].exists()
    assert (result["staged_bundle_dir"] / "atlas.png").exists()
    manifest = json.loads(result["manifest_path"].read_text(encoding="utf-8"))
    assert manifest["centerpiece_source"] == "src\\main_scene.cpp"
    assert manifest["asset_bundle_dir"].startswith("JumpClipAssets")
    assert "unity_import.json" in manifest["engine_outputs"]


def test_learning_profile_biases_bundle_style_and_motion(tmp_path: Path) -> None:
    ref_path = tmp_path / "learning_ref.png"
    _make_reference(ref_path)
    profile = synthesize_design_profile(
        [
            ReferenceImage(
                provider="local",
                identifier="learning-ref",
                title="Learning Ref",
                local_path=str(ref_path),
                tags=["pixel-art"],
            )
        ],
        grid_size=8,
    )
    profile_path = tmp_path / "learning_profile_base.json"
    profile_path.write_text(json.dumps(profile.to_dict(), indent=2), encoding="utf-8")
    learning_path = tmp_path / "learning_style.json"
    learning_path.write_text(
        json.dumps(
            {
                "subject": "jumpclip-region-amber-delta",
                "godai": {"earth": 0.1, "water": 0.15, "fire": 0.2, "wind": 0.4, "void": 0.15},
                "style_signals": {
                    "style_family": "bitmap-traced",
                    "silhouette_emphasis": 1.62,
                    "texture_detail": 0.84,
                    "palette_limit": 30,
                    "outline_weight": 1.44,
                    "accessory_density": 0.63,
                    "tracing_bias": 0.74
                },
                "motion_signals": {
                    "motion_silhouette_bias": 1.33,
                    "motion_squash_stretch": 0.24,
                    "motion_impact": 0.68,
                    "motion_lift": 1.22,
                    "preferred_key_pose_tags": ["airborne_extension", "landing_catch"]
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / "learning_bundle"

    exit_code = command_bundle(
        Namespace(
            profile=str(profile_path),
            character="learning courier",
            animation="jump arc",
            prompt="clean courier silhouette",
            out_dir=str(out_dir),
            pipeline="",
            canvas_size=48,
            upscale=1,
            grid_size=8,
            download_dir="",
            style_family=None,
            art_preset=None,
            silhouette_emphasis=None,
            texture_detail=None,
            palette_limit=None,
            cel_shading=None,
            outline_weight=None,
            accessory_density=None,
            tracing_bias=None,
            motion_silhouette_bias=None,
            motion_squash_stretch=None,
            motion_impact=None,
            motion_lift=None,
            learning_profile=str(learning_path),
            learning_weight=1.0,
        )
    )

    assert exit_code == 0
    metadata = json.loads((out_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["designer"]["style_family"] == "bitmap-traced"
    assert metadata["designer"]["silhouette_emphasis"] == 1.62
    assert metadata["designer"]["texture_detail"] == 0.84
    assert metadata["designer"]["palette_limit"] == 30
    assert metadata["designer"]["outline_weight"] == 1.44
    assert metadata["designer"]["accessory_density"] == 0.63
    assert metadata["designer"]["tracing_bias"] == 0.74
    assert metadata["animation"]["silhouette_bias"] == 1.33
    assert metadata["animation"]["squash_stretch"] == 0.24
    assert metadata["animation"]["impact"] == 0.68
    assert metadata["animation"]["lift_scale"] > 1.22
    assert metadata["learning"]["subject"] == "jumpclip-region-amber-delta"
    assert metadata["learning"]["weight"] == 1.0
