#ifndef GAME_H
#define GAME_H

#include <SDL.h>

#define MAX_ANCHORS 128

typedef struct {
    char asset_name[64];
    char anchor_name[64];
    float x;
    float y;
} AnchorPoint;

typedef struct {
    SDL_Texture *backgrounds[6];
    SDL_Texture *hud_rhythm_frame;
    SDL_Texture *media_deck_panel;
    SDL_Texture *misha_head;
    SDL_Texture *misha_torso;
    SDL_Texture *misha_arm_segment;
    SDL_Texture *misha_forearm_hand_segment;
    SDL_Texture *misha_leg_segment;
    SDL_Texture *misha_shin_foot_segment;
    SDL_Texture *leshy_core;
    SDL_Texture *leshy_limb;
    SDL_Texture *domovoi_vendor;
    SDL_Texture *ritual_ring_fx;
    SDL_Texture *parry_marker_fx;
    char runtime_root[260];
    AnchorPoint anchors[MAX_ANCHORS];
    int anchor_count;
} AssetPack;

typedef struct {
    SDL_Window *window;
    SDL_Renderer *renderer;
    int width, height;
    int quit;
    /* player */
    float px, py;
    float vx, vy;
    int on_ground;
    /* simple world index */
    int current_map;
    /* controller */
    SDL_GameController *controller;
    /* timing / tempo stub */
    int bpm;
    float beat_timer;
    /* media deck stub - 3 slots */
    int deck[3];
    float anim_time;
    float player_health;
    float player_stamina;
    int combo;
    float attack_timer;
    float attack_flash;
    float ritual_flash;
    float enemy_x;
    float enemy_health;
    float enemy_attack_timer;
    float enemy_stun_timer;
    float hit_message_timer;
    int last_attack_perfect;
    AssetPack assets;
} GameState;

int game_init(GameState *g, int w, int h);
void game_shutdown(GameState *g);
void game_process_input(GameState *g);
void game_update(GameState *g, float dt);
void game_render(GameState *g);

#endif
