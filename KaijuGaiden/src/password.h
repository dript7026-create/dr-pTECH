#ifndef KAJ_PASSWORD_H
#define KAJ_PASSWORD_H

#include <stdint.h>

// Encode current state into a password string. out must be >= 17 chars.
void encode_password(char* out, int out_size, uint32_t cleared_bosses, uint32_t cyphers);

// Decode password string into cleared_bosses and cyphers. Returns 0 on success.
int decode_password(const char* pwd, uint32_t* out_cleared_bosses, uint32_t* out_cyphers);

#endif // KAJ_PASSWORD_H
