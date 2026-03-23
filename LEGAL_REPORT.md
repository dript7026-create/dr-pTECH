LEGAL REPORT — drIpTECH workspace setup

Date: 2026-03-02

Prepared for: IT / Legal review
Prepared by: (workspace automation)

Summary of actions performed locally in workspace `drIpTECH`:
- Created virtual environment `.venv` and installed packages from PyPI: `jupyter`, `ipykernel`, `win10toast`, and dependencies.
- Registered an IPython kernel `driptech-venv` pointing to the workspace `.venv` Python executable.
- Added helper files to enable local notifications:
  - `readAIpolish/ps_notify.ps1` — PowerShell notification helper (now enforces script Authenticode signature before running).
  - `scripts/ps_notify.py` — Python wrapper that requires the PowerShell script to be signed and requires explicit consent typed by the user (`I CONSENT`).
  - `driptech_jupyter_setup.ipynb` — example notebook updated to call the Python wrapper (no longer uses `-ExecutionPolicy Bypass`).
  - `CONTINUE_DECISION.md` — decision note with recommendations.

Security & compliance notes:
- No remote code download or automatic remote execution has been added by these files.
- The Python wrapper refuses to execute the PowerShell helper unless it is signed with a valid Authenticode signature and the user types the explicit consent string `I CONSENT` at runtime.
- The PowerShell helper now validates its own Authenticode signature at startup and exits if the signature is not `Valid`.
- Jupyter and other PyPI packages were installed locally in the `.venv`; they should be audited for licenses and vulnerabilities before production use.

Recommended verification steps (for IT/Legal):
1) Confirm whether `-ExecutionPolicy Bypass` is permitted in your environment — it is no longer used by the notebook or wrapper.
2) Confirm whether running a local Jupyter server is acceptable; ensure binding is limited to `localhost` and a strong token/password is used.
3) Verify and audit installed packages for CVEs and license compatibility (see `pip-audit`, `pip-licenses`).
4) Verify the external backup on the detached drive is encrypted and scan it with updated AV prior to any restore.

Evidence and logs:
- Kernel registered at: `C:\Users\rrcar\AppData\Roaming\jupyter\kernels\driptech-venv` (local user kernelspec)
- Virtualenv Python: `C:\Users\rrcar\Documents\drIpTECH\.venv\Scripts\python.exe`
- Files changed/created: `readAIpolish/ps_notify.ps1`, `scripts/ps_notify.py`, `driptech_jupyter_setup.ipynb`, `CONTINUE_DECISION.md`, `LEGAL_REPORT.md`


Signature of reviewer (place your electronic signature or initial below to indicate you approve sending this to IT/Legal for review):

Signed by: Ryan Richard Carell  Date: 2026-03-02

Notes from reviewer (optional):



--- End of report
