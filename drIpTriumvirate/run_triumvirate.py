"""Run the drIpTriumvirate server."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from triumvirate.server import main  # noqa: E402

if __name__ == "__main__":
    main()
