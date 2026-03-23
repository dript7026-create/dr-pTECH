"""Python wrapper: calls the PowerShell notification helper with signature check and explicit consent."""
import subprocess
import sys
from pathlib import Path
import argparse

PS_SCRIPT = Path(__file__).resolve().parents[1] / 'readAIpolish' / 'ps_notify.ps1'


def is_signed(script_path: Path) -> bool:
    cmd = [
        'powershell', '-NoProfile', '-Command',
        f"(Get-AuthenticodeSignature -FilePath '{str(script_path)}').Status"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    status = res.stdout.strip()
    return status == 'Valid'


def require_consent(prompt_text: str = None) -> bool:
    prompt = prompt_text or "This will run a locally signed PowerShell script. Type 'I CONSENT' to continue: "
    try:
        resp = input(prompt)
    except EOFError:
        return False
    return resp.strip() == 'I CONSENT'


def send_notification(title: str, message: str, unsafe: bool = False, auto_consent: bool = False) -> int:
    if not unsafe and not is_signed(PS_SCRIPT):
        print(f"Refusing to run unsigned script: {PS_SCRIPT}")
        print("Please sign the script with a trusted certificate, or run it manually under your own risk.")
        return 2
    if not auto_consent and not unsafe:
        if not require_consent():
            print("Consent not provided; aborting.")
            return 3
    # Build and run PowerShell command
    cmd = ['powershell', '-NoProfile', '-File', str(PS_SCRIPT)]
    if unsafe:
        cmd.append('-AllowUnsafe')
    cmd += ['-Title', title, '-Message', message]
    res = subprocess.run(cmd)
    return res.returncode


def main(argv=None):
    parser = argparse.ArgumentParser(description='Call signed PowerShell notification helper')
    parser.add_argument('title')
    parser.add_argument('message')
    parser.add_argument('--unsafe', action='store_true', help='Skip signature check (for local testing only)')
    parser.add_argument('--yes', action='store_true', help='Auto-confirm consent prompt')
    args = parser.parse_args(argv)

    rc = send_notification(args.title, args.message, unsafe=args.unsafe, auto_consent=args.yes)
    sys.exit(rc)


if __name__ == '__main__':
    main()
