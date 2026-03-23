#pragma once
#include "genetics.h"

// Initialize UI systems and load placeholder assets
void ui_init(void);

// Draw HUD for the given entity (player). Prototype: uses console + palette cues.
void ui_draw_hud(const Entity* e);

// Update visual effects (call each frame)
void ui_update(int delta_ms);
