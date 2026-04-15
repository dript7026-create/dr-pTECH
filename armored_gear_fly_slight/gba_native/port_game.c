#include "port_game.h"

#include <stddef.h>

#define SCREEN_W 240
#define SCREEN_H 160
#define WORLD_W 2048
#define WORLD_H 2048
#define WORLD_CENTER_X (WORLD_W / 2)
#define WORLD_CENTER_Y (WORLD_H / 2)
#define WORLD_RADIUS 900
#define WORLD_SAFE_RADIUS 640
#define FIX_SHIFT 8
#define FIX_ONE (1 << FIX_SHIFT)
#define MOVE_ACCEL 26
#define MOVE_DRAG 4
#define MOVE_MAX_SPEED (4 * FIX_ONE)
#define CAMERA_LAG_SHIFT 2
#define CAMERA_ZOOM_NUM 9
#define CAMERA_ZOOM_DEN 8
#define SPRITE_PROTOCOL_SHAPES 1000u
#define SPRITE_PROTOCOL_SLICES 40u

enum PaletteIndex {
    PAL_VOID = 0,
    PAL_SAFE = 1,
    PAL_MID = 2,
    PAL_RIM = 3,
    PAL_GRID = 4,
    PAL_PLAYER = 5,
    PAL_PROJECTILE = 6,
    PAL_HUD = 7,
    PAL_WARNING = 8,
    PAL_STAR = 9,
    PAL_ENEMY = 10,
    PAL_ENEMY_HIT = 11,
    PAL_PLAYER_MOVE = 12,
    PAL_PLAYER_TORSO = 13,
    PAL_PLAYER_LIMB = 14,
    PAL_PLAYER_VISOR = 15,
    PAL_ENEMY_TORSO = 16,
    PAL_ENEMY_LIMB = 17,
    PAL_ENEMY_EYE = 18,
    PAL_INK = 19,
    PAL_WATER_DEEP = 20,
    PAL_WATER_LIGHT = 21,
    PAL_SOIL_DARK = 22,
    PAL_SOIL_LIGHT = 23,
    PAL_MOSS_DARK = 24,
    PAL_MOSS_LIGHT = 25,
    PAL_RUST_DARK = 26,
    PAL_RUST_LIGHT = 27,
    PAL_MIST = 28,
    PAL_GLOW = 29,
    PAL_SAND = 30,
};

static inline uint16_t rgb15(uint8_t r, uint8_t g, uint8_t b) {
    return (uint16_t)((r & 31u) | ((g & 31u) << 5) | ((b & 31u) << 10));
}

static inline int32_t clamp_i32(int32_t value, int32_t lo, int32_t hi) {
    if (value < lo) {
        return lo;
    }
    if (value > hi) {
        return hi;
    }
    return value;
}

static inline int16_t clamp_v(int32_t value, int32_t lo, int32_t hi) {
    if (value < lo) {
        return (int16_t)lo;
    }
    if (value > hi) {
        return (int16_t)hi;
    }
    return (int16_t)value;
}

static inline uint16_t hash2(uint16_t x, uint16_t y) {
    uint32_t n = (uint32_t)x * 1103515245u + (uint32_t)y * 12345u + 0x9E3779B9u;
    return (uint16_t)((n >> 16) ^ n);
}

static inline void mode4_put2(volatile uint16_t *buffer, uint16_t x, uint16_t y, uint8_t c0, uint8_t c1) {
    uint16_t packed = (uint16_t)c0 | ((uint16_t)c1 << 8);
    buffer[y * (SCREEN_W / 2) + x] = packed;
}

static inline void mode4_put_pixel(volatile uint16_t *buffer, int16_t x, int16_t y, uint8_t color) {
    uint16_t idx;
    uint16_t cell;

    if (x < 0 || x >= SCREEN_W || y < 0 || y >= SCREEN_H) {
        return;
    }

    idx = (uint16_t)x >> 1;
    cell = buffer[y * (SCREEN_W / 2) + idx];

    if ((x & 1) == 0) {
        buffer[y * (SCREEN_W / 2) + idx] = (cell & 0xFF00u) | color;
    } else {
        buffer[y * (SCREEN_W / 2) + idx] = (cell & 0x00FFu) | ((uint16_t)color << 8);
    }
}

static inline void set_palette_pressure(uint8_t pressure) {
    volatile uint16_t *palette = (volatile uint16_t *)0x05000000;
    uint8_t warn = (uint8_t)(pressure / 8u);

    palette[PAL_VOID] = rgb15(1, 1, 2);
    palette[PAL_SAFE] = rgb15(6, 15, 10);
    palette[PAL_MID] = rgb15(11, 14, 12);
    palette[PAL_RIM] = rgb15((uint8_t)(13 + warn), (uint8_t)(6 + (warn / 3u)), 4);
    palette[PAL_GRID] = rgb15(5, 5, 6);
    palette[PAL_PLAYER] = rgb15(26, 30, 28);
    palette[PAL_PROJECTILE] = rgb15(31, 19, 8);
    palette[PAL_HUD] = rgb15(24, 27, 31);
    palette[PAL_WARNING] = rgb15(31, 7, 4);
    palette[PAL_STAR] = rgb15(24, 26, 30);
    palette[PAL_ENEMY] = rgb15(24, 10, 8);
    palette[PAL_ENEMY_HIT] = rgb15(31, 24, 16);
    palette[PAL_PLAYER_MOVE] = rgb15(18, 31, 22);
    palette[PAL_PLAYER_TORSO] = rgb15(16, 19, 24);
    palette[PAL_PLAYER_LIMB] = rgb15(22, 15, 10);
    palette[PAL_PLAYER_VISOR] = rgb15(10, 28, 30);
    palette[PAL_ENEMY_TORSO] = rgb15(19, 8, 10);
    palette[PAL_ENEMY_LIMB] = rgb15(26, 14, 7);
    palette[PAL_ENEMY_EYE] = rgb15(31, 10, 12);
    palette[PAL_INK] = rgb15(0, 0, 0);
    palette[PAL_WATER_DEEP] = rgb15(3, 8, 14);
    palette[PAL_WATER_LIGHT] = rgb15(8, 15, 21);
    palette[PAL_SOIL_DARK] = rgb15(9, 7, 5);
    palette[PAL_SOIL_LIGHT] = rgb15(15, 11, 8);
    palette[PAL_MOSS_DARK] = rgb15(4, 9, 5);
    palette[PAL_MOSS_LIGHT] = rgb15(8, 14, 7);
    palette[PAL_RUST_DARK] = rgb15(14, 6, 4);
    palette[PAL_RUST_LIGHT] = rgb15((uint8_t)(18 + (warn / 4u)), 10, 6);
    palette[PAL_MIST] = rgb15(12, 13, 16);
    palette[PAL_GLOW] = rgb15(26, 21, 11);
    palette[PAL_SAND] = rgb15(19, 15, 10);
}

static inline uint8_t world_color_at(int32_t world_x, int32_t world_y) {
    int32_t dx = world_x - WORLD_CENTER_X;
    int32_t dy = world_y - WORLD_CENTER_Y;
    int32_t dist2 = dx * dx + dy * dy;
    int32_t safe2 = WORLD_SAFE_RADIUS * WORLD_SAFE_RADIUS;
    int32_t rim2 = WORLD_RADIUS * WORLD_RADIUS;
    uint16_t detail = hash2((uint16_t)(world_x >> 1), (uint16_t)(world_y >> 1));
    uint16_t broad = hash2((uint16_t)(world_x >> 4), (uint16_t)(world_y >> 4));
    uint16_t flow = hash2((uint16_t)((world_x + world_y) >> 3), (uint16_t)((world_y - world_x) >> 3));
    uint8_t waterish = (uint8_t)(((broad >> 2) + (flow >> 5)) & 3u);

    if (dist2 > rim2) {
        if ((detail & 0x1Fu) == 0u) {
            return PAL_STAR;
        }
        return (detail & 1u) ? PAL_VOID : PAL_MIST;
    }

    if ((detail & 0x7Fu) == 0u) {
        return PAL_STAR;
    }

    if (dist2 > ((safe2 + rim2) >> 1)) {
        if ((detail & 0x0Fu) == 0u) {
            return PAL_GLOW;
        }
        return (detail & 1u) ? PAL_RUST_LIGHT : PAL_RUST_DARK;
    }

    if (dist2 > safe2) {
        switch ((broad + waterish) & 3u) {
            case 0u: return PAL_SOIL_LIGHT;
            case 1u: return PAL_SOIL_DARK;
            case 2u: return PAL_RUST_LIGHT;
            default: return PAL_RUST_DARK;
        }
    }

    if ((broad & 7u) <= 1u) {
        return (flow & 1u) ? PAL_WATER_LIGHT : PAL_WATER_DEEP;
    }

    switch ((detail + (world_y >> 3)) & 3u) {
        case 0u: return PAL_MOSS_LIGHT;
        case 1u: return PAL_MOSS_DARK;
        case 2u: return PAL_SAND;
        default: return (detail & 1u) ? PAL_SOIL_LIGHT : PAL_SAFE;
    }
}

static inline int16_t project_screen_x(const PortGameState *state, int32_t world_x_fixed) {
    int32_t rel = (world_x_fixed >> FIX_SHIFT) - (state->camera_x >> FIX_SHIFT) - (SCREEN_W / 2);
    return (int16_t)((SCREEN_W / 2) + ((rel * CAMERA_ZOOM_NUM) / CAMERA_ZOOM_DEN));
}

static inline int16_t project_screen_y(const PortGameState *state, int32_t world_y_fixed) {
    int32_t rel = (world_y_fixed >> FIX_SHIFT) - (state->camera_y >> FIX_SHIFT) - (SCREEN_H / 2);
    return (int16_t)((SCREEN_H / 2) + ((rel * CAMERA_ZOOM_NUM) / CAMERA_ZOOM_DEN));
}

static void draw_line(volatile uint16_t *buffer, int16_t x0, int16_t y0, int16_t x1, int16_t y1, uint8_t color);

static void draw_landscape_strokes(volatile uint16_t *buffer, const PortGameState *state) {
    uint8_t i;
    int32_t cam_x = state->camera_x >> FIX_SHIFT;
    int32_t cam_y = state->camera_y >> FIX_SHIFT;

    for (i = 0; i < 16u; ++i) {
        uint16_t seed = hash2((uint16_t)(cam_x + i * 37u), (uint16_t)(cam_y + i * 19u));
        int32_t wx = cam_x + ((int32_t)(seed & 255u) - 8);
        int32_t wy = cam_y + ((int32_t)((seed >> 8) & 191u) - 16);
        int16_t sx = project_screen_x(state, wx << FIX_SHIFT);
        int16_t sy = project_screen_y(state, wy << FIX_SHIFT);
        int8_t len = (int8_t)(3 + ((seed >> 4) & 3u));
        uint8_t c0 = (seed & 1u) ? PAL_SOIL_LIGHT : PAL_MOSS_LIGHT;
        uint8_t c1 = (seed & 2u) ? PAL_RUST_DARK : PAL_WATER_LIGHT;

        draw_line(buffer, sx, sy, (int16_t)(sx + len), (int16_t)(sy + ((seed & 0x20u) ? 1 : -1)), c0);
        mode4_put_pixel(buffer, (int16_t)(sx + len / 2), sy, c1);
    }
}

static void draw_parallax(volatile uint16_t *buffer, const PortGameState *state) {
    uint8_t i;
    for (i = 0; i < 24u; ++i) {
        int32_t wx = (int32_t)((i * 97u + state->frame * 2u) % WORLD_W);
        int32_t wy = (int32_t)((i * 53u + state->frame) % WORLD_H);
        int16_t sx = (int16_t)(wx - ((state->camera_x >> FIX_SHIFT) >> 1));
        int16_t sy = (int16_t)(wy - ((state->camera_y >> FIX_SHIFT) >> 1));

        sx = (int16_t)(sx % SCREEN_W);
        sy = (int16_t)(sy % SCREEN_H);
        if (sx < 0) sx += SCREEN_W;
        if (sy < 0) sy += SCREEN_H;

        mode4_put_pixel(buffer, sx, sy, PAL_STAR);
    }
}

static void draw_actor_dot(volatile uint16_t *buffer, int16_t sx, int16_t sy, uint8_t color, uint8_t radius) {
    int8_t y;
    for (y = -(int8_t)radius; y <= (int8_t)radius; ++y) {
        int8_t x;
        for (x = -(int8_t)radius; x <= (int8_t)radius; ++x) {
            mode4_put_pixel(buffer, (int16_t)(sx + x), (int16_t)(sy + y), color);
        }
    }
}

static void draw_diamond(volatile uint16_t *buffer, int16_t sx, int16_t sy, uint8_t color, uint8_t radius) {
    int8_t y;
    for (y = -(int8_t)radius; y <= (int8_t)radius; ++y) {
        int8_t ay = (y < 0) ? (int8_t)(-y) : y;
        int8_t span = (int8_t)radius - ay;
        int8_t x;
        for (x = -span; x <= span; ++x) {
            mode4_put_pixel(buffer, (int16_t)(sx + x), (int16_t)(sy + y), color);
        }
    }
}

static void draw_box_frame(volatile uint16_t *buffer, int16_t sx, int16_t sy, uint8_t hw, uint8_t hh, uint8_t color) {
    int16_t x;
    int16_t y;
    for (x = (int16_t)(sx - hw); x <= (int16_t)(sx + hw); ++x) {
        mode4_put_pixel(buffer, x, (int16_t)(sy - hh), color);
        mode4_put_pixel(buffer, x, (int16_t)(sy + hh), color);
    }
    for (y = (int16_t)(sy - hh); y <= (int16_t)(sy + hh); ++y) {
        mode4_put_pixel(buffer, (int16_t)(sx - hw), y, color);
        mode4_put_pixel(buffer, (int16_t)(sx + hw), y, color);
    }
}

static void draw_line(volatile uint16_t *buffer, int16_t x0, int16_t y0, int16_t x1, int16_t y1, uint8_t color) {
    int16_t dx = (x1 > x0) ? (int16_t)(x1 - x0) : (int16_t)(x0 - x1);
    int16_t sx = (x0 < x1) ? 1 : -1;
    int16_t dy = (y1 > y0) ? (int16_t)(-(y1 - y0)) : (int16_t)(-(y0 - y1));
    int16_t sy = (y0 < y1) ? 1 : -1;
    int16_t err = (int16_t)(dx + dy);

    for (;;) {
        mode4_put_pixel(buffer, x0, y0, color);
        if (x0 == x1 && y0 == y1) {
            break;
        }

        {
            int16_t e2 = (int16_t)(err << 1);
            if (e2 >= dy) {
                err = (int16_t)(err + dy);
                x0 = (int16_t)(x0 + sx);
            }
            if (e2 <= dx) {
                err = (int16_t)(err + dx);
                y0 = (int16_t)(y0 + sy);
            }
        }
    }
}

/*
 * 1000-shape protocol (temporal): each sprite owns a virtual set of
 * 1000 micro-shapes. We render one slice per frame to maintain speed.
 */
static void draw_protocol_shapes(
    volatile uint16_t *buffer,
    int16_t sx,
    int16_t sy,
    uint8_t base_color,
    uint8_t accent_color,
    uint8_t radius,
    uint16_t phase,
    uint16_t salt
) {
    uint16_t slice = phase % SPRITE_PROTOCOL_SLICES;
    uint16_t per_slice = SPRITE_PROTOCOL_SHAPES / SPRITE_PROTOCOL_SLICES;
    uint16_t start = (uint16_t)(slice * per_slice);
    uint16_t end = (uint16_t)(start + per_slice);
    uint16_t i;
    int16_t rr = (int16_t)(radius * 3 + 2);
    int16_t rr2 = (int16_t)(rr * rr);

    for (i = start; i < end; ++i) {
        uint16_t h = hash2((uint16_t)(salt + i * 13u), (uint16_t)(phase * 7u + i * 5u));
        int16_t ox = (int16_t)((int16_t)(h & 31u) - 15);
        int16_t oy = (int16_t)((int16_t)((h >> 5) & 31u) - 15);
        int16_t px;
        int16_t py;
        uint8_t c;

        ox = (int16_t)((ox * rr) / 8);
        oy = (int16_t)((oy * rr) / 8);
        if ((ox * ox + oy * oy) > rr2) {
            continue;
        }

        px = (int16_t)(sx + ox);
        py = (int16_t)(sy + oy);
        c = ((h >> 10) & 1u) ? base_color : accent_color;

        switch ((h >> 11) & 3u) {
            case 0u:
                mode4_put_pixel(buffer, px, py, c);
                mode4_put_pixel(buffer, (int16_t)(px + 1), py, c);
                break;
            case 1u:
                mode4_put_pixel(buffer, px, py, c);
                mode4_put_pixel(buffer, px, (int16_t)(py + 1), c);
                break;
            case 2u:
                mode4_put_pixel(buffer, (int16_t)(px - 1), py, c);
                mode4_put_pixel(buffer, px, py, c);
                mode4_put_pixel(buffer, (int16_t)(px + 1), py, c);
                break;
            default:
                mode4_put_pixel(buffer, px, (int16_t)(py - 1), c);
                mode4_put_pixel(buffer, px, py, c);
                mode4_put_pixel(buffer, px, (int16_t)(py + 1), c);
                break;
        }
    }
}

static void draw_joint_node(volatile uint16_t *buffer, int16_t x, int16_t y, uint8_t core, uint8_t ring) {
    mode4_put_pixel(buffer, x, y, core);
    mode4_put_pixel(buffer, (int16_t)(x - 1), y, ring);
    mode4_put_pixel(buffer, (int16_t)(x + 1), y, ring);
    mode4_put_pixel(buffer, x, (int16_t)(y - 1), ring);
    mode4_put_pixel(buffer, x, (int16_t)(y + 1), ring);
}

static void draw_limb_chain(
    volatile uint16_t *buffer,
    int16_t x0,
    int16_t y0,
    int16_t x1,
    int16_t y1,
    int16_t x2,
    int16_t y2,
    uint8_t bone_color,
    uint8_t joint_color
) {
    draw_line(buffer, x0, y0, x1, y1, bone_color);
    draw_line(buffer, x1, y1, x2, y2, bone_color);
    draw_joint_node(buffer, x1, y1, bone_color, joint_color);
    draw_joint_node(buffer, x2, y2, bone_color, joint_color);
}

static void draw_protocol_sprite(
    volatile uint16_t *buffer,
    int16_t sx,
    int16_t sy,
    uint8_t base_color,
    uint8_t accent_color,
    uint8_t radius,
    uint16_t phase,
    uint16_t salt,
    int8_t dir_x,
    int8_t dir_y
) {
    int8_t rib;
    int8_t cable_bias = ((salt >> 2) & 1u) ? 1 : -1;

    if (dir_x == 0 && dir_y == 0) {
        dir_x = 1;
    }

    draw_diamond(buffer, sx, sy, base_color, (uint8_t)(radius + 1u));
    draw_box_frame(buffer, sx, sy, (uint8_t)(radius + 2u), radius, accent_color);
    draw_diamond(buffer, (int16_t)(sx + cable_bias * (radius + 1u)), (int16_t)(sy - 1), accent_color, (uint8_t)(radius / 2u + 1u));

    for (rib = (int8_t)(-radius); rib <= (int8_t)radius; rib += 2) {
        mode4_put_pixel(buffer, (int16_t)(sx - cable_bias * (radius + 2u)), (int16_t)(sy + rib), accent_color);
    }

    draw_line(
        buffer,
        sx,
        sy,
        (int16_t)(sx + dir_x * (radius + 5u)),
        (int16_t)(sy + dir_y * (radius + 5u)),
        accent_color
    );

    draw_protocol_shapes(buffer, sx, sy, base_color, accent_color, radius, phase, salt);
}

static void draw_pxgbprog_humanoid(
    volatile uint16_t *buffer,
    int16_t sx,
    int16_t sy,
    uint8_t base_color,
    uint8_t accent_color,
    uint8_t armor_rank,
    uint8_t weapon_rank,
    uint16_t phase,
    uint16_t salt,
    int8_t dir_x,
    int8_t dir_y,
    uint8_t moving,
    uint8_t hostile
) {
    int8_t cable_bias = ((salt >> 1) & 1u) ? 1 : -1;
    int8_t step = moving ? (int8_t)((phase >> 1) & 3u) - 1 : 0;
    int8_t arm_swing = moving ? (int8_t)(-step) : 0;
    int16_t head_x;
    int16_t head_y;
    int16_t torso_x;
    int16_t torso_y;
    int16_t shoulder_left_x;
    int16_t shoulder_left_y;
    int16_t shoulder_right_x;
    int16_t shoulder_right_y;
    int16_t elbow_left_x;
    int16_t elbow_left_y;
    int16_t elbow_right_x;
    int16_t elbow_right_y;
    int16_t hand_left_x;
    int16_t hand_left_y;
    int16_t hand_right_x;
    int16_t hand_right_y;
    int16_t hip_left_x;
    int16_t hip_left_y;
    int16_t hip_right_x;
    int16_t hip_right_y;
    int16_t knee_left_x;
    int16_t knee_left_y;
    int16_t knee_right_x;
    int16_t knee_right_y;
    int16_t foot_left_x;
    int16_t foot_left_y;
    int16_t foot_right_x;
    int16_t foot_right_y;
    uint8_t torso_color;
    uint8_t limb_color;
    uint8_t visor_color;
    uint8_t layer_color;
    int8_t spike;

    if (dir_x == 0 && dir_y == 0) {
        dir_x = hostile ? -1 : 1;
    }

    head_x = (int16_t)(sx + (hostile ? cable_bias : 0));
    head_y = (int16_t)(sy - 8);
    torso_x = sx;
    torso_y = sy;
    shoulder_left_x = (int16_t)(sx - 4);
    shoulder_left_y = (int16_t)(sy - 3);
    shoulder_right_x = (int16_t)(sx + 4);
    shoulder_right_y = (int16_t)(sy - 3);
    elbow_left_x = (int16_t)(sx - 6 - dir_x + cable_bias);
    elbow_left_y = (int16_t)(sy - 1 + arm_swing);
    elbow_right_x = (int16_t)(sx + 6 + dir_x);
    elbow_right_y = (int16_t)(sy - 1 - arm_swing);
    hand_left_x = (int16_t)(sx - 7 - dir_x + cable_bias);
    hand_left_y = (int16_t)(sy + 3 + arm_swing);
    hand_right_x = (int16_t)(sx + 7 + dir_x * (weapon_rank > 4u ? 2 : 1));
    hand_right_y = (int16_t)(sy + 2 - arm_swing);
    hip_left_x = (int16_t)(sx - 2);
    hip_left_y = (int16_t)(sy + 4);
    hip_right_x = (int16_t)(sx + 2);
    hip_right_y = (int16_t)(sy + 4);
    knee_left_x = (int16_t)(sx - 3 - step);
    knee_left_y = (int16_t)(sy + 8);
    knee_right_x = (int16_t)(sx + 3 + step);
    knee_right_y = (int16_t)(sy + 8);
    foot_left_x = (int16_t)(sx - 4 - step);
    foot_left_y = (int16_t)(sy + 12);
    foot_right_x = (int16_t)(sx + 4 + step);
    foot_right_y = (int16_t)(sy + 12);
    torso_color = hostile ? ((accent_color == PAL_ENEMY_HIT) ? PAL_ENEMY_HIT : PAL_ENEMY_TORSO) : (moving ? PAL_PLAYER_MOVE : PAL_PLAYER_TORSO);
    limb_color = hostile ? PAL_ENEMY_LIMB : PAL_PLAYER_LIMB;
    visor_color = hostile ? PAL_ENEMY_EYE : PAL_PLAYER_VISOR;
    layer_color = (armor_rank >= 3u) ? accent_color : (hostile ? PAL_RUST_LIGHT : PAL_HUD);

    /* Head and chest anchors */
    draw_diamond(buffer, head_x, head_y, torso_color, 2u);
    draw_box_frame(buffer, head_x, head_y, 2u, 2u, PAL_INK);
    mode4_put_pixel(buffer, head_x, head_y, visor_color);
    mode4_put_pixel(buffer, (int16_t)(head_x + cable_bias), head_y, visor_color);
    draw_diamond(buffer, torso_x, torso_y, torso_color, 4u);
    draw_box_frame(buffer, torso_x, (int16_t)(torso_y + 1), 5u, 4u, PAL_INK);
    draw_joint_node(buffer, torso_x, torso_y, torso_color, accent_color);
    mode4_put_pixel(buffer, torso_x, (int16_t)(torso_y - 1), PAL_INK);
    mode4_put_pixel(buffer, torso_x, (int16_t)(torso_y + 2), PAL_INK);

    /* Collar wrap / gorget */
    draw_line(buffer, (int16_t)(head_x - 2), (int16_t)(head_y + 2), (int16_t)(torso_x - 1), (int16_t)(torso_y - 3), accent_color);
    draw_line(buffer, (int16_t)(head_x + 2), (int16_t)(head_y + 2), (int16_t)(torso_x + 1), (int16_t)(torso_y - 3), accent_color);

    /* Arms and legs with visible joints */
    draw_limb_chain(buffer, shoulder_left_x, shoulder_left_y, elbow_left_x, elbow_left_y, hand_left_x, hand_left_y, limb_color, accent_color);
    draw_limb_chain(buffer, shoulder_right_x, shoulder_right_y, elbow_right_x, elbow_right_y, hand_right_x, hand_right_y, limb_color, accent_color);
    draw_limb_chain(buffer, hip_left_x, hip_left_y, knee_left_x, knee_left_y, foot_left_x, foot_left_y, limb_color, accent_color);
    draw_limb_chain(buffer, hip_right_x, hip_right_y, knee_right_x, knee_right_y, foot_right_x, foot_right_y, limb_color, accent_color);

    /* Layered armor driven by live PxGBPROG-style ranks */
    if (armor_rank >= 1u) {
        draw_box_frame(buffer, torso_x, torso_y, 4u, 3u, layer_color);
        draw_diamond(buffer, (int16_t)(shoulder_left_x - 1), shoulder_left_y, layer_color, 1u);
        draw_diamond(buffer, (int16_t)(shoulder_right_x + 1), shoulder_right_y, layer_color, 1u);
        draw_line(buffer, (int16_t)(torso_x - 2), (int16_t)(torso_y + 5), (int16_t)(torso_x + 2), (int16_t)(torso_y + 5), layer_color);
        draw_box_frame(buffer, torso_x, torso_y, 3u, 2u, PAL_INK);
    }
    if (armor_rank >= 2u) {
        draw_line(buffer, (int16_t)(torso_x - 3), (int16_t)(torso_y - 1), torso_x, (int16_t)(torso_y + 3), accent_color);
        draw_line(buffer, (int16_t)(torso_x + 3), (int16_t)(torso_y - 1), torso_x, (int16_t)(torso_y + 3), accent_color);
        draw_line(buffer, (int16_t)(shoulder_left_x - 1), shoulder_left_y, elbow_left_x, elbow_left_y, accent_color);
        draw_line(buffer, (int16_t)(shoulder_right_x + 1), shoulder_right_y, elbow_right_x, elbow_right_y, accent_color);
        mode4_put_pixel(buffer, torso_x, (int16_t)(torso_y + 6), accent_color);
        mode4_put_pixel(buffer, (int16_t)(torso_x - 2), (int16_t)(torso_y + 1), PAL_INK);
        mode4_put_pixel(buffer, (int16_t)(torso_x + 2), (int16_t)(torso_y + 1), PAL_INK);
    }
    if (armor_rank >= 3u) {
        for (spike = -3; spike <= 3; spike += 2) {
            mode4_put_pixel(buffer, (int16_t)(torso_x + spike), (int16_t)(torso_y - 5 - ((spike < 0) ? -spike : spike) / 2), accent_color);
            mode4_put_pixel(buffer, (int16_t)(torso_x + spike), (int16_t)(torso_y + 7), accent_color);
        }
        draw_box_frame(buffer, torso_x, (int16_t)(torso_y + 2), 3u, 5u, accent_color);
        draw_line(buffer, (int16_t)(shoulder_left_x - 2), (int16_t)(shoulder_left_y - 1), (int16_t)(shoulder_left_x + 1), (int16_t)(shoulder_left_y + 1), PAL_INK);
        draw_line(buffer, (int16_t)(shoulder_right_x - 1), (int16_t)(shoulder_right_y + 1), (int16_t)(shoulder_right_x + 2), (int16_t)(shoulder_right_y - 1), PAL_INK);
    }

    /* Weapon silhouette set */
    if (weapon_rank <= 3u) {
        draw_line(buffer, hand_right_x, hand_right_y, (int16_t)(hand_right_x + dir_x * 4), (int16_t)(hand_right_y + dir_y * 4), accent_color);
        mode4_put_pixel(buffer, (int16_t)(hand_right_x + dir_x * 4 + cable_bias), (int16_t)(hand_right_y + dir_y * 4 - cable_bias), accent_color);
        mode4_put_pixel(buffer, (int16_t)(hand_right_x + dir_x * 4 - cable_bias), (int16_t)(hand_right_y + dir_y * 4 + cable_bias), accent_color);
    } else if (weapon_rank <= 6u) {
        draw_line(buffer, hand_right_x, hand_right_y, (int16_t)(hand_right_x + dir_x * 5), (int16_t)(hand_right_y + dir_y * 5), accent_color);
        draw_line(buffer, (int16_t)(hand_right_x + dir_x * 4), (int16_t)(hand_right_y + dir_y * 4), (int16_t)(hand_right_x + dir_x * 5 + cable_bias * 2), (int16_t)(hand_right_y + dir_y * 5 - cable_bias * 2), accent_color);
    } else {
        draw_line(buffer, hand_right_x, hand_right_y, (int16_t)(hand_right_x + dir_x * 6), (int16_t)(hand_right_y + dir_y * 6), accent_color);
        draw_line(buffer, (int16_t)(hand_right_x + dir_x * 5), (int16_t)(hand_right_y + dir_y * 5), (int16_t)(hand_right_x + dir_x * 6 + cable_bias * 2), (int16_t)(hand_right_y + dir_y * 6 - cable_bias * 2), accent_color);
        draw_line(buffer, (int16_t)(hand_right_x + dir_x * 5), (int16_t)(hand_right_y + dir_y * 5), (int16_t)(hand_right_x + dir_x * 6 - cable_bias * 2), (int16_t)(hand_right_y + dir_y * 6 + cable_bias * 2), accent_color);
    }

    /* Cable halo and relic tail */
    mode4_put_pixel(buffer, (int16_t)(head_x - 2), (int16_t)(head_y - 2), PAL_HUD);
    mode4_put_pixel(buffer, head_x, (int16_t)(head_y - 3), PAL_HUD);
    mode4_put_pixel(buffer, (int16_t)(head_x + 2), (int16_t)(head_y - 2), PAL_HUD);
    draw_line(buffer, hip_left_x, hip_left_y, (int16_t)(hip_left_x - 3 - cable_bias), (int16_t)(hip_left_y + 4), PAL_GRID);

    /* Micro-detail pass */
    draw_protocol_shapes(buffer, sx, sy, base_color, accent_color, 4u, phase, salt);
}

static void draw_player(const PortGameState *state, volatile uint16_t *buffer) {
    int16_t px = project_screen_x(state, state->player_x);
    int16_t py = project_screen_y(state, state->player_y);
    uint8_t color = state->move_flash ? PAL_PLAYER_MOVE : PAL_PLAYER;
    uint8_t visual_armor = state->armor_rank;

    if (state->pressure > 96u && visual_armor < 2u) {
        visual_armor = 2u;
    }
    if (state->pressure > 180u && visual_armor < 3u) {
        visual_armor = 3u;
    }

    draw_pxgbprog_humanoid(
        buffer,
        px,
        py,
        color,
        PAL_HUD,
        visual_armor,
        state->weapon_rank,
        state->frame,
        (uint16_t)((state->player_x >> FIX_SHIFT) ^ (state->player_y >> FIX_SHIFT)),
        state->aim_x,
        state->aim_y,
        state->move_flash,
        0u
    );
}

static void draw_projectiles(const PortGameState *state, volatile uint16_t *buffer) {
    uint8_t i;
    for (i = 0; i < PORT_MAX_PROJECTILES; ++i) {
        const PortProjectile *p = &state->projectiles[i];
        int16_t sx;
        int16_t sy;
        if (!p->active) {
            continue;
        }

        sx = project_screen_x(state, p->x);
        sy = project_screen_y(state, p->y);
        if (sx < -8 || sx >= (SCREEN_W + 8) || sy < -8 || sy >= (SCREEN_H + 8)) {
            continue;
        }
        draw_protocol_sprite(
            buffer,
            sx,
            sy,
            PAL_PROJECTILE,
            PAL_GLOW,
            2u,
            (uint16_t)(state->frame + (i * 3u)),
            (uint16_t)(p->x ^ p->y),
            clamp_v(p->vx >> 10, -1, 1),
            clamp_v(p->vy >> 10, -1, 1)
        );
    }
}

static void draw_enemies(const PortGameState *state, volatile uint16_t *buffer) {
    uint8_t i;
    for (i = 0; i < PORT_MAX_ENEMIES; ++i) {
        const PortEnemy *e = &state->enemies[i];
        int16_t sx;
        int16_t sy;
        uint8_t color;
        uint8_t enemy_armor;
        if (!e->active) {
            continue;
        }

        sx = project_screen_x(state, e->x);
        sy = project_screen_y(state, e->y);
        if (sx < -20 || sx >= (SCREEN_W + 20) || sy < -20 || sy >= (SCREEN_H + 20)) {
            continue;
        }
        color = (e->cooldown > 0u) ? PAL_ENEMY_HIT : PAL_ENEMY;
        enemy_armor = (uint8_t)(1u + (i % 3u));

        draw_pxgbprog_humanoid(
            buffer,
            sx,
            sy,
            color,
            PAL_WARNING,
            enemy_armor,
            (uint8_t)(2u + (i % 5u)),
            (uint16_t)(state->frame + i),
            (uint16_t)((e->x >> FIX_SHIFT) ^ (e->y >> FIX_SHIFT)),
            clamp_v(e->vx >> 10, -1, 1),
            clamp_v(e->vy >> 10, -1, 1),
            1u,
            1u
        );
    }
}

static void draw_hud(const PortGameState *state, volatile uint16_t *buffer) {
    uint8_t pressure_bars = (uint8_t)(state->pressure / 10u);
    uint8_t weapon_bars = state->weapon_rank;
    uint8_t enemy_count = 0u;
    uint8_t i;

    for (i = 0; i < PORT_MAX_ENEMIES; ++i) {
        if (state->enemies[i].active) {
            ++enemy_count;
        }
    }

    for (i = 0; i < 24u; ++i) {
        uint8_t color = (i <= pressure_bars) ? PAL_WARNING : PAL_HUD;
        mode4_put2(buffer, i, 2, color, color);
        mode4_put2(buffer, i, 3, color, color);
    }

    for (i = 0; i < 12u; ++i) {
        uint8_t color = (i < weapon_bars) ? PAL_PROJECTILE : PAL_GRID;
        mode4_put2(buffer, (uint16_t)(i + 26u), 2, color, color);
    }

    for (i = 0; i < 12u; ++i) {
        uint8_t color = (i < enemy_count) ? PAL_ENEMY : PAL_GRID;
        mode4_put2(buffer, (uint16_t)(i + 26u), 4, color, color);
    }
}

void port_game_init(PortGameState *state) {
    uint8_t i;
    if (!state) {
        return;
    }

    state->player_x = WORLD_CENTER_X << FIX_SHIFT;
    state->player_y = WORLD_CENTER_Y << FIX_SHIFT;
    state->player_vx = 0;
    state->player_vy = 0;
    state->camera_x = state->player_x - ((SCREEN_W / 2) << FIX_SHIFT);
    state->camera_y = state->player_y - ((SCREEN_H / 2) << FIX_SHIFT);
    state->frame = 0;
    state->spawn_timer = 35u;
    state->weapon_rank = 2u;
    state->armor_rank = 1u;
    state->pressure = 0;
    state->dash_cooldown = 0;
    state->fire_cooldown = 0;
    state->exit_requested = 0;
    state->move_flash = 0u;
    state->aim_x = 1;
    state->aim_y = 0;

    for (i = 0; i < PORT_MAX_PROJECTILES; ++i) {
        state->projectiles[i].active = 0;
    }

    for (i = 0; i < PORT_MAX_ENEMIES; ++i) {
        state->enemies[i].active = 0;
    }

    set_palette_pressure(0);
}

static void spawn_projectile(PortGameState *state, int16_t dir_x, int16_t dir_y) {
    uint8_t i;
    for (i = 0; i < PORT_MAX_PROJECTILES; ++i) {
        PortProjectile *p = &state->projectiles[i];
        if (p->active) {
            continue;
        }

        p->active = 1;
        p->x = state->player_x;
        p->y = state->player_y;
        p->vx = (int16_t)(dir_x * (4 * FIX_ONE));
        p->vy = (int16_t)(dir_y * (4 * FIX_ONE));
        p->ttl = 52u;
        break;
    }
}

static void spawn_enemy(PortGameState *state) {
    uint8_t i;
    int16_t base_x = (int16_t)(state->player_x >> FIX_SHIFT);
    int16_t base_y = (int16_t)(state->player_y >> FIX_SHIFT);
    int16_t offset = 100;
    uint16_t selector = hash2((uint16_t)state->frame, (uint16_t)(state->pressure + 7u));

    for (i = 0; i < PORT_MAX_ENEMIES; ++i) {
        PortEnemy *e = &state->enemies[i];
        if (e->active) {
            continue;
        }

        e->active = 1;
        e->hp = 2u;
        e->cooldown = 0u;

        switch (selector & 3u) {
            case 0u: e->x = (base_x - offset) << FIX_SHIFT; e->y = (base_y + (selector & 31u) - 16) << FIX_SHIFT; break;
            case 1u: e->x = (base_x + offset) << FIX_SHIFT; e->y = (base_y + (selector & 31u) - 16) << FIX_SHIFT; break;
            case 2u: e->x = (base_x + (selector & 31u) - 16) << FIX_SHIFT; e->y = (base_y - offset) << FIX_SHIFT; break;
            default: e->x = (base_x + (selector & 31u) - 16) << FIX_SHIFT; e->y = (base_y + offset) << FIX_SHIFT; break;
        }

        e->x = clamp_i32(e->x, 8 << FIX_SHIFT, (WORLD_W - 8) << FIX_SHIFT);
        e->y = clamp_i32(e->y, 8 << FIX_SHIFT, (WORLD_H - 8) << FIX_SHIFT);
        e->vx = 0;
        e->vy = 0;
        port_gba_audio_spawn((uint8_t)(1u + (state->pressure >> 6)));
        break;
    }
}

static void update_projectiles(PortGameState *state) {
    uint8_t i;
    for (i = 0; i < PORT_MAX_PROJECTILES; ++i) {
        PortProjectile *p = &state->projectiles[i];
        int32_t px;
        int32_t py;
        if (!p->active) {
            continue;
        }

        p->x += p->vx;
        p->y += p->vy;
        if (p->ttl > 0u) {
            --p->ttl;
        }

        px = p->x >> FIX_SHIFT;
        py = p->y >> FIX_SHIFT;
        if (p->ttl == 0u || px < 0 || py < 0 || px >= WORLD_W || py >= WORLD_H) {
            p->active = 0;
        }
    }
}

static void update_enemies(PortGameState *state) {
    uint8_t i;
    for (i = 0; i < PORT_MAX_ENEMIES; ++i) {
        PortEnemy *e = &state->enemies[i];
        int32_t dx;
        int32_t dy;

        if (!e->active) {
            continue;
        }

        dx = state->player_x - e->x;
        dy = state->player_y - e->y;

        e->vx = clamp_v(dx >> 5, -(2 * FIX_ONE), (2 * FIX_ONE));
        e->vy = clamp_v(dy >> 5, -(2 * FIX_ONE), (2 * FIX_ONE));

        e->x += e->vx;
        e->y += e->vy;

        if (e->cooldown > 0u) {
            --e->cooldown;
        }

        if (((dx < (8 << FIX_SHIFT)) && (dx > -(8 << FIX_SHIFT))) &&
            ((dy < (8 << FIX_SHIFT)) && (dy > -(8 << FIX_SHIFT)))) {
            if (state->pressure < 245u) {
                state->pressure = (uint8_t)(state->pressure + 10u);
            }
            port_gba_audio_hit(0u);
            e->active = 0;
        }
    }
}

static void resolve_projectile_hits(PortGameState *state) {
    uint8_t i;
    for (i = 0; i < PORT_MAX_PROJECTILES; ++i) {
        PortProjectile *p = &state->projectiles[i];
        uint8_t j;
        if (!p->active) {
            continue;
        }

        for (j = 0; j < PORT_MAX_ENEMIES; ++j) {
            PortEnemy *e = &state->enemies[j];
            int32_t dx;
            int32_t dy;
            if (!e->active) {
                continue;
            }

            dx = p->x - e->x;
            dy = p->y - e->y;
            if (((dx < (6 << FIX_SHIFT)) && (dx > -(6 << FIX_SHIFT))) &&
                ((dy < (6 << FIX_SHIFT)) && (dy > -(6 << FIX_SHIFT)))) {
                p->active = 0;
                if (e->hp > 0u) {
                    --e->hp;
                }
                e->cooldown = 8u;
                if (e->hp == 0u) {
                    e->active = 0;
                    port_gba_audio_hit(1u);
                    if (state->pressure > 8u) {
                        state->pressure = (uint8_t)(state->pressure - 8u);
                    }
                } else {
                    port_gba_audio_hit(0u);
                }
                break;
            }
        }
    }
}

void port_game_update(PortGameState *state, const PortInputState *input) {
    int16_t move_x = 0;
    int16_t move_y = 0;
    int32_t dx;
    int32_t dy;
    int32_t dist2;
    int32_t target_cam_x;
    int32_t target_cam_y;

    if (!state || !input) {
        return;
    }

    if (input->held & KEY_LEFT) {
        move_x -= 1;
    }
    if (input->held & KEY_RIGHT) {
        move_x += 1;
    }
    if (input->held & KEY_UP) {
        move_y -= 1;
    }
    if (input->held & KEY_DOWN) {
        move_y += 1;
    }

    state->move_flash = (move_x != 0 || move_y != 0) ? 1u : 0u;

    /* Update persistent aim direction when moving */
    if (move_x != 0 || move_y != 0) {
        state->aim_x = (int8_t)move_x;
        state->aim_y = (int8_t)move_y;
    }

    state->player_vx = clamp_v(state->player_vx + (move_x * MOVE_ACCEL), -MOVE_MAX_SPEED, MOVE_MAX_SPEED);
    state->player_vy = clamp_v(state->player_vy + (move_y * MOVE_ACCEL), -MOVE_MAX_SPEED, MOVE_MAX_SPEED);

    if (state->player_vx > 0) {
        state->player_vx -= MOVE_DRAG;
    } else if (state->player_vx < 0) {
        state->player_vx += MOVE_DRAG;
    }

    if (state->player_vy > 0) {
        state->player_vy -= MOVE_DRAG;
    } else if (state->player_vy < 0) {
        state->player_vy += MOVE_DRAG;
    }

    if ((input->pressed & KEY_B) && state->dash_cooldown == 0u) {
        state->player_vx = (int16_t)(state->player_vx * 2);
        state->player_vy = (int16_t)(state->player_vy * 2);
        state->dash_cooldown = 20u;
        port_gba_audio_dash();
    }

    if (state->dash_cooldown > 0u) {
        --state->dash_cooldown;
    }

    if (state->fire_cooldown > 0u) {
        --state->fire_cooldown;
    }

    if ((input->pressed & KEY_L) && state->weapon_rank > 1u) {
        --state->weapon_rank;
    }
    if ((input->pressed & KEY_R) && state->weapon_rank < 9u) {
        ++state->weapon_rank;
    }

    if ((input->pressed & KEY_A) && state->fire_cooldown == 0u) {
        spawn_projectile(state, (int16_t)state->aim_x, (int16_t)state->aim_y);
        port_gba_audio_fire(state->weapon_rank);
        state->fire_cooldown = (uint8_t)(11u - (state->weapon_rank / 2u));
        if (state->fire_cooldown < 3u) {
            state->fire_cooldown = 3u;
        }
    }

    state->player_x += state->player_vx;
    state->player_y += state->player_vy;

    state->player_x = clamp_i32(state->player_x, 8 << FIX_SHIFT, (WORLD_W - 8) << FIX_SHIFT);
    state->player_y = clamp_i32(state->player_y, 8 << FIX_SHIFT, (WORLD_H - 8) << FIX_SHIFT);

    target_cam_x = state->player_x - ((SCREEN_W / 2) << FIX_SHIFT);
    target_cam_y = state->player_y - ((SCREEN_H / 2) << FIX_SHIFT);
    target_cam_x = clamp_i32(target_cam_x, 0, (WORLD_W - SCREEN_W) << FIX_SHIFT);
    target_cam_y = clamp_i32(target_cam_y, 0, (WORLD_H - SCREEN_H) << FIX_SHIFT);

    state->camera_x += (target_cam_x - state->camera_x) >> CAMERA_LAG_SHIFT;
    state->camera_y += (target_cam_y - state->camera_y) >> CAMERA_LAG_SHIFT;

    dx = (state->player_x >> FIX_SHIFT) - WORLD_CENTER_X;
    dy = (state->player_y >> FIX_SHIFT) - WORLD_CENTER_Y;
    dist2 = dx * dx + dy * dy;

    if (dist2 >= (WORLD_RADIUS * WORLD_RADIUS)) {
        state->pressure = 255u;
    } else {
        int32_t safe2 = WORLD_SAFE_RADIUS * WORLD_SAFE_RADIUS;
        if (dist2 <= safe2) {
            if (state->pressure > 20u) {
                --state->pressure;
            } else {
                state->pressure = 20u;
            }
        } else {
            int32_t numerator = dist2 - safe2;
            int32_t denom = (WORLD_RADIUS * WORLD_RADIUS) - safe2;
            uint8_t target_pressure = (uint8_t)(24 + ((numerator * 200) / denom));
            if (state->pressure < target_pressure) {
                ++state->pressure;
            }
        }
    }

    /* Live visual recomposition for the suit as combat pressure rises. */
    if (state->pressure > 180u) {
        state->armor_rank = 3u;
    } else if (state->pressure > 96u) {
        state->armor_rank = 2u;
    } else {
        state->armor_rank = 1u;
    }

    if (state->spawn_timer > 0u) {
        --state->spawn_timer;
    } else {
        spawn_enemy(state);
        state->spawn_timer = (uint16_t)(50u - (state->pressure / 7u));
        if (state->spawn_timer < 14u) {
            state->spawn_timer = 14u;
        }
    }

    update_projectiles(state);
    update_enemies(state);
    resolve_projectile_hits(state);

    set_palette_pressure(state->pressure);
    port_gba_audio_step(state->frame, state->pressure);
    ++state->frame;
}

void port_game_render(const PortGameState *state, volatile uint16_t *buffer) {
    uint16_t y;
    if (!state || !buffer) {
        return;
    }

    /* Background: 4x4 painter blocks with inverse zoom mapping.
       Much cheaper than the prior 2x2 pass while keeping the painted look. */
    for (y = 0; y < SCREEN_H; y += 4) {
        uint16_t x;
        int32_t world_y = (state->camera_y >> FIX_SHIFT) + (SCREEN_H / 2) + ((((int32_t)y - (SCREEN_H / 2)) * CAMERA_ZOOM_DEN) / CAMERA_ZOOM_NUM);
        for (x = 0; x < SCREEN_W; x += 4) {
            int32_t world_x = (state->camera_x >> FIX_SHIFT) + (SCREEN_W / 2) + ((((int32_t)x - (SCREEN_W / 2)) * CAMERA_ZOOM_DEN) / CAMERA_ZOOM_NUM);
            uint8_t c = world_color_at(world_x, world_y);
            uint16_t hx = x >> 1;
            uint16_t row;
            for (row = y; row < y + 4u && row < SCREEN_H; ++row) {
                mode4_put2(buffer, hx, row, c, c);
                mode4_put2(buffer, (uint16_t)(hx + 1u), row, c, c);
            }
        }
    }

    draw_parallax(buffer, state);
    draw_landscape_strokes(buffer, state);
    draw_enemies(state, buffer);
    draw_projectiles(state, buffer);
    draw_player(state, buffer);
    draw_hud(state, buffer);
}
