#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STREAMLINE_DIR = ROOT / "drIpTECH" / "ReCraftGenerationStreamline"
MANIFEST = STREAMLINE_DIR / "tommybeta_full_replacement_manifest_4100.json"
HELPER = STREAMLINE_DIR / "generate_orbengine_demo_assets.py"

CURRENT_TITLE = "Tommy: Gun"
BETA_TITLE = "ThompSonBeta"

GLOBAL_PIXEL_RULES = (
    "Strict original DMG and early GBA compliant pixel-art direction, orthographic top-down gameplay view, "
    "square pixel proportions, chunky 4-shade readability, no vertical squash, no tall stretched anatomy, "
    "no painterly gradients, no soft airbrushing, no blurry upscale, no side-view posing unless explicitly cinematic."
)

NOMENCLATURE_RULES = (
    "Use current nomenclature consistently: Tommy: Gun is the current GBA title, ThompSonBeta is the beta lineage, "
    "and avoid legacy TommyBeta or Tommy Goomba wording in the generated art itself."
)

ARCHETYPE_HIERARCHY_RULES = (
    "Build from a coherent specialization hierarchy: KaijuGaiden beta-era GB archetypes define compact silhouette logic and "
    "grounded duel spacing, while Tommy: Gun on GBA expands that same real-world gameplay grammar into richer color, clearer UI, "
    "and stronger encounter archetypes without losing systemic readability."
)

PHILOSOPHY_RULES = (
    "Overall philosophy: anime-ified, chibi-cute but slightly grotesque, vibrant highlight colors over grim dark tone, "
    "with restrained mobster cyber-noir flair and expressive but non-gory combat readability."
)

DUEL_RULES = (
    "Combat philosophy: stance balance, demeanour-protocol compliance, and stand-off stalemate duels like a high-noon western, "
    "where rapid shootout-like bursts happen only after one fighter breaks form."
)

RESCUE_STAKES_RULES = (
    "Keep Tommy's core narrative stakes intact as a player-driven rescue objective, presenting the abduction-and-rescue motivation with restraint, resolve, and no exploitative framing."
)

UI_RULES = (
    "Use crisp handheld-era UI blocks, bold outlines, compact glyph-safe shapes, and a restrained 4-shade palette so the sheet survives downsampling cleanly."
)

ENVIRONMENT_RULES = (
    "Build everything from a 16x16 modular tile logic with seamless neighbor transitions, shared ground materials, coherent path widths, "
    "consistent fungus-root-stone language, and no perspective skew."
)

ILLUSTRATION19_RULES = (
    "Follow the Illustration19 layout philosophy as a chunky overhead map language: readable lanes first, strong traversal landmarks, "
    "large cap-and-root masses, and seamless tile-to-tile translation between screens."
)

TOMMY_RULES = (
    "Tommy should match the Illustration18 reference direction as a compact stout hero with a broad cap-like head mass, short limbs, centered weight, "
    "clear bite-forward silhouette, and stable proportions across every frame. He is now framed under the Tommy: Gun identity with reluctant-duelist tension, "
    "more aggressive stance language than before but without eager bloodlust."
)

MAREAOU_RULES = (
    "Mareaou should match the Illustration23 reference direction as Tommy's coherent rival: similar world-language and sprite density, "
    "but leaner, sharper, more regal and menacing without leaving the same pixel-art family. Present Mareaou as an anime-styled rival duelist who also hesitates before violence, "
    "maintaining emotional tension instead of feral brutality."
)

CHARACTER_RULES = (
    "Keep each animation frame locked to a stable top-down sprite baseline with consistent head-to-body ratio, readable limb separation, and no elastic deformation."
)

FX_RULES = (
    "Effects must read as simple handheld-era pixel bursts with clean silhouettes, limited shade steps, and motion designed for gameplay readability over spectacle."
)

STRIP_LAYOUT_RULES = (
    "The source canvas will be square, so place the full sheet content inside a centered horizontal band through the middle of the image, with quiet padding above and below for a safe strip crop."
)

FULLSCREEN_LAYOUT_RULES = (
    "The source canvas will be square, so keep all critical landmarks inside a centered 3:2 safe crop area that will survive conversion to the gameplay screen without losing composition."
)


def normalize_nomenclature(text: str) -> str:
    replacements = [
        ("Tommy Goomba concept art", f"{CURRENT_TITLE} concept art"),
        ("TommyBeta Tommy", f"{CURRENT_TITLE} protagonist"),
        ("TommyBeta Mareaou", f"{CURRENT_TITLE} Mareaou"),
        ("TommyBeta", CURRENT_TITLE),
        ("Tommy Goomba", CURRENT_TITLE),
        ("tommy beta", BETA_TITLE),
    ]
    normalized = text
    for old, new in replacements:
        normalized = normalized.replace(old, new)
    return normalized

TRANSPARENT_OUT_NAMES = {
    "status_icon_sheet",
    "special_icon_sheet",
    "special_acquisition_icon_sheet",
    "roaming_creatures_sheet",
}


def load_manifest(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def with_sentence(base: str, extra: str) -> str:
    if extra in base:
        return base
    base = base.strip()
    if base and not base.endswith((".", "!", "?")):
        base += "."
    return f"{base} {extra}".strip()


def should_force_transparency(entry: dict) -> bool:
    out_path = entry.get("out", "")
    name = entry.get("name", "")
    return (
        "/characters/" in out_path
        or "/fx/" in out_path
        or name in TRANSPARENT_OUT_NAMES
        or "transparent background" in entry.get("prompt", "").lower()
        or out_path.endswith("environmental_objects_sheet_a.png")
        or out_path.endswith("environmental_objects_sheet_b.png")
        or out_path.endswith("edge_gate_portal_checkpoint_sheet.png")
        or out_path.endswith("puzzle_and_healing_objects_sheet.png")
    )


def enrich_entry(entry: dict) -> dict:
    updated = deepcopy(entry)
    prompt = normalize_nomenclature(updated["prompt"])
    name = updated.get("name", "")
    out_path = updated.get("out", "")

    prompt = with_sentence(prompt, GLOBAL_PIXEL_RULES)
    prompt = with_sentence(prompt, NOMENCLATURE_RULES)
    prompt = with_sentence(prompt, ARCHETYPE_HIERARCHY_RULES)
    prompt = with_sentence(prompt, PHILOSOPHY_RULES)

    if "/ui/" in out_path:
        prompt = with_sentence(prompt, UI_RULES)

    if "/quadrants/" in out_path or "/environment/" in out_path:
        prompt = with_sentence(prompt, ENVIRONMENT_RULES)
        prompt = with_sentence(prompt, ILLUSTRATION19_RULES)
        prompt = with_sentence(prompt, DUEL_RULES)

    width = int(updated.get("w", 1024))
    height = int(updated.get("h", 1024))
    if width > height:
        prompt = with_sentence(prompt, STRIP_LAYOUT_RULES)
    if width == 240 and height == 160:
        prompt = with_sentence(prompt, FULLSCREEN_LAYOUT_RULES)

    if name.startswith("tommy_"):
        prompt = with_sentence(prompt, CHARACTER_RULES)
        prompt = with_sentence(prompt, TOMMY_RULES)
        prompt = with_sentence(prompt, DUEL_RULES)
        prompt = with_sentence(prompt, RESCUE_STAKES_RULES)

    if name.startswith("mareaou_"):
        prompt = with_sentence(prompt, CHARACTER_RULES)
        prompt = with_sentence(prompt, MAREAOU_RULES)
        prompt = with_sentence(prompt, DUEL_RULES)

    if "/fx/" in out_path:
        prompt = with_sentence(prompt, FX_RULES)

    if "/cinematics/" in out_path:
        prompt = with_sentence(prompt, RESCUE_STAKES_RULES)
        prompt = with_sentence(prompt, DUEL_RULES)

    updated["prompt"] = prompt

    if should_force_transparency(updated):
        extra_body = deepcopy(updated.get("extra_body", {}))
        controls = deepcopy(extra_body.get("controls", {}))
        controls["transparent_background"] = True
        extra_body["controls"] = controls
        updated["extra_body"] = extra_body

    return updated


def prepare_manifest(manifest):
    return [enrich_entry(entry) for entry in manifest]


def print_summary(manifest, manifest_path: Path):
    print(f"{CURRENT_TITLE} Recraft asset batch")
    print(f"Manifest: {manifest_path}")
    print(f"Entries: {len(manifest)}")
    for entry in manifest:
        print(f" - {entry['name']}: {entry['w']}x{entry['h']} -> {entry['out']}")


def slice_manifest(manifest, start_name):
    if not start_name:
        return manifest
    for index, entry in enumerate(manifest):
        if entry["name"] == start_name:
            return manifest[index:]
    raise ValueError(f"start asset '{start_name}' not found in manifest")


def filter_missing(manifest, manifest_path: Path):
    missing = []
    for entry in manifest:
        out_path = (manifest_path.parent / entry["out"]).resolve()
        if not out_path.exists():
            missing.append(entry)
    return missing


def run_generation(manifest):
    env = os.environ.copy()
    with tempfile.NamedTemporaryFile("w", suffix=".json", dir=str(STREAMLINE_DIR), delete=False, encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        temp_manifest = handle.name
    cmd = [sys.executable, str(HELPER), temp_manifest]
    try:
        return subprocess.call(cmd, cwd=str(STREAMLINE_DIR), env=env)
    finally:
        try:
            os.unlink(temp_manifest)
        except OSError:
            pass


def main(argv):
    start_name = None
    manifest_path = MANIFEST
    missing_only = "--missing-only" in argv
    if "--manifest" in argv:
        at = argv.index("--manifest")
        if at + 1 >= len(argv):
            print("--manifest requires a path")
            return 4
        manifest_path = Path(argv[at + 1]).resolve()

    if "--from" in argv:
        at = argv.index("--from")
        if at + 1 >= len(argv):
            print("--from requires an asset name")
            return 3
        start_name = argv[at + 1]

    manifest = load_manifest(manifest_path)
    manifest = prepare_manifest(manifest)
    manifest = slice_manifest(manifest, start_name)
    if missing_only:
        manifest = filter_missing(manifest, manifest_path)
    dry_run = "--dry-run" in argv
    print_summary(manifest, manifest_path)
    if dry_run:
        print("\nDry run only. No API calls made.")
        return 0

    if not os.environ.get("RECRAFT_API_KEY"):
        print("\nRECRAFT_API_KEY is not set in this shell.")
        print("Set the key, then rerun this tool.")
        return 2

    return run_generation(manifest)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))