# Kaiju Gaiden Preference Profiling Terms Draft

Status: draft for legal review
Scope: gameplay taste and preference inference only

## Purpose

This system is intended to personalize narrative tone, cosmetic mutation selection, dialogue emphasis, and non-sensitive gameplay adaptation based on how a player plays the game.

This draft does not authorize inference of medical, psychological, addiction-related, criminal, coercion-related, or other sensitive personal traits.

## Proposed Consent Language

By enabling Preference Profiling, you allow Kaiju Gaiden to analyze your in-game actions to estimate non-sensitive play preferences such as:

- pacing preference
- aggression versus patience
- rhythm and timing preference
- resource spending preference
- spacing and control preference
- cosmetic and narrative affinity patterns

These signals may be used to:

- generate run-specific dialogue and narrative framing
- vary portraits, cosmetic mutations, and presentation details
- tailor non-sensitive gameplay flavor and encounter emphasis
- personalize local save-state flavor text and progression summaries

## Explicit Limitations

The system must not be used to infer or label:

- health status
- disability status
- sleep disorders or sleep deprivation
- drug or alcohol use
- trauma history
- abuse, captivity, or victimization status
- criminality or dangerousness
- demographic traits not explicitly provided by the player
- any legally protected or highly sensitive category

The system must not present inferred preference data as fact about the player outside the context of game behavior.

## Data Handling Rules

- Profiling must be opt-in and disabled by default.
- The baseline implementation should run locally on-device.
- No gameplay-derived preference profile may be transmitted off-device without separate explicit consent.
- Any persisted profile should be limited to non-sensitive gameplay preference vectors.
- Players must be able to reset or delete the profile.
- Players must be able to continue playing without enabling profiling.

## UX Requirements

- The enablement screen should clearly state that only gameplay taste and preference signals are analyzed.
- The game should explain what categories are inferred in plain language.
- The game should disclose whether the profile is stored, for how long, and where.
- The game should provide a visible toggle to disable profiling.

## Engineering Guardrails

- Prefer aggregate gameplay metrics over behavioral diagnosis.
- Keep feature names neutral, such as `pressure`, `rhythm`, `control`, and `resource`.
- Avoid labels that imply pathology or real-world life judgments.
- Keep narrative personalization framed as run interpretation, not personal truth.

## Activation Checklist

Before activation, confirm:

1. legal review completed
2. privacy copy approved
3. opt-in flow implemented
4. reset/delete flow implemented
5. storage and transmission behavior documented
6. sensitive inference paths removed or blocked
