from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
ORB_DIR = ROOT / "ORBEngine"
BUILD_DIR = ROOT / ".pytest_cache" / "orbengine"
OUTPUT_PATH = BUILD_DIR / "orbengine_tutorial_demo_test.exe"


def resolve_gpp() -> str | None:
    candidates = [
        shutil.which("g++"),
        r"C:\tools\msys64\mingw64\bin\g++.exe",
        r"C:\ProgramData\mingw64\mingw64\bin\g++.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(candidate)
    return None


def test_orbengine_tutorial_demo_build_smoke():
    compiler = resolve_gpp()
    if not compiler:
        pytest.skip("No supported g++ compiler found for ORBEngine smoke build")

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    command = [
        compiler,
        "-municode",
        str(ORB_DIR / "src" / "orbengine_tutorial_demo.cpp"),
        "-lgdiplus",
        "-lgdi32",
        "-luser32",
        "-lshell32",
        "-o",
        str(OUTPUT_PATH),
    ]
    result = subprocess.run(command, capture_output=True, text=True, cwd=ROOT)
    assert result.returncode == 0, result.stderr
    assert OUTPUT_PATH.exists()