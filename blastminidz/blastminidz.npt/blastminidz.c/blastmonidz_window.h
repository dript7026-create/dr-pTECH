#ifndef BLASTMONIDZ_WINDOW_H
#define BLASTMONIDZ_WINDOW_H

#include "blastmonidz.h"

int blastmonidz_window_init(void);
void blastmonidz_window_shutdown(void);
void blastmonidz_window_pump(void);
int blastmonidz_window_pop_input(void);
int blastmonidz_window_should_close(void);
void blastmonidz_window_reset_close_request(void);
void blastmonidz_window_present_title(void);
void blastmonidz_window_present_lore(void);
void blastmonidz_window_present_archive(void);
void blastmonidz_window_present_starter_draw(const GameState *state);
void blastmonidz_window_present_arena(const GameState *state);
void blastmonidz_window_present_summary(const GameState *state);

#endif