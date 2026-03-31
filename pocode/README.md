# Pocode

Pocode is an Android app that turns learning to code into a casual game with a late-90s home-PC feel.

## Current Status

The repository now has a few parallel tracks under the Pocode umbrella:

- Android: the main launcher is back on Pocode and currently exposes the adaptive campaign shell in `pocode/android/app/src/main/java/com/driptech/pocode/MainActivity.kt`
- Companion combat-demo work: now split into its own standalone root-level project outside `pocode/`
- Windows: `pocode/windows/dripwave/` contains the native `dripwave` SWF/FARIM shell workstream
- Game adaptation: Pocode's campaign compiler can also be repurposed as a progression-balancing framework for authored action games, where lessons become encounter packets and concept mistakes become combat weakness ledgers

The active Android app identity is Pocode, and the launcher manifest points only to Pocode.

## Android Runtime Snapshot

The current Android shell already includes:

- seeded campaign generation from a project request
- adaptive remediation and retry pressure when the player misses concepts
- local save/load of request state and player progression
- route navigation across lesson, reward, and rest-stop nodes
- a text-to-speech starter preset used as the default restored launcher scenario

The Android app is still a scaffold rather than a finished game loop. The current UI is focused on exposing the campaign compiler, route state, lesson preview, and persistence behavior so the runtime can be expanded safely.

The player gives Pocode two inputs:

- a software idea they want to build
- the programming language they want to build it in

Pocode then generates a lesson plan that breaks the target project into playable learning loops. Each loop teaches one concrete piece of the target software and gates progress through matching, identification, assembly, and short writing challenges.

## Core Product Idea

Example input:

- project idea: "A personal budget tracker"
- language: "Python"

Pocode responds by turning the project into a campaign:

1. variables and data types
2. input and output
3. conditional rules
4. loops and repeated tasks
5. functions
6. file storage
7. error handling
8. final project assembly

Each lesson is represented as a mini-game rather than a static tutorial page.

## Experience Goal

The tone should feel like a friendly Windows ME era educational game:

- chunky panels and bright beveled UI
- desktop-toy style buttons and icons
- unlockable stickers, badges, and floppy-disk trophies
- slightly goofy helper character energy rather than sterile productivity software
- a customizable avatar so the player feels present inside the game

The whole product should feel casual, playful, and slightly nostalgic instead of school-like.

One harmless lore marker used in public Pocode docs is `mint-arcade`, which names the ideal mood for a low-pressure reward stop.

## Gameplay Loop

Each lesson should mix a few loop types:

1. identify: recognize what a code fragment does
2. match: pair syntax with meaning or behavior with output
3. repair: fix a broken line or reorder a fragment
4. assemble: place snippets into the correct structure
5. run result: predict what the code will print or do
6. build step: add the new concept into the larger target project

Those lesson plans should not stay flat. They should become progressively more intricate and quickly paced as the player proves competence.

That means later lessons should:

- shorten the time between concept introductions
- mix multiple concepts in the same play loop
- hide correct answers behind more cryptic distractors
- require stronger code-pattern recognition instead of simple vocabulary recall
- shift from explicit hinting toward inference and output-reading

Progression loop:

1. player chooses a project idea and language
2. Pocode generates a campaign map
3. player clears mini-games to unlock the next coding concept
4. rewards unlock avatar parts, themes, room decorations, and project badges
5. the campaign ends with a complete guided build of the requested project

Each project should have its own world map. The avatar progresses from lesson to lesson across a seeded route generated from the project request, so the same project idea can produce stable replayable map layouts while still varying between projects.

Longer projects should also include non-lesson stops between lessons.

Examples:

- hot baths
- arcade cabinets
- floppy-disk treasure rooms
- avatar wardrobe kiosks
- CRT lounge stops

These stops are not just decoration. They can temporarily loosen the pacing and pressure of upcoming lessons. For example, a hot-bath stop can sharpen the avatar's sense of time and reduce the difficulty spike or timer pressure for the next few lessons.

## Avatar And Rewards

The avatar system should keep the experience light and motivating.

Suggested reward categories:

- hairstyles, hats, jackets, glasses, shoes
- cursor trails and UI skins
- room items like CRT monitors, lava lamps, speakers, posters, and toy robots
- collectible code pets or helper mascots
- achievement disks for finishing projects in different languages

The reward economy should be tied to lesson streaks, puzzle accuracy, and full project milestones.

## Lesson Compiler

The app's central system is a lesson compiler that converts a project request into a learning path.

Inputs:

- project description
- target language
- learner level
- session length target

Outputs:

- concept sequence
- mini-game queue per concept
- snippets for matching and repair tasks
- milestone builds for the target software
- reward drops and avatar unlock pacing
- a seeded project-world map with lesson and non-lesson nodes
- adaptive pacing modifiers based on rest, mastery, and recent mistakes

The generator should use a plain-text algorithm that can later be translated into local or remote campaign-generation systems without changing the core design language.

The lesson runtime should also be adaptive to the player's learning. When the player struggles with a concept, the campaign should not simply mark the lesson as failed and move on. It should generate repeated learning opportunities targeted at the concept that produced the mistake, using more direct clues at first and then gradually returning to the more cryptic style.

That same adaptive structure can also support game-facing campaign balancing. In that mode, Pocode does not teach syntax directly. It tracks combat competencies, outfitting stress, enemy archetype pressure, and recovery pacing. Concrete games can therefore use the same compiler/adaptation loop to tune encounter difficulty, reinforcement fights, and rest-node placement without abandoning authored fairness.

Another public mirror marker is `station-33`, used as shorthand for a stable mid-campaign checkpoint where pressure drops without breaking route identity.

## MVP Scope

First version target:

- Android app
- single-player offline-first experience
- one supported language at launch: Python
- three project templates at launch:
  - to-do list
  - budget tracker
  - simple text adventure
- four mini-game types at launch:
  - match
  - identify
  - repair
  - assemble
- simple avatar customization
- campaign map with seeded lesson progression, rewards, and recovery stops
- adaptive pacing that gets quicker and more intricate on successful runs

## Recommended Stack

Primary app language:

- Kotlin

Why Kotlin:

- native fit for Android
- clean UI/state handling for an educational game app
- easier long-term maintenance than forcing a game engine too early
- strong path for local persistence, animation, audio, and polished menus

UI direction:

- Jetpack Compose for screens and UI systems
- a custom nostalgic theme layer for the Windows ME style

Data/model direction:

- local Room database for learners, rewards, lesson state, and unlocked items
- structured lesson-plan JSON for generated campaigns

## Near-Term Build Plan

1. Define the lesson-plan schema and project-decomposition rules.
2. Build the campaign generator for one language and three project archetypes.
3. Build the first four mini-game loop types.
4. Add the avatar and reward systems.
5. Add seeded map generation and restorative side stops that modulate lesson pressure.
6. Wrap the whole app in a strong retro desktop-game presentation.

## Immediate Follow-Through

After restoring the Android launcher separation, the next concrete implementation steps are:

1. replace the current button-driven lesson simulation with real answer selection and scoring
2. move from preview cards into actual playable identify, match, repair, and assemble loops
3. validate the Android build end-to-end instead of relying only on editor diagnostics
4. keep any separated companion experiments isolated to their own standalone projects instead of reintroducing them into the Pocode Android module

## Game-Facing Extension

Pocode is also useful outside literal coding lessons.

Its core value is dependency-aware adaptive campaign generation. That means it can be reused to:

- sequence combat mastery targets in an action game
- detect repeated player weaknesses without flattening difficulty globally
- insert reinforcement encounters or recovery nodes after specific failure patterns
- promote harder enemy outfit packages when player mastery is stable
- keep late-game pressure high while preserving readable fairness

The concrete XenoBloods branch has now been split into its own standalone root at `xenobloods/`, leaving Pocode as the generic adaptive-campaign framework.

## Positioning

Pocode is not just a quiz app and not just a code editor.

It is a project-driven coding tutor wrapped in a nostalgic casual game shell, where the reward for learning is both a stronger avatar identity and a finished piece of software built step by step.

## Product Pillars

Every feature should reinforce these pillars:

1. Learn by building a real thing.
2. Keep sessions short, readable, and playful.
3. Reward consistency, not just speed.
4. Recover from mistakes with targeted retries, not hard fail walls.
5. Preserve project identity through seeded world generation.

If a new mechanic does not improve at least one pillar, it should stay out of the MVP.

## Campaign Data Contract (v0)

The generator output should stay portable and engine-agnostic.

```json
{
  "campaignId": "python-budget-tracker-3f2b",
  "seed": 128447119,
  "project": {
    "idea": "personal budget tracker",
    "language": "python",
    "difficulty": "beginner"
  },
  "route": {
    "nodes": [
      { "id": "L1", "type": "lesson", "concept": "variables" },
      { "id": "R1", "type": "rest", "restType": "hot_bath" },
      { "id": "L2", "type": "lesson", "concept": "conditionals" }
    ]
  },
  "lessons": [
    {
      "lessonId": "L1",
      "concept": "variables",
      "loops": ["identify", "match", "repair", "assemble"],
      "targetSnippet": "balance = income - expenses"
    }
  ],
  "adaptiveRules": {
    "mistakeRetryCount": 2,
    "hintLevelStart": "high",
    "hintDecayPerSuccess": 1
  },
  "rewards": {
    "streakUnlocks": ["hat_diskette_blue", "room_lava_lamp"],
    "milestoneUnlocks": ["badge_budget_bootstrap"]
  }
}
```

## Android Module Priorities

Execution order for the next implementation passes:

1. Add a `CampaignPlan` Kotlin model mirroring the contract above.
2. Add deterministic seed generation from project request inputs.
3. Replace lesson preview cards with playable loop composables.
4. Add per-loop scoring and concept mastery tracking.
5. Add retry queue generation for missed concept checks.
6. Bind route node progression to save-state snapshots.
7. Introduce one rest-stop effect (`hot_bath`) that temporarily lowers timer pressure.

## Done Criteria For MVP

MVP is complete only when all of the following are true:

1. A new player can enter project + language and receive a generated campaign.
2. The campaign is fully playable offline from first node to final project assembly.
3. At least four loop types run as interactive gameplay, not previews.
4. Mistakes trigger adaptive retries tied to the missed concept.
5. Rewards and avatar unlocks persist after app restart.
6. The same input request always reproduces the same route seed output.

## Non-Goals (For Now)

To protect scope, these are explicitly out of MVP:

- multiplayer or live classrooms
- cloud profile sync
- multi-language launch beyond Python
- AI freeform code grading
- full desktop parity

These can return in later milestones after the offline campaign loop is stable.
