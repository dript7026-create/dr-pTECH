#define UNICODE
#define _UNICODE

#include <windows.h>
#include <commctrl.h>
#include <commdlg.h>
#include <Richedit.h>
#include <stdbool.h>
#include <stdio.h>
#include <wchar.h>

#include "file_io.h"
#include "plugin_loader.h"

#pragma comment(lib, "Comctl32.lib")
#pragma comment(lib, "Comdlg32.lib")

#ifndef _countof
#define _countof(arr) (sizeof(arr) / sizeof((arr)[0]))
#endif

#define APP_NAME L"dotxt"
#define IDC_EDITOR 1001
#define IDC_STATUS 1002

#define IDM_FILE_NEW       1101
#define IDM_FILE_OPEN      1102
#define IDM_FILE_SAVE      1103
#define IDM_FILE_SAVEAS    1104
#define IDM_FILE_EXIT      1105

#define IDM_EDIT_UNDO      1201
#define IDM_EDIT_CUT       1202
#define IDM_EDIT_COPY      1203
#define IDM_EDIT_PASTE     1204
#define IDM_EDIT_SELECTALL 1205
#define IDM_EDIT_FIND      1206
#define IDM_EDIT_REPLACE   1207

#define IDM_RECENT_BASE    1300
#define IDM_RECENT_MAX     1307
#define MAX_RECENT_FILES   8

typedef struct AppState {
    HWND hwndMain;
    HWND hwndEditor;
    HWND hwndStatus;

    HMENU hMainMenu;
    HMENU hRecentMenu;

    wchar_t currentPath[MAX_PATH];
    bool hasPath;

    wchar_t recentFiles[MAX_RECENT_FILES][MAX_PATH];
    int recentCount;

    UINT findReplaceMsg;
    HWND hFindDlg;
    HWND hReplaceDlg;
    FINDREPLACEW fr;
    wchar_t findText[256];
    wchar_t replaceText[256];

    DotxtPluginLoadReport pluginReport;
} AppState;

static AppState g_app;

static const wchar_t* kOpenFilter =
    L"All Supported (*.txt;*.md;*.rtf;*.ini;*.cfg;*.json;*.xml;*.csv;*.c;*.h)\0"
    L"*.txt;*.md;*.rtf;*.ini;*.cfg;*.json;*.xml;*.csv;*.c;*.h\0"
    L"Rich Text Format (*.rtf)\0*.rtf\0"
    L"Text and Code Files (*.txt;*.md;*.ini;*.cfg;*.json;*.xml;*.csv;*.c;*.h)\0"
    L"*.txt;*.md;*.ini;*.cfg;*.json;*.xml;*.csv;*.c;*.h\0"
    L"All Files (*.*)\0*.*\0\0";

static const wchar_t* kSaveFilter =
    L"Text File (*.txt)\0*.txt\0"
    L"Rich Text Format (*.rtf)\0*.rtf\0"
    L"Markdown (*.md)\0*.md\0"
    L"All Files (*.*)\0*.*\0\0";

static bool editor_is_modified(void) {
    return SendMessageW(g_app.hwndEditor, EM_GETMODIFY, 0, 0) != 0;
}

static void editor_set_modified(bool modified) {
    SendMessageW(g_app.hwndEditor, EM_SETMODIFY, modified ? TRUE : FALSE, 0);
}

static const wchar_t* path_filename_or_default(void) {
    if (!g_app.hasPath) {
        return L"Untitled";
    }
    const wchar_t* slash = wcsrchr(g_app.currentPath, L'\\');
    if (!slash) {
        return g_app.currentPath;
    }
    return slash + 1;
}

static void update_status_bar(void) {
    wchar_t line[1024];
    if (g_app.hasPath) {
        _snwprintf_s(line, _countof(line), _TRUNCATE, L"%s", g_app.currentPath);
    } else {
        _snwprintf_s(line, _countof(line), _TRUNCATE, L"Unsaved document");
    }
    SendMessageW(g_app.hwndStatus, SB_SETTEXTW, 0, (LPARAM)line);
}

static void update_window_title(void) {
    wchar_t title[512];
    const wchar_t* name = path_filename_or_default();
    const wchar_t* dirty = editor_is_modified() ? L" *" : L"";
    _snwprintf_s(title, _countof(title), _TRUNCATE, L"%s - %s%s", APP_NAME, name, dirty);
    SetWindowTextW(g_app.hwndMain, title);
    update_status_bar();
}

static void refresh_recent_menu(void) {
    while (GetMenuItemCount(g_app.hRecentMenu) > 0) {
        DeleteMenu(g_app.hRecentMenu, 0, MF_BYPOSITION);
    }

    if (g_app.recentCount <= 0) {
        AppendMenuW(g_app.hRecentMenu, MF_GRAYED | MF_STRING, IDM_RECENT_BASE, L"(empty)");
        return;
    }

    for (int i = 0; i < g_app.recentCount && i < MAX_RECENT_FILES; ++i) {
        wchar_t itemText[MAX_PATH + 16];
        _snwprintf_s(itemText, _countof(itemText), _TRUNCATE, L"&%d %s", i + 1, g_app.recentFiles[i]);
        AppendMenuW(g_app.hRecentMenu, MF_STRING, IDM_RECENT_BASE + i, itemText);
    }
}

static void add_recent_file(const wchar_t* path) {
    if (!path || !path[0]) {
        return;
    }

    int existing = -1;
    for (int i = 0; i < g_app.recentCount; ++i) {
        if (_wcsicmp(g_app.recentFiles[i], path) == 0) {
            existing = i;
            break;
        }
    }

    if (existing > 0) {
        wchar_t temp[MAX_PATH];
        wcsncpy_s(temp, _countof(temp), g_app.recentFiles[existing], _TRUNCATE);
        for (int i = existing; i > 0; --i) {
            wcsncpy_s(g_app.recentFiles[i], _countof(g_app.recentFiles[i]), g_app.recentFiles[i - 1], _TRUNCATE);
        }
        wcsncpy_s(g_app.recentFiles[0], _countof(g_app.recentFiles[0]), temp, _TRUNCATE);
    } else if (existing < 0) {
        int limit = g_app.recentCount < MAX_RECENT_FILES ? g_app.recentCount : (MAX_RECENT_FILES - 1);
        for (int i = limit; i > 0; --i) {
            wcsncpy_s(g_app.recentFiles[i], _countof(g_app.recentFiles[i]), g_app.recentFiles[i - 1], _TRUNCATE);
        }
        wcsncpy_s(g_app.recentFiles[0], _countof(g_app.recentFiles[0]), path, _TRUNCATE);
        if (g_app.recentCount < MAX_RECENT_FILES) {
            g_app.recentCount += 1;
        }
    }

    refresh_recent_menu();
}

static void set_current_path(const wchar_t* pathOrNull) {
    if (!pathOrNull || !pathOrNull[0]) {
        g_app.currentPath[0] = 0;
        g_app.hasPath = false;
    } else {
        wcsncpy_s(g_app.currentPath, _countof(g_app.currentPath), pathOrNull, _TRUNCATE);
        g_app.hasPath = true;
    }
    update_window_title();
}

static bool prompt_discard_changes(void) {
    if (!editor_is_modified()) {
        return true;
    }

    int response = MessageBoxW(
        g_app.hwndMain,
        L"This document has unsaved changes. Continue and discard changes?",
        APP_NAME,
        MB_ICONWARNING | MB_YESNO | MB_DEFBUTTON2
    );

    return response == IDYES;
}

static bool load_document_path(const wchar_t* path) {
    if (!dotxt_load_into_editor(g_app.hwndEditor, path)) {
        MessageBoxW(g_app.hwndMain, L"Failed to open file.", APP_NAME, MB_ICONERROR | MB_OK);
        return false;
    }

    editor_set_modified(false);
    set_current_path(path);
    add_recent_file(path);
    update_window_title();
    return true;
}

static void do_new_document(void) {
    if (!prompt_discard_changes()) {
        return;
    }
    SetWindowTextW(g_app.hwndEditor, L"");
    editor_set_modified(false);
    set_current_path(NULL);
    update_window_title();
}

static bool get_open_path(wchar_t* outPath, size_t outCount) {
    OPENFILENAMEW ofn;
    ZeroMemory(&ofn, sizeof(ofn));
    outPath[0] = 0;

    ofn.lStructSize = sizeof(ofn);
    ofn.hwndOwner = g_app.hwndMain;
    ofn.lpstrFile = outPath;
    ofn.nMaxFile = (DWORD)outCount;
    ofn.lpstrFilter = kOpenFilter;
    ofn.nFilterIndex = 1;
    ofn.Flags = OFN_FILEMUSTEXIST | OFN_HIDEREADONLY | OFN_EXPLORER;

    return GetOpenFileNameW(&ofn) == TRUE;
}

static bool get_save_path(wchar_t* outPath, size_t outCount) {
    OPENFILENAMEW ofn;
    ZeroMemory(&ofn, sizeof(ofn));

    outPath[0] = 0;
    if (g_app.hasPath) {
        wcsncpy_s(outPath, outCount, g_app.currentPath, _TRUNCATE);
    }

    ofn.lStructSize = sizeof(ofn);
    ofn.hwndOwner = g_app.hwndMain;
    ofn.lpstrFile = outPath;
    ofn.nMaxFile = (DWORD)outCount;
    ofn.lpstrFilter = kSaveFilter;
    ofn.nFilterIndex = 1;
    ofn.lpstrDefExt = L"txt";
    ofn.Flags = OFN_OVERWRITEPROMPT | OFN_EXPLORER;

    return GetSaveFileNameW(&ofn) == TRUE;
}

static void do_open_document(void) {
    if (!prompt_discard_changes()) {
        return;
    }

    wchar_t path[MAX_PATH];
    if (!get_open_path(path, _countof(path))) {
        return;
    }

    load_document_path(path);
}

static bool save_document_to_path(const wchar_t* path) {
    if (!dotxt_save_from_editor(g_app.hwndEditor, path)) {
        MessageBoxW(g_app.hwndMain, L"Failed to save file.", APP_NAME, MB_ICONERROR | MB_OK);
        return false;
    }

    set_current_path(path);
    add_recent_file(path);
    editor_set_modified(false);
    update_window_title();
    return true;
}

static bool do_save_as(void) {
    wchar_t path[MAX_PATH];
    if (!get_save_path(path, _countof(path))) {
        return false;
    }
    return save_document_to_path(path);
}

static bool do_save(void) {
    if (!g_app.hasPath) {
        return do_save_as();
    }
    return save_document_to_path(g_app.currentPath);
}

static bool find_next(const wchar_t* needle, DWORD flags) {
    if (!needle || !needle[0]) {
        return false;
    }

    CHARRANGE sel;
    SendMessageW(g_app.hwndEditor, EM_EXGETSEL, 0, (LPARAM)&sel);

    FINDTEXTEXW ft;
    ft.chrg.cpMin = (flags & FR_DOWN) ? sel.cpMax : 0;
    ft.chrg.cpMax = -1;
    ft.lpstrText = (LPWSTR)needle;

    LRESULT found = SendMessageW(g_app.hwndEditor, EM_FINDTEXTEXW, flags, (LPARAM)&ft);
    if (found == -1) {
        MessageBoxW(g_app.hwndMain, L"No more matches.", APP_NAME, MB_OK | MB_ICONINFORMATION);
        return false;
    }

    SendMessageW(g_app.hwndEditor, EM_EXSETSEL, 0, (LPARAM)&ft.chrgText);
    SendMessageW(g_app.hwndEditor, EM_SCROLLCARET, 0, 0);
    SetFocus(g_app.hwndEditor);
    return true;
}

static void replace_current_selection(const wchar_t* replacement) {
    SendMessageW(g_app.hwndEditor, EM_REPLACESEL, TRUE, (LPARAM)replacement);
}

static void open_find_dialog(bool replace) {
    ZeroMemory(&g_app.fr, sizeof(g_app.fr));
    g_app.fr.lStructSize = sizeof(g_app.fr);
    g_app.fr.hwndOwner = g_app.hwndMain;
    g_app.fr.lpstrFindWhat = g_app.findText;
    g_app.fr.wFindWhatLen = (WORD)_countof(g_app.findText);
    g_app.fr.Flags = FR_DOWN;

    if (replace) {
        g_app.fr.lpstrReplaceWith = g_app.replaceText;
        g_app.fr.wReplaceWithLen = (WORD)_countof(g_app.replaceText);
        g_app.hReplaceDlg = ReplaceTextW(&g_app.fr);
    } else {
        g_app.hFindDlg = FindTextW(&g_app.fr);
    }
}

static HMENU build_menu(void) {
    HMENU hMain = CreateMenu();
    HMENU hFile = CreatePopupMenu();
    HMENU hEdit = CreatePopupMenu();

    AppendMenuW(hFile, MF_STRING, IDM_FILE_NEW, L"&New\tCtrl+N");
    AppendMenuW(hFile, MF_STRING, IDM_FILE_OPEN, L"&Open...\tCtrl+O");
    AppendMenuW(hFile, MF_STRING, IDM_FILE_SAVE, L"&Save\tCtrl+S");
    AppendMenuW(hFile, MF_STRING, IDM_FILE_SAVEAS, L"Save &As...");

    g_app.hRecentMenu = CreatePopupMenu();
    AppendMenuW(hFile, MF_POPUP, (UINT_PTR)g_app.hRecentMenu, L"Open &Recent");

    AppendMenuW(hFile, MF_SEPARATOR, 0, NULL);
    AppendMenuW(hFile, MF_STRING, IDM_FILE_EXIT, L"E&xit");

    AppendMenuW(hEdit, MF_STRING, IDM_EDIT_UNDO, L"&Undo\tCtrl+Z");
    AppendMenuW(hEdit, MF_SEPARATOR, 0, NULL);
    AppendMenuW(hEdit, MF_STRING, IDM_EDIT_CUT, L"Cu&t\tCtrl+X");
    AppendMenuW(hEdit, MF_STRING, IDM_EDIT_COPY, L"&Copy\tCtrl+C");
    AppendMenuW(hEdit, MF_STRING, IDM_EDIT_PASTE, L"&Paste\tCtrl+V");
    AppendMenuW(hEdit, MF_SEPARATOR, 0, NULL);
    AppendMenuW(hEdit, MF_STRING, IDM_EDIT_FIND, L"&Find...\tCtrl+F");
    AppendMenuW(hEdit, MF_STRING, IDM_EDIT_REPLACE, L"&Replace...\tCtrl+H");
    AppendMenuW(hEdit, MF_SEPARATOR, 0, NULL);
    AppendMenuW(hEdit, MF_STRING, IDM_EDIT_SELECTALL, L"Select &All\tCtrl+A");

    AppendMenuW(hMain, MF_POPUP, (UINT_PTR)hFile, L"&File");
    AppendMenuW(hMain, MF_POPUP, (UINT_PTR)hEdit, L"&Edit");

    return hMain;
}

static void size_children(HWND hwnd) {
    RECT rc;
    GetClientRect(hwnd, &rc);

    SendMessageW(g_app.hwndStatus, WM_SIZE, 0, 0);

    RECT sr;
    GetWindowRect(g_app.hwndStatus, &sr);
    int statusHeight = sr.bottom - sr.top;

    MoveWindow(g_app.hwndEditor, 0, 0, rc.right, rc.bottom - statusHeight, TRUE);
}

static LRESULT CALLBACK wndproc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    if (msg == g_app.findReplaceMsg) {
        LPFINDREPLACEW pfr = (LPFINDREPLACEW)lParam;
        if (pfr->Flags & FR_DIALOGTERM) {
            if (pfr == &g_app.fr) {
                g_app.hFindDlg = NULL;
                g_app.hReplaceDlg = NULL;
            }
            return 0;
        }

        if (pfr->Flags & FR_FINDNEXT) {
            find_next(g_app.findText, pfr->Flags);
            return 0;
        }

        if (pfr->Flags & FR_REPLACE) {
            replace_current_selection(g_app.replaceText);
            find_next(g_app.findText, pfr->Flags | FR_DOWN);
            return 0;
        }

        if (pfr->Flags & FR_REPLACEALL) {
            int replaced = 0;
            while (find_next(g_app.findText, pfr->Flags | FR_DOWN)) {
                replace_current_selection(g_app.replaceText);
                replaced++;
            }
            wchar_t info[128];
            _snwprintf_s(info, _countof(info), _TRUNCATE, L"Replace All complete. %d replacements.", replaced);
            MessageBoxW(g_app.hwndMain, info, APP_NAME, MB_OK | MB_ICONINFORMATION);
            return 0;
        }
    }

    switch (msg) {
        case WM_CREATE: {
            g_app.hwndMain = hwnd;

            g_app.hwndEditor = CreateWindowExW(
                WS_EX_CLIENTEDGE,
                MSFTEDIT_CLASS,
                L"",
                WS_CHILD | WS_VISIBLE | WS_VSCROLL | WS_HSCROLL | ES_MULTILINE | ES_AUTOVSCROLL | ES_AUTOHSCROLL,
                0, 0, 0, 0,
                hwnd,
                (HMENU)IDC_EDITOR,
                GetModuleHandleW(NULL),
                NULL
            );

            g_app.hwndStatus = CreateWindowExW(
                0,
                STATUSCLASSNAMEW,
                L"Ready",
                WS_CHILD | WS_VISIBLE,
                0, 0, 0, 0,
                hwnd,
                (HMENU)IDC_STATUS,
                GetModuleHandleW(NULL),
                NULL
            );

            HFONT hFont = (HFONT)GetStockObject(DEFAULT_GUI_FONT);
            SendMessageW(g_app.hwndEditor, WM_SETFONT, (WPARAM)hFont, TRUE);
            SendMessageW(g_app.hwndStatus, WM_SETFONT, (WPARAM)hFont, TRUE);

            refresh_recent_menu();

            set_current_path(NULL);
            update_window_title();
            return 0;
        }

        case WM_SIZE:
            size_children(hwnd);
            return 0;

        case WM_COMMAND: {
            int cmd = LOWORD(wParam);
            int notify = HIWORD(wParam);

            if ((HWND)lParam == g_app.hwndEditor && notify == EN_CHANGE) {
                update_window_title();
                return 0;
            }

            if (cmd >= IDM_RECENT_BASE && cmd <= IDM_RECENT_MAX) {
                int idx = cmd - IDM_RECENT_BASE;
                if (idx >= 0 && idx < g_app.recentCount) {
                    if (prompt_discard_changes()) {
                        load_document_path(g_app.recentFiles[idx]);
                    }
                }
                return 0;
            }

            switch (cmd) {
                case IDM_FILE_NEW:
                    do_new_document();
                    return 0;
                case IDM_FILE_OPEN:
                    do_open_document();
                    return 0;
                case IDM_FILE_SAVE:
                    do_save();
                    return 0;
                case IDM_FILE_SAVEAS:
                    do_save_as();
                    return 0;
                case IDM_FILE_EXIT:
                    PostMessageW(hwnd, WM_CLOSE, 0, 0);
                    return 0;

                case IDM_EDIT_UNDO:
                    SendMessageW(g_app.hwndEditor, WM_UNDO, 0, 0);
                    return 0;
                case IDM_EDIT_CUT:
                    SendMessageW(g_app.hwndEditor, WM_CUT, 0, 0);
                    return 0;
                case IDM_EDIT_COPY:
                    SendMessageW(g_app.hwndEditor, WM_COPY, 0, 0);
                    return 0;
                case IDM_EDIT_PASTE:
                    SendMessageW(g_app.hwndEditor, WM_PASTE, 0, 0);
                    return 0;
                case IDM_EDIT_FIND:
                    open_find_dialog(false);
                    return 0;
                case IDM_EDIT_REPLACE:
                    open_find_dialog(true);
                    return 0;
                case IDM_EDIT_SELECTALL:
                    SendMessageW(g_app.hwndEditor, EM_SETSEL, 0, -1);
                    return 0;
            }
            break;
        }

        case WM_CLOSE:
            if (!prompt_discard_changes()) {
                return 0;
            }
            DestroyWindow(hwnd);
            return 0;

        case WM_DESTROY:
            PostQuitMessage(0);
            return 0;
    }

    return DefWindowProcW(hwnd, msg, wParam, lParam);
}

int WINAPI wWinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPWSTR lpCmdLine, int nCmdShow) {
    (void)hPrevInstance;
    (void)lpCmdLine;

    INITCOMMONCONTROLSEX icc;
    icc.dwSize = sizeof(icc);
    icc.dwICC = ICC_STANDARD_CLASSES | ICC_BAR_CLASSES;
    InitCommonControlsEx(&icc);

    g_app.findReplaceMsg = RegisterWindowMessageW(FINDMSGSTRING);

    LoadLibraryW(L"Msftedit.dll");

    wchar_t appRoot[MAX_PATH];
    GetCurrentDirectoryW(_countof(appRoot), appRoot);
    dotxt_load_plugins(appRoot, &g_app.pluginReport);

    WNDCLASSEXW wc;
    ZeroMemory(&wc, sizeof(wc));
    wc.cbSize = sizeof(wc);
    wc.lpfnWndProc = wndproc;
    wc.hInstance = hInstance;
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);
    wc.hIcon = LoadIcon(NULL, IDI_APPLICATION);
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    wc.lpszClassName = L"dotxt_main_window";

    if (!RegisterClassExW(&wc)) {
        MessageBoxW(NULL, L"Failed to register window class.", APP_NAME, MB_ICONERROR | MB_OK);
        return 1;
    }

    g_app.hMainMenu = build_menu();

    HWND hwnd = CreateWindowExW(
        0,
        wc.lpszClassName,
        APP_NAME,
        WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT,
        CW_USEDEFAULT,
        1100,
        740,
        NULL,
        g_app.hMainMenu,
        hInstance,
        NULL
    );

    if (!hwnd) {
        MessageBoxW(NULL, L"Failed to create main window.", APP_NAME, MB_ICONERROR | MB_OK);
        return 1;
    }

    ShowWindow(hwnd, nCmdShow);
    UpdateWindow(hwnd);

    wchar_t pluginInfo[256];
    _snwprintf_s(pluginInfo, _countof(pluginInfo), _TRUNCATE,
        L"Plugins: %d loaded, %d failed (%d manifests)",
        g_app.pluginReport.loaded, g_app.pluginReport.failed, g_app.pluginReport.manifestsFound);
    SendMessageW(g_app.hwndStatus, SB_SETTEXTW, 0, (LPARAM)pluginInfo);

    MSG msg;
    while (GetMessageW(&msg, NULL, 0, 0) > 0) {
        if (g_app.hFindDlg && IsDialogMessageW(g_app.hFindDlg, &msg)) {
            continue;
        }
        if (g_app.hReplaceDlg && IsDialogMessageW(g_app.hReplaceDlg, &msg)) {
            continue;
        }

        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }

    return (int)msg.wParam;
}

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    (void)lpCmdLine;
    return wWinMain(hInstance, hPrevInstance, GetCommandLineW(), nCmdShow);
}
