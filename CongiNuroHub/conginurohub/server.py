"""Small HTTP server for the CongiNuroHub browser application."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import mimetypes
from pathlib import Path
from urllib.parse import unquote

from .model import Directive, bootstrap_state, dataset_payload, registry_payload, step_state

WEB_ROOT = Path(__file__).resolve().parent / "web"
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
NEOWAKEUP_ASSET_ROOT = WORKSPACE_ROOT / "NeoWakeUP" / "assets" / "recraft" / "gui_pass_600"


def build_asset_manifest() -> dict:
    return {
        "planet_core": "/neowakeup-assets/planet/planetary_mind_planet_core.png",
        "stream_map": "/neowakeup-assets/network/network_channel_streams.png",
        "signal_sheet": "/neowakeup-assets/network/signal_transfer_spritesheet.png",
        "node_sheet": "/neowakeup-assets/network/node_marker_spritesheet.png",
        "avatar_sheet": "/neowakeup-assets/icons/humanoid_mind_icons_set_a.png",
        "glyph_upper": "/neowakeup-assets/font/font_glyph_reference_uppercase.png",
        "glyph_lower": "/neowakeup-assets/font/font_glyph_reference_lowercase.png",
        "glyph_symbols": "/neowakeup-assets/font/font_glyph_reference_digits_symbols.png",
    }


def resolve_neowakeup_asset(request_path: str) -> Path | None:
    relative = request_path.removeprefix("/neowakeup-assets/")
    candidate = (NEOWAKEUP_ASSET_ROOT / unquote(relative)).resolve()
    try:
        candidate.relative_to(NEOWAKEUP_ASSET_ROOT.resolve())
    except ValueError:
        return None
    if not candidate.exists() or not candidate.is_file():
        return None
    return candidate


class CongiNuroHubHandler(BaseHTTPRequestHandler):
    server_version = "CongiNuroHub/0.1"

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
            body = (WEB_ROOT / "index.html").read_bytes()
            self._write(body, "text/html; charset=utf-8")
            return
        if self.path == "/app.js":
            body = (WEB_ROOT / "app.js").read_bytes()
            self._write(body, "application/javascript; charset=utf-8")
            return
        if self.path == "/styles.css":
            body = (WEB_ROOT / "styles.css").read_bytes()
            self._write(body, "text/css; charset=utf-8")
            return
        if self.path == "/api/health":
            self._json({"ok": True})
            return
        if self.path == "/api/state":
            self._json(self.server.state.to_dict())
            return
        if self.path == "/api/registry":
            self._json(registry_payload())
            return
        if self.path == "/api/dataset":
            self._json(dataset_payload())
            return
        if self.path == "/api/assets":
            self._json(build_asset_manifest())
            return
        if self.path.startswith("/neowakeup-assets/"):
            asset = resolve_neowakeup_asset(self.path)
            if asset is None:
                self._json({"error": "not_found"}, status=404)
                return
            content_type = mimetypes.guess_type(asset.name)[0] or "application/octet-stream"
            self._write(asset.read_bytes(), content_type)
            return
        self._json({"error": "not_found"}, status=404)

    def do_POST(self) -> None:
        payload = self._read_json()
        if self.path == "/api/step":
            raw_directive = payload.get("directive", {})
            directive = Directive(
                curiosity_bias=float(raw_directive.get("curiosity_bias", self.server.state.directive.curiosity_bias)),
                equity_bias=float(raw_directive.get("equity_bias", self.server.state.directive.equity_bias)),
                challenge_bias=float(raw_directive.get("challenge_bias", self.server.state.directive.challenge_bias)),
                reflection_bias=float(raw_directive.get("reflection_bias", self.server.state.directive.reflection_bias)),
            )
            steps = int(payload.get("steps", 1))
            step_state(self.server.state, steps=steps, directive=directive)
            self._json(self.server.state.to_dict())
            return
        if self.path == "/api/reset":
            seed = int(payload.get("seed", 11))
            agent_count = int(payload.get("agent_count", 18))
            habitat_count = int(payload.get("habitat_count", 4))
            self.server.state = bootstrap_state(seed=seed, agent_count=agent_count, habitat_count=habitat_count)
            self._json(self.server.state.to_dict())
            return
        self._json({"error": "not_found"}, status=404)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the CongiNuroHub local server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8877)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--agents", type=int, default=18)
    parser.add_argument("--habitats", type=int, default=4)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), CongiNuroHubHandler)
    server.state = bootstrap_state(seed=args.seed, agent_count=args.agents, habitat_count=args.habitats)
    print(f"CongiNuroHub listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()