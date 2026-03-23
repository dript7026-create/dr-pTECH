# Dependency installer (SDL2, raylib)

This folder contains a master dependency manifest and an installer script to fetch prebuilt SDKs (SDL2, SDL_image, SDL_ttf, SDL_mixer, raylib) for Windows.

Files:
- `master_deps.json` — manifest of dependency names, versions, and download URLs.
- `install_deps.ps1` — PowerShell script to download and extract each entry into `deps/`.

Usage (run in an elevated PowerShell if necessary):

```powershell
cd drIpTECH
.\\install_deps.ps1
```

After running, you'll find the extracted SDKs in `drIpTECH\deps\`.

Notes:
- This only downloads and extracts prebuilt SDK zips. You may still need to copy DLLs into your project's `KaijuGaiden\build` or `dist` folder depending on the target packaging.
- For `raylib` you can either use the prebuilt MSVC package or build from source using CMake and Visual Studio tools; the manifest points to an MSVC prebuilt zip when available.
