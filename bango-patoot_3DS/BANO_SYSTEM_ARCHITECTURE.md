# Bango-Patoot Systems Architecture

## Runtime Modules
- `WorldState`: hub/subworld topology, level gates, collectible completion, shrine activation.
- `PlayerState`: stats, skill points, equipped traversal/combat options, stamina and magic budgets.
- `MoveCatalog`: generated move roster, keyframe descriptors, inbetween hints, unlock state.
- `ShrineSystem`: honey refinement, fast travel, checkpointing, limited respec.
- `QuestState`: Tula rescue arc, world acts, subworld objective states.
- `RelationshipState`: EgoSphere-backed non-player-entity memory and attitude matrix.
- `RenderState`: simple stereoscopic scene config, sprite-billboard descriptors, mesh placeholders, camera state, and urban-horror atmosphere controls.

## Data Model Choices
- Keep the prototype as a single C translation unit for now because the user explicitly asked to code directly in the `.c` file.
- Use plain old data structs and deterministic update loops so the later 3DS optimization pass is straightforward.
- Generate content tables procedurally where scale is high, especially the move roster and skill nodes.
- Keep nouns, silhouettes, and encounter families original and not dependent on protected Banjo-Kazooie content.

## 3DS Technical Stack
- `libctru` for app lifecycle, input, and services.
- `citro2d` for UI and sprite-facing draw helpers.
- `citro3d` for stereoscopic world setup and simple geometry.
- First prototype should prioritize stable app flow and data visibility over advanced rendering.

## Animation Strategy
- Author and store 3 to 6 keyframes per move.
- Keep per-move timing, momentum, and contact metadata.
- Inbetweener concept in prototype: interpolation hints and physics weights, not ML inference.
- Later tool phase can consume authored key poses and generate refined animation clips offline.

## Urban Horror Layer
- Each biome should combine one mundane civic function with one folkloric violation.
- Enemy families should map to gangs, cult cells, cryptids, civic-machine failures, and doctrinal aberrations.
- RelationshipState should allow zones to become safer or more hostile based on rescue behavior, shrine use, and faction handling.

## Research/Design Follow-ups
- Define seven subworld biome identities.
- Formalize the shrine tree and cost curves.
- Formalize the NPE relationship events that write back into gameplay.
- Add content spreadsheets or JSON exporters once the prototype loop stabilizes.