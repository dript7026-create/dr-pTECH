PowerShell notification helper (ps_notify.ps1)

- Purpose: Provide a small, secure helper to trigger notifications from PowerShell or from Python (via the `scripts/ps_notify.py` wrapper).
- Usage (PowerShell):
  - `.









- Review the script before running. It uses `System.Windows.Forms.MessageBox` fallback if `BurntToast` is not available.  - `Install-Module -Name BurntToast -Scope CurrentUser`- To use native toasts, install `BurntToast` explicitly (run with elevated privileges only if you understand the risk):- The helper does not download or install modules automatically.Security notes:  - `python scripts\ps_notify.py "Hi" "Hello"`- Usage (Python):eadAIpolish\ps_notify.ps1 -Title "Hi" -Message "Hello"`