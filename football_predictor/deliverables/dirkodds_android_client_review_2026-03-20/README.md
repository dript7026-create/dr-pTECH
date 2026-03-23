# DirkOdds Android Client Review Package

## Contents

- `HANDOFF_NOTE.md`: fastest review entry point
- `CLIENT_EXEC_SUMMARY.md`: client-facing Android summary
- `README.md`: package guide
- `VALIDATION_SUMMARY.json`: build and APK verification snapshot
- `PACKAGE_MANIFEST.json`: package inventory
- `install_to_android.ps1`: local install helper
- `artifacts/dirkodds_mobile_release.apk`: installable Android release build
- `repo/android_app/`: curated Android source subset
- `repo/dirkodds_reference/`: DirkOdds reference README and progress notes

## Install

From this package folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\install_to_android.ps1
```

This helper uses the workspace Android SDK `adb.exe` path. If no device is connected, it prints the exact package path to install manually.

## Interaction Review Flow

1. Open the app.
2. Choose a fictional scenario from the match deck.
3. Select a prediction lane.
4. Launch the 3D prediction test.
5. Use `Pulse Pick`, `Set Shape`, and `Reflex Tap` during live playback.
6. Review whether the final synthetic outcome matched the chosen prediction lane.

## Guardrails

- No real teams, leagues, players, or likenesses are packaged.
- Scenario names, venues, colors, and motion are synthetic and abstract.
- This build is for review and testing, not final public deployment.
