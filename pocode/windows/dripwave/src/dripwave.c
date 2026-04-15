#include <windows.h>
#include <windowsx.h>
#include <commctrl.h>
#include <commdlg.h>
#include <shellapi.h>

#include <stdint.h>
#include <stdbool.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>

#include <zlib.h>

#define DRIPWAVE_MAX_SESSIONS 16
#define DRIPWAVE_STATUS_CAP 512
#define DRIPWAVE_TAB_CAP 96

#define IDC_OPEN_BUTTON 1001
#define IDC_TOGGLE_CONTROLS 1002
#define IDC_FIT_MODE 1003
#define IDC_TAB_CONTROL 1004
#define IDC_CANVAS 1005
#define IDC_STATUS 1006
#define IDC_RUN_BACKEND 1007
#define IDC_CLOSE_TAB 1008
#define IDC_SKIP_START 1009
#define IDC_FRAME_BACK 1010
#define IDC_PLAY_PAUSE 1011
#define IDC_FRAME_FWD 1012
#define IDC_SKIP_END 1013
#define IDC_DEAD_STOP 1014
#define IDC_VOLUME 1015
#define IDC_SAVE_STATE 1016
#define IDC_LOAD_STATE 1017
#define IDC_STATE_SLOT 1018
#define IDC_RECENT_COMBO 1019
#define IDC_OPEN_RECENT 1020
#define IDC_AUTHORING 1021

#define IDT_PLAYBACK 2001

#define DRIPWAVE_STATE_SLOT_COUNT 4
#define DRIPWAVE_RECENT_MAX 12

typedef enum DripwaveFitMode {
    DRIPWAVE_FIT_CONTAIN = 0,
    DRIPWAVE_FIT_NATIVE = 1,
    DRIPWAVE_FIT_STRETCH = 2,
} DripwaveFitMode;

typedef enum DripwaveBackendSource {
    DRIPWAVE_BACKEND_NONE = 0,
    DRIPWAVE_BACKEND_ENVIRONMENT = 1,
    DRIPWAVE_BACKEND_COLOCATED = 2,
    DRIPWAVE_BACKEND_USER_SELECTED = 3,
} DripwaveBackendSource;

typedef struct SwfInfo {
    int width_px;
    int height_px;
    int version;
    int frame_count;
    double frame_rate;
    uint32_t declared_file_length;
    int tag_count;
    int frame_label_count;
    bool recognized_signature;
    bool metadata_complete;
    bool tag_scan_complete;
    bool uses_avm1;
    bool uses_avm2;
    bool has_buttons;
    bool has_edit_text;
    bool has_sprites;
    bool has_video;
    bool has_sound_stream;
    bool has_binary_data;
    bool has_metadata_tag;
    bool uses_network;
    wchar_t compression[16];
} SwfInfo;

typedef struct DripwaveSession {
    bool loaded;
    bool is_farim;
    bool temp_owned;
    bool playing;
    int current_frame;
    int volume;
    double frame_accumulator;
    wchar_t source_path[MAX_PATH];
    wchar_t working_swf_path[MAX_PATH];
    wchar_t display_name[DRIPWAVE_TAB_CAP];
    wchar_t farim_entry[MAX_PATH];
    wchar_t state_path[MAX_PATH];
    wchar_t state_meta_path[MAX_PATH];
    wchar_t status[DRIPWAVE_STATUS_CAP];
    int last_state_slot;
    SwfInfo swf;
} DripwaveSession;

typedef struct DripwaveRecentEntry {
    wchar_t path[MAX_PATH];
    wchar_t display_name[DRIPWAVE_TAB_CAP];
} DripwaveRecentEntry;

typedef struct DripwaveApp {
    HINSTANCE instance;
    HWND window;
    HWND open_button;
    HWND toggle_button;
    HWND run_button;
    HWND save_button;
    HWND load_button;
    HWND slot_combo;
    HWND recent_combo;
    HWND recent_button;
    HWND author_button;
    HWND close_button;
    HWND fit_combo;
    HWND tab_control;
    HWND canvas;
    HWND status_label;
    HWND skip_start;
    HWND frame_back;
    HWND play_pause;
    HWND frame_fwd;
    HWND skip_end;
    HWND dead_stop;
    HWND volume_slider;
    bool controls_visible;
    bool backend_available;
    DripwaveBackendSource backend_source;
    DripwaveFitMode fit_mode;
    int selected_state_slot;
    int session_count;
    int active_index;
    int recent_count;
    HFONT headline_font;
    HFONT body_font;
    HFONT small_font;
    wchar_t backend_path[MAX_PATH];
    DripwaveSession sessions[DRIPWAVE_MAX_SESSIONS];
    DripwaveRecentEntry recent_entries[DRIPWAVE_RECENT_MAX];
} DripwaveApp;

static DripwaveApp g_app;

static void dripwave_select_session(int index);
static void dripwave_refresh_tab_titles(void);
static bool dripwave_add_session_from_path(HWND hwnd, const wchar_t *path);
static uint16_t dripwave_le16(const uint8_t *data);
static uint32_t dripwave_le32(const uint8_t *data);
static void dripwave_set_status(DripwaveSession *session, const wchar_t *fmt, ...);
static void dripwave_join_path(wchar_t *out_path, size_t out_cap, const wchar_t *left, const wchar_t *right);

static const wchar_t *dripwave_fit_mode_label(DripwaveFitMode mode) {
    switch (mode) {
        case DRIPWAVE_FIT_NATIVE:
            return L"1:1";
        case DRIPWAVE_FIT_STRETCH:
            return L"Stretch";
        case DRIPWAVE_FIT_CONTAIN:
        default:
            return L"Contain";
    }
}

static const wchar_t *dripwave_state_slot_label(int slot) {
    switch (slot) {
        case 1:
            return L"Checkpoint";
        case 2:
            return L"Branch A";
        case 3:
            return L"Sandbox";
        case 0:
        default:
            return L"Resume";
    }
}

static const wchar_t *dripwave_backend_source_label(DripwaveBackendSource source) {
    switch (source) {
        case DRIPWAVE_BACKEND_ENVIRONMENT:
            return L"env";
        case DRIPWAVE_BACKEND_COLOCATED:
            return L"colocated";
        case DRIPWAVE_BACKEND_USER_SELECTED:
            return L"saved/manual";
        case DRIPWAVE_BACKEND_NONE:
        default:
            return L"none";
    }
}

static void dripwave_assign_backend_path(const wchar_t *path, DripwaveBackendSource source) {
    if (!path || !path[0]) {
        g_app.backend_available = false;
        g_app.backend_source = DRIPWAVE_BACKEND_NONE;
        g_app.backend_path[0] = L'\0';
        return;
    }
    wcsncpy(g_app.backend_path, path, MAX_PATH - 1);
    g_app.backend_path[MAX_PATH - 1] = L'\0';
    g_app.backend_available = true;
    g_app.backend_source = source;
}

static void dripwave_init_swf_info(SwfInfo *info) {
    ZeroMemory(info, sizeof(*info));
    info->width_px = 640;
    info->height_px = 480;
    wcscpy(info->compression, L"unknown");
}

static bool dripwave_is_recognized_swf_signature(const uint8_t *data, size_t size) {
    return size >= 8 && (
        memcmp(data, "FWS", 3) == 0 ||
        memcmp(data, "CWS", 3) == 0 ||
        memcmp(data, "ZWS", 3) == 0
    );
}

static void dripwave_copy_swf_signature(const uint8_t *data, size_t size, wchar_t *out_text, size_t out_cap) {
    if (!out_text || out_cap == 0) {
        return;
    }
    if (size >= 3) {
        _snwprintf(out_text, out_cap - 1, L"%hc%hc%hc", data[0], data[1], data[2]);
        out_text[out_cap - 1] = L'\0';
        return;
    }
    wcsncpy(out_text, L"unknown", out_cap - 1);
    out_text[out_cap - 1] = L'\0';
}

static void dripwave_populate_fallback_swf_info(const uint8_t *data, size_t size, SwfInfo *info) {
    dripwave_init_swf_info(info);
    info->recognized_signature = dripwave_is_recognized_swf_signature(data, size);
    info->metadata_complete = false;
    info->tag_scan_complete = false;
    if (size >= 4) {
        info->version = data[3];
    }
    if (size >= 8) {
        info->declared_file_length = dripwave_le32(data + 4);
    }
    dripwave_copy_swf_signature(data, size, info->compression, sizeof(info->compression) / sizeof(info->compression[0]));
}

static const wchar_t *dripwave_swf_runtime_profile(const SwfInfo *info) {
    if (!info) {
        return L"unknown";
    }
    if (!info->metadata_complete) {
        return L"compatibility mode";
    }
    if (info->uses_avm2) {
        return L"AVM2 / ActionScript 3";
    }
    if (info->uses_avm1) {
        return L"AVM1 / ActionScript 1-2";
    }
    if (info->has_buttons || info->has_edit_text || info->has_sprites) {
        return L"interactive timeline";
    }
    return L"timeline-only";
}

static bool dripwave_swf_needs_projector(const SwfInfo *info) {
    if (!info) {
        return true;
    }
    return !info->metadata_complete ||
        info->uses_avm1 ||
        info->uses_avm2 ||
        info->has_buttons ||
        info->has_edit_text ||
        info->has_sprites ||
        info->has_video ||
        info->has_sound_stream ||
        info->has_binary_data;
}

static const wchar_t *dripwave_swf_backend_requirement(const SwfInfo *info) {
    if (!info) {
        return L"unknown";
    }
    if (!info->metadata_complete) {
        return L"projector required for full playback";
    }
    if (info->uses_avm2) {
        return L"projector required for AVM2";
    }
    if (info->uses_avm1) {
        return L"projector required for AVM1";
    }
    if (info->has_buttons || info->has_edit_text || info->has_sprites || info->has_video || info->has_sound_stream || info->has_binary_data) {
        return L"projector recommended for interactivity";
    }
    return L"native inspector ready";
}

static bool dripwave_scan_swf_tags(const uint8_t *data, size_t size, SwfInfo *info) {
    size_t cursor = 0;
    while (cursor + 2 <= size) {
        uint16_t tag_header = dripwave_le16(data + cursor);
        uint16_t tag_code = (uint16_t)(tag_header >> 6);
        uint32_t tag_length = (uint32_t)(tag_header & 0x3fu);
        const uint8_t *payload;
        cursor += 2;
        if (tag_length == 0x3fu) {
            if (cursor + 4 > size) {
                return false;
            }
            tag_length = dripwave_le32(data + cursor);
            cursor += 4;
        }
        if (cursor + tag_length > size) {
            return false;
        }

        payload = data + cursor;
        info->tag_count++;
        switch (tag_code) {
            case 0:
                return true;
            case 7:
            case 34:
                info->has_buttons = true;
                break;
            case 12:
            case 59:
                info->uses_avm1 = true;
                break;
            case 18:
            case 19:
            case 45:
                info->has_sound_stream = true;
                break;
            case 37:
                info->has_edit_text = true;
                break;
            case 39:
                info->has_sprites = true;
                break;
            case 43:
                info->frame_label_count++;
                break;
            case 60:
            case 61:
                info->has_video = true;
                break;
            case 69:
                if (tag_length >= 4) {
                    uint32_t flags = dripwave_le32(payload);
                    if (flags & 0x08u) {
                        info->has_metadata_tag = true;
                    }
                    if (flags & 0x10u) {
                        info->uses_avm2 = true;
                    }
                    if (flags & 0x80u) {
                        info->uses_network = true;
                    }
                }
                break;
            case 77:
                info->has_metadata_tag = true;
                break;
            case 82:
                info->uses_avm2 = true;
                break;
            case 86:
                info->frame_label_count++;
                break;
            case 87:
                info->has_binary_data = true;
                break;
        }

        cursor += tag_length;
    }
    return cursor == size;
}

static const wchar_t *dripwave_file_name(const wchar_t *path) {
    const wchar_t *cursor = wcsrchr(path, L'\\');
    const wchar_t *alt = wcsrchr(path, L'/');
    if (alt && (!cursor || alt > cursor)) {
        cursor = alt;
    }
    return cursor ? cursor + 1 : path;
}

static const wchar_t *dripwave_extension(const wchar_t *path) {
    const wchar_t *name = dripwave_file_name(path);
    const wchar_t *dot = wcsrchr(name, L'.');
    return dot ? dot : L"";
}

static bool dripwave_has_extension_a(const char *text, const char *suffix) {
    size_t text_len = strlen(text);
    size_t suffix_len = strlen(suffix);
    if (suffix_len > text_len) {
        return false;
    }
    return _stricmp(text + text_len - suffix_len, suffix) == 0;
}

static bool dripwave_file_exists(const wchar_t *path) {
    DWORD attributes = GetFileAttributesW(path);
    return attributes != INVALID_FILE_ATTRIBUTES && !(attributes & FILE_ATTRIBUTE_DIRECTORY);
}

static bool dripwave_directory_exists(const wchar_t *path) {
    DWORD attributes = GetFileAttributesW(path);
    return attributes != INVALID_FILE_ATTRIBUTES && (attributes & FILE_ATTRIBUTE_DIRECTORY);
}

static bool dripwave_ensure_directory(const wchar_t *path) {
    if (CreateDirectoryW(path, NULL)) {
        return true;
    }
    return GetLastError() == ERROR_ALREADY_EXISTS;
}

static uint32_t dripwave_hash_wide_text(const wchar_t *text) {
    uint32_t hash = 2166136261u;
    while (text && *text) {
        hash ^= (uint32_t)(*text++);
        hash *= 16777619u;
    }
    return hash;
}

static bool dripwave_resolve_app_root(wchar_t *out_path, size_t out_cap) {
    wchar_t local_appdata[MAX_PATH];
    DWORD length = GetEnvironmentVariableW(L"LOCALAPPDATA", local_appdata, MAX_PATH);
    if (length == 0 || length >= MAX_PATH) {
        return false;
    }
    dripwave_join_path(out_path, out_cap, local_appdata, L"dripwave");
    return dripwave_ensure_directory(out_path);
}

static bool dripwave_resolve_state_root(wchar_t *out_path, size_t out_cap) {
    wchar_t state_root[MAX_PATH];
    if (!dripwave_resolve_app_root(state_root, MAX_PATH)) {
        return false;
    }
    dripwave_join_path(out_path, out_cap, state_root, L"states");
    return dripwave_ensure_directory(out_path);
}

static bool dripwave_resolve_recent_path(wchar_t *out_path, size_t out_cap) {
    wchar_t app_root[MAX_PATH];
    if (!dripwave_resolve_app_root(app_root, MAX_PATH)) {
        return false;
    }
    _snwprintf(out_path, out_cap - 1, L"%ls\\recent.ini", app_root);
    out_path[out_cap - 1] = L'\0';
    return true;
}

static bool dripwave_build_state_meta_path(const wchar_t *source_path, wchar_t *out_path, size_t out_cap) {
    wchar_t state_root[MAX_PATH];
    uint32_t hash;
    if (!source_path || !source_path[0]) {
        return false;
    }
    if (!dripwave_resolve_state_root(state_root, MAX_PATH)) {
        return false;
    }
    hash = dripwave_hash_wide_text(source_path);
    _snwprintf(out_path, out_cap - 1, L"%ls\\%08X.dwmeta", state_root, hash);
    out_path[out_cap - 1] = L'\0';
    return true;
}

static bool dripwave_build_state_path(const wchar_t *source_path, int slot, wchar_t *out_path, size_t out_cap) {
    wchar_t state_root[MAX_PATH];
    uint32_t hash;
    if (!source_path || !source_path[0]) {
        return false;
    }
    if (slot < 0 || slot >= DRIPWAVE_STATE_SLOT_COUNT) {
        slot = 0;
    }
    if (!dripwave_resolve_state_root(state_root, MAX_PATH)) {
        return false;
    }
    hash = dripwave_hash_wide_text(source_path);
    _snwprintf(out_path, out_cap - 1, L"%ls\\%08X_slot%d.dwstate", state_root, hash, slot + 1);
    out_path[out_cap - 1] = L'\0';
    return true;
}

static int dripwave_current_state_slot(void) {
    if (g_app.slot_combo) {
        int slot = (int)SendMessageW(g_app.slot_combo, CB_GETCURSEL, 0, 0);
        if (slot >= 0 && slot < DRIPWAVE_STATE_SLOT_COUNT) {
            g_app.selected_state_slot = slot;
        }
    }
    if (g_app.selected_state_slot < 0 || g_app.selected_state_slot >= DRIPWAVE_STATE_SLOT_COUNT) {
        g_app.selected_state_slot = 0;
    }
    return g_app.selected_state_slot;
}

static int dripwave_resolve_last_state_slot(const wchar_t *source_path) {
    wchar_t meta_path[MAX_PATH];
    int slot;
    if (!dripwave_build_state_meta_path(source_path, meta_path, MAX_PATH) || !dripwave_file_exists(meta_path)) {
        return 0;
    }
    slot = GetPrivateProfileIntW(L"state", L"last_slot", 0, meta_path);
    if (slot < 0 || slot >= DRIPWAVE_STATE_SLOT_COUNT) {
        return 0;
    }
    return slot;
}

static void dripwave_write_last_state_slot(const wchar_t *source_path, int slot) {
    wchar_t meta_path[MAX_PATH];
    wchar_t value[16];
    if (slot < 0 || slot >= DRIPWAVE_STATE_SLOT_COUNT) {
        slot = 0;
    }
    if (!dripwave_build_state_meta_path(source_path, meta_path, MAX_PATH)) {
        return;
    }
    _snwprintf(value, 15, L"%d", slot);
    value[15] = L'\0';
    WritePrivateProfileStringW(L"state", L"last_slot", value, meta_path);
}

static void dripwave_refresh_recent_combo(void) {
    if (!g_app.recent_combo) {
        return;
    }
    SendMessageW(g_app.recent_combo, CB_RESETCONTENT, 0, 0);
    for (int i = 0; i < g_app.recent_count; ++i) {
        wchar_t line[DRIPWAVE_TAB_CAP + 24];
        _snwprintf(line, (sizeof(line) / sizeof(line[0])) - 1, L"%ls", g_app.recent_entries[i].display_name);
        line[(sizeof(line) / sizeof(line[0])) - 1] = L'\0';
        SendMessageW(g_app.recent_combo, CB_ADDSTRING, 0, (LPARAM)line);
    }
    if (g_app.recent_count > 0) {
        SendMessageW(g_app.recent_combo, CB_SETCURSEL, 0, 0);
    }
}

static void dripwave_save_recent_entries(void) {
    wchar_t recent_path[MAX_PATH];
    if (!dripwave_resolve_recent_path(recent_path, MAX_PATH)) {
        return;
    }
    for (int i = 0; i < DRIPWAVE_RECENT_MAX; ++i) {
        wchar_t section[32];
        _snwprintf(section, 31, L"recent%d", i);
        section[31] = L'\0';
        if (i < g_app.recent_count) {
            WritePrivateProfileStringW(section, L"path", g_app.recent_entries[i].path, recent_path);
            WritePrivateProfileStringW(section, L"display_name", g_app.recent_entries[i].display_name, recent_path);
        } else {
            WritePrivateProfileStringW(section, NULL, NULL, recent_path);
        }
    }
}

static void dripwave_load_recent_entries(void) {
    wchar_t recent_path[MAX_PATH];
    g_app.recent_count = 0;
    if (!dripwave_resolve_recent_path(recent_path, MAX_PATH) || !dripwave_file_exists(recent_path)) {
        dripwave_refresh_recent_combo();
        return;
    }
    for (int i = 0; i < DRIPWAVE_RECENT_MAX; ++i) {
        wchar_t section[32];
        wchar_t path[MAX_PATH];
        wchar_t display_name[DRIPWAVE_TAB_CAP];
        _snwprintf(section, 31, L"recent%d", i);
        section[31] = L'\0';
        GetPrivateProfileStringW(section, L"path", L"", path, MAX_PATH, recent_path);
        if (!path[0] || !dripwave_file_exists(path)) {
            continue;
        }
        GetPrivateProfileStringW(section, L"display_name", dripwave_file_name(path), display_name, DRIPWAVE_TAB_CAP, recent_path);
        wcsncpy(g_app.recent_entries[g_app.recent_count].path, path, MAX_PATH - 1);
        g_app.recent_entries[g_app.recent_count].path[MAX_PATH - 1] = L'\0';
        wcsncpy(g_app.recent_entries[g_app.recent_count].display_name, display_name, DRIPWAVE_TAB_CAP - 1);
        g_app.recent_entries[g_app.recent_count].display_name[DRIPWAVE_TAB_CAP - 1] = L'\0';
        g_app.recent_count++;
    }
    dripwave_refresh_recent_combo();
}

static void dripwave_register_recent_path(const wchar_t *path, const wchar_t *display_name) {
    DripwaveRecentEntry updated[DRIPWAVE_RECENT_MAX];
    int count = 0;
    if (!path || !path[0] || !dripwave_file_exists(path)) {
        return;
    }
    ZeroMemory(updated, sizeof(updated));
    wcsncpy(updated[count].path, path, MAX_PATH - 1);
    updated[count].path[MAX_PATH - 1] = L'\0';
    wcsncpy(updated[count].display_name, display_name && display_name[0] ? display_name : dripwave_file_name(path), DRIPWAVE_TAB_CAP - 1);
    updated[count].display_name[DRIPWAVE_TAB_CAP - 1] = L'\0';
    count++;
    for (int i = 0; i < g_app.recent_count && count < DRIPWAVE_RECENT_MAX; ++i) {
        if (_wcsicmp(g_app.recent_entries[i].path, path) == 0) {
            continue;
        }
        updated[count++] = g_app.recent_entries[i];
    }
    ZeroMemory(g_app.recent_entries, sizeof(g_app.recent_entries));
    for (int i = 0; i < count; ++i) {
        g_app.recent_entries[i] = updated[i];
    }
    g_app.recent_count = count;
    dripwave_save_recent_entries();
    dripwave_refresh_recent_combo();
}

static void dripwave_update_runtime_button(void) {
    DripwaveSession *session = NULL;
    const wchar_t *label = L"Runtime...";
    if (g_app.active_index >= 0 && g_app.active_index < g_app.session_count) {
        session = &g_app.sessions[g_app.active_index];
    }
    if (session && session->loaded) {
        if (!dripwave_swf_needs_projector(&session->swf)) {
            label = L"Native Ready";
        } else if (g_app.backend_available) {
            label = L"Launch Runtime";
        } else {
            label = L"Find Runtime...";
        }
    }
    if (g_app.run_button) {
        SetWindowTextW(g_app.run_button, label);
    }
}

static void dripwave_refresh_loaded_status(DripwaveSession *session, const wchar_t *suffix) {
    if (!session) {
        return;
    }
    if (session->swf.metadata_complete) {
        dripwave_set_status(
            session,
            L"Loaded %ls | %dx%d | SWF v%d | %ls%ls%ls",
            session->display_name,
            session->swf.width_px,
            session->swf.height_px,
            session->swf.version,
            dripwave_swf_runtime_profile(&session->swf),
            suffix && suffix[0] ? L" | " : L"",
            suffix && suffix[0] ? suffix : L""
        );
    } else {
        dripwave_set_status(
            session,
            L"Loaded %ls in compatibility mode | SWF v%d | %ls%ls%ls",
            session->display_name,
            session->swf.version,
            dripwave_swf_backend_requirement(&session->swf),
            suffix && suffix[0] ? L" | " : L"",
            suffix && suffix[0] ? suffix : L""
        );
    }
}

static bool dripwave_save_state_for_session(DripwaveSession *session, int slot, wchar_t *error_text, size_t error_cap) {
    wchar_t value[64];
    if (!session || !session->loaded) {
        _snwprintf(error_text, error_cap - 1, L"No active SWF session is loaded.");
        error_text[error_cap - 1] = L'\0';
        return false;
    }
    if (!dripwave_build_state_path(session->source_path, slot, session->state_path, MAX_PATH)) {
        _snwprintf(error_text, error_cap - 1, L"Failed to resolve a save-state path.");
        error_text[error_cap - 1] = L'\0';
        return false;
    }
    if (!session->state_meta_path[0]) {
        dripwave_build_state_meta_path(session->source_path, session->state_meta_path, MAX_PATH);
    }

    WritePrivateProfileStringW(L"state", L"source_path", session->source_path, session->state_path);
    WritePrivateProfileStringW(L"state", L"display_name", session->display_name, session->state_path);
    WritePrivateProfileStringW(L"state", L"backend_path", g_app.backend_available ? g_app.backend_path : L"", session->state_path);
    _snwprintf(value, 63, L"%d", session->current_frame);
    value[63] = L'\0';
    WritePrivateProfileStringW(L"state", L"current_frame", value, session->state_path);
    _snwprintf(value, 63, L"%d", session->volume);
    value[63] = L'\0';
    WritePrivateProfileStringW(L"state", L"volume", value, session->state_path);
    _snwprintf(value, 63, L"%d", (int)g_app.fit_mode);
    value[63] = L'\0';
    WritePrivateProfileStringW(L"state", L"fit_mode", value, session->state_path);
    _snwprintf(value, 63, L"%d", session->is_farim ? 1 : 0);
    value[63] = L'\0';
    WritePrivateProfileStringW(L"state", L"is_farim", value, session->state_path);
    WritePrivateProfileStringW(L"state", L"slot_name", dripwave_state_slot_label(slot), session->state_path);
    session->last_state_slot = slot;
    dripwave_write_last_state_slot(session->source_path, slot);

    _snwprintf(error_text, error_cap - 1, L"Saved %ls slot: frame %d / %d, volume %d%%, fit %ls",
        dripwave_state_slot_label(slot),
        session->current_frame + 1,
        max(session->swf.frame_count, 1),
        session->volume,
        dripwave_fit_mode_label(g_app.fit_mode));
    error_text[error_cap - 1] = L'\0';
    return true;
}

static bool dripwave_load_state_for_session(DripwaveSession *session, int slot, bool apply_fit_mode, wchar_t *error_text, size_t error_cap) {
    wchar_t stored_source[MAX_PATH];
    wchar_t stored_backend[MAX_PATH];
    int frame_limit;
    int frame_index;
    if (!session || !session->loaded) {
        _snwprintf(error_text, error_cap - 1, L"No active SWF session is loaded.");
        error_text[error_cap - 1] = L'\0';
        return false;
    }
    if (!dripwave_build_state_path(session->source_path, slot, session->state_path, MAX_PATH)) {
        _snwprintf(error_text, error_cap - 1, L"Failed to resolve a save-state path.");
        error_text[error_cap - 1] = L'\0';
        return false;
    }
    if (!dripwave_file_exists(session->state_path)) {
        _snwprintf(error_text, error_cap - 1, L"No %ls slot exists yet for %ls.", dripwave_state_slot_label(slot), session->display_name);
        error_text[error_cap - 1] = L'\0';
        return false;
    }

    GetPrivateProfileStringW(L"state", L"source_path", L"", stored_source, MAX_PATH, session->state_path);
    if (stored_source[0] && _wcsicmp(stored_source, session->source_path) != 0) {
        _snwprintf(error_text, error_cap - 1, L"Save state source mismatch for %ls.", session->display_name);
        error_text[error_cap - 1] = L'\0';
        return false;
    }

    frame_limit = max(session->swf.frame_count, 1);
    frame_index = GetPrivateProfileIntW(L"state", L"current_frame", 0, session->state_path);
    if (frame_index < 0) {
        frame_index = 0;
    }
    if (frame_index >= frame_limit) {
        frame_index = frame_limit - 1;
    }
    session->current_frame = frame_index;
    session->playing = false;
    session->frame_accumulator = 0.0;

    session->volume = GetPrivateProfileIntW(L"state", L"volume", session->volume, session->state_path);
    if (session->volume < 0) {
        session->volume = 0;
    }
    if (session->volume > 100) {
        session->volume = 100;
    }

    if (apply_fit_mode) {
        int fit_value = GetPrivateProfileIntW(L"state", L"fit_mode", (int)g_app.fit_mode, session->state_path);
        if (fit_value < (int)DRIPWAVE_FIT_CONTAIN || fit_value > (int)DRIPWAVE_FIT_STRETCH) {
            fit_value = (int)DRIPWAVE_FIT_CONTAIN;
        }
        g_app.fit_mode = (DripwaveFitMode)fit_value;
        if (g_app.fit_combo) {
            SendMessageW(g_app.fit_combo, CB_SETCURSEL, g_app.fit_mode, 0);
        }
    }

    GetPrivateProfileStringW(L"state", L"backend_path", L"", stored_backend, MAX_PATH, session->state_path);
    if (stored_backend[0] && dripwave_file_exists(stored_backend)) {
        dripwave_assign_backend_path(stored_backend, DRIPWAVE_BACKEND_USER_SELECTED);
    }
    session->last_state_slot = slot;
    dripwave_write_last_state_slot(session->source_path, slot);

    _snwprintf(error_text, error_cap - 1, L"Resumed %ls slot: frame %d / %d, volume %d%%, fit %ls",
        dripwave_state_slot_label(slot),
        session->current_frame + 1,
        frame_limit,
        session->volume,
        dripwave_fit_mode_label(g_app.fit_mode));
    error_text[error_cap - 1] = L'\0';
    return true;
}

static void dripwave_format_tab_title(const DripwaveSession *session, wchar_t *out_text, size_t out_cap) {
    _snwprintf(out_text, out_cap - 1, L"%ls  x", session->display_name);
    out_text[out_cap - 1] = L'\0';
}

static void dripwave_join_path(wchar_t *out_path, size_t out_cap, const wchar_t *left, const wchar_t *right) {
    _snwprintf(out_path, out_cap - 1, L"%ls\\%ls", left, right);
    out_path[out_cap - 1] = L'\0';
}

static void dripwave_detect_backend(void) {
    static const wchar_t *candidates[] = {
        L"ruffle_desktop.exe",
        L"flashplayer_32_sa.exe",
        L"flashplayer_sa.exe",
    };
    wchar_t configured[MAX_PATH];
    wchar_t module_path[MAX_PATH];
    wchar_t *slash;

    dripwave_assign_backend_path(NULL, DRIPWAVE_BACKEND_NONE);

    if (GetEnvironmentVariableW(L"DRIPWAVE_BACKEND", configured, MAX_PATH) > 0 && dripwave_file_exists(configured)) {
        dripwave_assign_backend_path(configured, DRIPWAVE_BACKEND_ENVIRONMENT);
        return;
    }

    if (!GetModuleFileNameW(NULL, module_path, MAX_PATH)) {
        return;
    }
    slash = wcsrchr(module_path, L'\\');
    if (!slash) {
        return;
    }
    *slash = L'\0';

    for (int i = 0; i < (int)(sizeof(candidates) / sizeof(candidates[0])); ++i) {
        wchar_t candidate_path[MAX_PATH];
        dripwave_join_path(candidate_path, MAX_PATH, module_path, candidates[i]);
        if (dripwave_file_exists(candidate_path)) {
            dripwave_assign_backend_path(candidate_path, DRIPWAVE_BACKEND_COLOCATED);
            return;
        }
    }
}

static void dripwave_set_status(DripwaveSession *session, const wchar_t *fmt, ...) {
    va_list args;
    va_start(args, fmt);
    _vsnwprintf(session->status, DRIPWAVE_STATUS_CAP - 1, fmt, args);
    session->status[DRIPWAVE_STATUS_CAP - 1] = L'\0';
    va_end(args);
}

static uint16_t dripwave_le16(const uint8_t *data) {
    return (uint16_t)(data[0] | (data[1] << 8));
}

static uint32_t dripwave_le32(const uint8_t *data) {
    return (uint32_t)(data[0] | (data[1] << 8) | (data[2] << 16) | (data[3] << 24));
}

typedef struct BitReader {
    const uint8_t *data;
    size_t size;
    size_t bit_pos;
} BitReader;

static uint32_t dripwave_read_bits(BitReader *reader, int count) {
    uint32_t value = 0;
    for (int i = 0; i < count; ++i) {
        if ((reader->bit_pos / 8) >= reader->size) {
            return value;
        }
        value <<= 1u;
        value |= (reader->data[reader->bit_pos / 8] >> (7 - (reader->bit_pos % 8))) & 1u;
        reader->bit_pos++;
    }
    return value;
}

static int32_t dripwave_read_sbits(BitReader *reader, int count) {
    uint32_t raw = dripwave_read_bits(reader, count);
    if (count <= 0) {
        return 0;
    }
    if (raw & (1u << (count - 1))) {
        raw |= ~((1u << count) - 1u);
    }
    return (int32_t)raw;
}

static bool dripwave_parse_rect(const uint8_t *data, size_t size, size_t *bytes_used, int *width_px, int *height_px) {
    BitReader reader = { data, size, 0 };
    int nbits = (int)dripwave_read_bits(&reader, 5);
    int32_t xmin = dripwave_read_sbits(&reader, nbits);
    int32_t xmax = dripwave_read_sbits(&reader, nbits);
    int32_t ymin = dripwave_read_sbits(&reader, nbits);
    int32_t ymax = dripwave_read_sbits(&reader, nbits);
    reader.bit_pos = (reader.bit_pos + 7u) & ~7u;
    *bytes_used = reader.bit_pos / 8u;
    *width_px = (xmax - xmin) / 20;
    *height_px = (ymax - ymin) / 20;
    return *width_px > 0 && *height_px > 0;
}

static bool dripwave_read_entire_file(const wchar_t *path, uint8_t **out_data, size_t *out_size) {
    FILE *handle = _wfopen(path, L"rb");
    long size;
    uint8_t *buffer;
    if (!handle) {
        return false;
    }
    if (fseek(handle, 0, SEEK_END) != 0) {
        fclose(handle);
        return false;
    }
    size = ftell(handle);
    if (size < 0) {
        fclose(handle);
        return false;
    }
    rewind(handle);
    buffer = (uint8_t*)malloc((size_t)size);
    if (!buffer) {
        fclose(handle);
        return false;
    }
    if (fread(buffer, 1, (size_t)size, handle) != (size_t)size) {
        free(buffer);
        fclose(handle);
        return false;
    }
    fclose(handle);
    *out_data = buffer;
    *out_size = (size_t)size;
    return true;
}

static bool dripwave_write_entire_file(const wchar_t *path, const uint8_t *data, size_t size) {
    FILE *handle = _wfopen(path, L"wb");
    if (!handle) {
        return false;
    }
    if (fwrite(data, 1, size, handle) != size) {
        fclose(handle);
        return false;
    }
    fclose(handle);
    return true;
}

static bool dripwave_parse_swf_bytes(const uint8_t *data, size_t size, SwfInfo *info, wchar_t *error_text, size_t error_cap) {
    uint8_t *decompressed = NULL;
    const uint8_t *stream = NULL;
    size_t stream_size = 0;
    size_t rect_bytes = 0;
    size_t tag_offset = 0;
    int width_px = 0;
    int height_px = 0;

    dripwave_init_swf_info(info);

    if (size < 12) {
        _snwprintf(error_text, error_cap - 1, L"SWF file is too small.");
        error_text[error_cap - 1] = L'\0';
        return false;
    }

    info->recognized_signature = dripwave_is_recognized_swf_signature(data, size);
    info->version = data[3];
    info->declared_file_length = dripwave_le32(data + 4);

    if (memcmp(data, "FWS", 3) == 0) {
        wcscpy(info->compression, L"FWS");
        stream = data + 8;
        stream_size = size - 8;
    } else if (memcmp(data, "CWS", 3) == 0) {
        uLongf expected = dripwave_le32(data + 4) - 8u;
        int z_result;
        wcscpy(info->compression, L"CWS");
        decompressed = (uint8_t*)malloc(expected);
        if (!decompressed) {
            _snwprintf(error_text, error_cap - 1, L"Out of memory while inflating SWF.");
            error_text[error_cap - 1] = L'\0';
            return false;
        }
        z_result = uncompress(decompressed, &expected, data + 8, (uLong)(size - 8));
        if (z_result != Z_OK) {
            free(decompressed);
            _snwprintf(error_text, error_cap - 1, L"Failed to inflate compressed SWF (zlib code %d).", z_result);
            error_text[error_cap - 1] = L'\0';
            return false;
        }
        stream = decompressed;
        stream_size = expected;
    } else if (memcmp(data, "ZWS", 3) == 0) {
        wcscpy(info->compression, L"ZWS");
        _snwprintf(error_text, error_cap - 1, L"LZMA-compressed ZWS files are not yet decoded by the native metadata parser.");
        error_text[error_cap - 1] = L'\0';
        return false;
    } else {
        _snwprintf(error_text, error_cap - 1, L"File is not a recognized SWF stream.");
        error_text[error_cap - 1] = L'\0';
        return false;
    }

    if (!dripwave_parse_rect(stream, stream_size, &rect_bytes, &width_px, &height_px) || stream_size < rect_bytes + 4) {
        free(decompressed);
        _snwprintf(error_text, error_cap - 1, L"Failed to parse SWF frame rectangle.");
        error_text[error_cap - 1] = L'\0';
        return false;
    }

    info->width_px = width_px;
    info->height_px = height_px;
    info->frame_rate = dripwave_le16(stream + rect_bytes) / 256.0;
    info->frame_count = dripwave_le16(stream + rect_bytes + 2);
    info->metadata_complete = true;

    tag_offset = rect_bytes + 4;
    if (stream_size >= tag_offset) {
        info->tag_scan_complete = dripwave_scan_swf_tags(stream + tag_offset, stream_size - tag_offset, info);
    }

    free(decompressed);
    return true;
}

typedef struct ZipEntry {
    uint16_t method;
    uint32_t compressed_size;
    uint32_t uncompressed_size;
    uint32_t local_offset;
    char name[260];
} ZipEntry;

static bool dripwave_zip_find_eocd(const uint8_t *zip_data, size_t zip_size, size_t *eocd_offset) {
    size_t start = zip_size > 0x10000 + 22 ? zip_size - (0x10000 + 22) : 0;
    for (size_t pos = zip_size >= 4 ? zip_size - 4 : 0; pos > start; --pos) {
        if (dripwave_le32(zip_data + pos) == 0x06054b50u) {
            *eocd_offset = pos;
            return true;
        }
    }
    if (start == 0 && zip_size >= 4 && dripwave_le32(zip_data) == 0x06054b50u) {
        *eocd_offset = 0;
        return true;
    }
    return false;
}

static bool dripwave_zip_locate_entry(const uint8_t *zip_data, size_t zip_size, const char *target_name, ZipEntry *entry_out) {
    size_t eocd_offset;
    uint16_t total_entries;
    uint32_t cd_offset;
    size_t cursor;
    if (!dripwave_zip_find_eocd(zip_data, zip_size, &eocd_offset) || eocd_offset + 22 > zip_size) {
        return false;
    }
    total_entries = dripwave_le16(zip_data + eocd_offset + 10);
    cd_offset = dripwave_le32(zip_data + eocd_offset + 16);
    if ((size_t)cd_offset >= zip_size) {
        return false;
    }
    cursor = cd_offset;
    for (uint16_t i = 0; i < total_entries && cursor + 46 <= zip_size; ++i) {
        uint16_t name_len;
        uint16_t extra_len;
        uint16_t comment_len;
        if (dripwave_le32(zip_data + cursor) != 0x02014b50u) {
            return false;
        }
        name_len = dripwave_le16(zip_data + cursor + 28);
        extra_len = dripwave_le16(zip_data + cursor + 30);
        comment_len = dripwave_le16(zip_data + cursor + 32);
        if (cursor + 46 + name_len > zip_size) {
            return false;
        }
        if (name_len < sizeof(entry_out->name)) {
            memcpy(entry_out->name, zip_data + cursor + 46, name_len);
            entry_out->name[name_len] = '\0';
        } else {
            entry_out->name[0] = '\0';
        }
        if (_stricmp(entry_out->name, target_name) == 0) {
            entry_out->method = dripwave_le16(zip_data + cursor + 10);
            entry_out->compressed_size = dripwave_le32(zip_data + cursor + 20);
            entry_out->uncompressed_size = dripwave_le32(zip_data + cursor + 24);
            entry_out->local_offset = dripwave_le32(zip_data + cursor + 42);
            return true;
        }
        cursor += 46u + name_len + extra_len + comment_len;
    }
    return false;
}

static bool dripwave_zip_find_first_swf(const uint8_t *zip_data, size_t zip_size, ZipEntry *entry_out) {
    size_t eocd_offset;
    uint16_t total_entries;
    uint32_t cd_offset;
    size_t cursor;
    if (!dripwave_zip_find_eocd(zip_data, zip_size, &eocd_offset) || eocd_offset + 22 > zip_size) {
        return false;
    }
    total_entries = dripwave_le16(zip_data + eocd_offset + 10);
    cd_offset = dripwave_le32(zip_data + eocd_offset + 16);
    if ((size_t)cd_offset >= zip_size) {
        return false;
    }
    cursor = cd_offset;
    for (uint16_t i = 0; i < total_entries && cursor + 46 <= zip_size; ++i) {
        uint16_t name_len;
        uint16_t extra_len;
        uint16_t comment_len;
        if (dripwave_le32(zip_data + cursor) != 0x02014b50u) {
            return false;
        }
        name_len = dripwave_le16(zip_data + cursor + 28);
        extra_len = dripwave_le16(zip_data + cursor + 30);
        comment_len = dripwave_le16(zip_data + cursor + 32);
        if (cursor + 46 + name_len > zip_size || name_len >= sizeof(entry_out->name)) {
            return false;
        }
        memcpy(entry_out->name, zip_data + cursor + 46, name_len);
        entry_out->name[name_len] = '\0';
        if (dripwave_has_extension_a(entry_out->name, ".swf")) {
            entry_out->method = dripwave_le16(zip_data + cursor + 10);
            entry_out->compressed_size = dripwave_le32(zip_data + cursor + 20);
            entry_out->uncompressed_size = dripwave_le32(zip_data + cursor + 24);
            entry_out->local_offset = dripwave_le32(zip_data + cursor + 42);
            return true;
        }
        cursor += 46u + name_len + extra_len + comment_len;
    }
    return false;
}

static bool dripwave_zip_extract(const uint8_t *zip_data, size_t zip_size, const ZipEntry *entry, uint8_t **out_data, size_t *out_size) {
    uint32_t local_offset = entry->local_offset;
    uint16_t name_len;
    uint16_t extra_len;
    const uint8_t *payload;
    if ((size_t)local_offset + 30 > zip_size || dripwave_le32(zip_data + local_offset) != 0x04034b50u) {
        return false;
    }
    name_len = dripwave_le16(zip_data + local_offset + 26);
    extra_len = dripwave_le16(zip_data + local_offset + 28);
    payload = zip_data + local_offset + 30 + name_len + extra_len;
    if (payload + entry->compressed_size > zip_data + zip_size) {
        return false;
    }
    *out_data = (uint8_t*)malloc(entry->uncompressed_size ? entry->uncompressed_size : entry->compressed_size);
    if (!*out_data) {
        return false;
    }
    if (entry->method == 0) {
        memcpy(*out_data, payload, entry->uncompressed_size);
        *out_size = entry->uncompressed_size;
        return true;
    }
    if (entry->method == 8) {
        z_stream stream;
        int result;
        memset(&stream, 0, sizeof(stream));
        stream.next_in = (Bytef*)payload;
        stream.avail_in = entry->compressed_size;
        stream.next_out = *out_data;
        stream.avail_out = entry->uncompressed_size;
        result = inflateInit2(&stream, -MAX_WBITS);
        if (result != Z_OK) {
            free(*out_data);
            *out_data = NULL;
            return false;
        }
        result = inflate(&stream, Z_FINISH);
        inflateEnd(&stream);
        if (result != Z_STREAM_END) {
            free(*out_data);
            *out_data = NULL;
            return false;
        }
        *out_size = stream.total_out;
        return true;
    }
    free(*out_data);
    *out_data = NULL;
    return false;
}

static bool dripwave_manifest_find_entry_swf(const char *json_text, char *out_path, size_t out_cap) {
    const char *entry_key = strstr(json_text, "\"entry_swf\"");
    const char *cursor = json_text;
    if (entry_key) {
        const char *colon = strchr(entry_key, ':');
        const char *quote = colon ? strchr(colon, '"') : NULL;
        const char *end = quote ? strchr(quote + 1, '"') : NULL;
        if (quote && end && (size_t)(end - quote - 1) < out_cap) {
            memcpy(out_path, quote + 1, (size_t)(end - quote - 1));
            out_path[end - quote - 1] = '\0';
            return true;
        }
    }
    while ((cursor = strchr(cursor, '"')) != NULL) {
        const char *end = strchr(cursor + 1, '"');
        size_t len;
        if (!end) {
            break;
        }
        len = (size_t)(end - cursor - 1);
        if (len > 4 && len < out_cap) {
            memcpy(out_path, cursor + 1, len);
            out_path[len] = '\0';
            if (dripwave_has_extension_a(out_path, ".swf")) {
                return true;
            }
        }
        cursor = end + 1;
    }
    return false;
}

static bool dripwave_create_temp_swf_path(wchar_t *out_path, size_t out_cap) {
    wchar_t temp_dir[MAX_PATH];
    wchar_t temp_file[MAX_PATH];
    if (!GetTempPathW(MAX_PATH, temp_dir)) {
        return false;
    }
    if (!GetTempFileNameW(temp_dir, L"drw", 0, temp_file)) {
        return false;
    }
    DeleteFileW(temp_file);
    _snwprintf(out_path, out_cap - 1, L"%ls.swf", temp_file);
    out_path[out_cap - 1] = L'\0';
    return true;
}

static void dripwave_session_reset(DripwaveSession *session) {
    if (session->temp_owned && session->working_swf_path[0]) {
        DeleteFileW(session->working_swf_path);
    }
    ZeroMemory(session, sizeof(*session));
    session->volume = 75;
    session->last_state_slot = 0;
}

static bool dripwave_load_swf_session(DripwaveSession *session, const wchar_t *swf_path, const wchar_t *display_name, bool is_farim, const wchar_t *source_path, const wchar_t *farim_entry) {
    uint8_t *buffer = NULL;
    size_t size = 0;
    wchar_t error_text[256];
    SwfInfo info;
    dripwave_init_swf_info(&info);
    if (!dripwave_read_entire_file(swf_path, &buffer, &size)) {
        dripwave_set_status(session, L"Failed to read %ls", swf_path);
        return false;
    }
    if (!dripwave_parse_swf_bytes(buffer, size, &info, error_text, 256)) {
        if (!dripwave_is_recognized_swf_signature(buffer, size)) {
            free(buffer);
            dripwave_set_status(session, L"%ls", error_text);
            return false;
        }
        dripwave_populate_fallback_swf_info(buffer, size, &info);
    }
    free(buffer);
    session->loaded = true;
    session->is_farim = is_farim;
    session->playing = false;
    session->current_frame = 0;
    session->frame_accumulator = 0.0;
    session->swf = info;
    wcsncpy(session->source_path, source_path, MAX_PATH - 1);
    wcsncpy(session->working_swf_path, swf_path, MAX_PATH - 1);
    wcsncpy(session->display_name, display_name, DRIPWAVE_TAB_CAP - 1);
    session->last_state_slot = dripwave_resolve_last_state_slot(session->source_path);
    dripwave_build_state_meta_path(session->source_path, session->state_meta_path, MAX_PATH);
    dripwave_build_state_path(session->source_path, session->last_state_slot, session->state_path, MAX_PATH);
    if (farim_entry) {
        wcsncpy(session->farim_entry, farim_entry, MAX_PATH - 1);
    }
    dripwave_refresh_loaded_status(session, NULL);
    return true;
}

static bool dripwave_load_farim_session(DripwaveSession *session, const wchar_t *farim_path) {
    uint8_t *zip_data = NULL;
    size_t zip_size = 0;
    ZipEntry manifest_entry;
    ZipEntry swf_entry;
    uint8_t *manifest_data = NULL;
    uint8_t *manifest_expanded = NULL;
    size_t manifest_size = 0;
    uint8_t *swf_data = NULL;
    size_t swf_size = 0;
    char manifest_swf[260] = {0};
    wchar_t temp_swf[MAX_PATH];
    wchar_t swf_entry_w[MAX_PATH];
    bool have_manifest = false;

    if (!dripwave_read_entire_file(farim_path, &zip_data, &zip_size)) {
        dripwave_set_status(session, L"Failed to read FARIM package.");
        return false;
    }
    if (dripwave_zip_locate_entry(zip_data, zip_size, "farim_manifest.json", &manifest_entry)) {
        if (!dripwave_zip_extract(zip_data, zip_size, &manifest_entry, &manifest_data, &manifest_size)) {
            free(zip_data);
            dripwave_set_status(session, L"Failed to extract farim_manifest.json.");
            return false;
        }
        manifest_expanded = (uint8_t*)realloc(manifest_data, manifest_size + 1);
        if (!manifest_expanded) {
            free(manifest_data);
            free(zip_data);
            dripwave_set_status(session, L"Out of memory while loading farim_manifest.json.");
            return false;
        }
        manifest_data = manifest_expanded;
        manifest_data[manifest_size] = 0;
        have_manifest = true;
    }

    if (have_manifest && dripwave_manifest_find_entry_swf((const char*)manifest_data, manifest_swf, sizeof(manifest_swf))) {
        if (!dripwave_zip_locate_entry(zip_data, zip_size, manifest_swf, &swf_entry)) {
            free(manifest_data);
            free(zip_data);
            dripwave_set_status(session, L"Manifest referenced %S but it was not found in the FARIM package.", manifest_swf);
            return false;
        }
    } else if (!dripwave_zip_find_first_swf(zip_data, zip_size, &swf_entry)) {
        free(manifest_data);
        free(zip_data);
        dripwave_set_status(session, L"No embedded .swf entry was found in the FARIM package.");
        return false;
    }

    if (!dripwave_zip_extract(zip_data, zip_size, &swf_entry, &swf_data, &swf_size)) {
        free(manifest_data);
        free(zip_data);
        dripwave_set_status(session, L"Failed to extract the embedded SWF from the FARIM package.");
        return false;
    }
    if (!dripwave_create_temp_swf_path(temp_swf, MAX_PATH) || !dripwave_write_entire_file(temp_swf, swf_data, swf_size)) {
        free(swf_data);
        free(manifest_data);
        free(zip_data);
        dripwave_set_status(session, L"Failed to materialize the embedded SWF to a temporary file.");
        return false;
    }

    session->temp_owned = true;
    MultiByteToWideChar(CP_UTF8, 0, swf_entry.name, -1, swf_entry_w, MAX_PATH);
    if (!dripwave_load_swf_session(session, temp_swf, dripwave_file_name(farim_path), true, farim_path, swf_entry_w)) {
        DeleteFileW(temp_swf);
        session->temp_owned = false;
        free(swf_data);
        free(manifest_data);
        free(zip_data);
        return false;
    }

    free(swf_data);
    free(manifest_data);
    free(zip_data);
    return true;
}

static void dripwave_update_status_label(void) {
    if (g_app.active_index >= 0 && g_app.active_index < g_app.session_count) {
        SetWindowTextW(g_app.status_label, g_app.sessions[g_app.active_index].status);
    } else {
        SetWindowTextW(g_app.status_label, L"Open a .swf or .farim package.");
    }
    dripwave_update_runtime_button();
}

static bool dripwave_pick_backend_path(HWND hwnd) {
    OPENFILENAMEW ofn;
    wchar_t path[MAX_PATH] = L"";

    ZeroMemory(&ofn, sizeof(ofn));
    ofn.lStructSize = sizeof(ofn);
    ofn.hwndOwner = hwnd;
    ofn.lpstrFilter = L"Executable Files\0*.exe\0All Files\0*.*\0";
    ofn.lpstrFile = path;
    ofn.nMaxFile = MAX_PATH;
    ofn.Flags = OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST;
    ofn.lpstrTitle = L"Select an SWF execution backend";

    if (!GetOpenFileNameW(&ofn)) {
        return false;
    }

    if (!dripwave_file_exists(path)) {
        return false;
    }

    dripwave_assign_backend_path(path, DRIPWAVE_BACKEND_USER_SELECTED);
    return true;
}

static bool dripwave_launch_configured_backend(DripwaveSession *session, wchar_t *error_text, size_t error_cap) {
    STARTUPINFOW startup_info;
    PROCESS_INFORMATION process_info;
    wchar_t command_line[(MAX_PATH * 2) + 8];

    if (!session || !session->loaded) {
        _snwprintf(error_text, error_cap - 1, L"No active SWF session is loaded.");
        error_text[error_cap - 1] = L'\0';
        return false;
    }

    _snwprintf(command_line, (sizeof(command_line) / sizeof(command_line[0])) - 1, L"\"%ls\" \"%ls\"", g_app.backend_path, session->working_swf_path);
    command_line[(sizeof(command_line) / sizeof(command_line[0])) - 1] = L'\0';

    ZeroMemory(&startup_info, sizeof(startup_info));
    ZeroMemory(&process_info, sizeof(process_info));
    startup_info.cb = sizeof(startup_info);
    if (!CreateProcessW(NULL, command_line, NULL, NULL, FALSE, 0, NULL, NULL, &startup_info, &process_info)) {
        _snwprintf(error_text, error_cap - 1, L"Failed to launch backend process (%lu).", GetLastError());
        error_text[error_cap - 1] = L'\0';
        return false;
    }

    CloseHandle(process_info.hProcess);
    CloseHandle(process_info.hThread);
    _snwprintf(error_text, error_cap - 1, L"Launched backend: %ls", dripwave_file_name(g_app.backend_path));
    error_text[error_cap - 1] = L'\0';
    return true;
}

static bool dripwave_launch_via_file_association(DripwaveSession *session, wchar_t *error_text, size_t error_cap) {
    HINSTANCE result;

    if (!session || !session->loaded) {
        _snwprintf(error_text, error_cap - 1, L"No active SWF session is loaded.");
        error_text[error_cap - 1] = L'\0';
        return false;
    }

    result = ShellExecuteW(g_app.window, L"open", session->working_swf_path, NULL, NULL, SW_SHOWNORMAL);
    if ((INT_PTR)result > 32) {
        _snwprintf(error_text, error_cap - 1, L"Launched via Windows file association.");
        error_text[error_cap - 1] = L'\0';
        return true;
    }

    if ((INT_PTR)result == SE_ERR_NOASSOC) {
        _snwprintf(error_text, error_cap - 1, L"No execution backend was configured, and Windows has no default .swf handler.");
        error_text[error_cap - 1] = L'\0';
        return false;
    }

    _snwprintf(error_text, error_cap - 1, L"Windows could not open this SWF directly (ShellExecute code %Id).", (INT_PTR)result);
    error_text[error_cap - 1] = L'\0';
    return false;
}

static bool dripwave_launch_backend_for_session(HWND hwnd, DripwaveSession *session, wchar_t *error_text, size_t error_cap) {
    if (!session || !session->loaded) {
        _snwprintf(error_text, error_cap - 1, L"No active SWF session is loaded.");
        error_text[error_cap - 1] = L'\0';
        return false;
    }

    if (!dripwave_swf_needs_projector(&session->swf)) {
        _snwprintf(error_text, error_cap - 1, L"Native inspector active: %ls", dripwave_swf_runtime_profile(&session->swf));
        error_text[error_cap - 1] = L'\0';
        return true;
    }

    if (!g_app.backend_available) {
        dripwave_detect_backend();
    }
    if (g_app.backend_available) {
        return dripwave_launch_configured_backend(session, error_text, error_cap);
    }
    if (dripwave_launch_via_file_association(session, error_text, error_cap)) {
        return true;
    }
    if (dripwave_pick_backend_path(hwnd)) {
        return dripwave_launch_configured_backend(session, error_text, error_cap);
    }

    _snwprintf(error_text, error_cap - 1, L"%ls. Choose ruffle_desktop.exe or a standalone Flash player when prompted, or place one next to dripwave.exe.", dripwave_swf_backend_requirement(&session->swf));
    error_text[error_cap - 1] = L'\0';
    return false;
}

static bool dripwave_find_authoring_script(wchar_t *out_path, size_t out_cap) {
    wchar_t module_path[MAX_PATH];
    wchar_t module_dir[MAX_PATH];
    wchar_t candidate[MAX_PATH];
    wchar_t *slash;
    if (!GetModuleFileNameW(NULL, module_path, MAX_PATH)) {
        return false;
    }
    wcsncpy(module_dir, module_path, MAX_PATH - 1);
    module_dir[MAX_PATH - 1] = L'\0';
    slash = wcsrchr(module_dir, L'\\');
    if (!slash) {
        return false;
    }
    *slash = L'\0';

    _snwprintf(candidate, MAX_PATH - 1, L"%ls\\..\\tools\\dripwave_authoring.py", module_dir);
    candidate[MAX_PATH - 1] = L'\0';
    if (dripwave_file_exists(candidate)) {
        GetFullPathNameW(candidate, (DWORD)out_cap, out_path, NULL);
        return true;
    }

    _snwprintf(candidate, MAX_PATH - 1, L"%ls\\tools\\dripwave_authoring.py", module_dir);
    candidate[MAX_PATH - 1] = L'\0';
    if (dripwave_file_exists(candidate)) {
        GetFullPathNameW(candidate, (DWORD)out_cap, out_path, NULL);
        return true;
    }
    return false;
}

static bool dripwave_find_python_gui(wchar_t *out_path, size_t out_cap) {
    wchar_t module_path[MAX_PATH];
    wchar_t search_dir[MAX_PATH];
    wchar_t candidate[MAX_PATH];
    wchar_t resolved[MAX_PATH];
    wchar_t *slash;
    DWORD found;
    if (!GetModuleFileNameW(NULL, module_path, MAX_PATH)) {
        return false;
    }
    wcsncpy(search_dir, module_path, MAX_PATH - 1);
    search_dir[MAX_PATH - 1] = L'\0';
    slash = wcsrchr(search_dir, L'\\');
    if (!slash) {
        return false;
    }
    *slash = L'\0';
    for (int i = 0; i < 6; ++i) {
        _snwprintf(candidate, MAX_PATH - 1, L"%ls\\.venv\\Scripts\\pythonw.exe", search_dir);
        candidate[MAX_PATH - 1] = L'\0';
        if (dripwave_file_exists(candidate)) {
            GetFullPathNameW(candidate, (DWORD)out_cap, out_path, NULL);
            return true;
        }
        _snwprintf(candidate, MAX_PATH - 1, L"%ls\\.venv\\Scripts\\python.exe", search_dir);
        candidate[MAX_PATH - 1] = L'\0';
        if (dripwave_file_exists(candidate)) {
            GetFullPathNameW(candidate, (DWORD)out_cap, out_path, NULL);
            return true;
        }
        slash = wcsrchr(search_dir, L'\\');
        if (!slash) {
            break;
        }
        *slash = L'\0';
    }
    found = SearchPathW(NULL, L"pythonw.exe", NULL, MAX_PATH, resolved, NULL);
    if (found > 0 && found < MAX_PATH) {
        wcsncpy(out_path, resolved, out_cap - 1);
        out_path[out_cap - 1] = L'\0';
        return true;
    }
    found = SearchPathW(NULL, L"python.exe", NULL, MAX_PATH, resolved, NULL);
    if (found > 0 && found < MAX_PATH) {
        wcsncpy(out_path, resolved, out_cap - 1);
        out_path[out_cap - 1] = L'\0';
        return true;
    }
    return false;
}

static bool dripwave_launch_authoring_shell(HWND hwnd, wchar_t *error_text, size_t error_cap) {
    wchar_t script_path[MAX_PATH];
    wchar_t python_path[MAX_PATH];
    wchar_t parameters[MAX_PATH * 2];
    HINSTANCE result;
    if (!dripwave_find_authoring_script(script_path, MAX_PATH)) {
        _snwprintf(error_text, error_cap - 1, L"dripwave authoring shell was not found beside this build.");
        error_text[error_cap - 1] = L'\0';
        return false;
    }
    if (!dripwave_find_python_gui(python_path, MAX_PATH)) {
        _snwprintf(error_text, error_cap - 1, L"Python was not found for launching the dripwave authoring shell.");
        error_text[error_cap - 1] = L'\0';
        return false;
    }
    _snwprintf(parameters, (sizeof(parameters) / sizeof(parameters[0])) - 1, L"\"%ls\"", script_path);
    parameters[(sizeof(parameters) / sizeof(parameters[0])) - 1] = L'\0';
    result = ShellExecuteW(hwnd, L"open", python_path, parameters, NULL, SW_SHOWNORMAL);
    if ((INT_PTR)result <= 32) {
        _snwprintf(error_text, error_cap - 1, L"Failed to launch authoring shell (ShellExecute code %Id).", (INT_PTR)result);
        error_text[error_cap - 1] = L'\0';
        return false;
    }
    _snwprintf(error_text, error_cap - 1, L"Opened dripwave authoring shell.");
    error_text[error_cap - 1] = L'\0';
    return true;
}

static bool dripwave_open_recent_selection(HWND hwnd) {
    int selection;
    if (!g_app.recent_combo || g_app.recent_count <= 0) {
        MessageBoxW(hwnd, L"No recent SWF or FARIM entries are available yet.", L"dripwave", MB_ICONINFORMATION | MB_OK);
        return false;
    }
    selection = (int)SendMessageW(g_app.recent_combo, CB_GETCURSEL, 0, 0);
    if (selection < 0 || selection >= g_app.recent_count) {
        MessageBoxW(hwnd, L"Choose a recent entry first.", L"dripwave", MB_ICONINFORMATION | MB_OK);
        return false;
    }
    if (!dripwave_file_exists(g_app.recent_entries[selection].path)) {
        MessageBoxW(hwnd, L"That recent entry no longer exists on disk.", L"dripwave", MB_ICONERROR | MB_OK);
        return false;
    }
    return dripwave_add_session_from_path(hwnd, g_app.recent_entries[selection].path);
}

static void dripwave_remove_session(int index) {
    wchar_t ignored_status[DRIPWAVE_STATUS_CAP];
    if (index < 0 || index >= g_app.session_count) {
        return;
    }

    if (g_app.sessions[index].loaded) {
        dripwave_save_state_for_session(&g_app.sessions[index], g_app.sessions[index].last_state_slot, ignored_status, DRIPWAVE_STATUS_CAP);
    }
    dripwave_session_reset(&g_app.sessions[index]);
    for (int i = index; i < g_app.session_count - 1; ++i) {
        g_app.sessions[i] = g_app.sessions[i + 1];
    }
    g_app.session_count--;
    if (g_app.session_count >= 0) {
        ZeroMemory(&g_app.sessions[g_app.session_count], sizeof(DripwaveSession));
        g_app.sessions[g_app.session_count].volume = 75;
    }
    TabCtrl_DeleteItem(g_app.tab_control, index);
    dripwave_refresh_tab_titles();

    if (g_app.session_count == 0) {
        g_app.active_index = -1;
        dripwave_update_status_label();
        InvalidateRect(g_app.canvas, NULL, TRUE);
        return;
    }

    if (g_app.active_index > index) {
        g_app.active_index--;
    } else if (g_app.active_index >= g_app.session_count) {
        g_app.active_index = g_app.session_count - 1;
    }
    dripwave_select_session(g_app.active_index);
}

static void dripwave_refresh_tab_titles(void) {
    TCITEMW item;
    wchar_t tab_text[DRIPWAVE_TAB_CAP + 8];
    ZeroMemory(&item, sizeof(item));
    item.mask = TCIF_TEXT;
    for (int i = 0; i < g_app.session_count; ++i) {
        dripwave_format_tab_title(&g_app.sessions[i], tab_text, sizeof(tab_text) / sizeof(tab_text[0]));
        item.pszText = tab_text;
        TabCtrl_SetItem(g_app.tab_control, i, &item);
    }
}

static int dripwave_tab_close_hit_test(POINT client_point) {
    TCHITTESTINFO hit;
    RECT tab_rect;
    RECT close_rect;
    int tab_index;
    ZeroMemory(&hit, sizeof(hit));
    hit.pt = client_point;
    tab_index = TabCtrl_HitTest(g_app.tab_control, &hit);
    if (tab_index < 0) {
        return -1;
    }
    if (!TabCtrl_GetItemRect(g_app.tab_control, tab_index, &tab_rect)) {
        return -1;
    }
    close_rect = tab_rect;
    close_rect.left = max(tab_rect.right - 20, tab_rect.left);
    InflateRect(&close_rect, 0, -4);
    return PtInRect(&close_rect, client_point) ? tab_index : -1;
}

static void dripwave_select_session(int index) {
    if (index < 0 || index >= g_app.session_count) {
        return;
    }
    g_app.active_index = index;
    TabCtrl_SetCurSel(g_app.tab_control, index);
    if (g_app.sessions[index].loaded) {
        SendMessageW(g_app.volume_slider, TBM_SETPOS, TRUE, g_app.sessions[index].volume);
        g_app.selected_state_slot = g_app.sessions[index].last_state_slot;
        if (g_app.slot_combo) {
            SendMessageW(g_app.slot_combo, CB_SETCURSEL, g_app.selected_state_slot, 0);
        }
    }
    dripwave_update_status_label();
    dripwave_update_runtime_button();
    InvalidateRect(g_app.canvas, NULL, TRUE);
}

static void dripwave_match_window_to_stage(HWND hwnd, const SwfInfo *swf) {
    RECT client = {0, 0, max(swf->width_px, 760), max(swf->height_px + 174 + (g_app.controls_visible ? 56 : 0), 480)};
    RECT work_area;
    AdjustWindowRectEx(&client, WS_OVERLAPPEDWINDOW, FALSE, 0);
    SystemParametersInfoW(SPI_GETWORKAREA, 0, &work_area, 0);
    if (client.right - client.left > work_area.right - work_area.left) {
        client.right = client.left + (work_area.right - work_area.left);
    }
    if (client.bottom - client.top > work_area.bottom - work_area.top) {
        client.bottom = client.top + (work_area.bottom - work_area.top);
    }
    SetWindowPos(hwnd, NULL, CW_USEDEFAULT, CW_USEDEFAULT, client.right - client.left, client.bottom - client.top, SWP_NOZORDER | SWP_NOMOVE);
}

static bool dripwave_add_session_from_path(HWND hwnd, const wchar_t *path) {
    DripwaveSession session;
    TCITEMW item;
    wchar_t tab_text[DRIPWAVE_TAB_CAP + 8];
    wchar_t state_status[DRIPWAVE_STATUS_CAP];
    bool ok = false;
    ZeroMemory(&session, sizeof(session));
    session.volume = 75;

    if (g_app.session_count >= DRIPWAVE_MAX_SESSIONS) {
        MessageBoxW(hwnd, L"Maximum tab count reached.", L"dripwave", MB_ICONWARNING | MB_OK);
        return false;
    }

    if (_wcsicmp(dripwave_extension(path), L".farim") == 0) {
        ok = dripwave_load_farim_session(&session, path);
    } else {
        ok = dripwave_load_swf_session(&session, path, dripwave_file_name(path), false, path, NULL);
    }
    if (!ok) {
        MessageBoxW(hwnd, session.status[0] ? session.status : L"Failed to load file.", L"dripwave", MB_ICONERROR | MB_OK);
        dripwave_session_reset(&session);
        return false;
    }

    if (dripwave_load_state_for_session(&session, session.last_state_slot, true, state_status, DRIPWAVE_STATUS_CAP)) {
        dripwave_refresh_loaded_status(&session, state_status);
    }

    g_app.sessions[g_app.session_count] = session;
    g_app.session_count++;
    dripwave_register_recent_path(path, session.display_name);
    ZeroMemory(&item, sizeof(item));
    item.mask = TCIF_TEXT;
    dripwave_format_tab_title(&g_app.sessions[g_app.session_count - 1], tab_text, sizeof(tab_text) / sizeof(tab_text[0]));
    item.pszText = tab_text;
    TabCtrl_InsertItem(g_app.tab_control, g_app.session_count - 1, &item);
    dripwave_refresh_tab_titles();
    dripwave_select_session(g_app.session_count - 1);
    dripwave_match_window_to_stage(hwnd, &session.swf);
    return true;
}

static void dripwave_open_dialog(HWND hwnd) {
    OPENFILENAMEW ofn;
    wchar_t path[MAX_PATH] = L"";
    ZeroMemory(&ofn, sizeof(ofn));
    ofn.lStructSize = sizeof(ofn);
    ofn.hwndOwner = hwnd;
    ofn.lpstrFilter = L"SWF and FARIM\0*.swf;*.farim\0SWF\0*.swf\0FARIM\0*.farim\0All Files\0*.*\0";
    ofn.lpstrFile = path;
    ofn.nMaxFile = MAX_PATH;
    ofn.Flags = OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST;
    if (GetOpenFileNameW(&ofn)) {
        dripwave_add_session_from_path(hwnd, path);
    }
}

static bool dripwave_smoke_test_path(const wchar_t *path) {
    DripwaveSession session;
    bool ok;
    ZeroMemory(&session, sizeof(session));
    session.volume = 75;

    if (_wcsicmp(dripwave_extension(path), L".farim") == 0) {
        ok = dripwave_load_farim_session(&session, path);
    } else {
        ok = dripwave_load_swf_session(&session, path, dripwave_file_name(path), false, path, NULL);
    }

    if (ok) {
        fwprintf(stdout, L"OK: %ls\n", session.status);
    } else {
        fwprintf(stderr, L"FAIL: %ls -> %ls\n", path, session.status[0] ? session.status : L"load failed");
    }
    dripwave_session_reset(&session);
    return ok;
}

static bool dripwave_inspect_path(const wchar_t *path) {
    DripwaveSession session;
    bool ok;
    ZeroMemory(&session, sizeof(session));
    session.volume = 75;

    if (_wcsicmp(dripwave_extension(path), L".farim") == 0) {
        ok = dripwave_load_farim_session(&session, path);
    } else {
        ok = dripwave_load_swf_session(&session, path, dripwave_file_name(path), false, path, NULL);
    }

    if (!ok) {
        fwprintf(stderr, L"FAIL: %ls -> %ls\n", path, session.status[0] ? session.status : L"load failed");
        dripwave_session_reset(&session);
        return false;
    }

    fwprintf(stdout, L"OK: %ls\n", path);
    fwprintf(stdout, L"  profile: %ls\n", dripwave_swf_runtime_profile(&session.swf));
    fwprintf(stdout, L"  backend: %ls\n", dripwave_swf_backend_requirement(&session.swf));
    fwprintf(stdout, L"  stage: %dx%d\n", session.swf.width_px, session.swf.height_px);
    fwprintf(stdout, L"  metadata: %ls\n", session.swf.metadata_complete ? L"complete" : L"compatibility mode");
    fwprintf(stdout, L"  actionscript: avm1=%ls avm2=%ls\n", session.swf.uses_avm1 ? L"yes" : L"no", session.swf.uses_avm2 ? L"yes" : L"no");
    fwprintf(stdout, L"  features: buttons=%ls edit_text=%ls sprites=%ls video=%ls sound_stream=%ls binary_data=%ls network=%ls\n",
        session.swf.has_buttons ? L"yes" : L"no",
        session.swf.has_edit_text ? L"yes" : L"no",
        session.swf.has_sprites ? L"yes" : L"no",
        session.swf.has_video ? L"yes" : L"no",
        session.swf.has_sound_stream ? L"yes" : L"no",
        session.swf.has_binary_data ? L"yes" : L"no",
        session.swf.uses_network ? L"yes" : L"no");
    fwprintf(stdout, L"  tags: count=%d scan=%ls labels=%d\n", session.swf.tag_count, session.swf.tag_scan_complete ? L"complete" : L"partial", session.swf.frame_label_count);

    dripwave_session_reset(&session);
    return true;
}

static void dripwave_attach_console(void) {
    if (AttachConsole(ATTACH_PARENT_PROCESS) || GetLastError() == ERROR_ACCESS_DENIED) {
        FILE *stream = NULL;
        freopen_s(&stream, "CONOUT$", "w", stdout);
        freopen_s(&stream, "CONOUT$", "w", stderr);
    }
}

static void dripwave_layout(HWND hwnd) {
    RECT rc;
    int width;
    int height;
    int top_h = 64;
    int tab_h = 28;
    int status_h = 22;
    int controller_h = g_app.controls_visible ? 60 : 0;
    int y;
    GetClientRect(hwnd, &rc);
    width = rc.right - rc.left;
    height = rc.bottom - rc.top;

    MoveWindow(g_app.open_button, 8, 6, 72, 24, TRUE);
    MoveWindow(g_app.run_button, 88, 6, 98, 24, TRUE);
    MoveWindow(g_app.save_button, 194, 6, 84, 24, TRUE);
    MoveWindow(g_app.load_button, 286, 6, 84, 24, TRUE);
    MoveWindow(g_app.slot_combo, 378, 6, 138, 400, TRUE);
    MoveWindow(g_app.fit_combo, width - 166, 6, 158, 400, TRUE);

    {
        int controls_x = width - 8 - 86;
        int close_x = controls_x - 8 - 86;
        int author_x = close_x - 8 - 108;
        int recent_button_x = author_x - 8 - 102;
        int recent_width = max(recent_button_x - 16, 220);
        MoveWindow(g_app.recent_combo, 8, 36, recent_width, 300, TRUE);
        MoveWindow(g_app.recent_button, recent_button_x, 36, 102, 24, TRUE);
        MoveWindow(g_app.author_button, author_x, 36, 108, 24, TRUE);
        MoveWindow(g_app.close_button, close_x, 36, 86, 24, TRUE);
        MoveWindow(g_app.toggle_button, controls_x, 36, 86, 24, TRUE);
    }

    y = top_h;
    MoveWindow(g_app.tab_control, 8, y, width - 16, tab_h, TRUE);
    y += tab_h + 4;
    MoveWindow(g_app.canvas, 8, y, width - 16, max(height - y - status_h - controller_h - 12, 120), TRUE);
    y += max(height - y - status_h - controller_h - 12, 120) + 4;
    MoveWindow(g_app.status_label, 8, y, width - 16, status_h, TRUE);
    y += status_h + 4;

    ShowWindow(g_app.skip_start, g_app.controls_visible ? SW_SHOW : SW_HIDE);
    ShowWindow(g_app.frame_back, g_app.controls_visible ? SW_SHOW : SW_HIDE);
    ShowWindow(g_app.play_pause, g_app.controls_visible ? SW_SHOW : SW_HIDE);
    ShowWindow(g_app.frame_fwd, g_app.controls_visible ? SW_SHOW : SW_HIDE);
    ShowWindow(g_app.skip_end, g_app.controls_visible ? SW_SHOW : SW_HIDE);
    ShowWindow(g_app.dead_stop, g_app.controls_visible ? SW_SHOW : SW_HIDE);
    ShowWindow(g_app.volume_slider, g_app.controls_visible ? SW_SHOW : SW_HIDE);

    if (g_app.controls_visible) {
        int center = width / 2;
        MoveWindow(g_app.skip_start, center - 188, y + 10, 48, 32, TRUE);
        MoveWindow(g_app.frame_back, center - 132, y + 10, 48, 32, TRUE);
        MoveWindow(g_app.play_pause, center - 34, y + 2, 68, 48, TRUE);
        MoveWindow(g_app.frame_fwd, center + 84, y + 10, 48, 32, TRUE);
        MoveWindow(g_app.skip_end, center + 140, y + 10, 48, 32, TRUE);
        MoveWindow(g_app.dead_stop, center + 196, y + 10, 56, 32, TRUE);
        MoveWindow(g_app.volume_slider, 8, y + 16, max(center - 212, 120), 28, TRUE);
    }
}

static void dripwave_update_play_button(void) {
    InvalidateRect(g_app.play_pause, NULL, TRUE);
}

static DripwaveSession *dripwave_active_session(void) {
    if (g_app.active_index < 0 || g_app.active_index >= g_app.session_count) {
        return NULL;
    }
    return &g_app.sessions[g_app.active_index];
}

static void dripwave_step_frame(DripwaveSession *session, int delta) {
    if (!session || !session->loaded) {
        return;
    }
    session->playing = false;
    session->current_frame += delta;
    if (session->current_frame < 0) {
        session->current_frame = 0;
    }
    if (session->current_frame >= max(session->swf.frame_count, 1)) {
        session->current_frame = max(session->swf.frame_count - 1, 0);
    }
    dripwave_set_status(session, L"%ls | frame %d / %d", session->display_name, session->current_frame + 1, session->swf.frame_count);
    dripwave_update_status_label();
    dripwave_update_play_button();
    InvalidateRect(g_app.canvas, NULL, TRUE);
}

static void dripwave_handle_command(HWND hwnd, int id, int code) {
    DripwaveSession *session = dripwave_active_session();
    if (id == IDC_OPEN_BUTTON && code == BN_CLICKED) {
        dripwave_open_dialog(hwnd);
    } else if (id == IDC_OPEN_RECENT && code == BN_CLICKED) {
        dripwave_open_recent_selection(hwnd);
    } else if (id == IDC_AUTHORING && code == BN_CLICKED) {
        wchar_t authoring_status[DRIPWAVE_STATUS_CAP];
        if (!dripwave_launch_authoring_shell(hwnd, authoring_status, DRIPWAVE_STATUS_CAP)) {
            MessageBoxW(hwnd, authoring_status, L"dripwave", MB_ICONERROR | MB_OK);
            return;
        }
        if (session && session->loaded) {
            dripwave_set_status(session, L"%ls | %ls", session->display_name, authoring_status);
            dripwave_update_status_label();
        } else {
            SetWindowTextW(g_app.status_label, authoring_status);
        }
    } else if (id == IDC_RUN_BACKEND && code == BN_CLICKED) {
        wchar_t launch_status[DRIPWAVE_STATUS_CAP];
        if (!dripwave_launch_backend_for_session(hwnd, session, launch_status, DRIPWAVE_STATUS_CAP)) {
            MessageBoxW(hwnd, launch_status, L"dripwave", MB_ICONERROR | MB_OK);
            return;
        }
        dripwave_set_status(session, L"%ls | %ls", session->display_name, launch_status);
        dripwave_update_status_label();
    } else if (id == IDC_SAVE_STATE && code == BN_CLICKED) {
        wchar_t save_status[DRIPWAVE_STATUS_CAP];
        int slot = dripwave_current_state_slot();
        if (!dripwave_save_state_for_session(session, slot, save_status, DRIPWAVE_STATUS_CAP)) {
            MessageBoxW(hwnd, save_status, L"dripwave", MB_ICONERROR | MB_OK);
            return;
        }
        dripwave_set_status(session, L"%ls | %ls", session->display_name, save_status);
        dripwave_update_status_label();
    } else if (id == IDC_LOAD_STATE && code == BN_CLICKED) {
        wchar_t load_status[DRIPWAVE_STATUS_CAP];
        int slot = dripwave_current_state_slot();
        if (!dripwave_load_state_for_session(session, slot, true, load_status, DRIPWAVE_STATUS_CAP)) {
            MessageBoxW(hwnd, load_status, L"dripwave", MB_ICONINFORMATION | MB_OK);
            return;
        }
        SendMessageW(g_app.volume_slider, TBM_SETPOS, TRUE, session->volume);
        dripwave_set_status(session, L"%ls | %ls", session->display_name, load_status);
        dripwave_update_status_label();
        dripwave_update_play_button();
        InvalidateRect(g_app.canvas, NULL, TRUE);
    } else if (id == IDC_STATE_SLOT && code == CBN_SELCHANGE) {
        int slot = dripwave_current_state_slot();
        if (session && session->loaded) {
            session->last_state_slot = slot;
            dripwave_set_status(session, L"%ls | active slot: %ls", session->display_name, dripwave_state_slot_label(slot));
            dripwave_update_status_label();
        }
    } else if (id == IDC_CLOSE_TAB && code == BN_CLICKED) {
        if (g_app.active_index >= 0) {
            dripwave_remove_session(g_app.active_index);
        }
    } else if (id == IDC_TOGGLE_CONTROLS && code == BN_CLICKED) {
        g_app.controls_visible = !g_app.controls_visible;
        dripwave_layout(hwnd);
    } else if (!session || !session->loaded) {
        return;
    } else if (id == IDC_SKIP_START && code == BN_CLICKED) {
        session->playing = false;
        session->current_frame = 0;
        session->frame_accumulator = 0.0;
        dripwave_step_frame(session, 0);
    } else if (id == IDC_FRAME_BACK && code == BN_CLICKED) {
        dripwave_step_frame(session, -1);
    } else if (id == IDC_PLAY_PAUSE && code == BN_CLICKED) {
        session->playing = !session->playing;
        dripwave_set_status(session, L"%ls | %ls", session->display_name, session->playing ? L"playing" : L"paused");
        dripwave_update_status_label();
        dripwave_update_play_button();
    } else if (id == IDC_FRAME_FWD && code == BN_CLICKED) {
        dripwave_step_frame(session, 1);
    } else if (id == IDC_SKIP_END && code == BN_CLICKED) {
        session->playing = false;
        session->current_frame = max(session->swf.frame_count - 1, 0);
        session->frame_accumulator = 0.0;
        dripwave_step_frame(session, 0);
    } else if (id == IDC_DEAD_STOP && code == BN_CLICKED) {
        session->playing = false;
        session->current_frame = 0;
        session->frame_accumulator = 0.0;
        dripwave_set_status(session, L"%ls | stopped", session->display_name);
        dripwave_update_status_label();
        dripwave_update_play_button();
        InvalidateRect(g_app.canvas, NULL, TRUE);
    } else if (id == IDC_FIT_MODE && code == CBN_SELCHANGE) {
        g_app.fit_mode = (DripwaveFitMode)SendMessageW(g_app.fit_combo, CB_GETCURSEL, 0, 0);
        InvalidateRect(g_app.canvas, NULL, TRUE);
    }
}

static COLORREF dripwave_lerp_color(COLORREF from, COLORREF to, double t) {
    int red = (int)(GetRValue(from) + (GetRValue(to) - GetRValue(from)) * t);
    int green = (int)(GetGValue(from) + (GetGValue(to) - GetGValue(from)) * t);
    int blue = (int)(GetBValue(from) + (GetBValue(to) - GetBValue(from)) * t);
    return RGB(red, green, blue);
}

static void dripwave_fill_gradient_bands(HDC dc, const RECT *rc, COLORREF from, COLORREF to, int bands) {
    RECT band = *rc;
    int height = max(rc->bottom - rc->top, 1);
    bands = max(bands, 1);
    for (int index = 0; index < bands; ++index) {
        int top = rc->top + (height * index) / bands;
        int bottom = rc->top + (height * (index + 1)) / bands;
        HBRUSH brush = CreateSolidBrush(dripwave_lerp_color(from, to, bands == 1 ? 0.0 : (double)index / (double)(bands - 1)));
        band.top = top;
        band.bottom = max(top + 1, bottom);
        FillRect(dc, &band, brush);
        DeleteObject(brush);
    }
}

static void dripwave_draw_signal_slashes(HDC dc, const RECT *rc, COLORREF color) {
    HPEN pen = CreatePen(PS_SOLID, 2, color);
    HPEN old_pen = SelectObject(dc, pen);
    int origin_x = rc->right - 34;
    int origin_y = rc->top + 10;
    for (int index = 0; index < 3; ++index) {
        int x = origin_x - (index * 12);
        int y = origin_y + (index * 4);
        MoveToEx(dc, x, y, NULL);
        LineTo(dc, x + 12, y + 9);
    }
    SelectObject(dc, old_pen);
    DeleteObject(pen);
}

static void dripwave_draw_frame_corners(HDC dc, const RECT *rc, COLORREF color) {
    HPEN pen = CreatePen(PS_SOLID, 3, color);
    HPEN old_pen = SelectObject(dc, pen);
    int length = 18;

    MoveToEx(dc, rc->left, rc->top + length, NULL);
    LineTo(dc, rc->left, rc->top);
    LineTo(dc, rc->left + length, rc->top);

    MoveToEx(dc, rc->right - length, rc->top, NULL);
    LineTo(dc, rc->right, rc->top);
    LineTo(dc, rc->right, rc->top + length);

    MoveToEx(dc, rc->left, rc->bottom - length, NULL);
    LineTo(dc, rc->left, rc->bottom);
    LineTo(dc, rc->left + length, rc->bottom);

    MoveToEx(dc, rc->right - length, rc->bottom, NULL);
    LineTo(dc, rc->right, rc->bottom);
    LineTo(dc, rc->right, rc->bottom - length);

    SelectObject(dc, old_pen);
    DeleteObject(pen);
}

static void dripwave_draw_panel(HDC dc, const RECT *rc, COLORREF top_fill, COLORREF bottom_fill, COLORREF border, COLORREF accent) {
    RECT inset = *rc;
    HBRUSH accent_brush;
    HPEN border_pen;
    HPEN old_pen;
    HBRUSH old_brush;

    dripwave_fill_gradient_bands(dc, rc, top_fill, bottom_fill, 12);

    accent_brush = CreateSolidBrush(accent);
    inset.bottom = min(rc->top + 6, rc->bottom);
    FillRect(dc, &inset, accent_brush);
    DeleteObject(accent_brush);

    border_pen = CreatePen(PS_SOLID, 2, border);
    old_pen = SelectObject(dc, border_pen);
    old_brush = SelectObject(dc, GetStockObject(NULL_BRUSH));
    RoundRect(dc, rc->left, rc->top, rc->right, rc->bottom, 16, 16);
    SelectObject(dc, old_brush);
    SelectObject(dc, old_pen);
    DeleteObject(border_pen);

    dripwave_draw_signal_slashes(dc, rc, dripwave_lerp_color(accent, RGB(255, 244, 214), 0.35));
    dripwave_draw_frame_corners(dc, rc, dripwave_lerp_color(border, RGB(255, 244, 214), 0.25));
}

static void dripwave_draw_chip(HDC dc, RECT rc, COLORREF fill, COLORREF border, COLORREF text_color, const wchar_t *text) {
    HBRUSH fill_brush = CreateSolidBrush(fill);
    HPEN border_pen = CreatePen(PS_SOLID, 1, border);
    HBRUSH old_brush = SelectObject(dc, fill_brush);
    HPEN old_pen = SelectObject(dc, border_pen);
    HFONT old_font = SelectObject(dc, g_app.small_font ? g_app.small_font : GetStockObject(DEFAULT_GUI_FONT));

    RoundRect(dc, rc.left, rc.top, rc.right, rc.bottom, 14, 14);
    SetTextColor(dc, text_color);
    SetBkMode(dc, TRANSPARENT);
    DrawTextW(dc, text, -1, &rc, DT_CENTER | DT_VCENTER | DT_SINGLELINE);

    SelectObject(dc, old_font);
    SelectObject(dc, old_pen);
    SelectObject(dc, old_brush);
    DeleteObject(border_pen);
    DeleteObject(fill_brush);
}

static void dripwave_draw_meter(HDC dc, const RECT *rc, const wchar_t *label, double value, COLORREF fill, COLORREF border) {
    RECT outer = *rc;
    RECT inner = *rc;
    RECT fill_rc;
    wchar_t value_text[32];
    HFONT old_font;
    HBRUSH bg_brush = CreateSolidBrush(RGB(18, 20, 24));
    HBRUSH fill_brush;
    HPEN border_pen = CreatePen(PS_SOLID, 1, border);
    HBRUSH old_brush = SelectObject(dc, bg_brush);
    HPEN old_pen = SelectObject(dc, border_pen);

    value = value < 0.0 ? 0.0 : (value > 1.0 ? 1.0 : value);
    RoundRect(dc, outer.left, outer.top, outer.right, outer.bottom, 12, 12);
    SelectObject(dc, old_pen);
    SelectObject(dc, old_brush);
    DeleteObject(border_pen);
    DeleteObject(bg_brush);

    inner.left += 6;
    inner.right -= 6;
    inner.top += 22;
    inner.bottom -= 6;
    fill_rc = inner;
    fill_rc.right = inner.left + (int)((inner.right - inner.left) * value);
    if (fill_rc.right < fill_rc.left + 2) {
        fill_rc.right = min(inner.left + 2, inner.right);
    }
    fill_brush = CreateSolidBrush(fill);
    FillRect(dc, &fill_rc, fill_brush);
    DeleteObject(fill_brush);

    old_font = SelectObject(dc, g_app.small_font ? g_app.small_font : GetStockObject(DEFAULT_GUI_FONT));
    SetBkMode(dc, TRANSPARENT);
    SetTextColor(dc, RGB(250, 236, 218));
    DrawTextW(dc, label, -1, &(RECT){ outer.left + 8, outer.top + 4, outer.right - 42, outer.top + 20 }, DT_LEFT | DT_VCENTER | DT_SINGLELINE);
    _snwprintf(value_text, (sizeof(value_text) / sizeof(value_text[0])) - 1, L"%d%%", (int)(value * 100.0 + 0.5));
    value_text[(sizeof(value_text) / sizeof(value_text[0])) - 1] = L'\0';
    DrawTextW(dc, value_text, -1, &(RECT){ outer.right - 40, outer.top + 4, outer.right - 8, outer.top + 20 }, DT_RIGHT | DT_VCENTER | DT_SINGLELINE);
    SelectObject(dc, old_font);
}

static void dripwave_draw_button_shell(HDC dc, const RECT *rc, COLORREF top_fill, COLORREF bottom_fill, COLORREF border, COLORREF accent, bool pressed, bool focused) {
    RECT shell = *rc;
    COLORREF pressed_top = pressed ? dripwave_lerp_color(top_fill, RGB(0, 0, 0), 0.25) : top_fill;
    COLORREF pressed_bottom = pressed ? dripwave_lerp_color(bottom_fill, RGB(0, 0, 0), 0.25) : bottom_fill;
    dripwave_fill_gradient_bands(dc, &shell, pressed_top, pressed_bottom, 8);
    dripwave_draw_panel(dc, &shell, pressed_top, pressed_bottom, border, accent);
    if (focused) {
        HPEN focus_pen = CreatePen(PS_DOT, 1, RGB(255, 244, 214));
        HPEN old_pen = SelectObject(dc, focus_pen);
        HBRUSH old_brush = SelectObject(dc, GetStockObject(NULL_BRUSH));
        Rectangle(dc, rc->left + 4, rc->top + 4, rc->right - 4, rc->bottom - 4);
        SelectObject(dc, old_brush);
        SelectObject(dc, old_pen);
        DeleteObject(focus_pen);
    }
}

static void dripwave_draw_owner_button(const DRAWITEMSTRUCT *draw) {
    wchar_t text[128];
    RECT text_rc = draw->rcItem;
    COLORREF top_fill = RGB(52, 28, 22);
    COLORREF bottom_fill = RGB(22, 18, 22);
    COLORREF border = RGB(255, 176, 84);
    COLORREF accent = RGB(255, 120, 48);
    COLORREF text_color = RGB(253, 241, 227);
    bool pressed = (draw->itemState & ODS_SELECTED) != 0;
    bool focused = (draw->itemState & ODS_FOCUS) != 0;
    HFONT old_font;

    switch (draw->CtlID) {
        case IDC_RUN_BACKEND:
            top_fill = RGB(98, 36, 20);
            bottom_fill = RGB(42, 18, 14);
            border = RGB(255, 206, 98);
            accent = RGB(255, 138, 44);
            break;
        case IDC_AUTHORING:
            top_fill = RGB(20, 52, 54);
            bottom_fill = RGB(12, 24, 28);
            border = RGB(88, 228, 216);
            accent = RGB(66, 188, 180);
            break;
        case IDC_CLOSE_TAB:
        case IDC_DEAD_STOP:
            top_fill = RGB(92, 24, 20);
            bottom_fill = RGB(34, 10, 14);
            border = RGB(255, 124, 96);
            accent = RGB(255, 88, 62);
            break;
        case IDC_SKIP_START:
        case IDC_FRAME_BACK:
        case IDC_FRAME_FWD:
        case IDC_SKIP_END:
            top_fill = RGB(22, 44, 58);
            bottom_fill = RGB(10, 18, 28);
            border = RGB(96, 210, 255);
            accent = RGB(255, 154, 72);
            break;
        default:
            break;
    }

    dripwave_draw_button_shell(draw->hDC, &draw->rcItem, top_fill, bottom_fill, border, accent, pressed, focused);
    GetWindowTextW(draw->hwndItem, text, (int)(sizeof(text) / sizeof(text[0])));
    if (pressed) {
        OffsetRect(&text_rc, 0, 1);
    }
    old_font = SelectObject(draw->hDC, g_app.small_font ? g_app.small_font : GetStockObject(DEFAULT_GUI_FONT));
    SetBkMode(draw->hDC, TRANSPARENT);
    SetTextColor(draw->hDC, text_color);
    DrawTextW(draw->hDC, text, -1, &text_rc, DT_CENTER | DT_VCENTER | DT_SINGLELINE);
    SelectObject(draw->hDC, old_font);
}

static void dripwave_draw_play_button(const DRAWITEMSTRUCT *draw) {
    DripwaveSession *session = dripwave_active_session();
    bool playing = session && session->playing;
    RECT rc = draw->rcItem;
    RECT disc_rc = { rc.left + 10, rc.top + 7, rc.right - 10, rc.bottom - 7 };
    HBRUSH disc_brush = CreateSolidBrush(RGB(14, 14, 18));
    HPEN disc_pen = CreatePen(PS_SOLID, 2, RGB(255, 237, 210));
    HBRUSH old_brush;
    HPEN old_pen;
    bool pressed = (draw->itemState & ODS_SELECTED) != 0;
    bool focused = (draw->itemState & ODS_FOCUS) != 0;

    dripwave_draw_button_shell(
        draw->hDC,
        &rc,
        playing ? RGB(110, 38, 22) : RGB(28, 54, 72),
        playing ? RGB(46, 14, 14) : RGB(10, 18, 30),
        playing ? RGB(255, 180, 92) : RGB(110, 218, 255),
        playing ? RGB(255, 110, 58) : RGB(88, 210, 255),
        pressed,
        focused);

    SetBkMode(draw->hDC, TRANSPARENT);
    old_brush = SelectObject(draw->hDC, disc_brush);
    old_pen = SelectObject(draw->hDC, disc_pen);
    Ellipse(draw->hDC, disc_rc.left, disc_rc.top, disc_rc.right, disc_rc.bottom);
    if (playing) {
        RECT left_bar = { rc.left + 25, rc.top + 14, rc.left + 31, rc.bottom - 14 };
        RECT right_bar = { rc.right - 31, rc.top + 14, rc.right - 25, rc.bottom - 14 };
        FillRect(draw->hDC, &left_bar, (HBRUSH)GetStockObject(WHITE_BRUSH));
        FillRect(draw->hDC, &right_bar, (HBRUSH)GetStockObject(WHITE_BRUSH));
    } else {
        POINT triangle[3] = {
            { rc.left + 25, rc.top + 14 },
            { rc.left + 25, rc.bottom - 14 },
            { rc.right - 20, (rc.top + rc.bottom) / 2 },
        };
        HBRUSH white = (HBRUSH)GetStockObject(WHITE_BRUSH);
        HBRUSH old_fill = SelectObject(draw->hDC, white);
        Polygon(draw->hDC, triangle, 3);
        SelectObject(draw->hDC, old_fill);
    }
    SelectObject(draw->hDC, old_pen);
    SelectObject(draw->hDC, old_brush);
    DeleteObject(disc_pen);
    DeleteObject(disc_brush);
}

static LRESULT CALLBACK dripwave_canvas_proc(HWND hwnd, UINT msg, WPARAM wparam, LPARAM lparam) {
    switch (msg) {
        case WM_PAINT: {
            PAINTSTRUCT ps;
            RECT rc;
            DripwaveSession *session = dripwave_active_session();
            HFONT old_font;
            HDC dc = BeginPaint(hwnd, &ps);
            GetClientRect(hwnd, &rc);
            dripwave_fill_gradient_bands(dc, &rc, RGB(52, 18, 10), RGB(8, 18, 28), 26);
            SetBkMode(dc, TRANSPARENT);
            old_font = SelectObject(dc, g_app.body_font ? g_app.body_font : GetStockObject(DEFAULT_GUI_FONT));
            if (!session || !session->loaded) {
                RECT hero_rc = { rc.left + 32, rc.top + 28, rc.right - 32, rc.bottom - 28 };
                RECT title_rc;
                RECT copy_rc;
                wchar_t summary[1024];
                dripwave_draw_panel(dc, &hero_rc, RGB(70, 26, 16), RGB(10, 20, 30), RGB(255, 184, 90), RGB(74, 220, 255));
                title_rc = (RECT){ hero_rc.left + 24, hero_rc.top + 22, hero_rc.right - 24, hero_rc.top + 64 };
                copy_rc = (RECT){ hero_rc.left + 24, hero_rc.top + 104, hero_rc.right - 24, hero_rc.bottom - 26 };
                SelectObject(dc, g_app.headline_font ? g_app.headline_font : old_font);
                SetTextColor(dc, RGB(255, 242, 220));
                DrawTextW(dc, L"DRIPWAVE PLAYBACK DECK", -1, &title_rc, DT_LEFT | DT_VCENTER | DT_SINGLELINE);
                dripwave_draw_chip(dc, (RECT){ hero_rc.left + 24, hero_rc.top + 68, hero_rc.left + 146, hero_rc.top + 94 }, RGB(22, 24, 30), RGB(255, 176, 84), RGB(255, 236, 214), L"SWF + FARIM");
                dripwave_draw_chip(dc, (RECT){ hero_rc.left + 154, hero_rc.top + 68, hero_rc.left + 318, hero_rc.top + 94 }, RGB(16, 40, 44), RGB(88, 224, 214), RGB(224, 255, 248), L"RUNTIME ROUTING");
                dripwave_draw_chip(dc, (RECT){ hero_rc.left + 326, hero_rc.top + 68, hero_rc.left + 458, hero_rc.top + 94 }, RGB(34, 20, 24), RGB(255, 124, 96), RGB(255, 232, 222), L"SAVE SLOTS");
                SelectObject(dc, g_app.body_font ? g_app.body_font : old_font);
                SetTextColor(dc, RGB(248, 232, 216));
                if (g_app.recent_count > 0) {
                    _snwprintf(summary, (sizeof(summary) / sizeof(summary[0])) - 1,
                        L"Open a .swf or .farim file to inspect the stage, classify runtime needs, and throw the session into a hotter control deck. Recent reloads: %ls, %ls, %ls. The shell keeps save slots, fit modes, and runtime routing on hand while the authoring shell stays one click away.",
                        g_app.recent_entries[0].display_name,
                        g_app.recent_count > 1 ? g_app.recent_entries[1].display_name : L"-",
                        g_app.recent_count > 2 ? g_app.recent_entries[2].display_name : L"-");
                } else {
                    _snwprintf(summary, (sizeof(summary) / sizeof(summary[0])) - 1,
                        L"Open a .swf or .farim file to inspect the stage, classify runtime needs, and route the session into a hotter playback deck. Dripwave keeps tabs, save slots, fit modes, and runtime routing sharp without pretending to be a full Flash runtime." );
                }
                summary[(sizeof(summary) / sizeof(summary[0])) - 1] = L'\0';
                DrawTextW(dc, summary, -1, &copy_rc, DT_LEFT | DT_TOP | DT_WORDBREAK);
            } else {
                RECT stage_rc = rc;
                RECT deck_rc = { rc.left + 16, rc.top + 16, rc.right - 16, rc.bottom - 16 };
                RECT info_rc;
                RECT meter_rc;
                RECT footer_rc;
                wchar_t summary[1024];
                wchar_t chip_text[160];
                double progress_value = (double)(session->current_frame + 1) / max(session->swf.frame_count, 1);
                double runtime_value = !dripwave_swf_needs_projector(&session->swf) ? 1.0 : (g_app.backend_available ? 0.84 : 0.22);
                double tag_value = min((double)session->swf.tag_count / 80.0, 1.0);
                double volume_value = session->volume / 100.0;
                int pad = 34;
                int stage_w = max(session->swf.width_px, 1);
                int stage_h = max(session->swf.height_px, 1);
                dripwave_draw_panel(dc, &deck_rc, RGB(72, 24, 14), RGB(8, 20, 32), RGB(255, 184, 92), RGB(88, 220, 255));
                InflateRect(&stage_rc, -pad, -pad);
                if (g_app.fit_mode == DRIPWAVE_FIT_CONTAIN) {
                    double scale_x = (double)(stage_rc.right - stage_rc.left) / stage_w;
                    double scale_y = (double)(stage_rc.bottom - stage_rc.top) / stage_h;
                    double scale = scale_x < scale_y ? scale_x : scale_y;
                    int draw_w = (int)(stage_w * scale);
                    int draw_h = (int)(stage_h * scale);
                    stage_rc.left += ((stage_rc.right - stage_rc.left) - draw_w) / 2;
                    stage_rc.top += ((stage_rc.bottom - stage_rc.top) - draw_h) / 2;
                    stage_rc.right = stage_rc.left + draw_w;
                    stage_rc.bottom = stage_rc.top + draw_h;
                } else if (g_app.fit_mode == DRIPWAVE_FIT_NATIVE) {
                    stage_rc.right = stage_rc.left + stage_w;
                    stage_rc.bottom = stage_rc.top + stage_h;
                }
                dripwave_draw_panel(dc, &stage_rc, RGB(12, 10, 18), RGB(30, 16, 10), RGB(96, 212, 255), RGB(255, 144, 54));
                dripwave_fill_gradient_bands(dc, &(RECT){ stage_rc.left + 10, stage_rc.top + 10, stage_rc.right - 10, stage_rc.bottom - 10 }, RGB(14, 8, 18), RGB(38, 18, 10), 18);
                for (int scan_y = stage_rc.top + 20; scan_y < stage_rc.bottom - 20; scan_y += 18) {
                    RECT scanline = { stage_rc.left + 12, scan_y, stage_rc.right - 12, min(scan_y + 2, stage_rc.bottom - 12) };
                    HBRUSH scan_brush = CreateSolidBrush((scan_y / 18) % 2 == 0 ? RGB(34, 18, 16) : RGB(14, 24, 28));
                    FillRect(dc, &scanline, scan_brush);
                    DeleteObject(scan_brush);
                }

                SetTextColor(dc, RGB(255, 243, 220));
                SelectObject(dc, g_app.headline_font ? g_app.headline_font : old_font);
                DrawTextW(dc, session->display_name, -1, &(RECT){ stage_rc.left + 20, stage_rc.top + 18, stage_rc.right - 20, stage_rc.top + 54 }, DT_LEFT | DT_VCENTER | DT_SINGLELINE);

                _snwprintf(chip_text, (sizeof(chip_text) / sizeof(chip_text[0])) - 1, L"PROFILE %ls", dripwave_swf_runtime_profile(&session->swf));
                chip_text[(sizeof(chip_text) / sizeof(chip_text[0])) - 1] = L'\0';
                dripwave_draw_chip(dc, (RECT){ stage_rc.left + 20, stage_rc.top + 58, stage_rc.left + 192, stage_rc.top + 84 }, RGB(20, 22, 28), RGB(255, 184, 92), RGB(255, 238, 214), chip_text);
                _snwprintf(chip_text, (sizeof(chip_text) / sizeof(chip_text[0])) - 1, L"REQUIRES %ls", dripwave_swf_backend_requirement(&session->swf));
                chip_text[(sizeof(chip_text) / sizeof(chip_text[0])) - 1] = L'\0';
                dripwave_draw_chip(dc, (RECT){ stage_rc.left + 202, stage_rc.top + 58, stage_rc.left + 392, stage_rc.top + 84 }, RGB(16, 40, 42), RGB(88, 224, 214), RGB(224, 255, 248), chip_text);
                _snwprintf(chip_text, (sizeof(chip_text) / sizeof(chip_text[0])) - 1, L"FIT %ls | SLOT %ls", dripwave_fit_mode_label(g_app.fit_mode), dripwave_state_slot_label(session->last_state_slot));
                chip_text[(sizeof(chip_text) / sizeof(chip_text[0])) - 1] = L'\0';
                dripwave_draw_chip(dc, (RECT){ stage_rc.left + 402, stage_rc.top + 58, stage_rc.left + 620, stage_rc.top + 84 }, RGB(32, 18, 24), RGB(255, 124, 96), RGB(255, 236, 224), chip_text);

                meter_rc = (RECT){ stage_rc.right - max((stage_rc.right - stage_rc.left) / 4, 196), stage_rc.top + 98, stage_rc.right - 20, stage_rc.bottom - 78 };
                info_rc = (RECT){ stage_rc.left + 20, stage_rc.top + 98, meter_rc.left - 18, stage_rc.bottom - 78 };
                footer_rc = (RECT){ stage_rc.left + 20, stage_rc.bottom - 64, stage_rc.right - 20, stage_rc.bottom - 18 };

                dripwave_draw_panel(dc, &info_rc, RGB(28, 14, 18), RGB(10, 20, 30), RGB(255, 176, 84), RGB(255, 116, 52));
                dripwave_draw_panel(dc, &meter_rc, RGB(14, 28, 34), RGB(12, 14, 20), RGB(88, 224, 214), RGB(255, 176, 84));
                dripwave_draw_panel(dc, &footer_rc, RGB(44, 18, 14), RGB(12, 18, 26), RGB(255, 184, 92), RGB(88, 224, 214));

                _snwprintf(summary, (sizeof(summary) / sizeof(summary[0])) - 1,
                    L"Stage %dx%d | SWF v%d | %ls | %.2f fps\n\nSource lane: %ls\nCompression path: %ls\nRuntime route: %ls (%ls)\nTag scan: %ls | Tags: %d | Labels: %d\nNetwork: %ls | AVM1: %ls | AVM2: %ls\n\nDripwave keeps this file in a spicy inspection deck: loud borders, save-slot recall, runtime routing, and transport state without pretending the shell itself is the whole projector.",
                    session->swf.width_px,
                    session->swf.height_px,
                    session->swf.version,
                    session->swf.compression,
                    session->swf.frame_rate,
                    session->is_farim ? L"FARIM package" : L"direct SWF",
                    session->swf.compression,
                    g_app.backend_available ? dripwave_file_name(g_app.backend_path) : L"not configured",
                    g_app.backend_available ? dripwave_backend_source_label(g_app.backend_source) : dripwave_backend_source_label(DRIPWAVE_BACKEND_NONE),
                    session->swf.tag_scan_complete ? L"complete" : L"partial",
                    session->swf.tag_count,
                    session->swf.frame_label_count,
                    session->swf.uses_network ? L"on" : L"off",
                    session->swf.uses_avm1 ? L"yes" : L"no",
                    session->swf.uses_avm2 ? L"yes" : L"no");
                summary[(sizeof(summary) / sizeof(summary[0])) - 1] = L'\0';
                SelectObject(dc, g_app.body_font ? g_app.body_font : old_font);
                SetTextColor(dc, RGB(247, 232, 216));
                DrawTextW(dc, summary, -1, &(RECT){ info_rc.left + 18, info_rc.top + 16, info_rc.right - 18, info_rc.bottom - 16 }, DT_LEFT | DT_TOP | DT_WORDBREAK);

                dripwave_draw_meter(dc, &(RECT){ meter_rc.left + 14, meter_rc.top + 16, meter_rc.right - 14, meter_rc.top + 48 }, L"FRAME HEAT", progress_value, RGB(255, 138, 48), RGB(255, 196, 92));
                dripwave_draw_meter(dc, &(RECT){ meter_rc.left + 14, meter_rc.top + 58, meter_rc.right - 14, meter_rc.top + 90 }, L"RUNTIME READY", runtime_value, RGB(88, 224, 214), RGB(120, 232, 224));
                dripwave_draw_meter(dc, &(RECT){ meter_rc.left + 14, meter_rc.top + 100, meter_rc.right - 14, meter_rc.top + 132 }, L"TAG DENSITY", tag_value, RGB(255, 110, 78), RGB(255, 156, 118));
                dripwave_draw_meter(dc, &(RECT){ meter_rc.left + 14, meter_rc.top + 142, meter_rc.right - 14, meter_rc.top + 174 }, L"VOLUME", volume_value, RGB(255, 188, 88), RGB(255, 214, 126));

                _snwprintf(summary, (sizeof(summary) / sizeof(summary[0])) - 1,
                    L"FRAME %d / %d  |  SLOT %ls  |  %ls",
                    session->current_frame + 1,
                    session->swf.frame_count,
                    dripwave_state_slot_label(session->last_state_slot),
                    session->status);
                summary[(sizeof(summary) / sizeof(summary[0])) - 1] = L'\0';
                SelectObject(dc, g_app.small_font ? g_app.small_font : old_font);
                DrawTextW(dc, summary, -1, &(RECT){ footer_rc.left + 16, footer_rc.top + 10, footer_rc.right - 16, footer_rc.bottom - 10 }, DT_LEFT | DT_VCENTER | DT_SINGLELINE | DT_END_ELLIPSIS);
            }
            SelectObject(dc, old_font);
            EndPaint(hwnd, &ps);
            return 0;
        }
    }
    return DefWindowProcW(hwnd, msg, wparam, lparam);
}

static LRESULT CALLBACK dripwave_window_proc(HWND hwnd, UINT msg, WPARAM wparam, LPARAM lparam) {
    switch (msg) {
        case WM_CREATE: {
            INITCOMMONCONTROLSEX icc = { sizeof(icc), ICC_STANDARD_CLASSES | ICC_TAB_CLASSES | ICC_BAR_CLASSES };
            InitCommonControlsEx(&icc);

            g_app.controls_visible = true;
            g_app.fit_mode = DRIPWAVE_FIT_CONTAIN;
            g_app.active_index = -1;
            dripwave_detect_backend();

            g_app.headline_font = CreateFontW(-24, 0, 0, 0, FW_HEAVY, FALSE, FALSE, FALSE, DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY, VARIABLE_PITCH, L"Bahnschrift SemiCondensed");
            g_app.body_font = CreateFontW(-16, 0, 0, 0, FW_SEMIBOLD, FALSE, FALSE, FALSE, DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY, VARIABLE_PITCH, L"Segoe UI Semibold");
            g_app.small_font = CreateFontW(-14, 0, 0, 0, FW_MEDIUM, FALSE, FALSE, FALSE, DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY, VARIABLE_PITCH, L"Segoe UI Semibold");

            g_app.open_button = CreateWindowW(L"BUTTON", L"Open", WS_CHILD | WS_VISIBLE | BS_OWNERDRAW, 0, 0, 0, 0, hwnd, (HMENU)IDC_OPEN_BUTTON, g_app.instance, NULL);
            g_app.run_button = CreateWindowW(L"BUTTON", L"Runtime...", WS_CHILD | WS_VISIBLE | BS_OWNERDRAW, 0, 0, 0, 0, hwnd, (HMENU)IDC_RUN_BACKEND, g_app.instance, NULL);
            g_app.save_button = CreateWindowW(L"BUTTON", L"Save State", WS_CHILD | WS_VISIBLE | BS_OWNERDRAW, 0, 0, 0, 0, hwnd, (HMENU)IDC_SAVE_STATE, g_app.instance, NULL);
            g_app.load_button = CreateWindowW(L"BUTTON", L"Load State", WS_CHILD | WS_VISIBLE | BS_OWNERDRAW, 0, 0, 0, 0, hwnd, (HMENU)IDC_LOAD_STATE, g_app.instance, NULL);
            g_app.slot_combo = CreateWindowW(WC_COMBOBOXW, L"", WS_CHILD | WS_VISIBLE | CBS_DROPDOWNLIST, 0, 0, 0, 0, hwnd, (HMENU)IDC_STATE_SLOT, g_app.instance, NULL);
            SendMessageW(g_app.slot_combo, CB_ADDSTRING, 0, (LPARAM)L"Slot: Resume");
            SendMessageW(g_app.slot_combo, CB_ADDSTRING, 0, (LPARAM)L"Slot: Checkpoint");
            SendMessageW(g_app.slot_combo, CB_ADDSTRING, 0, (LPARAM)L"Slot: Branch A");
            SendMessageW(g_app.slot_combo, CB_ADDSTRING, 0, (LPARAM)L"Slot: Sandbox");
            SendMessageW(g_app.slot_combo, CB_SETCURSEL, 0, 0);
            g_app.recent_combo = CreateWindowW(WC_COMBOBOXW, L"", WS_CHILD | WS_VISIBLE | CBS_DROPDOWNLIST, 0, 0, 0, 0, hwnd, (HMENU)IDC_RECENT_COMBO, g_app.instance, NULL);
            g_app.recent_button = CreateWindowW(L"BUTTON", L"Open Recent", WS_CHILD | WS_VISIBLE | BS_OWNERDRAW, 0, 0, 0, 0, hwnd, (HMENU)IDC_OPEN_RECENT, g_app.instance, NULL);
            g_app.author_button = CreateWindowW(L"BUTTON", L"Authoring...", WS_CHILD | WS_VISIBLE | BS_OWNERDRAW, 0, 0, 0, 0, hwnd, (HMENU)IDC_AUTHORING, g_app.instance, NULL);
            g_app.close_button = CreateWindowW(L"BUTTON", L"Close Tab", WS_CHILD | WS_VISIBLE | BS_OWNERDRAW, 0, 0, 0, 0, hwnd, (HMENU)IDC_CLOSE_TAB, g_app.instance, NULL);
            g_app.toggle_button = CreateWindowW(L"BUTTON", L"Controls", WS_CHILD | WS_VISIBLE | BS_OWNERDRAW, 0, 0, 0, 0, hwnd, (HMENU)IDC_TOGGLE_CONTROLS, g_app.instance, NULL);
            g_app.fit_combo = CreateWindowW(WC_COMBOBOXW, L"", WS_CHILD | WS_VISIBLE | CBS_DROPDOWNLIST, 0, 0, 0, 0, hwnd, (HMENU)IDC_FIT_MODE, g_app.instance, NULL);
            SendMessageW(g_app.fit_combo, CB_ADDSTRING, 0, (LPARAM)L"Fit: Contain");
            SendMessageW(g_app.fit_combo, CB_ADDSTRING, 0, (LPARAM)L"Fit: 1:1");
            SendMessageW(g_app.fit_combo, CB_ADDSTRING, 0, (LPARAM)L"Fit: Stretch");
            SendMessageW(g_app.fit_combo, CB_SETCURSEL, DRIPWAVE_FIT_CONTAIN, 0);

            g_app.tab_control = CreateWindowW(WC_TABCONTROLW, L"", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS, 0, 0, 0, 0, hwnd, (HMENU)IDC_TAB_CONTROL, g_app.instance, NULL);
            g_app.canvas = CreateWindowW(L"DripwaveCanvas", L"", WS_CHILD | WS_VISIBLE, 0, 0, 0, 0, hwnd, (HMENU)IDC_CANVAS, g_app.instance, NULL);
            g_app.status_label = CreateWindowW(L"STATIC", L"Open a .swf or .farim package.", WS_CHILD | WS_VISIBLE, 0, 0, 0, 0, hwnd, (HMENU)IDC_STATUS, g_app.instance, NULL);

            g_app.skip_start = CreateWindowW(L"BUTTON", L"|<<", WS_CHILD | WS_VISIBLE | BS_OWNERDRAW, 0, 0, 0, 0, hwnd, (HMENU)IDC_SKIP_START, g_app.instance, NULL);
            g_app.frame_back = CreateWindowW(L"BUTTON", L"<<", WS_CHILD | WS_VISIBLE | BS_OWNERDRAW, 0, 0, 0, 0, hwnd, (HMENU)IDC_FRAME_BACK, g_app.instance, NULL);
            g_app.play_pause = CreateWindowW(L"BUTTON", L"", WS_CHILD | WS_VISIBLE | BS_OWNERDRAW, 0, 0, 0, 0, hwnd, (HMENU)IDC_PLAY_PAUSE, g_app.instance, NULL);
            g_app.frame_fwd = CreateWindowW(L"BUTTON", L">>", WS_CHILD | WS_VISIBLE | BS_OWNERDRAW, 0, 0, 0, 0, hwnd, (HMENU)IDC_FRAME_FWD, g_app.instance, NULL);
            g_app.skip_end = CreateWindowW(L"BUTTON", L">>|", WS_CHILD | WS_VISIBLE | BS_OWNERDRAW, 0, 0, 0, 0, hwnd, (HMENU)IDC_SKIP_END, g_app.instance, NULL);
            g_app.dead_stop = CreateWindowW(L"BUTTON", L"STOP", WS_CHILD | WS_VISIBLE | BS_OWNERDRAW, 0, 0, 0, 0, hwnd, (HMENU)IDC_DEAD_STOP, g_app.instance, NULL);
            g_app.volume_slider = CreateWindowW(TRACKBAR_CLASSW, L"", WS_CHILD | WS_VISIBLE | TBS_AUTOTICKS, 0, 0, 0, 0, hwnd, (HMENU)IDC_VOLUME, g_app.instance, NULL);
            SendMessageW(g_app.volume_slider, TBM_SETRANGE, TRUE, MAKELPARAM(0, 100));
            SendMessageW(g_app.volume_slider, TBM_SETPOS, TRUE, 75);

            {
                HWND controls[] = {
                    g_app.open_button,
                    g_app.run_button,
                    g_app.save_button,
                    g_app.load_button,
                    g_app.slot_combo,
                    g_app.recent_combo,
                    g_app.recent_button,
                    g_app.author_button,
                    g_app.close_button,
                    g_app.toggle_button,
                    g_app.fit_combo,
                    g_app.tab_control,
                    g_app.status_label,
                    g_app.skip_start,
                    g_app.frame_back,
                    g_app.play_pause,
                    g_app.frame_fwd,
                    g_app.skip_end,
                    g_app.dead_stop,
                };
                for (int index = 0; index < (int)(sizeof(controls) / sizeof(controls[0])); ++index) {
                    if (controls[index]) {
                        SendMessageW(controls[index], WM_SETFONT, (WPARAM)(g_app.body_font ? g_app.body_font : GetStockObject(DEFAULT_GUI_FONT)), TRUE);
                    }
                }
            }

            g_app.selected_state_slot = 0;
            dripwave_load_recent_entries();
            DragAcceptFiles(hwnd, TRUE);
            SetTimer(hwnd, IDT_PLAYBACK, 30, NULL);
            dripwave_update_runtime_button();
            return 0;
        }
        case WM_ERASEBKGND: {
            RECT rc;
            RECT header_rc;
            RECT footer_rc;
            HDC dc = (HDC)wparam;
            GetClientRect(hwnd, &rc);
            dripwave_fill_gradient_bands(dc, &rc, RGB(32, 14, 10), RGB(10, 18, 28), 24);
            header_rc = (RECT){ rc.left, rc.top, rc.right, min(rc.top + 74, rc.bottom) };
            footer_rc = (RECT){ rc.left, max(rc.bottom - (g_app.controls_visible ? 80 : 34), rc.top), rc.right, rc.bottom };
            dripwave_fill_gradient_bands(dc, &header_rc, RGB(82, 30, 18), RGB(22, 16, 22), 10);
            dripwave_fill_gradient_bands(dc, &footer_rc, RGB(18, 24, 30), RGB(46, 18, 14), 8);
            dripwave_draw_frame_corners(dc, &rc, RGB(255, 176, 84));
            return 1;
        }
        case WM_SIZE:
            dripwave_layout(hwnd);
            return 0;
        case WM_COMMAND:
            dripwave_handle_command(hwnd, LOWORD(wparam), HIWORD(wparam));
            return 0;
        case WM_CTLCOLORSTATIC:
            if ((HWND)lparam == g_app.status_label) {
                SetTextColor((HDC)wparam, RGB(255, 236, 214));
                SetBkMode((HDC)wparam, TRANSPARENT);
                return (INT_PTR)GetStockObject(NULL_BRUSH);
            }
            break;
        case WM_NOTIFY:
            if (((LPNMHDR)lparam)->idFrom == IDC_TAB_CONTROL) {
                if (((LPNMHDR)lparam)->code == TCN_SELCHANGE) {
                    dripwave_select_session(TabCtrl_GetCurSel(g_app.tab_control));
                } else if (((LPNMHDR)lparam)->code == NM_CLICK) {
                    DWORD position = GetMessagePos();
                    POINT screen_point = { GET_X_LPARAM(position), GET_Y_LPARAM(position) };
                    POINT client_point = screen_point;
                    ScreenToClient(g_app.tab_control, &client_point);
                    {
                        int close_index = dripwave_tab_close_hit_test(client_point);
                        if (close_index >= 0) {
                            dripwave_remove_session(close_index);
                        }
                    }
                }
            }
            return 0;
        case WM_DROPFILES: {
            HDROP drop = (HDROP)wparam;
            UINT count = DragQueryFileW(drop, 0xFFFFFFFFu, NULL, 0);
            for (UINT i = 0; i < count; ++i) {
                wchar_t path[MAX_PATH];
                if (DragQueryFileW(drop, i, path, MAX_PATH)) {
                    dripwave_add_session_from_path(hwnd, path);
                }
            }
            DragFinish(drop);
            return 0;
        }
        case WM_KEYDOWN:
            if ((GetKeyState(VK_CONTROL) & 0x8000) && wparam == 'W' && g_app.active_index >= 0) {
                dripwave_remove_session(g_app.active_index);
                return 0;
            }
            return 0;
        case WM_HSCROLL: {
            HWND source = (HWND)lparam;
            DripwaveSession *session = dripwave_active_session();
            if (source == g_app.volume_slider && session) {
                session->volume = (int)SendMessageW(g_app.volume_slider, TBM_GETPOS, 0, 0);
                dripwave_set_status(session, L"%ls | volume %d%%", session->display_name, session->volume);
                dripwave_update_status_label();
            }
            return 0;
        }
        case WM_TIMER: {
            DripwaveSession *session = dripwave_active_session();
            if (wparam == IDT_PLAYBACK && session && session->loaded && session->playing && session->swf.frame_count > 0) {
                session->frame_accumulator += session->swf.frame_rate * 0.03;
                while (session->frame_accumulator >= 1.0) {
                    session->frame_accumulator -= 1.0;
                    session->current_frame++;
                    if (session->current_frame >= session->swf.frame_count) {
                        session->current_frame = session->swf.frame_count - 1;
                        session->playing = false;
                        break;
                    }
                }
                dripwave_set_status(session, L"%ls | playing frame %d / %d", session->display_name, session->current_frame + 1, session->swf.frame_count);
                dripwave_update_status_label();
                dripwave_update_play_button();
                InvalidateRect(g_app.canvas, NULL, TRUE);
            }
            return 0;
        }
        case WM_DRAWITEM:
            switch ((int)wparam) {
                case IDC_OPEN_BUTTON:
                case IDC_RUN_BACKEND:
                case IDC_SAVE_STATE:
                case IDC_LOAD_STATE:
                case IDC_OPEN_RECENT:
                case IDC_AUTHORING:
                case IDC_CLOSE_TAB:
                case IDC_TOGGLE_CONTROLS:
                case IDC_SKIP_START:
                case IDC_FRAME_BACK:
                case IDC_FRAME_FWD:
                case IDC_SKIP_END:
                case IDC_DEAD_STOP:
                    dripwave_draw_owner_button((const DRAWITEMSTRUCT*)lparam);
                    return TRUE;
                case IDC_PLAY_PAUSE:
                    dripwave_draw_play_button((const DRAWITEMSTRUCT*)lparam);
                    return TRUE;
            }
            return FALSE;
        case WM_DESTROY:
            {
                wchar_t ignored_status[DRIPWAVE_STATUS_CAP];
                for (int i = 0; i < g_app.session_count; ++i) {
                    if (g_app.sessions[i].loaded) {
                        dripwave_save_state_for_session(&g_app.sessions[i], g_app.sessions[i].last_state_slot, ignored_status, DRIPWAVE_STATUS_CAP);
                    }
                }
            }
            KillTimer(hwnd, IDT_PLAYBACK);
            DragAcceptFiles(hwnd, FALSE);
            for (int i = 0; i < g_app.session_count; ++i) {
                dripwave_session_reset(&g_app.sessions[i]);
            }
            if (g_app.headline_font) {
                DeleteObject(g_app.headline_font);
            }
            if (g_app.body_font) {
                DeleteObject(g_app.body_font);
            }
            if (g_app.small_font) {
                DeleteObject(g_app.small_font);
            }
            PostQuitMessage(0);
            return 0;
    }
    return DefWindowProcW(hwnd, msg, wparam, lparam);
}

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE prev_instance, PWSTR cmd_line, int show_cmd) {
    WNDCLASSW window_class;
    WNDCLASSW canvas_class;
    HWND hwnd;
    MSG msg;
    int argc = 0;
    LPWSTR *argv = CommandLineToArgvW(GetCommandLineW(), &argc);
    (void)prev_instance;
    (void)cmd_line;

    ZeroMemory(&g_app, sizeof(g_app));
    g_app.instance = instance;

    if (argv && argc > 1 && _wcsicmp(argv[1], L"--smoke") == 0) {
        int failures = 0;
        dripwave_attach_console();
        for (int i = 2; i < argc; ++i) {
            if (!dripwave_smoke_test_path(argv[i])) {
                failures++;
            }
        }
        if (argc < 3) {
            fwprintf(stderr, L"Usage: dripwave.exe --smoke <file1.swf|file1.farim> [more files...]\n");
            failures = 1;
        }
        if (argv) {
            LocalFree(argv);
        }
        return failures == 0 ? 0 : 1;
    }

    if (argv && argc > 1 && _wcsicmp(argv[1], L"--inspect") == 0) {
        int failures = 0;
        dripwave_attach_console();
        for (int i = 2; i < argc; ++i) {
            if (!dripwave_inspect_path(argv[i])) {
                failures++;
            }
        }
        if (argc < 3) {
            fwprintf(stderr, L"Usage: dripwave.exe --inspect <file1.swf|file1.farim> [more files...]\n");
            failures = 1;
        }
        if (argv) {
            LocalFree(argv);
        }
        return failures == 0 ? 0 : 1;
    }

    ZeroMemory(&window_class, sizeof(window_class));
    window_class.lpfnWndProc = dripwave_window_proc;
    window_class.hInstance = instance;
    window_class.lpszClassName = L"DripwaveWindow";
    window_class.hCursor = LoadCursorW(NULL, IDC_ARROW);
    window_class.hbrBackground = NULL;
    RegisterClassW(&window_class);

    ZeroMemory(&canvas_class, sizeof(canvas_class));
    canvas_class.lpfnWndProc = dripwave_canvas_proc;
    canvas_class.hInstance = instance;
    canvas_class.lpszClassName = L"DripwaveCanvas";
    canvas_class.hCursor = LoadCursorW(NULL, IDC_ARROW);
    canvas_class.hbrBackground = NULL;
    RegisterClassW(&canvas_class);

    hwnd = CreateWindowW(L"DripwaveWindow", L"dripwave", WS_OVERLAPPEDWINDOW | WS_VISIBLE,
        CW_USEDEFAULT, CW_USEDEFAULT, 960, 720, NULL, NULL, instance, NULL);
    if (!hwnd) {
        return 1;
    }
    g_app.window = hwnd;
    ShowWindow(hwnd, show_cmd);

    if (argv && argc > 1) {
        for (int i = 1; i < argc; ++i) {
            dripwave_add_session_from_path(hwnd, argv[i]);
        }
    }
    if (argv) {
        LocalFree(argv);
    }

    while (GetMessageW(&msg, NULL, 0, 0) > 0) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }
    return (int)msg.wParam;
}