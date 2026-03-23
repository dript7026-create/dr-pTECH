# DirkOdds

DirkOdds is a team-vs-team sports predictor with a desktop GUI, pre-match feature engineering, model selection, evolutionary hyperparameter search, and explicit uncertainty reporting.

It is designed as a probabilistic decision-support tool. It does not promise perfect accuracy, guaranteed profit, or certainty about future results.

The live-data and simulation extensions in this repo are also bounded by real source availability. Football can sync configured football-data.org and TheSportsDB feeds into a local warehouse. Baseball and basketball can now also sync schedule data through sport-specific TheSportsDB adapters when you provide league ids for the selected sport, and playback now renders a sport-specific pitch, diamond, or court view.

## Stack

- Python
- pandas and numpy for ingestion and feature engineering
- scikit-learn for baseline and auto-selected models
- DEAP for genetic hyperparameter search
- PySide6 plus matplotlib for the desktop GUI
- Panda3D for the live full-team 3D match renderer

## Features

- CSV ingestion with normalization for common football, baseball, and basketball schema variants
- Leakage-free pre-match features built from prior form only
- Team form, rolling points, goals for/against, win rate, rest days, and experience features
- Automatic model comparison across logistic regression, random forest, and gradient boosting
- Evolutionary search for a tuned random forest
- GUI workflow for loading data, training, evolving, exporting, loading saved models, and plotting prediction profiles
- Manual upcoming-fixture prediction with confidence, uncertainty, and entropy output across football, baseball, and basketball
- Optional SQLite warehouse sync from configured football-data.org and sport-specific TheSportsDB sources
- Optional media/gossip signal adjustment from RSS feeds
- Optional weather-aware forecast adjustment using OpenWeather
- Physics-inspired 3D trajectory export for simulated shot events in upcoming fixtures
- Real-time 3D playback window with abstract avatars, user probability overrides, optional licensed numerical player-stat adjustments, and sport-specific football, baseball, and basketball surfaces
- Playback transport controls for play, restart, frame stepping, timeline scrubbing, and saved-session restoration
- A second live 3D renderer path with full-team abstract motion, arena geometry, crowd layers, scoreboard overlay, camera-follow playback, and physics-driven action states
- Abstract entity-state simulation for readiness, fatigue, hydration, sodium balance, morale, discipline, coach motivation, confusion, vision disruption, reaction delay, decision noise, locomotion integrity, and match incidents
- Explicit football, baseball, and basketball ruleset catalogs that enumerate legal phase states, control behaviors, support behaviors, defensive actions, scoring actions, recovery actions, and mistake states
- Spectator-focused cue scaffolding that emits attention targets, reflex windows, hotspot prompts, and pressure states into playback and live 3D rendering without requiring direct player control
- Source-to-simulation delta signatures and influence-network summaries for non-identifying entity derivation
- Transparent regulated-session scaffolding for consent gates, previous-game datastreams, user-presence prompts, and channel state
- Challenge cue mode that hides exact accuracy percentages in the UI while surfacing statistically correlated gameplay tells
- Consent-ingestion scaffolding for lineup and per-entity approval tracking, plus operator-facing playback summaries

## Expected CSV schema

Required columns:

- `home_team`
- `away_team`
- `home_score`
- `away_score`

Optional but recommended:

- `date`

The loader also accepts common aliases such as `HomeTeam`, `AwayTeam`, `FTHG`, and `FTAG`.

Optional column:

- `sport` with values such as `football`, `baseball`, or `basketball`

If you do not include a `sport` column, the desktop app and training CLI let you choose the sport explicitly.

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m football_predictor.main
```

## Train from the command line

```powershell
python -m football_predictor.train --input football_predictor/sample_data.csv --output football_predictor/dirkodds.joblib --sport football
```

Baseball example:

```powershell
python -m football_predictor.train --input baseball_history.csv --output baseball_dirkodds.joblib --sport baseball
```

Basketball example:

```powershell
python -m football_predictor.train --input basketball_history.csv --output basketball_dirkodds.joblib --sport basketball
```

With genetic search:

```powershell
python -m football_predictor.train --input football_predictor/sample_data.csv --output football_predictor/dirkodds_evolved.joblib --evolve --ngen 10 --pop-size 18
```

## Live sync and upcoming fixture prediction

Environment variables:

- `FOOTBALL_DATA_API_KEY` for football-data.org
- `THESPORTSDB_API_KEY` for TheSportsDB if you want something other than the default free tier key path
- `OPENWEATHER_API_KEY` for weather-aware adjustments when fixture coordinates are available

Example:

```powershell
python -m football_predictor.predict_live `
  --bundle football_predictor/dirkodds_evolved.joblib `
  --sport football `
  --db .pytest_cache/dirkodds_live.sqlite `
  --history-csv football_predictor/sample_data.csv `
  --football-data-competition PL `
  --thesportsdb-league-id 4328 `
  --season 2025-2026 `
  --date-from 2026-03-15 `
  --date-to 2026-03-22 `
  --rss-url https://feeds.bbci.co.uk/sport/football/rss.xml `
  --simulate-count 2000 `
  --output-json .pytest_cache/dirkodds_live_report.json
```

The generated report includes adjusted probabilities, uncertainty, weather/media context, and a set of 3D shot trajectories for the most likely simulated scoreline.

For baseball or basketball live sync, use a model trained for that sport, pass `--sport baseball` or `--sport basketball`, and provide `--thesportsdb-league-id` values for the relevant league ids.

## 3D playback

Open the playback window directly from the desktop GUI with the `3D Fixture Playback` button, or launch it from a saved report:

```powershell
python -m football_predictor.playback --report .pytest_cache/dirkodds_live_report.json
```

For the new live full-team renderer, either use the `Live 3D Match View` button in the desktop GUI or launch it from a report:

```powershell
python -m football_predictor.live_render --report .pytest_cache/dirkodds_live_report.json
```

The live renderer uses Panda3D and therefore needs a working Panda3D display pipe. On normal desktop setups that means an OpenGL-capable driver. Headless smoke validation can run with `--offscreen`, but a full interactive window still depends on local graphics support.

The original playback renderer uses abstract humanoid mannequins and trajectories only. The new live renderer expands that into a continuous full-team abstract scene with arena seating, animated crowd pulses, scoreboard overlays, multiple camera modes, and team movement around the ball. Player movement now comes from a sequential kinematic scene feed with capped speed, acceleration, steering, ball pursuit, control pressure, and action labels such as `set`, `run`, `sprint`, `press`, `control`, `guard`, and `shoot`, which the renderer maps into rig pose changes.

Both renderers remain non-identifying and do not render player likenesses, names, portraits, badges, or biometric recreations. If you have a licensed or personally created player-stats CSV, you can load it into the playback window to derive anonymous performance archetypes from numerical stats only.

The system does not infer genetics or claim to reconstruct a real athlete's body from public stats. If you need exact physical attributes, provide them explicitly in licensed or user-created data columns such as `height_in`, `weight_lb`, `height_cm`, `weight_kg`, or `body_fat_pct`.

The entity-state layer is also deliberately abstract. It synthesizes readiness, fatigue, hydration, sodium balance, cramp risk, injury pressure, morale, discipline, confusion, vision disruption, reaction delay, crowd disruption, and Ego-Sphere/godAI-inspired state vectors as gameplay-style simulation inputs. It is not a medical model, not psychiatric advice, and not a claim that the software can reproduce the real inner state of any identifiable athlete.

The sport ruleset registry now sits ahead of the live scene. Football, baseball, and basketball each expose explicit lists for phase states, role sequences, control actions, support actions, defensive actions, scoring actions, recovery actions, and mistake states. The live scene then chooses from those lists by combining possession context with locomotion integrity, hesitation, decision noise, perception drag, and balance, so the renderer is no longer limited to the earlier small hard-coded action vocabulary.

The latest playback and live-render pass also leans harder into a spectator-game feel instead of a direct-control game feel. Simulation now emits effect-driven event metadata such as phase state, primary action, pressure window, attention focus, reflex intensity, hotspot radius, and spectator prompt text. The Qt playback window surfaces those as a passive cue banner and field hotspot, while the Panda3D renderer uses them for a broadcast-style HUD, animated focus marker, and urgency-reactive camera framing.

To make the transformation legible, each team state now emits a source-stat signature, a simulated-state signature, a delta signature, and a small influence network showing which public-context variables pushed the in-app state. This is the right place to capture the difference between real-world public performance data and the app's non-identifying entity model.

Future ArtiSapien hooks can be attached later if you secure licensed player mappings and the relevant deployment-side approval inputs. The current codebase only emits disabled placeholders for that bridge.

The regulated-session scaffold is intentionally transparent. It can emit lineup-consent gates, previous-game datastream stubs, user-presence prompts, timing-dilation factors, and simulation-channel states for a future regulated interactive product, but it does not hide channels from the user, fabricate guaranteed accuracy bands, or implement wagering logic.

The desktop prediction workflow and playback window now support football, baseball, and basketball. Football still has the broadest upstream live-data support because football-data.org remains football-only, while baseball and basketball live sync currently rely on TheSportsDB league adapters.

You can also pass an optional consent CSV into the live prediction flow to scaffold lineup-approval ratios and per-entity approval registries. Those values appear in the exported report and the playback operator panel, but they remain scaffolding until you connect a real consent service.

For richer scaffolding, you can pass a JSON consent manifest with audit and expiry fields by using `--player-consent-manifest`.

Expected player-consent CSV columns:

- `team`
- `approved`

Recommended columns for fixture-level matching:

- `home_team`
- `away_team`
- `date`

Optional columns:

- `entity_id`
- `approval_scope`
- `approval_source`
- `approval_granted_at`
- `approval_expires_at`
- `audit_ref`
- `play_scope`
- `consent_version`

Playback session reports now persist `session_state` as well, so challenge-mode visibility, selected fixture, manual probability overrides, quality sliders, and playback speed can reopen exactly as last saved.

The playback window now also keeps a visible fixture/status strip, timeline clock, score label, and tabbed state/operator panels so interactive review is easier to follow while scrubbing or stepping through a render.

Challenge cue mode is available for non-monetary gameplay. In that mode, exact confidence-style percentages stay hidden in the user-facing UI and are replaced with qualitative cues such as `Soft Lean`, `Readable Lean`, `Strong Tell`, timing-window hints, and pressure/rhythm labels that still track the underlying model and simulation state.

Expected player-stats CSV columns:

- `team`
- `minutes`
- `goals`
- `assists`
- `shots_on_target`
- `key_passes`
- `tackles`
- `interceptions`
- `saves`

Optional licensed/user-supplied physical columns:

- `height_in` or `height_cm`
- `weight_lb` or `weight_kg`
- `body_fat_pct`

## Tests

```powershell
python -m pytest tests/test_model.py -q
```

## Notes on uncertainty

DirkOdds reports:

- `confidence`: the largest class probability
- `uncertainty`: `1 - confidence`
- `entropy`: normalized distribution spread across all three outcomes

Higher entropy means the model sees the match as harder to separate.

## Live-data credits

The live football and weather source credits are tracked in [THIRD_PARTY_CREDITS.md](c:/Users/rrcar/Documents/drIpTECH/THIRD_PARTY_CREDITS.md) and [tools/dependency_manifests/football_live_data_sources.json](c:/Users/rrcar/Documents/drIpTECH/tools/dependency_manifests/football_live_data_sources.json).

## Sample data

A small demo dataset is included at [football_predictor/sample_data.csv](c:/Users/rrcar/Documents/drIpTECH/football_predictor/sample_data.csv).
