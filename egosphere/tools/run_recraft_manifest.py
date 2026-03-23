import argparse
import base64
import json
import os
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
API_URL = "https://external.api.recraft.ai/v1/images/generations"
API_KEY_ENV = "RECRAFT_API_KEY"
SAFE_GENERATION_SIZE = os.environ.get("RECRAFT_SAFE_SIZE", "1024x1024")


def is_pending(item: dict, project_root: Path) -> bool:
    out_path = project_root / item["out"]
    return not out_path.exists()


def load_manifest(path: Path) -> tuple[list[dict], Path, dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        items = raw.get("assets", [])
        output_root = Path(raw.get("output_root", "."))
        project_root = (path.parent / output_root).resolve()
        metadata = {key: value for key, value in raw.items() if key != "assets"}
        return items, project_root, metadata
    if isinstance(raw, list):
        return raw, path.parent, {}
    raise ValueError(f"Unsupported manifest shape in {path}")


def generate_one(item: dict, project_root: Path) -> dict:
    api_key = os.environ.get(API_KEY_ENV)
    if not api_key:
        return {"name": item["name"], "status": "skipped", "reason": "missing_api_key"}

    target_width = int(item.get("w", 1024))
    target_height = int(item.get("h", 1024))
    payload = {
        "prompt": item["prompt"],
        "model": item.get("model", "recraftv4"),
        "size": SAFE_GENERATION_SIZE,
        "n": 1,
        "response_format": "b64_json",
    }
    if "style" in item:
        payload["style"] = item["style"]
    if "style_id" in item:
        payload["style_id"] = item["style_id"]

    controls = {}
    if item.get("transparent_background"):
        controls["transparent_background"] = True
    if controls:
        payload["controls"] = controls

    model_name = str(payload["model"]).lower()
    if item.get("negative_prompt") and model_name != "recraftv4":
        payload["negative_prompt"] = item["negative_prompt"]

    response = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=180,
    )
    if response.status_code >= 400:
        return {
            "name": item["name"],
            "status": "failed",
            "reason": "http_error",
            "code": response.status_code,
            "detail": response.text[:1200],
        }

    body = response.json()
    data_block = body.get("data")
    if not data_block:
        return {"name": item["name"], "status": "failed", "reason": "missing_data_block"}

    payload_item = data_block[0]
    image_blob = payload_item.get("b64_json") or payload_item.get("image")
    if not image_blob:
        return {
            "name": item["name"],
            "status": "failed",
            "reason": "missing_image_payload",
            "detail": json.dumps(payload_item)[:800],
        }

    image = Image.open(BytesIO(base64.b64decode(image_blob))).convert("RGBA")
    if image.size != (target_width, target_height):
        image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
    out_path = project_root / item["out"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path)
    return {"name": item["name"], "status": "generated", "out": str(out_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a Recraft generation manifest if credentials are available")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    items, project_root, metadata = load_manifest(args.manifest)
    items = [item for item in items if is_pending(item, project_root)]
    if args.limit > 0:
        items = items[:args.limit]

    results = [generate_one(item, project_root) for item in items]
    payload = {"results": results}
    if metadata:
        payload["manifest"] = {
            "name": metadata.get("manifest_name"),
            "version": metadata.get("manifest_version"),
            "budget": metadata.get("budget"),
        }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())