from __future__ import annotations

import json
from pathlib import Path


ANIMATION_NAMES = [
    "idle",
    "walk",
    "sprint",
    "attack_light_combo",
    "attack_heavy_combo",
    "jump",
    "block_unarmed",
    "parry_unarmed",
    "take_damage",
    "heal_honey_vial",
    "death",
    "rest_apiary",
    "slide_from_sprint",
]


def _write_json(path: Path, payload: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return str(path)


def _write_text(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return str(path)


def build_idloadint_bundle(project_root: Path, output_dir: Path, blend_path: Path, glb_path: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    controller_profile = {
        "profile_name": "Xbox Series Default",
        "module_name": "idLoadINT",
        "default_controller": "xbox_series",
        "bindings": {
            "move": "left_stick",
            "camera": "right_stick",
            "crouch_or_slide": "A",
            "jump_or_sprint_hold": "B",
            "heal": "X",
            "unsheathe_weapon": "Y",
            "light_attack": "LB",
            "heavy_attack": "RT",
            "focus_lock_hold": "RB",
            "ability_wheel_hold": "LT",
            "parry_click": "right_stick_click",
            "block_click": "left_stick_click",
            "menu": "Menu",
            "game_menu": "View",
        },
        "timing_system": {
            "precision_parry": True,
            "precision_block": True,
            "stick_inclination_blend": True,
            "haptic_force_sampling": True,
        },
    }
    tutorial_spec = {
        "name": "bango_tutorial_voidroom",
        "environment": "minimal_void",
        "prompts": [
            "Move with left stick and turn the camera with right stick.",
            "Tap A to crouch or slide while sprinting.",
            "Hold B to sprint; tap B to jump.",
            "Use LB for light attacks and RT for heavy attacks.",
            "Click right stick to parry and left stick to block.",
            "Hold LT for the ability wheel and steer with right stick.",
        ],
        "waves": [
            {"enemy_tier": 1, "count": 3},
            {"enemy_tier": 2, "count": 3},
            {"enemy_tier": 3, "count": 3},
        ],
        "completion_rule": "defeat_all_waves",
    }
    orb_spec = {
        "enemy_family": "nightmaresludgebio_orb",
        "tiers": [
            {"tier": 1, "name": "peculiar_sludge_orb_scout", "animations": ["idle", "float", "attack_primary", "attack_secondary", "take_damage", "regen", "death"]},
            {"tier": 2, "name": "peculiar_sludge_orb_mire", "animations": ["idle", "float", "attack_primary", "attack_secondary", "take_damage", "regen", "death"]},
            {"tier": 3, "name": "peculiar_sludge_orb_horror", "animations": ["idle", "float", "attack_primary", "attack_secondary", "take_damage", "regen", "death"]},
        ],
    }
    manifest = {
        "project": "bango-patoot_3DS",
        "translator_trial_name": "idTech2 integration",
        "translator_vip_name": "idLoadINT",
        "source_blend": str(blend_path),
        "source_glb": str(glb_path),
        "animation_clips": ANIMATION_NAMES,
        "controller_profile": "xbox_series_default.json",
        "tutorial_spec": "tutorial_demo_spec.json",
        "enemy_spec": "nightmaresludgebio_orbs.json",
    }
    header = """
#ifndef BANGO_IDLOADINT_AUTOGEN_H
#define BANGO_IDLOADINT_AUTOGEN_H

typedef struct BangoIdLoadINTClipDef {
    const char *name;
    int looped;
} BangoIdLoadINTClipDef;

extern const BangoIdLoadINTClipDef g_bango_idloadint_clips[];
extern const int g_bango_idloadint_clip_count;

#endif
""".strip() + "\n"
    clip_lines = [f'    {{ "{name}", {1 if name in {"idle", "walk", "sprint", "block_unarmed", "rest_apiary"} else 0} }},' for name in ANIMATION_NAMES]
    source = "\n".join([
        '#include "g_bango_idloadint_autogen.h"',
        '',
        'const BangoIdLoadINTClipDef g_bango_idloadint_clips[] = {',
        *clip_lines,
        '};',
        f'const int g_bango_idloadint_clip_count = {len(ANIMATION_NAMES)};',
        '',
    ])

    return {
        "manifest": _write_json(output_dir / "idLoadINT_manifest.json", manifest),
        "controller_profile": _write_json(output_dir / "xbox_series_default.json", controller_profile),
        "tutorial_spec": _write_json(output_dir / "tutorial_demo_spec.json", tutorial_spec),
        "enemy_spec": _write_json(output_dir / "nightmaresludgebio_orbs.json", orb_spec),
        "header": _write_text(output_dir / "g_bango_idloadint_autogen.h", header),
        "source": _write_text(output_dir / "g_bango_idloadint_autogen.c", source),
    }
