"""
generate_gui_assets_manifest.py
Generates a Recraft batch manifest JSON for all custom GUI/shell assets
for the ECBMPS and CCP viewers (1500 credits budget).

Usage:
    python generate_gui_assets_manifest.py > ecbmps_ccp_assets_manifest.json
    python ../drIpTECH/ReCraftGenerationStreamline/batch_run_manifest.py \
        --manifest ecbmps_ccp_assets_manifest.json --concurrency 4
"""

import json
import sys

ASSETS_BASE = "assets/recraft"
STYLE = "digital_illustration"
MODEL = "recraftv3"

manifest = []


def add(name, prompt, w, h, out_path, **kw):
    entry = {
        "name": name,
        "prompt": prompt,
        "w": w,
        "h": h,
        "out": f"{ASSETS_BASE}/{out_path}",
        "style": kw.get("style", STYLE),
        "model": kw.get("model", MODEL),
    }
    if "negative_prompt" in kw:
        entry["negative_prompt"] = kw["negative_prompt"]
    manifest.append(entry)


# ═══════════════════════════════════════════════════════════════════
#  SECTION 1: SHELL ICONS — .ecbmps and .ccp file type icons
# ═══════════════════════════════════════════════════════════════════
ICON_SIZES = [16, 32, 48, 64, 128, 256]
for sz in ICON_SIZES:
    add(f"ecbmps_icon_{sz}",
        f"Flat vector file-type icon for electronic book format, open book with colorful gradient pages, "
        f"dark background, {sz}x{sz} pixel art style, clean edges, drIpTECH branding subtle watermark",
        sz, sz, f"icons/ecbmps_icon_{sz}.png")
    add(f"ccp_icon_{sz}",
        f"Flat vector file-type icon for interactive media book, film-strip merged with gamepad controller, "
        f"electric blue accent, dark background, {sz}x{sz} pixel art, crisp edges",
        sz, sz, f"icons/ccp_icon_{sz}.png")

# Shell badge overlays
for badge in ["new", "starred", "locked", "synced"]:
    add(f"shell_badge_{badge}",
        f"Tiny {badge} badge overlay icon, 16x16, subtle glow, clean vector pixel art, transparent bg",
        16, 16, f"icons/shell_badge_{badge}.png")

# Context menu icons
MENU_ICONS = ["open", "edit", "export", "print", "share", "delete", "properties", "compile", "validate", "preview"]
for mi in MENU_ICONS:
    add(f"ctx_menu_{mi}",
        f"Small context-menu icon for '{mi}' action, 20x20 flat vector, subtle gradient, "
        f"professional dark-theme UI icon, transparent background",
        20, 20, f"icons/ctx_menu_{mi}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 2: ECBMPS VIEWER GUI CHROME
# ═══════════════════════════════════════════════════════════════════

# Window frame tiles (3x3 grid: corners + edges + center)
FRAME_PARTS = ["tl", "tc", "tr", "ml", "mc", "mr", "bl", "bc", "br"]
for part in FRAME_PARTS:
    add(f"ecbmps_frame_{part}",
        f"Dark metallic window frame tile ({part} position), subtle brushed-steel texture, "
        f"blue-gray accent glow at edges, 64x64, seamless tile, futuristic book-reader UI",
        64, 64, f"gui/ecbmps/frame_{part}.png")

# Titlebar elements
for elem in ["close", "minimize", "maximize"]:
    for state in ["normal", "hover", "pressed"]:
        add(f"ecbmps_btn_{elem}_{state}",
            f"Window titlebar {elem} button in {state} state, circular 24x24, dark UI, "
            f"{'red glow' if elem=='close' else 'blue accent'} when {'hovered' if state=='hover' else state}, "
            f"glass-like surface, minimalist",
            24, 24, f"gui/ecbmps/titlebar/{elem}_{state}.png")

# Titlebar background tile
add("ecbmps_titlebar_bg",
    "Dark gradient titlebar background tile, horizontal, 256x36, subtle noise texture, "
    "left-to-right dark-charcoal to medium-slate, professional book reader app",
    256, 36, "gui/ecbmps/titlebar/titlebar_bg.png")

# Toolbar buttons
TB_BUTTONS = {
    "prev_page": "left-pointing arrow for previous page navigation",
    "next_page": "right-pointing arrow for next page navigation",
    "first_page": "double left arrow for jump-to-first-page",
    "last_page": "double right arrow for jump-to-last-page",
    "bookmark_add": "red heart or ribbon for adding a bookmark",
    "bookmark_remove": "heart with X for removing a bookmark",
    "highlight_on": "yellow brush/highlighter activated state",
    "highlight_off": "gray brush/highlighter deactivated state",
    "search": "magnifying glass for text search",
    "zoom_in": "plus-sign in circle for zoom-in",
    "zoom_out": "minus-sign in circle for zoom-out",
    "zoom_reset": "1:1 text for zoom-reset",
    "toc": "bullet list for table of contents",
    "settings": "gear/cog for settings",
    "mode_light": "sun icon for light reading mode",
    "mode_dark": "moon icon for dark reading mode",
    "mode_sepia": "warm-toned paper icon for sepia reading mode",
    "fullscreen": "expand arrows for fullscreen toggle",
    "print": "printer icon for print preview",
}
for btn_name, btn_desc in TB_BUTTONS.items():
    for state in ["normal", "hover"]:
        add(f"ecbmps_tb_{btn_name}_{state}",
            f"Toolbar button icon: {btn_desc}, 28x28, {'bright accent glow' if state=='hover' else 'subtle muted tone'}, "
            f"flat vector style, dark background, book-reader UI theme",
            28, 28, f"gui/ecbmps/toolbar/{btn_name}_{state}.png")

# Scrollbar elements
for elem in ["thumb", "track", "arrow_up", "arrow_down"]:
    add(f"ecbmps_scroll_{elem}",
        f"Custom scrollbar {elem} element, dark-theme, subtle blue accent, 16x{'64' if elem=='track' else '16'}, "
        f"rounded corners, glass-like, book-reader aesthetic",
        16, 64 if elem == "track" else 16,
        f"gui/ecbmps/scrollbar/{elem}.png")

# Reading mode backgrounds (full page)
for mode_name, mode_desc in [
    ("light", "clean warm white paper texture, subtle fiber grain"),
    ("dark", "dark charcoal matte surface, very subtle noise"),
    ("sepia", "aged parchment, warm yellowish-brown tone, subtle stain patterns"),
    ("night", "deep navy blue, very low contrast, easy on eyes at night"),
]:
    add(f"ecbmps_bg_{mode_name}",
        f"Full-page reading background: {mode_desc}, 800x600, seamlessly tileable, "
        f"no text or drawings, pure texture only",
        800, 600, f"gui/ecbmps/backgrounds/{mode_name}.png")

# Page corner decorations
for corner in ["tl", "tr", "bl", "br"]:
    add(f"ecbmps_page_corner_{corner}",
        f"Ornamental page corner decoration ({corner} corner), gold/bronze filigree on transparent bg, "
        f"48x48, elegant book-style flourish, semi-transparent",
        48, 48, f"gui/ecbmps/page/corner_{corner}.png")

# Bookmark indicators
for bk_type in ["ribbon_red", "ribbon_blue", "ribbon_green", "ribbon_gold", "dog_ear", "flag"]:
    add(f"ecbmps_bk_{bk_type}",
        f"Bookmark indicator: {bk_type.replace('_', ' ')} style, 24x36, subtle shadow, "
        f"peeking from top-right edge of page, transparent background",
        24, 36, f"gui/ecbmps/bookmarks/{bk_type}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 3: CCP VIEWER GUI CHROME
# ═══════════════════════════════════════════════════════════════════

# CCP Window frame tiles (distinct interactive style)
for part in FRAME_PARTS:
    add(f"ccp_frame_{part}",
        f"Futuristic interactive viewer frame tile ({part} position), neon-edged dark panel, "
        f"electric blue wire-frame accent, 64x64, seamless, sci-fi media player UI",
        64, 64, f"gui/ccp/frame_{part}.png")

# CCP Titlebar
for elem in ["close", "minimize", "maximize"]:
    for state in ["normal", "hover", "pressed"]:
        add(f"ccp_btn_{elem}_{state}",
            f"CCP viewer titlebar {elem} button ({state}), hexagonal 24x24, electric blue neon outline, "
            f"dark bg, sci-fi style, {'bright glow' if state=='hover' else 'subtle dim'} state",
            24, 24, f"gui/ccp/titlebar/{elem}_{state}.png")

add("ccp_titlebar_bg",
    "CCP viewer dark titlebar background, 256x40, horizontal gradient with subtle circuit-board pattern, "
    "electric blue neon line at bottom edge",
    256, 40, "gui/ccp/titlebar/titlebar_bg.png")

# CCP Toolbar buttons
CCP_TB = {
    "prev_page": "left arrow, interactive page navigation",
    "next_page": "right arrow, interactive page navigation",
    "play": "play triangle for animation playback",
    "pause": "pause bars for animation pause",
    "stop": "stop square for animation stop",
    "reset": "circular arrow for scene reset",
    "regions_show": "eye icon for showing interactive regions overlay",
    "regions_hide": "eye with slash for hiding interactive regions",
    "sidebar_show": "left panel icon for showing page sidebar",
    "sidebar_hide": "left panel with X for hiding sidebar",
    "grid_view": "grid icon for page thumbnail grid",
    "list_view": "list icon for page list view",
    "export": "download arrow for export/save",
    "settings": "gear cog for settings panel",
    "layers": "stacked squares for layer control",
    "timeline": "horizontal bars for timeline scrubber",
}
for btn_name, btn_desc in CCP_TB.items():
    for state in ["normal", "hover"]:
        add(f"ccp_tb_{btn_name}_{state}",
            f"CCP toolbar button: {btn_desc}, 28x28, neon-outlined flat vector, "
            f"{'electric blue glow' if state=='hover' else 'cool gray'}, dark bg, interactive media player style",
            28, 28, f"gui/ccp/toolbar/{btn_name}_{state}.png")

# Interactive region indicators
for rgn_type in ["clickable", "draggable", "hover_zone", "anim_trigger", "scene_link", "popup_trigger"]:
    add(f"ccp_region_{rgn_type}",
        f"Interactive region indicator icon for {rgn_type.replace('_', ' ')}, 20x20, semi-transparent, "
        f"neon outline, sci-fi UI element, transparent background",
        20, 20, f"gui/ccp/regions/{rgn_type}.png")

# CCP Sidebar elements
add("ccp_sidebar_bg",
    "CCP sidebar background tile, 180x600, dark panel with subtle vertical gradient, "
    "thin neon blue right-edge border, matte texture",
    180, 600, "gui/ccp/sidebar/sidebar_bg.png")
for elem in ["page_thumb_frame", "page_selected", "page_hover"]:
    add(f"ccp_sidebar_{elem}",
        f"CCP sidebar {elem.replace('_', ' ')}, 160x32, rounded dark pill shape, "
        f"{'bright blue border' if 'selected' in elem else 'subtle border'}, clean vector",
        160, 32, f"gui/ccp/sidebar/{elem}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 4: CUSTOM FONT GLYPH SHEETS
# ═══════════════════════════════════════════════════════════════════

FONT_FAMILIES = {
    "driptech_sans": "clean modern sans-serif, geometric, thin strokes",
    "driptech_serif": "elegant serif with subtle wedge serifs, classic book typography",
    "driptech_display": "bold decorative display face, wide strokes, tech aesthetic, header font",
    "driptech_mono": "monospaced coding font, even character widths, clean terminals",
}
FONT_WEIGHTS = ["light", "regular", "bold"]
FONT_CHAR_SETS = {
    "uppercase": "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z evenly spaced in a single row",
    "lowercase": "a b c d e f g h i j k l m n o p q r s t u v w x y z evenly spaced in a single row",
    "digits": "0 1 2 3 4 5 6 7 8 9 evenly spaced in a single row",
    "punctuation": ". , : ; ! ? - _ ( ) [ ] { } @ # $ % & * + = / \\ single row",
}
for fam_name, fam_desc in FONT_FAMILIES.items():
    for weight in FONT_WEIGHTS:
        for charset_name, charset_desc in FONT_CHAR_SETS.items():
            add(f"{fam_name}_{weight}_{charset_name}",
                f"Font glyph sheet: {fam_desc}, {weight} weight, white glyphs on black background, "
                f"characters: {charset_desc}, uniform cell grid, high contrast, anti-aliased edges, "
                f"256x64 sprite sheet, suitable for bitmap font extraction",
                256, 64, f"fonts/{fam_name}/{weight}_{charset_name}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 5: POPUP / DIALOG WINDOW TEMPLATES
# ═══════════════════════════════════════════════════════════════════

POPUP_TYPES = {
    "confirm": "Confirmation dialog frame with checkmark and X buttons, 'OK / Cancel' layout",
    "error": "Error dialog frame with warning triangle icon, red accent border",
    "info": "Information dialog frame with info-circle icon, blue accent border",
    "input": "Text input dialog frame with text field area and OK/Cancel buttons",
    "file_picker": "File picker overlay with folder tree left panel, file list right panel",
    "progress": "Progress dialog with horizontal progress bar, cancel button",
    "toast_info": "Small toast notification, info style, rounded pill shape, blue accent",
    "toast_success": "Toast notification, success green checkmark, rounded pill",
    "toast_warning": "Toast notification, warning amber triangle, rounded pill",
    "toast_error": "Toast notification, error red X, rounded pill",
    "tooltip": "Tooltip frame, small pointed callout box, dark with blue border",
    "context_menu": "Context menu background frame, dark panel with subtle border, 8 item slots",
}
for popup_name, popup_desc in POPUP_TYPES.items():
    for theme in ["light", "dark"]:
        add(f"popup_{popup_name}_{theme}",
            f"Custom popup template: {popup_desc}, {theme} theme, 320x200, rounded corners 8px, "
            f"{'dark charcoal bg, light text' if theme=='dark' else 'white bg, dark text'}, "
            f"subtle shadow, professional application UI, drIpTECH brand style",
            320, 200, f"gui/popups/{popup_name}_{theme}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 6: SPLASH SCREENS & BRANDING
# ═══════════════════════════════════════════════════════════════════

add("splash_ecbmps",
    "ECBMPS Reader splash screen, centered open-book logo with glowing pages, "
    "'drIpTECH' text below in custom font, dark gradient background, subtle particle effects, "
    "professional software splash, 640x400",
    640, 400, "branding/splash_ecbmps.png")

add("splash_ccp",
    "CCP Interactive Viewer splash screen, film-strip merging with game controller icon, "
    "electric blue neon glow, 'drIpTECH' text, dark futuristic background, 640x400",
    640, 400, "branding/splash_ccp.png")

for brand in ["logo_light", "logo_dark", "watermark", "favicon"]:
    sz = 64 if brand == "favicon" else 256
    add(f"brand_{brand}",
        f"drIpTECH {brand.replace('_', ' ')} asset, clean vector, "
        f"{'light bg' if 'light' in brand else 'dark bg'}, {sz}x{sz}, "
        f"modern tech company branding, book + circuit motif",
        sz, sz, f"branding/{brand}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 7: CONTENT TEMPLATES — pre-designed covers, borders, etc.
# ═══════════════════════════════════════════════════════════════════

# Book covers (genre-specific)
COVER_GENRES = [
    "fantasy", "sci-fi", "mystery", "romance", "horror", "history",
    "biography", "science", "technology", "art", "cooking", "travel",
    "children", "poetry", "philosophy", "music", "nature", "sports",
    "education", "reference", "memoir", "classic", "adventure", "comedy",
    "drama", "thriller", "western", "manga", "graphic_novel", "anthology",
    "self_help", "business", "health", "spirituality", "photography",
    "architecture", "fashion", "design", "economics", "politics",
    "sociology", "psychology", "mathematics", "engineering", "astronomy",
    "marine", "gardening", "craft", "gaming", "programming",
]
for genre in COVER_GENRES:
    add(f"cover_{genre}",
        f"Book cover template for {genre.replace('_', ' ')} genre, beautiful illustration, "
        f"space for title text at top, author name at bottom, 480x640, rich colors, "
        f"professional publishing quality, no actual text rendered",
        480, 640, f"templates/covers/{genre}.png")

# Decorative borders
BORDER_STYLES = [
    "art_nouveau", "art_deco", "celtic_knot", "floral", "geometric",
    "victorian", "japanese", "minimalist", "baroque", "modern",
    "tribal", "greek_key", "rope", "vine", "circuit_board",
    "watercolor", "gold_leaf", "woodcut", "manuscript", "neon",
]
for bstyle in BORDER_STYLES:
    add(f"border_{bstyle}",
        f"Page border decoration: {bstyle.replace('_', ' ')} style, rectangular frame, "
        f"640x480, ornate details, transparent center, suitable for overlaying on pages, "
        f"high-detail vector illustration",
        640, 480, f"templates/borders/{bstyle}.png")

# Chapter dividers
DIVIDER_STYLES = [
    "flourish", "line", "diamond", "star", "leaf", "scroll",
    "geometric", "wave", "arrow", "ornamental", "knot", "feather",
    "sword", "compass", "crown", "key", "anchor", "shield",
    "infinity", "lotus",
]
for dstyle in DIVIDER_STYLES:
    add(f"divider_{dstyle}",
        f"Chapter divider ornament: {dstyle} motif, horizontal, 480x48, centered, "
        f"intricate detail, transparent background, book typography quality",
        480, 48, f"templates/dividers/{dstyle}.png")

# Header/footer ornaments
for ornament in ["header_left", "header_center", "header_right",
                  "footer_left", "footer_center", "footer_right"]:
    for variant in range(1, 6):
        add(f"ornament_{ornament}_v{variant}",
            f"Page {ornament.replace('_', ' ')} ornament variant {variant}, delicate decorative element, "
            f"200x32, transparent background, professional typography accent",
            200, 32, f"templates/ornaments/{ornament}_v{variant}.png")

# Paper textures
PAPER_TYPES = [
    "smooth_white", "cream", "ivory", "parchment_light", "parchment_aged",
    "linen", "cotton", "recycled", "rice_paper", "vellum",
    "newsprint", "kraft", "watercolor_cold", "watercolor_hot", "canvas",
    "cardboard", "tissue", "tracing", "washi", "handmade",
    "marble_white", "marble_cream", "leather_tan", "leather_dark", "leather_red",
]
for paper in PAPER_TYPES:
    add(f"paper_{paper}",
        f"Paper texture: {paper.replace('_', ' ')}, 512x512, seamlessly tileable, "
        f"high-resolution scan quality, realistic fiber/grain detail, no text or marks",
        512, 512, f"templates/textures/paper/{paper}.png")

# Binding/cover material textures
BINDING_TEXTURES = [
    "cloth_navy", "cloth_burgundy", "cloth_green", "cloth_black",
    "leather_brown", "leather_black", "leather_red", "leather_green",
    "buckram_blue", "buckram_gray",
]
for binding in BINDING_TEXTURES:
    add(f"binding_{binding}",
        f"Book binding material texture: {binding.replace('_', ' ')}, 256x256, seamless tile, "
        f"realistic material surface, subtle grain/weave pattern",
        256, 256, f"templates/textures/binding/{binding}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 8: EXTENDED UI & UX ELEMENTS
# ═══════════════════════════════════════════════════════════════════

# Loading/progress indicators
for spinner_style in ["dots", "ring", "book_flip", "pulse", "gears"]:
    for frame in range(1, 9):
        add(f"spinner_{spinner_style}_f{frame}",
            f"Loading spinner animation frame {frame}/8: {spinner_style.replace('_', ' ')} style, "
            f"32x32, dark background, blue accent animation, smooth rotation/progression",
            32, 32, f"gui/spinners/{spinner_style}_f{frame}.png")

# Cursor variants
CURSOR_TYPES = [
    "pointer_default", "pointer_link", "text_select", "highlight_brush",
    "bookmark_place", "zoom_in", "zoom_out", "hand_grab", "hand_grabbing",
    "page_turn",
]
for cursor in CURSOR_TYPES:
    add(f"cursor_{cursor}",
        f"Custom cursor: {cursor.replace('_', ' ')}, 32x32, clean vector, "
        f"dark outline with blue accent, book-reader themed, transparent background",
        32, 32, f"gui/cursors/{cursor}.png")

# Welcome/empty state illustrations
for empty_state in ["no_file", "empty_bookmarks", "no_results", "first_launch", "loading_book"]:
    add(f"empty_{empty_state}",
        f"Empty state illustration: {empty_state.replace('_', ' ')}, centered illustration with "
        f"subtle text prompt area below, 200x200, muted blue-gray palette, friendly/inviting, "
        f"book and reading themed",
        200, 200, f"gui/empty_states/{empty_state}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 9: NAVIGATION & CONTENT ICONS
# ═══════════════════════════════════════════════════════════════════

CONTENT_ICONS = [
    "text_page", "image_page", "combined_page", "chapter_start",
    "chapter_end", "appendix", "index", "glossary", "bibliography",
    "footnote", "endnote", "sidebar", "callout", "quote",
    "table", "figure", "diagram", "chart", "map",
    "audio_clip", "video_clip", "interactive_widget", "animation",
    "quiz", "exercise", "example", "solution", "warning",
    "tip", "note", "important", "caution", "definition",
]
for icon in CONTENT_ICONS:
    add(f"content_{icon}",
        f"Content type icon: {icon.replace('_', ' ')}, 24x24, flat vector, "
        f"subtle gradient, professional palette, book & media reader UI",
        24, 24, f"gui/content_icons/{icon}.png")

# Genre tag icons
GENRE_ICONS = [
    "fiction", "nonfiction", "academic", "technical", "creative",
    "journalistic", "editorial", "instructional", "reference", "periodical",
]
for genre_icon in GENRE_ICONS:
    add(f"genre_{genre_icon}",
        f"Genre classification icon: {genre_icon}, 24x24, subtle color-coded badge, "
        f"recognizable symbol, transparent background",
        24, 24, f"gui/genre_icons/{genre_icon}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 10: THEME COLOR VARIANTS — duplicate key GUI elements in
#  accent color palettes (amethyst, emerald, amber, coral, ice)
# ═══════════════════════════════════════════════════════════════════

ACCENT_THEMES = {
    "amethyst": "purple/violet accent, amethyst crystal glow",
    "emerald": "rich green accent, emerald gem glow",
    "amber": "warm amber/gold accent, soft golden glow",
    "coral": "coral pink/salmon accent, warm inviting glow",
    "ice": "cool ice-blue/cyan accent, frosty crystalline glow",
}
THEMED_ELEMENTS = [
    ("frame_tl", 64, 64, "window frame top-left corner tile"),
    ("frame_tr", 64, 64, "window frame top-right corner tile"),
    ("frame_bl", 64, 64, "window frame bottom-left corner tile"),
    ("frame_br", 64, 64, "window frame bottom-right corner tile"),
    ("titlebar_bg", 256, 36, "titlebar background gradient tile"),
    ("scroll_thumb", 16, 64, "scrollbar thumb element"),
    ("btn_prev_normal", 28, 28, "previous page button"),
    ("btn_next_normal", 28, 28, "next page button"),
    ("btn_bookmark_normal", 28, 28, "bookmark button"),
    ("btn_settings_normal", 28, 28, "settings button"),
]
for viewer_prefix in ["ecbmps", "ccp"]:
    for theme_name, theme_desc in ACCENT_THEMES.items():
        for elem_name, ew, eh, elem_desc in THEMED_ELEMENTS:
            add(f"{viewer_prefix}_{theme_name}_{elem_name}",
                f"{viewer_prefix.upper()} viewer {elem_desc} in {theme_name} theme, {theme_desc}, "
                f"{ew}x{eh}, dark background, themed accent replacing default blue",
                ew, eh, f"gui/{viewer_prefix}/themes/{theme_name}/{elem_name}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 11: ADDITIONAL COVER VARIANTS — 2nd cover per genre
# ═══════════════════════════════════════════════════════════════════

for genre in COVER_GENRES:
    add(f"cover_{genre}_v2",
        f"Alternative book cover template for {genre.replace('_', ' ')} genre, distinct style from v1, "
        f"bold typography area, 480x640, contemporary design, eye-catching composition",
        480, 640, f"templates/covers/{genre}_v2.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 12: TEXTURE PACK EXPANSION — surfaces, fabrics, materials
# ═══════════════════════════════════════════════════════════════════

EXTRA_TEXTURES = [
    "slate_gray", "sandstone", "granite", "wood_oak", "wood_walnut",
    "wood_cherry", "wood_maple", "wood_birch", "bamboo", "cork",
    "denim_blue", "denim_black", "velvet_purple", "velvet_red", "silk_cream",
    "silk_gold", "burlap", "felt_green", "felt_gray", "suede_brown",
    "metal_brushed", "metal_hammered", "copper_patina", "brass_polished", "stone_cobble",
]
for tex in EXTRA_TEXTURES:
    add(f"texture_{tex}",
        f"Material texture: {tex.replace('_', ' ')}, 512x512, seamlessly tileable, "
        f"photorealistic surface detail, neutral color, high-res quality",
        512, 512, f"templates/textures/materials/{tex}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 13: TUTORIAL & HELP ILLUSTRATIONS
# ═══════════════════════════════════════════════════════════════════

TUTORIAL_SCENES = [
    "opening_a_file", "navigating_pages", "adding_bookmarks", "highlighting_text",
    "changing_reading_mode", "using_search", "zooming", "using_table_of_contents",
    "keyboard_shortcuts", "drag_and_drop", "interactive_regions", "sidebar_navigation",
    "animation_playback", "layer_toggling", "exporting_content",
    "setting_preferences", "first_time_welcome", "file_associations",
    "printing_pages", "sharing_content",
]
for scene in TUTORIAL_SCENES:
    add(f"tutorial_{scene}",
        f"Tutorial illustration: showing user how to {scene.replace('_', ' ')} in the book reader, "
        f"flat vector style, friendly muted palette, 320x240, step-by-step visual guide feel, "
        f"numbered annotation markers, clean composition",
        320, 240, f"gui/tutorials/{scene}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 14: ACHIEVEMENT / BADGE ICONS (CCP gamification)
# ═══════════════════════════════════════════════════════════════════

ACHIEVEMENTS = [
    "first_page", "speed_reader", "bookworm", "completionist", "explorer",
    "collector", "annotator", "night_owl", "early_bird", "marathoner",
    "discoverer", "scribe", "curator", "navigator", "scholar",
    "pathfinder", "archivist", "librarian", "connoisseur", "master_reader",
    "bronze_star", "silver_star", "gold_star", "platinum_star", "diamond_star",
    "streak_3", "streak_7", "streak_30", "streak_100", "streak_365",
    "highlight_novice", "highlight_expert", "bookmark_collector", "all_pages", "secret_found",
    "combo_2x", "combo_5x", "combo_10x", "perfect_run", "time_trial",
]
for ach in ACHIEVEMENTS:
    add(f"achievement_{ach}",
        f"Achievement badge: {ach.replace('_', ' ')}, circular 48x48, subtle metallic sheen, "
        f"embossed icon center, dark rim, gaming achievement style, beautiful detail",
        48, 48, f"gui/achievements/{ach}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 15: ADDITIONAL BORDER STYLES & DECORATIVE FRAMES
# ═══════════════════════════════════════════════════════════════════

EXTRA_BORDERS = [
    "steampunk", "cyberpunk", "botanical", "nautical", "astronomical",
    "medieval", "renaissance", "deco_gold", "deco_silver", "mosaic",
    "stained_glass", "origami", "calligraphy", "typographic", "photographic",
    "film_strip", "pixel_art", "wireframe", "blueprint", "chalkboard",
]
for bstyle in EXTRA_BORDERS:
    add(f"border_{bstyle}",
        f"Page border decoration: {bstyle.replace('_', ' ')} style, rectangular frame, "
        f"640x480, detailed ornamental design, transparent center for content overlay",
        640, 480, f"templates/borders/{bstyle}.png")

# Additional dividers
EXTRA_DIVIDERS = [
    "dragon", "phoenix", "oak_branch", "laurel", "quill",
    "chain", "ribbon", "banner", "torch", "hourglass",
    "scales", "harp", "butterfly", "peacock", "serpent",
    "thunderbolt", "trident", "wreath", "medallion", "chalice",
]
for dstyle in EXTRA_DIVIDERS:
    add(f"divider_{dstyle}",
        f"Chapter divider ornament: {dstyle} motif, horizontal, 480x48, "
        f"delicate linework, transparent background, book typography decoration",
        480, 48, f"templates/dividers/{dstyle}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 16: WINDOW ANIMATION FRAMES (open, close, minimize)
# ═══════════════════════════════════════════════════════════════════

for anim_type in ["window_open", "window_close", "window_minimize", "page_turn_left", "page_turn_right"]:
    for frame in range(1, 13):
        add(f"anim_{anim_type}_f{frame}",
            f"Window animation frame {frame}/12: {anim_type.replace('_', ' ')} transition, "
            f"64x64, alpha-blended, smooth easing {'start' if frame < 4 else 'middle' if frame < 9 else 'end'}, "
            f"dark theme, subtle blue glow particles",
            64, 64, f"gui/animations/{anim_type}/f{frame:02d}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 17: EXTENDED FONT VARIANTS (italic + condensed)
# ═══════════════════════════════════════════════════════════════════

EXTRA_FONT_STYLES = {
    "italic": "italic/oblique",
    "condensed": "condensed/narrow width",
    "wide": "extended/wide width",
}
for fam_name, fam_desc in FONT_FAMILIES.items():
    for style_name, style_desc in EXTRA_FONT_STYLES.items():
        for charset_name, charset_desc in FONT_CHAR_SETS.items():
            add(f"{fam_name}_{style_name}_{charset_name}",
                f"Font glyph sheet: {fam_desc}, {style_desc} variant, white on black, "
                f"characters: {charset_desc}, 256x64 sprite sheet, bitmap font extraction ready",
                256, 64, f"fonts/{fam_name}/{style_name}_{charset_name}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 18: DROP CAPS / INITIAL LETTER DECORATIONS
# ═══════════════════════════════════════════════════════════════════

DROP_CAP_STYLES = ["illuminated", "floral", "gothic", "modern", "celtic", "art_nouveau"]
for dc_style in DROP_CAP_STYLES:
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        add(f"dropcap_{dc_style}_{letter}",
            f"Decorative drop capital letter '{letter}': {dc_style.replace('_', ' ')} style, "
            f"ornate initial letter for chapter openings, 64x64, rich color, "
            f"transparent background, book typography quality",
            64, 64, f"templates/dropcaps/{dc_style}/{letter}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 19: PATTERN / ENDPAPER DESIGNS
# ═══════════════════════════════════════════════════════════════════

ENDPAPER_PATTERNS = [
    "marbled_blue", "marbled_red", "marbled_green", "marbled_gold",
    "paisley", "damask", "herringbone", "chevron",
    "polka_dots", "stripes", "plaid", "houndstooth",
    "stars", "moons", "leaves", "flowers",
    "scales", "honeycomb", "diamond_lattice", "ogee",
    "toile", "chinoiserie", "ikat", "batik",
    "shibori", "tie_dye", "galaxy", "nebula",
    "topographic", "fingerprint",
]
for pattern in ENDPAPER_PATTERNS:
    add(f"endpaper_{pattern}",
        f"Decorative endpaper pattern: {pattern.replace('_', ' ')}, 512x512, seamlessly tileable, "
        f"rich saturated colors, traditional bookbinding endpaper quality",
        512, 512, f"templates/textures/endpapers/{pattern}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 20: NOTIFICATION / ALERT ILLUSTRATIONS
# ═══════════════════════════════════════════════════════════════════

NOTIFICATION_TYPES = [
    "save_success", "save_failed", "bookmark_added", "bookmark_removed",
    "highlight_added", "highlight_removed", "file_opened", "file_closed",
    "search_found", "search_not_found", "export_complete", "export_failed",
    "settings_saved", "update_available", "offline_mode", "sync_complete",
    "new_content", "reading_complete", "milestone_reached", "daily_streak",
]
for nt in NOTIFICATION_TYPES:
    add(f"notif_{nt}",
        f"Notification illustration: {nt.replace('_', ' ')}, small centered icon with message area, "
        f"72x72, clean flat vector, muted palette with accent color, transparent bg",
        72, 72, f"gui/notifications/{nt}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 21: ADDITIONAL GUI DECORATIVE PANELS
# ═══════════════════════════════════════════════════════════════════

PANEL_TYPES = [
    "info_panel_bg", "warning_panel_bg", "error_panel_bg", "success_panel_bg",
    "quote_panel_bg", "code_panel_bg", "note_panel_bg", "tip_panel_bg",
    "sidebar_section_bg", "footer_panel_bg",
]
for panel in PANEL_TYPES:
    for theme in ["light", "dark"]:
        add(f"panel_{panel}_{theme}",
            f"Decorative panel background: {panel.replace('_', ' ')}, {theme} theme, "
            f"400x120, subtle gradient, rounded corners, left-accent stripe, "
            f"{'dark charcoal' if theme == 'dark' else 'soft white'} base",
            400, 120, f"gui/panels/{panel}_{theme}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 22: TAB / SEGMENTED CONTROL ELEMENTS
# ═══════════════════════════════════════════════════════════════════

for viewer in ["ecbmps", "ccp"]:
    for tab_state in ["active", "inactive", "hover", "disabled"]:
        add(f"{viewer}_tab_{tab_state}",
            f"{viewer.upper()} viewer tab element: {tab_state} state, 120x32, "
            f"rounded top corners, {'blue accent' if tab_state == 'active' else 'muted gray'}, "
            f"dark theme, clean segmented control appearance",
            120, 32, f"gui/{viewer}/tabs/tab_{tab_state}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 23: MINI-MAP / PAGE PREVIEW FRAMES
# ═══════════════════════════════════════════════════════════════════

for viewer in ["ecbmps", "ccp"]:
    for preview_type in ["thumbnail_frame", "minimap_bg", "minimap_viewport",
                          "preview_hover", "preview_selected", "preview_bookmarked"]:
        add(f"{viewer}_preview_{preview_type}",
            f"{viewer.upper()} page preview element: {preview_type.replace('_', ' ')}, "
            f"80x100, dark theme, subtle border, {'accent highlight' if 'selected' in preview_type else 'neutral'}, "
            f"page thumbnail UI component",
            80, 100, f"gui/{viewer}/previews/{preview_type}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 24: MORE COVER GENRE VARIANTS (v3 minimalist)
# ═══════════════════════════════════════════════════════════════════

for genre in COVER_GENRES[:25]:
    add(f"cover_{genre}_v3",
        f"Minimalist book cover template for {genre.replace('_', ' ')}: solid color background, "
        f"single iconic symbol centered, large title placeholder area, 480x640, "
        f"Scandinavian design aesthetic, two-tone palette",
        480, 640, f"templates/covers/{genre}_v3.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 25: SOCIAL / SHARING ICONS
# ═══════════════════════════════════════════════════════════════════

SOCIAL_ICONS = [
    "share_generic", "copy_link", "email", "qr_code",
    "embed_code", "citation", "rating_star_empty", "rating_star_half",
    "rating_star_full", "like", "dislike", "favorite",
    "comment", "reply", "flag", "report",
]
for sicon in SOCIAL_ICONS:
    add(f"social_{sicon}",
        f"Social/sharing icon: {sicon.replace('_', ' ')}, 24x24, flat vector, "
        f"professional palette, transparent bg, UI icon style",
        24, 24, f"gui/social_icons/{sicon}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 26: EX LIBRIS / BOOKPLATE DESIGNS
# ═══════════════════════════════════════════════════════════════════

BOOKPLATE_STYLES = [
    "classic_shield", "owl_wisdom", "tree_knowledge", "quill_ink",
    "open_book", "candle_flame", "compass_rose", "hourglass",
    "globe_world", "lighthouse", "crown_laurel", "eagle_banner",
    "floral_wreath", "celtic_cross", "ship_voyage", "castle_tower",
    "sun_moon", "phoenix_rebirth", "dragon_guard", "unicorn_magic",
]
for bp in BOOKPLATE_STYLES:
    add(f"bookplate_{bp}",
        f"Ex libris bookplate design: {bp.replace('_', ' ')} motif, 240x320, "
        f"detailed engraving/woodcut style, 'Ex Libris' text area at top, "
        f"name placeholder field, border decoration, vintage aesthetic",
        240, 320, f"templates/bookplates/{bp}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 27: BOOK SPINE DESIGNS
# ═══════════════════════════════════════════════════════════════════

SPINE_STYLES = [
    "cloth_plain", "leather_classic", "gilt_ornate", "modern_minimal",
    "art_deco", "japanese", "victorian", "medieval",
    "sci_fi", "botanical", "geometric", "embossed",
    "foil_stamped", "painted", "wrapped", "ribbon_marker",
    "tooled_leather", "linen_textured", "buckram_simple", "silk_wrapped",
]
for spine in SPINE_STYLES:
    add(f"spine_{spine}",
        f"Book spine design: {spine.replace('_', ' ')} style, 60x480 vertical, "
        f"horizontal title text placeholder area, publisher logo area at bottom, "
        f"realistic bookshelf appearance, professional binding",
        60, 480, f"templates/spines/{spine}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 28: READING PROGRESS VISUALIZATION
# ═══════════════════════════════════════════════════════════════════

for viz_type in ["progress_bar_fill", "progress_bar_bg", "progress_bar_glow",
                  "chapter_dot_complete", "chapter_dot_current", "chapter_dot_upcoming",
                  "milestone_marker", "reading_streak_flame",
                  "time_spent_clock", "pages_read_stack"]:
    for theme in ["light", "dark"]:
        add(f"progress_{viz_type}_{theme}",
            f"Reading progress element: {viz_type.replace('_', ' ')}, {theme} theme, "
            f"{'wide strip' if 'bar' in viz_type else '32x32 icon'}, "
            f"clean vector, {'warm gold' if 'complete' in viz_type else 'blue accent'}, "
            f"encouraging feel, book-reader progress tracking",
            200 if "bar" in viz_type else 32,
            16 if "bar" in viz_type else 32,
            f"gui/progress/{viz_type}_{theme}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 29: CARD / WIDGET TEMPLATES
# ═══════════════════════════════════════════════════════════════════

CARD_TYPES = [
    "book_card", "recent_card", "recommendation_card", "stats_card",
    "review_card", "note_card", "collection_card", "series_card",
    "author_card", "publisher_card",
]
for card in CARD_TYPES:
    for theme in ["light", "dark"]:
        add(f"card_{card}_{theme}",
            f"UI card template: {card.replace('_', ' ')}, {theme} theme, 280x180, "
            f"rounded corners, subtle shadow, thumbnail area left, text area right, "
            f"modern app card widget style, {'dark charcoal' if theme == 'dark' else 'white'} bg",
            280, 180, f"gui/cards/{card}_{theme}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 30: ADDITIONAL ORNAMENTAL DROP CAPS (2 more styles)
# ═══════════════════════════════════════════════════════════════════

for dc_style in ["art_deco", "watercolor"]:
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        add(f"dropcap_{dc_style}_{letter}",
            f"Decorative drop capital '{letter}': {dc_style.replace('_', ' ')} style, "
            f"ornate initial letter, 64x64, transparent bg, chapter-opening quality",
            64, 64, f"templates/dropcaps/{dc_style}/{letter}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 31: NAVIGATION BREADCRUMB ELEMENTS
# ═══════════════════════════════════════════════════════════════════

for nav_elem in ["breadcrumb_separator", "breadcrumb_home", "breadcrumb_bg",
                  "nav_dot_active", "nav_dot_inactive", "nav_dot_hover",
                  "page_indicator_current", "page_indicator_other",
                  "scroll_position_marker", "reading_position_indicator",
                  "chapter_progress_fill", "chapter_progress_empty",
                  "section_divider_h", "section_divider_v",
                  "expand_arrow", "collapse_arrow"]:
    add(f"nav_{nav_elem}",
        f"Navigation element: {nav_elem.replace('_', ' ')}, 24x24, "
        f"subtle dark-theme accent, clean vector, transparent bg",
        24, 24, f"gui/navigation/{nav_elem}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 32: SEASONAL / THEMED READING OVERLAYS
# ═══════════════════════════════════════════════════════════════════

SEASONAL_THEMES = [
    "spring_cherry_blossom", "spring_meadow", "spring_rain",
    "summer_tropical", "summer_sunset", "summer_ocean",
    "autumn_leaves", "autumn_harvest", "autumn_fog",
    "winter_snow", "winter_cozy", "winter_frost",
    "holiday_festive", "holiday_lantern", "holiday_fireworks",
    "night_stars", "night_aurora", "night_campfire",
    "morning_sunrise", "morning_dew",
]
for theme in SEASONAL_THEMES:
    for elem in ["page_overlay", "corner_accent"]:
        add(f"seasonal_{theme}_{elem}",
            f"Seasonal reading overlay: {theme.replace('_', ' ')} {elem.replace('_', ' ')}, "
            f"{'640x480 semi-transparent' if 'overlay' in elem else '120x120 corner decoration'}, "
            f"subtle atmospheric effect, beautiful seasonal ambiance, transparent bg",
            640 if "overlay" in elem else 120,
            480 if "overlay" in elem else 120,
            f"templates/seasonal/{theme}_{elem}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 33: ACCESSIBILITY & SETTINGS ICONS
# ═══════════════════════════════════════════════════════════════════

A11Y_ICONS = [
    "font_size_increase", "font_size_decrease", "font_family",
    "line_spacing", "word_spacing", "margin_adjust",
    "contrast_high", "contrast_low", "dyslexia_mode",
    "text_to_speech", "screen_reader", "color_filter",
    "focus_mode", "distraction_free", "night_light",
    "auto_scroll", "page_flip_style", "animation_reduce",
    "language_select", "dictionary_lookup",
]
for a11y in A11Y_ICONS:
    add(f"a11y_{a11y}",
        f"Accessibility/settings icon: {a11y.replace('_', ' ')}, 28x28, "
        f"clear universal-design icon, dark-theme friendly, blue accent, transparent bg",
        28, 28, f"gui/accessibility/{a11y}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 34: FILE FORMAT INDICATOR BADGES
# ═══════════════════════════════════════════════════════════════════

FORMAT_BADGES = [
    "ecbmps_v1", "ecbmps_v2", "ccp_v1", "ccp_v2",
    "text_only", "image_only", "combined",
    "interactive", "animated", "bookmarked",
    "highlighted", "annotated", "encrypted",
    "compressed", "validated", "draft",
    "published", "archived", "shared", "synced",
]
for badge in FORMAT_BADGES:
    add(f"format_badge_{badge}",
        f"File format indicator badge: {badge.replace('_', ' ')}, 48x20, "
        f"rounded pill shape, subtle gradient, professional tag/badge style, "
        f"clear readable small text aesthetic, transparent bg",
        48, 20, f"gui/format_badges/{badge}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 35: PRINT LAYOUT TEMPLATES
# ═══════════════════════════════════════════════════════════════════

PRINT_LAYOUTS = [
    "single_page", "two_up", "four_up", "booklet",
    "pocket", "letter", "a4", "legal",
    "landscape", "poster",
]
for layout in PRINT_LAYOUTS:
    add(f"print_layout_{layout}",
        f"Print layout preview template: {layout.replace('_', ' ')} format, 200x280, "
        f"wireframe page layout with text/image placeholder areas, printer-preview style, "
        f"light gray outlines on white, professional print dialog preview",
        200, 280, f"gui/print_layouts/{layout}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 36: TOOLBAR SEPARATOR & DECORATION ELEMENTS
# ═══════════════════════════════════════════════════════════════════

for viewer in ["ecbmps", "ccp"]:
    for deco in ["separator_v", "separator_h", "spacer", "grip_dots",
                  "toolbar_bg_left", "toolbar_bg_center", "toolbar_bg_right",
                  "toolbar_shadow", "toolbar_glow_accent",
                  "button_group_left", "button_group_center", "button_group_right"]:
        add(f"{viewer}_deco_{deco}",
            f"{viewer.upper()} toolbar decoration: {deco.replace('_', ' ')}, "
            f"{'4x28' if 'separator_v' in deco else '256x4' if 'separator_h' in deco else '32x32'}, "
            f"dark theme, subtle detail, seamless tile, professional toolbar chrome",
            4 if "separator_v" in deco else 256 if "separator_h" in deco else 32,
            28 if "separator_v" in deco else 4 if "separator_h" in deco else 32,
            f"gui/{viewer}/toolbar_deco/{deco}.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 37: REMAINING MINIMALIST COVER VARIANTS
# ═══════════════════════════════════════════════════════════════════

for genre in COVER_GENRES[25:]:
    add(f"cover_{genre}_v3",
        f"Minimalist book cover: {genre.replace('_', ' ')}, solid color bg, single symbol, "
        f"480x640, Scandinavian design aesthetic, two-tone palette, title placeholder",
        480, 640, f"templates/covers/{genre}_v3.png")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 38: STATUS BAR ELEMENTS
# ═══════════════════════════════════════════════════════════════════

STATUS_ELEMS = [
    "battery_reading", "wifi_sync", "cloud_connected", "cloud_offline",
    "clock", "page_count", "word_count", "time_remaining",
    "brightness", "volume", "zoom_level", "font_size_indicator",
    "mode_indicator_light", "mode_indicator_dark", "mode_indicator_sepia",
    "encoding_utf8", "language_en", "language_es", "language_fr", "language_de",
    "language_ja", "language_zh", "language_ko", "language_ar", "language_hi",
]
for se in STATUS_ELEMS:
    add(f"status_{se}",
        f"Status bar icon: {se.replace('_', ' ')}, 16x16, minimal flat vector, "
        f"subtle muted tone, dark-theme status bar element, transparent bg",
        16, 16, f"gui/status_bar/{se}.png")

# ═══════════════════════════════════════════════════════════════════
# OUTPUT
# ═══════════════════════════════════════════════════════════════════
total = len(manifest)
# Write to file or stdout
if len(sys.argv) > 1 and sys.argv[1] == "--count":
    print(f"Total assets: {total}")
    sys.exit(0)

output = json.dumps(manifest, indent=2)
print(output, file=sys.stdout)

# Also write summary stats to stderr
categories = {}
for item in manifest:
    cat = item["out"].split("/")[2] if len(item["out"].split("/")) > 2 else "other"
    categories[cat] = categories.get(cat, 0) + 1

print(f"\n=== ECBMPS/CCP Asset Manifest Summary ===", file=sys.stderr)
print(f"Total assets: {total}", file=sys.stderr)
print(f"Estimated Recraft credits: {total}", file=sys.stderr)
for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {count}", file=sys.stderr)
