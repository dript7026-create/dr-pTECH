from __future__ import annotations

import json
import threading
import urllib.request

from http.server import ThreadingHTTPServer

from NeoWakeUP.neowakeup import api_server


def test_neowakeup_api_smoke(tmp_path, monkeypatch):
    state_file = tmp_path / "planetary_mind.json"
    monkeypatch.setattr(api_server, "STATE_FILE", state_file)

    server = ThreadingHTTPServer(("127.0.0.1", 0), api_server.NeoWakeUPHandler)
    server.engine_state = api_server.build_server_state()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        base = f"http://127.0.0.1:{server.server_port}"
        health = json.loads(urllib.request.urlopen(f"{base}/health", timeout=5).read().decode("utf-8"))
        assert health["ok"] is True

        state = json.loads(urllib.request.urlopen(f"{base}/planetary/state", timeout=5).read().decode("utf-8"))
        assert "regions" in state
        assert "planetary_coherence" in state

        request = urllib.request.Request(
            f"{base}/planetary/step",
            data=json.dumps({"novelty": 0.8, "equity": 0.7, "resilience": 0.75, "speed": 0.6}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        report = json.loads(urllib.request.urlopen(request, timeout=5).read().decode("utf-8"))
        assert "directive" in report
        assert state_file.exists()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)