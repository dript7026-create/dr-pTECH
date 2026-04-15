from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = ROOT.parent
JUMPCLIP_SRC = WORKSPACE_ROOT / "JumpClip" / "src"
if str(JUMPCLIP_SRC) not in sys.path:
    sys.path.insert(0, str(JUMPCLIP_SRC))

from jumpclip.integration import stage_bundle_for_game  # noqa: E402
from jumpclip.pipeline import build_batch_bundles, load_bundle_jobs  # noqa: E402
from jumpclip.models import RenderRequest  # noqa: E402
from jumpclip.pipeline import export_game_bundle, load_pipeline_config, resolve_render_scale  # noqa: E402
from jumpclip.render import apply_motion_overrides, infer_animation_spec, load_profile_input, render_frames  # noqa: E402

ASSET_DIR = ROOT / "assets" / "generated"
LINK_MANIFEST = ROOT / "jumpclip_pipeline_link.json"
DEFAULT_BUNDLE_ROOT = ROOT / "assets" / "jumpclip_bundles"
DEFAULT_PIPELINE = WORKSPACE_ROOT / "JumpClip" / "examples" / "game_pipeline.json"
DEFAULT_PROFILE = ROOT / "examples" / "xenobloods_jumpclip_references.json"
DEFAULT_PREVIEW_ROSTER = ROOT / "examples" / "xenobloods_preview_roster.json"
DEFAULT_ACTIVE_PREVIEW = "lahgroid-boss-preview"
DEFAULT_CENTERPIECE = ROOT / "src" / "prototype_shell.py"


def load_link_manifest(path: Path = LINK_MANIFEST) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def prepare_profile_source(path: Path, working_dir: Path) -> Path:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "references" not in payload:
        return path
    resolved_payload = {**payload}
    resolved_references = []
    for item in payload.get("references", []):
        resolved = dict(item)
        local_path = resolved.get("local_path")
        if local_path:
            local = Path(local_path)
            if not local.is_absolute():
                manifest_relative = (path.parent / local).resolve()
                project_relative = (path.parents[1] / local).resolve() if len(path.parents) > 1 else manifest_relative
                if manifest_relative.exists():
                    resolved["local_path"] = str(manifest_relative)
                else:
                    resolved["local_path"] = str(project_relative)
        resolved_references.append(resolved)
    resolved_payload["references"] = resolved_references
    target = working_dir / f"resolved_{path.name}"
    target.write_text(json.dumps(resolved_payload, indent=2), encoding="utf-8")
    return target


def _resolve_manifest_local_path(path: Path, candidate: str) -> str:
    local = Path(candidate)
    if local.is_absolute():
        return str(local)
    manifest_relative = (path.parent / local).resolve()
    project_relative = (path.parents[1] / local).resolve() if len(path.parents) > 1 else manifest_relative
    if manifest_relative.exists():
        return str(manifest_relative)
    return str(project_relative)


def prepare_preview_roster_source(path: Path, working_dir: Path) -> Path:
    working_dir.mkdir(parents=True, exist_ok=True)
    payload = json.loads(path.read_text(encoding="utf-8"))
    resolved_payload = {**payload}
    shared_profile = payload.get("profile")
    if shared_profile:
        shared_profile_path = Path(_resolve_manifest_local_path(path, shared_profile))
        resolved_payload["profile"] = str(prepare_profile_source(shared_profile_path, working_dir))

    resolved_jobs = []
    for item in payload.get("jobs", []):
        resolved = dict(item)
        if resolved.get("profile"):
            job_profile_path = Path(_resolve_manifest_local_path(path, resolved["profile"]))
            resolved["profile"] = str(prepare_profile_source(job_profile_path, working_dir))
        if resolved.get("learning_profile"):
            resolved["learning_profile"] = _resolve_manifest_local_path(path, resolved["learning_profile"])
        resolved_jobs.append(resolved)
    resolved_payload["jobs"] = resolved_jobs

    target = working_dir / f"resolved_{path.name}"
    target.write_text(json.dumps(resolved_payload, indent=2), encoding="utf-8")
    return target


def write_preview_roster_summary(summary_path: Path, active_preview: str, staged_previews: list[dict]) -> Path:
    summary_path.write_text(
        json.dumps(
            {
                "active_preview": active_preview,
                "previews": staged_previews,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return summary_path


def resolve_linked_paths(manifest: dict) -> dict[str, Path]:
    game_root = Path(manifest["game_root"])
    return {
        "bundle_dir": game_root / manifest["asset_bundle_dir"],
        "atlas": game_root / manifest["atlas"],
        "metadata": game_root / manifest["metadata"],
        "profile": game_root / manifest["profile"],
    }


def _select_preview_frame_region(atlas: Image.Image, frames: list[dict]) -> tuple[int, int, int, int]:
    best_region = (0, 0, atlas.width, atlas.height)
    best_score = -1
    for frame in frames or [{}]:
        x = int(frame.get("x", 0))
        y = int(frame.get("y", 0))
        width = int(frame.get("width", atlas.width))
        height = int(frame.get("height", atlas.height))
        sprite = atlas.crop((x, y, x + width, y + height))
        bbox = sprite.getbbox()
        if bbox is None:
            score = 0
        else:
            bbox_width = bbox[2] - bbox[0]
            bbox_height = bbox[3] - bbox[1]
            alpha = sprite.getchannel("A")
            histogram = alpha.histogram()
            solid_pixels = sum(histogram[1:])
            score = (bbox_width * bbox_height) + solid_pixels
        if score > best_score:
            best_score = score
            best_region = (x, y, width, height)
    return best_region


def sync_runtime_assets_from_link(path: Path = LINK_MANIFEST) -> dict[str, Path] | None:
    manifest = load_link_manifest(path)
    if manifest is None:
        return None
    resolved = resolve_linked_paths(manifest)
    if not resolved["atlas"].exists() or not resolved["metadata"].exists():
        return None

    metadata = json.loads(resolved["metadata"].read_text(encoding="utf-8"))
    atlas = Image.open(resolved["atlas"]).convert("RGBA")
    x, y, width, height = _select_preview_frame_region(atlas, metadata.get("frames", []))
    sprite = atlas.crop((x, y, x + width, y + height))

    runtime_dir = ASSET_DIR / "jumpclip_runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    sprite_path = runtime_dir / "linked_sprite_preview.png"
    atlas_preview_path = runtime_dir / "linked_atlas_preview.png"
    sprite.resize((sprite.width * 4, sprite.height * 4), Image.Resampling.NEAREST).save(sprite_path)
    atlas.save(atlas_preview_path)

    visual_regression = resolved["bundle_dir"] / "visual_regression.png"
    regression_target = runtime_dir / "visual_regression.png"
    if visual_regression.exists():
        Image.open(visual_regression).save(regression_target)

    return {
        "runtime_dir": runtime_dir,
        "sprite_preview": sprite_path,
        "atlas_preview": atlas_preview_path,
        "visual_regression": regression_target if regression_target.exists() else atlas_preview_path,
    }


def load_serviced_preview_assets(runtime_dir: Path | None = None) -> dict[str, dict[str, Path | str | bool]]:
    runtime_dir = runtime_dir or (ASSET_DIR / "jumpclip_runtime")
    summary_path = runtime_dir / "asset_service_summary.json"
    if not summary_path.exists():
        return {}

    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    previews: dict[str, dict[str, Path | str | bool]] = {}
    for record in payload.get("previews", []):
        files = record.get("files", {})
        preview = {
            "name": record.get("name", ""),
            "character": record.get("character", ""),
            "ready": bool(record.get("ready", False)),
        }
        for key, value in files.items():
            preview[key] = Path(value) if value else None
        name = str(record.get("name", ""))
        if name:
            previews[name] = preview
    return previews


def service_preview_assets(staged_previews: list[dict], runtime_dir: Path | None = None) -> dict:
    runtime_dir = runtime_dir or (ASSET_DIR / "jumpclip_runtime")
    runtime_dir.mkdir(parents=True, exist_ok=True)
    preview_root = runtime_dir / "previews"
    preview_root.mkdir(parents=True, exist_ok=True)

    required_names = {
        "atlas": "atlas.png",
        "metadata": "metadata.json",
        "profile": "profile.json",
        "preview_gif": "preview.gif",
        "visual_regression": "visual_regression.png",
    }
    summary: list[dict] = []

    for preview in staged_previews:
        staged_bundle_dir = Path(preview["staged_bundle_dir"])
        preview_dir = preview_root / preview["name"]
        preview_dir.mkdir(parents=True, exist_ok=True)

        record = {
            "name": preview["name"],
            "character": preview["character"],
            "staged_bundle_dir": str(staged_bundle_dir),
            "manifest_path": preview["manifest_path"],
            "ready": True,
            "files": {},
        }

        for key, filename in required_names.items():
            source = staged_bundle_dir / filename
            exists = source.exists()
            record["files"][key] = str(source) if exists else None
            record["ready"] = record["ready"] and exists
            if exists and key in {"atlas", "preview_gif", "visual_regression"}:
                target = preview_dir / filename
                if key == "atlas":
                    Image.open(source).save(target)
                else:
                    target.write_bytes(source.read_bytes())

        if record["ready"]:
            atlas = Image.open(staged_bundle_dir / "atlas.png").convert("RGBA")
            metadata = json.loads((staged_bundle_dir / "metadata.json").read_text(encoding="utf-8"))
            x, y, width, height = _select_preview_frame_region(atlas, metadata.get("frames", []))
            sprite = atlas.crop((x, y, x + width, y + height))
            sprite_path = preview_dir / "sprite_preview.png"
            sprite.resize((sprite.width * 4, sprite.height * 4), Image.Resampling.NEAREST).save(sprite_path)
            record["files"]["sprite_preview"] = str(sprite_path)
        else:
            record["files"]["sprite_preview"] = None

        summary.append(record)

    summary_path = runtime_dir / "asset_service_summary.json"
    summary_path.write_text(json.dumps({"previews": summary}, indent=2), encoding="utf-8")
    return {"runtime_dir": runtime_dir, "summary_path": summary_path, "previews": summary}


def build_and_stage_xenobloods_preview_bundle(
    profile_path: Path = DEFAULT_PROFILE,
    pipeline_path: Path = DEFAULT_PIPELINE,
    character: str = "Ishtasha, botanical spider scout",
    animation: str = "run cycle",
    prompt: str = "soulslike-action humanoid botanical spider scout with ritual hood, vine-grown secondary limbs, readable silhouette, and thorn-seam stitch detail",
    art_preset: str = "soulslike-action",
    output_dir: Path | None = None,
) -> dict:
    pipeline = load_pipeline_config(pipeline_path)
    output_dir = output_dir or (DEFAULT_BUNDLE_ROOT / "xenobloods_landborne_preview")
    output_dir.mkdir(parents=True, exist_ok=True)
    resolved_profile_source = prepare_profile_source(profile_path, output_dir)
    profile = load_profile_input(resolved_profile_source, grid_size=12)

    motion = apply_motion_overrides(
        infer_animation_spec(animation),
        {"impact": 0.88, "squash_stretch": 0.22, "lift_scale": 1.08},
    )
    canvas_size, upscale = resolve_render_scale(pipeline)
    request = RenderRequest(
        character=character,
        prompt=prompt,
        animation=motion,
        canvas_size=canvas_size,
        upscale=upscale,
        output_path=output_dir,
        art_preset=art_preset,
        silhouette_emphasis=1.28,
        texture_detail=0.78,
        outline_weight=1.06,
        accessory_density=0.68,
        tracing_bias=0.8,
        motion_impact=0.88,
        motion_squash_stretch=0.22,
        motion_lift=1.08,
    )
    frames = render_frames(request, profile)
    bundle = export_game_bundle(request, profile, pipeline, frames, output_dir)
    staging = stage_bundle_for_game(ROOT, DEFAULT_CENTERPIECE, output_dir, assets_subdir="JumpClipAssets")
    runtime = sync_runtime_assets_from_link(staging["manifest_path"])
    return {
        "bundle": bundle,
        "staging": staging,
        "runtime": runtime,
    }


def build_and_stage_xenobloods_preview_set(
    roster_path: Path = DEFAULT_PREVIEW_ROSTER,
    pipeline_path: Path = DEFAULT_PIPELINE,
    active_preview: str = DEFAULT_ACTIVE_PREVIEW,
    output_dir: Path | None = None,
) -> dict:
    pipeline = load_pipeline_config(pipeline_path)
    output_dir = output_dir or (DEFAULT_BUNDLE_ROOT / "xenobloods_preview_set")
    output_dir.mkdir(parents=True, exist_ok=True)

    resolved_roster = prepare_preview_roster_source(roster_path, output_dir)
    shared_profile, jobs = load_bundle_jobs(resolved_roster)
    bundle_results = build_batch_bundles(jobs, shared_profile, pipeline, output_dir)

    staged_previews = []
    active_manifest_path: Path | None = None
    active_bundle_dir: Path | None = None
    for job, bundle in zip(jobs, bundle_results):
        manifest_name = "jumpclip_pipeline_link.json"
        if job.name != active_preview:
            manifest_name = f"jumpclip_pipeline_link_{job.name}.json"
        staging = stage_bundle_for_game(
            ROOT,
            DEFAULT_CENTERPIECE,
            bundle["bundle_dir"],
            assets_subdir="JumpClipAssets",
            manifest_name=manifest_name,
        )
        preview_record = {
            "name": job.name,
            "character": job.character,
            "bundle_dir": str(bundle["bundle_dir"]),
            "staged_bundle_dir": str(staging["staged_bundle_dir"]),
            "manifest_path": str(staging["manifest_path"]),
        }
        staged_previews.append(preview_record)
        if job.name == active_preview:
            active_manifest_path = staging["manifest_path"]
            active_bundle_dir = bundle["bundle_dir"]

    if active_manifest_path is None or active_bundle_dir is None:
        raise ValueError(f"Active preview '{active_preview}' was not found in {roster_path}")

    runtime = sync_runtime_assets_from_link(active_manifest_path)
    asset_service = service_preview_assets(staged_previews)
    summary_path = write_preview_roster_summary(ROOT / "jumpclip_preview_roster.json", active_preview, staged_previews)
    return {
        "active_preview": active_preview,
        "active_manifest": active_manifest_path,
        "active_bundle_dir": active_bundle_dir,
        "runtime": runtime,
        "asset_service": asset_service,
        "bundles": bundle_results,
        "staged_previews": staged_previews,
        "summary_path": summary_path,
    }
