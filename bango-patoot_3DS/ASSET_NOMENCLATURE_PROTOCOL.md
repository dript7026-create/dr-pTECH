# Bango-Patoot 2D Asset Nomenclature Protocol

Canonical example:

`bangopatoot_asset_graphical_charactersheet_bango_fouranglestpose_0001.png`

Protocol shape:

`[project]_[scope]_[medium]_[artifact_type]_[subject]_[variant]_[revision].[ext]`

Field meanings:

- `project`: project or game identifier.
- `scope`: pipeline scope such as `asset`, `ui`, `fx`, `env`, or another explicit domain marker.
- `medium`: media family such as `graphical`, `audio`, `video`, or `font`.
- `artifact_type`: the concrete asset container such as `charactersheet`, `spritesheet`, `tilesheet`, `portraitsheet`, `iconsheet`, `materialsheet`, or `fxsheet`.
- `subject`: the character, prop, faction, environment set, or system name.
- `variant`: the state, pose family, angle family, action family, palette family, or camera presentation.
- `revision`: zero-padded monotonic revision, usually four digits.

Current Bango sheet interpretation:

- `project`: `bangopatoot`
- `scope`: `asset`
- `medium`: `graphical`
- `artifact_type`: `charactersheet`
- `subject`: `bango`
- `variant`: `fouranglestpose`
- `revision`: `0001`

Allowed slight variations:

- Insert an additional qualifier between `artifact_type` and `subject` when needed for cross-project disambiguation.
- Use a richer `variant` token for action sets such as `sixframelocomotion`, `hurtfall`, `dodgeinteract`, or `materialatlas`.
- Keep tokens lowercase and underscore-delimited.
- Prefer descriptive but compact terms over abbreviations unless the abbreviation is already canonical in the project.

Recommended examples:

- `bangopatoot_asset_graphical_charactersheet_bango_sixframelocomotion_0002.png`
- `bangopatoot_env_graphical_tilesheet_underhivebrass_cobblestoneclean_0001.png`
- `bangopatoot_ui_graphical_portraitsheet_bango_dialoguecloseup_0001.png`
