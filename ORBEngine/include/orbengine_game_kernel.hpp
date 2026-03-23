#ifndef ORBENGINE_GAME_KERNEL_HPP
#define ORBENGINE_GAME_KERNEL_HPP

#include <windows.h>

#include "orbengine.h"

struct ORBGameKernelLaunchConfig
{
    int autoplayEnabled;
    int captureEnabled;
    int exitOnCompletion;
    int captureFrameInterval;
    int fixedStepMilliseconds;
    float fixedDeltaSeconds;
    wchar_t captureBasePath[MAX_PATH];
    wchar_t captureVideoPath[MAX_PATH];
};

typedef void (*ORBGameKernelInitializeProc)(const ORBGameKernelLaunchConfig *launchConfig, ORBEngineSandbox *kernel);
typedef void (*ORBGameKernelShutdownProc)();
typedef void (*ORBGameKernelStepProc)(float deltaSeconds);
typedef void (*ORBGameKernelRenderProc)(HDC hdc, RECT clientRect);
typedef void (*ORBGameKernelKeyProc)(WPARAM wParam);
typedef int (*ORBGameKernelShouldCloseProc)();

struct ORBGameKernelCallbacks
{
    const wchar_t *gameId;
    const wchar_t *windowClassName;
    const wchar_t *windowTitle;
    int windowWidth;
    int windowHeight;
    ORBGameKernelInitializeProc initialize;
    ORBGameKernelShutdownProc shutdown;
    ORBGameKernelStepProc step;
    ORBGameKernelRenderProc render;
    ORBGameKernelKeyProc keyDown;
    ORBGameKernelKeyProc keyUp;
    ORBGameKernelShouldCloseProc shouldClose;
};

int orb_run_game_kernel(HINSTANCE instance, int showCommand, PWSTR commandLine, const ORBGameKernelCallbacks *callbacks);

#endif