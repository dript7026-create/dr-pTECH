#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include "password.h"

// Simple hex-based password: 8 hex for cleared_bosses + 8 hex for cyphers
void encode_password(char* out, int out_size, uint32_t cleared_bosses, uint32_t cyphers) {
    if (!out || out_size < 17) return;
    // produce uppercase hex string without separators
    snprintf(out, out_size, "%08lX%08lX", (unsigned long)cleared_bosses, (unsigned long)cyphers);
}

int decode_password(const char* pwd, uint32_t* out_cleared_bosses, uint32_t* out_cyphers) {
    if (!pwd || strlen(pwd) < 16) return -1;
    char tmp[9];
    tmp[8] = '\0';
    memcpy(tmp, pwd, 8);
    unsigned long cb = strtoul(tmp, NULL, 16);
    memcpy(tmp, pwd+8, 8);
    unsigned long cy = strtoul(tmp, NULL, 16);
    if (out_cleared_bosses) *out_cleared_bosses = (uint32_t)cb;
    if (out_cyphers) *out_cyphers = (uint32_t)cy;
    return 0;
}
