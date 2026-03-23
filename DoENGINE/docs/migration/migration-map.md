# DoENGINE Migration Map

This document maps the original `D:\doengine-backup` recovery layout into the normalized workspace hierarchy.

## Directory Mapping

- `src/` -> `packages/core/src/`
- `encryption/` -> `packages/encryption/src/`
- `metadata/` -> `packages/telemetry/src/` and `docs/metadata/`
- `philosophy/` -> `docs/philosophy/`
- `backup/` -> `ops/backup/`
- `.github/` -> `.github/`
- `README.md` -> `README.md` plus `docs/migration/source-readme.md`
- `backup-log.txt` -> `docs/migration/source-backup-log.txt`

## File Mapping

- `src/doengine.ts` -> `packages/core/src/doengine.ts`
- `encryption/encryptor.ts` -> `packages/encryption/src/encryptor.ts`
- `metadata/traceWriter.ts` -> `packages/telemetry/src/trace-writer.ts`
- `metadata/reintegrate.md` -> `docs/metadata/reintegrate.md`
- `metadata/structure.md` -> `docs/metadata/structure.md`
- `philosophy/frequency-reality.md` -> `docs/philosophy/frequency-reality.md`
- `philosophy/hardware-trace.md` -> `docs/philosophy/hardware-trace.md`
- `backup/threefold-backup.ps1` -> `ops/backup/scripts/threefold-backup.ps1`

## Normalization Rules Applied

- Package-first code organization.
- Supporting file names shifted toward kebab-case where practical.
- Machine-specific filesystem paths removed from active source files.
- Recovery-source artifacts preserved under `docs/migration/` instead of being overwritten.
