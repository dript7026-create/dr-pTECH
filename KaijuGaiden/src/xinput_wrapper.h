// Minimal dynamic XInput wrapper header
#ifndef XINPUT_WRAPPER_H
#define XINPUT_WRAPPER_H

#ifdef __cplusplus
extern "C" {
#endif

// returns 0 on success
int xi_get_state(int idx, unsigned short *buttons, short *lx, short *ly, unsigned char *lt, unsigned char *rt);

#ifdef __cplusplus
}
#endif

#endif
