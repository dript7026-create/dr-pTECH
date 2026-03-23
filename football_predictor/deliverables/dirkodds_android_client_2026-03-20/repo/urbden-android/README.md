# DirkOdds Mobile Android Client

## Overview

- This project packages a synthetic DirkOdds Android client for client-ready prediction testing.
- The app focuses on anonymous multi-sport match simulation, not real teams, leagues, or player identities.
- It provides a 3D playback surface, fictional match scenarios, lightweight coaching interactions, and reflex-based QTE prompts to help users pressure-test prediction calls in motion.

## Current Mobile Features

- Fictional football, basketball, and baseball scenario deck
- Prediction lane selection before kickoff / tip / first pitch
- Real-time 3D OpenGL ES playback with abstract standee actors
- Anonymous team styling with non-identifying procedural textures
- Live momentum, control, reflex, pressure, and prediction-edge HUD bars
- Subtle coaching interactions: pulse pick, set shape, reflex tap
- Sport-specific field presentation for football, basketball, and baseball

## Android Identity

- App label: `DirkOdds Mobile`
- Application ID: `com.driptech.dirkodds.mobile.preview`
- Namespace: `com.urbden.game`
- Current version: `0.9-mobile-preview`

## Build Prerequisites

1. JDK 17 or newer.
2. Android SDK packages for API 35.
3. Gradle 8.7 or newer.

## Local Bootstrap Used In This Workspace

1. JDK installed under `../.jdk/jdk-17.0.16/`.
2. Android SDK installed under `../.android-bootstrap/android-sdk/` or `../android-bootstrap/android-sdk/`.
3. Gradle installed under the newest `../.android-bootstrap/gradle-*/` or `../android-bootstrap/gradle-*/` folder.
4. `local.properties` points the project at the local SDK.

## Build Command Used Successfully

1. Set `JAVA_HOME` to the local JDK.
2. Set `ANDROID_HOME` and `ANDROID_SDK_ROOT` to the local SDK.
3. Run `gradle.bat assembleRelease` from this folder using the bootstrapped Gradle binary.

## Generated Artifact

- `app/build/outputs/apk/release/app-release.apk`

## Interaction Model

- Users select a fictional scenario and prediction lane before entering playback.
- The match then unfolds in real time with anonymous 3D actors and a live HUD.
- `Pulse Pick` pressures the chosen forecast lane.
- `Set Shape` stabilizes control and slows match volatility.
- `Reflex Tap` rewards timely responses to subtle live-cue windows.

## Data / Identity Guardrails

- No real leagues, franchises, player names, or player likenesses are packaged in this mobile preview.
- Team identities, venues, and visual assets are synthetic and intentionally non-descriptive.
- The simulator is intended for interaction testing and prediction workflow review, not guaranteed forecasting or regulated deployment.

## Limitations

- This build is a client-ready preview, not a final licensed production release.
- Prediction inputs are synthetic scenario baselines rather than live regulated sports feeds.
- The release build variant is signed with the Android debug keystore for direct review installs, not production store distribution.
