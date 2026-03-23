;--------------------------------------------------------
; File Created by SDCC : free open source ISO C Compiler
; Version 4.5.1 #15267 (MINGW32)
;--------------------------------------------------------
	.module kaijugaiden
	
;--------------------------------------------------------
; Public variables in this module
;--------------------------------------------------------
	.globl _main
	.globl _set_bkg_palette
	.globl _set_sprite_data
	.globl _set_bkg_tile_xy
	.globl _set_bkg_data
	.globl _display_off
	.globl _wait_vbl_done
	.globl _joypad
	.globl _memset
;--------------------------------------------------------
; special function registers
;--------------------------------------------------------
	.area _HRAM
;--------------------------------------------------------
; ram data
;--------------------------------------------------------
	.area _DATA
_gs:
	.ds 135
;--------------------------------------------------------
; ram data
;--------------------------------------------------------
	.area _INITIALIZED
__joy_prev:
	.ds 1
__joy_cur:
	.ds 1
;--------------------------------------------------------
; absolute external ram data
;--------------------------------------------------------
	.area _DABS (ABS)
;--------------------------------------------------------
; global & static initialisations
;--------------------------------------------------------
	.area _HOME
	.area _GSINIT
	.area _GSFINAL
	.area _GSINIT
;--------------------------------------------------------
; Home
;--------------------------------------------------------
	.area _HOME
	.area _HOME
;--------------------------------------------------------
; code
;--------------------------------------------------------
	.area _CODE
;kaijugaiden.c:132: static inline void plat_poll_input(void) {
;	---------------------------------
; Function plat_poll_input
; ---------------------------------
_plat_poll_input:
;kaijugaiden.c:133: _joy_prev = _joy_cur;
	ld	a, (#__joy_cur)
	ld	(#__joy_prev),a
;kaijugaiden.c:134: _joy_cur  = joypad();
	call	_joypad
	ld	(#__joy_cur),a
;kaijugaiden.c:135: }
	ret
;kaijugaiden.c:136: static inline u8 plat_held(u8 mask)  { return (_joy_cur  & mask) ? 1 : 0; }
;	---------------------------------
; Function plat_held
; ---------------------------------
_plat_held:
	ld	hl, #__joy_cur
	and	a, (hl)
	ld	a, #0x01
	ret	NZ
	xor	a, a
	ret
;kaijugaiden.c:137: static inline u8 plat_pressed(u8 mask) {
;	---------------------------------
; Function plat_pressed
; ---------------------------------
_plat_pressed:
	ld	c, a
;kaijugaiden.c:138: return ((_joy_cur & mask) && !(_joy_prev & mask)) ? 1 : 0;
	ld	a, (#__joy_cur)
	and	a, c
	jr	Z, 00103$
	ld	a, (#__joy_prev)
	and	a, c
	ld	a, #0x01
	ret	Z
00103$:
	xor	a, a
;kaijugaiden.c:139: }
	ret
;kaijugaiden.c:140: static inline u16 plat_input_mask(void) { return (u16)_joy_cur; }
;	---------------------------------
; Function plat_input_mask
; ---------------------------------
_plat_input_mask:
	ld	a, (__joy_cur)
	ld	c, a
	ld	b, #0x00
	ret
;kaijugaiden.c:141: static inline u16 plat_pressed_mask(void) { return (u16)(_joy_cur & (u8)(~_joy_prev)); }
;	---------------------------------
; Function plat_pressed_mask
; ---------------------------------
_plat_pressed_mask:
	ld	a, (#__joy_prev)
	cpl
	ld	hl, #__joy_cur
	and	a, (hl)
	ld	c, a
	ld	b, #0x00
	ret
;kaijugaiden.c:142: static inline void plat_vsync(void)  { wait_vbl_done(); }
;	---------------------------------
; Function plat_vsync
; ---------------------------------
_plat_vsync:
	jp	_wait_vbl_done
;kaijugaiden.c:145: static inline void plat_set_bkg_tile(u8 x, u8 y, u8 tile) {
;	---------------------------------
; Function plat_set_bkg_tile
; ---------------------------------
_plat_set_bkg_tile:
;kaijugaiden.c:146: set_bkg_tile_xy(x, y, tile);
	ldhl	sp,	#2
	ld	h, (hl)
	push	hl
	inc	sp
	call	_set_bkg_tile_xy
;kaijugaiden.c:147: }
	pop	hl
	inc	sp
	jp	(hl)
;kaijugaiden.c:148: static inline void plat_set_sprite(u8 id, u8 x, u8 y, u8 tile, u8 flags) {
;	---------------------------------
; Function plat_set_sprite
; ---------------------------------
_plat_set_sprite:
	ld	c, a
;kaijugaiden.c:149: move_sprite(id, x + 8, y + 16);   /* GBDK uses offset convention */
	ldhl	sp,	#2
	ld	a, (hl)
	add	a, #0x10
	ld	d, a
	ld	a, e
	add	a, #0x08
	ld	e, a
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1973: OAM_item_t * itm = &shadow_OAM[nb];
	ld	l, c
	ld	h, #0x00
	add	hl, hl
	add	hl, hl
	ld	c, l
	ld	b, h
	ld	hl, #_shadow_OAM
	add	hl, bc
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1974: itm->y=y, itm->x=x;
	ld	(hl), d
	inc	hl
	ld	(hl), e
;kaijugaiden.c:150: set_sprite_tile(id, tile);
	ldhl	sp,	#3
	ld	e, (hl)
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1887: shadow_OAM[nb].tile=tile;
	ld	hl,#_shadow_OAM + 1
	add	hl,bc
	inc	hl
	ld	(hl), e
;kaijugaiden.c:151: set_sprite_prop(id, flags);
	ldhl	sp,	#4
	ld	e, (hl)
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1946: shadow_OAM[nb].prop=prop;
	ld	hl,#_shadow_OAM + 1
	add	hl,bc
	inc	hl
	inc	hl
	ld	(hl), e
;kaijugaiden.c:151: set_sprite_prop(id, flags);
;kaijugaiden.c:152: }
	pop	hl
	add	sp, #3
	jp	(hl)
;kaijugaiden.c:153: static inline void plat_load_bkg_tiles(const u8 *data, u8 first, u8 count) {
;	---------------------------------
; Function plat_load_bkg_tiles
; ---------------------------------
_plat_load_bkg_tiles:
;kaijugaiden.c:154: set_bkg_data(first, count, data);
	push	de
	ldhl	sp,	#4
	ld	h, (hl)
	push	hl
	inc	sp
	push	af
	inc	sp
	call	_set_bkg_data
	add	sp, #4
;kaijugaiden.c:155: }
	pop	hl
	inc	sp
	jp	(hl)
;kaijugaiden.c:156: static inline void plat_load_sprite_tiles(const u8 *data, u8 first, u8 count) {
;	---------------------------------
; Function plat_load_sprite_tiles
; ---------------------------------
_plat_load_sprite_tiles:
;kaijugaiden.c:157: set_sprite_data(first, count, data);
	push	de
	ldhl	sp,	#4
	ld	h, (hl)
	push	hl
	inc	sp
	push	af
	inc	sp
	call	_set_sprite_data
	add	sp, #4
;kaijugaiden.c:158: }
	pop	hl
	inc	sp
	jp	(hl)
;kaijugaiden.c:161: static inline void plat_delay_frames(u8 n) {
;	---------------------------------
; Function plat_delay_frames
; ---------------------------------
_plat_delay_frames:
	ld	c, a
;kaijugaiden.c:162: for (u8 i = 0; i < n; ++i) wait_vbl_done();
	ld	b, #0x00
00103$:
	ld	a, b
	sub	a, c
	ret	NC
	call	_wait_vbl_done
	inc	b
;kaijugaiden.c:163: }
	jr	00103$
;kaijugaiden.c:686: static void game_load_tiles(void) {
;	---------------------------------
; Function game_load_tiles
; ---------------------------------
_game_load_tiles:
	dec	sp
	dec	sp
;kaijugaiden.c:689: plat_load_bkg_tiles(tile_blank, TILE_BLANK, 1);
;kaijugaiden.c:154: set_bkg_data(first, count, data);
	ld	de, #_tile_blank
	push	de
	xor	a, a
	inc	a
	push	af
	call	_set_bkg_data
	add	sp, #4
;kaijugaiden.c:691: plat_load_bkg_tiles(tile_ground_lr[0], TILE_GROUND_L, 1);
;kaijugaiden.c:154: set_bkg_data(first, count, data);
	ld	de, #_tile_ground_lr
	push	de
	ld	hl, #0x101
	push	hl
	call	_set_bkg_data
	add	sp, #4
;kaijugaiden.c:692: plat_load_bkg_tiles(tile_ground_lr[1], TILE_GROUND_R, 1);
;kaijugaiden.c:154: set_bkg_data(first, count, data);
	ld	de, #(_tile_ground_lr + 16)
	push	de
	ld	hl, #0x102
	push	hl
	call	_set_bkg_data
	add	sp, #4
;kaijugaiden.c:694: plat_load_bkg_tiles(tile_water_ab[0], TILE_WATER_A, 1);
;kaijugaiden.c:154: set_bkg_data(first, count, data);
	ld	de, #_tile_water_ab
	push	de
	ld	hl, #0x103
	push	hl
	call	_set_bkg_data
	add	sp, #4
;kaijugaiden.c:695: plat_load_bkg_tiles(tile_water_ab[1], TILE_WATER_B, 1);
;kaijugaiden.c:154: set_bkg_data(first, count, data);
	ld	de, #(_tile_water_ab + 16)
	push	de
	ld	hl, #0x104
	push	hl
	call	_set_bkg_data
	add	sp, #4
;kaijugaiden.c:697: plat_load_bkg_tiles(tile_cliff_ab[0], TILE_CLIFF_A, 1);
;kaijugaiden.c:154: set_bkg_data(first, count, data);
	ld	de, #_tile_cliff_ab
	push	de
	ld	hl, #0x105
	push	hl
	call	_set_bkg_data
	add	sp, #4
;kaijugaiden.c:698: plat_load_bkg_tiles(tile_cliff_ab[1], TILE_CLIFF_B, 1);
;kaijugaiden.c:154: set_bkg_data(first, count, data);
	ld	de, #(_tile_cliff_ab + 16)
	push	de
	ld	hl, #0x106
	push	hl
	call	_set_bkg_data
	add	sp, #4
;kaijugaiden.c:700: plat_load_bkg_tiles(tile_sky_ab[0], TILE_SKY_A, 1);
;kaijugaiden.c:154: set_bkg_data(first, count, data);
	ld	de, #_tile_sky_ab
	push	de
	ld	hl, #0x107
	push	hl
	call	_set_bkg_data
	add	sp, #4
;kaijugaiden.c:701: plat_load_bkg_tiles(tile_sky_ab[1], TILE_SKY_B, 1);
;kaijugaiden.c:154: set_bkg_data(first, count, data);
	ld	de, #(_tile_sky_ab + 16)
	push	de
	ld	hl, #0x108
	push	hl
	call	_set_bkg_data
	add	sp, #4
;kaijugaiden.c:703: for (int i = 0; i < 8; ++i)
	ld	bc, #0x0000
00141$:
;kaijugaiden.c:704: plat_load_bkg_tiles(tile_splash[i], TILE_SPLASH1 + i, 1);
	ld	a,c
	cp	a,#0x08
	jr	NC, 00101$
	add	a, #0x09
	ld	e, a
	ld	l, c
	ld	h, b
	add	hl, hl
	add	hl, hl
	add	hl, hl
	add	hl, hl
	push	de
	ld	de, #_tile_splash
	add	hl, de
	pop	de
;kaijugaiden.c:154: set_bkg_data(first, count, data);
	push	hl
	ld	d, #0x01
	push	de
	call	_set_bkg_data
	add	sp, #4
;kaijugaiden.c:703: for (int i = 0; i < 8; ++i)
	inc	bc
	jr	00141$
00101$:
;kaijugaiden.c:706: for (int i = 0; i < 12; ++i)
	ld	bc, #0x0000
00144$:
;kaijugaiden.c:707: plat_load_bkg_tiles(tile_title[i], TILE_TITLE_A + i, 1);
	ld	a,c
	cp	a,#0x0c
	jr	NC, 00102$
	add	a, #0x11
	ld	d, a
	ld	l, c
	ld	h, b
	add	hl, hl
	add	hl, hl
	add	hl, hl
	add	hl, hl
	push	de
	ld	de, #_tile_title
	add	hl, de
	pop	de
;kaijugaiden.c:154: set_bkg_data(first, count, data);
	push	hl
	ld	a, #0x01
	push	af
	inc	sp
	push	de
	inc	sp
	call	_set_bkg_data
	add	sp, #4
;kaijugaiden.c:706: for (int i = 0; i < 12; ++i)
	inc	bc
	jr	00144$
00102$:
;kaijugaiden.c:709: plat_load_bkg_tiles(tile_hp_seg, TILE_HP_SEG, 1);
;kaijugaiden.c:154: set_bkg_data(first, count, data);
	ld	de, #_tile_hp_seg
	push	de
	ld	hl, #0x11d
	push	hl
	call	_set_bkg_data
	add	sp, #4
;kaijugaiden.c:711: plat_load_bkg_tiles(tile_boss_hp_bar[0], TILE_BOSS_SEG, 1);
;kaijugaiden.c:154: set_bkg_data(first, count, data);
	ld	de, #_tile_boss_hp_bar
	push	de
	ld	hl, #0x11e
	push	hl
	call	_set_bkg_data
	add	sp, #4
;kaijugaiden.c:713: for (int i = 0; i < 10; ++i)
	ld	bc, #0x0000
00147$:
;kaijugaiden.c:714: plat_load_bkg_tiles(tile_digit[i], TILE_FONT_0 + i, 1);
	ld	a,c
	cp	a,#0x0a
	jr	NC, 00103$
	add	a, #0x20
	ld	d, a
	ld	l, c
	ld	h, b
	add	hl, hl
	add	hl, hl
	add	hl, hl
	add	hl, hl
	push	de
	ld	de, #_tile_digit
	add	hl, de
	pop	de
;kaijugaiden.c:154: set_bkg_data(first, count, data);
	push	hl
	ld	a, #0x01
	push	af
	inc	sp
	push	de
	inc	sp
	call	_set_bkg_data
	add	sp, #4
;kaijugaiden.c:713: for (int i = 0; i < 10; ++i)
	inc	bc
	jr	00147$
00103$:
;kaijugaiden.c:717: for (int i = 0; i < 6; ++i)
	ld	bc, #0x0000
00150$:
	ld	a, c
	sub	a, #0x06
	jr	NC, 00104$
;kaijugaiden.c:718: plat_load_sprite_tiles(spr_rei_idle_data[i], SPR_REI_IDLE + i, 1);
	ld	d, c
	ld	l, c
	ld	h, b
	add	hl, hl
	add	hl, hl
	add	hl, hl
	add	hl, hl
	push	de
	ld	de, #_spr_rei_idle_data
	add	hl, de
	pop	de
;kaijugaiden.c:157: set_sprite_data(first, count, data);
	push	hl
	ld	a, #0x01
	push	af
	inc	sp
	push	de
	inc	sp
	call	_set_sprite_data
	add	sp, #4
;kaijugaiden.c:717: for (int i = 0; i < 6; ++i)
	inc	bc
	jr	00150$
00104$:
;kaijugaiden.c:720: for (int i = 0; i < 6; ++i)
	xor	a, a
	ldhl	sp,	#0
	ld	(hl+), a
	ld	(hl), a
00153$:
	ldhl	sp,	#0
	ld	a, (hl+)
	sub	a, #0x06
	ld	a, (hl)
	sbc	a, #0x00
	jr	NC, 00105$
;kaijugaiden.c:721: plat_load_sprite_tiles(spr_rei_run_data[i], SPR_REI_RUN + i, 1);
	dec	hl
	ld	a, (hl)
	add	a, #0x06
	ld	b, a
	ld	a, (hl)
	ld	c, #0x00
	add	a, a
	rl	c
	add	a, a
	rl	c
	add	a, a
	rl	c
	add	a, a
	rl	c
	ld	l, a
	ld	h, c
	ld	de, #_spr_rei_run_data
	add	hl, de
;kaijugaiden.c:157: set_sprite_data(first, count, data);
	push	hl
	ld	a, #0x01
	push	af
	inc	sp
	push	bc
	inc	sp
	call	_set_sprite_data
	add	sp, #4
;kaijugaiden.c:720: for (int i = 0; i < 6; ++i)
	ldhl	sp,	#0
	inc	(hl)
	jr	00153$
00105$:
;kaijugaiden.c:723: for (int i = 0; i < 6; ++i)
	xor	a, a
	ldhl	sp,	#0
	ld	(hl+), a
	ld	(hl), a
00156$:
	ldhl	sp,	#0
	ld	a, (hl+)
	sub	a, #0x06
	ld	a, (hl)
	sbc	a, #0x00
	jr	NC, 00106$
;kaijugaiden.c:724: plat_load_sprite_tiles(spr_rei_attack_data[i], SPR_REI_ATTACK + i, 1);
	dec	hl
	ld	a, (hl)
	add	a, #0x0c
	ld	b, a
	ld	a, (hl)
	ld	c, #0x00
	add	a, a
	rl	c
	add	a, a
	rl	c
	add	a, a
	rl	c
	add	a, a
	rl	c
	ld	l, a
	ld	h, c
	ld	de, #_spr_rei_attack_data
	add	hl, de
;kaijugaiden.c:157: set_sprite_data(first, count, data);
	push	hl
	ld	a, #0x01
	push	af
	inc	sp
	push	bc
	inc	sp
	call	_set_sprite_data
	add	sp, #4
;kaijugaiden.c:723: for (int i = 0; i < 6; ++i)
	ldhl	sp,	#0
	inc	(hl)
	jr	00156$
00106$:
;kaijugaiden.c:726: for (int i = 0; i < 8; ++i)
	xor	a, a
	ldhl	sp,	#0
	ld	(hl+), a
	ld	(hl), a
00159$:
	ldhl	sp,	#0
	ld	a, (hl+)
	sub	a, #0x08
	ld	a, (hl)
	sbc	a, #0x00
	jr	NC, 00107$
;kaijugaiden.c:727: plat_load_sprite_tiles(spr_boss_p1_data[i], SPR_BOSS_A + i, 1);
	dec	hl
	ld	a, (hl)
	add	a, #0x12
	ld	b, a
	ld	a, (hl)
	ld	c, #0x00
	add	a, a
	rl	c
	add	a, a
	rl	c
	add	a, a
	rl	c
	add	a, a
	rl	c
	ld	l, a
	ld	h, c
	ld	de, #_spr_boss_p1_data
	add	hl, de
;kaijugaiden.c:157: set_sprite_data(first, count, data);
	push	hl
	ld	a, #0x01
	push	af
	inc	sp
	push	bc
	inc	sp
	call	_set_sprite_data
	add	sp, #4
;kaijugaiden.c:726: for (int i = 0; i < 8; ++i)
	ldhl	sp,	#0
	inc	(hl)
	jr	00159$
00107$:
;kaijugaiden.c:728: for (int i = 0; i < 8; ++i)
	xor	a, a
	ldhl	sp,	#0
	ld	(hl+), a
	ld	(hl), a
00162$:
	ldhl	sp,	#0
	ld	a, (hl+)
	sub	a, #0x08
	ld	a, (hl)
	sbc	a, #0x00
	jr	NC, 00108$
;kaijugaiden.c:729: plat_load_sprite_tiles(spr_boss_p2_data[i], SPR_BOSS_B + i, 1);
	dec	hl
	ld	a, (hl)
	add	a, #0x1a
	ld	b, a
	ld	a, (hl)
	ld	c, #0x00
	add	a, a
	rl	c
	add	a, a
	rl	c
	add	a, a
	rl	c
	add	a, a
	rl	c
	ld	l, a
	ld	h, c
	ld	de, #_spr_boss_p2_data
	add	hl, de
;kaijugaiden.c:157: set_sprite_data(first, count, data);
	push	hl
	ld	a, #0x01
	push	af
	inc	sp
	push	bc
	inc	sp
	call	_set_sprite_data
	add	sp, #4
;kaijugaiden.c:728: for (int i = 0; i < 8; ++i)
	ldhl	sp,	#0
	inc	(hl)
	jr	00162$
00108$:
;kaijugaiden.c:730: for (int i = 0; i < 8; ++i)
	xor	a, a
	ldhl	sp,	#0
	ld	(hl+), a
	ld	(hl), a
00165$:
	ldhl	sp,	#0
	ld	a, (hl+)
	sub	a, #0x08
	ld	a, (hl)
	sbc	a, #0x00
	jr	NC, 00109$
;kaijugaiden.c:731: plat_load_sprite_tiles(spr_boss_p3_data[i], SPR_BOSS_C + i, 1);
	dec	hl
	ld	a, (hl)
	add	a, #0x22
	ld	b, a
	ld	a, (hl)
	ld	c, #0x00
	add	a, a
	rl	c
	add	a, a
	rl	c
	add	a, a
	rl	c
	add	a, a
	rl	c
	ld	l, a
	ld	h, c
	ld	de, #_spr_boss_p3_data
	add	hl, de
;kaijugaiden.c:157: set_sprite_data(first, count, data);
	push	hl
	ld	a, #0x01
	push	af
	inc	sp
	push	bc
	inc	sp
	call	_set_sprite_data
	add	sp, #4
;kaijugaiden.c:730: for (int i = 0; i < 8; ++i)
	ldhl	sp,	#0
	inc	(hl)
	jr	00165$
00109$:
;kaijugaiden.c:733: for (int i = 0; i < 4; ++i)
	xor	a, a
	ldhl	sp,	#0
	ld	(hl+), a
	ld	(hl), a
00168$:
	ldhl	sp,	#0
	ld	a, (hl+)
	sub	a, #0x04
	ld	a, (hl)
	sbc	a, #0x00
	jr	NC, 00110$
;kaijugaiden.c:734: plat_load_sprite_tiles(spr_minion_data[i], SPR_MINION + i, 1);
	dec	hl
	ld	a, (hl)
	add	a, #0x2a
	ld	b, a
	ld	a, (hl)
	ld	c, #0x00
	add	a, a
	rl	c
	add	a, a
	rl	c
	add	a, a
	rl	c
	add	a, a
	rl	c
	ld	l, a
	ld	h, c
	ld	de, #_spr_minion_data
	add	hl, de
;kaijugaiden.c:157: set_sprite_data(first, count, data);
	push	hl
	ld	a, #0x01
	push	af
	inc	sp
	push	bc
	inc	sp
	call	_set_sprite_data
	add	sp, #4
;kaijugaiden.c:733: for (int i = 0; i < 4; ++i)
	ldhl	sp,	#0
	inc	(hl)
	jr	00168$
00110$:
;kaijugaiden.c:736: for (int i = 0; i < 2; ++i)
	xor	a, a
	ldhl	sp,	#0
	ld	(hl+), a
	ld	(hl), a
00171$:
	ldhl	sp,	#0
	ld	a, (hl+)
	sub	a, #0x02
	ld	a, (hl)
	sbc	a, #0x00
	jr	NC, 00111$
;kaijugaiden.c:737: plat_load_sprite_tiles(spr_fx_hit_data[i],  SPR_FX_HIT + i, 1);
	dec	hl
	ld	a, (hl)
	add	a, #0x2e
	ld	b, a
	ld	a, (hl)
	ld	c, #0x00
	add	a, a
	rl	c
	add	a, a
	rl	c
	add	a, a
	rl	c
	add	a, a
	rl	c
	ld	l, a
	ld	h, c
	ld	de, #_spr_fx_hit_data
	add	hl, de
;kaijugaiden.c:157: set_sprite_data(first, count, data);
	push	hl
	ld	a, #0x01
	push	af
	inc	sp
	push	bc
	inc	sp
	call	_set_sprite_data
	add	sp, #4
;kaijugaiden.c:736: for (int i = 0; i < 2; ++i)
	ldhl	sp,	#0
	inc	(hl)
	jr	00171$
00111$:
;kaijugaiden.c:738: for (int i = 0; i < 2; ++i)
	xor	a, a
	ldhl	sp,	#0
	ld	(hl+), a
	ld	(hl), a
00174$:
	ldhl	sp,	#0
	ld	a, (hl+)
	sub	a, #0x02
	ld	a, (hl)
	sbc	a, #0x00
	jr	NC, 00112$
;kaijugaiden.c:739: plat_load_sprite_tiles(spr_fx_nano_data[i], SPR_FX_NANO + i, 1);
	dec	hl
	ld	a, (hl)
	add	a, #0x30
	ld	b, a
	ld	a, (hl)
	ld	c, #0x00
	add	a, a
	rl	c
	add	a, a
	rl	c
	add	a, a
	rl	c
	add	a, a
	rl	c
	ld	l, a
	ld	h, c
	ld	de, #_spr_fx_nano_data
	add	hl, de
;kaijugaiden.c:157: set_sprite_data(first, count, data);
	push	hl
	ld	a, #0x01
	push	af
	inc	sp
	push	bc
	inc	sp
	call	_set_sprite_data
	add	sp, #4
;kaijugaiden.c:738: for (int i = 0; i < 2; ++i)
	ldhl	sp,	#0
	inc	(hl)
	jr	00174$
00112$:
;kaijugaiden.c:741: for (int i = 0; i < 12; ++i)
	xor	a, a
	ldhl	sp,	#0
	ld	(hl+), a
	ld	(hl), a
00177$:
	ldhl	sp,	#0
	ld	a, (hl+)
	sub	a, #0x0c
	ld	a, (hl)
	sbc	a, #0x00
	jr	NC, 00113$
;kaijugaiden.c:742: plat_load_sprite_tiles(spr_cinematic_a[i], SPR_CINEMATIC_A + i, 1);
	dec	hl
	ld	a, (hl)
	add	a, #0x32
	ld	b, a
	ld	a, (hl)
	ld	c, #0x00
	add	a, a
	rl	c
	add	a, a
	rl	c
	add	a, a
	rl	c
	add	a, a
	rl	c
	ld	l, a
	ld	h, c
	ld	de, #_spr_cinematic_a
	add	hl, de
;kaijugaiden.c:157: set_sprite_data(first, count, data);
	push	hl
	ld	a, #0x01
	push	af
	inc	sp
	push	bc
	inc	sp
	call	_set_sprite_data
	add	sp, #4
;kaijugaiden.c:741: for (int i = 0; i < 12; ++i)
	ldhl	sp,	#0
	inc	(hl)
	jr	00177$
00113$:
;kaijugaiden.c:743: for (int i = 0; i < 12; ++i)
	ld	bc, #0x0000
00180$:
;kaijugaiden.c:744: plat_load_sprite_tiles(spr_cinematic_b[i], SPR_CINEMATIC_B + i, 1);
	ld	a,c
	cp	a,#0x0c
	jr	NC, 00182$
	add	a, #0x3e
	ld	e, a
	ld	l, c
	ld	h, b
	add	hl, hl
	add	hl, hl
	add	hl, hl
	add	hl, hl
	push	de
	ld	de, #_spr_cinematic_b
	add	hl, de
	pop	de
;kaijugaiden.c:157: set_sprite_data(first, count, data);
	push	hl
	ld	d, #0x01
	push	de
	call	_set_sprite_data
	add	sp, #4
;kaijugaiden.c:743: for (int i = 0; i < 12; ++i)
	inc	bc
	jr	00180$
00182$:
;kaijugaiden.c:745: }
	inc	sp
	inc	sp
	ret
_tile_blank:
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
_tile_ground_lr:
	.db #0xec	; 236
	.db #0xff	; 255
	.db #0x79	; 121	'y'
	.db #0xfe	; 254
	.db #0x01	; 1
	.db #0xff	; 255
	.db #0x80	; 128
	.db #0x7f	; 127
	.db #0xf9	; 249
	.db #0xe6	; 230
	.db #0x01	; 1
	.db #0xfe	; 254
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0x27	; 39
	.db #0xff	; 255
	.db #0x3e	; 62
	.db #0xff	; 255
	.db #0xe1	; 225
	.db #0xff	; 255
	.db #0x01	; 1
	.db #0xfe	; 254
	.db #0xc1	; 193
	.db #0x3f	; 63
	.db #0xf8	; 248
	.db #0x07	; 7
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x00	; 0
_tile_water_ab:
	.db #0x02	; 2
	.db #0xfd	; 253
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x70	; 112	'p'
	.db #0x8f	; 143
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x60	; 96
	.db #0x9f	; 159
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x40	; 64
	.db #0xbf	; 191
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x0e	; 14
	.db #0xf1	; 241
	.db #0xc0	; 192
	.db #0x3f	; 63
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x04	; 4
	.db #0xfb	; 251
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
_tile_cliff_ab:
	.db #0x32	; 50	'2'
	.db #0xfd	; 253
	.db #0x10	; 16
	.db #0xff	; 255
	.db #0x17	; 23
	.db #0xf8	; 248
	.db #0x37	; 55	'7'
	.db #0xf9	; 249
	.db #0x32	; 50	'2'
	.db #0xfd	; 253
	.db #0x11	; 17
	.db #0xfe	; 254
	.db #0x16	; 22
	.db #0xf9	; 249
	.db #0x37	; 55	'7'
	.db #0xf9	; 249
	.db #0x32	; 50	'2'
	.db #0xfd	; 253
	.db #0x11	; 17
	.db #0xfe	; 254
	.db #0x17	; 23
	.db #0xf8	; 248
	.db #0x37	; 55	'7'
	.db #0xf9	; 249
	.db #0x30	; 48	'0'
	.db #0xff	; 255
	.db #0x11	; 17
	.db #0xfe	; 254
	.db #0x16	; 22
	.db #0xf9	; 249
	.db #0x36	; 54	'6'
	.db #0xf9	; 249
_tile_sky_ab:
	.db #0x8f	; 143
	.db #0xe0	; 224
	.db #0x47	; 71	'G'
	.db #0xf8	; 248
	.db #0x41	; 65	'A'
	.db #0x3e	; 62
	.db #0x88	; 136
	.db #0x07	; 7
	.db #0x7e	; 126
	.db #0x81	; 129
	.db #0x03	; 3
	.db #0xfc	; 252
	.db #0x3f	; 63
	.db #0x00	; 0
	.db #0xaf	; 175
	.db #0x10	; 16
	.db #0xfd	; 253
	.db #0x03	; 3
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0x88	; 136
	.db #0x00	; 0
	.db #0x15	; 21
	.db #0xe0	; 224
	.db #0x7c	; 124
	.db #0x83	; 131
	.db #0xf6	; 246
	.db #0x01	; 1
	.db #0xfc	; 252
	.db #0x00	; 0
	.db #0xce	; 206
	.db #0x31	; 49	'1'
_tile_splash:
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xf0	; 240
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0x09	; 9
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xef	; 239
	.db #0xff	; 255
	.db #0x2f	; 47
	.db #0xff	; 255
	.db #0xf6	; 246
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0x66	; 102	'f'
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0x7b	; 123
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
_tile_title:
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xbf	; 191
	.db #0xff	; 255
	.db #0xe8	; 232
	.db #0xbf	; 191
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xa1	; 161
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0x7f	; 127
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xfc	; 252
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xfc	; 252
	.db #0xfc	; 252
	.db #0xff	; 255
	.db #0xf8	; 248
	.db #0xff	; 255
	.db #0x52	; 82	'R'
	.db #0xad	; 173
	.db #0x11	; 17
	.db #0xff	; 255
	.db #0x40	; 64
	.db #0xff	; 255
	.db #0xdf	; 223
	.db #0xff	; 255
	.db #0x23	; 35
	.db #0xff	; 255
	.db #0x28	; 40
	.db #0xd7	; 215
	.db #0x40	; 64
	.db #0xff	; 255
	.db #0x06	; 6
	.db #0xff	; 255
	.db #0x2a	; 42
	.db #0xf5	; 245
	.db #0x62	; 98	'b'
	.db #0xff	; 255
	.db #0x0a	; 10
	.db #0xff	; 255
	.db #0xd8	; 216
	.db #0xff	; 255
	.db #0x11	; 17
	.db #0xff	; 255
	.db #0xa8	; 168
	.db #0x57	; 87	'W'
	.db #0x42	; 66	'B'
	.db #0xff	; 255
	.db #0x06	; 6
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0x7f	; 127
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0x7f	; 127
	.db #0xff	; 255
	.db #0xdf	; 223
	.db #0x7f	; 127
	.db #0x3f	; 63
	.db #0x5f	; 95
	.db #0x1f	; 31
	.db #0xff	; 255
	.db #0xbf	; 191
	.db #0xff	; 255
	.db #0xfc	; 252
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xaa	; 170
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0x20	; 32
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xbf	; 191
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
_tile_hp_seg:
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xef	; 239
	.db #0xff	; 255
	.db #0xe3	; 227
	.db #0xff	; 255
	.db #0xe3	; 227
	.db #0xff	; 255
	.db #0xe7	; 231
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
_tile_boss_hp_bar:
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0x80	; 128
	.db #0xff	; 255
	.db #0x80	; 128
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0x21	; 33
	.db #0xde	; 222
	.db #0x01	; 1
	.db #0xfe	; 254
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0x01	; 1
	.db #0xff	; 255
	.db #0x01	; 1
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0x04	; 4
	.db #0xfb	; 251
	.db #0x05	; 5
	.db #0xfb	; 251
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0x01	; 1
	.db #0xff	; 255
	.db #0x01	; 1
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
_tile_digit:
	.db #0x3c	; 60
	.db #0x00	; 0
	.db #0x66	; 102	'f'
	.db #0x00	; 0
	.db #0x6e	; 110	'n'
	.db #0x00	; 0
	.db #0x76	; 118	'v'
	.db #0x00	; 0
	.db #0x66	; 102	'f'
	.db #0x00	; 0
	.db #0x66	; 102	'f'
	.db #0x00	; 0
	.db #0x3c	; 60
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x18	; 24
	.db #0x00	; 0
	.db #0x38	; 56	'8'
	.db #0x00	; 0
	.db #0x18	; 24
	.db #0x00	; 0
	.db #0x18	; 24
	.db #0x00	; 0
	.db #0x18	; 24
	.db #0x00	; 0
	.db #0x18	; 24
	.db #0x00	; 0
	.db #0x7e	; 126
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x3c	; 60
	.db #0x00	; 0
	.db #0x66	; 102	'f'
	.db #0x00	; 0
	.db #0x06	; 6
	.db #0x00	; 0
	.db #0x0c	; 12
	.db #0x00	; 0
	.db #0x18	; 24
	.db #0x00	; 0
	.db #0x30	; 48	'0'
	.db #0x00	; 0
	.db #0x7e	; 126
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x3c	; 60
	.db #0x00	; 0
	.db #0x66	; 102	'f'
	.db #0x00	; 0
	.db #0x06	; 6
	.db #0x00	; 0
	.db #0x1c	; 28
	.db #0x00	; 0
	.db #0x06	; 6
	.db #0x00	; 0
	.db #0x66	; 102	'f'
	.db #0x00	; 0
	.db #0x3c	; 60
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x0c	; 12
	.db #0x00	; 0
	.db #0x1c	; 28
	.db #0x00	; 0
	.db #0x3c	; 60
	.db #0x00	; 0
	.db #0x6c	; 108	'l'
	.db #0x00	; 0
	.db #0x7e	; 126
	.db #0x00	; 0
	.db #0x0c	; 12
	.db #0x00	; 0
	.db #0x0c	; 12
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x7e	; 126
	.db #0x00	; 0
	.db #0x60	; 96
	.db #0x00	; 0
	.db #0x7c	; 124
	.db #0x00	; 0
	.db #0x06	; 6
	.db #0x00	; 0
	.db #0x06	; 6
	.db #0x00	; 0
	.db #0x66	; 102	'f'
	.db #0x00	; 0
	.db #0x3c	; 60
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x3c	; 60
	.db #0x00	; 0
	.db #0x66	; 102	'f'
	.db #0x00	; 0
	.db #0x60	; 96
	.db #0x00	; 0
	.db #0x7c	; 124
	.db #0x00	; 0
	.db #0x66	; 102	'f'
	.db #0x00	; 0
	.db #0x66	; 102	'f'
	.db #0x00	; 0
	.db #0x3c	; 60
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x7e	; 126
	.db #0x00	; 0
	.db #0x06	; 6
	.db #0x00	; 0
	.db #0x0c	; 12
	.db #0x00	; 0
	.db #0x18	; 24
	.db #0x00	; 0
	.db #0x18	; 24
	.db #0x00	; 0
	.db #0x18	; 24
	.db #0x00	; 0
	.db #0x18	; 24
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x3c	; 60
	.db #0x00	; 0
	.db #0x66	; 102	'f'
	.db #0x00	; 0
	.db #0x66	; 102	'f'
	.db #0x00	; 0
	.db #0x3c	; 60
	.db #0x00	; 0
	.db #0x66	; 102	'f'
	.db #0x00	; 0
	.db #0x66	; 102	'f'
	.db #0x00	; 0
	.db #0x3c	; 60
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x3c	; 60
	.db #0x00	; 0
	.db #0x66	; 102	'f'
	.db #0x00	; 0
	.db #0x66	; 102	'f'
	.db #0x00	; 0
	.db #0x3e	; 62
	.db #0x00	; 0
	.db #0x06	; 6
	.db #0x00	; 0
	.db #0x66	; 102	'f'
	.db #0x00	; 0
	.db #0x3c	; 60
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
_spr_rei_idle_data:
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x02	; 2
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x02	; 2
	.db #0x00	; 0
	.db #0x03	; 3
	.db #0x02	; 2
	.db #0x01	; 1
	.db #0x00	; 0
	.db #0x01	; 1
	.db #0x03	; 3
	.db #0x01	; 1
	.db #0x00	; 0
	.db #0x03	; 3
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x40	; 64
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x40	; 64
	.db #0x00	; 0
	.db #0xc0	; 192
	.db #0x40	; 64
	.db #0x80	; 128
	.db #0x00	; 0
	.db #0x80	; 128
	.db #0xc0	; 192
	.db #0x80	; 128
	.db #0x00	; 0
	.db #0xc0	; 192
	.db #0x00	; 0
	.db #0x03	; 3
	.db #0x02	; 2
	.db #0x01	; 1
	.db #0x04	; 4
	.db #0x03	; 3
	.db #0x05	; 5
	.db #0x03	; 3
	.db #0x05	; 5
	.db #0x03	; 3
	.db #0x04	; 4
	.db #0x03	; 3
	.db #0x00	; 0
	.db #0x03	; 3
	.db #0x03	; 3
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0xc0	; 192
	.db #0x40	; 64
	.db #0x80	; 128
	.db #0x20	; 32
	.db #0xc0	; 192
	.db #0xa0	; 160
	.db #0xc0	; 192
	.db #0xa0	; 160
	.db #0xc0	; 192
	.db #0x20	; 32
	.db #0xc0	; 192
	.db #0x00	; 0
	.db #0xc0	; 192
	.db #0xc0	; 192
	.db #0x00	; 0
	.db #0x03	; 3
	.db #0x00	; 0
	.db #0x01	; 1
	.db #0x02	; 2
	.db #0x01	; 1
	.db #0x02	; 2
	.db #0x01	; 1
	.db #0x02	; 2
	.db #0x00	; 0
	.db #0x02	; 2
	.db #0x00	; 0
	.db #0x02	; 2
	.db #0x07	; 7
	.db #0x02	; 2
	.db #0x07	; 7
	.db #0x02	; 2
	.db #0xc0	; 192
	.db #0x00	; 0
	.db #0x80	; 128
	.db #0x40	; 64
	.db #0x80	; 128
	.db #0x40	; 64
	.db #0x80	; 128
	.db #0x40	; 64
	.db #0x00	; 0
	.db #0x40	; 64
	.db #0x80	; 128
	.db #0x40	; 64
	.db #0xe0	; 224
	.db #0x40	; 64
	.db #0xe0	; 224
	.db #0x40	; 64
_spr_rei_run_data:
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x03	; 3
	.db #0x00	; 0
	.db #0x1d	; 29
	.db #0x00	; 0
	.db #0x17	; 23
	.db #0x00	; 0
	.db #0x02	; 2
	.db #0x01	; 1
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x70	; 112	'p'
	.db #0x00	; 0
	.db #0x40	; 64
	.db #0x30	; 48	'0'
	.db #0x48	; 72	'H'
	.db #0x30	; 48	'0'
	.db #0xe8	; 232
	.db #0x30	; 48	'0'
	.db #0x6c	; 108	'l'
	.db #0xb0	; 176
	.db #0x3c	; 60
	.db #0xf2	; 242
	.db #0x3c	; 60
	.db #0x03	; 3
	.db #0x68	; 104	'h'
	.db #0x06	; 6
	.db #0x42	; 66	'B'
	.db #0x04	; 4
	.db #0x07	; 7
	.db #0x00	; 0
	.db #0x1f	; 31
	.db #0x03	; 3
	.db #0x3a	; 58
	.db #0x07	; 7
	.db #0x06	; 6
	.db #0x21	; 33
	.db #0x64	; 100	'd'
	.db #0x03	; 3
	.db #0x00	; 0
	.db #0xf6	; 246
	.db #0x52	; 82	'R'
	.db #0xf4	; 244
	.db #0x4c	; 76	'L'
	.db #0xfc	; 252
	.db #0x60	; 96
	.db #0xcc	; 204
	.db #0xe0	; 224
	.db #0xc0	; 192
	.db #0x68	; 104	'h'
	.db #0xf0	; 240
	.db #0x20	; 32
	.db #0xf8	; 248
	.db #0xbc	; 188
	.db #0x18	; 24
	.db #0x03	; 3
	.db #0x0e	; 14
	.db #0x14	; 20
	.db #0x0e	; 14
	.db #0x08	; 8
	.db #0x1c	; 28
	.db #0x28	; 40
	.db #0x18	; 24
	.db #0x31	; 49	'1'
	.db #0x18	; 24
	.db #0x24	; 36
	.db #0x18	; 24
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x10	; 16
	.db #0x38	; 56	'8'
	.db #0x78	; 120	'x'
	.db #0x30	; 48	'0'
	.db #0x30	; 48	'0'
	.db #0x60	; 96
	.db #0x70	; 112	'p'
	.db #0xe0	; 224
	.db #0x78	; 120	'x'
	.db #0x30	; 48	'0'
	.db #0x10	; 16
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
_spr_rei_attack_data:
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x01	; 1
	.db #0x00	; 0
	.db #0x06	; 6
	.db #0x01	; 1
	.db #0x38	; 56	'8'
	.db #0x03	; 3
	.db #0x10	; 16
	.db #0x23	; 35
	.db #0xf0	; 240
	.db #0x03	; 3
	.db #0x38	; 56	'8'
	.db #0xc3	; 195
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x0c	; 12
	.db #0x00	; 0
	.db #0xf0	; 240
	.db #0x08	; 8
	.db #0x08	; 8
	.db #0xf0	; 240
	.db #0x02	; 2
	.db #0xfc	; 252
	.db #0x2b	; 43
	.db #0xfc	; 252
	.db #0x1a	; 26
	.db #0xfc	; 252
	.db #0x64	; 100	'd'
	.db #0xfe	; 254
	.db #0x04	; 4
	.db #0xfb	; 251
	.db #0xa0	; 160
	.db #0x1f	; 31
	.db #0x7e	; 126
	.db #0x1f	; 31
	.db #0x66	; 102	'f'
	.db #0x1f	; 31
	.db #0x37	; 55	'7'
	.db #0x03	; 3
	.db #0x01	; 1
	.db #0x03	; 3
	.db #0x02	; 2
	.db #0x01	; 1
	.db #0x02	; 2
	.db #0x01	; 1
	.db #0x31	; 49	'1'
	.db #0xfe	; 254
	.db #0xb2	; 178
	.db #0xcd	; 205
	.db #0x8b	; 139
	.db #0xc4	; 196
	.db #0x0a	; 10
	.db #0xc4	; 196
	.db #0x62	; 98	'b'
	.db #0xc4	; 196
	.db #0xc8	; 200
	.db #0xc4	; 196
	.db #0xf8	; 248
	.db #0xc0	; 192
	.db #0xe0	; 224
	.db #0xc0	; 192
	.db #0x02	; 2
	.db #0x01	; 1
	.db #0x00	; 0
	.db #0x03	; 3
	.db #0x04	; 4
	.db #0x03	; 3
	.db #0x08	; 8
	.db #0x07	; 7
	.db #0x01	; 1
	.db #0x0f	; 15
	.db #0x17	; 23
	.db #0x0e	; 14
	.db #0x08	; 8
	.db #0x1c	; 28
	.db #0x3c	; 60
	.db #0x18	; 24
	.db #0x7b	; 123
	.db #0xe4	; 228
	.db #0x3d	; 61
	.db #0xff	; 255
	.db #0xe3	; 227
	.db #0xfe	; 254
	.db #0xf4	; 244
	.db #0xfe	; 254
	.db #0x78	; 120	'x'
	.db #0xf6	; 246
	.db #0x78	; 120	'x'
	.db #0x38	; 56	'8'
	.db #0x3c	; 60
	.db #0x1c	; 28
	.db #0x1c	; 28
	.db #0x0e	; 14
_spr_boss_p1_data:
	.db #0x03	; 3
	.db #0x00	; 0
	.db #0x14	; 20
	.db #0x0f	; 15
	.db #0x78	; 120	'x'
	.db #0x1f	; 31
	.db #0x70	; 112	'p'
	.db #0xff	; 255
	.db #0xf0	; 240
	.db #0x7f	; 127
	.db #0x70	; 112	'p'
	.db #0x3f	; 63
	.db #0x10	; 16
	.db #0x3f	; 63
	.db #0x13	; 19
	.db #0x0f	; 15
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0x07	; 7
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x01	; 1
	.db #0xff	; 255
	.db #0x0e	; 14
	.db #0xff	; 255
	.db #0x9f	; 159
	.db #0x7f	; 127
	.db #0x07	; 7
	.db #0xff	; 255
	.db #0x0a	; 10
	.db #0xff	; 255
	.db #0x80	; 128
	.db #0x00	; 0
	.db #0x90	; 144
	.db #0xe0	; 224
	.db #0x08	; 8
	.db #0xf0	; 240
	.db #0xa0	; 160
	.db #0xc1	; 193
	.db #0x98	; 152
	.db #0x01	; 1
	.db #0x21	; 33
	.db #0xf0	; 240
	.db #0x25	; 37
	.db #0xf8	; 248
	.db #0x10	; 16
	.db #0xf8	; 248
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x30	; 48	'0'
	.db #0x00	; 0
	.db #0xc3	; 195
	.db #0x60	; 96
	.db #0xc0	; 192
	.db #0xfe	; 254
	.db #0xf4	; 244
	.db #0xf8	; 248
	.db #0xc0	; 192
	.db #0x80	; 128
	.db #0x50	; 80	'P'
	.db #0xe0	; 224
	.db #0x1c	; 28
	.db #0x0f	; 15
	.db #0x0a	; 10
	.db #0x04	; 4
	.db #0x02	; 2
	.db #0x01	; 1
	.db #0x0f	; 15
	.db #0x03	; 3
	.db #0x3f	; 63
	.db #0x7e	; 126
	.db #0x50	; 80	'P'
	.db #0x26	; 38
	.db #0x0c	; 12
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x71	; 113	'q'
	.db #0xff	; 255
	.db #0x71	; 113	'q'
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xe7	; 231
	.db #0xb6	; 182
	.db #0xcf	; 207
	.db #0x38	; 56	'8'
	.db #0x1f	; 31
	.db #0x50	; 80	'P'
	.db #0x2f	; 47
	.db #0x6c	; 108	'l'
	.db #0x01	; 1
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x0e	; 14
	.db #0xf8	; 248
	.db #0x8d	; 141
	.db #0xfe	; 254
	.db #0x07	; 7
	.db #0xff	; 255
	.db #0x3f	; 63
	.db #0xff	; 255
	.db #0x27	; 39
	.db #0xff	; 255
	.db #0x1a	; 26
	.db #0x87	; 135
	.db #0x0b	; 11
	.db #0x87	; 135
	.db #0x0e	; 14
	.db #0x00	; 0
	.db #0x5c	; 92
	.db #0x38	; 56	'8'
	.db #0x0e	; 14
	.db #0x1c	; 28
	.db #0x1e	; 30
	.db #0xfc	; 252
	.db #0xf8	; 248
	.db #0xfc	; 252
	.db #0x88	; 136
	.db #0xf0	; 240
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x80	; 128
	.db #0x00	; 0
	.db #0x80	; 128
	.db #0x00	; 0
_spr_boss_p2_data:
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x01	; 1
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x01	; 1
	.db #0x00	; 0
	.db #0x04	; 4
	.db #0x00	; 0
	.db #0x9f	; 159
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0xa0	; 160
	.db #0x7f	; 127
	.db #0x21	; 33
	.db #0x7f	; 127
	.db #0xdc	; 220
	.db #0x3f	; 63
	.db #0xac	; 172
	.db #0x1f	; 31
	.db #0x0c	; 12
	.db #0x1f	; 31
	.db #0x60	; 96
	.db #0x00	; 0
	.db #0x5d	; 93
	.db #0x80	; 128
	.db #0x07	; 7
	.db #0xf8	; 248
	.db #0xf0	; 240
	.db #0xff	; 255
	.db #0xc0	; 192
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0xe4	; 228
	.db #0x1f	; 31
	.db #0x16	; 22
	.db #0x0f	; 15
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x80	; 128
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0xe0	; 224
	.db #0x00	; 0
	.db #0xfc	; 252
	.db #0xc0	; 192
	.db #0x48	; 72	'H'
	.db #0xf0	; 240
	.db #0xc3	; 195
	.db #0xe0	; 224
	.db #0x2d	; 45
	.db #0xf2	; 242
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x01	; 1
	.db #0x05	; 5
	.db #0x03	; 3
	.db #0x1e	; 30
	.db #0x0f	; 15
	.db #0x32	; 50	'2'
	.db #0x7f	; 127
	.db #0x40	; 64
	.db #0xe3	; 227
	.db #0x06	; 6
	.db #0xc0	; 192
	.db #0x40	; 64
	.db #0x00	; 0
	.db #0x5c	; 92
	.db #0xb9	; 185
	.db #0xf0	; 240
	.db #0xf9	; 249
	.db #0xc8	; 200
	.db #0xf3	; 243
	.db #0x80	; 128
	.db #0x0f	; 15
	.db #0x2f	; 47
	.db #0x1f	; 31
	.db #0x3f	; 63
	.db #0x7f	; 127
	.db #0x7f	; 127
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0x05	; 5
	.db #0xfe	; 254
	.db #0x9e	; 158
	.db #0xfc	; 252
	.db #0x1e	; 30
	.db #0xfd	; 253
	.db #0x36	; 54	'6'
	.db #0xff	; 255
	.db #0x9e	; 158
	.db #0xff	; 255
	.db #0xfc	; 252
	.db #0xff	; 255
	.db #0xfd	; 253
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0x40	; 64
	.db #0x3e	; 62
	.db #0x57	; 87	'W'
	.db #0x2c	; 44
	.db #0xa4	; 164
	.db #0x1e	; 30
	.db #0x78	; 120	'x'
	.db #0x0c	; 12
	.db #0x4c	; 76	'L'
	.db #0xb8	; 184
	.db #0xe6	; 230
	.db #0xd8	; 216
	.db #0x90	; 144
	.db #0xfc	; 252
	.db #0x30	; 48	'0'
	.db #0x00	; 0
_spr_boss_p3_data:
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x02	; 2
	.db #0x00	; 0
	.db #0x08	; 8
	.db #0x00	; 0
	.db #0x01	; 1
	.db #0x00	; 0
	.db #0x0a	; 10
	.db #0x01	; 1
	.db #0x02	; 2
	.db #0x09	; 9
	.db #0x07	; 7
	.db #0x09	; 9
	.db #0x30	; 48	'0'
	.db #0x07	; 7
	.db #0x18	; 24
	.db #0x00	; 0
	.db #0x78	; 120	'x'
	.db #0x00	; 0
	.db #0x0a	; 10
	.db #0xc0	; 192
	.db #0x34	; 52	'4'
	.db #0x80	; 128
	.db #0x9f	; 159
	.db #0x20	; 32
	.db #0x82	; 130
	.db #0x3f	; 63
	.db #0x52	; 82	'R'
	.db #0xbf	; 191
	.db #0xcb	; 203
	.db #0xff	; 255
	.db #0x30	; 48	'0'
	.db #0x00	; 0
	.db #0x1a	; 26
	.db #0x04	; 4
	.db #0x67	; 103	'g'
	.db #0x00	; 0
	.db #0x28	; 40
	.db #0x01	; 1
	.db #0x7d	; 125
	.db #0x80	; 128
	.db #0x43	; 67	'C'
	.db #0xfc	; 252
	.db #0x48	; 72	'H'
	.db #0xff	; 255
	.db #0xd3	; 211
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x30	; 48	'0'
	.db #0x00	; 0
	.db #0x80	; 128
	.db #0x10	; 16
	.db #0x40	; 64
	.db #0x90	; 144
	.db #0x60	; 96
	.db #0x90	; 144
	.db #0x40	; 64
	.db #0xb0	; 176
	.db #0x04	; 4
	.db #0xe0	; 224
	.db #0x14	; 20
	.db #0x03	; 3
	.db #0x3c	; 60
	.db #0x03	; 3
	.db #0x1b	; 27
	.db #0x07	; 7
	.db #0x02	; 2
	.db #0x01	; 1
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0xfe	; 254
	.db #0xff	; 255
	.db #0xfa	; 250
	.db #0xfc	; 252
	.db #0xfc	; 252
	.db #0xf8	; 248
	.db #0xe4	; 228
	.db #0xf8	; 248
	.db #0x70	; 112	'p'
	.db #0xe0	; 224
	.db #0x20	; 32
	.db #0xe0	; 224
	.db #0x10	; 16
	.db #0x20	; 32
	.db #0x10	; 16
	.db #0x00	; 0
	.db #0x7e	; 126
	.db #0xff	; 255
	.db #0x5f	; 95
	.db #0x3f	; 63
	.db #0x1f	; 31
	.db #0x3f	; 63
	.db #0x37	; 55	'7'
	.db #0x0f	; 15
	.db #0x0e	; 14
	.db #0x07	; 7
	.db #0x08	; 8
	.db #0x07	; 7
	.db #0x00	; 0
	.db #0x0c	; 12
	.db #0x18	; 24
	.db #0x00	; 0
	.db #0x6c	; 108	'l'
	.db #0x80	; 128
	.db #0x3c	; 60
	.db #0xc0	; 192
	.db #0xd8	; 216
	.db #0xe0	; 224
	.db #0xe0	; 224
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
_spr_minion_data:
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x04	; 4
	.db #0x00	; 0
	.db #0x0c	; 12
	.db #0x00	; 0
	.db #0x10	; 16
	.db #0x08	; 8
	.db #0x30	; 48	'0'
	.db #0x08	; 8
	.db #0x44	; 68	'D'
	.db #0x38	; 56	'8'
	.db #0x07	; 7
	.db #0x78	; 120	'x'
	.db #0x67	; 103	'g'
	.db #0x38	; 56	'8'
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x20	; 32
	.db #0x00	; 0
	.db #0x30	; 48	'0'
	.db #0x00	; 0
	.db #0x08	; 8
	.db #0x10	; 16
	.db #0x0c	; 12
	.db #0x10	; 16
	.db #0x22	; 34
	.db #0x1c	; 28
	.db #0xa0	; 160
	.db #0x5e	; 94
	.db #0xe6	; 230
	.db #0x1c	; 28
	.db #0x13	; 19
	.db #0x38	; 56	'8'
	.db #0x10	; 16
	.db #0x0f	; 15
	.db #0x0b	; 11
	.db #0x04	; 4
	.db #0x0c	; 12
	.db #0x07	; 7
	.db #0x0b	; 11
	.db #0x07	; 7
	.db #0x19	; 25
	.db #0x0f	; 15
	.db #0x05	; 5
	.db #0x18	; 24
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0xc8	; 200
	.db #0x1c	; 28
	.db #0x08	; 8
	.db #0xf0	; 240
	.db #0xd0	; 208
	.db #0x20	; 32
	.db #0x30	; 48	'0'
	.db #0xe0	; 224
	.db #0xd0	; 208
	.db #0xe0	; 224
	.db #0x98	; 152
	.db #0xf0	; 240
	.db #0xa0	; 160
	.db #0x18	; 24
	.db #0x00	; 0
	.db #0x00	; 0
_spr_fx_hit_data:
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x18	; 24
	.db #0x00	; 0
	.db #0x0f	; 15
	.db #0x00	; 0
	.db #0x05	; 5
	.db #0x03	; 3
	.db #0x04	; 4
	.db #0x03	; 3
	.db #0x1f	; 31
	.db #0x00	; 0
	.db #0x30	; 48	'0'
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x8c	; 140
	.db #0x00	; 0
	.db #0xf8	; 248
	.db #0x00	; 0
	.db #0x20	; 32
	.db #0xc0	; 192
	.db #0xa8	; 168
	.db #0xc0	; 192
	.db #0xf0	; 240
	.db #0x00	; 0
	.db #0x18	; 24
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
_spr_fx_nano_data:
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x09	; 9
	.db #0x07	; 7
	.db #0x16	; 22
	.db #0x0f	; 15
	.db #0x16	; 22
	.db #0x0f	; 15
	.db #0x09	; 9
	.db #0x07	; 7
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x90	; 144
	.db #0xe0	; 224
	.db #0x68	; 104	'h'
	.db #0xf0	; 240
	.db #0x68	; 104	'h'
	.db #0xf0	; 240
	.db #0x10	; 16
	.db #0xe0	; 224
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
_spr_cinematic_a:
	.db #0x06	; 6
	.db #0xff	; 255
	.db #0x07	; 7
	.db #0xff	; 255
	.db #0x03	; 3
	.db #0xff	; 255
	.db #0x03	; 3
	.db #0xff	; 255
	.db #0x01	; 1
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x0f	; 15
	.db #0xf0	; 240
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0x7f	; 127
	.db #0x80	; 128
	.db #0xc0	; 192
	.db #0xff	; 255
	.db #0xc1	; 193
	.db #0xff	; 255
	.db #0xf9	; 249
	.db #0xff	; 255
	.db #0x3f	; 63
	.db #0xff	; 255
	.db #0x1f	; 31
	.db #0xff	; 255
	.db #0xf0	; 240
	.db #0x0f	; 15
	.db #0xc0	; 192
	.db #0x3f	; 63
	.db #0x80	; 128
	.db #0x7f	; 127
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x03	; 3
	.db #0xff	; 255
	.db #0xe7	; 231
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xf8	; 248
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0xe0	; 224
	.db #0xff	; 255
	.db #0xe0	; 224
	.db #0xff	; 255
	.db #0xc0	; 192
	.db #0xff	; 255
	.db #0x80	; 128
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x7c	; 124
	.db #0x83	; 131
	.db #0xfe	; 254
	.db #0x01	; 1
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x0f	; 15
	.db #0xff	; 255
	.db #0xf7	; 247
	.db #0x0f	; 15
	.db #0xff	; 255
	.db #0x03	; 3
	.db #0xfb	; 251
	.db #0x07	; 7
	.db #0xf7	; 247
	.db #0x0f	; 15
	.db #0xef	; 239
	.db #0x1f	; 31
	.db #0xce	; 206
	.db #0x1f	; 31
	.db #0x2c	; 44
	.db #0x1e	; 30
	.db #0xe9	; 233
	.db #0xf0	; 240
	.db #0xf0	; 240
	.db #0xe0	; 224
	.db #0xe3	; 227
	.db #0xc0	; 192
	.db #0xde	; 222
	.db #0xe1	; 225
	.db #0xec	; 236
	.db #0xf3	; 243
	.db #0xff	; 255
	.db #0xf8	; 248
	.db #0xfb	; 251
	.db #0x7c	; 124
	.db #0x5c	; 92
	.db #0x3e	; 62
	.db #0xf8	; 248
	.db #0x07	; 7
	.db #0x70	; 112	'p'
	.db #0x0f	; 15
	.db #0xe0	; 224
	.db #0x1f	; 31
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x06	; 6
	.db #0xf9	; 249
	.db #0x70	; 112	'p'
	.db #0x80	; 128
	.db #0x7f	; 127
	.db #0x80	; 128
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0x7c	; 124
	.db #0x3c	; 60
	.db #0x3c	; 60
	.db #0x7c	; 124
	.db #0xbb	; 187
	.db #0x7c	; 124
	.db #0x38	; 56	'8'
	.db #0xff	; 255
	.db #0x78	; 120	'x'
	.db #0xff	; 255
	.db #0x30	; 48	'0'
	.db #0x78	; 120	'x'
	.db #0x78	; 120	'x'
	.db #0x3c	; 60
	.db #0x7c	; 124
	.db #0xff	; 255
	.db #0x3e	; 62
	.db #0x1c	; 28
	.db #0x3e	; 62
	.db #0x3c	; 60
	.db #0xfd	; 253
	.db #0x3e	; 62
	.db #0x1e	; 30
	.db #0xff	; 255
	.db #0x1e	; 30
	.db #0xff	; 255
	.db #0x3f	; 63
	.db #0x1c	; 28
	.db #0x3f	; 63
	.db #0x3c	; 60
	.db #0x3d	; 61
	.db #0xfe	; 254
	.db #0x80	; 128
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x00	; 0
	.db #0x70	; 112	'p'
	.db #0x8f	; 143
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xc0	; 192
	.db #0x3f	; 63
_spr_cinematic_b:
	.db #0x01	; 1
	.db #0xfe	; 254
	.db #0x03	; 3
	.db #0xfc	; 252
	.db #0x72	; 114	'r'
	.db #0x80	; 128
	.db #0xe0	; 224
	.db #0x00	; 0
	.db #0xfe	; 254
	.db #0x00	; 0
	.db #0xf8	; 248
	.db #0x00	; 0
	.db #0xfc	; 252
	.db #0x00	; 0
	.db #0xbc	; 188
	.db #0x40	; 64
	.db #0xc0	; 192
	.db #0x00	; 0
	.db #0x0c	; 12
	.db #0x00	; 0
	.db #0x74	; 116	't'
	.db #0x08	; 8
	.db #0x11	; 17
	.db #0x78	; 120	'x'
	.db #0xb7	; 183
	.db #0x78	; 120	'x'
	.db #0xfe	; 254
	.db #0x7f	; 127
	.db #0xaf	; 175
	.db #0x5f	; 95
	.db #0x1f	; 31
	.db #0x0f	; 15
	.db #0x01	; 1
	.db #0x00	; 0
	.db #0x1f	; 31
	.db #0x00	; 0
	.db #0x37	; 55	'7'
	.db #0x00	; 0
	.db #0x13	; 19
	.db #0x20	; 32
	.db #0x02	; 2
	.db #0x64	; 100	'd'
	.db #0x53	; 83	'S'
	.db #0xec	; 236
	.db #0x17	; 23
	.db #0xf8	; 248
	.db #0x33	; 51	'3'
	.db #0xfc	; 252
	.db #0xe0	; 224
	.db #0x1f	; 31
	.db #0xc0	; 192
	.db #0x3f	; 63
	.db #0xb8	; 184
	.db #0x47	; 71	'G'
	.db #0xf0	; 240
	.db #0x0f	; 15
	.db #0xf0	; 240
	.db #0x0f	; 15
	.db #0xf0	; 240
	.db #0x0f	; 15
	.db #0xe0	; 224
	.db #0x1f	; 31
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xfe	; 254
	.db #0x00	; 0
	.db #0x7f	; 127
	.db #0x80	; 128
	.db #0x0f	; 15
	.db #0xf0	; 240
	.db #0x07	; 7
	.db #0xf8	; 248
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x01	; 1
	.db #0xff	; 255
	.db #0x80	; 128
	.db #0x7f	; 127
	.db #0xe5	; 229
	.db #0x1f	; 31
	.db #0xe1	; 225
	.db #0x1f	; 31
	.db #0x9f	; 159
	.db #0x0f	; 15
	.db #0xff	; 255
	.db #0x0f	; 15
	.db #0x99	; 153
	.db #0x7f	; 127
	.db #0x4d	; 77	'M'
	.db #0xf3	; 243
	.db #0xbb	; 187
	.db #0xc7	; 199
	.db #0x0f	; 15
	.db #0xff	; 255
	.db #0xfb	; 251
	.db #0xfc	; 252
	.db #0xfc	; 252
	.db #0xff	; 255
	.db #0xe5	; 229
	.db #0xff	; 255
	.db #0xda	; 218
	.db #0xe7	; 231
	.db #0xdc	; 220
	.db #0xe3	; 227
	.db #0xf7	; 247
	.db #0xf9	; 249
	.db #0xf5	; 245
	.db #0xfb	; 251
	.db #0xd2	; 210
	.db #0xfd	; 253
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x40	; 64
	.db #0xff	; 255
	.db #0x80	; 128
	.db #0xff	; 255
	.db #0xd0	; 208
	.db #0xef	; 239
	.db #0xbf	; 191
	.db #0xc0	; 192
	.db #0xbf	; 191
	.db #0xc0	; 192
	.db #0xbf	; 191
	.db #0xc0	; 192
	.db #0xc0	; 192
	.db #0x3f	; 63
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0x07	; 7
	.db #0xf8	; 248
	.db #0xfe	; 254
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0x04	; 4
	.db #0xfb	; 251
	.db #0x5e	; 94
	.db #0xbf	; 191
	.db #0xbb	; 187
	.db #0x7c	; 124
	.db #0xde	; 222
	.db #0x3c	; 60
	.db #0xcd	; 205
	.db #0x1e	; 30
	.db #0xe0	; 224
	.db #0x1f	; 31
	.db #0xf8	; 248
	.db #0x07	; 7
	.db #0xe0	; 224
	.db #0x1f	; 31
	.db #0x0e	; 14
	.db #0xff	; 255
	.db #0xfa	; 250
	.db #0xfd	; 253
	.db #0x5b	; 91
	.db #0xfc	; 252
	.db #0xef	; 239
	.db #0x1e	; 30
	.db #0xb6	; 182
	.db #0x4f	; 79	'O'
	.db #0x00	; 0
	.db #0xff	; 255
	.db #0x01	; 1
	.db #0xff	; 255
	.db #0x07	; 7
	.db #0xff	; 255
	.db #0x21	; 33
	.db #0xff	; 255
	.db #0x3f	; 63
	.db #0xc0	; 192
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0xf8	; 248
	.db #0x07	; 7
	.db #0xff	; 255
	.db #0x00	; 0
	.db #0x3f	; 63
	.db #0xc0	; 192
	.db #0x30	; 48	'0'
	.db #0xcf	; 207
	.db #0x07	; 7
	.db #0xff	; 255
	.db #0xff	; 255
	.db #0xff	; 255
;kaijugaiden.c:753: static void bg_fill(u8 tile) {
;	---------------------------------
; Function bg_fill
; ---------------------------------
_bg_fill:
	dec	sp
	ldhl	sp,	#0
	ld	(hl), a
;kaijugaiden.c:754: for (u8 y = 0; y < BKG_ROWS; ++y)
	ld	e, #0x00
00108$:
	ld	a, e
	sub	a, #0x12
	jr	NC, 00110$
;kaijugaiden.c:755: for (u8 x = 0; x < BKG_COLS; ++x)
	ld	d, #0x00
00105$:
	ld	a, d
	sub	a, #0x14
	jr	NC, 00109$
;kaijugaiden.c:146: set_bkg_tile_xy(x, y, tile);
	push	de
	ldhl	sp,	#2
	ld	a, (hl)
	push	af
	inc	sp
	ld	a, d
	call	_set_bkg_tile_xy
	pop	de
;kaijugaiden.c:755: for (u8 x = 0; x < BKG_COLS; ++x)
	inc	d
	jr	00105$
00109$:
;kaijugaiden.c:754: for (u8 y = 0; y < BKG_ROWS; ++y)
	inc	e
	jr	00108$
00110$:
;kaijugaiden.c:757: }
	inc	sp
	ret
;kaijugaiden.c:759: static u8 bg_char_to_tile(char ch) {
;	---------------------------------
; Function bg_char_to_tile
; ---------------------------------
_bg_char_to_tile:
;kaijugaiden.c:760: if (ch >= '0' && ch <= '9') return (u8)(TILE_FONT_0 + (ch - '0'));
	ld	c, a
	xor	a, #0x80
	sub	a, #0xb0
	jr	C, 00102$
	ld	e, c
	ld	a,#0x39
	ld	d,a
	sub	a, c
	bit	7, e
	jr	Z, 00154$
	bit	7, d
	jr	NZ, 00155$
	cp	a, a
	jr	00155$
00154$:
	bit	7, d
	jr	Z, 00155$
	scf
00155$:
	jr	C, 00102$
	ld	a, c
	add	a, #0xf0
	ret
00102$:
;kaijugaiden.c:761: if (ch >= 'A' && ch <= 'Z') return (u8)(TILE_FONT_A + (ch - 'A'));
	ld	a, c
	xor	a, #0x80
	sub	a, #0xc1
	jr	C, 00105$
	ld	e, c
	ld	a,#0x5a
	ld	d,a
	sub	a, c
	bit	7, e
	jr	Z, 00156$
	bit	7, d
	jr	NZ, 00157$
	cp	a, a
	jr	00157$
00156$:
	bit	7, d
	jr	Z, 00157$
	scf
00157$:
	jr	C, 00105$
	ld	a, c
	add	a, #0xe9
	ret
00105$:
;kaijugaiden.c:762: if (ch >= 'a' && ch <= 'z') return (u8)(TILE_FONT_A + (ch - 'a'));
	ld	a, c
	xor	a, #0x80
	sub	a, #0xe1
	jr	C, 00108$
	ld	e, c
	ld	a,#0x7a
	ld	d,a
	sub	a, c
	bit	7, e
	jr	Z, 00158$
	bit	7, d
	jr	NZ, 00159$
	cp	a, a
	jr	00159$
00158$:
	bit	7, d
	jr	Z, 00159$
	scf
00159$:
	jr	C, 00108$
	ld	a, c
	add	a, #0xc9
	ret
00108$:
;kaijugaiden.c:763: return TILE_BLANK;
	xor	a, a
;kaijugaiden.c:764: }
	ret
;kaijugaiden.c:766: static void bg_draw_text(u8 x, u8 y, const char *text) {
;	---------------------------------
; Function bg_draw_text
; ---------------------------------
_bg_draw_text:
	add	sp, #-3
	ldhl	sp,	#1
	ld	(hl+), a
;kaijugaiden.c:767: u8 start_x = x;
	ld	a, e
	ld	(hl-), a
	ld	a, (hl-)
	ld	(hl), a
;kaijugaiden.c:768: while (*text && y < BKG_ROWS) {
	ldhl	sp,	#5
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
00107$:
	ld	a, (bc)
	ld	e, a
	or	a, a
	jr	Z, 00111$
	ldhl	sp,	#2
	ld	a, (hl)
	sub	a, #0x12
	jr	NC, 00111$
;kaijugaiden.c:769: if (*text == '\n') {
	ld	a, e
	sub	a, #0x0a
	jr	NZ, 00104$
;kaijugaiden.c:770: y++;
	inc	(hl)
;kaijugaiden.c:771: x = start_x;
	dec	hl
	dec	hl
	ld	a, (hl+)
	ld	(hl), a
	jr	00105$
00104$:
;kaijugaiden.c:772: } else if (x < BKG_COLS) {
	ldhl	sp,	#1
	ld	a, (hl)
	sub	a, #0x14
	jr	NC, 00105$
;kaijugaiden.c:773: plat_set_bkg_tile(x, y, bg_char_to_tile(*text));
	push	bc
	ld	a, e
	call	_bg_char_to_tile
;kaijugaiden.c:146: set_bkg_tile_xy(x, y, tile);
	push	af
	inc	sp
	ldhl	sp,	#5
	ld	a, (hl-)
	ld	e, a
	ld	a, (hl)
	call	_set_bkg_tile_xy
	pop	bc
;kaijugaiden.c:774: x++;
	ldhl	sp,	#1
	inc	(hl)
00105$:
;kaijugaiden.c:776: text++;
	inc	bc
	jr	00107$
00111$:
;kaijugaiden.c:778: }
	add	sp, #3
	pop	hl
	pop	af
	jp	(hl)
;kaijugaiden.c:780: static char password_nibble_to_hex(u8 value) {
;	---------------------------------
; Function password_nibble_to_hex
; ---------------------------------
_password_nibble_to_hex:
;kaijugaiden.c:781: value &= 0x0F;
	and	a, #0x0f
;kaijugaiden.c:782: return (value < 10) ? (char)('0' + value) : (char)('A' + (value - 10));
	ld	c, a
	sub	a, #0x0a
	jr	NC, 00103$
	ld	a, c
	add	a, #0x30
	ret
00103$:
	ld	a, c
	add	a, #0x37
;kaijugaiden.c:783: }
	ret
;kaijugaiden.c:785: static u8 password_hex_to_nibble(char ch) {
;	---------------------------------
; Function password_hex_to_nibble
; ---------------------------------
_password_hex_to_nibble:
;kaijugaiden.c:786: if (ch >= '0' && ch <= '9') return (u8)(ch - '0');
	ld	c, a
	xor	a, #0x80
	sub	a, #0xb0
	jr	C, 00102$
	ld	e, c
	ld	a,#0x39
	ld	d,a
	sub	a, c
	bit	7, e
	jr	Z, 00154$
	bit	7, d
	jr	NZ, 00155$
	cp	a, a
	jr	00155$
00154$:
	bit	7, d
	jr	Z, 00155$
	scf
00155$:
	jr	C, 00102$
	ld	a, c
	add	a, #0xd0
	ret
00102$:
;kaijugaiden.c:787: if (ch >= 'A' && ch <= 'F') return (u8)(10 + (ch - 'A'));
	ld	a, c
	xor	a, #0x80
	sub	a, #0xc1
	jr	C, 00105$
	ld	e, c
	ld	a,#0x46
	ld	d,a
	sub	a, c
	bit	7, e
	jr	Z, 00156$
	bit	7, d
	jr	NZ, 00157$
	cp	a, a
	jr	00157$
00156$:
	bit	7, d
	jr	Z, 00157$
	scf
00157$:
	jr	C, 00105$
	ld	a, c
	add	a, #0xc9
	ret
00105$:
;kaijugaiden.c:788: if (ch >= 'a' && ch <= 'f') return (u8)(10 + (ch - 'a'));
	ld	a, c
	xor	a, #0x80
	sub	a, #0xe1
	jr	C, 00108$
	ld	e, c
	ld	a,#0x66
	ld	d,a
	sub	a, c
	bit	7, e
	jr	Z, 00158$
	bit	7, d
	jr	NZ, 00159$
	cp	a, a
	jr	00159$
00158$:
	bit	7, d
	jr	Z, 00159$
	scf
00159$:
	jr	C, 00108$
	ld	a, c
	add	a, #0xa9
	ret
00108$:
;kaijugaiden.c:789: return 0xFF;
	ld	a, #0xff
;kaijugaiden.c:790: }
	ret
;kaijugaiden.c:792: static void password_encode(char *out, u32 cleared_bosses, u32 cyphers) {
;	---------------------------------
; Function password_encode
; ---------------------------------
_password_encode:
	add	sp, #-6
	ld	c, e
	ld	b, d
;kaijugaiden.c:793: for (u8 i = 0; i < 8; ++i) {
	ldhl	sp,	#5
	ld	(hl), #0x00
00103$:
	ldhl	sp,	#5
	ld	a, (hl)
	sub	a, #0x08
	jp	NC, 00101$
;kaijugaiden.c:794: u8 shift = (u8)((7 - i) * 4);
	ld	a, #0x07
	sub	a, (hl)
	dec	hl
	add	a, a
	add	a, a
;kaijugaiden.c:795: out[i]     = password_nibble_to_hex((u8)((cleared_bosses >> shift) & 0x0F));
	ld	(hl+), a
	ld	l, (hl)
	ld	h, #0x00
	add	hl, bc
	ld	e, l
	ld	d, h
	ldhl	sp,	#4
	ld	a, (hl)
	push	af
	ldhl	sp,	#10
	ld	a, (hl)
	ldhl	sp,	#2
	ld	(hl), a
	ldhl	sp,	#11
	ld	a, (hl)
	ldhl	sp,	#3
	ld	(hl), a
	ldhl	sp,	#12
	ld	a, (hl)
	ldhl	sp,	#4
	ld	(hl), a
	ldhl	sp,	#13
	ld	a, (hl)
	ldhl	sp,	#5
	ld	(hl), a
	pop	af
	inc	a
	jr	00123$
00122$:
	ldhl	sp,	#3
	srl	(hl)
	dec	hl
	rr	(hl)
	dec	hl
	rr	(hl)
	dec	hl
	rr	(hl)
00123$:
	dec	a
	jr	NZ, 00122$
	ldhl	sp,	#0
	ld	a, (hl)
	and	a, #0x0f
	push	bc
	push	de
	call	_password_nibble_to_hex
	pop	de
	pop	bc
	ld	(de), a
;kaijugaiden.c:796: out[8 + i] = password_nibble_to_hex((u8)((cyphers >> shift) & 0x0F));
	ldhl	sp,	#5
	ld	a, (hl-)
	add	a, #0x08
	add	a, c
	ld	e, a
	ld	a, #0x00
	adc	a, b
	ld	d, a
	ld	a, (hl)
	push	af
	ldhl	sp,	#14
	ld	a, (hl)
	ldhl	sp,	#3
	ld	(hl), a
	ldhl	sp,	#15
	ld	a, (hl)
	ldhl	sp,	#4
	ld	(hl), a
	ldhl	sp,	#16
	ld	a, (hl)
	ldhl	sp,	#5
	ld	(hl), a
	ldhl	sp,	#17
	ld	a, (hl)
	ldhl	sp,	#6
	ld	(hl), a
	pop	af
	inc	a
	jr	00125$
00124$:
	ldhl	sp,	#4
	srl	(hl)
	dec	hl
	rr	(hl)
	dec	hl
	rr	(hl)
	dec	hl
	rr	(hl)
00125$:
	dec	a
	jr	NZ, 00124$
	ldhl	sp,	#1
	ld	a, (hl)
	and	a, #0x0f
	push	bc
	push	de
	call	_password_nibble_to_hex
	pop	de
	pop	bc
	ld	(de), a
;kaijugaiden.c:793: for (u8 i = 0; i < 8; ++i) {
	ldhl	sp,	#5
	inc	(hl)
	jp	00103$
00101$:
;kaijugaiden.c:798: out[PASSWORD_LEN] = '\0';
	ld	hl, #0x0010
	add	hl, bc
	ld	(hl), #0x00
;kaijugaiden.c:799: }
	add	sp, #6
	pop	hl
	add	sp, #8
	jp	(hl)
;kaijugaiden.c:801: static int password_decode(const char *pwd, u32 *out_cleared_bosses, u32 *out_cyphers) {
;	---------------------------------
; Function password_decode
; ---------------------------------
_password_decode:
	add	sp, #-17
	ldhl	sp,	#15
	ld	a, e
	ld	(hl+), a
	ld	(hl), d
	ldhl	sp,	#13
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;kaijugaiden.c:802: u32 cleared_bosses = 0;
	xor	a, a
	ldhl	sp,	#0
	ld	(hl+), a
	ld	(hl+), a
	ld	(hl+), a
;kaijugaiden.c:803: u32 cyphers = 0;
	ld	(hl+), a
	xor	a, a
	ld	(hl+), a
	ld	(hl+), a
	ld	(hl+), a
	ld	(hl), a
;kaijugaiden.c:804: for (u8 i = 0; i < 8; ++i) {
	ld	c, #0x00
00110$:
	ld	a, c
	sub	a, #0x08
	jp	NC, 00104$
;kaijugaiden.c:805: u8 high = password_hex_to_nibble(pwd[i]);
	ldhl	sp,#15
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	l, c
	ld	h, #0x00
	add	hl, de
	ld	e, l
	ld	d, h
	ld	a, (de)
	push	bc
	call	_password_hex_to_nibble
	pop	bc
	ld	b, a
;kaijugaiden.c:806: u8 low  = password_hex_to_nibble(pwd[8 + i]);
	ld	a, c
	add	a, #0x08
	ld	e, a
	ld	d, #0x00
	ldhl	sp,	#15
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	ld	e, l
	ld	d, h
	ld	a, (de)
	push	bc
	call	_password_hex_to_nibble
	ldhl	sp,	#10
	ld	(hl), a
	pop	bc
;kaijugaiden.c:807: if (high == 0xFF || low == 0xFF) return -1;
	ld	a, b
	inc	a
	jr	Z, 00101$
	ldhl	sp,	#8
	ld	a, (hl)
	inc	a
	jr	NZ, 00102$
00101$:
	ld	bc, #0xffff
	jp	00112$
00102$:
;kaijugaiden.c:808: cleared_bosses = (cleared_bosses << 4) | high;
	push	af
	ldhl	sp,	#2
	ld	a, (hl)
	ldhl	sp,	#11
	ld	(hl), a
	ldhl	sp,	#3
	ld	a, (hl)
	ldhl	sp,	#12
	ld	(hl), a
	ldhl	sp,	#4
	ld	a, (hl)
	ldhl	sp,	#13
	ld	(hl), a
	ldhl	sp,	#5
	ld	a, (hl)
	ldhl	sp,	#14
	ld	(hl), a
	pop	af
	ld	a, #0x04
00152$:
	ldhl	sp,	#9
	sla	(hl)
	inc	hl
	rl	(hl)
	inc	hl
	rl	(hl)
	inc	hl
	rl	(hl)
	dec	a
	jr	NZ,00152$
	ld	e, b
	xor	a, a
	ld	d, a
	push	af
	ldhl	sp,	#11
	ld	a, (hl)
	or	a, e
	ldhl	sp,	#2
	ld	(hl), a
	ldhl	sp,	#12
	ld	a, (hl)
	or	a, d
	ldhl	sp,	#3
	ld	(hl), a
	pop	af
	ldhl	sp,	#11
	ld	a, (hl)
	ldhl	sp,	#2
	ld	(hl), a
	ldhl	sp,	#12
	ld	a, (hl)
	ldhl	sp,	#3
;kaijugaiden.c:809: cyphers        = (cyphers << 4) | low;
	ld	(hl+), a
	push	af
	ld	a, (hl)
	ldhl	sp,	#11
	ld	(hl), a
	ldhl	sp,	#7
	ld	a, (hl)
	ldhl	sp,	#12
	ld	(hl), a
	ldhl	sp,	#8
	ld	a, (hl)
	ldhl	sp,	#13
	ld	(hl), a
	ldhl	sp,	#9
	ld	a, (hl)
	ldhl	sp,	#14
	ld	(hl), a
	pop	af
	ld	a, #0x04
00154$:
	ldhl	sp,	#9
	sla	(hl)
	inc	hl
	rl	(hl)
	inc	hl
	rl	(hl)
	inc	hl
	rl	(hl)
	dec	a
	jr	NZ,00154$
	ldhl	sp,	#8
	ld	a, (hl+)
	ld	e, a
	xor	a, a
	ld	d, a
	ld	b, a
	push	af
	ld	a, (hl)
	or	a, e
	ldhl	sp,	#6
	ld	(hl), a
	ldhl	sp,	#12
	ld	a, (hl)
	or	a, d
	ldhl	sp,	#7
	ld	(hl), a
	pop	af
	ldhl	sp,	#11
	ld	a, (hl)
	ldhl	sp,	#6
	ld	(hl), a
	ldhl	sp,	#12
	ld	a, (hl)
	ldhl	sp,	#7
	ld	(hl), a
;kaijugaiden.c:804: for (u8 i = 0; i < 8; ++i) {
	inc	c
	jp	00110$
00104$:
;kaijugaiden.c:811: if (out_cleared_bosses) *out_cleared_bosses = cleared_bosses;
	ldhl	sp,	#14
	ld	a, (hl-)
	or	a, (hl)
	jr	Z, 00106$
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ldhl	sp,	#0
	ld	a, (hl+)
	ld	(de), a
	inc	de
	ld	a, (hl+)
	ld	(de), a
	inc	de
	ld	a, (hl+)
	ld	(de), a
	inc	de
	ld	a, (hl)
	ld	(de), a
00106$:
;kaijugaiden.c:812: if (out_cyphers) *out_cyphers = cyphers;
	ldhl	sp,	#20
	ld	a, (hl-)
	or	a, (hl)
	jr	Z, 00108$
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	ldhl	sp,	#4
	ld	a, (hl+)
	ld	(bc), a
	inc	bc
	ld	a, (hl+)
	ld	(bc), a
	inc	bc
	ld	a, (hl+)
	ld	(bc), a
	inc	bc
	ld	a, (hl)
	ld	(bc), a
00108$:
;kaijugaiden.c:813: return 0;
	ld	bc, #0x0000
00112$:
;kaijugaiden.c:814: }
	add	sp, #17
	pop	hl
	pop	af
	jp	(hl)
;kaijugaiden.c:822: static void bg_draw_beach(void) {
;	---------------------------------
; Function bg_draw_beach
; ---------------------------------
_bg_draw_beach:
	add	sp, #-6
;kaijugaiden.c:823: s8 bg_x = gs.camera_bg_x;
	ld	hl, #_gs + 123
	ld	c, (hl)
;kaijugaiden.c:824: s8 bg_y = gs.camera_bg_y;
	ld	hl, #_gs + 124
	ld	b, (hl)
;kaijugaiden.c:825: u8 water_tile = ((gs.anim_tick >> 3) & 1) ? TILE_WATER_A : TILE_WATER_B;
	ld	a, (#_gs + 118)
	rrca
	rrca
	rrca
	and	a, #0x01
	ld	a, #0x03
	jr	NZ, 00122$
	ld	a, #0x04
00122$:
	ldhl	sp,	#0
	ld	(hl), a
;kaijugaiden.c:826: u8 water_start = (bg_y <= -1) ? 10 : (bg_y >= 1) ? 12 : 11;
	ld	e, b
	ld	a,#0xff
	ld	d,a
	sub	a, b
	bit	7, e
	jr	Z, 00244$
	bit	7, d
	jr	NZ, 00245$
	cp	a, a
	jr	00245$
00244$:
	bit	7, d
	jr	Z, 00245$
	scf
00245$:
	jr	C, 00123$
	ld	b, #0x0a
	jr	00124$
00123$:
	ld	a, b
	xor	a, #0x80
	sub	a, #0x81
	jr	C, 00125$
	ld	b, #0x0c
	jr	00126$
00125$:
	ld	b, #0x0b
00126$:
00124$:
;kaijugaiden.c:827: u8 ground_split = (bg_x <= -1) ? 9 : (bg_x >= 1) ? 11 : 10;
	ld	e, c
	ld	a,#0xff
	ld	d,a
	sub	a, c
	bit	7, e
	jr	Z, 00246$
	bit	7, d
	jr	NZ, 00247$
	cp	a, a
	jr	00247$
00246$:
	bit	7, d
	jr	Z, 00247$
	scf
00247$:
	jr	C, 00127$
	ld	a, #0x09
	jr	00128$
00127$:
	ld	a, c
	xor	a, #0x80
	sub	a, #0x81
	jr	C, 00129$
	ld	a, #0x0b
	jr	00130$
00129$:
	ld	a, #0x0a
00130$:
00128$:
	ldhl	sp,	#1
;kaijugaiden.c:828: for (u8 row = 0; row < BKG_ROWS; ++row) {
	ld	(hl+), a
	ld	a, c
	sub	a, #0x01
	ld	a, #0x00
	rla
	xor	a, #0x01
	ld	(hl), a
	ld	e, #0x00
00117$:
	ld	a, e
	sub	a, #0x12
	jr	NC, 00119$
;kaijugaiden.c:829: for (u8 col = 0; col < BKG_COLS; ++col) {
	ld	a, e
	sub	a, b
	ld	a, #0x00
	rla
	ldhl	sp,	#3
	ld	(hl), a
	ld	c, #0x00
00114$:
	ld	a, c
	sub	a, #0x14
	jr	NC, 00118$
;kaijugaiden.c:831: if (row < water_start)       t = ((row + col + (bg_x != 0)) % 2) ? TILE_SKY_A : TILE_SKY_B;
	ldhl	sp,	#3
	ld	a, (hl)
	or	a, a
	jr	Z, 00108$
	dec	hl
	ld	a, e
	ld	d, c
	add	a, d
	ld	d, (hl)
	add	a, d
	and	a, #0x01
	jr	Z, 00131$
	ld	d, #0x07
	jr	00109$
00131$:
	ld	d, #0x08
	jr	00109$
00108$:
;kaijugaiden.c:832: else if (row < water_start + 3)  t = water_tile;
	ld	l, b
	ld	h, l
	inc	h
	inc	h
	inc	h
	ld	d, e
	ld	a, d
	sub	a, h
	jr	NC, 00105$
	ldhl	sp,	#0
	ld	d, (hl)
	jr	00109$
00105$:
;kaijugaiden.c:833: else if (row < water_start + 5)  t = (col < ground_split) ? TILE_GROUND_L : TILE_GROUND_R;
	ld	a, l
	add	a, #0x05
	ldhl	sp,	#4
	ld	(hl), a
	ld	a, c
	ldhl	sp,	#1
	sub	a, (hl)
	ld	a, #0x00
	rla
	ldhl	sp,	#5
	ld	(hl-), a
	ld	a, d
	sub	a, (hl)
	jr	NC, 00102$
	inc	hl
	ld	a, (hl)
	or	a, a
	jr	Z, 00133$
	ld	d, #0x01
	jr	00109$
00133$:
	ld	d, #0x02
	jr	00109$
00102$:
;kaijugaiden.c:834: else                             t = (col < ground_split) ? TILE_CLIFF_A  : TILE_CLIFF_B;
	ldhl	sp,	#5
	ld	a, (hl)
	or	a, a
	jr	Z, 00135$
	ld	d, #0x05
	jr	00136$
00135$:
	ld	d, #0x06
00136$:
00109$:
;kaijugaiden.c:146: set_bkg_tile_xy(x, y, tile);
	push	bc
	push	de
	push	de
	inc	sp
	ld	a, c
	call	_set_bkg_tile_xy
	pop	de
	pop	bc
;kaijugaiden.c:829: for (u8 col = 0; col < BKG_COLS; ++col) {
	inc	c
	jr	00114$
00118$:
;kaijugaiden.c:828: for (u8 row = 0; row < BKG_ROWS; ++row) {
	inc	e
	jr	00117$
00119$:
;kaijugaiden.c:838: }
	add	sp, #6
	ret
;kaijugaiden.c:841: static void bg_draw_splash(void) {
;	---------------------------------
; Function bg_draw_splash
; ---------------------------------
_bg_draw_splash:
;kaijugaiden.c:842: bg_fill(TILE_BLANK);
	xor	a, a
	call	_bg_fill
;kaijugaiden.c:845: for (u8 row = 0; row < 2; ++row)
	ld	c, #0x00
00111$:
	ld	a, c
	sub	a, #0x02
	jr	NC, 00102$
;kaijugaiden.c:846: for (u8 col = 0; col < 4; ++col)
	ld	b, #0x00
00108$:
	ld	a, b
	sub	a, #0x04
	jr	NC, 00112$
;kaijugaiden.c:847: plat_set_bkg_tile(8 + col, 6 + row, start_tile + row * 4 + col);
	ld	a, c
	add	a, a
	add	a, a
	add	a, #0x09
	ld	l, b
	add	a, l
	ld	d, a
	ld	a, c
	add	a, #0x06
	ld	e, a
	ld	a, l
	add	a, #0x08
;kaijugaiden.c:146: set_bkg_tile_xy(x, y, tile);
	push	bc
	push	de
	inc	sp
	call	_set_bkg_tile_xy
	pop	bc
;kaijugaiden.c:846: for (u8 col = 0; col < 4; ++col)
	inc	b
	jr	00108$
00112$:
;kaijugaiden.c:845: for (u8 row = 0; row < 2; ++row)
	inc	c
	jr	00111$
00102$:
;kaijugaiden.c:146: set_bkg_tile_xy(x, y, tile);
	ld	a, #0x2f
	push	af
	inc	sp
	ld	e, #0x0a
	ld	a, #0x07
	call	_set_bkg_tile_xy
	ld	a, #0x2a
	push	af
	inc	sp
	ld	e, #0x0a
	ld	a, #0x08
	call	_set_bkg_tile_xy
	ld	a, #0x37
	push	af
	inc	sp
	ld	e, #0x0a
	ld	a, #0x09
	call	_set_bkg_tile_xy
;kaijugaiden.c:851: plat_set_bkg_tile(9, 10, TILE_FONT_A + 13);  /* n */
;kaijugaiden.c:852: }
	ret
;kaijugaiden.c:855: static void bg_draw_title(void) {
;	---------------------------------
; Function bg_draw_title
; ---------------------------------
_bg_draw_title:
;kaijugaiden.c:856: bg_fill(TILE_BLANK);
	xor	a, a
	call	_bg_fill
;kaijugaiden.c:859: for (u8 row = 0; row < 4; ++row)
	ld	c, #0x00
00109$:
	ld	a, c
	sub	a, #0x04
	jr	NC, 00102$
;kaijugaiden.c:860: for (u8 col = 0; col < 3; ++col)
	ld	b, #0x00
00106$:
	ld	a, b
	sub	a, #0x03
	jr	NC, 00110$
;kaijugaiden.c:861: plat_set_bkg_tile(8 + col, 3 + row, start + row * 3 + col);
	ld	a, c
	ld	e, a
	add	a, a
	add	a, e
	add	a, #0x11
	ld	l, b
	add	a, l
	ld	d, a
	ld	a, c
	add	a, #0x03
	ld	e, a
	ld	a, l
	add	a, #0x08
;kaijugaiden.c:146: set_bkg_tile_xy(x, y, tile);
	push	bc
	push	de
	inc	sp
	call	_set_bkg_tile_xy
	pop	bc
;kaijugaiden.c:860: for (u8 col = 0; col < 3; ++col)
	inc	b
	jr	00106$
00110$:
;kaijugaiden.c:859: for (u8 row = 0; row < 4; ++row)
	inc	c
	jr	00109$
00102$:
;kaijugaiden.c:862: bg_draw_text(7, 9, "START");
	ld	de, #___str_0
	push	de
	ld	e, #0x09
	ld	a, #0x07
	call	_bg_draw_text
;kaijugaiden.c:863: bg_draw_text(5, 10, "PASSWORD");
	ld	de, #___str_1
	push	de
	ld	e, #0x0a
	ld	a, #0x05
	call	_bg_draw_text
;kaijugaiden.c:864: plat_set_bkg_tile(4, 9 + gs.menu_sel, TILE_CLIFF_A);
	ld	a, (#(_gs + 82) + 0)
	add	a, #0x09
;kaijugaiden.c:146: set_bkg_tile_xy(x, y, tile);
	ld	h, #0x05
	push	hl
	inc	sp
	ld	e, a
	ld	a, #0x04
	call	_set_bkg_tile_xy
;kaijugaiden.c:864: plat_set_bkg_tile(4, 9 + gs.menu_sel, TILE_CLIFF_A);
;kaijugaiden.c:865: }
	ret
___str_0:
	.ascii "START"
	.db 0x00
___str_1:
	.ascii "PASSWORD"
	.db 0x00
;kaijugaiden.c:868: static void bg_draw_number_2(u8 tx, u8 ty, u8 val) {
;	---------------------------------
; Function bg_draw_number_2
; ---------------------------------
_bg_draw_number_2:
	dec	sp
	ld	c, a
	ldhl	sp,	#0
	ld	(hl), e
;kaijugaiden.c:869: plat_set_bkg_tile(tx,   ty, TILE_FONT_0 + (val / 10) % 10);
	ldhl	sp,	#3
	ld	b, (hl)
	push	bc
	ld	e, #0x0a
	ld	a, b
	call	__divuchar
	ld	a, c
	ld	e, #0x0a
	call	__moduchar
	ld	a, c
	pop	bc
	add	a, #0x20
;kaijugaiden.c:146: set_bkg_tile_xy(x, y, tile);
	push	bc
	push	af
	inc	sp
	ldhl	sp,	#3
	ld	e, (hl)
	ld	a, c
	call	_set_bkg_tile_xy
	pop	bc
;kaijugaiden.c:870: plat_set_bkg_tile(tx+1, ty, TILE_FONT_0 + val % 10);
	push	bc
	ld	e, #0x0a
	ld	a, b
	call	__moduchar
	ld	a, c
	pop	bc
	add	a, #0x20
	inc	c
;kaijugaiden.c:146: set_bkg_tile_xy(x, y, tile);
	push	af
	inc	sp
	ldhl	sp,	#1
	ld	e, (hl)
	ld	a, c
	call	_set_bkg_tile_xy
;kaijugaiden.c:870: plat_set_bkg_tile(tx+1, ty, TILE_FONT_0 + val % 10);
;kaijugaiden.c:871: }
	inc	sp
	pop	hl
	inc	sp
	jp	(hl)
;kaijugaiden.c:873: static void bg_clear_row(u8 y) {
;	---------------------------------
; Function bg_clear_row
; ---------------------------------
_bg_clear_row:
	ld	e, a
;kaijugaiden.c:874: for (u8 x = 0; x < BKG_COLS; ++x)
	ld	d, #0x00
00104$:
	ld	a, d
	sub	a, #0x14
	ret	NC
;kaijugaiden.c:146: set_bkg_tile_xy(x, y, tile);
	push	de
	xor	a, a
	push	af
	inc	sp
	ld	a, d
	call	_set_bkg_tile_xy
	pop	de
;kaijugaiden.c:874: for (u8 x = 0; x < BKG_COLS; ++x)
	inc	d
;kaijugaiden.c:876: }
	jr	00104$
;kaijugaiden.c:878: static u8 combat_minions_alive(void) {
;	---------------------------------
; Function combat_minions_alive
; ---------------------------------
_combat_minions_alive:
;kaijugaiden.c:880: for (u8 i = 0; i < MINION_MAX; ++i)
	ld	bc, #0x0
00105$:
	ld	a, c
	sub	a, #0x05
	jr	NC, 00103$
;kaijugaiden.c:881: if (gs.minions[i].active) count++;
	ld	l, c
	add	hl, hl
	add	hl, hl
	add	hl, hl
	add	hl, bc
	ld	h, #0x00
	ld	de, #(_gs + 31)
	add	hl, de
	ld	a, (hl)
	or	a, a
	jr	Z, 00106$
	inc	b
00106$:
;kaijugaiden.c:880: for (u8 i = 0; i < MINION_MAX; ++i)
	inc	c
	jr	00105$
00103$:
;kaijugaiden.c:882: return count;
	ld	a, b
;kaijugaiden.c:883: }
	ret
;kaijugaiden.c:885: static u8 attack_hits_target(s16 player_center, u8 facing_left, s16 target_center, u8 forward_range, u8 rear_range) {
;	---------------------------------
; Function attack_hits_target
; ---------------------------------
_attack_hits_target:
	add	sp, #-3
	ld	c, e
	ld	b, d
	ldhl	sp,	#2
	ld	(hl), a
;kaijugaiden.c:886: s16 delta = target_center - player_center;
	ldhl	sp,#5
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, e
	sub	a, c
	ld	e, a
	ld	a, d
	sbc	a, b
	ld	b, a
	ld	c, e
;kaijugaiden.c:887: if (facing_left) delta = -delta;
	ldhl	sp,	#2
	ld	a, (hl)
	or	a, a
	jr	Z, 00102$
	xor	a, a
	sub	a, c
	ld	c, a
	sbc	a, a
	sub	a, b
	ld	b, a
00102$:
;kaijugaiden.c:888: if (delta >= 0) return delta <= forward_range;
	ld	h, b
	bit	7, h
	jr	NZ, 00104$
	ldhl	sp,	#7
	ld	a, (hl)
	ldhl	sp,	#0
	ld	(hl+), a
	xor	a, a
	ld	(hl-), a
	ld	a, (hl+)
	sub	a, c
	ld	a, (hl)
	sbc	a, b
	ld	d, (hl)
	ld	a, b
	ld	e, a
	bit	7, e
	jr	Z, 00121$
	bit	7, d
	jr	NZ, 00122$
	cp	a, a
	jr	00122$
00121$:
	bit	7, d
	jr	Z, 00122$
	scf
00122$:
	ld	a, #0x00
	rla
	xor	a, #0x01
	jr	00105$
00104$:
;kaijugaiden.c:889: return (-delta) <= rear_range;
	xor	a, a
	sub	a, c
	ld	c, a
	sbc	a, a
	sub	a, b
	ld	b, a
	ldhl	sp,	#8
	ld	a, (hl)
	ldhl	sp,	#0
	ld	(hl+), a
	xor	a, a
	ld	(hl-), a
	ld	a, (hl+)
	sub	a, c
	ld	a, (hl)
	sbc	a, b
	ld	d, (hl)
	ld	a, b
	ld	e, a
	bit	7, e
	jr	Z, 00123$
	bit	7, d
	jr	NZ, 00124$
	cp	a, a
	jr	00124$
00123$:
	bit	7, d
	jr	Z, 00124$
	scf
00124$:
	ld	a, #0x00
	rla
	xor	a, #0x01
00105$:
;kaijugaiden.c:890: }
	add	sp, #3
	pop	hl
	add	sp, #4
	jp	(hl)
;kaijugaiden.c:892: static u8 abs_distance_u8(s16 a, s16 b) {
;	---------------------------------
; Function abs_distance_u8
; ---------------------------------
_abs_distance_u8:
	ld	a, e
;kaijugaiden.c:893: s16 d = a - b;
	sub	a, c
	ld	c, a
	ld	a, d
	sbc	a, b
;kaijugaiden.c:894: if (d < 0) d = -d;
	bit	7,a
	jr	Z, 00102$
	xor	a, a
	sub	a, c
	ld	c, a
00102$:
;kaijugaiden.c:895: return (u8)d;
	ld	a, c
;kaijugaiden.c:896: }
	ret
;kaijugaiden.c:898: static s8 clamp_s8(s16 value, s8 min_value, s8 max_value) {
;	---------------------------------
; Function clamp_s8
; ---------------------------------
_clamp_s8:
	add	sp, #-3
	ldhl	sp,	#1
	ld	(hl), e
	inc	hl
	ld	(hl), d
	dec	hl
	dec	hl
;kaijugaiden.c:899: if (value < min_value) return min_value;
	ld	(hl+), a
	ld	c, a
	rlca
	sbc	a, a
	ld	b, a
	ld	a, (hl+)
	sub	a, c
	ld	a, (hl)
	sbc	a, b
	ld	d, (hl)
	ld	a, b
	ld	e, a
	bit	7, e
	jr	Z, 00121$
	bit	7, d
	jr	NZ, 00122$
	cp	a, a
	jr	00122$
00121$:
	bit	7, d
	jr	Z, 00122$
	scf
00122$:
	jr	NC, 00102$
	ldhl	sp,	#0
	ld	a, (hl)
	jr	00105$
00102$:
;kaijugaiden.c:900: if (value > max_value) return max_value;
	ldhl	sp,	#5
	ld	a, (hl)
	ld	c, a
	rlca
	sbc	a, a
	ld	b, a
	ldhl	sp,	#1
	ld	a, c
	sub	a, (hl)
	inc	hl
	ld	a, b
	sbc	a, (hl)
	ld	a, b
	ld	d, a
	ld	e, (hl)
	bit	7, e
	jr	Z, 00123$
	bit	7, d
	jr	NZ, 00124$
	cp	a, a
	jr	00124$
00123$:
	bit	7, d
	jr	Z, 00124$
	scf
00124$:
	jr	NC, 00104$
	ldhl	sp,	#5
	ld	a, (hl)
	jr	00105$
00104$:
;kaijugaiden.c:901: return (s8)value;
	ldhl	sp,	#1
	ld	a, (hl)
00105$:
;kaijugaiden.c:902: }
	add	sp, #3
	pop	hl
	inc	sp
	jp	(hl)
;kaijugaiden.c:904: static void combat_set_banner(u8 kind, u8 timer) {
;	---------------------------------
; Function combat_set_banner
; ---------------------------------
_combat_set_banner:
	ld	c, a
;kaijugaiden.c:905: gs.banner_kind = kind;
	ld	hl, #_gs + 120
	ld	(hl), c
;kaijugaiden.c:906: gs.banner_timer = timer;
	ld	hl, #_gs + 119
	ld	(hl), e
;kaijugaiden.c:907: }
	ret
;kaijugaiden.c:909: static void input_capture_frame(void) {
;	---------------------------------
; Function input_capture_frame
; ---------------------------------
_input_capture_frame:
;kaijugaiden.c:910: gs.input_held_mask = plat_input_mask();
;kaijugaiden.c:140: static inline u16 plat_input_mask(void) { return (u16)_joy_cur; }
	ld	a, (__joy_cur)
	ld	c, a
	ld	b, #0x00
;kaijugaiden.c:910: gs.input_held_mask = plat_input_mask();
	ld	hl, #(_gs + 127)
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;kaijugaiden.c:911: gs.input_pressed_mask = plat_pressed_mask();
;kaijugaiden.c:141: static inline u16 plat_pressed_mask(void) { return (u16)(_joy_cur & (u8)(~_joy_prev)); }
	ld	a, (#__joy_prev)
	cpl
	ld	hl, #__joy_cur
	and	a, (hl)
	ld	c, a
	ld	b, #0x00
;kaijugaiden.c:911: gs.input_pressed_mask = plat_pressed_mask();
	ld	hl, #(_gs + 129)
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;kaijugaiden.c:912: if (gs.input_held_mask != 0) gs.input_active_frames++;
	ld	hl, #(_gs + 127)
	ld	a, (hl+)
	or	a, (hl)
	jr	Z, 00102$
	ld	hl, #(_gs + 133)
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	inc	bc
	ld	hl, #(_gs + 133)
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
00102$:
;kaijugaiden.c:913: if (gs.input_pressed_mask != 0) gs.input_edge_total++;
	ld	hl, #(_gs + 129)
	ld	a, (hl+)
	or	a, (hl)
	ret	Z
	ld	hl, #(_gs + 131)
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	inc	bc
	ld	hl, #(_gs + 131)
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;kaijugaiden.c:914: }
	ret
;kaijugaiden.c:916: static void camera_reset(void) {
;	---------------------------------
; Function camera_reset
; ---------------------------------
_camera_reset:
;kaijugaiden.c:917: gs.camera_x = 0;
	ld	hl, #_gs + 121
	ld	(hl), #0x00
;kaijugaiden.c:918: gs.camera_y = 0;
	ld	hl, #_gs + 122
	ld	(hl), #0x00
;kaijugaiden.c:919: gs.camera_bg_x = 0;
	ld	hl, #_gs + 123
	ld	(hl), #0x00
;kaijugaiden.c:920: gs.camera_bg_y = 0;
	ld	hl, #_gs + 124
	ld	(hl), #0x00
;kaijugaiden.c:921: gs.camera_shake_timer = 0;
	ld	hl, #_gs + 125
	ld	(hl), #0x00
;kaijugaiden.c:922: gs.camera_shake_mag = 0;
	ld	hl, #_gs + 126
	ld	(hl), #0x00
;kaijugaiden.c:923: }
	ret
;kaijugaiden.c:925: static void camera_punch(u8 magnitude, u8 timer) {
;	---------------------------------
; Function camera_punch
; ---------------------------------
_camera_punch:
	ld	c, a
;kaijugaiden.c:926: if (magnitude > gs.camera_shake_mag) gs.camera_shake_mag = magnitude;
	ld	hl, #_gs + 126
	ld	a, (hl)
	sub	a, c
	jr	NC, 00102$
	ld	(hl), c
00102$:
;kaijugaiden.c:927: if (timer > gs.camera_shake_timer) gs.camera_shake_timer = timer;
	ld	hl, #_gs + 125
	ld	a, (hl)
	sub	a, e
	ret	NC
	ld	(hl), e
;kaijugaiden.c:928: }
	ret
;kaijugaiden.c:930: static s8 camera_shake_x(void) {
;	---------------------------------
; Function camera_shake_x
; ---------------------------------
_camera_shake_x:
;kaijugaiden.c:931: if (gs.camera_shake_timer == 0 || gs.camera_shake_mag == 0) return 0;
	ld	a, (#(_gs + 125) + 0)
	or	a, a
	jr	Z, 00101$
	ld	hl, #_gs + 126
	ld	c, (hl)
	ld	a, c
	or	a, a
	jr	NZ, 00102$
00101$:
	xor	a, a
	ret
00102$:
;kaijugaiden.c:932: return (gs.anim_tick & 0x01) ? (s8)gs.camera_shake_mag : (s8)(-(s8)gs.camera_shake_mag);
	ld	a, (#(_gs + 118) + 0)
	rrca
	jr	C, 00107$
	xor	a, a
	sub	a, c
	ld	c, a
00107$:
	ld	a, c
;kaijugaiden.c:933: }
	ret
;kaijugaiden.c:935: static s8 camera_shake_y(void) {
;	---------------------------------
; Function camera_shake_y
; ---------------------------------
_camera_shake_y:
;kaijugaiden.c:936: if (gs.camera_shake_timer == 0 || gs.camera_shake_mag == 0) return 0;
	ld	a, (#(_gs + 125) + 0)
	or	a, a
	jr	Z, 00101$
	ld	hl, #_gs + 126
	ld	c, (hl)
	ld	a, c
	or	a, a
	jr	NZ, 00102$
00101$:
	xor	a, a
	ret
00102$:
;kaijugaiden.c:937: return (gs.anim_tick & 0x02) ? (s8)(gs.camera_shake_mag >> 1) : 0;
	ld	a, (#(_gs + 118) + 0)
	bit	1, a
	jr	Z, 00106$
	ld	a, c
	srl	a
	ret
00106$:
	xor	a, a
;kaijugaiden.c:938: }
	ret
;kaijugaiden.c:940: static s16 camera_apply_x(s16 x) {
;	---------------------------------
; Function camera_apply_x
; ---------------------------------
_camera_apply_x:
;kaijugaiden.c:941: return x - gs.camera_x + camera_shake_x();
	ld	bc, #_gs+121
	ld	a, (bc)
	ld	c, a
	rlca
	sbc	a, a
	ld	b, a
	ld	a, e
	sub	a, c
	ld	c, a
	ld	a, d
	sbc	a, b
	ld	b, a
	push	bc
	call	_camera_shake_x
	pop	bc
	ld	l, a
	rlca
	sbc	a, a
	ld	h, a
	add	hl, bc
	ld	c, l
	ld	b, h
;kaijugaiden.c:942: }
	ret
;kaijugaiden.c:944: static s16 camera_apply_y(s16 y) {
;	---------------------------------
; Function camera_apply_y
; ---------------------------------
_camera_apply_y:
;kaijugaiden.c:945: return y - gs.camera_y + camera_shake_y();
	ld	bc, #_gs+122
	ld	a, (bc)
	ld	c, a
	rlca
	sbc	a, a
	ld	b, a
	ld	a, e
	sub	a, c
	ld	c, a
	ld	a, d
	sbc	a, b
	ld	b, a
	push	bc
	call	_camera_shake_y
	pop	bc
	ld	l, a
	rlca
	sbc	a, a
	ld	h, a
	add	hl, bc
	ld	c, l
	ld	b, h
;kaijugaiden.c:946: }
	ret
;kaijugaiden.c:948: static u8 combat_camera_update(void) {
;	---------------------------------
; Function combat_camera_update
; ---------------------------------
_combat_camera_update:
	add	sp, #-12
;kaijugaiden.c:949: s8 prev_bg_x = gs.camera_bg_x;
	ld	a, (#(_gs + 123) + 0)
	ldhl	sp,	#0
	ld	(hl), a
;kaijugaiden.c:950: s8 prev_bg_y = gs.camera_bg_y;
	ld	a, (#(_gs + 124) + 0)
	ldhl	sp,	#1
	ld	(hl), a
;kaijugaiden.c:951: s16 player_px = (s16)(gs.player_x * TILE_W + 8);
	ld	hl, #_gs + 1
	ld	l, (hl)
	ld	h, #0x00
	add	hl, hl
	add	hl, hl
	add	hl, hl
	ld	a, l
	add	a, #0x08
	ld	c, a
	ld	a, h
	adc	a, #0x00
	ldhl	sp,	#10
	ld	(hl), c
	inc	hl
;kaijugaiden.c:952: s16 target_x = (player_px - (SCR_W / 2)) / 6;
	ld	(hl-), a
	ld	a, (hl+)
	ld	c, (hl)
	add	a, #0xb0
	ld	e, a
	ld	a, c
	adc	a, #0xff
	ld	bc, #0x0006
	ld	d, a
	call	__divsint
	ldhl	sp,	#6
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;kaijugaiden.c:953: s16 target_y = 0;
	xor	a, a
	ldhl	sp,	#2
	ld	(hl+), a
	ld	(hl), a
;kaijugaiden.c:955: if (gs.boss_awake) {
	ld	a, (#_gs + 20)
	or	a, a
	jp	Z, 00104$
;kaijugaiden.c:956: s16 duel_mid = (player_px + gs.boss_x + 16) / 2;
	ld	de, #(_gs + 23)
	ld	a, (de)
	ldhl	sp,	#4
	ld	(hl+), a
	inc	de
	ld	a, (de)
	ld	(hl), a
	ldhl	sp,#10
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ldhl	sp,	#4
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	ld	c, l
	ld	b, h
	ld	hl, #0x0010
	add	hl, bc
	push	hl
	ld	a, l
	ldhl	sp,	#10
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#9
	ld	(hl-), a
	ld	a, (hl+)
	inc	hl
	ld	(hl-), a
	ld	a, (hl+)
	inc	hl
	ld	(hl-), a
	dec	hl
	bit	7, (hl)
	jr	Z, 00128$
	ld	hl, #0x0011
	add	hl, bc
	push	hl
	ld	a, l
	ldhl	sp,	#12
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#11
	ld	(hl), a
00128$:
	ldhl	sp,#10
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	sra	b
	rr	c
;kaijugaiden.c:957: target_x = (target_x * 2 + ((duel_mid - (SCR_W / 2)) / 8)) / 3;
	ldhl	sp,	#6
	ld	a, (hl+)
	ld	e, (hl)
	dec	hl
	add	a, a
	rl	e
	ld	(hl+), a
	ld	a, e
	ld	(hl+), a
	ld	a, c
	ld	(hl+), a
	ld	a, b
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0x0050
	ld	a, e
	sub	a, l
	ld	e, a
	ld	a, d
	sbc	a, h
	ldhl	sp,	#11
	ld	(hl-), a
	ld	(hl), e
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	bit	7, (hl)
	jr	Z, 00129$
	dec	hl
	dec	hl
	dec	hl
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0xffb7
	add	hl, de
	ld	c, l
	ld	b, h
00129$:
	sra	b
	rr	c
	sra	b
	rr	c
	sra	b
	rr	c
	ldhl	sp,	#6
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, bc
	ld	e, l
	ld	d, h
	ld	bc, #0x0003
	call	__divsint
	ldhl	sp,	#6
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;kaijugaiden.c:958: if (gs.boss_windup > 0) {
	ld	a, (#(_gs + 28) + 0)
	or	a, a
	jr	Z, 00104$
;kaijugaiden.c:959: target_x = (target_x * 2 + ((gs.boss_x + 16 - (SCR_W / 2)) / 12)) / 3;
	dec	hl
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	sla	e
	rl	d
	ldhl	sp,	#4
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	ld	hl, #0xffc0
	add	hl, bc
	push	de
	ld	bc, #0x000c
	ld	e, l
	ld	d, h
	call	__divsint
	ld	l, c
	ld	h, b
	pop	de
	add	hl, de
	ld	e, l
	ld	d, h
	ld	bc, #0x0003
	call	__divsint
	ldhl	sp,	#6
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;kaijugaiden.c:960: target_y = (gs.boss_atk_type == BOSS_ATK_SLAM) ? 2 : 1;
	ld	a, (#(_gs + 27) + 0)
	sub	a, #0x02
	ld	a, #0x02
	jr	Z, 00131$
	ld	a, #0x01
00131$:
	ldhl	sp,	#2
	ld	(hl+), a
	ld	(hl), #0x00
00104$:
;kaijugaiden.c:964: if (gs.dodge_timer > 0) {
	ld	hl, #_gs + 10
	ld	e, (hl)
;kaijugaiden.c:957: target_x = (target_x * 2 + ((duel_mid - (SCR_W / 2)) / 8)) / 3;
	ldhl	sp,	#6
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
;kaijugaiden.c:965: target_x += gs.player_facing ? -2 : 2;
;kaijugaiden.c:964: if (gs.dodge_timer > 0) {
	ld	a, e
	or	a, a
	jr	Z, 00111$
;kaijugaiden.c:965: target_x += gs.player_facing ? -2 : 2;
	ld	a, (#(_gs + 3) + 0)
	or	a, a
	jr	Z, 00132$
	ld	hl, #0xfffe
	jr	00133$
00132$:
	ld	hl, #0x0002
00133$:
	add	hl, bc
	ld	c, l
	ld	a, h
	ldhl	sp,	#6
	ld	(hl), c
	inc	hl
	ld	(hl), a
;kaijugaiden.c:966: target_y = -1;
	ldhl	sp,	#2
	ld	a, #0xff
	ld	(hl+), a
	ld	(hl), #0xff
	jr	00112$
00111$:
;kaijugaiden.c:967: } else if (gs.attack_timer > 0) {
	ld	a, (#(_gs + 5) + 0)
	or	a, a
	jr	Z, 00108$
;kaijugaiden.c:968: target_x += gs.player_facing ? -1 : 1;
	ld	a, (#(_gs + 3) + 0)
	or	a, a
	jr	Z, 00134$
	ld	de, #0xffff
	jr	00135$
00134$:
	ld	de, #0x0001
00135$:
	ld	a, e
	add	a, c
	ld	c, a
	ld	a, d
	adc	a, b
	ldhl	sp,	#6
	ld	(hl), c
	inc	hl
	ld	(hl), a
;kaijugaiden.c:969: target_y = -1;
	ldhl	sp,	#2
	ld	a, #0xff
	ld	(hl+), a
	ld	(hl), #0xff
	jr	00112$
00108$:
;kaijugaiden.c:970: } else if (gs.hit_stun > 0) {
	ld	a, (#(_gs + 9) + 0)
	or	a, a
	jr	Z, 00112$
;kaijugaiden.c:971: target_y = 1;
	ldhl	sp,	#2
	ld	a, #0x01
	ld	(hl+), a
	xor	a, a
	ld	(hl), a
00112$:
;kaijugaiden.c:974: target_x = clamp_s8(target_x, -6, 6);
	ld	a, #0x06
	push	af
	inc	sp
	ld	a, #0xfa
	ldhl	sp,	#7
	ld	e, (hl)
	inc	hl
	ld	d, (hl)
	call	_clamp_s8
	ldhl	sp,	#10
	ld	(hl+), a
	rlca
	sbc	a, a
	ld	(hl), a
;kaijugaiden.c:975: target_y = clamp_s8(target_y, -2, 3);
	ld	a, #0x03
	push	af
	inc	sp
	ld	a, #0xfe
	ldhl	sp,	#3
	ld	e, (hl)
	inc	hl
	ld	d, (hl)
	call	_clamp_s8
	ldhl	sp,	#6
	ld	(hl+), a
	rlca
	sbc	a, a
	ld	(hl), a
;kaijugaiden.c:977: if (gs.camera_x < target_x) gs.camera_x++;
	ld	hl, #(_gs + 121)
	ld	c, (hl)
	ld	a, c
	ldhl	sp,	#8
	ld	(hl+), a
	rlca
	sbc	a, a
	ld	(hl), a
	ldhl	sp,	#8
	ld	e, l
	ld	d, h
	ldhl	sp,	#10
	ld	a, (de)
	inc	de
	sub	a, (hl)
	inc	hl
	ld	a, (de)
	sbc	a, (hl)
	ld	a, (de)
	ld	d, a
	bit	7, (hl)
	jr	Z, 00278$
	bit	7, d
	jr	NZ, 00279$
	cp	a, a
	jr	00279$
00278$:
	bit	7, d
	jr	Z, 00279$
	scf
00279$:
	jr	NC, 00116$
	inc	c
	ld	hl, #(_gs + 121)
	ld	(hl), c
	jr	00117$
00116$:
;kaijugaiden.c:978: else if (gs.camera_x > target_x) gs.camera_x--;
	ldhl	sp,	#10
	ld	e, l
	ld	d, h
	ldhl	sp,	#8
	ld	a, (de)
	inc	de
	sub	a, (hl)
	inc	hl
	ld	a, (de)
	sbc	a, (hl)
	ld	a, (de)
	ld	d, a
	bit	7, (hl)
	jr	Z, 00280$
	bit	7, d
	jr	NZ, 00281$
	cp	a, a
	jr	00281$
00280$:
	bit	7, d
	jr	Z, 00281$
	scf
00281$:
	jr	NC, 00117$
	dec	c
	ld	hl, #(_gs + 121)
	ld	(hl), c
00117$:
;kaijugaiden.c:979: if (gs.camera_y < target_y) gs.camera_y++;
	ld	hl, #(_gs + 122)
	ld	c, (hl)
	ld	a, c
	ldhl	sp,	#10
	ld	(hl+), a
	rlca
	sbc	a, a
	ld	(hl), a
	ldhl	sp,	#10
	ld	e, l
	ld	d, h
	ldhl	sp,	#6
	ld	a, (de)
	inc	de
	sub	a, (hl)
	inc	hl
	ld	a, (de)
	sbc	a, (hl)
	ld	a, (de)
	ld	d, a
	bit	7, (hl)
	jr	Z, 00282$
	bit	7, d
	jr	NZ, 00283$
	cp	a, a
	jr	00283$
00282$:
	bit	7, d
	jr	Z, 00283$
	scf
00283$:
	jr	NC, 00121$
	inc	c
	ld	hl, #(_gs + 122)
	ld	(hl), c
	jr	00122$
00121$:
;kaijugaiden.c:980: else if (gs.camera_y > target_y) gs.camera_y--;
	ldhl	sp,	#6
	ld	e, l
	ld	d, h
	ldhl	sp,	#10
	ld	a, (de)
	inc	de
	sub	a, (hl)
	inc	hl
	ld	a, (de)
	sbc	a, (hl)
	ld	a, (de)
	ld	d, a
	bit	7, (hl)
	jr	Z, 00284$
	bit	7, d
	jr	NZ, 00285$
	cp	a, a
	jr	00285$
00284$:
	bit	7, d
	jr	Z, 00285$
	scf
00285$:
	jr	NC, 00122$
	dec	c
	ld	hl, #(_gs + 122)
	ld	(hl), c
00122$:
;kaijugaiden.c:982: if (gs.camera_shake_timer > 0) gs.camera_shake_timer--;
	ld	a, (#(_gs + 125) + 0)
	or	a, a
	jr	Z, 00124$
	dec	a
	ld	(#(_gs + 125)),a
	jr	00125$
00124$:
;kaijugaiden.c:983: else gs.camera_shake_mag = 0;
	ld	hl, #(_gs + 126)
	ld	(hl), #0x00
00125$:
;kaijugaiden.c:985: gs.camera_bg_x = clamp_s8(gs.camera_x / 4, -1, 1);
	ld	a, (#(_gs + 121) + 0)
	ld	c, a
	rlca
	sbc	a, a
	ld	b, a
	ld	l, c
	ld	h, b
	bit	7, b
	jr	Z, 00136$
	ld	l, c
	ld	h, b
	inc	hl
	inc	hl
	inc	hl
00136$:
	ld	e, l
	ld	d, h
	sra	d
	rr	e
	sra	d
	rr	e
	ld	a, #0x01
	push	af
	inc	sp
	ld	a, #0xff
	call	_clamp_s8
	ld	(#(_gs + 123)),a
;kaijugaiden.c:986: gs.camera_bg_y = clamp_s8(gs.camera_y / 2, -1, 1);
	ld	a, (#(_gs + 122) + 0)
	ld	c, a
	rlca
	sbc	a, a
	ld	b, a
	ld	l, c
	ld	h, b
	bit	7, b
	jr	Z, 00137$
	ld	l, c
	ld	h, b
	inc	hl
00137$:
	ld	e, l
	ld	d, h
	sra	d
	rr	e
	ld	a, #0x01
	push	af
	inc	sp
	ld	a, #0xff
	call	_clamp_s8
	ld	(#(_gs + 124)),a
;kaijugaiden.c:987: return (u8)((prev_bg_x != gs.camera_bg_x) || (prev_bg_y != gs.camera_bg_y));
	ld	hl, #(_gs + 123)
	ld	c, (hl)
	ldhl	sp,	#0
	ld	a, (hl)
	sub	a, c
	jr	NZ, 00139$
	ld	hl, #(_gs + 124)
	ld	c, (hl)
	ldhl	sp,	#1
	ld	a, (hl)
	sub	a, c
	jr	NZ, 00139$
	xor	a, a
	jr	00140$
00139$:
	ld	a, #0x01
00140$:
;kaijugaiden.c:988: }
	add	sp, #12
	ret
;kaijugaiden.c:990: static const char *boss_attack_label(u8 type) {
;	---------------------------------
; Function boss_attack_label
; ---------------------------------
_boss_attack_label:
	ld	c, a
;kaijugaiden.c:991: switch (type) {
	ld	a, #0x03
	sub	a, c
	jr	C, 00105$
	ld	b, #0x00
	ld	hl, #00116$
	add	hl, bc
	add	hl, bc
	ld	c, (hl)
	inc	hl
	ld	h, (hl)
	ld	l, c
	jp	(hl)
00116$:
	.dw	00101$
	.dw	00102$
	.dw	00103$
	.dw	00104$
;kaijugaiden.c:992: case BOSS_ATK_SWEEP: return "SWEEP";
00101$:
	ld	bc, #___str_2
	ret
;kaijugaiden.c:993: case BOSS_ATK_SPIT:  return "SPIT";
00102$:
	ld	bc, #___str_3
	ret
;kaijugaiden.c:994: case BOSS_ATK_SLAM:  return "SLAM";
00103$:
	ld	bc, #___str_4
	ret
;kaijugaiden.c:995: case BOSS_ATK_TIDAL: return "TIDAL";
00104$:
	ld	bc, #___str_5
	ret
;kaijugaiden.c:996: default:             return "DUEL";
00105$:
	ld	bc, #___str_6
;kaijugaiden.c:997: }
;kaijugaiden.c:998: }
	ret
___str_2:
	.ascii "SWEEP"
	.db 0x00
___str_3:
	.ascii "SPIT"
	.db 0x00
___str_4:
	.ascii "SLAM"
	.db 0x00
___str_5:
	.ascii "TIDAL"
	.db 0x00
___str_6:
	.ascii "DUEL"
	.db 0x00
;kaijugaiden.c:1000: static u8 boss_attack_windup_frames(u8 type) {
;	---------------------------------
; Function boss_attack_windup_frames
; ---------------------------------
_boss_attack_windup_frames:
	ld	c, a
;kaijugaiden.c:1001: switch (type) {
	ld	a, #0x03
	sub	a, c
	jr	C, 00105$
	ld	b, #0x00
	ld	hl, #00116$
	add	hl, bc
	add	hl, bc
	ld	c, (hl)
	inc	hl
	ld	h, (hl)
	ld	l, c
	jp	(hl)
00116$:
	.dw	00101$
	.dw	00102$
	.dw	00103$
	.dw	00104$
;kaijugaiden.c:1002: case BOSS_ATK_SWEEP: return 16;
00101$:
	ld	a, #0x10
	ret
;kaijugaiden.c:1003: case BOSS_ATK_SPIT:  return 22;
00102$:
	ld	a, #0x16
	ret
;kaijugaiden.c:1004: case BOSS_ATK_SLAM:  return 26;
00103$:
	ld	a, #0x1a
	ret
;kaijugaiden.c:1005: case BOSS_ATK_TIDAL: return 18;
00104$:
	ld	a, #0x12
	ret
;kaijugaiden.c:1006: default:             return 16;
00105$:
	ld	a, #0x10
;kaijugaiden.c:1007: }
;kaijugaiden.c:1008: }
	ret
;kaijugaiden.c:1010: static u8 boss_attack_recover_frames(u8 type) {
;	---------------------------------
; Function boss_attack_recover_frames
; ---------------------------------
_boss_attack_recover_frames:
	ld	c, a
;kaijugaiden.c:1011: switch (type) {
	ld	a, #0x03
	sub	a, c
	jr	C, 00105$
	ld	b, #0x00
	ld	hl, #00116$
	add	hl, bc
	add	hl, bc
	ld	c, (hl)
	inc	hl
	ld	h, (hl)
	ld	l, c
	jp	(hl)
00116$:
	.dw	00101$
	.dw	00102$
	.dw	00103$
	.dw	00104$
;kaijugaiden.c:1012: case BOSS_ATK_SWEEP: return 18;
00101$:
	ld	a, #0x12
	ret
;kaijugaiden.c:1013: case BOSS_ATK_SPIT:  return 14;
00102$:
	ld	a, #0x0e
	ret
;kaijugaiden.c:1014: case BOSS_ATK_SLAM:  return 24;
00103$:
	ld	a, #0x18
	ret
;kaijugaiden.c:1015: case BOSS_ATK_TIDAL: return 20;
00104$:
	ld	a, #0x14
	ret
;kaijugaiden.c:1016: default:             return 16;
00105$:
	ld	a, #0x10
;kaijugaiden.c:1017: }
;kaijugaiden.c:1018: }
	ret
;kaijugaiden.c:1020: static u8 boss_current_range(u8 type) {
;	---------------------------------
; Function boss_current_range
; ---------------------------------
_boss_current_range:
	ld	c, a
;kaijugaiden.c:1021: switch (type) {
	ld	a, #0x03
	sub	a, c
	jr	C, 00105$
	ld	b, #0x00
	ld	hl, #00116$
	add	hl, bc
	add	hl, bc
	ld	c, (hl)
	inc	hl
	ld	h, (hl)
	ld	l, c
	jp	(hl)
00116$:
	.dw	00101$
	.dw	00102$
	.dw	00103$
	.dw	00104$
;kaijugaiden.c:1022: case BOSS_ATK_SWEEP: return BOSS_SWEEP_RANGE;
00101$:
	ld	a, #0x20
	ret
;kaijugaiden.c:1023: case BOSS_ATK_SPIT:  return BOSS_SPIT_RANGE;
00102$:
	ld	a, #0x58
	ret
;kaijugaiden.c:1024: case BOSS_ATK_SLAM:  return BOSS_SLAM_RANGE;
00103$:
	ld	a, #0x1a
	ret
;kaijugaiden.c:1025: case BOSS_ATK_TIDAL: return BOSS_SPIT_RANGE;
00104$:
	ld	a, #0x58
	ret
;kaijugaiden.c:1026: default:             return BOSS_SWEEP_RANGE;
00105$:
	ld	a, #0x20
;kaijugaiden.c:1027: }
;kaijugaiden.c:1028: }
	ret
;kaijugaiden.c:1030: static u8 boss_pick_attack(void) {
;	---------------------------------
; Function boss_pick_attack
; ---------------------------------
_boss_pick_attack:
;kaijugaiden.c:1031: u8 distance = abs_distance_u8(gs.boss_x, (s16)(gs.player_x * TILE_W));
	ld	hl, #_gs + 1
	ld	l, (hl)
	ld	h, #0x00
	add	hl, hl
	add	hl, hl
	add	hl, hl
	ld	c, l
	ld	b, h
	ld	hl, #_gs + 23
	ld	a, (hl+)
	ld	l, (hl)
	ld	e, a
	ld	d, l
	call	_abs_distance_u8
	ld	c, a
;kaijugaiden.c:1032: if (gs.boss_phase == 1) {
	ld	hl, #_gs + 21
	ld	b, (hl)
	ld	a, b
	dec	a
	jr	NZ, 00102$
;kaijugaiden.c:1033: return (distance <= 34) ? BOSS_ATK_SWEEP : BOSS_ATK_SPIT;
	ld	a, #0x22
	sub	a, c
	jr	C, 00114$
	xor	a, a
	ret
00114$:
	ld	a, #0x01
	ret
00102$:
;kaijugaiden.c:1037: return ((gs.anim_tick & 0x10) != 0) ? BOSS_ATK_SPIT : BOSS_ATK_SWEEP;
	ld	de, #_gs + 118
;kaijugaiden.c:1035: if (gs.boss_phase == 2) {
	ld	a, b
	sub	a, #0x02
	jr	NZ, 00106$
;kaijugaiden.c:1036: if (distance <= 22) return BOSS_ATK_SLAM;
	ld	a, #0x16
	sub	a, c
	jr	C, 00104$
	ld	a, #0x02
	ret
00104$:
;kaijugaiden.c:1037: return ((gs.anim_tick & 0x10) != 0) ? BOSS_ATK_SPIT : BOSS_ATK_SWEEP;
	ld	a, (de)
	bit	4, a
	jr	Z, 00116$
	ld	a, #0x01
	ret
00116$:
	xor	a, a
	ret
00106$:
;kaijugaiden.c:1039: if ((gs.anim_tick % 96) < 12 && distance > 18) return BOSS_ATK_TIDAL;
	ld	a, (de)
	push	bc
	ld	e, #0x60
	call	__moduchar
	ld	a, c
	pop	bc
	sub	a, #0x0c
	jr	NC, 00108$
	ld	a, #0x12
	sub	a, c
	jr	NC, 00108$
	ld	a, #0x03
	ret
00108$:
;kaijugaiden.c:1040: if (distance <= 24) return BOSS_ATK_SLAM;
	ld	a, #0x18
	sub	a, c
	jr	C, 00111$
	ld	a, #0x02
	ret
00111$:
;kaijugaiden.c:1041: return (distance > 54) ? BOSS_ATK_TIDAL : BOSS_ATK_SWEEP;
	ld	a, #0x36
	sub	a, c
	jr	NC, 00118$
	ld	a, #0x03
	ret
00118$:
	xor	a, a
;kaijugaiden.c:1042: }
	ret
;kaijugaiden.c:1050: static void hud_draw(void) {
;	---------------------------------
; Function hud_draw
; ---------------------------------
_hud_draw:
	add	sp, #-4
;kaijugaiden.c:1052: for (u8 i = 0; i < PLAYER_MAX_HP; ++i)
	ld	c, #0x00
00150$:
	ld	a, c
	sub	a, #0x06
	jr	NC, 00101$
;kaijugaiden.c:1053: plat_set_bkg_tile(i, HUD_ROW, (i < gs.player_hp) ? TILE_HP_SEG : TILE_BLANK);
	ld	hl, #_gs
	ld	b, (hl)
	ld	a, c
	sub	a, b
	jr	NC, 00160$
	ld	a, #0x1d
	jr	00161$
00160$:
	xor	a, a
00161$:
;kaijugaiden.c:146: set_bkg_tile_xy(x, y, tile);
	push	bc
	push	af
	inc	sp
	ld	e, #0x00
	ld	a, c
	call	_set_bkg_tile_xy
	pop	bc
;kaijugaiden.c:1052: for (u8 i = 0; i < PLAYER_MAX_HP; ++i)
	inc	c
	jr	00150$
00101$:
;kaijugaiden.c:1056: bg_draw_number_2(10, HUD_ROW, gs.nanocell_count);
	ld	a, (#(_gs + 14) + 0)
	push	af
	inc	sp
	ld	e, #0x00
	ld	a, #0x0a
	call	_bg_draw_number_2
;kaijugaiden.c:1059: if (gs.phase == PHASE_COMBAT && gs.boss_awake) {
	ld	hl, #(_gs + 76)
;kaijugaiden.c:1060: u8 boss_max = (gs.boss_phase == 1) ? BOSS_HP_P1
;kaijugaiden.c:1059: if (gs.phase == PHASE_COMBAT && gs.boss_awake) {
	ld	a, (hl)
	sub	a, #0x04
	jr	NZ, 00179$
	ld	a, (#(_gs + 20) + 0)
	or	a, a
	jr	Z, 00179$
;kaijugaiden.c:1060: u8 boss_max = (gs.boss_phase == 1) ? BOSS_HP_P1
	ld	a, (#(_gs + 21) + 0)
	cp	a, #0x01
	jr	NZ, 00162$
	ld	e, #0x0c
	jr	00163$
00162$:
	sub	a, #0x02
	ld	e, #0x0a
	jr	Z, 00165$
	ld	e, #0x08
00165$:
00163$:
	ldhl	sp,	#0
	ld	(hl), e
;kaijugaiden.c:1062: for (u8 i = 0; i < 6; ++i) {
	ldhl	sp,	#3
	ld	(hl), #0x00
00153$:
	ldhl	sp,	#3
	ld	a, (hl)
	sub	a, #0x06
	jr	NC, 00106$
;kaijugaiden.c:1063: u8 filled = (u8)((u16)gs.boss_hp * 6 / boss_max);
	ld	hl, #(_gs + 22)
	ld	c, (hl)
	ld	b, #0x00
	ld	l, c
	ld	h, b
	add	hl, hl
	add	hl, bc
	add	hl, hl
	push	hl
	ld	a, l
	ldhl	sp,	#3
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#2
	ld	(hl-), a
	dec	hl
	ld	a, (hl+)
	ld	c, a
	xor	a, a
	ld	b, a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	call	__divuint
;kaijugaiden.c:1065: (i < filled) ? TILE_BOSS_SEG : TILE_BLANK);
	ldhl	sp,	#3
	ld	a, (hl)
	sub	a, c
	jr	NC, 00166$
	ld	b, #0x1e
	jr	00167$
00166$:
	ld	b, #0x00
00167$:
;kaijugaiden.c:1064: plat_set_bkg_tile(14 + i, HUD_ROW,
	ldhl	sp,	#3
	ld	a, (hl)
	add	a, #0x0e
;kaijugaiden.c:146: set_bkg_tile_xy(x, y, tile);
	push	bc
	inc	sp
	ld	e, #0x00
	call	_set_bkg_tile_xy
;kaijugaiden.c:1062: for (u8 i = 0; i < 6; ++i) {
	ldhl	sp,	#3
	inc	(hl)
	jr	00153$
;kaijugaiden.c:1068: for (u8 i = 0; i < 6; ++i)
00179$:
	ld	c, #0x00
00156$:
;kaijugaiden.c:1069: plat_set_bkg_tile(14 + i, HUD_ROW, TILE_BLANK);
	ld	a,c
	cp	a,#0x06
	jr	NC, 00106$
	add	a, #0x0e
;kaijugaiden.c:146: set_bkg_tile_xy(x, y, tile);
	push	bc
	ld	h, #0x00
	push	hl
	inc	sp
	ld	e, #0x00
	call	_set_bkg_tile_xy
	pop	bc
;kaijugaiden.c:1068: for (u8 i = 0; i < 6; ++i)
	inc	c
	jr	00156$
00106$:
;kaijugaiden.c:1072: bg_clear_row(1);
	ld	a, #0x01
	call	_bg_clear_row
;kaijugaiden.c:1073: bg_clear_row(2);
	ld	a, #0x02
	call	_bg_clear_row
;kaijugaiden.c:1074: if (gs.phase == PHASE_COMBAT) {
	ld	a, (#(_gs + 76) + 0)
	sub	a, #0x04
	jp	NZ, 00158$
;kaijugaiden.c:1075: if (!gs.boss_awake) {
	ld	a, (#(_gs + 20) + 0)
	or	a, a
	jr	NZ, 00141$
;kaijugaiden.c:1076: bg_draw_text(0, 1, "WAVE");
	ld	de, #___str_7
	push	de
	ld	e, #0x01
	xor	a, a
	call	_bg_draw_text
;kaijugaiden.c:1077: bg_draw_number_2(4, 1, gs.wave + 1);
	ld	a, (#(_gs + 80) + 0)
	inc	a
	push	af
	inc	sp
	ld	e, #0x01
	ld	a, #0x04
	call	_bg_draw_number_2
;kaijugaiden.c:1078: bg_draw_text(8, 1, "FOE");
	ld	de, #___str_8
	push	de
	ld	e, #0x01
	ld	a, #0x08
	call	_bg_draw_text
;kaijugaiden.c:1079: bg_draw_number_2(11, 1, combat_minions_alive());
	call	_combat_minions_alive
	push	af
	inc	sp
	ld	e, #0x01
	ld	a, #0x0b
	call	_bg_draw_number_2
;kaijugaiden.c:1080: bg_draw_text(0, 2, "CLEAR TO DRAW BOSS");
	ld	de, #___str_9
	push	de
	ld	e, #0x02
	xor	a, a
	call	_bg_draw_text
	jp	00158$
00141$:
;kaijugaiden.c:1081: } else if (gs.banner_timer > 0) {
	ld	a, (#(_gs + 119) + 0)
	or	a, a
	jp	Z, 00138$
;kaijugaiden.c:1082: switch (gs.banner_kind) {
	ld	hl, #(_gs + 120)
	ld	c, (hl)
	ld	a, #0x06
	sub	a, c
	jr	C, 00114$
	ld	b, #0x00
	ld	hl, #00340$
	add	hl, bc
	add	hl, bc
	ld	c, (hl)
	inc	hl
	ld	h, (hl)
	ld	l, c
	jp	(hl)
00340$:
	.dw	00114$
	.dw	00109$
	.dw	00108$
	.dw	00110$
	.dw	00111$
	.dw	00112$
	.dw	00113$
;kaijugaiden.c:1083: case BANNER_BOSS_RISE:  bg_draw_text(0, 1, "LEVIATHAN RISES"); break;
00108$:
	ld	de, #___str_10
	push	de
	ld	e, #0x01
	xor	a, a
	call	_bg_draw_text
	jp	00158$
;kaijugaiden.c:1084: case BANNER_WAVE_CLEAR: bg_draw_text(0, 1, "WAVE BROKEN"); break;
00109$:
	ld	de, #___str_11
	push	de
	ld	e, #0x01
	xor	a, a
	call	_bg_draw_text
	jp	00158$
;kaijugaiden.c:1085: case BANNER_DODGE:      bg_draw_text(0, 1, "DODGE CLEAN"); break;
00110$:
	ld	de, #___str_12
	push	de
	ld	e, #0x01
	xor	a, a
	call	_bg_draw_text
	jp	00158$
;kaijugaiden.c:1086: case BANNER_PERFECT:    bg_draw_text(0, 1, "PERFECT STRIKE"); break;
00111$:
	ld	de, #___str_13
	push	de
	ld	e, #0x01
	xor	a, a
	call	_bg_draw_text
	jp	00158$
;kaijugaiden.c:1087: case BANNER_FINISHER:   bg_draw_text(0, 1, "FINISHER WINDOW"); break;
00112$:
	ld	de, #___str_14
	push	de
	ld	e, #0x01
	xor	a, a
	call	_bg_draw_text
	jp	00158$
;kaijugaiden.c:1088: case BANNER_BOSS_STUN:  bg_draw_text(0, 1, "BOSS STUNNED"); break;
00113$:
	ld	de, #___str_15
	push	de
	ld	e, #0x01
	xor	a, a
	call	_bg_draw_text
	jp	00158$
;kaijugaiden.c:1089: default:                bg_draw_text(0, 1, "DUEL LIVE"); break;
00114$:
	ld	de, #___str_16
	push	de
	ld	e, #0x01
	xor	a, a
	call	_bg_draw_text
;kaijugaiden.c:1090: }
	jp	00158$
00138$:
;kaijugaiden.c:1091: } else if (gs.boss_windup > 0) {
;kaijugaiden.c:1093: if (abs_distance_u8(gs.boss_x, (s16)(gs.player_x * TILE_W)) <= boss_current_range(gs.boss_atk_type))
;kaijugaiden.c:1091: } else if (gs.boss_windup > 0) {
	ld	a, (#(_gs + 28) + 0)
	or	a, a
	jr	Z, 00135$
;kaijugaiden.c:1092: bg_draw_text(0, 1, boss_attack_label(gs.boss_atk_type));
	ld	a, (#(_gs + 27) + 0)
	call	_boss_attack_label
	push	bc
	ld	e, #0x01
	xor	a, a
	call	_bg_draw_text
;kaijugaiden.c:1093: if (abs_distance_u8(gs.boss_x, (s16)(gs.player_x * TILE_W)) <= boss_current_range(gs.boss_atk_type))
	ld	hl, #(_gs + 1)
	ld	l, (hl)
	xor	a, a
	ld	h, a
	add	hl, hl
	add	hl, hl
	add	hl, hl
	ld	c, l
	ld	b, h
	ld	hl, #(_gs + 23)
	ld	a,	(hl+)
	ld	h, (hl)
	ld	e, a
	ld	d, h
	call	_abs_distance_u8
	ld	c, a
	ld	a, (#(_gs + 27) + 0)
	push	bc
	call	_boss_current_range
	ld	e, a
	pop	bc
	ld	a, e
	sub	a, c
	jr	C, 00117$
;kaijugaiden.c:1094: bg_draw_text(0, 2, "DANGER STEP OR DODGE");
	ld	de, #___str_17
	push	de
	ld	e, #0x02
	xor	a, a
	call	_bg_draw_text
	jp	00158$
00117$:
;kaijugaiden.c:1096: bg_draw_text(0, 2, "OUTSIDE STRIKE EDGE");
	ld	de, #___str_18
	push	de
	ld	e, #0x02
	xor	a, a
	call	_bg_draw_text
	jp	00158$
00135$:
;kaijugaiden.c:1097: } else if (gs.boss_stun > 0) {
	ld	a, (#(_gs + 30) + 0)
	or	a, a
	jr	Z, 00132$
;kaijugaiden.c:1098: bg_draw_text(0, 1, "STUN");
	ld	de, #___str_19
	push	de
	ld	e, #0x01
	xor	a, a
	call	_bg_draw_text
;kaijugaiden.c:1099: bg_draw_text(0, 2, "PRESS ADVANTAGE");
	ld	de, #___str_20
	push	de
	ld	e, #0x02
	xor	a, a
	call	_bg_draw_text
	jp	00158$
00132$:
;kaijugaiden.c:1100: } else if (gs.dodge_timer > 0) {
	ld	a, (#(_gs + 10) + 0)
	or	a, a
	jr	Z, 00129$
;kaijugaiden.c:1101: bg_draw_text(0, 1, "DODGE");
	ld	de, #___str_21
	push	de
	ld	e, #0x01
	xor	a, a
	call	_bg_draw_text
;kaijugaiden.c:1102: bg_draw_text(0, 2, "COUNTER WINDOW");
	ld	de, #___str_22
	push	de
	ld	e, #0x02
	xor	a, a
	call	_bg_draw_text
	jp	00158$
00129$:
;kaijugaiden.c:1103: } else if (gs.perfect_flash_timer > 0) {
	ld	a, (#(_gs + 19) + 0)
	or	a, a
	jr	Z, 00126$
;kaijugaiden.c:1104: bg_draw_text(0, 1, "PERFECT");
	ld	de, #___str_23
	push	de
	ld	e, #0x01
	xor	a, a
	call	_bg_draw_text
;kaijugaiden.c:1105: bg_draw_text(0, 2, "CHAIN THE COMBO");
	ld	de, #___str_24
	push	de
	ld	e, #0x02
	xor	a, a
	call	_bg_draw_text
	jp	00158$
00126$:
;kaijugaiden.c:1106: } else if (gs.nanocell_boost_timer > 0) {
	ld	a, (#(_gs + 15) + 0)
	or	a, a
	jr	Z, 00123$
;kaijugaiden.c:1107: bg_draw_text(0, 1, "POWER");
	ld	de, #___str_25
	push	de
	ld	e, #0x01
	xor	a, a
	call	_bg_draw_text
;kaijugaiden.c:1108: bg_draw_number_2(6, 1, (u8)(gs.nanocell_boost_timer / 10));
	ld	a, (#(_gs + 15) + 0)
	ld	e, #0x0a
	call	__divuchar
	ld	a, c
	push	af
	inc	sp
	ld	e, #0x01
	ld	a, #0x06
	call	_bg_draw_number_2
;kaijugaiden.c:1109: bg_draw_text(0, 2, "PRESS THE BOSS");
	ld	de, #___str_26
	push	de
	ld	e, #0x02
	xor	a, a
	call	_bg_draw_text
	jr	00158$
00123$:
;kaijugaiden.c:1111: bg_draw_text(0, 1, "PHASE");
	ld	de, #___str_27
	push	de
	ld	e, #0x01
	xor	a, a
	call	_bg_draw_text
;kaijugaiden.c:1112: plat_set_bkg_tile(6, 1, TILE_FONT_0 + gs.boss_phase);
	ld	a, (#(_gs + 21) + 0)
	add	a, #0x20
;kaijugaiden.c:146: set_bkg_tile_xy(x, y, tile);
	push	af
	inc	sp
	ld	e, #0x01
	ld	a, #0x06
	call	_set_bkg_tile_xy
;kaijugaiden.c:1113: bg_draw_text(9, 1, "COMBO");
	ld	de, #___str_28
	push	de
	ld	e, #0x01
	ld	a, #0x09
	call	_bg_draw_text
;kaijugaiden.c:1114: bg_draw_number_2(15, 1, gs.combo_count);
	ld	a, (#(_gs + 11) + 0)
	push	af
	inc	sp
	ld	e, #0x01
	ld	a, #0x0f
	call	_bg_draw_number_2
;kaijugaiden.c:1115: if (attack_hits_target((s16)(gs.player_x * TILE_W + 8), gs.player_facing, (s16)(gs.boss_x + 16), PLAYER_ATTACK_FRONT + 4, PLAYER_ATTACK_REAR))
	ld	hl, #(_gs + 23)
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	ld	hl, #0x0010
	add	hl, bc
	ld	c, l
	ld	b, h
	ld	a, (#(_gs + 3) + 0)
	ldhl	sp,	#3
	ld	(hl), a
	ld	a, (#(_gs + 1) + 0)
	ld	h, #0x00
	ld	l, a
	add	hl, hl
	add	hl, hl
	add	hl, hl
	ld	de, #0x0008
	add	hl, de
	ld	e, l
	ld	d, h
	ld	hl, #0x820
	push	hl
	push	bc
	ldhl	sp,	#7
	ld	a, (hl)
	call	_attack_hits_target
	or	a, a
	jr	Z, 00120$
;kaijugaiden.c:1116: bg_draw_text(0, 2, "BOSS IN RANGE");
	ld	de, #___str_29
	push	de
	ld	e, #0x02
	xor	a, a
	call	_bg_draw_text
	jr	00158$
00120$:
;kaijugaiden.c:1118: bg_draw_text(0, 2, "SET YOUR ANGLE");
	ld	de, #___str_30
	push	de
	ld	e, #0x02
	xor	a, a
	call	_bg_draw_text
00158$:
;kaijugaiden.c:1121: }
	add	sp, #4
	ret
___str_7:
	.ascii "WAVE"
	.db 0x00
___str_8:
	.ascii "FOE"
	.db 0x00
___str_9:
	.ascii "CLEAR TO DRAW BOSS"
	.db 0x00
___str_10:
	.ascii "LEVIATHAN RISES"
	.db 0x00
___str_11:
	.ascii "WAVE BROKEN"
	.db 0x00
___str_12:
	.ascii "DODGE CLEAN"
	.db 0x00
___str_13:
	.ascii "PERFECT STRIKE"
	.db 0x00
___str_14:
	.ascii "FINISHER WINDOW"
	.db 0x00
___str_15:
	.ascii "BOSS STUNNED"
	.db 0x00
___str_16:
	.ascii "DUEL LIVE"
	.db 0x00
___str_17:
	.ascii "DANGER STEP OR DODGE"
	.db 0x00
___str_18:
	.ascii "OUTSIDE STRIKE EDGE"
	.db 0x00
___str_19:
	.ascii "STUN"
	.db 0x00
___str_20:
	.ascii "PRESS ADVANTAGE"
	.db 0x00
___str_21:
	.ascii "DODGE"
	.db 0x00
___str_22:
	.ascii "COUNTER WINDOW"
	.db 0x00
___str_23:
	.ascii "PERFECT"
	.db 0x00
___str_24:
	.ascii "CHAIN THE COMBO"
	.db 0x00
___str_25:
	.ascii "POWER"
	.db 0x00
___str_26:
	.ascii "PRESS THE BOSS"
	.db 0x00
___str_27:
	.ascii "PHASE"
	.db 0x00
___str_28:
	.ascii "COMBO"
	.db 0x00
___str_29:
	.ascii "BOSS IN RANGE"
	.db 0x00
___str_30:
	.ascii "SET YOUR ANGLE"
	.db 0x00
;kaijugaiden.c:1142: static void spr_draw_rei(void) {
;	---------------------------------
; Function spr_draw_rei
; ---------------------------------
_spr_draw_rei:
	add	sp, #-17
;kaijugaiden.c:1143: u8 base_tile = SPR_REI_IDLE;
	ldhl	sp,	#0
	ld	(hl), #0x00
;kaijugaiden.c:1144: if (gs.attack_timer > 0)       base_tile = SPR_REI_ATTACK;
	ld	a, (#(_gs + 5) + 0)
	ldhl	sp,#11
	ld	(hl), a
	ld	a, (hl)
	or	a, a
	jr	Z, 00104$
	ldhl	sp,	#0
	ld	(hl), #0x0c
	jr	00105$
00104$:
;kaijugaiden.c:1145: else if (gs.player_anim > 0)   base_tile = SPR_REI_RUN;
	ld	a, (#(_gs + 4) + 0)
	or	a, a
	jr	Z, 00105$
	ldhl	sp,	#0
	ld	(hl), #0x06
00105$:
;kaijugaiden.c:1147: if (gs.hit_stun > 0 && (gs.anim_tick & 0x02)) return;
	ld	a, (#(_gs + 9) + 0)
	ldhl	sp,#16
	ld	(hl), a
	ld	a, (hl)
	or	a, a
	jr	Z, 00107$
	ld	a, (#(_gs + 118) + 0)
	bit	1, a
	jp	NZ, 00127$
00107$:
;kaijugaiden.c:1148: if (gs.dodge_timer > 0 && (gs.anim_tick & 0x01)) return;
	ld	a, (#(_gs + 10) + 0)
	or	a, a
	jr	Z, 00110$
	ld	a, (#(_gs + 118) + 0)
	rrca
	jp	C, 00127$
00110$:
;kaijugaiden.c:1150: s16 bx = (s16)(gs.player_x * TILE_W);
	ld	a, (#(_gs + 1) + 0)
	ldhl	sp,#16
	ld	(hl), a
	ld	a, (hl-)
	ld	(hl+), a
	ld	(hl), #0x00
	ld	a, #0x03
00220$:
	ldhl	sp,	#15
	sla	(hl)
	inc	hl
	rl	(hl)
	dec	a
	jr	NZ, 00220$
	dec	hl
	ld	a, (hl)
	ldhl	sp,	#12
	ld	(hl), a
	ldhl	sp,	#16
	ld	a, (hl)
	ldhl	sp,	#13
	ld	(hl), a
;kaijugaiden.c:1151: s16 by = (s16)(gs.player_y - 16);  /* anchor at feet */
	ld	a, (#(_gs + 2) + 0)
	ldhl	sp,#16
	ld	(hl), a
	ld	a, (hl)
	ldhl	sp,	#9
	ld	(hl+), a
	xor	a, a
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0x0010
	ld	a, e
	sub	a, l
	ld	e, a
	ld	a, d
	sbc	a, h
	ldhl	sp,	#16
	ld	(hl-), a
	ld	(hl), e
;kaijugaiden.c:1152: if (gs.attack_queued && gs.attack_timer <= ATTACK_ACTIVE_FRAME) {
	ld	a, (#(_gs + 6) + 0)
;kaijugaiden.c:1153: bx += gs.player_facing ? -2 : 2;
;kaijugaiden.c:1152: if (gs.attack_queued && gs.attack_timer <= ATTACK_ACTIVE_FRAME) {
	ldhl	sp,#14
	ld	(hl), a
	ld	a, (hl)
	or	a, a
	jr	Z, 00113$
	ld	a, #0x08
	ldhl	sp,	#11
	sub	a, (hl)
	jr	C, 00113$
;kaijugaiden.c:1153: bx += gs.player_facing ? -2 : 2;
	ld	a, (#(_gs + 3) + 0)
	or	a, a
	jr	Z, 00129$
	ld	bc, #0xfffe
	jr	00130$
00129$:
	ld	bc, #0x0002
00130$:
	ldhl	sp,	#12
	ld	a, (hl+)
	ld	e, (hl)
	dec	hl
	add	a, c
	ld	c, a
	ld	a, e
	adc	a, b
	ld	(hl), c
	inc	hl
	ld	(hl), a
00113$:
;kaijugaiden.c:1155: bx = camera_apply_x(bx);
	ldhl	sp,	#12
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	call	_camera_apply_x
	ldhl	sp,	#1
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;kaijugaiden.c:1156: by = camera_apply_y(by);
	ldhl	sp,	#15
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	call	_camera_apply_y
	ldhl	sp,	#3
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;kaijugaiden.c:1157: u8 flip = gs.player_facing ? 0x20 : 0x00;  /* flag bit 5 = X-flip */
	ld	a, (#(_gs + 3) + 0)
	ldhl	sp,#16
	ld	(hl), a
	ld	a, (hl)
	or	a, a
	jr	Z, 00131$
	ld	(hl), #0x20
	jr	00132$
00131$:
	ldhl	sp,	#16
	ld	(hl), #0x00
00132$:
	ldhl	sp,	#16
	ld	a, (hl)
	ldhl	sp,	#5
	ld	(hl), a
;kaijugaiden.c:1160: for (u8 row = 0; row < 3; ++row) {
	ldhl	sp,	#16
	ld	(hl), #0x00
00125$:
	ldhl	sp,	#16
	ld	a, (hl)
	sub	a, #0x03
	jp	NC, 00127$
;kaijugaiden.c:1161: plat_set_sprite(row * 2,     bx,            (u8)(by + row * 8), base_tile + row * 2,     flip);
	ld	c, (hl)
	ld	a, c
	add	a, a
	ldhl	sp,	#6
	ld	(hl), a
	ldhl	sp,	#0
	ld	a, (hl)
	ldhl	sp,	#6
	add	a, (hl)
	inc	hl
	ld	(hl), a
	ld	a, (hl+)
	ld	(hl), a
	ldhl	sp,	#3
	ld	b, (hl)
	ld	a, c
	add	a, a
	add	a, a
	add	a, a
	add	a, b
	ldhl	sp,	#9
	ld	(hl), a
	ld	c, (hl)
	ldhl	sp,	#1
	ld	b, (hl)
	ldhl	sp,	#16
	ld	a, (hl)
	add	a, a
	ld	e, a
;kaijugaiden.c:149: move_sprite(id, x + 8, y + 16);   /* GBDK uses offset convention */
	ld	a, c
	add	a, #0x10
	ldhl	sp,	#10
	ld	(hl+), a
	ld	a, b
	add	a, #0x08
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1973: OAM_item_t * itm = &shadow_OAM[nb];
	ld	(hl+), a
	xor	a, a
	sla	e
	adc	a, a
	sla	e
	adc	a, a
	ld	(hl), e
	inc	hl
	ld	(hl), a
	ld	de, #_shadow_OAM
	ld	a, (hl-)
	ld	l, (hl)
	ld	h, a
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#16
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#15
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1974: itm->y=y, itm->x=x;
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ldhl	sp,	#10
	ld	a, (hl)
	ld	(de), a
	ldhl	sp,	#14
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	inc	bc
	ldhl	sp,	#11
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1887: shadow_OAM[nb].tile=tile;
	ld	a, (hl+)
	ld	(bc), a
	ld	de, #_shadow_OAM
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	inc	hl
	inc	hl
	ld	c, l
	ld	b, h
	ldhl	sp,	#8
	ld	a, (hl)
	ld	(bc), a
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1946: shadow_OAM[nb].prop=prop;
	ld	de, #_shadow_OAM
	ldhl	sp,	#12
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#16
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#15
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0x0003
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#14
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#13
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ldhl	sp,	#5
;kaijugaiden.c:1162: plat_set_sprite(row * 2 + 1, bx + TILE_W,  (u8)(by + row * 8), base_tile + row * 2 + 1, flip);
	ld	a, (hl+)
	inc	hl
	ld	(de), a
	ld	a, (hl)
	inc	a
	ldhl	sp,	#15
	ld	(hl), a
	ldhl	sp,	#1
	ld	a, (hl)
	add	a, #0x08
	ld	c, a
	ldhl	sp,	#6
	ld	b, (hl)
	inc	b
;kaijugaiden.c:149: move_sprite(id, x + 8, y + 16);   /* GBDK uses offset convention */
	ldhl	sp,	#9
	ld	a, (hl)
	add	a, #0x10
	ld	(hl+), a
	ld	a, c
	add	a, #0x08
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1973: OAM_item_t * itm = &shadow_OAM[nb];
	ld	(hl+), a
	xor	a, a
	sla	b
	adc	a, a
	sla	b
	adc	a, a
	ld	(hl), b
	inc	hl
	ld	(hl), a
	ld	de, #_shadow_OAM
	ld	a, (hl-)
	ld	l, (hl)
	ld	h, a
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#15
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#14
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1974: itm->y=y, itm->x=x;
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ldhl	sp,	#9
	ld	a, (hl)
	ld	(de), a
	ldhl	sp,	#13
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	inc	bc
	ldhl	sp,	#10
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1887: shadow_OAM[nb].tile=tile;
	ld	a, (hl+)
	ld	(bc), a
	ld	de, #_shadow_OAM
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	inc	hl
	inc	hl
	ld	c, l
	ld	b, h
	ldhl	sp,	#15
	ld	a, (hl)
	ld	(bc), a
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1946: shadow_OAM[nb].prop=prop;
	ld	de, #_shadow_OAM
	ldhl	sp,	#11
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#16
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#15
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0x0003
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#14
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#13
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ldhl	sp,	#5
	ld	a, (hl)
	ld	(de), a
;kaijugaiden.c:1160: for (u8 row = 0; row < 3; ++row) {
	ldhl	sp,	#16
	inc	(hl)
	jp	00125$
00127$:
;kaijugaiden.c:1164: }
	add	sp, #17
	ret
;kaijugaiden.c:1168: static void spr_draw_boss(void) {
;	---------------------------------
; Function spr_draw_boss
; ---------------------------------
_spr_draw_boss:
	add	sp, #-8
;kaijugaiden.c:1169: if (gs.boss_phase == 0) return;
	ld	a, (#(_gs + 21) + 0)
	or	a, a
	jp	Z, 00132$
;kaijugaiden.c:1170: u8 base_tile = (gs.boss_phase == 1) ? SPR_BOSS_A
	cp	a, #0x01
	jr	NZ, 00134$
	ld	e, #0x12
	jr	00135$
00134$:
	sub	a, #0x02
	ld	e, #0x1a
	jr	Z, 00137$
	ld	e, #0x22
00137$:
00135$:
	ld	c, e
;kaijugaiden.c:1172: s16 bx = gs.boss_x;
	ld	de, #(_gs + 23)
	ld	a, (de)
	ldhl	sp,	#4
	ld	(hl+), a
	inc	de
	ld	a, (de)
;kaijugaiden.c:1173: s16 by = (s16)(SCR_H - 16 - 32);  /* boss stands near ground, two tile rows tall */
	ld	(hl+), a
	ld	a, #0x60
	ld	(hl+), a
	xor	a, a
	ld	(hl), a
;kaijugaiden.c:1174: if (!gs.boss_awake) {
	ld	hl, #_gs + 20
	ld	b, (hl)
;kaijugaiden.c:1176: if (gs.anim_tick & 0x04) return;
;kaijugaiden.c:1174: if (!gs.boss_awake) {
	ld	a, b
	or	a, a
	jr	NZ, 00118$
;kaijugaiden.c:1175: by += 4;
	ldhl	sp,	#6
	ld	a, #0x64
	ld	(hl+), a
	xor	a, a
	ld	(hl), a
;kaijugaiden.c:1176: if (gs.anim_tick & 0x04) return;
	ld	a, (#(_gs + 118) + 0)
	bit	2, a
	jr	Z, 00119$
	jp	00132$
00118$:
;kaijugaiden.c:1177: } else if (gs.boss_windup > 0) {
	ld	a, (#(_gs + 28) + 0)
	or	a, a
	jr	Z, 00115$
;kaijugaiden.c:1178: if (gs.boss_atk_type == BOSS_ATK_SLAM) by += 4;
	ld	hl, #_gs + 27
	ld	b, (hl)
	ld	a, b
	sub	a, #0x02
	jr	NZ, 00109$
	ldhl	sp,	#6
	ld	a, #0x64
	ld	(hl+), a
	xor	a, a
	ld	(hl), a
	jr	00119$
00109$:
;kaijugaiden.c:1176: if (gs.anim_tick & 0x04) return;
	ld	a, (#(_gs + 118) + 0)
;kaijugaiden.c:1179: else if (gs.boss_atk_type == BOSS_ATK_SWEEP) bx += (gs.anim_tick & 0x02) ? -2 : 2;
	and	a, #0x02
	ld	e, #0x00
	inc	b
	dec	b
	jr	NZ, 00106$
	or	a, e
	jr	Z, 00138$
	ld	de, #0xfffe
	jr	00139$
00138$:
	ld	de, #0x0002
00139$:
	ldhl	sp,	#4
	ld	a, (hl+)
	ld	b, (hl)
	dec	hl
	add	a, e
	ld	e, a
	ld	a, b
	adc	a, d
	ld	d, a
	ld	a, e
	ld	(hl+), a
	ld	(hl), d
	jr	00119$
00106$:
;kaijugaiden.c:1180: else by += (gs.anim_tick & 0x02) ? 1 : 0;
	or	a, e
	ld	a, #0x01
	jr	NZ, 00141$
	xor	a, a
00141$:
	add	a, #0x60
	ldhl	sp,	#6
	ld	(hl+), a
	ld	(hl), #0x00
	jr	00119$
00115$:
;kaijugaiden.c:1181: } else if (gs.boss_recover > 0) {
	ld	a, (#(_gs + 29) + 0)
	or	a, a
	jr	Z, 00112$
;kaijugaiden.c:1182: by -= 1;
	ldhl	sp,	#6
	ld	a, #0x5f
	ld	(hl+), a
	xor	a, a
	ld	(hl), a
	jr	00119$
00112$:
;kaijugaiden.c:1184: by += (gs.anim_tick & 0x08) ? 1 : 0;
	ld	a, (#(_gs + 118) + 0)
	bit	3, a
	ld	a, #0x01
	jr	NZ, 00143$
	xor	a, a
00143$:
	add	a, #0x60
	ldhl	sp,	#6
	ld	(hl+), a
	ld	(hl), #0x00
00119$:
;kaijugaiden.c:1186: bx = camera_apply_x(bx);
	push	bc
	ldhl	sp,	#6
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	call	_camera_apply_x
	ldhl	sp,	#2
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;kaijugaiden.c:1187: by = camera_apply_y(by);
	ldhl	sp,	#8
	ld	e, (hl)
	ld	d, #0x00
	call	_camera_apply_y
	ldhl	sp,	#4
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
	pop	bc
;kaijugaiden.c:1189: for (u8 row = 0; row < 2; ++row)
	ldhl	sp,	#6
	ld	(hl), #0x00
00130$:
	ldhl	sp,	#6
	ld	a, (hl)
	sub	a, #0x02
	jr	NC, 00132$
;kaijugaiden.c:1190: for (u8 col = 0; col < 4; ++col)
	inc	hl
	ld	(hl), #0x00
00127$:
	ldhl	sp,	#7
	ld	a, (hl)
	sub	a, #0x04
	jr	NC, 00131$
;kaijugaiden.c:1193: base_tile + row * 4 + col, 0x00);
	dec	hl
	ld	a, (hl+)
	ld	b, a
	add	a, a
	add	a, a
	ld	e, a
	add	a,c
	ld	d, (hl)
	add	a, d
	ldhl	sp,	#4
;kaijugaiden.c:1192: bx + col * TILE_W, (u8)(by + row * TILE_H),
	ld	(hl-), a
	dec	hl
	ld	l, (hl)
	ld	a, b
	add	a, a
	add	a, a
	add	a, a
	add	a, l
	ldhl	sp,	#5
	ld	(hl), a
	ldhl	sp,	#0
	ld	b, (hl)
	ldhl	sp,	#7
;kaijugaiden.c:1191: plat_set_sprite(id_base + row * 4 + col,
;kaijugaiden.c:149: move_sprite(id, x + 8, y + 16);   /* GBDK uses offset convention */
	ld	a, (hl-)
	dec	hl
	add	a, a
	add	a, a
	add	a, a
	add	a, b
	ld	b, a
	ld	a, e
	add	a, #0x1a
	add	a, d
	ld	e, a
	ld	a, (hl)
	add	a, #0x10
	ld	(hl), a
	ld	a, b
	add	a, #0x08
	ld	b, a
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1973: OAM_item_t * itm = &shadow_OAM[nb];
	ld	l, e
	ld	h, #0x00
	add	hl, hl
	add	hl, hl
	ld	e, l
	ld	d, h
	ld	hl, #_shadow_OAM
	add	hl, de
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1974: itm->y=y, itm->x=x;
	push	hl
	ldhl	sp,	#7
	ld	a, (hl)
	pop	hl
	ld	(hl+), a
	ld	(hl), b
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1887: shadow_OAM[nb].tile=tile;
	ld	hl,#_shadow_OAM + 1
	add	hl,de
	inc	hl
	push	hl
	ldhl	sp,	#6
	ld	a, (hl)
	pop	hl
	ld	(hl), a
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1946: shadow_OAM[nb].prop=prop;
	ld	hl,#_shadow_OAM + 1
	add	hl,de
	inc	hl
	inc	hl
	ld	(hl), #0x00
;kaijugaiden.c:1190: for (u8 col = 0; col < 4; ++col)
	ldhl	sp,	#7
	inc	(hl)
	jr	00127$
00131$:
;kaijugaiden.c:1189: for (u8 row = 0; row < 2; ++row)
	ldhl	sp,	#6
	inc	(hl)
	jr	00130$
00132$:
;kaijugaiden.c:1194: }
	add	sp, #8
	ret
;kaijugaiden.c:1197: static void spr_draw_minions(void) {
;	---------------------------------
; Function spr_draw_minions
; ---------------------------------
_spr_draw_minions:
	add	sp, #-15
;kaijugaiden.c:1198: for (u8 i = 0; i < MINION_MAX; ++i) {
	ldhl	sp,	#14
	ld	(hl), #0x00
00136$:
	ldhl	sp,	#14
	ld	a, (hl)
	sub	a, #0x05
	jp	NC, 00137$
;kaijugaiden.c:1199: if (!gs.minions[i].active) continue;
	ld	a, (hl)
	ld	c, a
	add	a, a
	add	a, a
	add	a, a
	add	a, c
	ld	e, a
	ld	d, #0x00
	ld	hl, #(_gs + 31)
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#13
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#12
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	a, (hl+)
	ld	d, a
	ld	a, (de)
	ld	(hl), a
	ld	a, (hl)
	or	a, a
	jp	Z, 00117$
;kaijugaiden.c:1200: u8 id_base = 6 + i * 4;
	inc	hl
	ld	a, (hl)
	add	a, a
	add	a, a
	add	a, #0x06
	ldhl	sp,	#2
	ld	(hl), a
;kaijugaiden.c:1201: s16 mx = gs.minions[i].x;
	ldhl	sp,	#11
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	inc	bc
	ld	e, c
	ld	d, b
	ld	a, (de)
	ldhl	sp,	#8
	ld	(hl+), a
	inc	de
	ld	a, (de)
;kaijugaiden.c:1202: u8  my = gs.minions[i].y;
	ld	(hl+), a
	inc	hl
	ld	a, (hl+)
	ld	c, a
	ld	a, (hl+)
	ld	b, a
	inc	bc
	inc	bc
	inc	bc
	ld	a, (bc)
;kaijugaiden.c:1203: if (gs.minions[i].attack_windup > 0) {
	ld	(hl-), a
	dec	hl
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0x0006
	add	hl, de
	ld	c, l
	ld	b, h
	ld	a, (bc)
	ld	c, a
;kaijugaiden.c:1205: if (my > 1) my -= 2;
	ldhl	sp,	#13
	ld	a, (hl)
	ldhl	sp,	#10
	ld	(hl), a
;kaijugaiden.c:1203: if (gs.minions[i].attack_windup > 0) {
	ld	a, c
	or	a, a
	jr	Z, 00115$
;kaijugaiden.c:1204: mx += (gs.minions[i].vx >= 0) ? 1 : -1;
	inc	hl
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0x0008
	add	hl, de
	ld	c, l
	ld	b, h
	ld	a, (bc)
	bit	7,a
	jr	NZ, 00139$
	ldhl	sp,	#11
	ld	a, #0x01
	ld	(hl+), a
	xor	a, a
	ld	(hl), a
	jr	00140$
00139$:
	ldhl	sp,	#11
	ld	a, #0xff
	ld	(hl+), a
	ld	(hl), #0xff
00140$:
	ldhl	sp,	#8
	ld	a, (hl+)
	ld	c, a
	ld	a, (hl+)
	inc	hl
	ld	b, a
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, bc
	ld	c, l
	ld	a, h
	ldhl	sp,	#8
	ld	(hl), c
	inc	hl
	ld	(hl), a
;kaijugaiden.c:1205: if (my > 1) my -= 2;
	ld	a, #0x01
	ldhl	sp,	#13
	sub	a, (hl)
	jr	NC, 00116$
	ldhl	sp,	#10
	ld	a, (hl)
	add	a, #0xfe
	ldhl	sp,	#13
	ld	(hl), a
	jr	00116$
00115$:
;kaijugaiden.c:1206: } else if (gs.minions[i].attack_recover > 0) {
	ldhl	sp,#11
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0x0007
	add	hl, de
	ld	c, l
	ld	b, h
	ld	a, (bc)
	or	a, a
	jr	Z, 00112$
;kaijugaiden.c:1207: if (my < SCR_H - 18) my += 2;
	ldhl	sp,	#13
	ld	a, (hl)
	sub	a, #0x7e
	jr	NC, 00116$
	ldhl	sp,	#10
	ld	a, (hl)
	add	a, #0x02
	ldhl	sp,	#13
	ld	(hl), a
	jr	00116$
00112$:
;kaijugaiden.c:1208: } else if (gs.minions[i].anim & 0x04) {
	ldhl	sp,#11
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0x0005
	add	hl, de
	ld	c, l
	ld	b, h
	ld	a, (bc)
	bit	2, a
	jr	Z, 00116$
;kaijugaiden.c:1209: if (my < SCR_H - 17) my += 1;
	ldhl	sp,	#13
	ld	a, (hl)
	sub	a, #0x7f
	jr	NC, 00116$
	ldhl	sp,	#10
	ld	a, (hl)
	inc	a
	ldhl	sp,	#13
	ld	(hl), a
00116$:
;kaijugaiden.c:1211: mx = camera_apply_x(mx);
	ldhl	sp,	#8
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	call	_camera_apply_x
	ldhl	sp,	#3
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;kaijugaiden.c:1212: my = (u8)camera_apply_y(my);
	ldhl	sp,	#13
	ld	e, (hl)
	xor	a, a
	ld	d, a
	call	_camera_apply_y
;kaijugaiden.c:1213: plat_set_sprite(id_base+0, mx,           my,           SPR_MINION+0, 0);
	ldhl	sp,	#3
	ld	a, (hl+)
	inc	hl
	ld	(hl), a
;kaijugaiden.c:149: move_sprite(id, x + 8, y + 16);   /* GBDK uses offset convention */
	ld	a, (hl+)
	ld	b, a
	ld	(hl), c
	ld	a, (hl+)
	add	a, #0x10
	ld	(hl), a
	ld	a, (hl+)
	ld	(hl+), a
	ld	a, b
	add	a, #0x08
	ld	(hl), a
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1973: OAM_item_t * itm = &shadow_OAM[nb];
	ldhl	sp,	#2
	ld	a, (hl)
	ldhl	sp,	#12
	ld	(hl+), a
	xor	a, a
	ld	(hl-), a
	ld	a, (hl-)
	dec	hl
	ld	(hl+), a
	ld	(hl), #0x00
	ld	a, #0x02
00213$:
	ldhl	sp,	#10
	sla	(hl)
	inc	hl
	rl	(hl)
	dec	a
	jr	NZ, 00213$
	ld	de, #_shadow_OAM
	ld	a, (hl-)
	ld	l, (hl)
	ld	h, a
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#14
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#13
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1974: itm->y=y, itm->x=x;
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ldhl	sp,	#8
	ld	a, (hl)
	ld	(de), a
	ldhl	sp,#12
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	l, e
	ld	h, d
	inc	hl
	inc	sp
	inc	sp
	ld	e, l
	ld	d, h
	push	de
	ldhl	sp,	#9
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1887: shadow_OAM[nb].tile=tile;
	ld	a, (hl+)
	ld	(de), a
	ld	de, #_shadow_OAM
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#10
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#9
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0x0002
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#14
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#13
	ld	(hl-), a
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	ld	(hl), #0x2a
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1946: shadow_OAM[nb].prop=prop;
	ld	de, #_shadow_OAM
	ldhl	sp,	#10
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#14
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#13
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0x0003
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#12
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#11
	ld	(hl-), a
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	ld	(hl), #0x00
;kaijugaiden.c:1214: plat_set_sprite(id_base+1, mx+TILE_W,    my,           SPR_MINION+1, 0);
	ldhl	sp,	#3
	ld	a, (hl)
	ldhl	sp,	#13
	ld	(hl), a
	ld	a, (hl-)
	add	a, #0x08
	ld	(hl), a
	ld	c, (hl)
	ldhl	sp,	#2
	ld	a, (hl)
	ldhl	sp,	#13
	ld	(hl), a
	ld	a, (hl-)
	dec	hl
	inc	a
;kaijugaiden.c:149: move_sprite(id, x + 8, y + 16);   /* GBDK uses offset convention */
	ld	(hl-), a
	ld	(hl), c
	ld	a, (hl)
	add	a, #0x08
	ldhl	sp,	#4
	ld	(hl), a
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1973: OAM_item_t * itm = &shadow_OAM[nb];
	ldhl	sp,	#11
	ld	a, (hl-)
	ld	(hl+), a
	xor	a, a
	ld	(hl-), a
	ld	a, (hl-)
	dec	hl
	ld	(hl+), a
	ld	(hl), #0x00
	ld	a, #0x02
00214$:
	ldhl	sp,	#8
	sla	(hl)
	inc	hl
	rl	(hl)
	dec	a
	jr	NZ, 00214$
	ld	de, #_shadow_OAM
	ld	a, (hl-)
	ld	l, (hl)
	ld	h, a
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#12
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#11
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1974: itm->y=y, itm->x=x;
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ldhl	sp,	#7
	ld	a, (hl)
	ld	(de), a
	ldhl	sp,#10
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	l, e
	ld	h, d
	inc	hl
	push	hl
	ld	a, l
	ldhl	sp,	#4
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#3
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	a, (hl+)
	ld	d, a
	ld	a, (hl)
	ld	(de), a
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1887: shadow_OAM[nb].tile=tile;
	ld	de, #_shadow_OAM
	ldhl	sp,	#8
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#5
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#4
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0x0002
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#12
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#11
	ld	(hl-), a
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	ld	(hl), #0x2b
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1946: shadow_OAM[nb].prop=prop;
	ld	de, #_shadow_OAM
	ldhl	sp,	#8
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#12
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#11
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0x0003
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#10
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#9
	ld	(hl-), a
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	ld	(hl), #0x00
;kaijugaiden.c:1215: plat_set_sprite(id_base+2, mx,           my+TILE_H,    SPR_MINION+2, 0);
	ldhl	sp,	#6
	ld	a, (hl)
	add	a, #0x08
	ldhl	sp,	#11
	ld	(hl), a
	ld	a, (hl+)
	inc	hl
	ld	c, a
	ld	a, (hl)
	add	a, #0x02
	ldhl	sp,	#9
;kaijugaiden.c:149: move_sprite(id, x + 8, y + 16);   /* GBDK uses offset convention */
	ld	(hl+), a
	ld	(hl), c
	ld	a, (hl)
	add	a, #0x10
	ld	(hl), a
	ldhl	sp,	#5
	ld	a, (hl)
	ldhl	sp,	#8
	ld	(hl), a
	ld	a, (hl)
	add	a, #0x08
	ldhl	sp,	#5
	ld	(hl), a
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1973: OAM_item_t * itm = &shadow_OAM[nb];
	ldhl	sp,	#9
	ld	a, (hl-)
	ld	(hl+), a
	xor	a, a
	ld	(hl-), a
	ld	a, (hl-)
	dec	hl
	ld	(hl+), a
	ld	(hl), #0x00
	ld	a, #0x02
00215$:
	ldhl	sp,	#6
	sla	(hl)
	inc	hl
	rl	(hl)
	dec	a
	jr	NZ, 00215$
	ld	de, #_shadow_OAM
	ld	a, (hl-)
	ld	l, (hl)
	ld	h, a
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#10
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#9
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1974: itm->y=y, itm->x=x;
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	a, (hl+)
	ld	d, a
	ld	a, (hl-)
	dec	hl
	ld	(de), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	l, e
	ld	h, d
	inc	hl
	push	hl
	ld	a, l
	ldhl	sp,	#5
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#4
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	a, (hl+)
	ld	d, a
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1887: shadow_OAM[nb].tile=tile;
	ld	a, (hl+)
	ld	(de), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #_shadow_OAM
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#6
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#5
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0x0002
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#11
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#10
	ld	(hl-), a
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	ld	(hl), #0x2c
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1946: shadow_OAM[nb].prop=prop;
	ld	de, #_shadow_OAM
	ldhl	sp,	#6
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#11
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#10
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0x0003
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#9
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#8
	ld	(hl-), a
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	ld	(hl), #0x00
;kaijugaiden.c:1216: plat_set_sprite(id_base+3, mx+TILE_W,    my+TILE_H,    SPR_MINION+3, 0);
	ldhl	sp,	#13
	inc	(hl)
	inc	(hl)
	inc	(hl)
;kaijugaiden.c:149: move_sprite(id, x + 8, y + 16);   /* GBDK uses offset convention */
	dec	hl
	dec	hl
	ld	a, (hl)
	add	a, #0x10
	ld	(hl+), a
	ld	a, (hl)
	add	a, #0x08
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1973: OAM_item_t * itm = &shadow_OAM[nb];
	ld	(hl+), a
	ld	a, (hl)
	ldhl	sp,	#9
	ld	(hl+), a
	xor	a, a
	ld	(hl-), a
	ld	a, (hl-)
	dec	hl
	ld	(hl+), a
	ld	(hl), #0x00
	ld	a, #0x02
00216$:
	ldhl	sp,	#7
	sla	(hl)
	inc	hl
	rl	(hl)
	dec	a
	jr	NZ, 00216$
	ld	de, #_shadow_OAM
	ld	a, (hl-)
	ld	l, (hl)
	ld	h, a
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#11
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#10
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1974: itm->y=y, itm->x=x;
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	a, (hl+)
	ld	d, a
	ld	a, (hl-)
	dec	hl
	ld	(de), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	l, e
	ld	h, d
	inc	hl
	push	hl
	ld	a, l
	ldhl	sp,	#7
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#6
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ldhl	sp,	#12
	ld	a, (hl)
	ld	(de), a
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1887: shadow_OAM[nb].tile=tile;
	ld	de, #_shadow_OAM
	ldhl	sp,	#7
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#12
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#11
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0x0002
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#14
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#13
	ld	(hl-), a
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	ld	(hl), #0x2d
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1946: shadow_OAM[nb].prop=prop;
	ld	de, #_shadow_OAM
	ldhl	sp,	#7
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#14
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#13
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0x0003
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#12
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#11
	ld	(hl-), a
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	ld	(hl), #0x00
;kaijugaiden.c:1216: plat_set_sprite(id_base+3, mx+TILE_W,    my+TILE_H,    SPR_MINION+3, 0);
00117$:
;kaijugaiden.c:1198: for (u8 i = 0; i < MINION_MAX; ++i) {
	ldhl	sp,	#14
	inc	(hl)
	jp	00136$
00137$:
;kaijugaiden.c:1218: }
	add	sp, #15
	ret
;kaijugaiden.c:1221: static void spr_draw_fx(void) {
;	---------------------------------
; Function spr_draw_fx
; ---------------------------------
_spr_draw_fx:
	add	sp, #-3
;kaijugaiden.c:1222: if (gs.fx_hit_timer > 0) {
	ld	a, (#(_gs + 114) + 0)
	or	a, a
	jr	Z, 00102$
;kaijugaiden.c:1223: s16 fx_hit_x = camera_apply_x(gs.fx_hit_x);
	ld	hl, #_gs + 112
	ld	e, (hl)
	xor	a, a
	ld	d, a
	call	_camera_apply_x
	pop	hl
	push	bc
;kaijugaiden.c:1224: s16 fx_hit_y = camera_apply_y(gs.fx_hit_y);
	ld	hl, #_gs + 113
	ld	e, (hl)
	xor	a, a
	ld	d, a
	call	_camera_apply_y
;kaijugaiden.c:1225: plat_set_sprite(34, fx_hit_x,          fx_hit_y,   SPR_FX_HIT+0, 0);
	ld	a, c
	ldhl	sp,	#0
	ld	l, (hl)
;kaijugaiden.c:149: move_sprite(id, x + 8, y + 16);   /* GBDK uses offset convention */
	add	a, #0x10
	ld	e, a
	ld	a, l
	add	a, #0x08
	ldhl	sp,	#2
	ld	(hl), a
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1973: OAM_item_t * itm = &shadow_OAM[nb];
	ld	hl, #(_shadow_OAM + 136)
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1974: itm->y=y, itm->x=x;
	ld	(hl), e
	ld	de, #(_shadow_OAM + 137)
	ldhl	sp,	#2
	ld	a, (hl)
	ld	(de), a
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1887: shadow_OAM[nb].tile=tile;
	ld	hl, #(_shadow_OAM + 138)
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1946: shadow_OAM[nb].prop=prop;
	ld	a, #0x2e
	ld	(hl+), a
	ld	(hl), #0x00
;kaijugaiden.c:1226: plat_set_sprite(35, fx_hit_x+TILE_W,   fx_hit_y,   SPR_FX_HIT+1, 0);
	ldhl	sp,	#0
	ld	a, (hl)
	add	a, #0x08
	ld	e, a
;kaijugaiden.c:149: move_sprite(id, x + 8, y + 16);   /* GBDK uses offset convention */
	ld	a, c
	add	a, #0x10
	ld	b, a
	ld	a, e
	add	a, #0x08
	ld	c, a
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1973: OAM_item_t * itm = &shadow_OAM[nb];
	ld	hl, #(_shadow_OAM + 140)
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1974: itm->y=y, itm->x=x;
	ld	a, b
	ld	(hl+), a
	ld	(hl), c
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1887: shadow_OAM[nb].tile=tile;
	ld	hl, #(_shadow_OAM + 142)
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1946: shadow_OAM[nb].prop=prop;
	ld	a, #0x2f
	ld	(hl+), a
	ld	(hl), #0x00
;kaijugaiden.c:1226: plat_set_sprite(35, fx_hit_x+TILE_W,   fx_hit_y,   SPR_FX_HIT+1, 0);
00102$:
;kaijugaiden.c:1228: if (gs.fx_nano_timer > 0) {
	ld	a, (#(_gs + 117) + 0)
	or	a, a
	jr	Z, 00121$
;kaijugaiden.c:1229: s16 fx_nano_x = camera_apply_x(gs.fx_nano_x);
	ld	hl, #_gs + 115
	ld	e, (hl)
	xor	a, a
	ld	d, a
	call	_camera_apply_x
	pop	hl
	push	bc
;kaijugaiden.c:1230: s16 fx_nano_y = camera_apply_y(gs.fx_nano_y);
	ld	hl, #_gs + 116
	ld	e, (hl)
	xor	a, a
	ld	d, a
	call	_camera_apply_y
;kaijugaiden.c:1231: plat_set_sprite(36, fx_nano_x,          fx_nano_y,  SPR_FX_NANO+0, 0);
	ld	a, c
	ldhl	sp,	#0
	ld	l, (hl)
;kaijugaiden.c:149: move_sprite(id, x + 8, y + 16);   /* GBDK uses offset convention */
	add	a, #0x10
	ld	e, a
	ld	a, l
	add	a, #0x08
	ldhl	sp,	#2
	ld	(hl), a
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1973: OAM_item_t * itm = &shadow_OAM[nb];
	ld	hl, #(_shadow_OAM + 144)
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1974: itm->y=y, itm->x=x;
	ld	(hl), e
	ld	de, #(_shadow_OAM + 145)
	ldhl	sp,	#2
	ld	a, (hl)
	ld	(de), a
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1887: shadow_OAM[nb].tile=tile;
	ld	hl, #(_shadow_OAM + 146)
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1946: shadow_OAM[nb].prop=prop;
	ld	a, #0x30
	ld	(hl+), a
	ld	(hl), #0x00
;kaijugaiden.c:1232: plat_set_sprite(37, fx_nano_x+TILE_W,   fx_nano_y,  SPR_FX_NANO+1, 0);
	ldhl	sp,	#0
	ld	a, (hl)
	add	a, #0x08
	ld	e, a
;kaijugaiden.c:149: move_sprite(id, x + 8, y + 16);   /* GBDK uses offset convention */
	ld	a, c
	add	a, #0x10
	ld	b, a
	ld	a, e
	add	a, #0x08
	ld	c, a
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1973: OAM_item_t * itm = &shadow_OAM[nb];
	ld	hl, #(_shadow_OAM + 148)
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1974: itm->y=y, itm->x=x;
	ld	a, b
	ld	(hl+), a
	ld	(hl), c
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1887: shadow_OAM[nb].tile=tile;
	ld	hl, #(_shadow_OAM + 150)
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1946: shadow_OAM[nb].prop=prop;
	ld	a, #0x31
	ld	(hl+), a
	ld	(hl), #0x00
;kaijugaiden.c:1232: plat_set_sprite(37, fx_nano_x+TILE_W,   fx_nano_y,  SPR_FX_NANO+1, 0);
00121$:
;kaijugaiden.c:1234: }
	add	sp, #3
	ret
;kaijugaiden.c:1238: static void spr_draw_cinematic(void) {
;	---------------------------------
; Function spr_draw_cinematic
; ---------------------------------
_spr_draw_cinematic:
	add	sp, #-16
;kaijugaiden.c:1240: s16 ay = (s16)(SCR_H/2 - 24 + (gs.cut_frame % 2) * 2);
	ld	a, (#(_gs + 101) + 0)
	and	a, #0x01
	add	a, a
	ld	c, a
	add	a, #0x30
	ldhl	sp,	#2
;kaijugaiden.c:1241: s16 by_pos = (s16)(SCR_H/2 - 24 - (gs.cut_frame % 2) * 2);
	ld	(hl+), a
	ld	a, #0x30
	sub	a, c
	ld	(hl), a
;kaijugaiden.c:1242: for (u8 row = 0; row < 4; ++row)
	ldhl	sp,	#14
	ld	(hl), #0x00
00115$:
	ldhl	sp,	#14
	ld	a, (hl)
	sub	a, #0x04
	jp	NC, 00117$
;kaijugaiden.c:1243: for (u8 col = 0; col < 3; ++col) {
	inc	hl
	ld	(hl), #0x00
00112$:
	ldhl	sp,	#15
	ld	a, (hl)
	sub	a, #0x03
	jp	NC, 00116$
;kaijugaiden.c:1247: SPR_CINEMATIC_A + row*3+col, 0x00);
	dec	hl
	ld	c, (hl)
	ld	a, c
	add	a, a
	add	a, c
	ldhl	sp,	#4
	ld	(hl), a
	ld	a, (hl)
	add	a, #0x32
	ld	b, a
	ldhl	sp,	#15
	ld	a, (hl)
	ldhl	sp,	#5
	ld	(hl+), a
	add	a, b
;kaijugaiden.c:1246: 8  + col * TILE_W, (u8)(ay + row * TILE_H),
	ld	(hl+), a
	ld	a, c
	add	a, a
	add	a, a
	add	a, a
	ld	(hl), a
	ldhl	sp,	#2
	ld	a, (hl)
	ldhl	sp,	#7
	add	a, (hl)
	ld	c, a
	ldhl	sp,	#15
	ld	a, (hl)
	add	a, a
	add	a, a
	add	a, a
	add	a, #0x08
	ld	b, a
;kaijugaiden.c:1245: plat_set_sprite(row*3+col,
	ldhl	sp,	#4
	ld	a, (hl+)
	add	a, (hl)
	ld	e, a
;kaijugaiden.c:149: move_sprite(id, x + 8, y + 16);   /* GBDK uses offset convention */
	ld	a, c
	add	a, #0x10
	ldhl	sp,	#8
	ld	(hl+), a
	ld	a, b
	add	a, #0x08
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1973: OAM_item_t * itm = &shadow_OAM[nb];
	ld	(hl+), a
	xor	a, a
	sla	e
	adc	a, a
	sla	e
	adc	a, a
	ld	(hl), e
	inc	hl
	ld	(hl), a
	ld	de, #_shadow_OAM
	ld	a, (hl-)
	ld	l, (hl)
	ld	h, a
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#14
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#13
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1974: itm->y=y, itm->x=x;
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ldhl	sp,	#8
	ld	a, (hl)
	ld	(de), a
	ldhl	sp,#12
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	l, e
	ld	h, d
	inc	hl
	inc	sp
	inc	sp
	ld	e, l
	ld	d, h
	push	de
	ldhl	sp,	#9
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1887: shadow_OAM[nb].tile=tile;
	ld	a, (hl+)
	ld	(de), a
	ld	de, #_shadow_OAM
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#10
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#9
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0x0002
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#14
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#13
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ldhl	sp,	#6
	ld	a, (hl)
	ld	(de), a
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1946: shadow_OAM[nb].prop=prop;
	ld	de, #_shadow_OAM
	ldhl	sp,	#10
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#14
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#13
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0x0003
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#12
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#11
	ld	(hl-), a
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	ld	(hl), #0x00
;kaijugaiden.c:1251: SPR_CINEMATIC_B + row*3+col, 0x20);
	ldhl	sp,	#4
	ld	a, (hl)
	add	a, #0x3e
	ldhl	sp,	#13
	ld	(hl), a
	ld	a, (hl)
	ldhl	sp,	#5
	add	a, (hl)
	ldhl	sp,	#13
	ld	(hl), a
;kaijugaiden.c:1250: 92 + (2-col) * TILE_W, (u8)(by_pos + row * TILE_H),
	ldhl	sp,	#7
	ld	a, (hl)
	ldhl	sp,	#3
	add	a, (hl)
	ldhl	sp,	#10
	ld	(hl), a
	ld	a, #0x02
	ldhl	sp,	#5
	sub	a, (hl)
	add	a, a
	add	a, a
	add	a, a
	add	a, #0x5c
	ldhl	sp,	#11
	ld	(hl), a
;kaijugaiden.c:1249: plat_set_sprite(12 + row*3+col,
	ldhl	sp,	#4
	ld	a, (hl)
	add	a, #0x0c
	ldhl	sp,	#12
	ld	(hl), a
	ld	a, (hl)
	ldhl	sp,	#5
	add	a, (hl)
	ldhl	sp,	#12
;kaijugaiden.c:149: move_sprite(id, x + 8, y + 16);   /* GBDK uses offset convention */
	ld	(hl-), a
	dec	hl
	ld	a, (hl)
	add	a, #0x10
	ld	(hl+), a
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1973: OAM_item_t * itm = &shadow_OAM[nb];
	ld	a, (hl+)
	add	a, #0x08
	ld	c, a
	ld	de, #_shadow_OAM+0
	ld	a, (hl-)
	ld	b, a
	xor	a, a
	sla	b
	adc	a, a
	sla	b
	adc	a, a
	ld	(hl), b
	inc	hl
	ld	(hl-), a
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	ld	e, l
	ld	d, h
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1974: itm->y=y, itm->x=x;
	ldhl	sp,	#10
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1887: shadow_OAM[nb].tile=tile;
	ld	a, (hl+)
	ld	(de), a
	inc	de
	ld	a, c
	ld	(de), a
	ld	bc, #_shadow_OAM+0
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, bc
	inc	hl
	inc	hl
	ld	c, l
	ld	b, h
	ldhl	sp,	#13
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1946: shadow_OAM[nb].prop=prop;
	ld	a, (hl-)
	ld	(bc), a
	ld	de, #_shadow_OAM
	ld	a, (hl-)
	ld	l, (hl)
	ld	h, a
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#11
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#10
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0x0003
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#14
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#13
	ld	(hl-), a
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	ld	(hl), #0x20
;kaijugaiden.c:1243: for (u8 col = 0; col < 3; ++col) {
	ldhl	sp,	#15
	inc	(hl)
	jp	00112$
00116$:
;kaijugaiden.c:1242: for (u8 row = 0; row < 4; ++row)
	ldhl	sp,	#14
	inc	(hl)
	jp	00115$
00117$:
;kaijugaiden.c:1253: }
	add	sp, #16
	ret
;kaijugaiden.c:1256: static void spr_hide_all(void) {
;	---------------------------------
; Function spr_hide_all
; ---------------------------------
_spr_hide_all:
;kaijugaiden.c:1261: for (u8 i = 0; i < 40; ++i) { move_sprite(i, 0, 0); }
	ld	c, #0x00
00104$:
	ld	a, c
	sub	a, #0x28
	ret	NC
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1973: OAM_item_t * itm = &shadow_OAM[nb];
	ld	de, #_shadow_OAM+0
	ld	l, c
	xor	a, a
	ld	h, a
	add	hl, hl
	add	hl, hl
	add	hl, de
;c:\users\rrcar\documents\driptech\.tools\gbdk\gbdk\include\gb\gb.h:1974: itm->y=y, itm->x=x;
	xor	a, a
	ld	(hl+), a
	ld	(hl), a
;kaijugaiden.c:1261: for (u8 i = 0; i < 40; ++i) { move_sprite(i, 0, 0); }
	inc	c
;kaijugaiden.c:1268: }
	jr	00104$
;kaijugaiden.c:1275: static void splash_init(void) {
;	---------------------------------
; Function splash_init
; ---------------------------------
_splash_init:
;kaijugaiden.c:1276: camera_reset();
	call	_camera_reset
;kaijugaiden.c:1277: gs.phase_timer = 0;
	ld	hl, #(_gs + 77)
	xor	a, a
	ld	(hl+), a
;kaijugaiden.c:1278: gs.skip_b_hold = 0;
	ld	(hl+), a
	ld	(hl), #0x00
;kaijugaiden.c:1279: spr_hide_all();
	call	_spr_hide_all
;kaijugaiden.c:1280: bg_draw_splash();
;kaijugaiden.c:1281: }
	jp	_bg_draw_splash
;kaijugaiden.c:1284: static int splash_update(void) {
;	---------------------------------
; Function splash_update
; ---------------------------------
_splash_update:
;kaijugaiden.c:1285: gs.phase_timer++;
	ld	hl, #(_gs + 77)
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	inc	bc
	ld	hl, #(_gs + 77)
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;kaijugaiden.c:136: static inline u8 plat_held(u8 mask)  { return (_joy_cur  & mask) ? 1 : 0; }
	push	hl
	ld	hl, #__joy_cur
	bit	1, (hl)
	pop	hl
	ld	e, #0x01
	jr	NZ, 00117$
	ld	e, #0x00
00117$:
;kaijugaiden.c:1286: if (plat_held(BTN_B)) gs.skip_b_hold++;
	ld	bc, #_gs + 79
	ld	a, e
	or	a, a
	jr	Z, 00102$
	ld	a, (bc)
	inc	a
	ld	(bc), a
	jr	00103$
00102$:
;kaijugaiden.c:1287: else                   gs.skip_b_hold = 0;
	xor	a, a
	ld	(bc), a
00103$:
;kaijugaiden.c:1289: if (gs.phase_timer >= SPLASH_HOLD_FRAMES) return 1;
	ld	hl, #(_gs + 77)
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	sub	a, #0x78
	ld	a, h
	sbc	a, #0x00
	jr	C, 00105$
	ld	bc, #0x0001
	ret
00105$:
;kaijugaiden.c:138: return ((_joy_cur & mask) && !(_joy_prev & mask)) ? 1 : 0;
	push	hl
	ld	hl, #__joy_cur
	bit	0, (hl)
	pop	hl
	jr	Z, 00118$
	push	hl
	ld	hl, #__joy_prev
	bit	0, (hl)
	pop	hl
	ld	a, #0x01
	jr	Z, 00119$
00118$:
	xor	a, a
00119$:
;kaijugaiden.c:1290: if (plat_pressed(BTN_A) || plat_pressed(BTN_START)) return 1;
	or	a, a
	jr	NZ, 00106$
;kaijugaiden.c:138: return ((_joy_cur & mask) && !(_joy_prev & mask)) ? 1 : 0;
	push	hl
	ld	hl, #__joy_cur
	bit	3, (hl)
	pop	hl
	jr	Z, 00123$
	push	hl
	ld	hl, #__joy_prev
	bit	3, (hl)
	pop	hl
	ld	a, #0x01
	jr	Z, 00124$
00123$:
	xor	a, a
00124$:
;kaijugaiden.c:1290: if (plat_pressed(BTN_A) || plat_pressed(BTN_START)) return 1;
	or	a, a
	jr	Z, 00107$
00106$:
	ld	bc, #0x0001
	ret
00107$:
;kaijugaiden.c:1291: if (gs.skip_b_hold >= SKIP_HOLD_FRAMES) return 1;
	ld	a, (bc)
	sub	a, #0x5a
	jr	C, 00110$
	ld	bc, #0x0001
	ret
00110$:
;kaijugaiden.c:1292: return 0;
	ld	bc, #0x0000
;kaijugaiden.c:1293: }
	ret
;kaijugaiden.c:1318: static void cinematic_init(void) {
;	---------------------------------
; Function cinematic_init
; ---------------------------------
_cinematic_init:
;kaijugaiden.c:1319: camera_reset();
	call	_camera_reset
;kaijugaiden.c:1320: gs.cut_frame = 0;
	ld	hl, #_gs + 101
	ld	(hl), #0x00
;kaijugaiden.c:1321: gs.cut_timer = 0;
	ld	hl, #(_gs + 102)
	xor	a, a
	ld	(hl+), a
	ld	(hl), a
;kaijugaiden.c:1322: gs.skip_b_hold = 0;
	ld	hl, #_gs + 79
	ld	(hl), #0x00
;kaijugaiden.c:1323: bg_draw_beach();
	call	_bg_draw_beach
;kaijugaiden.c:1324: spr_draw_cinematic();
;kaijugaiden.c:1325: }
	jp	_spr_draw_cinematic
;kaijugaiden.c:1328: static int cinematic_update(void) {
;	---------------------------------
; Function cinematic_update
; ---------------------------------
_cinematic_update:
;kaijugaiden.c:1329: gs.cut_timer++;
	ld	hl, #(_gs + 102)
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	inc	bc
	ld	hl, #(_gs + 102)
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;kaijugaiden.c:1330: gs.anim_tick++;
	ld	bc, #_gs + 118
	ld	a, (bc)
	inc	a
	ld	(bc), a
;kaijugaiden.c:136: static inline u8 plat_held(u8 mask)  { return (_joy_cur  & mask) ? 1 : 0; }
	push	hl
	ld	hl, #__joy_cur
	bit	1, (hl)
	pop	hl
	ld	e, #0x01
	jr	NZ, 00116$
	ld	e, #0x00
00116$:
;kaijugaiden.c:1333: if (plat_held(BTN_B)) gs.skip_b_hold++;
	ld	hl, #_gs + 79
	ld	a, e
	or	a, a
	jr	Z, 00102$
	inc	(hl)
	jr	00103$
00102$:
;kaijugaiden.c:1334: else                   gs.skip_b_hold = 0;
	ld	(hl), #0x00
00103$:
;kaijugaiden.c:1335: if (gs.skip_b_hold >= SKIP_HOLD_FRAMES) return 1;
	ld	a, (hl)
	sub	a, #0x5a
	jr	C, 00105$
	ld	bc, #0x0001
	ret
00105$:
;kaijugaiden.c:1338: if (gs.cut_timer >= CUT_DURATION) {
	ld	hl, #(_gs + 102)
	ld	a,	(hl+)
	ld	h, (hl)
	sub	a, #0x3c
	ld	a, h
	sbc	a, #0x00
	jr	C, 00109$
;kaijugaiden.c:1339: gs.cut_timer = 0;
	ld	hl, #(_gs + 102)
	xor	a, a
	ld	(hl+), a
;kaijugaiden.c:1340: gs.cut_frame++;
	ld	(hl-), a
	dec	hl
	inc	(hl)
;kaijugaiden.c:1342: bg_draw_beach();
	push	hl
	push	bc
	call	_bg_draw_beach
	pop	bc
	pop	hl
;kaijugaiden.c:1343: if (gs.cut_frame >= CUT_COUNT) return 1;
	ld	a, (hl)
	sub	a, #0x08
	jr	C, 00109$
	ld	bc, #0x0001
	ret
00109$:
;kaijugaiden.c:1346: if ((gs.anim_tick % 8) == 0) bg_draw_beach();
	ld	a, (bc)
	and	a, #0x07
	jr	NZ, 00111$
	call	_bg_draw_beach
00111$:
;kaijugaiden.c:1348: spr_draw_cinematic();
	call	_spr_draw_cinematic
;kaijugaiden.c:1349: return 0;
	ld	bc, #0x0000
;kaijugaiden.c:1350: }
	ret
;kaijugaiden.c:1357: static void title_init(void) {
;	---------------------------------
; Function title_init
; ---------------------------------
_title_init:
;kaijugaiden.c:1358: camera_reset();
	call	_camera_reset
;kaijugaiden.c:1359: gs.menu_sel  = 0;
	ld	hl, #_gs + 82
	ld	(hl), #0x00
;kaijugaiden.c:1360: gs.phase_timer = 0;
	ld	hl, #(_gs + 77)
	xor	a, a
	ld	(hl+), a
	ld	(hl), a
;kaijugaiden.c:1361: spr_hide_all();
	call	_spr_hide_all
;kaijugaiden.c:1362: bg_draw_title();
;kaijugaiden.c:1363: }
	jp	_bg_draw_title
;kaijugaiden.c:1366: static int title_update(void) {
;	---------------------------------
; Function title_update
; ---------------------------------
_title_update:
	add	sp, #-4
;kaijugaiden.c:1367: gs.phase_timer++;
	ld	hl, #(_gs + 77)
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	inc	bc
	ld	hl, #(_gs + 77)
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;kaijugaiden.c:138: return ((_joy_cur & mask) && !(_joy_prev & mask)) ? 1 : 0;
	push	hl
	ld	hl, #__joy_cur
	bit	7, (hl)
	pop	hl
	jr	Z, 00114$
	push	hl
	ld	hl, #__joy_prev
	bit	7, (hl)
	pop	hl
	ld	a, #0x01
	jr	Z, 00115$
00114$:
	xor	a, a
00115$:
	ldhl	sp,	#3
;kaijugaiden.c:1369: gs.menu_sel = (gs.menu_sel + 1) % 2;
;kaijugaiden.c:1368: if (plat_pressed(BTN_DOWN)) {
	ld	(hl), a
	or	a, a
	jr	Z, 00102$
;kaijugaiden.c:1369: gs.menu_sel = (gs.menu_sel + 1) % 2;
	ld	a, (#(_gs + 82) + 0)
	ldhl	sp,#3
	ld	(hl), a
	ldhl	sp,	#0
	ld	(hl+), a
	ld	(hl), #0x00
	pop	de
	push	de
	ld	l, e
	ld	h, d
	inc	hl
	push	hl
	ld	a, l
	ldhl	sp,	#4
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#3
	ld	(hl-), a
	ld	bc, #0x0002
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	call	__modsint
	ld	hl, #(_gs + 82)
	ld	(hl), c
;kaijugaiden.c:1370: bg_draw_title();
	call	_bg_draw_title
00102$:
;kaijugaiden.c:138: return ((_joy_cur & mask) && !(_joy_prev & mask)) ? 1 : 0;
	push	hl
	ld	hl, #__joy_cur
	bit	6, (hl)
	pop	hl
	jr	Z, 00119$
	push	hl
	ld	hl, #__joy_prev
	bit	6, (hl)
	pop	hl
	ld	a, #0x01
	jr	Z, 00120$
00119$:
	xor	a, a
00120$:
;kaijugaiden.c:1372: if (plat_pressed(BTN_UP)) {
	or	a, a
	jr	Z, 00104$
;kaijugaiden.c:1373: gs.menu_sel = (gs.menu_sel == 0) ? 1 : 0;
	ld	a, (#(_gs + 82) + 0)
	or	a, a
	ld	a, #0x01
	jr	Z, 00125$
	xor	a, a
00125$:
	ld	(#(_gs + 82)),a
;kaijugaiden.c:1374: bg_draw_title();
	call	_bg_draw_title
00104$:
;kaijugaiden.c:138: return ((_joy_cur & mask) && !(_joy_prev & mask)) ? 1 : 0;
	push	hl
	ld	hl, #__joy_cur
	bit	0, (hl)
	pop	hl
	jr	Z, 00126$
	push	hl
	ld	hl, #__joy_prev
	bit	0, (hl)
	pop	hl
	ld	a, #0x01
	jr	Z, 00127$
00126$:
	xor	a, a
00127$:
;kaijugaiden.c:1376: if (plat_pressed(BTN_A) || plat_pressed(BTN_START)) {
	or	a, a
	jr	NZ, 00105$
;kaijugaiden.c:138: return ((_joy_cur & mask) && !(_joy_prev & mask)) ? 1 : 0;
	push	hl
	ld	hl, #__joy_cur
	bit	3, (hl)
	pop	hl
	jr	Z, 00131$
	push	hl
	ld	hl, #__joy_prev
	bit	3, (hl)
	pop	hl
	ld	a, #0x01
	jr	Z, 00132$
00131$:
	xor	a, a
00132$:
;kaijugaiden.c:1376: if (plat_pressed(BTN_A) || plat_pressed(BTN_START)) {
	or	a, a
	jr	Z, 00106$
00105$:
;kaijugaiden.c:1377: return (gs.menu_sel == 0) ? 1 : 2;
	ld	a, (#(_gs + 82) + 0)
	or	a, a
	jr	NZ, 00136$
	ld	bc, #0x0001
	jr	00112$
00136$:
	ld	bc, #0x0002
	jr	00112$
00106$:
;kaijugaiden.c:1379: return 0;
	ld	bc, #0x0000
00112$:
;kaijugaiden.c:1380: }
	add	sp, #4
	ret
;kaijugaiden.c:1382: static void password_draw(void) {
;	---------------------------------
; Function password_draw
; ---------------------------------
_password_draw:
;kaijugaiden.c:1383: bg_fill(TILE_BLANK);
	xor	a, a
	call	_bg_fill
;kaijugaiden.c:1384: spr_hide_all();
	call	_spr_hide_all
;kaijugaiden.c:1385: bg_draw_text(6, 2, "PASSWORD");
	ld	de, #___str_31
	push	de
	ld	e, #0x02
	ld	a, #0x06
	call	_bg_draw_text
;kaijugaiden.c:1386: bg_draw_text(2, 5, "EDIT 16 HEX");
	ld	de, #___str_32
	push	de
	ld	e, #0x05
	ld	a, #0x02
	call	_bg_draw_text
;kaijugaiden.c:1387: for (u8 i = 0; i < PASSWORD_LEN; ++i)
	ld	c, #0x00
00107$:
	ld	a, c
	sub	a, #0x10
	jr	NC, 00101$
;kaijugaiden.c:1388: plat_set_bkg_tile(2 + i, 8, bg_char_to_tile(gs.password_buf[i]));
	ld	hl, #(_gs + 83)
	ld	b, #0x00
	add	hl, bc
	ld	a, (hl)
	push	bc
	call	_bg_char_to_tile
	pop	bc
	ld	b, c
	inc	b
	inc	b
;kaijugaiden.c:146: set_bkg_tile_xy(x, y, tile);
	push	bc
	push	af
	inc	sp
	ld	e, #0x08
	ld	a, b
	call	_set_bkg_tile_xy
	pop	bc
;kaijugaiden.c:1387: for (u8 i = 0; i < PASSWORD_LEN; ++i)
	inc	c
	jr	00107$
00101$:
;kaijugaiden.c:1389: for (u8 i = 0; i < PASSWORD_LEN; ++i)
	ld	c, #0x00
00110$:
;kaijugaiden.c:1390: plat_set_bkg_tile(2 + i, 9, TILE_BLANK);
	ld	a,c
	cp	a,#0x10
	jr	NC, 00102$
	add	a, #0x02
;kaijugaiden.c:146: set_bkg_tile_xy(x, y, tile);
	push	bc
	ld	h, #0x00
	push	hl
	inc	sp
	ld	e, #0x09
	call	_set_bkg_tile_xy
	pop	bc
;kaijugaiden.c:1389: for (u8 i = 0; i < PASSWORD_LEN; ++i)
	inc	c
	jr	00110$
00102$:
;kaijugaiden.c:1391: plat_set_bkg_tile(2 + gs.password_index, 9, TILE_CLIFF_A);
	ld	a, (#(_gs + 100) + 0)
	add	a, #0x02
;kaijugaiden.c:146: set_bkg_tile_xy(x, y, tile);
	ld	h, #0x05
	push	hl
	inc	sp
	ld	e, #0x09
	call	_set_bkg_tile_xy
;kaijugaiden.c:1392: bg_draw_text(2, 12, "UD CHANGE");
	ld	de, #___str_33
	push	de
	ld	e, #0x0c
	ld	a, #0x02
	call	_bg_draw_text
;kaijugaiden.c:1393: bg_draw_text(2, 13, "LR MOVE");
	ld	de, #___str_34
	push	de
	ld	e, #0x0d
	ld	a, #0x02
	call	_bg_draw_text
;kaijugaiden.c:1394: bg_draw_text(2, 14, "A APPLY");
	ld	de, #___str_35
	push	de
	ld	e, #0x0e
	ld	a, #0x02
	call	_bg_draw_text
;kaijugaiden.c:1395: bg_draw_text(2, 15, "B BACK");
	ld	de, #___str_36
	push	de
	ld	e, #0x0f
	ld	a, #0x02
	call	_bg_draw_text
;kaijugaiden.c:1396: }
	ret
___str_31:
	.ascii "PASSWORD"
	.db 0x00
___str_32:
	.ascii "EDIT 16 HEX"
	.db 0x00
___str_33:
	.ascii "UD CHANGE"
	.db 0x00
___str_34:
	.ascii "LR MOVE"
	.db 0x00
___str_35:
	.ascii "A APPLY"
	.db 0x00
___str_36:
	.ascii "B BACK"
	.db 0x00
;kaijugaiden.c:1398: static void password_init(void) {
;	---------------------------------
; Function password_init
; ---------------------------------
_password_init:
	add	sp, #-8
;kaijugaiden.c:1399: camera_reset();
	call	_camera_reset
;kaijugaiden.c:1400: gs.phase_timer = 0;
	ld	hl, #(_gs + 77)
	xor	a, a
	ld	(hl+), a
	ld	(hl), a
;kaijugaiden.c:1401: gs.password_index = 0;
	ld	hl, #_gs + 100
	ld	(hl), #0x00
;kaijugaiden.c:1402: password_encode(gs.password_buf, gs.cleared_bosses, gs.cyphers);
	ld	de, #(_gs + 108)
	ld	a, (de)
	ldhl	sp,	#0
	ld	(hl+), a
	inc	de
	ld	a, (de)
	ld	(hl+), a
	inc	de
	ld	a, (de)
	ld	(hl+), a
	inc	de
	ld	a, (de)
	ld	(hl+), a
	ld	de, #(_gs + 104)
	ld	a, (de)
	ld	(hl+), a
	inc	de
	ld	a, (de)
	ld	(hl+), a
	inc	de
	ld	a, (de)
	ld	(hl+), a
	inc	de
	ld	a, (de)
	ld	(hl), a
	ldhl	sp,	#2
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	push	de
	ldhl	sp,	#2
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	push	de
	ldhl	sp,	#10
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	push	de
	ldhl	sp,	#10
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	push	de
	ld	de, #(_gs + 83)
	call	_password_encode
;kaijugaiden.c:1403: password_draw();
	call	_password_draw
;kaijugaiden.c:1404: }
	add	sp, #8
	ret
;kaijugaiden.c:1407: static int password_update(void) {
;	---------------------------------
; Function password_update
; ---------------------------------
_password_update:
	add	sp, #-4
;kaijugaiden.c:1408: gs.phase_timer++;
	ld	bc, #_gs+0
	ld	de, #(_gs + 77)
	ld	a, (de)
	ldhl	sp,	#0
	ld	(hl+), a
	inc	de
	ld	a, (de)
	ld	(hl), a
	pop	de
	push	de
	ld	l, e
	ld	h, d
	inc	hl
	push	hl
	ld	a, l
	ldhl	sp,	#4
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#3
	ld	(hl-), a
	ld	de, #(_gs + 77)
	ld	a, (hl+)
	ld	(de), a
	inc	de
	ld	a, (hl)
	ld	(de), a
;kaijugaiden.c:138: return ((_joy_cur & mask) && !(_joy_prev & mask)) ? 1 : 0;
	push	hl
	ld	hl, #__joy_cur
	bit	5, (hl)
	pop	hl
	jr	Z, 00125$
	push	hl
	ld	hl, #__joy_prev
	bit	5, (hl)
	pop	hl
	ld	e, #0x01
	jr	Z, 00126$
00125$:
	ld	e, #0x00
00126$:
;kaijugaiden.c:1410: if (plat_pressed(BTN_LEFT) && gs.password_index > 0) {
	ld	a, e
	or	a, a
	jr	Z, 00102$
	ld	a, (#(_gs + 100) + 0)
	or	a, a
	jr	Z, 00102$
;kaijugaiden.c:1411: gs.password_index--;
	dec	a
	ld	(#(_gs + 100)),a
;kaijugaiden.c:1412: password_draw();
	push	bc
	call	_password_draw
	pop	bc
00102$:
;kaijugaiden.c:138: return ((_joy_cur & mask) && !(_joy_prev & mask)) ? 1 : 0;
	push	hl
	ld	hl, #__joy_cur
	bit	4, (hl)
	pop	hl
	jr	Z, 00130$
	push	hl
	ld	hl, #__joy_prev
	bit	4, (hl)
	pop	hl
	ld	a, #0x01
	jr	Z, 00131$
00130$:
	xor	a, a
00131$:
;kaijugaiden.c:1414: if (plat_pressed(BTN_RIGHT) && gs.password_index + 1 < PASSWORD_LEN) {
	or	a, a
	jr	Z, 00105$
	ld	a, (#(_gs + 100) + 0)
	ldhl	sp,#3
	ld	(hl), a
	ld	e, (hl)
	xor	a, a
	ld	l, e
	ld	h, a
	inc	hl
	ld	a, l
	sub	a, #0x10
	ld	a, h
	sbc	a, #0x00
	jr	NC, 00105$
;kaijugaiden.c:1415: gs.password_index++;
	ldhl	sp,	#3
	ld	a, (hl)
	inc	a
	ld	(#(_gs + 100)),a
;kaijugaiden.c:1416: password_draw();
	push	bc
	call	_password_draw
	pop	bc
00105$:
;kaijugaiden.c:138: return ((_joy_cur & mask) && !(_joy_prev & mask)) ? 1 : 0;
	push	hl
	ld	hl, #__joy_cur
	bit	6, (hl)
	pop	hl
	jr	Z, 00135$
	push	hl
	ld	hl, #__joy_prev
	bit	6, (hl)
	pop	hl
	ld	e, #0x01
	jr	Z, 00136$
00135$:
	ld	e, #0x00
00136$:
;kaijugaiden.c:1419: u8 nibble = password_hex_to_nibble(gs.password_buf[gs.password_index]);
;kaijugaiden.c:1418: if (plat_pressed(BTN_UP)) {
	ld	a, e
	or	a, a
	jr	Z, 00108$
;kaijugaiden.c:1419: u8 nibble = password_hex_to_nibble(gs.password_buf[gs.password_index]);
	ld	hl, #(_gs + 100)
	ld	l, (hl)
	ld	h, #0x00
	ld	de, #(_gs + 83)
	add	hl, de
	ld	a, (hl)
	push	bc
	call	_password_hex_to_nibble
	ldhl	sp,	#5
	ld	(hl), a
	pop	bc
;kaijugaiden.c:1420: gs.password_buf[gs.password_index] = password_nibble_to_hex((u8)((nibble + 1) & 0x0F));
	ld	a, (#(_gs + 100) + 0)
	add	a, #<((_gs + 83))
	ld	e, a
	ld	a, #0x00
	adc	a, #>((_gs + 83))
	ld	d, a
	ldhl	sp,	#3
	ld	a, (hl)
	inc	a
	and	a, #0x0f
	push	bc
	push	de
	call	_password_nibble_to_hex
	pop	de
;kaijugaiden.c:1421: password_draw();
	ld	(de), a
	call	_password_draw
	pop	bc
00108$:
;kaijugaiden.c:138: return ((_joy_cur & mask) && !(_joy_prev & mask)) ? 1 : 0;
	push	hl
	ld	hl, #__joy_cur
	bit	7, (hl)
	pop	hl
	jr	Z, 00140$
	push	hl
	ld	hl, #__joy_prev
	bit	7, (hl)
	pop	hl
	ld	a, #0x01
	jr	Z, 00141$
00140$:
	xor	a, a
00141$:
;kaijugaiden.c:1423: if (plat_pressed(BTN_DOWN)) {
	or	a, a
	jr	Z, 00110$
;kaijugaiden.c:1424: u8 nibble = password_hex_to_nibble(gs.password_buf[gs.password_index]);
	ld	hl, #(_gs + 100)
	ld	l, (hl)
	ld	h, #0x00
	ld	de, #(_gs + 83)
	add	hl, de
	ld	a, (hl)
	push	bc
	call	_password_hex_to_nibble
	ldhl	sp,	#5
	ld	(hl), a
	pop	bc
;kaijugaiden.c:1425: gs.password_buf[gs.password_index] = password_nibble_to_hex((u8)((nibble - 1) & 0x0F));
	ld	a, (#(_gs + 100) + 0)
	add	a, #<((_gs + 83))
	ld	e, a
	ld	a, #0x00
	adc	a, #>((_gs + 83))
	ld	d, a
	ldhl	sp,	#3
	ld	a, (hl)
	dec	a
	and	a, #0x0f
	push	bc
	push	de
	call	_password_nibble_to_hex
	pop	de
;kaijugaiden.c:1426: password_draw();
	ld	(de), a
	call	_password_draw
	pop	bc
00110$:
;kaijugaiden.c:138: return ((_joy_cur & mask) && !(_joy_prev & mask)) ? 1 : 0;
	push	hl
	ld	hl, #__joy_cur
	bit	0, (hl)
	pop	hl
	jr	Z, 00145$
	push	hl
	ld	hl, #__joy_prev
	bit	0, (hl)
	pop	hl
	ld	a, #0x01
	jr	Z, 00146$
00145$:
	xor	a, a
00146$:
;kaijugaiden.c:1428: if (plat_pressed(BTN_A) || plat_pressed(BTN_START)) {
	or	a, a
	jr	NZ, 00111$
;kaijugaiden.c:138: return ((_joy_cur & mask) && !(_joy_prev & mask)) ? 1 : 0;
	push	hl
	ld	hl, #__joy_cur
	bit	3, (hl)
	pop	hl
	jr	Z, 00150$
	push	hl
	ld	hl, #__joy_prev
	bit	3, (hl)
	pop	hl
	ld	a, #0x01
	jr	Z, 00151$
00150$:
	xor	a, a
00151$:
;kaijugaiden.c:1428: if (plat_pressed(BTN_A) || plat_pressed(BTN_START)) {
	or	a, a
	jr	Z, 00112$
00111$:
;kaijugaiden.c:1429: (void)password_decode(gs.password_buf, &gs.cleared_bosses, &gs.cyphers);
	ld	de, #(_gs + 108)
	push	de
	ld	bc, #(_gs + 104)
	ld	de, #(_gs + 83)
	call	_password_decode
;kaijugaiden.c:1430: return 1;
	ld	bc, #0x0001
	jr	00123$
00112$:
;kaijugaiden.c:138: return ((_joy_cur & mask) && !(_joy_prev & mask)) ? 1 : 0;
	push	hl
	ld	hl, #__joy_cur
	bit	1, (hl)
	pop	hl
	jr	Z, 00155$
	push	hl
	ld	hl, #__joy_prev
	bit	1, (hl)
	pop	hl
	ld	a, #0x01
	jr	Z, 00156$
00155$:
	xor	a, a
00156$:
;kaijugaiden.c:1432: if (plat_pressed(BTN_B)) return 2;
	or	a, a
	jr	Z, 00115$
	ld	bc, #0x0002
	jr	00123$
00115$:
;kaijugaiden.c:1433: return 0;
	ld	bc, #0x0000
00123$:
;kaijugaiden.c:1434: }
	add	sp, #4
	ret
;kaijugaiden.c:1443: static void stage_intro_init(void) {
;	---------------------------------
; Function stage_intro_init
; ---------------------------------
_stage_intro_init:
;kaijugaiden.c:1444: camera_reset();
	call	_camera_reset
;kaijugaiden.c:1445: gs.phase_timer = 0;
	ld	hl, #(_gs + 77)
	xor	a, a
	ld	(hl+), a
	ld	(hl), a
;kaijugaiden.c:1446: bg_draw_beach();
	call	_bg_draw_beach
;kaijugaiden.c:1447: spr_hide_all();
	call	_spr_hide_all
;kaijugaiden.c:1448: bg_draw_text(8, 6, "DUEL");
	ld	de, #___str_37
	push	de
	ld	e, #0x06
	ld	a, #0x08
	call	_bg_draw_text
;kaijugaiden.c:146: set_bkg_tile_xy(x, y, tile);
	ld	a, #0x23
	push	af
	inc	sp
	ld	e, #0x08
	ld	a, #0x09
	call	_set_bkg_tile_xy
	xor	a, a
	push	af
	inc	sp
	ld	e, #0x08
	ld	a, #0x0a
	call	_set_bkg_tile_xy
;kaijugaiden.c:1450: plat_set_bkg_tile(10, 8, TILE_BLANK);
;kaijugaiden.c:1451: }
	ret
___str_37:
	.ascii "DUEL"
	.db 0x00
;kaijugaiden.c:1454: static int stage_intro_update(void) {
;	---------------------------------
; Function stage_intro_update
; ---------------------------------
_stage_intro_update:
;kaijugaiden.c:1455: gs.phase_timer++;
	ld	hl, #(_gs + 77)
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	inc	bc
	ld	hl, #(_gs + 77)
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;kaijugaiden.c:1456: u8 beat = (u8)(gs.phase_timer / INTRO_BEAT_DUR);
	ld	e, c
	ld	d, b
	ld	bc, #0x0028
	call	__divuint
;kaijugaiden.c:1458: if (beat < 3)
	ld	a, c
	sub	a, #0x03
	jr	NC, 00104$
;kaijugaiden.c:1459: plat_set_bkg_tile(9, 8, TILE_FONT_0 + (3 - beat));
	ld	b, c
	ld	a, #0x23
	sub	a, b
;kaijugaiden.c:146: set_bkg_tile_xy(x, y, tile);
	push	bc
	push	af
	inc	sp
	ld	e, #0x08
	ld	a, #0x09
	call	_set_bkg_tile_xy
	pop	bc
;kaijugaiden.c:1459: plat_set_bkg_tile(9, 8, TILE_FONT_0 + (3 - beat));
	jr	00105$
00104$:
;kaijugaiden.c:1460: else if (beat == 3) {
	ld	a, c
	sub	a, #0x03
	jr	NZ, 00105$
;kaijugaiden.c:1461: bg_draw_text(8, 8, "DUEL");
	push	bc
	ld	de, #___str_38
	push	de
	ld	a,#0x08
	ld	e,a
	call	_bg_draw_text
	pop	bc
00105$:
;kaijugaiden.c:1463: if (beat >= 5) return 1;
	ld	a, c
	sub	a, #0x05
	jr	C, 00107$
	ld	bc, #0x0001
	ret
00107$:
;kaijugaiden.c:1464: return 0;
	ld	bc, #0x0000
;kaijugaiden.c:1465: }
	ret
___str_38:
	.ascii "DUEL"
	.db 0x00
;kaijugaiden.c:1472: static void minion_spawn_wave(void) {
;	---------------------------------
; Function minion_spawn_wave
; ---------------------------------
_minion_spawn_wave:
	add	sp, #-7
;kaijugaiden.c:1474: u8 wave_size = (gs.wave + 1 >= BOSS_WAVES_TO_CLEAR) ? 3 : 2;
	ld	hl, #(_gs + 80)
	ld	c, (hl)
	ld	b, #0x00
	inc	bc
	ld	a, c
	sub	a, #0x03
	ld	a, b
	sbc	a, #0x00
	jr	C, 00113$
	ld	a, #0x03
	jr	00114$
00113$:
	ld	a, #0x02
00114$:
	ldhl	sp,	#0
	ld	(hl), a
;kaijugaiden.c:1475: for (u8 i = 0; i < MINION_MAX && spawned < wave_size; ++i) {
	ldhl	sp,	#6
	ld	(hl), #0x00
	ld	c, #0x00
00109$:
	ld	a, c
	sub	a, #0x05
	jp	NC, 00106$
	ldhl	sp,	#6
	ld	a, (hl)
	ldhl	sp,	#0
	sub	a, (hl)
	jp	NC, 00106$
;kaijugaiden.c:1476: if (!gs.minions[i].active) {
	ld	a, c
	add	a, a
	add	a, a
	add	a, a
	add	a, c
	ld	e, a
	ld	d, #0x00
	ld	hl, #(_gs + 31)
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#3
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#2
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	or	a, a
	jp	NZ, 00110$
;kaijugaiden.c:1477: gs.minions[i].active = 1;
;kaijugaiden.c:1478: gs.minions[i].hp     = MINION_HP;
	dec	hl
	ld	a, #0x01
	ld	(de), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0x0004
	add	hl, de
	ld	(hl), #0x02
;kaijugaiden.c:1479: gs.minions[i].y      = (u8)(SCR_H - 32);
	ldhl	sp,	#1
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	inc	hl
	inc	hl
	inc	hl
	ld	(hl), #0x70
;kaijugaiden.c:1480: gs.minions[i].attack_windup = 0;
	ldhl	sp,#1
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0x0006
	add	hl, de
	ld	e, l
	ld	d, h
	xor	a, a
	ld	(de), a
;kaijugaiden.c:1481: gs.minions[i].attack_recover = 0;
	ldhl	sp,#1
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0x0007
	add	hl, de
	ld	e, l
	ld	d, h
	xor	a, a
	ld	(de), a
;kaijugaiden.c:1483: if (i % 2 == 0) {
	ld	a, c
	and	a, #0x01
	ldhl	sp,	#3
;kaijugaiden.c:1484: gs.minions[i].x  = SCR_W - 24;
	ld	(hl-), a
	dec	hl
	ld	a, (hl+)
	ld	e, a
;kaijugaiden.c:1485: gs.minions[i].vx = -1;
	ld	a, (hl-)
	ld	d, a
	inc	de
	push	de
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0x0008
	add	hl, de
	pop	de
	push	hl
	ld	a, l
	ldhl	sp,	#6
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#5
;kaijugaiden.c:1483: if (i % 2 == 0) {
	ld	(hl-), a
	dec	hl
	ld	a, (hl)
	or	a, a
	jr	NZ, 00102$
;kaijugaiden.c:1484: gs.minions[i].x  = SCR_W - 24;
;kaijugaiden.c:1485: gs.minions[i].vx = -1;
	inc	hl
	ld	a, #0x88
	ld	(de), a
	inc	de
	xor	a, a
	ld	(de), a
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	ld	(hl), #0xff
	jr	00103$
00102$:
;kaijugaiden.c:1487: gs.minions[i].x  = 4;
	ld	a, #0x04
	ld	(de), a
	inc	de
	xor	a, a
	ld	(de), a
;kaijugaiden.c:1488: gs.minions[i].vx = +1;
	ldhl	sp,	#4
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	ld	(hl), #0x01
00103$:
;kaijugaiden.c:1490: gs.minions[i].anim = 0;
	ldhl	sp,#1
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0x0005
	add	hl, de
	ld	e, l
	ld	d, h
	xor	a, a
	ld	(de), a
;kaijugaiden.c:1491: spawned++;
	ldhl	sp,	#6
	inc	(hl)
00110$:
;kaijugaiden.c:1475: for (u8 i = 0; i < MINION_MAX && spawned < wave_size; ++i) {
	inc	c
	jp	00109$
00106$:
;kaijugaiden.c:1494: gs.wave++;
	ld	a, (#(_gs + 80) + 0)
	inc	a
	ld	hl, #(_gs + 80)
;kaijugaiden.c:1495: gs.wave_timer = 120; /* next wave in 2s */
	ld	(hl+), a
	ld	(hl), #0x78
;kaijugaiden.c:1496: }
	add	sp, #7
	ret
;kaijugaiden.c:1498: static void minion_update_all(void) {
;	---------------------------------
; Function minion_update_all
; ---------------------------------
_minion_update_all:
	add	sp, #-16
;kaijugaiden.c:1499: for (u8 i = 0; i < MINION_MAX; ++i) {
	ldhl	sp,	#15
	ld	(hl), #0x00
00134$:
	ldhl	sp,	#15
;kaijugaiden.c:1502: if (!gs.minions[i].active) continue;
	ld	a,(hl)
	cp	a,#0x05
	jp	NC,00135$
	ld	c, a
	add	a, a
	add	a, a
	add	a, a
	add	a, c
	ld	e, a
	ld	d, #0x00
	ld	hl, #(_gs + 31)
	add	hl, de
	inc	sp
	inc	sp
	push	hl
	ldhl	sp,	#0
	ld	a, (hl+)
	inc	hl
	ld	(hl-), a
	ld	a, (hl+)
	inc	hl
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	ld	c, a
	or	a, a
	jp	Z, 00131$
;kaijugaiden.c:1503: gs.minions[i].anim++;
	pop	de
	push	de
	ld	hl, #0x0005
	add	hl, de
	ld	c, l
	ld	b, h
	ld	a, (bc)
	inc	a
	ld	(bc), a
;kaijugaiden.c:1504: player_px = (s16)(gs.player_x * TILE_W);
	ld	hl, #_gs + 1
	ld	l, (hl)
	ld	h, #0x00
	add	hl, hl
	add	hl, hl
	add	hl, hl
	ld	a, l
	ld	c, h
	ldhl	sp,	#4
	ld	(hl+), a
	ld	(hl), c
;kaijugaiden.c:1505: delta = player_px - gs.minions[i].x;
	pop	de
	push	de
	ld	l, e
	ld	h, d
	inc	hl
	push	hl
	ld	a, l
	ldhl	sp,	#8
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#7
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	a, (hl-)
	dec	hl
	dec	hl
	ld	d, a
	ld	a, (de)
	ld	c, a
	inc	de
	ld	a, (de)
	ld	b, a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, e
	sub	a, c
	ld	e, a
	ld	a, d
	sbc	a, b
	ld	c, e
;kaijugaiden.c:1506: if (delta < 0) gs.minions[i].vx = -1;
	ldhl	sp,	#13
	ld	(hl), c
	inc	hl
	ld	(hl), a
	pop	de
	push	de
	ld	hl, #0x0008
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#10
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#9
	ld	(hl), a
	ldhl	sp,	#14
	bit	7, (hl)
	jr	Z, 00106$
	ldhl	sp,	#8
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	ld	(hl), #0xff
	jr	00107$
00106$:
;kaijugaiden.c:1507: else if (delta > 0) gs.minions[i].vx = 1;
	ldhl	sp,	#13
	xor	a, a
	sub	a, (hl)
	inc	hl
	ld	a, #0x00
	sbc	a, (hl)
	jr	NC, 00107$
	ldhl	sp,	#8
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	ld	(hl), #0x01
00107$:
;kaijugaiden.c:1509: if (gs.minions[i].attack_recover > 0) {
	pop	de
	push	de
	ld	hl, #0x0007
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#12
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#11
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	ldhl	sp,	#14
;kaijugaiden.c:1510: gs.minions[i].attack_recover--;
	ld	(hl),a
	or	a,a
	jr	Z, 00123$
	dec	a
	ldhl	sp,	#10
	ld	e, (hl)
	inc	hl
	ld	h, (hl)
	ld	l, e
	ld	(hl), a
	jp	00124$
00123$:
;kaijugaiden.c:1511: } else if (gs.minions[i].attack_windup > 0) {
	pop	de
	push	de
	ld	hl, #0x0006
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#14
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#13
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	or	a, a
	jr	Z, 00120$
;kaijugaiden.c:1512: gs.minions[i].attack_windup--;
	inc	hl
	dec	a
	ld	(hl-), a
	dec	hl
	ld	a, (hl+)
	ld	e, a
	ld	a, (hl+)
	ld	d, a
	ld	a, (hl)
	ld	(de), a
;kaijugaiden.c:1513: if (gs.minions[i].attack_windup == 0) {
	ld	a, (hl)
	or	a, a
	jp	NZ, 00124$
;kaijugaiden.c:1514: if (abs_distance_u8(gs.minions[i].x, player_px) <= MINION_ATTACK_RANGE && gs.hit_stun == 0 && gs.dodge_timer == 0) {
	ldhl	sp,#6
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	ldhl	sp,	#13
	ld	(hl+), a
	inc	de
	ld	a, (de)
	ld	(hl), a
	ldhl	sp,	#4
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	ldhl	sp,	#13
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	call	_abs_distance_u8
	cp	a, #0x13
	jr	NC, 00111$
	ld	bc, #_gs + 9
	ld	a, (bc)
	or	a, a
	jr	NZ, 00111$
	ld	a, (#(_gs + 10) + 0)
	or	a, a
	jr	NZ, 00111$
;kaijugaiden.c:1515: if (gs.player_hp > 0) gs.player_hp--;
	ld	hl, #_gs
	ld	a, (hl)
	or	a, a
	jr	Z, 00109$
	dec	a
	ld	(hl), a
00109$:
;kaijugaiden.c:1516: gs.hit_stun = 36;
	ld	a, #0x24
	ld	(bc), a
;kaijugaiden.c:1517: gs.fx_hit_x = (u8)player_px;
	ldhl	sp,	#4
	ld	a, (hl)
	ld	hl, #(_gs + 112)
;kaijugaiden.c:1518: gs.fx_hit_y = (u8)(SCR_H - 28);
	ld	(hl+), a
	ld	(hl), #0x74
;kaijugaiden.c:1519: gs.fx_hit_timer = 8;
	ld	hl, #_gs + 114
	ld	(hl), #0x08
00111$:
;kaijugaiden.c:1521: gs.minions[i].attack_recover = MINION_RECOVER_FRAMES;
	ldhl	sp,	#10
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	ld	(hl), #0x14
	jr	00124$
00120$:
;kaijugaiden.c:1524: if (abs_distance_u8(gs.minions[i].x, player_px) <= MINION_ATTACK_RANGE) {
	ldhl	sp,#6
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	ldhl	sp,	#10
	ld	(hl+), a
	inc	de
	ld	a, (de)
	ld	(hl), a
	ldhl	sp,	#4
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	ldhl	sp,	#10
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	call	_abs_distance_u8
	ldhl	sp,	#14
	ld	(hl), a
	ld	a, #0x12
	ldhl	sp,	#14
	sub	a, (hl)
	jr	C, 00117$
;kaijugaiden.c:1525: gs.minions[i].attack_windup = MINION_WINDUP_FRAMES;
	dec	hl
	ld	a, (hl-)
	ld	l, (hl)
	ld	h, a
	ld	(hl), #0x0e
	jr	00124$
00117$:
;kaijugaiden.c:1527: gs.minions[i].x += gs.minions[i].vx;
	ldhl	sp,#6
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	ldhl	sp,	#13
	ld	(hl+), a
	inc	de
	ld	a, (de)
	ld	(hl), a
	ldhl	sp,#8
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	ldhl	sp,	#4
	ld	(hl+), a
	rlca
	sbc	a, a
	ld	(hl), a
	ldhl	sp,	#13
	ld	a, (hl-)
	dec	hl
	ld	(hl), a
	ldhl	sp,	#14
	ld	a, (hl-)
	dec	hl
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ldhl	sp,	#4
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#15
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#14
	ld	(hl), a
	ldhl	sp,	#6
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ldhl	sp,	#13
	ld	a, (hl+)
	ld	(de), a
	inc	de
	ld	a, (hl)
	ld	(de), a
00124$:
;kaijugaiden.c:1532: if (gs.minions[i].x < 0)         { gs.minions[i].x = 0;            gs.minions[i].vx = +1; }
	ldhl	sp,#6
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	inc	de
	ld	a, (de)
	bit	7,a
	jr	Z, 00126$
	ld	a, (hl-)
	ld	l, (hl)
	ld	h, a
	xor	a, a
	ld	(hl+), a
	ld	(hl), a
	ldhl	sp,	#8
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	ld	(hl), #0x01
00126$:
;kaijugaiden.c:1533: if (gs.minions[i].x > SCR_W - 16){ gs.minions[i].x = SCR_W - 16;   gs.minions[i].vx = -1; }
	ldhl	sp,#6
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	ld	c, a
	inc	de
	ld	a, (de)
	ld	b, a
	ld	e, b
	ld	d, #0x00
	ld	a, #0x90
	cp	a, c
	ld	a, #0x00
	sbc	a, b
	bit	7, e
	jr	Z, 00250$
	bit	7, d
	jr	NZ, 00251$
	cp	a, a
	jr	00251$
00250$:
	bit	7, d
	jr	Z, 00251$
	scf
00251$:
	jr	NC, 00128$
	ldhl	sp,	#6
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	ld	a, #0x90
	ld	(hl+), a
	ld	(hl), #0x00
	ldhl	sp,	#8
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	ld	(hl), #0xff
00128$:
;kaijugaiden.c:1534: if (gs.minions[i].hp == 0) {
	pop	de
	push	de
	ld	hl, #0x0004
	add	hl, de
	ld	c, l
	ld	b, h
	ld	a, (bc)
	or	a, a
	jr	NZ, 00131$
;kaijugaiden.c:1535: gs.minions[i].active = 0;
	ldhl	sp,	#2
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	ld	(hl), #0x00
00131$:
;kaijugaiden.c:1499: for (u8 i = 0; i < MINION_MAX; ++i) {
	ldhl	sp,	#15
	inc	(hl)
	jp	00134$
00135$:
;kaijugaiden.c:1538: }
	add	sp, #16
	ret
;kaijugaiden.c:1541: static void player_attack_minions(u8 radius) {
;	---------------------------------
; Function player_attack_minions
; ---------------------------------
_player_attack_minions:
	add	sp, #-14
	ldhl	sp,	#12
	ld	(hl), a
;kaijugaiden.c:1542: s16 px = (s16)(gs.player_x * TILE_W + 8);
	ld	hl, #_gs + 1
	ld	l, (hl)
	ld	h, #0x00
	add	hl, hl
	add	hl, hl
	add	hl, hl
	ld	bc, #0x8
	add	hl,bc
	ld	c, l
	ld	b, h
	inc	sp
	inc	sp
	push	bc
;kaijugaiden.c:1543: for (u8 i = 0; i < MINION_MAX; ++i) {
	ldhl	sp,	#13
	ld	(hl), #0x00
00117$:
	ldhl	sp,	#13
	ld	a, (hl)
	sub	a, #0x05
	jp	NC, 00118$
;kaijugaiden.c:1544: if (!gs.minions[i].active) continue;
	ld	a, (hl-)
	dec	hl
	ld	c, a
	add	a, a
	add	a, a
	add	a, a
	add	a, c
	ld	(hl), a
	ld	e, (hl)
	ld	d, #0x00
	ld	hl, #(_gs + 31)
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#4
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#3
	ld	(hl-), a
	ld	a, (hl+)
	inc	hl
	ld	(hl-), a
	ld	a, (hl+)
	inc	hl
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	or	a, a
	jp	Z, 00114$
;kaijugaiden.c:1545: s16 target_x = gs.minions[i].x + 8;
	dec	hl
	dec	hl
	dec	hl
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	l, e
	ld	h, d
	inc	hl
	push	hl
	ld	a, l
	ldhl	sp,	#8
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#7
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	ldhl	sp,	#10
	ld	(hl+), a
	inc	de
	ld	a, (de)
	ld	(hl-), a
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	ld	hl, #0x0008
	add	hl, bc
	ld	c, l
	ld	b, h
;kaijugaiden.c:1546: if (attack_hits_target(px, gs.player_facing, target_x, radius, PLAYER_ATTACK_REAR)) {
	ld	a, (#(_gs + 3) + 0)
	ld	h, #0x08
	push	hl
	inc	sp
	ldhl	sp,	#13
	ld	h, (hl)
	push	hl
	inc	sp
	push	bc
	ldhl	sp,	#4
	ld	e, (hl)
	inc	hl
	ld	d, (hl)
	call	_attack_hits_target
	or	a, a
	jp	Z, 00114$
;kaijugaiden.c:1547: gs.minions[i].attack_windup = 0;
	ldhl	sp,#2
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0x0006
	add	hl, de
	ld	c, l
	ld	b, h
	xor	a, a
	ld	(bc), a
;kaijugaiden.c:1548: gs.minions[i].attack_recover = MINION_RECOVER_FRAMES;
	ldhl	sp,#2
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0x0007
	add	hl, de
	ld	(hl), #0x14
;kaijugaiden.c:1549: if (gs.minions[i].hp <= gs.attack_dmg) {
	ldhl	sp,#2
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0x0004
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#10
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#9
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	a, (hl+)
	ld	d, a
	ld	a, (de)
	ld	(hl), a
	ld	a, (#(_gs + 13) + 0)
	ldhl	sp,	#11
	ld	(hl), a
;kaijugaiden.c:1555: gs.fx_nano_y = gs.minions[i].y;
	ldhl	sp,	#2
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	inc	bc
	inc	bc
	inc	bc
;kaijugaiden.c:1549: if (gs.minions[i].hp <= gs.attack_dmg) {
	ldhl	sp,	#11
	ld	a, (hl-)
	sub	a, (hl)
	jr	C, 00110$
;kaijugaiden.c:1550: gs.minions[i].active = 0;
	ldhl	sp,	#4
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	ld	(hl), #0x00
;kaijugaiden.c:1552: if (gs.nanocell_count < NANOCELL_MAX) {
	ld	hl, #_gs + 14
	ld	a, (hl)
	cp	a, #0x09
	jp	NC, 00111$
;kaijugaiden.c:1553: gs.nanocell_count++;
	inc	a
	ld	(hl), a
;kaijugaiden.c:1554: gs.fx_nano_x = (u8)(gs.minions[i].x);
	ldhl	sp,#6
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	ld	hl, #(_gs + 115)
;kaijugaiden.c:1555: gs.fx_nano_y = gs.minions[i].y;
	ld	(hl+), a
	ld	a, (bc)
;kaijugaiden.c:1556: gs.fx_nano_timer = 12;
	ld	(hl+), a
	ld	(hl), #0x0c
	jp	00111$
00110$:
;kaijugaiden.c:1559: gs.minions[i].hp -= gs.attack_dmg;
	ldhl	sp,	#10
	ld	a, (hl+)
	sub	a, (hl)
	ldhl	sp,	#8
	ld	e, (hl)
	inc	hl
	ld	h, (hl)
	ld	l, e
	ld	(hl), a
;kaijugaiden.c:1560: gs.minions[i].x += gs.player_facing ? -6 : 6;
	ldhl	sp,	#6
	ld	a, (hl+)
	inc	hl
	ld	(hl-), a
	ld	a, (hl+)
	inc	hl
	ld	(hl-), a
	dec	hl
	dec	hl
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	ldhl	sp,	#10
	ld	(hl+), a
	inc	de
	ld	a, (de)
	ld	(hl), a
	ld	a, (#(_gs + 3) + 0)
	or	a, a
	jr	Z, 00120$
	ld	de, #0xfffa
	jr	00121$
00120$:
	ld	de, #0x0006
00121$:
	ldhl	sp,	#10
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	ld	e, l
	ld	a, h
	ldhl	sp,	#10
	ld	(hl), e
	inc	hl
	ld	(hl), a
	ldhl	sp,	#8
	ld	a, (hl+)
	ld	e, a
	ld	a, (hl+)
	ld	d, a
	ld	a, (hl+)
	ld	(de), a
	inc	de
	ld	a, (hl)
	ld	(de), a
;kaijugaiden.c:1561: if (gs.minions[i].x < 0) gs.minions[i].x = 0;
	ldhl	sp,#6
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	inc	de
	ld	a, (de)
	bit	7,a
	jr	Z, 00106$
	ldhl	sp,	#6
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	xor	a, a
	ld	(hl+), a
	ld	(hl), a
00106$:
;kaijugaiden.c:1562: if (gs.minions[i].x > SCR_W - 16) gs.minions[i].x = SCR_W - 16;
	ldhl	sp,#6
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	ld	l, a
	inc	de
	ld	a, (de)
	ld	h, a
	ld	e, h
	ld	d, #0x00
	ld	a, #0x90
	cp	a, l
	ld	a, #0x00
	sbc	a, h
	bit	7, e
	jr	Z, 00186$
	bit	7, d
	jr	NZ, 00187$
	cp	a, a
	jr	00187$
00186$:
	bit	7, d
	jr	Z, 00187$
	scf
00187$:
	jr	NC, 00111$
	ldhl	sp,	#6
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	ld	a, #0x90
	ld	(hl+), a
	ld	(hl), #0x00
00111$:
;kaijugaiden.c:1564: gs.fx_hit_x = (u8)gs.minions[i].x;
	ldhl	sp,#6
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	ld	hl, #(_gs + 112)
;kaijugaiden.c:1565: gs.fx_hit_y = gs.minions[i].y;
	ld	(hl+), a
	ld	a, (bc)
;kaijugaiden.c:1566: gs.fx_hit_timer = 8;
	ld	(hl+), a
	ld	(hl), #0x08
;kaijugaiden.c:1567: camera_punch(1, 4);
	ld	e, #0x04
	ld	a, #0x01
	call	_camera_punch
00114$:
;kaijugaiden.c:1543: for (u8 i = 0; i < MINION_MAX; ++i) {
	ldhl	sp,	#13
	inc	(hl)
	jp	00117$
00118$:
;kaijugaiden.c:1570: }
	add	sp, #14
	ret
;kaijugaiden.c:1599: static void boss_init(void) {
;	---------------------------------
; Function boss_init
; ---------------------------------
_boss_init:
;kaijugaiden.c:1600: gs.boss_awake     = 0;
	ld	hl, #_gs + 20
	ld	(hl), #0x00
;kaijugaiden.c:1601: gs.boss_phase     = 1;
	ld	hl, #_gs + 21
	ld	(hl), #0x01
;kaijugaiden.c:1602: gs.boss_hp        = BOSS_HP_P1;
	ld	hl, #_gs + 22
	ld	(hl), #0x0c
;kaijugaiden.c:1603: gs.boss_x         = SCR_W - 40;
	ld	hl, #(_gs + 23)
	ld	(hl), #0x78
	inc	hl
	ld	(hl), #0x00
;kaijugaiden.c:1604: gs.boss_atk_timer = BOSS_ATK_INTERVAL_P1;
	inc	hl
	inc	hl
	ld	(hl), #0x5a
;kaijugaiden.c:1605: gs.boss_atk_type  = BOSS_ATK_SWEEP;
	ld	hl, #_gs + 27
	ld	(hl), #0x00
;kaijugaiden.c:1606: gs.boss_windup    = 0;
	ld	hl, #_gs + 28
	ld	(hl), #0x00
;kaijugaiden.c:1607: gs.boss_recover   = 0;
	ld	hl, #_gs + 29
	ld	(hl), #0x00
;kaijugaiden.c:1608: gs.boss_stun      = 0;
	ld	hl, #_gs + 30
	ld	(hl), #0x00
;kaijugaiden.c:1609: }
	ret
;kaijugaiden.c:1612: static int boss_take_damage(u8 dmg) {
;	---------------------------------
; Function boss_take_damage
; ---------------------------------
_boss_take_damage:
	dec	sp
	dec	sp
	ldhl	sp,	#1
	ld	(hl), a
;kaijugaiden.c:1613: if (!gs.boss_awake) return 0;
	ld	a, (#(_gs + 20) + 0)
	or	a, a
	jr	NZ, 00102$
	ld	bc, #0x0000
	jp	00116$
00102$:
;kaijugaiden.c:1614: if (gs.boss_stun == 0 && gs.boss_hp > 0) {
	ld	bc, #_gs + 30
	ld	a, (bc)
	or	a, a
	jp	NZ, 00112$
	ld	a, (#(_gs + 22) + 0)
	ldhl	sp,#0
	ld	(hl), a
	or	a, a
	jp	Z, 00112$
;kaijugaiden.c:1621: gs.boss_windup = 0;
;kaijugaiden.c:1622: gs.boss_recover = 30;
;kaijugaiden.c:1615: if (gs.boss_hp <= dmg) {
	inc	hl
	ld	a, (hl-)
	sub	a, (hl)
	jr	C, 00109$
;kaijugaiden.c:1616: gs.boss_hp = 0;
	ld	hl, #(_gs + 22)
	ld	(hl), #0x00
;kaijugaiden.c:1618: if (gs.boss_phase < 3) {
	ld	a, (#(_gs + 21) + 0)
	cp	a, #0x03
	jr	NC, 00104$
;kaijugaiden.c:1619: gs.boss_phase++;
	dec	hl
	inc	a
	ld	(hl), a
;kaijugaiden.c:1620: gs.boss_hp = (gs.boss_phase == 2) ? BOSS_HP_P2 : BOSS_HP_P3;
	sub	a, #0x02
	ld	a, #0x0a
	jr	Z, 00119$
	ld	a, #0x08
00119$:
	ld	(#(_gs + 22)),a
;kaijugaiden.c:1621: gs.boss_windup = 0;
	ld	hl, #(_gs + 28)
;kaijugaiden.c:1622: gs.boss_recover = 30;
	xor	a, a
	ld	(hl+), a
	ld	(hl), #0x1e
;kaijugaiden.c:1623: gs.boss_stun = 60;      /* brief stun at phase change */
	ld	a, #0x3c
	ld	(bc), a
;kaijugaiden.c:1624: combat_set_banner(BANNER_BOSS_STUN, 50);
	ld	e, #0x32
	ld	a, #0x06
	call	_combat_set_banner
;kaijugaiden.c:1625: camera_punch(3, 10);
	ld	e, #0x0a
	ld	a, #0x03
	call	_camera_punch
;kaijugaiden.c:1626: gs.boss_atk_timer = (gs.boss_phase == 2) ? BOSS_ATK_INTERVAL_P2
	ld	bc, #_gs + 26
	ld	a, (#(_gs + 21) + 0)
	sub	a, #0x02
;kaijugaiden.c:1627: : BOSS_ATK_INTERVAL_P3;
	ld	a, #0x46
	jr	Z, 00121$
	ld	a, #0x37
00121$:
	ld	(bc), a
;kaijugaiden.c:1629: bg_fill(TILE_GROUND_R);
	ld	a, #0x02
	call	_bg_fill
;kaijugaiden.c:142: static inline void plat_vsync(void)  { wait_vbl_done(); }
	call	_wait_vbl_done
	call	_wait_vbl_done
;kaijugaiden.c:1632: bg_draw_beach();
	call	_bg_draw_beach
;kaijugaiden.c:1633: return 0;
	ld	bc, #0x0000
	jr	00116$
00104$:
;kaijugaiden.c:1635: return 1; /* boss fully defeated */
	ld	bc, #0x0001
	jr	00116$
00109$:
;kaijugaiden.c:1638: gs.boss_hp -= dmg;
	ldhl	sp,	#0
	ld	a, (hl+)
	sub	a, (hl)
	ld	(#(_gs + 22)),a
;kaijugaiden.c:1639: if (gs.boss_windup > 0) {
	ld	a, (#(_gs + 28) + 0)
	or	a, a
	jr	Z, 00107$
;kaijugaiden.c:1640: gs.boss_windup = 0;
	ld	hl, #(_gs + 28)
;kaijugaiden.c:1641: gs.boss_recover = 18;
	xor	a, a
	ld	(hl+), a
	ld	(hl), #0x12
00107$:
;kaijugaiden.c:1643: gs.boss_stun = 20;
	ld	a, #0x14
	ld	(bc), a
;kaijugaiden.c:1644: combat_set_banner(BANNER_BOSS_STUN, 20);
	ld	e, #0x14
	ld	a, #0x06
	call	_combat_set_banner
;kaijugaiden.c:1645: camera_punch(2, 6);
	ld	e, #0x06
	ld	a, #0x02
	call	_camera_punch
;kaijugaiden.c:1646: return 0;
	ld	bc, #0x0000
	jr	00116$
00112$:
;kaijugaiden.c:1649: return 0;
	ld	bc, #0x0000
00116$:
;kaijugaiden.c:1650: }
	inc	sp
	inc	sp
	ret
;kaijugaiden.c:1653: static void boss_update(void) {
;	---------------------------------
; Function boss_update
; ---------------------------------
_boss_update:
	add	sp, #-10
;kaijugaiden.c:1654: if (gs.boss_phase == 0 || !gs.boss_awake) return;
	ld	a, (#(_gs + 21) + 0)
	or	a, a
	jp	Z, 00155$
	ld	a, (#(_gs + 20) + 0)
	or	a, a
	jp	Z, 00155$
;kaijugaiden.c:1657: if (gs.boss_stun > 0) { gs.boss_stun--; return; }
	ld	hl, #_gs + 30
	ld	a, (hl)
	or	a, a
	jr	Z, 00105$
	dec	a
	ld	(hl), a
	jp	00155$
00105$:
;kaijugaiden.c:1659: if (gs.boss_recover > 0) {
	ld	a, (#(_gs + 29) + 0)
	or	a, a
	jr	Z, 00107$
;kaijugaiden.c:1660: gs.boss_recover--;
	dec	a
	ld	(#(_gs + 29)),a
;kaijugaiden.c:1661: return;
	jp	00155$
00107$:
;kaijugaiden.c:1664: if (gs.boss_windup > 0) {
	ld	hl, #(_gs + 28)
	ld	c, (hl)
;kaijugaiden.c:1665: u8 resolved_type = gs.boss_atk_type;
;kaijugaiden.c:1670: s16 px_now = (s16)(gs.player_x * TILE_W);
;kaijugaiden.c:1671: s16 dist_now = gs.boss_x - px_now;
;kaijugaiden.c:1721: gs.boss_atk_timer = (gs.boss_phase == 1) ? BOSS_ATK_INTERVAL_P1
;kaijugaiden.c:1664: if (gs.boss_windup > 0) {
	ld	a, c
	or	a, a
	jp	Z, 00148$
;kaijugaiden.c:1665: u8 resolved_type = gs.boss_atk_type;
	ld	a, (#(_gs + 27) + 0)
	ldhl	sp,	#0
	ld	(hl), a
;kaijugaiden.c:1666: gs.boss_windup--;
	ld	a, c
	dec	a
	ld	(#(_gs + 28)),a
;kaijugaiden.c:1667: if (gs.boss_windup > 0) return;
	or	a, a
	jp	NZ, 00155$
;kaijugaiden.c:1670: s16 px_now = (s16)(gs.player_x * TILE_W);
	ld	a, (#(_gs + 1) + 0)
	ldhl	sp,#1
	ld	(hl), a
	ld	a, (hl+)
	ld	c, a
	ld	b, #0x00
	sla	c
	rl	b
	sla	c
	rl	b
	sla	c
	rl	b
	ld	a, c
	ld	(hl+), a
;kaijugaiden.c:1671: s16 dist_now = gs.boss_x - px_now;
	ld	a, b
	ld	(hl+), a
	ld	de, #(_gs + 23)
	ld	a, (de)
	ld	(hl+), a
	inc	de
	ld	a, (de)
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ldhl	sp,	#2
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	ld	a, e
	sub	a, l
	ld	e, a
	ld	a, d
	sbc	a, h
	ldhl	sp,	#9
	ld	(hl-), a
	ld	(hl), e
;kaijugaiden.c:1672: if (dist_now < 0) dist_now = -dist_now;
	ld	a, (hl+)
	bit	7, (hl)
	jr	Z, 00111$
	ld	de, #0x0000
	ld	a, (hl-)
	ld	l, (hl)
	ld	h, a
	ld	a, e
	sub	a, l
	ld	e, a
	ld	a, d
	sbc	a, h
	ldhl	sp,	#9
	ld	(hl-), a
	ld	(hl), e
00111$:
;kaijugaiden.c:1674: switch (resolved_type) {
	ld	a, #0x03
	ldhl	sp,	#0
	sub	a, (hl)
	jp	C, 00146$
;kaijugaiden.c:1672: if (dist_now < 0) dist_now = -dist_now;
	ldhl	sp,	#8
	ld	a, (hl-)
	dec	hl
	ld	(hl), a
	ldhl	sp,	#9
	ld	a, (hl-)
	dec	hl
	ld	(hl), a
;kaijugaiden.c:1676: if (dist_now < BOSS_SWEEP_RANGE && gs.hit_stun == 0 && gs.dodge_timer == 0) {
;kaijugaiden.c:1677: if (gs.player_hp > 0) gs.player_hp--;
;kaijugaiden.c:1679: gs.fx_hit_x  = (u8)px_now;
	ldhl	sp,	#2
	ld	a, (hl)
	ldhl	sp,	#8
;kaijugaiden.c:1680: gs.fx_hit_y  = (u8)(SCR_H - 32);
;kaijugaiden.c:1681: gs.fx_hit_timer = 8;
;kaijugaiden.c:1687: if (dist_now < BOSS_SPIT_RANGE && gs.hit_stun == 0 && gs.dodge_timer == 0) {
	ld	(hl-), a
	dec	hl
	ld	a, (hl+)
	sub	a, #0x58
	ld	a, (hl)
	sbc	a, #0x00
	ld	d, (hl)
	ld	a, #0x00
	ld	e, a
	bit	7, e
	jr	Z, 00395$
	bit	7, d
	jr	NZ, 00396$
	cp	a, a
	jr	00396$
00395$:
	bit	7, d
	jr	Z, 00396$
	scf
00396$:
	ld	a, #0x00
	rla
	ldhl	sp,	#9
	ld	(hl), a
;kaijugaiden.c:1674: switch (resolved_type) {
	ldhl	sp,	#0
	ld	c, (hl)
	ld	b, #0x00
	ld	hl, #00397$
	add	hl, bc
	add	hl, bc
	ld	c, (hl)
	inc	hl
	ld	h, (hl)
	ld	l, c
	jp	(hl)
00397$:
	.dw	00112$
	.dw	00119$
	.dw	00126$
	.dw	00131$
;kaijugaiden.c:1675: case BOSS_ATK_SWEEP:
00112$:
;kaijugaiden.c:1676: if (dist_now < BOSS_SWEEP_RANGE && gs.hit_stun == 0 && gs.dodge_timer == 0) {
	ldhl	sp,	#6
	ld	a, (hl+)
	sub	a, #0x20
	ld	a, (hl)
	sbc	a, #0x00
	ld	d, (hl)
	ld	a, #0x00
	ld	e, a
	bit	7, e
	jr	Z, 00398$
	bit	7, d
	jr	NZ, 00399$
	cp	a, a
	jr	00399$
00398$:
	bit	7, d
	jr	Z, 00399$
	scf
00399$:
	jp	NC, 00146$
	ld	a, (#(_gs + 9) + 0)
	or	a, a
	jp	NZ, 00146$
	ld	a, (#(_gs + 10) + 0)
	or	a, a
	jp	NZ, 00146$
;kaijugaiden.c:1677: if (gs.player_hp > 0) gs.player_hp--;
	ld	a, (#_gs + 0)
	or	a, a
	jr	Z, 00114$
	dec	a
	ld	(#_gs),a
00114$:
;kaijugaiden.c:1678: gs.hit_stun = 30;
	ld	hl, #(_gs + 9)
	ld	(hl), #0x1e
;kaijugaiden.c:1679: gs.fx_hit_x  = (u8)px_now;
	ld	de, #(_gs + 112)
	ldhl	sp,	#8
	ld	a, (hl)
	ld	(de), a
;kaijugaiden.c:1680: gs.fx_hit_y  = (u8)(SCR_H - 32);
	ld	hl, #(_gs + 113)
;kaijugaiden.c:1681: gs.fx_hit_timer = 8;
	ld	a, #0x70
	ld	(hl+), a
	ld	(hl), #0x08
;kaijugaiden.c:1682: camera_punch(2, 6);
	ld	e, #0x06
	ld	a, #0x02
	call	_camera_punch
;kaijugaiden.c:1684: break;
	jp	00146$
;kaijugaiden.c:1686: case BOSS_ATK_SPIT:
00119$:
;kaijugaiden.c:1687: if (dist_now < BOSS_SPIT_RANGE && gs.hit_stun == 0 && gs.dodge_timer == 0) {
	ldhl	sp,	#9
	ld	a, (hl)
	or	a, a
	jp	Z, 00146$
	ld	a, (#(_gs + 9) + 0)
	or	a, a
	jp	NZ, 00146$
	ld	a, (#(_gs + 10) + 0)
	or	a, a
	jp	NZ, 00146$
;kaijugaiden.c:1688: if (gs.player_hp > 0) gs.player_hp--;
	ld	a, (#_gs + 0)
	or	a, a
	jr	Z, 00121$
	dec	a
	ld	(#_gs),a
00121$:
;kaijugaiden.c:1689: gs.hit_stun = 25;
	ld	hl, #(_gs + 9)
	ld	(hl), #0x19
;kaijugaiden.c:1690: gs.fx_hit_x  = (u8)px_now;
	ld	de, #(_gs + 112)
	ldhl	sp,	#8
	ld	a, (hl)
	ld	(de), a
;kaijugaiden.c:1691: gs.fx_hit_y  = (u8)(SCR_H - 40);
	ld	hl, #(_gs + 113)
;kaijugaiden.c:1692: gs.fx_hit_timer = 8;
	ld	a, #0x68
	ld	(hl+), a
	ld	(hl), #0x08
;kaijugaiden.c:1693: camera_punch(2, 5);
	ld	e, #0x05
	ld	a, #0x02
	call	_camera_punch
;kaijugaiden.c:1695: break;
	jp	00146$
;kaijugaiden.c:1697: case BOSS_ATK_SLAM:
00126$:
;kaijugaiden.c:1698: if (dist_now < BOSS_SLAM_RANGE && gs.hit_stun == 0 && gs.dodge_timer == 0) {
	ldhl	sp,	#6
	ld	a, (hl+)
	sub	a, #0x1a
	ld	a, (hl)
	sbc	a, #0x00
	ld	d, (hl)
	ld	a, #0x00
	bit	7,a
	jr	Z, 00400$
	bit	7, d
	jr	NZ, 00401$
	cp	a, a
	jr	00401$
00400$:
	bit	7, d
	jr	Z, 00401$
	scf
00401$:
	jp	NC, 00146$
	ld	a, (#(_gs + 9) + 0)
	or	a, a
	jp	NZ, 00146$
	ld	a, (#(_gs + 10) + 0)
	or	a, a
	jp	NZ, 00146$
;kaijugaiden.c:1699: gs.player_hp = (gs.player_hp >= 2) ? gs.player_hp - 2 : 0;
	ld	a, (#_gs + 0)
	ldhl	sp,#9
	ld	(hl), a
	sub	a, #0x02
	jr	C, 00157$
	ld	a, (hl)
	dec	a
	dec	a
	ldhl	sp,	#6
	ld	(hl+), a
	rlca
	sbc	a, a
	ld	(hl), a
	jr	00158$
00157$:
	xor	a, a
	ldhl	sp,	#6
	ld	(hl+), a
	ld	(hl), a
00158$:
	ldhl	sp,	#6
	ld	a, (hl)
	ld	(#_gs),a
;kaijugaiden.c:1700: gs.hit_stun = 40;
	ld	hl, #(_gs + 9)
	ld	(hl), #0x28
;kaijugaiden.c:1701: gs.fx_hit_x = (u8)px_now;
	ld	de, #(_gs + 112)
	ldhl	sp,	#8
	ld	a, (hl)
	ld	(de), a
;kaijugaiden.c:1702: gs.fx_hit_y = (u8)(SCR_H - 28);
	ld	hl, #(_gs + 113)
	ld	(hl), #0x74
;kaijugaiden.c:1703: gs.fx_hit_timer = 10;
	inc	hl
	ld	(hl), #0x0a
;kaijugaiden.c:1704: camera_punch(3, 8);
	ld	e, #0x08
	ld	a, #0x03
	call	_camera_punch
;kaijugaiden.c:1706: break;
	jr	00146$
;kaijugaiden.c:1708: case BOSS_ATK_TIDAL:
00131$:
;kaijugaiden.c:1709: if (gs.boss_x > px_now && gs.player_x < 18) gs.player_x++;
	ldhl	sp,	#2
	ld	e, l
	ld	d, h
	ldhl	sp,	#4
	ld	a, (de)
	inc	de
	sub	a, (hl)
	inc	hl
	ld	a, (de)
	sbc	a, (hl)
	ld	a, (de)
	ld	d, a
	bit	7, (hl)
	jr	Z, 00402$
	bit	7, d
	jr	NZ, 00403$
	cp	a, a
	jr	00403$
00402$:
	bit	7, d
	jr	Z, 00403$
	scf
00403$:
	ld	a, #0x00
	rla
	ld	c, a
	or	a, a
	jr	Z, 00136$
	ldhl	sp,	#1
	ld	a,(hl)
	cp	a,#0x12
	jr	NC, 00136$
	inc	a
	ld	(#(_gs + 1)),a
	jr	00137$
00136$:
;kaijugaiden.c:1710: else if (gs.boss_x <= px_now && gs.player_x > 0) gs.player_x--;
	bit	0, c
	jr	NZ, 00137$
	ldhl	sp,	#1
	ld	a, (hl)
	or	a, a
	jr	Z, 00137$
	ld	a, (hl)
	dec	a
	ld	(#(_gs + 1)),a
00137$:
;kaijugaiden.c:1711: if (gs.nanocell_boost_timer == 0 && gs.hit_stun == 0 && gs.dodge_timer == 0 && dist_now < BOSS_SPIT_RANGE) {
	ld	a, (#(_gs + 15) + 0)
	or	a, a
	jr	NZ, 00146$
	ld	a, (#(_gs + 9) + 0)
	or	a, a
	jr	NZ, 00146$
	ld	a, (#(_gs + 10) + 0)
	or	a, a
	jr	NZ, 00146$
	ldhl	sp,	#9
	ld	a, (hl)
	or	a, a
	jr	Z, 00146$
;kaijugaiden.c:1712: if (gs.player_hp > 0) gs.player_hp--;
	ld	hl, #_gs
	ld	b, (hl)
	ld	a, b
	or	a, a
	jr	Z, 00140$
	dec	b
	ld	hl, #_gs
	ld	(hl), b
00140$:
;kaijugaiden.c:1713: gs.hit_stun = 18;
	ld	hl, #(_gs + 9)
	ld	(hl), #0x12
;kaijugaiden.c:1714: camera_punch(2, 5);
	ld	e, #0x05
	ld	a, #0x02
	call	_camera_punch
;kaijugaiden.c:1717: }
00146$:
;kaijugaiden.c:1719: gs.boss_recover = boss_attack_recover_frames(resolved_type);
	ldhl	sp,	#0
	ld	a, (hl)
	call	_boss_attack_recover_frames
	ld	(#(_gs + 29)),a
;kaijugaiden.c:1720: gs.boss_atk_type = boss_pick_attack();
	call	_boss_pick_attack
	ld	(#(_gs + 27)),a
;kaijugaiden.c:1721: gs.boss_atk_timer = (gs.boss_phase == 1) ? BOSS_ATK_INTERVAL_P1
	ld	a, (#(_gs + 21) + 0)
	cp	a, #0x01
	jr	NZ, 00159$
	ld	e, #0x5a
	jr	00160$
00159$:
;kaijugaiden.c:1722: : (gs.boss_phase == 2) ? BOSS_ATK_INTERVAL_P2
	sub	a, #0x02
;kaijugaiden.c:1723: : BOSS_ATK_INTERVAL_P3;
	ld	e, #0x46
	jr	Z, 00162$
	ld	e, #0x37
00162$:
00160$:
	ld	a, e
	ld	(#(_gs + 26)),a
;kaijugaiden.c:1724: return;
	jp	00155$
00148$:
;kaijugaiden.c:1728: s16 px = (s16)(gs.player_x * TILE_W);
	ld	hl, #(_gs + 1)
	ld	l, (hl)
	xor	a, a
	ld	h, a
	add	hl, hl
	add	hl, hl
	add	hl, hl
	ld	c, l
	ld	b, h
;kaijugaiden.c:1729: if (gs.boss_x > px + 30) gs.boss_x -= 1;
	ld	de, #(_gs + 23)
	ld	a, (de)
	ldhl	sp,	#8
	ld	(hl+), a
	inc	de
	ld	a, (de)
	ld	(hl), a
	ld	hl, #0x001e
	add	hl, bc
	push	hl
	ld	a, l
	ldhl	sp,	#8
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#7
	ld	(hl), a
	ldhl	sp,	#6
	ld	e, l
	ld	d, h
	ldhl	sp,	#8
	ld	a, (de)
	inc	de
	sub	a, (hl)
	inc	hl
	ld	a, (de)
	sbc	a, (hl)
	ld	a, (de)
	ld	d, a
	bit	7, (hl)
	jr	Z, 00408$
	bit	7, d
	jr	NZ, 00409$
	cp	a, a
	jr	00409$
00408$:
	bit	7, d
	jr	Z, 00409$
	scf
00409$:
	jr	NC, 00150$
	ldhl	sp,#8
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #0x0001
	ld	a, e
	sub	a, l
	ld	e, a
	ld	a, d
	sbc	a, h
	ldhl	sp,	#7
	ld	(hl-), a
	ld	(hl), e
	ld	a, (hl+)
	inc	hl
	ld	(hl-), a
	ld	a, (hl+)
	inc	hl
	ld	(hl-), a
	ld	de, #(_gs + 23)
	ld	a, (hl+)
	ld	(de), a
	inc	de
	ld	a, (hl)
	ld	(de), a
00150$:
	ld	hl, #(_gs + 23)
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
;kaijugaiden.c:1730: if (gs.boss_x < px - 10) gs.boss_x += 1;
	ld	a, c
	add	a, #0xf6
	ld	c, a
	ld	a, b
	adc	a, #0xff
	ld	b, a
	ld	e, b
	ld	d, h
	ld	a, l
	sub	a, c
	ld	a, h
	sbc	a, b
	bit	7, e
	jr	Z, 00410$
	bit	7, d
	jr	NZ, 00411$
	cp	a, a
	jr	00411$
00410$:
	bit	7, d
	jr	Z, 00411$
	scf
00411$:
	jr	NC, 00152$
	inc	hl
	ld	c, l
	ld	b, h
	ld	hl, #(_gs + 23)
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
00152$:
;kaijugaiden.c:1733: if (gs.boss_atk_timer > 0) { gs.boss_atk_timer--; return; }
	ld	a, (#(_gs + 26) + 0)
	or	a, a
	jr	Z, 00154$
	dec	a
	ld	(#(_gs + 26)),a
	jr	00155$
00154$:
;kaijugaiden.c:1735: gs.boss_atk_type = boss_pick_attack();
	call	_boss_pick_attack
	ld	(#(_gs + 27)),a
;kaijugaiden.c:1736: gs.boss_windup = boss_attack_windup_frames(gs.boss_atk_type);
	call	_boss_attack_windup_frames
	ld	(#(_gs + 28)),a
00155$:
;kaijugaiden.c:1737: }
	add	sp, #10
	ret
;kaijugaiden.c:1744: static void combat_init(void) {
;	---------------------------------
; Function combat_init
; ---------------------------------
_combat_init:
;kaijugaiden.c:1745: memset(&gs.minions, 0, sizeof(gs.minions));
	ld	de, #0x002d
	push	de
	ld	de, #0x0000
	push	de
	ld	de, #(_gs + 31)
	push	de
	call	_memset
	add	sp, #6
;kaijugaiden.c:1746: camera_reset();
	call	_camera_reset
;kaijugaiden.c:1747: gs.wave       = 0;
	ld	hl, #_gs + 80
	ld	(hl), #0x00
;kaijugaiden.c:1748: gs.wave_timer = 60;
	ld	hl, #_gs + 81
	ld	(hl), #0x3c
;kaijugaiden.c:1749: gs.player_hp  = PLAYER_MAX_HP;
	ld	hl, #_gs
;kaijugaiden.c:1750: gs.player_x   = 2;
	ld	a, #0x06
	ld	(hl+), a
	ld	(hl), #0x02
;kaijugaiden.c:1751: gs.player_y   = (u8)(SCR_H - 24);
	ld	hl, #_gs + 2
	ld	(hl), #0x78
;kaijugaiden.c:1752: gs.player_facing = 0;
	ld	hl, #_gs + 3
	ld	(hl), #0x00
;kaijugaiden.c:1753: gs.player_anim = 0;
	ld	hl, #_gs + 4
	ld	(hl), #0x00
;kaijugaiden.c:1754: gs.attack_timer  = 0;
	ld	hl, #_gs + 5
	ld	(hl), #0x00
;kaijugaiden.c:1755: gs.attack_queued = 0;
	ld	hl, #_gs + 6
	ld	(hl), #0x00
;kaijugaiden.c:1756: gs.attack_buffer = 0;
	ld	hl, #_gs + 7
	ld	(hl), #0x00
;kaijugaiden.c:1757: gs.dodge_buffer = 0;
	ld	hl, #_gs + 8
	ld	(hl), #0x00
;kaijugaiden.c:1758: gs.hit_stun      = 0;
	ld	hl, #_gs + 9
	ld	(hl), #0x00
;kaijugaiden.c:1759: gs.dodge_timer   = 0;
	ld	hl, #_gs + 10
	ld	(hl), #0x00
;kaijugaiden.c:1760: gs.combo_count   = 0;
	ld	hl, #_gs + 11
	ld	(hl), #0x00
;kaijugaiden.c:1761: gs.combo_timer   = 0;
	ld	hl, #_gs + 12
	ld	(hl), #0x00
;kaijugaiden.c:1762: gs.beat_timer    = 0;
	ld	hl, #(_gs + 16)
	xor	a, a
	ld	(hl+), a
;kaijugaiden.c:1763: gs.perfect_flash_timer = 0;
	ld	(hl+), a
	inc	hl
	ld	(hl), #0x00
;kaijugaiden.c:1764: gs.nanocell_count = 0;
	ld	hl, #_gs + 14
	ld	(hl), #0x00
;kaijugaiden.c:1765: gs.nanocell_boost_timer = 0;
	ld	hl, #_gs + 15
	ld	(hl), #0x00
;kaijugaiden.c:1766: gs.attack_dmg    = 1;
	ld	hl, #_gs + 13
	ld	(hl), #0x01
;kaijugaiden.c:1767: gs.fx_hit_timer  = 0;
	ld	hl, #_gs + 114
	ld	(hl), #0x00
;kaijugaiden.c:1768: gs.fx_nano_timer = 0;
	ld	hl, #_gs + 117
	ld	(hl), #0x00
;kaijugaiden.c:1769: gs.phase_timer   = 0;
	ld	hl, #(_gs + 77)
	xor	a, a
	ld	(hl+), a
	ld	(hl), a
;kaijugaiden.c:1770: gs.banner_kind   = BANNER_NONE;
	ld	hl, #_gs + 120
	ld	(hl), #0x00
;kaijugaiden.c:1771: gs.banner_timer  = 0;
	ld	hl, #_gs + 119
	ld	(hl), #0x00
;kaijugaiden.c:1772: gs.input_held_mask = 0;
	ld	hl, #(_gs + 127)
	xor	a, a
	ld	(hl+), a
;kaijugaiden.c:1773: gs.input_pressed_mask = 0;
	ld	(hl+), a
	xor	a, a
	ld	(hl+), a
;kaijugaiden.c:1774: gs.input_edge_total = 0;
	ld	(hl+), a
	xor	a, a
	ld	(hl+), a
;kaijugaiden.c:1775: gs.input_active_frames = 0;
	ld	(hl+), a
	xor	a, a
	ld	(hl+), a
	ld	(hl), a
;kaijugaiden.c:1776: boss_init();
	call	_boss_init
;kaijugaiden.c:1777: bg_draw_beach();
	call	_bg_draw_beach
;kaijugaiden.c:1778: spr_hide_all();
;kaijugaiden.c:1779: }
	jp	_spr_hide_all
;kaijugaiden.c:1782: static int combat_update(void) {
;	---------------------------------
; Function combat_update
; ---------------------------------
_combat_update:
	add	sp, #-6
;kaijugaiden.c:1786: gs.anim_tick++;
	ld	a, (#(_gs + 118) + 0)
	inc	a
	ld	(#(_gs + 118)),a
;kaijugaiden.c:1787: gs.phase_timer++;
	ld	hl, #(_gs + 77)
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	inc	bc
	ld	hl, #(_gs + 77)
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;kaijugaiden.c:1790: gs.beat_timer++;
	ld	hl, #(_gs + 16)
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	inc	bc
	ld	hl, #(_gs + 16)
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;kaijugaiden.c:1791: if (gs.beat_timer >= (u16)BEAT_PERIOD) gs.beat_timer = 0;
	ld	a, c
	sub	a, #0x20
	ld	a, b
	sbc	a, #0x00
	jr	C, 00102$
	dec	hl
	xor	a, a
	ld	(hl+), a
	ld	(hl), a
00102$:
;kaijugaiden.c:1792: gs.beat_perfect = 0;
	ld	hl, #(_gs + 18)
	ld	(hl), #0x00
;kaijugaiden.c:1790: gs.beat_timer++;
	ld	hl, #(_gs + 16)
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
;kaijugaiden.c:1793: if (gs.beat_timer < 5 || gs.beat_timer >= (u16)(BEAT_PERIOD - 5))
	ld	e, c
	ld	d, b
	ld	a, e
	sub	a, #0x05
	ld	a, d
	sbc	a, #0x00
	jr	C, 00103$
	ld	a, c
	sub	a, #0x1b
	ld	a, b
	sbc	a, #0x00
	jr	C, 00104$
00103$:
;kaijugaiden.c:1794: gs.beat_perfect = 1;
	ld	hl, #(_gs + 18)
	ld	(hl), #0x01
00104$:
;kaijugaiden.c:1797: if (gs.attack_timer > 0)          gs.attack_timer--;
	ld	a, (#(_gs + 5) + 0)
	or	a, a
	jr	Z, 00107$
	dec	a
	ld	(#(_gs + 5)),a
00107$:
;kaijugaiden.c:1798: if (gs.attack_buffer > 0)         gs.attack_buffer--;
	ld	a, (#(_gs + 7) + 0)
	or	a, a
	jr	Z, 00109$
	dec	a
	ld	(#(_gs + 7)),a
00109$:
;kaijugaiden.c:1799: if (gs.dodge_buffer > 0)          gs.dodge_buffer--;
	ld	a, (#(_gs + 8) + 0)
	or	a, a
	jr	Z, 00111$
	dec	a
	ld	(#(_gs + 8)),a
00111$:
;kaijugaiden.c:1800: if (gs.hit_stun > 0)               gs.hit_stun--;
	ld	a, (#(_gs + 9) + 0)
	or	a, a
	jr	Z, 00113$
	dec	a
	ld	(#(_gs + 9)),a
00113$:
;kaijugaiden.c:1801: if (gs.dodge_timer > 0)            gs.dodge_timer--;
	ld	a, (#(_gs + 10) + 0)
	or	a, a
	jr	Z, 00115$
	dec	a
	ld	(#(_gs + 10)),a
00115$:
;kaijugaiden.c:1802: if (gs.combo_timer > 0)            gs.combo_timer--;
	ld	hl, #(_gs + 12)
	ld	c, (hl)
;kaijugaiden.c:1803: else                               gs.combo_count = 0;
;kaijugaiden.c:1802: if (gs.combo_timer > 0)            gs.combo_timer--;
	ld	a, c
	or	a, a
	jr	Z, 00117$
	dec	c
	ld	hl, #(_gs + 12)
	ld	(hl), c
	jr	00118$
00117$:
;kaijugaiden.c:1803: else                               gs.combo_count = 0;
	ld	hl, #(_gs + 11)
	ld	(hl), #0x00
00118$:
;kaijugaiden.c:1804: if (gs.player_anim > 0)            gs.player_anim--;
	ld	a, (#(_gs + 4) + 0)
	or	a, a
	jr	Z, 00120$
	dec	a
	ld	(#(_gs + 4)),a
00120$:
;kaijugaiden.c:1805: if (gs.perfect_flash_timer > 0)    gs.perfect_flash_timer--;
	ld	a, (#(_gs + 19) + 0)
	or	a, a
	jr	Z, 00122$
	dec	a
	ld	(#(_gs + 19)),a
00122$:
;kaijugaiden.c:1806: if (gs.banner_timer > 0)           gs.banner_timer--;
	ld	hl, #_gs + 119
	ld	a, (hl)
	or	a, a
	jr	Z, 00124$
	dec	a
	ld	(hl), a
00124$:
;kaijugaiden.c:1807: if (gs.nanocell_boost_timer > 0) {
	ld	hl, #(_gs + 15)
	ld	c, (hl)
;kaijugaiden.c:1809: gs.attack_dmg = 2;
;kaijugaiden.c:1807: if (gs.nanocell_boost_timer > 0) {
	ld	a, c
	or	a, a
	jr	Z, 00126$
;kaijugaiden.c:1808: gs.nanocell_boost_timer--;
	dec	c
	ld	hl, #(_gs + 15)
;kaijugaiden.c:1809: gs.attack_dmg = 2;
	ld	a, c
	ld	(hl-), a
	dec	hl
	ld	(hl), #0x02
	jr	00127$
00126$:
;kaijugaiden.c:1811: gs.attack_dmg = 1;
	ld	hl, #(_gs + 13)
	ld	(hl), #0x01
00127$:
;kaijugaiden.c:1813: if (gs.fx_hit_timer  > 0) gs.fx_hit_timer--;
	ld	a, (#(_gs + 114) + 0)
	or	a, a
	jr	Z, 00129$
	dec	a
	ld	(#(_gs + 114)),a
00129$:
;kaijugaiden.c:1814: if (gs.fx_nano_timer > 0) gs.fx_nano_timer--;
	ld	hl, #_gs + 117
	ld	a, (hl)
	or	a, a
	jr	Z, 00131$
	dec	a
	ld	(hl), a
00131$:
;kaijugaiden.c:1816: if (gs.input_pressed_mask & BTN_A) gs.attack_buffer = INPUT_BUFFER_FRAMES;
	ld	hl, #(_gs + 129)
	ld	a, (hl+)
	bit	0,a
	jr	Z, 00133$
	ld	hl, #(_gs + 7)
	ld	(hl), #0x05
00133$:
;kaijugaiden.c:1817: if (gs.input_pressed_mask & BTN_B) gs.dodge_buffer = INPUT_BUFFER_FRAMES;
	ld	hl, #(_gs + 129)
	ld	a, (hl+)
	bit	1,a
	jr	Z, 00135$
	ld	hl, #(_gs + 8)
	ld	(hl), #0x05
00135$:
;kaijugaiden.c:1820: if (!gs.boss_awake) {
	ld	hl, #(_gs + 20)
;kaijugaiden.c:1822: else if (gs.wave < BOSS_WAVES_TO_CLEAR) minion_spawn_wave();
;kaijugaiden.c:1826: gs.boss_stun = 30;
;kaijugaiden.c:1820: if (!gs.boss_awake) {
	ld	a, (hl)
	or	a, a
	jr	NZ, 00145$
;kaijugaiden.c:1821: if (gs.wave_timer > 0) gs.wave_timer--;
	ld	bc, #_gs + 81
	ld	a, (bc)
	or	a, a
	jr	Z, 00139$
	dec	a
	ld	(bc), a
	jr	00140$
00139$:
;kaijugaiden.c:1822: else if (gs.wave < BOSS_WAVES_TO_CLEAR) minion_spawn_wave();
	ld	a, (#(_gs + 80) + 0)
	sub	a, #0x03
	jr	NC, 00140$
	call	_minion_spawn_wave
00140$:
;kaijugaiden.c:1823: if (gs.wave >= BOSS_WAVES_TO_CLEAR && combat_minions_alive() == 0) {
	ld	a, (#(_gs + 80) + 0)
	sub	a, #0x03
	jr	C, 00145$
	call	_combat_minions_alive
	or	a, a
	jr	NZ, 00145$
;kaijugaiden.c:1824: gs.boss_awake = 1;
	ld	hl, #(_gs + 20)
	ld	(hl), #0x01
;kaijugaiden.c:1825: combat_set_banner(BANNER_BOSS_RISE, 90);
	ld	e, #0x5a
	ld	a, #0x02
	call	_combat_set_banner
;kaijugaiden.c:1826: gs.boss_stun = 30;
	ld	hl, #(_gs + 30)
;kaijugaiden.c:1827: gs.boss_recover = 20;
	ld	a, #0x1e
	ld	(hl-), a
	ld	(hl), #0x14
;kaijugaiden.c:1828: camera_punch(2, 12);
	ld	e, #0x0c
	ld	a, #0x02
	call	_camera_punch
00145$:
;kaijugaiden.c:1833: u8 moved = 0;
	ld	e, #0x00
;kaijugaiden.c:136: static inline u8 plat_held(u8 mask)  { return (_joy_cur  & mask) ? 1 : 0; }
	push	hl
	ld	hl, #__joy_cur
	bit	5, (hl)
	pop	hl
	ld	l, #0x01
	jr	NZ, 00211$
	ld	l, #0x00
00211$:
;kaijugaiden.c:1834: if (plat_held(BTN_LEFT)  && gs.player_x > 0)   { gs.player_x--;  gs.player_facing = 1; moved = 1; }
	ld	bc, #_gs + 1
	ld	a, l
	or	a, a
	jr	Z, 00147$
	ld	a, (bc)
	or	a, a
	jr	Z, 00147$
	dec	a
	ld	(bc), a
	ld	hl, #(_gs + 3)
	ld	(hl), #0x01
	ld	e, #0x01
00147$:
;kaijugaiden.c:136: static inline u8 plat_held(u8 mask)  { return (_joy_cur  & mask) ? 1 : 0; }
	push	hl
	ld	hl, #__joy_cur
	bit	4, (hl)
	pop	hl
	ld	a, #0x01
	jr	NZ, 00213$
	xor	a, a
00213$:
;kaijugaiden.c:1835: if (plat_held(BTN_RIGHT) && gs.player_x < 17)  { gs.player_x++;  gs.player_facing = 0; moved = 1; }
	or	a, a
	jr	Z, 00150$
	ld	a, (bc)
	cp	a, #0x11
	jr	NC, 00150$
	inc	a
	ld	(bc), a
	ld	hl, #(_gs + 3)
	ld	(hl), #0x00
	ld	e, #0x01
00150$:
;kaijugaiden.c:1836: if (moved) gs.player_anim = 8;
	ld	a, e
	or	a, a
	jr	Z, 00153$
	ld	hl, #(_gs + 4)
	ld	(hl), #0x08
00153$:
;kaijugaiden.c:1839: if (gs.attack_buffer > 0 && gs.attack_timer == 0 && gs.dodge_timer == 0 && gs.hit_stun == 0) {
;kaijugaiden.c:1841: gs.attack_queued = 1;
;kaijugaiden.c:1839: if (gs.attack_buffer > 0 && gs.attack_timer == 0 && gs.dodge_timer == 0 && gs.hit_stun == 0) {
	ld	a, (#(_gs + 7) + 0)
	or	a, a
	jr	Z, 00155$
	ld	a, (#(_gs + 5) + 0)
	or	a, a
	jr	NZ, 00155$
	ld	a, (#(_gs + 10) + 0)
	or	a, a
	jr	NZ, 00155$
	ld	a, (#(_gs + 9) + 0)
	or	a, a
	jr	NZ, 00155$
;kaijugaiden.c:1840: gs.attack_timer = ATTACK_TOTAL_FRAMES;
	ld	hl, #(_gs + 5)
;kaijugaiden.c:1841: gs.attack_queued = 1;
	ld	a, #0x0e
	ld	(hl+), a
;kaijugaiden.c:1842: gs.attack_buffer = 0;
	ld	a, #0x01
	ld	(hl+), a
	ld	(hl), #0x00
00155$:
;kaijugaiden.c:1845: if (gs.attack_queued && gs.attack_timer == ATTACK_ACTIVE_FRAME) {
	ld	a, (#(_gs + 6) + 0)
	or	a, a
	jp	Z, 00173$
	ld	a, (#(_gs + 5) + 0)
	sub	a, #0x08
	jp	NZ, 00173$
;kaijugaiden.c:1846: u8 dmg = gs.attack_dmg;
	ld	a, (#(_gs + 13) + 0)
	ldhl	sp,	#5
	ld	(hl), a
;kaijugaiden.c:1847: u8 finisher = 0;
	ldhl	sp,	#0
	ld	(hl), #0x00
;kaijugaiden.c:1848: gs.attack_queued = 0;
	ld	hl, #(_gs + 6)
	ld	(hl), #0x00
;kaijugaiden.c:1849: if (gs.beat_perfect) {
	ld	a, (#(_gs + 18) + 0)
	or	a, a
	jr	Z, 00162$
;kaijugaiden.c:1850: dmg++;
	ldhl	sp,	#5
	inc	(hl)
;kaijugaiden.c:1851: gs.combo_count++;
	ld	a, (#(_gs + 11) + 0)
	inc	a
	ld	hl, #(_gs + 11)
;kaijugaiden.c:1852: gs.combo_timer = ATTACK_COMBO_WINDOW;
	ld	(hl+), a
	ld	(hl), #0x14
;kaijugaiden.c:1853: gs.perfect_flash_timer = 12;
	ld	hl, #(_gs + 19)
	ld	(hl), #0x0c
;kaijugaiden.c:1854: combat_set_banner(BANNER_PERFECT, 12);
	push	bc
	ld	e, #0x0c
	ld	a, #0x04
	call	_combat_set_banner
	pop	bc
;kaijugaiden.c:1855: if (gs.combo_count >= PLAYER_FINISHER_COMBO) {
	ld	a, (#(_gs + 11) + 0)
	sub	a, #0x03
	jr	C, 00162$
;kaijugaiden.c:1856: finisher = 1;
	ldhl	sp,	#0
	ld	(hl), #0x01
;kaijugaiden.c:1857: dmg += 2;
	ldhl	sp,	#5
	ld	a, (hl)
	add	a, #0x02
	ld	(hl), a
;kaijugaiden.c:1858: combat_set_banner(BANNER_FINISHER, 20);
	push	bc
	ld	e, #0x14
	ld	a, #0x05
	call	_combat_set_banner
;kaijugaiden.c:1859: camera_punch(2, 6);
	ld	e, #0x06
	ld	a, #0x02
	call	_camera_punch
	pop	bc
00162$:
;kaijugaiden.c:1862: player_attack_minions(PLAYER_ATTACK_FRONT);
	push	bc
	ld	a, #0x1c
	call	_player_attack_minions
	pop	bc
;kaijugaiden.c:1863: if (gs.boss_awake) {
	ld	a, (#(_gs + 20) + 0)
	or	a, a
	jp	Z, 00173$
;kaijugaiden.c:1864: s16 px = (s16)(gs.player_x * TILE_W + 8);
	ld	a, (bc)
	ld	h, #0x00
	ld	l, a
	add	hl, hl
	add	hl, hl
	add	hl, hl
	ld	a, l
	add	a, #0x08
	ld	e, a
	ld	a, h
	adc	a, #0x00
	ldhl	sp,	#1
	ld	(hl), e
	inc	hl
	ld	(hl), a
;kaijugaiden.c:1865: s16 target = (s16)(gs.boss_x + 16);
	ld	hl, #(_gs + 23)
	ld	a,	(hl+)
	ld	h, (hl)
	add	a, #0x10
	ld	e, a
	ld	a, h
	adc	a, #0x00
	ldhl	sp,	#3
	ld	(hl), e
	inc	hl
	ld	(hl), a
;kaijugaiden.c:1866: if (attack_hits_target(px, gs.player_facing, target, PLAYER_ATTACK_FRONT + 4, PLAYER_ATTACK_REAR)) {
	ld	a, (#(_gs + 3) + 0)
	push	bc
	ld	h, #0x08
	push	hl
	inc	sp
	ld	h, #0x20
	push	hl
	inc	sp
	ldhl	sp,	#7
	ld	e, (hl)
	inc	hl
	ld	d, (hl)
	push	de
	ldhl	sp,	#7
	ld	e, (hl)
	inc	hl
	ld	d, (hl)
	call	_attack_hits_target
	pop	bc
	or	a, a
	jr	Z, 00173$
;kaijugaiden.c:1867: if (finisher && gs.boss_stun < 24) gs.boss_stun = 24;
	ldhl	sp,	#0
	ld	a, (hl)
	or	a, a
	jr	Z, 00164$
	ld	a, (#(_gs + 30) + 0)
	sub	a, #0x18
	jr	NC, 00164$
	ld	hl, #(_gs + 30)
	ld	(hl), #0x18
00164$:
;kaijugaiden.c:1868: if (boss_take_damage(dmg)) {
	push	bc
	ldhl	sp,	#7
	ld	a, (hl)
	call	_boss_take_damage
	ld	e, c
	ld	d, b
	pop	bc
	ld	a, d
	or	a, e
	jr	Z, 00167$
;kaijugaiden.c:1869: return 2; /* boss defeated */
	ld	bc, #0x0002
	jp	00208$
00167$:
;kaijugaiden.c:1871: gs.fx_hit_x = (u8)(gs.boss_x - 4);
	ld	a, (#(_gs + 23) + 0)
	add	a, #0xfc
	ld	hl, #(_gs + 112)
;kaijugaiden.c:1872: gs.fx_hit_y = (u8)(SCR_H - 40);
	ld	(hl+), a
	ld	(hl), #0x68
;kaijugaiden.c:1873: gs.fx_hit_timer = 10;
	ld	hl, #(_gs + 114)
	ld	(hl), #0x0a
;kaijugaiden.c:1874: camera_punch(finisher ? 3 : 2, finisher ? 8 : 5);
	ldhl	sp,	#0
	ld	a, (hl)
	or	a, a
	ld	e, #0x08
	jr	NZ, 00215$
	ld	e, #0x05
00215$:
	ldhl	sp,	#0
	ld	a, (hl)
	or	a, a
	ld	a, #0x03
	jr	NZ, 00217$
	ld	a, #0x02
00217$:
	push	bc
	call	_camera_punch
	pop	bc
00173$:
;kaijugaiden.c:1880: if ((gs.input_pressed_mask & BTN_SELECT) && gs.nanocell_count > 0) {
	ld	hl, #(_gs + 129)
	ld	a,	(hl+)
	bit	2,a
	jr	Z, 00176$
	ld	hl, #_gs + 14
	ld	a, (hl)
	or	a, a
	jr	Z, 00176$
;kaijugaiden.c:1881: gs.nanocell_count--;
	dec	a
	ld	(hl), a
;kaijugaiden.c:1882: gs.nanocell_boost_timer = NANOCELL_BOOST_DUR;
	ld	hl, #(_gs + 15)
	ld	(hl), #0x5a
;kaijugaiden.c:1884: bg_fill(TILE_SKY_B);
	push	bc
	ld	a, #0x08
	call	_bg_fill
	pop	bc
;kaijugaiden.c:142: static inline void plat_vsync(void)  { wait_vbl_done(); }
	call	_wait_vbl_done
;kaijugaiden.c:1886: bg_draw_beach();
	push	bc
	call	_bg_draw_beach
;kaijugaiden.c:1887: camera_punch(1, 6);
	ld	e, #0x06
	ld	a, #0x01
	call	_camera_punch
	pop	bc
00176$:
;kaijugaiden.c:1891: if (gs.dodge_buffer > 0 && gs.hit_stun == 0 && gs.attack_timer == 0) {
	ld	a, (#(_gs + 8) + 0)
	or	a, a
	jr	Z, 00192$
	ld	a, (#(_gs + 9) + 0)
	or	a, a
	jr	NZ, 00192$
	ld	a, (#(_gs + 5) + 0)
	or	a, a
	jr	NZ, 00192$
;kaijugaiden.c:1892: gs.dodge_timer = DODGE_FRAMES;
	ld	hl, #(_gs + 10)
	ld	(hl), #0x0a
;kaijugaiden.c:1894: if (!gs.player_facing && gs.player_x < 17 - DODGE_STEP) gs.player_x += DODGE_STEP;
	ld	hl, #(_gs + 3)
	ld	l, (hl)
	ld	a, l
	or	a, a
	jr	NZ, 00182$
	ld	a, (bc)
	cp	a, #0x0f
	jr	NC, 00182$
	add	a, #0x02
	ld	(bc), a
	jr	00183$
00182$:
;kaijugaiden.c:1895: else if (!gs.player_facing && gs.player_x < 17) gs.player_x = 17;
	ld	a, l
	or	a, a
	jr	NZ, 00183$
	ld	a, (bc)
	sub	a, #0x11
	jr	NC, 00183$
	ld	a, #0x11
	ld	(bc), a
00183$:
;kaijugaiden.c:1896: if ( gs.player_facing && gs.player_x > DODGE_STEP - 1)  gs.player_x -= DODGE_STEP;
	ld	hl, #(_gs + 3)
	ld	l, (hl)
	ld	a, l
	or	a, a
	jr	Z, 00188$
	ld	a, (bc)
	ld	h, a
	ld	e, h
	ld	a,#0x01
	ld	d,a
	sub	a, h
	bit	7, e
	jr	Z, 00652$
	bit	7, d
	jr	NZ, 00653$
	cp	a, a
	jr	00653$
00652$:
	bit	7, d
	jr	Z, 00653$
	scf
00653$:
	jr	NC, 00188$
	ld	a, h
	dec	a
	dec	a
	ld	(bc), a
	jr	00189$
00188$:
;kaijugaiden.c:1897: else if (gs.player_facing) gs.player_x = 0;
	ld	a, l
	or	a, a
	jr	Z, 00189$
	xor	a, a
	ld	(bc), a
00189$:
;kaijugaiden.c:1898: combat_set_banner(BANNER_DODGE, 10);
	ld	e, #0x0a
	ld	a, #0x03
	call	_combat_set_banner
;kaijugaiden.c:1899: gs.dodge_buffer = 0;
	ld	hl, #(_gs + 8)
	ld	(hl), #0x00
;kaijugaiden.c:1900: camera_punch(1, 4);
	ld	e, #0x04
	ld	a, #0x01
	call	_camera_punch
00192$:
;kaijugaiden.c:1904: minions_before = combat_minions_alive();
	call	_combat_minions_alive
	ldhl	sp,	#5
	ld	(hl), a
;kaijugaiden.c:1905: minion_update_all();
	call	_minion_update_all
;kaijugaiden.c:1906: minions_after = combat_minions_alive();
	call	_combat_minions_alive
	ld	c, a
;kaijugaiden.c:1907: if (!gs.boss_awake && minions_before > 0 && minions_after == 0 && gs.wave < BOSS_WAVES_TO_CLEAR) {
	ld	a, (#(_gs + 20) + 0)
	or	a, a
	jr	NZ, 00196$
	ldhl	sp,	#5
	ld	a, (hl)
	or	a, a
	jr	Z, 00196$
	ld	a, c
	or	a, a
	jr	NZ, 00196$
	ld	a, (#(_gs + 80) + 0)
	sub	a, #0x03
	jr	NC, 00196$
;kaijugaiden.c:1908: combat_set_banner(BANNER_WAVE_CLEAR, 30);
	ld	e, #0x1e
	ld	a, #0x01
	call	_combat_set_banner
00196$:
;kaijugaiden.c:1912: boss_update();
	call	_boss_update
;kaijugaiden.c:1914: camera_redraw = combat_camera_update();
	call	_combat_camera_update
;kaijugaiden.c:1917: if (camera_redraw || (gs.anim_tick % 8) == 0) bg_draw_beach();
	or	a, a
	jr	NZ, 00200$
	ld	a, (#(_gs + 118) + 0)
	and	a, #0x07
	jr	NZ, 00201$
00200$:
	call	_bg_draw_beach
00201$:
;kaijugaiden.c:1920: hud_draw();
	call	_hud_draw
;kaijugaiden.c:1923: spr_hide_all();
	call	_spr_hide_all
;kaijugaiden.c:1924: spr_draw_rei();
	call	_spr_draw_rei
;kaijugaiden.c:1925: spr_draw_boss();
	call	_spr_draw_boss
;kaijugaiden.c:1926: spr_draw_minions();
	call	_spr_draw_minions
;kaijugaiden.c:1927: spr_draw_fx();
	call	_spr_draw_fx
;kaijugaiden.c:1930: if (gs.player_hp == 0) return 1;
	ld	a, (#_gs + 0)
	or	a, a
	jr	NZ, 00204$
	ld	bc, #0x0001
	jr	00208$
00204$:
;kaijugaiden.c:1931: return 0;
	ld	bc, #0x0000
00208$:
;kaijugaiden.c:1932: }
	add	sp, #6
	ret
;kaijugaiden.c:1942: static void cypher_init(void) {
;	---------------------------------
; Function cypher_init
; ---------------------------------
_cypher_init:
	add	sp, #-8
;kaijugaiden.c:1943: camera_reset();
	call	_camera_reset
;kaijugaiden.c:1944: gs.phase_timer = 0;
	ld	hl, #(_gs + 77)
	xor	a, a
	ld	(hl+), a
	ld	(hl), a
;kaijugaiden.c:1945: gs.cleared_bosses |= (1u << 0);
	ld	hl, #(_gs + 104)
	ld	a, (hl+)
	ld	c, a
	ld	a, (hl+)
	inc	hl
	ld	b, a
	ld	a, (hl-)
	ld	l, (hl)
	ld	h, a
	ld	a, c
	or	a, #0x01
	push	hl
	ldhl	sp,	#6
	ld	(hl), a
	ldhl	sp,	#7
	ld	(hl), b
	pop	hl
	push	hl
	ld	a, l
	ldhl	sp,	#8
	ld	(hl), a
	pop	hl
	push	hl
	ld	a, h
	ldhl	sp,	#9
	ld	(hl), a
	pop	hl
	ld	de, #(_gs + 104)
	ldhl	sp,	#4
	ld	a, (hl+)
	ld	(de), a
	inc	de
	ld	a, (hl+)
	ld	(de), a
	inc	de
	ld	a, (hl+)
	ld	(de), a
	inc	de
	ld	a, (hl)
	ld	(de), a
;kaijugaiden.c:1946: gs.cyphers        |= (1u << 0);
	ld	hl, #(_gs + 108)
	ld	a, (hl+)
	ld	c, a
	ld	a, (hl+)
	inc	hl
	ld	b, a
	ld	a, (hl-)
	ld	l, (hl)
	ld	h, a
	ld	a, c
	or	a, #0x01
	push	hl
	ldhl	sp,	#2
	ld	(hl), a
	ldhl	sp,	#3
	ld	(hl), b
	pop	hl
	push	hl
	ld	a, l
	ldhl	sp,	#4
	ld	(hl), a
	pop	hl
	push	hl
	ld	a, h
	ldhl	sp,	#5
	ld	(hl), a
	pop	hl
	ld	de, #(_gs + 108)
	ldhl	sp,	#0
	ld	a, (hl+)
	ld	(de), a
	inc	de
	ld	a, (hl+)
	ld	(de), a
	inc	de
	ld	a, (hl+)
	ld	(de), a
	inc	de
;kaijugaiden.c:1947: password_encode(gs.password_buf, gs.cleared_bosses, gs.cyphers);
	ld	a, (hl+)
	ld	(de), a
	ld	de, #(_gs + 104)
	ld	a, (de)
	ld	(hl+), a
	inc	de
	ld	a, (de)
	ld	(hl+), a
	inc	de
	ld	a, (de)
	ld	(hl+), a
	inc	de
	ld	a, (de)
	ld	(hl), a
	ldhl	sp,	#2
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	push	de
	ldhl	sp,	#2
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	push	de
	ldhl	sp,	#10
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	push	de
	ldhl	sp,	#10
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	push	de
	ld	de, #(_gs + 83)
	call	_password_encode
;kaijugaiden.c:1948: spr_hide_all();
	call	_spr_hide_all
;kaijugaiden.c:1949: bg_fill(TILE_BLANK);
	xor	a, a
	call	_bg_fill
;kaijugaiden.c:1950: bg_draw_text(7, 5, "CYPHER");
	ld	de, #___str_39
	push	de
	ld	e, #0x05
	ld	a, #0x07
	call	_bg_draw_text
;kaijugaiden.c:1951: bg_draw_text(5, 8, "SAVE CODE");
	ld	de, #___str_40
	push	de
	ld	e, #0x08
	ld	a, #0x05
	call	_bg_draw_text
;kaijugaiden.c:1952: bg_draw_text(2, 10, gs.password_buf);
	ld	de, #(_gs + 83)
	push	de
	ld	e, #0x0a
	ld	a, #0x02
	call	_bg_draw_text
;kaijugaiden.c:1953: bg_draw_text(4, 14, "A OR START");
	ld	de, #___str_41
	push	de
	ld	e, #0x0e
	ld	a, #0x04
	call	_bg_draw_text
;kaijugaiden.c:1954: }
	add	sp, #8
	ret
___str_39:
	.ascii "CYPHER"
	.db 0x00
___str_40:
	.ascii "SAVE CODE"
	.db 0x00
___str_41:
	.ascii "A OR START"
	.db 0x00
;kaijugaiden.c:1957: static int cypher_update(void) {
;	---------------------------------
; Function cypher_update
; ---------------------------------
_cypher_update:
;kaijugaiden.c:1958: gs.phase_timer++;
	ld	hl, #(_gs + 77)
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	inc	bc
	ld	hl, #(_gs + 77)
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;kaijugaiden.c:1959: if (gs.phase_timer >= CYPHER_DISPLAY_FRAMES) return 1;
	ld	a, c
	sub	a, #0xb4
	ld	a, b
	sbc	a, #0x00
	jr	C, 00102$
	ld	bc, #0x0001
	ret
00102$:
;kaijugaiden.c:138: return ((_joy_cur & mask) && !(_joy_prev & mask)) ? 1 : 0;
	push	hl
	ld	hl, #__joy_cur
	bit	0, (hl)
	pop	hl
	jr	Z, 00110$
	push	hl
	ld	hl, #__joy_prev
	bit	0, (hl)
	pop	hl
	ld	a, #0x01
	jr	Z, 00111$
00110$:
	xor	a, a
00111$:
;kaijugaiden.c:1960: if (plat_pressed(BTN_A) || plat_pressed(BTN_START)) return 1;
	or	a, a
	jr	NZ, 00103$
;kaijugaiden.c:138: return ((_joy_cur & mask) && !(_joy_prev & mask)) ? 1 : 0;
	push	hl
	ld	hl, #__joy_cur
	bit	3, (hl)
	pop	hl
	jr	Z, 00115$
	push	hl
	ld	hl, #__joy_prev
	bit	3, (hl)
	pop	hl
	ld	a, #0x01
	jr	Z, 00116$
00115$:
	xor	a, a
00116$:
;kaijugaiden.c:1960: if (plat_pressed(BTN_A) || plat_pressed(BTN_START)) return 1;
	or	a, a
	jr	Z, 00104$
00103$:
	ld	bc, #0x0001
	ret
00104$:
;kaijugaiden.c:1961: return 0;
	ld	bc, #0x0000
;kaijugaiden.c:1962: }
	ret
;kaijugaiden.c:1971: static void gameover_init(void) {
;	---------------------------------
; Function gameover_init
; ---------------------------------
_gameover_init:
;kaijugaiden.c:1972: camera_reset();
	call	_camera_reset
;kaijugaiden.c:1973: gs.phase_timer = 0;
	ld	hl, #(_gs + 77)
	xor	a, a
	ld	(hl+), a
	ld	(hl), a
;kaijugaiden.c:1974: spr_hide_all();
	call	_spr_hide_all
;kaijugaiden.c:1975: bg_fill(TILE_BLANK);
	xor	a, a
	call	_bg_fill
;kaijugaiden.c:1976: bg_draw_text(5, 8, "GAME OVER");
	ld	de, #___str_42
	push	de
	ld	e, #0x08
	ld	a, #0x05
	call	_bg_draw_text
;kaijugaiden.c:1977: bg_draw_text(3, 12, "PRESS A OR START");
	ld	de, #___str_43
	push	de
	ld	e, #0x0c
	ld	a, #0x03
	call	_bg_draw_text
;kaijugaiden.c:1978: }
	ret
___str_42:
	.ascii "GAME OVER"
	.db 0x00
___str_43:
	.ascii "PRESS A OR START"
	.db 0x00
;kaijugaiden.c:1981: static int gameover_update(void) {
;	---------------------------------
; Function gameover_update
; ---------------------------------
_gameover_update:
;kaijugaiden.c:1982: gs.phase_timer++;
	ld	hl, #(_gs + 77)
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	inc	bc
	ld	hl, #(_gs + 77)
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;kaijugaiden.c:1983: if (gs.phase_timer >= GAMEOVER_HOLD_FRAMES && plat_pressed(BTN_A)) return 1;
	ld	a, c
	sub	a, #0xb4
	ld	a, b
	sbc	a, #0x00
	jr	C, 00102$
;kaijugaiden.c:138: return ((_joy_cur & mask) && !(_joy_prev & mask)) ? 1 : 0;
	push	hl
	ld	hl, #__joy_cur
	bit	0, (hl)
	pop	hl
	jr	Z, 00111$
	push	hl
	ld	hl, #__joy_prev
	bit	0, (hl)
	pop	hl
	ld	a, #0x01
	jr	Z, 00112$
00111$:
	xor	a, a
00112$:
;kaijugaiden.c:1983: if (gs.phase_timer >= GAMEOVER_HOLD_FRAMES && plat_pressed(BTN_A)) return 1;
	or	a, a
	jr	Z, 00102$
	ld	bc, #0x0001
	ret
00102$:
;kaijugaiden.c:1984: if (gs.phase_timer >= GAMEOVER_HOLD_FRAMES && plat_pressed(BTN_START)) return 1;
	ld	hl, #(_gs + 77)
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	ld	a, c
	sub	a, #0xb4
	ld	a, b
	sbc	a, #0x00
	jr	C, 00105$
;kaijugaiden.c:138: return ((_joy_cur & mask) && !(_joy_prev & mask)) ? 1 : 0;
	push	hl
	ld	hl, #__joy_cur
	bit	3, (hl)
	pop	hl
	jr	Z, 00116$
	push	hl
	ld	hl, #__joy_prev
	bit	3, (hl)
	pop	hl
	ld	a, #0x01
	jr	Z, 00117$
00116$:
	xor	a, a
00117$:
;kaijugaiden.c:1984: if (gs.phase_timer >= GAMEOVER_HOLD_FRAMES && plat_pressed(BTN_START)) return 1;
	or	a, a
	jr	Z, 00105$
	ld	bc, #0x0001
	ret
00105$:
;kaijugaiden.c:1985: return 0;
	ld	bc, #0x0000
;kaijugaiden.c:1986: }
	ret
;kaijugaiden.c:1993: int main(void) {
;	---------------------------------
; Function main
; ---------------------------------
_main::
;kaijugaiden.c:1997: DISPLAY_OFF;
	call	_display_off
;kaijugaiden.c:2000: set_bkg_palette(0, 4, gb_dmg_pal);
	ld	de, #_main_gb_dmg_pal_20000_1026
	push	de
	ld	hl, #0x400
	push	hl
	call	_set_bkg_palette
	add	sp, #4
;kaijugaiden.c:2002: SHOW_BKG;
	ldh	a, (_LCDC_REG + 0)
	or	a, #0x01
	ldh	(_LCDC_REG + 0), a
;kaijugaiden.c:2003: SHOW_SPRITES;
	ldh	a, (_LCDC_REG + 0)
	or	a, #0x02
	ldh	(_LCDC_REG + 0), a
;kaijugaiden.c:2004: DISPLAY_ON;
	ldh	a, (_LCDC_REG + 0)
	or	a, #0x80
	ldh	(_LCDC_REG + 0), a
;kaijugaiden.c:2030: game_load_tiles();
	call	_game_load_tiles
;kaijugaiden.c:2033: memset(&gs, 0, sizeof(gs));
	ld	de, #0x0087
	push	de
	ld	de, #0x0000
	push	de
	ld	de, #_gs
	push	de
	call	_memset
	add	sp, #6
;kaijugaiden.c:2034: gs.phase = PHASE_SPLASH;
	ld	hl, #(_gs + 76)
	ld	(hl), #0x00
;kaijugaiden.c:2035: splash_init();
	call	_splash_init
;kaijugaiden.c:2038: while (1) {
00135$:
;kaijugaiden.c:133: _joy_prev = _joy_cur;
	ld	a, (#__joy_cur)
	ld	(#__joy_prev),a
;kaijugaiden.c:134: _joy_cur  = joypad();
	call	_joypad
	ld	(#__joy_cur),a
;kaijugaiden.c:2043: input_capture_frame();
	call	_input_capture_frame
;kaijugaiden.c:2045: switch (gs.phase) {
	ld	hl, #(_gs + 76)
	ld	c, (hl)
	ld	a, #0x08
	sub	a, c
	jp	C, 00133$
	ld	b, #0x00
	ld	hl, #00244$
	add	hl, bc
	add	hl, bc
	ld	c, (hl)
	inc	hl
	ld	h, (hl)
	ld	l, c
	jp	(hl)
00244$:
	.dw	00101$
	.dw	00104$
	.dw	00107$
	.dw	00117$
	.dw	00120$
	.dw	00133$
	.dw	00127$
	.dw	00130$
	.dw	00113$
;kaijugaiden.c:2047: case PHASE_SPLASH:
00101$:
;kaijugaiden.c:2048: if (splash_update()) {
	call	_splash_update
	ld	a, b
	or	a, c
	jp	Z, 00133$
;kaijugaiden.c:2049: gs.phase = PHASE_CINEMATIC;
	ld	hl, #(_gs + 76)
	ld	(hl), #0x01
;kaijugaiden.c:2050: cinematic_init();
	call	_cinematic_init
;kaijugaiden.c:2052: break;
	jp	00133$
;kaijugaiden.c:2054: case PHASE_CINEMATIC:
00104$:
;kaijugaiden.c:2055: if (cinematic_update()) {
	call	_cinematic_update
	ld	a, b
	or	a, c
	jp	Z, 00133$
;kaijugaiden.c:2056: gs.phase = PHASE_TITLE;
	ld	hl, #(_gs + 76)
	ld	(hl), #0x02
;kaijugaiden.c:2057: title_init();
	call	_title_init
;kaijugaiden.c:2059: break;
	jp	00133$
;kaijugaiden.c:2061: case PHASE_TITLE: {
00107$:
;kaijugaiden.c:2062: int sel = title_update();
	call	_title_update
;kaijugaiden.c:2063: if (sel == 1) {
	ld	a, c
	dec	a
	or	a, b
	jr	NZ, 00111$
;kaijugaiden.c:2064: gs.phase = PHASE_STAGE_INTRO;
	ld	hl, #(_gs + 76)
	ld	(hl), #0x03
;kaijugaiden.c:2065: stage_intro_init();
	call	_stage_intro_init
	jp	00133$
00111$:
;kaijugaiden.c:2066: } else if (sel == 2) {
	ld	a, c
	sub	a, #0x02
	or	a, b
	jp	NZ, 00133$
;kaijugaiden.c:2067: gs.phase = PHASE_PASSWORD;
	ld	hl, #(_gs + 76)
	ld	(hl), #0x08
;kaijugaiden.c:2068: password_init();
	call	_password_init
;kaijugaiden.c:2070: break;
	jp	00133$
;kaijugaiden.c:2073: case PHASE_PASSWORD: {
00113$:
;kaijugaiden.c:2074: int result = password_update();
	call	_password_update
;kaijugaiden.c:2075: if (result == 1 || result == 2) {
	ld	a, c
	dec	a
	or	a, b
	jr	Z, 00114$
	ld	a, c
	sub	a, #0x02
	or	a, b
	jr	NZ, 00133$
00114$:
;kaijugaiden.c:2076: gs.phase = PHASE_TITLE;
	ld	hl, #(_gs + 76)
	ld	(hl), #0x02
;kaijugaiden.c:2077: title_init();
	call	_title_init
;kaijugaiden.c:2079: break;
	jr	00133$
;kaijugaiden.c:2082: case PHASE_STAGE_INTRO:
00117$:
;kaijugaiden.c:2083: if (stage_intro_update()) {
	call	_stage_intro_update
	ld	a, b
	or	a, c
	jr	Z, 00133$
;kaijugaiden.c:2084: gs.phase = PHASE_COMBAT;
	ld	hl, #(_gs + 76)
	ld	(hl), #0x04
;kaijugaiden.c:2085: combat_init();
	call	_combat_init
;kaijugaiden.c:2087: break;
	jr	00133$
;kaijugaiden.c:2089: case PHASE_COMBAT: {
00120$:
;kaijugaiden.c:2090: int result = combat_update();
	call	_combat_update
;kaijugaiden.c:2091: if (result == 1) {
	ld	a, c
	dec	a
	or	a, b
	jr	NZ, 00125$
;kaijugaiden.c:2092: gs.phase = PHASE_GAME_OVER;
	ld	hl, #(_gs + 76)
	ld	(hl), #0x07
;kaijugaiden.c:2093: gameover_init();
	call	_gameover_init
	jr	00133$
00125$:
;kaijugaiden.c:2094: } else if (result == 2) {
	ld	a, c
	sub	a, #0x02
	or	a, b
	jr	NZ, 00133$
;kaijugaiden.c:2095: gs.phase = PHASE_BOSS_DEATH;
	ld	hl, #(_gs + 76)
;kaijugaiden.c:2096: gs.phase_timer = 0;
	ld	a, #0x05
	ld	(hl+), a
	xor	a, a
	ld	(hl+), a
	ld	(hl), a
;kaijugaiden.c:2097: bg_fill(TILE_SKY_A);
	ld	a, #0x07
	call	_bg_fill
;kaijugaiden.c:2098: spr_hide_all();
	call	_spr_hide_all
;kaijugaiden.c:2100: for (u8 f = 0; f < 8; ++f) plat_vsync();
	ld	c, #0x00
00141$:
	ld	a, c
	sub	a, #0x08
	jr	NC, 00121$
;kaijugaiden.c:142: static inline void plat_vsync(void)  { wait_vbl_done(); }
	call	_wait_vbl_done
;kaijugaiden.c:2100: for (u8 f = 0; f < 8; ++f) plat_vsync();
	inc	c
	jr	00141$
00121$:
;kaijugaiden.c:2101: gs.phase = PHASE_CYPHER_DROP;
	ld	hl, #(_gs + 76)
	ld	(hl), #0x06
;kaijugaiden.c:2102: cypher_init();
	call	_cypher_init
;kaijugaiden.c:2104: break;
	jr	00133$
;kaijugaiden.c:2107: case PHASE_CYPHER_DROP:
00127$:
;kaijugaiden.c:2108: if (cypher_update()) {
	call	_cypher_update
	ld	a, b
	or	a, c
	jr	Z, 00133$
;kaijugaiden.c:2109: gs.phase = PHASE_TITLE;
	ld	hl, #(_gs + 76)
	ld	(hl), #0x02
;kaijugaiden.c:2110: title_init();
	call	_title_init
;kaijugaiden.c:2112: break;
	jr	00133$
;kaijugaiden.c:2114: case PHASE_GAME_OVER:
00130$:
;kaijugaiden.c:2115: if (gameover_update()) {
	call	_gameover_update
	ld	a, b
	or	a, c
	jr	Z, 00133$
;kaijugaiden.c:2116: gs.phase = PHASE_TITLE;
	ld	hl, #(_gs + 76)
	ld	(hl), #0x02
;kaijugaiden.c:2117: title_init();
	call	_title_init
;kaijugaiden.c:2120: }
00133$:
;kaijugaiden.c:142: static inline void plat_vsync(void)  { wait_vbl_done(); }
	call	_wait_vbl_done
;kaijugaiden.c:2122: plat_vsync();
;kaijugaiden.c:2137: }
	jp	00135$
_main_gb_dmg_pal_20000_1026:
	.dw #0x7fff
	.dw #0x56b5
	.dw #0x294a
	.dw #0x0000
	.area _CODE
	.area _INITIALIZER
__xinit___joy_prev:
	.db #0x00	; 0
__xinit___joy_cur:
	.db #0x00	; 0
	.area _CABS (ABS)
