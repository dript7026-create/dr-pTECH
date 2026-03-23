import base64
import json
import os
import sys
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image, ImageOps


API_ENDPOINT = "https://external.api.recraft.ai/v1/images/generations"
DEFAULT_MODEL = "recraftv4"
DEFAULT_RESPONSE_FORMAT = "b64_json"
SAFE_GENERATION_SIZE = "1024x1024"


def load_manifest(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Manifest root must be a JSON array")
    return data


def resolve_generation_size(width: int, height: int) -> str:
    explicit_size = os.environ.get("RECRAFT_SAFE_SIZE")
    if explicit_size:
        return explicit_size
    return SAFE_GENERATION_SIZE


def fetch_image_bytes(api_key: str, prompt: str, width: int, height: int, extra_body: dict | None):
    payload = {
        "prompt": prompt,
        "n": 1,
        "model": os.environ.get("RECRAFT_MODEL", DEFAULT_MODEL),
        "response_format": os.environ.get("RECRAFT_RESPONSE_FORMAT", DEFAULT_RESPONSE_FORMAT),
        "size": resolve_generation_size(width, height),
    }
    if extra_body:
        payload.update(extra_body)

    response = requests.post(
        API_ENDPOINT,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        data=json.dumps(payload),
        timeout=180,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Recraft error {response.status_code}: {response.text[:1200]}")
    data = response.json().get("data")
    item = data[0] if isinstance(data, list) and data else data
    if not item:
        raise RuntimeError("No image data returned from Recraft")

    b64_json = item.get("b64_json") or item.get("image")
    if isinstance(b64_json, str):
        return base64.b64decode(b64_json)

    url = item.get("url")
    if isinstance(url, str):
        image_response = requests.get(url, headers={"Authorization": f"Bearer {api_key}"}, timeout=180)
        image_response.raise_for_status()
        return image_response.content

    raise RuntimeError(f"Unsupported response payload keys: {list(item.keys())}")


def fit_image(image: Image.Image, width: int, height: int) -> Image.Image:
    if image.size == (width, height):
        return image
    return ImageOps.fit(image, (width, height), Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def save_image(bytes_data: bytes, out_path: Path, width: int, height: int):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.open(BytesIO(bytes_data)).convert("RGBA")
    image = fit_image(image, width, height)
    image.save(out_path)


def main():
    if len(sys.argv) != 2:
        print("Usage: generate_orbengine_demo_assets.py <manifest.json>")
        return 1

    api_key = os.environ.get("RECRAFT_API_KEY")
    if not api_key:
        print("RECRAFT_API_KEY is not set.")
        return 2

    manifest_path = Path(sys.argv[1]).resolve()
    manifest = load_manifest(manifest_path)

    for entry in manifest:
        prompt = entry["prompt"]
        width = int(entry["w"])
        height = int(entry["h"])
        out_path = (manifest_path.parent / entry["out"]).resolve()
        extra_body = entry.get("extra_body")
        name = entry.get("name", out_path.stem)
        print(f"Generating {name} -> {out_path}")
        image_bytes = fetch_image_bytes(api_key, prompt, width, height, extra_body)
        save_image(image_bytes, out_path, width, height)

    print("Asset generation completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())