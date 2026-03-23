#ifndef KAJ_GENETICS_H
#define KAJ_GENETICS_H

#include <stdint.h>

typedef struct Entity {
    uint8_t genome_id;    // index into genome table
    uint8_t growth_tier;  // 0..N
    uint8_t variant;      // visual/moveset variant index
    uint8_t vib_signature; // accumulated vibrational affectation (0-255)
    // Health + regen for cellular regrowth
    uint16_t hp;
    uint16_t max_hp;
    uint8_t regen_rate; // HP per second base

    // Pending nanocell effect state
    int16_t pending_nanocell_amount; // positive integer units
    int8_t pending_nanocell_polarity; // +1 benevolent, -1 malignant, 0 none
    int pending_nanocell_timer_ms; // remaining effect time in ms

    uint8_t visual_cue; // bitflags for debug/visual effects
} Entity;

// Apply one Growth NanoCell to entity (increments growth meter, returns new tier)
int apply_growth_nano(Entity* e);

// Apply vibrational affectation at an (atomic-scale) intensity level.
// vibration_level: arbitrary units; positive integers. Higher values increase
// the chance of mutational shifts and can eventually alter genome_id.
void apply_vibrational_affectation(Entity* e, int vibration_level);

// Compute a signed mutational shift (-2..+2) derived from entity state and vibration.
int compute_mutational_shift(const Entity* e, int vibration_level);

// Deposit nanocells onto an entity. amount: units. polarity: +1 benevolent, -1 malignant.
// duration_ms: how long the nanocells remain active.
void deposit_nanocells(Entity* e, int amount, int polarity, int duration_ms);

// Tick/update genetics over time (delta_ms milliseconds). Handles ongoing nanocell
// vibration processing, growth over time, and cellular regrowth.
void genetics_tick(Entity* e, int delta_ms);

// Check for combo unlocks based on current genetic path; will set global state.
void genetics_check_combo_unlocks(Entity* e);

// Query variant string for debug/console
const char* get_variant_name(const Entity* e);

#endif // KAJ_GENETICS_H
