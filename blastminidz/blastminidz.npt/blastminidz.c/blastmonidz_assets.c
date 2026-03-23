#include "blastmonidz.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const char *const kGemPaintAssets[BLASTMONIDZ_PAINT_VARIANTS] = {
    "graphics/bomb, crate, tile, paint/redPaint.png",
    "graphics/bomb, crate, tile, paint/greenPaint.png",
    "graphics/bomb, crate, tile, paint/bluePaint.png",
    "graphics/bomb, crate, tile, paint/goldPaint.png",
    "graphics/bomb, crate, tile, paint/purplePaint.png"
};

static const char *const kVisualThemeNames[] = {
    "Consensus Ember",
    "Virid Lattice",
    "Brine Prism",
    "Ghost Static"
};

static const char *const kWorldPhaseNames[] = {
    "Grounded Chorus",
    "World Lattice",
    "Rival Static",
    "Ghost Bloom",
    "Mythic Drift"
};

const char *const blastmonidz_run_profile_path = "blastmonidz_run_profile.txt";
const char *const blastmonidz_replay_summary_path = "blastmonidz_replay_summary.txt";
const char *const blastmonidz_design_profile_path = "blastmonidz_design_profile.txt";

const char *const blastmonidz_concoctions[4] = {
    "Ion Mist",
    "Spore Spark",
    "Brine Pulse",
    "Cinder Haze"
};

const BlastmonidzHomeTile blastmonidz_home_tiles[BLASTMONIDZ_HOME_TILES] = {
    {"Anchor Slab", "load-bearing base plate", 'a', 0.92f, 0.18f, 0.16f, 0.84f},
    {"Choir Brick", "modular communal lattice", 'c', 0.78f, 0.26f, 0.34f, 0.75f},
    {"Spore Hearth", "organic warmth pocket", 's', 0.48f, 0.42f, 0.78f, 0.88f},
    {"Brine Arch", "hydrated threshold span", 'b', 0.66f, 0.54f, 0.44f, 0.71f},
    {"Ghost Lintel", "memory-bearing overhead seam", 'g', 0.58f, 0.63f, 0.28f, 0.59f},
    {"Kiln Weave", "thermal braid flooring", 'k', 0.62f, 0.48f, 0.57f, 0.67f},
    {"Root Mat", "civil underlay for living load", 'r', 0.44f, 0.31f, 0.81f, 0.91f},
    {"Signal Paver", "optical registration grid", 'p', 0.86f, 0.21f, 0.24f, 0.64f},
    {"Vault Petal", "protective ornament shell", 'v', 0.52f, 0.76f, 0.46f, 0.73f},
    {"Myth Terrace", "ceremonial elevated dwelling band", 'm', 0.74f, 0.68f, 0.52f, 0.82f}
};

const AssetArchetype blastmonidz_archive_map[MAX_ARCHIVE_ITEMS] = {
    {"titleScreen.png", "blastmonidz_ui_title_harmonic_logo", "ui/logo", "Primary title plate and attract-screen composition."},
    {"titleScreen.jpg", "blastmonidz_ui_title_scanbackdrop", "ui/backdrop", "Fallback rasterized title backdrop for menu presentation."},
    {"graphics/characters/bMan forWalk0001.png", "blastmonidz_blastkin_stride_front_a", "blastkin/motion", "Front-facing walk archetype remapped into BlastKin locomotion frames."},
    {"graphics/characters/bMan backWalk0001.png", "blastmonidz_blastkin_stride_back_a", "blastkin/motion", "Rear movement reference for consensus-camera trailing."},
    {"graphics/characters/bMan sideWalk0005.png", "blastmonidz_blastkin_stride_side_a", "blastkin/motion", "Side stride frame used for lateral tracking and dodge silhouettes."},
    {"bomb.fla", "blastmonidz_bomb_core_assembly", "bomb/core", "Bomb shell timing archetype and detonation silhouette source."},
    {"bomb.swf", "blastmonidz_bomb_core_runtime", "bomb/core", "Motion timing reference for pulse and fuse cadence."},
    {"Bomberman Sprites.fla", "blastmonidz_sprite_ancestry_sheet", "archive/source", "Legacy source sheet cataloged into internal naming conventions."},
    {"graphics/bomb, crate, tile, paint/", "blastmonidz_arena_tile_cluster", "arena/tiles", "Tile, obstacle, and mineral paint ancestry grouping."},
    {"graphics/characters/spritesheets/", "blastmonidz_blastkin_sheet_cluster", "blastkin/sheets", "Sprite sheet assembly bucket for motion archetypes."},
    {"bMan Walk.swf", "blastmonidz_blastkin_motion_reel", "blastkin/motion", "Reference reel for cyclic movement interpolation."},
    {"bMan baddieWalk.swf", "blastmonidz_artisapien_rival_motion_reel", "artisapien/motion", "Rival locomotion ancestry mapped to ArtiSapien opponents."},
    {"skullphuc.swf", "blastmonidz_ghost_timeline_manifest", "timeline/ghost", "Timeline ghost presentation ancestry for rewind state."},
    {"graphics/characters/bMan forWalk20001.png", "blastmonidz_stride_variant_beta", "blastkin/motion", "Variant stride set used as mutation seed for cosmetic evolution."},
    {"graphics/characters/bMan forWalk30001.png", "blastmonidz_stride_variant_gamma", "blastkin/motion", "Second mutation stride set used for growth stage remaps."},
    {"graphics/characters/bMan forWalk40001.png", "blastmonidz_stride_variant_delta", "blastkin/motion", "Third mutation stride set used for late-round silhouette shifts."}
};

const StarterSeed blastmonidz_starter_seeds[MAX_PLAYERS] = {
    {"Cinder Mite", "Pyroclast Bloom", 'C', 110, 34, 4, 7, {236, 92, 61, 255}},
    {"Virid Volt", "Spore Lattice", 'V', 100, 41, 6, 5, {92, 201, 120, 255}},
    {"Azure Shard", "Brine Prism", 'A', 118, 28, 5, 4, {88, 150, 236, 255}},
    {"Gloam Husk", "Echo Husk", 'G', 124, 25, 3, 8, {163, 106, 211, 255}}
};

const BlastmonidzStyle blastmonidz_style = {
    {17, 22, 30, 255},
    {29, 37, 49, 255},
    {82, 103, 126, 255},
    {232, 229, 217, 255},
    {241, 176, 82, 255},
    {74, 88, 108, 255},
    {134, 96, 65, 255},
    {42, 55, 68, 255},
    {232, 133, 72, 255},
    {146, 157, 188, 255}
};

static unsigned int hash_visual(unsigned int seed, int a, int b, int c) {
    unsigned int value = seed ^ (unsigned int)(a * 73856093u) ^ (unsigned int)(b * 19349663u) ^ (unsigned int)(c * 83492791u);
    value ^= value >> 13;
    value *= 1274126177u;
    value ^= value >> 16;
    return value;
}

static unsigned int home_tile_seed(const GameState *state, int world_x, int world_y) {
    unsigned int seed = 0x9E3779B9u;
    if (state) {
        seed ^= state->visuals.run_seed;
        seed ^= (unsigned int)(state->world_feed.balance * 131u);
        seed ^= (unsigned int)(state->round_index * 911u);
    }
    return hash_visual(seed, world_x, world_y, world_x + world_y * 3);
}

static float clampf_value(float value, float min_value, float max_value) {
    if (value < min_value) {
        return min_value;
    }
    if (value > max_value) {
        return max_value;
    }
    return value;
}

static int clampi_value(int value, int min_value, int max_value) {
    if (value < min_value) {
        return min_value;
    }
    if (value > max_value) {
        return max_value;
    }
    return value;
}

static const BlastmonidzHomeTile *player_home_tile(const GameState *state, int player_id) {
    if (!state || player_id < 0 || player_id >= MAX_PLAYERS) {
        return NULL;
    }
    return blastmonidz_select_home_tile(state, state->players[player_id].mon.x, state->players[player_id].mon.y);
}

static int dominant_chemistry(const GameState *state) {
    int dominant = 0;
    if (state->arena.chemistry[1] > state->arena.chemistry[dominant]) {
        dominant = 1;
    }
    if (state->arena.chemistry[2] > state->arena.chemistry[dominant]) {
        dominant = 2;
    }
    return dominant;
}

const char *blastmonidz_growth_title(int growth_stage) {
    if (growth_stage <= 0) {
        return "Seed Form";
    }
    if (growth_stage == 1) {
        return "Burst Form";
    }
    if (growth_stage == 2) {
        return "Crown Form";
    }
    return "Myth Form";
}

const AssetArchetype *blastmonidz_title_logo_asset(void) {
    return &blastmonidz_archive_map[0];
}

const AssetArchetype *blastmonidz_title_backdrop_asset(void) {
    return &blastmonidz_archive_map[1];
}

const AssetArchetype *blastmonidz_primary_motion_asset(void) {
    return &blastmonidz_archive_map[2];
}

const char *blastmonidz_world_phase_name(const GameState *state) {
    if (!state) {
        return kWorldPhaseNames[0];
    }
    if (state->world_feed.ghost_signal >= 58) {
        return kWorldPhaseNames[3];
    }
    if (state->world_feed.rival_signal >= 62) {
        return kWorldPhaseNames[2];
    }
    if (state->world_feed.balance >= 78) {
        return kWorldPhaseNames[4];
    }
    if (state->world_feed.world_signal >= 56) {
        return kWorldPhaseNames[1];
    }
    return kWorldPhaseNames[0];
}

const char *blastmonidz_gem_paint_asset(int chemistry_index) {
    if (chemistry_index < 0) {
        chemistry_index = 0;
    }
    return kGemPaintAssets[chemistry_index % BLASTMONIDZ_PAINT_VARIANTS];
}

const char *blastmonidz_visual_theme_name(const GameState *state) {
    int theme_family = 0;
    if (state) {
        theme_family = state->visuals.theme_family;
    }
    if (theme_family < 0) {
        theme_family = 0;
    }
    return kVisualThemeNames[theme_family % ((int)(sizeof(kVisualThemeNames) / sizeof(kVisualThemeNames[0])))];
}

int blastmonidz_select_home_tile_index(const GameState *state, int world_x, int world_y) {
    unsigned int mixed = home_tile_seed(state, world_x, world_y);
    int chemistry_mode = 0;
    if (state) {
        chemistry_mode = dominant_chemistry(state);
        mixed ^= (unsigned int)(state->world_feed.world_signal * 17 + chemistry_mode * 101 + state->arena.mineral_pressure * 3);
    }
    return (int)(mixed % BLASTMONIDZ_HOME_TILES);
}

const BlastmonidzHomeTile *blastmonidz_select_home_tile(const GameState *state, int world_x, int world_y) {
    return &blastmonidz_home_tiles[blastmonidz_select_home_tile_index(state, world_x, world_y)];
}

void blastmonidz_describe_home_tile(const BlastmonidzHomeTile *home_tile, char *buffer, int buffer_size) {
    if (!buffer || buffer_size <= 0) {
        return;
    }
    if (!home_tile) {
        buffer[0] = '\0';
        return;
    }
    snprintf(buffer, (size_t)buffer_size,
        "%s | shelter %.2f | growth %.2f | structure %.2f | ornament %.2f",
        home_tile->theory_role,
        home_tile->shelter_bias,
        home_tile->growth_bias,
        home_tile->structural_bias,
        home_tile->ornamental_bias);
}

void blastmonidz_describe_genome_profile(const BlastmonidzGenomeProfile *profile, char *buffer, int buffer_size) {
    if (!profile || !buffer || buffer_size <= 0) {
        return;
    }
    snprintf(buffer, (size_t)buffer_size,
        "passes %d | silhouette %.2f | shading %.2f | depth %.2f | cosmetic %.2f | structure %.2f | mutation %.2f | motion %.2f | hero %d | rival %d | dir %d | stride %d",
        profile->generation_passes,
        profile->silhouette_factor,
        profile->shading_factor,
        profile->depth_factor,
        profile->cosmetic_factor,
        profile->structural_factor,
        profile->mutation_factor,
        profile->animation_factor,
        profile->hero_family,
        profile->rival_family,
        profile->direction_bias,
        profile->frame_stride);
}

void blastmonidz_refresh_player_genome(GameState *state, int player_id) {
    BlastKin *player;
    Blastonid *mon;
    BlastmonidzGenomeProfile *profile;
    const BlastmonidzHomeTile *home_tile;
    float silhouette;
    float shading;
    float depth;
    float cosmetic;
    float structural;
    float mutation;
    float animation;
    int pass;

    if (!state || player_id < 0 || player_id >= MAX_PLAYERS) {
        return;
    }

    player = &state->players[player_id];
    mon = &player->mon;
    profile = &mon->cosmetic_genome;
    home_tile = player_home_tile(state, player_id);

    silhouette = clampf_value((float)(mon->genome[0] + mon->genome[3] + player->profile_rank * 3 + mon->starter->volatility * 2) / 80.0f, 0.0f, 1.0f);
    shading = clampf_value((float)(mon->starter->base_frequency + mon->self_feed.inner_signal + mon->self_feed.ghost_signal + mon->genome[1] * 2) / 140.0f, 0.0f, 1.0f);
    depth = clampf_value((float)(mon->growth_stage * 24 + mon->self_feed.world_signal + state->world_feed.ghost_signal + mon->genome[4] * 2) / 160.0f, 0.0f, 1.0f);
    cosmetic = clampf_value((float)(player->profile_rank * 6 + mon->concoction_id * 11 + mon->self_feed.balance + mon->genome[5] * 2 + (home_tile ? (int)(home_tile->ornamental_bias * 24.0f) : 8)) / 150.0f, 0.0f, 1.0f);
    structural = clampf_value((float)(mon->starter->metabolic_bias * 8 + mon->self_feed.world_signal + state->arena.mineral_pressure + (home_tile ? (int)(home_tile->structural_bias * 36.0f) : 18)) / 160.0f, 0.0f, 1.0f);
    mutation = clampf_value((float)(mon->evo_points + mon->gems_cleared * 10 + state->arena.chemistry[mon->concoction_id % 3] * 2 + (home_tile ? (int)(home_tile->growth_bias * 28.0f) : 10)) / 220.0f, 0.0f, 1.0f);
    animation = clampf_value((float)(mon->self_feed.inner_signal + mon->self_feed.balance + 40 - mon->delay_ticks * 4 + (mon->alive ? 12 : 0)) / 150.0f, 0.0f, 1.0f);

    memset(profile, 0, sizeof(*profile));
    for (pass = 0; pass < BLASTMONIDZ_GENOME_PASSES; ++pass) {
        float phase = (float)(pass + 1) / (float)BLASTMONIDZ_GENOME_PASSES;
        float echo = (float)(hash_visual(state->visuals.run_seed ^ (unsigned int)((player_id + 1) * 2654435761u), pass, mon->genome[pass % 6], mon->concoction_id + player->profile_rank) & 255u) / 255.0f;
        silhouette = clampf_value(silhouette * 0.58f + structural * 0.18f + mutation * 0.14f + echo * 0.10f * phase, 0.0f, 1.0f);
        shading = clampf_value(shading * 0.54f + cosmetic * 0.20f + depth * 0.16f + echo * 0.10f * (1.0f - phase * 0.5f), 0.0f, 1.0f);
        depth = clampf_value(depth * 0.56f + shading * 0.18f + structural * 0.14f + phase * 0.12f, 0.0f, 1.0f);
        cosmetic = clampf_value(cosmetic * 0.52f + shading * 0.16f + mutation * 0.18f + (home_tile ? home_tile->ornamental_bias * 0.14f : 0.07f), 0.0f, 1.0f);
        structural = clampf_value(structural * 0.60f + silhouette * 0.15f + (home_tile ? home_tile->structural_bias * 0.16f : 0.08f) + (player->artisapien ? 0.05f : 0.0f), 0.0f, 1.0f);
        mutation = clampf_value(mutation * 0.58f + cosmetic * 0.12f + depth * 0.10f + echo * 0.20f + phase * 0.08f, 0.0f, 1.0f);
        animation = clampf_value(animation * 0.57f + silhouette * 0.15f + cosmetic * 0.10f + (1.0f - structural) * 0.10f + echo * 0.08f, 0.0f, 1.0f);
    }

    profile->generation_passes = BLASTMONIDZ_GENOME_PASSES;
    profile->matured = BLASTMONIDZ_GENOME_PASSES >= 12 ? 1 : 0;
    profile->silhouette_factor = silhouette;
    profile->shading_factor = shading;
    profile->depth_factor = depth;
    profile->cosmetic_factor = cosmetic;
    profile->structural_factor = structural;
    profile->mutation_factor = mutation;
    profile->animation_factor = animation;
    profile->hero_family = (state->visuals.player_family[player_id] + (int)(silhouette * 7.0f) + (int)(cosmetic * 5.0f) + (int)(mutation * 3.0f)) % BLASTMONIDZ_HERO_FAMILIES;
    profile->rival_family = (state->visuals.rival_family[player_id] + (int)(silhouette * 5.0f) + (int)(depth * 4.0f) + player->artisapien) % BLASTMONIDZ_RIVAL_FAMILIES;
    profile->direction_bias = (state->visuals.player_direction_bias[player_id] + (int)(depth * 5.0f) + (int)(animation * 3.0f)) % BLASTMONIDZ_PLAYER_DIRECTIONS;
    profile->frame_stride = clampi_value(3 - (int)(animation * 2.4f) + (int)(structural * 0.6f), 1, 3);
    profile->frame_phase_bias = (int)(depth * 7.0f + shading * 5.0f + mutation * 13.0f);
    profile->floor_overlay_bias = (int)(cosmetic * 11.0f + depth * 7.0f);
    profile->crate_variant_bias = (int)(structural * 9.0f + silhouette * 5.0f);
    profile->bomb_frame_bias = (int)(mutation * 17.0f + animation * 9.0f);
    profile->paint_bias = (int)(shading * 9.0f + cosmetic * 13.0f);
}

void blastmonidz_refresh_asset_genome(GameState *state) {
    BlastmonidzGenomeProfile *profile;
    float silhouette = 0.0f;
    float shading = 0.0f;
    float depth = 0.0f;
    float cosmetic = 0.0f;
    float structural = 0.0f;
    float mutation = 0.0f;
    float animation = 0.0f;
    int i;

    if (!state) {
        return;
    }

    profile = &state->visuals.asset_genome;
    memset(profile, 0, sizeof(*profile));
    profile->generation_passes = BLASTMONIDZ_GENOME_PASSES;
    profile->matured = 1;

    for (i = 0; i < MAX_PLAYERS; ++i) {
        const BlastmonidzGenomeProfile *player_profile = &state->players[i].mon.cosmetic_genome;
        silhouette += player_profile->silhouette_factor;
        shading += player_profile->shading_factor;
        depth += player_profile->depth_factor;
        cosmetic += player_profile->cosmetic_factor;
        structural += player_profile->structural_factor;
        mutation += player_profile->mutation_factor;
        animation += player_profile->animation_factor;
        profile->floor_overlay_bias += player_profile->floor_overlay_bias;
        profile->crate_variant_bias += player_profile->crate_variant_bias;
        profile->bomb_frame_bias += player_profile->bomb_frame_bias;
        profile->paint_bias += player_profile->paint_bias;
        profile->frame_phase_bias += player_profile->frame_phase_bias;
    }

    profile->silhouette_factor = silhouette / (float)MAX_PLAYERS;
    profile->shading_factor = shading / (float)MAX_PLAYERS;
    profile->depth_factor = depth / (float)MAX_PLAYERS;
    profile->cosmetic_factor = cosmetic / (float)MAX_PLAYERS;
    profile->structural_factor = structural / (float)MAX_PLAYERS;
    profile->mutation_factor = mutation / (float)MAX_PLAYERS;
    profile->animation_factor = animation / (float)MAX_PLAYERS;
    profile->floor_overlay_bias /= MAX_PLAYERS;
    profile->crate_variant_bias /= MAX_PLAYERS;
    profile->bomb_frame_bias /= MAX_PLAYERS;
    profile->paint_bias /= MAX_PLAYERS;
    profile->frame_phase_bias /= MAX_PLAYERS;
    profile->hero_family = ((int)(profile->silhouette_factor * 7.0f) + (int)(profile->cosmetic_factor * 5.0f)) % BLASTMONIDZ_HERO_FAMILIES;
    profile->rival_family = ((int)(profile->depth_factor * 5.0f) + (int)(profile->mutation_factor * 3.0f)) % BLASTMONIDZ_RIVAL_FAMILIES;
    profile->direction_bias = ((int)(profile->depth_factor * 5.0f) + (int)(profile->animation_factor * 3.0f)) % BLASTMONIDZ_PLAYER_DIRECTIONS;
    profile->frame_stride = clampi_value(3 - (int)(profile->animation_factor * 2.4f), 1, 3);
}

void blastmonidz_refresh_all_genomes(GameState *state) {
    int i;
    if (!state) {
        return;
    }
    for (i = 0; i < MAX_PLAYERS; ++i) {
        blastmonidz_refresh_player_genome(state, i);
    }
    blastmonidz_refresh_asset_genome(state);
}

void blastmonidz_configure_visual_profile(GameState *state) {
    unsigned int round_seed;
    int i;
    if (!state) {
        return;
    }
    if (state->visuals.run_seed == 0) {
        state->visuals.run_seed = ((unsigned int)rand() << 16) ^ (unsigned int)rand() ^ 0x6D2B79F5u;
    }
    round_seed = state->visuals.run_seed ^ (unsigned int)(state->round_index * 2654435761u);
    state->visuals.theme_family = (int)(round_seed % 4u);
    state->visuals.floor_phase = (int)((round_seed >> 3) % BLASTMONIDZ_PAINT_VARIANTS);
    state->visuals.crate_phase = (int)((round_seed >> 6) % BLASTMONIDZ_CRATE_VARIANTS);
    state->visuals.bomb_phase = 1 + (int)((round_seed >> 9) % 4u);
    for (i = 0; i < BLASTMONIDZ_PAINT_VARIANTS; ++i) {
        state->visuals.paint_order[i] = i;
    }
    for (i = BLASTMONIDZ_PAINT_VARIANTS - 1; i > 0; --i) {
        unsigned int mixed = hash_visual(round_seed, i, state->round_index, i * 7);
        int swap_index = (int)(mixed % (unsigned int)(i + 1));
        int temp = state->visuals.paint_order[i];
        state->visuals.paint_order[i] = state->visuals.paint_order[swap_index];
        state->visuals.paint_order[swap_index] = temp;
    }
    for (i = 0; i < MAX_PLAYERS; ++i) {
        unsigned int mixed = hash_visual(round_seed, i + 1, state->players[i].artisapien, state->players[i].profile_rank);
        state->visuals.player_family[i] = (int)(mixed % BLASTMONIDZ_HERO_FAMILIES);
        state->visuals.player_direction_bias[i] = (int)((mixed >> 4) % BLASTMONIDZ_PLAYER_DIRECTIONS);
        state->visuals.player_frame_stride[i] = 1 + (int)((mixed >> 7) % 3u);
        state->visuals.rival_family[i] = (int)((mixed >> 11) % BLASTMONIDZ_RIVAL_FAMILIES);
    }
}

int blastmonidz_select_floor_overlay(const GameState *state, int world_x, int world_y) {
    unsigned int mixed;
    int chemistry_mode;
    if (!state) {
        return -1;
    }
    chemistry_mode = dominant_chemistry(state);
    mixed = hash_visual(state->visuals.run_seed + (unsigned int)state->visuals.floor_phase, world_x, world_y, chemistry_mode + state->round_index);
    if ((mixed & 7u) < 3u) {
        return -1;
    }
    return state->visuals.paint_order[(mixed + (unsigned int)chemistry_mode + (unsigned int)state->visuals.asset_genome.floor_overlay_bias) % BLASTMONIDZ_PAINT_VARIANTS];
}

int blastmonidz_select_crate_variant(const GameState *state, int world_x, int world_y) {
    unsigned int mixed;
    if (!state) {
        return 0;
    }
    mixed = hash_visual(state->visuals.run_seed + (unsigned int)state->visuals.crate_phase, world_x, world_y, state->arena.mineral_pressure + dominant_chemistry(state));
    mixed += (unsigned int)state->visuals.asset_genome.crate_variant_bias;
    return (int)(mixed % BLASTMONIDZ_CRATE_VARIANTS);
}

int blastmonidz_select_bomb_frame(const GameState *state, const Bomb *bomb, int bomb_id) {
    int frame;
    if (!state || !bomb) {
        return 0;
    }
    frame = state->consensus_tick * state->visuals.bomb_phase;
    frame += bomb->chemistry * 3;
    frame += bomb->power * 2;
    frame += (3 - bomb->timer) * 4;
    frame += bomb_id;
    frame += state->visuals.asset_genome.bomb_frame_bias;
    if (bomb->owner_id >= 0 && bomb->owner_id < MAX_PLAYERS) {
        const BlastmonidzGenomeProfile *profile = &state->players[bomb->owner_id].mon.cosmetic_genome;
        frame += profile->bomb_frame_bias;
        frame += profile->frame_phase_bias;
    }
    if (frame < 0) {
        frame = -frame;
    }
    return frame % BLASTMONIDZ_PLAYER_FRAMES;
}

int blastmonidz_select_gem_paint(const GameState *state, const BombGem *gem) {
    int chemistry_mode;
    if (!state || !gem) {
        return 0;
    }
    chemistry_mode = dominant_chemistry(state);
    return state->visuals.paint_order[(gem->class_id + gem->tier + chemistry_mode + state->round_index + state->visuals.asset_genome.paint_bias) % BLASTMONIDZ_PAINT_VARIANTS];
}

void blastmonidz_select_player_visual(const GameState *state, int player_id, int *use_rival, int *family, int *direction, int *frame) {
    const Blastonid *mon;
    const BlastmonidzGenomeProfile *profile;
    int chemistry_mode;
    int frame_stride;
    int frame_value;
    if (!state || player_id < 0 || player_id >= MAX_PLAYERS) {
        if (use_rival) {
            *use_rival = 0;
        }
        if (family) {
            *family = 0;
        }
        if (direction) {
            *direction = 0;
        }
        if (frame) {
            *frame = 0;
        }
        return;
    }
    mon = &state->players[player_id].mon;
    profile = &mon->cosmetic_genome;
    chemistry_mode = dominant_chemistry(state);
    frame_stride = profile->frame_stride > 0 ? profile->frame_stride : state->visuals.player_frame_stride[player_id];
    frame_value = state->consensus_tick / frame_stride;
    frame_value += mon->growth_stage * 3;
    frame_value += mon->concoction_id * 2;
    frame_value += mon->delay_ticks;
    frame_value += mon->x + mon->y;
    frame_value += profile->frame_phase_bias;
    frame_value += (int)(profile->animation_factor * 9.0f);
    if (use_rival) {
        *use_rival = state->players[player_id].artisapien ? 1 : 0;
    }
    if (family) {
        if (state->players[player_id].artisapien) {
            *family = (profile->rival_family + chemistry_mode + mon->growth_stage + state->players[player_id].profile_rank) % BLASTMONIDZ_RIVAL_FAMILIES;
        } else {
            *family = (profile->hero_family + chemistry_mode + mon->growth_stage) % BLASTMONIDZ_HERO_FAMILIES;
        }
    }
    if (direction) {
        *direction = (profile->direction_bias + mon->concoction_id + chemistry_mode + mon->growth_stage + (int)(profile->depth_factor * 2.0f)) % BLASTMONIDZ_PLAYER_DIRECTIONS;
    }
    if (frame) {
        if (frame_value < 0) {
            frame_value = -frame_value;
        }
        *frame = frame_value % BLASTMONIDZ_PLAYER_FRAMES;
    }
}