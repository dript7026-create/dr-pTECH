"""Builds the NeoWakeUP GUI Recraft manifests."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RECRAFT_DIR = ROOT / "assets" / "recraft"


def save_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def build_gui_pass_600() -> dict:
    shared = (
        "NeoWakeUP planetary mind network visual system. Transparent background unless asset is a full panel. "
        "High readability for desktop UI, no text unless the asset specifically requests glyph samples. "
        "Use crisp silhouettes and coherent philosophy-driven design language: techno-noetic cartography, "
        "disciplined geometry, luminous signal ecology, non-corporate, reflective, alive without looking generic."
    )
    assets = [
        {
            "name": "planetary_mind_planet_core",
            "prompt": "Transparent background planet graphic for a live planetary mind network, layered atmosphere rings, data-ocean glow, continental light constellations, sacred-technical cartography aesthetic, centered composition. " + shared,
            "negative_prompt": "black background, stars, text, logo, watermark, blurry edges, cropped planet",
            "w": 1024,
            "h": 1024,
            "api_units": 75,
            "model": "recraftv4",
            "out": "gui_pass_600/planet/planetary_mind_planet_core.png",
        },
        {
            "name": "humanoid_mind_icons_set_a",
            "prompt": "Transparent background sprite lineup sheet containing five unique humanoid icons representing distinct minds in a living network: analyst, dreamer, mediator, maker, sentinel. Arrange as five separated full-body icons on one sheet with consistent baseline and equal spacing. " + shared,
            "negative_prompt": "merged characters, background scene, text labels, duplicates, cropped limbs",
            "w": 1024,
            "h": 1024,
            "api_units": 75,
            "model": "recraftv4",
            "out": "gui_pass_600/icons/humanoid_mind_icons_set_a.png",
        },
        {
            "name": "network_channel_streams",
            "prompt": "Transparent background set of network mapping channel stream graphics: arcs, braided beams, filament highways, modular connection lines, signal conduits, all separated on one sheet for UI compositing. " + shared,
            "negative_prompt": "background scene, text, clutter, perspective environment",
            "w": 1024,
            "h": 1024,
            "api_units": 75,
            "model": "recraftv4",
            "out": "gui_pass_600/network/network_channel_streams.png",
        },
        {
            "name": "signal_transfer_spritesheet",
            "prompt": "Transparent background PNG sprite sheet in a single horizontal row, eight columns left-to-right, animated signal transfer pulse moving through a channel stream, clean loop, each column a distinct frame. " + shared,
            "negative_prompt": "multiple rows, text, background panel, irregular frame sizes",
            "w": 1024,
            "h": 1024,
            "api_units": 75,
            "model": "recraftv4",
            "out": "gui_pass_600/network/signal_transfer_spritesheet.png",
        },
        {
            "name": "node_marker_spritesheet",
            "prompt": "Transparent background PNG sprite sheet in a single horizontal row, eight columns left-to-right, node marker activation animation for when a humanoid mind contributes to the overarching process, luminous pulse loop, each column a frame. " + shared,
            "negative_prompt": "multiple rows, text, background panel, messy glow",
            "w": 1024,
            "h": 1024,
            "api_units": 75,
            "model": "recraftv4",
            "out": "gui_pass_600/network/node_marker_spritesheet.png",
        },
        {
            "name": "font_glyph_reference_uppercase",
            "prompt": "Custom uppercase alphanumeric glyph reference for NeoWakeUP, philosophy-based AI nomenclature aesthetic, austere techno-calligraphic forms, all glyphs isolated and evenly spaced, transparent background, reference sheet for later font tracing. " + shared,
            "negative_prompt": "paragraph text, decorative poster, watermark, background scene",
            "w": 1024,
            "h": 1024,
            "api_units": 75,
            "model": "recraftv4",
            "out": "gui_pass_600/font/font_glyph_reference_uppercase.png",
        },
        {
            "name": "font_glyph_reference_lowercase",
            "prompt": "Custom lowercase alphanumeric glyph reference for NeoWakeUP, philosophy-based AI nomenclature aesthetic, austere techno-calligraphic forms, all glyphs isolated and evenly spaced, transparent background, reference sheet for later font tracing. " + shared,
            "negative_prompt": "paragraph text, decorative poster, watermark, background scene",
            "w": 1024,
            "h": 1024,
            "api_units": 75,
            "model": "recraftv4",
            "out": "gui_pass_600/font/font_glyph_reference_lowercase.png",
        },
        {
            "name": "font_glyph_reference_digits_symbols",
            "prompt": "Custom digits and symbolic punctuation glyph reference for NeoWakeUP, philosophy-based AI nomenclature aesthetic, technical but organic, transparent background, evenly spaced glyph sheet for font tracing. " + shared,
            "negative_prompt": "paragraph text, poster, watermark, background scene",
            "w": 1024,
            "h": 1024,
            "api_units": 75,
            "model": "recraftv4",
            "out": "gui_pass_600/font/font_glyph_reference_digits_symbols.png",
        },
    ]
    return {
        "manifest_name": "neowakeup_gui_pass_600",
        "manifest_version": "2026-03-12.neowakeup_gui_pass_600",
        "intent": "600-credit Recraft pass for the primary NeoWakeUP control hub visual system.",
        "budget": {"unit_cost": 75, "asset_count": len(assets), "total_credits": 600},
        "shared_prompt_appendix": shared,
        "assets": assets,
    }


def build_gui_pass_300() -> dict:
    shared = (
        "NeoWakeUP UI finalization asset pass. Clean desktop readability, coherent with the planetary mind visuals, "
        "avoid generic SaaS styling, prefer signal cartography, layered fields, measured glow, transparent background when possible."
    )
    assets = [
        {
            "name": "control_panel_background",
            "prompt": "Main control panel background for NeoWakeUP, wide desktop dashboard panel with layered atmospheric gradients, subtle linework, no text, usable as a backdrop for controls. " + shared,
            "negative_prompt": "text labels, clutter, busy illustration, logo, watermark",
            "w": 1024,
            "h": 1024,
            "api_units": 50,
            "model": "recraftv4",
            "out": "gui_pass_300/panels/control_panel_background.png",
        },
        {
            "name": "dial_knob_set",
            "prompt": "Transparent background set of distinct UI dial and knob assets for NeoWakeUP, reflective but restrained, include neutral, hover, and active variants laid out cleanly on one sheet. " + shared,
            "negative_prompt": "text labels, background scene, blurry controls",
            "w": 1024,
            "h": 1024,
            "api_units": 50,
            "model": "recraftv4",
            "out": "gui_pass_300/controls/dial_knob_set.png",
        },
        {
            "name": "slider_track_set",
            "prompt": "Transparent background set of slider tracks, thumbs, and active fill variations for NeoWakeUP, precise technical styling, arranged cleanly for slicing. " + shared,
            "negative_prompt": "text labels, background scene, clutter",
            "w": 1024,
            "h": 1024,
            "api_units": 50,
            "model": "recraftv4",
            "out": "gui_pass_300/controls/slider_track_set.png",
        },
        {
            "name": "button_cluster_set",
            "prompt": "Transparent background set of action buttons for NeoWakeUP, start, pause, commit, simulate, export, arranged as a coherent cluster with visual state variations and no text. " + shared,
            "negative_prompt": "word labels, background scene, generic web buttons",
            "w": 1024,
            "h": 1024,
            "api_units": 50,
            "model": "recraftv4",
            "out": "gui_pass_300/controls/button_cluster_set.png",
        },
        {
            "name": "node_map_overlay",
            "prompt": "Transparent background node map overlay for NeoWakeUP, elegant graph scaffolding, branching thought chains, circular and orbital anchor points for a canvas-based neural node map. " + shared,
            "negative_prompt": "text, poster, background scene, human faces",
            "w": 1024,
            "h": 1024,
            "api_units": 50,
            "model": "recraftv4",
            "out": "gui_pass_300/network/node_map_overlay.png",
        },
        {
            "name": "brand_mark_set",
            "prompt": "Transparent background NeoWakeUP brand mark set, central sigil, app badge, and compact emblem variants, coherent with a living planetary intelligence dashboard, no text. " + shared,
            "negative_prompt": "full poster, paragraph text, watermark",
            "w": 1024,
            "h": 1024,
            "api_units": 50,
            "model": "recraftv4",
            "out": "gui_pass_300/branding/brand_mark_set.png",
        },
    ]
    return {
        "manifest_name": "neowakeup_gui_pass_300",
        "manifest_version": "2026-03-12.neowakeup_gui_pass_300",
        "intent": "300-credit Recraft pass for NeoWakeUP GUI finalization assets.",
        "budget": {"unit_cost": 50, "asset_count": len(assets), "total_credits": 300},
        "shared_prompt_appendix": shared,
        "assets": assets,
    }


def build_gui_pass_300_corrective() -> dict:
    shared = (
        "NeoWakeUP corrective UI asset pass for transparency-sensitive interface elements. "
        "Every asset must be isolated on a truly transparent background with no backing plate, no poster field, no scene fill, and no opaque framing. "
        "Deliver clean silhouettes and internal detail only."
    )
    assets = [
        {
            "name": "dial_knob_set_transparency_corrective",
            "prompt": "Transparent background sheet of NeoWakeUP dials and knobs only, floating isolated controls, no panel, no scene, no shadow card, neutral hover and active variations grouped cleanly. " + shared,
            "w": 1024,
            "h": 1024,
            "api_units": 40,
            "model": "recraftv4",
            "out": "gui_pass_300_corrective/controls/dial_knob_set.png",
        },
        {
            "name": "slider_track_set_transparency_corrective",
            "prompt": "Transparent background sheet of NeoWakeUP slider tracks and thumbs only, isolated controls with no panel fill and no surrounding background, precise technical styling. " + shared,
            "w": 1024,
            "h": 1024,
            "api_units": 40,
            "model": "recraftv4",
            "out": "gui_pass_300_corrective/controls/slider_track_set.png",
        },
        {
            "name": "button_cluster_set_transparency_corrective",
            "prompt": "Transparent background sheet of NeoWakeUP action buttons only, isolated controls, no backdrop, no words, no panel card, coherent visual states for start, pause, commit, simulate, export. " + shared,
            "w": 1024,
            "h": 1024,
            "api_units": 40,
            "model": "recraftv4",
            "out": "gui_pass_300_corrective/controls/button_cluster_set.png",
        },
        {
            "name": "node_map_overlay_transparency_corrective",
            "prompt": "Transparent background neural node-map overlay for NeoWakeUP, only the graph filaments, orbital guides, and node anchors, no backing panel or opaque fill. " + shared,
            "w": 1024,
            "h": 1024,
            "api_units": 40,
            "model": "recraftv4",
            "out": "gui_pass_300_corrective/network/node_map_overlay.png",
        },
        {
            "name": "brand_mark_set_transparency_corrective",
            "prompt": "Transparent background NeoWakeUP brand mark sheet only, isolated sigil, badge, and compact emblem variants, no card, no poster, no opaque field. " + shared,
            "w": 1024,
            "h": 1024,
            "api_units": 40,
            "model": "recraftv4",
            "out": "gui_pass_300_corrective/branding/brand_mark_set.png",
        },
    ]
    return {
        "manifest_name": "neowakeup_gui_pass_300_corrective",
        "manifest_version": "2026-03-12.neowakeup_gui_pass_300_corrective",
        "intent": "200-credit corrective Recraft pass for transparency-sensitive NeoWakeUP GUI assets.",
        "budget": {"unit_cost": 40, "asset_count": len(assets), "total_credits": 200},
        "shared_prompt_appendix": shared,
        "assets": assets,
    }


def build_dial_knob_v2_corrective() -> dict:
    shared = (
        "NeoWakeUP dial corrective rerun. Deliver only isolated dial and knob objects on true transparent alpha. "
        "No backing card, no poster field, no panel silhouette, no scene, no decorative frame. "
        "Arrange as a neat three-column control sheet with generous empty space between controls."
    )
    assets = [
        {
            "name": "dial_knob_set_v2",
            "prompt": "Transparent background sticker-sheet style set of NeoWakeUP circular dials and knobs only, three primary controls with neutral, hover, and active appearance cues, floating isolated objects, no backing plate, no panel, no typography. " + shared,
            "w": 1024,
            "h": 1024,
            "api_units": 40,
            "model": "recraftv4",
            "out": "gui_pass_300_corrective_v2/controls/dial_knob_set.png",
        }
    ]
    return {
        "manifest_name": "neowakeup_dial_knob_corrective_v2",
        "manifest_version": "2026-03-13.neowakeup_dial_knob_corrective_v2",
        "intent": "40-credit targeted rerun for the NeoWakeUP dial/knob sheet with stricter transparency requirements.",
        "budget": {"unit_cost": 40, "asset_count": 1, "total_credits": 40},
        "shared_prompt_appendix": shared,
        "assets": assets,
    }


def main() -> int:
    save_json(RECRAFT_DIR / "neowakeup_gui_pass_600_manifest.json", build_gui_pass_600())
    save_json(RECRAFT_DIR / "neowakeup_gui_pass_300_manifest.json", build_gui_pass_300())
    save_json(RECRAFT_DIR / "neowakeup_gui_pass_300_corrective_manifest.json", build_gui_pass_300_corrective())
    save_json(RECRAFT_DIR / "neowakeup_dial_knob_corrective_v2_manifest.json", build_dial_knob_v2_corrective())
    print("Wrote NeoWakeUP Recraft manifests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())