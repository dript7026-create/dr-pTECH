from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_shoot_reports_obj_cgi_renderer_mode() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "shoot_game.py"), "--smoke-test"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    summary = json.loads(result.stdout.strip())
    assert summary["renderer_mode"] == "obj_low_poly_3d"
    assert summary["controller_support"] is True
    assert summary["rooms"] == 3
