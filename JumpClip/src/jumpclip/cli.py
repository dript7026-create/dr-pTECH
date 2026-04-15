from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analysis import synthesize_design_profile
from .models import RenderRequest
from .pipeline import build_batch_bundles, export_game_bundle, load_bundle_jobs, load_pipeline_config, resolve_render_scale
from .reference_sources import load_manifest, search_openverse, search_wikimedia, write_manifest
from .render import apply_motion_overrides, infer_animation_spec, load_profile_input, render_frames, save_gif, save_sequence, save_sheet


def _apply_design_args(args: argparse.Namespace) -> dict:
    return {
        "art_preset": getattr(args, "art_preset", None),
        "style_family": getattr(args, "style_family", None),
        "silhouette_emphasis": getattr(args, "silhouette_emphasis", None),
        "texture_detail": getattr(args, "texture_detail", None),
        "palette_limit": getattr(args, "palette_limit", None),
        "cel_shading": getattr(args, "cel_shading", None),
        "outline_weight": getattr(args, "outline_weight", None),
        "accessory_density": getattr(args, "accessory_density", None),
        "tracing_bias": getattr(args, "tracing_bias", None),
    }


def _apply_motion_args(args: argparse.Namespace) -> dict:
    return {
        "silhouette_bias": getattr(args, "motion_silhouette_bias", None),
        "squash_stretch": getattr(args, "motion_squash_stretch", None),
        "impact": getattr(args, "motion_impact", None),
        "lift_scale": getattr(args, "motion_lift", None),
    }


def command_collect(args: argparse.Namespace) -> int:
    if args.provider == "openverse":
        references = search_openverse(args.query, args.limit)
    else:
        references = search_wikimedia(args.query, args.limit)
    out_path = write_manifest(references, Path(args.out))
    print(json.dumps({"manifest": str(out_path), "count": len(references), "provider": args.provider}, indent=2))
    return 0


def command_analyze(args: argparse.Namespace) -> int:
    references = load_manifest(Path(args.manifest))
    profile = synthesize_design_profile(references, grid_size=args.grid_size, download_dir=Path(args.download_dir) if args.download_dir else None)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(profile.to_dict(), indent=2), encoding="utf-8")
    print(json.dumps({"profile": str(out_path), "sources": profile.source_count, "providers": profile.providers}, indent=2))
    return 0


def command_render(args: argparse.Namespace) -> int:
    profile = load_profile_input(
        Path(args.profile),
        grid_size=args.grid_size,
        download_dir=Path(args.download_dir) if args.download_dir else None,
    )
    animation = infer_animation_spec(args.animation)
    animation = apply_motion_overrides(animation, _apply_motion_args(args))
    request = RenderRequest(
        character=args.character,
        prompt=args.prompt,
        animation=animation,
        canvas_size=args.canvas_size,
        upscale=args.upscale,
        output_path=Path(args.out),
        learning_profile=getattr(args, "learning_profile", None) or None,
        learning_weight=getattr(args, "learning_weight", None),
        **_apply_design_args(args),
    )
    frames = render_frames(request, profile)
    output = Path(args.out)
    if args.format == "sheet":
        save_sheet(frames, output, args.upscale)
    elif args.format == "sequence":
        save_sequence(frames, output, args.upscale)
    else:
        save_gif(frames, output, args.upscale)
    print(json.dumps({
        "out": str(output),
        "format": args.format,
        "frame_count": animation.frame_count,
        "character": args.character,
        "animation": args.animation,
    }, indent=2))
    return 0


def command_bundle(args: argparse.Namespace) -> int:
    profile = load_profile_input(
        Path(args.profile),
        grid_size=args.grid_size,
        download_dir=Path(args.download_dir) if args.download_dir else None,
    )
    config = load_pipeline_config(Path(args.pipeline)) if args.pipeline else load_pipeline_config(None)
    animation = infer_animation_spec(args.animation)
    animation = apply_motion_overrides(animation, _apply_motion_args(args))
    canvas_size, upscale = resolve_render_scale(
        config,
        requested_canvas_size=args.canvas_size,
        requested_upscale=args.upscale,
    )
    request = RenderRequest(
        character=args.character,
        prompt=args.prompt,
        animation=animation,
        canvas_size=canvas_size,
        upscale=upscale,
        output_path=Path(args.out_dir),
        learning_profile=getattr(args, "learning_profile", None) or None,
        learning_weight=getattr(args, "learning_weight", None),
        **_apply_design_args(args),
    )
    frames = render_frames(request, profile)
    bundle = export_game_bundle(request, profile, config, frames, Path(args.out_dir))
    print(json.dumps({
        "bundle_dir": str(bundle["bundle_dir"]),
        "atlas": str(bundle["outputs"]["atlas"]),
        "metadata": str(bundle["outputs"]["metadata"]),
        "profile": str(bundle["outputs"]["profile"]),
        "engine_outputs": {key: str(value) for key, value in bundle["outputs"].items() if key not in {"atlas", "metadata", "profile", "preview_gif", "frame_sequence"}},
        "frame_count": animation.frame_count,
        "frame_size": bundle["metadata"]["atlas"]["frame_width"],
        "pipeline": config.pipeline_name,
    }, indent=2))
    return 0


def command_bundle_batch(args: argparse.Namespace) -> int:
    config = load_pipeline_config(Path(args.pipeline)) if args.pipeline else load_pipeline_config(None)
    shared_profile, jobs = load_bundle_jobs(Path(args.batch_manifest))
    results = build_batch_bundles(jobs, shared_profile, config, Path(args.out_dir))
    print(json.dumps({
        "bundle_count": len(results),
        "out_dir": args.out_dir,
        "pipeline": config.pipeline_name,
        "bundles": [
            {
                "bundle_dir": str(result["bundle_dir"]),
                "atlas": str(result["outputs"]["atlas"]),
                "metadata": str(result["outputs"]["metadata"]),
            }
            for result in results
        ],
    }, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="JumpClip sprite generation toolkit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    collect = subparsers.add_parser("collect", help="Collect public-domain or openly licensed references")
    collect.add_argument("--provider", choices=["openverse", "wikimedia"], required=True)
    collect.add_argument("--query", required=True)
    collect.add_argument("--limit", type=int, default=20)
    collect.add_argument("--out", required=True)
    collect.set_defaults(func=command_collect)

    analyze = subparsers.add_parser("analyze", help="Analyze a reference manifest into a design profile")
    analyze.add_argument("--manifest", required=True)
    analyze.add_argument("--out", required=True)
    analyze.add_argument("--grid-size", type=int, default=12)
    analyze.add_argument("--download-dir", default="")
    analyze.set_defaults(func=command_analyze)

    render = subparsers.add_parser("render", help="Render a sprite sheet, frame sequence, or animated GIF")
    render.add_argument("--profile", required=True)
    render.add_argument("--character", required=True)
    render.add_argument("--animation", required=True)
    render.add_argument("--prompt", required=True)
    render.add_argument("--out", required=True)
    render.add_argument("--format", choices=["sheet", "sequence", "gif"], default="sheet")
    render.add_argument("--canvas-size", type=int, default=64)
    render.add_argument("--upscale", type=int, default=4)
    render.add_argument("--grid-size", type=int, default=12, help="Grid size used if --profile points to a reference manifest")
    render.add_argument("--download-dir", default="", help="Optional download dir if --profile points to a manifest with remote references")
    render.add_argument("--art-preset", choices=["retro-arcade", "snes-rpg", "hd2d-rpg", "cel-brawler", "space-shooter", "soulslike-action"])
    render.add_argument("--style-family", choices=["8bit", "16bit", "hd2d", "bitmap-traced", "cel-shaded-2.5d"])
    render.add_argument("--silhouette-emphasis", type=float)
    render.add_argument("--texture-detail", type=float)
    render.add_argument("--palette-limit", type=int)
    render.add_argument("--cel-shading", type=float)
    render.add_argument("--outline-weight", type=float)
    render.add_argument("--accessory-density", type=float)
    render.add_argument("--tracing-bias", type=float)
    render.add_argument("--motion-silhouette-bias", type=float)
    render.add_argument("--motion-squash-stretch", type=float)
    render.add_argument("--motion-impact", type=float)
    render.add_argument("--motion-lift", type=float)
    render.add_argument("--learning-profile", help="Optional JSON influence profile that biases style and motion using gameplay-history learning")
    render.add_argument("--learning-weight", type=float, default=1.0, help="Blend weight for --learning-profile, from 0.0 to 1.0")
    render.set_defaults(func=command_render)

    bundle = subparsers.add_parser("bundle", help="Export a game-ready atlas bundle with metadata for engine integration")
    bundle.add_argument("--profile", required=True)
    bundle.add_argument("--character", required=True)
    bundle.add_argument("--animation", required=True)
    bundle.add_argument("--prompt", required=True)
    bundle.add_argument("--out-dir", required=True)
    bundle.add_argument("--pipeline", default="")
    bundle.add_argument("--canvas-size", type=int)
    bundle.add_argument("--upscale", type=int)
    bundle.add_argument("--grid-size", type=int, default=12)
    bundle.add_argument("--download-dir", default="")
    bundle.add_argument("--art-preset", choices=["retro-arcade", "snes-rpg", "hd2d-rpg", "cel-brawler", "space-shooter", "soulslike-action"])
    bundle.add_argument("--style-family", choices=["8bit", "16bit", "hd2d", "bitmap-traced", "cel-shaded-2.5d"])
    bundle.add_argument("--silhouette-emphasis", type=float)
    bundle.add_argument("--texture-detail", type=float)
    bundle.add_argument("--palette-limit", type=int)
    bundle.add_argument("--cel-shading", type=float)
    bundle.add_argument("--outline-weight", type=float)
    bundle.add_argument("--accessory-density", type=float)
    bundle.add_argument("--tracing-bias", type=float)
    bundle.add_argument("--motion-silhouette-bias", type=float)
    bundle.add_argument("--motion-squash-stretch", type=float)
    bundle.add_argument("--motion-impact", type=float)
    bundle.add_argument("--motion-lift", type=float)
    bundle.add_argument("--learning-profile", help="Optional JSON influence profile that biases style and motion using gameplay-history learning")
    bundle.add_argument("--learning-weight", type=float, default=1.0, help="Blend weight for --learning-profile, from 0.0 to 1.0")
    bundle.set_defaults(func=command_bundle)

    bundle_batch = subparsers.add_parser("bundle-batch", help="Export multiple game-ready bundles from a batch manifest")
    bundle_batch.add_argument("--batch-manifest", required=True)
    bundle_batch.add_argument("--out-dir", required=True)
    bundle_batch.add_argument("--pipeline", default="")
    bundle_batch.set_defaults(func=command_bundle_batch)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)
