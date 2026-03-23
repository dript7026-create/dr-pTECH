# Gravo Art Intake Spec

When returning with concept art, package it as a `.zip` rooted at `concept_art_intake/` using the directories already created in this project.

Expected structure:
- `concept_art_intake/characters/gravo/`
- `concept_art_intake/enemies/basic/`
- `concept_art_intake/enemies/high_tier/`
- `concept_art_intake/environments/`

Preferred filename pattern:
- `gravo_[sheet-or-view]_[angle-or-state]_v01.png`
- `enemy_basic_[family]_[sheet-or-view]_v01.png`
- `enemy_hightier_[family]_[sheet-or-view]_v01.png`
- `environment_[biome]_[angle-or-location]_v01.png`

Required art properties:
- Transparent background.
- Clean silhouette edges.
- Readable lighting direction.
- Deliberate shade/highlight gradients.
- Shape curvature that implies volume.
- Consistent attachment points where limbs, gear, and FX would align.
- Negative space around the figure/object for extraction and atlas packing.

Helpful overlays if available:
- Front, 3/4, side, and rear views for Gravo and major enemies.
- Callout variants for beam eye, beamsword, shrine interaction, hit reaction, and traversal poses.
- Environment sheets with multiple angles, landmark callouts, ground pattern callouts, and scale references.
- Optional guide layers that indicate pseudo-depth planes, material boundaries, emissive zones, and likely collision extents.

What I will do with the intake later:
1. Normalize the sheets into a production asset inventory.
2. Map art families onto ORBSystems ownership rules.
3. Build a Recraft completion manifest targeting the missing asset surface.
4. Generate the expansive follow-up pass in the planned `6000-10000` credit band.
5. Integrate approved outputs into the Gravo runtime and future PS5-facing content pipeline.