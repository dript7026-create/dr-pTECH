import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "assets" / "orbengine_ui_shell"
MANIFEST_PATH = OUTPUT_ROOT / "recraft_orbengine_ui_shell_manifest.json"
PLAN_PATH = OUTPUT_ROOT / "ORBENGINE_UI_SHELL_PLAN.md"

STYLE_BIBLE = (
	"transparent background premium custom Windows desktop game-engine UI asset for ORBEngine, "
	"clean bespoke shell language, obsidian slate base, brushed brass trim, muted teal signal light, soft ember accent, "
	"monolithic sci-fantasy industrial tooling aesthetic, readable at small sizes, no text labels unless specifically requested"
)

WINDOW_SHELLS = [
	("orb_shell_main_window_frame", "main engine shell frame with title bar, dock wells, command strip, and flexible content viewport"),
	("orb_shell_scene_hierarchy_panel", "hierarchy and outliner shell for scene tree and object listing"),
	("orb_shell_inspector_panel", "property inspector shell with grouped controls, foldout lanes, and stat blocks"),
	("orb_shell_asset_browser_panel", "asset browser shell with breadcrumbs, search strip, and tiled content area"),
	("orb_shell_nodegraph_window", "floating node graph editor shell with grid margin, pin shelves, and tab rail"),
	("orb_shell_console_log_panel", "developer console shell with filter rail, line gutter, and status footer"),
	("orb_shell_timeline_panel", "timeline and keyframe shell with scrub rail, track stack, and transport housing"),
	("orb_shell_tool_properties_float", "small floating tool settings shell for contextual brush or transform properties"),
	("orb_shell_command_palette", "command palette shell with omnibox header, result stack, shortcut hint column, and ghosted recent command rail"),
	("orb_shell_docking_overlay_guides", "docking and panel-placement overlay shell with quadrant guides, preview glow, and snap targets"),
]

NAV_TABS = [
	("orb_nav_tabs_primary_strip", "navigation tab strip with multiple coherent tab states in one asset: active, idle, hovered, attention, disabled"),
	("orb_nav_tabs_secondary_strip", "secondary utility tab strip with compact state variants and subtle hierarchy cues"),
	("orb_nav_breadcrumb_capsules", "breadcrumb capsule navigation pieces for deep editor views and drill-down panels"),
	("orb_nav_workspace_switcher", "workspace switcher tab bar for scene, materials, scripting, debug, and UI authoring modes"),
]

POPUPS_AND_DROPDOWNS = [
	("orb_popup_modal_template", "large modal popup shell template with layered frame, confirm area, and content body"),
	("orb_popup_context_menu_shell", "context menu and command list popup shell with nested arrow affordances"),
	("orb_popup_dropdown_shell", "dropdown list shell template with scroll gutter and item highlight states"),
	("orb_popup_notification_toast", "notification toast shell with icon well, short headline lane, and dismiss corner"),
	("orb_popup_tooltip_shell", "tooltip shell with compact frame, pointer notch, and short metadata stripe"),
	("orb_popup_dialog_choice_grid", "choice dialog shell template with multi-button footer, icon socket, and warning accent state"),
]

FONT_ATLASES = [
	("orb_font_monotype_uppercase_atlas", "custom alphanumeric monotype font atlas, uppercase A through Z plus core symbols, grid aligned, clean transparent background"),
	("orb_font_monotype_lowercase_atlas", "custom alphanumeric monotype font atlas, lowercase a through z plus alternate punctuation, grid aligned, clean transparent background"),
	("orb_font_monotype_numeric_atlas", "custom alphanumeric monotype font atlas, numerals 0 through 9 with currency, math, and time separators, grid aligned, clean transparent background"),
	("orb_font_monotype_extended_ui_atlas", "custom alphanumeric monotype font atlas, brackets, arrows, slashes, underscores, pipes, coding punctuation, and UI shorthand marks, grid aligned, clean transparent background"),
]

CURSORS = [
	("orb_cursor_precision_set", "custom cursor set atlas for arrow, beam, precision crosshair, and target reticle states"),
	("orb_cursor_transform_set", "custom cursor set atlas for move, rotate, scale, and axis-handle interaction states"),
	("orb_cursor_resize_set", "custom cursor set atlas for horizontal, vertical, diagonal, and panel-divider resize states"),
	("orb_cursor_link_and_pick_set", "custom cursor set atlas for hand, grab, eyedropper, link, and picker interaction states"),
]

ICON_ATLASES = [
	("orb_icons_toolbar_editing", "toolbar icon atlas for select, move, rotate, scale, duplicate, delete, and snap editing tools"),
	("orb_icons_toolbar_world", "toolbar icon atlas for terrain, lights, fog, camera, markers, portals, and region setup tools"),
	("orb_icons_toolbar_scripting", "toolbar icon atlas for script, compile, hot reload, debug, breakpoint, and event graph tools"),
	("orb_icons_toolbar_animation", "toolbar icon atlas for keyframe, easing, scrub, onion skin, playback, and rig controls"),
	("orb_icons_toolbar_materials", "toolbar icon atlas for brush, fill, sampler, material slot, shader graph, and texture import tools"),
	("orb_icons_status_indicators", "status icon atlas for success, warning, error, dirty, sync, lock, and perf states"),
	("orb_icons_inventory_and_widgets", "widget icon atlas for tabs, drawers, pin, favorite, visibility, folder, list, grid, and filter controls"),
	("orb_icons_scrollbar_and_splitters", "widget icon atlas for scrollbar caps, thumb states, splitter handles, and drag affordances"),
	("orb_icons_window_controls", "window chrome icon atlas for close, maximize, restore, minimize, undock, collapse, and pin controls"),
]

def make_item(name: str, description: str) -> dict:
	return {
		"name": name,
		"prompt": f"{STYLE_BIBLE}, {description}",
		"w": 1024,
		"h": 1024,
		"out": f"orbengine_ui_shell/{name}.png",
		"api_units": 40,
		"model": "recraftv4",
	}


def build_manifest() -> list[dict]:
	groups = [
		WINDOW_SHELLS,
		NAV_TABS,
		POPUPS_AND_DROPDOWNS,
		FONT_ATLASES,
		CURSORS,
		ICON_ATLASES,
	]
	items = []
	for group in groups:
		for name, description in group:
			items.append(make_item(name, description))
	return items


def build_plan(items: list[dict]) -> str:
	lines = [
		"# ORBEngine GUI Shell Recraft Pass",
		"",
		f"Total assets: {len(items)}",
		f"Estimated units: {sum(item['api_units'] for item in items)}",
		"",
		"## Included Groups",
		f"- Window shells: {len(WINDOW_SHELLS)}",
		f"- Navigation tab assets: {len(NAV_TABS)}",
		f"- Popups and dropdown templates: {len(POPUPS_AND_DROPDOWNS)}",
		f"- Monotype font atlases: {len(FONT_ATLASES)}",
		f"- Cursor sets: {len(CURSORS)}",
		f"- Toolbar and widget icon atlases: {len(ICON_ATLASES)}",
		"",
		"## Visual Direction",
		"- Obsidian slate shells with brushed brass edges and muted teal highlights.",
		"- Desktop-application readability first, but with a bespoke ORBEngine sci-fantasy industrial identity.",
		"- Transparent isolated assets so they can be composed in-engine rather than baked into a fixed background.",
		"- Coherent modular panel language across tabs, windows, popups, cursors, icons, and font atlases.",
	]
	return "\n".join(lines) + "\n"


def main() -> int:
	OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
	items = build_manifest()
	MANIFEST_PATH.write_text(json.dumps(items, indent=2), encoding="utf-8")
	PLAN_PATH.write_text(build_plan(items), encoding="utf-8")
	print(
		json.dumps(
			{
				"manifest": str(MANIFEST_PATH),
				"plan": str(PLAN_PATH),
				"items": len(items),
				"estimated_units": sum(item["api_units"] for item in items),
			},
			indent=2,
		)
	)
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
