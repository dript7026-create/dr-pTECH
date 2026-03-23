"""Bridge planetary directives into QAIJockey tuning."""

from __future__ import annotations

import json
from pathlib import Path


class DirectiveBridge:
    def __init__(self, state_path: str | None = None):
        self.state_path = Path(state_path) if state_path else None
        self.directive = None
        self.planetary_coherence = 0.5

    def refresh(self) -> bool:
        if self.state_path is None or not self.state_path.exists():
            return False
        payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        self.planetary_coherence = float(payload.get("exchange", 0.5))
        return True

    def apply_to_qai(self, qai) -> None:
        if self.state_path is None:
            return
        if not self.refresh():
            return
        coherence = max(0.0, min(1.0, self.planetary_coherence))
        qai.skill_mgr.base_skill = max(0.1, min(1.0, qai.skill_mgr.base_skill * (0.85 + 0.30 * coherence)))
        qai.genetics.active["courage"] = max(0.0, min(1.6, qai.genetics.active["courage"] * (0.85 + 0.25 * coherence)))
        qai.genetics.active["patience"] = max(0.0, min(1.6, qai.genetics.active["patience"] * (1.10 - 0.20 * coherence)))