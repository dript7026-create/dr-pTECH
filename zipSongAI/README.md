zipSongAI
=========

`zipSongAI` is a Windows C prototype for prompt-guided procedural song generation from `.zip` sample packs.

`SynthVoice` is now split into a reusable library plus a standalone service executable.

Files:
- `zipSongAI.c`: the main song-generator GUI.
- `synthvoice.h` and `synthvoice.c`: the shared adaptive/personality API.
- `synthvoice_service.c`: a standalone CLI service for chat, scheduling, notifications, diagnostics, and summary output.

What it does:
- Opens a `.zip` sample pack and extracts it with PowerShell `Expand-Archive`.
- Indexes `.wav` files inside the pack.
- Lets you shape a multi-section song with per-section tempo, meter, key, and context tags.
- Generates a fresh arrangement on every run using a unique seed.
- Persists a compact `SynthVoice` learning bank in `synthvoice_bank.dat` next to the executable.
- Persists `SynthVoice` personality/scheduling state in `synthvoice_personality.dat`.
- Opens a player window with `Play`, `Stop`, and `Save As...` controls after rendering.
- Exposes a separate `SynthVoice` service interface for other tools and generators.

Current scope:
- `zipSongAI` and `SynthVoice` are now separate software components in the same folder.
- `SynthVoice` provides practical adaptive heuristics, chat-like reporting, notifications, diagnostics, and scheduling primitives.
- It is API-ready in the sense that external tools can invoke the standalone service or link against the shared library interface.
- It does not claim true sentience or mathematical perfection.
- Best with WAV-based sample packs in the ZIP.

Build with MSVC Developer PowerShell:

```powershell
cd C:\Users\rrcar\Documents\drIpTECH\zipSongAI
cl /EHsc /DUNICODE /D_UNICODE zipSongAI.c synthvoice.c user32.lib gdi32.lib comdlg32.lib comctl32.lib shell32.lib shlwapi.lib winmm.lib
cl /EHsc /DUNICODE /D_UNICODE synthvoice_service.c synthvoice.c shlwapi.lib
```

Run:

```powershell
.\zipSongAI.exe
.\synthvoice_service.exe summary
```

Service examples:

```powershell
.\synthvoice_service.exe chat rrcar "summarize the current generator status"
.\synthvoice_service.exe diagnostics
.\synthvoice_service.exe schedule-add "Render review" "2026-03-11T09:00:00" music "Check last generated song"
.\synthvoice_service.exe schedule-list
.\synthvoice_service.exe notify "Generation completed"
```

Notes:
- Each click on `Generate Unique Song` uses a new seed and writes a new WAV file in the system temp folder.
- If your sample ZIP contains no `.wav` files, generation will stop with an error.
- `SynthVoice` evolves heuristics and communication state from prior runs, but it is deliberately implemented as deterministic learning logic rather than a claim of true sentience.
- The renderer is intentionally lightweight and should be treated as a foundation for a richer arranger, sampler, or model-backed audio workflow.