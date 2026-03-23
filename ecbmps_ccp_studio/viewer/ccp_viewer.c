/* ccp_viewer.c — Win32 custom-shell viewer for .ccp interactive media books
 * ClipConceptBook runtime/reader with interactive regions
 * Build: cl /W4 /O2 ccp_viewer.c /link user32.lib gdi32.lib comctl32.lib comdlg32.lib shell32.lib
 *   or:  gcc -O2 ccp_viewer.c -o ccp_viewer.exe -lgdi32 -lcomctl32 -lcomdlg32 -lshell32 -mwindows
 */

#include "../compiler/common.h"
#include "gui_common.h"
#include "ccp_gameplay.h"
#include "controller_input.h"
#include "gui_assets.h"

/* ------------------------------------------------------------------ */
/*  Constants                                                         */
/* ------------------------------------------------------------------ */
#define APP_TITLE   L"drIpTECH \u00b7 CCP Interactive Viewer"
#define CLS_MAIN    L"CcpViewerMain"
#define CLS_STAGE   L"CcpStageView"
#define TOOLBAR_H   44
#define STATUSBAR_H 24
#define SIDEBAR_W   180
#define MAX_REGIONS 128
#define MAX_PAGES   512
#define MAX_MANIFEST (1 << 20)  /* 1 MB manifest cap */
#define GAMEPLAY_TIMER_ID  1001
#define GAMEPLAY_TICK_MS   16     /* ~60fps gameplay/controller poll */

/* ------------------------------------------------------------------ */
/*  Interactive region (parsed from manifest JSON)                    */
/* ------------------------------------------------------------------ */
typedef struct {
    int page;
    int x, y, w, h;
    int action;       /* 0=goto_page, 1=play_anim, 2=show_popup, 3=toggle_layer */
    int target;       /* page index / anim id / popup id / layer id */
    char label[64];
    int hover;        /* runtime: mouse hover state */
} InteractiveRegion;

/* ------------------------------------------------------------------ */
/*  Book state                                                        */
/* ------------------------------------------------------------------ */
typedef struct {
    uint8_t *raw;
    long     raw_size;
    CcpHeader header;

    char *manifest_json;
    int   manifest_len;

    int page_count;
    int current_page;

    char page_titles[MAX_PAGES][128];
    InteractiveRegion regions[MAX_REGIONS];
    int region_count;

    wchar_t source_path[MAX_PATH];
    int     playing_anim;
    int     anim_frame;

    /* Gameplay VM (v3 only) */
    int      has_gameplay;
    uint8_t *gameplay_data;
    uint32_t gameplay_size;
    GplyVM   vm;
} CcpState;

static CcpState g_ccp;

/* ------------------------------------------------------------------ */
/*  GUI state                                                         */
/* ------------------------------------------------------------------ */
static HWND  g_hwndMain;
static HWND  g_hwndStage;     /* interactive canvas */
static HWND  g_hwndSidebar;   /* page list sidebar */
static HWND  g_hwndStatus;
static HFONT g_fontUI;
static HFONT g_fontStage;
static HFONT g_fontSmall;
static int   g_show_sidebar = 1;
static int   g_show_regions = 1; /* overlay clickable regions */
static int   g_splash_shown = 0;
#define SPLASH_DURATION_MS 2000

/* ------------------------------------------------------------------ */
/*  Forward declarations                                              */
/* ------------------------------------------------------------------ */
static int  load_ccp(const wchar_t *path);
static void parse_manifest(void);
static void render_stage(HDC hdc, RECT *area);
static void draw_region_overlay(HDC hdc, InteractiveRegion *r);
static void update_status(void);
static void open_file_dialog(HWND parent);
static void goto_page(int p);
static void handle_region_click(InteractiveRegion *r);
static void show_about(HWND parent);

/* ------------------------------------------------------------------ */
/*  Minimal JSON string extractor (no dependency)                     */
/* ------------------------------------------------------------------ */
static const char *json_find_key(const char *json, const char *key) {
    char search[128];
    int len = snprintf(search, sizeof(search), "\"%s\"", key);
    if (len < 0 || len >= (int)sizeof(search)) return NULL;
    const char *found = strstr(json, search);
    if (!found) return NULL;
    found += strlen(search);
    while (*found == ' ' || *found == ':' || *found == '\t' || *found == '\n' || *found == '\r')
        found++;
    return found;
}

static int json_extract_string(const char *pos, char *out, int max) {
    if (!pos || *pos != '"') return 0;
    pos++;
    int i = 0;
    while (*pos && *pos != '"' && i < max - 1)
        out[i++] = *pos++;
    out[i] = '\0';
    return i;
}

static int json_extract_int(const char *pos) {
    if (!pos) return 0;
    return atoi(pos);
}

/* ------------------------------------------------------------------ */
/*  Load & parse .ccp file                                            */
/* ------------------------------------------------------------------ */
static int load_ccp(const wchar_t *path) {
    FILE *fp = _wfopen(path, L"rb");
    if (!fp) return 0;

    if (g_ccp.raw) free(g_ccp.raw);
    if (g_ccp.manifest_json) free(g_ccp.manifest_json);
    if (g_ccp.gameplay_data) free(g_ccp.gameplay_data);
    memset(&g_ccp, 0, sizeof(g_ccp));
    wcscpy_s(g_ccp.source_path, MAX_PATH, path);

    fseek(fp, 0, SEEK_END);
    g_ccp.raw_size = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    g_ccp.raw = (uint8_t*)malloc((size_t)g_ccp.raw_size);
    fread(g_ccp.raw, 1, (size_t)g_ccp.raw_size, fp);
    fseek(fp, 0, SEEK_SET);

    /* Read base header fields (common to v2 and v3) */
    g_ccp.header.magic           = read_u32(fp);
    g_ccp.header.version         = read_u32(fp);
    g_ccp.header.page_count      = read_u32(fp);
    g_ccp.header.manifest_size   = read_u64(fp);
    g_ccp.header.source_zip_size = read_u64(fp);

    if (g_ccp.header.magic != CCP_MAGIC) {
        fclose(fp); free(g_ccp.raw); g_ccp.raw = NULL;
        return 0;
    }

    /* V3: read gameplay_size field */
    uint64_t gameplay_file_size = 0;
    if (g_ccp.header.version >= CCP_VERSION_V3) {
        gameplay_file_size = read_u64(fp);
    }

    g_ccp.page_count = (int)g_ccp.header.page_count;
    if (g_ccp.page_count > MAX_PAGES) g_ccp.page_count = MAX_PAGES;

    /* Read manifest JSON */
    int mlen = (int)g_ccp.header.manifest_size;
    if (mlen > MAX_MANIFEST) mlen = MAX_MANIFEST;
    g_ccp.manifest_json = (char*)malloc(mlen + 1);
    fread(g_ccp.manifest_json, 1, mlen, fp);
    g_ccp.manifest_json[mlen] = '\0';
    g_ccp.manifest_len = mlen;

    /* Skip source ZIP to reach gameplay section */
    if (g_ccp.header.source_zip_size > 0) {
        fseek(fp, (long)g_ccp.header.source_zip_size, SEEK_CUR);
    }

    /* V3: Load gameplay section */
    if (gameplay_file_size > 0) {
        g_ccp.gameplay_size = (uint32_t)gameplay_file_size;
        g_ccp.gameplay_data = (uint8_t*)malloc((size_t)gameplay_file_size);
        fread(g_ccp.gameplay_data, 1, (size_t)gameplay_file_size, fp);
        if (gply_vm_init(&g_ccp.vm, g_ccp.gameplay_data, g_ccp.gameplay_size)) {
            g_ccp.has_gameplay = 1;
        }
    }

    fclose(fp);

    parse_manifest();
    g_ccp.current_page = 0;

    /* Initialize gameplay for page 0 */
    if (g_ccp.has_gameplay) {
        gply_vm_set_page(&g_ccp.vm, 0);
    }

    return 1;
}

/* ------------------------------------------------------------------ */
/*  Parse manifest JSON for page titles and interactive regions       */
/* ------------------------------------------------------------------ */
static void parse_manifest(void) {
    if (!g_ccp.manifest_json) return;
    g_ccp.region_count = 0;

    /* Extract page titles */
    const char *pages = json_find_key(g_ccp.manifest_json, "pages");
    if (pages && *pages == '[') {
        pages++;
        int pg = 0;
        while (pg < g_ccp.page_count && *pages) {
            const char *title_pos = json_find_key(pages, "title");
            if (title_pos) {
                json_extract_string(title_pos, g_ccp.page_titles[pg], 128);
            } else {
                snprintf(g_ccp.page_titles[pg], 128, "Page %d", pg + 1);
            }

            /* Look for interactive_regions array */
            const char *rgn_pos = json_find_key(pages, "interactive_regions");
            if (rgn_pos && *rgn_pos == '[') {
                rgn_pos++;
                while (*rgn_pos && *rgn_pos != ']' && g_ccp.region_count < MAX_REGIONS) {
                    InteractiveRegion *r = &g_ccp.regions[g_ccp.region_count];
                    r->page = pg;
                    r->hover = 0;

                    const char *xp = json_find_key(rgn_pos, "x");
                    r->x = json_extract_int(xp);
                    const char *yp = json_find_key(rgn_pos, "y");
                    r->y = json_extract_int(yp);
                    const char *wp = json_find_key(rgn_pos, "w");
                    r->w = json_extract_int(wp);
                    const char *hp = json_find_key(rgn_pos, "h");
                    r->h = json_extract_int(hp);

                    const char *act = json_find_key(rgn_pos, "action");
                    if (act) {
                        char abuf[32];
                        json_extract_string(act, abuf, 32);
                        if (strcmp(abuf, "goto_page") == 0) r->action = 0;
                        else if (strcmp(abuf, "play_anim") == 0) r->action = 1;
                        else if (strcmp(abuf, "show_popup") == 0) r->action = 2;
                        else if (strcmp(abuf, "toggle_layer") == 0) r->action = 3;
                    }
                    const char *tgt = json_find_key(rgn_pos, "target");
                    r->target = json_extract_int(tgt);

                    const char *lbl = json_find_key(rgn_pos, "label");
                    if (lbl) json_extract_string(lbl, r->label, 64);

                    g_ccp.region_count++;

                    /* Skip to next region object */
                    const char *next_brace = strchr(rgn_pos, '}');
                    if (next_brace) rgn_pos = next_brace + 1;
                    else break;
                }
            }

            /* Advance to next page object */
            const char *next = strchr(pages, '}');
            if (next) pages = next + 1;
            else break;
            pg++;
        }
    }

    /* Default page titles for any remaining */
    for (int i = 0; i < g_ccp.page_count; i++) {
        if (g_ccp.page_titles[i][0] == '\0')
            snprintf(g_ccp.page_titles[i], 128, "Page %d", i + 1);
    }
}

/* ------------------------------------------------------------------ */
/*  Navigation                                                        */
/* ------------------------------------------------------------------ */
static void goto_page(int p) {
    if (!g_ccp.raw) return;
    if (p < 0) p = 0;
    if (p >= g_ccp.page_count) p = g_ccp.page_count - 1;
    g_ccp.current_page = p;
    g_ccp.playing_anim = 0;
    g_ccp.anim_frame = 0;

    /* Sync gameplay VM with page change */
    if (g_ccp.has_gameplay) {
        gply_vm_set_page(&g_ccp.vm, p);
    }

    InvalidateRect(g_hwndStage, NULL, TRUE);
    if (g_hwndSidebar) InvalidateRect(g_hwndSidebar, NULL, TRUE);
    update_status();
}

/* ------------------------------------------------------------------ */
/*  Region click handler                                              */
/* ------------------------------------------------------------------ */
static void handle_region_click(InteractiveRegion *r) {
    switch (r->action) {
    case 0: /* goto_page */
        goto_page(r->target);
        break;
    case 1: /* play_anim */
        g_ccp.playing_anim = 1;
        g_ccp.anim_frame = 0;
        /* In a full implementation an animation timer would drive frames */
        break;
    case 2: { /* show_popup */
        wchar_t wlabel[128];
        MultiByteToWideChar(CP_UTF8, 0, r->label, -1, wlabel, 128);
        MessageBoxW(g_hwndMain, wlabel, L"Interactive Popup", MB_ICONINFORMATION);
        break;
    }
    case 3: /* toggle_layer — placeholder */
        break;
    }
}

/* ------------------------------------------------------------------ */
/*  Render interactive region overlay                                 */
/* ------------------------------------------------------------------ */
static void draw_region_overlay(HDC hdc, InteractiveRegion *r) {
    COLORREF fill = r->hover ? GUI_ACCENT_HOT : GUI_ACCENT;
    /* Semi-transparent region rectangle */
    HBRUSH brush = CreateSolidBrush(fill);
    RECT rc = { r->x, r->y, r->x + r->w, r->y + r->h };
    FrameRect(hdc, &rc, brush);
    /* Draw inner border for visibility */
    RECT inner = { r->x + 1, r->y + 1, r->x + r->w - 1, r->y + r->h - 1 };
    FrameRect(hdc, &inner, brush);
    DeleteObject(brush);

    /* Label */
    if (r->label[0]) {
        wchar_t wlabel[64];
        MultiByteToWideChar(CP_UTF8, 0, r->label, -1, wlabel, 64);
        gui_draw_text(hdc, r->x + 4, r->y + 2, wlabel,
            r->hover ? RGB(255,255,255) : GUI_ACCENT, g_fontSmall);
    }

    /* Action icon */
    const wchar_t *icon = L"\u25B6"; /* play */
    if (r->action == 0) icon = L"\u2192";      /* arrow for goto */
    else if (r->action == 2) icon = L"\u2139";  /* info for popup */
    else if (r->action == 3) icon = L"\u25A0";  /* square for layer */
    gui_draw_text(hdc, r->x + r->w - 18, r->y + 2, icon, fill, g_fontSmall);
}

/* ------------------------------------------------------------------ */
/*  Render stage (page canvas)                                        */
/* ------------------------------------------------------------------ */
static void render_stage(HDC hdc, RECT *area) {
    int w = area->right - area->left;
    int h = area->bottom - area->top;

    /* Dark canvas background */
    gui_fill_rect(hdc, area->left, area->top, w, h, GUI_BG_DARK);

    if (!g_ccp.raw) {
        gui_draw_text(hdc, area->left + 40, area->top + 60,
            L"Drag & drop a .ccp file or use Ctrl+O",
            GUI_ACCENT, g_fontUI);
        return;
    }

    int pg = g_ccp.current_page;

    /* Page area (centered card) */
    int card_w = w - 48;
    int card_h = h - 48;
    int cx = area->left + 24;
    int cy = area->top + 24;
    gui_draw_rounded_rect(hdc, cx, cy, card_w, card_h, 8, GUI_BG_PAGE, GUI_BORDER);

    /* Page title */
    wchar_t wtitle[128];
    MultiByteToWideChar(CP_UTF8, 0, g_ccp.page_titles[pg], -1, wtitle, 128);
    gui_draw_text(hdc, cx + 16, cy + 12, wtitle, GUI_ACCENT, g_fontUI);

    /* Page number */
    wchar_t pnum[64];
    wsprintfW(pnum, L"%d / %d", pg + 1, g_ccp.page_count);
    gui_draw_text(hdc, cx + card_w - 80, cy + 12, pnum, GUI_BORDER, g_fontSmall);

    /* Separator */
    gui_fill_rect(hdc, cx + 12, cy + 36, card_w - 24, 1, GUI_BORDER);

    /* Content area (placeholder — real impl would render page assets) */
    gui_draw_text(hdc, cx + 16, cy + 48,
        L"[Interactive content area]", GUI_TEXT_DARK, g_fontStage);

    /* Draw interactive region overlays for this page */
    if (g_show_regions) {
        for (int i = 0; i < g_ccp.region_count; i++) {
            if (g_ccp.regions[i].page == pg) {
                InteractiveRegion *r = &g_ccp.regions[i];
                /* Offset regions by card position */
                InteractiveRegion shifted = *r;
                shifted.x += cx;
                shifted.y += cy + 40; /* below title area */
                draw_region_overlay(hdc, &shifted);
            }
        }
    }

    /* Animation indicator */
    if (g_ccp.playing_anim) {
        gui_draw_rounded_rect(hdc, cx + card_w - 120, cy + card_h - 36, 108, 28, 6,
            GUI_ACCENT, GUI_ACCENT);
        gui_draw_text(hdc, cx + card_w - 112, cy + card_h - 32,
            L"\u25B6 Playing...", RGB(255,255,255), g_fontSmall);
    }

    /* Gameplay entity rendering (v3 with GPLY) */
    if (g_ccp.has_gameplay) {
        for (int i = 0; i < g_ccp.vm.instance_count; i++) {
            GplyEntityInstance *inst = &g_ccp.vm.instances[i];
            if (!inst->active || !inst->visible) continue;

            const GplyEntityDef *def = &g_ccp.vm.entity_defs[inst->def_id];
            int ex = cx + (int)inst->x;
            int ey = cy + 40 + (int)inst->y;
            int ew = def->width > 0 ? def->width : 32;
            int eh = def->height > 0 ? def->height : 32;

            /* Entity body (colored rectangle placeholder for sprite) */
            COLORREF entColor = RGB(80, 180, 120);
            gui_draw_rounded_rect(hdc, ex, ey, ew, eh, 4, entColor, RGB(60, 140, 90));

            /* Entity name label */
            const char *ename = gply_vm_string(&g_ccp.vm, def->name_offset);
            if (ename[0]) {
                wchar_t wname[64];
                MultiByteToWideChar(CP_UTF8, 0, ename, -1, wname, 64);
                gui_draw_text(hdc, ex + 2, ey + 2, wname, RGB(255,255,255), g_fontSmall);
            }

            /* Draw hitbox outlines for this entity */
            for (int h = 0; h < g_ccp.vm.header->hitbox_def_count; h++) {
                const GplyHitboxDef *hb = &g_ccp.vm.hitbox_defs[h];
                if (hb->entity_def_id != inst->def_id) continue;
                if (hb->frame_index != 0xFFFF && hb->frame_index != (uint16_t)inst->current_frame)
                    continue;
                int hx = ex + hb->offset_x;
                int hy = ey + hb->offset_y;
                COLORREF hcol;
                switch (hb->kind) {
                    case 0: hcol = RGB(60, 60, 255); break;   /* solid: blue */
                    case 1: hcol = RGB(255, 200, 0); break;   /* trigger: yellow */
                    case 2: hcol = RGB(255, 60, 60); break;   /* hurtbox: red */
                    case 3: hcol = RGB(0, 200, 255); break;   /* button: cyan */
                    default: hcol = GUI_BORDER; break;
                }
                gui_draw_frame(hdc, hx, hy, hb->width, hb->height, hcol);
            }

            /* Animation frame indicator */
            if (inst->anim_playing) {
                wchar_t fbuf[16];
                wsprintfW(fbuf, L"F%d", inst->current_frame);
                gui_draw_text(hdc, ex + ew - 24, ey + eh - 14, fbuf,
                    RGB(255, 255, 0), g_fontSmall);
            }
        }

        /* Gameplay HUD — controller connected indicator */
        if (g_controller.connected) {
            gui_draw_text(hdc, cx + card_w - 100, cy + card_h - 16,
                L"\u2B50 Controller", RGB(100, 220, 100), g_fontSmall);
        }

        /* Entity/scene count */
        wchar_t ginfo[64];
        wsprintfW(ginfo, L"Ent: %d  Scn: %d",
            g_ccp.vm.instance_count, g_ccp.vm.current_scene);
        gui_draw_text(hdc, cx + 16, cy + card_h - 16, ginfo, GUI_BORDER, g_fontSmall);
    }
}

/* ------------------------------------------------------------------ */
/*  Status bar                                                        */
/* ------------------------------------------------------------------ */
static void update_status(void) {
    if (!g_hwndStatus) return;
    wchar_t buf[256];
    if (g_ccp.raw) {
        const wchar_t *gply_tag = g_ccp.has_gameplay ? L"GPLY" : L"v2";
        const wchar_t *ctrl_tag = g_controller.connected ? L"Ctrl:ON" : L"Ctrl:--";
        wsprintfW(buf, L"  Page %d/%d  |  %d regions  |  %s  |  %s  |  %s",
            g_ccp.current_page + 1, g_ccp.page_count,
            g_ccp.region_count,
            g_show_regions ? L"Regions visible" : L"Regions hidden",
            gply_tag, ctrl_tag);
    } else {
        wsprintfW(buf, L"  No file loaded");
    }
    SetWindowTextW(g_hwndStatus, buf);
}

/* ------------------------------------------------------------------ */
/*  Toolbar                                                           */
/* ------------------------------------------------------------------ */
typedef struct { int id; const wchar_t *label; int x; int w; } CcpToolBtn;
static CcpToolBtn g_tb[] = {
    { IDC_BTN_PREV,     L"\u25C0 Prev",   4,   72 },
    { IDC_BTN_NEXT,     L"Next \u25B6",   80,  72 },
    { IDC_BTN_SEARCH,   L"\u26A1 Rgn",    164, 56 },
    { IDC_BTN_SETTINGS, L"\u2699",        228, 34 },
    { IDC_BTN_ABOUT,    L"?",             266, 34 },
};
#define TB_COUNT (sizeof(g_tb)/sizeof(g_tb[0]))

static int tb_hittest(int mx, int my) {
    if (my < 0 || my >= TOOLBAR_H) return -1;
    for (int i = 0; i < (int)TB_COUNT; i++)
        if (mx >= g_tb[i].x && mx < g_tb[i].x + g_tb[i].w)
            return g_tb[i].id;
    return -1;
}

static void draw_tb(HDC hdc, int width) {
    if (!gui_draw_asset(hdc, ASSET_CCP_TITLEBAR_BG, 0, 0, width, TOOLBAR_H))
        gui_fill_rect(hdc, 0, 0, width, TOOLBAR_H, GUI_BG_PANEL);
    gui_fill_rect(hdc, 0, TOOLBAR_H - 1, width, 1, GUI_BORDER);
    gui_draw_asset(hdc, ASSET_CCP_FRAME_TL, 0, 0, 16, 16);
    gui_draw_asset(hdc, ASSET_CCP_FRAME_TR, width - 16, 0, 16, 16);
    for (int i = 0; i < (int)TB_COUNT; i++) {
        CcpToolBtn *b = &g_tb[i];
        gui_draw_rounded_rect(hdc, b->x, 6, b->w, TOOLBAR_H - 12, 6,
            GUI_BG_DARK, GUI_BORDER);
        gui_draw_text(hdc, b->x + 8, 12, b->label, GUI_TEXT_LIGHT, g_fontUI);
    }
    /* drIpTECH branding */
    gui_draw_text(hdc, width - 130, 12, L"drIpTECH \u00b7 CCP", GUI_BORDER, g_fontSmall);
}

/* ------------------------------------------------------------------ */
/*  Sidebar (page list)                                               */
/* ------------------------------------------------------------------ */
static void draw_sidebar(HDC hdc, RECT *area) {
    int w = area->right - area->left;
    int h = area->bottom - area->top;
    if (!gui_draw_asset(hdc, ASSET_CCP_SIDEBAR_BG, area->left, area->top, w, h))
        gui_fill_rect(hdc, area->left, area->top, w, h, GUI_BG_PANEL);
    gui_fill_rect(hdc, area->right - 1, area->top, 1, h, GUI_BORDER);

    gui_draw_text(hdc, area->left + 8, area->top + 8, L"Pages", GUI_ACCENT, g_fontUI);
    gui_fill_rect(hdc, area->left + 8, area->top + 28, w - 16, 1, GUI_BORDER);

    int y = area->top + 36;
    for (int i = 0; i < g_ccp.page_count && y < area->bottom - 20; i++) {
        int selected = (i == g_ccp.current_page);
        if (selected)
            gui_fill_rect(hdc, area->left + 4, y - 2, w - 8, 22, GUI_BG_DARK);

        /* Count regions on this page */
        int rcount = 0;
        for (int r = 0; r < g_ccp.region_count; r++)
            if (g_ccp.regions[r].page == i) rcount++;

        wchar_t line[128];
        wchar_t wtitle[64];
        MultiByteToWideChar(CP_UTF8, 0, g_ccp.page_titles[i], -1, wtitle, 64);
        if (rcount > 0)
            wsprintfW(line, L"%d. %s (%d)", i + 1, wtitle, rcount);
        else
            wsprintfW(line, L"%d. %s", i + 1, wtitle);

        gui_draw_text(hdc, area->left + 12, y,
            line, selected ? GUI_ACCENT : GUI_TEXT_LIGHT, g_fontSmall);
        y += 22;
    }
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
    ofn.lpstrFilter = L"CCP Files (*.ccp)\0*.ccp\0All Files (*.*)\0*.*\0";
    ofn.lpstrFile = path;
    ofn.nMaxFile = MAX_PATH;
    ofn.Flags = OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST;
    if (GetOpenFileNameW(&ofn)) {
        if (load_ccp(path)) {
            wchar_t cap[256];
            wsprintfW(cap, L"CCP Interactive \u2014 %s", path);
            SetWindowTextW(g_hwndMain, cap);
            goto_page(0);
        } else {
            MessageBoxW(parent, L"Failed to open file.\nPlease select a valid .ccp file.",
                APP_TITLE, MB_ICONERROR);
        }
    }
}

/* ------------------------------------------------------------------ */
/*  About                                                             */
/* ------------------------------------------------------------------ */
static void show_about(HWND parent) {
    MessageBoxW(parent,
        L"drIpTECH CCP Interactive Viewer v2.0\n\n"
        L"ClipConceptBook Interactive Media Reader\n"
        L"with GPLY Gameplay VM & Controller Support\n\n"
        L"Navigation: Left/Right arrows, LT/RT triggers\n"
        L"Toggle regions: R key\n"
        L"Toggle sidebar: Tab key\n"
        L"Click interactive regions to activate\n"
        L"Controller: A/B/X/Y/D-pad for gameplay\n"
        L"  LT = Previous Page  |  RT = Next Page\n\n"
        L"\u00A9 2026 drIpTECH",
        APP_TITLE, MB_ICONINFORMATION);
}

/* ------------------------------------------------------------------ */
/*  Stage child window proc                                           */
/* ------------------------------------------------------------------ */
static LRESULT CALLBACK StageWndProc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp) {
    switch (msg) {
    case WM_PAINT: {
        PAINTSTRUCT ps;
        HDC hdc = BeginPaint(hwnd, &ps);
        RECT rc;
        GetClientRect(hwnd, &rc);
        HDC mem = CreateCompatibleDC(hdc);
        HBITMAP bmp = CreateCompatibleBitmap(hdc, rc.right, rc.bottom);
        HBITMAP oldBmp = (HBITMAP)SelectObject(mem, bmp);
        render_stage(mem, &rc);
        BitBlt(hdc, 0, 0, rc.right, rc.bottom, mem, 0, 0, SRCCOPY);
        SelectObject(mem, oldBmp);
        DeleteObject(bmp);
        DeleteDC(mem);
        EndPaint(hwnd, &ps);
        return 0;
    }
    case WM_MOUSEMOVE: {
        int mx = GET_X_LPARAM(lp), my = GET_Y_LPARAM(lp);
        RECT rc;
        GetClientRect(hwnd, &rc);
        int cx = 24, cy = 24 + 40;
        int changed = 0;
        for (int i = 0; i < g_ccp.region_count; i++) {
            if (g_ccp.regions[i].page != g_ccp.current_page) continue;
            InteractiveRegion *r = &g_ccp.regions[i];
            int rx = r->x + cx, ry = r->y + cy;
            int was_hover = r->hover;
            r->hover = (mx >= rx && mx < rx + r->w && my >= ry && my < ry + r->h);
            if (r->hover != was_hover) changed = 1;
        }
        if (changed) InvalidateRect(hwnd, NULL, TRUE);
        return 0;
    }
    case WM_LBUTTONDOWN: {
        int mx = GET_X_LPARAM(lp), my = GET_Y_LPARAM(lp);
        RECT rc;
        GetClientRect(hwnd, &rc);
        int cx = 24, cy = 24 + 40;

        /* Gameplay entity hit testing (v3) */
        if (g_ccp.has_gameplay) {
            float fpx = (float)(mx - cx);
            float fpy = (float)(my - cy);
            for (int i = 0; i < g_ccp.vm.instance_count; i++) {
                if (!g_ccp.vm.instances[i].active) continue;
                if (gply_hit_test_point(&g_ccp.vm, i, fpx, fpy)) {
                    gply_vm_fire_event(&g_ccp.vm, GPLY_EVT_CLICK, (uint16_t)i, 0);
                }
            }
            /* Check if VM triggered a page change */
            if (g_ccp.vm.pending_page >= 0) {
                int target = g_ccp.vm.pending_page;
                g_ccp.vm.pending_page = -1;
                goto_page(target);
                return 0;
            }
        }

        /* Legacy interactive region click */
        for (int i = 0; i < g_ccp.region_count; i++) {
            if (g_ccp.regions[i].page != g_ccp.current_page) continue;
            InteractiveRegion *r = &g_ccp.regions[i];
            int rx = r->x + cx, ry = r->y + cy;
            if (mx >= rx && mx < rx + r->w && my >= ry && my < ry + r->h) {
                handle_region_click(r);
                return 0;
            }
        }
        return 0;
    }
    case WM_MOUSEWHEEL: {
        int delta = GET_WHEEL_DELTA_WPARAM(wp);
        goto_page(g_ccp.current_page + (delta > 0 ? -1 : 1));
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
        RECT rc;
        GetClientRect(hwnd, &rc);
        int sb = g_show_sidebar ? SIDEBAR_W : 0;
        g_hwndSidebar = CreateWindowExW(0, L"STATIC", L"",
            WS_CHILD | (g_show_sidebar ? WS_VISIBLE : 0) | SS_OWNERDRAW,
            0, TOOLBAR_H, SIDEBAR_W, rc.bottom - TOOLBAR_H - STATUSBAR_H,
            hwnd, NULL, GetModuleHandle(NULL), NULL);
        g_hwndStage = CreateWindowExW(0, CLS_STAGE, L"", WS_CHILD | WS_VISIBLE,
            sb, TOOLBAR_H, rc.right - sb, rc.bottom - TOOLBAR_H - STATUSBAR_H,
            hwnd, NULL, GetModuleHandle(NULL), NULL);
        g_hwndStatus = CreateWindowExW(0, L"STATIC", L"  No file loaded",
            WS_CHILD | WS_VISIBLE | SS_LEFT,
            0, rc.bottom - STATUSBAR_H, rc.right, STATUSBAR_H,
            hwnd, (HMENU)IDC_PAGE_LABEL, GetModuleHandle(NULL), NULL);
        return 0;
    }
    case WM_SIZE: {
        int w = LOWORD(lp), h = HIWORD(lp);
        int sb = g_show_sidebar ? SIDEBAR_W : 0;
        MoveWindow(g_hwndSidebar, 0, TOOLBAR_H, SIDEBAR_W, h - TOOLBAR_H - STATUSBAR_H, TRUE);
        MoveWindow(g_hwndStage, sb, TOOLBAR_H, w - sb, h - TOOLBAR_H - STATUSBAR_H, TRUE);
        MoveWindow(g_hwndStatus, 0, h - STATUSBAR_H, w, STATUSBAR_H, TRUE);
        InvalidateRect(hwnd, NULL, TRUE);
        return 0;
    }
    case WM_PAINT: {
        PAINTSTRUCT ps;
        HDC hdc = BeginPaint(hwnd, &ps);
        RECT rc;
        GetClientRect(hwnd, &rc);
        draw_tb(hdc, rc.right);
        /* Status bar */
        gui_fill_rect(hdc, 0, rc.bottom - STATUSBAR_H, rc.right, STATUSBAR_H, GUI_BG_PANEL);
        gui_fill_rect(hdc, 0, rc.bottom - STATUSBAR_H, rc.right, 1, GUI_BORDER);
        gui_draw_asset(hdc, ASSET_CCP_FRAME_BL, 0, rc.bottom - 16, 16, 16);
        gui_draw_asset(hdc, ASSET_CCP_FRAME_BR, rc.right - 16, rc.bottom - 16, 16, 16);
        EndPaint(hwnd, &ps);
        return 0;
    }
    case WM_DRAWITEM: {
        /* Sidebar owner-draw */
        DRAWITEMSTRUCT *dis = (DRAWITEMSTRUCT*)lp;
        if (dis->hwndItem == g_hwndSidebar) {
            RECT sbrc;
            GetClientRect(g_hwndSidebar, &sbrc);
            draw_sidebar(dis->hDC, &sbrc);
        }
        return TRUE;
    }
    case WM_LBUTTONDOWN: {
        int mx = GET_X_LPARAM(lp), my = GET_Y_LPARAM(lp);
        /* Toolbar hits */
        int btn = tb_hittest(mx, my);
        switch (btn) {
        case IDC_BTN_PREV: goto_page(g_ccp.current_page - 1); break;
        case IDC_BTN_NEXT: goto_page(g_ccp.current_page + 1); break;
        case IDC_BTN_SEARCH:
            g_show_regions = !g_show_regions;
            InvalidateRect(g_hwndStage, NULL, TRUE);
            update_status();
            break;
        case IDC_BTN_SETTINGS:
            g_show_sidebar = !g_show_sidebar;
            ShowWindow(g_hwndSidebar, g_show_sidebar ? SW_SHOW : SW_HIDE);
            SendMessageW(hwnd, WM_SIZE, 0,
                MAKELPARAM(LOWORD(GetWindowLongPtrW(hwnd, GWL_STYLE)), 0));
            {
                RECT rc;
                GetClientRect(hwnd, &rc);
                int w = rc.right, h = rc.bottom;
                int sb = g_show_sidebar ? SIDEBAR_W : 0;
                MoveWindow(g_hwndStage, sb, TOOLBAR_H, w - sb, h - TOOLBAR_H - STATUSBAR_H, TRUE);
            }
            InvalidateRect(hwnd, NULL, TRUE);
            break;
        case IDC_BTN_ABOUT: show_about(hwnd); break;
        }
        /* Sidebar click — page selection */
        if (g_show_sidebar && mx < SIDEBAR_W && my > TOOLBAR_H + 36) {
            int idx = (my - TOOLBAR_H - 36) / 22;
            if (idx >= 0 && idx < g_ccp.page_count)
                goto_page(idx);
        }
        return 0;
    }
    case WM_KEYDOWN:
        switch (wp) {
        case VK_LEFT:  case VK_PRIOR: goto_page(g_ccp.current_page - 1); break;
        case VK_RIGHT: case VK_NEXT:  goto_page(g_ccp.current_page + 1); break;
        case VK_HOME:  goto_page(0); break;
        case VK_END:   goto_page(g_ccp.page_count - 1); break;
        case 'R':
            g_show_regions = !g_show_regions;
            InvalidateRect(g_hwndStage, NULL, TRUE);
            update_status();
            break;
        case VK_TAB:
            g_show_sidebar = !g_show_sidebar;
            ShowWindow(g_hwndSidebar, g_show_sidebar ? SW_SHOW : SW_HIDE);
            {
                RECT rc;
                GetClientRect(hwnd, &rc);
                int w = rc.right, h = rc.bottom;
                int sb = g_show_sidebar ? SIDEBAR_W : 0;
                MoveWindow(g_hwndStage, sb, TOOLBAR_H, w - sb, h - TOOLBAR_H - STATUSBAR_H, TRUE);
            }
            InvalidateRect(hwnd, NULL, TRUE);
            break;
        case 'O':
            if (GetKeyState(VK_CONTROL) & 0x8000) open_file_dialog(hwnd);
            break;
        }
        return 0;
    case WM_DROPFILES: {
        wchar_t path[MAX_PATH];
        DragQueryFileW((HDROP)wp, 0, path, MAX_PATH);
        DragFinish((HDROP)wp);
        if (load_ccp(path)) {
            wchar_t cap[256];
            wsprintfW(cap, L"CCP Interactive \u2014 %s", path);
            SetWindowTextW(hwnd, cap);
            goto_page(0);
        }
        return 0;
    }
    case WM_CLOSE:
        DestroyWindow(hwnd);
        return 0;
    case WM_TIMER:
        if (wp == 999 && g_splash_shown) {
            KillTimer(hwnd, 999);
            g_splash_shown = 0;
            InvalidateRect(g_hwndStage, NULL, TRUE);
        }
        if (wp == GAMEPLAY_TIMER_ID) {
            /* Poll controller */
            controller_poll();

            /* LT/RT page navigation (reserved - works in all .ccp files) */
            if (g_controller.page_prev_edge)
                goto_page(g_ccp.current_page - 1);
            if (g_controller.page_next_edge)
                goto_page(g_ccp.current_page + 1);

            /* Gameplay VM tick (v3 only) */
            if (g_ccp.has_gameplay) {
                controller_update_vm(&g_ccp.vm);
                gply_vm_tick(&g_ccp.vm);

                /* Check if VM triggered a page change */
                if (g_ccp.vm.pending_page >= 0) {
                    int target = g_ccp.vm.pending_page;
                    g_ccp.vm.pending_page = -1;
                    goto_page(target);
                }

                InvalidateRect(g_hwndStage, NULL, FALSE);
            }
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

    g_fontUI    = CreateFontW(-14, 0, 0, 0, FW_SEMIBOLD, 0, 0, 0,
        DEFAULT_CHARSET, 0, 0, CLEARTYPE_QUALITY, DEFAULT_PITCH, L"Segoe UI");
    g_fontStage = CreateFontW(-15, 0, 0, 0, FW_NORMAL, 0, 0, 0,
        DEFAULT_CHARSET, 0, 0, CLEARTYPE_QUALITY, DEFAULT_PITCH, L"Consolas");
    g_fontSmall = CreateFontW(-12, 0, 0, 0, FW_NORMAL, 0, 0, 0,
        DEFAULT_CHARSET, 0, 0, CLEARTYPE_QUALITY, DEFAULT_PITCH, L"Segoe UI");

    /* Register stage class */
    WNDCLASSEXW wcs = {0};
    wcs.cbSize = sizeof(wcs);
    wcs.lpfnWndProc = StageWndProc;
    wcs.hInstance = hInst;
    wcs.hCursor = LoadCursorW(NULL, IDC_HAND);
    wcs.lpszClassName = CLS_STAGE;
    RegisterClassExW(&wcs);

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
        CW_USEDEFAULT, CW_USEDEFAULT, 960, 680,
        NULL, NULL, hInst, NULL);

    ShowWindow(g_hwndMain, showCmd);
    UpdateWindow(g_hwndMain);

    /* Splash screen */
    if (gui_get_asset(ASSET_SPLASH_CCP)) {
        HDC hdc = GetDC(g_hwndStage);
        RECT prc;
        GetClientRect(g_hwndStage, &prc);
        gui_draw_asset(hdc, ASSET_SPLASH_CCP, 0, 0, prc.right, prc.bottom);
        ReleaseDC(g_hwndStage, hdc);
        g_splash_shown = 1;
        SetTimer(g_hwndMain, 999, SPLASH_DURATION_MS, NULL);
    }

    /* Start gameplay/controller polling timer (~60fps) */
    SetTimer(g_hwndMain, GAMEPLAY_TIMER_ID, GAMEPLAY_TICK_MS, NULL);

    /* Open from command line */
    if (cmdLine && cmdLine[0]) {
        wchar_t path[MAX_PATH];
        wcscpy_s(path, MAX_PATH, cmdLine);
        if (path[0] == L'"') {
            memmove(path, path + 1, wcslen(path) * sizeof(wchar_t));
            wchar_t *q = wcsrchr(path, L'"');
            if (q) *q = L'\0';
        }
        if (load_ccp(path)) {
            wchar_t cap[256];
            wsprintfW(cap, L"CCP Interactive \u2014 %s", path);
            SetWindowTextW(g_hwndMain, cap);
            goto_page(0);
        }
    }

    MSG msg;
    while (GetMessageW(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }

    if (g_ccp.raw) free(g_ccp.raw);
    if (g_ccp.manifest_json) free(g_ccp.manifest_json);
    if (g_ccp.gameplay_data) free(g_ccp.gameplay_data);
    KillTimer(g_hwndMain, GAMEPLAY_TIMER_ID);
    gui_assets_cleanup();
    DeleteObject(g_fontUI);
    DeleteObject(g_fontStage);
    DeleteObject(g_fontSmall);
    return (int)msg.wParam;
}
