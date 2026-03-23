#define _CRT_SECURE_NO_WARNINGS

#include "../include/orbengine.h"

#include <windows.h>
#include <gdiplus.h>
#include <gdiplus/gdiplusinit.h>
#include <gdiplus/gdiplusflat.h>
#include <wchar.h>

#ifdef __cplusplus
using namespace Gdiplus;
using namespace Gdiplus::DllExports;
#endif

#define ORB_SANDBOX_CLASS L"ORBEngineSandboxWindow"

static LRESULT CALLBACK orb_sandbox_wnd_proc(HWND hwnd, UINT message, WPARAM wParam, LPARAM lParam);
static void orb_handle_paint(HWND hwnd);
static int orb_ui_bitmap_ready_local(const ORBUIBitmapAsset *asset);
static void orb_ui_build_asset_path(const wchar_t *relativePath, wchar_t *buffer, size_t bufferCount);
static int orb_ui_load_bitmap_asset(const wchar_t *relativePath, ORBUIBitmapAsset *asset);
static void orb_ui_load_shell_assets(ORBEngineSandbox *sandbox);
static HCURSOR orb_ui_create_cursor_from_asset(const ORBUIBitmapAsset *asset);
static void orb_ui_release_bitmap_asset(ORBUIBitmapAsset *asset);
static void orb_ui_release_shell_assets(ORBEngineSandbox *sandbox);

static ORBEngineSandbox g_sandbox;
static ULONG_PTR g_gdiplus_token;
static int g_gdiplus_started;

static LRESULT CALLBACK orb_sandbox_wnd_proc(HWND hwnd, UINT message, WPARAM wParam, LPARAM lParam)
{
    switch (message)
    {
    case WM_CREATE:
        if (!g_gdiplus_started)
        {
            GdiplusStartupInput startupInput;
            startupInput.GdiplusVersion = 1;
            startupInput.DebugEventCallback = NULL;
            startupInput.SuppressBackgroundThread = FALSE;
            startupInput.SuppressExternalCodecs = FALSE;
            if (GdiplusStartup(&g_gdiplus_token, &startupInput, NULL) == Ok)
            {
                g_gdiplus_started = 1;
            }
        }
        orb_sandbox_init(&g_sandbox);
        orb_ui_load_shell_assets(&g_sandbox);
        SetTimer(hwnd, 1, 16, NULL);
        return 0;
    case WM_TIMER:
        orb_sandbox_step(&g_sandbox, 0.016f);
        InvalidateRect(hwnd, NULL, TRUE);
        return 0;
    case WM_KEYDOWN:
        orb_sandbox_handle_key(&g_sandbox, wParam);
        InvalidateRect(hwnd, NULL, TRUE);
        return 0;
    case WM_PAINT:
        orb_handle_paint(hwnd);
        return 0;
    case WM_SETCURSOR:
        if (LOWORD(lParam) == HTCLIENT && g_sandbox.uiShell.precisionCursor != NULL)
        {
            SetCursor(g_sandbox.uiShell.precisionCursor);
            return TRUE;
        }
        break;
    case WM_DESTROY:
        KillTimer(hwnd, 1);
        orb_ui_release_shell_assets(&g_sandbox);
        if (g_gdiplus_started)
        {
            GdiplusShutdown(g_gdiplus_token);
            g_gdiplus_started = 0;
        }
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProcW(hwnd, message, wParam, lParam);
}

static void orb_handle_paint(HWND hwnd)
{
    PAINTSTRUCT paint;
    RECT clientRect;
    HDC hdc = BeginPaint(hwnd, &paint);
    GetClientRect(hwnd, &clientRect);
    orb_sandbox_render(&g_sandbox, hdc, clientRect);
    EndPaint(hwnd, &paint);
}

static int orb_ui_bitmap_ready_local(const ORBUIBitmapAsset *asset)
{
    return asset != NULL && asset->bitmap != NULL && asset->width > 0 && asset->height > 0;
}

static void orb_ui_build_asset_path(const wchar_t *relativePath, wchar_t *buffer, size_t bufferCount)
{
    DWORD length = GetModuleFileNameW(NULL, buffer, (DWORD)bufferCount);
    while (length > 0 && buffer[length - 1] != L'\\' && buffer[length - 1] != L'/')
    {
        --length;
    }
    buffer[length] = 0;
    wcsncat(buffer, relativePath, bufferCount - wcslen(buffer) - 1);
}

static int orb_ui_load_bitmap_asset(const wchar_t *relativePath, ORBUIBitmapAsset *asset)
{
    wchar_t fullPath[MAX_PATH];
    GpBitmap *bitmap = NULL;
    UINT width = 0;
    UINT height = 0;
    HBITMAP hbitmap = NULL;

    ZeroMemory(asset, sizeof(*asset));
    if (!g_gdiplus_started)
    {
        return 0;
    }

    orb_ui_build_asset_path(relativePath, fullPath, MAX_PATH);
    if (GdipCreateBitmapFromFile(fullPath, &bitmap) != Ok || bitmap == NULL)
    {
        return 0;
    }

    GdipGetImageWidth((GpImage *)bitmap, &width);
    GdipGetImageHeight((GpImage *)bitmap, &height);
    if (GdipCreateHBITMAPFromBitmap(bitmap, &hbitmap, 0) != Ok)
    {
        GdipDisposeImage((GpImage *)bitmap);
        return 0;
    }

    asset->bitmap = hbitmap;
    asset->width = (int)width;
    asset->height = (int)height;
    GdipDisposeImage((GpImage *)bitmap);
    return 1;
}

static void orb_ui_load_shell_assets(ORBEngineSandbox *sandbox)
{
    ORBUIShellAssets *ui = &sandbox->uiShell;
    ui->loaded = 0;
    orb_ui_load_bitmap_asset(L"assets\\orbengine_ui_shell\\orbengine_ui_shell\\orb_shell_main_window_frame.png", &ui->mainWindowFrame);
    orb_ui_load_bitmap_asset(L"assets\\orbengine_ui_shell\\orbengine_ui_shell\\orb_shell_scene_hierarchy_panel.png", &ui->sceneHierarchyPanel);
    orb_ui_load_bitmap_asset(L"assets\\orbengine_ui_shell\\orbengine_ui_shell\\orb_shell_inspector_panel.png", &ui->inspectorPanel);
    orb_ui_load_bitmap_asset(L"assets\\orbengine_ui_shell\\orbengine_ui_shell\\orb_shell_asset_browser_panel.png", &ui->assetBrowserPanel);
    orb_ui_load_bitmap_asset(L"assets\\orbengine_ui_shell\\orbengine_ui_shell\\orb_shell_console_log_panel.png", &ui->consoleLogPanel);
    orb_ui_load_bitmap_asset(L"assets\\orbengine_ui_shell\\orbengine_ui_shell\\orb_shell_timeline_panel.png", &ui->timelinePanel);
    orb_ui_load_bitmap_asset(L"assets\\orbengine_ui_shell\\orbengine_ui_shell\\orb_shell_tool_properties_float.png", &ui->toolPropertiesFloat);
    orb_ui_load_bitmap_asset(L"assets\\orbengine_ui_shell\\orbengine_ui_shell\\orb_popup_modal_template.png", &ui->modalTemplate);
    orb_ui_load_bitmap_asset(L"assets\\orbengine_ui_shell\\orbengine_ui_shell\\orb_popup_context_menu_shell.png", &ui->contextMenuShell);
    orb_ui_load_bitmap_asset(L"assets\\orbengine_ui_shell\\orbengine_ui_shell\\orb_popup_dropdown_shell.png", &ui->dropdownShell);
    orb_ui_load_bitmap_asset(L"assets\\orbengine_ui_shell\\orbengine_ui_shell\\orb_popup_notification_toast.png", &ui->notificationToast);
    orb_ui_load_bitmap_asset(L"assets\\orbengine_ui_shell\\orbengine_ui_shell\\orb_popup_tooltip_shell.png", &ui->tooltipShell);
    orb_ui_load_bitmap_asset(L"assets\\orbengine_ui_shell\\orbengine_ui_shell\\orb_popup_dialog_choice_grid.png", &ui->dialogChoiceGrid);
    orb_ui_load_bitmap_asset(L"assets\\orbengine_ui_shell\\orbengine_ui_shell\\orb_nav_workspace_switcher.png", &ui->workspaceSwitcher);
    orb_ui_load_bitmap_asset(L"assets\\orbengine_ui_shell\\orbengine_ui_shell\\orb_nav_tabs_primary_strip.png", &ui->primaryTabs);
    orb_ui_load_bitmap_asset(L"assets\\orbengine_ui_shell\\orbengine_ui_shell\\orb_nav_tabs_secondary_strip.png", &ui->secondaryTabs);
    orb_ui_load_bitmap_asset(L"assets\\orbengine_ui_shell\\orbengine_ui_shell\\orb_icons_toolbar_world.png", &ui->toolbarWorld);
    orb_ui_load_bitmap_asset(L"assets\\orbengine_ui_shell\\orbengine_ui_shell\\orb_icons_toolbar_scripting.png", &ui->toolbarScripting);
    orb_ui_load_bitmap_asset(L"assets\\orbengine_ui_shell\\orbengine_ui_shell\\orb_icons_toolbar_animation.png", &ui->toolbarAnimation);
    orb_ui_load_bitmap_asset(L"assets\\orbengine_ui_shell\\orbengine_ui_shell\\orb_icons_toolbar_materials.png", &ui->toolbarMaterials);
    orb_ui_load_bitmap_asset(L"assets\\orbengine_ui_shell\\orbengine_ui_shell\\orb_icons_status_indicators.png", &ui->statusIndicators);
    orb_ui_load_bitmap_asset(L"assets\\orbengine_ui_shell\\orbengine_ui_shell\\orb_icons_window_controls.png", &ui->windowControls);
    orb_ui_load_bitmap_asset(L"assets\\orbengine_ui_shell\\orbengine_ui_shell\\orb_font_monotype_uppercase_atlas.png", &ui->fontUppercase);
    orb_ui_load_bitmap_asset(L"assets\\orbengine_ui_shell\\orbengine_ui_shell\\orb_font_monotype_lowercase_atlas.png", &ui->fontLowercase);
    orb_ui_load_bitmap_asset(L"assets\\orbengine_ui_shell\\orbengine_ui_shell\\orb_font_monotype_numeric_atlas.png", &ui->fontNumeric);
    orb_ui_load_bitmap_asset(L"assets\\orbengine_ui_shell\\orbengine_ui_shell\\orb_font_monotype_extended_ui_atlas.png", &ui->fontExtendedUi);
    orb_ui_load_bitmap_asset(L"assets\\orbengine_ui_shell\\orbengine_ui_shell\\orb_cursor_precision_set.png", &ui->cursorPrecision);
    ui->precisionCursor = orb_ui_create_cursor_from_asset(&ui->cursorPrecision);
    ui->loaded = ui->mainWindowFrame.bitmap != NULL;
}

static HCURSOR orb_ui_create_cursor_from_asset(const ORBUIBitmapAsset *asset)
{
    HDC screenDc;
    HDC sourceDc;
    HDC colorDc;
    HBITMAP sourceOldBitmap;
    HBITMAP colorBitmap;
    HBITMAP colorOldBitmap;
    HBITMAP maskBitmap;
    BITMAPINFO bitmapInfo;
    ICONINFO iconInfo;
    BLENDFUNCTION blend;
    void *bits;
    int tileWidth;
    int tileHeight;
    HCURSOR cursor;

    if (!orb_ui_bitmap_ready_local(asset))
    {
        return NULL;
    }

    tileWidth = asset->width / 2;
    tileHeight = asset->height / 2;
    if (tileWidth <= 0 || tileHeight <= 0)
    {
        return NULL;
    }

    ZeroMemory(&bitmapInfo, sizeof(bitmapInfo));
    bitmapInfo.bmiHeader.biSize = sizeof(bitmapInfo.bmiHeader);
    bitmapInfo.bmiHeader.biWidth = 48;
    bitmapInfo.bmiHeader.biHeight = -48;
    bitmapInfo.bmiHeader.biPlanes = 1;
    bitmapInfo.bmiHeader.biBitCount = 32;
    bitmapInfo.bmiHeader.biCompression = BI_RGB;

    screenDc = GetDC(NULL);
    sourceDc = CreateCompatibleDC(screenDc);
    colorDc = CreateCompatibleDC(screenDc);
    sourceOldBitmap = (HBITMAP)SelectObject(sourceDc, asset->bitmap);
    colorBitmap = CreateDIBSection(screenDc, &bitmapInfo, DIB_RGB_COLORS, &bits, NULL, 0);
    colorOldBitmap = (HBITMAP)SelectObject(colorDc, colorBitmap);
    maskBitmap = CreateBitmap(48, 48, 1, 1, NULL);

    PatBlt(colorDc, 0, 0, 48, 48, BLACKNESS);
    blend.BlendOp = AC_SRC_OVER;
    blend.BlendFlags = 0;
    blend.SourceConstantAlpha = 255;
    blend.AlphaFormat = AC_SRC_ALPHA;
    AlphaBlend(colorDc, 0, 0, 48, 48, sourceDc, 0, 0, tileWidth, tileHeight, blend);

    ZeroMemory(&iconInfo, sizeof(iconInfo));
    iconInfo.fIcon = FALSE;
    iconInfo.xHotspot = 6;
    iconInfo.yHotspot = 6;
    iconInfo.hbmMask = maskBitmap;
    iconInfo.hbmColor = colorBitmap;
    cursor = CreateIconIndirect(&iconInfo);

    SelectObject(sourceDc, sourceOldBitmap);
    SelectObject(colorDc, colorOldBitmap);
    DeleteDC(sourceDc);
    DeleteDC(colorDc);
    ReleaseDC(NULL, screenDc);
    DeleteObject(maskBitmap);
    DeleteObject(colorBitmap);
    return cursor;
}

static void orb_ui_release_bitmap_asset(ORBUIBitmapAsset *asset)
{
    if (asset->bitmap != NULL)
    {
        DeleteObject(asset->bitmap);
        asset->bitmap = NULL;
    }
    asset->width = 0;
    asset->height = 0;
}

static void orb_ui_release_shell_assets(ORBEngineSandbox *sandbox)
{
    ORBUIShellAssets *ui = &sandbox->uiShell;
    orb_ui_release_bitmap_asset(&ui->mainWindowFrame);
    orb_ui_release_bitmap_asset(&ui->sceneHierarchyPanel);
    orb_ui_release_bitmap_asset(&ui->inspectorPanel);
    orb_ui_release_bitmap_asset(&ui->assetBrowserPanel);
    orb_ui_release_bitmap_asset(&ui->consoleLogPanel);
    orb_ui_release_bitmap_asset(&ui->timelinePanel);
    orb_ui_release_bitmap_asset(&ui->toolPropertiesFloat);
    orb_ui_release_bitmap_asset(&ui->modalTemplate);
    orb_ui_release_bitmap_asset(&ui->contextMenuShell);
    orb_ui_release_bitmap_asset(&ui->dropdownShell);
    orb_ui_release_bitmap_asset(&ui->notificationToast);
    orb_ui_release_bitmap_asset(&ui->tooltipShell);
    orb_ui_release_bitmap_asset(&ui->dialogChoiceGrid);
    orb_ui_release_bitmap_asset(&ui->workspaceSwitcher);
    orb_ui_release_bitmap_asset(&ui->primaryTabs);
    orb_ui_release_bitmap_asset(&ui->secondaryTabs);
    orb_ui_release_bitmap_asset(&ui->toolbarWorld);
    orb_ui_release_bitmap_asset(&ui->toolbarScripting);
    orb_ui_release_bitmap_asset(&ui->toolbarAnimation);
    orb_ui_release_bitmap_asset(&ui->toolbarMaterials);
    orb_ui_release_bitmap_asset(&ui->statusIndicators);
    orb_ui_release_bitmap_asset(&ui->windowControls);
    orb_ui_release_bitmap_asset(&ui->fontUppercase);
    orb_ui_release_bitmap_asset(&ui->fontLowercase);
    orb_ui_release_bitmap_asset(&ui->fontNumeric);
    orb_ui_release_bitmap_asset(&ui->fontExtendedUi);
    orb_ui_release_bitmap_asset(&ui->cursorPrecision);
    if (ui->precisionCursor != NULL)
    {
        DestroyCursor(ui->precisionCursor);
        ui->precisionCursor = NULL;
    }
    ui->loaded = 0;
}

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE previous, PWSTR commandLine, int showCommand)
{
    WNDCLASSEXW windowClass;
    HWND window;
    MSG message;
    (void)previous;
    (void)commandLine;

    ZeroMemory(&windowClass, sizeof(windowClass));
    windowClass.cbSize = sizeof(windowClass);
    windowClass.lpfnWndProc = orb_sandbox_wnd_proc;
    windowClass.hInstance = instance;
    windowClass.lpszClassName = ORB_SANDBOX_CLASS;
    windowClass.hCursor = LoadCursor(NULL, IDC_ARROW);
    windowClass.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    RegisterClassExW(&windowClass);

    window = CreateWindowExW(
        WS_EX_APPWINDOW,
        ORB_SANDBOX_CLASS,
        L"ORBEngine Sandbox - Island / Agriculture / Combat Simulator",
        WS_OVERLAPPEDWINDOW | WS_VISIBLE,
        CW_USEDEFAULT,
        CW_USEDEFAULT,
        1280,
        820,
        NULL,
        NULL,
        instance,
        NULL);

    ShowWindow(window, showCommand);
    UpdateWindow(window);

    while (GetMessageW(&message, NULL, 0, 0) > 0)
    {
        TranslateMessage(&message);
        DispatchMessageW(&message);
    }

    return (int)message.wParam;
}