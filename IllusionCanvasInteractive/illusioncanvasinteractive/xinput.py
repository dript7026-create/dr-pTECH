from __future__ import annotations

import ctypes
from ctypes import wintypes


ERROR_SUCCESS = 0
XINPUT_GAMEPAD_DPAD_UP = 0x0001
XINPUT_GAMEPAD_DPAD_DOWN = 0x0002
XINPUT_GAMEPAD_DPAD_LEFT = 0x0004
XINPUT_GAMEPAD_DPAD_RIGHT = 0x0008
XINPUT_GAMEPAD_START = 0x0010
XINPUT_GAMEPAD_BACK = 0x0020
XINPUT_GAMEPAD_LEFT_SHOULDER = 0x0100
XINPUT_GAMEPAD_RIGHT_SHOULDER = 0x0200
XINPUT_GAMEPAD_A = 0x1000
XINPUT_GAMEPAD_B = 0x2000
XINPUT_GAMEPAD_X = 0x4000
XINPUT_GAMEPAD_Y = 0x8000


class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ("wButtons", wintypes.WORD),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]


class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
        ("dwPacketNumber", wintypes.DWORD),
        ("Gamepad", XINPUT_GAMEPAD),
    ]


def _load_xinput():
    for dll_name in ("xinput1_4", "xinput1_3", "xinput9_1_0"):
        try:
            return ctypes.WinDLL(dll_name)
        except OSError:
            continue
    return None


_XINPUT = _load_xinput()


def available() -> bool:
    return _XINPUT is not None


def _axis(value: int, deadzone: int = 8192) -> float:
    if abs(value) < deadzone:
        return 0.0
    return max(-1.0, min(1.0, value / 32767.0))


def read_gamepad(index: int = 0) -> dict | None:
    if _XINPUT is None:
        return None
    state = XINPUT_STATE()
    if _XINPUT.XInputGetState(index, ctypes.byref(state)) != ERROR_SUCCESS:
        return None
    buttons = state.Gamepad.wButtons
    left_x = _axis(state.Gamepad.sThumbLX)
    left_y = _axis(state.Gamepad.sThumbLY)
    return {
        "connected": True,
        "left_x": left_x,
        "left_y": left_y,
        "a": bool(buttons & XINPUT_GAMEPAD_A),
        "b": bool(buttons & XINPUT_GAMEPAD_B),
        "x": bool(buttons & XINPUT_GAMEPAD_X),
        "y": bool(buttons & XINPUT_GAMEPAD_Y),
        "lb": bool(buttons & XINPUT_GAMEPAD_LEFT_SHOULDER),
        "rb": bool(buttons & XINPUT_GAMEPAD_RIGHT_SHOULDER),
        "start": bool(buttons & XINPUT_GAMEPAD_START),
        "back": bool(buttons & XINPUT_GAMEPAD_BACK),
        "dpad_up": bool(buttons & XINPUT_GAMEPAD_DPAD_UP),
        "dpad_down": bool(buttons & XINPUT_GAMEPAD_DPAD_DOWN),
        "dpad_left": bool(buttons & XINPUT_GAMEPAD_DPAD_LEFT),
        "dpad_right": bool(buttons & XINPUT_GAMEPAD_DPAD_RIGHT),
        "lt": state.Gamepad.bLeftTrigger / 255.0,
        "rt": state.Gamepad.bRightTrigger / 255.0,
    }