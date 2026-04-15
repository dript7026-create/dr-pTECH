# Security Policy

## Reporting

Do not open public issues for suspected secrets exposure, credential leakage, vulnerable deployment configuration, or remotely exploitable defects.

Use a private reporting path instead:

- If you already have a direct maintainer contact, report there first.
- Otherwise open a minimal GitHub issue without exploit details and request a private handoff channel.

## What to Include

- Affected project or path
- Reproduction steps
- Impact summary
- Whether credentials, user data, or deployment infrastructure are involved
- Any proposed mitigation or temporary containment step

## Repository Notes

- This workspace contains multiple projects with different maturity levels.
- Some folders are prototypes or research artifacts and may not be production-hardened.
- Machine-local environments, caches, archives, and large generated outputs are intentionally excluded from the published mirror.

## Push Hygiene

- Run `powershell -File scripts/prepare_workspace_push.ps1` before any full-workspace push.
- Run `powershell -File scripts/pre_push_security_check.ps1` before pushing mixed workspace changes.
- Use `powershell -File scripts/pre_push_security_check.ps1 -AllFiles` before milestone or release pushes.
- Run `powershell -File scripts/publication_scope_pass.ps1` to separate publish-now files from review-only or excluded material before staging a full-workspace push.
- Do not push the whole workspace blindly when unrelated projects are modified. Stage or commit only the reviewed subset.
- Treat lender, budget, certificate, incident, and operator files as private by default unless they are deliberately redacted for publication.
- Keep credentials only in environment variables or local secret stores, never in tracked files.

## Launch Key Protocol

- The versioned helper scripts `set_openai_key.ps1` and `set_recraft_key.ps1` are an intentional part of the local launch-key workflow.
- They may prompt for key material and populate the current or user environment, but they must never write live secrets to tracked files, CI variables, generated manifests, or logs.
- Treat those scripts as workflow surface and operator prompts, not as credential storage.

## Governance And Longevity

- Full-workspace pushes must stay manual, reviewable, and reversible. Do not rely on unattended mirror-push jobs or self-committing CI for this repository.
- Publication decisions must protect business continuity, ethical obligations, financing posture, legal exposure, and market strategy, not just code quality.
- Use the generated filesystem signature from `scripts/write_workspace_signature.ps1` for milestone push evidence and release hygiene.

## Contact

- Maintainer contact: [rrcarell@gmail.com](mailto:rrcarell@gmail.com)
- Phone contact: (613) 808 - 4968

## Response Expectations

- Triage should focus first on credential exposure, remote code execution, unsafe automation, and supply-chain risk.
- Public disclosure should wait until the issue is understood and a mitigation path exists.
