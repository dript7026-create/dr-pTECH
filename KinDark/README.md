# Kin Dark

Kin Dark is a new drIpTECH production foundation for a three-protagonist comic-noir urban nightmare RPG: Moe, Yil, and Lou traverse one contiguous 3D city built from sprite-prefab actors and sprite-assembled environment geometry.

This folder does not falsely claim to contain a fully hand-authored 300-hour commercial game in one turn. It does contain a truthful production foundation built around the exact scope you asked for:

- a generated story book using a ScanTide-derived pressure model
- an exact-count graphics manifest with 109867 entries
- an exact-count audio manifest with 2037 entries including 200 two-minute loops
- runtime and controller contracts for the behind-the-back, right-stick-reticle, controller-first 3D lane

## Generated Outputs

- [generated/kin_dark_master_book.md](generated/kin_dark_master_book.md)
- [generated/kin_dark_story_summary.json](generated/kin_dark_story_summary.json)
- [generated/kin_dark_tutorial_slice.json](generated/kin_dark_tutorial_slice.json)
- [generated/kin_dark_asset_summary.json](generated/kin_dark_asset_summary.json)
- [generated/kin_dark_graphics_manifest.jsonl](generated/kin_dark_graphics_manifest.jsonl)
- [generated/kin_dark_audio_manifest.jsonl](generated/kin_dark_audio_manifest.jsonl)
- [generated/kin_dark_game_project.json](generated/kin_dark_game_project.json)
- [generated/kin_dark_game_project.drip3d.json](generated/kin_dark_game_project.drip3d.json)

## Docs

- [docs/KIN_DARK_GAME_BIBLE.md](docs/KIN_DARK_GAME_BIBLE.md)
- [docs/KIN_DARK_RUNTIME_AND_CONTROLLER_SPEC.md](docs/KIN_DARK_RUNTIME_AND_CONTROLLER_SPEC.md)
- [docs/KIN_DARK_TUTORIAL_SLICE.md](docs/KIN_DARK_TUTORIAL_SLICE.md)
- [docs/KIN_DARK_ASSET_PROGRAM_OVERVIEW.md](docs/KIN_DARK_ASSET_PROGRAM_OVERVIEW.md)

## Regenerate

Run:

```cmd
build_kindark_foundation.cmd
```

or:

```cmd
python tools/build_kindark_foundation.py
```
