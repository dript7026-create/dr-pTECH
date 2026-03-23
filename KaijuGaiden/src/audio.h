#pragma once

// Prototype audio API (stubs for GBA builds). Replace with actual audio engine later.
void audio_init(void);
void audio_play_bgm(const char* name);
void audio_play_sfx(const char* name);
