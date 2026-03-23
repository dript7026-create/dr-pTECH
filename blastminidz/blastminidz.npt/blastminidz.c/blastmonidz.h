#ifndef BLASTMONIDZ_H
#define BLASTMONIDZ_H

#define VIEWPORT_W 18
#define VIEWPORT_H 12
#define ARENA_SCALE 8
#define ARENA_W (VIEWPORT_W * ARENA_SCALE)
#define ARENA_H (VIEWPORT_H * ARENA_SCALE)
#define MAX_PLAYERS 4
#define MAX_GEMS 72
#define MAX_BOMBS 32
#define MAX_LOG_LINES 8
#define MAX_LOG_LEN 96
#define MAX_NAME_LEN 48
#define MAX_ARCHIVE_ITEMS 16
#define MAX_TURNS_PER_ROUND 180
#define TARGET_RUN_WINS 3
#define BLASTMONIDZ_GROWTH_STAGES 4
#define BLASTMONIDZ_PLAYER_DIRECTIONS 3
#define BLASTMONIDZ_HERO_FAMILIES 4
#define BLASTMONIDZ_RIVAL_FAMILIES 2
#define BLASTMONIDZ_PLAYER_FRAMES 18
#define BLASTMONIDZ_PAINT_VARIANTS 5
#define BLASTMONIDZ_CRATE_VARIANTS 3
#define BLASTMONIDZ_HOME_TILES 10
#define BLASTMONIDZ_PROFILE_TEXT_MAX 512
#define BLASTMONIDZ_GENOME_PASSES 13

enum TileType {
    TILE_EMPTY = 0,
    TILE_WALL,
    TILE_CRATE
};

typedef struct {
    unsigned char r;
    unsigned char g;
    unsigned char b;
    unsigned char a;
} Color;

typedef struct {
    int width;
    int height;
    int stride;
    unsigned char *rgba;
} BlastmonidzPixelArray;

typedef struct {
    float aspect_ratio;
    float alpha_coverage;
    float palette_depth;
    float contrast;
    float edge_density;
    float curvature_bias;
    float symmetry_vertical;
    float symmetry_horizontal;
    float modularity;
    float structural_mass;
    float foundation_bias;
    float hue_temperature;
    float silhouette_complexity;
    float proportional_tension;
    Color dominant_colors[3];
} BlastmonidzAssetProfile;

typedef struct {
    int assets_analyzed;
    float mean_aspect_ratio;
    float mean_alpha_coverage;
    float mean_palette_depth;
    float mean_contrast;
    float mean_edge_density;
    float mean_curvature_bias;
    float mean_symmetry;
    float mean_modularity;
    float mean_structural_mass;
    float mean_foundation_bias;
    float mean_hue_temperature;
    float mean_silhouette_complexity;
    float mean_proportional_tension;
    float animation_elasticity;
    float environmental_mutation_bias;
    float structural_discipline;
    float ornamental_bias;
    Color dominant_colors[3];
    char theory_summary[BLASTMONIDZ_PROFILE_TEXT_MAX];
} BlastmonidzDesignOrganism;

typedef struct {
    const char *archive_entry;
    const char *blastmonidz_id;
    const char *role;
    const char *notes;
} AssetArchetype;

typedef struct {
    const char *name;
    const char *theory_role;
    char glyph;
    float structural_bias;
    float ornamental_bias;
    float growth_bias;
    float shelter_bias;
} BlastmonidzHomeTile;

typedef struct {
    const char *name;
    const char *growth_family;
    char glyph;
    int base_health;
    int base_frequency;
    int metabolic_bias;
    int volatility;
    Color color;
} StarterSeed;

typedef struct {
    int active;
    int x;
    int y;
    int timer;
    int power;
    int owner_id;
    int frequency;
    int chemistry;
} Bomb;

typedef struct {
    int active;
    int x;
    int y;
    int class_id;
    int tier;
    int frequency;
    int stability;
    char glyph;
} BombGem;

typedef struct {
    int inner_signal;
    int world_signal;
    int rival_signal;
    int ghost_signal;
    int balance;
} BlastmonidzSelfFeed;

typedef enum {
    BLASTMONIDZ_DOCTRINE_HARMONIZER = 0,
    BLASTMONIDZ_DOCTRINE_STEWARD,
    BLASTMONIDZ_DOCTRINE_MEDIATOR,
    BLASTMONIDZ_DOCTRINE_KINWEAVER,
    BLASTMONIDZ_DOCTRINE_COUNT
} BlastmonidzDoctrine;

typedef struct {
    int generation_passes;
    int matured;
    float silhouette_factor;
    float shading_factor;
    float depth_factor;
    float cosmetic_factor;
    float structural_factor;
    float mutation_factor;
    float animation_factor;
    int hero_family;
    int rival_family;
    int direction_bias;
    int frame_stride;
    int frame_phase_bias;
    int floor_overlay_bias;
    int crate_variant_bias;
    int bomb_frame_bias;
    int paint_bias;
} BlastmonidzGenomeProfile;

typedef struct {
    const StarterSeed *starter;
    char name[MAX_NAME_LEN];
    int genome[6];
    int x;
    int y;
    int health;
    int max_health;
    int delay_ticks;
    int growth_stage;
    int evo_points;
    int bomb_cooldown;
    int alive;
    int ghost_timer;
    int ghost_target_id;
    int qte_charge;
    int concoction_id;
    int round_kills;
    int gems_cleared;
    int precision_chain;
    int stage_penalties_applied;
    BlastmonidzSelfFeed self_feed;
    BlastmonidzGenomeProfile cosmetic_genome;
} Blastonid;

typedef struct {
    char name[MAX_NAME_LEN];
    int is_human;
    int artisapien;
    int doctrine;
    int profile_rank;
    int run_wins;
    char ai_debug_line[MAX_LOG_LEN];
    Blastonid mon;
} BlastKin;

typedef struct {
    int width;
    int height;
    unsigned char *tiles;
    BombGem gems[MAX_GEMS];
    Bomb bombs[MAX_BOMBS];
    int chemistry[3];
    int mineral_pressure;
    int last_explosion_owner;
    int last_explosion_kills;
    int last_explosion_gems;
} Arena;

typedef struct {
    unsigned int run_seed;
    int theme_family;
    int floor_phase;
    int crate_phase;
    int bomb_phase;
    int paint_order[BLASTMONIDZ_PAINT_VARIANTS];
    int player_family[MAX_PLAYERS];
    int player_direction_bias[MAX_PLAYERS];
    int player_frame_stride[MAX_PLAYERS];
    int rival_family[MAX_PLAYERS];
    BlastmonidzGenomeProfile asset_genome;
} BlastmonidzVisualProfile;

typedef struct {
    BlastKin players[MAX_PLAYERS];
    Arena arena;
    BlastmonidzVisualProfile visuals;
    BlastmonidzSelfFeed world_feed;
    int round_index;
    int consensus_tick;
    int optical_buffer;
    int running;
    int winner_id;
    int turns_this_round;
    char log_lines[MAX_LOG_LINES][MAX_LOG_LEN];
} GameState;

typedef struct {
    Color background;
    Color panel;
    Color panel_edge;
    Color text;
    Color accent;
    Color wall;
    Color crate;
    Color floor;
    Color bomb;
    Color ghost;
} BlastmonidzStyle;

typedef struct {
    int left;
    int top;
    int width;
    int height;
} ArenaView;

extern const char *const blastmonidz_run_profile_path;
extern const char *const blastmonidz_replay_summary_path;
extern const char *const blastmonidz_design_profile_path;
extern const char *const blastmonidz_concoctions[4];
extern const AssetArchetype blastmonidz_archive_map[MAX_ARCHIVE_ITEMS];
extern const BlastmonidzHomeTile blastmonidz_home_tiles[BLASTMONIDZ_HOME_TILES];
extern const StarterSeed blastmonidz_starter_seeds[MAX_PLAYERS];
extern const BlastmonidzStyle blastmonidz_style;

const char *blastmonidz_growth_title(int growth_stage);
const char *blastmonidz_doctrine_name(int doctrine);
const AssetArchetype *blastmonidz_title_logo_asset(void);
const AssetArchetype *blastmonidz_title_backdrop_asset(void);
const AssetArchetype *blastmonidz_primary_motion_asset(void);
const char *blastmonidz_world_phase_name(const GameState *state);
const char *blastmonidz_gem_paint_asset(int chemistry_index);
const char *blastmonidz_visual_theme_name(const GameState *state);
const BlastmonidzHomeTile *blastmonidz_select_home_tile(const GameState *state, int world_x, int world_y);
int blastmonidz_select_home_tile_index(const GameState *state, int world_x, int world_y);
void blastmonidz_describe_home_tile(const BlastmonidzHomeTile *home_tile, char *buffer, int buffer_size);
void blastmonidz_describe_genome_profile(const BlastmonidzGenomeProfile *profile, char *buffer, int buffer_size);
void blastmonidz_refresh_player_genome(GameState *state, int player_id);
void blastmonidz_refresh_asset_genome(GameState *state);
void blastmonidz_refresh_all_genomes(GameState *state);
void blastmonidz_configure_visual_profile(GameState *state);
int blastmonidz_select_floor_overlay(const GameState *state, int world_x, int world_y);
int blastmonidz_select_crate_variant(const GameState *state, int world_x, int world_y);
int blastmonidz_select_bomb_frame(const GameState *state, const Bomb *bomb, int bomb_id);
int blastmonidz_select_gem_paint(const GameState *state, const BombGem *gem);
void blastmonidz_select_player_visual(const GameState *state, int player_id, int *use_rival, int *family, int *direction, int *frame);
void blastmonidz_pixel_array_reset(BlastmonidzPixelArray *pixels);
void blastmonidz_asset_profile_reset(BlastmonidzAssetProfile *profile);
int blastmonidz_analyze_pixel_array(const BlastmonidzPixelArray *pixels, BlastmonidzAssetProfile *profile);
void blastmonidz_design_organism_reset(BlastmonidzDesignOrganism *organism);
void blastmonidz_design_organism_absorb(BlastmonidzDesignOrganism *organism, const BlastmonidzAssetProfile *profile);
void blastmonidz_design_organism_finalize(BlastmonidzDesignOrganism *organism);
void blastmonidz_describe_asset_profile(const BlastmonidzAssetProfile *profile, char *buffer, int buffer_size);
void blastmonidz_describe_design_organism(const BlastmonidzDesignOrganism *organism, char *buffer, int buffer_size);

void blastmonidz_push_log(GameState *state, const char *message);
void blastmonidz_load_archive_notice(GameState *state);
void blastmonidz_init_arena(Arena *arena);
void blastmonidz_free_arena(Arena *arena);
void blastmonidz_setup_players(GameState *state);
void blastmonidz_init_game(GameState *state);
void blastmonidz_begin_round(GameState *state);
int blastmonidz_count_active_gems(const Arena *arena);
int blastmonidz_gem_at(const Arena *arena, int x, int y);
int blastmonidz_bomb_at(const Arena *arena, int x, int y);
int blastmonidz_player_at(const GameState *state, int x, int y);
ArenaView blastmonidz_calculate_view(const GameState *state);
int blastmonidz_handle_player_command(GameState *state, int player_id, char command);
void blastmonidz_run_bot_turns(GameState *state);
void blastmonidz_advance_world(GameState *state);
int blastmonidz_determine_round_winner(GameState *state);
void blastmonidz_announce_round_winner(GameState *state, int round_winner);
int blastmonidz_check_run_winner(const GameState *state);
void blastmonidz_save_run_profile(const GameState *state);

#endif