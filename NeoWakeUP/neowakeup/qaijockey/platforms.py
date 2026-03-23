from __future__ import annotations

import ctypes
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from PIL import Image, ImageGrab


DMG_FRAME_SIZE = (160, 144)

DEFAULT_DESKTOP_KEYMAP = {
    "a": "z",
    "b": "x",
    "left": "left",
    "right": "right",
    "up": "up",
    "down": "down",
    "select": "backspace",
    "start": "enter",
}

VK_CODES = {
    "backspace": 0x08,
    "tab": 0x09,
    "enter": 0x0D,
    "shift": 0x10,
    "ctrl": 0x11,
    "alt": 0x12,
    "pause": 0x13,
    "capslock": 0x14,
    "esc": 0x1B,
    "space": 0x20,
    "pageup": 0x21,
    "pagedown": 0x22,
    "end": 0x23,
    "home": 0x24,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
    "insert": 0x2D,
    "delete": 0x2E,
    "0": 0x30,
    "1": 0x31,
    "2": 0x32,
    "3": 0x33,
    "4": 0x34,
    "5": 0x35,
    "6": 0x36,
    "7": 0x37,
    "8": 0x38,
    "9": 0x39,
    "a": 0x41,
    "b": 0x42,
    "c": 0x43,
    "d": 0x44,
    "e": 0x45,
    "f": 0x46,
    "g": 0x47,
    "h": 0x48,
    "i": 0x49,
    "j": 0x4A,
    "k": 0x4B,
    "l": 0x4C,
    "m": 0x4D,
    "n": 0x4E,
    "o": 0x4F,
    "p": 0x50,
    "q": 0x51,
    "r": 0x52,
    "s": 0x53,
    "t": 0x54,
    "u": 0x55,
    "v": 0x56,
    "w": 0x57,
    "x": 0x58,
    "y": 0x59,
    "z": 0x5A,
    "numpad0": 0x60,
    "numpad1": 0x61,
    "numpad2": 0x62,
    "numpad3": 0x63,
    "numpad4": 0x64,
    "numpad5": 0x65,
    "numpad6": 0x66,
    "numpad7": 0x67,
    "numpad8": 0x68,
    "numpad9": 0x69,
    "f1": 0x70,
    "f2": 0x71,
    "f3": 0x72,
    "f4": 0x73,
    "f5": 0x74,
    "f6": 0x75,
    "f7": 0x76,
    "f8": 0x77,
    "f9": 0x78,
    "f10": 0x79,
    "f11": 0x7A,
    "f12": 0x7B,
}


class EmulatorSession:
    def press(self, btn: str) -> None:
        raise NotImplementedError

    def release(self, btn: str) -> None:
        raise NotImplementedError

    def step(self) -> bool:
        raise NotImplementedError

    def capture_frame(self) -> Image.Image:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError


class PyBoySession(EmulatorSession):
    def __init__(self, rom_path: Path, window: str, speed: int):
        from pyboy import PyBoy

        self._pyboy = PyBoy(str(rom_path), window=window)
        self._pyboy.set_emulation_speed(speed)

    def press(self, btn: str) -> None:
        try:
            self._pyboy.button_press(btn)
        except Exception:
            pass

    def release(self, btn: str) -> None:
        try:
            self._pyboy.button_release(btn)
        except Exception:
            pass

    def step(self) -> bool:
        return bool(self._pyboy.tick())

    def capture_frame(self) -> Image.Image:
        return self._pyboy.screen.image

    def close(self) -> None:
        self._pyboy.stop()


@dataclass
class WindowRect:
    left: int
    top: int
    right: int
    bottom: int


class WindowsWindowController:
    def __init__(self) -> None:
        if ctypes.sizeof(ctypes.c_void_p) == 0:
            raise RuntimeError("ctypes is unavailable")
        self.user32 = ctypes.windll.user32

        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            ]

        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

        self.RECT = RECT
        self.POINT = POINT

    def _enum_windows(self, predicate: Callable[[int, str], bool]) -> Optional[int]:
        matches: list[int] = []

        @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        def callback(hwnd, _lparam):
            if not self.user32.IsWindowVisible(hwnd):
                return True
            length = self.user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            buffer = ctypes.create_unicode_buffer(length + 1)
            self.user32.GetWindowTextW(hwnd, buffer, length + 1)
            title = buffer.value.strip()
            if title and predicate(int(hwnd), title):
                matches.append(int(hwnd))
                return False
            return True

        self.user32.EnumWindows(callback, 0)
        return matches[0] if matches else None

    def find_window(self, title_substring: Optional[str] = None, process_id: Optional[int] = None) -> Optional[int]:
        title_match = title_substring.lower() if title_substring else None

        def predicate(hwnd: int, title: str) -> bool:
            if process_id is not None:
                found_pid = ctypes.c_ulong()
                self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(found_pid))
                if int(found_pid.value) != int(process_id):
                    return False
            if title_match is not None and title_match not in title.lower():
                return False
            return True

        return self._enum_windows(predicate)

    def wait_for_window(self, title_substring: Optional[str], process_id: Optional[int], timeout_seconds: float = 20.0) -> int:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            hwnd = self.find_window(title_substring=title_substring, process_id=process_id)
            if hwnd is not None:
                return hwnd
            time.sleep(0.2)
        needle = title_substring or f"pid={process_id}"
        raise RuntimeError(f"Timed out waiting for emulator window matching {needle}")

    def client_rect(self, hwnd: int) -> WindowRect:
        rect = self.RECT()
        if not self.user32.GetClientRect(hwnd, ctypes.byref(rect)):
            raise RuntimeError("GetClientRect failed")
        tl = self.POINT(rect.left, rect.top)
        br = self.POINT(rect.right, rect.bottom)
        if not self.user32.ClientToScreen(hwnd, ctypes.byref(tl)):
            raise RuntimeError("ClientToScreen failed for top-left")
        if not self.user32.ClientToScreen(hwnd, ctypes.byref(br)):
            raise RuntimeError("ClientToScreen failed for bottom-right")
        return WindowRect(tl.x, tl.y, br.x, br.y)

    def focus(self, hwnd: int) -> None:
        self.user32.ShowWindow(hwnd, 5)
        self.user32.SetForegroundWindow(hwnd)


def _normalize_key_name(name: str) -> str:
    return name.strip().lower().replace("return", "enter")


def parse_keymap(keymap_text: Optional[str]) -> dict[str, str]:
    keymap = dict(DEFAULT_DESKTOP_KEYMAP)
    if not keymap_text:
        return keymap
    for part in keymap_text.split(","):
        piece = part.strip()
        if not piece:
            continue
        if "=" not in piece:
            raise ValueError(f"Invalid key mapping '{piece}'. Expected button=key")
        button, host_key = piece.split("=", 1)
        button = button.strip().lower()
        host_key = _normalize_key_name(host_key)
        if button not in DEFAULT_DESKTOP_KEYMAP:
            raise ValueError(f"Unsupported QAIJockey button '{button}' in keymap")
        if host_key not in VK_CODES:
            raise ValueError(f"Unsupported host key '{host_key}' in keymap")
        keymap[button] = host_key
    return keymap


class DesktopWindowSession(EmulatorSession):
    def __init__(
        self,
        rom_path: Path,
        emulator_path: Optional[Path],
        window_title: Optional[str],
        keymap_text: Optional[str],
        poll_hz: float,
        launch_args: Optional[str],
        focus_window: bool,
    ) -> None:
        if ctypes.sizeof(ctypes.c_void_p) <= 0:
            raise RuntimeError("Desktop window backend requires ctypes support")
        if not hasattr(ctypes, "windll"):
            raise RuntimeError("Desktop window backend is currently implemented for Windows only")
        if poll_hz <= 0.0:
            raise ValueError("poll_hz must be greater than zero")

        self.rom_path = rom_path
        self.focus_window_each_step = focus_window
        self.poll_interval = 1.0 / poll_hz
        self.keymap = parse_keymap(keymap_text)
        self._controller = WindowsWindowController()
        self._process: Optional[subprocess.Popen] = None
        self._hwnd: Optional[int] = None

        process_id = None
        if emulator_path is not None:
            if not emulator_path.exists():
                raise RuntimeError(f"Emulator not found: {emulator_path}")
            args = [str(emulator_path), str(rom_path)]
            if launch_args:
                args.extend([piece for piece in launch_args.split(" ") if piece])
            self._process = subprocess.Popen(args)
            process_id = self._process.pid

        self._hwnd = self._controller.wait_for_window(window_title, process_id, timeout_seconds=25.0)
        self._controller.focus(self._hwnd)

    def _send_key(self, btn: str, is_keyup: bool) -> None:
        mapped = self.keymap.get(btn)
        if mapped is None:
            return
        vk = VK_CODES[mapped]
        flags = 0x0002 if is_keyup else 0x0000
        ctypes.windll.user32.keybd_event(vk, 0, flags, 0)

    def press(self, btn: str) -> None:
        self._send_key(btn, is_keyup=False)

    def release(self, btn: str) -> None:
        self._send_key(btn, is_keyup=True)

    def step(self) -> bool:
        if self._process is not None and self._process.poll() is not None:
            return False
        if self._hwnd is None:
            return False
        if self.focus_window_each_step:
            self._controller.focus(self._hwnd)
        time.sleep(self.poll_interval)
        return True

    def capture_frame(self) -> Image.Image:
        if self._hwnd is None:
            raise RuntimeError("Desktop emulator window is not available")
        bbox = self._controller.client_rect(self._hwnd)
        if bbox.right <= bbox.left or bbox.bottom <= bbox.top:
            raise RuntimeError("Desktop emulator client area is invalid")
        image = ImageGrab.grab(bbox=(bbox.left, bbox.top, bbox.right, bbox.bottom), all_screens=True)
        return image.convert("RGB").resize(DMG_FRAME_SIZE, Image.Resampling.NEAREST)

    def close(self) -> None:
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()


def create_session(
    backend: str,
    rom_path: Path,
    headless: bool,
    speed: int,
    emulator_path: Optional[str],
    window_title: Optional[str],
    desktop_keymap: Optional[str],
    desktop_poll_hz: float,
    desktop_launch_args: Optional[str],
    desktop_focus_window: bool,
) -> EmulatorSession:
    if backend == "pyboy":
        window = "null" if headless else "SDL2"
        return PyBoySession(rom_path=rom_path, window=window, speed=speed)
    if backend == "desktop":
        if headless:
            raise RuntimeError("--headless is not supported with the desktop backend")
        return DesktopWindowSession(
            rom_path=rom_path,
            emulator_path=Path(emulator_path).resolve() if emulator_path else None,
            window_title=window_title,
            keymap_text=desktop_keymap,
            poll_hz=desktop_poll_hz,
            launch_args=desktop_launch_args,
            focus_window=desktop_focus_window,
        )
    raise RuntimeError(f"Unsupported backend: {backend}")