# Master dependency orchestrator — drIpTECH

Purpose

- Provide a simple, centralized way to scan `drIpTECH` and downstream subfolders
  for dependency manifests and produce/install dependencies consistently.
- Build/test orchestration is handled separately by `workspace_build.py` and
  `workspace_build.ps1`, which use a curated manifest instead of recursive
  discovery.

Quick usage

- Dry-run (safe):

```bash
python master --root drIpTECH
```

- Execute installs (use with care):

```bash
python master --root drIpTECH --apply
```

Windows (PowerShell)

Run the included wrapper from the `drIpTECH` folder:

```powershell
.\master.ps1           # dry-run
.\master.ps1 -Apply    # actually run installs
```

Workspace build runner

```powershell
.\workspace_build.ps1
.\workspace_build.ps1 -List -IncludeManual
```

Options

- `--venv-pip` : provide an explicit pip executable path to use for Python
- `--quiet` : reduce output

CI integration

- A GitHub Actions workflow is included to run the script in dry-run mode on
  commits and on a schedule. To run installs from CI, trigger the workflow
  manually and provide the `apply` input (not recommended for public repos).

Notes

- The orchestrator inspects common manifests: `requirements.txt`, `pyproject.toml`,
  `package.json`, `go.mod`, `Cargo.toml`, `composer.json`, and `Makefile`.
- It prefers safe install commands (`npm ci`, `poetry install`, `go mod download`,
  `cargo fetch`) when a lockfile or tool configuration is present.

CI secret: allow `--apply`

- Name: `CI_ALLOW_APPLY`
- Purpose: prevents accidental execution of `--apply` (actual installs) in CI. The
  workflow will only pass `--apply` when the workflow dispatch input `apply` is
  set to `true` AND the repository secret `CI_ALLOW_APPLY` is set to `true`.
- How to set: go to the repository Settings → Secrets and variables → Actions →
  New repository secret, set `CI_ALLOW_APPLY` to `true` (string) when you want to
  allow manual runs that perform installs. Do NOT set this for public forks or
  untrusted contributors.
- Recommendation: Keep `CI_ALLOW_APPLY` unset or `false` for most repositories.
  Use only for controlled, trusted runners and trusted maintainers. Prefer
  running dry-runs (default) in PRs and scheduled runs.

Manual run with apply

- To trigger an install from the Actions UI, use the workflow dispatch input
  `apply=true` and ensure `CI_ALLOW_APPLY` is configured. Otherwise the workflow
  will still run in dry-run mode.
