from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_DIR = ROOT / "tools" / "dependency_manifests"
CURATED_TEST_FOLDERS = [
    ROOT / "tests",
    ROOT / "speech_to_text_google" / "tests",
    ROOT / "IllusionCanvasInteractive" / "tests",
]


@dataclass
class CommandResult:
    label: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def run_command(label: str, command: list[str]) -> CommandResult:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return CommandResult(
        label=label,
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )


def load_manifests() -> list[dict]:
    manifests: list[dict] = []
    for manifest_path in sorted(MANIFEST_DIR.glob("*.json")):
        manifests.append(json.loads(manifest_path.read_text(encoding="utf-8")))
    return manifests


def module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def audit_manifests(strict_optional: bool) -> tuple[list[dict], int]:
    manifests = load_manifests()
    failures = 0
    print("Optional dependency audit")
    print("-------------------------")
    for manifest in manifests:
        provider = manifest.get("provider", "python")
        print(f"{manifest['project']} [{provider}]")
        requirements_file = manifest.get("requirements_file")
        if requirements_file:
            print(f"  requirements: {requirements_file}")
        for group in manifest.get("module_groups", []):
            missing = [name for name in group.get("modules", []) if not module_available(name)]
            if provider == "blender":
                status = "external-runtime"
            else:
                status = "ok" if not missing else "missing"
            print(f"  - {group['name']}: {status}")
            if missing:
                print(f"    missing modules: {', '.join(missing)}")
                if provider == "python" and strict_optional:
                    failures += 1
            purpose = group.get("purpose")
            if purpose:
                print(f"    purpose: {purpose}")
        for note in manifest.get("notes", []):
            print(f"    note: {note}")
        print()
    return manifests, failures


def print_command_result(result: CommandResult) -> None:
    state = "PASS" if result.ok else "FAIL"
    print(f"{state}: {result.label}")
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run curated drIpTECH workspace health checks.")
    parser.add_argument("--skip-pip-check", action="store_true", help="Skip python -m pip check.")
    parser.add_argument("--skip-tests", action="store_true", help="Skip curated pytest folders.")
    parser.add_argument(
        "--strict-optional",
        action="store_true",
        help="Fail when optional python-provider manifests are missing from the active interpreter.",
    )
    args = parser.parse_args()

    print(f"Workspace root: {ROOT}")
    print(f"Python: {sys.executable}")
    print()

    failures = 0

    if not args.skip_pip_check:
        pip_check = run_command("pip consistency", [sys.executable, "-m", "pip", "check"])
        print_command_result(pip_check)
        if not pip_check.ok:
            failures += 1

    if not args.skip_tests:
        pytest_command = [sys.executable, "-m", "pytest", "-q", *[str(path) for path in CURATED_TEST_FOLDERS]]
        pytest_result = run_command("curated python test folders", pytest_command)
        print_command_result(pytest_result)
        if not pytest_result.ok:
            failures += 1

    _, optional_failures = audit_manifests(strict_optional=args.strict_optional)
    failures += optional_failures

    print("Summary")
    print("-------")
    if failures == 0:
        print("Workspace health check passed.")
    else:
        print(f"Workspace health check found {failures} blocking issue(s).")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())