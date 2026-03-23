# FARIM Specification

`FARIM` stands for `FluidAnimationRealityInteractiveMedia`.

This repository currently defines `FARIM 0.1` as a portable package for browser and native interactive media prototypes. The package is intentionally pragmatic: it is designed to be shippable now, versionable, and extensible, rather than pretending to provide impossible anti-reverse-engineering guarantees.

## Package Model

- Container: ZIP archive with `.farim` extension
- Manifest: `farim_manifest.json`
- Optional runtime tables: `runtime_anchors.csv`
- Asset payloads: `assets/*`
- Future extension points:
  - `scripts/*`
  - `audio/*`
  - `shaders/*`
  - `signatures/*`

## Required Entries

### `farim_manifest.json`

Required top-level fields:

- `format`: must be `farim`
- `format_version`: semantic format version string
- `description`: human-readable package description
- `created_at_utc`: ISO-8601 timestamp
- `assets`: array of asset metadata entries

Each asset entry currently supports:

- `name`: logical asset id
- `category`: semantic category such as `background`, `ui`, `rig_part`, `npc`, `fx`
- `entity`: optional logical owner for rig parts or NPC families
- `farim_layer`: rendering lane such as `background`, `actors`, `ui`, `fx`
- `joint_anchors`: normalized anchor map for runtime animation
- `palette_target`: optional palette hint for downstream runtime rendering
- `archive_path`: in-package path to the binary asset
- `sha256`: payload digest
- `width`
- `height`
- `size_bytes`

### `runtime_anchors.csv`

This is a runtime-friendly projection of anchor metadata for native loaders that do not want to parse JSON.

Schema:

```csv
name,anchor_name,x,y
misha_torso,shoulder_l,0.27,0.23
misha_torso,shoulder_r,0.73,0.23
```

## Security Model

`FARIM 0.1` is not an encrypted DRM container.

What it supports today:

- package hashing via per-asset SHA-256
- explicit manifest versioning
- deterministic archive contents
- compatibility with native and browser preview runtimes

What should be added for `FARIM 0.2+` if productization continues:

- signed package manifest
- detached signature block under `signatures/`
- optional encrypted payload groups for premium portal delivery
- asset chunking and streaming
- explicit script sandbox contract
- browser runtime capability manifest
- package-to-runtime compatibility matrix

## Browser Runtime Contract

The browser FARIM player in this repository assumes:

- the `.farim` file is fetchable over HTTP(S)
- the container is ZIP-compatible
- `farim_manifest.json` and `runtime_anchors.csv` are present
- visual assets are PNG files

The browser runtime should treat `.farim` as untrusted input and must:

- validate `format === "farim"`
- reject unexpectedly large packages
- reject missing `archive_path` entries
- only decode supported image/audio/script types

## Portal Integration Direction

For web portals such as Newgrounds, the recommended integration model is:

- FARIM player HTML/JS runtime hosted alongside the package
- the runtime fetches a `.farim` URL and mounts its asset payloads in-memory
- portal wrappers use iframe or direct embed pages
- save/progression remains runtime-defined, not package-defined

## Versioning

- `0.1`: ZIP bundle + JSON manifest + CSV anchors + PNG payloads
- `0.2`: signed package and explicit browser capability schema
- `0.3`: streamed chunks, audio, script sandbox, formal portal API bridge
