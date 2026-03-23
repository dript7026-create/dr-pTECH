# Bango-Patoot idTech2 Game Module

Derived from OrbSeeker's idTech2 skeleton and adapted into a dedicated Bango-Patoot mod target.

What this is:

- a Bango-specific idTech2 game module that compiles against the real Quake II SDK,
- a bridge to the shared `bango_engine_target` layer (controller, telemetry, DoENGINE state),
- a place to wire generated `idLoadINT` runtime outputs into a true engine-facing mod,
- a controller-support entry point that lives in the engine target, not only in the game layer.

Build status:

- Real Quake II SDK is installed repo-locally at `.tools/quake2-sdk/Quake-2`.
- `game.dll` builds successfully via `.tools/bin/bango-idtech2-build.ps1`.
- Deployment to a Q2 mod folder is handled by `.tools/bin/bango-idtech2-deploy.ps1`.
- All three platforms (3DS, Windows, idTech2) can be built in one pass via `.tools/bin/build-all-platforms.ps1`.
