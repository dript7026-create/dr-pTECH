from __future__ import annotations

import ctypes
from dataclasses import dataclass, asdict


XINPUT_GAMEPAD_DPAD_UP = 0x0001
XINPUT_GAMEPAD_DPAD_DOWN = 0x0002
XINPUT_GAMEPAD_DPAD_LEFT = 0x0004
XINPUT_GAMEPAD_DPAD_RIGHT = 0x0008
XINPUT_GAMEPAD_START = 0x0010
XINPUT_GAMEPAD_BACK = 0x0020
XINPUT_GAMEPAD_LEFT_THUMB = 0x0040
XINPUT_GAMEPAD_RIGHT_THUMB = 0x0080
XINPUT_GAMEPAD_LEFT_SHOULDER = 0x0100
XINPUT_GAMEPAD_RIGHT_SHOULDER = 0x0200
XINPUT_GAMEPAD_A = 0x1000
XINPUT_GAMEPAD_B = 0x2000
XINPUT_GAMEPAD_X = 0x4000
XINPUT_GAMEPAD_Y = 0x8000
ERROR_SUCCESS = 0
MAX_THUMB = 32767.0
MAX_TRIGGER = 255.0


DEFAULT_BINDINGS = {
    "move": "left_stick",
    "aim": "right_stick",
    "shoot": "right_trigger",
    "parry": "left_shoulder",
    "melee": "right_shoulder",
    "dodge": "b",
    "jump": "a",
    "reload": "x",
    "swap_mode": "y",
    "sprint": "left_trigger",
    "pause": "menu",
}


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


@dataclass(slots=True)
class AimVector:
    x: float = 0.0
    y: float = 0.0


@dataclass(slots=True)
class MoveVector:
    x: float = 0.0
    y: float = 0.0


@dataclass(slots=True)
class ControlFrame:
    move: MoveVector
    aim: AimVector
    shoot: bool
    parry: bool
    melee: bool
    evade: bool
    jump: bool
    reload: bool
    swap_mode: bool
    sprint: bool
    pause: bool


@dataclass(slots=True)
class ControllerSnapshot:
    connected: bool = False
    left_x: float = 0.0
    left_y: float = 0.0
    right_x: float = 0.0
    right_y: float = 0.0
    left_trigger: float = 0.0
    right_trigger: float = 0.0
    a: bool = False
    b: bool = False
    x: bool = False
    y: bool = False
    left_stick_press: bool = False
    right_stick_press: bool = False
    left_shoulder: bool = False
    right_shoulder: bool = False
    menu: bool = False
    view: bool = False

    def to_dict(self) -> dict[str, float | bool]:
        return asdict(self)


def _normalize_axis(value: int) -> float:
    return max(-1.0, min(1.0, float(value) / MAX_THUMB))


def _normalize_trigger(value: int) -> float:
    return max(0.0, min(1.0, float(value) / MAX_TRIGGER))


def _apply_deadzone(value: float, deadzone: float = 0.16) -> float:
    if abs(value) < deadzone:
        return 0.0
    return max(-1.0, min(1.0, value))


def translate_raw_state(raw: dict[str, float | bool]) -> ControlFrame:
    return ControlFrame(
        move=MoveVector(
            x=_apply_deadzone(float(raw.get("left_x", 0.0)), 0.1),
            y=_apply_deadzone(float(raw.get("left_y", 0.0)), 0.1),
        ),
        aim=AimVector(
            x=_apply_deadzone(-float(raw.get("right_x", 0.0)), 0.08),
            y=_apply_deadzone(float(raw.get("right_y", 0.0)), 0.08),
        ),
        shoot=float(raw.get("right_trigger", 0.0)) > 0.2,
        parry=bool(raw.get("left_shoulder", False)),
        melee=bool(raw.get("right_shoulder", False)),
        evade=bool(raw.get("b", False)),
        jump=bool(raw.get("a", False)),
        reload=bool(raw.get("x", False)),
        swap_mode=bool(raw.get("y", False)),
        sprint=float(raw.get("left_trigger", 0.0)) > 0.2,
        pause=bool(raw.get("menu", False)),
    )


class XboxSeriesController:
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
        buttons = int(gamepad.wButtons)
        return ControllerSnapshot(
            connected=True,
            left_x=_normalize_axis(int(gamepad.sThumbLX)),
            left_y=_normalize_axis(int(gamepad.sThumbLY)),
            right_x=_normalize_axis(int(gamepad.sThumbRX)),
            right_y=_normalize_axis(int(gamepad.sThumbRY)),
            left_trigger=_normalize_trigger(int(gamepad.bLeftTrigger)),
            right_trigger=_normalize_trigger(int(gamepad.bRightTrigger)),
            a=bool(buttons & XINPUT_GAMEPAD_A),
            b=bool(buttons & XINPUT_GAMEPAD_B),
            x=bool(buttons & XINPUT_GAMEPAD_X),
            y=bool(buttons & XINPUT_GAMEPAD_Y),
            left_stick_press=bool(buttons & XINPUT_GAMEPAD_LEFT_THUMB),
            right_stick_press=bool(buttons & XINPUT_GAMEPAD_RIGHT_THUMB),
            left_shoulder=bool(buttons & XINPUT_GAMEPAD_LEFT_SHOULDER),
            right_shoulder=bool(buttons & XINPUT_GAMEPAD_RIGHT_SHOULDER),
            menu=bool(buttons & XINPUT_GAMEPAD_START),
            view=bool(buttons & XINPUT_GAMEPAD_BACK),
        )

    def poll_frame(self) -> ControlFrame:
        return translate_raw_state(self.poll().to_dict())


XInputController = XboxSeriesController
