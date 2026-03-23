#ifndef URBDEN_GENERATOR_H
#define URBDEN_GENERATOR_H

#include <stdint.h>

void generator_seed_from_string(const char* seed);
uint32_t generator_next_u32();
int generator_range(int min, int max);

#endif
