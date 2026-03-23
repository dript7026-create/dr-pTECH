from __future__ import annotations

import json
from pathlib import Path


REQUIRED_TOP_LEVEL = {
    "format",
    "metadata",
    "integrations",
    "rendering",
    "gameplay",
    "world",
    "player",
    "pets",
}


def validate_iig(document: dict) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_TOP_LEVEL.difference(document))
    if missing:
        errors.append(f"missing top-level sections: {', '.join(missing)}")

    format_block = document.get("format", {})
    if format_block.get("id") != "illusioninteractivegame":
        errors.append("format.id must equal 'illusioninteractivegame'")
    if format_block.get("extension") != ".iig":
        errors.append("format.extension must equal '.iig'")

    metadata = document.get("metadata", {})
    if not metadata.get("title"):
        errors.append("metadata.title is required")

    world = document.get("world", {})
    if not world.get("rooms"):
        errors.append("world.rooms must contain at least one room")
    else:
        room_ids = [room.get("id") for room in world.get("rooms", [])]
        if any(not room_id for room_id in room_ids):
            errors.append("each room must define a non-empty id")
        if len(room_ids) != len(set(room_ids)):
            errors.append("world.rooms contains duplicate room ids")
        if world.get("start_room") and world.get("start_room") not in set(room_ids):
            errors.append("world.start_room must match one of the declared room ids")

    player = document.get("player", {})
    if not player.get("loadout"):
        errors.append("player.loadout is required")

    pets = document.get("pets", {})
    if not pets.get("definitions"):
        errors.append("pets.definitions must contain at least one pet")
    else:
        pet_ids = {pet.get("id") for pet in pets.get("definitions", []) if pet.get("id")}
        loadout = player.get("loadout", {})
        for slot in ("burst", "chorus"):
            pet_id = loadout.get(slot)
            if pet_id and pet_id not in pet_ids:
                errors.append(f"player.loadout.{slot} must reference a declared pet id")

    milestones = document.get("gameplay", {}).get("milestones", [])
    if milestones and not isinstance(milestones, list):
        errors.append("gameplay.milestones must be a list when present")
    return errors


def load_iig(path: str | Path) -> dict:
    file_path = Path(path)
    document = json.loads(file_path.read_text(encoding="utf-8"))
    errors = validate_iig(document)
    if errors:
        raise ValueError(f"Invalid IIG document at {file_path}: {'; '.join(errors)}")
    return document


def save_iig(document: dict, path: str | Path) -> Path:
    file_path = Path(path)
    errors = validate_iig(document)
    if errors:
        raise ValueError(f"Cannot save invalid IIG document: {'; '.join(errors)}")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(document, indent=2), encoding="utf-8")
    return file_path