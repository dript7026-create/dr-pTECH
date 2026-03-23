# KrabSurf

KrabSurf is a Windows-first controller-driven store browser shell for Xbox Series controllers.

It is designed around two modes:

- `Desktop Nav`: uses XInput and Windows `SendInput` to move the cursor, click, scroll, and send browser/navigation keys across the Windows desktop.
- `Store Surf`: presents a large-format launcher for approved web-based game stores and opens only allowlisted domains.

## Current Prototype Scope

- Xbox Series controller input through `xinput1_4.dll`, `xinput1_3.dll`, or `xinput9_1_0.dll`
- Desktop pointer control with left stick
- Scroll with right stick
- `A` left click
- `B` right click / back
- `X` refresh (`F5`)
- `Y` address / focus gesture (`Ctrl+L`)
- `LB` previous tab (`Ctrl+Shift+Tab`)
- `RB` next tab (`Ctrl+Tab`)
- `View` toggles desktop navigation on or off
- `Menu` launches the currently selected store
- Store launcher UI with allowlisted domains only
- Optional embedded browser path if `pywebview` is installed later
- Fallback launch path using Microsoft Edge or Google Chrome app mode

## Allowed Store Domains

- `store.steampowered.com`
- `steamcommunity.com`
- `www.gog.com`
- `gog.com`
- `itch.io`
- `www.itch.io`
- `store.epicgames.com`
- `www.xbox.com`
- `xbox.com`
- `apps.microsoft.com`
- `www.humblebundle.com`
- `humblebundle.com`

## Run

```powershell
python .\KrabSurf\krabsurf.py
```

## Notes

- This prototype is Windows-only because it uses `ctypes` bindings for XInput and `SendInput`.
- It does not attempt to replace the system browser stack. It provides a branded store-only shell with strict domain gating and controller navigation.
- If neither Edge nor Chrome is available, KrabSurf still runs as a controller shell and store selector, but external browsing will be unavailable.