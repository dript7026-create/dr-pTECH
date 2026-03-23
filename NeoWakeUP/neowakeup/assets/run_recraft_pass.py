"""Run a NeoWakeUP Recraft manifest with metadata support."""

from __future__ import annotations

import argparse
import base64
import json
import os
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image


API_URL = "https://external.api.recraft.ai/v1/images/generations"
API_KEY_ENV = "RECRAFT_API_KEY"


def _load_assets(manifest_path: Path) -> tuple[Path, list[dict], dict]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return manifest_path.parent, payload, {}
    assets = payload.get("assets", []) if isinstance(payload, dict) else []
    return manifest_path.parent, assets, payload if isinstance(payload, dict) else {}


def _generate_one(item: dict, project_root: Path) -> dict:
    api_key = os.environ.get(API_KEY_ENV)
    if not api_key:
        return {"name": item["name"], "status": "skipped", "reason": "missing_api_key"}
    out_path = project_root / item["out"]
    if out_path.exists():
        return {"name": item["name"], "status": "existing", "out": str(out_path)}
    payload = {
        "prompt": item["prompt"],
        "model": item.get("model", "recraftv4"),
        "size": f"{item.get('w', 1024)}x{item.get('h', 1024)}",
        "n": 1,
        "response_format": "b64_json",
    }
    response = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=120,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError:
        return {
            "name": item["name"],
            "status": "error",
            "reason": f"http_{response.status_code}",
            "body": response.text[:4000],
        }
    data = response.json()["data"][0]["b64_json"]
    image = Image.open(BytesIO(base64.b64decode(data))).convert("RGBA")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path)
    return {"name": item["name"], "status": "generated", "out": str(out_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a NeoWakeUP Recraft manifest")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    project_root, assets, meta = _load_assets(args.manifest)
    if args.limit > 0:
        assets = assets[:args.limit]
    if meta:
        print(json.dumps({"manifest_name": meta.get("manifest_name"), "budget": meta.get("budget")}, indent=2))
    results = [_generate_one(item, project_root) for item in assets]
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())