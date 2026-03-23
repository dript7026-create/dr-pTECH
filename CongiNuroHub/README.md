# CongiNuroHub

CongiNuroHub is a first-cut educator-facing cognition simulation tool built for live browser access over a local or deployed URL. It is intentionally scoped as a deterministic educational simulation, not a claim of literal consciousness.

This milestone focuses on four deliverables:

- a browser-accessible live simulation hub
- a canonical ArtiSapiens dataset stored in this project and loaded by default
- a documented assembly-style tick kernel reference
- an 800-credit Recraft asset brief specialized from the NeoWakeUP control-hub visual philosophy

## Scope notes

- The request to generate the entire application in every programming language, markup language, natural language, and alphabet is not technically finite or verifiable. This repository milestone does not pretend to satisfy that requirement.
- The app runs as a small HTTP server so educators can open a URL locally or expose it on a school network.
- The visual system now reuses served NeoWakeUP-generated assets from the existing workspace while retaining the custom CongiNuroHub simulation core.

## Run

```powershell
python .\CongiNuroHub\run_conginurohub.py
python .\CongiNuroHub\run_conginurohub.py --host 0.0.0.0 --port 8877
```

Open the printed URL in a browser.

## API

- `GET /api/health`
- `GET /api/state`
- `GET /api/registry`
- `POST /api/step`
- `POST /api/reset`

Example step request:

```json
{
  "steps": 6,
  "directive": {
    "curiosity_bias": 0.72,
    "equity_bias": 0.78,
    "challenge_bias": 0.66,
    "reflection_bias": 0.81
  }
}
```

## Files

- `conginurohub/model.py` contains the deterministic simulation model.
- `conginurohub/data/artisapiens_seed_v1.json` is the canonical default ArtiSapiens dataset.
- `conginurohub/server.py` exposes the model and serves the browser UI.
- `docs/raw_tick_kernel.asm` contains the assembly-style tick reference.
- `docs/mathematical_model.md` explains the equation registry.
- `docs/deployment.md` documents container and Render deployment.
- `assets/recraft/conginurohub_gui_pass_800_manifest.json` defines the future Recraft art pass.

## Deployment

The repository now includes a `Dockerfile`, `.dockerignore`, and `render.yaml` so the app can run behind a stable hosted URL.

Local container run:

```powershell
docker build -t conginurohub .\CongiNuroHub
docker run --rm -p 8877:8877 conginurohub
```

## Testing

```powershell
pytest .\CongiNuroHub\tests\test_model.py
```