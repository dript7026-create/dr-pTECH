# FARIM Player

This folder contains the reference browser runtime for `FARIM 0.1` packages.

## Local Run

Serve the repository root over HTTP and open:

```text
skazka_terranova_c/farim/player/index.html?src=../../build/skazka_terranova_demo.farim
```

Example:

```powershell
cd C:\Users\rrcar\Documents\drIpTECH
.\.venv\Scripts\python.exe -m http.server 8040
```

Then open:

```text
http://127.0.0.1:8040/skazka_terranova_c/farim/player/index.html?src=../../build/skazka_terranova_demo.farim
```

## Current Scope

- loads `.farim` ZIP packages in-browser
- validates `farim_manifest.json`
- parses `runtime_anchors.csv`
- renders generated backgrounds, HUD, Media Deck panel, actor art, and simple interaction

## Not Yet Included

- signed package verification
- audio pipeline
- gameplay scripting section
- save files or progression persistence
- formal portal SDK hooks
