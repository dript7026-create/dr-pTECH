# dripwave runtime drop

Place optional external runtimes here before running `build.ps1`.

Supported colocated names:

- `ruffle_desktop.exe`
- `flashplayer_32_sa.exe`
- `flashplayer_sa.exe`

The build script copies any matching runtime found here into `build/` so the finished `dripwave.exe` can discover it automatically.

You can also point the build at a runtime with the `DRIPWAVE_BACKEND_SOURCE` environment variable.