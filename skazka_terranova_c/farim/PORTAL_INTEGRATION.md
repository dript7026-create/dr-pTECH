# FARIM Portal Integration Notes

This document describes the current integration shape for shipping a `FARIM` package through a browser-based media hub or a portal-style web submission flow.

## Current Delivery Model

The current browser integration is:

- `player/index.html`: browser FARIM player shell
- `player/player.js`: package loader and renderer
- `player/styles.css`: presentation layer
- `../../build/skazka_terranova_demo.farim`: demo content package

The browser runtime is intended to be hosted over HTTP(S). It should not be treated as a plugin or browser-extension model.

## Newgrounds-Friendly Shape

For a portal like Newgrounds, the low-friction approach is:

1. Host the FARIM player page as the portal submission entry page.
2. Host the `.farim` package beside it.
3. Load the package with a query parameter such as:

```text
player/index.html?src=../../build/skazka_terranova_demo.farim
```

4. Keep all portal-facing controls inside the HTML player surface.

## Recommended Submission Structure

- `index.html`
- `player.js`
- `styles.css`
- `skazka_terranova_demo.farim`

If a portal requires a single entry HTML file, `index.html` should remain the entry point and fetch the `.farim` package asynchronously.

## Runtime API Direction

The current FARIM browser player is a reference runtime, not yet a production portal SDK.

Recommended next API surface:

- `window.FARIMPlayer.load(url)`
- `window.FARIMPlayer.pause()`
- `window.FARIMPlayer.resume()`
- `window.FARIMPlayer.setInputProfile(profile)`
- `window.FARIMPlayer.getPackageMetadata()`

Optional portal bridge methods:

- `onFarimReady`
- `onFarimError`
- `onFarimProgress`
- `onFarimAchievement`

## Limits

The current implementation does not yet provide:

- asset encryption strong enough to prevent determined extraction
- secure commercial DRM
- authoritative multiplayer or anti-cheat systems
- an official Newgrounds-side API contract

The right product framing today is:

- portable interactive media package
- browser-playable game bundle
- self-contained asset/runtime archive

not:

- tamper-proof anti-decompile format
- fully locked proprietary runtime

## Next Productization Steps

1. Add signed manifests.
2. Add package chunking and streaming.
3. Add audio and script sections.
4. Add a stricter JS runtime API.
5. Add a build command that emits a portal-ready `dist/` folder.
