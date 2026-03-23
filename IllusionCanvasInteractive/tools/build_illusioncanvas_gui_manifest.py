from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT / "recraft" / "illusioncanvas_gui_1000_credit_manifest.json"


def make_asset(name: str, prompt: str, out: str) -> dict:
    return {
        "name": name,
        "prompt": prompt,
        "w": 1024,
        "h": 1024,
        "out": out,
        "model": "recraftv4",
        "planned_credits": 40,
        "api_units": 40,
        "transparent_background": True,
    }


def build_manifest() -> dict:
    base = (
        "transparent background custom game UI asset for IllusionCanvasInteractive, pixel-art 32-bit style, "
        "gothic sculpture and cathedral architecture, horror-movie Victorian meets late medieval survival game tone, "
        "weathered stone, brass reliquary trim, candle ember accents, readable silhouette language, no text labels unless required as decorative glyph lanes"
    )
    specs = [
        ("ic_shell_runtime_frame", "runtime shell frame with vaulted gothic tracery, playable viewport aperture, lower command altar, and reliquary corners", "shells/ic_shell_runtime_frame.png"),
        ("ic_shell_studio_frame", "editor studio shell frame with docking wells, archivist tooling rails, rose-window header band, and stained-metal corners", "shells/ic_shell_studio_frame.png"),
        ("ic_hud_command_frame", "combat HUD command frame with cathedral niche panels for health, bond tension, and bond weave", "shells/ic_hud_command_frame.png"),
        ("ic_panel_status_sidebar", "status sidebar shell with sculpted saints, inventory grooves, and vertical stat cartouches", "shells/ic_panel_status_sidebar.png"),
        ("ic_shell_asset_browser_frame", "asset browser and codex frame with ossuary drawers, breadcrumb rail, and gothic archive tabs", "shells/ic_shell_asset_browser_frame.png"),
        ("ic_popup_tutorial_tip_shell", "tutorial pop-up shell template with candlelit lintel and framed instructional plaque", "popups/ic_popup_tutorial_tip_shell.png"),
        ("ic_popup_dialogue_shell", "dialogue pop-up shell template with speaking portrait socket and lower response shelf", "popups/ic_popup_dialogue_shell.png"),
        ("ic_popup_quest_shell", "quest notification shell template with heraldic plate, reward lane, and parchment recess", "popups/ic_popup_quest_shell.png"),
        ("ic_popup_choice_shell", "multi-choice pop-up shell template with three decision bays and consecrated button wells", "popups/ic_popup_choice_shell.png"),
        ("ic_popup_codex_shell", "codex and bestiary pop-up shell template with tabbed chapter ribs and carved frame", "popups/ic_popup_codex_shell.png"),
        ("ic_popup_inventory_shell", "inventory pop-up shell template with gridded vault shelves and equipment sockets", "popups/ic_popup_inventory_shell.png"),
        ("ic_popup_merchant_shell", "merchant or barter pop-up shell template with scale niche, price plaques, and item trays", "popups/ic_popup_merchant_shell.png"),
        ("ic_popup_save_shell", "save or load shell template with reliquary slot plaques and pilgrimage seals", "popups/ic_popup_save_shell.png"),
        ("ic_popup_settings_shell", "settings pop-up shell template with slider alcoves, toggle medallions, and nested borders", "popups/ic_popup_settings_shell.png"),
        ("ic_popup_death_shell", "death or collapse shell template with shattered angel statuary, warning glow, and retry altar", "popups/ic_popup_death_shell.png"),
        ("ic_popup_tooltip_shell", "small tooltip shell template with gargoyle pointer notch and compact gilded inset", "popups/ic_popup_tooltip_shell.png"),
        ("ic_popup_toast_shell", "notification toast shell template with small heraldic flare and dismiss socket", "popups/ic_popup_toast_shell.png"),
        ("ic_popup_map_shell", "world map shell template with cardinal plaques and route-key legend bays", "popups/ic_popup_map_shell.png"),
        ("ic_popup_journal_shell", "journal shell template with timeline bands, clipped notes, and scripture dividers", "popups/ic_popup_journal_shell.png"),
        ("ic_popup_sanctuary_shell", "sanctuary and rest shell template with prayer circle recess and roster blessing slots", "popups/ic_popup_sanctuary_shell.png"),
        ("ic_font_cathedral_caps_alphanumeric", "custom bitmap-like alphanumeric font atlas, uppercase and numerals, blackletter-cathedral hybrid, grid aligned for UI extraction", "fonts/ic_font_cathedral_caps_alphanumeric.png"),
        ("ic_font_cryptic_runes_alphanumeric", "custom bitmap-like alphanumeric font atlas, mixed-case and numerals, runic reliquary style, grid aligned for UI extraction", "fonts/ic_font_cryptic_runes_alphanumeric.png"),
        ("ic_icon_button_state_atlas", "button state atlas for idle hover active disabled pressed, gothic sculpted medallion style", "atlases/ic_icon_button_state_atlas.png"),
        ("ic_icon_cursor_prompt_atlas", "cursor and control prompt atlas for arrow hand crosshair pickup rescue and confirm, cathedral metalwork style", "atlases/ic_icon_cursor_prompt_atlas.png"),
        ("ic_nav_tab_and_breadcrumb_atlas", "navigation atlas for tabs breadcrumbs and route markers in worn brass and stone", "atlases/ic_nav_tab_and_breadcrumb_atlas.png"),
    ]
    assets = [make_asset(name, f"{base}, {prompt}", out) for name, prompt, out in specs]
    return {
        "manifest_name": "illusioncanvas_gui_1000_credit_pass",
        "manifest_version": "2026-03-13.ui_shells",
        "intent": "1000-credit GUI shell pass for IllusionCanvasInteractive themed around gothic sculpture and architecture in a 32-bit horror-survival pixel-art language.",
        "output_root": "../generated/recraft_ui",
        "budget": {"allocated_credits": 1000, "asset_count": len(assets), "units_per_asset": 40},
        "assets": assets,
    }


def main() -> int:
    manifest = build_manifest()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"manifest": str(OUTPUT_PATH), "allocated_credits": manifest["budget"]["allocated_credits"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())