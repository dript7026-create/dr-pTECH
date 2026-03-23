/* gui_assets.h — Runtime asset loader for Recraft-generated GUI resources
 *
 * This module loads PNG assets from the assets/recraft/ directory tree
 * and provides them as HBITMAP / icon handles to the viewer applications.
 *
 * Integration:
 *   #include "gui_assets.h"
 *   gui_assets_init("C:\\path\\to\\assets\\recraft");
 *   HBITMAP bmp = gui_get_asset(ASSET_ECBMPS_SPLASH);
 *   ...
 *   gui_assets_cleanup();
 */
#ifndef GUI_ASSETS_H
#define GUI_ASSETS_H

#include <windows.h>
#include <stdio.h>

/* ------------------------------------------------------------------ */
/*  Asset slot enumeration                                            */
/* ------------------------------------------------------------------ */
typedef enum {
    /* --- Branding --- */
    ASSET_SPLASH_ECBMPS,
    ASSET_SPLASH_CCP,
    ASSET_BRAND_LOGO_LIGHT,
    ASSET_BRAND_LOGO_DARK,
    ASSET_BRAND_WATERMARK,
    ASSET_BRAND_FAVICON,

    /* --- ECBMPS Shell Icons --- */
    ASSET_ECBMPS_ICON_16,
    ASSET_ECBMPS_ICON_32,
    ASSET_ECBMPS_ICON_48,
    ASSET_ECBMPS_ICON_64,
    ASSET_ECBMPS_ICON_128,
    ASSET_ECBMPS_ICON_256,

    /* --- CCP Shell Icons --- */
    ASSET_CCP_ICON_16,
    ASSET_CCP_ICON_32,
    ASSET_CCP_ICON_48,
    ASSET_CCP_ICON_64,
    ASSET_CCP_ICON_128,
    ASSET_CCP_ICON_256,

    /* --- ECBMPS Viewer GUI --- */
    ASSET_ECBMPS_FRAME_TL,
    ASSET_ECBMPS_FRAME_TR,
    ASSET_ECBMPS_FRAME_BL,
    ASSET_ECBMPS_FRAME_BR,
    ASSET_ECBMPS_TITLEBAR_BG,
    ASSET_ECBMPS_BTN_CLOSE_NORMAL,
    ASSET_ECBMPS_BTN_CLOSE_HOVER,
    ASSET_ECBMPS_BTN_CLOSE_PRESSED,
    ASSET_ECBMPS_BTN_MIN_NORMAL,
    ASSET_ECBMPS_BTN_MIN_HOVER,
    ASSET_ECBMPS_BTN_MAX_NORMAL,
    ASSET_ECBMPS_BTN_MAX_HOVER,
    ASSET_ECBMPS_BG_LIGHT,
    ASSET_ECBMPS_BG_DARK,
    ASSET_ECBMPS_BG_SEPIA,
    ASSET_ECBMPS_BG_NIGHT,
    ASSET_ECBMPS_SCROLL_THUMB,
    ASSET_ECBMPS_SCROLL_TRACK,

    /* --- CCP Viewer GUI --- */
    ASSET_CCP_FRAME_TL,
    ASSET_CCP_FRAME_TR,
    ASSET_CCP_FRAME_BL,
    ASSET_CCP_FRAME_BR,
    ASSET_CCP_TITLEBAR_BG,
    ASSET_CCP_BTN_CLOSE_NORMAL,
    ASSET_CCP_BTN_CLOSE_HOVER,
    ASSET_CCP_BTN_PLAY_NORMAL,
    ASSET_CCP_BTN_PLAY_HOVER,
    ASSET_CCP_BTN_PAUSE_NORMAL,
    ASSET_CCP_SIDEBAR_BG,

    /* --- Popup Templates --- */
    ASSET_POPUP_CONFIRM_DARK,
    ASSET_POPUP_ERROR_DARK,
    ASSET_POPUP_INFO_DARK,
    ASSET_POPUP_TOAST_INFO_DARK,
    ASSET_POPUP_TOOLTIP_DARK,

    ASSET_COUNT
} AssetSlot;

/* ------------------------------------------------------------------ */
/*  Asset path map (relative to assets root)                          */
/* ------------------------------------------------------------------ */
static const char *g_asset_paths[ASSET_COUNT] = {
    [ASSET_SPLASH_ECBMPS]        = "branding/splash_ecbmps.png",
    [ASSET_SPLASH_CCP]           = "branding/splash_ccp.png",
    [ASSET_BRAND_LOGO_LIGHT]     = "branding/logo_light.png",
    [ASSET_BRAND_LOGO_DARK]      = "branding/logo_dark.png",
    [ASSET_BRAND_WATERMARK]      = "branding/watermark.png",
    [ASSET_BRAND_FAVICON]        = "branding/favicon.png",

    [ASSET_ECBMPS_ICON_16]      = "icons/ecbmps_icon_16.png",
    [ASSET_ECBMPS_ICON_32]      = "icons/ecbmps_icon_32.png",
    [ASSET_ECBMPS_ICON_48]      = "icons/ecbmps_icon_48.png",
    [ASSET_ECBMPS_ICON_64]      = "icons/ecbmps_icon_64.png",
    [ASSET_ECBMPS_ICON_128]     = "icons/ecbmps_icon_128.png",
    [ASSET_ECBMPS_ICON_256]     = "icons/ecbmps_icon_256.png",

    [ASSET_CCP_ICON_16]         = "icons/ccp_icon_16.png",
    [ASSET_CCP_ICON_32]         = "icons/ccp_icon_32.png",
    [ASSET_CCP_ICON_48]         = "icons/ccp_icon_48.png",
    [ASSET_CCP_ICON_64]         = "icons/ccp_icon_64.png",
    [ASSET_CCP_ICON_128]        = "icons/ccp_icon_128.png",
    [ASSET_CCP_ICON_256]        = "icons/ccp_icon_256.png",

    [ASSET_ECBMPS_FRAME_TL]     = "gui/ecbmps/frame_tl.png",
    [ASSET_ECBMPS_FRAME_TR]     = "gui/ecbmps/frame_tr.png",
    [ASSET_ECBMPS_FRAME_BL]     = "gui/ecbmps/frame_bl.png",
    [ASSET_ECBMPS_FRAME_BR]     = "gui/ecbmps/frame_br.png",
    [ASSET_ECBMPS_TITLEBAR_BG]  = "gui/ecbmps/titlebar/titlebar_bg.png",
    [ASSET_ECBMPS_BTN_CLOSE_NORMAL]  = "gui/ecbmps/titlebar/close_normal.png",
    [ASSET_ECBMPS_BTN_CLOSE_HOVER]   = "gui/ecbmps/titlebar/close_hover.png",
    [ASSET_ECBMPS_BTN_CLOSE_PRESSED] = "gui/ecbmps/titlebar/close_pressed.png",
    [ASSET_ECBMPS_BTN_MIN_NORMAL]    = "gui/ecbmps/titlebar/minimize_normal.png",
    [ASSET_ECBMPS_BTN_MIN_HOVER]     = "gui/ecbmps/titlebar/minimize_hover.png",
    [ASSET_ECBMPS_BTN_MAX_NORMAL]    = "gui/ecbmps/titlebar/maximize_normal.png",
    [ASSET_ECBMPS_BTN_MAX_HOVER]     = "gui/ecbmps/titlebar/maximize_hover.png",
    [ASSET_ECBMPS_BG_LIGHT]     = "gui/ecbmps/backgrounds/light.png",
    [ASSET_ECBMPS_BG_DARK]      = "gui/ecbmps/backgrounds/dark.png",
    [ASSET_ECBMPS_BG_SEPIA]     = "gui/ecbmps/backgrounds/sepia.png",
    [ASSET_ECBMPS_BG_NIGHT]     = "gui/ecbmps/backgrounds/night.png",
    [ASSET_ECBMPS_SCROLL_THUMB] = "gui/ecbmps/scrollbar/thumb.png",
    [ASSET_ECBMPS_SCROLL_TRACK] = "gui/ecbmps/scrollbar/track.png",

    [ASSET_CCP_FRAME_TL]        = "gui/ccp/frame_tl.png",
    [ASSET_CCP_FRAME_TR]        = "gui/ccp/frame_tr.png",
    [ASSET_CCP_FRAME_BL]        = "gui/ccp/frame_bl.png",
    [ASSET_CCP_FRAME_BR]        = "gui/ccp/frame_br.png",
    [ASSET_CCP_TITLEBAR_BG]     = "gui/ccp/titlebar/titlebar_bg.png",
    [ASSET_CCP_BTN_CLOSE_NORMAL]= "gui/ccp/titlebar/close_normal.png",
    [ASSET_CCP_BTN_CLOSE_HOVER] = "gui/ccp/titlebar/close_hover.png",
    [ASSET_CCP_BTN_PLAY_NORMAL] = "gui/ccp/toolbar/play_normal.png",
    [ASSET_CCP_BTN_PLAY_HOVER]  = "gui/ccp/toolbar/play_hover.png",
    [ASSET_CCP_BTN_PAUSE_NORMAL]= "gui/ccp/toolbar/pause_normal.png",
    [ASSET_CCP_SIDEBAR_BG]      = "gui/ccp/sidebar/sidebar_bg.png",

    [ASSET_POPUP_CONFIRM_DARK]   = "gui/popups/confirm_dark.png",
    [ASSET_POPUP_ERROR_DARK]     = "gui/popups/error_dark.png",
    [ASSET_POPUP_INFO_DARK]      = "gui/popups/info_dark.png",
    [ASSET_POPUP_TOAST_INFO_DARK]= "gui/popups/toast_info_dark.png",
    [ASSET_POPUP_TOOLTIP_DARK]   = "gui/popups/tooltip_dark.png",
};

/* ------------------------------------------------------------------ */
/*  Runtime state                                                     */
/* ------------------------------------------------------------------ */
static HBITMAP g_asset_bitmaps[ASSET_COUNT];
static char    g_assets_root[MAX_PATH];
static int     g_assets_loaded = 0;

/* ------------------------------------------------------------------ */
/*  PNG loader via stb_image (when available) or LoadImage fallback   */
/* ------------------------------------------------------------------ */
#ifdef __has_include
  #if __has_include("stb_image.h")
    #define GUI_ASSETS_HAS_STB 1
    #ifndef STB_IMAGE_IMPLEMENTATION
      #include "stb_image.h"
    #endif
  #endif
#endif

static HBITMAP load_png_as_bitmap(const char *path) {
#ifdef GUI_ASSETS_HAS_STB
    /* Use stb_image to decode PNG → RGBA pixels, then create a DIB section */
    int w, h, channels;
    unsigned char *pixels = stbi_load(path, &w, &h, &channels, 4); /* force RGBA */
    if (!pixels) return NULL;

    BITMAPINFO bmi;
    memset(&bmi, 0, sizeof(bmi));
    bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    bmi.bmiHeader.biWidth = w;
    bmi.bmiHeader.biHeight = -h; /* top-down */
    bmi.bmiHeader.biPlanes = 1;
    bmi.bmiHeader.biBitCount = 32;
    bmi.bmiHeader.biCompression = BI_RGB;

    void *dibBits = NULL;
    HBITMAP bmp = CreateDIBSection(NULL, &bmi, DIB_RGB_COLORS, &dibBits, NULL, 0);
    if (bmp && dibBits) {
        /* stb gives RGBA; Windows DIB is BGRA — swap R and B */
        unsigned char *src = pixels;
        unsigned char *dst = (unsigned char *)dibBits;
        for (int i = 0; i < w * h; i++) {
            dst[0] = src[2]; /* B */
            dst[1] = src[1]; /* G */
            dst[2] = src[0]; /* R */
            dst[3] = src[3]; /* A */
            src += 4;
            dst += 4;
        }
    }
    stbi_image_free(pixels);
    return bmp;
#else
    /* Fallback: try LoadImage for BMP files */
    wchar_t wpath[MAX_PATH];
    MultiByteToWideChar(CP_UTF8, 0, path, -1, wpath, MAX_PATH);
    HBITMAP bmp = (HBITMAP)LoadImageW(NULL, wpath,
        IMAGE_BITMAP, 0, 0, LR_LOADFROMFILE | LR_CREATEDIBSECTION);
    return bmp;
#endif
}

/* ------------------------------------------------------------------ */
/*  Public API                                                        */
/* ------------------------------------------------------------------ */

/*  Initialize asset system. assets_root = path to assets/recraft/ dir */
static void gui_assets_init(const char *assets_root) {
    strncpy(g_assets_root, assets_root, MAX_PATH - 1);
    g_assets_root[MAX_PATH - 1] = '\0';
    memset(g_asset_bitmaps, 0, sizeof(g_asset_bitmaps));

    /* Try loading each mapped asset */
    int loaded = 0;
    for (int i = 0; i < ASSET_COUNT; i++) {
        if (!g_asset_paths[i]) continue;
        char full[MAX_PATH * 2];
        snprintf(full, sizeof(full), "%s/%s", g_assets_root, g_asset_paths[i]);
        /* Normalize path separators */
        for (char *p = full; *p; p++)
            if (*p == '/') *p = '\\';

        g_asset_bitmaps[i] = load_png_as_bitmap(full);
        if (g_asset_bitmaps[i]) loaded++;
    }
    g_assets_loaded = loaded;
}

/* Get a loaded asset bitmap. Returns NULL if not loaded (viewer uses fallback) */
static HBITMAP gui_get_asset(AssetSlot slot) {
    if (slot < 0 || slot >= ASSET_COUNT) return NULL;
    return g_asset_bitmaps[slot];
}

/* Draw an asset onto HDC if available, returning 1 on success */
static int gui_draw_asset(HDC hdc, AssetSlot slot, int x, int y, int w, int h) {
    HBITMAP bmp = gui_get_asset(slot);
    if (!bmp) return 0;

    HDC mem = CreateCompatibleDC(hdc);
    HBITMAP old = (HBITMAP)SelectObject(mem, bmp);
    BITMAP info;
    GetObject(bmp, sizeof(info), &info);
    StretchBlt(hdc, x, y, w, h, mem, 0, 0, info.bmWidth, info.bmHeight, SRCCOPY);
    SelectObject(mem, old);
    DeleteDC(mem);
    return 1;
}

/* Number of successfully loaded assets */
static int gui_assets_count(void) { return g_assets_loaded; }

/* Cleanup */
static void gui_assets_cleanup(void) {
    for (int i = 0; i < ASSET_COUNT; i++) {
        if (g_asset_bitmaps[i]) {
            DeleteObject(g_asset_bitmaps[i]);
            g_asset_bitmaps[i] = NULL;
        }
    }
    g_assets_loaded = 0;
}

#endif /* GUI_ASSETS_H */
