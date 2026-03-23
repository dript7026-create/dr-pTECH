/* ecbmps_viewer.c — Win32 custom-shell viewer for .ecbmps media books
 * Electronic Colour Book Media Playback Shell runtime/reader
 * Build: cl /W4 /O2 ecbmps_viewer.c /link user32.lib gdi32.lib comctl32.lib comdlg32.lib shell32.lib
 *   or:  gcc -O2 ecbmps_viewer.c -o ecbmps_viewer.exe -lgdi32 -lcomctl32 -lcomdlg32 -lshell32 -mwindows
 */

#include "../compiler/common.h"
#include "gui_common.h"
#include "controller_input.h"
#include "gui_assets.h"
#include <objidl.h>
#include <wincodec.h>

/* ------------------------------------------------------------------ */
/*  Constants                                                         */
/* ------------------------------------------------------------------ */
#define APP_TITLE   L"drIpTECH \u00b7 ECBMPS Reader"
#define CLS_MAIN    L"EcbmpsViewerMain"
#define CLS_PAGE    L"EcbmpsPageView"
#define TOOLBAR_H   40
#define STATUSBAR_H 24
#define MARGIN       24
#define CTRL_TIMER_ID  1001
#define CTRL_POLL_MS   50     /* controller polling rate for page nav */

/* Reading modes */
enum { MODE_LIGHT = 0, MODE_DARK, MODE_SEPIA, MODE_COUNT };
static const COLORREF mode_bg[]   = { GUI_BG_PAGE, GUI_BG_PAGE_DARK, GUI_BG_PAGE_SEPIA };
static const COLORREF mode_text[] = { GUI_TEXT_DARK, GUI_TEXT_LIGHT, RGB(70, 50, 30) };

/* ------------------------------------------------------------------ */
/*  Loaded book state                                                 */
/* ------------------------------------------------------------------ */
typedef struct {
    /* Raw file data */
    uint8_t *raw;
    long     raw_size;

    /* Parsed header */
    EcbmpsHeader header;

    /* Title / author */
    char title[ECBMPS_MAX_TITLE];
    char author[ECBMPS_MAX_TITLE];

    /* TOC */
    EcbmpsTocEntry *toc;

    /* Current view state */
    int  current_page;
    int  reading_mode;
    float zoom;

    /* Bookmarks & highlights (mutable – written back) */
    int bookmark_count;
    EcbmpsBookmark bookmarks[ECBMPS_MAX_BOOKMARKS];
    int highlight_count;
    EcbmpsHighlight highlights[ECBMPS_MAX_HIGHLIGHTS];

    /* Source path for saving user data */
    wchar_t source_path[MAX_PATH];
    int     dirty;
} BookState;

static BookState g_book;

/* ------------------------------------------------------------------ */
/*  GUI state                                                         */
/* ------------------------------------------------------------------ */
static HWND  g_hwndMain;
static HWND  g_hwndPage;      /* page render child */
static HWND  g_hwndStatus;
static HFONT g_fontUI;
static HFONT g_fontPage;
static HFONT g_fontPageBold;
static int   g_highlight_mode = 0; /* 1 when user is in highlight-drag */
static POINT g_highlight_start;
static int   g_splash_shown = 0;
static DWORD g_splash_time  = 0;
#define SPLASH_DURATION_MS 2000

/* ------------------------------------------------------------------ */
/*  Forward declarations                                              */
/* ------------------------------------------------------------------ */
static int  load_ecbmps(const wchar_t *path);
static void save_userdata(void);
static void render_page(HDC hdc, RECT *area);
static void update_status(void);
static void open_file_dialog(HWND parent);
static void goto_page(int p);
static void toggle_bookmark(void);
static void show_bookmark_list(HWND parent);
static void show_about(HWND parent);

/* ------------------------------------------------------------------ */
/*  Load & parse .ecbmps file                                        */
/* ------------------------------------------------------------------ */
static int load_ecbmps(const wchar_t *path) {
    FILE *fp = _wfopen(path, L"rb");
    if (!fp) return 0;

    if (g_book.raw) { free(g_book.raw); free(g_book.toc); }
    memset(&g_book, 0, sizeof(g_book));
    wcscpy_s(g_book.source_path, MAX_PATH, path);

    fseek(fp, 0, SEEK_END);
    g_book.raw_size = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    g_book.raw = (uint8_t*)malloc((size_t)g_book.raw_size);
    if (!g_book.raw) { fclose(fp); return 0; }
    fread(g_book.raw, 1, (size_t)g_book.raw_size, fp);
    fseek(fp, 0, SEEK_SET);

    /* Header */
    g_book.header.magic          = read_u32(fp);
    g_book.header.version        = read_u32(fp);
    g_book.header.page_count     = read_u32(fp);
    g_book.header.flags          = read_u32(fp);
    g_book.header.title_offset   = read_u64(fp);
    g_book.header.toc_offset     = read_u64(fp);
    g_book.header.userdata_offset= read_u64(fp);

    if (g_book.header.magic != ECBMPS_MAGIC) {
        fclose(fp); free(g_book.raw); g_book.raw = NULL;
        return 0;
    }

    /* Title section */
    fseek(fp, (long)g_book.header.title_offset, SEEK_SET);
    uint32_t tlen = read_u32(fp);
    if (tlen > ECBMPS_MAX_TITLE - 1) tlen = ECBMPS_MAX_TITLE - 1;
    fread(g_book.title, 1, tlen, fp);
    g_book.title[tlen] = '\0';
    uint32_t alen = read_u32(fp);
    if (alen > ECBMPS_MAX_TITLE - 1) alen = ECBMPS_MAX_TITLE - 1;
    fread(g_book.author, 1, alen, fp);
    g_book.author[alen] = '\0';

    /* TOC */
    fseek(fp, (long)g_book.header.toc_offset, SEEK_SET);
    g_book.toc = (EcbmpsTocEntry*)calloc(g_book.header.page_count, sizeof(EcbmpsTocEntry));
    for (uint32_t i = 0; i < g_book.header.page_count; i++) {
        g_book.toc[i].page_offset = read_u64(fp);
        g_book.toc[i].page_size   = read_u32(fp);
        g_book.toc[i].page_type   = (uint8_t)fgetc(fp);
        g_book.toc[i].flags       = (uint8_t)fgetc(fp);
        uint16_t reserved;
        fread(&reserved, 2, 1, fp);
    }

    /* User data */
    if (g_book.header.userdata_offset > 0 &&
        (long)g_book.header.userdata_offset < g_book.raw_size) {
        fseek(fp, (long)g_book.header.userdata_offset, SEEK_SET);
        uint32_t ud_magic = read_u32(fp);
        if (ud_magic == ECBMPS_UD_MAGIC) {
            /* Bookmarks */
            uint16_t bc;
            fread(&bc, 2, 1, fp);
            g_book.bookmark_count = bc;
            for (int i = 0; i < bc && i < ECBMPS_MAX_BOOKMARKS; i++) {
                g_book.bookmarks[i].page_index   = read_u32(fp);
                g_book.bookmarks[i].scroll_offset = read_u32(fp);
                uint8_t ll = (uint8_t)fgetc(fp);
                g_book.bookmarks[i].label_length = ll;
                fread(g_book.bookmarks[i].label, 1, ll, fp);
                g_book.bookmarks[i].label[ll] = '\0';
            }
            /* Highlights */
            uint16_t hc;
            fread(&hc, 2, 1, fp);
            g_book.highlight_count = hc;
            for (int i = 0; i < hc && i < ECBMPS_MAX_HIGHLIGHTS; i++) {
                g_book.highlights[i].page_index  = read_u32(fp);
                g_book.highlights[i].start_char  = read_u32(fp);
                g_book.highlights[i].end_char    = read_u32(fp);
                g_book.highlights[i].color_rgba  = read_u32(fp);
            }
        }
    }

    fclose(fp);
    g_book.current_page = 0;
    g_book.zoom = 1.0f;
    g_book.reading_mode = MODE_LIGHT;
    return 1;
}

/* ------------------------------------------------------------------ */
/*  Save user data back into the .ecbmps file                         */
/* ------------------------------------------------------------------ */
static void save_userdata(void) {
    if (!g_book.raw || !g_book.dirty) return;

    FILE *fp = _wfopen(g_book.source_path, L"r+b");
    if (!fp) return;

    /* Seek to userdata section and rewrite */
    fseek(fp, (long)g_book.header.userdata_offset, SEEK_SET);
    write_u32(fp, ECBMPS_UD_MAGIC);

    /* Bookmarks */
    write_u16(fp, (uint16_t)g_book.bookmark_count);
    for (int i = 0; i < g_book.bookmark_count; i++) {
        write_u32(fp, g_book.bookmarks[i].page_index);
        write_u32(fp, g_book.bookmarks[i].scroll_offset);
        write_u8(fp, g_book.bookmarks[i].label_length);
        fwrite(g_book.bookmarks[i].label, 1, g_book.bookmarks[i].label_length, fp);
    }

    /* Highlights */
    write_u16(fp, (uint16_t)g_book.highlight_count);
    for (int i = 0; i < g_book.highlight_count; i++) {
        write_u32(fp, g_book.highlights[i].page_index);
        write_u32(fp, g_book.highlights[i].start_char);
        write_u32(fp, g_book.highlights[i].end_char);
        write_u32(fp, g_book.highlights[i].color_rgba);
    }

    fclose(fp);
    g_book.dirty = 0;
}

/* ------------------------------------------------------------------ */
/*  Get page text content (returns pointer into g_book.raw)           */
/* ------------------------------------------------------------------ */
static const char *page_text(int idx, uint32_t *out_len) {
    if (idx < 0 || idx >= (int)g_book.header.page_count) { *out_len = 0; return ""; }
    EcbmpsTocEntry *e = &g_book.toc[idx];
    uint8_t *base = g_book.raw + e->page_offset;
    if (e->page_type == ECBMPS_PAGE_TEXT || e->page_type == ECBMPS_PAGE_COMBINED) {
        uint32_t tlen;
        memcpy(&tlen, base, 4);
        *out_len = tlen;
        return (const char*)(base + 4);
    }
    *out_len = 0;
    return "";
}

/* ------------------------------------------------------------------ */
/*  Navigation                                                        */
/* ------------------------------------------------------------------ */
static void goto_page(int p) {
    if (!g_book.raw) return;
    if (p < 0) p = 0;
    if (p >= (int)g_book.header.page_count) p = (int)g_book.header.page_count - 1;
    g_book.current_page = p;
    InvalidateRect(g_hwndPage, NULL, TRUE);
    update_status();
}

/* ------------------------------------------------------------------ */
/*  Bookmark toggle                                                   */
/* ------------------------------------------------------------------ */
static void toggle_bookmark(void) {
    if (!g_book.raw) return;
    int pg = g_book.current_page;
    /* Check if already bookmarked */
    for (int i = 0; i < g_book.bookmark_count; i++) {
        if ((int)g_book.bookmarks[i].page_index == pg) {
            /* Remove */
            memmove(&g_book.bookmarks[i], &g_book.bookmarks[i + 1],
                (g_book.bookmark_count - i - 1) * sizeof(EcbmpsBookmark));
            g_book.bookmark_count--;
            g_book.dirty = 1;
            InvalidateRect(g_hwndPage, NULL, TRUE);
            return;
        }
    }
    /* Add */
    if (g_book.bookmark_count < ECBMPS_MAX_BOOKMARKS) {
        EcbmpsBookmark *bk = &g_book.bookmarks[g_book.bookmark_count++];
        bk->page_index = (uint32_t)pg;
        bk->scroll_offset = 0;
        bk->label_length = 0;
        bk->label[0] = '\0';
        g_book.dirty = 1;
        InvalidateRect(g_hwndPage, NULL, TRUE);
    }
}

static int is_bookmarked(int pg) {
    for (int i = 0; i < g_book.bookmark_count; i++)
        if ((int)g_book.bookmarks[i].page_index == pg) return 1;
    return 0;
}

/* ------------------------------------------------------------------ */
/*  Decode & draw an embedded image from page data                    */
/* ------------------------------------------------------------------ */
#ifndef STB_IMAGE_IMPLEMENTATION
  #include "stb_image.h"
#endif

static unsigned char *decode_image_wic(uint8_t *img_data, uint32_t img_size,
                                       int *out_w, int *out_h) {
    HRESULT hr;
    HGLOBAL hmem = NULL;
    IStream *stream = NULL;
    IWICImagingFactory *factory = NULL;
    IWICBitmapDecoder *decoder = NULL;
    IWICBitmapFrameDecode *frame = NULL;
    IWICFormatConverter *converter = NULL;
    unsigned char *pixels = NULL;
    UINT width = 0, height = 0;

    if (!img_data || img_size == 0) return NULL;

    hmem = GlobalAlloc(GMEM_MOVEABLE, img_size);
    if (!hmem) goto cleanup;

    void *dst = GlobalLock(hmem);
    if (!dst) goto cleanup;
    memcpy(dst, img_data, img_size);
    GlobalUnlock(hmem);

    hr = CreateStreamOnHGlobal(hmem, TRUE, &stream);
    if (FAILED(hr)) goto cleanup;
    hmem = NULL;

    hr = CoCreateInstance(&CLSID_WICImagingFactory, NULL, CLSCTX_INPROC_SERVER,
                          &IID_IWICImagingFactory, (void**)&factory);
    if (FAILED(hr)) goto cleanup;

    hr = factory->lpVtbl->CreateDecoderFromStream(
        factory, stream, NULL, WICDecodeMetadataCacheOnLoad, &decoder);
    if (FAILED(hr)) goto cleanup;

    hr = decoder->lpVtbl->GetFrame(decoder, 0, &frame);
    if (FAILED(hr)) goto cleanup;

    hr = factory->lpVtbl->CreateFormatConverter(factory, &converter);
    if (FAILED(hr)) goto cleanup;

    hr = converter->lpVtbl->Initialize(
        converter, (IWICBitmapSource*)frame, &GUID_WICPixelFormat32bppBGRA,
        WICBitmapDitherTypeNone, NULL, 0.0f, WICBitmapPaletteTypeCustom);
    if (FAILED(hr)) goto cleanup;

    hr = converter->lpVtbl->GetSize(converter, &width, &height);
    if (FAILED(hr) || width == 0 || height == 0) goto cleanup;

    pixels = (unsigned char*)malloc((size_t)width * (size_t)height * 4u);
    if (!pixels) goto cleanup;

    hr = converter->lpVtbl->CopyPixels(
        converter, NULL, width * 4u, width * height * 4u, pixels);
    if (FAILED(hr)) {
        free(pixels);
        pixels = NULL;
        goto cleanup;
    }

    *out_w = (int)width;
    *out_h = (int)height;

cleanup:
    if (converter) converter->lpVtbl->Release(converter);
    if (frame) frame->lpVtbl->Release(frame);
    if (decoder) decoder->lpVtbl->Release(decoder);
    if (factory) factory->lpVtbl->Release(factory);
    if (stream) stream->lpVtbl->Release(stream);
    if (hmem) GlobalFree(hmem);
    return pixels;
}

static void render_page_image(HDC hdc, int dx, int dy, int max_w, int max_h,
                              uint8_t *img_data, uint32_t img_size) {
    int iw = 0, ih = 0, channels = 0;
    int used_wic = 0;
    unsigned char *pixels = decode_image_wic(img_data, img_size, &iw, &ih);
    if (pixels) {
        used_wic = 1;
    } else {
        pixels = stbi_load_from_memory(img_data, (int)img_size,
                                       &iw, &ih, &channels, 4);
    }
    if (!pixels || iw <= 0 || ih <= 0) return;

    /* Compute aspect-fit scaling */
    float sx = (float)max_w / (float)iw;
    float sy = (float)max_h / (float)ih;
    float scale = (sx < sy) ? sx : sy;
    if (scale > 1.0f) scale = 1.0f;  /* don't upscale */
    int dw = (int)(iw * scale);
    int dh = (int)(ih * scale);
    int ox = dx + (max_w - dw) / 2;
    int oy = dy + (max_h - dh) / 2;

    if (!used_wic) {
        /* RGBA -> BGRA for GDI DIB */
        for (int p = 0; p < iw * ih; p++) {
            unsigned char tmp = pixels[p * 4 + 0];
            pixels[p * 4 + 0] = pixels[p * 4 + 2];
            pixels[p * 4 + 2] = tmp;
        }
    }

    BITMAPINFO bmi;
    memset(&bmi, 0, sizeof(bmi));
    bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    bmi.bmiHeader.biWidth = iw;
    bmi.bmiHeader.biHeight = -ih;       /* top-down */
    bmi.bmiHeader.biPlanes = 1;
    bmi.bmiHeader.biBitCount = 32;
    bmi.bmiHeader.biCompression = BI_RGB;

    SetStretchBltMode(hdc, HALFTONE);
    StretchDIBits(hdc, ox, oy, dw, dh,
                  0, 0, iw, ih,
                  pixels, &bmi, DIB_RGB_COLORS, SRCCOPY);

    if (used_wic) free(pixels);
    else stbi_image_free(pixels);
}

/* ------------------------------------------------------------------ */
/*  Render current page onto the page child window                    */
/* ------------------------------------------------------------------ */
static void render_page(HDC hdc, RECT *area) {
    COLORREF bg   = mode_bg[g_book.reading_mode];
    COLORREF text = mode_text[g_book.reading_mode];

    /* Try asset-based background for reading mode, fall back to solid fill */
    AssetSlot bg_slot = ASSET_ECBMPS_BG_LIGHT;
    if (g_book.reading_mode == MODE_DARK)  bg_slot = ASSET_ECBMPS_BG_DARK;
    if (g_book.reading_mode == MODE_SEPIA) bg_slot = ASSET_ECBMPS_BG_SEPIA;
    int aw = area->right - area->left, ah = area->bottom - area->top;
    if (!gui_draw_asset(hdc, bg_slot, area->left, area->top, aw, ah))
        gui_fill_rect(hdc, area->left, area->top, aw, ah, bg);

    if (!g_book.raw) {
        gui_draw_text(hdc, area->left + 40, area->top + 60,
            L"Drag & drop an .ecbmps file or use File \u2192 Open",
            GUI_ACCENT, g_fontUI);
        return;
    }

    int pg = g_book.current_page;
    int x = area->left + MARGIN;
    int y = area->top + MARGIN;
    int w = area->right - area->left - MARGIN * 2;

    /* Page number header */
    wchar_t hdr[128];
    wsprintfW(hdr, L"Page %d of %d", pg + 1, (int)g_book.header.page_count);
    gui_draw_text(hdc, x, y, hdr, GUI_ACCENT, g_fontUI);
    y += 28;

    /* Bookmark indicator */
    if (is_bookmarked(pg)) {
        gui_draw_text(hdc, area->right - MARGIN - 20, area->top + MARGIN,
            L"\u2764", GUI_BOOKMARK, g_fontPageBold);
    }

    /* Divider line */
    gui_fill_rect(hdc, x, y, w, 1, GUI_BORDER);
    y += 12;

    /* Page content */
    uint32_t tlen = 0;
    const char *txt = page_text(pg, &tlen);
    if (tlen > 0) {
        /* Convert UTF-8 to wide for rendering */
        int wlen = MultiByteToWideChar(CP_UTF8, 0, txt, (int)tlen, NULL, 0);
        wchar_t *wbuf = (wchar_t*)malloc((wlen + 1) * sizeof(wchar_t));
        MultiByteToWideChar(CP_UTF8, 0, txt, (int)tlen, wbuf, wlen);
        wbuf[wlen] = L'\0';

        /* Draw text with word-wrap using DrawText */
        HFONT old = (HFONT)SelectObject(hdc, g_fontPage);
        SetTextColor(hdc, text);
        SetBkMode(hdc, TRANSPARENT);
        RECT tr = { x, y, x + w, area->bottom - MARGIN };
        DrawTextW(hdc, wbuf, wlen, &tr, DT_LEFT | DT_WORDBREAK | DT_NOCLIP);
        SelectObject(hdc, old);

        /* Render highlights for this page */
        for (int i = 0; i < g_book.highlight_count; i++) {
            if ((int)g_book.highlights[i].page_index == pg) {
                /* Approximate highlight rectangle from char offsets */
                int hs = (int)g_book.highlights[i].start_char;
                int he = (int)g_book.highlights[i].end_char;
                if (hs < wlen && he <= wlen && hs < he) {
                    /* Measure text up to start and end to compute rects */
                    SIZE sz_start, sz_end;
                    GetTextExtentPoint32W(hdc, wbuf, hs, &sz_start);
                    GetTextExtentPoint32W(hdc, wbuf, he, &sz_end);
                    /* Simple single-line highlight overlay */
                    RECT hr;
                    hr.left   = x + sz_start.cx % w;
                    hr.top    = y + (sz_start.cx / w) * 20;
                    hr.right  = x + sz_end.cx % w;
                    hr.bottom = hr.top + 20;
                    /* Semi-transparent highlight */
                    HBRUSH hb = CreateSolidBrush(GUI_HIGHLIGHT);
                    int oldMode = SetBkMode(hdc, TRANSPARENT);
                    SetROP2(hdc, R2_MASKPEN);
                    FillRect(hdc, &hr, hb);
                    SetROP2(hdc, R2_COPYPEN);
                    SetBkMode(hdc, oldMode);
                    DeleteObject(hb);
                }
            }
        }
        free(wbuf);
    }

    /* Render embedded image for IMAGE or COMBINED pages */
    EcbmpsTocEntry *e = &g_book.toc[pg];
    uint8_t *base = g_book.raw + e->page_offset;
    if (e->page_type == 1 /* IMAGE */) {
        /* Layout: [u8 format][u32 w_hint][u32 h_hint][u32 data_size][bytes] */
        if (e->page_size >= 13) {
            uint32_t img_size;
            memcpy(&img_size, base + 9, 4);
            if (13 + img_size <= e->page_size) {
                int img_y = area->top + MARGIN + 40; /* below page header + divider */
                int img_max_w = area->right - area->left - MARGIN * 2;
                int img_max_h = area->bottom - img_y - MARGIN;
                if (img_max_w > 0 && img_max_h > 0) {
                    render_page_image(hdc, area->left + MARGIN, img_y,
                                      img_max_w, img_max_h, base + 13, img_size);
                }
            }
        }
    } else if (e->page_type == 2 /* COMBINED */ && (e->flags & 0x01)) {
        /* Layout: [u32 text_len][text][u8 img_count][u8 format][u16 x][u16 y][u16 w][u16 h][u32 data_size][bytes] */
        uint32_t text_len;
        memcpy(&text_len, base, 4);
        uint8_t *after_text = base + 4 + text_len;
        uint32_t remaining = e->page_size - 4 - text_len;
        if (remaining >= 1 && after_text[0] >= 1) {
            /* skip: img_count(1) + format(1) + layout_xywh(8) = 10 bytes, then u32 data_size */
            if (remaining >= 14) {
                uint32_t img_size;
                memcpy(&img_size, after_text + 10, 4);
                if (14 + img_size <= remaining) {
                    int img_y = y + 8; /* below where text ended */
                    int img_max_w = area->right - area->left - MARGIN * 2;
                    int img_max_h = area->bottom - img_y - MARGIN;
                    if (img_max_h < 200) img_max_h = 200;
                    if (img_max_w > 0 && img_max_h > 0) {
                        render_page_image(hdc, area->left + MARGIN, img_y,
                                          img_max_w, img_max_h, after_text + 14, img_size);
                    }
                }
            }
        }
    }
}

/* ------------------------------------------------------------------ */
/*  Status bar update                                                 */
/* ------------------------------------------------------------------ */
static void update_status(void) {
    if (!g_hwndStatus) return;
    wchar_t buf[256];
    if (g_book.raw) {
        wchar_t wtitle[128];
        MultiByteToWideChar(CP_UTF8, 0, g_book.title, -1, wtitle, 128);
        wsprintfW(buf, L"  %s  |  Page %d/%d  |  %d bookmarks  |  %s",
            wtitle,
            g_book.current_page + 1, (int)g_book.header.page_count,
            g_book.bookmark_count,
            g_book.reading_mode == MODE_LIGHT ? L"Light" :
            g_book.reading_mode == MODE_DARK  ? L"Dark" : L"Sepia");
    } else {
        wsprintfW(buf, L"  No file loaded");
    }
    SetWindowTextW(g_hwndStatus, buf);
}

/* ------------------------------------------------------------------ */
/*  Toolbar button drawing helper                                     */
/* ------------------------------------------------------------------ */
typedef struct { int id; const wchar_t *label; int x; int w; } ToolBtn;
static ToolBtn g_toolbar[] = {
    { IDC_BTN_PREV,      L"\u25C0 Prev",  4,   70 },
    { IDC_BTN_NEXT,      L"Next \u25B6",  78,  70 },
    { IDC_BTN_BOOKMARK,  L"\u2764 Mark",  160, 70 },
    { IDC_BTN_HIGHLIGHT, L"\u270E Hi",    234, 56 },
    { IDC_BTN_ZOOM_IN,   L"+",           300, 32 },
    { IDC_BTN_ZOOM_OUT,  L"\u2013",      336, 32 },
    { IDC_BTN_SETTINGS,  L"\u2699",      380, 32 },
    { IDC_BTN_ABOUT,     L"?",           416, 32 },
};
#define TOOLBAR_BTN_COUNT (sizeof(g_toolbar)/sizeof(g_toolbar[0]))

static int toolbar_hittest(int mx, int my) {
    if (my < 0 || my >= TOOLBAR_H) return -1;
    for (int i = 0; i < (int)TOOLBAR_BTN_COUNT; i++) {
        if (mx >= g_toolbar[i].x && mx < g_toolbar[i].x + g_toolbar[i].w)
            return g_toolbar[i].id;
    }
    return -1;
}

static void draw_toolbar(HDC hdc, int width) {
    /* Try asset-based titlebar background */
    if (!gui_draw_asset(hdc, ASSET_ECBMPS_TITLEBAR_BG, 0, 0, width, TOOLBAR_H))
        gui_fill_rect(hdc, 0, 0, width, TOOLBAR_H, GUI_BG_PANEL);
    gui_fill_rect(hdc, 0, TOOLBAR_H - 1, width, 1, GUI_BORDER);
    for (int i = 0; i < (int)TOOLBAR_BTN_COUNT; i++) {
        ToolBtn *b = &g_toolbar[i];
        gui_draw_rounded_rect(hdc, b->x, 4, b->w, TOOLBAR_H - 8, 6,
            GUI_BG_DARK, GUI_BORDER);
        gui_draw_text(hdc, b->x + 8, 10, b->label, GUI_TEXT_LIGHT, g_fontUI);
    }
    /* Frame corner overlays */
    gui_draw_asset(hdc, ASSET_ECBMPS_FRAME_TL, 0, 0, 16, 16);
    gui_draw_asset(hdc, ASSET_ECBMPS_FRAME_TR, width - 16, 0, 16, 16);
}

/* ------------------------------------------------------------------ */
/*  Open file dialog                                                  */
/* ------------------------------------------------------------------ */
static void open_file_dialog(HWND parent) {
    wchar_t path[MAX_PATH] = {0};
    OPENFILENAMEW ofn;
    memset(&ofn, 0, sizeof(ofn));
    ofn.lStructSize = sizeof(ofn);
    ofn.hwndOwner = parent;
    ofn.lpstrFilter = L"ECBMPS Files (*.ecbmps)\0*.ecbmps\0All Files (*.*)\0*.*\0";
    ofn.lpstrFile = path;
    ofn.nMaxFile = MAX_PATH;
    ofn.Flags = OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST;
    if (GetOpenFileNameW(&ofn)) {
        if (load_ecbmps(path)) {
            wchar_t cap[512];
            wchar_t wtitle[256];
            MultiByteToWideChar(CP_UTF8, 0, g_book.title, -1, wtitle, 256);
            wsprintfW(cap, L"%s \u2014 %s", wtitle, APP_TITLE);
            SetWindowTextW(g_hwndMain, cap);
            goto_page(0);
        } else {
            MessageBoxW(parent, L"Failed to open file.\nPlease select a valid .ecbmps file.",
                APP_TITLE, MB_ICONERROR);
        }
    }
}

/* ------------------------------------------------------------------ */
/*  About popup                                                       */
/* ------------------------------------------------------------------ */
static void show_about(HWND parent) {
    MessageBoxW(parent,
        L"drIpTECH ECBMPS Reader v1.0\n\n"
        L"Electronic Colour Book Media Playback Shell\n\n"
        L"Page navigation: Left/Right arrows or toolbar\n"
        L"Bookmark: B key or toolbar heart button\n"
        L"Reading mode: M key cycles Light/Dark/Sepia\n"
        L"Highlight: H key toggles highlight brush\n\n"
        L"\u00A9 2026 drIpTECH",
        APP_TITLE, MB_ICONINFORMATION);
}

/* ------------------------------------------------------------------ */
/*  Bookmark list popup                                               */
/* ------------------------------------------------------------------ */
static void show_bookmark_list(HWND parent) {
    if (g_book.bookmark_count == 0) {
        MessageBoxW(parent, L"No bookmarks set.\nPress B or the heart button to bookmark a page.",
            L"Bookmarks", MB_ICONINFORMATION);
        return;
    }
    wchar_t buf[4096] = {0};
    wchar_t line[128];
    for (int i = 0; i < g_book.bookmark_count; i++) {
        wsprintfW(line, L"  \u2764 Page %d\n", (int)g_book.bookmarks[i].page_index + 1);
        wcscat_s(buf, 4096, line);
    }
    MessageBoxW(parent, buf, L"Bookmarks", MB_ICONINFORMATION);
}

/* ------------------------------------------------------------------ */
/*  Page child window proc                                            */
/* ------------------------------------------------------------------ */
static LRESULT CALLBACK PageWndProc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp) {
    switch (msg) {
    case WM_PAINT: {
        PAINTSTRUCT ps;
        HDC hdc = BeginPaint(hwnd, &ps);
        RECT rc;
        GetClientRect(hwnd, &rc);
        /* Double-buffer */
        HDC mem = CreateCompatibleDC(hdc);
        HBITMAP bmp = CreateCompatibleBitmap(hdc, rc.right, rc.bottom);
        HBITMAP oldBmp = (HBITMAP)SelectObject(mem, bmp);
        render_page(mem, &rc);
        BitBlt(hdc, 0, 0, rc.right, rc.bottom, mem, 0, 0, SRCCOPY);
        SelectObject(mem, oldBmp);
        DeleteObject(bmp);
        DeleteDC(mem);
        EndPaint(hwnd, &ps);
        return 0;
    }
    case WM_LBUTTONDOWN:
        if (g_highlight_mode && g_book.raw) {
            g_highlight_start.x = GET_X_LPARAM(lp);
            g_highlight_start.y = GET_Y_LPARAM(lp);
        }
        return 0;
    case WM_LBUTTONUP:
        if (g_highlight_mode && g_book.raw && g_book.highlight_count < ECBMPS_MAX_HIGHLIGHTS) {
            /* Approximate character offsets from pixel positions */
            int endX = GET_X_LPARAM(lp);
            EcbmpsHighlight *hl = &g_book.highlights[g_book.highlight_count];
            hl->page_index = (uint32_t)g_book.current_page;
            /* Rough character estimate: ~8px per char at default zoom */
            int cw = (int)(8.0f * g_book.zoom);
            if (cw < 1) cw = 1;
            hl->start_char = (uint32_t)((g_highlight_start.x - MARGIN) / cw);
            hl->end_char   = (uint32_t)((endX - MARGIN) / cw);
            if (hl->end_char > hl->start_char) {
                hl->color_rgba = 0xFFDC5000u; /* yellow-ish */
                g_book.highlight_count++;
                g_book.dirty = 1;
                InvalidateRect(hwnd, NULL, TRUE);
            }
        }
        return 0;
    case WM_MOUSEWHEEL: {
        int delta = GET_WHEEL_DELTA_WPARAM(wp);
        if (GetKeyState(VK_CONTROL) & 0x8000) {
            /* Zoom */
            g_book.zoom += (delta > 0) ? 0.1f : -0.1f;
            if (g_book.zoom < 0.5f) g_book.zoom = 0.5f;
            if (g_book.zoom > 3.0f) g_book.zoom = 3.0f;
            InvalidateRect(hwnd, NULL, TRUE);
        } else {
            /* Page navigation */
            goto_page(g_book.current_page + (delta > 0 ? -1 : 1));
        }
        return 0;
    }
    }
    return DefWindowProcW(hwnd, msg, wp, lp);
}

/* ------------------------------------------------------------------ */
/*  Main window proc                                                  */
/* ------------------------------------------------------------------ */
static LRESULT CALLBACK MainWndProc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp) {
    switch (msg) {
    case WM_CREATE: {
        /* Create page child */
        RECT rc;
        GetClientRect(hwnd, &rc);
        g_hwndPage = CreateWindowExW(0, CLS_PAGE, L"", WS_CHILD | WS_VISIBLE,
            0, TOOLBAR_H, rc.right, rc.bottom - TOOLBAR_H - STATUSBAR_H,
            hwnd, NULL, GetModuleHandle(NULL), NULL);
        g_hwndStatus = CreateWindowExW(0, L"STATIC", L"  No file loaded",
            WS_CHILD | WS_VISIBLE | SS_LEFT,
            0, rc.bottom - STATUSBAR_H, rc.right, STATUSBAR_H,
            hwnd, (HMENU)IDC_PAGE_LABEL, GetModuleHandle(NULL), NULL);
        return 0;
    }
    case WM_SIZE: {
        int w = LOWORD(lp), h = HIWORD(lp);
        MoveWindow(g_hwndPage, 0, TOOLBAR_H, w, h - TOOLBAR_H - STATUSBAR_H, TRUE);
        MoveWindow(g_hwndStatus, 0, h - STATUSBAR_H, w, STATUSBAR_H, TRUE);
        InvalidateRect(hwnd, NULL, TRUE);
        return 0;
    }
    case WM_PAINT: {
        PAINTSTRUCT ps;
        HDC hdc = BeginPaint(hwnd, &ps);
        RECT rc;
        GetClientRect(hwnd, &rc);
        /* Draw toolbar */
        draw_toolbar(hdc, rc.right);
        /* Status bar bg */
        gui_fill_rect(hdc, 0, rc.bottom - STATUSBAR_H, rc.right, STATUSBAR_H, GUI_BG_PANEL);
        gui_fill_rect(hdc, 0, rc.bottom - STATUSBAR_H, rc.right, 1, GUI_BORDER);
        /* Bottom frame corners */
        gui_draw_asset(hdc, ASSET_ECBMPS_FRAME_BL, 0, rc.bottom - 16, 16, 16);
        gui_draw_asset(hdc, ASSET_ECBMPS_FRAME_BR, rc.right - 16, rc.bottom - 16, 16, 16);
        EndPaint(hwnd, &ps);
        return 0;
    }
    case WM_LBUTTONDOWN: {
        int mx = GET_X_LPARAM(lp), my = GET_Y_LPARAM(lp);
        int btn = toolbar_hittest(mx, my);
        switch (btn) {
        case IDC_BTN_PREV:      goto_page(g_book.current_page - 1); break;
        case IDC_BTN_NEXT:      goto_page(g_book.current_page + 1); break;
        case IDC_BTN_BOOKMARK:  toggle_bookmark(); update_status(); break;
        case IDC_BTN_HIGHLIGHT: g_highlight_mode = !g_highlight_mode; break;
        case IDC_BTN_ZOOM_IN:
            g_book.zoom += 0.1f;
            if (g_book.zoom > 3.0f) g_book.zoom = 3.0f;
            InvalidateRect(g_hwndPage, NULL, TRUE);
            break;
        case IDC_BTN_ZOOM_OUT:
            g_book.zoom -= 0.1f;
            if (g_book.zoom < 0.5f) g_book.zoom = 0.5f;
            InvalidateRect(g_hwndPage, NULL, TRUE);
            break;
        case IDC_BTN_SETTINGS:
            g_book.reading_mode = (g_book.reading_mode + 1) % MODE_COUNT;
            InvalidateRect(g_hwndPage, NULL, TRUE);
            update_status();
            break;
        case IDC_BTN_ABOUT: show_about(hwnd); break;
        }
        return 0;
    }
    case WM_KEYDOWN:
        switch (wp) {
        case VK_LEFT:  case VK_PRIOR: goto_page(g_book.current_page - 1); break;
        case VK_RIGHT: case VK_NEXT:  goto_page(g_book.current_page + 1); break;
        case VK_HOME:  goto_page(0); break;
        case VK_END:   goto_page((int)g_book.header.page_count - 1); break;
        case 'B': toggle_bookmark(); update_status(); break;
        case 'M':
            g_book.reading_mode = (g_book.reading_mode + 1) % MODE_COUNT;
            InvalidateRect(g_hwndPage, NULL, TRUE);
            update_status();
            break;
        case 'H': g_highlight_mode = !g_highlight_mode; break;
        case 'L': show_bookmark_list(hwnd); break;
        case 'O':
            if (GetKeyState(VK_CONTROL) & 0x8000) open_file_dialog(hwnd);
            break;
        }
        return 0;
    case WM_DROPFILES: {
        wchar_t path[MAX_PATH];
        DragQueryFileW((HDROP)wp, 0, path, MAX_PATH);
        DragFinish((HDROP)wp);
        if (load_ecbmps(path)) {
            wchar_t cap[512];
            wchar_t wtitle[256];
            MultiByteToWideChar(CP_UTF8, 0, g_book.title, -1, wtitle, 256);
            wsprintfW(cap, L"%s \u2014 %s", wtitle, APP_TITLE);
            SetWindowTextW(hwnd, cap);
            goto_page(0);
        }
        return 0;
    }
    case WM_CLOSE:
        if (g_book.dirty) save_userdata();
        DestroyWindow(hwnd);
        return 0;
    case WM_TIMER:
        if (wp == 999 && g_splash_shown) {
            KillTimer(hwnd, 999);
            g_splash_shown = 0;
            InvalidateRect(g_hwndPage, NULL, TRUE);
        }
        if (wp == CTRL_TIMER_ID) {
            controller_poll();
            /* LT = previous page, RT = next page */
            if (g_controller.page_prev_edge)
                goto_page(g_book.current_page - 1);
            if (g_controller.page_next_edge)
                goto_page(g_book.current_page + 1);
        }
        return 0;
    case WM_DESTROY:
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProcW(hwnd, msg, wp, lp);
}

/* ------------------------------------------------------------------ */
/*  Entry point                                                       */
/* ------------------------------------------------------------------ */
int WINAPI wWinMain(HINSTANCE hInst, HINSTANCE hPrev, LPWSTR cmdLine, int showCmd) {
    (void)hPrev;
    CoInitializeEx(NULL, COINIT_APARTMENTTHREADED);

    /* Discover assets directory relative to executable */
    {
        char exePath[MAX_PATH];
        GetModuleFileNameA(NULL, exePath, MAX_PATH);
        char *last = strrchr(exePath, '\\');
        if (last) *last = '\0';
        char assetsDir[MAX_PATH + 32];
        snprintf(assetsDir, sizeof(assetsDir), "%s\\assets\\recraft", exePath);
        gui_assets_init(assetsDir);
    }

    /* Fonts */
    g_fontUI = CreateFontW(-14, 0, 0, 0, FW_SEMIBOLD, 0, 0, 0,
        DEFAULT_CHARSET, 0, 0, CLEARTYPE_QUALITY, DEFAULT_PITCH, L"Segoe UI");
    g_fontPage = CreateFontW(-16, 0, 0, 0, FW_NORMAL, 0, 0, 0,
        DEFAULT_CHARSET, 0, 0, CLEARTYPE_QUALITY, DEFAULT_PITCH, L"Georgia");
    g_fontPageBold = CreateFontW(-16, 0, 0, 0, FW_BOLD, 0, 0, 0,
        DEFAULT_CHARSET, 0, 0, CLEARTYPE_QUALITY, DEFAULT_PITCH, L"Georgia");

    /* Register page child class */
    WNDCLASSEXW wcp = {0};
    wcp.cbSize = sizeof(wcp);
    wcp.lpfnWndProc = PageWndProc;
    wcp.hInstance = hInst;
    wcp.hCursor = LoadCursorW(NULL, IDC_ARROW);
    wcp.lpszClassName = CLS_PAGE;
    RegisterClassExW(&wcp);

    /* Register main class */
    WNDCLASSEXW wc = {0};
    wc.cbSize = sizeof(wc);
    wc.lpfnWndProc = MainWndProc;
    wc.hInstance = hInst;
    wc.hCursor = LoadCursorW(NULL, IDC_ARROW);
    wc.hbrBackground = CreateSolidBrush(GUI_BG_DARK);
    wc.lpszClassName = CLS_MAIN;
    wc.hIcon = LoadIconW(NULL, IDI_APPLICATION);
    RegisterClassExW(&wc);

    g_hwndMain = CreateWindowExW(
        WS_EX_ACCEPTFILES,
        CLS_MAIN, APP_TITLE,
        WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT, 800, 640,
        NULL, NULL, hInst, NULL);

    ShowWindow(g_hwndMain, showCmd);
    UpdateWindow(g_hwndMain);

    /* Splash screen: paint asset over page area for a brief moment */
    if (gui_get_asset(ASSET_SPLASH_ECBMPS)) {
        HDC hdc = GetDC(g_hwndPage);
        RECT prc;
        GetClientRect(g_hwndPage, &prc);
        gui_draw_asset(hdc, ASSET_SPLASH_ECBMPS, 0, 0, prc.right, prc.bottom);
        ReleaseDC(g_hwndPage, hdc);
        g_splash_shown = 1;
        g_splash_time = GetTickCount();
        SetTimer(g_hwndMain, 999, SPLASH_DURATION_MS, NULL);
    }

    /* Start controller polling timer (LT/RT page navigation) */
    SetTimer(g_hwndMain, CTRL_TIMER_ID, CTRL_POLL_MS, NULL);

    /* If launched with a file argument, open it */
    if (cmdLine && cmdLine[0]) {
        /* Strip surrounding quotes if present */
        wchar_t path[MAX_PATH];
        wcscpy_s(path, MAX_PATH, cmdLine);
        if (path[0] == L'"') {
            memmove(path, path + 1, (wcslen(path)) * sizeof(wchar_t));
            wchar_t *q = wcsrchr(path, L'"');
            if (q) *q = L'\0';
        }
        if (load_ecbmps(path)) {
            wchar_t cap[512];
            wchar_t wtitle[256];
            MultiByteToWideChar(CP_UTF8, 0, g_book.title, -1, wtitle, 256);
            wsprintfW(cap, L"%s \u2014 %s", wtitle, APP_TITLE);
            SetWindowTextW(g_hwndMain, cap);
            goto_page(0);
        }
    }

    MSG msg;
    while (GetMessageW(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }

    if (g_book.dirty) save_userdata();
    if (g_book.raw) { free(g_book.raw); free(g_book.toc); }
    KillTimer(g_hwndMain, CTRL_TIMER_ID);
    gui_assets_cleanup();
    DeleteObject(g_fontUI);
    DeleteObject(g_fontPage);
    DeleteObject(g_fontPageBold);
    CoUninitialize();
    return (int)msg.wParam;
}
