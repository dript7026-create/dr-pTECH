# DoENGINE Backup System

- All critical files and traces are backed up threefold:
  1. `ops/backup/primary`
  2. `ops/backup/secondary`
  3. `ops/backup/tertiary`
- Backups are encrypted and include metadata traces.
- Automated scripts ensure all changes are mirrored and recoverable.
- Backup logs are themselves encrypted and traced.
- The canonical backup script now lives at `ops/backup/scripts/threefold-backup.ps1` and preserves relative paths instead of flattening the project tree.
