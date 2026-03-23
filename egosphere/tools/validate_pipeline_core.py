import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "pipeline" / "sample_project" / "game_project.json"
OUT = ROOT / "pipeline" / "out" / "validation"
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
        OUT / "clipstudio_bundle" / "clipstudio_export.json",
        OUT / "clipstudio_bundle" / "clipstudio_runtime_manifest.json",
        OUT / "blender_bundle" / "blender_conversion.json",
        OUT / "blender_bundle" / "blender_ingest.py",
        OUT / "idtech2_bundle" / "idtech2_manifest.json",
        OUT / "idtech2_bundle" / "g_driptech_pipeline_autogen.h",
        OUT / "idtech2_bundle" / "g_driptech_pipeline_autogen.c",
    ]

    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise ValidationFailure(
            "Sample pipeline output is incomplete",
            details={"suite": "sample", "missing": missing},
        )

    manifest = json.loads((OUT / "idtech2_bundle" / "idtech2_manifest.json").read_text(encoding="utf-8"))
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


def run_validation_suite(suite: str, *, on_event: EventCallback | None = None) -> dict:
    suites = ["sample", "pertinence"] if suite == "all" else [suite]
    _emit(on_event, "info", "Starting validation suite", suite=suite)

    results = []
    for item in suites:
        if item == "sample":
            results.append(validate_sample_pipeline(on_event=on_event))
        elif item == "pertinence":
            results.append(validate_pertinence_pipeline(on_event=on_event))
        else:
            raise ValidationFailure("Unknown validation suite", details={"suite": item})

    summary = {
        "status": "ok",
        "suite": suite,
        "results": results,
    }
    _emit(on_event, "success", "Validation suite finished", summary=summary)
    return summary