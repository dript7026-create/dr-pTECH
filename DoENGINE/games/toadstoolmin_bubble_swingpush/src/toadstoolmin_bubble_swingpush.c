#include <stddef.h>

typedef struct SwingPushState {
    float bubble_charge;
    float swing_arc;
    float push_force;
    int airborne;
    unsigned int ticks;
} SwingPushState;

static SwingPushState g_swingpush_state = {0.0f, 0.0f, 0.0f, 0, 0U};

const char* dodo_game_id(void) {
    return "toadstoolmin-bubble-swingpush";
}

const char* dodo_game_title(void) {
    return "toadstoolmin bubble SWINGPUSH";
}

const char* dodo_game_tagline(void) {
    return "Bubble lift, swing timing, and push-force traversal inside the DODO pipeline.";
}

void dodo_game_boot(void) {
    g_swingpush_state.bubble_charge = 0.0f;
    g_swingpush_state.swing_arc = 0.0f;
    g_swingpush_state.push_force = 0.0f;
    g_swingpush_state.airborne = 0;
    g_swingpush_state.ticks = 0U;
}

void dodo_game_tick(float bubble_input, float swing_input, float push_input) {
    float next_bubble = g_swingpush_state.bubble_charge + (bubble_input * 0.08f);
    float next_swing = (g_swingpush_state.swing_arc * 0.82f) + (swing_input * 0.18f);
    float next_push = (g_swingpush_state.push_force * 0.74f) + (push_input * 0.26f);

    if (next_bubble < 0.0f) {
        next_bubble = 0.0f;
    }
    if (next_bubble > 1.0f) {
        next_bubble = 1.0f;
    }
    if (next_swing < -1.0f) {
        next_swing = -1.0f;
    }
    if (next_swing > 1.0f) {
        next_swing = 1.0f;
    }
    if (next_push < 0.0f) {
        next_push = 0.0f;
    }
    if (next_push > 1.0f) {
        next_push = 1.0f;
    }

    g_swingpush_state.bubble_charge = next_bubble;
    g_swingpush_state.swing_arc = next_swing;
    g_swingpush_state.push_force = next_push;
    g_swingpush_state.airborne = (next_bubble > 0.55f || next_push > 0.68f) ? 1 : 0;
    g_swingpush_state.ticks += 1U;
}

const SwingPushState* dodo_game_state(void) {
    return &g_swingpush_state;
}