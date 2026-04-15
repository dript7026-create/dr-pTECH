#include "password.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void gorge_password_encode(char *out, int out_size, uint32_t cleared_mask, uint32_t reward_mask) {
    if (!out || out_size < 17) {
        return;
    }
    snprintf(out, out_size, "%08lX%08lX", (unsigned long)cleared_mask, (unsigned long)reward_mask);
}

int gorge_password_decode(const char *pwd, uint32_t *out_cleared_mask, uint32_t *out_reward_mask) {
    char tmp[9];
    unsigned long cleared;
    unsigned long rewards;
    if (!pwd || strlen(pwd) < 16u) {
        return -1;
    }
    tmp[8] = '\0';
    memcpy(tmp, pwd, 8u);
    cleared = strtoul(tmp, 0, 16);
    memcpy(tmp, pwd + 8, 8u);
    rewards = strtoul(tmp, 0, 16);
    if (out_cleared_mask) {
        *out_cleared_mask = (uint32_t)cleared;
    }
    if (out_reward_mask) {
        *out_reward_mask = (uint32_t)rewards;
    }
    return 0;
}