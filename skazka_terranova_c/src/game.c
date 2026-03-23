#include "game.h"

#include <math.h>
#include <stdio.h>
#include <string.h>

#include <SDL.h>
#include <SDL_image.h>

typedef struct {
    float x;
    float y;
} Vec2;

static int file_exists(const char *path) {
    FILE *handle = fopen(path, "rb");
    if (handle) {
        fclose(handle);
        return 1;
    }
    return 0;
}

static void join_path(char *out, size_t out_size, const char *base, const char *leaf) {
    snprintf(out, out_size, "%s/%s", base, leaf);
}

static int find_runtime_root(char *out, size_t out_size) {
    const char *candidates[] = {
        "skazka_terranova_c/build/runtime_farim",
        "build/runtime_farim",
        "../build/runtime_farim",
        "../../build/runtime_farim"
    };
    int i;
    char probe[512];
    for (i = 0; i < 4; ++i) {
        join_path(probe, sizeof(probe), candidates[i], "farim_manifest.json");
        if (file_exists(probe)) {
            snprintf(out, out_size, "%s", candidates[i]);
            return 1;
        }
    }
    out[0] = '\0';
    return 0;
}

static SDL_Texture *load_texture(GameState *g, const char *relative_path) {
    char full_path[512];
    join_path(full_path, sizeof(full_path), g->assets.runtime_root, relative_path);
    if (!file_exists(full_path)) {
        return NULL;
    }
    return IMG_LoadTexture(g->renderer, full_path);
}

static void clear_texture(SDL_Texture **texture) {
    if (*texture) {
        SDL_DestroyTexture(*texture);
        *texture = NULL;
    }
}

static AnchorPoint *find_anchor(GameState *g, const char *asset_name, const char *anchor_name) {
    int i;
    for (i = 0; i < g->assets.anchor_count; ++i) {
        AnchorPoint *anchor = &g->assets.anchors[i];
        if (strcmp(anchor->asset_name, asset_name) == 0 && strcmp(anchor->anchor_name, anchor_name) == 0) {
            return anchor;
        }
    }
    return NULL;
}

static int load_anchor_csv(GameState *g) {
    char path[512];
    char line[256];
    FILE *handle;
    join_path(path, sizeof(path), g->assets.runtime_root, "runtime_anchors.csv");
    handle = fopen(path, "r");
    if (!handle) {
        return 0;
    }

    g->assets.anchor_count = 0;
    while (fgets(line, sizeof(line), handle)) {
        char *name;
        char *anchor_name;
        char *x_str;
        char *y_str;
        AnchorPoint *anchor;
        if (strncmp(line, "name,anchor_name", 16) == 0) {
            continue;
        }
        if (g->assets.anchor_count >= MAX_ANCHORS) {
            break;
        }
        name = strtok(line, ",\r\n");
        anchor_name = strtok(NULL, ",\r\n");
        x_str = strtok(NULL, ",\r\n");
        y_str = strtok(NULL, ",\r\n");
        if (!name || !anchor_name || !x_str || !y_str) {
            continue;
        }
        anchor = &g->assets.anchors[g->assets.anchor_count++];
        snprintf(anchor->asset_name, sizeof(anchor->asset_name), "%s", name);
        snprintf(anchor->anchor_name, sizeof(anchor->anchor_name), "%s", anchor_name);
        anchor->x = (float)atof(x_str);
        anchor->y = (float)atof(y_str);
    }

    fclose(handle);
    return 1;
}

static void load_generated_assets(GameState *g) {
    int i;
    for (i = 0; i < 6; ++i) {
        g->assets.backgrounds[i] = NULL;
    }

    if (!find_runtime_root(g->assets.runtime_root, sizeof(g->assets.runtime_root))) {
        return;
    }

    load_anchor_csv(g);

    g->assets.backgrounds[0] = load_texture(g, "assets/wild_orchard_backdrop.png");
    g->assets.backgrounds[1] = load_texture(g, "assets/wild_marsh_backdrop.png");
    g->assets.backgrounds[2] = load_texture(g, "assets/wild_mire_backdrop.png");
    g->assets.backgrounds[3] = load_texture(g, "assets/hub_city_segment_a.png");
    g->assets.backgrounds[4] = load_texture(g, "assets/hub_city_segment_b.png");
    g->assets.backgrounds[5] = load_texture(g, "assets/hub_city_segment_c.png");
    g->assets.hud_rhythm_frame = load_texture(g, "assets/hud_rhythm_frame.png");
    g->assets.media_deck_panel = load_texture(g, "assets/media_deck_panel.png");
    g->assets.misha_head = load_texture(g, "assets/misha_head.png");
    g->assets.misha_torso = load_texture(g, "assets/misha_torso.png");
    g->assets.misha_arm_segment = load_texture(g, "assets/misha_arm_segment.png");
    g->assets.misha_forearm_hand_segment = load_texture(g, "assets/misha_forearm_hand_segment.png");
    g->assets.misha_leg_segment = load_texture(g, "assets/misha_leg_segment.png");
    g->assets.misha_shin_foot_segment = load_texture(g, "assets/misha_shin_foot_segment.png");
    g->assets.leshy_core = load_texture(g, "assets/leshy_core.png");
    g->assets.leshy_limb = load_texture(g, "assets/leshy_limb.png");
    g->assets.domovoi_vendor = load_texture(g, "assets/domovoi_vendor.png");
    g->assets.ritual_ring_fx = load_texture(g, "assets/ritual_ring_fx.png");
    g->assets.parry_marker_fx = load_texture(g, "assets/parry_marker_fx.png");
}

static void unload_generated_assets(GameState *g) {
    int i;
    for (i = 0; i < 6; ++i) {
        clear_texture(&g->assets.backgrounds[i]);
    }
    clear_texture(&g->assets.hud_rhythm_frame);
    clear_texture(&g->assets.media_deck_panel);
    clear_texture(&g->assets.misha_head);
    clear_texture(&g->assets.misha_torso);
    clear_texture(&g->assets.misha_arm_segment);
    clear_texture(&g->assets.misha_forearm_hand_segment);
    clear_texture(&g->assets.misha_leg_segment);
    clear_texture(&g->assets.misha_shin_foot_segment);
    clear_texture(&g->assets.leshy_core);
    clear_texture(&g->assets.leshy_limb);
    clear_texture(&g->assets.domovoi_vendor);
    clear_texture(&g->assets.ritual_ring_fx);
    clear_texture(&g->assets.parry_marker_fx);
}

static Vec2 compute_anchor_world(SDL_FRect dst, float angle_deg, SDL_FPoint center_norm, AnchorPoint *anchor, SDL_RendererFlip flip) {
    float anchor_x = anchor ? anchor->x : center_norm.x;
    float anchor_y = anchor ? anchor->y : center_norm.y;
    float center_world_x = dst.x + center_norm.x * dst.w;
    float center_world_y = dst.y + center_norm.y * dst.h;
    float local_x;
    float local_y;
    float rad = angle_deg * 0.01745329252f;
    Vec2 result;

    if (flip & SDL_FLIP_HORIZONTAL) {
        anchor_x = 1.0f - anchor_x;
    }

    local_x = (anchor_x - center_norm.x) * dst.w;
    local_y = (anchor_y - center_norm.y) * dst.h;

    result.x = center_world_x + cosf(rad) * local_x - sinf(rad) * local_y;
    result.y = center_world_y + sinf(rad) * local_x + cosf(rad) * local_y;
    return result;
}

static SDL_FRect place_by_anchor(float world_x, float world_y, float width, float height, AnchorPoint *anchor, SDL_RendererFlip flip) {
    float anchor_x = anchor ? anchor->x : 0.5f;
    float anchor_y = anchor ? anchor->y : 0.5f;
    SDL_FRect dst;
    if (flip & SDL_FLIP_HORIZONTAL) {
        anchor_x = 1.0f - anchor_x;
    }
    dst.w = width;
    dst.h = height;
    dst.x = world_x - anchor_x * width;
    dst.y = world_y - anchor_y * height;
    return dst;
}

static void render_texture_fullscreen(GameState *g, SDL_Texture *texture) {
    if (texture) {
        SDL_FRect dst = {0.0f, 0.0f, (float)g->width, (float)g->height};
        SDL_RenderCopyF(g->renderer, texture, NULL, &dst);
    }
}

static void render_piece(GameState *g, SDL_Texture *texture, SDL_FRect dst, float angle_deg, SDL_FPoint center_norm, SDL_RendererFlip flip) {
    SDL_FPoint center_px = { center_norm.x * dst.w, center_norm.y * dst.h };
    if (!texture) {
        SDL_SetRenderDrawBlendMode(g->renderer, SDL_BLENDMODE_BLEND);
        SDL_SetRenderDrawColor(g->renderer, 220, 120, 180, 180);
        SDL_RenderFillRectF(g->renderer, &dst);
        return;
    }
    SDL_RenderCopyExF(g->renderer, texture, NULL, &dst, angle_deg, &center_px, flip);
}

static void render_player_rig(GameState *g) {
    float sway = sinf(g->anim_time * 3.4f);
    float stride = sinf(g->anim_time * 7.0f);
    SDL_FRect torso_dst = { g->px - 88.0f, g->py - 276.0f, 176.0f, 220.0f };
    SDL_FPoint torso_center = {0.5f, 0.5f};
    AnchorPoint *torso_neck = find_anchor(g, "misha_torso", "neck_socket");
    AnchorPoint *torso_shoulder_l = find_anchor(g, "misha_torso", "shoulder_l");
    AnchorPoint *torso_shoulder_r = find_anchor(g, "misha_torso", "shoulder_r");
    AnchorPoint *torso_hip_l = find_anchor(g, "misha_torso", "hip_l");
    AnchorPoint *torso_hip_r = find_anchor(g, "misha_torso", "hip_r");
    AnchorPoint *head_neck = find_anchor(g, "misha_head", "neck_pivot");
    AnchorPoint *arm_parent = find_anchor(g, "misha_arm_segment", "pivot_parent");
    AnchorPoint *arm_child = find_anchor(g, "misha_arm_segment", "pivot_child");
    AnchorPoint *forearm_parent = find_anchor(g, "misha_forearm_hand_segment", "pivot_parent");
    AnchorPoint *leg_parent = find_anchor(g, "misha_leg_segment", "pivot_parent");
    AnchorPoint *leg_child = find_anchor(g, "misha_leg_segment", "pivot_child");
    AnchorPoint *shin_parent = find_anchor(g, "misha_shin_foot_segment", "pivot_parent");
    float left_arm_angle = -18.0f + sway * 8.0f;
    float right_arm_angle = 20.0f - sway * 10.0f;
    float left_leg_angle = -10.0f + stride * 12.0f;
    float right_leg_angle = 8.0f - stride * 12.0f;
    Vec2 attach;
    SDL_FRect dst;
    Vec2 elbow;
    Vec2 knee;

    render_piece(g, g->assets.misha_torso, torso_dst, sway * 2.0f, torso_center, SDL_FLIP_NONE);

    attach = compute_anchor_world(torso_dst, sway * 2.0f, torso_center, torso_neck, SDL_FLIP_NONE);
    dst = place_by_anchor(attach.x, attach.y, 150.0f, 150.0f, head_neck, SDL_FLIP_NONE);
    render_piece(g, g->assets.misha_head, dst, sway * 3.0f, (SDL_FPoint){ head_neck ? head_neck->x : 0.5f, head_neck ? head_neck->y : 0.5f }, SDL_FLIP_NONE);

    attach = compute_anchor_world(torso_dst, sway * 2.0f, torso_center, torso_shoulder_l, SDL_FLIP_NONE);
    dst = place_by_anchor(attach.x, attach.y, 132.0f, 132.0f, arm_parent, SDL_FLIP_NONE);
    render_piece(g, g->assets.misha_arm_segment, dst, left_arm_angle, (SDL_FPoint){ arm_parent ? arm_parent->x : 0.2f, arm_parent ? arm_parent->y : 0.2f }, SDL_FLIP_NONE);
    elbow = compute_anchor_world(dst, left_arm_angle, (SDL_FPoint){ arm_parent ? arm_parent->x : 0.2f, arm_parent ? arm_parent->y : 0.2f }, arm_child, SDL_FLIP_NONE);
    dst = place_by_anchor(elbow.x, elbow.y, 132.0f, 132.0f, forearm_parent, SDL_FLIP_NONE);
    render_piece(g, g->assets.misha_forearm_hand_segment, dst, left_arm_angle + 18.0f + sway * 5.0f, (SDL_FPoint){ forearm_parent ? forearm_parent->x : 0.2f, forearm_parent ? forearm_parent->y : 0.2f }, SDL_FLIP_NONE);

    attach = compute_anchor_world(torso_dst, sway * 2.0f, torso_center, torso_shoulder_r, SDL_FLIP_NONE);
    dst = place_by_anchor(attach.x, attach.y, 132.0f, 132.0f, arm_parent, SDL_FLIP_HORIZONTAL);
    render_piece(g, g->assets.misha_arm_segment, dst, right_arm_angle, (SDL_FPoint){ arm_parent ? 1.0f - arm_parent->x : 0.8f, arm_parent ? arm_parent->y : 0.2f }, SDL_FLIP_HORIZONTAL);
    elbow = compute_anchor_world(dst, right_arm_angle, (SDL_FPoint){ arm_parent ? 1.0f - arm_parent->x : 0.8f, arm_parent ? arm_parent->y : 0.2f }, arm_child, SDL_FLIP_HORIZONTAL);
    dst = place_by_anchor(elbow.x, elbow.y, 132.0f, 132.0f, forearm_parent, SDL_FLIP_HORIZONTAL);
    render_piece(g, g->assets.misha_forearm_hand_segment, dst, right_arm_angle - 20.0f - sway * 3.0f, (SDL_FPoint){ forearm_parent ? 1.0f - forearm_parent->x : 0.8f, forearm_parent ? forearm_parent->y : 0.2f }, SDL_FLIP_HORIZONTAL);

    attach = compute_anchor_world(torso_dst, sway * 2.0f, torso_center, torso_hip_l, SDL_FLIP_NONE);
    dst = place_by_anchor(attach.x, attach.y, 138.0f, 138.0f, leg_parent, SDL_FLIP_NONE);
    render_piece(g, g->assets.misha_leg_segment, dst, left_leg_angle, (SDL_FPoint){ leg_parent ? leg_parent->x : 0.3f, leg_parent ? leg_parent->y : 0.2f }, SDL_FLIP_NONE);
    knee = compute_anchor_world(dst, left_leg_angle, (SDL_FPoint){ leg_parent ? leg_parent->x : 0.3f, leg_parent ? leg_parent->y : 0.2f }, leg_child, SDL_FLIP_NONE);
    dst = place_by_anchor(knee.x, knee.y, 138.0f, 138.0f, shin_parent, SDL_FLIP_NONE);
    render_piece(g, g->assets.misha_shin_foot_segment, dst, left_leg_angle - 10.0f, (SDL_FPoint){ shin_parent ? shin_parent->x : 0.2f, shin_parent ? shin_parent->y : 0.2f }, SDL_FLIP_NONE);

    attach = compute_anchor_world(torso_dst, sway * 2.0f, torso_center, torso_hip_r, SDL_FLIP_NONE);
    dst = place_by_anchor(attach.x, attach.y, 138.0f, 138.0f, leg_parent, SDL_FLIP_HORIZONTAL);
    render_piece(g, g->assets.misha_leg_segment, dst, right_leg_angle, (SDL_FPoint){ leg_parent ? 1.0f - leg_parent->x : 0.7f, leg_parent ? leg_parent->y : 0.2f }, SDL_FLIP_HORIZONTAL);
    knee = compute_anchor_world(dst, right_leg_angle, (SDL_FPoint){ leg_parent ? 1.0f - leg_parent->x : 0.7f, leg_parent ? leg_parent->y : 0.2f }, leg_child, SDL_FLIP_HORIZONTAL);
    dst = place_by_anchor(knee.x, knee.y, 138.0f, 138.0f, shin_parent, SDL_FLIP_HORIZONTAL);
    render_piece(g, g->assets.misha_shin_foot_segment, dst, right_leg_angle + 8.0f, (SDL_FPoint){ shin_parent ? 1.0f - shin_parent->x : 0.8f, shin_parent ? shin_parent->y : 0.2f }, SDL_FLIP_HORIZONTAL);
}

static void try_player_attack(GameState *g) {
    float beat_window = 60.0f / (float)g->bpm;
    float distance_to_beat = g->beat_timer;
    float enemy_distance = fabsf((g->width - 250.0f) - g->px);
    int attack_hits = (g->current_map < 3 && g->enemy_health > 0.0f && enemy_distance < 220.0f);

    if (g->attack_timer > 0.0f || g->player_stamina < 10.0f) {
        return;
    }

    if (distance_to_beat > beat_window * 0.5f) {
        distance_to_beat = beat_window - distance_to_beat;
    }

    g->attack_timer = 0.24f;
    g->attack_flash = 0.16f;
    g->player_stamina -= 10.0f;
    g->last_attack_perfect = 0;

    if (attack_hits) {
        float damage = 8.0f;
        if (distance_to_beat <= 0.05f) {
            damage = 18.0f;
            g->combo += 1;
            g->last_attack_perfect = 1;
        } else if (distance_to_beat <= 0.12f) {
            damage = 12.0f;
            g->combo += 1;
        } else {
            g->combo = 0;
        }
        g->enemy_health -= damage;
        if (g->enemy_health < 0.0f) g->enemy_health = 0.0f;
        g->hit_message_timer = 0.45f;
    } else {
        g->combo = 0;
    }
}

static void try_cast_ritual(GameState *g) {
    int a = g->deck[0];
    int b = g->deck[1];
    int c = g->deck[2];
    if (a == -1 || b == -1 || c == -1) {
        return;
    }
    g->ritual_flash = 0.45f;
    if (a == 1 && b == 2 && c == 3) {
        g->player_health += 22.0f;
        if (g->player_health > 100.0f) g->player_health = 100.0f;
    } else if (a == 3 && b == 3 && c == 3) {
        g->enemy_stun_timer = 2.0f;
    } else {
        g->enemy_health -= 14.0f;
        if (g->enemy_health < 0.0f) g->enemy_health = 0.0f;
    }
    g->deck[0] = g->deck[1] = g->deck[2] = -1;
}

int game_init(GameState *g, int w, int h) {
    memset(g, 0, sizeof(*g));
    g->width = w;
    g->height = h;
    g->px = w / 2.0f;
    g->py = h / 2.0f;
    g->current_map = 0;
    g->bpm = 100;
    g->deck[0] = g->deck[1] = g->deck[2] = -1;
    g->player_health = 100.0f;
    g->player_stamina = 100.0f;
    g->enemy_x = w - 250.0f;
    g->enemy_health = 100.0f;
    g->enemy_attack_timer = 2.0f;

    g->window = SDL_CreateWindow("SKAZKA: Terranova - Prototype",
                                 SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                                 w, h, SDL_WINDOW_SHOWN);
    if (!g->window) {
        fprintf(stderr, "SDL_CreateWindow: %s\n", SDL_GetError());
        return 0;
    }
    g->renderer = SDL_CreateRenderer(g->window, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);
    if (!g->renderer) {
        fprintf(stderr, "SDL_CreateRenderer: %s\n", SDL_GetError());
        SDL_DestroyWindow(g->window);
        return 0;
    }
    if ((IMG_Init(IMG_INIT_PNG) & IMG_INIT_PNG) == 0) {
        fprintf(stderr, "IMG_Init: %s\n", IMG_GetError());
    }

    if (SDL_NumJoysticks() > 0) {
        int i;
        for (i = 0; i < SDL_NumJoysticks(); ++i) {
            if (SDL_IsGameController(i)) {
                g->controller = SDL_GameControllerOpen(i);
                break;
            }
        }
    }

    load_generated_assets(g);
    return 1;
}

void game_shutdown(GameState *g) {
    unload_generated_assets(g);
    if (g->controller) SDL_GameControllerClose(g->controller);
    if (g->renderer) SDL_DestroyRenderer(g->renderer);
    if (g->window) SDL_DestroyWindow(g->window);
    IMG_Quit();
}

void game_process_input(GameState *g) {
    SDL_Event e;
    while (SDL_PollEvent(&e)) {
        if (e.type == SDL_QUIT) g->quit = 1;
        if (e.type == SDL_KEYDOWN) {
            if (e.key.keysym.sym == SDLK_ESCAPE) g->quit = 1;
            if (e.key.keysym.sym == SDLK_1) g->deck[0] = (g->deck[0] == -1) ? 1 : -1;
            if (e.key.keysym.sym == SDLK_2) g->deck[1] = (g->deck[1] == -1) ? 2 : -1;
            if (e.key.keysym.sym == SDLK_3) g->deck[2] = (g->deck[2] == -1) ? 3 : -1;
            if (e.key.keysym.sym == SDLK_j || e.key.keysym.sym == SDLK_x) try_player_attack(g);
            if (e.key.keysym.sym == SDLK_k || e.key.keysym.sym == SDLK_e) try_cast_ritual(g);
        }
        if (e.type == SDL_CONTROLLERBUTTONDOWN) {
            if (e.cbutton.button == SDL_CONTROLLER_BUTTON_BACK) {
                g->quit = 1;
            }
            if (e.cbutton.button == SDL_CONTROLLER_BUTTON_X) {
                try_player_attack(g);
            }
            if (e.cbutton.button == SDL_CONTROLLER_BUTTON_Y) {
                try_cast_ritual(g);
            }
        }
    }

    {
        const Uint8 *kb = SDL_GetKeyboardState(NULL);
        float speed = 300.0f;
        g->vx = 0.0f;
        if (kb[SDL_SCANCODE_A] || kb[SDL_SCANCODE_LEFT]) g->vx = -speed;
        if (kb[SDL_SCANCODE_D] || kb[SDL_SCANCODE_RIGHT]) g->vx = speed;
        if ((kb[SDL_SCANCODE_W] || kb[SDL_SCANCODE_SPACE] || kb[SDL_SCANCODE_UP]) && g->on_ground) {
            g->vy = -520.0f;
            g->on_ground = 0;
        }
    }

    if (g->controller) {
        Sint16 ax = SDL_GameControllerGetAxis(g->controller, SDL_CONTROLLER_AXIS_LEFTX);
        float fx = ax / 32767.0f;
        if (fabsf(fx) > 0.15f) g->vx = fx * 300.0f;
        if (SDL_GameControllerGetButton(g->controller, SDL_CONTROLLER_BUTTON_A) && g->on_ground) {
            g->vy = -520.0f;
            g->on_ground = 0;
        }
    }
}

void game_update(GameState *g, float dt) {
    float seconds_per_beat;
    g->anim_time += dt;
    if (g->attack_timer > 0.0f) g->attack_timer -= dt;
    if (g->attack_flash > 0.0f) g->attack_flash -= dt;
    if (g->ritual_flash > 0.0f) g->ritual_flash -= dt;
    if (g->enemy_stun_timer > 0.0f) g->enemy_stun_timer -= dt;
    if (g->hit_message_timer > 0.0f) g->hit_message_timer -= dt;

    g->vy += 1200.0f * dt;
    g->px += g->vx * dt;
    g->py += g->vy * dt;
    if (g->py >= g->height - 100) {
        g->py = g->height - 100;
        g->vy = 0.0f;
        g->on_ground = 1;
    }

    if (g->px < 50) {
        g->current_map = (g->current_map + 5) % 6;
        g->px = g->width - 100;
    }
    if (g->px > g->width - 50) {
        g->current_map = (g->current_map + 1) % 6;
        g->px = 100;
    }

    g->player_stamina += dt * 18.0f;
    if (g->player_stamina > 100.0f) g->player_stamina = 100.0f;

    if (g->current_map < 3) {
        if (g->enemy_health <= 0.0f) {
            g->enemy_health = 100.0f;
            g->enemy_attack_timer = 2.2f;
        }
        if (g->enemy_stun_timer <= 0.0f) {
            g->enemy_attack_timer -= dt;
            if (g->enemy_attack_timer <= 0.0f) {
                if (fabsf(g->enemy_x - g->px) < 260.0f) {
                    g->player_health -= 9.0f;
                    if (g->player_health < 0.0f) g->player_health = 0.0f;
                }
                g->enemy_attack_timer = 2.0f + fabsf(sinf(g->anim_time)) * 1.1f;
            }
        }
    }

    seconds_per_beat = 60.0f / (float)g->bpm;
    g->beat_timer += dt;
    if (g->beat_timer >= seconds_per_beat) {
        g->beat_timer -= seconds_per_beat;
    }
}

void game_render(GameState *g) {
    SDL_SetRenderDrawColor(g->renderer, 20, 20, 24, 255);
    SDL_RenderClear(g->renderer);

    render_texture_fullscreen(g, g->assets.backgrounds[g->current_map]);
    if (!g->assets.backgrounds[g->current_map]) {
        SDL_SetRenderDrawColor(g->renderer, 70, 70, 80, 255);
        SDL_RenderFillRect(g->renderer, &(SDL_Rect){0, 0, g->width, g->height});
    }

    SDL_SetRenderDrawBlendMode(g->renderer, SDL_BLENDMODE_BLEND);
    SDL_SetRenderDrawColor(g->renderer, 26, 18, 12, 255);
    SDL_RenderFillRect(g->renderer, &(SDL_Rect){0, g->height - 90, g->width, 90});

    if (g->attack_flash > 0.0f) {
        SDL_SetRenderDrawColor(g->renderer, 255, 220, 120, (Uint8)(g->attack_flash * 480.0f));
        SDL_RenderFillRect(g->renderer, &(SDL_Rect){0, 0, g->width, g->height});
    }
    if (g->ritual_flash > 0.0f) {
        SDL_SetRenderDrawColor(g->renderer, 120, 220, 255, (Uint8)(g->ritual_flash * 260.0f));
        SDL_RenderFillRect(g->renderer, &(SDL_Rect){0, 0, g->width, g->height});
    }

    render_player_rig(g);

    if (g->current_map < 3 && g->assets.leshy_core) {
        SDL_FRect leshy = { g->width - 360.0f, g->height - 360.0f, 230.0f, 230.0f };
        render_piece(g, g->assets.leshy_core, leshy, sinf(g->anim_time * 2.0f) * 4.0f, (SDL_FPoint){0.5f, 0.5f}, SDL_FLIP_HORIZONTAL);
        if (g->assets.parry_marker_fx && g->enemy_attack_timer < 0.45f && g->enemy_stun_timer <= 0.0f) {
            SDL_FRect marker = { g->width - 250.0f, 180.0f + fabsf(sinf(g->anim_time * 8.0f)) * 8.0f, 72.0f, 72.0f };
            render_piece(g, g->assets.parry_marker_fx, marker, 0.0f, (SDL_FPoint){0.5f, 0.5f}, SDL_FLIP_NONE);
        }
    }
    if (g->assets.domovoi_vendor && g->current_map >= 3) {
        SDL_FRect vendor = { 80.0f, g->height - 300.0f, 150.0f, 150.0f };
        render_piece(g, g->assets.domovoi_vendor, vendor, 0.0f, (SDL_FPoint){0.5f, 0.5f}, SDL_FLIP_NONE);
    }
    if (g->assets.ritual_ring_fx) {
        SDL_FRect ring = { g->px - 90.0f, g->py - 240.0f - fabsf(sinf(g->anim_time * 4.0f)) * 12.0f, 180.0f, 180.0f };
        render_piece(g, g->assets.ritual_ring_fx, ring, g->anim_time * 20.0f, (SDL_FPoint){0.5f, 0.5f}, SDL_FLIP_NONE);
    }
    if (g->assets.hud_rhythm_frame) {
        SDL_FRect hud = { 0.0f, 0.0f, (float)g->width, 160.0f };
        render_piece(g, g->assets.hud_rhythm_frame, hud, 0.0f, (SDL_FPoint){0.5f, 0.5f}, SDL_FLIP_NONE);
    }
    if (g->assets.media_deck_panel) {
        SDL_FRect panel = { 18.0f, g->height - 204.0f, 380.0f, 180.0f };
        render_piece(g, g->assets.media_deck_panel, panel, 0.0f, (SDL_FPoint){0.5f, 0.5f}, SDL_FLIP_NONE);
    }

    {
        int i;
        for (i = 0; i < 3; ++i) {
            SDL_Rect slot = { 58 + i * 98, g->height - 138, 64, 64 };
            if (g->deck[i] == -1) SDL_SetRenderDrawColor(g->renderer, 24, 24, 24, 220);
            else SDL_SetRenderDrawColor(g->renderer, 184, 104, 144, 240);
            SDL_RenderFillRect(g->renderer, &slot);
        }
    }

    SDL_SetRenderDrawColor(g->renderer, 20, 20, 20, 220);
    SDL_RenderFillRect(g->renderer, &(SDL_Rect){36, 26, 260, 18});
    SDL_SetRenderDrawColor(g->renderer, 186, 52, 72, 240);
    SDL_RenderFillRect(g->renderer, &(SDL_Rect){36, 26, (int)(260.0f * (g->player_health / 100.0f)), 18});
    SDL_SetRenderDrawColor(g->renderer, 20, 20, 20, 220);
    SDL_RenderFillRect(g->renderer, &(SDL_Rect){36, 52, 260, 12});
    SDL_SetRenderDrawColor(g->renderer, 76, 198, 132, 240);
    SDL_RenderFillRect(g->renderer, &(SDL_Rect){36, 52, (int)(260.0f * (g->player_stamina / 100.0f)), 12});
    if (g->current_map < 3) {
        SDL_SetRenderDrawColor(g->renderer, 20, 20, 20, 220);
        SDL_RenderFillRect(g->renderer, &(SDL_Rect){g->width - 296, 26, 260, 16});
        SDL_SetRenderDrawColor(g->renderer, 148, 116, 54, 240);
        SDL_RenderFillRect(g->renderer, &(SDL_Rect){g->width - 296, 26, (int)(260.0f * (g->enemy_health / 100.0f)), 16});
    }

    if (g->hit_message_timer > 0.0f) {
        SDL_SetRenderDrawColor(g->renderer, g->last_attack_perfect ? 255 : 220, g->last_attack_perfect ? 220 : 140, 120, 220);
        SDL_RenderFillRect(g->renderer, &(SDL_Rect){g->width / 2 - 40, 90, 80, 16});
    }

    SDL_RenderPresent(g->renderer);
}
