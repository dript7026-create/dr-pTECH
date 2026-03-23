# DoENGINE Progress

Date: 2026-03-13

## D-drive backup migration and workspace dedication pass

- Established a dedicated `DoENGINE/` workspace subtree in the main repository root.
- Migrated the recovered `D:\doengine-backup` snapshot into the normalized `packages/core/src/`, `packages/encryption/src/`, `packages/telemetry/src/`, `docs/philosophy/`, `docs/metadata/`, `docs/migration/`, and `ops/backup/` layout.
- Preserved the original recovery context as source artifacts in `docs/migration/source-readme.md` and `docs/migration/source-backup-log.txt`.
- Added `docs/migration/migration-map.md` to document the old-to-new directory and file mapping.
- Added workspace manifests `package.json` and `tsconfig.json` so the TypeScript subtree has a clean project root.
- Rewrote active source paths so the core engine now imports from the normalized package layout.
- Replaced hard-coded OneDrive backup paths in telemetry with workspace-relative resolution plus optional `DOENGINE_BACKUP_ROOT` override support.
- Reworked the backup script to mirror the project tree into `ops/backup/primary`, `secondary`, and `tertiary` instead of flattening every file into a single folder.
- Added and normalized workspace documentation at `README.md` and `.github/copilot-instructions.md`.
- Validated the migrated TypeScript files in-place: no editor errors were reported for the core, encryption, or telemetry modules.

## Open gaps after this pass

- No package manager install or TypeScript compile has been run yet inside `DoENGINE/`.
- The encryption and hardware/session key generation remain placeholders.
- Shared trace typings now exist, but the new contract layer has not yet been broken into published package entrypoints.
- Philosophy and metadata docs are migrated but not yet rewritten into a final consolidated architecture spec.

## First package reintegration pass

- Added `packages/shared/src/contracts.ts` so core, encryption, telemetry, and platform bridge packages share explicit typed contracts.
- Replaced the encryption package's implicit `any` trace payloads with `DoTraceRecord` contracts.
- Updated the telemetry package to return structured write results instead of an untyped side effect only.
- Added `packages/bango-target/src/bango-bridge.ts` as the first reintegrated DoENGINE package derived from the existing `bango-patoot_3DS/bango_engine_target` bridge logic.
- Ported the Bango engine-target config, input ingestion, telemetry ingestion, and bridge-state update logic into TypeScript so the reintegration has an actual code artifact, not just a placeholder directory.
- Attempted to install the DoENGINE TypeScript toolchain, but the current shell does not expose `npm` or `node` on `PATH`, so compiler validation remains blocked on local tool availability.

## DoNOW and GUI pass

- Added `packages/donow/src/donow.ts` as the DoENGINE automated implementation module that translates clip-blend-id asset streams into immediate runtime buckets and preload groups.
- Added `tools/build_donow_runtime_manifest.py` so external pipelines can emit DoENGINE-ready runtime manifests directly beside other generated bundle outputs.
- Added `tools/build_doengine_gui_asset_manifest.py` to define a 3000-credit Recraft pass for a full DoENGINE GUI asset package following the MOTION philosophy.
- Added `apps/doengine_studio.py` and `DoENGINEStudio.cmd` as a standalone Windows-launchable DoENGINE Studio GUI around the generated manifests.

## Recommended next implementation order

1. Restore Node.js tooling in the shell and run a real `npm install` plus `npm run typecheck` inside `DoENGINE/`.
2. Replace placeholder hardware/session key generation with deterministic providers or injectable adapters.
3. Add compiled packaging for `DoENGINEStudio.cmd` once a preferred Python app bundler is selected in this environment.
4. Decide the production backup target strategy for `DOENGINE_BACKUP_ROOT`.
5. Continue reintegrating external modules or prior subprojects as packages/plugins under `DoENGINE/packages/`.

## DODOGame hybrid runtime validation pass

- Validated the DODOGame launcher surface in `apps/dodogame.py` and the Windows launcher `DODOGame.cmd`.
- Rebuilt the DODOGame GUI Recraft manifest and confirmed the requested budget is allocated exactly at 1500 credits in `generated/dodogame_gui_recraft_manifest.json`.
- Expanded `tools/generate_dodogame_placeholder_assets.py` and the generated `theme.json` contract so the DODOGame shell now has a full themed asset surface, not just badge/frame/panel placeholders.
- Regenerated the local fallback GUI shell assets and the two custom alphanumeric bitmap fonts (`dodo_font_stone`, `dodo_font_bone`) through `tools/generate_dodogame_placeholder_assets.py`.
- Rebuilt the hybrid runtime profile in `generated/dodogame_hybrid_runtime.json` so the combined DoENGINE + ORBEngine runtime advertises both the Bango-Patoot profile and a generic reusable hybrid-game profile.
- Corrected controller-contract coherence so the runtime profile now matches both DODOGame XInput button names and the Bango tutorial spec: tap `B` to jump, hold `B` to sprint, `A` for crouch/slide, `LB` and `RT` for attacks, `LeftThumb` and `RightThumb` for block/parry, and `LT` plus `right_stick` for the ability wheel.
- Expanded `apps/dodogame.py` so the launcher now previews the live/generated visual asset pack and input asset pack directly inside the GUI instead of only showing text dumps.
- Refreshed the PlayNOW handoff via `bango-patoot_3DS/tools/run_playnow.py --asset-root bango-patoot_3DS --pass-label dodogame --skip-autorig`, which regenerated the DODOGame-linked runtime manifest and pass manifest.
- Re-ran `bango-patoot_3DS/tools/simulate_bango_tutorial_completion.py`, which produced a fresh 100% completion report at `bango-patoot_3DS/generated/playnow/tutorial_completion_simulation_report.md`.
- Rebuilt the current Windows Bango-Patoot preview and confirmed `BangoPatootWindowsPreview.exe` still builds cleanly after the PlayNOW tutorial refresh.
- Hydrated `RECRAFT_API_KEY` from the persisted user environment into the active shell, cleared the generated DODOGame GUI image targets, and executed the full live 1500-credit Recraft pass successfully through `tools/run_dodogame_recraft_pass.py`.
- Verified all 21 DODOGame GUI outputs were generated into `generated/dodogame_gui/` in the same paths consumed by the launcher.

## Current limits after the DODOGame pass

- The DODOGame Recraft manifest targets the generated asset tree that `apps/dodogame.py` consumes, and the full live 1500-credit pass has now been executed successfully against that tree.
- Controller support is fully wired at the software/input-contract level through XInput polling, but physical-device validation still depends on an attached controller at runtime.
- The tutorial completion report is a deterministic rule-based player simulation against the current tutorial spec, not a computer-vision or emulator-driven playthrough of rendered gameplay.
- The combined DoENGINE + ORBEngine runtime is integrated through shared runtime contracts, manifests, and the DODOGame host shell, not yet fused into a single native compiled engine executable.
