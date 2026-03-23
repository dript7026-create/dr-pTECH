/* controller_input.h — XInput controller abstraction for ECBMPS/CCP viewers
 *
 * Provides gamepad polling with LT/RT RESERVED for page navigation.
 * LT = previous page, RT = next page (in BOTH .ccp and .ecbmps viewers).
 * All other buttons are available for gameplay scripting in .ccp files.
 *
 * Dynamically loads XInput at runtime — no DLL link dependency.
 * Tries xinput1_4.dll (Win8+), xinput1_3.dll (DX SDK), xinput9_1_0.dll.
 */

#ifndef CONTROLLER_INPUT_H
#define CONTROLLER_INPUT_H

#include <windows.h>

/* ---- Inline XInput definitions (avoid #include <xinput.h> dependency) ---- */
#ifndef XINPUT_GAMEPAD_DPAD_UP
typedef struct { WORD wButtons; BYTE bLeftTrigger; BYTE bRightTrigger;
    SHORT sThumbLX; SHORT sThumbLY; SHORT sThumbRX; SHORT sThumbRY;
} XINPUT_GAMEPAD;
typedef struct { DWORD dwPacketNumber; XINPUT_GAMEPAD Gamepad; } XINPUT_STATE;
#define XINPUT_GAMEPAD_DPAD_UP        0x0001
#define XINPUT_GAMEPAD_DPAD_DOWN      0x0002
#define XINPUT_GAMEPAD_DPAD_LEFT      0x0004
#define XINPUT_GAMEPAD_DPAD_RIGHT     0x0008
#define XINPUT_GAMEPAD_START          0x0010
#define XINPUT_GAMEPAD_BACK           0x0020
#define XINPUT_GAMEPAD_LEFT_THUMB     0x0040
#define XINPUT_GAMEPAD_RIGHT_THUMB    0x0080
#define XINPUT_GAMEPAD_LEFT_SHOULDER  0x0100
#define XINPUT_GAMEPAD_RIGHT_SHOULDER 0x0200
#define XINPUT_GAMEPAD_A              0x1000
#define XINPUT_GAMEPAD_B              0x2000
#define XINPUT_GAMEPAD_X              0x4000
#define XINPUT_GAMEPAD_Y              0x8000
#endif

typedef DWORD (WINAPI *PFN_XInputGetState)(DWORD, XINPUT_STATE *);

/* Dead zone thresholds */
#define CTRL_STICK_DEADZONE    7849   /* ~24% of 32767 */
#define CTRL_TRIGGER_THRESHOLD 128    /* 0-255 range; ~50% press */

typedef struct {
    int  connected;

    /* Digital buttons (1 = pressed) */
    int  btn_a, btn_b, btn_x, btn_y;
    int  btn_lb, btn_rb;
    int  btn_start, btn_back;
    int  btn_lstick, btn_rstick;
    int  dpad_up, dpad_down, dpad_left, dpad_right;

    /* Analog axes (-1.0 to 1.0) */
    float axis_lx, axis_ly;
    float axis_rx, axis_ry;

    /* Triggers (0.0 to 1.0) */
    float trigger_left;
    float trigger_right;

    /* Page navigation signals (LT/RT reserved) */
    int  page_prev;         /* LT held past threshold */
    int  page_next;         /* RT held past threshold */
    int  page_prev_edge;    /* LT just pressed this frame */
    int  page_next_edge;    /* RT just pressed this frame */
} ControllerState;

static ControllerState g_controller;
static int g_ctrl_prev_lt = 0;
static int g_ctrl_prev_rt = 0;
static HMODULE g_xinput_dll = NULL;
static PFN_XInputGetState g_pfnXInputGetState = NULL;
static int g_xinput_init_done = 0;

static void ctrl_load_xinput(void) {
    if (g_xinput_init_done) return;
    g_xinput_init_done = 1;
    /* Try modern first, fall back to older versions */
    const char *dlls[] = { "xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll" };
    for (int i = 0; i < 3; i++) {
        g_xinput_dll = LoadLibraryA(dlls[i]);
        if (g_xinput_dll) {
            g_pfnXInputGetState = (PFN_XInputGetState)GetProcAddress(g_xinput_dll, "XInputGetState");
            if (g_pfnXInputGetState) return;
            FreeLibrary(g_xinput_dll);
            g_xinput_dll = NULL;
        }
    }
}

static float ctrl_apply_deadzone(SHORT raw, int deadzone) {
    if (raw > deadzone)
        return (float)(raw - deadzone) / (32767 - deadzone);
    if (raw < -deadzone)
        return (float)(raw + deadzone) / (32767 - deadzone);
    return 0.0f;
}

static void controller_poll(void) {
    ctrl_load_xinput();
    if (!g_pfnXInputGetState) {
        memset(&g_controller, 0, sizeof(g_controller));
        return;
    }

    XINPUT_STATE state;
    memset(&state, 0, sizeof(state));
    DWORD result = g_pfnXInputGetState(0, &state);

    g_controller.connected = (result == ERROR_SUCCESS);
    if (!g_controller.connected) {
        memset(&g_controller, 0, sizeof(g_controller));
        g_ctrl_prev_lt = 0;
        g_ctrl_prev_rt = 0;
        return;
    }

    XINPUT_GAMEPAD *gp = &state.Gamepad;

    g_controller.btn_a      = !!(gp->wButtons & XINPUT_GAMEPAD_A);
    g_controller.btn_b      = !!(gp->wButtons & XINPUT_GAMEPAD_B);
    g_controller.btn_x      = !!(gp->wButtons & XINPUT_GAMEPAD_X);
    g_controller.btn_y      = !!(gp->wButtons & XINPUT_GAMEPAD_Y);
    g_controller.btn_lb     = !!(gp->wButtons & XINPUT_GAMEPAD_LEFT_SHOULDER);
    g_controller.btn_rb     = !!(gp->wButtons & XINPUT_GAMEPAD_RIGHT_SHOULDER);
    g_controller.btn_start  = !!(gp->wButtons & XINPUT_GAMEPAD_START);
    g_controller.btn_back   = !!(gp->wButtons & XINPUT_GAMEPAD_BACK);
    g_controller.btn_lstick = !!(gp->wButtons & XINPUT_GAMEPAD_LEFT_THUMB);
    g_controller.btn_rstick = !!(gp->wButtons & XINPUT_GAMEPAD_RIGHT_THUMB);
    g_controller.dpad_up    = !!(gp->wButtons & XINPUT_GAMEPAD_DPAD_UP);
    g_controller.dpad_down  = !!(gp->wButtons & XINPUT_GAMEPAD_DPAD_DOWN);
    g_controller.dpad_left  = !!(gp->wButtons & XINPUT_GAMEPAD_DPAD_LEFT);
    g_controller.dpad_right = !!(gp->wButtons & XINPUT_GAMEPAD_DPAD_RIGHT);

    g_controller.axis_lx = ctrl_apply_deadzone(gp->sThumbLX, CTRL_STICK_DEADZONE);
    g_controller.axis_ly = ctrl_apply_deadzone(gp->sThumbLY, CTRL_STICK_DEADZONE);
    g_controller.axis_rx = ctrl_apply_deadzone(gp->sThumbRX, CTRL_STICK_DEADZONE);
    g_controller.axis_ry = ctrl_apply_deadzone(gp->sThumbRY, CTRL_STICK_DEADZONE);

    g_controller.trigger_left  = (float)gp->bLeftTrigger / 255.0f;
    g_controller.trigger_right = (float)gp->bRightTrigger / 255.0f;

    /* Page navigation edge detection (LT/RT reserved) */
    int lt_pressed = (gp->bLeftTrigger > CTRL_TRIGGER_THRESHOLD);
    int rt_pressed = (gp->bRightTrigger > CTRL_TRIGGER_THRESHOLD);

    g_controller.page_prev      = lt_pressed;
    g_controller.page_next      = rt_pressed;
    g_controller.page_prev_edge = (lt_pressed && !g_ctrl_prev_lt);
    g_controller.page_next_edge = (rt_pressed && !g_ctrl_prev_rt);

    g_ctrl_prev_lt = lt_pressed;
    g_ctrl_prev_rt = rt_pressed;
}

/* Map controller state to GplyVM input (CCP viewer only) */
#ifdef CCP_GAMEPLAY_H
static void controller_update_vm(GplyVM *vm) {
    vm->buttons[GPLY_BTN_A]          = g_controller.btn_a;
    vm->buttons[GPLY_BTN_B]          = g_controller.btn_b;
    vm->buttons[GPLY_BTN_X]          = g_controller.btn_x;
    vm->buttons[GPLY_BTN_Y]          = g_controller.btn_y;
    vm->buttons[GPLY_BTN_DPAD_UP]    = g_controller.dpad_up;
    vm->buttons[GPLY_BTN_DPAD_DOWN]  = g_controller.dpad_down;
    vm->buttons[GPLY_BTN_DPAD_LEFT]  = g_controller.dpad_left;
    vm->buttons[GPLY_BTN_DPAD_RIGHT] = g_controller.dpad_right;
    vm->buttons[GPLY_BTN_START]      = g_controller.btn_start;
    vm->buttons[GPLY_BTN_BACK]       = g_controller.btn_back;
    vm->buttons[GPLY_BTN_LB]         = g_controller.btn_lb;
    vm->buttons[GPLY_BTN_RB]         = g_controller.btn_rb;
    vm->buttons[GPLY_BTN_LSTICK]     = g_controller.btn_lstick;
    vm->buttons[GPLY_BTN_RSTICK]     = g_controller.btn_rstick;

    vm->axes[GPLY_AXIS_LX] = g_controller.axis_lx;
    vm->axes[GPLY_AXIS_LY] = g_controller.axis_ly;
    vm->axes[GPLY_AXIS_RX] = g_controller.axis_rx;
    vm->axes[GPLY_AXIS_RY] = g_controller.axis_ry;

    vm->trigger_left  = g_controller.trigger_left;
    vm->trigger_right = g_controller.trigger_right;
}
#endif

#endif /* CONTROLLER_INPUT_H */
