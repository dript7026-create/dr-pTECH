from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "kaijugaiden.c"
JOCKEY = ROOT / "qaijockey" / "jockey.py"
HOST_GRAPHICAL = ROOT / "host_graphical.py"


def expect(pattern: str, text: str, label: str, failures: list[str]) -> None:
    if re.search(pattern, text, re.MULTILINE) is None:
        failures.append(label)


def extract_int(pattern: str, text: str) -> int:
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        raise ValueError(pattern)
    return int(match.group(1))


def main() -> int:
    source_text = SOURCE.read_text(encoding="utf-8")
    jockey_text = JOCKEY.read_text(encoding="utf-8")
    host_graphical_text = HOST_GRAPHICAL.read_text(encoding="utf-8")
    failures: list[str] = []

    for name, value in {
        "BTN_UP": "0x40",
        "BTN_DOWN": "0x80",
        "BTN_LEFT": "0x20",
        "BTN_RIGHT": "0x10",
        "BTN_A": "0x01",
        "BTN_B": "0x02",
        "BTN_START": "0x08",
        "BTN_SELECT": "0x04",
    }.items():
        expect(rf"#\s*define {name}\s+{value}", source_text, f"missing host/GB mapping for {name}", failures)

    for name, value in {
        "BTN_UP": "KEY_UP",
        "BTN_DOWN": "KEY_DOWN",
        "BTN_LEFT": "KEY_LEFT",
        "BTN_RIGHT": "KEY_RIGHT",
        "BTN_A": "KEY_A",
        "BTN_B": "KEY_B",
        "BTN_START": "KEY_START",
        "BTN_SELECT": "KEY_SELECT",
    }.items():
        expect(rf"#\s*define {name}\s+{value}", source_text, f"missing GBA mapping for {name}", failures)

    expect(r"SDL_SCANCODE_Z[^\n]*BTN_A", source_text, "host attack mapping missing", failures)
    expect(r"SDL_SCANCODE_X[^\n]*BTN_B", source_text, "host dodge mapping missing", failures)
    expect(r"SDL_SCANCODE_A\s*\]\s*\)\s*_joy_cur \|= BTN_LEFT", source_text, "host left alias missing", failures)
    expect(r"SDL_SCANCODE_D\s*\]\s*\)\s*_joy_cur \|= BTN_RIGHT", source_text, "host right alias missing", failures)
    expect(r"SDL_SCANCODE_RETURN.*BTN_START", source_text, "host start mapping missing", failures)
    expect(r"SDL_SCANCODE_RSHIFT.*BTN_SELECT", source_text, "host select mapping missing", failures)

    expect(r"static inline u16 plat_input_mask\(void\)", source_text, "input mask helper missing", failures)
    expect(r"static inline u16 plat_pressed_mask\(void\)", source_text, "pressed mask helper missing", failures)
    expect(r"#define INPUT_BUFFER_FRAMES\s+5", source_text, "input buffer constant missing", failures)
    expect(r"u8\s+attack_buffer;", source_text, "attack buffer field missing", failures)
    expect(r"u8\s+dodge_buffer;", source_text, "dodge buffer field missing", failures)
    expect(r"input_capture_frame\(\);", source_text, "per-frame input capture missing", failures)
    expect(r"if \(gs\.input_pressed_mask & BTN_A\) gs\.attack_buffer = INPUT_BUFFER_FRAMES;", source_text, "attack input buffering missing", failures)
    expect(r"if \(gs\.input_pressed_mask & BTN_B\) gs\.dodge_buffer = INPUT_BUFFER_FRAMES;", source_text, "dodge input buffering missing", failures)
    expect(r"if \(gs\.dodge_buffer > 0 && gs\.hit_stun == 0 && gs\.attack_timer == 0\)", source_text, "buffered dodge execution missing", failures)
    expect(r"while \(edge_mask != 0\)", source_text, "input edge tracking loop missing", failures)
    expect(r"left_active = lx < -dead or gp\.get\('dpad_left'\)", host_graphical_text, "host controller left movement mapping missing", failures)
    expect(r"right_active = lx > dead or gp\.get\('dpad_right'\)", host_graphical_text, "host controller right movement mapping missing", failures)
    expect(r"up_active = ly < -dead or gp\.get\('dpad_up'\)", host_graphical_text, "host controller up movement mapping missing", failures)
    expect(r"down_active = ly > dead or gp\.get\('dpad_down'\)", host_graphical_text, "host controller down movement mapping missing", failures)
    expect(r"if gp\.get\('a'\) and not prev\.get\('a'\):\s+if self\.state == 'playing':\s+self\.on_attack\(\)", host_graphical_text, "host controller A mapping missing", failures)
    expect(r"if gp\.get\('b'\) and not prev\.get\('b'\):\s+if self\.state == 'playing':\s+self\._dodge\(\)", host_graphical_text, "host controller B mapping missing", failures)
    expect(r"if gp\.get\('x'\) and not prev\.get\('x'\):\s+if self\.state == 'playing':\s+self\.on_attack\(\)", host_graphical_text, "host controller X alias missing", failures)
    expect(r"if gp\.get\('start'\) and not prev\.get\('start'\):\s+if self\.state == 'title':\s+self\.on_start\(\)\s+else:\s+self\.on_pause\(\)", host_graphical_text, "host controller start mapping missing", failures)
    expect(r"'dpad_up': bool\(buttons & 0x0001\)", host_graphical_text, "host XInput dpad up parse missing", failures)
    expect(r"'dpad_down': bool\(buttons & 0x0002\)", host_graphical_text, "host XInput dpad down parse missing", failures)
    expect(r"'dpad_left': bool\(buttons & 0x0004\)", host_graphical_text, "host XInput dpad left parse missing", failures)
    expect(r"'dpad_right': bool\(buttons & 0x0008\)", host_graphical_text, "host XInput dpad right parse missing", failures)

    expect(r'ACTION_BUTTONS\s*=\s*\["a",\s*"b",\s*"left",\s*"right",\s*"select",\s*None\]', jockey_text, "QAIJockey action/button contract mismatch", failures)
    expect(r'ACTION_LABELS\s*=\s*\["ATTACK",\s*"DODGE",\s*"LEFT",\s*"RIGHT",\s*"NANO",\s*"WAIT"\]', jockey_text, "QAIJockey action labels mismatch", failures)

    skip_hold = extract_int(r"#define SKIP_HOLD_FRAMES\s+(\d+)", source_text)
    cinematic_hold = extract_int(r"CINEMATIC_B_HOLD\s*=\s*(\d+)", jockey_text)
    if cinematic_hold < skip_hold:
        failures.append("QAIJockey cinematic hold is below the runtime skip threshold")

    if failures:
        print("KaijuGaiden input contract verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("KaijuGaiden input contract verified:")
    print("- GB, GBA, and host button maps present")
    print("- Per-frame input tracking and buffered A/B combat controls present")
    print("- Host graphical controller bridge maps A/B/X/Start and d-pad plus stick movement consistently")
    print("- QAIJockey action bindings align with runtime controls")
    print(f"- Cinematic skip margin verified: runtime={skip_hold}, rider={cinematic_hold}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())