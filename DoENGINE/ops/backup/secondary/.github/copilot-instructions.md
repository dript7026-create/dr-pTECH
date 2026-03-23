<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->
- Keep DoENGINE organized as a package-first workspace: `packages/` for code, `docs/` for theory and metadata contracts, `ops/` for scripts and backups.
- Prefer normalized kebab-case file names for new supporting modules and docs unless a runtime entrypoint must keep a specific exported name.
- Do not hard-code machine-specific OneDrive or user-profile paths into source files; resolve paths relative to the workspace or from environment variables.
- Preserve the threefold backup model and encrypted-trace intent when extending the system.
- Treat the recovered files in `docs/migration/` as source artifacts; update the normalized files rather than editing the source snapshots.