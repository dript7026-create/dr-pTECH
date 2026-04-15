#ifndef GORGE_PASSWORD_H
#define GORGE_PASSWORD_H

#include <stdint.h>

void gorge_password_encode(char *out, int out_size, uint32_t cleared_mask, uint32_t reward_mask);
int gorge_password_decode(const char *pwd, uint32_t *out_cleared_mask, uint32_t *out_reward_mask);

#endif
