from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analysis import synthesize_design_profile
from .models import RenderRequest
from .reference_sources import load_manifest, search_openverse, search_wikimedia, write_manifest
from .render import infer_animation_spec, load_profile, render_frames, save_gif, save_sequence, save_sheet


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
    profile = load_profile(Path(args.profile))
    animation = infer_animation_spec(args.animation)
    request = RenderRequest(
        character=args.character,
        prompt=args.prompt,
        animation=animation,
        canvas_size=args.canvas_size,
        upscale=args.upscale,
        output_path=Path(args.out),
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
    render.set_defaults(func=command_render)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)
