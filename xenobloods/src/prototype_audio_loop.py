from __future__ import annotations

import argparse
import signal
import time
from pathlib import Path

try:
    import winsound
except ImportError:  # pragma: no cover
    winsound = None


RUNNING = True


def _handle_stop(_signum, _frame) -> None:
    global RUNNING
    RUNNING = False
    if winsound is not None:
        winsound.PlaySound(None, 0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("audio_path", type=Path)
    args = parser.parse_args()

    signal.signal(signal.SIGTERM, _handle_stop)
    signal.signal(signal.SIGINT, _handle_stop)

    if winsound is None or not args.audio_path.exists():
        return 0

    winsound.PlaySound(str(args.audio_path), winsound.SND_ASYNC | winsound.SND_FILENAME | winsound.SND_LOOP | winsound.SND_NODEFAULT)
    while RUNNING:
        time.sleep(0.25)
    winsound.PlaySound(None, 0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())