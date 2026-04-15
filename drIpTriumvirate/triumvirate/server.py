"""Unified HTTP server for the drIpTriumvirate."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import mimetypes
from pathlib import Path

_WORKSPACE = Path(__file__).resolve().parents[2]
_STUDIO_ROOT = _WORKSPACE / "drIpSignalStudio"
if str(_STUDIO_ROOT) not in sys.path:
    sys.path.insert(0, str(_STUDIO_ROOT))

from dripsignalstudio.model import build_plan, coerce_profile, coerce_signals  # noqa: E402
from dripsignalstudio.render import enrich_plan_with_renders, resolve_generated_asset  # noqa: E402

from .driplive import LivePulse, FeelState, derive_feel_state, VALID_WEATHER  # noqa: E402
from .dripsignals import feel_to_signals, resonance_score, translation_trace  # noqa: E402
from .matrix_tasks import TaskBoard  # noqa: E402

WEB_ROOT = Path(__file__).resolve().parent / "web"

_pulse = LivePulse()
_board = TaskBoard()

# Seed demo tasks
_board.add("ignite-velocity-cut", priority=8)
_board.add("prime-cinematic-reveal", priority=7)
_board.add("night-story-loop", priority=6)


def _clamp_float(data: dict, key: str, fallback: float) -> float:
    try:
        return max(0.0, min(1.0, float(data[key])))
    except (KeyError, ValueError, TypeError):
        return fallback


class TriumvirateHandler(BaseHTTPRequestHandler):
    server_version = "drIpTriumvirate/0.1"

    def log_message(self, format: str, *args: object) -> None:
        pass

    def _write(self, body: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload: dict, status: int = 200) -> None:
        self._write(
            json.dumps(payload, indent=2).encode("utf-8"),
            "application/json; charset=utf-8",
            status,
        )

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def _serve_static(self, filename: str) -> None:
        path = WEB_ROOT / filename
        if not path.exists():
            self._json({"error": "not_found"}, 404)
            return
        ct = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self._write(path.read_bytes(), ct)

    # ── GET ──────────────────────────────────────────────
    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/", "/index.html"}:
            self._serve_static("index.html")
            return
        for static_name in ("app.js", "styles.css", "matrix.js", "disco.js"):
            if self.path == f"/{static_name}":
                self._serve_static(static_name)
                return

        if self.path == "/api/health":
            self._json({"ok": True, "engine": "triumvirate"})
            return
        if self.path == "/api/live/pulse":
            _pulse.tick()
            self._json(_pulse.snapshot())
            return
        if self.path == "/api/tasks":
            self._json(_board.to_dict())
            return
        if self.path == "/api/tasks/terminal":
            self._json({"lines": _board.terminal_view()})
            return

        if self.path == "/api/stats":
            d = _board.to_dict()
            self._json({
                "total": d["total"],
                "states": d["states"],
                "live_count": d["states"].get("LIVE", 0),
                "in_flight": sum(
                    d["states"].get(s, 0)
                    for s in ("DRAFT", "FEEL", "SIGNAL", "RENDER", "ENCODE", "REVIEW", "SUBMIT")
                ),
            })
            return

        if self.path == "/api/live/auto-tick":
            _pulse.tick()
            self._json(_pulse.snapshot())
            return

        if self.path.startswith("/generated/"):
            asset = resolve_generated_asset(self.path)
            if asset is None:
                self._json({"error": "not_found"}, 404)
                return
            ct = mimetypes.guess_type(asset.name)[0] or "application/octet-stream"
            self._write(asset.read_bytes(), ct)
            return

        self._json({"error": "not_found"}, 404)

    # ── POST ─────────────────────────────────────────────
    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/api/live/context":
            data = self._read_json()
            if "hour" in data:
                _pulse.set_hour(float(data["hour"]))
            if "weather" in data:
                w = str(data["weather"])
                if w in VALID_WEATHER:
                    _pulse.set_weather(w)
            for ctx_key in ("day_energy", "audience_pulse", "content_freshness", "platform_noise"):
                if ctx_key in data:
                    setattr(_pulse.context, ctx_key, _clamp_float(data, ctx_key, getattr(_pulse.context, ctx_key)))
            _pulse.feel = derive_feel_state(_pulse.context)
            self._json(_pulse.snapshot())
            return

        if self.path == "/api/signals/translate":
            data = self._read_json()
            feel = FeelState(
                urgency=_clamp_float(data, "urgency", 0.5),
                trust=_clamp_float(data, "trust", 0.5),
                wonder=_clamp_float(data, "wonder", 0.5),
                tenderness=_clamp_float(data, "tenderness", 0.5),
                grit=_clamp_float(data, "grit", 0.5),
                clarity=_clamp_float(data, "clarity", 0.5),
                volatility=_clamp_float(data, "volatility", 0.5),
            )
            signals = feel_to_signals(feel)
            trace = translation_trace(feel)
            self._json({
                "feel": feel.to_dict(),
                "signals": asdict(signals),
                "resonance": resonance_score(feel, signals),
                "trace": trace,
            })
            return

        if self.path == "/api/plan":
            data = self._read_json()
            if "feel" in data:
                feel_data = data["feel"]
                feel = FeelState(**{k: _clamp_float(feel_data, k, 0.5) for k in FeelState.__dataclass_fields__})
                signals = feel_to_signals(feel)
            else:
                signals = coerce_signals(data.get("signals"))

            profile = coerce_profile(data.get("profile"))
            plan = build_plan(profile, signals)
            if data.get("render_previews", True):
                enrich_plan_with_renders(plan)

            result = plan.to_dict()
            if "feel" in data:
                result["feel_source"] = data["feel"]
                result["resonance"] = resonance_score(feel, signals)
            self._json(result)
            return

        if self.path == "/api/tasks":
            data = self._read_json()
            label = str(data.get("label", "untitled"))[:120]
            priority = max(1, min(10, int(data.get("priority", 5))))
            task = _board.add(label=label, priority=priority)
            self._json(task.to_dict())
            return

        if self.path.startswith("/api/tasks/") and self.path.endswith("/advance"):
            parts = self.path.split("/")
            if len(parts) >= 4:
                task_id = parts[3]
                task = _board.advance(task_id)
                if task:
                    self._json(task.to_dict())
                    return
            self._json({"error": "task_not_found"}, 404)
            return

        if self.path.startswith("/api/tasks/") and self.path.endswith("/remove"):
            parts = self.path.split("/")
            if len(parts) >= 4:
                task_id = parts[3]
                if _board.remove(task_id):
                    self._json({"ok": True})
                    return
            self._json({"error": "task_not_found"}, 404)
            return

        if self.path.startswith("/api/tasks/") and self.path.endswith("/artifact"):
            parts = self.path.split("/")
            if len(parts) >= 4:
                task_id = parts[3]
                artifact = str(data.get("label", ""))[:200].strip()
                if artifact:
                    task = _board.attach_artifact(task_id, artifact)
                    if task:
                        self._json(task.to_dict())
                        return
            self._json({"error": "task_not_found"}, 404)
            return

        self._json({"error": "not_found"}, 404)


def main() -> None:
    parser = argparse.ArgumentParser(description="drIpTriumvirate — feel-first ad engine")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8892)
    args = parser.parse_args()

    print(f"\n  drIpTriumvirate listening on http://{args.host}:{args.port}\n")
    print("  drIpLIVE ............. experiential runtime  [ONLINE]")
    print("  dripsignals .......... feeling→signal bridge  [ONLINE]")
    print("  drIpSignalStudio ..... campaign output engine [ONLINE]")
    print("  MatrixTaskBoard ...... pipeline management    [ONLINE]")
    print()

    server = ThreadingHTTPServer((args.host, args.port), TriumvirateHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
