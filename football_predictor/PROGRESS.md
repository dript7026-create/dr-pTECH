# DirkOdds Progress Note

Date: 2026-03-16
Status: Multi-sport predictor and playback baseline is stable; GUI interactivity polish is now underway.

## Completed

- Football, baseball, and basketball training and prediction now share one normalized probability/report shape.
- Live warehouse sync persists sport identity and supports sport-specific TheSportsDB adapters for baseball and basketball.
- 3D playback renders a football pitch, baseball diamond, and basketball court with abstract avatars and event trajectories.
- Consent/session scaffolding, operator summaries, and challenge-cue presentation remain active in exported reports and playback.
- Validation is green on the broad predictor suite, and offscreen Qt playback smoke has already succeeded for all three sports.

## Current Focus

- Polish the desktop interaction flow so sport selection, fixture prediction, and playback launch state stay legible.
- Improve playback transport controls so scrubbing, stepping, restarting, and session restoration feel deliberate.
- Re-verify the 3D playback render path with actual widget interaction, not only helper-level tests.

## Next Likely Follow-Ons

- Add richer baseball- and basketball-specific upstream feeds beyond TheSportsDB league adapters.
- Deepen sport-authentic event semantics and camera/presentation details in playback.
- Add broader GUI/playback smoke coverage for interactive regression detection.