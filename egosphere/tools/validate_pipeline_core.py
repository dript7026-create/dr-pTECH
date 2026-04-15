import contextlib
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable

try:
    import hope_runtime_sample
    import synthesis_pipeline
except ImportError:
    from egosphere.tools import hope_runtime_sample
    from egosphere.tools import synthesis_pipeline


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "pipeline" / "sample_project" / "game_project.json"
OUT = ROOT / "pipeline" / "out" / "validation"
HOPE_SEED = ROOT / "pipeline" / "projects" / "hope_synthesis" / "hope_world.seed.json"
HOPE_OUT = ROOT / "pipeline" / "out" / "hope_validation"
PERTINENCE_E2E = ROOT / "tools" / "run_pertinence_e2e.py"

EventCallback = Callable[[str, str, dict], None]


class ValidationFailure(RuntimeError):
    def __init__(self, message: str, *, details: dict | None = None):
        super().__init__(message)
        self.details = details or {}


def _emit(on_event: EventCallback | None, level: str, message: str, **details: object) -> None:
    if on_event is not None:
        on_event(level, message, details)


def _run_json_command(cmd: list[str], *, label: str, on_event: EventCallback | None = None) -> dict:
    _emit(on_event, "command", label, command=cmd)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)

    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    if stdout:
        _emit(on_event, "stdout", f"{label} stdout", text=stdout)
    if stderr:
        _emit(on_event, "stderr", f"{label} stderr", text=stderr)

    if result.returncode != 0:
        raise ValidationFailure(
            f"{label} failed with exit code {result.returncode}",
            details={
                "command": cmd,
                "returncode": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
            },
        )

    if not stdout:
        _emit(on_event, "success", f"{label} completed")
        return {}

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise ValidationFailure(
            f"{label} returned non-JSON output",
            details={"command": cmd, "stdout": stdout, "stderr": stderr},
        ) from exc

    _emit(on_event, "success", f"{label} completed", summary=payload)
    return payload


def validate_sample_pipeline(*, on_event: EventCallback | None = None) -> dict:
    _emit(on_event, "info", "Running sample pipeline validation", suite="sample")

    if OUT.exists():
        _emit(on_event, "info", "Removing previous sample validation output", path=str(OUT))
        shutil.rmtree(OUT)

    cmd = [
        sys.executable,
        str(ROOT / "tools" / "game_pipeline.py"),
        "build",
        "--project",
        str(PROJECT),
        "--out",
        str(OUT),
    ]
    pipeline_output = _run_json_command(cmd, label="Sample pipeline build", on_event=on_event)

    required = [
        OUT / "art_bundle" / "art_export.json",
        OUT / "art_bundle" / "art_runtime_manifest.json",
        OUT / "blender_bundle" / "blender_conversion.json",
        OUT / "blender_bundle" / "blender_ingest.py",
        OUT / "engine_bundle" / "engine_manifest.json",
        OUT / "engine_bundle" / "g_driptech_pipeline_autogen.h",
        OUT / "engine_bundle" / "g_driptech_pipeline_autogen.c",
    ]

    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise ValidationFailure(
            "Sample pipeline output is incomplete",
            details={"suite": "sample", "missing": missing},
        )

    manifest = json.loads((OUT / "engine_bundle" / "engine_manifest.json").read_text(encoding="utf-8"))
    result = {
        "status": "ok",
        "project": "sample",
        "pipeline_output": pipeline_output,
        "project_name": manifest["project_name"],
        "system_count": len(manifest["systems"]),
        "entity_count": len(manifest["entities"]),
        "precache_count": len(manifest["precache"]),
    }
    _emit(on_event, "success", "Sample validation passed", result=result)
    return result


def validate_pertinence_pipeline(*, on_event: EventCallback | None = None) -> dict:
    _emit(on_event, "info", "Running Pertinence end-to-end validation", suite="pertinence")
    report = _run_json_command(
        [sys.executable, str(PERTINENCE_E2E)],
        label="Pertinence validation",
        on_event=on_event,
    )
    report["status"] = "ok"
    report["project"] = "pertinence"
    _emit(on_event, "success", "Pertinence validation passed", result=report)
    return report


def validate_hope_pipeline(*, on_event: EventCallback | None = None) -> dict:
    _emit(on_event, "info", "Running HOPE synthesis validation", suite="hope")

    if HOPE_OUT.exists():
        _emit(on_event, "info", "Removing previous HOPE validation output", path=str(HOPE_OUT))
        shutil.rmtree(HOPE_OUT)

    _emit(
        on_event,
        "command",
        "HOPE synthesis build",
        command=["build", str(HOPE_SEED), str(HOPE_OUT)],
    )
    captured_stdout = io.StringIO()
    with contextlib.redirect_stdout(captured_stdout):
        project_path = synthesis_pipeline.build(HOPE_SEED, HOPE_OUT)
    pipeline_output = {"canonical_project": str(project_path)}
    nested_stdout = captured_stdout.getvalue().strip()
    if nested_stdout:
        _emit(on_event, "stdout", "HOPE synthesis build stdout", text=nested_stdout)
    _emit(on_event, "success", "HOPE synthesis build completed", summary=pipeline_output)

    required = [
        HOPE_OUT / "game_project.generated.json",
        HOPE_OUT / "generation" / "generation_manifest.json",
        HOPE_OUT / "art_bundle" / "art_export.json",
        HOPE_OUT / "blender_bundle" / "blender_conversion.json",
        HOPE_OUT / "engine_bundle" / "engine_manifest.json",
    ]

    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise ValidationFailure(
            "HOPE synthesis output is incomplete",
            details={"suite": "hope", "missing": missing},
        )

    preview = hope_runtime_sample.build_preview_snapshot(project_path, ticks=1, cycles=1)
    runtime_save_path = HOPE_OUT / "hope_runtime_state.json"
    runtime = hope_runtime_sample.run_project(project_path, ticks=1, cycles=1, save_path=runtime_save_path)

    generation_manifest = json.loads((HOPE_OUT / "generation" / "generation_manifest.json").read_text(encoding="utf-8"))
    engine_manifest = json.loads((HOPE_OUT / "engine_bundle" / "engine_manifest.json").read_text(encoding="utf-8"))
    ecology_assets = [item for item in generation_manifest["assets"] if item.get("asset_type") == "ecology"]
    interaction_graph_assets = [item for item in generation_manifest["assets"] if item.get("asset_type") == "interaction_graph"]
    hitbox_manifest_assets = [item for item in generation_manifest["assets"] if item.get("asset_type") == "hitbox_manifest"]
    anim_state_machine_assets = [item for item in generation_manifest["assets"] if item.get("asset_type") == "anim_state_machine"]
    vfx_descriptor_assets = [item for item in generation_manifest["assets"] if item.get("asset_type") == "vfx_descriptor"]

    result = {
        "status": "ok",
        "project": "hope",
        "pipeline_output": pipeline_output,
        "project_name": preview["project_name"],
        "scene_count": len(preview["scene_cards"]),
        "system_graph_count": len(preview["system_graph"]),
        "generation_asset_count": generation_manifest["asset_count"],
        "ecology_asset_count": len(ecology_assets),
        "runtime_scene_count": len(runtime["scenes"]),
        "runtime_transitions": int(runtime["sanctuary_state"]["transitions"]),
        "sanctuary_memory": float(preview["sanctuary_state"]["memory"]),
        "engine_entity_count": len(engine_manifest["entities"]),
        "engine_precache_count": len(engine_manifest["precache"]),
        "interaction_graph_count": len(interaction_graph_assets),
        "hitbox_manifest_count": len(hitbox_manifest_assets),
        "anim_state_machine_count": len(anim_state_machine_assets),
        "vfx_descriptor_count": len(vfx_descriptor_assets),
    }
    _emit(on_event, "success", "HOPE validation passed", result=result)
    return result


def run_validation_suite(suite: str, *, on_event: EventCallback | None = None) -> dict:
    suites = ["sample", "pertinence", "hope"] if suite == "all" else [suite]
    _emit(on_event, "info", "Starting validation suite", suite=suite)

    results = []
    for item in suites:
        if item == "sample":
            results.append(validate_sample_pipeline(on_event=on_event))
        elif item == "pertinence":
            results.append(validate_pertinence_pipeline(on_event=on_event))
        elif item == "hope":
            results.append(validate_hope_pipeline(on_event=on_event))
        else:
            raise ValidationFailure("Unknown validation suite", details={"suite": item})

    summary = {
        "status": "ok",
        "suite": suite,
        "results": results,
    }
    _emit(on_event, "success", "Validation suite finished", summary=summary)
    return summary