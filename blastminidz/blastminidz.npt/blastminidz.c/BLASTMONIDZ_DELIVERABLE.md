# Blastmonidz Deliverable

This package is the current Windows host vertical slice for Blastmonidz.

## Included

- `blastmonidz_host.exe` - console host and match loop
- `bomberman_archive_cache/` - extracted title, tile, bomb, paint, and character art used by the companion window
- `launch_blastmonidz.cmd` - one-click launcher
- `profiles/` - saved run outputs when present
- `blastmonidz_bridge_inbox.txt` and `blastmonidz_bridge_outbox.txt` - live workflow bridge files for short updates between the running host and outside work

## Shipped Feature Spec

- maximized full-screen title scene with archive-backed title art, animated bomb pulses, rotating silhouette families, and live anti-gossip rhyme marquee copy
- lore brief and archive coherency browser
- starter token draw with procedurally selected archive-backed portraits
- seeded procedural graphics engine that rotates full Bomberman walk-frame pools, bomb animation frames, paint overlays, and arena prop variants into unique per-run presentation
- consensus arena match loop with archive-backed floor, crate, bomb, gem, and blastkin rendering in the window companion
- chemistry-driven evolution, ghost-line re-entry, and first-to-3 run progression
- run-profile and replay-summary save output including visual theme and seed metadata
- file-backed live bridge polling so the host and external workflow notes can exchange short real-time updates while the build is running

## Controls

- `w`, `a`, `s`, `d` move
- `b` place bomb
- `c` cycle concoction
- `r` manifest from ghost state when available
- `t` wait
- `q` quit the run

## Packaging

Run `package_blastmonidz_deliverable.ps1` to rebuild the host, refresh the extracted archive cache, stage the deliverable folder, and emit `dist/blastmonidz_deliverable.zip`.