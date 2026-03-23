from pathlib import Path
import json
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
AA_DIR = ROOT / "ArchesAndAngels"
BUILD_DIR = ROOT / ".pytest_cache" / "arches_and_angels"
EXE_PATH = BUILD_DIR / "arches_and_angels_sim_test.exe"
EXPORT_PATH = BUILD_DIR / "arches_and_angels_campaign.json"


def build_sim() -> Path:
    gcc = shutil.which("gcc")
    if not gcc:
        raise AssertionError("gcc is required to build ArchesAndAngels regression binary")

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    command = [
        gcc,
        str(AA_DIR / "src" / "main.c"),
        str(AA_DIR / "src" / "aa_sim.c"),
        str(AA_DIR / "src" / "aa_export.c"),
        str(AA_DIR / "ArchesAndAngels_Sinner_of_Oblivion.c"),
        "-I" + str(AA_DIR / "src"),
        "-I" + str(AA_DIR),
        "-o",
        str(EXE_PATH),
    ]
    result = subprocess.run(command, capture_output=True, text=True, cwd=ROOT)
    assert result.returncode == 0, result.stderr
    return EXE_PATH


def test_arches_and_angels_sim_output_markers():
    exe = build_sim()
    result = subprocess.run([str(exe)], capture_output=True, text=True, cwd=ROOT)
    assert result.returncode == 0, result.stderr

    output = result.stdout
    assert "Week 1 pre-brief" in output
    assert "Public Works" in output
    assert "Smuggle Compact" in output
    assert "Recommendation Chain" in output or "Ignored Recommendation" in output
    assert "Scenario Cards" in output
    assert "Mission Board" in output
    assert "Final Assessment" in output
    assert "Campaign stability:" in output


def test_arches_and_angels_json_export():
    exe = build_sim()
    if EXPORT_PATH.exists():
        EXPORT_PATH.unlink()

    result = subprocess.run([str(exe), "--json-out", str(EXPORT_PATH)], capture_output=True, text=True, cwd=ROOT)
    assert result.returncode == 0, result.stderr
    assert EXPORT_PATH.exists()

    payload = json.loads(EXPORT_PATH.read_text(encoding="utf-8"))
    assert payload["campaign"]["week"] >= 1
    assert len(payload["districts"]) == 5
    assert "missions" in payload
    assert "incidents" in payload
