# InnsmouthIsland Protocol Pass Report

Date: 2026-03-11

## Scope

This report captures the resumed InnsmouthIsland protocol-generation pass after the ORBdimensionView, ORBKinetics, and ORBGlue ownership contract was locked into the engine and saved generation profile.

## Saved Protocol Artifacts

- Protocol profile: [drIpTECH/ReCraftGenerationStreamline/innsmouth_island_dimensional_protocol_profile.json](c:/Users/rrcar/Documents/drIpTECH/drIpTECH/ReCraftGenerationStreamline/innsmouth_island_dimensional_protocol_profile.json)
  - Size: `3415` bytes
- Attachment map: [drIpTECH/ReCraftGenerationStreamline/innsmouth_island_attachment_map_v1.json](c:/Users/rrcar/Documents/drIpTECH/drIpTECH/ReCraftGenerationStreamline/innsmouth_island_attachment_map_v1.json)
  - Size: `8226` bytes
- Environment runtime metadata: [drIpTECH/ReCraftGenerationStreamline/innsmouth_island_environment_runtime_metadata_v1.json](c:/Users/rrcar/Documents/drIpTECH/drIpTECH/ReCraftGenerationStreamline/innsmouth_island_environment_runtime_metadata_v1.json)
  - Size: `7749` bytes

The saved protocol now assigns:

- ORBdimensionView: dimensional anchor translation, curvature-consistent depth translation, top-cap projection, and pseudo-3D plane stitching.
- ORBKinetics: invisible hit and traversal silhouettes, exact-mask collision intent, and anchor-linked precision collision interpretation.
- ORBGlue: binding of generated anchor-node metadata to runtime sockets, equipment attachment, animation-state handoff, and gameplay-facing precision telemetry.

## Runtime Integration

- The InnsmouthIsland demo and research demo now load the saved ORBGlue attachment map JSON at startup instead of relying only on hardcoded runtime socket placement.
- The attachment map artifact now carries authored runtime socket profiles for base, armor, melee, and projectile bindings.
- Environment collision and occlusion logic now prefer authored environment metadata from a saved JSON artifact, with the prior procedural profile logic retained only as a fallback path.

## Runtime Metadata Refinement

- The duplicated Innsmouth runtime JSON parsing path has been extracted into the shared helper [ORBEngine/include/orbengine_innsmouth_runtime_metadata.hpp](c:/Users/rrcar/Documents/drIpTECH/ORBEngine/include/orbengine_innsmouth_runtime_metadata.hpp), so both standalone demos now consume the same attachment-map and environment-metadata loader code.
- Environment runtime metadata is no longer limited to raw `type` lookup. Both demos now assign stable placement keys to the 24 authored environment placements and resolve environment render/collision profiles by placement key first, then by type, then by procedural fallback.
- The environment runtime metadata artifact now carries a `placements` array alongside the original `profiles` array, which allows future per-placement silhouette, anchor, and occlusion overrides without changing current gameplay behavior.

## Full Protocol Generation Pass

Full manifest used:

- [drIpTECH/ReCraftGenerationStreamline/innsmouth_island_protocol_full_manifest.json](c:/Users/rrcar/Documents/drIpTECH/drIpTECH/ReCraftGenerationStreamline/innsmouth_island_protocol_full_manifest.json)

Result:

- `14/14` generations succeeded through the direct Recraft API path.
- Output directory: [ORBEngine/assets/innsmouth_island/protocol_full](c:/Users/rrcar/Documents/drIpTECH/ORBEngine/assets/innsmouth_island/protocol_full)
- Review sheet: [ORBEngine/assets/innsmouth_island/protocol_full/innsmouth_protocol_full_contact_sheet.png](c:/Users/rrcar/Documents/drIpTECH/ORBEngine/assets/innsmouth_island/protocol_full/innsmouth_protocol_full_contact_sheet.png)
  - Dimensions: `1302x1678`
  - File size: `2179546` bytes

Key environment outputs from the full pass:

- [ORBEngine/assets/innsmouth_island/protocol_full/innsmouth_environment_props_sheet_v2_research.png](c:/Users/rrcar/Documents/drIpTECH/ORBEngine/assets/innsmouth_island/protocol_full/innsmouth_environment_props_sheet_v2_research.png)
  - Dimensions: `1536x768`
  - File size: `1475480` bytes
- [ORBEngine/assets/innsmouth_island/protocol_full/innsmouth_landmark_panorama_sheet_v2_research.png](c:/Users/rrcar/Documents/drIpTECH/ORBEngine/assets/innsmouth_island/protocol_full/innsmouth_landmark_panorama_sheet_v2_research.png)
  - Dimensions: `1536x768`
  - File size: `1582506` bytes

## Full Protocol Polish Pass

Polish manifest used:

- [drIpTECH/ReCraftGenerationStreamline/innsmouth_island_protocol_polish_manifest.json](c:/Users/rrcar/Documents/drIpTECH/drIpTECH/ReCraftGenerationStreamline/innsmouth_island_protocol_polish_manifest.json)

Result:

- `14/14` polish generations succeeded through the direct Recraft API path.

Polish output directory:

- [ORBEngine/assets/innsmouth_island/protocol_polish](c:/Users/rrcar/Documents/drIpTECH/ORBEngine/assets/innsmouth_island/protocol_polish)

Polish review sheet:

- [ORBEngine/assets/innsmouth_island/protocol_polish/innsmouth_protocol_polish_contact_sheet.png](c:/Users/rrcar/Documents/drIpTECH/ORBEngine/assets/innsmouth_island/protocol_polish/innsmouth_protocol_polish_contact_sheet.png)
  - Dimensions: `636x1492`
  - File size: `1050622` bytes

Polish environment outputs:

- [ORBEngine/assets/innsmouth_island/protocol_polish/innsmouth_environment_props_sheet_v2_research.png](c:/Users/rrcar/Documents/drIpTECH/ORBEngine/assets/innsmouth_island/protocol_polish/innsmouth_environment_props_sheet_v2_research.png)
  - Dimensions: `1536x768`
  - File size: `1451064` bytes
- [ORBEngine/assets/innsmouth_island/protocol_polish/innsmouth_landmark_panorama_sheet_v2_research.png](c:/Users/rrcar/Documents/drIpTECH/ORBEngine/assets/innsmouth_island/protocol_polish/innsmouth_landmark_panorama_sheet_v2_research.png)
  - Dimensions: `1536x768`
  - File size: `1531150` bytes
- Comparison sheet: [ORBEngine/assets/innsmouth_island/protocol_polish/innsmouth_protocol_environment_compare_sheet.png](c:/Users/rrcar/Documents/drIpTECH/ORBEngine/assets/innsmouth_island/protocol_polish/innsmouth_protocol_environment_compare_sheet.png)
  - Dimensions: `1160x660`
  - File size: `1035792` bytes

## Build Verification

Validated successfully after the new runtime JSON loader integration:

- [ORBEngine/innsmouth_island_demo.exe](c:/Users/rrcar/Documents/drIpTECH/ORBEngine/innsmouth_island_demo.exe)
- [ORBEngine/innsmouth_island_research_demo.exe](c:/Users/rrcar/Documents/drIpTECH/ORBEngine/innsmouth_island_research_demo.exe)
- [ORBEngine/orbengine_sandbox.exe](c:/Users/rrcar/Documents/drIpTECH/ORBEngine/orbengine_sandbox.exe)

Validated successfully again after the shared-loader extraction and per-placement environment metadata pass:

- [ORBEngine/innsmouth_island_demo.exe](c:/Users/rrcar/Documents/drIpTECH/ORBEngine/innsmouth_island_demo.exe)
- [ORBEngine/innsmouth_island_research_demo.exe](c:/Users/rrcar/Documents/drIpTECH/ORBEngine/innsmouth_island_research_demo.exe)

## Outcome

The protocol pass is no longer just an art-side specification. The saved protocol, authored runtime attachment map, authored environment metadata, demo-side JSON loader path, ORBdimensionView anchor translation, ORBKinetics invisible silhouette handling, and ORBGlue binding model are now aligned enough to support future rerolls and deeper runtime attachment work without reintroducing conflicting vocabularies.