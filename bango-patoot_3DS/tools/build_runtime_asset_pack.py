from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageSequence


ROOT = Path(__file__).resolve().parent.parent
RIG_FILE = ROOT / "rigs" / "entity_rigs.json"
POSE_FILE = ROOT / "pose_imports" / "imported_pose_registry.json"
OBJECT_DIR = ROOT / "assets" / "object_sheets"
OUT_DIR = ROOT / "generated"
OUT_FILE = OUT_DIR / "bango_runtime_asset_pack.h"

ANGLE_LABELS = ["front", "left", "right", "rear"]
FRAME_W = 24
FRAME_H = 36
MAX_COLORS = 15


def load_json(path: Path, fallback):
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def tokenise(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "unnamed"


def fit_frame(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    bbox = rgba.getchannel("A").getbbox()
    if bbox is None:
        return Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))

    cropped = rgba.crop(bbox)
    scale = min((FRAME_W - 2) / max(1, cropped.width), (FRAME_H - 2) / max(1, cropped.height))
    scaled_size = (
        max(1, int(round(cropped.width * scale))),
        max(1, int(round(cropped.height * scale))),
    )
    resized = cropped.resize(scaled_size, Image.Resampling.NEAREST)

    canvas = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
    offset_x = (FRAME_W - scaled_size[0]) // 2
    offset_y = FRAME_H - scaled_size[1] - 1
    canvas.alpha_composite(resized, (offset_x, offset_y))
    return canvas


def quantize_frame(image: Image.Image) -> tuple[list[int], list[int]]:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    rgb = Image.new("RGB", rgba.size, (0, 0, 0))
    rgb.paste(rgba.convert("RGB"), mask=alpha)

    quantized = rgb.quantize(colors=MAX_COLORS, dither=Image.Dither.NONE)
    raw_palette = quantized.getpalette()[: MAX_COLORS * 3]
    alpha_data = list(alpha.tobytes())
    quant_data = list(quantized.tobytes())

    used_indices: list[int] = []
    seen = set()
    for pixel_index, alpha_value in zip(quant_data, alpha_data):
        if alpha_value < 32:
            continue
        if pixel_index not in seen:
            seen.add(pixel_index)
            used_indices.append(pixel_index)

    palette: list[int] = []
    index_map = {value: idx + 1 for idx, value in enumerate(used_indices)}
    for source_index in used_indices:
        base = source_index * 3
        red = raw_palette[base]
        green = raw_palette[base + 1]
        blue = raw_palette[base + 2]
        palette.append((red << 24) | (green << 16) | (blue << 8) | 0xFF)

    pixels: list[int] = []
    for pixel_index, alpha_value in zip(quant_data, alpha_data):
        if alpha_value < 32:
            pixels.append(0)
        else:
            pixels.append(index_map[pixel_index])

    return palette, pixels


def emit_u32_array(name: str, values: Iterable[int]) -> str:
    values = list(values)
    body = ",\n    ".join(f"0x{value:08X}u" for value in values) if values else "0u"
    return f"static const uint32_t {name}[] = {{\n    {body}\n}};\n"


def emit_u8_array(name: str, values: Iterable[int]) -> str:
    values = list(values)
    rows = []
    for start in range(0, len(values), FRAME_W):
        rows.append(", ".join(f"{value}u" for value in values[start : start + FRAME_W]))
    body = ",\n    ".join(rows) if rows else "0u"
    return f"static const uint8_t {name}[] = {{\n    {body}\n}};\n"


def load_pose_entries() -> list[dict]:
    registry = load_json(POSE_FILE, [])
    merged_entries: list[dict] = []
    for entry in registry:
        merged = dict(entry)
        pose_json = entry.get("pose_json")
        if pose_json:
            pose_doc = load_json(Path(pose_json), {})
            for key, value in pose_doc.items():
                merged.setdefault(key, value)
        merged_entries.append(merged)
    return merged_entries


def emit_object_assets(chunks: list[str]) -> None:
    object_refs: list[str] = []
    if OBJECT_DIR.exists():
        for object_path in sorted(OBJECT_DIR.glob("*.png")):
            token = tokenise(object_path.stem)
            fitted = fit_frame(Image.open(object_path).convert("RGBA"))
            palette, pixels = quantize_frame(fitted)
            palette_name = f"g_object_{token}_palette"
            pixel_name = f"g_object_{token}_pixels"
            frame_name = f"g_object_{token}_frame"
            asset_name = f"g_object_{token}_asset"

            chunks.append(emit_u32_array(palette_name, palette))
            chunks.append(emit_u8_array(pixel_name, pixels))
            chunks.append(
                f"static const RuntimeSpriteFrameDef {frame_name} = {{\n"
                f"    \"{object_path.stem}\",\n"
                f"    {FRAME_W}, {FRAME_H}, {FRAME_W // 2}, {FRAME_H - 1},\n"
                f"    {len(palette)}, {palette_name}, {pixel_name}\n"
                f"}};\n\n"
            )
            chunks.append(
                f"static const RuntimeEnvironmentAssetDef {asset_name} = {{\n"
                f"    \"{object_path.stem}\",\n"
                f"    {FRAME_W},\n"
                f"    {FRAME_H},\n"
                f"    &{frame_name},\n"
                f"    0\n"
                f"}};\n\n"
            )
            object_refs.append(asset_name)

    if object_refs:
        body = ",\n    ".join(object_refs)
        chunks.append(f"static const int g_bango_runtime_object_asset_count = {len(object_refs)};\n")
        chunks.append(f"static const RuntimeEnvironmentAssetDef g_bango_runtime_object_assets[] = {{\n    {body}\n}};\n\n")
    else:
        chunks.append("static const int g_bango_runtime_object_asset_count = 0;\n")
        chunks.append(
            "static const RuntimeEnvironmentAssetDef g_bango_runtime_object_assets[1] = {\n"
            "    {0, 0, 0, 0, 0}\n"
            "};\n\n"
        )


def main() -> int:
    rig_data = load_json(RIG_FILE, {"skeletons": []})
    pose_entries = load_pose_entries()
    pose_entries_by_entity: dict[str, list[dict]] = {}
    for entry in pose_entries:
        entity = entry.get("entity", "")
        pose_entries_by_entity.setdefault(entity, []).append(entry)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    chunks: list[str] = [
        "#ifndef BANGO_RUNTIME_ASSET_PACK_H\n",
        "#define BANGO_RUNTIME_ASSET_PACK_H\n\n",
        "#include <stdint.h>\n\n",
        "typedef struct RuntimeSpriteFrameDef {\n",
        "    const char *label;\n",
        "    int width;\n",
        "    int height;\n",
        "    int pivot_x;\n",
        "    int pivot_y;\n",
        "    int palette_count;\n",
        "    const uint32_t *palette;\n",
        "    const uint8_t *pixels;\n",
        "} RuntimeSpriteFrameDef;\n\n",
        "typedef struct RuntimeLoopClipDef {\n",
        "    int frame_count;\n",
        "    const RuntimeSpriteFrameDef *const *frames;\n",
        "} RuntimeLoopClipDef;\n\n",
        "typedef struct RuntimeRigBoneDef {\n",
        "    const char *name;\n",
        "    int parent_index;\n",
        "    float x;\n",
        "    float y;\n",
        "} RuntimeRigBoneDef;\n\n",
        "typedef struct RuntimePoseBoneOffsetDef {\n",
        "    int bone_index;\n",
        "    float x;\n",
        "    float y;\n",
        "    float rotation;\n",
        "} RuntimePoseBoneOffsetDef;\n\n",
        "typedef struct RuntimeImportedPoseDef {\n",
        "    const char *entity_name;\n",
        "    const char *move_name;\n",
        "    int frame_index;\n",
        "    int duration_ms;\n",
        "    float stiffness;\n",
        "    float damping;\n",
        "    float overshoot;\n",
        "    float gravity_bias;\n",
        "    int offset_count;\n",
        "    const RuntimePoseBoneOffsetDef *offsets;\n",
        "} RuntimeImportedPoseDef;\n\n",
        "typedef struct RuntimeRigDef {\n",
        "    const char *name;\n",
        "    const char *entity_name;\n",
        "    int bone_count;\n",
        "    const RuntimeRigBoneDef *bones;\n",
        "    int imported_pose_count;\n",
        "    const RuntimeImportedPoseDef *const *poses;\n",
        "} RuntimeRigDef;\n\n",
        "typedef struct RuntimeEnvironmentAssetDef {\n",
        "    const char *name;\n",
        "    int width;\n",
        "    int height;\n",
        "    const RuntimeSpriteFrameDef *frame;\n",
        "    int interactive_default;\n",
        "} RuntimeEnvironmentAssetDef;\n\n",
        "typedef struct RuntimeEntityAssetPack {\n",
        "    const char *entity_name;\n",
        "    const char *rig_name;\n",
        "    int bone_count;\n",
        "    int imported_pose_count;\n",
        "    int angle_count;\n",
        "    const RuntimeSpriteFrameDef *angles[4];\n",
        "    RuntimeLoopClipDef loop;\n",
        "    const RuntimeRigDef *rig;\n",
        "} RuntimeEntityAssetPack;\n\n",
    ]

    entity_tokens: list[str] = []

    for skeleton in rig_data.get("skeletons", []):
        entity = skeleton["entity"]
        rig_name = skeleton["name"]
        entity_token = tokenise(entity)
        entity_tokens.append(entity_token)

        sheet_path = ROOT / skeleton["sprite_sheet"]
        sheet = Image.open(sheet_path).convert("RGBA")
        sheet_w = max(1, sheet.width // 4)

        angle_frame_names: list[str] = []
        for angle_index, label in enumerate(ANGLE_LABELS):
            frame = sheet.crop((angle_index * sheet_w, 0, (angle_index + 1) * sheet_w, sheet.height))
            fitted = fit_frame(frame)
            palette, pixels = quantize_frame(fitted)

            palette_name = f"g_{entity_token}_{label}_palette"
            pixel_name = f"g_{entity_token}_{label}_pixels"
            frame_name = f"g_{entity_token}_{label}_frame"
            angle_frame_names.append(frame_name)

            chunks.append(emit_u32_array(palette_name, palette))
            chunks.append(emit_u8_array(pixel_name, pixels))
            chunks.append(
                f"static const RuntimeSpriteFrameDef {frame_name} = {{\n"
                f"    \"{label}\",\n"
                f"    {FRAME_W}, {FRAME_H}, {FRAME_W // 2}, {FRAME_H - 1},\n"
                f"    {len(palette)}, {palette_name}, {pixel_name}\n"
                f"}};\n\n"
            )

        loop_image = Image.open(ROOT / skeleton["concept_loop"])
        loop_frame_names: list[str] = []
        for loop_index, loop_frame in enumerate(ImageSequence.Iterator(loop_image)):
            fitted = fit_frame(loop_frame.convert("RGBA"))
            palette, pixels = quantize_frame(fitted)
            palette_name = f"g_{entity_token}_loop_{loop_index}_palette"
            pixel_name = f"g_{entity_token}_loop_{loop_index}_pixels"
            frame_name = f"g_{entity_token}_loop_{loop_index}_frame"
            loop_frame_names.append(frame_name)

            chunks.append(emit_u32_array(palette_name, palette))
            chunks.append(emit_u8_array(pixel_name, pixels))
            chunks.append(
                f"static const RuntimeSpriteFrameDef {frame_name} = {{\n"
                f"    \"loop_{loop_index}\",\n"
                f"    {FRAME_W}, {FRAME_H}, {FRAME_W // 2}, {FRAME_H - 1},\n"
                f"    {len(palette)}, {palette_name}, {pixel_name}\n"
                f"}};\n\n"
            )

        loop_ptr_name = f"g_{entity_token}_loop_frames"
        loop_body = ",\n    ".join(f"&{name}" for name in loop_frame_names) if loop_frame_names else "0"
        chunks.append(f"static const RuntimeSpriteFrameDef *const {loop_ptr_name}[] = {{\n    {loop_body}\n}};\n\n")

        bone_name_to_index: dict[str, int] = {}
        bone_rows: list[str] = []
        for bone_index, bone in enumerate(skeleton.get("bones", [])):
            bone_name_to_index[bone["name"]] = bone_index
            parent_name = bone.get("parent")
            parent_index = bone_name_to_index.get(parent_name, -1) if parent_name else -1
            bone_rows.append(
                f'    {{"{bone["name"]}", {parent_index}, {float(bone.get("x", 0.0)):.3f}f, {float(bone.get("y", 0.0)):.3f}f}}'
            )

        bones_name = f"g_{entity_token}_rig_bones"
        chunks.append(f"static const RuntimeRigBoneDef {bones_name}[] = {{\n" + ",\n".join(bone_rows) + "\n};\n\n")

        pose_ptr_names: list[str] = []
        for pose_index, entry in enumerate(pose_entries_by_entity.get(entity, [])):
            pose_token = tokenise(entry.get("move_name", f"pose_{pose_index}"))
            offsets = entry.get("bone_offsets", {})
            offset_rows: list[str] = []
            for bone_name, offset in offsets.items():
                if bone_name not in bone_name_to_index:
                    continue
                offset_rows.append(
                    f'    {{{bone_name_to_index[bone_name]}, {float(offset.get("x", 0.0)):.3f}f, {float(offset.get("y", 0.0)):.3f}f, {float(offset.get("rotation", 0.0)):.3f}f}}'
                )

            offsets_name = f"g_{entity_token}_{pose_token}_{pose_index}_offsets"
            if offset_rows:
                chunks.append(f"static const RuntimePoseBoneOffsetDef {offsets_name}[] = {{\n" + ",\n".join(offset_rows) + "\n};\n\n")
            else:
                chunks.append(f"static const RuntimePoseBoneOffsetDef {offsets_name}[1] = {{\n    {{-1, 0.0f, 0.0f, 0.0f}}\n}};\n\n")

            inbetween = entry.get("inbetween", {})
            pose_name = f"g_{entity_token}_{pose_token}_{pose_index}_pose"
            pose_ptr_names.append(f"&{pose_name}")
            chunks.append(
                f"static const RuntimeImportedPoseDef {pose_name} = {{\n"
                f"    \"{entity}\",\n"
                f"    \"{entry.get('move_name', 'Pose')}\",\n"
                f"    {int(entry.get('frame_index', 0))},\n"
                f"    {int(entry.get('duration_ms', 100))},\n"
                f"    {float(inbetween.get('stiffness', 0.5)):.3f}f,\n"
                f"    {float(inbetween.get('damping', 0.25)):.3f}f,\n"
                f"    {float(inbetween.get('overshoot', 0.0)):.3f}f,\n"
                f"    {float(inbetween.get('gravity_bias', 0.0)):.3f}f,\n"
                f"    {len(offset_rows)},\n"
                f"    {offsets_name}\n"
                f"}};\n\n"
            )

        pose_ptr_array_name = f"g_{entity_token}_rig_pose_ptrs"
        pose_ptr_body = ",\n    ".join(pose_ptr_names) if pose_ptr_names else "0"
        chunks.append(f"static const RuntimeImportedPoseDef *const {pose_ptr_array_name}[] = {{\n    {pose_ptr_body}\n}};\n\n")

        rig_def_name = f"g_{entity_token}_rig"
        chunks.append(
            f"static const RuntimeRigDef {rig_def_name} = {{\n"
            f"    \"{rig_name}\",\n"
            f"    \"{entity}\",\n"
            f"    {len(skeleton.get('bones', []))},\n"
            f"    {bones_name},\n"
            f"    {len(pose_ptr_names)},\n"
            f"    {pose_ptr_array_name}\n"
            f"}};\n\n"
        )

        pack_name = f"g_{entity_token}_pack"
        angle_ptrs = ", ".join(f"&{name}" for name in angle_frame_names)
        chunks.append(
            f"static const RuntimeEntityAssetPack {pack_name} = {{\n"
            f"    \"{entity}\",\n"
            f"    \"{rig_name}\",\n"
            f"    {len(skeleton.get('bones', []))},\n"
            f"    {len(pose_ptr_names)},\n"
            f"    4,\n"
            f"    {{{angle_ptrs}}},\n"
            f"    {{{len(loop_frame_names)}, {loop_ptr_name}}},\n"
            f"    &{rig_def_name}\n"
            f"}};\n\n"
        )

    pack_refs = ",\n    ".join(f"g_{name}_pack" for name in entity_tokens) if entity_tokens else "{0}"
    chunks.append(f"static const int g_bango_runtime_asset_pack_count = {len(entity_tokens)};\n")
    chunks.append(f"static const RuntimeEntityAssetPack g_bango_runtime_asset_pack[] = {{\n    {pack_refs}\n}};\n\n")
    emit_object_assets(chunks)
    chunks.append("#endif\n")

    OUT_FILE.write_text("".join(chunks), encoding="utf-8")
    print(f"Wrote runtime asset pack header to {OUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())