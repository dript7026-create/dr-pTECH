#define _CRT_SECURE_NO_WARNINGS

#include "gravo.h"
#include "../ORBEngine/include/orbengine_game_kernel.hpp"

namespace
{
ORBEngineSandbox *g_kernel = nullptr;
GravoRuntimeState *g_runtime = nullptr;

void gravo_initialize(const ORBGameKernelLaunchConfig *launchConfig, ORBEngineSandbox *kernel)
{
    g_kernel = kernel;
    g_runtime = gravo_runtime_create(kernel, launchConfig ? launchConfig->autoplayEnabled : 0);
}

void gravo_shutdown()
{
    gravo_runtime_destroy(g_runtime);
    g_runtime = nullptr;
    g_kernel = nullptr;
}

void gravo_step(float deltaSeconds)
{
    gravo_runtime_step(g_runtime, deltaSeconds);
}

void gravo_render(HDC hdc, RECT clientRect)
{
    if (g_kernel)
    {
        orb_sandbox_render(g_kernel, hdc, clientRect);
    }
    gravo_runtime_render(g_runtime, hdc, clientRect);
}

void gravo_key_down(WPARAM wParam)
{
    gravo_runtime_key_down(g_runtime, wParam);
}

void gravo_key_up(WPARAM wParam)
{
    gravo_runtime_key_up(g_runtime, wParam);
}

int gravo_should_close()
{
    return gravo_runtime_should_close(g_runtime);
}
}

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, PWSTR commandLine, int showCommand)
{
    const ORBGameKernelCallbacks callbacks = {
        L"gravo_boy_dimenhyde",
        L"GravoBoyDimenhydeWindow",
        L"Gravo: Boy Dimenhyde",
        1360,
        840,
        gravo_initialize,
        gravo_shutdown,
        gravo_step,
        gravo_render,
        gravo_key_down,
        gravo_key_up,
        gravo_should_close};

    return orb_run_game_kernel(instance, showCommand, commandLine, &callbacks);
}