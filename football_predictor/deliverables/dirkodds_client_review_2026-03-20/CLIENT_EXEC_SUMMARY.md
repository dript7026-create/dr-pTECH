# DirkOdds Executive Summary

DirkOdds is a multi-sport team-vs-team prediction application with a desktop GUI, pre-match feature engineering, model comparison, evolutionary hyperparameter search, and interactive playback views.

Current package scope:

- Football, baseball, and basketball prediction workflows
- Desktop GUI for training, loading, prediction, and visualization
- Exportable trained model bundles
- Probability, uncertainty, and entropy reporting
- Abstract 3D playback and live-render review paths
- Optional live-data, media, weather, player-stat, and consent scaffolding

What this package proves:

- The core training and prediction path passes focused automated validation.
- A fresh football bundle was trained from the included sample dataset.
- A sample fixture prediction is included as JSON for direct review.

What this package is not:

- Not a guarantee engine
- Not a wagering system
- Not a claim of 100% accuracy
- Not a biometric, psychiatric, or medical reconstruction system

Recommended client review path:

1. Review `artifacts/dirkodds_demo_prediction.json`.
2. Review `VALIDATION_SUMMARY.json`.
3. Launch the GUI with `launch_dirkodds_gui.ps1`.
4. Inspect the source package under `repo/` if technical review is needed.
