# CCP File Format Specification v3
# ClipConceptBook

## Overview
CCP is a binary container for interactive media books.  Each page
may contain artwork, text, AND scriptable interactive elements such
as clickable regions, embedded animations, and mini-game scenes.
CCP extends the ECBMPS reading model with gameplay hooks.

V3 adds the **GPLY gameplay section** — compiled bytecode from
Clip Studio Paint visual scripting via the pipeline bridge.  This
enables full in-page interactivity/gameplay beyond simple clickable
regions: entities with collision detection, timeline animations,
controller input, scene state machines, and a stack-based VM.

## Controller Support
Both .ccp and .ecbmps viewers support XInput controllers:
- **LT (Left Trigger)** = Previous page  *(RESERVED, not scriptable)*
- **RT (Right Trigger)** = Next page  *(RESERVED, not scriptable)*
- A/B/X/Y, D-pad, bumpers, sticks = Available for gameplay scripting

## Header
### V2 Header (28 bytes, little-endian) — backward compatible
| Offset | Size | Field           | Notes                             |
|--------|------|-----------------|-----------------------------------|
| 0      | 4    | magic           | `CCP1` (0x43 0x43 0x50 0x31)     |
| 4      | 4    | version         | uint32, `2` for v2                |
| 8      | 4    | page_count      | uint32                            |
| 12     | 8    | manifest_size   | uint64 — size of JSON manifest    |
| 20     | 8    | source_zip_size | uint64 — size of optional zip     |

### V3 Header (36 bytes, little-endian) — with gameplay
| Offset | Size | Field           | Notes                             |
|--------|------|-----------------|-----------------------------------|
| 0      | 4    | magic           | `CCP1` (0x43 0x43 0x50 0x31)     |
| 4      | 4    | version         | uint32, `3` for v3                |
| 8      | 4    | page_count      | uint32                            |
| 12     | 8    | manifest_size   | uint64 — size of JSON manifest    |
| 20     | 8    | source_zip_size | uint64 — size of optional zip     |
| 28     | 8    | gameplay_size   | uint64 — size of GPLY section     |

## File Layout
```
[Header 28 or 36 bytes]
[Manifest JSON — manifest_size bytes]
[Source ZIP — source_zip_size bytes (optional)]
[Gameplay GPLY — gameplay_size bytes (v3 only)]
```

## Manifest Payload
Immediately follows header.  UTF-8 JSON object with keys:
- `title` — book title string
- `author` — author string
- `book_mode` — `"interactive"` or `"presentation"`
- `pages` — array of page descriptors
- `prompt_map` — per-page metadata for asset generation
- `scripts` — optional embedded interaction script table

### Page Descriptor
```json
{
  "page": 1,
  "clip": "pg1.clip",
  "type": "combined",
  "interactive": true,
  "regions": [
    {"id": "btn_next", "x": 100, "y": 200, "w": 80, "h": 40, "action": "goto_page:2"}
  ]
}
```

## Source ZIP Payload
Optional appended ZIP archive containing `.clip` source files,
raw artwork, and ancillary data.  The ZIP should contain compressed
.clip files with embedded interactivity scripting from Clip Studio
Paint.  The pipeline bridge exports (`clipstudio_runtime_manifest.json`,
`clipstudio_export.json`) inside the ZIP define the gameplay metadata
that gets compiled into the GPLY section.

## Interactive Region Actions (v2 legacy)
| Action Pattern       | Description                        |
|---------------------|------------------------------------|
| `goto_page:N`       | Navigate to page N                 |
| `play_anim:name`    | Play named animation on page       |
| `toggle:id`         | Toggle visibility of element       |
| `run_scene:name`    | Launch embedded mini-scene         |
| `set_var:key=value` | Set persistent variable            |

## GPLY Gameplay Section (v3)
Binary section containing compiled gameplay bytecode from CSP
visual scripting.  Maps Clip Studio Paint concepts to runtime:

| CSP Concept       | GPLY Concept   | Description                    |
|-------------------|----------------|--------------------------------|
| SymbolObject      | EntityDef      | Sprite with timeline animation |
| VisualScript      | ScriptDef      | Bytecode event handler         |
| HitDetection      | HitboxDef      | Collision shape per entity     |
| SceneSequence     | SceneDef       | Entity/script activation group |
| ButtonObject      | EventBinding   | Input → script wiring          |

### GPLY Header (28 bytes)
| Offset | Size | Field               | Notes                    |
|--------|------|---------------------|--------------------------|
| 0      | 4    | magic               | `GPLY` (0x594C5047)      |
| 4      | 4    | version             | uint32, `1`              |
| 8      | 2    | entity_def_count    | uint16                   |
| 10     | 2    | hitbox_def_count    | uint16                   |
| 12     | 2    | script_count        | uint16                   |
| 14     | 2    | scene_count         | uint16                   |
| 16     | 2    | event_binding_count | uint16                   |
| 18     | 2    | variable_count      | uint16                   |
| 20     | 4    | string_table_size   | uint32                   |
| 24     | 4    | bytecode_size       | uint32                   |

### GPLY Section Layout
```
[GplyHeader 28 bytes]
[EntityDef entries — 16 bytes each]
[HitboxDef entries — 14 bytes each]
[ScriptDef entries — 10 bytes each]
[SceneDef entries — 12 bytes each]
[EventBinding entries — 10 bytes each]
[VariableDef entries — 6 bytes each]
[String table — null-terminated strings]
[Bytecode — raw VM instructions]
```

### VM Opcodes
Stack-based VM with 30+ opcodes for entity lifecycle, collision,
variables, control flow, input, UI, and math.  See `ccp_gameplay.h`
for the full opcode table.

### Event Types
| Event          | Trigger                              |
|----------------|--------------------------------------|
| PAGE_ENTER     | Page becomes active                  |
| PAGE_EXIT      | Page deactivated                     |
| FRAME_TICK     | Every frame (~16ms, ~60fps)          |
| CLICK          | Mouse/touch on entity hitbox         |
| HOVER_ENTER    | Cursor enters entity hitbox          |
| HOVER_EXIT     | Cursor leaves entity hitbox          |
| COLLIDE        | Two entity hitboxes overlap          |
| TRIGGER        | Timeline trigger frame reached       |
| BUTTON_DOWN    | Controller button pressed            |
| BUTTON_UP      | Controller button released           |
| SCENE_ENTER    | Scene activated                      |
| SCENE_EXIT     | Scene deactivated                    |

### Hitbox Kinds
| Kind | Name    | Description                     |
|------|---------|---------------------------------|
| 0    | solid   | Blocks movement                 |
| 1    | trigger | Fires events on overlap         |
| 2    | hurtbox | Damage/interaction zone         |
| 3    | button  | Clickable UI element            |

## Compilation Pipeline
```
Clip Studio Paint
  └─ CSP Plugin (ClipStudioPixelBrushSuite)
       └─ Pipeline Bridge (ClipStudioPipelineBridge)
            └─ clipstudio_runtime_manifest.json
                 └─ GPLY Compiler → gameplay.gply
                      └─ CCP Compiler → output.ccp (v3)
                           -m manifest.json
                           -z source.zip (compressed .clip files)
                           -g gameplay.gply
```

## File Extension
`.ccp`

## MIME Type
`application/x-ccp`
