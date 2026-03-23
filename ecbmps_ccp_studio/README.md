# ECBMPS & CCP Studio

**drIpTECH** — Electronic Colour Book Media Playback Shell (.ecbmps) and ClipConceptBook (.ccp) compiler and viewer applications.

## File Types

### .ecbmps — Electronic Colour Book Media Playback Shell
A media-book format for rich, paged reading experiences.  
Features: page turning, bookmarking, passage highlighting, persistent reading state.  
No in-page gameplay. Read-only interactive content.

### .ccp — ClipConceptBook
An interactive media-book format with embedded gameplay and interactive scene elements.  
Extends .ecbmps with per-page scripted interactions and clip-based animations.

## Components

| Component | Description |
|-----------|-------------|
| `compiler/ecbmps_compiler.c` | Assembles source content into `.ecbmps` binary |
| `compiler/ccp_compiler.c` | Assembles source content into `.ccp` binary |
| `viewer/ecbmps_viewer.c` | Win32 GUI reader for `.ecbmps` files |
| `viewer/ccp_viewer.c` | Win32 GUI reader for `.ccp` files |
| `tools/recraft_manifest_generator.py` | Generates the Recraft asset manifest (1500 credits) |
| `assets/recraft/` | Generated GUI/shell art |

## Build

```powershell
.\build.ps1            # Build all (requires MSVC or MinGW)
.\build.ps1 -Target ecbmps_compiler
.\build.ps1 -Target ccp_compiler
.\build.ps1 -Target ecbmps_viewer
.\build.ps1 -Target ccp_viewer
```

## Asset Generation

```powershell
python tools\recraft_manifest_generator.py   # Write manifest JSON
python ..\drIpTECH\ReCraftGenerationStreamline\batch_run_manifest.py assets\ecbmps_ccp_shell_manifest.json
```
