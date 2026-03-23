#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#endif
#include <stdio.h>
#include <conio.h>
#include <time.h>
#include "../include/gba.h"

static volatile unsigned short _host_keys = 0;

// XInput dynamic loader state -------------------------------------------------
#ifdef _WIN32
typedef DWORD (WINAPI *XInputGetState_t)(DWORD, void*);
static HMODULE xinput_lib = NULL;
static XInputGetState_t pXInputGetState = NULL;

// Minimal XInput constants/types so we don't need any headers
#ifndef XINPUT_GAMEPAD_DPAD_UP
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

typedef struct XINPUT_GAMEPAD {
    WORD wButtons;
    BYTE bLeftTrigger;
    BYTE bRightTrigger;
    SHORT sThumbLX;
    SHORT sThumbLY;
    SHORT sThumbRX;
    SHORT sThumbRY;
} XINPUT_GAMEPAD;

typedef struct XINPUT_STATE {
    DWORD dwPacketNumber;
    XINPUT_GAMEPAD Gamepad;
} XINPUT_STATE;

static void ensure_xinput_loaded(void) {
    if (pXInputGetState) return;
    const char *names[] = {"xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll"};
    for (size_t i = 0; i < sizeof(names)/sizeof(names[0]); ++i) {
        HMODULE h = LoadLibraryA(names[i]);
        if (!h) continue;
        XInputGetState_t f = (XInputGetState_t)GetProcAddress(h, "XInputGetState");
        if (f) {
            xinput_lib = h;
            pXInputGetState = f;
            return;
        }
        FreeLibrary(h);
    }
}

// Poll the first controller and merge keys into _host_keys
static void poll_xinput(void) {
    ensure_xinput_loaded();
    if (!pXInputGetState) return;
    XINPUT_STATE state = {0};
    DWORD res = pXInputGetState(0, &state);
    if (res != 0) return; // controller not connected
    WORD b = state.Gamepad.wButtons;
    // Map face buttons
    if (b & XINPUT_GAMEPAD_A) _host_keys |= KEY_A;
    if (b & XINPUT_GAMEPAD_B) _host_keys |= KEY_B;
    if (b & XINPUT_GAMEPAD_START) _host_keys |= KEY_START;
    if (b & XINPUT_GAMEPAD_BACK) _host_keys |= KEY_SELECT;
    if (b & XINPUT_GAMEPAD_LEFT_SHOULDER) _host_keys |= KEY_L;
    if (b & XINPUT_GAMEPAD_RIGHT_SHOULDER) _host_keys |= KEY_R;
    // D-pad
    if (b & XINPUT_GAMEPAD_DPAD_UP) _host_keys |= KEY_UP;
    if (b & XINPUT_GAMEPAD_DPAD_DOWN) _host_keys |= KEY_DOWN;
    if (b & XINPUT_GAMEPAD_DPAD_LEFT) _host_keys |= KEY_LEFT;
    if (b & XINPUT_GAMEPAD_DPAD_RIGHT) _host_keys |= KEY_RIGHT;
    // Left thumb as digital fallback
    const int THUMB_THRESH = 8000;
    if (state.Gamepad.sThumbLY > THUMB_THRESH) _host_keys |= KEY_UP;
    if (state.Gamepad.sThumbLY < -THUMB_THRESH) _host_keys |= KEY_DOWN;
    if (state.Gamepad.sThumbLX < -THUMB_THRESH) _host_keys |= KEY_LEFT;
    if (state.Gamepad.sThumbLX > THUMB_THRESH) _host_keys |= KEY_RIGHT;
    // Triggers -> L/R as alternate mapping
    if (state.Gamepad.bLeftTrigger > 30) _host_keys |= KEY_L;
    if (state.Gamepad.bRightTrigger > 30) _host_keys |= KEY_R;
}
#endif
// -----------------------------------------------------------------------------

void irqInit(void) { /* no-op on host */ }
void irqEnable(int flags) { (void)flags; }

void VBlankIntrWait(void) {
#ifdef _WIN32
    Sleep(16);
#else
    struct timespec ts = {0, 16000000};
    nanosleep(&ts, NULL);
#endif
}

void scanKeys(void) {
    // First, poll XInput controllers (Windows/Xbox Series support)
#ifdef _WIN32
    poll_xinput();
#endif
    // non-blocking keyboard poll; map some keys to GBA masks
    while (_kbhit()) {
        int c = _getch();
        if (c == 0 || c == 224) { // arrow/special
            int s = _getch();
            if (s == 72) _host_keys |= KEY_UP; // up
            if (s == 80) _host_keys |= KEY_DOWN; // down
            if (s == 75) _host_keys |= KEY_LEFT; // left
            if (s == 77) _host_keys |= KEY_RIGHT; // right
        } else {
            if (c == 'a' || c == 'A') _host_keys |= KEY_A;
            if (c == 'b' || c == 'B') _host_keys |= KEY_B;
            if (c == 's' || c == 'S') _host_keys |= KEY_START;
            if (c == 'q' || c == 'Q') _host_keys |= KEY_SELECT;
            if (c == 'l' || c == 'L') _host_keys |= KEY_L;
            if (c == 'r' || c == 'R') _host_keys |= KEY_R;
        }
    }
}

u16 keysDown(void) {
    u16 k = _host_keys;
    _host_keys = 0; // clear after read
    return k;
}

void consoleDemoInit(void) {
    // No special console init required
}

void consoleClear(void) {
#ifdef _WIN32
    system("cls");
#else
    system("clear");
#endif
}
