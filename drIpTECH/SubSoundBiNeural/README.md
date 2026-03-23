SubSoundBiNeural

Purpose
- Procedural audio prototype focused on binaural-ish ambience, sub-frequency beds, and one-shot SFX generation.
- Intended as a standalone synthesis utility with hooks for richer external generators.

Files
- SubSoundBiNeural.c: standalone C implementation with WAV export and GBA-safe fallback profile.

What It Does Now
- Generates rainforest bed ambience.
- Generates bite-impact one-shot SFX.
- Generates a GBA-safe menu downmix example.
- Exposes a callback hook for external generators or AI-driven synthesis layers.

Practical Constraint
- Real-time high-fidelity binaural surround is not feasible on original GBA hardware.
- For TommyBeta on GBA, the intended path is offline generation plus low-rate downmixes.
- For richer engines, keep the full stereo synthesis path and integrate through the external callback bridge.

Build Example
gcc SubSoundBiNeural.c -o SubSoundBiNeural -lm

Output Files
- SubSoundBiNeural_forest_bed.wav
- SubSoundBiNeural_bite_impact.wav
- SubSoundBiNeural_gba_menu_downmix.wav