$projectRoot = "C:\Users\rrcar\Documents\drIpTECH\tommygoomba\tommy-goomba-1"
New-Item -ItemType Directory -Force -Path (Join-Path $projectRoot "scripts") | Out-Null

$readmeCombined = @'
# TOMMY GOOMBA
An original parody puzzle-RPG marriage rescue adventure by the Carell brothers.  
Target platform: Nintendo Game Boy family of systems (`.gb` via GBDK).

## Overview
Tommy Goomba is a stage-based action-adventure with puzzle and RPG encounter elements.
The player navigates 66 prebuilt stages while searching for Tommy’s wife in a dynamic world
where hostile and neutral entities migrate over time.

## Story Context
Tommy’s home life is shattered by a sudden attack from two mysterious brothers.
His wife is abducted, and a damaged phone short-circuit unlocks Tommy’s first special ability:
Charged Dash. Tommy is launched into a fractured overworld and must pursue across moving
encounter routes until reunion.

## Core Gameplay
1. Move to a stage
2. Search / explore
3. Resolve encounter (dialogue, puzzle, combat, boss)
4. Advance world simulation tick
5. Continue pursuit

Win condition: reunite with Tommy’s wife (ending variant depends on encounter history).

## Controls + Combat
- A: Bite (basic attack)
- B: Selected special attack
- D-Pad: Move
- Start: Pause/menu
- Xbox View button (emulator mapping): cycle special attacks
- Starting special: Charged Dash

## Overworld Boss Encounters (Parody)
- Fortress Tyrant (Bowser-inspired) -> Shell Guard
- Jungle Giant (DK-inspired) -> Primal Toss
- Mirage Duelist (Birdo-inspired) -> Egg Arc
- Vault Brute (Wario-inspired) -> Greed Rush
- Trickster Duelist (Waluigi-inspired) -> Chaos Spin
- Hex Mage (Kamek-inspired) -> Counter Sigil
- Phantom Lord (King Boo-inspired) -> Phase Step

## NPC Migration + AI
All non-player entities run lightweight world-tick behavior:
- intent-weighted routing
- faction relationship logic
- region affinity and danger avoidance
- dynamic encounter composition by co-location

Persistence:
- major brothers can be permanently removed on defeat
- recurring rivals can reappear in later ticks

## EgoSphere Integration Plan
Use EgoSphere systems for:
- entity world-state tracking
- migration/path weighting
- event queue and encounter resolution
- persistent narrative flags and save outcomes

## Asset Requirements Summary
Graphics:
- overworld/interior/puzzle tilesets
- character sprites (Tommy, wife, rivals, bosses, civilians)
- HUD/menu/cinematic cards
- combat and traversal VFX

Audio:
- title/overworld/combat/boss/ending music
- bite/dash/hit/menu/puzzle/ambient SFX
- optional dialogue text blips by faction

## Build
- Build artifact (`.gb`) is generated from source.
- Do not edit ROM binary directly.
- Commands:
  - make clean
  - make

## Xbox Series Controller Compatibility
Via emulator mapping:
- Xbox A -> GB A
- Xbox B -> GB B
- D-Pad -> GB D-Pad
- View -> Cycle Special
- Menu/Start -> GB Start

## Credits
Developed by the Carell brothers.
Built with GBDK and original parody assets.
'@

$fullContext = @'
TOMMY GOOMBA - FULL CONTEXT

Project: parody puzzle-RPG marriage rescue game for Game Boy.
Player: Tommy, searching across 66 stages to recover his wife.
Core systems: movement, search, encounter resolution, combat, save persistence.

Combat:
- A = Bite
- B = selected special
- Starts with Charged Dash
- View button (emulator mapped) cycles specials

Boss progression:
- Fortress Tyrant -> Shell Guard
- Jungle Giant -> Primal Toss
- Mirage Duelist -> Egg Arc
- Vault Brute -> Greed Rush
- Trickster Duelist -> Chaos Spin
- Hex Mage -> Counter Sigil
- Phantom Lord -> Phase Step

World simulation:
- NPC migration per world tick
- faction-aware movement
- stage co-location determines encounter composition
- save file records key outcomes and completion

EgoSphere integration target:
- state store
- route weighting
- event bus
- narrative flag persistence
'@

$loreBible = @'
TOMMY GOOMBA - LORE BIBLE

World Premise:
A fractured kingdom where old rivalries, fortress rule, carnival zones, and spectral districts overlap.

Factions:
1) Homebound Civilians
2) Brother Syndicate
3) Recurring Cousin Cell
4) Fortress Court
5) Jungle Barrel Guild
6) Mirage Performers
7) Hex Circle
8) Spectral Court

Event Types:
- Siege Event
- Migration Wave
- Duel Event
- Rift Event
- Reunion Window

Progression Philosophy:
Boss encounters are political and traversal gates, not just combat checks.
Defeats and alliances alter future route pressure and encounter probability.
'@

$assetReqs = @'
TOMMY GOOMBA - ASSET REQUIREMENTS

GRAPHICS
- Tilesets: overworld, interior, puzzle
- Sprites: Tommy, wife, brothers, recurring rivals, bosses, civilians
- Effects: dash trail, impacts, shield pulse, projectile arcs, ghost fades
- UI: title, menu, save, HUD, encounter banners
- Cinematics: intro cards, boss cards, reunion variants

AUDIO
- Music: title, intro, region loops, combat, boss variants, ending
- SFX: bite, dash, hit/block, menu, puzzle triggers, ambience
- Optional: dialogue text blips by faction

TECHNICAL
- DMG-safe contrast
- tile reuse optimization
- bank-aware packing
- source-driven ROM build only
- original parody assets only (no ripped copyrighted content)
'@

# Write files
Set-Content -Path (Join-Path $projectRoot "README.md") -Value $readmeCombined -Encoding utf8
Set-Content -Path (Join-Path $projectRoot "README_full_context.txt") -Value $fullContext -Encoding utf8
Set-Content -Path (Join-Path $projectRoot "lore_bible.txt") -Value $loreBible -Encoding utf8
Set-Content -Path (Join-Path $projectRoot "asset_requirements.txt") -Value $assetReqs -Encoding utf8

Write-Host "Done. Generated:"
Write-Host " - README.md"
Write-Host " - README_full_context.txt"
Write-Host " - lore_bible.txt"
Write-Host " - asset_requirements.txt"