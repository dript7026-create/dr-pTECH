/* gui_common.h — Shared GUI definitions for ECBMPS and CCP viewers */
#ifndef ECBMPS_CCP_GUI_COMMON_H
#define ECBMPS_CCP_GUI_COMMON_H

#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif

#include <windows.h>
#include <windowsx.h>
#include <commctrl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ---------- Color palette ---------- */
#define GUI_BG_DARK       RGB(22, 24, 30)
#define GUI_BG_PANEL      RGB(34, 38, 48)
#define GUI_BG_PAGE       RGB(245, 240, 232)
#define GUI_BG_PAGE_DARK  RGB(40, 42, 50)
#define GUI_BG_PAGE_SEPIA RGB(240, 224, 196)
#define GUI_TEXT_LIGHT     RGB(230, 232, 238)
#define GUI_TEXT_DARK      RGB(30, 30, 34)
#define GUI_ACCENT         RGB(92, 164, 220)
#define GUI_ACCENT_HOT     RGB(120, 186, 238)
#define GUI_HIGHLIGHT      RGB(250, 220, 80)
#define GUI_BOOKMARK       RGB(220, 60, 60)
#define GUI_BORDER         RGB(58, 62, 76)

/* ---------- Toolbar IDs ---------- */
#define IDC_BTN_PREV       1001
#define IDC_BTN_NEXT       1002
#define IDC_BTN_BOOKMARK   1003
#define IDC_BTN_HIGHLIGHT  1004
#define IDC_BTN_ZOOM_IN    1005
#define IDC_BTN_ZOOM_OUT   1006
#define IDC_BTN_SEARCH     1007
#define IDC_BTN_SETTINGS   1008
#define IDC_BTN_ABOUT      1009
#define IDC_PAGE_LABEL     1010

/* ---------- Popup Window IDs ---------- */
#define IDD_ABOUT          2001
#define IDD_SEARCH         2002
#define IDD_SETTINGS       2003
#define IDD_BOOKMARK_LIST  2004

/* ---------- Custom GUI drawing helpers ---------- */
static void gui_fill_rect(HDC hdc, int x, int y, int w, int h, COLORREF color) {
    HBRUSH brush = CreateSolidBrush(color);
    RECT rc = { x, y, x + w, y + h };
    FillRect(hdc, &rc, brush);
    DeleteObject(brush);
}

static void gui_draw_frame(HDC hdc, int x, int y, int w, int h, COLORREF color) {
    HPEN pen = CreatePen(PS_SOLID, 1, color);
    HPEN old = (HPEN)SelectObject(hdc, pen);
    HBRUSH oldBrush = (HBRUSH)SelectObject(hdc, GetStockObject(NULL_BRUSH));
    Rectangle(hdc, x, y, x + w, y + h);
    SelectObject(hdc, oldBrush);
    SelectObject(hdc, old);
    DeleteObject(pen);
}

static void gui_draw_text(HDC hdc, int x, int y, const wchar_t *text, COLORREF color, HFONT font) {
    HFONT old = (HFONT)SelectObject(hdc, font);
    SetTextColor(hdc, color);
    SetBkMode(hdc, TRANSPARENT);
    TextOutW(hdc, x, y, text, (int)wcslen(text));
    SelectObject(hdc, old);
}

static void gui_draw_rounded_rect(HDC hdc, int x, int y, int w, int h, int r, COLORREF fill, COLORREF border) {
    HBRUSH brush = CreateSolidBrush(fill);
    HPEN pen = CreatePen(PS_SOLID, 1, border);
    HBRUSH oldBrush = (HBRUSH)SelectObject(hdc, brush);
    HPEN oldPen = (HPEN)SelectObject(hdc, pen);
    RoundRect(hdc, x, y, x + w, y + h, r, r);
    SelectObject(hdc, oldPen);
    SelectObject(hdc, oldBrush);
    DeleteObject(pen);
    DeleteObject(brush);
}

/* Custom popup window template */
static HWND gui_create_popup(HWND parent, const wchar_t *title, int w, int h) {
    RECT rc;
    int sx, sy;
    HWND popup;
    GetWindowRect(parent, &rc);
    sx = rc.left + ((rc.right - rc.left) - w) / 2;
    sy = rc.top + ((rc.bottom - rc.top) - h) / 2;
    popup = CreateWindowExW(
        WS_EX_DLGMODALFRAME | WS_EX_TOOLWINDOW,
        L"STATIC", title,
        WS_POPUP | WS_VISIBLE | WS_CAPTION | WS_SYSMENU,
        sx, sy, w, h,
        parent, NULL, GetModuleHandle(NULL), NULL
    );
    return popup;
}

#endif /* ECBMPS_CCP_GUI_COMMON_H */
