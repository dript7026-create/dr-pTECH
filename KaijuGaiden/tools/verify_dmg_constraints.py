from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "kaijugaiden.c"
ROM = ROOT / "kaijugaiden.gb"
ROM_LIMIT_BYTES = 32 * 1024


def expect(condition: bool, label: str, failures: list[str]) -> None:
    if not condition:
        failures.append(label)


def extract_int(pattern: str, text: str) -> int:
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        raise ValueError(pattern)
    return int(match.group(1))


def main() -> int:
    source_text = SOURCE.read_text(encoding="utf-8")
    failures: list[str] = []

    bkg_cols = extract_int(r"#define BKG_COLS\s+(\d+)", source_text)
    bkg_rows = extract_int(r"#define BKG_ROWS\s+(\d+)", source_text)
    bkg_tiles = extract_int(r"#define BKG_TILE_COUNT\s+(\d+)", source_text)
    minion_max = extract_int(r"#define MINION_MAX\s+(\d+)", source_text)
    player_slots = 6
    minion_slots = minion_max * 4
    boss_slots = 8
    fx_slots = 4
    total_sprite_slots = player_slots + minion_slots + boss_slots + fx_slots
    sprite_tile_end = extract_int(r"#define SPR_CINEMATIC_B\s+(\d+)", source_text) + 12

    expect(bkg_cols == 20, f"unexpected BKG_COLS: {bkg_cols}", failures)
    expect(bkg_rows == 18, f"unexpected BKG_ROWS: {bkg_rows}", failures)
    expect(bkg_tiles <= 256, f"background tile budget exceeded: {bkg_tiles}", failures)
    expect(total_sprite_slots <= 40, f"sprite slot budget exceeded: {total_sprite_slots}", failures)
    expect(sprite_tile_end <= 128, f"sprite tile budget exceeded: {sprite_tile_end}", failures)
    expect("static void bg_draw_beach_water_only(void)" in source_text, "water-only redraw optimization missing", failures)
    expect("else if ((gs.anim_tick % WATER_REDRAW_PERIOD) == 0) bg_draw_beach_water_only();" in source_text,
           "combat background redraw is not using the water-only fast path", failures)

    if ROM.exists():
        rom_size = ROM.stat().st_size
        expect(rom_size <= ROM_LIMIT_BYTES, f"ROM size {rom_size} exceeds {ROM_LIMIT_BYTES}", failures)
    else:
        rom_size = -1
        failures.append("kaijugaiden.gb not found; build the GB ROM before running the DMG audit")

    if failures:
        print("KaijuGaiden DMG constraint verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("KaijuGaiden DMG constraint verification passed:")
    print(f"- Background grid: {bkg_cols}x{bkg_rows}")
    print(f"- Background tiles: {bkg_tiles}/256")
    print(f"- Sprite slots reserved at peak: {total_sprite_slots}/40")
    print(f"- Sprite tile span used: {sprite_tile_end}/128")
    print(f"- ROM size: {rom_size}/{ROM_LIMIT_BYTES} bytes")
    print("- Combat path uses the lower-cost water-only redraw between camera layout shifts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())