/* ccp_gameplay.h — CCP Gameplay VM types, opcodes, and runtime structures
 *
 * Maps Clip Studio Paint visual scripting concepts to a bytecode VM:
 *   SymbolObject  -> EntityDef  (sprites with timeline animation)
 *   VisualScript  -> ScriptDef  (bytecode event handlers)
 *   HitDetection  -> HitboxDef  (collision shapes per entity)
 *   SceneSequence -> SceneDef   (entity/script activation groups)
 *   ButtonObject  -> Input      (controller button -> gameplay action)
 *
 * LT and RT are RESERVED for page navigation in both .ccp and .ecbmps
 * viewers and are NOT exposed to gameplay scripts.
 */

#ifndef CCP_GAMEPLAY_H
#define CCP_GAMEPLAY_H

#include <stdint.h>
#include <string.h>

/* Gameplay section file magic */
#define GPLY_MAGIC    0x594C5047u  /* "GPLY" little-endian */
#define GPLY_VERSION  1u

/* ================================================================== */
/*  VM Opcodes                                                        */
/* ================================================================== */
enum {
    /* Stack manipulation */
    OP_NOP          = 0x00,
    OP_PUSH_INT     = 0x01,  /* +int32 */
    OP_PUSH_FLOAT   = 0x02,  /* +float32 */
    OP_PUSH_STR     = 0x03,  /* +uint16 string_table_offset */
    OP_POP          = 0x04,
    OP_DUP          = 0x05,

    /* Variables */
    OP_SET_VAR      = 0x10,  /* +uint16 var_id; pop value */
    OP_GET_VAR      = 0x11,  /* +uint16 var_id; push value */

    /* Control flow */
    OP_JMP          = 0x20,  /* +int32 offset (relative to PC after operand) */
    OP_JMP_IF       = 0x21,  /* +int32 offset; pop, jump if nonzero */
    OP_JMP_IFNOT    = 0x22,  /* +int32 offset; pop, jump if zero */
    OP_CALL         = 0x23,  /* +uint16 script_id */
    OP_RET          = 0x24,
    OP_HALT         = 0xFF,

    /* Entity operations (from CSP SymbolObject) */
    OP_ENT_SPAWN    = 0x30,  /* +uint16 entity_def_id -> push instance_id */
    OP_ENT_DESTROY  = 0x31,  /* pop(instance_id) */
    OP_ENT_MOVE     = 0x32,  /* pop(instance_id, dx, dy) — relative move */
    OP_ENT_SET_POS  = 0x33,  /* pop(instance_id, x, y) — absolute position */
    OP_ENT_GET_POS  = 0x34,  /* pop(instance_id) -> push(x, y) */
    OP_ENT_SET_ANIM = 0x35,  /* pop(instance_id, anim_id) */
    OP_ENT_SET_FRAME= 0x36,  /* pop(instance_id, frame_idx) */
    OP_ENT_SHOW     = 0x37,  /* pop(instance_id) */
    OP_ENT_HIDE     = 0x38,  /* pop(instance_id) */

    /* Collision / hit detection (from CSP HitDetection) */
    OP_HIT_TEST     = 0x40,  /* pop(inst_a, inst_b) -> push(bool) */
    OP_POINT_TEST   = 0x41,  /* pop(inst_id, x, y) -> push(bool) */

    /* Page / scene navigation */
    OP_GOTO_PAGE    = 0x50,  /* pop(page_num) */
    OP_SET_SCENE    = 0x51,  /* +uint16 scene_id */
    OP_PLAY_ANIM    = 0x52,  /* +uint16 anim_name_str_offset */

    /* Controller input queries */
    OP_GET_BUTTON   = 0x60,  /* +uint8 button_id -> push(bool) */
    OP_GET_AXIS     = 0x61,  /* +uint8 axis_id -> push(float) */
    OP_GET_DPAD     = 0x62,  /* -> push(uint bitmask: 1=up,2=down,4=left,8=right) */

    /* UI actions */
    OP_SHOW_DIALOGUE= 0x70,  /* +uint16 string_offset */
    OP_SHOW_POPUP   = 0x71,  /* +uint16 string_offset */
    OP_PLAY_SOUND   = 0x72,  /* +uint16 sound_id */

    /* Math/logic (binary: pop 2, push 1; unary: pop 1, push 1) */
    OP_ADD          = 0x80,
    OP_SUB          = 0x81,
    OP_MUL          = 0x82,
    OP_DIV          = 0x83,
    OP_CMP_EQ       = 0x84,
    OP_CMP_LT       = 0x85,
    OP_CMP_GT       = 0x86,
    OP_AND          = 0x87,
    OP_OR           = 0x88,
    OP_NOT          = 0x89   /* unary */
};

/* ================================================================== */
/*  Controller button/axis IDs (maps to XInput)                       */
/*  NOTE: LT/RT are RESERVED for page navigation — not scriptable    */
/* ================================================================== */
enum {
    GPLY_BTN_A = 0,
    GPLY_BTN_B,
    GPLY_BTN_X,
    GPLY_BTN_Y,
    GPLY_BTN_DPAD_UP,
    GPLY_BTN_DPAD_DOWN,
    GPLY_BTN_DPAD_LEFT,
    GPLY_BTN_DPAD_RIGHT,
    GPLY_BTN_START,
    GPLY_BTN_BACK,
    GPLY_BTN_LB,
    GPLY_BTN_RB,
    GPLY_BTN_LSTICK,
    GPLY_BTN_RSTICK,
    GPLY_BTN_COUNT
};

enum {
    GPLY_AXIS_LX = 0,   /* left stick X: -1.0 to 1.0 */
    GPLY_AXIS_LY,        /* left stick Y */
    GPLY_AXIS_RX,        /* right stick X */
    GPLY_AXIS_RY,        /* right stick Y */
    GPLY_AXIS_COUNT
};

/* ================================================================== */
/*  Event types for script bindings                                   */
/*  (from CSP VisualScript + CSPipelineScriptBindingDesc)             */
/* ================================================================== */
enum {
    GPLY_EVT_PAGE_ENTER = 0,   /* fires when page becomes active */
    GPLY_EVT_PAGE_EXIT,
    GPLY_EVT_FRAME_TICK,       /* fires every frame (~16ms) */
    GPLY_EVT_CLICK,            /* mouse/touch on entity hitbox */
    GPLY_EVT_HOVER_ENTER,
    GPLY_EVT_HOVER_EXIT,
    GPLY_EVT_COLLIDE,          /* two entities' hitboxes overlap */
    GPLY_EVT_TRIGGER,          /* timeline trigger frame reached */
    GPLY_EVT_BUTTON_DOWN,      /* controller button pressed */
    GPLY_EVT_BUTTON_UP,
    GPLY_EVT_SCENE_ENTER,      /* scene activated */
    GPLY_EVT_SCENE_EXIT,
    GPLY_EVT_COUNT
};

/* ================================================================== */
/*  Binary format structures (on-disk, packed little-endian)          */
/* ================================================================== */
#pragma pack(push, 1)

typedef struct {
    uint32_t magic;                /* GPLY_MAGIC */
    uint32_t version;              /* GPLY_VERSION */
    uint16_t entity_def_count;
    uint16_t hitbox_def_count;
    uint16_t script_count;
    uint16_t scene_count;
    uint16_t event_binding_count;
    uint16_t variable_count;
    uint32_t string_table_size;
    uint32_t bytecode_size;
} GplyHeader;  /* 28 bytes */

/* Entity definition (from CSP SymbolObject) */
typedef struct {
    uint16_t name_offset;          /* into string table */
    uint16_t sprite_asset_offset;  /* into string table (asset path) */
    int16_t  default_x;
    int16_t  default_y;
    uint16_t width;
    uint16_t height;
    uint16_t timeline_length;      /* animation frame count */
    uint8_t  visible_by_default;
    uint8_t  page;                 /* which page (0xFF = global) */
} GplyEntityDef;  /* 16 bytes */

/* Hitbox definition (from CSP HitDetection / CSPipelineHitboxDesc) */
typedef struct {
    uint16_t entity_def_id;
    uint16_t frame_index;          /* 0xFFFF = all frames */
    int16_t  offset_x;             /* relative to entity pos */
    int16_t  offset_y;
    uint16_t width;
    uint16_t height;
    uint8_t  kind;                 /* 0=solid, 1=trigger, 2=hurtbox, 3=button */
    uint8_t  padding;
} GplyHitboxDef;  /* 14 bytes */

/* Script definition (from CSP VisualScript) */
typedef struct {
    uint16_t name_offset;          /* into string table */
    uint32_t bytecode_offset;      /* offset into bytecode section */
    uint32_t bytecode_length;
} GplyScriptDef;  /* 10 bytes */

/* Scene definition (from CSP SceneSequence) */
typedef struct {
    uint16_t name_offset;          /* into string table */
    uint16_t first_entity;         /* range of entity defs active */
    uint16_t entity_count;
    uint16_t first_binding;        /* range of event bindings active */
    uint16_t binding_count;
    uint8_t  page;
    uint8_t  flags;
} GplySceneDef;  /* 12 bytes */

/* Event binding (wires events to scripts) */
typedef struct {
    uint8_t  event_type;           /* GPLY_EVT_* */
    uint8_t  filter_btn;           /* for BUTTON_DOWN/UP: which button; else 0xFF */
    uint16_t source_entity;        /* entity generating event (0xFFFF = any) */
    uint16_t target_entity;        /* for COLLIDE: other entity; else 0xFFFF */
    uint16_t script_id;            /* script to execute */
    uint8_t  page;                 /* page scope (0xFF = all) */
    uint8_t  padding;
} GplyEventBinding;  /* 10 bytes */

/* Variable definition */
typedef struct {
    uint16_t name_offset;          /* into string table */
    int32_t  initial_value;
} GplyVariableDef;  /* 6 bytes */

#pragma pack(pop)

/* ================================================================== */
/*  Runtime structures (in-memory, viewer-side)                       */
/* ================================================================== */

#define GPLY_MAX_ENTITIES    256
#define GPLY_MAX_INSTANCES   512
#define GPLY_MAX_VARIABLES   256
#define GPLY_MAX_STACK       256
#define GPLY_MAX_CALL_DEPTH  32

/* Runtime entity instance */
typedef struct {
    uint16_t def_id;
    int      active;
    float    x, y;
    int      current_frame;
    int      visible;
    int      anim_playing;
    int      anim_speed;  /* frames per tick */
} GplyEntityInstance;

/* VM value (union for int/float on the stack) */
typedef union {
    int32_t  i;
    float    f;
    uint16_t str_offset;
} GplyValue;

/* VM execution state */
typedef struct {
    /* Loaded gameplay data (points into mmap'd .ccp) */
    const GplyHeader       *header;
    const GplyEntityDef    *entity_defs;
    const GplyHitboxDef    *hitbox_defs;
    const GplyScriptDef    *script_defs;
    const GplySceneDef     *scene_defs;
    const GplyEventBinding *event_bindings;
    const GplyVariableDef  *variable_defs;
    const char             *string_table;
    const uint8_t          *bytecode;

    /* Runtime state */
    GplyEntityInstance instances[GPLY_MAX_INSTANCES];
    int                instance_count;
    GplyValue          variables[GPLY_MAX_VARIABLES];
    int                current_page;
    uint16_t           current_scene;

    /* VM execution registers */
    GplyValue stack[GPLY_MAX_STACK];
    int       sp;
    uint32_t  call_stack[GPLY_MAX_CALL_DEPTH];
    int       csp;
    uint32_t  pc;
    int       running;

    /* Pending page change (set by OP_GOTO_PAGE, consumed by viewer) */
    int       pending_page;

    /* Controller state (updated externally by controller_poll) */
    int   buttons[GPLY_BTN_COUNT];
    int   buttons_prev[GPLY_BTN_COUNT];
    float axes[GPLY_AXIS_COUNT];
    float trigger_left;    /* 0.0-1.0 (for page nav, NOT exposed to scripts) */
    float trigger_right;
} GplyVM;

/* ================================================================== */
/*  API declarations (implemented in ccp_gameplay_vm.c)               */
/* ================================================================== */

/* Initialize VM from gameplay section data (pointer into loaded .ccp) */
int  gply_vm_init(GplyVM *vm, const void *gameplay_data, uint32_t gameplay_size);

/* Reset runtime state (call when switching pages) */
void gply_vm_reset(GplyVM *vm);

/* Fire an event — runs all matching scripts */
void gply_vm_fire_event(GplyVM *vm, int event_type, uint16_t source, uint16_t target);

/* Execute a single script by ID */
void gply_vm_exec_script(GplyVM *vm, uint16_t script_id);

/* Tick — call once per frame for animations, collisions, input edges */
void gply_vm_tick(GplyVM *vm);

/* Set page — fires PAGE_EXIT/PAGE_ENTER, spawns page entities */
void gply_vm_set_page(GplyVM *vm, int page);

/* String lookup in the string table */
const char *gply_vm_string(const GplyVM *vm, uint16_t offset);

/* Variable access */
int  gply_vm_get_var(const GplyVM *vm, uint16_t var_id);
void gply_vm_set_var(GplyVM *vm, uint16_t var_id, int value);

/* Hit testing */
int  gply_hit_test_instances(const GplyVM *vm, int inst_a, int inst_b);
int  gply_hit_test_point(const GplyVM *vm, int inst_id, float px, float py);

#endif /* CCP_GAMEPLAY_H */
