# Kin Dark Asset Program Overview

## Exact Requested Scope

- Graphical assets: 109867
- Audio assets: 2037
- Looping songs: 200

## Graphics Categories

- player_animation_prefabs: 288
- player_story_comics: 864
- npc_animation_prefabs: 29952
- enemy_animation_prefabs: 24960
- boss_animation_prefabs: 3456
- interaction_vfx_prefabs: 18432
- photo_texture_panels: 21600
- sprite_mesh_cards: 6912
- ui_controller_map_cards: 1536
- title_cinematic_save_cards: 312
- item_equipment_icons: 1555

## Audio Categories

- looping_songs: 200
- combat_sfx: 512
- traversal_sfx: 288
- interaction_cues: 420
- ambient_stingers: 240
- narrative_barks: 192
- menu_ui: 64
- save_load_title: 24
- boss_cues: 97

## Manifest Notes

- Graphics manifest format: JSON Lines at generated/kin_dark_graphics_manifest.jsonl
- Audio manifest format: JSON Lines at generated/kin_dark_audio_manifest.jsonl
- The graphics program includes the giant world-map model within the sprite-mesh card category.
- The audio program includes 200 two-minute looping songs and 1,837 non-music audio assets.
- Interaction VFX coverage is explicit rather than implied.
