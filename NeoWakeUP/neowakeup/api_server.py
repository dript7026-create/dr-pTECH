#!/usr/bin/env python3
"""Minimal local API surface for NeoWakeUP engines."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .planetary.erpsequencer import ERP_LEGEND_FAMILIES, ErpSequencer
from .planetary.models import MODEL_PRESETS
from .planetary.network import Directive, PlanetaryMindNetwork, PlanetaryMindStore

ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = ROOT / "state" / "planetary_mind.json"
ERP_REPORT_FILE = ROOT / "state" / "erpsequencer_report.json"


def build_server_state() -> dict:
    network = PlanetaryMindNetwork(seed=7)
    store = PlanetaryMindStore(str(STATE_FILE))
    loaded = store.load_into(network)
    if not loaded:
        network.bootstrap()
        store.save(network)
    return {"network": network, "store": store}


def run_erp_sequence(state: dict, payload: dict) -> dict[str, object]:
    network = state["network"]
    store = state["store"]
    report = ErpSequencer(seed=23).sequence(
        network,
        steps=int(payload.get("steps", 12)),
        intoxication=float(payload.get("intoxication", 0.42)),
        recovery=float(payload.get("recovery", 0.46)),
        focus=float(payload.get("focus", 0.37)),
        model_name=str(payload.get("model", "mythic")),
    )
    ERP_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    ERP_REPORT_FILE.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    store.save(network)
    return report


class NeoWakeUPHandler(BaseHTTPRequestHandler):
    server_version = "NeoWakeUP/0.1"

    def _json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        state = self.server.engine_state
        network = state["network"]
        if self.path == "/health":
            self._json({"ok": True})
            return
        if self.path == "/models":
            self._json({"models": MODEL_PRESETS})
            return
        if self.path == "/erpsequencer/aliases":
            self._json({"legend_catalog": ERP_LEGEND_FAMILIES})
            return
        if self.path == "/erpsequencer/latest":
            if not ERP_REPORT_FILE.exists():
                self._json({"error": "not_found"}, status=404)
                return
            self._json(json.loads(ERP_REPORT_FILE.read_text(encoding="utf-8")))
            return
        if self.path == "/planetary/state":
            self._json(network.solve(Directive()))
            return
        self._json({"error": "not_found"}, status=404)

    def do_POST(self) -> None:
        state = self.server.engine_state
        network = state["network"]
        store = state["store"]
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        payload = json.loads(raw.decode("utf-8"))
        if self.path == "/planetary/step":
            directive = Directive(
                novelty=float(payload.get("novelty", 0.7)),
                equity=float(payload.get("equity", 0.7)),
                resilience=float(payload.get("resilience", 0.7)),
                speed=float(payload.get("speed", 0.6)),
            )
            report = network.step(directive)
            store.save(network)
            self._json(report)
            return
        if self.path == "/erpsequencer/run":
            self._json(run_erp_sequence(state, payload))
            return
        self._json({"error": "not_found"}, status=404)


def main() -> None:
    parser = argparse.ArgumentParser(description="NeoWakeUP local API server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), NeoWakeUPHandler)
    server.engine_state = build_server_state()
    print(f"NeoWakeUP API listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()