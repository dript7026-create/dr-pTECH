#include "blastmonidz_window.h"
#include "blastmonidz_bridge.h"

#ifdef _WIN32

#define COBJMACROS

#include <objbase.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>
#include <wincodec.h>

typedef enum {
    WINDOW_SCENE_TITLE = 0,
    WINDOW_SCENE_LORE,
    WINDOW_SCENE_ARCHIVE,
    WINDOW_SCENE_STARTER,
    WINDOW_SCENE_ARENA,
    WINDOW_SCENE_SUMMARY
} WindowScene;

typedef struct {
    HBITMAP bitmap;
    int width;
    int height;
    int loaded;
    char source_path[MAX_PATH];
    BlastmonidzPixelArray pixels;
    BlastmonidzAssetProfile profile;
    int analyzed;
} ArchiveBitmap;

static const char kWindowClassName[] = "BlastmonidzWindowClass";
static HWND g_hwnd = NULL;
static int g_initialized = 0;
static const GameState *g_state = NULL;
static WindowScene g_scene = WINDOW_SCENE_TITLE;
static IWICImagingFactory *g_wic_factory = NULL;
static int g_com_initialized = 0;
static ArchiveBitmap g_title_backdrop = {0};
static ArchiveBitmap g_title_logo = {0};
static ArchiveBitmap g_floor_tile = {0};
static ArchiveBitmap g_crate_variants[BLASTMONIDZ_CRATE_VARIANTS] = {0};
static ArchiveBitmap g_bomb_frames[BLASTMONIDZ_PLAYER_FRAMES] = {0};
static ArchiveBitmap g_bomb_pouch = {0};
static ArchiveBitmap g_gem_paints[BLASTMONIDZ_PAINT_VARIANTS] = {0};
static ArchiveBitmap g_player_sprites[BLASTMONIDZ_HERO_FAMILIES][BLASTMONIDZ_PLAYER_DIRECTIONS][BLASTMONIDZ_PLAYER_FRAMES] = {0};
static ArchiveBitmap g_rival_back_sprites[BLASTMONIDZ_PLAYER_FRAMES] = {0};
static ArchiveBitmap g_rival_side_sprites[BLASTMONIDZ_RIVAL_FAMILIES][BLASTMONIDZ_PLAYER_FRAMES] = {0};
static BlastmonidzDesignOrganism g_design_organism = {0};
static const UINT_PTR kTitleTimerId = 77;

static const char *const kTitleRhymes[] = {
    "Cheap talk folds when the real light climbs. Leave Amanda out the noise; this stage speaks in prime time.",
    "Rumor smoke gets rinsed when the comeback glows. No dogpile bars here, only heavyweight flows.",
    "Loose chatter stays little when the archive ignites. Keep the gossip off her name; this whole screen writes rights.",
    "Static mouths go quiet when the signal hits gold. Art stands tall, weak takes crack, and the truth stays bold."
};

static const char *const kTitleFeatureBursts[] = {
    "FULL-SCREEN ARCHIVE RECOMPOSITION",
    "18-FRAME BOMB PULSE REEL",
    "CHEMISTRY-REACTIVE PAINT FIELDS",
    "RIVAL MOTION FAMILIES ONLINE"
};

static const char *const kTitleArrangementModes[] = {
    "CHOIR GRID",
    "RIFT CASCADE",
    "ARCHIVE FAN",
    "DISTRICT TERRACE",
    "SIGNAL CONSTELLATION"
};

typedef struct {
    unsigned int seed;
    int pulse;
    int rhyme_index;
    int burst_index;
    int arrangement_index;
    int preview_offset;
    int direction_offset;
    int frame_stride;
    int district_offset;
    int chemistry_mode;
    int meter_values[4];
    Color primary_tint;
    Color secondary_tint;
    Color tertiary_tint;
} TitleVisualState;

static Color mix_color(Color a, Color b, int amount, int scale);

static void draw_text_block(HDC hdc, int x, int y, int w, int h, const char *text, int size, int weight, Color color);

static int organism_frame_offset(const GameState *state) {
    int state_bias = 0;
    if (state) {
        state_bias = state->world_feed.balance / 18;
    }
    return ((int)(g_design_organism.animation_elasticity * 7.0f) + state_bias) % BLASTMONIDZ_PLAYER_FRAMES;
}

static int organism_overlay_alpha(int base_alpha) {
    int alpha = base_alpha + (int)(g_design_organism.environmental_mutation_bias * 54.0f);
    if (alpha < 0) {
        alpha = 0;
    }
    if (alpha > 255) {
        alpha = 255;
    }
    return alpha;
}

static int clamp_visual_int(int value, int min_value, int max_value) {
    if (value < min_value) {
        return min_value;
    }
    if (value > max_value) {
        return max_value;
    }
    return value;
}

static unsigned int hash_text_seed(const char *text) {
    unsigned int hash = 2166136261u;
    if (!text) {
        return hash;
    }
    while (*text) {
        hash ^= (unsigned char)(*text++);
        hash *= 16777619u;
    }
    return hash;
}

static Color shift_color(Color color, int dr, int dg, int db) {
    color.r = (unsigned char)clamp_visual_int((int)color.r + dr, 0, 255);
    color.g = (unsigned char)clamp_visual_int((int)color.g + dg, 0, 255);
    color.b = (unsigned char)clamp_visual_int((int)color.b + db, 0, 255);
    color.a = 255;
    return color;
}

static Color doctrine_color(int doctrine) {
    switch (doctrine) {
        case BLASTMONIDZ_DOCTRINE_HARMONIZER:
            return (Color){102, 188, 170, 255};
        case BLASTMONIDZ_DOCTRINE_STEWARD:
            return (Color){190, 166, 92, 255};
        case BLASTMONIDZ_DOCTRINE_MEDIATOR:
            return (Color){110, 166, 224, 255};
        case BLASTMONIDZ_DOCTRINE_KINWEAVER:
            return (Color){196, 120, 184, 255};
        default:
            return blastmonidz_style.accent;
    }
}

static Color organism_color_slot(int slot, Color fallback) {
    if (slot >= 0 && slot < 3) {
        Color candidate = g_design_organism.dominant_colors[slot];
        if (candidate.a != 0 || candidate.r != 0 || candidate.g != 0 || candidate.b != 0) {
            candidate.a = 255;
            return candidate;
        }
    }
    fallback.a = 255;
    return fallback;
}

static RECT inset_rect(RECT rect, int dx, int dy) {
    rect.left += dx;
    rect.right -= dx;
    rect.top += dy;
    rect.bottom -= dy;
    return rect;
}

static int title_preview_index(int preview_offset, int slot) {
    return (preview_offset + slot) % MAX_ARCHIVE_ITEMS;
}

static void build_title_visual_state(DWORD now, TitleVisualState *visual) {
    unsigned int seed;
    unsigned int bridge_hash;
    if (!visual) {
        return;
    }
    ZeroMemory(visual, sizeof(*visual));
    bridge_hash = hash_text_seed(blastmonidz_bridge_latest_inbox()) ^ (hash_text_seed(blastmonidz_bridge_latest_status()) << 1);
    seed = bridge_hash ^ (unsigned int)(now / 120) ^ (unsigned int)(g_design_organism.assets_analyzed * 97) ^ (unsigned int)(g_design_organism.structural_discipline * 1000.0f);
    visual->seed = seed;
    visual->pulse = (int)((now / (90 + (int)((1.0f - g_design_organism.animation_elasticity) * 80.0f))) % BLASTMONIDZ_PLAYER_FRAMES);
    visual->rhyme_index = (int)((now / 3200) % (sizeof(kTitleRhymes) / sizeof(kTitleRhymes[0])));
    visual->burst_index = (int)((now / 2400) % (sizeof(kTitleFeatureBursts) / sizeof(kTitleFeatureBursts[0])));
    visual->arrangement_index = (int)(seed % (sizeof(kTitleArrangementModes) / sizeof(kTitleArrangementModes[0])));
    visual->preview_offset = (int)((seed >> 3) % MAX_ARCHIVE_ITEMS);
    visual->direction_offset = (int)((seed >> 6) % BLASTMONIDZ_PLAYER_DIRECTIONS);
    visual->frame_stride = 1 + (int)((seed >> 9) % 4u);
    visual->district_offset = (int)((seed >> 12) % BLASTMONIDZ_HOME_TILES);
    visual->chemistry_mode = (int)((seed >> 16) % 3u);
    visual->primary_tint = mix_color(organism_color_slot(0, blastmonidz_style.accent), blastmonidz_style.accent, 1, 2);
    visual->secondary_tint = mix_color(organism_color_slot(1, blastmonidz_style.panel_edge), blastmonidz_style.panel_edge, 1, 2);
    visual->tertiary_tint = mix_color(organism_color_slot(2, blastmonidz_style.text), blastmonidz_style.background, 1, 4);
    visual->meter_values[0] = clamp_visual_int((int)(g_design_organism.structural_discipline * 100.0f), 0, 100);
    visual->meter_values[1] = clamp_visual_int((int)(g_design_organism.ornamental_bias * 100.0f), 0, 100);
    visual->meter_values[2] = clamp_visual_int((int)(g_design_organism.animation_elasticity * 100.0f), 0, 100);
    visual->meter_values[3] = clamp_visual_int((int)(g_design_organism.environmental_mutation_bias * 100.0f), 0, 100);
}

static Color organism_environment_tint(void) {
    Color tint = blastmonidz_style.panel_edge;
    tint.r = (unsigned char)((tint.r + g_design_organism.dominant_colors[0].r + g_design_organism.dominant_colors[1].r) / 3);
    tint.g = (unsigned char)((tint.g + g_design_organism.dominant_colors[0].g + g_design_organism.dominant_colors[1].g) / 3);
    tint.b = (unsigned char)((tint.b + g_design_organism.dominant_colors[0].b + g_design_organism.dominant_colors[1].b) / 3);
    tint.a = 255;
    return tint;
}

static COLORREF to_rgb(Color color) {
    return RGB(color.r, color.g, color.b);
}

static TRIVERTEX make_vertex(LONG x, LONG y, Color color) {
    TRIVERTEX vertex;
    vertex.x = x;
    vertex.y = y;
    vertex.Red = (COLOR16)(color.r << 8);
    vertex.Green = (COLOR16)(color.g << 8);
    vertex.Blue = (COLOR16)(color.b << 8);
    vertex.Alpha = (COLOR16)(color.a << 8);
    return vertex;
}

static Color mix_color(Color a, Color b, int amount, int scale) {
    Color mixed;
    mixed.r = (unsigned char)((a.r * (scale - amount) + b.r * amount) / scale);
    mixed.g = (unsigned char)((a.g * (scale - amount) + b.g * amount) / scale);
    mixed.b = (unsigned char)((a.b * (scale - amount) + b.b * amount) / scale);
    mixed.a = (unsigned char)((a.a * (scale - amount) + b.a * amount) / scale);
    return mixed;
}

static void fill_rect_color(HDC hdc, const RECT *rect, Color color) {
    HBRUSH brush = CreateSolidBrush(to_rgb(color));
    FillRect(hdc, rect, brush);
    DeleteObject(brush);
}

static void fill_gradient_rect(HDC hdc, const RECT *rect, Color start, Color end, int vertical) {
    TRIVERTEX vertices[2];
    GRADIENT_RECT gradient = {0, 1};
    ULONG mode = vertical ? GRADIENT_FILL_RECT_V : GRADIENT_FILL_RECT_H;
    vertices[0] = make_vertex(rect->left, rect->top, start);
    vertices[1] = make_vertex(rect->right, rect->bottom, end);
    GradientFill(hdc, vertices, 2, &gradient, 1, mode);
}

static void frame_rect_color(HDC hdc, const RECT *rect, Color color) {
    HBRUSH brush = CreateSolidBrush(to_rgb(color));
    FrameRect(hdc, rect, brush);
    DeleteObject(brush);
}

static void draw_panel(HDC hdc, const RECT *rect, Color top, Color bottom, Color edge, int radius) {
    HBRUSH brush = CreateSolidBrush(to_rgb(top));
    HPEN pen = CreatePen(PS_SOLID, 1, to_rgb(edge));
    HBRUSH old_brush = (HBRUSH)SelectObject(hdc, brush);
    HPEN old_pen = (HPEN)SelectObject(hdc, pen);
    RoundRect(hdc, rect->left, rect->top, rect->right, rect->bottom, radius, radius);
    SelectObject(hdc, old_pen);
    DeleteObject(pen);
    SelectObject(hdc, old_brush);
    DeleteObject(brush);
    {
        RECT inner = {rect->left + 1, rect->top + 1, rect->right - 1, rect->bottom - 1};
        fill_gradient_rect(hdc, &inner, top, bottom, 1);
    }
    {
        HPEN glow_pen = CreatePen(PS_SOLID, 1, to_rgb(mix_color(edge, blastmonidz_style.text, 1, 4)));
        HPEN previous_pen = (HPEN)SelectObject(hdc, glow_pen);
        HGDIOBJ previous_brush = SelectObject(hdc, GetStockObject(HOLLOW_BRUSH));
        RoundRect(hdc, rect->left, rect->top, rect->right, rect->bottom, radius, radius);
        SelectObject(hdc, previous_brush);
        SelectObject(hdc, previous_pen);
        DeleteObject(glow_pen);
    }
}

static void draw_pill(HDC hdc, const RECT *rect, Color fill, Color edge, const char *text, Color text_color) {
    draw_panel(hdc, rect, fill, mix_color(fill, blastmonidz_style.background, 1, 3), edge, 18);
    draw_text_block(hdc, rect->left + 12, rect->top + 6, rect->right - rect->left - 24, rect->bottom - rect->top - 8, text, 16, FW_SEMIBOLD, text_color);
}

static void draw_meter(HDC hdc, int x, int y, int w, int h, const char *label, int value, int max_value, Color fill, Color glow) {
    RECT rail = {x, y + 18, x + w, y + 18 + h};
    RECT amount = rail;
    int clamped = value;
    if (max_value <= 0) {
        max_value = 1;
    }
    if (clamped < 0) {
        clamped = 0;
    }
    if (clamped > max_value) {
        clamped = max_value;
    }
    amount.right = rail.left + ((rail.right - rail.left) * clamped) / max_value;
    draw_text_block(hdc, x, y, w, 18, label, 14, FW_SEMIBOLD, blastmonidz_style.text);
    draw_panel(hdc, &rail, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, blastmonidz_style.panel_edge, 10);
    if (amount.right > amount.left) {
        RECT inner = {amount.left + 2, amount.top + 2, amount.right - 2, amount.bottom - 2};
        if (inner.right > inner.left) {
            draw_panel(hdc, &inner, fill, glow, glow, 8);
        }
    }
}

static void draw_text_block(HDC hdc, int x, int y, int w, int h, const char *text, int size, int weight, Color color) {
    HFONT font = CreateFontA(size, 0, 0, 0, weight, 0, 0, 0, ANSI_CHARSET, OUT_DEFAULT_PRECIS,
        CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY, DEFAULT_PITCH | FF_DONTCARE, "Bahnschrift");
    RECT rect;
    HFONT old_font = (HFONT)SelectObject(hdc, font);
    SetBkMode(hdc, TRANSPARENT);
    SetTextColor(hdc, to_rgb(color));
    rect.left = x;
    rect.top = y;
    rect.right = x + w;
    rect.bottom = y + h;
    DrawTextA(hdc, text, -1, &rect, DT_WORDBREAK | DT_NOPREFIX);
    SelectObject(hdc, old_font);
    DeleteObject(font);
}

static void reset_archive_bitmap(ArchiveBitmap *bitmap) {
    if (bitmap->bitmap) {
        DeleteObject(bitmap->bitmap);
    }
    blastmonidz_pixel_array_reset(&bitmap->pixels);
    blastmonidz_asset_profile_reset(&bitmap->profile);
    ZeroMemory(bitmap, sizeof(*bitmap));
}

static int get_module_directory(char *buffer, size_t size) {
    DWORD length = GetModuleFileNameA(NULL, buffer, (DWORD)size);
    if (length == 0 || length >= size) {
        return 0;
    }
    while (length > 0 && buffer[length - 1] != '\\' && buffer[length - 1] != '/') {
        --length;
    }
    buffer[length] = '\0';
    return 1;
}

static int build_archive_asset_path(const char *entry, char *buffer, size_t size) {
    char module_dir[MAX_PATH];
    static const char archive_cache_dir[] = "bomberman_archive_cache\\";
    size_t module_len;
    size_t cache_len = sizeof(archive_cache_dir) - 1;
    size_t entry_len = strlen(entry);
    if (!get_module_directory(module_dir, sizeof(module_dir))) {
        return 0;
    }
    module_len = strlen(module_dir);
    if (module_len + cache_len + entry_len + 1 > size) {
        return 0;
    }
    memcpy(buffer, module_dir, module_len);
    memcpy(buffer + module_len, archive_cache_dir, cache_len);
    memcpy(buffer + module_len + cache_len, entry, entry_len + 1);
    return 1;
}

static int build_runtime_output_path(const char *file_name, char *buffer, size_t size) {
    char module_dir[MAX_PATH];
    size_t module_len;
    size_t file_len;
    if (!get_module_directory(module_dir, sizeof(module_dir))) {
        return 0;
    }
    module_len = strlen(module_dir);
    file_len = strlen(file_name);
    if (module_len + file_len + 1 > size) {
        return 0;
    }
    memcpy(buffer, module_dir, module_len);
    memcpy(buffer + module_len, file_name, file_len + 1);
    return 1;
}

static int load_archive_bitmap(const char *relative_entry, ArchiveBitmap *out_bitmap) {
    WCHAR wide_path[MAX_PATH];
    char path[MAX_PATH];
    IWICBitmapDecoder *decoder = NULL;
    IWICBitmapFrameDecode *frame = NULL;
    IWICFormatConverter *converter = NULL;
    HBITMAP bitmap = NULL;
    HDC screen_dc = NULL;
    BITMAPINFO bitmap_info;
    void *bits = NULL;
    UINT width = 0;
    UINT height = 0;
    UINT stride = 0;
    UINT image_size = 0;
    HRESULT hr;

    if (!g_wic_factory) {
        return 0;
    }
    if (!build_archive_asset_path(relative_entry, path, sizeof(path))) {
        return 0;
    }
    if (GetFileAttributesA(path) == INVALID_FILE_ATTRIBUTES) {
        return 0;
    }
    if (MultiByteToWideChar(CP_ACP, 0, path, -1, wide_path, MAX_PATH) == 0) {
        return 0;
    }

    hr = IWICImagingFactory_CreateDecoderFromFilename(
        g_wic_factory,
        wide_path,
        NULL,
        GENERIC_READ,
        WICDecodeMetadataCacheOnLoad,
        &decoder);
    if (FAILED(hr)) {
        goto cleanup;
    }
    hr = IWICBitmapDecoder_GetFrame(decoder, 0, &frame);
    if (FAILED(hr)) {
        goto cleanup;
    }
    hr = IWICImagingFactory_CreateFormatConverter(g_wic_factory, &converter);
    if (FAILED(hr)) {
        goto cleanup;
    }
    hr = IWICFormatConverter_Initialize(
        converter,
        (IWICBitmapSource *)frame,
        &GUID_WICPixelFormat32bppPBGRA,
        WICBitmapDitherTypeNone,
        NULL,
        0.0f,
        WICBitmapPaletteTypeCustom);
    if (FAILED(hr)) {
        goto cleanup;
    }
    hr = IWICBitmapSource_GetSize((IWICBitmapSource *)converter, &width, &height);
    if (FAILED(hr) || width == 0 || height == 0) {
        goto cleanup;
    }

    stride = width * 4;
    image_size = stride * height;
    ZeroMemory(&bitmap_info, sizeof(bitmap_info));
    bitmap_info.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    bitmap_info.bmiHeader.biWidth = (LONG)width;
    bitmap_info.bmiHeader.biHeight = -((LONG)height);
    bitmap_info.bmiHeader.biPlanes = 1;
    bitmap_info.bmiHeader.biBitCount = 32;
    bitmap_info.bmiHeader.biCompression = BI_RGB;

    screen_dc = GetDC(NULL);
    bitmap = CreateDIBSection(screen_dc, &bitmap_info, DIB_RGB_COLORS, &bits, NULL, 0);
    ReleaseDC(NULL, screen_dc);
    if (!bitmap || !bits) {
        goto cleanup;
    }

    hr = IWICBitmapSource_CopyPixels((IWICBitmapSource *)converter, NULL, stride, image_size, (BYTE *)bits);
    if (FAILED(hr)) {
        DeleteObject(bitmap);
        bitmap = NULL;
        goto cleanup;
    }

    reset_archive_bitmap(out_bitmap);
    out_bitmap->bitmap = bitmap;
    out_bitmap->width = (int)width;
    out_bitmap->height = (int)height;
    out_bitmap->loaded = 1;
    snprintf(out_bitmap->source_path, sizeof(out_bitmap->source_path), "%s", path);
    out_bitmap->pixels.width = (int)width;
    out_bitmap->pixels.height = (int)height;
    out_bitmap->pixels.stride = (int)stride;
    out_bitmap->pixels.rgba = (unsigned char *)malloc((size_t)image_size);
    if (out_bitmap->pixels.rgba) {
        memcpy(out_bitmap->pixels.rgba, bits, (size_t)image_size);
        out_bitmap->analyzed = blastmonidz_analyze_pixel_array(&out_bitmap->pixels, &out_bitmap->profile);
        if (out_bitmap->analyzed) {
            blastmonidz_design_organism_absorb(&g_design_organism, &out_bitmap->profile);
        }
    }

cleanup:
    if (converter) {
        IWICFormatConverter_Release(converter);
    }
    if (frame) {
        IWICBitmapFrameDecode_Release(frame);
    }
    if (decoder) {
        IWICBitmapDecoder_Release(decoder);
    }
    return out_bitmap->loaded;
}

static void load_title_archive_images(void) {
    load_archive_bitmap(blastmonidz_title_backdrop_asset()->archive_entry, &g_title_backdrop);
    load_archive_bitmap(blastmonidz_title_logo_asset()->archive_entry, &g_title_logo);
}

static void load_hero_sprite_family(int family, int direction, const char *direction_name) {
    static const int family_prefixes[BLASTMONIDZ_HERO_FAMILIES] = {0, 2, 3, 4};
    int frame;
    char path[128];
    for (frame = 0; frame < BLASTMONIDZ_PLAYER_FRAMES; ++frame) {
        if (family_prefixes[family] == 0) {
            snprintf(path, sizeof(path), "graphics/characters/bMan %s%04d.png", direction_name, frame + 1);
        } else {
            snprintf(path, sizeof(path), "graphics/characters/bMan %s%d%04d.png", direction_name, family_prefixes[family], frame + 1);
        }
        load_archive_bitmap(path, &g_player_sprites[family][direction][frame]);
    }
}

static void load_rival_sprite_family(void) {
    int frame;
    int family;
    char path[128];
    for (frame = 0; frame < BLASTMONIDZ_PLAYER_FRAMES; ++frame) {
        snprintf(path, sizeof(path), "graphics/characters/bMan baddieWalkback%04d.png", frame + 1);
        load_archive_bitmap(path, &g_rival_back_sprites[frame]);
    }
    for (family = 0; family < BLASTMONIDZ_RIVAL_FAMILIES; ++family) {
        for (frame = 0; frame < BLASTMONIDZ_PLAYER_FRAMES; ++frame) {
            if (family == 0) {
                snprintf(path, sizeof(path), "graphics/characters/bMan baddieWalkSide%04d.png", frame + 1);
            } else {
                snprintf(path, sizeof(path), "graphics/characters/bMan baddieWalkSide2%04d.png", frame + 1);
            }
            load_archive_bitmap(path, &g_rival_side_sprites[family][frame]);
        }
    }
}

static void load_runtime_archive_images(void) {
    static const char *const paint_assets[BLASTMONIDZ_PAINT_VARIANTS] = {
        "graphics/bomb, crate, tile, paint/redPaint.png",
        "graphics/bomb, crate, tile, paint/greenPaint.png",
        "graphics/bomb, crate, tile, paint/bluePaint.png",
        "graphics/bomb, crate, tile, paint/goldPaint.png",
        "graphics/bomb, crate, tile, paint/purplePaint.png"
    };
    static const char *const crate_assets[BLASTMONIDZ_CRATE_VARIANTS] = {
        "graphics/bomb, crate, tile, paint/crate.png",
        "graphics/bomb, crate, tile, paint/bMan door.png",
        "graphics/bomb, crate, tile, paint/bMan gunPowder.png"
    };
    int family;
    int chemistry_index;
    int frame;

    load_archive_bitmap("graphics/bomb, crate, tile, paint/bMan tile.png", &g_floor_tile);
    load_archive_bitmap("graphics/bomb, crate, tile, paint/bMan bombPouch.png", &g_bomb_pouch);
    for (chemistry_index = 0; chemistry_index < BLASTMONIDZ_CRATE_VARIANTS; ++chemistry_index) {
        load_archive_bitmap(crate_assets[chemistry_index], &g_crate_variants[chemistry_index]);
    }
    for (frame = 0; frame < BLASTMONIDZ_PLAYER_FRAMES; ++frame) {
        char path[128];
        snprintf(path, sizeof(path), "graphics/bomb, crate, tile, paint/bMan bomb%04d.png", frame + 1);
        load_archive_bitmap(path, &g_bomb_frames[frame]);
    }
    for (chemistry_index = 0; chemistry_index < BLASTMONIDZ_PAINT_VARIANTS; ++chemistry_index) {
        load_archive_bitmap(paint_assets[chemistry_index], &g_gem_paints[chemistry_index]);
    }
    for (family = 0; family < BLASTMONIDZ_HERO_FAMILIES; ++family) {
        load_hero_sprite_family(family, 0, "forWalk");
        load_hero_sprite_family(family, 1, "backWalk");
        load_hero_sprite_family(family, 2, "sideWalk");
    }
    load_rival_sprite_family();
}

static void write_bitmap_profile(FILE *stream, const char *label, const ArchiveBitmap *bitmap) {
    char line[320];
    if (!stream || !label || !bitmap || !bitmap->loaded || !bitmap->analyzed) {
        return;
    }
    blastmonidz_describe_asset_profile(&bitmap->profile, line, (int)sizeof(line));
    fprintf(stream, "%s\n  path=%s\n  %s\n", label, bitmap->source_path, line);
}

static void write_design_profile_report(void) {
    char output_path[MAX_PATH];
    FILE *report;
    char organism_line[320];
    int family;
    int direction;
    int frame;
    int chemistry_index;
    if (!build_runtime_output_path(blastmonidz_design_profile_path, output_path, sizeof(output_path))) {
        return;
    }
    report = fopen(output_path, "w");
    if (!report) {
        return;
    }
    blastmonidz_design_organism_finalize(&g_design_organism);
    blastmonidz_describe_design_organism(&g_design_organism, organism_line, (int)sizeof(organism_line));

    fprintf(report, "BLASTMONIDZ DESIGN ORGANISM REPORT\n\n");
    fprintf(report, "Aggregate profile\n%s\n\n", organism_line);
    fprintf(report, "Theory synthesis\n%s\n\n", g_design_organism.theory_summary);
    if (g_state) {
        char genome_line[256];
        int player_index;
        blastmonidz_describe_genome_profile(&g_state->visuals.asset_genome, genome_line, (int)sizeof(genome_line));
        fprintf(report, "Runtime asset genome\n%s\n\n", genome_line);
        fprintf(report, "Active character genomes\n");
        for (player_index = 0; player_index < MAX_PLAYERS; ++player_index) {
            blastmonidz_describe_genome_profile(&g_state->players[player_index].mon.cosmetic_genome, genome_line, (int)sizeof(genome_line));
            fprintf(report, "- %s: %s\n", g_state->players[player_index].name, genome_line);
        }
        fprintf(report, "\n");
    }
    fprintf(report, "Applied reading\n");
    fprintf(report, "- Art theory: silhouette control outranks interior texture, so identity is carried by contour rhythm and color hierarchy.\n");
    fprintf(report, "- Design theory: the asset base behaves like a modular kit where repeated primitives are varied through timing, hue reassignment, and local ornament.\n");
    fprintf(report, "- Architecture: massing is bottom-weighted and foundation-biased, which makes forms read as stable and load-bearing rather than floating.\n");
    fprintf(report, "- Civil and construction logic: crate, tile, bomb, and body forms all privilege prefabrication, repeatability, and reliable joint logic over bespoke one-off detailing.\n");
    fprintf(report, "- Evolution pipeline: animation elasticity, environmental mutation bias, structural discipline, and ornamental bias can be treated as phenotype controls for runtime adaptation.\n\n");
    fprintf(report, "Ten home tiles\n");
    for (chemistry_index = 0; chemistry_index < BLASTMONIDZ_HOME_TILES; ++chemistry_index) {
        fprintf(report, "- %c %s: %s | structure %.2f | ornament %.2f | growth %.2f | shelter %.2f\n",
            blastmonidz_home_tiles[chemistry_index].glyph,
            blastmonidz_home_tiles[chemistry_index].name,
            blastmonidz_home_tiles[chemistry_index].theory_role,
            blastmonidz_home_tiles[chemistry_index].structural_bias,
            blastmonidz_home_tiles[chemistry_index].ornamental_bias,
            blastmonidz_home_tiles[chemistry_index].growth_bias,
            blastmonidz_home_tiles[chemistry_index].shelter_bias);
    }
    fprintf(report, "\n");

    write_bitmap_profile(report, "title.logo", &g_title_logo);
    write_bitmap_profile(report, "title.backdrop", &g_title_backdrop);
    write_bitmap_profile(report, "arena.floor", &g_floor_tile);
    write_bitmap_profile(report, "arena.bombPouch", &g_bomb_pouch);
    for (chemistry_index = 0; chemistry_index < BLASTMONIDZ_CRATE_VARIANTS; ++chemistry_index) {
        char label[64];
        snprintf(label, sizeof(label), "arena.crate[%d]", chemistry_index);
        write_bitmap_profile(report, label, &g_crate_variants[chemistry_index]);
    }
    for (chemistry_index = 0; chemistry_index < BLASTMONIDZ_PAINT_VARIANTS; ++chemistry_index) {
        char label[64];
        snprintf(label, sizeof(label), "paint[%d]", chemistry_index);
        write_bitmap_profile(report, label, &g_gem_paints[chemistry_index]);
    }
    for (frame = 0; frame < BLASTMONIDZ_PLAYER_FRAMES; frame += 3) {
        char label[64];
        snprintf(label, sizeof(label), "bomb.frame[%d]", frame);
        write_bitmap_profile(report, label, &g_bomb_frames[frame]);
    }
    for (family = 0; family < BLASTMONIDZ_HERO_FAMILIES; ++family) {
        for (direction = 0; direction < BLASTMONIDZ_PLAYER_DIRECTIONS; ++direction) {
            char label[64];
            snprintf(label, sizeof(label), "hero[%d][%d][0]", family, direction);
            write_bitmap_profile(report, label, &g_player_sprites[family][direction][0]);
        }
    }
    for (family = 0; family < BLASTMONIDZ_RIVAL_FAMILIES; ++family) {
        char label[64];
        snprintf(label, sizeof(label), "rival.side[%d][0]", family);
        write_bitmap_profile(report, label, &g_rival_side_sprites[family][0]);
    }
    write_bitmap_profile(report, "rival.back[0]", &g_rival_back_sprites[0]);
    fclose(report);
}

static void draw_archive_bitmap(HDC hdc, const RECT *dest, const ArchiveBitmap *bitmap, int alpha) {
    HDC memory_dc;
    HGDIOBJ old_bitmap;
    BLENDFUNCTION blend;
    if (!bitmap->loaded || !bitmap->bitmap) {
        return;
    }
    memory_dc = CreateCompatibleDC(hdc);
    old_bitmap = SelectObject(memory_dc, bitmap->bitmap);
    blend.BlendOp = AC_SRC_OVER;
    blend.BlendFlags = 0;
    blend.SourceConstantAlpha = (BYTE)alpha;
    blend.AlphaFormat = AC_SRC_ALPHA;
    AlphaBlend(
        hdc,
        dest->left,
        dest->top,
        dest->right - dest->left,
        dest->bottom - dest->top,
        memory_dc,
        0,
        0,
        bitmap->width,
        bitmap->height,
        blend);
    SelectObject(memory_dc, old_bitmap);
    DeleteDC(memory_dc);
}

static const char *player_direction_name(int direction) {
    switch (direction) {
        case 1: return "back";
        case 2: return "side";
        default: return "front";
    }
}

static const ArchiveBitmap *get_floor_overlay_bitmap(const GameState *state, int world_x, int world_y) {
    int overlay = blastmonidz_select_floor_overlay(state, world_x, world_y);
    if (overlay < 0 || overlay >= BLASTMONIDZ_PAINT_VARIANTS) {
        return NULL;
    }
    return g_gem_paints[overlay].loaded ? &g_gem_paints[overlay] : NULL;
}

static const ArchiveBitmap *get_crate_bitmap(const GameState *state, int world_x, int world_y) {
    int variant = blastmonidz_select_crate_variant(state, world_x, world_y);
    if (variant < 0 || variant >= BLASTMONIDZ_CRATE_VARIANTS) {
        variant = 0;
    }
    return g_crate_variants[variant].loaded ? &g_crate_variants[variant] : &g_crate_variants[0];
}

static const ArchiveBitmap *get_bomb_bitmap(const GameState *state, const Bomb *bomb, int bomb_id) {
    int frame = blastmonidz_select_bomb_frame(state, bomb, bomb_id) + organism_frame_offset(state);
    if (frame < 0 || frame >= BLASTMONIDZ_PLAYER_FRAMES) {
        frame %= BLASTMONIDZ_PLAYER_FRAMES;
        if (frame < 0) {
            frame += BLASTMONIDZ_PLAYER_FRAMES;
        }
    }
    return g_bomb_frames[frame].loaded ? &g_bomb_frames[frame] : NULL;
}

static const ArchiveBitmap *get_gem_bitmap(const GameState *state, const BombGem *gem) {
    int paint = blastmonidz_select_gem_paint(state, gem);
    if (paint < 0 || paint >= BLASTMONIDZ_PAINT_VARIANTS) {
        paint = 0;
    }
    return g_gem_paints[paint].loaded ? &g_gem_paints[paint] : NULL;
}

static const ArchiveBitmap *get_player_sprite_bitmap(const GameState *state, int player_id, int *use_rival, int *family, int *direction, int *frame) {
    int selected_rival = 0;
    int selected_family = 0;
    int selected_direction = 0;
    int selected_frame = 0;
    blastmonidz_select_player_visual(state, player_id, &selected_rival, &selected_family, &selected_direction, &selected_frame);
    if (use_rival) {
        *use_rival = selected_rival;
    }
    if (family) {
        *family = selected_family;
    }
    if (direction) {
        *direction = selected_direction;
    }
    if (frame) {
        *frame = selected_frame;
    }
    selected_frame = (selected_frame + organism_frame_offset(state)) % BLASTMONIDZ_PLAYER_FRAMES;
    if (selected_rival) {
        if (selected_direction == 1 && g_rival_back_sprites[selected_frame].loaded) {
            return &g_rival_back_sprites[selected_frame];
        }
        if (selected_family < 0 || selected_family >= BLASTMONIDZ_RIVAL_FAMILIES) {
            selected_family = 0;
        }
        if (g_rival_side_sprites[selected_family][selected_frame].loaded) {
            return &g_rival_side_sprites[selected_family][selected_frame];
        }
    }
    if (selected_family < 0 || selected_family >= BLASTMONIDZ_HERO_FAMILIES) {
        selected_family = 0;
    }
    if (selected_direction < 0 || selected_direction >= BLASTMONIDZ_PLAYER_DIRECTIONS) {
        selected_direction = 0;
    }
    return &g_player_sprites[selected_family][selected_direction][selected_frame];
}

static void draw_home_tile_pattern(HDC hdc, const RECT *tile, const BlastmonidzHomeTile *home_tile, Color base_color) {
    HPEN pen;
    HPEN old_pen;
    int mid_x;
    int mid_y;
    if (!tile || !home_tile) {
        return;
    }
    mid_x = (tile->left + tile->right) / 2;
    mid_y = (tile->top + tile->bottom) / 2;
    pen = CreatePen(PS_SOLID, 1, to_rgb(base_color));
    old_pen = (HPEN)SelectObject(hdc, pen);
    switch (home_tile->glyph) {
        case 'a':
            MoveToEx(hdc, tile->left + 2, tile->bottom - 3, NULL);
            LineTo(hdc, tile->right - 2, tile->bottom - 3);
            break;
        case 'c':
            MoveToEx(hdc, tile->left + 2, mid_y, NULL);
            LineTo(hdc, tile->right - 2, mid_y);
            MoveToEx(hdc, mid_x, tile->top + 2, NULL);
            LineTo(hdc, mid_x, tile->bottom - 2);
            break;
        case 's':
            Arc(hdc, tile->left + 1, tile->top + 1, tile->right - 1, tile->bottom - 1, tile->left + 1, mid_y, tile->right - 1, mid_y);
            break;
        case 'b':
            Arc(hdc, tile->left + 2, tile->top + 2, tile->right - 2, tile->bottom - 2, tile->left + 2, tile->bottom - 2, tile->right - 2, tile->bottom - 2);
            break;
        case 'g':
            MoveToEx(hdc, tile->left + 3, tile->top + 3, NULL);
            LineTo(hdc, tile->right - 3, tile->bottom - 3);
            break;
        case 'k':
            MoveToEx(hdc, tile->left + 2, tile->top + 3, NULL);
            LineTo(hdc, tile->right - 2, tile->bottom - 3);
            MoveToEx(hdc, tile->right - 2, tile->top + 3, NULL);
            LineTo(hdc, tile->left + 2, tile->bottom - 3);
            break;
        case 'r':
            MoveToEx(hdc, mid_x, tile->top + 2, NULL);
            LineTo(hdc, mid_x, tile->bottom - 2);
            MoveToEx(hdc, mid_x, tile->bottom - 4, NULL);
            LineTo(hdc, tile->left + 3, tile->bottom - 2);
            MoveToEx(hdc, mid_x, tile->bottom - 4, NULL);
            LineTo(hdc, tile->right - 3, tile->bottom - 2);
            break;
        case 'p':
            Rectangle(hdc, tile->left + 3, tile->top + 3, tile->right - 3, tile->bottom - 3);
            break;
        case 'v':
            MoveToEx(hdc, tile->left + 2, tile->bottom - 3, NULL);
            LineTo(hdc, mid_x, tile->top + 2);
            LineTo(hdc, tile->right - 2, tile->bottom - 3);
            break;
        case 'm':
            MoveToEx(hdc, tile->left + 2, tile->bottom - 4, NULL);
            LineTo(hdc, tile->right - 2, tile->bottom - 4);
            MoveToEx(hdc, tile->left + 4, mid_y, NULL);
            LineTo(hdc, tile->right - 4, mid_y);
            break;
        default:
            break;
    }
    SelectObject(hdc, old_pen);
    DeleteObject(pen);
}

static void draw_centered_tile_label(HDC hdc, const RECT *tile, const char *text, int size, Color color) {
    draw_text_block(hdc,
        tile->left,
        tile->top + ((tile->bottom - tile->top) - size - 2) / 2,
        tile->right - tile->left,
        size + 8,
        text,
        size,
        FW_BOLD,
        color);
}

static const ArchiveBitmap *get_archive_preview_bitmap(int index) {
    switch (index) {
        case 0: return &g_title_logo;
        case 1: return &g_title_backdrop;
        case 2: return &g_player_sprites[0][0][0];
        case 3: return &g_player_sprites[0][1][0];
        case 4: return &g_player_sprites[1][2][0];
        case 5: return &g_bomb_frames[3];
        case 6: return &g_bomb_frames[9];
        case 7: return &g_title_backdrop;
        case 8: return &g_floor_tile;
        case 9: return &g_player_sprites[2][0][6];
        case 10: return &g_player_sprites[3][1][10];
        case 11: return &g_rival_side_sprites[0][4];
        case 12: return &g_rival_back_sprites[7];
        case 13: return &g_player_sprites[1][0][11];
        case 14: return &g_player_sprites[2][1][13];
        case 15: return &g_player_sprites[3][2][15];
        default: return NULL;
    }
}

static void draw_title_preview_card(HDC hdc, const RECT *rect, const ArchiveBitmap *bitmap, const char *label, Color edge, int alpha) {
    RECT preview = inset_rect(*rect, 10, 10);
    draw_panel(hdc, rect, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, edge, 18);
    preview.bottom -= 30;
    if (bitmap && bitmap->loaded) {
        draw_archive_bitmap(hdc, &preview, bitmap, alpha);
    } else {
        fill_rect_color(hdc, &preview, mix_color(edge, blastmonidz_style.background, 1, 3));
    }
    frame_rect_color(hdc, &preview, edge);
    draw_text_block(hdc, rect->left + 12, rect->bottom - 28, rect->right - rect->left - 24, 22, label, 13, FW_BOLD, blastmonidz_style.text);
}

static void draw_title_district_grid(HDC hdc, const RECT *rect, const TitleVisualState *visual) {
    int row;
    int column;
    int index = 0;
    int cell_w;
    int cell_h;
    draw_panel(hdc, rect, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, visual->secondary_tint, 22);
    draw_text_block(hdc, rect->left + 16, rect->top + 12, rect->right - rect->left - 32, 22, "HOME-TILE DISTRICT ARRAY", 16, FW_BOLD, visual->primary_tint);
    cell_w = (rect->right - rect->left - 42) / 5;
    cell_h = (rect->bottom - rect->top - 56) / 2;
    for (row = 0; row < 2; ++row) {
        for (column = 0; column < 5; ++column) {
            RECT cell = {
                rect->left + 16 + column * cell_w,
                rect->top + 38 + row * cell_h,
                rect->left + 16 + (column + 1) * cell_w - 8,
                rect->top + 38 + (row + 1) * cell_h - 8
            };
            const BlastmonidzHomeTile *home_tile = &blastmonidz_home_tiles[(visual->district_offset + index) % BLASTMONIDZ_HOME_TILES];
            Color edge = mix_color(visual->secondary_tint, shift_color(visual->primary_tint, 8 * column, -4 * row, 6 * index), 1, 2);
            draw_panel(hdc, &cell, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, edge, 12);
            draw_home_tile_pattern(hdc, &cell, home_tile, edge);
            {
                char glyph[2] = {home_tile->glyph, '\0'};
                draw_centered_tile_label(hdc, &cell, glyph, 20, blastmonidz_style.text);
            }
            draw_text_block(hdc, cell.left + 8, cell.bottom - 22, cell.right - cell.left - 16, 18, home_tile->name, 11, FW_BOLD, blastmonidz_style.text);
            ++index;
        }
    }
}

static void draw_title_signal_stack(HDC hdc, const RECT *rect, const TitleVisualState *visual) {
    RECT meter_shell = inset_rect(*rect, 14, 14);
    draw_panel(hdc, rect, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, visual->primary_tint, 22);
    draw_text_block(hdc, rect->left + 16, rect->top + 12, rect->right - rect->left - 32, 20, "COSMETIC ADAPTATION BUS", 16, FW_BOLD, visual->primary_tint);
    draw_meter(hdc, meter_shell.left, meter_shell.top + 18, meter_shell.right - meter_shell.left, 18, "Structure", visual->meter_values[0], 100, visual->primary_tint, shift_color(visual->primary_tint, 30, 20, 12));
    draw_meter(hdc, meter_shell.left, meter_shell.top + 52, meter_shell.right - meter_shell.left, 18, "Ornament", visual->meter_values[1], 100, visual->secondary_tint, shift_color(visual->secondary_tint, 18, 22, 34));
    draw_meter(hdc, meter_shell.left, meter_shell.top + 86, meter_shell.right - meter_shell.left, 18, "Elasticity", visual->meter_values[2], 100, visual->tertiary_tint, shift_color(visual->tertiary_tint, 22, 28, 40));
    draw_meter(hdc, meter_shell.left, meter_shell.top + 120, meter_shell.right - meter_shell.left, 18, "Mutation", visual->meter_values[3], 100, blastmonidz_style.accent, shift_color(blastmonidz_style.accent, 16, 24, 8));
    draw_text_block(hdc, meter_shell.left, meter_shell.top + 154, meter_shell.right - meter_shell.left, 36, kTitleArrangementModes[visual->arrangement_index], 18, FW_BOLD, blastmonidz_style.text);
    draw_text_block(hdc, meter_shell.left, meter_shell.top + 180, meter_shell.right - meter_shell.left, 52, blastmonidz_bridge_latest_status(), 14, FW_NORMAL, visual->tertiary_tint);
}

static void draw_title_hero_stage(HDC hdc, const RECT *rect, const TitleVisualState *visual) {
    int family;
    draw_panel(hdc, rect, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 3), visual->primary_tint, 28);
    if (g_bomb_frames[(visual->pulse + visual->frame_stride) % BLASTMONIDZ_PLAYER_FRAMES].loaded) {
        RECT bomb_overlay = inset_rect(*rect, 12, 12);
        draw_archive_bitmap(hdc, &bomb_overlay, &g_bomb_frames[(visual->pulse + visual->frame_stride) % BLASTMONIDZ_PLAYER_FRAMES], organism_overlay_alpha(76));
    }
    if (g_gem_paints[visual->chemistry_mode].loaded) {
        RECT paint_overlay = inset_rect(*rect, 18, 18);
        draw_archive_bitmap(hdc, &paint_overlay, &g_gem_paints[visual->chemistry_mode], organism_overlay_alpha(94));
    }
    for (family = 0; family < BLASTMONIDZ_HERO_FAMILIES; ++family) {
        RECT slot = *rect;
        int direction = (visual->direction_offset + family) % BLASTMONIDZ_PLAYER_DIRECTIONS;
        int frame = (visual->pulse + family * visual->frame_stride) % BLASTMONIDZ_PLAYER_FRAMES;
        const ArchiveBitmap *bitmap = &g_player_sprites[family][direction][frame];
        int third_w = (rect->right - rect->left) / 3;
        int half_h = (rect->bottom - rect->top) / 2;
        switch (visual->arrangement_index) {
            case 0:
                slot.left = rect->left + (family % 2) * (third_w + 36) + 20;
                slot.right = slot.left + third_w;
                slot.top = rect->top + (family / 2) * (half_h - 8) + 16;
                slot.bottom = slot.top + half_h - 22;
                break;
            case 1:
                slot.left = rect->left + 18 + family * ((rect->right - rect->left - third_w - 36) / 3);
                slot.right = slot.left + third_w;
                slot.top = rect->top + 12 + ((family * 27) % 54);
                slot.bottom = rect->bottom - 20 - ((3 - family) * 6);
                break;
            case 2:
                if (family == 0) {
                    slot.left = rect->left + third_w - 12;
                    slot.right = rect->right - third_w + 12;
                    slot.top = rect->top + 10;
                    slot.bottom = rect->bottom - 18;
                } else {
                    slot.left = rect->left + 20 + (family - 1) * (third_w - 12);
                    slot.right = slot.left + third_w - 18;
                    slot.top = rect->top + half_h - 18 + ((family & 1) ? -22 : 10);
                    slot.bottom = rect->bottom - 22;
                }
                break;
            case 3:
                slot.left = rect->left + 24 + (family % 2) * (third_w + 42);
                slot.right = slot.left + third_w + ((family / 2) ? 26 : -6);
                slot.top = rect->top + 16 + (family / 2) * (half_h - 2);
                slot.bottom = slot.top + half_h - 26;
                break;
            default:
                slot.left = rect->left + 24 + family * ((rect->right - rect->left - third_w - 48) / 4);
                slot.right = slot.left + third_w - 10;
                slot.top = rect->top + 26 + abs(2 - family) * 12;
                slot.bottom = rect->bottom - 24 - abs(1 - family) * 6;
                break;
        }
        draw_panel(hdc, &slot, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 3), blastmonidz_style.panel, shift_color(visual->secondary_tint, family * 12, family * 4, 10), 18);
        if (bitmap->loaded) {
            RECT preview = inset_rect(slot, 8, 8);
            draw_archive_bitmap(hdc, &preview, bitmap, 255);
        }
    }
}

static void draw_title_scene(HDC hdc, RECT client) {
    RECT full = {0, 0, client.right, client.bottom};
    RECT top_band = {0, 0, client.right, client.bottom / 3};
    RECT lower_stage = {0, client.bottom / 3, client.right, client.bottom};
    RECT logo_rect = {client.right / 2 - 250, 42, client.right / 2 + 250, client.bottom / 3 + 36};
    RECT marquee_rect = {84, client.bottom / 3 + 30, client.right - 84, client.bottom / 3 + 124};
    RECT rhyme_rect = {84, client.bottom / 3 + 124, client.right - 84, client.bottom / 2 + 52};
    RECT district_panel = {72, client.bottom / 2 + 56, client.right / 3 - 12, client.bottom - 126};
    RECT hero_stage = {client.right / 3 + 4, client.bottom / 2 + 12, client.right - 328, client.bottom - 126};
    RECT signal_panel = {client.right - 312, client.bottom / 2 + 56, client.right - 72, client.bottom - 126};
    RECT command_bar = {72, client.bottom - 102, client.right - 72, client.bottom - 42};
    RECT preview_cards[3];
    const AssetArchetype *logo_asset = blastmonidz_title_logo_asset();
    const AssetArchetype *backdrop_asset = blastmonidz_title_backdrop_asset();
    const AssetArchetype *motion_asset = blastmonidz_primary_motion_asset();
    DWORD now = GetTickCount();
    TitleVisualState visual;
    char status[512];
    char feature_text[512];
    char arrangement_text[256];
    int card_index;
    const char *backdrop_status = g_title_backdrop.loaded ? blastmonidz_title_backdrop_asset()->archive_entry : "not loaded";
    const char *logo_status = g_title_logo.loaded ? blastmonidz_title_logo_asset()->archive_entry : "not loaded";
    const char *arena_status = g_floor_tile.loaded ? "procedural pool online" : "not loaded";

    build_title_visual_state(now, &visual);

    preview_cards[0].left = client.right - 300;
    preview_cards[0].right = client.right - 170;
    preview_cards[0].top = client.bottom / 3 + 24;
    preview_cards[0].bottom = client.bottom / 3 + 166;
    preview_cards[1].left = client.right - 166;
    preview_cards[1].right = client.right - 40;
    preview_cards[1].top = client.bottom / 3 + 58 + ((visual.seed >> 3) & 15u);
    preview_cards[1].bottom = preview_cards[1].top + 132;
    preview_cards[2].left = client.right - 260;
    preview_cards[2].right = client.right - 92;
    preview_cards[2].top = client.bottom / 3 + 176;
    preview_cards[2].bottom = preview_cards[2].top + 122;

    fill_gradient_rect(hdc, &full, mix_color(blastmonidz_style.background, visual.secondary_tint, 1, 2), shift_color(blastmonidz_style.background, -4, -2, 10), 1);
    if (g_title_backdrop.loaded) {
        draw_archive_bitmap(hdc, &full, &g_title_backdrop, 210);
    }
    fill_gradient_rect(hdc, &top_band, mix_color(blastmonidz_style.panel, visual.primary_tint, 1, 5), blastmonidz_style.panel, 1);
    fill_gradient_rect(hdc, &lower_stage, blastmonidz_style.background, mix_color(blastmonidz_style.panel, visual.tertiary_tint, 1, 4), 1);
    draw_archive_bitmap(hdc, &top_band, &g_title_backdrop, 116);
    draw_archive_bitmap(hdc, &lower_stage, &g_title_backdrop, 54);
    {
        RECT left_paint = {0, 0, 88, client.bottom};
        RECT right_paint = {client.right - 88, 0, client.right, client.bottom};
        RECT horizon = {72, client.bottom / 3 + 18, client.right - 72, client.bottom / 3 + 28};
        fill_gradient_rect(hdc, &left_paint, mix_color(visual.primary_tint, blastmonidz_style.background, 1, 3), blastmonidz_style.background, 0);
        fill_gradient_rect(hdc, &right_paint, blastmonidz_style.background, mix_color(visual.secondary_tint, blastmonidz_style.background, 1, 3), 0);
        fill_gradient_rect(hdc, &horizon, visual.primary_tint, visual.secondary_tint, 0);
        if (g_gem_paints[(visual.pulse / 4) % BLASTMONIDZ_PAINT_VARIANTS].loaded) {
            draw_archive_bitmap(hdc, &left_paint, &g_gem_paints[(visual.pulse / 4) % BLASTMONIDZ_PAINT_VARIANTS], organism_overlay_alpha(120));
            draw_archive_bitmap(hdc, &right_paint, &g_gem_paints[(visual.pulse / 3) % BLASTMONIDZ_PAINT_VARIANTS], organism_overlay_alpha(120));
        }
    }
    if (g_title_logo.loaded) {
        draw_archive_bitmap(hdc, &logo_rect, &g_title_logo, 255);
        draw_panel(hdc, &logo_rect, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 3), blastmonidz_style.panel, visual.primary_tint, 26);
        draw_archive_bitmap(hdc, &logo_rect, &g_title_logo, 255);
    }

    draw_text_block(hdc, 88, 52, client.right - 176, 64, "BLASTMONIDZ", 64, FW_BOLD, visual.primary_tint);
    draw_text_block(hdc, 92, 122, client.right - 184, 32, "CONSENSUS ARENA // FULL-SCREEN ARCHIVE STRIKE", 24, FW_SEMIBOLD, blastmonidz_style.text);
    snprintf(arrangement_text, sizeof(arrangement_text),
        "Adaptive title mode: %s // paint %d // bridge-seeded rearrangement online",
        kTitleArrangementModes[visual.arrangement_index],
        visual.chemistry_mode + 1);
    draw_text_block(hdc, 96, 164, client.right - 420, 54, arrangement_text, 18, FW_NORMAL, blastmonidz_style.text);

    {
        RECT badge_left = {92, 20, 272, 56};
        RECT badge_right = {client.right - 292, 20, client.right - 92, 56};
        draw_pill(hdc, &badge_left, mix_color(visual.primary_tint, blastmonidz_style.background, 1, 3), visual.primary_tint, "INDIE SHOWCASE BUILD", blastmonidz_style.text);
        draw_pill(hdc, &badge_right, mix_color(visual.secondary_tint, blastmonidz_style.background, 1, 2), visual.secondary_tint, "CHAT BRIDGE ONLINE", blastmonidz_style.text);
    }

    draw_panel(hdc, &marquee_rect, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, visual.secondary_tint, 22);
    draw_text_block(hdc, marquee_rect.left + 16, marquee_rect.top + 12, marquee_rect.right - marquee_rect.left - 32, 26, kTitleFeatureBursts[visual.burst_index], 24, FW_BOLD, visual.primary_tint);
    draw_text_block(hdc, marquee_rect.left + 16, marquee_rect.top + 44, marquee_rect.right - marquee_rect.left - 332, 48,
        "Bomberman.zip is no longer a museum piece. The title recomposes itself from bridge traffic, design analysis, home-tile districts, bomb reels, and motion-family staging.",
        18, FW_NORMAL, blastmonidz_style.text);
    for (card_index = 0; card_index < 3; ++card_index) {
        const ArchiveBitmap *preview_bitmap = get_archive_preview_bitmap(title_preview_index(visual.preview_offset, card_index * 3));
        char label[64];
        snprintf(label, sizeof(label), "PREVIEW %02d", title_preview_index(visual.preview_offset, card_index * 3) + 1);
        draw_title_preview_card(hdc, &preview_cards[card_index], preview_bitmap, label, shift_color(visual.secondary_tint, card_index * 10, 6, 12), 232 - card_index * 18);
    }

    draw_text_block(hdc, rhyme_rect.left, rhyme_rect.top, rhyme_rect.right - rhyme_rect.left, rhyme_rect.bottom - rhyme_rect.top,
        kTitleRhymes[visual.rhyme_index],
        28, FW_BOLD, blastmonidz_style.text);
    draw_title_district_grid(hdc, &district_panel, &visual);
    draw_title_hero_stage(hdc, &hero_stage, &visual);
    draw_title_signal_stack(hdc, &signal_panel, &visual);

    snprintf(feature_text, sizeof(feature_text),
        "Title Plate: %s\nBackdrop: %s\nPrimary Motion: %s\nDistrict seed: %u",
        logo_asset->archive_entry,
        backdrop_asset->archive_entry,
        motion_asset->archive_entry,
        visual.seed);

    snprintf(status, sizeof(status),
        "Archive render status: backdrop %s // logo %s // arena %s // pulse frame %02d // arrangement %s",
        backdrop_status,
        logo_status,
        arena_status,
        visual.pulse + 1,
        kTitleArrangementModes[visual.arrangement_index]);
    draw_panel(hdc, &command_bar, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, blastmonidz_style.panel_edge, 22);
    draw_text_block(hdc, command_bar.left + 18, command_bar.top + 8, command_bar.right - command_bar.left - 36, 22, status, 16, FW_NORMAL, blastmonidz_style.text);
    draw_text_block(hdc, command_bar.left + 18, command_bar.top + 26, command_bar.right - command_bar.left - 36, 18, feature_text, 12, FW_NORMAL, visual.tertiary_tint);
    draw_text_block(hdc, command_bar.left + 18, command_bar.top + 30, command_bar.right - command_bar.left - 36, 24,
        blastmonidz_bridge_latest_inbox(),
        20, FW_SEMIBOLD, visual.primary_tint);
}

static void draw_lore_scene(HDC hdc, RECT client) {
    RECT frame = {34, 24, client.right - 34, client.bottom - 24};
    draw_panel(hdc, &frame, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, blastmonidz_style.panel_edge, 28);
    draw_text_block(hdc, 58, 48, client.right - 116, 42, "BLASTMONIDZ WORLD BRIEF", 28, FW_BOLD, blastmonidz_style.accent);
    draw_text_block(hdc, 58, 106, client.right - 116, client.bottom - 210,
        "BlastKin are sentient AI entities inhabiting a collective stream-consciousness.\n\n"
        "ArtiSapiens persist as rival profiles inside the same data spectrum. Their encounters are filtered through a consensus timeline buffered at ten times human optical registration.\n\n"
        "Bomb Gems are electromineral obstacles. Explosions rewrite the local chemical atmosphere, while each Blastmonid evolves metabolically and cosmetically against that shifting chemistry field.\n\n"
        "Each combatant also carries a decentralized self-communication feed: inner signal, world attunement, rival pressure, ghost noise, and a rolling balance score. Combat, chemistry, and re-entry all push the same feed.\n\n"
        "Blastminidz remains the handheld spinoff line in-world: micro-cellular descendants cultivated through wireless eco-chemical turf conflicts.",
        18, FW_NORMAL, blastmonidz_style.text);
    {
        RECT badge = {58, client.bottom - 92, 356, client.bottom - 54};
        draw_pill(hdc, &badge, mix_color(blastmonidz_style.accent, blastmonidz_style.background, 1, 3), blastmonidz_style.accent, "LORE MODE // FOCUS READING", blastmonidz_style.text);
    }
    draw_text_block(hdc, 380, client.bottom - 88, client.right - 438, 30, blastmonidz_bridge_latest_status(), 14, FW_NORMAL, blastmonidz_style.text);
}

static void draw_archive_scene(HDC hdc, RECT client) {
    int i;
    int y = 92;
    RECT shell = {32, 22, client.right - 32, client.bottom - 24};
    draw_panel(hdc, &shell, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, blastmonidz_style.panel_edge, 28);
    draw_text_block(hdc, 50, y + 4, client.right - 100, 36, "ARCHIVE COHERENCY MAP", 28, FW_BOLD, blastmonidz_style.accent);
    {
        char organism_line[320];
        blastmonidz_describe_design_organism(&g_design_organism, organism_line, (int)sizeof(organism_line));
        draw_text_block(hdc, 50, 58, client.right - 100, 40, organism_line, 14, FW_NORMAL, blastmonidz_style.text);
    }
    draw_text_block(hdc, 50, 76, client.right - 100, 24, "Representative preview cards from the remapped archive. The console catalog still lists the full source lineage.", 15, FW_NORMAL, blastmonidz_style.text);
    for (i = 0; i < MAX_ARCHIVE_ITEMS; ++i) {
        int column = i / 8;
        int row = i % 8;
        int left = 50 + column * ((client.right - 124) / 2);
        int right = left + ((client.right - 156) / 2);
        RECT card = {left, y + row * 84, right, y + row * 84 + 72};
        RECT preview = {card.left + 10, card.top + 8, card.left + 74, card.bottom - 8};
        const ArchiveBitmap *preview_bitmap = get_archive_preview_bitmap(i);
        char metrics[256];
        draw_panel(hdc, &card, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, blastmonidz_style.panel_edge, 18);
        if (preview_bitmap && preview_bitmap->loaded) {
            draw_archive_bitmap(hdc, &preview, preview_bitmap, 255);
        } else {
            fill_rect_color(hdc, &preview, mix_color(blastmonidz_style.panel_edge, blastmonidz_style.background, 1, 2));
        }
        frame_rect_color(hdc, &preview, blastmonidz_style.panel_edge);
        draw_text_block(hdc, card.left + 84, card.top + 8, card.right - card.left - 94, 18, blastmonidz_archive_map[i].blastmonidz_id, 13, FW_BOLD, blastmonidz_style.text);
        draw_text_block(hdc, card.left + 84, card.top + 26, card.right - card.left - 94, 16, blastmonidz_archive_map[i].role, 12, FW_SEMIBOLD, blastmonidz_style.accent);
        if (preview_bitmap && preview_bitmap->analyzed) {
            blastmonidz_describe_asset_profile(&preview_bitmap->profile, metrics, (int)sizeof(metrics));
        } else {
            snprintf(metrics, sizeof(metrics), "%s", blastmonidz_archive_map[i].archive_entry);
        }
        draw_text_block(hdc, card.left + 84, card.top + 42, card.right - card.left - 94, 24, metrics, 11, FW_NORMAL, blastmonidz_style.text);
        if (i == 15) {
            draw_text_block(hdc, 52, client.bottom - 40, client.right - 104, 20, "Archive previews stay bound to the Bomberman-derived cache, but the naming and role language remain fully re-authored for Blastmonidz.", 13, FW_NORMAL, blastmonidz_style.text);
        }
    }
}

static void draw_starter_scene(HDC hdc, RECT client) {
    int i;
    draw_text_block(hdc, 42, 34, client.right - 84, 36, "STARTER TOKEN DRAW", 28, FW_BOLD, blastmonidz_style.accent);
    if (!g_state) {
        return;
    }
    {
        char world_line[160];
        snprintf(world_line, sizeof(world_line), "Whole-self phase %s | balance %d", blastmonidz_world_phase_name(g_state), g_state->world_feed.balance);
        draw_text_block(hdc, 44, 70, client.right - 88, 24, world_line, 16, FW_SEMIBOLD, blastmonidz_style.text);
    }
    for (i = 0; i < MAX_PLAYERS; ++i) {
        RECT card = {54, 104 + i * 118, client.right - 54, 196 + i * 118};
        int use_rival = 0;
        int family = 0;
        int direction = 0;
        int frame = 0;
        draw_panel(hdc, &card, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, blastmonidz_style.panel_edge, 22);
        {
            RECT portrait = {card.left + 12, card.top + 12, card.left + 84, card.bottom - 12};
            const ArchiveBitmap *sprite = get_player_sprite_bitmap(g_state, i, &use_rival, &family, &direction, &frame);
            if (sprite->loaded) {
                draw_archive_bitmap(hdc, &portrait, sprite, 255);
            } else {
                HBRUSH brush = CreateSolidBrush(to_rgb(g_state->players[i].mon.starter->color));
                FillRect(hdc, &portrait, brush);
                DeleteObject(brush);
            }
            frame_rect_color(hdc, &portrait, blastmonidz_style.panel_edge);
        }
        draw_text_block(hdc, card.left + 100, card.top + 10, 360, 28, g_state->players[i].name, 20, FW_BOLD, blastmonidz_style.text);
        draw_text_block(hdc, card.left + 100, card.top + 38, 420, 24, g_state->players[i].mon.starter->name, 18, FW_SEMIBOLD, blastmonidz_style.accent);
        draw_text_block(hdc, card.left + 100, card.top + 62, client.right - card.left - 124, 24, g_state->players[i].mon.starter->growth_family, 15, FW_NORMAL, blastmonidz_style.text);
        {
            char visual_line[256];
            snprintf(visual_line, sizeof(visual_line), "%s | doctrine %s | %s frame %02d | %s | feed %d/%d/%d/%d/%d",
                blastmonidz_growth_title(g_state->players[i].mon.growth_stage),
                blastmonidz_doctrine_name(g_state->players[i].doctrine),
                player_direction_name(direction),
                frame + 1,
                use_rival ? "rival silhouette" : "blastkin silhouette",
                g_state->players[i].mon.self_feed.inner_signal,
                g_state->players[i].mon.self_feed.world_signal,
                g_state->players[i].mon.self_feed.rival_signal,
                g_state->players[i].mon.self_feed.ghost_signal,
                g_state->players[i].mon.self_feed.balance);
            draw_text_block(hdc, card.left + 100, card.top + 82, client.right - card.left - 124, 24, visual_line, 15, FW_NORMAL, blastmonidz_style.text);
        }
    }
}

static void draw_arena_scene(HDC hdc, RECT client) {
    int map_left = 32;
    int map_top = 72;
    int map_width = (client.right * 2) / 3;
    int map_height = client.bottom - 220;
    int side_left = map_left + map_width + 24;
    int i;
    ArenaView view;
    if (!g_state || !g_state->arena.tiles) {
        draw_text_block(hdc, 40, 40, client.right - 80, 40, "Arena unavailable", 22, FW_BOLD, blastmonidz_style.accent);
        return;
    }
    view = blastmonidz_calculate_view(g_state);
    {
        RECT header = {22, 16, client.right - 22, 60};
        char header_line[256];
        draw_panel(hdc, &header, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, blastmonidz_style.panel_edge, 22);
        snprintf(header_line, sizeof(header_line), "BLASTMONIDZ ARENA VIEW // %s // seed %08X", blastmonidz_visual_theme_name(g_state), g_state->visuals.run_seed);
        draw_text_block(hdc, 36, 26, client.right - 72, 24, header_line, 24, FW_BOLD, blastmonidz_style.accent);
    }
    draw_meter(hdc, 34, 68, 180, 18, "Ion", g_state->arena.chemistry[0], 24, (Color){118, 180, 255, 255}, (Color){82, 132, 230, 255});
    draw_meter(hdc, 226, 68, 180, 18, "Spore", g_state->arena.chemistry[1], 24, (Color){116, 214, 134, 255}, (Color){66, 148, 90, 255});
    draw_meter(hdc, 418, 68, 180, 18, "Brine", g_state->arena.chemistry[2], 24, (Color){244, 184, 108, 255}, (Color){208, 116, 72, 255});
    {
        int cell_w = map_width / view.width;
        int cell_h = map_height / view.height;
        int cell = cell_w < cell_h ? cell_w : cell_h;
        RECT frame = {map_left - 2, map_top - 2, map_left + view.width * cell + 2, map_top + view.height * cell + 2};
        draw_panel(hdc, &frame, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, blastmonidz_style.panel_edge, 16);
        for (i = 0; i < view.height; ++i) {
            int j;
            for (j = 0; j < view.width; ++j) {
                int world_x = view.left + j;
                int world_y = view.top + i;
                const BlastmonidzHomeTile *home_tile = blastmonidz_select_home_tile(g_state, world_x, world_y);
                RECT tile = {map_left + j * cell, map_top + i * cell, map_left + (j + 1) * cell, map_top + (i + 1) * cell};
                int player_id = blastmonidz_player_at(g_state, world_x, world_y);
                int bomb_id = blastmonidz_bomb_at(&g_state->arena, world_x, world_y);
                int gem_id = blastmonidz_gem_at(&g_state->arena, world_x, world_y);
                unsigned char tile_type = g_state->arena.tiles[world_y * g_state->arena.width + world_x];
                if (tile_type == TILE_WALL) {
                    fill_rect_color(hdc, &tile, blastmonidz_style.wall);
                } else {
                    if (g_floor_tile.loaded) {
                        draw_archive_bitmap(hdc, &tile, &g_floor_tile, 255);
                    } else {
                                fill_rect_color(hdc, &tile, mix_color(blastmonidz_style.floor, organism_environment_tint(), 1, 4));
                    }
                    {
                        const ArchiveBitmap *overlay = get_floor_overlay_bitmap(g_state, world_x, world_y);
                        if (overlay) {
                                    draw_archive_bitmap(hdc, &tile, overlay, organism_overlay_alpha(72 + (g_state->arena.chemistry[(world_x + world_y) % 3] % 80)));
                        }
                    }
                    draw_home_tile_pattern(hdc, &tile, home_tile, mix_color(organism_environment_tint(), blastmonidz_style.text, 1, 2));
                }
                if (tile_type == TILE_CRATE) {
                    const ArchiveBitmap *crate_bitmap = get_crate_bitmap(g_state, world_x, world_y);
                    if (crate_bitmap && crate_bitmap->loaded) {
                        RECT inner = {tile.left + 1, tile.top + 1, tile.right - 1, tile.bottom - 1};
                        draw_archive_bitmap(hdc, &inner, crate_bitmap, 255);
                    } else {
                        fill_rect_color(hdc, &tile, blastmonidz_style.crate);
                    }
                }
                frame_rect_color(hdc, &tile, mix_color(blastmonidz_style.panel_edge, blastmonidz_style.background, 1, 3));
                if (gem_id >= 0) {
                    const ArchiveBitmap *gem_bitmap = get_gem_bitmap(g_state, &g_state->arena.gems[gem_id]);
                    char gem_label[2] = {g_state->arena.gems[gem_id].glyph, '\0'};
                    if (gem_bitmap && gem_bitmap->loaded) {
                        RECT inner = {tile.left + cell / 8, tile.top + cell / 8, tile.right - cell / 8, tile.bottom - cell / 8};
                        draw_archive_bitmap(hdc, &inner, gem_bitmap, 220);
                    } else {
                        RECT inner = {tile.left + cell / 4, tile.top + cell / 4, tile.right - cell / 4, tile.bottom - cell / 4};
                        HBRUSH gem_brush = CreateSolidBrush(RGB(91 + (g_state->arena.gems[gem_id].tier * 11) % 120, 120, 190));
                        FillRect(hdc, &inner, gem_brush);
                        DeleteObject(gem_brush);
                    }
                    draw_centered_tile_label(hdc, &tile, gem_label, cell > 28 ? 14 : 10, blastmonidz_style.text);
                }
                if (bomb_id >= 0) {
                    const ArchiveBitmap *bomb_bitmap = get_bomb_bitmap(g_state, &g_state->arena.bombs[bomb_id], bomb_id);
                    if (bomb_bitmap && bomb_bitmap->loaded) {
                        RECT inner = {tile.left + 1, tile.top + 1, tile.right - 1, tile.bottom - 1};
                        draw_archive_bitmap(hdc, &inner, bomb_bitmap, 255);
                    } else {
                        HBRUSH bomb_brush = CreateSolidBrush(to_rgb(blastmonidz_style.bomb));
                        HBRUSH old_brush = (HBRUSH)SelectObject(hdc, bomb_brush);
                        HPEN pen = CreatePen(PS_SOLID, 1, to_rgb(blastmonidz_style.text));
                        HPEN old_pen = (HPEN)SelectObject(hdc, pen);
                        Ellipse(hdc, tile.left + 2, tile.top + 2, tile.right - 2, tile.bottom - 2);
                        SelectObject(hdc, old_pen);
                        DeleteObject(pen);
                        SelectObject(hdc, old_brush);
                        DeleteObject(bomb_brush);
                    }
                }
                if (player_id >= 0) {
                    const ArchiveBitmap *player_sprite = get_player_sprite_bitmap(g_state, player_id, NULL, NULL, NULL, NULL);
                    if (player_sprite && player_sprite->loaded) {
                        RECT inner = {tile.left + 1, tile.top + 1, tile.right - 1, tile.bottom - 1};
                        draw_archive_bitmap(hdc, &inner, player_sprite, 255);
                    } else {
                        Color player_color = g_state->players[player_id].mon.alive ? g_state->players[player_id].mon.starter->color : blastmonidz_style.ghost;
                        HBRUSH player_brush = CreateSolidBrush(to_rgb(player_color));
                        HBRUSH old_brush = (HBRUSH)SelectObject(hdc, player_brush);
                        HPEN pen = CreatePen(PS_SOLID, 1, RGB(20, 20, 20));
                        HPEN old_pen = (HPEN)SelectObject(hdc, pen);
                        RoundRect(hdc, tile.left + 1, tile.top + 1, tile.right - 1, tile.bottom - 1, 6, 6);
                        SelectObject(hdc, old_pen);
                        DeleteObject(pen);
                        SelectObject(hdc, old_brush);
                        DeleteObject(player_brush);
                    }
                    frame_rect_color(hdc, &tile, blastmonidz_style.accent);
                }
            }
        }
    }
    {
        RECT profile_shell = {side_left - 12, 72, client.right - 26, client.bottom - 150};
        draw_panel(hdc, &profile_shell, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, blastmonidz_style.panel_edge, 22);
    }
    draw_text_block(hdc, side_left, 82, client.right - side_left - 24, 26, "Profiles", 22, FW_BOLD, blastmonidz_style.accent);
    {
        RECT world_shell = {side_left - 6, 114, client.right - 34, 186};
        char world_line[192];
        draw_panel(hdc, &world_shell, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, blastmonidz_style.panel_edge, 18);
        snprintf(world_line, sizeof(world_line), "%s | inner %d | world %d | rival %d | ghost %d | balance %d",
            blastmonidz_world_phase_name(g_state),
            g_state->world_feed.inner_signal,
            g_state->world_feed.world_signal,
            g_state->world_feed.rival_signal,
            g_state->world_feed.ghost_signal,
            g_state->world_feed.balance);
        draw_text_block(hdc, side_left, 126, client.right - side_left - 24, 22, "Whole-Self Communication Feed", 16, FW_BOLD, blastmonidz_style.accent);
        draw_text_block(hdc, side_left, 148, client.right - side_left - 24, 26, world_line, 14, FW_NORMAL, blastmonidz_style.text);
    }
    for (i = 0; i < MAX_PLAYERS; ++i) {
        char line[256];
        Color doctrine_tint = doctrine_color(g_state->players[i].doctrine);
        int use_rival = 0;
        int family = 0;
        int direction = 0;
        int frame = 0;
        RECT icon_rect = {side_left + 4, 204 + i * 84, side_left + 40, 240 + i * 84};
        get_player_sprite_bitmap(g_state, i, &use_rival, &family, &direction, &frame);
        if (g_bomb_pouch.loaded && g_state->players[i].mon.bomb_cooldown > 0) {
            draw_archive_bitmap(hdc, &icon_rect, &g_bomb_pouch, 210);
        }
        {
            RECT player_card = {side_left - 6, 194 + i * 84, client.right - 34, 266 + i * 84};
            RECT doctrine_badge = {player_card.right - 132, player_card.top + 8, player_card.right - 12, player_card.top + 34};
            draw_panel(hdc, &player_card, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, doctrine_tint, 18);
            draw_pill(hdc, &doctrine_badge, mix_color(doctrine_tint, blastmonidz_style.background, 1, 3), doctrine_tint, blastmonidz_doctrine_name(g_state->players[i].doctrine), blastmonidz_style.text);
        }
        snprintf(line, sizeof(line), "%s\nDoctrine %s  Wins %d  HP %d/%d  Lag %d\n%s | %s\nFeed %d/%d/%d/%d/%d | %s f%02d\nAI %s",
            g_state->players[i].name,
            blastmonidz_doctrine_name(g_state->players[i].doctrine),
            g_state->players[i].run_wins,
            g_state->players[i].mon.health,
            g_state->players[i].mon.max_health,
            g_state->players[i].mon.delay_ticks,
            blastmonidz_growth_title(g_state->players[i].mon.growth_stage),
            blastmonidz_concoctions[g_state->players[i].mon.concoction_id],
            g_state->players[i].mon.self_feed.inner_signal,
            g_state->players[i].mon.self_feed.world_signal,
            g_state->players[i].mon.self_feed.rival_signal,
            g_state->players[i].mon.self_feed.ghost_signal,
            g_state->players[i].mon.self_feed.balance,
            player_direction_name(direction),
            frame + 1,
            g_state->players[i].ai_debug_line);
        draw_text_block(hdc, side_left, 200 + i * 84, client.right - side_left - 24, 72, line, 14, FW_NORMAL, blastmonidz_style.text);
        draw_text_block(hdc, side_left, 254 + i * 84, client.right - side_left - 24, 16, g_state->players[i].ai_debug_line, 12, FW_SEMIBOLD, doctrine_tint);
    }
    {
        RECT events_shell = {24, client.bottom - 144, client.right - 24, client.bottom - 20};
        draw_panel(hdc, &events_shell, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, blastmonidz_style.panel_edge, 20);
    }
    draw_text_block(hdc, 36, client.bottom - 136, client.right - 72, 28, "Recent Events + Bridge", 20, FW_BOLD, blastmonidz_style.accent);
    for (i = 0; i < MAX_LOG_LINES; ++i) {
        if (g_state->log_lines[i][0] != '\0') {
            draw_text_block(hdc, 44, client.bottom - 104 + i * 16, client.right - 88, 18, g_state->log_lines[i], 13, FW_NORMAL, blastmonidz_style.text);
        }
    }
    {
        char tile_line[384];
        char tile_effects[320];
        const BlastmonidzHomeTile *focus_tile = blastmonidz_select_home_tile(g_state, g_state->players[0].mon.x, g_state->players[0].mon.y);
        snprintf(tile_line, sizeof(tile_line), "Home Tile Focus: %s [%c] | %s",
            focus_tile->name,
            focus_tile->glyph,
            focus_tile->theory_role);
        draw_text_block(hdc, 44, client.bottom - 120, client.right - 88, 16, tile_line, 13, FW_SEMIBOLD, blastmonidz_style.accent);
        blastmonidz_describe_home_tile(focus_tile, tile_effects, (int)sizeof(tile_effects));
        draw_text_block(hdc, 44, client.bottom - 104, client.right - 88, 16, tile_effects, 12, FW_NORMAL, blastmonidz_style.text);
    }
    draw_text_block(hdc, 44, client.bottom - 88, client.right - 88, 16, blastmonidz_bridge_latest_status(), 12, FW_NORMAL, blastmonidz_style.text);
    draw_text_block(hdc, 44, client.bottom - 72, client.right - 88, 16, blastmonidz_bridge_latest_inbox(), 12, FW_NORMAL, blastmonidz_style.text);
}

static void draw_summary_scene(HDC hdc, RECT client) {
    int i;
    if (!g_state) {
        return;
    }
    {
        RECT shell = {28, 20, client.right - 28, client.bottom - 24};
        draw_panel(hdc, &shell, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, blastmonidz_style.panel_edge, 28);
    }
    draw_text_block(hdc, 42, 34, client.right - 84, 36, "RUN COMPLETE", 28, FW_BOLD, blastmonidz_style.accent);
    draw_text_block(hdc, 48, 84, client.right - 96, 30, g_state->players[g_state->winner_id].name, 24, FW_BOLD, blastmonidz_style.text);
    {
        RECT crown = {client.right - 300, 34, client.right - 56, 76};
        draw_pill(hdc, &crown, mix_color(blastmonidz_style.accent, blastmonidz_style.background, 1, 3), blastmonidz_style.accent, "SHOWCASE CLEAR", blastmonidz_style.text);
    }
    for (i = 0; i < MAX_PLAYERS; ++i) {
        char line[192];
        Color doctrine_tint = doctrine_color(g_state->players[i].doctrine);
        RECT card = {44, 136 + i * 48, client.right - 52, 176 + i * 48};
        draw_panel(hdc, &card, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, doctrine_tint, 16);
        snprintf(line, sizeof(line), "%s | doctrine %s | wins %d | %s | gems %d | kills %d | feed %d/%d/%d/%d/%d | ai %s",
            g_state->players[i].name,
            blastmonidz_doctrine_name(g_state->players[i].doctrine),
            g_state->players[i].run_wins,
            blastmonidz_growth_title(g_state->players[i].mon.growth_stage),
            g_state->players[i].mon.gems_cleared,
            g_state->players[i].mon.round_kills,
            g_state->players[i].mon.self_feed.inner_signal,
            g_state->players[i].mon.self_feed.world_signal,
            g_state->players[i].mon.self_feed.rival_signal,
            g_state->players[i].mon.self_feed.ghost_signal,
            g_state->players[i].mon.self_feed.balance,
            g_state->players[i].ai_debug_line);
        draw_text_block(hdc, 56, 146 + i * 48, client.right - 116, 28, line, 18, FW_NORMAL, doctrine_tint);
    }
    draw_text_block(hdc, 54, client.bottom - 150, client.right - 108, 92,
        "This vertical-slice deliverable packages the simulation state, a seeded procedural archive renderer, the whole-self communication world feed, and saved run-profile output into a shippable Windows host bundle.\n"
        "Theme, bomb cadence, floor paint field, crate props, motion-frame families, world phase, and analysis-derived phenotype biases are recombined each run while the arena formulas stay unchanged.",
        17, FW_NORMAL, blastmonidz_style.text);
    {
        char visual_summary[224];
        snprintf(visual_summary, sizeof(visual_summary), "Visual profile: %s | %s | feed %d/%d/%d/%d/%d | elastic %.2f | env %.2f | seed %08X",
            blastmonidz_visual_theme_name(g_state),
            blastmonidz_world_phase_name(g_state),
            g_state->world_feed.inner_signal,
            g_state->world_feed.world_signal,
            g_state->world_feed.rival_signal,
            g_state->world_feed.ghost_signal,
            g_state->world_feed.balance,
            g_design_organism.animation_elasticity,
            g_design_organism.environmental_mutation_bias,
            g_state->visuals.run_seed);
        draw_text_block(hdc, 54, client.bottom - 52, client.right - 108, 26, visual_summary, 16, FW_SEMIBOLD, blastmonidz_style.accent);
    }
}

static void draw_scene(HDC hdc, RECT client) {
    fill_rect_color(hdc, &client, blastmonidz_style.background);
    switch (g_scene) {
        case WINDOW_SCENE_TITLE: draw_title_scene(hdc, client); break;
        case WINDOW_SCENE_LORE: draw_lore_scene(hdc, client); break;
        case WINDOW_SCENE_ARCHIVE: draw_archive_scene(hdc, client); break;
        case WINDOW_SCENE_STARTER: draw_starter_scene(hdc, client); break;
        case WINDOW_SCENE_ARENA: draw_arena_scene(hdc, client); break;
        case WINDOW_SCENE_SUMMARY: draw_summary_scene(hdc, client); break;
    }
}

static LRESULT CALLBACK blastmonidz_window_proc(HWND hwnd, UINT message, WPARAM w_param, LPARAM l_param) {
    switch (message) {
        case WM_CLOSE:
            ShowWindow(hwnd, SW_HIDE);
            return 0;
        case WM_TIMER:
            InvalidateRect(hwnd, NULL, FALSE);
            return 0;
        case WM_PAINT: {
            PAINTSTRUCT paint;
            RECT client;
            HDC hdc = BeginPaint(hwnd, &paint);
            (void)w_param;
            (void)l_param;
            GetClientRect(hwnd, &client);
            draw_scene(hdc, client);
            EndPaint(hwnd, &paint);
            return 0;
        }
    }
    return DefWindowProc(hwnd, message, w_param, l_param);
}

int blastmonidz_window_init(void) {
    WNDCLASSA window_class;
    HINSTANCE instance;
    HRESULT hr;
    if (g_initialized) {
        return 1;
    }
    hr = CoInitializeEx(NULL, COINIT_APARTMENTTHREADED);
    if (hr == S_OK || hr == S_FALSE) {
        g_com_initialized = 1;
    }
    hr = CoCreateInstance(&CLSID_WICImagingFactory, NULL, CLSCTX_INPROC_SERVER,
        &IID_IWICImagingFactory, (LPVOID *)&g_wic_factory);
    if (FAILED(hr)) {
        g_wic_factory = NULL;
    }
    instance = GetModuleHandleA(NULL);
    ZeroMemory(&window_class, sizeof(window_class));
    window_class.lpfnWndProc = blastmonidz_window_proc;
    window_class.hInstance = instance;
    window_class.lpszClassName = kWindowClassName;
    window_class.hCursor = LoadCursor(NULL, IDC_ARROW);
    window_class.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    RegisterClassA(&window_class);
        g_hwnd = CreateWindowExA(0, kWindowClassName, "Blastmonidz Visual Companion", WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT, 1120, 860, NULL, NULL, instance, NULL);
    if (!g_hwnd) {
        return 0;
    }
    blastmonidz_design_organism_reset(&g_design_organism);
    SetTimer(g_hwnd, kTitleTimerId, 120, NULL);
    ShowWindow(g_hwnd, SW_MAXIMIZE);
    UpdateWindow(g_hwnd);
    load_title_archive_images();
    load_runtime_archive_images();
    write_design_profile_report();
    g_initialized = 1;
    return 1;
}

void blastmonidz_window_shutdown(void) {
    int family;
    int direction;
    int frame;
    int chemistry_index;
    reset_archive_bitmap(&g_title_backdrop);
    reset_archive_bitmap(&g_title_logo);
    reset_archive_bitmap(&g_floor_tile);
    reset_archive_bitmap(&g_bomb_pouch);
    for (chemistry_index = 0; chemistry_index < BLASTMONIDZ_CRATE_VARIANTS; ++chemistry_index) {
        reset_archive_bitmap(&g_crate_variants[chemistry_index]);
    }
    for (frame = 0; frame < BLASTMONIDZ_PLAYER_FRAMES; ++frame) {
        reset_archive_bitmap(&g_bomb_frames[frame]);
        reset_archive_bitmap(&g_rival_back_sprites[frame]);
    }
    for (chemistry_index = 0; chemistry_index < BLASTMONIDZ_PAINT_VARIANTS; ++chemistry_index) {
        reset_archive_bitmap(&g_gem_paints[chemistry_index]);
    }
    for (family = 0; family < BLASTMONIDZ_HERO_FAMILIES; ++family) {
        for (direction = 0; direction < BLASTMONIDZ_PLAYER_DIRECTIONS; ++direction) {
            for (frame = 0; frame < BLASTMONIDZ_PLAYER_FRAMES; ++frame) {
                reset_archive_bitmap(&g_player_sprites[family][direction][frame]);
            }
        }
    }
    for (family = 0; family < BLASTMONIDZ_RIVAL_FAMILIES; ++family) {
        for (frame = 0; frame < BLASTMONIDZ_PLAYER_FRAMES; ++frame) {
            reset_archive_bitmap(&g_rival_side_sprites[family][frame]);
        }
    }
    if (g_wic_factory) {
        IWICImagingFactory_Release(g_wic_factory);
        g_wic_factory = NULL;
    }
    if (g_com_initialized) {
        CoUninitialize();
        g_com_initialized = 0;
    }
    if (g_hwnd) {
        KillTimer(g_hwnd, kTitleTimerId);
        DestroyWindow(g_hwnd);
        g_hwnd = NULL;
    }
    blastmonidz_design_organism_reset(&g_design_organism);
    g_initialized = 0;
    g_state = NULL;
}

void blastmonidz_window_pump(void) {
    MSG message;
    blastmonidz_bridge_poll();
    while (PeekMessage(&message, NULL, 0, 0, PM_REMOVE)) {
        TranslateMessage(&message);
        DispatchMessage(&message);
    }
}

static void present_scene(WindowScene scene, const GameState *state) {
    if (!g_initialized || !g_hwnd) {
        return;
    }
    g_scene = scene;
    g_state = state;
    InvalidateRect(g_hwnd, NULL, TRUE);
    UpdateWindow(g_hwnd);
    blastmonidz_window_pump();
}

void blastmonidz_window_present_title(void) {
    present_scene(WINDOW_SCENE_TITLE, NULL);
}

void blastmonidz_window_present_lore(void) {
    present_scene(WINDOW_SCENE_LORE, NULL);
}

void blastmonidz_window_present_archive(void) {
    present_scene(WINDOW_SCENE_ARCHIVE, NULL);
}

void blastmonidz_window_present_starter_draw(const GameState *state) {
    present_scene(WINDOW_SCENE_STARTER, state);
}

void blastmonidz_window_present_arena(const GameState *state) {
    present_scene(WINDOW_SCENE_ARENA, state);
}

void blastmonidz_window_present_summary(const GameState *state) {
    present_scene(WINDOW_SCENE_SUMMARY, state);
}

#else

int blastmonidz_window_init(void) { return 1; }
void blastmonidz_window_shutdown(void) {}
void blastmonidz_window_pump(void) {}
void blastmonidz_window_present_title(void) {}
void blastmonidz_window_present_lore(void) {}
void blastmonidz_window_present_archive(void) {}
void blastmonidz_window_present_starter_draw(const GameState *state) { (void)state; }
void blastmonidz_window_present_arena(const GameState *state) { (void)state; }
void blastmonidz_window_present_summary(const GameState *state) { (void)state; }

#endif
