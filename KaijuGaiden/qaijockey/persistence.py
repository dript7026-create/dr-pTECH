"""
Persistence and immediate logging helpers for QAIJockey.

This module keeps runtime state small and explicit:
  - genomes are saved as JSON snapshots for reuse across runs
  - immediate input decisions are appended as JSONL records as they happen
"""

from __future__ import annotations

import json
import time
from pathlib import Path


class GenomeStore:
    def __init__(self, path: str):
        self.path = Path(path)

    def load(self):
        if not self.path.exists():
            return None
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, payload: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


class ImmediateInputLogger:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.path.open("a", encoding="utf-8")

    def _write(self, kind: str, payload: dict) -> None:
        record = {
            "ts": round(time.time(), 6),
            "kind": kind,
            **payload,
        }
        self._fh.write(json.dumps(record, sort_keys=True) + "\n")
        self._fh.flush()

    def log_input(self, payload: dict) -> None:
        self._write("input", payload)

    def log_outcome(self, payload: dict) -> None:
        self._write("outcome", payload)

    def close(self) -> None:
        if not self._fh.closed:
            self._fh.close()