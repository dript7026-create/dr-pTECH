"""
Small pipeline runner: Generate images via manifest and run Blender addon headless to auto-model.

Usage:
  - Set `RECRAFT_API_KEY` env var.
  - Ensure either `recraft_gen` binary (built from recraft_generation_streamline.c) exists in this folder, or the python helper `../tommygoomba/recraft_generate.py` is available.
  - (Optional) Set `BLENDER_BIN` env var to your Blender executable path to run headless modelling.

This script is conservative: it will print the Blender command if `BLENDER_BIN` is not set.
"""
import os
import sys
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
MANIFEST = HERE / 'manifest_example.json'
OUT_DIR = HERE / 'assets'
OUT_DIR.mkdir(parents=True, exist_ok=True)

def run_recraft_manifest(concurrency=2, enforce_palette=False, palette='gameboy4', dry_run=False):
    # prefer batch runner if present
    batch = HERE / 'batch_run_manifest.py'
    if batch.exists():
        cmd = [sys.executable, str(batch), '--manifest', str(MANIFEST), '--concurrency', str(concurrency)]
        if dry_run:
            cmd.append('--dry-run')
        if enforce_palette:
            cmd.extend(['--enforce-palette', '--palette', palette])
        print('Running batch manifest runner:', ' '.join(cmd))
        return subprocess.run(cmd).returncode

    # prefer compiled binary if no batch runner
    bin_path = HERE / 'recraft_gen'
    if os.name == 'nt':
        bin_path = bin_path.with_suffix('.exe')
    if bin_path.exists():
        cmd = [str(bin_path), '--manifest', str(MANIFEST)]
        print('Running compiled recraft client:', ' '.join(cmd))
        return subprocess.run(cmd).returncode
    # fallback to python helper in repo
    py_helper = HERE.parent.parent / 'tommygoomba' / 'recraft_generate.py'
    if py_helper.exists():
        cmd = [sys.executable, str(py_helper), '--dry-run']
        print('Compiled client not found; showing dry-run of Python helper:', ' '.join(cmd))
        return subprocess.run(cmd).returncode
    print('No recraft client found. Build recraft_gen or add tommygoomba/recraft_generate.py')
    return 2

def run_blender_on_image(image_path, out_blend=None):
    blender = os.environ.get('BLENDER_BIN')
    script = f"import bpy; bpy.ops.wm.open_mainfile(filepath=''); bpy.ops.recraft.import_and_model(\"{image_path}\", \"{out_blend or ''}\")"
    if blender:
        cmd = [blender, '--background', '--python-expr', script]
        print('Launching Blender headless:', ' '.join(cmd))
        return subprocess.run(cmd).returncode
    else:
        print('\nBLENDER_BIN not set. To run headless, set BLENDER_BIN to your Blender executable and rerun.')
        print('Example command:')
        print('BLENDER_BIN=blender', "blender --background --python-expr \"import bpy; bpy.ops.recraft.import_and_model('assets/tommy_sprite.png','recraft_out.blend')\"")
        return 0

if __name__ == '__main__':
    # defaults: 2 workers, enforce GameBoy palette on outputs
    rc = run_recraft_manifest(concurrency=2, enforce_palette=False, palette='gameboy4', dry_run=False)
    if rc != 0:
        print('Recraft manifest step returned', rc)
        sys.exit(rc)
    # demo: run blender on first asset
    demo_img = OUT_DIR / 'tommy_sprite.png'
    if demo_img.exists():
        run_blender_on_image(str(demo_img), str(OUT_DIR / 'recraft_out.blend'))
    else:
        print('Demo image not present at', demo_img)
    print('Pipeline finished (or skipped Blender run).')
