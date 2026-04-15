from __future__ import annotations

import ctypes
from dataclasses import dataclass


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
ERROR_SUCCESS = 0


class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ("wButtons", ctypes.c_ushort),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]


class XINPUT_STATE(ctypes.Structure):
    _fields_ = [("dwPacketNumber", ctypes.c_ulong), ("Gamepad", XINPUT_GAMEPAD)]


@dataclass(frozen=True)
class ControllerSnapshot:
    connected: bool = False
    buttons: int = 0
    left_trigger: int = 0
    right_trigger: int = 0
    left_x: int = 0
    left_y: int = 0

    def pressed(self, flag: int) -> bool:
        return bool(self.buttons & flag)


class XInputController:
    def __init__(self, user_index: int = 0) -> None:
        self.user_index = user_index
        self._dll = self._load_xinput()

    def _load_xinput(self):
        for name in ("xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll"):
            try:
                return ctypes.WinDLL(name)
            except OSError:
                continue
        return None

    def poll(self) -> ControllerSnapshot:
        if self._dll is None:
            return ControllerSnapshot()
        state = XINPUT_STATE()
        result = self._dll.XInputGetState(self.user_index, ctypes.byref(state))
        if result != ERROR_SUCCESS:
            return ControllerSnapshot()
        gamepad = state.Gamepad
        return ControllerSnapshot(
            connected=True,
            buttons=int(gamepad.wButtons),
            left_trigger=int(gamepad.bLeftTrigger),
            right_trigger=int(gamepad.bRightTrigger),
            left_x=int(gamepad.sThumbLX),
            left_y=int(gamepad.sThumbLY),
        )
