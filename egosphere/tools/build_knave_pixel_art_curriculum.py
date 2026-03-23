import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT / "pipeline" / "projects" / "knave_prototype"
CURRICULUM_PATH = PROJECT_ROOT / "pixel_art_history_curriculum.json"
CORPUS_PATH = PROJECT_ROOT / "knave_ml_training_corpus.jsonl"
MODEL_PATH = PROJECT_ROOT / "knave_asset_generator_model.json"


PIXEL_ART_HISTORY = [
    {
        "era": "arcade_1978_1985",
        "title": "Arcade Readability",
        "summary": "Early arcade pixel art prioritized fast silhouette recognition, two-tone grouping, and immediate state readability under low resolution and bright cabinet conditions.",
        "craft_principles": [
            "clear silhouettes",
            "high contrast",
            "instant player-state readability",
            "limited palette discipline",
        ],
        "axis_bias": {
            "silhouette_readability": 1.0,
            "material_storytelling": 0.1,
            "animation_density": 0.4,
            "environment_depth": 0.1,
            "fx_legibility": 0.5,
            "ui_authorship": 0.2,
        },
    },
    {
        "era": "nes_master_system_1985_1990",
        "title": "Iconic 8-bit Economy",
        "summary": "8-bit home-console art matured icon economy, tile reuse, sprite-state clarity, and compact environmental storytelling through efficient clusters.",
        "craft_principles": [
            "tile economy",
            "cluster discipline",
            "animation shorthand",
            "shape-first design",
        ],
        "axis_bias": {
            "silhouette_readability": 0.9,
            "material_storytelling": 0.2,
            "animation_density": 0.45,
            "environment_depth": 0.2,
            "fx_legibility": 0.4,
            "ui_authorship": 0.25,
        },
    },
    {
        "era": "snes_megadrive_1990_1995",
        "title": "16-bit Motion and Layering",
        "summary": "16-bit craft expanded animation timing, layered backgrounds, richer palettes, and stronger mood while preserving gameplay readability.",
        "craft_principles": [
            "parallax staging",
            "clean timing bands",
            "palette ramp control",
            "foreground-midground-backdrop logic",
        ],
        "axis_bias": {
            "silhouette_readability": 0.7,
            "material_storytelling": 0.45,
            "animation_density": 0.8,
            "environment_depth": 0.75,
            "fx_legibility": 0.55,
            "ui_authorship": 0.35,
        },
    },
    {
        "era": "neo_geo_fighting_1992_1999",
        "title": "Prestige Combat Spritecraft",
        "summary": "High-end fighting and action spritecraft pushed animation density, combat telegraphing, premium silhouette breakup, and authored impact effects.",
        "craft_principles": [
            "combat pose readability",
            "anticipation and follow-through",
            "premium character rendering",
            "impact taxonomy",
        ],
        "axis_bias": {
            "silhouette_readability": 0.8,
            "material_storytelling": 0.5,
            "animation_density": 1.0,
            "environment_depth": 0.25,
            "fx_legibility": 0.9,
            "ui_authorship": 0.3,
        },
    },
    {
        "era": "pc_dos_vga_1991_1998",
        "title": "Atmosphere and Material Suggestion",
        "summary": "PC VGA pixel art developed nuanced material suggestion, moody environments, and painterly lighting in adventure and role-playing games.",
        "craft_principles": [
            "material suggestion",
            "mood lighting",
            "environmental storytelling",
            "controlled texture density",
        ],
        "axis_bias": {
            "silhouette_readability": 0.45,
            "material_storytelling": 0.9,
            "animation_density": 0.35,
            "environment_depth": 0.65,
            "fx_legibility": 0.35,
            "ui_authorship": 0.45,
        },
    },
    {
        "era": "gba_ds_2001_2010",
        "title": "Portable Premium Constraints",
        "summary": "Portable-era pixel art balanced small-screen readability with premium layering, character identity, and efficient interface hierarchy.",
        "craft_principles": [
            "small-screen readability",
            "clean UI hierarchy",
            "modular animation sets",
            "portable palette contrast",
        ],
        "axis_bias": {
            "silhouette_readability": 0.75,
            "material_storytelling": 0.4,
            "animation_density": 0.65,
            "environment_depth": 0.4,
            "fx_legibility": 0.55,
            "ui_authorship": 0.8,
        },
    },
    {
        "era": "indie_pixel_2010_2026",
        "title": "Modern Prestige Pixel Art",
        "summary": "Modern pixel art combines historical readability discipline with premium atmospheric layering, authored UI, cinematic framing, and strong thematic cohesion.",
        "craft_principles": [
            "historical synthesis",
            "premium authorship",
            "atmospheric layering",
            "intentional restraint",
        ],
        "axis_bias": {
            "silhouette_readability": 0.85,
            "material_storytelling": 0.8,
            "animation_density": 0.8,
            "environment_depth": 0.85,
            "fx_legibility": 0.7,
            "ui_authorship": 0.9,
        },
    },
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_knave_components() -> list[dict]:
    payload = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    return payload["designer_components"]


def build_corpus(curriculum: list[dict], components: list[dict]) -> list[dict]:
    corpus = []
    for entry in curriculum:
        corpus.append(
            {
                "source_type": "pixel_art_history",
                "id": entry["era"],
                "text": f"{entry['title']} {entry['summary']} {' '.join(entry['craft_principles'])}",
                "component_tags": entry["craft_principles"],
                "targets": entry["axis_bias"],
                "godai_bias": {
                    "pressure": round(0.9 + entry["axis_bias"]["animation_density"] * 0.25, 3),
                    "mercy": round(1.15 - entry["axis_bias"]["fx_legibility"] * 0.15, 3),
                    "novelty": round(0.95 + entry["axis_bias"]["ui_authorship"] * 0.2, 3),
                },
            }
        )
    for component in components:
        targets = {axis_name: 0.0 for axis_name in curriculum[0]["axis_bias"].keys()}
        for axis_name in component["advanced_axes"]:
            targets[axis_name] = 1.0
        corpus.append(
            {
                "source_type": "knave_component",
                "id": component["asset_id"],
                "text": component["compiled_prompt"],
                "component_tags": component["component_tags"],
                "targets": targets,
                "godai_bias": component["godai_weights"],
            }
        )
    return corpus


def main() -> int:
    ensure_dir(PROJECT_ROOT)
    components = load_knave_components()
    corpus = build_corpus(PIXEL_ART_HISTORY, components)
    CURRICULUM_PATH.write_text(json.dumps(PIXEL_ART_HISTORY, indent=2) + "\n", encoding="utf-8")
    with CORPUS_PATH.open("w", encoding="utf-8") as handle:
        for row in corpus:
            handle.write(json.dumps(row) + "\n")
    summary = {
        "curriculum_path": str(CURRICULUM_PATH),
        "corpus_path": str(CORPUS_PATH),
        "history_entries": len(PIXEL_ART_HISTORY),
        "component_entries": len(components),
        "training_examples": len(corpus),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())