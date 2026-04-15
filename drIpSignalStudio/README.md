# drIpSignalStudio

drIpSignalStudio is a local browser app for generating full ad draft packages and ranking five recommended daily submission windows from configurable performance signals.

It is scoped for manual posting. The app builds draft creative packages, timing recommendations, and rationale so you can review and submit them yourself.

## Features

- five recommended daily submission windows from configurable signals
- full ad draft packages with hooks, scripts, captions, and shot plans
- rendered poster and short video previews for each draft
- trend-shaped visual direction without requiring external APIs
- small local Python HTTP server and static browser UI

## Run

```powershell
python .\drIpSignalStudio\run_dripsignalstudio.py
python .\drIpSignalStudio\run_dripsignalstudio.py --host 0.0.0.0 --port 8891
```

Open the printed URL in a browser.

## API

- `GET /api/health`
- `GET /api/defaults`
- `GET /api/catalog`
- `POST /api/plan`

`POST /api/plan` renders local preview assets by default. Set `"render_previews": false` in the request body if you only want the planning payload.

Example request:

```json
{
  "profile": {
    "brand_name": "drIpTECH",
    "product_name": "Signal Forge",
    "audience": "indie founders and creators",
    "offer": "turn raw ideas into polished promo packages",
    "tone": "incisive, cinematic, hopeful",
    "cta": "Book a build sprint"
  },
  "signals": {
    "trend_momentum": 0.82,
    "audience_match": 0.77,
    "proof_strength": 0.69,
    "novelty_gap": 0.71,
    "fatigue_risk": 0.28,
    "conversion_intent": 0.74,
    "retention_pull": 0.63
  }
}
```

## Testing

```powershell
pytest .\drIpSignalStudio\tests\test_model.py
```

## Render Requirements

- `Pillow` is used to generate the preview frames.
- `ffmpeg` is used to encode short MP4 previews when available on `PATH`.
- If `ffmpeg` is not available, the app still generates poster renders and returns poster-only preview assets.
