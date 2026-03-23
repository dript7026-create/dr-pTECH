# DoENGINE Metadata Structure

- All files, actions, and events are logged as encrypted Traces.
- Each Trace includes: timestamp, Doer, Motif, Vibe, and hardware signature.
- Traces are written to hardware using proprietary encryption and are permanent.
- Metadata is threefold-backed up in /backup and mirrored in /metadata.
- Example Trace (JSON):
{
  "timestamp": "2026-02-15T00:00:00Z",
  "doer": "engine",
  "motif": "startup",
  "vibe": "init",
  "hardware": "HWID-123456",
  "trace": "<encrypted>"
}