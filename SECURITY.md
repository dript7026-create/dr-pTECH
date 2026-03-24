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

## Response Expectations

- Triage should focus first on credential exposure, remote code execution, unsafe automation, and supply-chain risk.
- Public disclosure should wait until the issue is understood and a mitigation path exists.
