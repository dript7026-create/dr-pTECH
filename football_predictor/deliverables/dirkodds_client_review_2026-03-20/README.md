# DirkOdds Client Review Package

## Contents

- `HANDOFF_NOTE.md`: fastest entry point
- `CLIENT_EXEC_SUMMARY.md`: client-facing product summary
- `VALIDATION_SUMMARY.json`: current validation and training snapshot
- `launch_dirkodds_gui.ps1`: package-local GUI launcher
- `artifacts/dirkodds_client_bundle.joblib`: trained football demo bundle
- `artifacts/dirkodds_demo_prediction.json`: sample prediction output
- `artifacts/sample_data.csv`: sample training dataset
- `repo/`: curated source, test, requirements, and credit files

## Launch

From this package folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\launch_dirkodds_gui.ps1
```

The launcher creates a package-local virtual environment under `repo/.venv` if needed, installs requirements, and starts the desktop app.

## Validation Baseline

- Focused automated model tests passed.
- Fresh football demo bundle trained successfully.
- Example prediction artifact generated successfully.

## Notes

- This package is review-ready, not a store/distribution build.
- Some optional live-data features require network access and API credentials.
- The included bundle and demo prediction are based on the packaged sample dataset.
