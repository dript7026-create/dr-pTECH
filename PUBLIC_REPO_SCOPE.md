# Public Repository Scope

This repository is the public mirror for maintainable source, tests, build tooling, and attribution across the drIpTECH workspace.

## Public By Default

- source code, reusable scripts, and checked-in assets required to build or test a project
- reproducible build entry points such as `Makefile`, `build.ps1`, `workspace_build.py`, and curated CI workflows
- dependency manifests, credits, and contributor/security intake files needed to operate an open-source mirror
- project READMEs and technical notes that explain how to build, test, or extend the published code

## Kept Private

- lender, milestone, budget, financing, and portfolio execution documents
- internal legal, certification, or incident-response writeups that are not part of the public maintenance surface
- account-adjacent helper scripts that serialize, cache, or hardcode secrets; the versioned prompt-only helpers `set_openai_key.ps1` and `set_recraft_key.ps1` remain approved because they do not store credential material in the repository
- workstation captures, traces, backup snapshots, notebook scratchpads, and environment inventory dumps
- handoff bundles, review packages, and other deliverable artifacts that duplicate source or expose internal process

## Publication Rule

When in doubt, keep only the minimum material needed for a stranger to clone the repo, understand the project, build it, test it, and contribute safely.

If a file primarily preserves strategic advantage, financing posture, or workstation state rather than enabling open-source maintenance, it should stay out of the public mirror.

Before any full-workspace push, run `powershell -File scripts/prepare_workspace_push.ps1` so the current security scan and filesystem signature are produced from the same reviewed working tree.