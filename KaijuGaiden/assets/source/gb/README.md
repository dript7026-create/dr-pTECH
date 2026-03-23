# KaijuGaiden GB Source Art

This directory is the editable source of truth for the generated headers in `assets/gb`.

Preferred workflow:

1. Place or update the source PNGs in this folder.
2. Run `python tools/build_gb_assets.py` from the KaijuGaiden root.
3. Review the regenerated headers in `assets/gb`.
4. Rebuild the host or NDS target and verify gameplay flow.

Expected source filenames:

- `tile_ground.png`
- `tile_water.png`
- `tile_cliff.png`
- `tile_sky.png`
- `bg_splash_driptech.png`
- `bg_title_logo.png`
- `spr_rei_idle.png`
- `spr_rei_run.png`
- `spr_rei_attack.png`
- `spr_boss_leviathan_p1.png`
- `spr_boss_leviathan_p2.png`
- `spr_boss_leviathan_p3.png`
- `spr_minion_crablet.png`
- `spr_fx_hit_spark.png`
- `spr_fx_nanocell_orb.png`
- `spr_cinematic_rei_large.png`
- `spr_cinematic_storm_kaiju.png`
- `hud_hp_segment.png`
- `hud_boss_hp_bar.png`

Current art direction:

- Rei: clean silhouette, aggressive forward lean, readable blade hand.
- Leviathan boss: phase 1 should read sleek and predatory, phase 2 should open the maw and widen the body mass, phase 3 should look damaged, flared, and unstable.
- Minions: compact crab-like bodies with clear claw read.
- Backgrounds: stronger lane readability, layered horizons, and biome-specific obstruction density.