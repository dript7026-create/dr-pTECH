TommyBeta Capture Workflow

Artifacts
- `tommybeta_autoplay.gba`: autoplay-enabled GBA ROM build.
- `tommybeta_100_percent_run_log.json`: structured 100% completion route summary.
- `tommybeta_100_percent_run_log.txt`: human-readable fight-by-fight summary.
- `tommybeta_100_percent_run.avi`: real-time VisualBoyAdvance-M window capture.
- `capture_session_log.txt`: capture session metadata.
- `capture_ffmpeg.out.log` and `capture_ffmpeg.err.log`: ffmpeg process logs.

Build
1. Run `./build.ps1 -Target gba-autoplay` from `tommybeta/`.
2. This regenerates assets and builds `tommybeta_autoplay.gba` with `-DTOMMYBETA_AUTOPLAY`.

Run Log
1. Run `C:/Users/rrcar/Documents/drIpTECH/.venv/Scripts/python.exe tommybeta/capture/generate_autoplay_run_log.py` from the workspace root.
2. This writes both JSON and text summaries for the deterministic 100% route.

Capture
1. Run `tommybeta/capture/capture_autoplay_run.ps1`.
2. The script launches VisualBoyAdvance-M with `tommybeta_autoplay.gba`.
3. It waits until VBA-M exposes a non-empty live window title.
4. It starts ffmpeg using gdigrab against that exact title.
5. It records the emulator window to AVI for the configured duration.
6. It stops VBA-M and writes the session log.

Notes
- The capture is graphical video capture of the emulator window. Audio is not currently captured.
- The ROM itself performs the AI completion route in autoplay mode; no external key injection is required during capture.
- The route is deterministic and matched to the simulator log produced by `generate_autoplay_run_log.py`.