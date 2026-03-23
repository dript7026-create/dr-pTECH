# DoENGINE

DoENGINE is the dedicated recovered workspace for the D-drive `doengine-backup` snapshot. This normalized hierarchy turns the backup into a clean package-first project structure instead of leaving it as a flat recovery dump.

## Workspace Layout

- `packages/core/src/` — runtime engine entrypoints and orchestration.
- `packages/encryption/src/` — encryption primitives and trace protection.
- `packages/telemetry/src/` — trace writing, metadata emission, and backup-facing I/O.
- `docs/philosophy/` — theory, nomenclature, and hardware-trace concepts.
- `docs/metadata/` — reintegration notes and metadata contracts.
- `docs/migration/` — source backup snapshots and migration mapping.
- `ops/backup/` — threefold backup tiers and scripts.
- `.github/` — workspace-specific Copilot instructions.

## Recovery Source

The source snapshot was recovered from `D:\doengine-backup` and preserved as read-only reference material under `docs/migration/`.

## Next Reintegration Steps

1. Add package manifests and build tasks for the TypeScript packages.
2. Replace placeholder hardware/session key generation with deterministic providers.
3. Define shared trace types instead of using `any`.
4. Decide whether the threefold backup stays inside the repo workspace or moves to a configured external root via `DOENGINE_BACKUP_ROOT`.
