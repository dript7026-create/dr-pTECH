#include "genetics.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "state.h"
#include "password.h"
#include <gba.h>

// Very small prototype genome table
static const char* genome_names[] = {
    "Human-Rooted",
    "Harbor-Adapted",
    "Ash-Lattice",
    "Mangrove-Braider"
};

// For simplicity, each growth tier maps to a variant id (same as tier here)
int apply_growth_nano(Entity* e) {
    if (!e) return -1;
    // Base growth behavior
    if (e->growth_tier < 3) {
        e->growth_tier++;
    }

    // Vibrational signature can bias growth to produce larger variants
    if (e->vib_signature > 128 && e->growth_tier < 4) {
        // small chance for an extra tier
        e->growth_tier++;
    }

    // Update variant mapping (variant influenced by tier and vibration)
    int shift = compute_mutational_shift(e, (int)e->vib_signature);
    int var = (int)e->growth_tier + shift;
    if (var < 0) var = 0;
    if (var > 5) var = 5;
    e->variant = (uint8_t)var;
    return e->growth_tier;
}

const char* get_variant_name(const Entity* e) {
    if (!e) return "<null>";
    uint8_t gid = e->genome_id;
    if (gid >= (sizeof(genome_names)/sizeof(genome_names[0]))) gid = 0;
    static char buf[64];
    snprintf(buf, sizeof(buf), "%s - variant %u (tier %u) vib=%u", genome_names[gid], e->variant, e->growth_tier, e->vib_signature);
    return buf;
}

// Compute a signed mutational shift in range [-2,2]
int compute_mutational_shift(const Entity* e, int vibration_level) {
    if (!e) return 0;
    // Deterministic pseudo-random mix of state
    unsigned seed = (unsigned)(vibration_level * 1103515245u + e->genome_id * 1664525u + e->growth_tier);
    // Simple xorshift
    seed ^= (seed << 13);
    seed ^= (seed >> 17);
    seed ^= (seed << 5);
    int r = (int)(seed & 0x7FFFFFFF);
    // Map into -2..2 biased by vibration_level magnitude
    int bias = vibration_level / 100; // 0..2++
    int val = (r % 5) - 2; // -2..2
    // Apply bias towards positive shifts when vibration_level is high
    if (bias > 0) {
        val += bias;
    }
    if (val > 2) val = 2;
    if (val < -2) val = -2;
    return val;
}

void apply_vibrational_affectation(Entity* e, int vibration_level) {
    if (!e) return;
    if (vibration_level <= 0) return;

    // Accumulate into vib_signature with saturation
    int acc = (int)e->vib_signature + vibration_level / 2;
    if (acc > 255) acc = 255;
    e->vib_signature = (uint8_t)acc;

    // Compute mutational shift and apply to variant
    int shift = compute_mutational_shift(e, vibration_level);
    int new_variant = (int)e->variant + shift;
    if (new_variant < 0) new_variant = 0;
    if (new_variant > 7) new_variant = 7;
    e->variant = (uint8_t)new_variant;

    // If signature crosses extreme threshold, mutate genome_id (coarse mutation)
    if (e->vib_signature > 220) {
        uint8_t genome_count = (uint8_t)(sizeof(genome_names)/sizeof(genome_names[0]));
        e->genome_id = (e->genome_id + 1) % genome_count;
        // reset signature slightly after a major mutation
        e->vib_signature = 64;
    }
}

// Deposit nanocells onto the entity
void deposit_nanocells(Entity* e, int amount, int polarity, int duration_ms) {
    if (!e) return;
    if (amount <= 0) return;
    if (polarity >= 0) e->pending_nanocell_polarity = 1; else e->pending_nanocell_polarity = -1;
    e->pending_nanocell_amount += (int16_t)amount;
    // extend timer
    e->pending_nanocell_timer_ms += duration_ms;

    // visual cue
    if (e->pending_nanocell_polarity > 0) e->visual_cue |= 1; // glow/benefit
    else e->visual_cue |= 2; // corrosion/malign
    iprintf("Nanocells deposited: amt=%d pol=%d dur=%dms\n", amount, e->pending_nanocell_polarity, duration_ms);
}

// Regeneration and nanocell processing per tick
void genetics_tick(Entity* e, int delta_ms) {
    if (!e) return;
    // Process nanocell active period
    if (e->pending_nanocell_timer_ms > 0 && e->pending_nanocell_amount > 0) {
        int process = delta_ms; // treat as intensity per ms for prototype
        // compute vibration intensity from amount and polarity
        int vib_intensity = (e->pending_nanocell_amount * (e->pending_nanocell_polarity)) / 2;
        // apply vibrational effect scaled by delta
        apply_vibrational_affectation(e, vib_intensity);

        // gradually consume nanocells
        int consumed = (process / 100) * (e->pending_nanocell_amount > 0 ? 1 : 0);
        if (consumed <= 0) consumed = 1;
        if (consumed > e->pending_nanocell_amount) consumed = e->pending_nanocell_amount;
        e->pending_nanocell_amount -= consumed;
        e->pending_nanocell_timer_ms -= process;
        if (e->pending_nanocell_amount <= 0 || e->pending_nanocell_timer_ms <= 0) {
            // clear visual cues
            e->pending_nanocell_amount = 0;
            e->pending_nanocell_timer_ms = 0;
            e->pending_nanocell_polarity = 0;
            e->visual_cue &= ~(1|2);
            iprintf("Nanocell activity ended\n");
        }
    }

    // Cellular regrowth (HP regen). Regenerate scaled by genetic growth_tier
    if (e->hp < e->max_hp && e->regen_rate > 0) {
        // Calc regen per ms = regen_rate / 1000 * (1 + growth_tier*0.25)
        float scale = 1.0f + (e->growth_tier * 0.25f);
        int heal = (int)((e->regen_rate * scale) * ((float)delta_ms / 1000.0f));
        if (heal <= 0) heal = 1;
        e->hp += heal;
        if (e->hp > e->max_hp) e->hp = e->max_hp;
    }

    // Check combo unlocks when variant/tier changes
    genetics_check_combo_unlocks(e);
}

// Simple combo unlock mapping
void genetics_check_combo_unlocks(Entity* e) {
    if (!e) return;
    // Example: unlock combo 0 when genome 2 reaches variant >= 3 and tier >=2
    if (e->genome_id == 2 && e->variant >= 3 && e->growth_tier >= 2) {
        state_set_cleared(  /* reuse cleared bitfield for combos? better add dedicated function */  16 );
        // For prototype we mark boss bit 16 as combo unlocked indicator
        iprintf("Combo unlock condition met for genome=%u variant=%u tier=%u\n", e->genome_id, e->variant, e->growth_tier);
    }
}
