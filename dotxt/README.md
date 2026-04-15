# dotxt

dotxt is a Win32 C starter codebase for a broad file-acceptance word processor shell.

## Included So Far

- standard Windows shell window with menu bar
- RichEdit text surface for basic editing
- open and save flows with common dialogs
- broad open filter for common text/code formats and RTF
- plain text save as UTF-8 and RTF save/load support
- modified-state tracking with title/status updates
- Find and Replace dialogs (modeless common dialogs)
- Recent Files submenu with quick reopen
- startup plugin manifest scan and DLL loading attempt for free/premium/enterprise tiers
- WinMain compatibility shim for MinGW and other non-unicode entrypoint expectations

## Verified State

- Windows SDK headers were verified on this machine, including `windows.h`
- MinGW GCC toolchain was verified and used to build the app successfully
- the current output binary is `dotxt/build/dotxt.exe`
- editor tooling support was improved with `build/compile_commands.json`

See [docs/TOOLCHAIN_VERIFICATION.md](docs/TOOLCHAIN_VERIFICATION.md) for the full audit.

## Build (CMake)

From this directory:

```powershell
cmake -S . -B build
cmake --build build --config Release
```

Output executable: build/Release/dotxt.exe (multi-config generators) or build/dotxt.exe (single-config generators).

Or use the helper script:

```powershell
.\build.ps1
```

To rerun the toolchain/header/build verification pass:

```powershell
.\scripts\verify_toolchain.ps1
```

## Folder Layout

- src/: application C source files
- include/: headers
- plugins/free/: no-cost plugin drop-ins
- plugins/premium/: paid plugin drop-ins
- plugins/enterprise/: paid enterprise plugin drop-ins
- docs/: docs and plugin API notes
- scripts/: helper scripts for build and verification

## Documentation

- [docs/TOOLCHAIN_VERIFICATION.md](docs/TOOLCHAIN_VERIFICATION.md): verified tools, headers, missing installs, and build result
- [docs/PLUGIN_ROADMAP.md](docs/PLUGIN_ROADMAP.md): innovative plugin roadmap beyond normal word processors

## Next Steps

1. Add toolbar and keyboard accelerators table.
2. Persist Recent Files across launches.
3. Replace naive manifest parsing with a real JSON parser.
4. Add richer format adapters and safer large-file streaming.
5. Define a stable exported plugin API for DLL registration and capability negotiation.
