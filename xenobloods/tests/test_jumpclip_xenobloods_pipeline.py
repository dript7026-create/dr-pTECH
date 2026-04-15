from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

jumpclip_pipeline = importlib.import_module("jumpclip_xenobloods_pipeline")
build_and_stage_xenobloods_preview_set = jumpclip_pipeline.build_and_stage_xenobloods_preview_set
prepare_preview_roster_source = jumpclip_pipeline.prepare_preview_roster_source
resolve_linked_paths = jumpclip_pipeline.resolve_linked_paths
sync_runtime_assets_from_link = jumpclip_pipeline.sync_runtime_assets_from_link
service_preview_assets = jumpclip_pipeline.service_preview_assets
load_serviced_preview_assets = jumpclip_pipeline.load_serviced_preview_assets


def test_sync_runtime_assets_from_link_generates_preview_files(tmp_path: Path) -> None:
    game_root = tmp_path / "xenobloods"
    bundle_dir = game_root / "JumpClipAssets" / "test-bundle"
    bundle_dir.mkdir(parents=True)

    atlas = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
    for x in range(16, 32):
        for y in range(8, 24):
            atlas.putpixel((x, y), (220, 80, 90, 255))
    atlas.save(bundle_dir / "atlas.png")
    Image.new("RGBA", (128, 64), (40, 20, 24, 255)).save(bundle_dir / "visual_regression.png")
    (bundle_dir / "profile.json").write_text("{}", encoding="utf-8")
    (bundle_dir / "metadata.json").write_text(
        json.dumps(
            {
                "frames": [{"x": 16, "y": 8, "width": 16, "height": 16}],
                "animation": {"name": "run cycle"},
                "designer": {"style_family": "16bit"},
                "pipeline": {"pipeline_name": "test"},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    manifest_path = game_root / "jumpclip_pipeline_link.json"
    manifest_path.write_text(
        json.dumps(
            {
                "game_root": str(game_root),
                "centerpiece_source": "src/prototype_shell.py",
                "asset_bundle_dir": "JumpClipAssets/test-bundle",
                "atlas": "JumpClipAssets/test-bundle/atlas.png",
                "metadata": "JumpClipAssets/test-bundle/metadata.json",
                "profile": "JumpClipAssets/test-bundle/profile.json",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    runtime = sync_runtime_assets_from_link(manifest_path)

    assert runtime is not None
    assert runtime["sprite_preview"].exists()
    assert runtime["atlas_preview"].exists()
    assert runtime["visual_regression"].exists()
    resolved = resolve_linked_paths(json.loads(manifest_path.read_text(encoding="utf-8")))
    assert resolved["atlas"] == bundle_dir / "atlas.png"


def test_sync_runtime_assets_from_link_uses_most_expressive_frame(tmp_path: Path) -> None:
    game_root = tmp_path / "xenobloods"
    bundle_dir = game_root / "JumpClipAssets" / "test-bundle"
    bundle_dir.mkdir(parents=True)

    atlas = Image.new("RGBA", (32, 16), (0, 0, 0, 0))
    for x in range(18, 31):
        for y in range(1, 15):
            atlas.putpixel((x, y), (220, 80, 90, 255))
    atlas.save(bundle_dir / "atlas.png")
    (bundle_dir / "profile.json").write_text("{}", encoding="utf-8")
    (bundle_dir / "metadata.json").write_text(
        json.dumps(
            {
                "frames": [
                    {"x": 0, "y": 0, "width": 16, "height": 16},
                    {"x": 16, "y": 0, "width": 16, "height": 16},
                ],
                "animation": {"name": "attack combo"},
                "designer": {"style_family": "bitmap-traced"},
                "pipeline": {"pipeline_name": "test"},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    manifest_path = game_root / "jumpclip_pipeline_link.json"
    manifest_path.write_text(
        json.dumps(
            {
                "game_root": str(game_root),
                "centerpiece_source": "src/prototype_shell.py",
                "asset_bundle_dir": "JumpClipAssets/test-bundle",
                "atlas": "JumpClipAssets/test-bundle/atlas.png",
                "metadata": "JumpClipAssets/test-bundle/metadata.json",
                "profile": "JumpClipAssets/test-bundle/profile.json",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    runtime = sync_runtime_assets_from_link(manifest_path)

    assert runtime is not None
    preview = Image.open(runtime["sprite_preview"]).convert("RGBA")
    assert preview.getbbox() == (8, 4, 60, 60)


def test_prepare_preview_roster_source_resolves_shared_profile_path(tmp_path: Path) -> None:
    references = tmp_path / "refs.json"
    references.write_text(json.dumps({"references": []}, indent=2), encoding="utf-8")
    roster = tmp_path / "preview_roster.json"
    roster.write_text(
        json.dumps(
            {
                "profile": "refs.json",
                "jobs": [
                    {
                        "name": "hero-preview",
                        "character": "hero",
                        "animation": "run cycle",
                        "prompt": "hero prompt",
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    resolved = prepare_preview_roster_source(roster, tmp_path / "out")
    payload = json.loads(resolved.read_text(encoding="utf-8"))

    resolved_profile = Path(payload["profile"])

    assert resolved_profile == (tmp_path / "out" / "resolved_refs.json")
    assert resolved_profile.exists()
    assert json.loads(resolved_profile.read_text(encoding="utf-8")) == {"references": []}


def test_build_and_stage_xenobloods_preview_set_uses_named_active_preview(tmp_path: Path, monkeypatch) -> None:
    roster = tmp_path / "preview_roster.json"
    roster.write_text(json.dumps({"jobs": []}), encoding="utf-8")
    center = tmp_path / "prototype_shell.py"
    center.write_text("print('shell')\n", encoding="utf-8")

    monkeypatch.setattr(jumpclip_pipeline, "DEFAULT_CENTERPIECE", center)
    monkeypatch.setattr(jumpclip_pipeline, "load_pipeline_config", lambda _path: object())

    jobs = [
        type("Job", (), {"name": "hero-preview", "character": "hero"})(),
        type("Job", (), {"name": "lahgroid-boss-preview", "character": "boss"})(),
    ]
    monkeypatch.setattr(jumpclip_pipeline, "prepare_preview_roster_source", lambda path, working_dir: path)
    monkeypatch.setattr(jumpclip_pipeline, "load_bundle_jobs", lambda path: (None, jobs))
    monkeypatch.setattr(
        jumpclip_pipeline,
        "build_batch_bundles",
        lambda jobs, shared_profile, config, out_dir: [
            {"bundle_dir": out_dir / job.name, "metadata": {}, "outputs": {}} for job in jobs
        ],
    )

    staged_calls: list[str] = []

    def fake_stage_bundle_for_game(game_root: Path, centerpiece_file: Path, bundle_dir: Path, assets_subdir: str = "JumpClipAssets", manifest_name: str = "jumpclip_pipeline_link.json") -> dict:
        staged_calls.append(manifest_name)
        manifest_path = game_root / manifest_name
        manifest_path.write_text(
            json.dumps(
                {
                    "game_root": str(game_root),
                    "asset_bundle_dir": str(bundle_dir.name),
                    "atlas": "atlas.png",
                    "metadata": "metadata.json",
                    "profile": "profile.json",
                }
            ),
            encoding="utf-8",
        )
        return {
            "staged_bundle_dir": bundle_dir,
            "manifest_path": manifest_path,
            "manifest": {},
        }

    monkeypatch.setattr(jumpclip_pipeline, "stage_bundle_for_game", fake_stage_bundle_for_game)
    monkeypatch.setattr(jumpclip_pipeline, "sync_runtime_assets_from_link", lambda path: {"sprite_preview": path})
    monkeypatch.setattr(jumpclip_pipeline, "service_preview_assets", lambda previews: {"summary_path": tmp_path / "service.json", "previews": previews})

    result = build_and_stage_xenobloods_preview_set(roster_path=roster, output_dir=tmp_path / "build")

    assert staged_calls == ["jumpclip_pipeline_link_hero-preview.json", "jumpclip_pipeline_link.json"]
    assert result["active_preview"] == "lahgroid-boss-preview"
    assert result["runtime"]["sprite_preview"].name == "jumpclip_pipeline_link.json"


def test_service_preview_assets_emits_runtime_preview_copies(tmp_path: Path) -> None:
    staged_bundle_dir = tmp_path / "JumpClipAssets" / "ishtasha"
    staged_bundle_dir.mkdir(parents=True)

    atlas = Image.new("RGBA", (32, 16), (0, 0, 0, 0))
    for x in range(2, 14):
        for y in range(1, 15):
            atlas.putpixel((x, y), (220, 80, 90, 255))
    atlas.save(staged_bundle_dir / "atlas.png")
    (staged_bundle_dir / "metadata.json").write_text(
        json.dumps(
            {
                "frames": [{"x": 0, "y": 0, "width": 16, "height": 16}],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (staged_bundle_dir / "profile.json").write_text("{}", encoding="utf-8")
    Image.new("RGBA", (48, 16), (10, 10, 10, 255)).save(staged_bundle_dir / "visual_regression.png")
    (staged_bundle_dir / "preview.gif").write_bytes(b"GIF89a")

    result = service_preview_assets(
        [
            {
                "name": "ishtasha-botanical-spider-preview",
                "character": "Ishtasha",
                "staged_bundle_dir": str(staged_bundle_dir),
                "manifest_path": str(tmp_path / "jumpclip_pipeline_link.json"),
            }
        ],
        runtime_dir=tmp_path / "runtime",
    )

    record = result["previews"][0]
    assert Path(record["files"]["atlas"]).exists()
    assert Path(record["files"]["preview_gif"]).exists()
    assert Path(record["files"]["visual_regression"]).exists()
    assert Path(record["files"]["sprite_preview"]).exists()
    assert Path(result["summary_path"]).exists()


def test_load_serviced_preview_assets_reads_summary_paths(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    sprite_path = runtime_dir / "sprite.png"
    sprite_path.write_bytes(b"png")
    (runtime_dir / "asset_service_summary.json").write_text(
        json.dumps(
            {
                "previews": [
                    {
                        "name": "lattice-ward-preview",
                        "character": "Lattice Ward",
                        "ready": True,
                        "files": {
                            "sprite_preview": str(sprite_path),
                            "atlas": str(sprite_path),
                            "metadata": str(sprite_path),
                        },
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    result = load_serviced_preview_assets(runtime_dir)

    assert "lattice-ward-preview" in result
    assert Path(result["lattice-ward-preview"]["sprite_preview"]) == sprite_path
