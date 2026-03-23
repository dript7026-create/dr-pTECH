# egosphere Client Presentation Script

Use this as the short live-talk outline when presenting the package.

## 30-Second Framing

egosphere is the product.

It has two linked surfaces:

1. a reusable gameplay cognition runtime in C;
2. a deterministic bundle-generation pipeline for downstream art and engine tooling.

The package is designed to let the client review those two surfaces quickly without needing a live code walkthrough first.

## What To Say First

1. The core product is not the Pertinence Tribunal example.
2. Pertinence Tribunal is the scaled validation example included to prove the pipeline and package structure can carry a larger content set.
3. The Android APK is a review companion app that carries the package documents, not a runtime port of egosphere.

## Fast Walkthrough Order

1. `HANDOFF_NOTE.md`
2. `CLIENT_EXEC_SUMMARY.md`
3. `PRODUCT_BRIEF.md`
4. `REVIEW_GUIDE.md`
5. `VALIDATION_SNAPSHOT.json`
6. `PACKAGE_MANIFEST.json`

If the client wants something tangible on a phone, use the packaged review APK rather than improvising a fresh build during the meeting.

## If The Client Asks “What Is Actually Proven?”

Say:

- the core runtime smoke path passed;
- the sample pipeline validation passed;
- the Pertinence Tribunal end-to-end validation passed;
- the package includes the generated outputs that correspond to those checks.

## If The Client Asks “What Is Not Claimed Yet?”

Say:

- this package is not production signoff;
- the APK is not the runtime itself;
- the repository snapshot validates emitted bundles and dry-run tooling, not a finished end-user game.

## Recommended Close

Ask the client which of these they want to evaluate next:

1. runtime integration value across projects;
2. generated pipeline output credibility;
3. readiness path from technical package to stronger production-facing preview.
