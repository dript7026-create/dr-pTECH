# DirkOdds Handoff Note

This package is the client-ready review deliverable for DirkOdds.

Start here:

1. Read `CLIENT_EXEC_SUMMARY.md` for the product-level overview.
2. Read `README.md` for package contents and launch steps.
3. Inspect `VALIDATION_SUMMARY.json` for the validated baseline.
4. Use `launch_dirkodds_gui.ps1` if you want to open the desktop app from this package.

Core facts:

- Product: DirkOdds
- Project source: `repo/football_predictor/`
- Trained demo model: `artifacts/dirkodds_client_bundle.joblib`
- Example output: `artifacts/dirkodds_demo_prediction.json`

Important limits:

- DirkOdds is a probabilistic decision-support tool.
- It does not guarantee accuracy, outcomes, or profit.
- Live-data features depend on external providers and operator-supplied credentials.
