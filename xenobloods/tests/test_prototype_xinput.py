from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from prototype_xinput import XInputController


def test_xinput_controller_without_dll_returns_disconnected(monkeypatch) -> None:
    monkeypatch.setattr(XInputController, "_load_xinput", lambda self: None)

    controller = XInputController()
    snapshot = controller.poll()

    assert snapshot.connected is False
    assert snapshot.buttons == 0