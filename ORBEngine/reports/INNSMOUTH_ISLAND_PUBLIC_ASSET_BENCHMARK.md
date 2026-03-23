# InnsmouthIsland Public Asset Benchmark

Date: 2026-03-11

## Purpose

This document records the external public-asset benchmark pass used to pressure-test InnsmouthIsland asset-planning quality, modularity, consistency, and audit posture. No third-party assets were imported or copied into the project. The benchmark was used to derive production standards only.

## References

1. OpenGameArt. Home and community art index. https://opengameart.org/ Accessed 2026-03-11.
2. OpenGameArt. Art marketplace cross-promotion. https://opengameart.org/content/art-marketplace-cross-promotion Accessed 2026-03-11.
3. Kenney. Assets index. https://kenney.nl/assets Accessed 2026-03-11.
4. Liberated Pixel Cup. Project overview and style-guide framing. https://lpc.opengameart.org/ Accessed 2026-03-11.

## What The Benchmark Showed

### OpenGameArt

- Strength observed: breadth across art, UI, music, sound, and environment material, plus explicit free-license culture around CC0, CC-BY, CC-BY-SA, Public Domain, OGA-BY, and related terms from the cross-promotion note.
- Risk implication: license provenance can vary per asset and per contributor, so any future reference or import workflow needs per-asset logging instead of treating the platform as a single uniform license source.
- Design implication for InnsmouthIsland: our internal documents should explicitly separate inspiration research from any future actual imported references, and each future external image or sound reference needs individual provenance logging.

### Kenney

- Strength observed: highly modular kit philosophy, broad category spread across 2D, 3D, UI, audio, textures, input prompts, environment kits, and development essentials.
- Production implication: InnsmouthIsland should benchmark itself against Kenney-style completeness at the family level, meaning every gameplay system should have a full supporting asset family instead of isolated hero pieces.
- Concrete change adopted: our InnsmouthIsland atlas planning now favors family-complete outputs such as full weapon atlases, full armor-piece atlases, pickup-plus-shelter atlases, landmark boards, ground/decal sheets, and HUD/icon atlases.

### Liberated Pixel Cup

- Strength observed: explicit emphasis on stylistic consistency, a style guide, collaboration around shared constraints, and a deliberately chosen base perspective to enable broad reuse.
- Production implication: InnsmouthIsland needs a hard internal style guide, not just good prompts. Perspective, silhouette logic, tile-scale assumptions, and animation readability rules must be fixed before large-batch generation.
- Concrete change adopted: the asset bible now locks naming, pivots, collision-mask separation, neutral-light reference renders, and pseudo-3D translation metadata as first-class requirements.

## Benchmark Conclusions Incorporated Into InnsmouthIsland

1. Modular completeness standard.
   InnsmouthIsland asset families are now organized as whole kits rather than isolated image requests.

2. Style-guide discipline standard.
   Every generated family must satisfy one visual doctrine: black-tide ooze-punk, wet New England ruin-horror, readable gameplay silhouettes, and authored pseudo-3D anchors.

3. Provenance discipline standard.
   Every future external reference should be logged individually with source URL, date, rights basis, and exact usage mode.

4. Interface completeness standard.
   Research from Kenney-like kit breadth reinforced that HUD, codex, icons, prompts, and node markers must be treated as first-order production deliverables, not cleanup tasks.

5. Animation-system completeness standard.
   Research from LPC-style consistency reinforced that motion families need normalized coverage across locomotion, attack, reaction, and utility states so the runtime does not become a patchwork of missing transitions.

## Non-Adoption Rules

- Do not copy visual motifs, layouts, or sprite constructions directly from benchmarked sources.
- Do not reuse prompt wording taken verbatim from benchmark references.
- Do not assume platform-wide licensing from any single host; verify per asset if future importing or conditioning occurs.

## Research-Integrated Standalone Version

The separate research-integrated standalone executable exists to preserve these benchmark-informed standards without mutating the current main InnsmouthIsland demo branch. That build keeps gameplay parity while labeling itself as the benchmark-informed research track and pairing with the cited benchmark report, bibliography, and provenance ledger.