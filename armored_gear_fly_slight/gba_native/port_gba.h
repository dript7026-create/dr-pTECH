#ifndef PORT_GBA_H
#define PORT_GBA_H

#include <gba_input.h>
#include <stdint.h>

typedef struct PortInputState {
    uint16_t held;
    uint16_t pressed;
    uint16_t released;
} PortInputState;

void port_gba_init(void);
void port_gba_wait_vblank(void);
void port_gba_poll_input(PortInputState *input);
void port_gba_audio_init(void);
void port_gba_audio_step(uint16_t frame, uint8_t pressure);
void port_gba_audio_fire(uint8_t weapon_rank);
void port_gba_audio_dash(void);
void port_gba_audio_spawn(uint8_t threat_rank);
void port_gba_audio_hit(uint8_t defeated);
volatile uint16_t *port_gba_get_draw_buffer(void);
void port_gba_present(void);

#endif