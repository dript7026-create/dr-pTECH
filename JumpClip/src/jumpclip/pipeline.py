from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw

from .models import BundleJob, DesignProfile, GamePipelineConfig, RenderRequest
from .render import apply_motion_overrides, infer_animation_spec, load_profile_input, render_frames, resolve_render_plan, save_gif, save_sequence, save_sheet, sheet_layout


def load_pipeline_config(path: Path | None) -> GamePipelineConfig:
    if path is None:
        return GamePipelineConfig()
    payload = json.loads(path.read_text(encoding="utf-8"))
    return GamePipelineConfig(**payload)


def resolve_render_scale(config: GamePipelineConfig, requested_canvas_size: int | None = None, requested_upscale: int | None = None) -> tuple[int, int]:
    canvas_size = requested_canvas_size or max(32, min(128, config.target_frame_size))
    upscale = requested_upscale or max(1, config.target_frame_size // max(1, canvas_size))
    if canvas_size * upscale < config.target_frame_size:
        upscale = max(1, -(-config.target_frame_size // canvas_size))
    return canvas_size, upscale


def build_bundle_metadata(
    config: GamePipelineConfig,
    request: RenderRequest,
    profile: DesignProfile,
    frame_size: tuple[int, int],
    atlas_path: Path,
    columns: int,
) -> dict:
    frame_width, frame_height = frame_size
    layout = sheet_layout(request.animation.frame_count, frame_width, frame_height, columns=columns)
    animation, directive, learning = resolve_render_plan(request, profile)
    frames = []
    for index in range(animation.frame_count):
        frames.append(
            {
                "index": index,
                "x": (index % layout["columns"]) * frame_width,
                "y": (index // layout["columns"]) * frame_height,
                "width": frame_width,
                "height": frame_height,
                "duration_ms": config.frame_duration_ms,
            }
        )
    return {
        "pipeline": config.to_dict(),
        "character": request.character,
        "prompt": request.prompt,
        "animation": {
            "name": animation.name,
            "motion": animation.motion,
            "frame_count": animation.frame_count,
            "silhouette_bias": animation.silhouette_bias,
            "squash_stretch": animation.squash_stretch,
            "impact": animation.impact,
            "lift_scale": animation.lift_scale,
        },
        "atlas": {
            "path": atlas_path.name,
            "width": layout["sheet_width"],
            "height": layout["sheet_height"],
            "columns": layout["columns"],
            "rows": layout["rows"],
            "frame_width": frame_width,
            "frame_height": frame_height,
        },
        "frames": frames,
        "pivot": {"x": config.pivot_x, "y": config.pivot_y},
        "pixels_per_unit": config.pixels_per_unit,
        "profile": {
            "grid_size": profile.grid_size,
            "palette": profile.palette,
            "providers": profile.providers,
            "tags": profile.tags,
            "source_count": profile.source_count,
        },
        "designer": directive.to_dict(),
        "learning": learning,
        "render": {
            "canvas_size": request.canvas_size,
            "upscale": request.upscale,
        },
    }


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned or "bundle"


def _unity_metadata(metadata: dict) -> dict:
    return {
        "texture": metadata["atlas"]["path"],
        "pixelsPerUnit": metadata["pixels_per_unit"],
        "sprites": [
            {
                "name": f"{metadata['character']}_{metadata['animation']['name']}_{frame['index']:03d}",
                "rect": {
                    "x": frame["x"],
                    "y": frame["y"],
                    "width": frame["width"],
                    "height": frame["height"],
                },
                "pivot": metadata["pivot"],
                "border": {"left": 0, "right": 0, "top": 0, "bottom": 0},
            }
            for frame in metadata["frames"]
        ],
    }


def _godot_metadata(metadata: dict) -> dict:
    animation_name = _slugify(metadata["animation"]["name"])
    return {
        "resource_type": "SpriteFrames",
        "animations": {
            animation_name: {
                "speed_fps": max(1, round(1000 / max(1, metadata["frames"][0]["duration_ms"]))),
                "loop": True,
                "frames": [
                    {
                        "atlas": metadata["atlas"]["path"],
                        "region": {
                            "x": frame["x"],
                            "y": frame["y"],
                            "width": frame["width"],
                            "height": frame["height"],
                        },
                        "duration_ms": frame["duration_ms"],
                    }
                    for frame in metadata["frames"]
                ],
            }
        },
    }


def _aseprite_metadata(metadata: dict) -> dict:
    return {
        "frames": {
            f"{_slugify(metadata['character'])}_{frame['index']:03d}.png": {
                "frame": {"x": frame["x"], "y": frame["y"], "w": frame["width"], "h": frame["height"]},
                "rotated": False,
                "trimmed": False,
                "spriteSourceSize": {"x": 0, "y": 0, "w": frame["width"], "h": frame["height"]},
                "sourceSize": {"w": frame["width"], "h": frame["height"]},
                "duration": frame["duration_ms"],
            }
            for frame in metadata["frames"]
        },
        "meta": {
            "app": "jumpclip",
            "image": metadata["atlas"]["path"],
            "size": {"w": metadata["atlas"]["width"], "h": metadata["atlas"]["height"]},
            "scale": "1",
        },
    }


def emit_engine_metadata(out_dir: Path, metadata: dict, emitters: list[str]) -> dict[str, Path]:
    outputs: dict[str, Path] = {}
    normalized = [emitter.lower() for emitter in emitters]
    if any(emitter in {"unity", "unity-json"} for emitter in normalized):
        path = out_dir / "unity_import.json"
        path.write_text(json.dumps(_unity_metadata(metadata), indent=2), encoding="utf-8")
        outputs["unity"] = path
    if any(emitter in {"godot", "godot-json"} for emitter in normalized):
        path = out_dir / "godot_spriteframes.json"
        path.write_text(json.dumps(_godot_metadata(metadata), indent=2), encoding="utf-8")
        outputs["godot"] = path
    if any(emitter in {"aseprite", "aseprite-json"} for emitter in normalized):
        path = out_dir / "aseprite.json"
        path.write_text(json.dumps(_aseprite_metadata(metadata), indent=2), encoding="utf-8")
        outputs["aseprite"] = path
    return outputs


def emit_visual_regression_outputs(
    out_dir: Path,
    frames: list,
    request: RenderRequest,
    metadata: dict,
    columns: int,
) -> dict[str, Path]:
    preview_scale = max(2, request.upscale)
    preview_frames = [frame.resize((frame.width * preview_scale, frame.height * preview_scale), Image.Resampling.NEAREST) for frame in frames]
    cell_w = preview_frames[0].width + 8
    cell_h = preview_frames[0].height + 18
    rows = max(1, -(-len(preview_frames) // max(1, columns)))
    canvas = Image.new("RGBA", (cell_w * columns, cell_h * rows), (244, 240, 232, 255))
    draw = ImageDraw.Draw(canvas)
    frame_hashes = []
    for index, frame in enumerate(preview_frames):
        x = (index % columns) * cell_w
        y = (index // columns) * cell_h
        canvas.paste(frame, (x + 4, y + 14), frame)
        draw.text((x + 4, y + 2), f"F{index:02d}", fill=(32, 28, 26, 255))
        bbox = frames[index].getbbox()
        frame_hashes.append(
            {
                "index": index,
                "sha1": hashlib.sha1(frames[index].tobytes()).hexdigest(),
                "bbox": list(bbox) if bbox else None,
            }
        )

    image_path = out_dir / "visual_regression.png"
    manifest_path = out_dir / "visual_regression.json"
    html_path = out_dir / "visual_regression.html"
    canvas.save(image_path)
    regression_payload = {
        "character": request.character,
        "animation": metadata["animation"],
        "designer": metadata["designer"],
        "frame_hashes": frame_hashes,
    }
    manifest_path.write_text(json.dumps(regression_payload, indent=2), encoding="utf-8")
    html_path.write_text(
        """<!doctype html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\">
    <title>JumpClip Regression Viewer</title>
    <style>
        body { font-family: Georgia, serif; background: #f4f0e8; color: #201c1a; margin: 24px; }
        .hero { display: grid; grid-template-columns: 1.2fr 1fr; gap: 24px; align-items: start; }
        .card { background: rgba(255,255,255,0.72); border: 1px solid rgba(32,28,26,0.14); padding: 16px; }
        img { width: 100%; image-rendering: pixelated; background: #fff; border: 1px solid rgba(32,28,26,0.1); }
        table { width: 100%; border-collapse: collapse; font-size: 14px; }
        th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid rgba(32,28,26,0.12); }
        code { font-family: Consolas, monospace; }
    </style>
</head>
<body>
    <h1>JumpClip Regression Viewer</h1>
    <div class=\"hero\">
        <div class=\"card\">
            <img src=\"visual_regression.png\" alt=\"Visual regression contact sheet\">
        </div>
        <div class=\"card\">
            <h2>Bundle</h2>
            <p><strong>Character:</strong> __CHARACTER__</p>
            <p><strong>Animation:</strong> __ANIMATION__</p>
            <p><strong>Preset:</strong> __PRESET__</p>
            <p><strong>Style Family:</strong> __STYLE__</p>
            <p><strong>Prompt:</strong> __PROMPT__</p>
            <p><strong>Atlas:</strong> <code>__ATLAS__</code></p>
        </div>
    </div>
    <div class=\"card\" style=\"margin-top: 24px;\">
        <h2>Frame Hashes</h2>
        <table>
            <thead><tr><th>Frame</th><th>SHA1</th><th>Bounding Box</th></tr></thead>
            <tbody>
__ROWS__
            </tbody>
        </table>
    </div>
</body>
</html>
""".replace("__CHARACTER__", request.character)
        .replace("__ANIMATION__", metadata["animation"]["name"])
        .replace("__PRESET__", str(metadata["designer"].get("art_preset") or "none"))
        .replace("__STYLE__", metadata["designer"]["style_family"])
        .replace("__PROMPT__", request.prompt)
        .replace("__ATLAS__", metadata["atlas"]["path"])
        .replace(
            "__ROWS__",
            "\n".join(
                f"        <tr><td>{item['index']:02d}</td><td><code>{item['sha1']}</code></td><td><code>{item['bbox']}</code></td></tr>"
                for item in frame_hashes
            ),
        ),
        encoding="utf-8",
    )
    return {
        "visual_regression_image": image_path,
        "visual_regression_manifest": manifest_path,
        "visual_regression_viewer": html_path,
    }


def load_bundle_jobs(path: Path) -> tuple[str | None, list[BundleJob]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    shared_profile = payload.get("profile")
    design_templates = payload.get("design_templates", {})
    motion_templates = payload.get("motion_templates", {})
    jobs = []
    for item in payload.get("jobs", []):
        design_template_name = item.get("design_template")
        motion_template_name = item.get("motion_template")
        merged = {}
        if design_template_name:
            merged.update(design_templates.get(design_template_name, {}))
        if motion_template_name:
            merged.update(motion_templates.get(motion_template_name, {}))
        merged.update(item)
        jobs.append(BundleJob(**merged))
    if not jobs:
        raise ValueError("Batch manifest must include at least one job")
    return shared_profile, jobs


def export_game_bundle(
    request: RenderRequest,
    profile: DesignProfile,
    config: GamePipelineConfig,
    frames: list,
    out_dir: Path,
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    frame_width = frames[0].width * request.upscale
    frame_height = frames[0].height * request.upscale
    columns = max(1, min(len(frames), config.max_sheet_width // max(1, frame_width)))
    atlas_path = out_dir / "atlas.png"
    metadata_path = out_dir / "metadata.json"
    profile_path = out_dir / "profile.json"

    save_sheet(frames, atlas_path, request.upscale, columns=columns)
    profile_path.write_text(json.dumps(profile.to_dict(), indent=2), encoding="utf-8")

    outputs = {
        "atlas": atlas_path,
        "profile": profile_path,
        "metadata": metadata_path,
    }

    if config.emit_preview_gif:
        preview_path = out_dir / "preview.gif"
        save_gif(frames, preview_path, request.upscale, duration_ms=config.frame_duration_ms)
        outputs["preview_gif"] = preview_path

    if config.emit_frame_sequence:
        sequence_path = out_dir / "frames"
        save_sequence(frames, sequence_path, request.upscale)
        outputs["frame_sequence"] = sequence_path

    metadata = build_bundle_metadata(config, request, profile, (frame_width, frame_height), atlas_path, columns)
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    if config.emit_visual_regression:
        outputs.update(emit_visual_regression_outputs(out_dir, frames, request, metadata, max(1, config.visual_regression_columns)))
    outputs.update(emit_engine_metadata(out_dir, metadata, config.emitters))
    return {
        "bundle_dir": out_dir,
        "metadata": metadata,
        "outputs": outputs,
    }


def build_batch_bundles(
    jobs: list[BundleJob],
    shared_profile: str | None,
    config: GamePipelineConfig,
    out_dir: Path,
) -> list[dict]:
    results = []
    for job in jobs:
        profile_source = Path(job.profile or shared_profile or "")
        if not str(profile_source):
            raise ValueError(f"Job '{job.name}' does not specify a profile or manifest path")
        profile = load_profile_input(
            profile_source,
            grid_size=job.grid_size or 12,
            download_dir=Path(job.download_dir) if job.download_dir else None,
        )
        canvas_size, upscale = resolve_render_scale(config, requested_canvas_size=job.canvas_size, requested_upscale=job.upscale)
        request = RenderRequest(
            character=job.character,
            prompt=job.prompt,
            animation=apply_motion_overrides(
                infer_animation_spec(job.animation),
                {
                    "silhouette_bias": job.motion_silhouette_bias,
                    "squash_stretch": job.motion_squash_stretch,
                    "impact": job.motion_impact,
                    "lift_scale": job.motion_lift,
                },
            ),
            canvas_size=canvas_size,
            upscale=upscale,
            output_path=out_dir / _slugify(job.name),
            art_preset=job.art_preset,
            style_family=job.style_family,
            silhouette_emphasis=job.silhouette_emphasis,
            texture_detail=job.texture_detail,
            palette_limit=job.palette_limit,
            cel_shading=job.cel_shading,
            outline_weight=job.outline_weight,
            accessory_density=job.accessory_density,
            tracing_bias=job.tracing_bias,
            motion_silhouette_bias=job.motion_silhouette_bias,
            motion_squash_stretch=job.motion_squash_stretch,
            motion_impact=job.motion_impact,
            motion_lift=job.motion_lift,
            learning_profile=job.learning_profile,
            learning_weight=job.learning_weight,
        )
        frames = render_frames(request, profile)
        results.append(export_game_bundle(request, profile, config, frames, out_dir / _slugify(job.name)))
    return results