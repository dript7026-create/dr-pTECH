from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from egosphere.tools import validate_pipeline
from egosphere.tools import validate_pipeline_gui
from egosphere.tools.validate_pipeline_core import run_validation_suite


ROOT = Path(__file__).resolve().parents[1]
EGOSPHERE_DIR = ROOT / "egosphere"


def _run_validator(command: list[str], *, cwd: Path) -> dict:
    result = subprocess.run(command, capture_output=True, text=True, cwd=cwd)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_validate_pipeline_script_entrypoint_outputs_ok_summary():
    payload = _run_validator(
        [sys.executable, "tools/validate_pipeline.py", "--suite", "sample"],
        cwd=EGOSPHERE_DIR,
    )

    assert payload["status"] == "ok"
    assert payload["suite"] == "sample"
    assert payload["results"][0]["project"] == "sample"
    assert payload["results"][0]["project_name"] == "EgosphereGame"


def test_validate_pipeline_module_entrypoint_outputs_ok_summary():
    payload = _run_validator(
        [sys.executable, "-m", "egosphere.tools.validate_pipeline", "--suite", "sample"],
        cwd=ROOT,
    )

    assert payload["status"] == "ok"
    assert payload["suite"] == "sample"
    assert payload["results"][0]["project"] == "sample"
    assert payload["results"][0]["project_name"] == "EgosphereGame"


def test_validate_pipeline_script_entrypoint_outputs_hope_summary():
    payload = _run_validator(
        [sys.executable, "tools/validate_pipeline.py", "--suite", "hope"],
        cwd=EGOSPHERE_DIR,
    )

    assert payload["status"] == "ok"
    assert payload["suite"] == "hope"
    assert payload["results"][0]["project"] == "hope"
    assert payload["results"][0]["project_name"] == "HopeOpenArms"


def test_validate_pipeline_gui_module_imports_launch_surface():
    assert validate_pipeline_gui.ROOT == EGOSPHERE_DIR
    assert callable(validate_pipeline_gui.launch_app)


def test_validate_pipeline_parse_args_defaults():
    args = validate_pipeline.parse_args([])

    assert args.suite == "sample"
    assert args.gui is False
    assert args.run is False


def test_validate_pipeline_parse_args_gui_run_all_suite():
    args = validate_pipeline.parse_args(["--suite", "all", "--gui", "--run"])

    assert args.suite == "all"
    assert args.gui is True
    assert args.run is True


def test_validate_pipeline_parse_args_accepts_hope_suite():
    args = validate_pipeline.parse_args(["--suite", "hope"])

    assert args.suite == "hope"
    assert args.gui is False
    assert args.run is False


def test_validate_pipeline_core_runs_hope_suite():
    payload = run_validation_suite("hope")

    assert payload["status"] == "ok"
    assert payload["suite"] == "hope"
    result = payload["results"][0]
    assert result["project"] == "hope"
    assert result["project_name"] == "HopeOpenArms"
    assert result["scene_count"] >= 3
    assert result["ecology_asset_count"] >= 3
    assert result["interaction_graph_count"] >= 3
    assert result["hitbox_manifest_count"] >= 3
    assert result["anim_state_machine_count"] >= 3
    assert result["vfx_descriptor_count"] >= 3
    assert result["runtime_transitions"] >= 1


def test_validate_pipeline_main_prints_json_summary(monkeypatch, capsys):
    def fake_run_validation_suite(suite: str) -> dict:
        assert suite == "sample"
        return {
            "status": "ok",
            "suite": suite,
            "results": [{"project": "sample", "project_name": "EgosphereGame"}],
        }

    monkeypatch.setattr(validate_pipeline, "run_validation_suite", fake_run_validation_suite)

    exit_code = validate_pipeline.main(["--suite", "sample"])
    output = capsys.readouterr().out
    payload = json.loads(output)

    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["suite"] == "sample"
    assert payload["results"][0]["project_name"] == "EgosphereGame"


def test_validate_pipeline_gui_main_delegates_to_launch_app(monkeypatch):
    captured: dict[str, object] = {}

    def fake_launch_app(*, initial_suite: str, auto_run: bool) -> int:
        captured["initial_suite"] = initial_suite
        captured["auto_run"] = auto_run
        return 7

    monkeypatch.setattr(validate_pipeline_gui, "launch_app", fake_launch_app)

    exit_code = validate_pipeline_gui.main(["--suite", "all", "--run"])

    assert exit_code == 7
    assert captured == {"initial_suite": "all", "auto_run": True}