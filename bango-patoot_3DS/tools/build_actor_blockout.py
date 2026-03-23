from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GENERATED = ROOT / "generated" / "windows_preview"
RIGS = ROOT / "rigs" / "entity_rigs.json"
POSE_TEMPLATE = ROOT / "pose_imports" / "pose_import_template.json"
SYMBOLS = ROOT / "generated" / "reconstruction_preview" / "bango" / "symbol_objects.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def normalized_entity_lookup(rigs: dict, target: str) -> dict:
    target_key = target.lower()
    for skeleton in rigs["skeletons"]:
        if skeleton["entity"].lower() == target_key:
            return skeleton
    raise KeyError(target)


def infer_bone_index(symbol: dict, bones: list[dict], frame_width: float, frame_height: float) -> int:
    cx = symbol["centroid"][0]
    cy = symbol["centroid"][1]
    best_index = 0
    best_dist = 1e9
    for index, bone in enumerate(bones):
        bx = frame_width * 0.5 + float(bone["x"])
        by = frame_height * 0.72 - float(bone["y"])
        dist = (cx - bx) ** 2 + (cy - by) ** 2
        if dist < best_dist:
            best_dist = dist
            best_index = index
    return best_index


def color_to_ints(color_triplet: list[float]) -> tuple[int, int, int]:
    return tuple(max(0, min(255, int(round(value)))) for value in color_triplet)


def build_sections(symbols: list[dict], bones: list[dict]) -> list[dict]:
    front_symbols = [symbol for symbol in symbols if symbol["centroid"][0] < 128.0]
    sections = []
    for symbol in front_symbols:
        bbox = symbol["bounding_box"]
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        bone_index = infer_bone_index(symbol, bones, 128.0, 192.0)
        red, green, blue = color_to_ints(symbol["primary_color_family"])
        sections.append({
            "name": symbol["symbol_id"],
            "bone_index": bone_index,
            "offset_x": round((symbol["centroid"][0] - 64.0) / 24.0, 4),
            "offset_y": round((160.0 - symbol["centroid"][1]) / 28.0, 4),
            "offset_z": round((symbol["thickness_hint"] * 0.04), 4),
            "half_x": round(max(0.08, width / 52.0), 4),
            "half_y": round(max(0.08, height / 54.0), 4),
            "half_z": round(max(0.06, symbol["thickness_hint"] / 18.0), 4),
            "color": [red, green, blue],
            "material": symbol["material_family"],
        })
    return sections


def build_pose_chain(bones: list[dict], pose_template: dict) -> dict:
    bone_names = [bone["name"] for bone in bones]
    default_frame = {name: {"rotation": 0.0, "offset_x": 0.0, "offset_y": 0.0} for name in bone_names}
    attack_frame = {name: {"rotation": 0.0, "offset_x": 0.0, "offset_y": 0.0} for name in bone_names}
    for name, values in pose_template["bone_offsets"].items():
        if name in attack_frame:
            attack_frame[name] = {
                "rotation": float(values.get("rotation", 0.0)),
                "offset_x": float(values.get("x", 0.0)) / 18.0,
                "offset_y": float(values.get("y", 0.0)) / 18.0,
            }
    locomotion_a = {name: {"rotation": 0.0, "offset_x": 0.0, "offset_y": 0.0} for name in bone_names}
    locomotion_b = {name: {"rotation": 0.0, "offset_x": 0.0, "offset_y": 0.0} for name in bone_names}
    locomotion_a["leg_l"] = {"rotation": 18.0, "offset_x": -0.1, "offset_y": -0.08}
    locomotion_a["leg_r"] = {"rotation": -22.0, "offset_x": 0.12, "offset_y": 0.03}
    locomotion_a["arm_l"] = {"rotation": -20.0, "offset_x": -0.14, "offset_y": 0.04}
    locomotion_a["arm_r"] = {"rotation": 18.0, "offset_x": 0.1, "offset_y": 0.0}
    locomotion_a["spine"] = {"rotation": 6.0, "offset_x": 0.0, "offset_y": 0.05}
    locomotion_b["leg_l"] = {"rotation": -20.0, "offset_x": 0.08, "offset_y": 0.03}
    locomotion_b["leg_r"] = {"rotation": 18.0, "offset_x": -0.1, "offset_y": -0.08}
    locomotion_b["arm_l"] = {"rotation": 18.0, "offset_x": 0.1, "offset_y": 0.0}
    locomotion_b["arm_r"] = {"rotation": -20.0, "offset_x": -0.14, "offset_y": 0.04}
    locomotion_b["spine"] = {"rotation": -4.0, "offset_x": 0.0, "offset_y": 0.04}
    carry_frame = {name: {"rotation": 0.0, "offset_x": 0.0, "offset_y": 0.0} for name in bone_names}
    carry_frame["arm_l"] = {"rotation": -35.0, "offset_x": -0.08, "offset_y": 0.11}
    carry_frame["arm_r"] = {"rotation": 35.0, "offset_x": 0.08, "offset_y": 0.11}
    celebrate_frame = {name: {"rotation": 0.0, "offset_x": 0.0, "offset_y": 0.0} for name in bone_names}
    celebrate_frame["arm_l"] = {"rotation": -58.0, "offset_x": -0.06, "offset_y": 0.18}
    celebrate_frame["arm_r"] = {"rotation": 58.0, "offset_x": 0.06, "offset_y": 0.18}
    celebrate_frame["head"] = {"rotation": 9.0, "offset_x": 0.0, "offset_y": 0.04}

    return {
        "entity": "Bango",
        "clips": [
            {"name": "idle", "loop": True, "frames": [{"time": 0.0, "bones": default_frame}, {"time": 0.5, "bones": carry_frame}, {"time": 1.0, "bones": default_frame}]},
            {"name": "locomotion", "loop": True, "frames": [{"time": 0.0, "bones": locomotion_a}, {"time": 0.5, "bones": default_frame}, {"time": 1.0, "bones": locomotion_b}, {"time": 1.5, "bones": default_frame}]},
            {"name": pose_template["move_name"], "loop": False, "frames": [{"time": 0.0, "bones": default_frame}, {"time": 0.18, "bones": attack_frame}, {"time": 0.38, "bones": default_frame}]},
            {"name": "carry", "loop": True, "frames": [{"time": 0.0, "bones": carry_frame}, {"time": 0.8, "bones": default_frame}]},
            {"name": "celebrate", "loop": True, "frames": [{"time": 0.0, "bones": celebrate_frame}, {"time": 0.6, "bones": default_frame}]},
        ],
        "inbetween": pose_template["inbetween"],
    }


def emit_actor_header(skeleton: dict, sections: list[dict]) -> None:
    lines = [
        "#pragma once",
        "",
        f"#define PREVIEW_BANGO_BONE_COUNT {len(skeleton['bones'])}",
        f"#define PREVIEW_BANGO_SECTION_COUNT {len(sections)}",
        "",
        "static const PreviewBoneDef kPreviewBangoBones[PREVIEW_BANGO_BONE_COUNT] = {",
    ]
    bone_name_to_index = {bone["name"]: index for index, bone in enumerate(skeleton["bones"])}
    for bone in skeleton["bones"]:
        parent = bone_name_to_index.get(bone["parent"], -1) if bone["parent"] else -1
        lines.append(
            f'    {{"{bone["name"]}", {parent}, {float(bone["x"]):.4f}f, {float(bone["y"]):.4f}f, 0.0f}},'
        )
    lines.extend([
        "};",
        "",
        "static const PreviewSectionDef kPreviewBangoSections[PREVIEW_BANGO_SECTION_COUNT] = {",
    ])
    for section in sections:
        lines.append(
            f'    {{"{section["name"]}", {section["bone_index"]}, {section["offset_x"]:.4f}f, {section["offset_y"]:.4f}f, {section["offset_z"]:.4f}f, {section["half_x"]:.4f}f, {section["half_y"]:.4f}f, {section["half_z"]:.4f}f, {section["color"][0]}, {section["color"][1]}, {section["color"][2]}}},'
        )
    lines.append("};")
    (GENERATED / "generated_bango_actor.h").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    GENERATED.mkdir(parents=True, exist_ok=True)
    rigs = load_json(RIGS)
    skeleton = normalized_entity_lookup(rigs, "bango")
    symbols = load_json(SYMBOLS)
    pose_template = load_json(POSE_TEMPLATE)
    sections = build_sections(symbols, skeleton["bones"])
    pose_chain = build_pose_chain(skeleton["bones"], pose_template)
    emit_actor_header(skeleton, sections)
    save_json(GENERATED / "bango_model_blockout.json", {"rig": skeleton, "sections": sections})
    save_json(GENERATED / "bango_pose_chain.json", pose_chain)
    print("Built Bango actor blockout and pose-chain data.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())