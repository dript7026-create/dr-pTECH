#!/usr/bin/env python3
"""Curated workspace build runner for drIpTECH.

This script intentionally does not recurse through the whole workspace.
It uses a maintained manifest so archived traces, toolchain examples, and
generated output folders do not derail a top-level build.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "workspace_build.json"
DEFAULT_AUTOMATION = ("automatic",)


def load_manifest() -> dict:
    with MANIFEST.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def available_tool(tool_name: str) -> str | None:
    if tool_name == "python":
        return sys.executable
    if tool_name == "make":
        return shutil.which("make") or shutil.which("mingw32-make")
    if tool_name == "powershell":
        return shutil.which("powershell") or shutil.which("pwsh")
    return shutil.which(tool_name)


def resolve_command(command: list[str]) -> list[str]:
    resolved = list(command)
    executable = available_tool(resolved[0])
    if executable:
        resolved[0] = executable

    expanded = []
    for part in resolved:
        expanded.append(os.path.expandvars(part))
    return expanded


def missing_requirements(project: dict) -> tuple[list[str], list[str]]:
    missing_tools = []
    for tool_name in project.get("required_tools", []):
        if not available_tool(tool_name):
            missing_tools.append(tool_name)

    missing_env = []
    for env_name in project.get("required_env", []):
        if not os.environ.get(env_name):
            missing_env.append(env_name)

    return missing_tools, missing_env


def selected_projects(manifest: dict, project_ids: list[str], include_manual: bool) -> list[dict]:
    allowed = {"automatic", "manual"} if include_manual else set(DEFAULT_AUTOMATION)
    projects = [project for project in manifest["projects"] if project["automation"] in allowed]
    if project_ids:
        wanted = set(project_ids)
        projects = [project for project in projects if project["id"] in wanted]
    return projects


def print_project(project: dict) -> None:
    print(f"- {project['id']}: {project['name']} [{project['automation']}]")
    print(f"  path: {project['path']}")
    print(f"  notes: {project.get('notes', 'n/a')}")
    if project.get("required_tools"):
        print(f"  tools: {', '.join(project['required_tools'])}")
    if project.get("required_env"):
        print(f"  env: {', '.join(project['required_env'])}")
    for command in project.get("commands", []):
        print("  cmd: " + " ".join(resolve_command(command)))


def run_project(project: dict, dry_run: bool) -> tuple[str, str]:
    missing_tools, missing_env = missing_requirements(project)
    if missing_tools or missing_env:
        reasons = []
        if missing_tools:
            reasons.append("missing tools: " + ", ".join(missing_tools))
        if missing_env:
            reasons.append("missing env: " + ", ".join(missing_env))
        return "skipped", "; ".join(reasons)

    project_dir = ROOT / project["path"]
    for command in project.get("commands", []):
        resolved = resolve_command(command)
        printable = subprocess.list2cmdline(resolved)
        print(f"[{project['id']}] {project_dir} $ {printable}")
        if dry_run:
            continue
        completed = subprocess.run(resolved, cwd=project_dir, check=False)
        if completed.returncode != 0:
            return "failed", f"command exited with {completed.returncode}"

    return "passed", "ok"


def main() -> int:
    parser = argparse.ArgumentParser(description="Curated workspace build runner")
    parser.add_argument("--dry-run", action="store_true", help="Show commands without executing them")
    parser.add_argument("--list", action="store_true", help="List configured projects and exit")
    parser.add_argument("--include-manual", action="store_true", help="Include manual/toolchain-bound projects")
    parser.add_argument("--strict-skips", action="store_true", help="Return a failure code if any selected project is skipped")
    parser.add_argument("--project", action="append", default=[], help="Run a specific project id (repeatable)")
    args = parser.parse_args()

    manifest = load_manifest()
    projects = selected_projects(manifest, args.project, args.include_manual)
    if not projects:
        print("No projects matched the current selection.")
        return 1

    if args.list:
        for project in projects:
            print_project(project)
        return 0

    results = []
    for project in projects:
        status, detail = run_project(project, dry_run=args.dry_run)
        results.append((project["id"], status, detail))

    print("\nSummary:")
    for project_id, status, detail in results:
        print(f"- {project_id}: {status} ({detail})")

    failed = [item for item in results if item[1] == "failed"]
    skipped = [item for item in results if item[1] == "skipped"]
    if failed:
        return 2
    if args.strict_skips and skipped:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())