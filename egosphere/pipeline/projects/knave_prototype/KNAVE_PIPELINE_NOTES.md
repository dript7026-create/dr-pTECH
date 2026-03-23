# Knave Prototype Asset Generator Notes

This project was created because no direct `Knave_prototype` or `Asset Generator` source tree existed in the workspace.
The pipeline therefore defines an explicit baseline profile, an advanced delta profile, and a symbolic godAI-driven evolution model.

## Advancement Axes
- silhouette_readability: hero, rival, elite, and boss silhouettes that read immediately at gameplay scale with asymmetry and role-specific profile breaks
- material_storytelling: layered materials that signal rank, weathering, ritual use, and combat history without collapsing readability
- animation_density: expanded anticipation, follow-through, guard states, finishers, and combat recovery frames with clean timing bands
- environment_depth: foreground-midground-backdrop separation with traversal cues, light wells, and combat readability lanes
- fx_legibility: distinct weapon, spell, guard-break, and finisher FX families that communicate outcome before impact resolves
- ui_authorship: premium interface systems with authored hierarchy, diegetic ornament restraint, and clean command-state separation

## Model Intent
- Compile designer-image components into Recraft-ready prompts.
- Preserve original authorship and prohibit direct copying.
- Use godAI pressure/mercy/novelty weights to guide real-time evolution decisions.
- Component count: 20

## ML Bootstrap
- Pixel-art history curriculum generated at `pixel_art_history_curriculum.json` with 7 curated eras spanning arcade readability through modern prestige pixel art.
- Combined training corpus generated at `knave_ml_training_corpus.jsonl` with 27 examples: 7 history examples plus 20 knave component examples.
- Trained steering model exported at `knave_trained_ml_model.json`.
- Validation report exported at `knave_trained_ml_report.json`.
- The trained layer is a lightweight text-and-metadata steering model for advancement axes and godAI weights, not a generative image foundation model.
- Inference contract clamps axis outputs to `[0.0, 1.0]` and godAI outputs to `[0.8, 1.4]` for stable downstream use.
