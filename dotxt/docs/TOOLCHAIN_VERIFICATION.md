# dotxt Toolchain Verification (2026-03-31)

## Verified Present

- gcc: C:/ProgramData/mingw64/mingw64/bin/gcc.exe
- windres: C:/ProgramData/mingw64/mingw64/bin/windres.exe
- mingw32-make: C:/ProgramData/mingw64/mingw64/bin/mingw32-make.exe
- gdb: C:/ProgramData/mingw64/mingw64/bin/gdb.exe
- cmake: c:/devkitPro/msys2/usr/bin/cmake.exe
- make: c:/devkitPro/msys2/usr/bin/make.exe

## Verified Windows SDK Headers

- Windows SDK base: C:/Program Files (x86)/Windows Kits/10
- detected include versions: 10.0.10240.0, 10.0.22621.0, 10.0.26100.0
- windows.h found at:
  - C:/Program Files (x86)/Windows Kits/10/Include/10.0.26100.0/um/windows.h

## Missing From PATH

- cl (MSVC compiler)
- clang
- ninja
- rc (Microsoft resource compiler)
- lld-link
- msbuild
- devenv

## Build Validation Result

A full CMake configure/build succeeded for dotxt using MinGW:

- configure: success
- compile: success
- link: success
- output: dotxt/build/dotxt.exe

## Header/Tooling Resolution Changes Applied

To address editor header diagnostics and keep IntelliSense aligned with the actual toolchain:

- enabled compile command export in CMake (`CMAKE_EXPORT_COMPILE_COMMANDS ON`)
- generated `dotxt/build/compile_commands.json`
- added VS Code settings at `dotxt/.vscode/settings.json` to use compile commands

## Recommended Optional Installs

Install these only if you want the corresponding workflow:

1. Visual Studio Build Tools (for `cl`, `rc`, `msbuild`)
2. Ninja (faster CMake generator option)
3. LLVM/Clang toolchain (`clang`, `lld-link`)
