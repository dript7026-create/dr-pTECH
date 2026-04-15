"""Small HTTP server for the drIpSignalStudio browser application."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import mimetypes
from pathlib import Path

from .model import build_plan, catalog_payload, coerce_profile, coerce_signals, default_payload
from .render import enrich_plan_with_renders, resolve_generated_asset


WEB_ROOT = Path(__file__).resolve().parent / "web"


class drIpSignalStudioHandler(BaseHTTPRequestHandler):
    server_version = "drIpSignalStudio/0.1"

    def _write(self, body: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload: dict, status: int = 200) -> None:
        self._write(json.dumps(payload, indent=2).encode("utf-8"), "application/json; charset=utf-8", status)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def do_GET(self) -> None:
        if self.path in {"/", "/index.html"}:
            self._write((WEB_ROOT / "index.html").read_bytes(), "text/html; charset=utf-8")
            return
        if self.path == "/app.js":
            self._write((WEB_ROOT / "app.js").read_bytes(), "application/javascript; charset=utf-8")
            return
        if self.path == "/styles.css":
            self._write((WEB_ROOT / "styles.css").read_bytes(), "text/css; charset=utf-8")
            return
        if self.path == "/api/health":
            self._json({"ok": True})
            return
        if self.path == "/api/defaults":
            self._json(default_payload())
            return
        if self.path == "/api/catalog":
            self._json(catalog_payload())
            return
        if self.path.startswith("/generated/"):
            asset = resolve_generated_asset(self.path)
            if asset is None:
                self._json({"error": "not_found"}, status=404)
                return
            content_type = mimetypes.guess_type(asset.name)[0] or "application/octet-stream"
            self._write(asset.read_bytes(), content_type)
            return
        self._json({"error": "not_found"}, status=404)

    def do_POST(self) -> None:
        if self.path == "/api/plan":
            payload = self._read_json()
            profile = coerce_profile(payload.get("profile"))
            signals = coerce_signals(payload.get("signals"))
            plan = build_plan(profile, signals)
            if payload.get("render_previews", True):
                enrich_plan_with_renders(plan)
            self._json(plan.to_dict())
            return
        self._json({"error": "not_found"}, status=404)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the drIpSignalStudio local server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8891)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), drIpSignalStudioHandler)
    print(f"drIpSignalStudio listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()