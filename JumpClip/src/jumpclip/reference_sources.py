from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path

import requests

from .models import ReferenceImage


OPENVERSE_ENDPOINT = "https://api.openverse.org/v1/images/"
WIKIMEDIA_ENDPOINT = "https://commons.wikimedia.org/w/api.php"


def _clean_text(text: str | None) -> str | None:
    if not text:
        return None
    text = unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip() or None


def search_openverse(query: str, page_size: int = 20) -> list[ReferenceImage]:
    response = requests.get(
        OPENVERSE_ENDPOINT,
        params={"q": query, "page_size": page_size, "license_type": "commercial"},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    results = []
    for item in payload.get("results", []):
        results.append(
            ReferenceImage(
                provider="openverse",
                identifier=str(item.get("id", "")),
                title=item.get("title") or "Untitled",
                image_url=item.get("url"),
                source_url=item.get("foreign_landing_url"),
                license_name=item.get("license"),
                creator=item.get("creator"),
                tags=[tag.get("name", "") for tag in item.get("tags", []) if tag.get("name")],
                width=item.get("width"),
                height=item.get("height"),
            )
        )
    return results


def search_wikimedia(query: str, page_size: int = 20) -> list[ReferenceImage]:
    response = requests.get(
        WIKIMEDIA_ENDPOINT,
        params={
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": 6,
            "gsrlimit": page_size,
            "prop": "imageinfo|info",
            "iiprop": "url|size|extmetadata",
            "inprop": "url",
            "format": "json",
            "origin": "*",
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    pages = payload.get("query", {}).get("pages", {})
    results = []
    for page in pages.values():
        image_info = (page.get("imageinfo") or [{}])[0]
        metadata = image_info.get("extmetadata") or {}
        results.append(
            ReferenceImage(
                provider="wikimedia",
                identifier=str(page.get("pageid", "")),
                title=page.get("title", "File").replace("File:", ""),
                image_url=image_info.get("url"),
                source_url=page.get("fullurl"),
                license_name=_clean_text((metadata.get("LicenseShortName") or {}).get("value")),
                creator=_clean_text((metadata.get("Artist") or {}).get("value")),
                tags=[query],
                width=image_info.get("width"),
                height=image_info.get("height"),
            )
        )
    return results


def write_manifest(references: list[ReferenceImage], out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "references": [reference.to_dict() for reference in references],
        "count": len(references),
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path


def load_manifest(path: Path) -> list[ReferenceImage]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [ReferenceImage(**item) for item in payload.get("references", [])]
