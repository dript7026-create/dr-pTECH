# SkullDummy

SkullDummy is now split out as its own standalone project line.

## Android

The Android app lives in `skulldummy/android/`.

Current state:

- standalone Gradle project
- standalone namespace and application ID: `com.driptech.skulldummy`
- dedicated launcher activity in `skulldummy/android/app/src/main/java/com/driptech/skulldummy/MainActivity.kt`
- dedicated SkullDummy theme, manifest, audio, and image assets

Build from PowerShell:

```powershell
cd skulldummy\android
.\gradlew.bat assembleDebug
```

## GBA

The Game Boy Advance prototype now lives in `skulldummy/gba/`.

Current state:

- standalone SkullDummy demake/prototype folder
- local asset conversion pipeline that now reads from `skulldummy/android/app/src/main/res/drawable-nodpi`
- build, launch, and capture scripts rooted under `skulldummy/gba/`

Build from PowerShell:

```powershell
cd skulldummy\gba
.\build.ps1
```

Tooling notes:

- `build.ps1` resolves Python from `SKULLDUMMY_PYTHON`, `py -3`, or `python`
- it uses `make` directly when available, or falls back to a bash executable from `DEVKITPRO_BASH`, `MSYS2_BASH`, or `bash` on PATH

Both the Android and GBA tracks are now self-contained inside the `skulldummy/` root.
