#include <3ds.h>
#include <citro2d.h>
#include <citro3d.h>

#include "../egosphere/egosphere.h"

#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "generated/bango_runtime_asset_pack.h"
#include "generated/bango_test_level.h"
#include "bango_engine_target/include/bango_engine_target.h"
#include "bango_engine_target/include/bango_telemetry_bridge.h"

#define BANGO_MOVE_COUNT 1000
#define BANGO_SKILL_NODE_COUNT 48
#define BANGO_WORLD_COUNT 8
#define BANGO_RELATIONSHIP_COUNT 6
#define BANGO_RIG_COUNT 2
#define BANGO_MAX_ENEMIES 10
#define BANGO_MAX_ENV_OBJECTS 24
#define BANGO_MAX_RUNTIME_BONES 24
#define BANGO_LANDSCAPE_W 32
#define BANGO_LANDSCAPE_H 32
#define BANGO_TERRAIN_UV_SUBDIV 4
#define BANGO_MAX_WILDLIFE 16
#define BANGO_PI 3.1415926535f

static BangoEngineTargetState g_engine_target;
static BangoTelemetryBridge g_telemetry_bridge;

typedef enum AttributeKind {
	ATTR_VIGOR,
	ATTR_HONEYHEART,
	ATTR_TALONCRAFT,
	ATTR_NERVE,
	ATTR_GRIT,
	ATTR_ARCANA,
	ATTR_COUNT
} AttributeKind;

typedef enum MoveCategory {
	MOVE_GROUND,
	MOVE_AERIAL,
	MOVE_MAGIC,
	MOVE_UTILITY,
	MOVE_CATEGORY_COUNT
} MoveCategory;

typedef enum XpVariety {
	XP_COMBAT,
	XP_EXPLORATION,
	XP_DIPLOMACY,
	XP_ARCANA,
	XP_SURVIVAL,
	XP_CRAFT,
	XP_VARIETY_COUNT
} XpVariety;

typedef enum WildlifeKind {
	WILD_FLORA_MOSS,
	WILD_FLORA_FUNGUS,
	WILD_FLORA_VINE,
	WILD_FAUNA_RAT,
	WILD_FAUNA_MOTH,
	WILD_FAUNA_CROW,
	WILD_KIND_COUNT
} WildlifeKind;

typedef struct Vec2 {
	float x;
	float y;
} Vec2;

typedef struct Vec3 {
	float x;
	float y;
	float z;
} Vec3;

typedef struct ScreenPoint {
	float x;
	float y;
	float depth;
	int visible;
} ScreenPoint;

typedef struct PhysicsBody {
	Vec3 position;
	Vec3 velocity;
	Vec3 half_extents;
	float mass;
	float ground_friction;
	float air_friction;
	int grounded;
} PhysicsBody;

typedef struct MoveSpec {
	int id;
	char name[48];
	MoveCategory category;
	int frame_count;
	int unlock_tier;
	float stamina_cost;
	float magic_cost;
	float momentum;
} MoveSpec;

typedef struct RigAssetSpec {
	char entity_name[32];
	char rig_name[32];
	char sheet_path[96];
	char loop_path[96];
	int bone_count;
	int imported_pose_count;
	float inbetween_stiffness;
	float inbetween_damping;
} RigAssetSpec;

typedef struct SkillNode {
	char name[40];
	int attribute;
	int branch;
	int cost;
	int unlocked;
} SkillNode;

typedef struct WorldNode {
	char name[40];
	int unlocked;
	int hive_sigils_required;
	int hive_sigils_found;
	int lantern_kin_found;
	float horror_pressure;
	float verticality;
} WorldNode;

typedef struct ShrineState {
	int active_world;
	int honey;
	int shrine_level;
	int attribute_points;
	int skill_points;
} ShrineState;

typedef struct RelationshipEntity {
	char name[40];
	float affinity;
	float fear;
	float trust;
	float rivalry;
	int last_action;
	Agent psyche;
} RelationshipEntity;

typedef struct QuestState {
	int act;
	int tula_stage;
	int witch_signal;
} QuestState;

typedef struct GameplayStats {
	float total_damage_dealt;
	float total_damage_taken;
	int enemies_defeated;
	int moves_executed;
	int dodges_performed;
	int shrines_refined;
	float distance_traveled;
	int objects_interacted;
	int magic_moves_used;
	int worlds_unlocked;
	int notes_earned;
	int sigils_earned;
} GameplayStats;

typedef struct XpAccumulator {
	float xp[XP_VARIETY_COUNT];
	float xp_rate[XP_VARIETY_COUNT];
	float lifetime[XP_VARIETY_COUNT];
	float attr_weights[ATTR_COUNT];
	int thresholds[XP_VARIETY_COUNT];
	int levels[XP_VARIETY_COUNT];
} XpAccumulator;

typedef struct PlayerState {
	PhysicsBody physics;
	float health;
	float max_health;
	float stamina;
	float max_stamina;
	float magic;
	float max_magic;
	int level;
	int selected_move;
	int nocturne_notes;
	int hive_sigils;
	int lantern_kin;
	int facing_angle;
	int attack_cooldown;
	int invulnerability;
	int combo_step;
	float attack_radius;
	int attributes[ATTR_COUNT];
	GameplayStats stats;
	XpAccumulator xp;
	Vec3 last_position;
} PlayerState;

typedef struct LandscapeMesh {
	int width;
	int height;
	float cell_size;
	float origin_x;
	float origin_z;
	float heights[BANGO_LANDSCAPE_W * BANGO_LANDSCAPE_H];
	uint8_t tile_indices[BANGO_LANDSCAPE_W * BANGO_LANDSCAPE_H];
} LandscapeMesh;

typedef struct EnvironmentObject {
	char name[40];
	Vec3 position;
	Vec3 half_extents;
	int asset_index;
	int active;
	int solid;
	int interactive;
} EnvironmentObject;

typedef struct EnemyActor {
	char name[40];
	PhysicsBody physics;
	float health;
	float max_health;
	float aggro_radius;
	float attack_range;
	float strike_power;
	float hurt_flash;
	int cooldown;
	int active;
	int archetype;
	int facing_angle;
	Agent psyche;
} EnemyActor;

typedef struct WildlifeEntity {
	char name[32];
	WildlifeKind kind;
	Vec3 position;
	Vec3 velocity;
	float health;
	float interaction_radius;
	int active;
	int is_flora;
	Agent psyche;
	float affinity;
	float fear;
	int harvested;
	float regrow_timer;
} WildlifeEntity;

typedef struct BoneWorldState {
	Vec3 position;
	float rotation;
} BoneWorldState;

typedef struct CharacterRigState {
	const RuntimeEntityAssetPack *pack;
	const RuntimeRigDef *rig;
	const RuntimeImportedPoseDef *active_pose;
	Vec3 root_position;
	BoneWorldState bones[BANGO_MAX_RUNTIME_BONES];
	BoneWorldState target_bones[BANGO_MAX_RUNTIME_BONES];
	Vec3 bone_velocities[BANGO_MAX_RUNTIME_BONES];
	float pose_clock_ms;
	float locomotion_phase;
	int current_angle;
	float inbetween_stiffness;
	float inbetween_damping;
} CharacterRigState;

typedef struct GameState {
	C3D_RenderTarget *top_left;
	C3D_RenderTarget *top_right;
	C3D_RenderTarget *bottom;
	C2D_TextBuf text_buf;
	MoveSpec moves[BANGO_MOVE_COUNT];
	RigAssetSpec rigs[BANGO_RIG_COUNT];
	SkillNode skill_nodes[BANGO_SKILL_NODE_COUNT];
	WorldNode worlds[BANGO_WORLD_COUNT];
	RelationshipEntity relationships[BANGO_RELATIONSHIP_COUNT];
	ShrineState shrine;
	QuestState quest;
	PlayerState player;
	LandscapeMesh landscape;
	EnvironmentObject objects[BANGO_MAX_ENV_OBJECTS];
	EnemyActor enemies[BANGO_MAX_ENEMIES];
	WildlifeEntity wildlife[BANGO_MAX_WILDLIFE];
	int wildlife_count;
	CharacterRigState bango_rig_state;
	CharacterRigState patoot_rig_state;
	int object_count;
	int enemy_count;
	int current_world;
	int selected_skill;
	int message_timer;
	u64 frame_counter;
	float camera_yaw;
	float camera_distance;
	float camera_height;
	char status_line[160];
} GameState;

static GameState g_game;

static const char *k_attribute_names[ATTR_COUNT] = {
	"Vigor", "Honeyheart", "Taloncraft", "Nerve", "Grit", "Arcana"
};

static const char *k_wildlife_names[WILD_KIND_COUNT] = {
	"Hive Moss", "Spore Cap", "Wax Vine", "Gutter Rat", "Lantern Moth", "Soot Crow"
};

static Vec3 vec3_make(float x, float y, float z)
{
	Vec3 value;
	value.x = x;
	value.y = y;
	value.z = z;
	return value;
}

static Vec3 vec3_add(Vec3 a, Vec3 b)
{
	return vec3_make(a.x + b.x, a.y + b.y, a.z + b.z);
}

static Vec3 vec3_sub(Vec3 a, Vec3 b)
{
	return vec3_make(a.x - b.x, a.y - b.y, a.z - b.z);
}

static Vec3 vec3_scale(Vec3 value, float scalar)
{
	return vec3_make(value.x * scalar, value.y * scalar, value.z * scalar);
}

static float vec3_dot(Vec3 a, Vec3 b)
{
	return a.x * b.x + a.y * b.y + a.z * b.z;
}

static Vec3 vec3_cross(Vec3 a, Vec3 b)
{
	return vec3_make(
		a.y * b.z - a.z * b.y,
		a.z * b.x - a.x * b.z,
		a.x * b.y - a.y * b.x);
}

static Vec3 vec3_normalize(Vec3 value)
{
	float length = sqrtf(vec3_dot(value, value));
	if (length <= 0.0001f) {
		return vec3_make(0.0f, 1.0f, 0.0f);
	}
	return vec3_scale(value, 1.0f / length);
}

static float vec2_length(float x, float y)
{
	return sqrtf(x * x + y * y);
}

static float clampf(float value, float minimum, float maximum)
{
	if (value < minimum) return minimum;
	if (value > maximum) return maximum;
	return value;
}

static float lerpf(float a, float b, float t)
{
	return a + (b - a) * t;
}

static float world_height_noise(int x, int z, int world_index)
{
	float fx = (float)x * 0.46f;
	float fz = (float)z * 0.37f;
	float seed = (float)(world_index + 1) * 0.71f;
	return sinf(fx + seed) * 0.55f + cosf(fz * 1.3f - seed) * 0.35f + sinf((fx + fz) * 0.33f) * 0.22f;
}

static const RuntimeEntityAssetPack *find_runtime_pack(const char *entity_name)
{
	int i;
	for (i = 0; i < g_bango_runtime_asset_pack_count; ++i) {
		if (strcmp(g_bango_runtime_asset_pack[i].entity_name, entity_name) == 0) {
			return &g_bango_runtime_asset_pack[i];
		}
	}
	return NULL;
}

static const RuntimeLandscapeTileDef *get_landscape_tile_def(int tile_index)
{
	if (tile_index < 0 || tile_index >= BANGO_TEST_TILE_COUNT) {
		return &g_bango_test_tiles[0];
	}
	return &g_bango_test_tiles[tile_index];
}

static int wrap_tile_sample(int value)
{
	int size = BANGO_TEST_TILE_SAMPLE_SIZE;
	value %= size;
	if (value < 0) {
		value += size;
	}
	return value;
}

static float sample_landscape_tile_height(const RuntimeLandscapeTileDef *tile, float u, float v)
{
	int sample_x = wrap_tile_sample((int)floorf(u * (float)BANGO_TEST_TILE_SAMPLE_SIZE));
	int sample_y = wrap_tile_sample((int)floorf(v * (float)BANGO_TEST_TILE_SAMPLE_SIZE));
	int index = sample_y * BANGO_TEST_TILE_SAMPLE_SIZE + sample_x;
	return (float)tile->height_samples[index] / 255.0f;
}

static u32 sample_landscape_tile_color(const RuntimeLandscapeTileDef *tile, float u, float v, float light, float horror)
{
	int sample_x = wrap_tile_sample((int)floorf(u * (float)BANGO_TEST_TILE_SAMPLE_SIZE));
	int sample_y = wrap_tile_sample((int)floorf(v * (float)BANGO_TEST_TILE_SAMPLE_SIZE));
	int index = sample_y * BANGO_TEST_TILE_SAMPLE_SIZE + sample_x;
	uint32_t packed = tile->albedo_samples[index];
	float relief = sample_landscape_tile_height(tile, u, v);
	float red = (float)((packed >> 24) & 0xFF);
	float green = (float)((packed >> 16) & 0xFF);
	float blue = (float)((packed >> 8) & 0xFF);
	float highlight = (relief - 0.5f) * tile->relief_strength * 95.0f + horror * 12.0f;
	red = clampf(red * light + highlight + (float)tile->accent_r * tile->relief_strength * 0.12f, 0.0f, 255.0f);
	green = clampf(green * light + highlight * 0.78f + (float)tile->accent_g * tile->relief_strength * 0.10f, 0.0f, 255.0f);
	blue = clampf(blue * light + highlight * 0.62f + (float)tile->accent_b * tile->relief_strength * 0.08f + horror * 10.0f, 0.0f, 255.0f);
	return C2D_Color32((u8)red, (u8)green, (u8)blue, 255);
}

static const RuntimeEnvironmentAssetDef *find_runtime_object_asset(int asset_index)
{
	if (asset_index < 0 || asset_index >= g_bango_runtime_object_asset_count) {
		return NULL;
	}
	return &g_bango_runtime_object_assets[asset_index];
}

static const RuntimeSpriteFrameDef *get_angle_frame(const RuntimeEntityAssetPack *pack, int angle_index)
{
	if (!pack || pack->angle_count <= 0) {
		return NULL;
	}
	if (angle_index < 0 || angle_index >= pack->angle_count) {
		angle_index = 0;
	}
	return pack->angles[angle_index];
}

static const RuntimeSpriteFrameDef *get_loop_frame(const RuntimeEntityAssetPack *pack, u64 frame_counter)
{
	if (!pack || pack->loop.frame_count <= 0 || !pack->loop.frames) {
		return NULL;
	}
	return pack->loop.frames[(frame_counter / 8u) % (u64)pack->loop.frame_count];
}

static u32 rgba_to_c2d_color(uint32_t rgba)
{
	unsigned int red = (rgba >> 24) & 0xFFu;
	unsigned int green = (rgba >> 16) & 0xFFu;
	unsigned int blue = (rgba >> 8) & 0xFFu;
	unsigned int alpha = rgba & 0xFFu;
	return C2D_Color32(red, green, blue, alpha);
}

#define BANGO_MAX_GPU_SPRITES 48

typedef struct GpuSpriteSlot {
	const RuntimeSpriteFrameDef *source;
	C3D_Tex tex;
	Tex3DS_SubTexture subtex;
	C2D_Image image;
	int valid;
} GpuSpriteSlot;

static GpuSpriteSlot g_gpu_sprites[BANGO_MAX_GPU_SPRITES];
static int g_gpu_sprite_count = 0;

static int next_pow2(int v)
{
	v--;
	v |= v >> 1;
	v |= v >> 2;
	v |= v >> 4;
	v |= v >> 8;
	return v + 1;
}

static C2D_Image *upload_sprite_to_gpu(const RuntimeSpriteFrameDef *frame)
{
	int i;
	int tw;
	int th;
	int x;
	int y;
	u32 *buf;
	GpuSpriteSlot *slot;

	if (!frame || !frame->pixels || !frame->palette) {
		return NULL;
	}
	for (i = 0; i < g_gpu_sprite_count; ++i) {
		if (g_gpu_sprites[i].source == frame) {
			return &g_gpu_sprites[i].image;
		}
	}
	if (g_gpu_sprite_count >= BANGO_MAX_GPU_SPRITES) {
		return NULL;
	}

	slot = &g_gpu_sprites[g_gpu_sprite_count];
	tw = next_pow2(frame->width);
	th = next_pow2(frame->height);
	if (tw < 8) tw = 8;
	if (th < 8) th = 8;
	if (!C3D_TexInit(&slot->tex, (u16)tw, (u16)th, GPU_RGBA8)) {
		return NULL;
	}

	buf = (u32 *)slot->tex.data;
	memset(buf, 0, (size_t)(tw * th * 4));

	for (y = 0; y < frame->height; ++y) {
		for (x = 0; x < frame->width; ++x) {
			uint8_t ci = frame->pixels[y * frame->width + x];
			u32 pixel_rgba = 0;
			int ty;
			int tile_x;
			int tile_y;
			int tile_w;
			int tile_offset;
			int inner_x;
			int inner_y;
			int inner_morton;
			int bit;
			if (ci > 0 && ci <= frame->palette_count) {
				uint32_t src = frame->palette[ci - 1];
				unsigned int r = (src >> 24) & 0xFFu;
				unsigned int g = (src >> 16) & 0xFFu;
				unsigned int b = (src >> 8) & 0xFFu;
				unsigned int a = src & 0xFFu;
				pixel_rgba = (a << 24) | (b << 16) | (g << 8) | r;
			}
			ty = th - 1 - y;
			tile_x = x >> 3;
			tile_y = ty >> 3;
			tile_w = tw >> 3;
			tile_offset = (tile_y * tile_w + tile_x) * 64;
			inner_x = x & 7;
			inner_y = ty & 7;
			inner_morton = 0;
			for (bit = 0; bit < 3; ++bit) {
				inner_morton |= ((inner_x >> bit) & 1) << (2 * bit + 1);
				inner_morton |= ((inner_y >> bit) & 1) << (2 * bit);
			}
			buf[tile_offset + inner_morton] = pixel_rgba;
		}
	}
	C3D_TexFlush(&slot->tex);

	slot->subtex.width = (u16)frame->width;
	slot->subtex.height = (u16)frame->height;
	slot->subtex.left = 0.0f;
	slot->subtex.top = 1.0f;
	slot->subtex.right = (float)frame->width / (float)tw;
	slot->subtex.bottom = 1.0f - (float)frame->height / (float)th;

	slot->image.tex = &slot->tex;
	slot->image.subtex = &slot->subtex;
	slot->source = frame;
	slot->valid = 1;
	g_gpu_sprite_count++;
	return &slot->image;
}

static void free_gpu_sprites(void)
{
	int i;
	for (i = 0; i < g_gpu_sprite_count; ++i) {
		if (g_gpu_sprites[i].valid) {
			C3D_TexDelete(&g_gpu_sprites[i].tex);
			g_gpu_sprites[i].valid = 0;
		}
	}
	g_gpu_sprite_count = 0;
}

static void draw_runtime_sprite_frame(const RuntimeSpriteFrameDef *frame, float anchor_x, float anchor_y, float pixel_scale)
{
	int row;
	float origin_x;
	float origin_y;
	C2D_Image *gpu_image;
	if (!frame || !frame->pixels || !frame->palette) {
		return;
	}

	gpu_image = upload_sprite_to_gpu(frame);
	if (gpu_image) {
		origin_x = anchor_x - (float)frame->pivot_x * pixel_scale;
		origin_y = anchor_y - (float)frame->pivot_y * pixel_scale;
		C2D_DrawImageAt(*gpu_image, origin_x, origin_y, 0.4f, NULL, pixel_scale, pixel_scale);
		return;
	}

	origin_x = anchor_x - (float)frame->pivot_x * pixel_scale;
	origin_y = anchor_y - (float)frame->pivot_y * pixel_scale;
	for (row = 0; row < frame->height; ++row) {
		int col;
		uint8_t run_color = frame->pixels[row * frame->width];
		int run_start = 0;
		for (col = 1; col <= frame->width; ++col) {
			uint8_t pixel = (col < frame->width) ? frame->pixels[row * frame->width + col] : 0u;
			if (pixel != run_color) {
				if (run_color > 0 && run_color <= frame->palette_count) {
					float draw_x = origin_x + (float)run_start * pixel_scale;
					float draw_y = origin_y + (float)row * pixel_scale;
					float draw_w = (float)(col - run_start) * pixel_scale;
					C2D_DrawRectSolid(draw_x, draw_y, 0.4f, draw_w, pixel_scale, rgba_to_c2d_color(frame->palette[run_color - 1]));
				}
				run_color = pixel;
				run_start = col;
			}
		}
	}
}

static void draw_text_line(float x, float y, float scale, u32 color, const char *text)
{
	C2D_Text line;
	C2D_TextParse(&line, g_game.text_buf, text);
	C2D_TextOptimize(&line);
	C2D_DrawText(&line, C2D_WithColor, x, y, 0.5f, scale, scale, color);
}

static void set_status(const char *text)
{
	strncpy(g_game.status_line, text, sizeof(g_game.status_line) - 1u);
	g_game.status_line[sizeof(g_game.status_line) - 1u] = '\0';
	g_game.message_timer = 180;
}

static float landscape_height_at(float world_x, float world_z)
{
	float local_x = (world_x - g_game.landscape.origin_x) / g_game.landscape.cell_size;
	float local_z = (world_z - g_game.landscape.origin_z) / g_game.landscape.cell_size;
	int x0 = (int)floorf(local_x);
	int z0 = (int)floorf(local_z);
	int x1;
	int z1;
	float tx;
	float tz;
	float h00;
	float h10;
	float h01;
	float h11;

	x0 = (int)clampf((float)x0, 0.0f, (float)(g_game.landscape.width - 1));
	z0 = (int)clampf((float)z0, 0.0f, (float)(g_game.landscape.height - 1));
	x1 = x0 + 1 < g_game.landscape.width ? x0 + 1 : x0;
	z1 = z0 + 1 < g_game.landscape.height ? z0 + 1 : z0;
	tx = clampf(local_x - (float)x0, 0.0f, 1.0f);
	tz = clampf(local_z - (float)z0, 0.0f, 1.0f);
	h00 = g_game.landscape.heights[z0 * g_game.landscape.width + x0];
	h10 = g_game.landscape.heights[z0 * g_game.landscape.width + x1];
	h01 = g_game.landscape.heights[z1 * g_game.landscape.width + x0];
	h11 = g_game.landscape.heights[z1 * g_game.landscape.width + x1];
	return lerpf(lerpf(h00, h10, tx), lerpf(h01, h11, tx), tz);
}

static void build_landscape_for_world(int world_index)
{
	WorldNode *world = &g_game.worlds[world_index];
	int x;
	int z;
	if (world_index == 0) {
		g_game.landscape.width = BANGO_TEST_LEVEL_W;
		g_game.landscape.height = BANGO_TEST_LEVEL_H;
		g_game.landscape.cell_size = g_bango_test_level_cell_size;
		g_game.landscape.origin_x = g_bango_test_level_origin_x;
		g_game.landscape.origin_z = g_bango_test_level_origin_z;
		for (z = 0; z < g_game.landscape.height; ++z) {
			for (x = 0; x < g_game.landscape.width; ++x) {
				int index = z * g_game.landscape.width + x;
				g_game.landscape.heights[index] = g_bango_test_level_heights[index];
				g_game.landscape.tile_indices[index] = g_bango_test_level_tile_indices[index];
			}
		}
		return;
	}

	g_game.landscape.width = BANGO_LANDSCAPE_W;
	g_game.landscape.height = BANGO_LANDSCAPE_H;
	g_game.landscape.cell_size = 1.25f + world->verticality * 0.7f;
	g_game.landscape.origin_x = -((float)(g_game.landscape.width - 1) * g_game.landscape.cell_size) * 0.5f;
	g_game.landscape.origin_z = 4.0f;

	for (z = 0; z < g_game.landscape.height; ++z) {
		for (x = 0; x < g_game.landscape.width; ++x) {
			float ridge = world_height_noise(x, z, world_index);
			float valley = sinf((float)z * 0.35f + world->horror_pressure * 5.0f) * 0.35f;
			float height = ridge * (0.75f + world->verticality * 1.4f) + valley;
			int index = z * g_game.landscape.width + x;
			g_game.landscape.heights[index] = height;
			g_game.landscape.tile_indices[index] = (uint8_t)((x + z) % BANGO_TEST_TILE_COUNT);
		}
	}
}

static void populate_environment_objects(int world_index)
{
	int i;
	WorldNode *world = &g_game.worlds[world_index];
	if (world_index == 0) {
		g_game.object_count = BANGO_TEST_LEVEL_OBJECT_COUNT;
		if (g_game.object_count > BANGO_MAX_ENV_OBJECTS) {
			g_game.object_count = BANGO_MAX_ENV_OBJECTS;
		}
		for (i = 0; i < g_game.object_count; ++i) {
			EnvironmentObject *object = &g_game.objects[i];
			const RuntimeLevelObjectSpawnDef *spawn = &g_bango_test_level_objects[i];
			memset(object, 0, sizeof(*object));
			strncpy(object->name, spawn->name, sizeof(object->name) - 1u);
			object->position.x = spawn->x;
			object->position.z = spawn->z;
			object->position.y = landscape_height_at(object->position.x, object->position.z);
			object->half_extents = vec3_make(spawn->half_x, spawn->half_y, spawn->half_z);
			object->asset_index = (g_bango_runtime_object_asset_count > 0) ? (i % g_bango_runtime_object_asset_count) : -1;
			object->active = 1;
			object->solid = spawn->solid;
			object->interactive = spawn->interactive;
		}
		return;
	}

	g_game.object_count = 10;
	if (g_game.object_count > BANGO_MAX_ENV_OBJECTS) {
		g_game.object_count = BANGO_MAX_ENV_OBJECTS;
	}
	for (i = 0; i < g_game.object_count; ++i) {
		EnvironmentObject *object = &g_game.objects[i];
		float lane = (float)((i % 5) - 2) * 1.9f;
		float depth = 7.0f + (float)(i / 2) * 1.9f;
		memset(object, 0, sizeof(*object));
		snprintf(object->name, sizeof(object->name), "%s Node %d", world->name, i + 1);
		object->position.x = lane + sinf((float)i * 0.8f) * 0.6f;
		object->position.z = depth;
		object->position.y = landscape_height_at(object->position.x, object->position.z);
		object->half_extents = vec3_make(0.35f + 0.08f * (float)(i % 3), 0.5f + 0.18f * (float)(i % 4), 0.35f + 0.05f * (float)(i % 2));
		object->asset_index = (g_bango_runtime_object_asset_count > 0) ? (i % g_bango_runtime_object_asset_count) : -1;
		object->active = 1;
		object->solid = 1;
		object->interactive = (i % 3 == 0);
	}
}

static void populate_enemy_wave(int world_index)
{
	int i;
	WorldNode *world = &g_game.worlds[world_index];
	if (world_index == 0) {
		g_game.enemy_count = BANGO_TEST_LEVEL_ENEMY_COUNT;
		if (g_game.enemy_count > BANGO_MAX_ENEMIES) {
			g_game.enemy_count = BANGO_MAX_ENEMIES;
		}
		for (i = 0; i < g_game.enemy_count; ++i) {
			EnemyActor *enemy = &g_game.enemies[i];
			const RuntimeLevelEnemySpawnDef *spawn = &g_bango_test_level_enemies[i];
			memset(enemy, 0, sizeof(*enemy));
			strncpy(enemy->name, spawn->name, sizeof(enemy->name) - 1u);
			enemy->physics.position.x = spawn->x;
			enemy->physics.position.z = spawn->z;
			enemy->physics.position.y = landscape_height_at(enemy->physics.position.x, enemy->physics.position.z) + 0.75f;
			enemy->physics.half_extents = vec3_make(0.33f, 0.75f, 0.33f);
			enemy->physics.mass = 1.35f + world->horror_pressure;
			enemy->physics.ground_friction = 7.6f;
			enemy->physics.air_friction = 1.1f;
			enemy->health = spawn->health;
			enemy->max_health = spawn->health;
			enemy->aggro_radius = 8.6f + world->horror_pressure * 4.5f;
			enemy->attack_range = 1.3f;
			enemy->strike_power = 4.2f + (float)spawn->kind * 1.8f + world->horror_pressure * 5.5f;
			enemy->hurt_flash = 0.0f;
			enemy->cooldown = 24 + i * 7;
			enemy->active = 1;
			enemy->archetype = spawn->kind;
			enemy->facing_angle = i % 4;
			egosphere_init_agent(&enemy->psyche, enemy->name);
		}
		return;
	}

	g_game.enemy_count = 4 + (world_index % 3);
	if (g_game.enemy_count > BANGO_MAX_ENEMIES) {
		g_game.enemy_count = BANGO_MAX_ENEMIES;
	}
	for (i = 0; i < g_game.enemy_count; ++i) {
		EnemyActor *enemy = &g_game.enemies[i];
		memset(enemy, 0, sizeof(*enemy));
		snprintf(enemy->name, sizeof(enemy->name), "Underhive Horror %d", i + 1);
		enemy->physics.position.x = -3.0f + (float)i * 1.8f;
		enemy->physics.position.z = 10.0f + (float)(i % 3) * 1.7f;
		enemy->physics.position.y = landscape_height_at(enemy->physics.position.x, enemy->physics.position.z) + 0.75f;
		enemy->physics.half_extents = vec3_make(0.33f, 0.75f, 0.33f);
		enemy->physics.mass = 1.2f + world->horror_pressure;
		enemy->physics.ground_friction = 7.4f;
		enemy->physics.air_friction = 1.1f;
		enemy->health = 22.0f + world->horror_pressure * 12.0f;
		enemy->max_health = enemy->health;
		enemy->aggro_radius = 8.0f + world->horror_pressure * 5.0f;
		enemy->attack_range = 1.25f;
		enemy->strike_power = 4.0f + world->horror_pressure * 6.0f;
		enemy->hurt_flash = 0.0f;
		enemy->cooldown = 30 + i * 5;
		enemy->active = 1;
		enemy->archetype = i % 3;
		enemy->facing_angle = i % 4;
		egosphere_init_agent(&enemy->psyche, enemy->name);
	}
}

static void free_wildlife(void)
{
	int i;
	for (i = 0; i < g_game.wildlife_count; ++i) {
		egosphere_free_agent(&g_game.wildlife[i].psyche);
	}
	g_game.wildlife_count = 0;
}

static void free_enemies(void)
{
	int i;
	for (i = 0; i < g_game.enemy_count; ++i) {
		egosphere_free_agent(&g_game.enemies[i].psyche);
	}
}

static void populate_wildlife(int world_index)
{
	int i;
	WorldNode *world = &g_game.worlds[world_index];
	g_game.wildlife_count = 8 + (world_index % 3) * 2;
	if (g_game.wildlife_count > BANGO_MAX_WILDLIFE) {
		g_game.wildlife_count = BANGO_MAX_WILDLIFE;
	}
	for (i = 0; i < g_game.wildlife_count; ++i) {
		WildlifeEntity *w = &g_game.wildlife[i];
		memset(w, 0, sizeof(*w));
		w->kind = (WildlifeKind)(i % WILD_KIND_COUNT);
		w->is_flora = (w->kind <= WILD_FLORA_VINE) ? 1 : 0;
		snprintf(w->name, sizeof(w->name), "%s %d", k_wildlife_names[w->kind], i + 1);
		w->position.x = -4.0f + (float)(i % 6) * 1.7f + sinf((float)i * 1.1f) * 0.6f;
		w->position.z = 5.5f + (float)(i / 3) * 1.8f;
		w->position.y = landscape_height_at(w->position.x, w->position.z);
		w->health = w->is_flora ? 1.0f : (3.0f + world->horror_pressure * 2.0f);
		w->interaction_radius = w->is_flora ? 1.2f : 3.5f;
		w->active = 1;
		w->harvested = 0;
		w->regrow_timer = 0.0f;
		w->affinity = 0.0f;
		w->fear = w->is_flora ? 0.0f : (0.2f + world->horror_pressure * 0.15f);
		egosphere_init_agent(&w->psyche, w->name);
	}
}

static void load_world_runtime(int world_index)
{
	free_wildlife();
	free_enemies();
	build_landscape_for_world(world_index);
	populate_environment_objects(world_index);
	populate_enemy_wave(world_index);
	populate_wildlife(world_index);
	g_game.shrine.active_world = world_index;
}

static void sync_runtime_rig_metadata(void)
{
	int i;
	for (i = 0; i < BANGO_RIG_COUNT; ++i) {
		const RuntimeEntityAssetPack *pack = find_runtime_pack(g_game.rigs[i].entity_name);
		if (!pack) {
			continue;
		}
		g_game.rigs[i].bone_count = pack->bone_count;
		g_game.rigs[i].imported_pose_count = pack->imported_pose_count;
	}
}

static void init_worlds(void)
{
	static const char *names[BANGO_WORLD_COUNT] = {
		"Brassroot Borough",
		"Saint Voltage Arcade",
		"Ossuary Transit",
		"Gutterwake Sewers",
		"Cinder Tenements",
		"Aviary Broadcast",
		"Witchcoil Spire",
		"Underhive Hub"
	};
	int i;
	for (i = 0; i < BANGO_WORLD_COUNT; ++i) {
		strncpy(g_game.worlds[i].name, names[i], sizeof(g_game.worlds[i].name) - 1u);
		g_game.worlds[i].unlocked = (i == 0 || i == BANGO_WORLD_COUNT - 1);
		g_game.worlds[i].hive_sigils_required = i * 2;
		g_game.worlds[i].hive_sigils_found = 0;
		g_game.worlds[i].lantern_kin_found = 0;
		g_game.worlds[i].horror_pressure = 0.15f + 0.1f * (float)i;
		g_game.worlds[i].verticality = 0.20f + 0.08f * (float)(i % 4);
	}
	g_game.current_world = 0;
}

static void init_moves(void)
{
	static const char *prefixes[] = {"Horn", "Patoot", "Hex", "Hive", "Gutter", "Volt", "Feather", "Spine", "Nocturne", "Witch"};
	static const char *middles[] = {"Rush", "Sweep", "Ward", "Lunge", "Dive", "Sigil", "Crack", "Spiral", "Surge", "Vault"};
	static const char *suffixes[] = {"I", "II", "III", "IV", "V", "Echo", "Bloom", "Refrain", "Burst", "Rite"};
	int i;
	for (i = 0; i < BANGO_MOVE_COUNT; ++i) {
		MoveSpec *move = &g_game.moves[i];
		move->id = i;
		snprintf(move->name, sizeof(move->name), "%s %s %s", prefixes[i % 10], middles[(i / 10) % 10], suffixes[(i / 100) % 10]);
		move->category = (MoveCategory)(i % MOVE_CATEGORY_COUNT);
		move->frame_count = 3 + (i % 4);
		move->unlock_tier = i / 125;
		move->stamina_cost = 4.0f + (float)(i % 7);
		move->magic_cost = (move->category == MOVE_MAGIC) ? (2.0f + (float)(i % 5)) : 0.0f;
		move->momentum = 0.8f + 0.1f * (float)(i % 6);
	}
}

static void init_rigs(void)
{
	strncpy(g_game.rigs[0].entity_name, "Bango", sizeof(g_game.rigs[0].entity_name) - 1u);
	strncpy(g_game.rigs[0].rig_name, "bango_base_rig", sizeof(g_game.rigs[0].rig_name) - 1u);
	strncpy(g_game.rigs[0].sheet_path, "assets/source_sheets/bango_tpose_4angle.png", sizeof(g_game.rigs[0].sheet_path) - 1u);
	strncpy(g_game.rigs[0].loop_path, "assets/concept_loops/bango_idle_keypose_loop.gif", sizeof(g_game.rigs[0].loop_path) - 1u);
	g_game.rigs[0].bone_count = 16;
	g_game.rigs[0].imported_pose_count = 0;
	g_game.rigs[0].inbetween_stiffness = 0.62f;
	g_game.rigs[0].inbetween_damping = 0.27f;

	strncpy(g_game.rigs[1].entity_name, "Patoot", sizeof(g_game.rigs[1].entity_name) - 1u);
	strncpy(g_game.rigs[1].rig_name, "patoot_base_rig", sizeof(g_game.rigs[1].rig_name) - 1u);
	strncpy(g_game.rigs[1].sheet_path, "assets/source_sheets/patoot_tpose_4angle.png", sizeof(g_game.rigs[1].sheet_path) - 1u);
	strncpy(g_game.rigs[1].loop_path, "assets/concept_loops/patoot_strut_keypose_loop.gif", sizeof(g_game.rigs[1].loop_path) - 1u);
	g_game.rigs[1].bone_count = 13;
	g_game.rigs[1].imported_pose_count = 0;
	g_game.rigs[1].inbetween_stiffness = 0.58f;
	g_game.rigs[1].inbetween_damping = 0.24f;
}

static void init_skill_tree(void)
{
	static const char *branches[] = {
		"Horn Arts", "Patoot Wingcraft", "Apiary Sorcery", "Street Rite", "Relic Salvage", "Underhive Social"
	};
	int i;
	for (i = 0; i < BANGO_SKILL_NODE_COUNT; ++i) {
		SkillNode *node = &g_game.skill_nodes[i];
		snprintf(node->name, sizeof(node->name), "%s %02d", branches[i % 6], i + 1);
		node->attribute = i % ATTR_COUNT;
		node->branch = i % 6;
		node->cost = 1 + (i % 4);
		node->unlocked = (i < 3);
	}
}

static void init_relationships(void)
{
	static const char *names[BANGO_RELATIONSHIP_COUNT] = {
		"Lantern Broker", "Rail Saint", "Gutter Choir", "Boiler Jackals", "Waxbound Kin", "Signal Heretic"
	};
	int i;
	for (i = 0; i < BANGO_RELATIONSHIP_COUNT; ++i) {
		RelationshipEntity *entity = &g_game.relationships[i];
		strncpy(entity->name, names[i], sizeof(entity->name) - 1u);
		entity->affinity = 0.1f * (float)i;
		entity->fear = 0.2f + 0.05f * (float)i;
		entity->trust = 0.15f;
		entity->rivalry = 0.05f * (float)i;
		entity->last_action = 0;
		egosphere_init_agent(&entity->psyche, entity->name);
	}
}

static void init_player(void)
{
	memset(&g_game.player, 0, sizeof(g_game.player));
	g_game.player.physics.position = vec3_make(0.0f, 1.1f, 6.2f);
	g_game.player.physics.half_extents = vec3_make(0.35f, 0.85f, 0.35f);
	g_game.player.physics.mass = 1.0f;
	g_game.player.physics.ground_friction = 8.0f;
	g_game.player.physics.air_friction = 1.3f;
	g_game.player.max_health = 100.0f;
	g_game.player.health = 100.0f;
	g_game.player.max_stamina = 72.0f;
	g_game.player.stamina = 72.0f;
	g_game.player.max_magic = 40.0f;
	g_game.player.magic = 40.0f;
	g_game.player.level = 1;
	g_game.player.selected_move = 0;
	g_game.player.nocturne_notes = 12;
	g_game.player.hive_sigils = 1;
	g_game.player.lantern_kin = 0;
	g_game.player.facing_angle = 0;
	g_game.player.attack_radius = 1.25f;
	g_game.player.attributes[ATTR_VIGOR] = 2;
	g_game.player.attributes[ATTR_HONEYHEART] = 2;
	g_game.player.attributes[ATTR_TALONCRAFT] = 2;
	g_game.player.attributes[ATTR_NERVE] = 3;
	g_game.player.attributes[ATTR_GRIT] = 2;
	g_game.player.attributes[ATTR_ARCANA] = 1;
}

static void init_character_rigs(void)
{
	memset(&g_game.bango_rig_state, 0, sizeof(g_game.bango_rig_state));
	memset(&g_game.patoot_rig_state, 0, sizeof(g_game.patoot_rig_state));
	g_game.bango_rig_state.pack = find_runtime_pack("Bango");
	g_game.patoot_rig_state.pack = find_runtime_pack("Patoot");
	g_game.bango_rig_state.rig = g_game.bango_rig_state.pack ? g_game.bango_rig_state.pack->rig : NULL;
	g_game.patoot_rig_state.rig = g_game.patoot_rig_state.pack ? g_game.patoot_rig_state.pack->rig : NULL;
	g_game.bango_rig_state.inbetween_stiffness = g_game.rigs[0].inbetween_stiffness;
	g_game.bango_rig_state.inbetween_damping = g_game.rigs[0].inbetween_damping;
	g_game.patoot_rig_state.inbetween_stiffness = g_game.rigs[1].inbetween_stiffness;
	g_game.patoot_rig_state.inbetween_damping = g_game.rigs[1].inbetween_damping;
}

static void init_xp(void)
{
	int i;
	memset(&g_game.player.xp, 0, sizeof(g_game.player.xp));
	memset(&g_game.player.stats, 0, sizeof(g_game.player.stats));
	for (i = 0; i < XP_VARIETY_COUNT; ++i) {
		g_game.player.xp.thresholds[i] = 100 + i * 20;
	}
	g_game.player.xp.attr_weights[ATTR_VIGOR] = 0.18f;
	g_game.player.xp.attr_weights[ATTR_HONEYHEART] = 0.15f;
	g_game.player.xp.attr_weights[ATTR_TALONCRAFT] = 0.18f;
	g_game.player.xp.attr_weights[ATTR_NERVE] = 0.17f;
	g_game.player.xp.attr_weights[ATTR_GRIT] = 0.16f;
	g_game.player.xp.attr_weights[ATTR_ARCANA] = 0.16f;
	g_game.player.last_position = g_game.player.physics.position;
}

static void init_game(void)
{
	memset(&g_game, 0, sizeof(g_game));
	init_worlds();
	init_moves();
	init_rigs();
	sync_runtime_rig_metadata();
	init_skill_tree();
	init_relationships();
	init_player();
	init_character_rigs();
	init_xp();
	g_game.shrine.honey = 16;
	g_game.shrine.shrine_level = 1;
	g_game.shrine.attribute_points = 2;
	g_game.shrine.skill_points = 2;
	g_game.quest.act = 1;
	g_game.quest.tula_stage = 1;
	g_game.quest.witch_signal = 15;
	g_game.camera_yaw = 0.08f;
	g_game.camera_distance = 8.2f;
	g_game.camera_height = 3.8f;
	load_world_runtime(g_game.current_world);
	g_game.player.physics.position.x = g_bango_test_spawn_x;
	g_game.player.physics.position.z = g_bango_test_spawn_z;
	g_game.player.physics.position.y = landscape_height_at(g_game.player.physics.position.x, g_game.player.physics.position.z) + g_game.player.physics.half_extents.y;
	set_status("Bango and Patoot descend into a tile-mapped 3D Underhive test level built from the new surface set.");
}

static void free_relationships(void)
{
	int i;
	for (i = 0; i < BANGO_RELATIONSHIP_COUNT; ++i) {
		egosphere_free_agent(&g_game.relationships[i].psyche);
	}
	free_enemies();
	free_wildlife();
}

static void update_relationships(void)
{
	int i;
	for (i = 0; i < BANGO_RELATIONSHIP_COUNT; ++i) {
		RelationshipEntity *entity = &g_game.relationships[i];
		int action = egosphere_decide_action(&entity->psyche, CONTEXT_COMBAT);
		double reward = 0.0;
		if (action == 0) reward = 0.15;
		if (action == 1) reward = (g_game.player.nocturne_notes > 20) ? 0.25 : -0.10;
		if (action == 2) reward = (g_game.player.stamina < 18.0f) ? 0.30 : -0.18;
		egosphere_update(&entity->psyche, action, reward, CONTEXT_COMBAT);
		entity->last_action = action;
		entity->affinity = clampf(entity->affinity + (float)reward * 0.08f, -1.0f, 1.0f);
		entity->fear = clampf(entity->fear + (action == 2 ? 0.01f : -0.004f), 0.0f, 1.0f);
		entity->trust = clampf(entity->trust + (reward > 0.0 ? 0.008f : -0.006f), 0.0f, 1.0f);
		entity->rivalry = clampf(entity->rivalry + (action == 2 ? 0.01f : 0.002f), 0.0f, 1.0f);
	}
}

static void refine_at_shrine(void)
{
	if (g_game.player.nocturne_notes < 5) {
		set_status("Not enough Nocturne Notes to refine at the apiary shrine.");
		return;
	}
	g_game.player.nocturne_notes -= 5;
	g_game.shrine.honey += 3;
	g_game.shrine.attribute_points += 1;
	g_game.shrine.skill_points += 1;
	g_game.player.level += 1;
	g_game.player.stats.shrines_refined += 1;
	set_status("Apiary reliquary refined bitter honey into growth.");
}

static void unlock_next_world(void)
{
	int next_world = g_game.current_world + 1;
	if (next_world >= BANGO_WORLD_COUNT - 1) {
		set_status("No further district is visible from this shrine route.");
		return;
	}
	if (g_game.player.hive_sigils < g_game.worlds[next_world].hive_sigils_required) {
		set_status("More Hive Sigils are needed to open that district.");
		return;
	}
	g_game.worlds[next_world].unlocked = 1;
	g_game.player.stats.worlds_unlocked += 1;
	g_game.current_world = next_world;
	load_world_runtime(next_world);
	set_status("A new district opens beneath the city skin.");
}

static void spend_attribute_point(int attribute)
{
	char buffer[96];
	if (g_game.shrine.attribute_points <= 0) {
		set_status("No attribute points available.");
		return;
	}
	g_game.player.attributes[attribute] += 1;
	g_game.shrine.attribute_points -= 1;
	g_game.player.max_stamina += (attribute == ATTR_GRIT || attribute == ATTR_NERVE) ? 2.0f : 0.5f;
	g_game.player.max_magic += (attribute == ATTR_ARCANA) ? 2.5f : 0.0f;
	g_game.player.max_health += (attribute == ATTR_VIGOR) ? 3.5f : 1.0f;
	g_game.player.health = clampf(g_game.player.health, 0.0f, g_game.player.max_health);
	g_game.player.stamina = clampf(g_game.player.stamina, 0.0f, g_game.player.max_stamina);
	g_game.player.magic = clampf(g_game.player.magic, 0.0f, g_game.player.max_magic);
	snprintf(buffer, sizeof(buffer), "%s increased.", k_attribute_names[attribute]);
	set_status(buffer);
}

static void apply_environment_collisions(PhysicsBody *body)
{
	int i;
	for (i = 0; i < g_game.object_count; ++i) {
		EnvironmentObject *object = &g_game.objects[i];
		float dx;
		float dz;
		float overlap_x;
		float overlap_z;
		if (!object->active || !object->solid) {
			continue;
		}
		dx = body->position.x - object->position.x;
		dz = body->position.z - object->position.z;
		overlap_x = (body->half_extents.x + object->half_extents.x) - fabsf(dx);
		overlap_z = (body->half_extents.z + object->half_extents.z) - fabsf(dz);
		if (overlap_x > 0.0f && overlap_z > 0.0f && body->position.y < object->position.y + object->half_extents.y + 1.8f) {
			if (overlap_x < overlap_z) {
				body->position.x += (dx < 0.0f) ? -overlap_x : overlap_x;
				body->velocity.x *= -0.15f;
			} else {
				body->position.z += (dz < 0.0f) ? -overlap_z : overlap_z;
				body->velocity.z *= -0.15f;
			}
		}
	}
}

static void integrate_body(PhysicsBody *body, float dt)
{
	float half_w = ((float)(g_game.landscape.width - 1) * g_game.landscape.cell_size) * 0.5f - 0.6f;
	float max_z = g_game.landscape.origin_z + (float)(g_game.landscape.height - 1) * g_game.landscape.cell_size - 0.6f;
	body->velocity.y -= 10.6f * dt;
	body->position = vec3_add(body->position, vec3_scale(body->velocity, dt));
	body->velocity.x *= 1.0f - clampf(body->grounded ? body->ground_friction * dt : body->air_friction * dt, 0.0f, 0.92f);
	body->velocity.z *= 1.0f - clampf(body->grounded ? body->ground_friction * dt : body->air_friction * dt, 0.0f, 0.92f);
	body->position.x = clampf(body->position.x, -half_w, half_w);
	body->position.z = clampf(body->position.z, g_game.landscape.origin_z + 0.3f, max_z);
	apply_environment_collisions(body);
	{
		float floor_y = landscape_height_at(body->position.x, body->position.z) + body->half_extents.y;
		if (body->position.y <= floor_y) {
			body->position.y = floor_y;
			body->velocity.y = 0.0f;
			body->grounded = 1;
		} else {
			body->grounded = 0;
		}
	}
}

static const RuntimeImportedPoseDef *select_pose_for_move(const CharacterRigState *state, const MoveSpec *move)
{
	int pose_count;
	int index;
	if (!state->rig || state->rig->imported_pose_count <= 0) {
		return NULL;
	}
	pose_count = state->rig->imported_pose_count;
	index = (move->id + move->category) % pose_count;
	return state->rig->poses[index];
}

static void trigger_move(void)
{
	MoveSpec *move = &g_game.moves[g_game.player.selected_move];
	float forward_x = 0.0f;
	float forward_z = 1.0f;
	int i;
	int hits = 0;
	if (g_game.player.attack_cooldown > 0) {
		set_status("Recovering from the last strike.");
		return;
	}
	if (g_game.player.stamina < move->stamina_cost) {
		set_status("Too exhausted to execute the selected move.");
		return;
	}
	if (g_game.player.magic < move->magic_cost) {
		set_status("Arcana reserves are too low for that move.");
		return;
	}
	g_game.player.stamina -= move->stamina_cost;
	g_game.player.magic -= move->magic_cost;
	if (move->magic_cost > 0.0f) g_game.player.stats.magic_moves_used += 1;
	g_game.player.attack_cooldown = 16 + move->frame_count * 2;
	g_game.player.combo_step = (g_game.player.combo_step + 1) % 3;
	g_game.player.attack_radius = 1.15f + move->momentum * 0.28f;
	switch (g_game.player.facing_angle) {
	case 1: forward_x = -1.0f; forward_z = 0.0f; break;
	case 2: forward_x = 1.0f; forward_z = 0.0f; break;
	case 3: forward_x = 0.0f; forward_z = -1.0f; break;
	default: forward_x = 0.0f; forward_z = 1.0f; break;
	}
	for (i = 0; i < g_game.enemy_count; ++i) {
		EnemyActor *enemy = &g_game.enemies[i];
		float dx;
		float dz;
		float dist_sq;
		float dist;
		float dot;
		float damage;
		if (!enemy->active || enemy->health <= 0.0f) {
			continue;
		}
		dx = enemy->physics.position.x - g_game.player.physics.position.x;
		dz = enemy->physics.position.z - g_game.player.physics.position.z;
		dist_sq = dx * dx + dz * dz;
		dist = sqrtf(dist_sq);
		if (dist <= 0.0001f || dist > g_game.player.attack_radius) {
			continue;
		}
		dot = ((dx / dist) * forward_x) + ((dz / dist) * forward_z);
		if (dot < -0.15f) {
			continue;
		}
		damage = 8.0f + (float)g_game.player.attributes[ATTR_TALONCRAFT] * 1.8f + (float)g_game.player.combo_step * 2.5f;
		enemy->health -= damage;
		g_game.player.stats.total_damage_dealt += damage;
		enemy->hurt_flash = 12.0f;
		enemy->physics.velocity.x += (dx / dist) * (1.7f + move->momentum * 0.32f);
		enemy->physics.velocity.z += (dz / dist) * (1.7f + move->momentum * 0.32f);
		enemy->physics.velocity.y += 2.4f;
		if (enemy->health <= 0.0f) {
			enemy->active = 0;
			g_game.player.nocturne_notes += 3;
			g_game.player.hive_sigils += ((move->id + i) % 5 == 0) ? 1 : 0;
			g_game.player.stats.enemies_defeated += 1;
			g_game.player.stats.sigils_earned += ((move->id + i) % 5 == 0) ? 1 : 0;
		}
		egosphere_update(&enemy->psyche, 1, -0.5, CONTEXT_COMBAT);
		++hits;
	}
	g_game.player.stats.moves_executed += 1;
	{
		const RuntimeImportedPoseDef *selected = select_pose_for_move(&g_game.bango_rig_state, move);
		if (selected) {
			g_game.bango_rig_state.active_pose = selected;
			g_game.bango_rig_state.pose_clock_ms = 0.0f;
		}
	}
	g_game.player.nocturne_notes += 1 + (move->id % 2);
	g_game.quest.witch_signal += 1;
	if (hits > 0) {
		set_status("Move connected inside the 3D arena.");
	} else {
		set_status(move->name);
	}
}

static void update_character_rig(CharacterRigState *state, Vec3 root_position, int angle_index, float dt_ms, int locomotion_active)
{
	int i;
	float stiffness;
	float damping;
	float dt_sec;
	if (!state->rig) {
		return;
	}
	state->root_position = root_position;
	state->current_angle = angle_index;
	state->pose_clock_ms += dt_ms;
	state->locomotion_phase += locomotion_active ? dt_ms * 0.015f : dt_ms * 0.004f;
	if (state->active_pose && state->pose_clock_ms > (float)state->active_pose->duration_ms) {
		state->active_pose = NULL;
		state->pose_clock_ms = 0.0f;
	}

	stiffness = state->inbetween_stiffness > 0.0f ? state->inbetween_stiffness : 0.6f;
	damping = state->inbetween_damping > 0.0f ? state->inbetween_damping : 0.25f;
	if (state->active_pose) {
		stiffness = state->active_pose->stiffness > 0.0f ? state->active_pose->stiffness : stiffness;
		damping = state->active_pose->damping > 0.0f ? state->active_pose->damping : damping;
	}
	dt_sec = dt_ms * 0.001f;

	for (i = 0; i < state->rig->bone_count && i < BANGO_MAX_RUNTIME_BONES; ++i) {
		const RuntimeRigBoneDef *bone = &state->rig->bones[i];
		float offset_x = 0.0f;
		float offset_y = 0.0f;
		float offset_rot = 0.0f;
		float local_x = bone->x * 0.028f;
		float local_y = bone->y * 0.028f;
		float rot_yaw = (float)angle_index * (BANGO_PI * 0.5f);
		float sin_yaw = sinf(rot_yaw);
		float cos_yaw = cosf(rot_yaw);
		Vec3 target;
		float target_rot;
		float spring_force_x;
		float spring_force_y;
		float spring_force_z;
		int pose_index;
		if (state->active_pose) {
			for (pose_index = 0; pose_index < state->active_pose->offset_count; ++pose_index) {
				const RuntimePoseBoneOffsetDef *offset = &state->active_pose->offsets[pose_index];
				if (offset->bone_index == i) {
					offset_x = offset->x * 0.020f;
					offset_y = offset->y * 0.020f;
					offset_rot = offset->rotation;
					break;
				}
			}
		}
		local_x += sinf(state->locomotion_phase + (float)i * 0.17f) * 0.03f;
		target.x = root_position.x + (local_x + offset_x) * cos_yaw;
		target.z = root_position.z + (local_x + offset_x) * sin_yaw;
		target.y = root_position.y + local_y + offset_y;
		target_rot = offset_rot;

		state->target_bones[i].position = target;
		state->target_bones[i].rotation = target_rot;

		spring_force_x = (target.x - state->bones[i].position.x) * stiffness * 120.0f;
		spring_force_y = (target.y - state->bones[i].position.y) * stiffness * 120.0f;
		spring_force_z = (target.z - state->bones[i].position.z) * stiffness * 120.0f;
		state->bone_velocities[i].x = (state->bone_velocities[i].x + spring_force_x * dt_sec) * (1.0f - damping);
		state->bone_velocities[i].y = (state->bone_velocities[i].y + spring_force_y * dt_sec) * (1.0f - damping);
		state->bone_velocities[i].z = (state->bone_velocities[i].z + spring_force_z * dt_sec) * (1.0f - damping);

		state->bones[i].position.x += state->bone_velocities[i].x * dt_sec;
		state->bones[i].position.y += state->bone_velocities[i].y * dt_sec;
		state->bones[i].position.z += state->bone_velocities[i].z * dt_sec;
		state->bones[i].rotation = lerpf(state->bones[i].rotation, target_rot, clampf(stiffness * 2.0f * dt_sec, 0.0f, 1.0f));
	}
}

static void update_enemy_ai(float dt)
{
	int i;
	for (i = 0; i < g_game.enemy_count; ++i) {
		EnemyActor *enemy = &g_game.enemies[i];
		float dx;
		float dz;
		float dist_sq;
		float dist;
		if (!enemy->active) {
			continue;
		}
		if (enemy->hurt_flash > 0.0f) {
			enemy->hurt_flash -= 1.0f;
		}
		dx = g_game.player.physics.position.x - enemy->physics.position.x;
		dz = g_game.player.physics.position.z - enemy->physics.position.z;
		dist_sq = dx * dx + dz * dz;
		dist = sqrtf(dist_sq);
		if (enemy->cooldown > 0) {
			enemy->cooldown -= 1;
		}
		if (dist < enemy->aggro_radius && dist > 0.001f) {
			float speed = 1.2f + (float)enemy->archetype * 0.18f;
			int ai_action = egosphere_decide_action(&enemy->psyche, CONTEXT_COMBAT);
			if (ai_action == 1 && enemy->health < enemy->max_health * 0.3f) {
				enemy->physics.velocity.x -= (dx / dist) * speed * dt * 2.8f;
				enemy->physics.velocity.z -= (dz / dist) * speed * dt * 2.8f;
			} else if (ai_action == 2) {
				speed *= 1.35f;
				enemy->physics.velocity.x += (dx / dist) * speed * dt * 5.2f;
				enemy->physics.velocity.z += (dz / dist) * speed * dt * 5.2f;
			} else {
				enemy->physics.velocity.x += (dx / dist) * speed * dt * 4.0f;
				enemy->physics.velocity.z += (dz / dist) * speed * dt * 4.0f;
			}
			enemy->facing_angle = (fabsf(dx) > fabsf(dz)) ? (dx < 0.0f ? 1 : 2) : (dz < 0.0f ? 3 : 0);
		}
		if (dist < enemy->attack_range && enemy->cooldown <= 0 && g_game.player.invulnerability <= 0) {
			g_game.player.health = clampf(g_game.player.health - enemy->strike_power, 0.0f, g_game.player.max_health);
			g_game.player.stats.total_damage_taken += enemy->strike_power;
			g_game.player.invulnerability = 30;
			g_game.player.physics.velocity.x -= (dx / (dist > 0.001f ? dist : 1.0f)) * 1.2f;
			g_game.player.physics.velocity.z -= (dz / (dist > 0.001f ? dist : 1.0f)) * 1.2f;
			g_game.player.physics.velocity.y += 1.3f;
			enemy->cooldown = 48;
			egosphere_update(&enemy->psyche, 2, 0.4, CONTEXT_COMBAT);
			set_status("A hostile closed in with a close-range strike.");
		}
		integrate_body(&enemy->physics, dt);
	}
}

static void update_xp_rates(void)
{
	GameplayStats *s = &g_game.player.stats;
	XpAccumulator *xp = &g_game.player.xp;
	float total_actions;
	xp->xp_rate[XP_COMBAT] = s->total_damage_dealt * 0.008f + (float)s->enemies_defeated * 0.35f + (float)s->moves_executed * 0.02f;
	xp->xp_rate[XP_EXPLORATION] = s->distance_traveled * 0.04f + (float)s->worlds_unlocked * 2.0f;
	xp->xp_rate[XP_DIPLOMACY] = (float)s->objects_interacted * 0.18f;
	xp->xp_rate[XP_ARCANA] = (float)s->magic_moves_used * 0.22f;
	xp->xp_rate[XP_SURVIVAL] = s->total_damage_taken * 0.012f + (float)s->dodges_performed * 0.28f;
	xp->xp_rate[XP_CRAFT] = (float)s->notes_earned * 0.12f + (float)s->sigils_earned * 0.45f + (float)s->shrines_refined * 0.6f;
	total_actions = (float)(s->moves_executed + s->dodges_performed + s->shrines_refined + s->objects_interacted + s->magic_moves_used + 1);
	xp->attr_weights[ATTR_VIGOR] = 0.10f + (float)s->dodges_performed / total_actions * 0.3f;
	xp->attr_weights[ATTR_HONEYHEART] = 0.10f + (float)s->shrines_refined / total_actions * 0.3f;
	xp->attr_weights[ATTR_TALONCRAFT] = 0.10f + (float)s->moves_executed / total_actions * 0.3f;
	xp->attr_weights[ATTR_NERVE] = 0.10f + (float)s->enemies_defeated / total_actions * 0.3f;
	xp->attr_weights[ATTR_GRIT] = 0.10f + s->total_damage_taken / (total_actions * 10.0f + 1.0f) * 0.3f;
	xp->attr_weights[ATTR_ARCANA] = 0.10f + (float)s->magic_moves_used / total_actions * 0.3f;
}

static void distribute_xp(float dt)
{
	XpAccumulator *xp = &g_game.player.xp;
	int i;
	int j;
	for (i = 0; i < XP_VARIETY_COUNT; ++i) {
		float gain = xp->xp_rate[i] * dt * 0.016f;
		xp->xp[i] += gain;
		xp->lifetime[i] += gain;
		if (xp->xp[i] >= (float)xp->thresholds[i]) {
			xp->xp[i] -= (float)xp->thresholds[i];
			xp->levels[i] += 1;
			xp->thresholds[i] = (int)((float)xp->thresholds[i] * 1.18f) + 15;
			for (j = 0; j < ATTR_COUNT; ++j) {
				if (xp->attr_weights[j] > 0.18f) {
					g_game.player.attributes[j] += 1;
				}
			}
			g_game.player.max_health += 1.5f;
			g_game.player.max_stamina += 0.8f;
			g_game.player.max_magic += 0.4f;
			g_game.player.level += 1;
		}
	}
}

static void track_distance(void)
{
	Vec3 delta = vec3_sub(g_game.player.physics.position, g_game.player.last_position);
	float dist = sqrtf(delta.x * delta.x + delta.y * delta.y + delta.z * delta.z);
	if (dist > 0.01f && dist < 5.0f) {
		g_game.player.stats.distance_traveled += dist;
	}
	g_game.player.last_position = g_game.player.physics.position;
}

static void update_wildlife(float dt)
{
	int i;
	float player_x = g_game.player.physics.position.x;
	float player_z = g_game.player.physics.position.z;
	for (i = 0; i < g_game.wildlife_count; ++i) {
		WildlifeEntity *w = &g_game.wildlife[i];
		float dx;
		float dz;
		float dist;
		int action;
		double reward;
		if (!w->active) {
			if (w->is_flora && w->harvested) {
				w->regrow_timer -= dt;
				if (w->regrow_timer <= 0.0f) {
					w->active = 1;
					w->harvested = 0;
					w->health = 1.0f;
				}
			}
			continue;
		}
		if (w->is_flora) {
			continue;
		}
		dx = player_x - w->position.x;
		dz = player_z - w->position.z;
		dist = sqrtf(dx * dx + dz * dz);
		action = egosphere_decide_action(&w->psyche, CONTEXT_HABIT);
		reward = 0.0;
		if (dist < w->interaction_radius) {
			switch (action) {
			case 0: break;
			case 1:
				if (dist > 0.1f) {
					w->velocity.x = -(dx / dist) * 2.2f;
					w->velocity.z = -(dz / dist) * 2.2f;
				}
				w->fear = clampf(w->fear + 0.008f, 0.0f, 1.0f);
				reward = (w->fear > 0.5f) ? 0.15 : -0.05;
				break;
			case 2:
				if (dist > 0.8f) {
					w->velocity.x = (dx / dist) * 0.9f;
					w->velocity.z = (dz / dist) * 0.9f;
				}
				w->affinity = clampf(w->affinity + 0.006f, -1.0f, 1.0f);
				reward = 0.2;
				g_game.player.stats.objects_interacted += 1;
				break;
			}
		} else {
			w->velocity.x += sinf((float)g_game.frame_counter * 0.03f + (float)i * 0.7f) * 0.14f;
			w->velocity.z += cosf((float)g_game.frame_counter * 0.025f + (float)i * 1.1f) * 0.10f;
			reward = 0.05;
		}
		egosphere_update(&w->psyche, action, reward, CONTEXT_HABIT);
		w->position.x += w->velocity.x * dt;
		w->position.z += w->velocity.z * dt;
		w->velocity.x *= 0.88f;
		w->velocity.z *= 0.88f;
		{
			float half_w = ((float)(g_game.landscape.width - 1) * g_game.landscape.cell_size) * 0.5f - 0.5f;
			float max_z = g_game.landscape.origin_z + (float)(g_game.landscape.height - 1) * g_game.landscape.cell_size - 0.5f;
			w->position.x = clampf(w->position.x, -half_w, half_w);
			w->position.z = clampf(w->position.z, g_game.landscape.origin_z + 0.3f, max_z);
		}
		w->position.y = landscape_height_at(w->position.x, w->position.z);
	}
}

static void interact_wildlife_nearby(void)
{
	int i;
	float px = g_game.player.physics.position.x;
	float pz = g_game.player.physics.position.z;
	for (i = 0; i < g_game.wildlife_count; ++i) {
		WildlifeEntity *w = &g_game.wildlife[i];
		float dx;
		float dz;
		float dist;
		if (!w->active || !w->is_flora || w->harvested) {
			continue;
		}
		dx = px - w->position.x;
		dz = pz - w->position.z;
		dist = sqrtf(dx * dx + dz * dz);
		if (dist < w->interaction_radius) {
			w->harvested = 1;
			w->active = 0;
			w->regrow_timer = 12.0f + (float)(w->kind % 3) * 4.0f;
			g_game.player.nocturne_notes += 1;
			g_game.player.stats.notes_earned += 1;
			g_game.player.stats.objects_interacted += 1;
			egosphere_update(&w->psyche, 0, 0.2, CONTEXT_HABIT);
			set_status("Harvested wild growth for Nocturne Notes.");
			return;
		}
	}
}

static void update_game(u32 k_down, circlePosition pad)
{
	float dt = 1.0f / 60.0f;
	float input_x = (float)pad.dx / 160.0f;
	float input_z = (float)(-pad.dy) / 160.0f;
	float input_mag = vec2_length(input_x, input_z);
	g_game.frame_counter += 1;
	if (input_mag > 1.0f) {
		input_x /= input_mag;
		input_z /= input_mag;
		input_mag = 1.0f;
	}
	g_game.player.physics.velocity.x = lerpf(g_game.player.physics.velocity.x, input_x * 4.4f, 0.18f);
	g_game.player.physics.velocity.z = lerpf(g_game.player.physics.velocity.z, input_z * 4.4f, 0.18f);
	if (input_mag > 0.18f) {
		if (fabsf(input_x) >= fabsf(input_z)) {
			g_game.player.facing_angle = input_x < 0.0f ? 1 : 2;
		} else {
			g_game.player.facing_angle = input_z < 0.0f ? 3 : 0;
		}
	}

	if (k_down & KEY_A) trigger_move();
	if (k_down & KEY_X) refine_at_shrine();
	if (k_down & KEY_Y) {
		g_game.player.selected_move = (g_game.player.selected_move + 1) % BANGO_MOVE_COUNT;
		set_status("Cycled move catalog entry.");
	}
	if (k_down & KEY_SELECT) interact_wildlife_nearby();
	if (k_down & KEY_L) spend_attribute_point((g_game.selected_skill + ATTR_VIGOR) % ATTR_COUNT);
	if (k_down & KEY_R) unlock_next_world();
	if (k_down & KEY_DUP) g_game.selected_skill = (g_game.selected_skill + BANGO_SKILL_NODE_COUNT - 1) % BANGO_SKILL_NODE_COUNT;
	if (k_down & KEY_DDOWN) g_game.selected_skill = (g_game.selected_skill + 1) % BANGO_SKILL_NODE_COUNT;
	if (k_down & KEY_DLEFT && g_game.current_world > 0) {
		g_game.current_world -= 1;
		load_world_runtime(g_game.current_world);
		set_status("Shifted route toward an earlier district.");
	}
	if (k_down & KEY_DRIGHT && g_game.current_world + 1 < BANGO_WORLD_COUNT && g_game.worlds[g_game.current_world + 1].unlocked) {
		g_game.current_world += 1;
		load_world_runtime(g_game.current_world);
		set_status("Shifted route toward a deeper district.");
	}
	if ((k_down & KEY_B) && g_game.player.stamina >= 8.0f) {
		float dodge_dx = 0.0f;
		float dodge_dz = 0.0f;
		g_game.player.stamina -= 8.0f;
		switch (g_game.player.facing_angle) {
		case 1: dodge_dx = -1.0f; break;
		case 2: dodge_dx = 1.0f; break;
		case 3: dodge_dz = -1.0f; break;
		default: dodge_dz = 1.0f; break;
		}
		g_game.player.physics.velocity.x += dodge_dx * 5.0f;
		g_game.player.physics.velocity.z += dodge_dz * 5.0f;
		g_game.player.physics.velocity.y += 1.0f;
		g_game.player.stats.dodges_performed += 1;
		set_status("Feather-ward sidestep.");
	}

	if (g_game.player.attack_cooldown > 0) g_game.player.attack_cooldown -= 1;
	if (g_game.player.invulnerability > 0) g_game.player.invulnerability -= 1;
	g_game.player.stamina = clampf(g_game.player.stamina + 0.26f, 0.0f, g_game.player.max_stamina);
	g_game.player.magic = clampf(g_game.player.magic + 0.09f, 0.0f, g_game.player.max_magic);
	integrate_body(&g_game.player.physics, dt);
	update_enemy_ai(dt);
	update_wildlife(dt);
	track_distance();
	update_xp_rates();
	distribute_xp(dt);
	if ((g_game.frame_counter % 45u) == 0u) {
		update_relationships();
	}
	update_character_rig(&g_game.bango_rig_state, g_game.player.physics.position, g_game.player.facing_angle, dt * 1000.0f, input_mag > 0.16f);
	update_character_rig(&g_game.patoot_rig_state, vec3_add(g_game.player.physics.position, vec3_make(0.55f, 0.45f, -0.35f)), (g_game.player.facing_angle + 1) % 4, dt * 1000.0f, input_mag > 0.16f);
	g_game.camera_yaw = lerpf(g_game.camera_yaw, ((float)g_game.player.facing_angle - 1.5f) * 0.18f, 0.05f);
	g_game.camera_distance = 7.8f - g_game.worlds[g_game.current_world].verticality * 0.7f;
	g_game.camera_height = 3.7f + g_game.worlds[g_game.current_world].verticality * 0.6f;
	if (g_game.message_timer > 0) {
		g_game.message_timer -= 1;
	}
}

static ScreenPoint project_world_point(Vec3 world, float eye_shift)
{
	Vec3 camera = vec3_make(
		g_game.player.physics.position.x - sinf(g_game.camera_yaw) * g_game.camera_distance + eye_shift * 0.18f,
		g_game.player.physics.position.y + g_game.camera_height,
		g_game.player.physics.position.z - cosf(g_game.camera_yaw) * g_game.camera_distance);
	Vec3 rel = vec3_sub(world, camera);
	float sin_yaw = sinf(g_game.camera_yaw);
	float cos_yaw = cosf(g_game.camera_yaw);
	float view_x = rel.x * cos_yaw - rel.z * sin_yaw;
	float view_z = rel.x * sin_yaw + rel.z * cos_yaw;
	ScreenPoint point;
	point.visible = view_z > 0.2f;
	point.depth = view_z;
	point.x = 200.0f + (view_x / (view_z + 0.001f)) * 160.0f;
	point.y = 122.0f - (rel.y / (view_z + 0.001f)) * 120.0f;
	return point;
}

static void draw_landscape_eye(float eye_shift)
{
	int z;
	Vec3 light_dir = vec3_normalize(vec3_make(-0.35f, 0.82f, -0.44f));
	WorldNode *world = &g_game.worlds[g_game.current_world];
	for (z = g_game.landscape.height - 2; z >= 0; --z) {
		int x;
		for (x = 0; x < g_game.landscape.width - 1; ++x) {
			int idx00 = z * g_game.landscape.width + x;
			int idx10 = z * g_game.landscape.width + x + 1;
			int idx01 = (z + 1) * g_game.landscape.width + x;
			int idx11 = (z + 1) * g_game.landscape.width + x + 1;
			Vec3 p00 = vec3_make(g_game.landscape.origin_x + (float)x * g_game.landscape.cell_size, g_game.landscape.heights[idx00], g_game.landscape.origin_z + (float)z * g_game.landscape.cell_size);
			Vec3 p10 = vec3_make(g_game.landscape.origin_x + (float)(x + 1) * g_game.landscape.cell_size, g_game.landscape.heights[idx10], g_game.landscape.origin_z + (float)z * g_game.landscape.cell_size);
			Vec3 p01 = vec3_make(g_game.landscape.origin_x + (float)x * g_game.landscape.cell_size, g_game.landscape.heights[idx01], g_game.landscape.origin_z + (float)(z + 1) * g_game.landscape.cell_size);
			Vec3 p11 = vec3_make(g_game.landscape.origin_x + (float)(x + 1) * g_game.landscape.cell_size, g_game.landscape.heights[idx11], g_game.landscape.origin_z + (float)(z + 1) * g_game.landscape.cell_size);
			const RuntimeLandscapeTileDef *tile = get_landscape_tile_def(g_game.landscape.tile_indices[idx00]);
			Vec3 edge_a = vec3_sub(p10, p00);
			Vec3 edge_b = vec3_sub(p01, p00);
			Vec3 normal = vec3_normalize(vec3_cross(edge_a, edge_b));
			float diffuse = clampf(vec3_dot(normal, light_dir), 0.12f, 1.0f);
			float ambient = 0.54f - world->horror_pressure * 0.08f;
			float shade = clampf(ambient + diffuse * 0.72f, 0.18f, 1.30f);
			for (int sub_z = 0; sub_z < BANGO_TERRAIN_UV_SUBDIV; ++sub_z) {
				for (int sub_x = 0; sub_x < BANGO_TERRAIN_UV_SUBDIV; ++sub_x) {
					float u0 = (float)sub_x / (float)BANGO_TERRAIN_UV_SUBDIV;
					float u1 = (float)(sub_x + 1) / (float)BANGO_TERRAIN_UV_SUBDIV;
					float v0 = (float)sub_z / (float)BANGO_TERRAIN_UV_SUBDIV;
					float v1 = (float)(sub_z + 1) / (float)BANGO_TERRAIN_UV_SUBDIV;
					float relief_scale = 0.22f + tile->relief_strength * 0.18f;
					Vec3 q00 = vec3_make(
						lerpf(p00.x, p10.x, u0),
						lerpf(lerpf(p00.y, p10.y, u0), lerpf(p01.y, p11.y, u0), v0),
						lerpf(p00.z, p01.z, v0));
					Vec3 q10 = vec3_make(
						lerpf(p00.x, p10.x, u1),
						lerpf(lerpf(p00.y, p10.y, u1), lerpf(p01.y, p11.y, u1), v0),
						lerpf(p00.z, p01.z, v0));
					Vec3 q01 = vec3_make(
						lerpf(p00.x, p10.x, u0),
						lerpf(lerpf(p00.y, p10.y, u0), lerpf(p01.y, p11.y, u0), v1),
						lerpf(p00.z, p01.z, v1));
					Vec3 q11 = vec3_make(
						lerpf(p00.x, p10.x, u1),
						lerpf(lerpf(p00.y, p10.y, u1), lerpf(p01.y, p11.y, u1), v1),
						lerpf(p00.z, p01.z, v1));
					q00.y += (sample_landscape_tile_height(tile, u0, v0) - 0.5f) * relief_scale;
					q10.y += (sample_landscape_tile_height(tile, u1, v0) - 0.5f) * relief_scale;
					q01.y += (sample_landscape_tile_height(tile, u0, v1) - 0.5f) * relief_scale;
					q11.y += (sample_landscape_tile_height(tile, u1, v1) - 0.5f) * relief_scale;
					ScreenPoint s00 = project_world_point(q00, eye_shift);
					ScreenPoint s10 = project_world_point(q10, eye_shift);
					ScreenPoint s01 = project_world_point(q01, eye_shift);
					ScreenPoint s11 = project_world_point(q11, eye_shift);
					u32 c00 = sample_landscape_tile_color(tile, u0, v0, shade, world->horror_pressure);
					u32 c10 = sample_landscape_tile_color(tile, u1, v0, shade, world->horror_pressure);
					u32 c01 = sample_landscape_tile_color(tile, u0, v1, shade, world->horror_pressure);
					u32 c11 = sample_landscape_tile_color(tile, u1, v1, shade, world->horror_pressure);
					u32 edge_color = C2D_Color32(18, 16, 26, 80 + (u8)clampf(tile->relief_strength * 90.0f, 0.0f, 90.0f));
					if (!s00.visible || !s10.visible || !s01.visible || !s11.visible) {
						continue;
					}
					C2D_DrawTriangle(s00.x, s00.y, c00, s10.x, s10.y, c10, s11.x, s11.y, c11, 0.1f);
					C2D_DrawTriangle(s00.x, s00.y, c00, s11.x, s11.y, c11, s01.x, s01.y, c01, 0.1f);
					C2D_DrawLine(s00.x, s00.y, edge_color, s10.x, s10.y, edge_color, 0.8f, 0.08f);
					C2D_DrawLine(s10.x, s10.y, edge_color, s11.x, s11.y, edge_color, 0.8f, 0.08f);
					C2D_DrawLine(s11.x, s11.y, edge_color, s01.x, s01.y, edge_color, 0.8f, 0.08f);
					C2D_DrawLine(s01.x, s01.y, edge_color, s00.x, s00.y, edge_color, 0.8f, 0.08f);
				}
			}
		}
	}
}

static void draw_skeletal_overlay(const CharacterRigState *state, float eye_shift, u32 color)
{
	int i;
	if (!state->rig) {
		return;
	}
	for (i = 0; i < state->rig->bone_count && i < BANGO_MAX_RUNTIME_BONES; ++i) {
		ScreenPoint point = project_world_point(state->bones[i].position, eye_shift);
		if (!point.visible) {
			continue;
		}
		C2D_DrawCircleSolid(point.x, point.y, 0.46f, 2.0f + clampf(8.0f / (point.depth + 1.0f), 0.0f, 2.0f), color);
		if (state->rig->bones[i].parent_index >= 0 && state->rig->bones[i].parent_index < state->rig->bone_count) {
			ScreenPoint parent = project_world_point(state->bones[state->rig->bones[i].parent_index].position, eye_shift);
			if (parent.visible) {
				C2D_DrawLine(parent.x, parent.y, color, point.x, point.y, color, 1.4f, 0.45f);
			}
		}
	}
}

static void draw_character_billboard(const CharacterRigState *state, float eye_shift, u64 frame_counter)
{
	ScreenPoint root;
	float scale;
	const RuntimeSpriteFrameDef *frame;
	if (!state->pack) {
		return;
	}
	root = project_world_point(state->root_position, eye_shift);
	if (!root.visible) {
		return;
	}
	frame = state->active_pose ? get_angle_frame(state->pack, state->current_angle) : get_loop_frame(state->pack, frame_counter);
	if (!frame) {
		frame = get_angle_frame(state->pack, state->current_angle);
	}
	scale = clampf(22.0f / (root.depth + 0.4f), 1.4f, 5.2f);
	draw_runtime_sprite_frame(frame, root.x, root.y, scale);
	draw_skeletal_overlay(state, eye_shift, C2D_Color32(212, 240, 255, 180));
}

static void draw_environment_object(const EnvironmentObject *object, float eye_shift)
{
	ScreenPoint base = project_world_point(object->position, eye_shift);
	ScreenPoint top = project_world_point(vec3_add(object->position, vec3_make(0.0f, object->half_extents.y * 2.0f, 0.0f)), eye_shift);
	const RuntimeEnvironmentAssetDef *asset = find_runtime_object_asset(object->asset_index);
	if (!object->active || !base.visible || !top.visible) {
		return;
	}
	if (asset && asset->frame) {
		float scale = clampf(16.0f / (base.depth + 0.5f), 1.0f, 4.2f);
		draw_runtime_sprite_frame(asset->frame, base.x, base.y, scale);
	} else {
		float width = clampf(18.0f / (base.depth + 0.5f), 3.0f, 24.0f);
		u32 body_color = object->interactive ? C2D_Color32(196, 168, 92, 220) : C2D_Color32(96, 112, 138, 220);
		C2D_DrawRectSolid(base.x - width * 0.5f, top.y, 0.38f, width, base.y - top.y, body_color);
		C2D_DrawLine(base.x - width * 0.5f, top.y, C2D_Color32(28, 24, 28, 200), base.x + width * 0.5f, top.y, C2D_Color32(28, 24, 28, 200), 1.0f, 0.37f);
	}
}

static void draw_enemy_actor(const EnemyActor *enemy, float eye_shift)
{
	ScreenPoint base = project_world_point(enemy->physics.position, eye_shift);
	ScreenPoint top = project_world_point(vec3_add(enemy->physics.position, vec3_make(0.0f, enemy->physics.half_extents.y * 2.2f, 0.0f)), eye_shift);
	u32 body_color;
	float width;
	float horn;
	if (!enemy->active || enemy->health <= 0.0f || !base.visible || !top.visible) {
		return;
	}
	body_color = enemy->hurt_flash > 0.0f ? C2D_Color32(255, 120, 120, 255) : C2D_Color32(158, 78, 86, 255);
	width = clampf(18.0f / (base.depth + 0.4f), 4.0f, 22.0f);
	horn = width * 0.45f;
	C2D_DrawTriangle(base.x, top.y, body_color, base.x - width * 0.5f, base.y, body_color, base.x + width * 0.5f, base.y, body_color, 0.42f);
	C2D_DrawTriangle(base.x - horn * 0.4f, top.y - horn * 0.7f, body_color, base.x - horn, top.y + horn * 0.1f, body_color, base.x - horn * 0.1f, top.y + horn * 0.3f, body_color, 0.43f);
	C2D_DrawTriangle(base.x + horn * 0.4f, top.y - horn * 0.7f, body_color, base.x + horn, top.y + horn * 0.1f, body_color, base.x + horn * 0.1f, top.y + horn * 0.3f, body_color, 0.43f);
	C2D_DrawCircleSolid(base.x, top.y + width * 0.2f, 0.44f, 2.0f, C2D_Color32(255, 232, 190, 255));
}

static void draw_wildlife_entities(float eye_shift)
{
	int i;
	for (i = 0; i < g_game.wildlife_count; ++i) {
		WildlifeEntity *w = &g_game.wildlife[i];
		ScreenPoint base;
		float sz;
		u32 color;
		if (!w->active) continue;
		base = project_world_point(w->position, eye_shift);
		if (!base.visible) continue;
		sz = clampf(6.0f / (base.depth + 0.3f), 2.0f, 12.0f);
		if (w->is_flora) {
			switch (w->kind) {
			case WILD_FLORA_MOSS: color = C2D_Color32(68, 148, 92, 255); break;
			case WILD_FLORA_FUNGUS: color = C2D_Color32(185, 140, 78, 255); break;
			default: color = C2D_Color32(82, 170, 65, 255); break;
			}
			C2D_DrawCircleSolid(base.x, base.y, 0.38f, sz, color);
			C2D_DrawCircleSolid(base.x - sz * 0.4f, base.y - sz * 0.3f, 0.39f, sz * 0.6f, C2D_Color32(55, 128, 72, 255));
		} else {
			switch (w->kind) {
			case WILD_FAUNA_RAT: color = C2D_Color32(140, 110, 90, 255); break;
			case WILD_FAUNA_MOTH: color = C2D_Color32(220, 195, 160, 255); break;
			default: color = C2D_Color32(50, 50, 58, 255); break;
			}
			C2D_DrawTriangle(base.x, base.y - sz, color, base.x - sz * 0.5f, base.y, color, base.x + sz * 0.5f, base.y, color, 0.38f);
			C2D_DrawCircleSolid(base.x, base.y - sz * 0.6f, 0.39f, 1.5f, C2D_Color32(255, 232, 190, 255));
		}
	}
}

static void render_world_eye(C3D_RenderTarget *target, float eye_shift)
{
	char buffer[192];
	int i;
	WorldNode *world = &g_game.worlds[g_game.current_world];
	C2D_TargetClear(target, C2D_Color32(8, 10, 18, 255));
	C2D_SceneBegin(target);
	C2D_DrawRectSolid(0.0f, 0.0f, 0.0f, 400.0f, 240.0f, C2D_Color32(8, 10, 18, 255));
	C2D_DrawRectSolid(0.0f, 0.0f, 0.0f, 400.0f, 86.0f, C2D_Color32(28, 22, 42, 255));
	C2D_DrawRectSolid(0.0f, 86.0f, 0.0f, 400.0f, 154.0f, C2D_Color32(18, 16, 24, 255));
	draw_landscape_eye(eye_shift);
	for (i = 0; i < g_game.object_count; ++i) {
		draw_environment_object(&g_game.objects[i], eye_shift);
	}
	for (i = 0; i < g_game.enemy_count; ++i) {
		draw_enemy_actor(&g_game.enemies[i], eye_shift);
	}
	draw_wildlife_entities(eye_shift);
	draw_character_billboard(&g_game.bango_rig_state, eye_shift, g_game.frame_counter);
	draw_character_billboard(&g_game.patoot_rig_state, eye_shift, g_game.frame_counter + 9u);

	snprintf(buffer, sizeof(buffer), "Bango-Patoot: %s", world->name);
	draw_text_line(16.0f, 16.0f, 0.55f, C2D_Color32(240, 232, 208, 255), buffer);
	snprintf(buffer, sizeof(buffer), "HP %.0f/%.0f  ST %.0f/%.0f  MA %.0f/%.0f", g_game.player.health, g_game.player.max_health, g_game.player.stamina, g_game.player.max_stamina, g_game.player.magic, g_game.player.max_magic);
	draw_text_line(16.0f, 34.0f, 0.45f, C2D_Color32(214, 214, 226, 255), buffer);
	snprintf(buffer, sizeof(buffer), "Move %d/1000: %s", g_game.player.selected_move + 1, g_game.moves[g_game.player.selected_move].name);
	draw_text_line(16.0f, 52.0f, 0.42f, C2D_Color32(210, 190, 120, 255), buffer);
	snprintf(buffer, sizeof(buffer), "Mesh %dx%d  Enemies %d  Objects %d  Wildlife %d  Horror %.2f", g_game.landscape.width, g_game.landscape.height, g_game.enemy_count, g_game.object_count, g_game.wildlife_count, world->horror_pressure);
	draw_text_line(16.0f, 70.0f, 0.40f, C2D_Color32(196, 180, 214, 255), buffer);
	if (g_game.message_timer > 0) {
		draw_text_line(16.0f, 204.0f, 0.44f, C2D_Color32(255, 214, 164, 255), g_game.status_line);
	}
}

static void render_bottom_screen(void)
{
	char buffer[224];
	SkillNode *node = &g_game.skill_nodes[g_game.selected_skill];
	RelationshipEntity *relationship = &g_game.relationships[g_game.frame_counter % BANGO_RELATIONSHIP_COUNT];
	RigAssetSpec *rig = &g_game.rigs[(g_game.frame_counter / 120u) % BANGO_RIG_COUNT];
	const RuntimeEntityAssetPack *pack = find_runtime_pack(rig->entity_name);
	const RuntimeRigDef *runtime_rig = pack ? pack->rig : NULL;
	int alive_enemies = 0;
	int i;
	for (i = 0; i < g_game.enemy_count; ++i) {
		if (g_game.enemies[i].active && g_game.enemies[i].health > 0.0f) {
			++alive_enemies;
		}
	}
	C2D_TargetClear(g_game.bottom, C2D_Color32(18, 14, 20, 255));
	C2D_SceneBegin(g_game.bottom);
	C2D_DrawRectSolid(286.0f, 16.0f, 0.0f, 102.0f, 96.0f, C2D_Color32(28, 22, 30, 255));
	C2D_DrawRectSolid(290.0f, 20.0f, 0.0f, 94.0f, 88.0f, C2D_Color32(10, 10, 14, 255));

	draw_text_line(12.0f, 12.0f, 0.52f, C2D_Color32(240, 230, 214, 255), "Apiary Reliquary / Combat / Rig Ledger");
	snprintf(buffer, sizeof(buffer), "Act %d  Tula Stage %d  Witch Signal %d  Alive Enemies %d", g_game.quest.act, g_game.quest.tula_stage, g_game.quest.witch_signal, alive_enemies);
	draw_text_line(12.0f, 30.0f, 0.40f, C2D_Color32(214, 214, 226, 255), buffer);
	snprintf(buffer, sizeof(buffer), "Shrine Honey %d  Attribute Pts %d  Skill Pts %d", g_game.shrine.honey, g_game.shrine.attribute_points, g_game.shrine.skill_points);
	draw_text_line(12.0f, 48.0f, 0.40f, C2D_Color32(255, 196, 120, 255), buffer);
	snprintf(buffer, sizeof(buffer), "Selected Skill: %s  Cost %d  Unlocked %s", node->name, node->cost, node->unlocked ? "yes" : "no");
	draw_text_line(12.0f, 66.0f, 0.38f, C2D_Color32(190, 214, 255, 255), buffer);
	snprintf(buffer, sizeof(buffer), "Faction: %s  Aff %.2f  Trust %.2f  Fear %.2f  Rival %.2f", relationship->name, relationship->affinity, relationship->trust, relationship->fear, relationship->rivalry);
	draw_text_line(12.0f, 84.0f, 0.36f, C2D_Color32(204, 184, 222, 255), buffer);
	snprintf(buffer, sizeof(buffer), "Rig: %s  Bones %d  Imported Poses %d  Runtime Bones %d", rig->rig_name, rig->bone_count, rig->imported_pose_count, runtime_rig ? runtime_rig->bone_count : 0);
	draw_text_line(12.0f, 102.0f, 0.36f, C2D_Color32(184, 232, 214, 255), buffer);
	snprintf(buffer, sizeof(buffer), "Landscape tris %d  Object PNG assets %d  Camera yaw %.2f", (g_game.landscape.width - 1) * (g_game.landscape.height - 1) * 2, g_bango_runtime_object_asset_count, g_game.camera_yaw);
	draw_text_line(12.0f, 120.0f, 0.36f, C2D_Color32(232, 226, 174, 255), buffer);
	snprintf(buffer, sizeof(buffer), "Controls: A att  B dodge  X shrine  Y cycle  L attr  R unlock  SEL harvest  DPad nav");
	draw_text_line(12.0f, 138.0f, 0.35f, C2D_Color32(220, 220, 220, 255), buffer);
	snprintf(buffer, sizeof(buffer), "Physics: pos %.1f %.1f %.1f  vel %.1f %.1f %.1f", g_game.player.physics.position.x, g_game.player.physics.position.y, g_game.player.physics.position.z, g_game.player.physics.velocity.x, g_game.player.physics.velocity.y, g_game.player.physics.velocity.z);
	draw_text_line(12.0f, 156.0f, 0.34f, C2D_Color32(220, 220, 220, 255), buffer);
	snprintf(buffer, sizeof(buffer), "Attr: Vig %d Hon %d Tal %d Ner %d Gri %d Arc %d", g_game.player.attributes[0], g_game.player.attributes[1], g_game.player.attributes[2], g_game.player.attributes[3], g_game.player.attributes[4], g_game.player.attributes[5]);
	draw_text_line(12.0f, 174.0f, 0.36f, C2D_Color32(240, 232, 208, 255), buffer);
	snprintf(buffer, sizeof(buffer), "XP: Cmb L%d %.0f  Exp L%d %.0f  Dip L%d %.0f  Arc L%d %.0f  Sur L%d %.0f  Crf L%d %.0f", g_game.player.xp.levels[0], g_game.player.xp.xp[0], g_game.player.xp.levels[1], g_game.player.xp.xp[1], g_game.player.xp.levels[2], g_game.player.xp.xp[2], g_game.player.xp.levels[3], g_game.player.xp.xp[3], g_game.player.xp.levels[4], g_game.player.xp.xp[4], g_game.player.xp.levels[5], g_game.player.xp.xp[5]);
	draw_text_line(12.0f, 192.0f, 0.32f, C2D_Color32(180, 255, 180, 255), buffer);
	snprintf(buffer, sizeof(buffer), "Wildlife %d  Dist %.0f  Kills %d  Dmg %.0f  Dodges %d", g_game.wildlife_count, g_game.player.stats.distance_traveled, g_game.player.stats.enemies_defeated, g_game.player.stats.total_damage_dealt, g_game.player.stats.dodges_performed);
	draw_text_line(12.0f, 206.0f, 0.32f, C2D_Color32(194, 210, 255, 255), buffer);
	if (pack) {
		const RuntimeSpriteFrameDef *preview = get_angle_frame(pack, g_game.player.facing_angle);
		if (preview) {
			draw_runtime_sprite_frame(preview, 336.0f, 90.0f, 2.4f);
		}
	}
}

int main(int argc, char **argv)
{
	(void)argc;
	(void)argv;
	BangoEngineTargetConfig engine_config = bango_engine_target_default_config(BANGO_PLATFORM_N3DS);

	gfxInitDefault();
	gfxSet3D(true);
	C3D_Init(C3D_DEFAULT_CMDBUF_SIZE);
	C2D_Init(C2D_DEFAULT_MAX_OBJECTS);
	C2D_Prepare();
	bango_engine_target_init(&g_engine_target, &engine_config);
	bango_telemetry_bridge_init(&g_telemetry_bridge, BANGO_PLATFORM_N3DS, engine_config.telemetry);

	g_game.top_left = C2D_CreateScreenTarget(GFX_TOP, GFX_LEFT);
	g_game.top_right = C2D_CreateScreenTarget(GFX_TOP, GFX_RIGHT);
	g_game.bottom = C2D_CreateScreenTarget(GFX_BOTTOM, GFX_LEFT);
	g_game.text_buf = C2D_TextBufNew(8192);

	init_game();

	while (aptMainLoop()) {
		circlePosition pad;
		touchPosition touch;
		u32 k_down;
		u32 k_held;
		hidScanInput();
		k_down = hidKeysDown();
		k_held = hidKeysHeld();
		hidCircleRead(&pad);
		hidTouchRead(&touch);
		bango_engine_target_begin_frame(&g_engine_target);
		bango_engine_target_ingest_analog(&g_engine_target, pad.dx / 156.0f, pad.dy / 156.0f, 0.0f, 0.0f);
		bango_engine_target_ingest_buttons(&g_engine_target, k_held, k_down);
		bango_engine_target_ingest_touch(&g_engine_target, (k_held & KEY_TOUCH) != 0, (float)touch.px / 320.0f, (float)touch.py / 240.0f);
		bango_engine_target_ingest_stereo(&g_engine_target, osGet3DSliderState());
		{
			BangoTelemetrySample sample = bango_telemetry_bridge_sample(&g_telemetry_bridge, osGet3DSliderState(), 0.0f);
			bango_engine_target_ingest_telemetry(&g_engine_target, &sample);
		}
		bango_engine_target_update(&g_engine_target, 1.0f / 60.0f);
		if (k_down & KEY_START) {
			break;
		}

		update_game(k_down, pad);
		C2D_TextBufClear(g_game.text_buf);

		C3D_FrameBegin(C3D_FRAME_SYNCDRAW);
		render_world_eye(g_game.top_left, -osGet3DSliderState());
		render_world_eye(g_game.top_right, osGet3DSliderState());
		render_bottom_screen();
		C3D_FrameEnd(0);
	}

	free_relationships();
	free_gpu_sprites();
	bango_telemetry_bridge_shutdown(&g_telemetry_bridge);
	bango_engine_target_shutdown(&g_engine_target);
	C2D_TextBufDelete(g_game.text_buf);
	C2D_Fini();
	C3D_Fini();
	gfxExit();
	return 0;
}