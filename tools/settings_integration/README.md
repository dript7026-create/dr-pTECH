Generate build and editor snippets from a centralized VS Code settings file.

Usage:

- Python 3.8+ is required.
- Run: `python generate_configs.py --settings /path/to/settings.json --outdir ./out`

What it produces (basic, extensible):
- `CMakeLists.txt` with find_package/pkg-config stubs for Qt, raylib, SDL2/3
- `Makefile` sample using `gcc`/`clang` with flags for libraries
- `.vscode/tasks.json` with build tasks (cmake, make, gcc)
- `requirements.txt` listing common Python deps for AI APIs (transformers, openai)

This is intentionally minimal and meant as a starting point. Add more templates
or expand mappings in `generate_configs.py`.
