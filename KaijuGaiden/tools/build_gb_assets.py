#!/usr/bin/env python3
"""
build_gb_assets.py — Batch convert all KaijuGaiden GB Recraft PNGs to C headers.

Run from the KaijuGaiden/ root directory:
  python tools/build_gb_assets.py

Reads from:   assets/source/gb/*.png (preferred, repo-native)
              assets/raw/gb/*.png or assets/png/gb/*.png (fallbacks)
Writes to:    assets/gb/  (relative to KaijuGaiden/)

Produces these header files (matching kaijugaiden.c array names exactly):
  assets/gb/bg_tiles_generated.h     — tile_ground_l/r, water_a/b, cliff_a/b, sky_a/b
                                       tile_splash[8][16], tile_title[12][16]
  assets/gb/spr_rei_generated.h      — spr_rei_idle_data[6][16]
                                       spr_rei_run_data[6][16]
                                       spr_rei_attack_data[6][16]
  assets/gb/spr_boss_generated.h     — spr_boss_p1_data[8][16]
                                       spr_boss_p2_data[8][16]
                                       spr_boss_p3_data[8][16]
  assets/gb/spr_minion_generated.h   — spr_minion_data[4][16]
  assets/gb/spr_fx_generated.h       — spr_fx_hit_data[2][16], spr_fx_nano_data[2][16]
  assets/gb/spr_cinematic_generated.h— spr_cinematic_a[12][16], spr_cinematic_b[12][16]
  assets/gb/hud_tiles_generated.h    — tile_hp_seg[16] (1 tile for HP segment)
"""

import os
import sys
import subprocess

# ── paths ──────────────────────────────────────────────────────────────────── #
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR    = os.path.dirname(SCRIPT_DIR)
PREFERRED_ASSET_SRC = os.path.join(ROOT_DIR, "assets", "source", "gb")
ASSET_SRC_CANDIDATES = [
    os.environ.get("KAIJUGAIDEN_ASSET_SRC"),
    PREFERRED_ASSET_SRC,
    os.path.join(ROOT_DIR, "assets", "raw", "gb"),
    os.path.join(ROOT_DIR, "assets", "png", "gb"),
    r"C:\Users\rrcar\KaijuGaiden\assets\gb",
]
ASSET_OUT   = os.path.join(ROOT_DIR, "assets", "gb")
CONVERTER   = os.path.join(SCRIPT_DIR, "gb_convert.py")
PYTHON      = sys.executable

EXPECTED_SOURCE_FILES = [
    "tile_ground.png",
    "tile_water.png",
    "tile_cliff.png",
    "tile_sky.png",
    "bg_splash_driptech.png",
    "bg_title_logo.png",
    "spr_rei_idle.png",
    "spr_rei_run.png",
    "spr_rei_attack.png",
    "spr_boss_leviathan_p1.png",
    "spr_boss_leviathan_p2.png",
    "spr_boss_leviathan_p3.png",
    "spr_minion_crablet.png",
    "spr_fx_hit_spark.png",
    "spr_fx_nanocell_orb.png",
    "spr_cinematic_rei_large.png",
    "spr_cinematic_storm_kaiju.png",
    "hud_hp_segment.png",
    "hud_boss_hp_bar.png",
]


def count_source_files(asset_src: str) -> int:
    return sum(1 for name in EXPECTED_SOURCE_FILES if os.path.exists(os.path.join(asset_src, name)))


def resolve_asset_src() -> tuple[str, int]:
    resolved = []
    for candidate in ASSET_SRC_CANDIDATES:
        if candidate and os.path.isdir(candidate):
            resolved.append((candidate, count_source_files(candidate)))
    if not resolved:
        return PREFERRED_ASSET_SRC, 0
    preferred = [item for item in resolved if os.path.abspath(item[0]) == os.path.abspath(PREFERRED_ASSET_SRC)]
    if preferred and preferred[0][1] > 0:
        return preferred[0]
    best = max(resolved, key=lambda item: item[1])
    if best[1] > 0:
        return best
    if preferred:
        return preferred[0]
    return resolved[0]


def report_source_status(asset_src: str, available_count: int):
    missing = [name for name in EXPECTED_SOURCE_FILES if not os.path.exists(os.path.join(asset_src, name))]
    preferred = os.path.abspath(asset_src) == os.path.abspath(PREFERRED_ASSET_SRC)
    if preferred:
        print(f"Using repo source art: {asset_src}")
    else:
        print(f"Using fallback source art: {asset_src}")
        print(f"Preferred source art path: {PREFERRED_ASSET_SRC}")
    print(f"Available source files: {available_count}/{len(EXPECTED_SOURCE_FILES)}")
    if missing and available_count > 0:
        print("Missing source files:")
        for name in missing:
            print(f"  - {name}")


ASSET_SRC, SOURCE_FILE_COUNT = resolve_asset_src()
report_source_status(ASSET_SRC, SOURCE_FILE_COUNT)

if SOURCE_FILE_COUNT == 0:
    print("No source PNGs found in repo-native or fallback asset paths.")
    print("Preserving existing generated headers in assets/gb and exiting cleanly.")
    sys.exit(0)

os.makedirs(ASSET_OUT, exist_ok=True)


def src(name: str) -> str:
    return os.path.join(ASSET_SRC, name)


def out(name: str) -> str:
    return os.path.join(ASSET_OUT, name)


def convert(png: str, tiles: str, name: str, header: str, center: bool = True,
            flat: bool = False, append: bool = False) -> bool:
    """
    Run gb_convert.py for a single PNG.
    If append=True, dumps raw array text and appends to an existing .h rather
    than overwriting it (used to pack multiple assets into one file).
    For simplicity here we generate to a temp file and merge in the caller.
    Returns True on success.
    """
    cmd = [PYTHON, CONVERTER,
           src(png),
           "--tiles", tiles,
           "--name",  name,
           "--out",   header]
    if center:
        cmd.append("--center")
    if flat:
        cmd.append("--flat")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FAIL  {png}  →  {result.stderr.strip()}")
        return False
    print(result.stdout.strip())
    return True


def merge_headers(output_path: str, *input_paths: str, banner: str = ""):
    """Merge multiple single-array .h files into one combined header."""
    with open(output_path, 'w', encoding='utf-8') as out_f:
        out_f.write('/* Generated by build_gb_assets.py from assets/source/gb where available. Edit source PNGs, not this header. */\n')
        out_f.write('#pragma once\n')
        out_f.write('#include <stdint.h>\n\n')
        if banner:
            out_f.write(f'/* {banner} */\n\n')
        for path in input_paths:
            if not os.path.exists(path):
                out_f.write(f'/* MISSING: {os.path.basename(path)} */\n')
                continue
            with open(path, encoding='utf-8') as in_f:
                lines = in_f.readlines()
            # Skip the boilerplate header lines (pragma once, stdint, etc.)
            skip = {'/* Generated', '#pragma', '#include <stdint', '\n'}
            for line in lines:
                if any(line.startswith(s) for s in skip) and len(line) < 60:
                    continue
                out_f.write(line)
            out_f.write('\n')
    print(f'Merged → {output_path}')


TMPDIR = os.path.join(ASSET_OUT, "_tmp")
os.makedirs(TMPDIR, exist_ok=True)


def tmp(name: str) -> str:
    return os.path.join(TMPDIR, name)


# ═══════════════════════════════════════════════════════════════════════════ #
# bg_tiles_generated.h
# ═══════════════════════════════════════════════════════════════════════════ #
print("\n── Background tiles ──────────────────────────────────────────────")
print(f"Using asset source: {ASSET_SRC}")

# tile_ground_l and tile_ground_r from tile_ground.png (2×1 grid)
# We generate them together as a 2-element array then split.
# Simpler: generate as [2][16] array called tile_ground_lr, then manually
# alias the two entries in the combined header.
convert("tile_ground.png",  "2x1", "tile_ground_lr",   tmp("tile_ground.h"),  center=True)
convert("tile_water.png",   "2x1", "tile_water_ab",    tmp("tile_water.h"),   center=True)
convert("tile_cliff.png",   "2x1", "tile_cliff_ab",    tmp("tile_cliff.h"),   center=True)
convert("tile_sky.png",     "2x1", "tile_sky_ab",      tmp("tile_sky.h"),     center=True)
convert("bg_splash_driptech.png", "4x2", "tile_splash",    tmp("tile_splash.h"),  center=True)
convert("bg_title_logo.png",      "4x3", "tile_title",     tmp("tile_title.h"),   center=True)

# Combine into bg_tiles_generated.h (with aliases)
BG_HDR = out("bg_tiles_generated.h")
with open(BG_HDR, 'w', encoding='utf-8') as f:
    f.write('/* Generated by build_gb_assets.py from assets/source/gb where available. Edit source PNGs, not this header. */\n')
    f.write('#pragma once\n')
    f.write('#include <stdint.h>\n\n')

    for src_name, hdr in [
        ("tile_ground.h",  "tile_ground_lr"),
        ("tile_water.h",   "tile_water_ab"),
        ("tile_cliff.h",   "tile_cliff_ab"),
        ("tile_sky.h",     "tile_sky_ab"),
        ("tile_splash.h",  "tile_splash"),
        ("tile_title.h",   "tile_title"),
    ]:
        p = tmp(src_name)
        if os.path.exists(p):
            with open(p, encoding='utf-8') as in_f:
                for line in in_f:
                    if line.startswith(('/* Gen', '#pragma', '#include <std')):
                        continue
                    f.write(line)
            f.write('\n')

    # Convenience aliases so kaijugaiden.c can use the original names
    f.write('/* Per-tile aliases for kaijugaiden.c compatibility */\n')
    f.write('#define tile_ground_l  (tile_ground_lr[0])\n')
    f.write('#define tile_ground_r  (tile_ground_lr[1])\n')
    f.write('#define tile_water_a   (tile_water_ab[0])\n')
    f.write('#define tile_water_b   (tile_water_ab[1])\n')
    f.write('#define tile_cliff_a   (tile_cliff_ab[0])\n')
    f.write('#define tile_cliff_b   (tile_cliff_ab[1])\n')
    f.write('#define tile_sky_a     (tile_sky_ab[0])\n')
    f.write('#define tile_sky_b     (tile_sky_ab[1])\n')

print(f'Wrote → {BG_HDR}')


# ═══════════════════════════════════════════════════════════════════════════ #
# spr_rei_generated.h
# ═══════════════════════════════════════════════════════════════════════════ #
print("\n── Rei sprites ───────────────────────────────────────────────────")
convert("spr_rei_idle.png",   "2x3", "spr_rei_idle_data",   tmp("rei_idle.h"),   center=True)
convert("spr_rei_run.png",    "2x3", "spr_rei_run_data",    tmp("rei_run.h"),    center=True)
convert("spr_rei_attack.png", "2x3", "spr_rei_attack_data", tmp("rei_attack.h"), center=True)
merge_headers(out("spr_rei_generated.h"),
              tmp("rei_idle.h"),
              tmp("rei_run.h"),
              tmp("rei_attack.h"),
              banner="Rei sprite tiles — idle / run / attack (each 2×3 = 6 tiles)")


# ═══════════════════════════════════════════════════════════════════════════ #
# spr_boss_generated.h
# ═══════════════════════════════════════════════════════════════════════════ #
print("\n── Boss sprites ──────────────────────────────────────────────────")
convert("spr_boss_leviathan_p1.png", "4x2", "spr_boss_p1_data", tmp("boss_p1.h"), center=True)
convert("spr_boss_leviathan_p2.png", "4x2", "spr_boss_p2_data", tmp("boss_p2.h"), center=True)
convert("spr_boss_leviathan_p3.png", "4x2", "spr_boss_p3_data", tmp("boss_p3.h"), center=True)
merge_headers(out("spr_boss_generated.h"),
              tmp("boss_p1.h"),
              tmp("boss_p2.h"),
              tmp("boss_p3.h"),
              banner="Harbor Leviathan boss sprites — phase 1/2/3 (each 4×2 = 8 tiles)")


# ═══════════════════════════════════════════════════════════════════════════ #
# spr_minion_generated.h
# ═══════════════════════════════════════════════════════════════════════════ #
print("\n── Minion sprite ─────────────────────────────────────────────────")
convert("spr_minion_crablet.png", "2x2", "spr_minion_data", tmp("minion.h"), center=True)
merge_headers(out("spr_minion_generated.h"),
              tmp("minion.h"),
              banner="Crablet minion sprite (2×2 = 4 tiles)")


# ═══════════════════════════════════════════════════════════════════════════ #
# spr_fx_generated.h
# ═══════════════════════════════════════════════════════════════════════════ #
print("\n── FX sprites ────────────────────────────────────────────────────")
convert("spr_fx_hit_spark.png",    "2x1", "spr_fx_hit_data",  tmp("fx_hit.h"),  center=True)
convert("spr_fx_nanocell_orb.png", "2x1", "spr_fx_nano_data", tmp("fx_nano.h"), center=True)
merge_headers(out("spr_fx_generated.h"),
              tmp("fx_hit.h"),
              tmp("fx_nano.h"),
              banner="FX tiles — hit spark / nanocell orb (each 2×1 = 2 tiles)")


# ═══════════════════════════════════════════════════════════════════════════ #
# spr_cinematic_generated.h
# ═══════════════════════════════════════════════════════════════════════════ #
print("\n── Cinematic sprites ─────────────────────────────────────────────")
convert("spr_cinematic_rei_large.png",    "4x3", "spr_cinematic_a", tmp("cine_a.h"), center=True)
convert("spr_cinematic_storm_kaiju.png",  "4x3", "spr_cinematic_b", tmp("cine_b.h"), center=True)
merge_headers(out("spr_cinematic_generated.h"),
              tmp("cine_a.h"),
              tmp("cine_b.h"),
              banner="Intro cinematic sprites — Rei large / Storm Kaiju (each 4×3 = 12 tiles)")


# ═══════════════════════════════════════════════════════════════════════════ #
# hud_tiles_generated.h
# ═══════════════════════════════════════════════════════════════════════════ #
print("\n── HUD tiles ─────────────────────────────────────────────────────")
convert("hud_hp_segment.png",  "1x1", "tile_hp_seg",       tmp("hud_hp.h"),   center=True)
convert("hud_boss_hp_bar.png", "6x1", "tile_boss_hp_bar",  tmp("hud_boss.h"), center=True)
merge_headers(out("hud_tiles_generated.h"),
              tmp("hud_hp.h"),
              tmp("hud_boss.h"),
              banner="HUD tiles — player HP segment (1×1) and boss HP bar (6×1)")


# ─── Summary ─────────────────────────────────────────────────────────────── #
print(f"""
Done.  Generated headers in {ASSET_OUT}:
  bg_tiles_generated.h
  spr_rei_generated.h
  spr_boss_generated.h
  spr_minion_generated.h
  spr_fx_generated.h
  spr_cinematic_generated.h
  hud_tiles_generated.h

Include these in kaijugaiden.c in the ASSET DATA section.
""")
