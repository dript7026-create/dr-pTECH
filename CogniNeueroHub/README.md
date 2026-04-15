# CogniNeueroHub

CogniNeueroHub is a first-cut educator-facing cognition simulation tool built for live browser access over a local or deployed URL. It is intentionally scoped as a deterministic educational simulation, not a claim of literal consciousness.

This milestone focuses on four deliverables:

- a browser-accessible live simulation hub
- a canonical ArtiSapiens dataset stored in this project and loaded by default
- a documented assembly-style tick kernel reference
- an 800-credit Recraft asset brief specialized from the NeoWakeUP control-hub visual philosophy

## Scope notes

- The request to generate the entire application in every programming language, markup language, natural language, and alphabet is not technically finite or verifiable. This repository milestone does not pretend to satisfy that requirement.
- The app runs as a small HTTP server so educators can open a URL locally or expose it on a school network.
- The visual system now reuses served NeoWakeUP-generated assets from the existing workspace while retaining the custom CogniNeueroHub simulation core.

## Run

```powershell
python .\CogniNeueroHub\run_cognineuerohub.py
python .\CogniNeueroHub\run_cognineuerohub.py --host 0.0.0.0 --port 8877
```

Open the printed URL in a browser.

## API

- `GET /api/health`
- `GET /api/animations`
- `GET /api/lessons`
- `GET /api/course`
- `GET /api/course/export`
- `GET /api/state`
- `GET /api/registry`
- `GET /api/dataset`
- `POST /api/respond`
- `POST /api/course/import`
- `POST /api/course/setup`
- `POST /api/student-note`
- `POST /api/step`
- `POST /api/reset`

Example step request:

```json
{
  "steps": 6,
  "lesson": {
    "title": "Medieval Bavaria: duchies, monasteries, and the Wittelsbach rise",
    "subject": "history",
    "region": "Bavaria",
    "era": "900-1300 CE",
    "essential_question": "How did political power, monastic culture, and imperial ties shape medieval Bavaria?"
  },
  "directive": {
    "curiosity_bias": 0.72,
    "equity_bias": 0.78,
    "challenge_bias": 0.66,
    "reflection_bias": 0.81
  }
}
```

Example response-analysis request:

```json
{
  "lesson": {
    "lesson_id": "medieval-bavaria-v1"
  },
  "response": "Bavaria stayed tied to the Holy Roman Empire, while monasteries and trade routes helped support political order. The Wittelsbachs gained power in a world shaped by investiture conflict and regional exchange."
}
```

Example course-start profile setup:

```json
{
  "title": "Bavaria Seminar Spring",
  "educator_name": "Dr. Rowan",
  "course_notes": "Profiles are developed at the start of the course and refined as students reveal strengths and supports.",
  "god_profile": {
    "conductor_name": "GodAI Seminar Voice",
    "tone": "steady mercy",
    "mercy_bias": 0.82,
    "challenge_bias": 0.61,
    "wonder_bias": 0.86
  },
  "politeness_protocol": {
    "greeting_template": "Good morning",
    "affirmation_template": "Thank you for your thoughtful work",
    "closing_template": "Take your time and proceed with care",
    "redirection_template": "Let us return to one anchor at a time"
  },
  "pace_profile": {
    "auto_pace_enabled": true,
    "manual_pace_bias": 0.46,
    "manual_clarity_bias": 0.84,
    "ai_authority": 0.78,
    "target_page_minutes": 5.5,
    "target_puzzle_seconds": 80.0,
    "live_metrics": {
      "page_minutes": 6.8,
      "average_puzzle_seconds": 108.0,
      "last_puzzle_seconds": 124.0,
      "active_activity_seconds": 42.0,
      "solved_activity_count": 2
    }
  },
  "students": [
    {
      "student_id": "ada-l",
      "display_name": "Ada L.",
      "archetype": "careful synthesizer",
      "strengths": ["pattern recognition", "measured writing"],
      "support_needs": ["clear sequencing", "spoken recap"],
      "interests": ["monastic history", "maps"],
      "preferred_modalities": ["discussion", "short writing"],
      "egosphere": {
        "trust": 0.67,
        "fear": 0.31,
        "adaptability": 0.72,
        "reciprocity": 0.6,
        "resonance": 0.79,
        "dominance": 0.22
      },
      "speech": {
        "voice_name": "Microsoft Aria Online (Natural) - English (United States)",
        "voice_hint": "calm",
        "rate": 0.95,
        "pitch": 1.02,
        "volume": 1.0
      }
    }
  ]
}
```

Example personalized note request:

```json
{
  "student_id": "ada-l",
  "lesson": {
    "lesson_id": "medieval-bavaria-v1"
  }
}
```

Example animation-library response excerpt:

```json
{
  "library_id": "lesson-animation-library-v1",
  "title": "Quiet Animation Library",
  "animations": [
    {
      "animation_id": "teddy-bear-scribe",
      "title": "Teddy Bear Scribe",
      "asset_path": "/lesson-animations/teddy-bear-scribe.svg"
    },
    {
      "animation_id": "fawn-route-guide",
      "title": "Fawn Route Guide",
      "asset_path": "/lesson-animations/fawn-route-guide.svg"
    }
  ]
}
```

Example course export payload:

```json
{
  "course": {
    "title": "Bavaria Seminar Spring"
  },
  "exported_from": "CogniNeueroHub",
  "version": 1
}
```

## What Changed

- Course profiles now include a politeness protocol so generated notes and spoken guidance greet students, affirm effort, and redirect gently.
- Student profiles now keep per-lesson history, including mastery, response score, pace compensation mode, and obscurity risk.
- The browser course dock now supports import/export of course setup JSON and offers exact browser voice selection alongside voice-hint fallback.
- Lesson state now includes a pace-and-visual-clarity profile that tests whether erratic pacing, long-term drag, page duration, and puzzle solve speed are obscuring the display, then applies compensations such as anchor recaps, rhythmic refresh, or focus-windowed stillness.
- Those compensations also flow into the live feed so motion and opacity are softened when obscurity risk rises.
- The educator can keep pace controls hidden in a collapsed dock section, while AI auto-run uses the live pace profile to choose step count and interval in real time.
- Lesson authors can now attach local animation-library entries to lessons and activities through `animation_ids`.
- The app now serves a dedicated local animation manifest from `GET /api/animations` and local SVG animation assets from `cognineuerohub/web/lesson-animations/`.
- The default Bavaria lesson pack now includes authored custom-game activities using a declarative `custom_game` type with `config` payloads.
- The browser lesson panel now previews selected animation companions, and the learning studio can run sequence-based custom games.
- The browser course dock now includes a lesson author studio for choosing animation companions, building a custom sequence game, restoring the packaged lesson, and exporting authored lesson JSON.

## Lesson Authoring

Lesson JSON now supports two additional authoring surfaces:

- `animation_ids` at the lesson level or activity level for selecting entries from the local animation database.
- `custom_game` activities with a `config` object for declarative game setup.

The browser UI now also supports a no-code authoring pass inside the course dock:

- choose lesson animation companions from the local animation library
- define a sequence-based custom game with token lines in the form `id | label | hint`
- apply the authored game to the active lesson immediately for simulation and puzzle play
- restore the packaged lesson or export the authored lesson as JSON

Minimal custom-game example:

```json
{
  "activity_id": "charter-chain",
  "type": "custom_game",
  "title": "Charter Chain",
  "prompt": "Place the civic chain in the strongest explanatory order.",
  "animation_ids": ["teddy-bear-scribe", "fawn-route-guide"],
  "config": {
    "game_type": "sequence_builder",
    "support_text": "Start from the institution or route that makes the next link possible.",
    "completion_message": "The chain is complete.",
    "tokens": [
      {"id": "memory", "label": "Monastic Memory", "hint": "Preserves literacy and records."},
      {"id": "route", "label": "Route Network", "hint": "Moves goods and people."},
      {"id": "rule", "label": "Visible Rule", "hint": "Turns the network into authority."}
    ],
    "correct_order": ["memory", "route", "rule"]
  }
}
```

## Files

- `cognineuerohub/model.py` contains the deterministic simulation model.
- `cognineuerohub/data/lesson_library_v1.json` carries the default lesson content pack with eras, figures, vocabulary, source excerpt material, and multi-activity lesson flows.
- `cognineuerohub/data/animation_library_v1.json` carries the local lesson animation manifest for author-selected companions and motion themes.
- `cognineuerohub/model.py` now also holds course-start student profiles, Egosphere-style student state signals, God-conductor note guidance, politeness protocol handling, student lesson history, pace-obscurity compensation, and speech metadata for browser playback.
- `cognineuerohub/data/artisapiens_seed_v1.json` is the canonical default ArtiSapiens dataset.
- `cognineuerohub/server.py` exposes the model and serves the browser UI.
- `cognineuerohub/web/lesson-animations/` contains the generated local SVG animation assets, including teddy-bear and baby-deer themed companions.
- `docs/raw_tick_kernel.asm` contains the assembly-style tick reference.
- `docs/mathematical_model.md` explains the equation registry.
- `docs/deployment.md` documents container and Render deployment.
- `assets/recraft/cognineuerohub_gui_pass_800_manifest.json` defines the future Recraft art pass.

## Deployment

The repository now includes a `Dockerfile`, `.dockerignore`, and `render.yaml` so the app can run behind a stable hosted URL.

Local container run:

```powershell
docker build -t cognineuerohub .\CogniNeueroHub
docker run --rm -p 8877:8877 cognineuerohub
```

## Testing

```powershell
pytest .\CogniNeueroHub\tests
```