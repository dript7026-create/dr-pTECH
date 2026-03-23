# DirkOdds Android Client Package

## Contents

- `HANDOFF_NOTE.md`
- `CLIENT_EXEC_SUMMARY.md`
- `README.md`
- `VALIDATION_SUMMARY.json`
- `PACKAGE_MANIFEST.json`
- `artifacts/DirkOddsMobile-release.apk`
- `repo/urbden-android/README.md`

## Install

Use `adb install -r artifacts/DirkOddsMobile-release.apk` from this folder, or transfer the APK to an Android device and install it directly.

## Test Flow

1. Open the app.
2. Choose a fictional sport scenario.
3. Pick a prediction lane.
4. Launch the 3D match test.
5. Use `Pulse Pick`, `Set Shape`, and `Reflex Tap` while the live HUD updates.
6. Review whether the prediction held through the final synthetic result.

## Validation Scope

- Android release build compiled successfully.
- APK metadata verified as API 35 release output.
- Interactive mobile experience includes synthetic scenarios and abstract visuals only.

## Important Limits

- This package is a preview for testing and review.
- It does not use real sports identities or live regulated data.
- It is not a final licensed commercial deployment.
