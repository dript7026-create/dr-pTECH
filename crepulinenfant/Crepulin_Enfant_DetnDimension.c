#include <ctype.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CREP_ROOM_COUNT 6
#define CREP_TOOL_COUNT 9
#define CREP_THREAT_COUNT 4
#define VIEWPORT_WIDTH 57
#define VIEWPORT_HEIGHT 18

#define ABILITY_HOUSE_LISTENING  (1u << 0)
#define ABILITY_CURTAIN_CUT      (1u << 1)
#define ABILITY_STOVE_BLESSING   (1u << 2)
#define ABILITY_WARMTH_CARRY     (1u << 3)
#define ABILITY_BLACK_ROAD_REFUSAL (1u << 4)

typedef enum RoomKind {
	ROOM_COURTYARD,
	ROOM_STAIRWELL,
	ROOM_CURTAIN_FLAT,
	ROOM_STOVE_NICHE,
	ROOM_SERVICE_SHAFT,
	ROOM_BLACK_ROAD_VAULT,
} RoomKind;

typedef enum RuleKind {
	RULE_BREAD_OFF_FLOOR,
	RULE_NAME_THE_CORRIDOR,
	RULE_CURTAINS_TIED,
	RULE_CROSS_STEAM_WARM,
	RULE_DO_NOT_ANSWER_AFTER_MIDNIGHT,
	RULE_MIRROR_COVERED,
	RULE_COUNT,
} RuleKind;

typedef enum ToolKind {
	TOOL_CANDLE_STUB,
	TOOL_BOX_CUTTER,
	TOOL_KEY_RING,
	TOOL_IRON_SPOON,
	TOOL_THREAD_SPOOL,
	TOOL_CHALK,
	TOOL_BREAD_SALT,
	TOOL_HAND_BELL,
	TOOL_GLASS_MARBLE,
} ToolKind;

typedef enum ThreatKind {
	THREAT_DOMOV_KEEPER,
	THREAT_KEYHOLE_KIKIMORA,
	THREAT_BLACK_ROAD_CHAUFFEUR,
	THREAT_CREPULIN_BLOOM,
} ThreatKind;

typedef struct ToolState {
	ToolKind kind;
	const char *name;
	int available;
} ToolState;

typedef struct RoomState {
	RoomKind kind;
	const char *name;
	const char *description;
	int rule_respected[RULE_COUNT];
	float corruption;
	float shelter;
	int hidden_route_revealed;
	int visited;
} RoomState;

typedef struct ThreatState {
	ThreatKind kind;
	const char *name;
	float pressure;
	int active;
} ThreatState;

typedef struct EnfantState {
	RoomKind room;
	float dread;
	float warmth;
	float health;
	float depth_focus;
	float camera_sway;
	float ritual_charge;
	unsigned int abilities;
	int children_rescued;
	int hide_streak;
} EnfantState;

typedef struct RoomVisualProfile {
	char sky_char;
	char wall_char;
	char floor_char;
	char accent_char;
	char feature_char;
	char threat_char;
	const char *skybox_name;
	const char *tile_palette_name;
	const char *feature_name;
	const char *camera_name;
} RoomVisualProfile;

typedef struct CrepulinState {
	RoomState rooms[CREP_ROOM_COUNT];
	ThreatState threats[CREP_THREAT_COUNT];
	ToolState tools[CREP_TOOL_COUNT];
	EnfantState enfant;
	float domov_favor;
	float babka_favor;
	int turns;
	int story_gate;
	char status[192];
} CrepulinState;

static CrepulinState g_crepulin;

static const RoomVisualProfile k_room_visuals[CREP_ROOM_COUNT] = {
	{'`', '|', '.', '*', 'L', 'D', "dead sodium courtyard haze", "cracked shared paving", "broken warning lamp", "threshold courtyard lens"},
	{'~', '#', ':', '|', 'N', 'K', "stretched corridor afterglow", "worn stair rib tiles", "named stair mouth", "vanishing stairwell lens"},
	{'"', '!', ';', '/', 'C', 'K', "watchful window smear", "yellowed domestic boards", "looping curtain wall", "curtain-flat pressure lens"},
	{'^', ']', '=', '+', 'S', 'D', "stove warmth plume", "plaster-and-ash floor", "household spirit hearth", "stove niche sanctuary lens"},
	{'~', '/', ':', '=', 'P', 'C', "steam shaft vapor band", "service gantry grating", "pipe rack and valve spine", "maintenance shaft drift lens"},
	{'.', '\\', '_', '=', 'H', 'C', "headlight void horizon", "oil-black vault concrete", "black road headlamps", "vault pursuit lens"},
};

static const char *k_rule_names[RULE_COUNT] = {
	"Keep bread off the floor.",
	"Name the corridor before crossing it.",
	"Do not leave curtains half-tied.",
	"Cross steam rooms warm, not cold.",
	"Do not answer corridor voices after midnight.",
	"Keep the mirror covered when you sleep.",
};

static void set_status(const char *text)
{
	strncpy(g_crepulin.status, text, sizeof(g_crepulin.status) - 1u);
	g_crepulin.status[sizeof(g_crepulin.status) - 1u] = '\0';
}

static float clampf(float value, float minimum, float maximum)
{
	if (value < minimum) return minimum;
	if (value > maximum) return maximum;
	return value;
}

static RoomState *current_room(void)
{
	return &g_crepulin.rooms[g_crepulin.enfant.room];
}

static ThreatState *get_threat(ThreatKind kind)
{
	return &g_crepulin.threats[kind];
}

static ToolState *get_tool(ToolKind kind)
{
	return &g_crepulin.tools[kind];
}

static const RoomVisualProfile *current_room_visual(void)
{
	return &k_room_visuals[g_crepulin.enfant.room];
}

static void print_divider(void)
{
	printf("------------------------------------------------------------\n");
}

static void increase_dread(float amount)
{
	g_crepulin.enfant.dread = clampf(g_crepulin.enfant.dread + amount, 0.0f, 100.0f);
}

static void increase_warmth(float amount)
{
	g_crepulin.enfant.warmth = clampf(g_crepulin.enfant.warmth + amount, 0.0f, 100.0f);
}

static void shift_camera(float depth_delta, float sway_delta, float ritual_delta)
{
	g_crepulin.enfant.depth_focus = clampf(g_crepulin.enfant.depth_focus + depth_delta, 0.0f, 1.0f);
	g_crepulin.enfant.camera_sway = clampf(g_crepulin.enfant.camera_sway + sway_delta, -1.0f, 1.0f);
	g_crepulin.enfant.ritual_charge = clampf(g_crepulin.enfant.ritual_charge + ritual_delta, 0.0f, 1.0f);
}

static void viewport_clear(char buffer[VIEWPORT_HEIGHT][VIEWPORT_WIDTH + 1])
{
	int row;
	int column;
	for (row = 0; row < VIEWPORT_HEIGHT; ++row) {
		for (column = 0; column < VIEWPORT_WIDTH; ++column) {
			buffer[row][column] = ' ';
		}
		buffer[row][VIEWPORT_WIDTH] = '\0';
	}
}

static void viewport_set(char buffer[VIEWPORT_HEIGHT][VIEWPORT_WIDTH + 1], int x, int y, char value)
{
	if (x < 0 || x >= VIEWPORT_WIDTH || y < 0 || y >= VIEWPORT_HEIGHT) {
		return;
	}
	buffer[y][x] = value;
}

static void viewport_fill_span(char buffer[VIEWPORT_HEIGHT][VIEWPORT_WIDTH + 1], int y, int left, int right, char value)
{
	int x;
	if (y < 0 || y >= VIEWPORT_HEIGHT) {
		return;
	}
	if (left < 0) left = 0;
	if (right >= VIEWPORT_WIDTH) right = VIEWPORT_WIDTH - 1;
	for (x = left; x <= right; ++x) {
		buffer[y][x] = value;
	}
}

static void draw_enfant_anchor(char buffer[VIEWPORT_HEIGHT][VIEWPORT_WIDTH + 1], int center_x)
{
	viewport_set(buffer, center_x, VIEWPORT_HEIGHT - 5, 'o');
	viewport_set(buffer, center_x - 1, VIEWPORT_HEIGHT - 4, '/');
	viewport_set(buffer, center_x, VIEWPORT_HEIGHT - 4, '|');
	viewport_set(buffer, center_x + 1, VIEWPORT_HEIGHT - 4, '\\');
	viewport_set(buffer, center_x - 1, VIEWPORT_HEIGHT - 3, '/');
	viewport_set(buffer, center_x + 1, VIEWPORT_HEIGHT - 3, '\\');
}

static void render_room_feature(char buffer[VIEWPORT_HEIGHT][VIEWPORT_WIDTH + 1], const RoomVisualProfile *visual, RoomState *room, int center_x, int horizon)
{
	int row;
	int column;
	switch (room->kind) {
		case ROOM_COURTYARD:
			viewport_set(buffer, center_x, 1, visual->feature_char);
			viewport_set(buffer, center_x, 2, '|');
			viewport_set(buffer, center_x - 1, VIEWPORT_HEIGHT - 2, '~');
			viewport_set(buffer, center_x, VIEWPORT_HEIGHT - 2, '~');
			viewport_set(buffer, center_x + 1, VIEWPORT_HEIGHT - 2, '~');
			break;
		case ROOM_STAIRWELL:
			for (row = horizon - 1; row < horizon + 4; ++row) {
				viewport_set(buffer, center_x - 5, row, visual->feature_char);
				viewport_set(buffer, center_x + 5, row, visual->feature_char);
			}
			viewport_fill_span(buffer, horizon - 1, center_x - 5, center_x + 5, visual->accent_char);
			break;
		case ROOM_CURTAIN_FLAT:
			for (row = 1; row < VIEWPORT_HEIGHT - 4; ++row) {
				viewport_set(buffer, 7, row, visual->feature_char);
				viewport_set(buffer, VIEWPORT_WIDTH - 8, row, visual->feature_char);
			}
			break;
		case ROOM_STOVE_NICHE:
			for (column = center_x - 4; column <= center_x + 4; ++column) {
				viewport_set(buffer, column, horizon + 2, visual->feature_char);
			}
			viewport_set(buffer, center_x, horizon + 1, '*');
			viewport_set(buffer, center_x - 1, horizon + 1, '*');
			viewport_set(buffer, center_x + 1, horizon + 1, '*');
			break;
		case ROOM_SERVICE_SHAFT:
			for (row = 1; row < VIEWPORT_HEIGHT - 2; ++row) {
				viewport_set(buffer, center_x - 11, row, '|');
				viewport_set(buffer, center_x + 11, row, '|');
			}
			viewport_fill_span(buffer, 2, center_x - 11, center_x + 11, visual->feature_char);
			break;
		case ROOM_BLACK_ROAD_VAULT:
			viewport_set(buffer, center_x - 4, horizon - 1, 'O');
			viewport_set(buffer, center_x + 4, horizon - 1, 'O');
			viewport_fill_span(buffer, horizon, center_x - 7, center_x + 7, '_');
			break;
	}
	if (room->hidden_route_revealed) {
		for (row = horizon; row < VIEWPORT_HEIGHT - 1; ++row) {
			viewport_set(buffer, center_x + 8 + (row - horizon) / 3, row, '/');
		}
	}
}

static void render_threat_overlay(char buffer[VIEWPORT_HEIGHT][VIEWPORT_WIDTH + 1], const RoomVisualProfile *visual, int center_x, int horizon)
{
	ThreatState *dominant = get_threat(THREAT_CREPULIN_BLOOM);
	int row = horizon + 2;
	int column = center_x;
	int threat_index;
	for (threat_index = 0; threat_index < CREP_THREAT_COUNT; ++threat_index) {
		if (g_crepulin.threats[threat_index].pressure > dominant->pressure) {
			dominant = &g_crepulin.threats[threat_index];
		}
	}
	if (!dominant->active || dominant->pressure < 0.32f) {
		return;
	}
	if (dominant->kind == THREAT_KEYHOLE_KIKIMORA) {
		column = center_x + 10;
		row = horizon + 1;
	} else if (dominant->kind == THREAT_BLACK_ROAD_CHAUFFEUR) {
		column = center_x;
		row = horizon;
	} else if (dominant->kind == THREAT_DOMOV_KEEPER) {
		column = center_x - 8;
		row = horizon + 2;
	} else {
		column = center_x + 2;
		row = horizon + 3;
	}
	viewport_set(buffer, column, row, visual->threat_char);
	viewport_set(buffer, column - 1, row + 1, '/');
	viewport_set(buffer, column + 1, row + 1, '\\');
	viewport_set(buffer, column, row + 1, '|');
	}

static void render_pseudo3d_viewport(void)
{
	char buffer[VIEWPORT_HEIGHT][VIEWPORT_WIDTH + 1];
	RoomState *room = current_room();
	const RoomVisualProfile *visual = current_room_visual();
	int row;
	int column;
	int center_x = (VIEWPORT_WIDTH / 2) + (int)(g_crepulin.enfant.camera_sway * 6.0f);
	int horizon = 4 + (int)(room->corruption * 5.0f) - (int)(g_crepulin.enfant.warmth / 35.0f);
	if (horizon < 3) horizon = 3;
	if (horizon > VIEWPORT_HEIGHT - 7) horizon = VIEWPORT_HEIGHT - 7;
	viewport_clear(buffer);

	for (row = 0; row < VIEWPORT_HEIGHT; ++row) {
		if (row < horizon) {
			for (column = 0; column < VIEWPORT_WIDTH; ++column) {
				buffer[row][column] = ((column + row) % 11 == 0) ? '.' : visual->sky_char;
			}
		} else {
			float depth = (float)(row - horizon) / (float)(VIEWPORT_HEIGHT - horizon - 1);
			int half_width = 4 + (int)(depth * (((float)VIEWPORT_WIDTH / 2.0f) - 6.0f));
			int left = center_x - half_width;
			int right = center_x + half_width;
			for (column = 0; column < VIEWPORT_WIDTH; ++column) {
				if (column < left || column > right) {
					buffer[row][column] = visual->wall_char;
				} else {
					buffer[row][column] = ((row + column) % 5 == 0) ? visual->accent_char : visual->floor_char;
				}
			}
			viewport_set(buffer, left, row, '/');
			viewport_set(buffer, right, row, '\\');
			if ((row % 2) == 0) {
				viewport_set(buffer, center_x, row, visual->accent_char);
			}
		}
	}

	viewport_fill_span(buffer, horizon, center_x - 9, center_x + 9, '-');
	viewport_fill_span(buffer, horizon + 1, center_x - 13, center_x + 13, '=');
	render_room_feature(buffer, visual, room, center_x, horizon);
	render_threat_overlay(buffer, visual, center_x, horizon);
	draw_enfant_anchor(buffer, center_x);

	print_divider();
	printf("Pseudo3D View: %s | skybox=%s | tiles=%s\n",
		   visual->camera_name,
		   visual->skybox_name,
		   visual->tile_palette_name);
	for (row = 0; row < VIEWPORT_HEIGHT; ++row) {
		printf("|%s|\n", buffer[row]);
	}
	printf("Depth %.2f | Sway %.2f | Ritual %.2f | Feature %s\n",
		   g_crepulin.enfant.depth_focus,
		   g_crepulin.enfant.camera_sway,
		   g_crepulin.enfant.ritual_charge,
		   visual->feature_name);
}

static void init_rooms(void)
{
	g_crepulin.rooms[ROOM_COURTYARD] = (RoomState){
		ROOM_COURTYARD,
		"Courtyard Warning",
		"A cracked shared courtyard beneath dead windows and one broken lamp. Children whisper about the Black Car here.",
		{0}, 0.10f, 0.40f, 0, 1
	};
	g_crepulin.rooms[ROOM_STAIRWELL] = (RoomState){
		ROOM_STAIRWELL,
		"Stairwell Mouth",
		"The stairwell is longer than the building should allow. A corridor hum waits for a true name.",
		{0}, 0.24f, 0.35f, 0, 0
	};
	g_crepulin.rooms[ROOM_CURTAIN_FLAT] = (RoomState){
		ROOM_CURTAIN_FLAT,
		"Curtain Flat 12",
		"A child's room with yellowed drapes, black lining, and a window that watches harder than it should.",
		{0}, 0.42f, 0.20f, 0, 0
	};
	g_crepulin.rooms[ROOM_STOVE_NICHE] = (RoomState){
		ROOM_STOVE_NICHE,
		"Stove Niche",
		"A hidden domestic chamber behind old plaster where a household spirit still expects courtesy.",
		{0}, 0.28f, 0.72f, 0, 0
	};
	g_crepulin.rooms[ROOM_SERVICE_SHAFT] = (RoomState){
		ROOM_SERVICE_SHAFT,
		"Service Shaft",
		"A steam-warm maintenance vein leading toward the under-road. Someone drags tires where no car should fit.",
		{0}, 0.46f, 0.30f, 0, 0
	};
	g_crepulin.rooms[ROOM_BLACK_ROAD_VAULT] = (RoomState){
		ROOM_BLACK_ROAD_VAULT,
		"Black Road Vault",
		"A parking chamber below the district where curtains, headlights, and service markings collapse into one moving law.",
		{0}, 0.66f, 0.10f, 0, 0
	};
}

static void init_threats(void)
{
	g_crepulin.threats[THREAT_DOMOV_KEEPER] = (ThreatState){THREAT_DOMOV_KEEPER, "Domov Keeper", 0.10f, 1};
	g_crepulin.threats[THREAT_KEYHOLE_KIKIMORA] = (ThreatState){THREAT_KEYHOLE_KIKIMORA, "Keyhole Kikimora", 0.18f, 1};
	g_crepulin.threats[THREAT_BLACK_ROAD_CHAUFFEUR] = (ThreatState){THREAT_BLACK_ROAD_CHAUFFEUR, "Chauffeur", 0.08f, 0};
	g_crepulin.threats[THREAT_CREPULIN_BLOOM] = (ThreatState){THREAT_CREPULIN_BLOOM, "Crepulin Bloom", 0.20f, 1};
}

static void init_tools(void)
{
	g_crepulin.tools[TOOL_CANDLE_STUB] = (ToolState){TOOL_CANDLE_STUB, "candle stub", 1};
	g_crepulin.tools[TOOL_BOX_CUTTER] = (ToolState){TOOL_BOX_CUTTER, "box cutter", 1};
	g_crepulin.tools[TOOL_KEY_RING] = (ToolState){TOOL_KEY_RING, "key ring", 1};
	g_crepulin.tools[TOOL_IRON_SPOON] = (ToolState){TOOL_IRON_SPOON, "iron spoon", 1};
	g_crepulin.tools[TOOL_THREAD_SPOOL] = (ToolState){TOOL_THREAD_SPOOL, "thread spool", 1};
	g_crepulin.tools[TOOL_CHALK] = (ToolState){TOOL_CHALK, "chalk", 1};
	g_crepulin.tools[TOOL_BREAD_SALT] = (ToolState){TOOL_BREAD_SALT, "bread and salt packet", 1};
	g_crepulin.tools[TOOL_HAND_BELL] = (ToolState){TOOL_HAND_BELL, "hand bell", 1};
	g_crepulin.tools[TOOL_GLASS_MARBLE] = (ToolState){TOOL_GLASS_MARBLE, "glass marble", 1};
}

static void init_game(void)
{
	memset(&g_crepulin, 0, sizeof(g_crepulin));
	init_rooms();
	init_threats();
	init_tools();
	g_crepulin.enfant.room = ROOM_COURTYARD;
	g_crepulin.enfant.dread = 12.0f;
	g_crepulin.enfant.warmth = 18.0f;
	g_crepulin.enfant.health = 100.0f;
	g_crepulin.enfant.depth_focus = 0.18f;
	g_crepulin.enfant.camera_sway = 0.0f;
	g_crepulin.enfant.ritual_charge = 0.05f;
	g_crepulin.domov_favor = 0.20f;
	g_crepulin.babka_favor = 0.00f;
	g_crepulin.story_gate = 0;
	set_status("A blackout swallows Block Nine. Someone is missing.");
}

static void print_inventory(void)
{
	int i;
	printf("Tools: ");
	for (i = 0; i < CREP_TOOL_COUNT; ++i) {
		if (g_crepulin.tools[i].available) {
			printf("%s; ", g_crepulin.tools[i].name);
		}
	}
	printf("\n");
}

static void print_room_rules(void)
{
	int i;
	printf("Room Rules: ");
	for (i = 0; i < RULE_COUNT; ++i) {
		printf("[%c] %s ", current_room()->rule_respected[i] ? 'x' : ' ', k_rule_names[i]);
	}
	printf("\n");
}

static void print_help(void)
{
	print_divider();
	printf("Commands:\n");
	printf("  s = status\n");
	printf("  l = listen\n");
	printf("  h = hide\n");
	printf("  o = offer bread and salt\n");
	printf("  c = cut curtains\n");
	printf("  w = light candle / carry warmth\n");
	printf("  b = bargain with Babka / assert refusal\n");
	printf("  m = move forward\n");
	printf("  q = quit\n");
}

static void print_state(void)
{
	RoomState *room = current_room();
	printf("\n");
	render_pseudo3d_viewport();
	print_divider();
	printf("Room: %s\n", room->name);
	printf("%s\n", room->description);
	printf("Dread %.1f | Warmth %.1f | Health %.1f | Domov Favor %.2f | Babka Favor %.2f\n",
		   g_crepulin.enfant.dread, g_crepulin.enfant.warmth, g_crepulin.enfant.health,
		   g_crepulin.domov_favor, g_crepulin.babka_favor);
	printf("Abilities: listening=%s curtain_cut=%s stove_blessing=%s warmth_carry=%s black_road_refusal=%s\n",
		   (g_crepulin.enfant.abilities & ABILITY_HOUSE_LISTENING) ? "yes" : "no",
		   (g_crepulin.enfant.abilities & ABILITY_CURTAIN_CUT) ? "yes" : "no",
		   (g_crepulin.enfant.abilities & ABILITY_STOVE_BLESSING) ? "yes" : "no",
		   (g_crepulin.enfant.abilities & ABILITY_WARMTH_CARRY) ? "yes" : "no",
		   (g_crepulin.enfant.abilities & ABILITY_BLACK_ROAD_REFUSAL) ? "yes" : "no");
	printf("Threat Pressure: Domov %.2f | Kikimora %.2f | Chauffeur %.2f | Bloom %.2f\n",
		   get_threat(THREAT_DOMOV_KEEPER)->pressure,
		   get_threat(THREAT_KEYHOLE_KIKIMORA)->pressure,
		   get_threat(THREAT_BLACK_ROAD_CHAUFFEUR)->pressure,
		   get_threat(THREAT_CREPULIN_BLOOM)->pressure);
	printf("Render Bindings: skybox=%s | tile_palette=%s | camera=%s\n",
		   current_room_visual()->skybox_name,
		   current_room_visual()->tile_palette_name,
		   current_room_visual()->camera_name);
	print_room_rules();
	printf("Status: %s\n", g_crepulin.status);
	printf("Reference sprites: detn_idletoward_sprite.clip, detn_walktoward_sprite.clip\n");
	print_inventory();
}

static void update_room_rule(RuleKind rule, int respected)
{
	RoomState *room = current_room();
	room->rule_respected[rule] = respected;
}

static void listen_in_room(void)
{
	RoomState *room = current_room();
	if (room->kind == ROOM_STAIRWELL) {
		g_crepulin.enfant.abilities |= ABILITY_HOUSE_LISTENING;
		room->hidden_route_revealed = 1;
		increase_dread(4.0f);
		shift_camera(0.12f, -0.08f, 0.10f);
		set_status("Enfant hears the corridor's true cadence. The stairwell accepts a spoken name.");
		return;
	}
	if (room->kind == ROOM_CURTAIN_FLAT) {
		get_threat(THREAT_KEYHOLE_KIKIMORA)->pressure = clampf(get_threat(THREAT_KEYHOLE_KIKIMORA)->pressure + 0.10f, 0.0f, 1.0f);
		increase_dread(6.0f);
		shift_camera(0.08f, 0.15f, 0.06f);
		set_status("Something breathes behind the drapes. Listening too long feeds the Kikimora.");
		return;
	}
	if (room->kind == ROOM_SERVICE_SHAFT) {
		get_threat(THREAT_BLACK_ROAD_CHAUFFEUR)->active = 1;
		get_threat(THREAT_BLACK_ROAD_CHAUFFEUR)->pressure = clampf(get_threat(THREAT_BLACK_ROAD_CHAUFFEUR)->pressure + 0.15f, 0.0f, 1.0f);
		shift_camera(0.10f, 0.10f, 0.08f);
		set_status("A distant engine purr answers through the pipes. The Black Road has found the district.");
		return;
	}
	increase_dread(2.0f);
	shift_camera(0.04f, 0.02f, 0.02f);
	set_status("The building answers in knocks, steam, and old plaster settling.");
}

static void hide_in_room(void)
{
	RoomState *room = current_room();
	float shelter = room->shelter + g_crepulin.domov_favor * 0.15f - get_threat(THREAT_KEYHOLE_KIKIMORA)->pressure * 0.10f;
	if (shelter > 0.45f) {
		g_crepulin.enfant.hide_streak += 1;
		increase_dread(-8.0f);
		shift_camera(-0.12f, -0.10f, 0.04f);
		set_status("Enfant holds still until the room remembers how to be ordinary.");
	} else {
		g_crepulin.enfant.hide_streak = 0;
		increase_dread(9.0f);
		shift_camera(0.06f, 0.14f, -0.02f);
		set_status("The hiding place is wrong for this threat. Something notices the breath under it.");
	}
}

static void offer_bread_and_salt(void)
{
	ToolState *bread_salt = get_tool(TOOL_BREAD_SALT);
	RoomState *room = current_room();
	if (!bread_salt->available) {
		set_status("The bread and salt offering has already been used.");
		return;
	}
	bread_salt->available = 0;
	g_crepulin.domov_favor = clampf(g_crepulin.domov_favor + 0.35f, 0.0f, 1.0f);
	update_room_rule(RULE_BREAD_OFF_FLOOR, 1);
	shift_camera(-0.05f, 0.0f, 0.18f);
	if (room->kind == ROOM_STOVE_NICHE) {
		g_crepulin.enfant.abilities |= ABILITY_STOVE_BLESSING;
		increase_warmth(18.0f);
		set_status("The Domov Keeper accepts the offering and blesses the stove path.");
	} else {
		increase_warmth(8.0f);
		set_status("The domestic air shifts. Something old and house-bound is less hostile now.");
	}
}

static void cut_curtains(void)
{
	ToolState *box_cutter = get_tool(TOOL_BOX_CUTTER);
	if (!box_cutter->available) {
		set_status("No cutting edge remains in Enfant's pocket.");
		return;
	}
	if (g_crepulin.enfant.room != ROOM_CURTAIN_FLAT) {
		increase_dread(4.0f);
		set_status("There is nothing here that should be cut open yet.");
		return;
	}
	g_crepulin.enfant.abilities |= ABILITY_CURTAIN_CUT;
	update_room_rule(RULE_CURTAINS_TIED, 1);
	current_room()->hidden_route_revealed = 1;
	get_threat(THREAT_KEYHOLE_KIKIMORA)->pressure = clampf(get_threat(THREAT_KEYHOLE_KIKIMORA)->pressure - 0.12f, 0.0f, 1.0f);
	shift_camera(0.16f, -0.20f, 0.12f);
	set_status("Enfant cuts the drapes in the right order. The looping room finally breaks open.");
}

static void light_candle(void)
{
	ToolState *candle = get_tool(TOOL_CANDLE_STUB);
	if (!candle->available) {
		set_status("The candle stub is already spent.");
		return;
	}
	candle->available = 0;
	increase_warmth(24.0f);
	shift_camera(-0.03f, 0.0f, 0.14f);
	if (g_crepulin.enfant.room == ROOM_STOVE_NICHE || g_crepulin.enfant.room == ROOM_SERVICE_SHAFT) {
		g_crepulin.enfant.abilities |= ABILITY_WARMTH_CARRY;
		update_room_rule(RULE_CROSS_STEAM_WARM, 1);
		set_status("Warmth takes hold in Enfant's hands. Steam passages no longer reject the body outright.");
	} else {
		set_status("The candle makes the air feel inhabited rather than empty.");
	}
}

static void bargain_or_refuse(void)
{
	if (g_crepulin.enfant.room == ROOM_SERVICE_SHAFT) {
		if ((g_crepulin.enfant.abilities & ABILITY_WARMTH_CARRY) == 0u) {
			increase_dread(10.0f);
			shift_camera(0.10f, 0.18f, -0.05f);
			set_status("Babka Kuroles laughs from the steam. Cold children do not pass under roads alive.");
			return;
		}
		g_crepulin.babka_favor = clampf(g_crepulin.babka_favor + 0.30f, 0.0f, 1.0f);
		g_crepulin.enfant.abilities |= ABILITY_BLACK_ROAD_REFUSAL;
		shift_camera(0.08f, -0.06f, 0.20f);
		set_status("Babka Kuroles trades a refusal phrase for one future favor. Enfant can now deny the Black Road's invitation.");
		return;
	}
	if (g_crepulin.enfant.room == ROOM_BLACK_ROAD_VAULT) {
		if ((g_crepulin.enfant.abilities & ABILITY_BLACK_ROAD_REFUSAL) == 0u) {
			increase_dread(18.0f);
			shift_camera(0.14f, 0.22f, -0.08f);
			set_status("The Chauffeur hears fear instead of refusal. The engine comes closer.");
			return;
		}
		g_crepulin.enfant.children_rescued = 1;
		get_threat(THREAT_BLACK_ROAD_CHAUFFEUR)->pressure = 0.0f;
		shift_camera(0.20f, -0.22f, 0.30f);
		set_status("Enfant speaks the refusal. Headlights dim, curtains slacken, and the road releases one stolen child-route.");
		return;
	}
	set_status("No bargain presents itself here.");
}

static int can_move_forward(void)
{
	switch (g_crepulin.enfant.room) {
		case ROOM_COURTYARD:
			return 1;
		case ROOM_STAIRWELL:
			return (g_crepulin.enfant.abilities & ABILITY_HOUSE_LISTENING) != 0u;
		case ROOM_CURTAIN_FLAT:
			return (g_crepulin.enfant.abilities & ABILITY_CURTAIN_CUT) != 0u;
		case ROOM_STOVE_NICHE:
			return (g_crepulin.enfant.abilities & ABILITY_STOVE_BLESSING) != 0u;
		case ROOM_SERVICE_SHAFT:
			return (g_crepulin.enfant.abilities & ABILITY_BLACK_ROAD_REFUSAL) != 0u;
		case ROOM_BLACK_ROAD_VAULT:
		default:
			return 0;
	}
}

static void move_forward(void)
{
	if (!can_move_forward()) {
		increase_dread(5.0f);
		set_status("The next threshold refuses Enfant. A room rule or bargain is still unresolved.");
		return;
	}
	if (g_crepulin.enfant.room + 1 >= CREP_ROOM_COUNT) {
		set_status("There is no further room beyond the current threshold.");
		return;
	}
	g_crepulin.enfant.room = (RoomKind)(g_crepulin.enfant.room + 1);
	current_room()->visited = 1;
	increase_dread(3.0f + current_room()->corruption * 8.0f);
	g_crepulin.enfant.depth_focus = 0.14f + current_room()->corruption * 0.18f;
	g_crepulin.enfant.camera_sway = current_room()->corruption * 0.10f;
	g_crepulin.enfant.ritual_charge = clampf(g_crepulin.enfant.ritual_charge + 0.06f, 0.0f, 1.0f);
	if (g_crepulin.enfant.room == ROOM_BLACK_ROAD_VAULT) {
		get_threat(THREAT_BLACK_ROAD_CHAUFFEUR)->active = 1;
		get_threat(THREAT_BLACK_ROAD_CHAUFFEUR)->pressure = 0.72f;
		set_status("Enfant reaches the Black Road Vault. The Chauffeur is already waiting.");
	} else {
		set_status(current_room()->description);
	}
}

static void update_world(void)
{
	ThreatState *kikimora = get_threat(THREAT_KEYHOLE_KIKIMORA);
	ThreatState *chauffeur = get_threat(THREAT_BLACK_ROAD_CHAUFFEUR);
	ThreatState *bloom = get_threat(THREAT_CREPULIN_BLOOM);

	g_crepulin.turns += 1;
	increase_dread(current_room()->corruption * 1.8f);
	increase_warmth(-1.5f);
	g_crepulin.enfant.camera_sway *= 0.72f;
	g_crepulin.enfant.depth_focus = clampf(g_crepulin.enfant.depth_focus + 0.02f + current_room()->corruption * 0.03f, 0.0f, 1.0f);
	g_crepulin.enfant.ritual_charge = clampf(g_crepulin.enfant.ritual_charge + current_room()->corruption * 0.04f - g_crepulin.domov_favor * 0.02f, 0.0f, 1.0f);

	if (g_crepulin.enfant.room == ROOM_CURTAIN_FLAT && (g_crepulin.enfant.abilities & ABILITY_CURTAIN_CUT) == 0u) {
		kikimora->pressure = clampf(kikimora->pressure + 0.08f, 0.0f, 1.0f);
	}
	if (g_crepulin.enfant.room == ROOM_SERVICE_SHAFT || g_crepulin.enfant.room == ROOM_BLACK_ROAD_VAULT) {
		chauffeur->active = 1;
		chauffeur->pressure = clampf(chauffeur->pressure + 0.05f, 0.0f, 1.0f);
	}
	bloom->pressure = clampf(bloom->pressure + current_room()->corruption * 0.03f, 0.0f, 1.0f);

	if (g_crepulin.enfant.warmth < 5.0f && current_room()->kind == ROOM_SERVICE_SHAFT) {
		increase_dread(6.0f);
		shift_camera(0.06f, 0.08f, -0.03f);
		set_status("Cold steam bites through Enfant's clothes. The shaft wants a warmer body than this.");
	}
}

static int game_finished(void)
{
	if (g_crepulin.enfant.children_rescued > 0) {
		print_divider();
		printf("Ending: Enfant pulls one child-route back from the Black Road.\n");
		printf("The district is not healed, but it is finally named honestly.\n");
		return 1;
	}
	if (g_crepulin.enfant.dread >= 100.0f) {
		print_divider();
		printf("Failure: Dread overwhelms Enfant. The DetnDimension closes like a throat.\n");
		return 1;
	}
	return 0;
}

int main(void)
{
	char command[32];

	init_game();
	print_help();
	print_state();

	while (!game_finished()) {
		printf("\nCommand> ");
		if (!fgets(command, sizeof(command), stdin)) {
			break;
		}

		switch (tolower((unsigned char)command[0])) {
			case 's':
				print_state();
				continue;
			case 'l':
				listen_in_room();
				break;
			case 'h':
				hide_in_room();
				break;
			case 'o':
				offer_bread_and_salt();
				break;
			case 'c':
				cut_curtains();
				break;
			case 'w':
				light_candle();
				break;
			case 'b':
				bargain_or_refuse();
				break;
			case 'm':
				move_forward();
				break;
			case 'q':
				printf("Exiting Crepulin prototype.\n");
				return 0;
			default:
				set_status("Unknown command. Use s, l, h, o, c, w, b, m, or q.");
				break;
		}

		update_world();
		print_state();
	}

	return 0;
}
