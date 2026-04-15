# dripwave

`dripwave` is a native Win32 `.swf` shell and SWF capability backend written in C.

Current scope:

- opens `.swf` files directly
- opens `.farim` packages and resolves the embedded `.swf` payload
- parses SWF stage width, stage height, version, frame rate, and frame count
- classifies SWFs by runtime profile: timeline-only, interactive timeline, AVM1, or AVM2
- keeps recognized `.swf` inputs loadable in compatibility mode even when metadata parsing is incomplete
- matches the shell client area to the SWF frame boundary on load
- supports tabbed navigation for multiple loaded files
- supports drag-and-drop loading onto the main window
- supports closing the active tab from the `Close Tab` button, `Ctrl+W`, or the tab-strip `x`
- persists per-title save states with current frame, volume, fit mode, and last known runtime path
- supports named save slots: `Resume`, `Checkpoint`, `Branch A`, and `Sandbox`
- automatically resumes a saved state when the same `.swf` or `.farim` source is reopened
- keeps a recent library for reopening prior `.swf` and `.farim` titles
- launches a companion authoring shell for prompt-driven game scaffolding, prefab authoring, asset queues, and code translation
- supports `--smoke` CLI validation for `.swf` and `.farim` inputs without using the GUI
- includes a togglable playback controller with:
  - skip to beginning
  - frame backward
  - central play/pause button
  - frame forward
  - skip to end
  - dead stop
  - volume slider

FARIM support follows the repo's current `farim 0.1` convention:

- `.farim` is treated as a ZIP container
- `farim_manifest.json` is read when present
- `entry_swf` is honored if present in the manifest
- otherwise the first embedded `.swf` entry is used

Portable shell behavior:

- `build\dripwave.exe` is a standalone native Win32 executable
- no installer is required
- `.farim` payloads are extracted to a temporary `.swf` only for the active session and cleaned up on exit
- the `Runtime...` button only asks for an external runtime when the active file actually needs one
- simple timeline inspection stays inside `dripwave`
- recognized but partially parsed SWFs are still admitted in compatibility mode so they can be handed to a projector instead of being rejected up front
- save-state files are stored under `%LOCALAPPDATA%\dripwave\states`
- recent entries are stored under `%LOCALAPPDATA%\dripwave\recent.ini`
- `build.ps1` copies supported runtimes from `runtime\` or `DRIPWAVE_BACKEND_SOURCE` into `build\`

Execution backend discovery:

- `DRIPWAVE_BACKEND` environment variable, if set to an executable path
- `ruffle_desktop.exe` next to `dripwave.exe`
- `flashplayer_32_sa.exe` next to `dripwave.exe`
- `flashplayer_sa.exe` next to `dripwave.exe`
- the last runtime path saved for a given title

Run fallback order:

- configured backend via `DRIPWAVE_BACKEND`
- colocated backend executable beside `dripwave.exe`
- Windows default `.swf` file association
- manual picker dialog for `ruffle_desktop.exe` or a standalone Flash player executable

Current limitation:

- this build now includes a native SWF capability backend that classifies runtime requirements and stops rejecting recognized SWF signatures when only partial parsing is available
- full Flash rendering and lossless ActionScript execution still require a real AVM/projector implementation; `dripwave` can now make that requirement explicit per file instead of treating every SWF the same way

## Build

From the workspace root:

```powershell
.\pocode\windows\dripwave\build.ps1
```

Output:

```text
pocode\windows\dripwave\build\dripwave.exe
```

## Usage

- Launch `dripwave.exe`
- Click `Open` to load a `.swf` or `.farim`
- You can also drag `.swf` and `.farim` files onto the window
- Use the recent-library combo and `Open Recent` to reopen prior titles
- Use the tabs to switch files
- Use `Close Tab`, `Ctrl+W`, or the `x` at the right edge of a tab to close the active file tab
- Use `Fit` to switch between `Contain`, `1:1`, and `Stretch`
- Use `Controls` to show or hide the playback controller
- Use the slot combo to switch between `Resume`, `Checkpoint`, `Branch A`, and `Sandbox`
- Use `Runtime...` to let `dripwave` decide whether the active file can stay in the native inspector path or should be launched in a detected runtime/backend; if no runtime is configured, `dripwave` will try the Windows file association and then let you pick an executable
- Use `Save State` to persist the current frame, volume, fit mode, and active runtime path for the loaded title
- Use `Load State` to resume that saved state manually; matching titles also auto-resume when reopened
- Use `Authoring...` to open the companion prompt-driven game-authoring shell

The stage canvas automatically sizes to the SWF frame bounds when a file is loaded.

## Authoring Shell

The companion authoring shell lives at `tools\dripwave_authoring.py` and is launched from the `Authoring...` button.

It can:

- scaffold a Flash-ready project under `projects\<slug>`
- store prefab metadata for actors, environment pieces, and triggers
- queue Recraft image jobs from plain-text asset prompts
- queue or run JumpClip sprite/video-style bundle generation for actor and video assets
- queue or run OpenAI TTS audio generation when `OPENAI_API_KEY` is available
- translate plain-text gameplay prompts into `src\GameScript.as`
- package a built `.swf` into `.farim`

Current authoring limitation:

- `dripwave` can scaffold SWF source and package FARIM immediately, but direct `.swf` compilation still depends on an external ActionScript compiler such as Apache Flex `mxmlc`

## Smoke Test Mode

To validate files without opening the GUI:

```powershell
.\pocode\windows\dripwave\build\dripwave.exe --smoke path\to\movie.swf path\to\package.farim
```

This prints `OK` or `FAIL` lines and exits nonzero if any input fails to load.

## Inspect Mode

To print the detected SWF runtime profile and backend requirement without opening the GUI:

```powershell
.\pocode\windows\dripwave\build\dripwave.exe --inspect path\to\movie.swf path\to\package.farim
```

## One-Command Validation

To rebuild `dripwave`, regenerate a valid sample `.swf`, package a matching `.farim`, and run smoke validation in one command:

```powershell
.\pocode\windows\dripwave\tools\smoke_pipeline.ps1
```

## FARIM Packaging Helper

You can create a simple `.farim` package from any `.swf` with:

```powershell
.venv\Scripts\python.exe .\pocode\windows\dripwave\tools\make_farim_from_swf.py path\to\movie.swf
```

This writes `movie.farim` next to the source `.swf` and includes a minimal `farim_manifest.json` with `entry_swf` set for `dripwave`.
