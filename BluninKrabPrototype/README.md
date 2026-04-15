# Blunin Krab Prototype

This is a standalone side-scrolling action-RPG/metroidvania prototype that uses the discovered Blunin, Krab Combat, latent boss, probe, relic, HUD, and background assets already in the workspace.

What is wired in:

- Blunin idle, walk, and full attack sheets as the playable character
- All five skull relic sprites as progression pickups
- All Krab Combat small sprite strips as enemy variants, including the inchworm-like set
- Ghost, probe, sludgelord, boop20xx, Ghost Maw, and both Libertykong silhouette assets
- All discovered background plates, including the three Blunin layers and the latent biome backgrounds
- Krab Combat heart and menu/play button icons for the HUD and title screen
- Krab Combat music and SFX for title, room traversal, combat, relic pickup, boss phase shift, and clear-state flourish
- Combat feedback polish: hit flashes, floating combat text, camera shake, and a two-phase Ghost Maw finish

Controls:

- A/D or Left/Right: move
- Space or Up: jump
- J or Z: melee attack
- K or X: probe pulse after the third relic
- Esc: quit

Run it from the workspace venv:

```powershell
python BluninKrabPrototype/prototype.py
```

Or use the bundled launcher:

```powershell
powershell -ExecutionPolicy Bypass -File BluninKrabPrototype/run_preview.ps1
```

Automated smoke test:

```powershell
$env:SDL_VIDEODRIVER = 'dummy'
python BluninKrabPrototype/prototype.py --smoke-test --frames 2400 --output-basename smoke_test_preview
```

Launcher-based smoke test:

```powershell
powershell -ExecutionPolicy Bypass -File BluninKrabPrototype/run_preview.ps1 -SmokeTest -Frames 2400 -OutputBasename smoke_test_preview
```

The smoke test runs on a deterministic fixed timestep and now has a validated clear-state route at 2400 frames. It writes a preview PNG plus a JSON summary into this folder.
The JSON includes the simulated frame count, visited rooms, clear-state flags, and the full loaded-asset manifest.

Local dependency pin for this slice:

```powershell
pip install -r BluninKrabPrototype/requirements.txt
```
