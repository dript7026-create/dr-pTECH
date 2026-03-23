# NeoWakeUP

NeoWakeUP is the dedicated home for the drIpTECH AI runtime stack.

Current modules:

- `neowakeup/qaijockey/` — migrated KaijuGaiden AI player with persistent genome learning.
- `neowakeup/relationships.py` — egosphere-inspired interpersonal state model.
- `neowakeup/planetary/` — recursive social simulation with explicit equation registry.
- `neowakeup/planetary/erpsequencer.py` — symbolic stress/intoxication perturbation sequencer over planetary mind state.
- `neowakeup/hub/` — Tkinter control hub for directive input, node-map viewing, and simulation control.
- `neowakeup/api_server.py` — local HTTP surface exposing planetary engine state and stepping.
- `Bango-Patoot/egoassurance/spectrumexprncs.py` — Bango-Patoot-specific EgoAssurance module.

Entry points:

- `run_qaijockey.py` — run the migrated KaijuGaiden AI from the NeoWakeUP directory.
- `run_planetary_mind.py` — run the planetary simulation with configurable directives.
- `run_erpsequencer.py` — generate an ERP-style perturbation report from stress, volatility, and intoxication factors.
- `run_control_hub.py` — launch the NeoWakeUP control hub.
- `run_engine_api.py` — expose the engines over local HTTP.
- `build_neowakeup_recraft_manifests.py` — regenerate the 600-credit and 300-credit GUI Recraft manifests.
- `run_neowakeup_recraft_pass.py` — execute a NeoWakeUP Recraft manifest once `RECRAFT_API_KEY` is available.
- `export_public_samples.py` — write sanitized sample state files for public distribution.
- `render_public_preview.py` — generate a static preview image for README / public repo use.

Examples:

```powershell
python .\NeoWakeUP\run_planetary_mind.py --model scientific --steps 20 --show-equations
python .\NeoWakeUP\run_erpsequencer.py --model mythic --steps 24 --intoxication 0.58
python .\NeoWakeUP\run_qaijockey.py --headless --max-frames 120 --no-record
python .\NeoWakeUP\run_qaijockey.py --profile generic --backend desktop --window-title VisualBoyAdvance-M --desktop-keymap "a=z,b=x,left=left,right=right,up=up,down=down,select=backspace,start=enter"
python .\NeoWakeUP\run_qaijockey.py --backend desktop --emulator C:\Users\rrcar\Documents\visualboyadvance\visualboyadvance-m.exe --rom .\KaijuGaiden\dist\kaijugaiden.gb --window-title VisualBoyAdvance-M --desktop-keymap "a=z,b=x,left=left,right=right,select=backspace,start=enter"
python .\NeoWakeUP\run_control_hub.py
python .\NeoWakeUP\run_engine_api.py --port 8765
python .\NeoWakeUP\build_neowakeup_recraft_manifests.py
python .\NeoWakeUP\run_neowakeup_recraft_pass.py .\NeoWakeUP\assets\recraft\neowakeup_gui_pass_600_manifest.json
python .\NeoWakeUP\export_public_samples.py
python .\NeoWakeUP\render_public_preview.py
```

Design constraints:

- The planetary system is an explicit simulation, not a claim of literal consciousness.
- Equation forms are fixed and inspectable so users can route inputs through deterministic logic.
- Interpersonal dynamics reuse the same lightweight modeling philosophy already present in `egosphere`.
- The Recraft manifests are prepared locally, but live paid generation still requires `RECRAFT_API_KEY` in the active shell.

QAIJockey emulator backends:

- `--backend pyboy` preserves the original direct PyBoy integration for GB ROMs and headless local testing.
- `--backend desktop` drives any visible Windows emulator window through generic client-area capture plus keyboard injection, so emulator support no longer requires a dedicated code path per emulator.
- The desktop backend accepts either `--emulator` to launch an emulator process or `--window-title` to attach to an already-running emulator window.
- `--desktop-keymap` maps QAIJockey buttons (`a`, `b`, `left`, `right`, `select`, `start`) onto the emulator's host keyboard bindings.

QAIJockey game profiles:

- `--profile kaijugaiden` keeps the original tuned analyzer and policy for the KaijuGaiden duel HUD.
- `--profile generic` uses a game-agnostic exploratory profile built from generic frame motion, centroids, and standard emulator buttons so QAIJockey can attach to unfamiliar games without adding core code.
- `--profile some.module.path` loads an external custom profile module if it exposes `PROFILE`, `build_profile()`, or `Profile`.
- The combination of `--backend desktop` plus `--profile generic` is the zero-adaptation path for arbitrary emulator games, while a custom profile upgrades that same bridge with game-specific state extraction and policy hints.

Public repo artifacts:

- `public_samples/` contains sanitized example state files.
- `public_preview/neowakeup_control_hub_preview.png` is a generated preview image suitable for documentation.

ERP sequencer notes:

- Sequencer events now carry coined alias families such as `erpsquible`, `erp skwible`, `erpsquerble`, and `swkeeble`.
- The control hub exposes ERP sliders for intoxication, recovery, and focus plus `ERP x12` and `ERP x24` actions.
- The local API exposes `GET /erpsequencer/aliases`, `GET /erpsequencer/latest`, and `POST /erpsequencer/run`.
