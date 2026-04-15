Gorge: Elemental Card Spectrums
================================

Overview
--------

- Platform: Game Boy Advance homebrew ROM (`.gba`)
- Genre: turn-based collectible creature card battler with a simple campaign ladder
- Delivery shape: complete, compact GBA adaptation of the requested design
- Hardware note: the NFC card reader and wireless dice are simulated inside the ROM as an in-universe `Spectral Reader` system because external hardware cannot be built or verified in this repository

Implemented Scope
-----------------

- 14 full decks
- 52 cards per deck
- 36 creature cards per deck
- 16 habitat cards per deck (`Jools` and `Gaorg`)
- campaign against 14 deck masters
- reward cards awarded after victories
- password-based progression continuation
- generated card art pack and generated audio preview pack
- real GBA ROM build path through devkitARM

Rules Translation
-----------------

- `Gaolite` beats `Jeurgren`
- `Jeurgren` beats `Fallows`
- `Fallows` beats `Gaolite`
- `Jools` and `Gaorg` are habitat cards that stabilize creatures and enable `Coupling`
- each battle begins after a simulated three-roll `d9` initiative contest
- each side fields a roster of three creature cards drawn from its deck
- attack resolution uses the requested `d6` and `d9` rolls plus a seven-stat `Spectrum` calculation across:
  - `degree`
  - `angle`
  - `cut`
  - `range`
  - `flow`
  - `arc`
  - `gauge`

Controls
--------

- `START`: title confirm / pause / continue text
- `A`: confirm / accept / advance battle choice
- `B`: cancel / back / end campaign screen text
- `UP/DOWN`: menu navigation
- `LEFT/RIGHT`: swap action targets and evolve branch previews when available
- `L`: quick stance toward patience
- `R`: quick stance toward aggression

Build
-----

From PowerShell in the workspace root:

```powershell
cd Gorge
cmd /c build.cmd
```

The build script will:

1. generate the full deck data, card PNGs, and audio previews
2. emit generated C headers under `src/generated/`
3. build `gorge.gba`

Outputs
-------

- ROM: `Gorge/gorge.gba`
- generated cards: `Gorge/generated/cards/`
- generated audio previews: `Gorge/generated/audio/`
- manifest: `Gorge/generated/gorge_manifest.json`
- generated runtime header: `Gorge/src/generated/gorge_content.h`
