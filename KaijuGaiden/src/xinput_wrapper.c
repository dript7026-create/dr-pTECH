// Minimal C wrapper that dynamically loads XInput and exposes a simple C API
#include <windows.h>
#include <stdint.h>
#include "xinput_wrapper.h"

typedef DWORD (WINAPI *XInputGetState_t)(DWORD, void*);

int xi_get_state(int idx, unsigned short *buttons, short *lx, short *ly, unsigned char *lt, unsigned char *rt) {
    HMODULE mod = LoadLibraryA("xinput1_4.dll");
    if (!mod) mod = LoadLibraryA("xinput1_3.dll");
    if (!mod) mod = LoadLibraryA("xinput9_1_0.dll");
    if (!mod) return -1;
    XInputGetState_t fn = (XInputGetState_t)GetProcAddress(mod, "XInputGetState");
    if (!fn) return -2;
    // minimal XINPUT_STATE struct size; we'll read into a buffer
    unsigned char buf[28];
    DWORD res = fn((DWORD)idx, buf);
    if (res != 0) return (int)res;
    // parse: dwPacketNumber (4) + XINPUT_GAMEPAD (struct 16)
    unsigned short wButtons = *(unsigned short*)(buf + 4);
    short sThumbLX = *(short*)(buf + 8);
    short sThumbLY = *(short*)(buf + 10);
    unsigned char bLeftTrigger = *(unsigned char*)(buf + 14);
    unsigned char bRightTrigger = *(unsigned char*)(buf + 15);
    if (buttons) *buttons = wButtons;
    if (lx) *lx = sThumbLX;
    if (ly) *ly = sThumbLY;
    if (lt) *lt = bLeftTrigger;
    if (rt) *rt = bRightTrigger;
    return 0;
}
