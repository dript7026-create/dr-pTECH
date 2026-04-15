#include "../include/honorsphere.h"

static uint8_t honorsphere_clamp_u8(int16_t value) {
    if (value < 0) return 0u;
    if (value > 255) return 255u;
    return (uint8_t)value;
}

uint8_t honorsphere_score(const HonorSphereNode *node, uint8_t passage_id, uint8_t threat, uint8_t tier) {
    int16_t score;
    if (!node) return 0u;
    score = 48;
    score += node->respect / 2u;
    score += node->pressure / 3u;
    score += node->channel_bias;
    score += (int16_t)threat / 4u;
    score += (int16_t)tier * 12;
    score += (int16_t)passage_id * 7;
    score -= node->tension / 3u;
    return honorsphere_clamp_u8(score);
}

int8_t honorsphere_signed_delta(uint8_t score, uint8_t ceiling) {
    int16_t centered;
    if (ceiling == 0u) return 0;
    centered = (int16_t)score - 128;
    centered = (centered * ceiling) / 128;
    if (centered > ceiling) centered = ceiling;
    if (centered < -(int16_t)ceiling) centered = -(int16_t)ceiling;
    return (int8_t)centered;
}