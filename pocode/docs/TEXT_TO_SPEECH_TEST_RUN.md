# Pocode Test Run: Text To Speech App

This is a concrete test-run artifact for the current Pocode campaign compiler using the request below.

## Request

- project idea: `An app for text to speech`
- language: `Python`
- learner level: `starter`
- session length: `20 minutes`
- seed word: `SPEAKTONE`

## Compiler Interpretation

The current compiler would classify this request into these feature intents:

1. `User Input`
2. `Readable Output`
3. `Program Rules`
4. `Text Processing`
5. `Speech Synthesis Output`
6. `Voice Settings`
7. `Utterance History`

That leads to a concept graph centered on:

1. Variables and values
2. Input and output
3. Conditions and branching
4. Loops and repeated tasks
5. Functions and reusable actions
6. Persistence and saved state
7. Text cleanup and normalization
8. Platform audio and speech APIs
9. Configuration and voice controls
10. History and saved phrases
11. Debugging and assembly

## Expected Lesson Campaign

With the current lesson chunking rules, the request becomes a fast campaign like this:

1. Variables and values
2. Input and output
3. Conditions and branching + Loops and repeated tasks
4. Functions and reusable actions + Persistence and saved state
5. Text cleanup and normalization + Platform audio and speech APIs
6. Configuration and voice controls + History and saved phrases
7. Debugging and assembly

Later lessons become more cryptic and more mixed-concept by design.

## Seeded Map Shape

The map is deterministic from the request and seed word. For `SPEAKTONE`, the current seeded route should be understood as a project-specific corridor with lesson nodes, reward caches, and restorative side stops.

Representative map flow:

1. Lesson: Variables and values
2. Reward Cache: Floppy Cache
3. Lesson: Input and output
4. Rest Stop: Hot Bath Stop
5. Boss Lesson: Conditions and branching + Loops and repeated tasks
6. Lesson: Functions and reusable actions + Persistence and saved state
7. Reward Cache: Floppy Cache
8. Lesson: Text cleanup and normalization + Platform audio and speech APIs
9. Rest Stop: CRT Lounge
10. Boss Lesson: Configuration and voice controls + History and saved phrases
11. Final Boss Lesson: Debugging and assembly

The exact rest/reward placement depends on the seeded hash stream, but the route remains stable for the same request and seed combination.

## Example Mini-Game Pressure

Early lesson example:

- prompt style: direct clue
- distractors: obvious bad behavior
- hinting: explicit

Late lesson example for platform speech playback:

- prompt style: indirect description of app behavior
- distractors: plausible but subtly wrong state transitions
- hinting: reduced
- remediation: if the player misses a speech-API or voice-config concept, the next lesson instance inserts one or more reinforcement identify/match rounds with a clearer clue set

## Adaptive Remediation Behavior

If the player repeatedly misses `platform_audio` or `config`:

1. the mistake ledger increments for that concept
2. the next lesson instance inserts reinforcement prompts for that concept
3. obscurity tier is lowered for those reinforcement prompts
4. if the player uses a hot bath, pacing and ambiguity soften temporarily for nearby lessons

That gives the TTS campaign a loop that does not just test recall. It corrects weaknesses by repeating targeted learning opportunities until the concept is stabilized.