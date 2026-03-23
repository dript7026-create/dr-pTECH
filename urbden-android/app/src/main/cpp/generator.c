#include "generator.h"
#include <string.h>

// Simple deterministic PRNG seeded from string (xorshift32)
static uint32_t g_state = 0x811C9DC5u;

void generator_seed_from_string(const char* seed) {
    if (!seed) { g_state = 0x811C9DC5u; return; }
    uint32_t h = 2166136261u;
    for (size_t i = 0; seed[i]; ++i) {
        h ^= (unsigned char)seed[i];
        h *= 16777619u;
    }
    g_state = h ? h : 0x811C9DC5u;
}

uint32_t generator_next_u32() {
    uint32_t x = g_state;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    g_state = x;
    return x;
}

int generator_range(int min, int max) {
    if (max <= min) return min;
    uint32_t r = generator_next_u32();
    return min + (int)(r % (uint32_t)(max - min + 1));
}
