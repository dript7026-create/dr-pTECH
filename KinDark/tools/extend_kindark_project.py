from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GENERATED_DIR = ROOT / "generated"
GAME_DIR = ROOT / "game"
CONFIG_DIR = GAME_DIR / "config"
DATA_DIR = GAME_DIR / "data"
SCANTIDE_DIR = ROOT.parent / "ScanTide"

STORY_SUMMARY_PATH = GENERATED_DIR / "kin_dark_story_summary.json"
ASSET_SUMMARY_PATH = GENERATED_DIR / "kin_dark_asset_summary.json"
GAME_PROJECT_PATH = GENERATED_DIR / "kin_dark_game_project.json"
TUTORIAL_SUMMARY_PATH = GENERATED_DIR / "kin_dark_tutorial_slice.json"
SCANTIDE_BRIDGE_PATH = GENERATED_DIR / "kin_dark_scantide_bridge.json"

SCANTIDE_GATE_REPORT_PATH = SCANTIDE_DIR / "SCANTIDE_GATE_REPORT_CURRENT.txt"
SCANTIDE_BEAT_OUTLINE_PATH = SCANTIDE_DIR / "SCANTIDE_112_PAGE_BEAT_OUTLINE.md"
SCANTIDE_CHARACTER_BIBLE_PATH = SCANTIDE_DIR / "SCANTIDE_CHARACTER_BIBLE.txt"
SCANTIDE_MANUSCRIPT_PATH = SCANTIDE_DIR / "SCANTIDE_MANUSCRIPT_CURRENT_RUN.txt"

PROJECT_MANIFEST_PATH = GAME_DIR / "project_manifest.json"
BOOT_FLOW_PATH = CONFIG_DIR / "boot_flow.json"
CONTROLLER_LAYOUT_PATH = CONFIG_DIR / "xbox_series_controller.json"
WORLD_MANIFEST_PATH = DATA_DIR / "world_manifest.json"
ACTOR_PREFABS_PATH = DATA_DIR / "actor_prefab_contracts.json"
PRODUCTION_SCOPE_PATH = DATA_DIR / "production_scope.json"
TUTORIAL_SLICE_PATH = DATA_DIR / "tutorial_slice.json"


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def load_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def parse_scantide_gates(report_text: str) -> list[dict[str, object]]:
    gates: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    capture_condition = False
    condition_lines: list[str] = []

    for raw_line in report_text.splitlines():
        line = raw_line.strip()
        if line.startswith("# GATE-"):
            if current is not None:
                if condition_lines:
                    current["condition"] = " ".join(condition_lines).strip()
                gates.append(current)
            label = line[2:].strip()
            gate_id, _, title = label.partition(":")
            current = {
                "gate": gate_id.strip(),
                "title": title.strip(),
                "status": "UNKNOWN",
            }
            capture_condition = False
            condition_lines = []
            continue

        if current is None:
            continue

        if line.startswith("# STATUS:"):
            current["status"] = line.split(":", 1)[1].strip().strip("*")
            capture_condition = False
            continue

        if line.startswith("# Narrative condition:"):
            capture_condition = True
            condition_lines = []
            continue

        if capture_condition:
            if line.startswith("#"):
                condition_line = line[1:].strip()
                if condition_line:
                    condition_lines.append(condition_line)
            elif line:
                condition_lines.append(line)
            else:
                capture_condition = False

    if current is not None:
        if condition_lines:
            current["condition"] = " ".join(condition_lines).strip()
        gates.append(current)

    deduped: dict[tuple[str, str], dict[str, object]] = {}
    for gate in gates:
        key = (str(gate.get("gate", "")), str(gate.get("title", "")))
        deduped[key] = gate
    return list(deduped.values())


def first_nonempty_lines(text: str, count: int) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[:count]


def build_scantide_bridge() -> dict[str, object]:
    gate_report = load_text(SCANTIDE_GATE_REPORT_PATH)
    beat_outline = load_text(SCANTIDE_BEAT_OUTLINE_PATH)
    character_bible = load_text(SCANTIDE_CHARACTER_BIBLE_PATH)
    manuscript = load_text(SCANTIDE_MANUSCRIPT_PATH)
    gates = parse_scantide_gates(gate_report)

    return {
        "integrationMode": "saved_scantide_artifacts",
        "note": "Direct execution of a freshly built ScanTide binary is blocked on this workstation, so Kin Dark bridges to the saved local ScanTide outputs already present in the workspace.",
        "sourceFiles": {
            "gateReport": str(SCANTIDE_GATE_REPORT_PATH),
            "beatOutline": str(SCANTIDE_BEAT_OUTLINE_PATH),
            "characterBible": str(SCANTIDE_CHARACTER_BIBLE_PATH),
            "manuscriptCurrentRun": str(SCANTIDE_MANUSCRIPT_PATH),
        },
        "gateSummary": {
            "gateCount": len(gates),
            "passed": sum(1 for gate in gates if "PASSED" in str(gate.get("status", "")).upper()),
            "failed": sum(1 for gate in gates if "FAIL" in str(gate.get("status", "")).upper()),
            "gates": gates,
        },
        "beatOutlinePreview": first_nonempty_lines(beat_outline, 20),
        "characterBiblePreview": first_nonempty_lines(character_bible, 20),
        "manuscriptPreview": first_nonempty_lines(manuscript, 20),
    }


def build_project_outputs() -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object], dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    summary = load_json(STORY_SUMMARY_PATH)
    asset_summary = load_json(ASSET_SUMMARY_PATH)
    project = load_json(GAME_PROJECT_PATH)
    tutorial = load_json(TUTORIAL_SUMMARY_PATH)
    scantide_bridge = build_scantide_bridge()

    protagonists = project["protagonists"]
    world = project["world"]

    project_manifest = {
        "projectName": project["project_name"],
        "seed": project["seed"],
        "projectType": project["project_type"],
        "designIntent": project["design_intent"],
        "playtimeHours": project["playtime_hours"],
        "storySummary": str(STORY_SUMMARY_PATH.relative_to(ROOT)).replace("\\", "/"),
        "tutorialSlice": str(TUTORIAL_SLICE_PATH.relative_to(ROOT)).replace("\\", "/"),
        "assetSummary": str(ASSET_SUMMARY_PATH.relative_to(ROOT)).replace("\\", "/"),
        "scantideBridge": str(SCANTIDE_BRIDGE_PATH.relative_to(ROOT)).replace("\\", "/"),
        "graphicsManifest": project["graphics_manifest"],
        "audioManifest": project["audio_manifest"],
        "systems": project["systems"],
        "camera": project["camera"],
        "input": project["input"],
        "boot": project["boot"],
    }

    boot_flow = {
        "titleScreen": {
            "logoText": "Kin Dark",
            "style": "rusty blood-red sketch splatter",
            "menuOptions": ["Play Game"],
        },
        "saveBehavior": {
            "noSave": "launch_new_game_tutorial_slice_immediately",
            "existingSave": "continue_last_clean_quit_immediately",
        },
        "firstRunSequence": tutorial["sliceName"],
        "interactionRule": {
            "button": "A",
            "mode": "adaptive_context_action",
            "holdSeconds": 1.0,
        },
    }

    controller_layout = {
        "profile": "xbox_series_default",
        "movement": {"axis": "left_stick", "mode": "omnidirectional"},
        "aim": {"axis": "right_stick", "mode": "reticle_and_camera_bias"},
        "focus": {"button": "LT", "effect": "zoom_and_soft_lock"},
        "primaryAttack": {"button": "RT"},
        "modifiers": [
            {"button": "LB", "usage": "stance_or_power_modifier"},
            {"button": "RB", "usage": "stance_or_power_modifier"}
        ],
        "actionCluster": ["X", "Y", "B"],
        "map": "View",
        "menu": "Menu",
    }

    world_manifest = {
        "mapType": world["map_type"],
        "districts": world["districts"],
        "institutions": world["institutions"],
        "bosses": world["bosses"],
        "tone": "light-hearted comic grimness with morally challenging urban cryptid horror",
        "environmentConstruction": {
            "geometry": "sprite_assembled_3d_shapes",
            "textures": "artificially_generated_surface_photographs",
            "detailDirection": "lush_extravagantly_expressionistic_dark_detail"
        }
    }

    actor_prefabs = {
        "protagonists": protagonists,
        "sharedActorRules": {
            "rendering": "2d_high_definition_comicbook_fluid_motion_prefabs_in_simulated_3d_space",
            "facing": "8_way_omnidirectional",
            "cameraRelationship": "behind_player_body_with_reticle_bias",
            "interactionVfxCoverage": True
        }
    }

    production_scope = {
        "graphics": asset_summary["graphicsCategories"],
        "graphicsTarget": asset_summary["graphicsTarget"],
        "audio": asset_summary["audioCategories"],
        "audioTarget": asset_summary["audioTarget"],
        "loopingSongs": asset_summary["loopingSongs"],
        "plotArcCount": summary["plotArcCount"],
        "districtCount": summary["districtCount"],
        "bossCount": summary["bossCount"],
        "notableNpcCount": summary["notableNpcCount"],
        "enemySpeciationCount": summary["enemySpeciationCount"],
        "tutorialSlice": {
            "name": tutorial["sliceName"],
            "beats": len(tutorial["beats"]),
            "playtimeMinutes": tutorial["playtimeMinutes"],
        },
        "scantide": {
            "mode": scantide_bridge["integrationMode"],
            "passedGates": scantide_bridge["gateSummary"]["passed"],
            "failedGates": scantide_bridge["gateSummary"]["failed"]
        }
    }

    return project_manifest, boot_flow, controller_layout, world_manifest, actor_prefabs, production_scope, tutorial, scantide_bridge


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    project_manifest, boot_flow, controller_layout, world_manifest, actor_prefabs, production_scope, tutorial_slice, scantide_bridge = build_project_outputs()
    write_json(PROJECT_MANIFEST_PATH, project_manifest)
    write_json(BOOT_FLOW_PATH, boot_flow)
    write_json(CONTROLLER_LAYOUT_PATH, controller_layout)
    write_json(WORLD_MANIFEST_PATH, world_manifest)
    write_json(ACTOR_PREFABS_PATH, actor_prefabs)
    write_json(PRODUCTION_SCOPE_PATH, production_scope)
    write_json(TUTORIAL_SLICE_PATH, tutorial_slice)
    write_json(SCANTIDE_BRIDGE_PATH, scantide_bridge)
    print(json.dumps({
        "projectManifest": str(PROJECT_MANIFEST_PATH),
        "bootFlow": str(BOOT_FLOW_PATH),
        "controllerLayout": str(CONTROLLER_LAYOUT_PATH),
        "worldManifest": str(WORLD_MANIFEST_PATH),
        "actorPrefabs": str(ACTOR_PREFABS_PATH),
        "productionScope": str(PRODUCTION_SCOPE_PATH),
        "tutorialSlice": str(TUTORIAL_SLICE_PATH),
        "scantideBridge": str(SCANTIDE_BRIDGE_PATH)
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
