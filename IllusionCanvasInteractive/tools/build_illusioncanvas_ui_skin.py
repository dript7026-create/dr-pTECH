from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_manifest(path: Path) -> tuple[list[dict], Path]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    assets = raw.get("assets", raw)
    output_root = (path.parent / raw.get("output_root", ".")).resolve() if isinstance(raw, dict) else path.parent.resolve()
    return assets, output_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build an IllusionCanvas UI skin manifest from a GUI Recraft manifest")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest)
    out_path = Path(args.out)
    assets, output_root = load_manifest(manifest_path)
    asset_map = {asset["name"]: asset for asset in assets}

    def asset_entry(name: str, subsample: int = 2) -> dict:
        asset = asset_map[name]
        return {"path": str(output_root / asset["out"]), "subsample": subsample}

    skin = {
        "theme_name": "IllusionCanvas Gothic Reliquary",
        "palette": {
            "sky": "#140f18",
            "ground": "#1d171c",
            "floor": "#30232b",
            "panel": "#241921",
            "panel_alt": "#160f16",
            "ink": "#f3e6d0",
            "accent": "#c79a57",
            "accent_soft": "#8ba6b6",
            "success": "#bfd9c5",
            "warning": "#d6a36d",
        },
        "runtime_assets": {
            "shell_frame": asset_entry("ic_shell_runtime_frame", 2),
            "hud_frame": asset_entry("ic_hud_command_frame", 4),
            "sidebar_frame": asset_entry("ic_panel_status_sidebar", 4),
        },
        "studio_assets": {
            "header_frame": asset_entry("ic_shell_studio_frame", 2),
            "asset_browser_frame": asset_entry("ic_shell_asset_browser_frame", 3),
        },
        "popup_templates": {
            "tutorial_tip_shell": asset_entry("ic_popup_tutorial_tip_shell", 4),
            "dialogue_shell": asset_entry("ic_popup_dialogue_shell", 4),
            "quest_shell": asset_entry("ic_popup_quest_shell", 4),
            "choice_shell": asset_entry("ic_popup_choice_shell", 4),
            "codex_shell": asset_entry("ic_popup_codex_shell", 4),
            "inventory_shell": asset_entry("ic_popup_inventory_shell", 4),
            "merchant_shell": asset_entry("ic_popup_merchant_shell", 4),
            "save_shell": asset_entry("ic_popup_save_shell", 4),
            "settings_shell": asset_entry("ic_popup_settings_shell", 4),
            "death_shell": asset_entry("ic_popup_death_shell", 4),
            "tooltip_shell": asset_entry("ic_popup_tooltip_shell", 5),
            "toast_shell": asset_entry("ic_popup_toast_shell", 5),
            "map_shell": asset_entry("ic_popup_map_shell", 4),
            "journal_shell": asset_entry("ic_popup_journal_shell", 4),
            "sanctuary_shell": asset_entry("ic_popup_sanctuary_shell", 4),
        },
        "font_atlases": {
            "cathedral_caps": asset_entry("ic_font_cathedral_caps_alphanumeric", 3),
            "cryptic_runes": asset_entry("ic_font_cryptic_runes_alphanumeric", 3),
        },
        "icon_atlases": {
            "button_states": asset_entry("ic_icon_button_state_atlas", 4),
            "cursor_prompts": asset_entry("ic_icon_cursor_prompt_atlas", 4),
            "navigation": asset_entry("ic_nav_tab_and_breadcrumb_atlas", 4),
        },
        "notes": {
            "art_direction": "gothic sculpture and reliquary architecture interpreted as 32-bit horror-survival pixel UI shells",
            "source_manifest": str(manifest_path),
        },
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(skin, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(out_path), "theme": skin["theme_name"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())