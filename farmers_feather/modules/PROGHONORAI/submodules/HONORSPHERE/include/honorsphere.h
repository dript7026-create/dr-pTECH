#ifndef HONORSPHERE_H
#define HONORSPHERE_H

#include <stdint.h>

typedef struct {
    uint8_t respect;
    uint8_t tension;
    uint8_t pressure;
    uint8_t channel_bias;
} HonorSphereNode;

uint8_t honorsphere_score(const HonorSphereNode *node, uint8_t passage_id, uint8_t threat, uint8_t tier);
int8_t honorsphere_signed_delta(uint8_t score, uint8_t ceiling);

#endif