import ctypes
import json
import math
import os
import subprocess
import sys
import threading
import time
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import messagebox
from urllib.parse import urlparse


if os.name != "nt":
    raise SystemExit("KrabSurf currently supports Windows only.")


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

VK_CONTROL = 0x11
VK_L = 0x4C
VK_F5 = 0x74
VK_TAB = 0x09
VK_LEFT = 0x25
VK_RIGHT = 0x27
VK_UP = 0x26
VK_DOWN = 0x28
VK_RETURN = 0x0D
VK_ESCAPE = 0x1B
VK_BROWSER_BACK = 0xA6

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_WHEEL = 0x0800
KEYEVENTF_KEYUP = 0x0002

SM_CXSCREEN = 0
SM_CYSCREEN = 1


user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


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
    _fields_ = [
        ("dwPacketNumber", ctypes.c_ulong),
        ("Gamepad", XINPUT_GAMEPAD),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("union", INPUT_UNION)]


def normalize_thumb(value: int, deadzone: int = 6000) -> float:
    if abs(value) < deadzone:
        return 0.0
    sign = -1.0 if value < 0 else 1.0
    magnitude = (abs(value) - deadzone) / (32767 - deadzone)
    return sign * max(0.0, min(1.0, magnitude))


def send_mouse(flags: int, data: int = 0, dx: int = 0, dy: int = 0) -> None:
    command = INPUT(
        type=INPUT_MOUSE,
        union=INPUT_UNION(mi=MOUSEINPUT(dx=dx, dy=dy, mouseData=data, dwFlags=flags, time=0, dwExtraInfo=None)),
    )
    user32.SendInput(1, ctypes.byref(command), ctypes.sizeof(INPUT))


def send_key(vk: int, keyup: bool = False) -> None:
    flags = KEYEVENTF_KEYUP if keyup else 0
    command = INPUT(
        type=INPUT_KEYBOARD,
        union=INPUT_UNION(ki=KEYBDINPUT(wVk=vk, wScan=0, dwFlags=flags, time=0, dwExtraInfo=None)),
    )
    user32.SendInput(1, ctypes.byref(command), ctypes.sizeof(INPUT))


def send_key_combo(keys) -> None:
    for vk in keys:
        send_key(vk, keyup=False)
    for vk in reversed(keys):
        send_key(vk, keyup=True)


def move_cursor(dx: float, dy: float) -> None:
    point = ctypes.wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(point))
    width = user32.GetSystemMetrics(SM_CXSCREEN)
    height = user32.GetSystemMetrics(SM_CYSCREEN)
    next_x = max(0, min(width - 1, int(point.x + dx)))
    next_y = max(0, min(height - 1, int(point.y + dy)))
    user32.SetCursorPos(next_x, next_y)


class XInputWrapper:
    def __init__(self) -> None:
        self.module = None
        self.get_state = None
        for dll_name in ("xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll"):
            try:
                module = ctypes.WinDLL(dll_name)
            except OSError:
                continue
            self.module = module
            self.get_state = module.XInputGetState
            self.get_state.argtypes = [ctypes.c_uint, ctypes.POINTER(XINPUT_STATE)]
            self.get_state.restype = ctypes.c_ulong
            break

    def read(self, index: int = 0):
        if not self.get_state:
            return None
        state = XINPUT_STATE()
        result = self.get_state(index, ctypes.byref(state))
        if result != 0:
            return None
        return state


@dataclass
class StoreEntry:
    store_id: str
    name: str
    url: str
    domains: list[str]


class BrowserLauncher:
    def __init__(self, allowed_domains: set[str]) -> None:
        self.allowed_domains = allowed_domains
        self.edge_path = self._find_edge()
        self.chrome_path = self._find_chrome()

    def _find_edge(self):
        candidates = [
            Path(os.environ.get("ProgramFiles(x86)", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
            Path(os.environ.get("ProgramFiles", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        ]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        return None

    def _find_chrome(self):
        candidates = [
            Path(os.environ.get("ProgramFiles", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
            Path(os.environ.get("ProgramFiles(x86)", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        ]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        return None

    def is_allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        if not host:
            return False
        if host in self.allowed_domains:
            return True
        return any(host.endswith("." + domain) for domain in self.allowed_domains)

    def launch(self, url: str) -> tuple[bool, str]:
        if not self.is_allowed(url):
            return False, "Blocked: domain is outside the KrabSurf store allowlist."
        if self.edge_path:
            subprocess.Popen([self.edge_path, f"--app={url}", "--disable-features=msHubApps"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True, "Opened in Edge app mode."
        if self.chrome_path:
            subprocess.Popen([self.chrome_path, f"--app={url}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True, "Opened in Chrome app mode."
        return False, "No supported browser runtime was found. Install Edge or Chrome for store launch mode."


class ControllerNavigator(threading.Thread):
    def __init__(self, on_menu, on_selection_move, on_toggle_nav, on_status) -> None:
        super().__init__(daemon=True)
        self.xinput = XInputWrapper()
        self.on_menu = on_menu
        self.on_selection_move = on_selection_move
        self.on_toggle_nav = on_toggle_nav
        self.on_status = on_status
        self.running = True
        self.desktop_nav_enabled = True
        self.last_buttons = 0
        self.last_dpad_time = 0.0
        self.last_shoulder_time = 0.0
        self.last_face_time = 0.0
        self.last_scroll_time = 0.0

    def stop(self) -> None:
        self.running = False

    def _button_pressed(self, buttons: int, mask: int) -> bool:
        return (buttons & mask) and not (self.last_buttons & mask)

    def run(self) -> None:
        if not self.xinput.get_state:
            self.on_status("No XInput runtime detected. KrabSurf UI is available, but controller navigation is offline.")
            return
        self.on_status("Xbox Series controller bridge online.")
        while self.running:
            state = self.xinput.read(0)
            if state is None:
                time.sleep(0.05)
                continue
            gamepad = state.Gamepad
            buttons = int(gamepad.wButtons)
            now = time.time()

            left_x = normalize_thumb(int(gamepad.sThumbLX))
            left_y = normalize_thumb(int(gamepad.sThumbLY))
            right_y = normalize_thumb(int(gamepad.sThumbRY))

            if self.desktop_nav_enabled and (left_x != 0.0 or left_y != 0.0):
                speed = 18.0 + float(gamepad.bLeftTrigger) * 0.15
                move_cursor(left_x * speed, -left_y * speed)

            if self.desktop_nav_enabled and abs(right_y) > 0.10 and (now - self.last_scroll_time) > 0.02:
                wheel_delta = int(right_y * 180)
                if wheel_delta != 0:
                    send_mouse(MOUSEEVENTF_WHEEL, data=wheel_delta)
                    self.last_scroll_time = now

            if self._button_pressed(buttons, XINPUT_GAMEPAD_A):
                send_mouse(MOUSEEVENTF_LEFTDOWN)
                send_mouse(MOUSEEVENTF_LEFTUP)
            if self._button_pressed(buttons, XINPUT_GAMEPAD_B):
                send_mouse(MOUSEEVENTF_RIGHTDOWN)
                send_mouse(MOUSEEVENTF_RIGHTUP)
            if self._button_pressed(buttons, XINPUT_GAMEPAD_X) and (now - self.last_face_time) > 0.12:
                send_key(VK_F5)
                send_key(VK_F5, keyup=True)
                self.last_face_time = now
            if self._button_pressed(buttons, XINPUT_GAMEPAD_Y) and (now - self.last_face_time) > 0.12:
                send_key_combo([VK_CONTROL, VK_L])
                self.last_face_time = now
            if self._button_pressed(buttons, XINPUT_GAMEPAD_LEFT_SHOULDER) and (now - self.last_shoulder_time) > 0.12:
                send_key_combo([VK_CONTROL, 0x10, VK_TAB])
                self.last_shoulder_time = now
            if self._button_pressed(buttons, XINPUT_GAMEPAD_RIGHT_SHOULDER) and (now - self.last_shoulder_time) > 0.12:
                send_key_combo([VK_CONTROL, VK_TAB])
                self.last_shoulder_time = now
            if self._button_pressed(buttons, XINPUT_GAMEPAD_BACK):
                self.desktop_nav_enabled = not self.desktop_nav_enabled
                self.on_toggle_nav(self.desktop_nav_enabled)
            if self._button_pressed(buttons, XINPUT_GAMEPAD_START):
                self.on_menu()

            if (now - self.last_dpad_time) > 0.16:
                if buttons & XINPUT_GAMEPAD_DPAD_UP:
                    self.on_selection_move(-1)
                    self.last_dpad_time = now
                elif buttons & XINPUT_GAMEPAD_DPAD_DOWN:
                    self.on_selection_move(1)
                    self.last_dpad_time = now
                elif buttons & XINPUT_GAMEPAD_DPAD_LEFT:
                    send_key(VK_LEFT)
                    send_key(VK_LEFT, keyup=True)
                    self.last_dpad_time = now
                elif buttons & XINPUT_GAMEPAD_DPAD_RIGHT:
                    send_key(VK_RIGHT)
                    send_key(VK_RIGHT, keyup=True)
                    self.last_dpad_time = now

            self.last_buttons = buttons
            time.sleep(0.01)


class KrabSurfApp:
    def __init__(self) -> None:
        self.base_dir = Path(__file__).resolve().parent
        self.stores = self._load_stores()
        self.allowed_domains = {domain for store in self.stores for domain in store.domains}
        self.browser = BrowserLauncher(self.allowed_domains)
        self.selected_index = 0
        self.root = tk.Tk()
        self.root.title("KrabSurf")
        self.root.geometry("1120x760")
        self.root.configure(bg="#09131c")
        self.root.minsize(920, 640)
        self.store_buttons = []

        self.status_var = tk.StringVar(value="KrabSurf booted.")
        self.nav_var = tk.StringVar(value="Desktop Nav: ON")
        self.store_var = tk.StringVar(value="")

        self._build_ui()
        self._refresh_selection()
        self.root.bind("<Up>", lambda _event: self.move_selection(-1))
        self.root.bind("<Down>", lambda _event: self.move_selection(1))
        self.root.bind("<Return>", lambda _event: self.open_selected_store())
        self.root.bind("<Escape>", lambda _event: self.root.destroy())

        self.controller = ControllerNavigator(
            on_menu=self._schedule_open_selected,
            on_selection_move=self._schedule_move_selection,
            on_toggle_nav=self._schedule_nav_toggle,
            on_status=self._schedule_status,
        )
        self.controller.start()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _load_stores(self) -> list[StoreEntry]:
        config_path = self.base_dir / "stores.json"
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        return [
            StoreEntry(
                store_id=item["id"],
                name=item["name"],
                url=item["url"],
                domains=list(item["domains"]),
            )
            for item in payload
        ]

    def _build_ui(self) -> None:
        header = tk.Frame(self.root, bg="#0e2230", padx=24, pady=20)
        header.pack(fill="x")

        title = tk.Label(header, text="KrabSurf", font=("Bahnschrift", 28, "bold"), fg="#f1f7fb", bg="#0e2230")
        title.pack(anchor="w")
        subtitle = tk.Label(
            header,
            text="Controller-first store browser shell for approved web game storefronts.",
            font=("Bahnschrift", 12),
            fg="#a8c0d1",
            bg="#0e2230",
        )
        subtitle.pack(anchor="w", pady=(4, 0))

        body = tk.Frame(self.root, bg="#09131c", padx=24, pady=20)
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg="#09131c")
        left.pack(side="left", fill="both", expand=True)
        right = tk.Frame(body, bg="#112433", width=320, padx=18, pady=18)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        grid_title = tk.Label(left, text="Approved Stores", font=("Bahnschrift", 18, "bold"), fg="#eef5fa", bg="#09131c")
        grid_title.pack(anchor="w", pady=(0, 14))

        grid = tk.Frame(left, bg="#09131c")
        grid.pack(fill="both", expand=True)
        for index, store in enumerate(self.stores):
            button = tk.Button(
                grid,
                text=store.name,
                font=("Bahnschrift", 16, "bold"),
                padx=18,
                pady=18,
                relief="flat",
                bd=0,
                command=lambda idx=index: self.set_selection(idx),
                activebackground="#21506d",
                activeforeground="#ffffff",
                cursor="hand2",
            )
            row = index // 2
            col = index % 2
            button.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)
            grid.grid_columnconfigure(col, weight=1)
            self.store_buttons.append(button)
        for row in range(math.ceil(len(self.stores) / 2)):
            grid.grid_rowconfigure(row, weight=1)

        detail_title = tk.Label(right, text="Controller Map", font=("Bahnschrift", 18, "bold"), fg="#f7fbfd", bg="#112433")
        detail_title.pack(anchor="w")
        detail_copy = [
            "Left Stick  Cursor",
            "Right Stick  Scroll",
            "A  Left Click",
            "B  Right Click / Back",
            "X  Refresh",
            "Y  Focus Address",
            "LB / RB  Cycle Tabs",
            "D-Pad  Move KrabSurf Selection",
            "View  Toggle Desktop Nav",
            "Menu  Open Selected Store",
        ]
        for line in detail_copy:
            label = tk.Label(right, text=line, font=("Consolas", 11), fg="#c7d9e4", bg="#112433", justify="left")
            label.pack(anchor="w", pady=2)

        tk.Label(right, text="", bg="#112433").pack(pady=6)

        selected_title = tk.Label(right, text="Selection", font=("Bahnschrift", 16, "bold"), fg="#f7fbfd", bg="#112433")
        selected_title.pack(anchor="w")
        selected_label = tk.Label(right, textvariable=self.store_var, font=("Bahnschrift", 13), fg="#8be0ff", bg="#112433", wraplength=260, justify="left")
        selected_label.pack(anchor="w", pady=(6, 12))

        launch_button = tk.Button(
            right,
            text="Open Store",
            command=self.open_selected_store,
            font=("Bahnschrift", 14, "bold"),
            padx=12,
            pady=12,
            relief="flat",
            bd=0,
            bg="#168aad",
            fg="#ffffff",
            activebackground="#1b9ec6",
            activeforeground="#ffffff",
            cursor="hand2",
        )
        launch_button.pack(fill="x", pady=(0, 18))

        footer = tk.Frame(self.root, bg="#0b1822", padx=24, pady=14)
        footer.pack(fill="x")
        nav_label = tk.Label(footer, textvariable=self.nav_var, font=("Bahnschrift", 11, "bold"), fg="#9dd7ef", bg="#0b1822")
        nav_label.pack(side="left")
        status_label = tk.Label(footer, textvariable=self.status_var, font=("Bahnschrift", 11), fg="#dce8ef", bg="#0b1822")
        status_label.pack(side="right")

    def _refresh_selection(self) -> None:
        for index, button in enumerate(self.store_buttons):
            if index == self.selected_index:
                button.configure(bg="#1d5f87", fg="#ffffff")
            else:
                button.configure(bg="#163042", fg="#d5e7f1")
        selected = self.stores[self.selected_index]
        self.store_var.set(f"{selected.name}\n{selected.url}")

    def set_selection(self, index: int) -> None:
        self.selected_index = max(0, min(len(self.stores) - 1, index))
        self._refresh_selection()
        self.status_var.set(f"Selected {self.stores[self.selected_index].name}.")

    def move_selection(self, delta: int) -> None:
        self.set_selection((self.selected_index + delta) % len(self.stores))

    def open_selected_store(self) -> None:
        selected = self.stores[self.selected_index]
        ok, detail = self.browser.launch(selected.url)
        self.status_var.set(detail)
        if not ok:
            messagebox.showwarning("KrabSurf", detail)

    def _schedule_open_selected(self) -> None:
        self.root.after(0, self.open_selected_store)

    def _schedule_move_selection(self, delta: int) -> None:
        self.root.after(0, lambda: self.move_selection(delta))

    def _schedule_nav_toggle(self, enabled: bool) -> None:
        self.root.after(0, lambda: self._update_nav(enabled))

    def _schedule_status(self, message: str) -> None:
        self.root.after(0, lambda: self.status_var.set(message))

    def _update_nav(self, enabled: bool) -> None:
        self.nav_var.set(f"Desktop Nav: {'ON' if enabled else 'OFF'}")
        self.status_var.set("Desktop navigation enabled." if enabled else "Desktop navigation paused.")

    def _on_close(self) -> None:
        self.controller.stop()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    app = KrabSurfApp()
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())