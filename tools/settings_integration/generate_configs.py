#!/usr/bin/env python3
"""Generate basic build/editor snippets from a VSCode settings.json.

This tool is intentionally small and extensible. It produces a minimal set of
files (CMakeLists.txt, Makefile, .vscode/tasks.json, requirements.txt) that
show how to integrate common graphics/audio libs and AI API deps.
"""
import argparse
import json
import os
from pathlib import Path

DEFAULT_TEMPLATES = Path(__file__).parent / 'templates'

LIB_MAPPINGS = {
    'qt': {
        'cmake': 'find_package(Qt6 REQUIRED COMPONENTS Widgets Core Gui)\n',
        'pkgconfig': 'Qt6',
        'notes': 'Use Qt6 or Qt5 depending on your project.'
    },
    'raylib': {
        'cmake': 'find_package(raylib REQUIRED)\n',
        'pkgconfig': 'raylib',
    },
    'sdl2': {
        'cmake': 'find_package(SDL2 REQUIRED)\n',
        'pkgconfig': 'sdl2',
    }
}

AI_DEPS = ['transformers', 'torch', 'openai', 'sentence-transformers']


def render_template(path: Path, **ctx):
    with open(path, 'r', encoding='utf-8') as f:
        tpl = f.read()
    # Use simple replacement to avoid conflicts with JSON/CMake braces
    for k, v in ctx.items():
        tpl = tpl.replace('{' + k + '}', str(v))
    return tpl


def ensure_outdir(outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print('Wrote', path)


def generate(settings_path: Path, outdir: Path):
    ensure_outdir(outdir)
    # load settings if possible
    settings = {}
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    except Exception:
        print('Warning: could not parse settings.json; proceeding with defaults')

    project_name = settings.get('name', 'project')

    # CMake
    cmake_tpl = DEFAULT_TEMPLATES / 'cmakelists.tpl'
    libs_cmake = []
    for key in ('qt', 'raylib', 'sdl2'):
        if key in settings.get('extensions', {}) or settings.get('use_' + key, False):
            libs_cmake.append(LIB_MAPPINGS[key]['cmake'])
    cmake_text = render_template(cmake_tpl, project_name=project_name, libs='\n'.join(libs_cmake))
    write(outdir / 'CMakeLists.txt', cmake_text)

    # Makefile
    make_tpl = DEFAULT_TEMPLATES / 'Makefile.tpl'
    make_text = render_template(make_tpl, project_name=project_name)
    write(outdir / 'Makefile', make_text)

    # VSCode tasks
    tasks_tpl = DEFAULT_TEMPLATES / 'tasks.tpl'
    tasks_text = render_template(tasks_tpl, project_name=project_name)
    write(outdir / '.vscode' / 'tasks.json', tasks_text)

    # requirements
    reqs = AI_DEPS
    reqs_text = render_template(DEFAULT_TEMPLATES / 'requirements.tpl', packages='\n'.join(reqs))
    write(outdir / 'requirements.txt', reqs_text)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--settings', default='settings.json', help='path to settings.json')
    p.add_argument('--outdir', default='out', help='output directory')
    args = p.parse_args()
    generate(Path(args.settings), Path(args.outdir))


if __name__ == '__main__':
    main()
