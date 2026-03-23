#define _CRT_SECURE_NO_WARNINGS

#include "../include/orbengine_game_kernel.hpp"

#include <shellapi.h>
#include <cstdio>
#include <cwchar>

namespace
{
struct CapturePipe
{
    int active;
    FILE *pipe;
    unsigned int capturedFrameCount;
};

struct KernelHostState
{
    const ORBGameKernelCallbacks *callbacks;
    ORBGameKernelLaunchConfig launchConfig;
    ORBEngineSandbox kernel;
    HWND window;
    HDC backBufferDc;
    HBITMAP backBufferBitmap;
    void *backBufferPixels;
    int windowWidth;
    int windowHeight;
    unsigned int timerTickCount;
    CapturePipe capture;
};

KernelHostState g_host = {};

void buildDefaultCaptureBasePath(const wchar_t *gameId, wchar_t *buffer, size_t bufferCount)
{
    SYSTEMTIME localTime;
    CreateDirectoryW(L"captures", NULL);
    GetLocalTime(&localTime);
    _snwprintf(
        buffer,
        bufferCount,
        L"captures\\%ls_%04d%02d%02d_%02d%02d%02d",
        gameId,
        (int)localTime.wYear,
        (int)localTime.wMonth,
        (int)localTime.wDay,
        (int)localTime.wHour,
        (int)localTime.wMinute,
        (int)localTime.wSecond);
    buffer[bufferCount - 1] = 0;
}

void parseLaunchConfig(PWSTR commandLine, const ORBGameKernelCallbacks *callbacks, ORBGameKernelLaunchConfig *config)
{
    int argumentCount = 0;
    LPWSTR *arguments = CommandLineToArgvW(GetCommandLineW(), &argumentCount);
    ZeroMemory(config, sizeof(*config));
    config->captureFrameInterval = 4;
    config->fixedStepMilliseconds = 16;
    config->fixedDeltaSeconds = 0.016f;

    for (int index = 1; arguments && index < argumentCount; ++index)
    {
        const wchar_t *argument = arguments[index];
        if (wcscmp(argument, L"--autoplay-capture") == 0)
        {
            config->autoplayEnabled = 1;
            config->captureEnabled = 1;
            config->exitOnCompletion = 1;
        }
        else if (wcscmp(argument, L"--autoplay") == 0)
        {
            config->autoplayEnabled = 1;
        }
        else if (wcscmp(argument, L"--capture") == 0)
        {
            config->captureEnabled = 1;
        }
        else if (wcscmp(argument, L"--exit-on-completion") == 0)
        {
            config->exitOnCompletion = 1;
        }
        else if (wcsncmp(argument, L"--capture-base=", 15) == 0)
        {
            wcsncpy(config->captureBasePath, argument + 15, MAX_PATH - 1);
            config->captureBasePath[MAX_PATH - 1] = 0;
        }
        else if (wcsncmp(argument, L"--capture-interval=", 19) == 0)
        {
            int parsed = _wtoi(argument + 19);
            if (parsed > 0)
            {
                config->captureFrameInterval = parsed;
            }
        }
    }

    if ((config->captureEnabled || config->autoplayEnabled) && !config->captureBasePath[0])
    {
        buildDefaultCaptureBasePath(callbacks->gameId, config->captureBasePath, MAX_PATH);
    }
    if (config->captureBasePath[0])
    {
        _snwprintf(config->captureVideoPath, MAX_PATH, L"%ls.avi", config->captureBasePath);
        config->captureVideoPath[MAX_PATH - 1] = 0;
    }

    if (arguments)
    {
        LocalFree(arguments);
    }
    (void)commandLine;
}

int initializeBackBuffer(int width, int height)
{
    BITMAPINFO bitmapInfo = {};
    HDC screenDc = GetDC(NULL);
    g_host.backBufferDc = CreateCompatibleDC(screenDc);
    ReleaseDC(NULL, screenDc);
    if (!g_host.backBufferDc)
    {
        return 0;
    }

    bitmapInfo.bmiHeader.biSize = sizeof(bitmapInfo.bmiHeader);
    bitmapInfo.bmiHeader.biWidth = width;
    bitmapInfo.bmiHeader.biHeight = -height;
    bitmapInfo.bmiHeader.biPlanes = 1;
    bitmapInfo.bmiHeader.biBitCount = 32;
    bitmapInfo.bmiHeader.biCompression = BI_RGB;

    g_host.backBufferBitmap = CreateDIBSection(g_host.backBufferDc, &bitmapInfo, DIB_RGB_COLORS, &g_host.backBufferPixels, NULL, 0);
    if (!g_host.backBufferBitmap)
    {
        DeleteDC(g_host.backBufferDc);
        g_host.backBufferDc = NULL;
        return 0;
    }

    SelectObject(g_host.backBufferDc, g_host.backBufferBitmap);
    g_host.windowWidth = width;
    g_host.windowHeight = height;
    return 1;
}

void shutdownBackBuffer()
{
    if (g_host.backBufferBitmap)
    {
        DeleteObject(g_host.backBufferBitmap);
    }
    if (g_host.backBufferDc)
    {
        DeleteDC(g_host.backBufferDc);
    }
    g_host.backBufferBitmap = NULL;
    g_host.backBufferDc = NULL;
    g_host.backBufferPixels = NULL;
}

int initializeCapturePipe()
{
    wchar_t command[2048];
    const wchar_t *ffmpegPath = L"C:\\ProgramData\\chocolatey\\bin\\ffmpeg.exe";
    if (!g_host.launchConfig.captureEnabled)
    {
        return 1;
    }
    if (GetFileAttributesW(ffmpegPath) == INVALID_FILE_ATTRIBUTES)
    {
        return 0;
    }

    _snwprintf(
        command,
        sizeof(command) / sizeof(command[0]),
        L"%ls -y -hide_banner -loglevel error -f rawvideo -pix_fmt bgra -video_size %dx%d -framerate %d -i - -an -c:v mjpeg -q:v 3 \"%ls\"",
        ffmpegPath,
        g_host.windowWidth,
        g_host.windowHeight,
        60 / g_host.launchConfig.captureFrameInterval,
        g_host.launchConfig.captureVideoPath);
    command[(sizeof(command) / sizeof(command[0])) - 1] = 0;

    g_host.capture.pipe = _wpopen(command, L"wb");
    g_host.capture.active = g_host.capture.pipe != NULL;
    g_host.capture.capturedFrameCount = 0;
    return g_host.capture.active;
}

void shutdownCapturePipe()
{
    if (g_host.capture.pipe)
    {
        fflush(g_host.capture.pipe);
        _pclose(g_host.capture.pipe);
    }
    ZeroMemory(&g_host.capture, sizeof(g_host.capture));
}

void captureFrameIfNeeded()
{
    if (!g_host.capture.active)
    {
        return;
    }
    if ((g_host.timerTickCount % (unsigned int)g_host.launchConfig.captureFrameInterval) != 0)
    {
        return;
    }

    size_t byteCount = (size_t)g_host.windowWidth * (size_t)g_host.windowHeight * 4u;
    if (fwrite(g_host.backBufferPixels, 1, byteCount, g_host.capture.pipe) == byteCount)
    {
        g_host.capture.capturedFrameCount += 1;
    }
}

void renderBackBuffer()
{
    RECT clientRect = {0, 0, g_host.windowWidth, g_host.windowHeight};
    HBRUSH clearBrush = CreateSolidBrush(RGB(0, 0, 0));
    FillRect(g_host.backBufferDc, &clientRect, clearBrush);
    DeleteObject(clearBrush);
    g_host.callbacks->render(g_host.backBufferDc, clientRect);
    captureFrameIfNeeded();
}

void blitBackBuffer(HDC targetDc)
{
    BitBlt(targetDc, 0, 0, g_host.windowWidth, g_host.windowHeight, g_host.backBufferDc, 0, 0, SRCCOPY);
}

LRESULT CALLBACK kernelWndProc(HWND hwnd, UINT message, WPARAM wParam, LPARAM lParam)
{
    switch (message)
    {
    case WM_CREATE:
        g_host.window = hwnd;
        if (!initializeBackBuffer(g_host.callbacks->windowWidth, g_host.callbacks->windowHeight))
        {
            return -1;
        }
        orb_sandbox_init(&g_host.kernel);
        if (g_host.callbacks->initialize)
        {
            g_host.callbacks->initialize(&g_host.launchConfig, &g_host.kernel);
        }
        initializeCapturePipe();
        renderBackBuffer();
        SetTimer(hwnd, 1, g_host.launchConfig.fixedStepMilliseconds, NULL);
        return 0;
    case WM_TIMER:
        g_host.timerTickCount += 1;
        orb_sandbox_step(&g_host.kernel, g_host.launchConfig.fixedDeltaSeconds);
        if (g_host.callbacks->step)
        {
            g_host.callbacks->step(g_host.launchConfig.fixedDeltaSeconds);
        }
        renderBackBuffer();
        InvalidateRect(hwnd, NULL, FALSE);
        if (g_host.launchConfig.exitOnCompletion && g_host.callbacks->shouldClose && g_host.callbacks->shouldClose())
        {
            PostMessageW(hwnd, WM_CLOSE, 0, 0);
        }
        return 0;
    case WM_KEYDOWN:
        if (g_host.callbacks->keyDown)
        {
            g_host.callbacks->keyDown(wParam);
        }
        return 0;
    case WM_KEYUP:
        if (g_host.callbacks->keyUp)
        {
            g_host.callbacks->keyUp(wParam);
        }
        return 0;
    case WM_PAINT:
    {
        PAINTSTRUCT paint;
        HDC hdc = BeginPaint(hwnd, &paint);
        blitBackBuffer(hdc);
        EndPaint(hwnd, &paint);
        return 0;
    }
    case WM_DESTROY:
        KillTimer(hwnd, 1);
        shutdownCapturePipe();
        if (g_host.callbacks->shutdown)
        {
            g_host.callbacks->shutdown();
        }
        shutdownBackBuffer();
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProcW(hwnd, message, wParam, lParam);
}
} // namespace

int orb_run_game_kernel(HINSTANCE instance, int showCommand, PWSTR commandLine, const ORBGameKernelCallbacks *callbacks)
{
    WNDCLASSEXW windowClass = {};
    HWND window;
    MSG message;

    ZeroMemory(&g_host, sizeof(g_host));
    g_host.callbacks = callbacks;
    parseLaunchConfig(commandLine, callbacks, &g_host.launchConfig);

    windowClass.cbSize = sizeof(windowClass);
    windowClass.lpfnWndProc = kernelWndProc;
    windowClass.hInstance = instance;
    windowClass.lpszClassName = callbacks->windowClassName;
    windowClass.hCursor = LoadCursor(NULL, IDC_ARROW);
    windowClass.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    RegisterClassExW(&windowClass);

    window = CreateWindowExW(
        WS_EX_APPWINDOW,
        callbacks->windowClassName,
        callbacks->windowTitle,
        WS_OVERLAPPEDWINDOW | WS_VISIBLE,
        CW_USEDEFAULT,
        CW_USEDEFAULT,
        callbacks->windowWidth,
        callbacks->windowHeight,
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