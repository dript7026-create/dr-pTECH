# Contributing to drIpTECH

## Scope

This repository is a workspace mirror containing multiple active projects, experiments, prototypes, and supporting tools. Changes should stay focused, reversible, and project-scoped.

## Before You Start

- Open an issue or discussion for large refactors, repository-wide dependency changes, or structural moves.
- Keep machine-local artifacts, generated bundles, archives, and credentials out of commits.
- Preserve per-project terminology and design direction instead of flattening projects into generic shared language.

## Development Baseline

- Python environment: use the workspace `.venv` when working on Python tools and tests.
- Health check: run `python tools/workspace_health.py --skip-pip-check` from the workspace root.
- Targeted tests: prefer running only the project or test files affected by your change.

## Change Rules

- Keep commits small and explain the project area affected.
- Do not mix generated outputs with source changes unless the generated artifacts are intentionally tracked.
- Do not commit secrets, API keys, local environment exports, or workstation-specific paths.
- Update `THIRD_PARTY_CREDITS.md` and the relevant file in `tools/dependency_manifests/` when adding new third-party dependencies.
- Document new build or runtime prerequisites in the nearest project README.

## Pull Requests

- Describe the project area changed.
- Summarize validation performed.
- Call out follow-up work or known limitations.
- Include screenshots only when the change affects a GUI or visual output.

## Dependency Policy

- Prefer project-scoped dependencies over workspace-wide expansion when only one project needs them.
- Keep heavyweight SDKs and toolchains optional unless they are required for the curated workspace checks.

## Release Mindset

- Treat the root repository as a durable open-source mirror.
- Favor source, docs, manifests, and reproducible tooling over shipping archives or local deliverable bundles.
