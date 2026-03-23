#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>

/* TxTUR Plugin - Blender Texturing and Surface Mapping Toolkit */

/* Export macro for building a shared library on Windows */
#if defined(_WIN32) || defined(__CYGWIN__)
#  define TXTUR_API __declspec(dllexport)
#else
#  define TXTUR_API
#endif

#define MAX_BRUSHES 12
#define MAX_MAPPINGS 32

/* ============== BRUSH DEFINITIONS ============== */
typedef struct {
    char name[64];
    int brush_id;
    float falloff;
    float strength;
    float radius;
} TextureBrush;

typedef struct {
    TextureBrush brushes[12];
    int brush_count;
} TextureBrushKit;

typedef struct {
    char name[64];
    int mapping_id;
    float depth;
    float detail;
    int pattern_type;
} SurfaceMapping;

typedef struct {
    SurfaceMapping mappings[32];
    int mapping_count;
} SurfaceMappingKit;

/* ============== INTERLINK/NODECRAFT DEFINITIONS ============== */
typedef enum {
    LINKAGE_CHAIN,
    LINKAGE_FIBER,
    LINKAGE_COIL,
    LINKAGE_CABLE,
    LINKAGE_WIRE,
    LINKAGE_MESH,
    LINKAGE_LATTICE,
    LINKAGE_FRAMEWORK
} LinkageType;

typedef struct {
    float x, y, z;
} Vec3;

typedef struct {
    int node_id;
    Vec3 position;
    float scale;
    int connection_count;
} NodePoint;

typedef struct {
    int from_node;
    int to_node;
    LinkageType type;
    float tension;
    float thickness;
} NodeLink;

typedef struct {
    NodePoint* nodes;
    NodeLink* links;
    int node_count;
    int link_count;
    int max_nodes;
    int max_links;
} NodeCraftNetwork;

/* ============== PLUGIN STATE ============== */
typedef struct {
    TextureBrushKit texture_kit;
    SurfaceMappingKit surface_kit;
    NodeCraftNetwork network;
    int active_brush;
    int active_mapping;
    int mode; /* 0=default, 1=texture, 2=surface, 3=nodecraft */
    char blend_filepath[256];
} TxTURPluginState;

/* ============== INITIALIZATION ============== */
TxTURPluginState* txtur_init(void) {
    TxTURPluginState* state = (TxTURPluginState*)malloc(sizeof(TxTURPluginState));
    if (!state) return NULL;

    memset(state, 0, sizeof(TxTURPluginState));
    
    /* Initialize texture brushes */
    state->texture_kit.brush_count = MAX_BRUSHES;
    const char* texture_names[] = {
        "Layered Hair", "Scales", "Feathers", "Spines", 
        "Bristles", "Fur", "Noise", "Stipple",
        "Splatter", "Wave", "Ripple", "Crystalline"
    };
    
    for (int i = 0; i < 12; i++) {
        state->texture_kit.brushes[i].brush_id = i;
        strncpy(state->texture_kit.brushes[i].name, texture_names[i], sizeof(state->texture_kit.brushes[i].name) - 1);
        state->texture_kit.brushes[i].name[sizeof(state->texture_kit.brushes[i].name) - 1] = '\0';
        state->texture_kit.brushes[i].falloff = 1.0f;
        state->texture_kit.brushes[i].strength = 0.5f;
        state->texture_kit.brushes[i].radius = 50.0f;
    }

    /* Initialize surface mappings */
    state->surface_kit.mapping_count = MAX_MAPPINGS;
    const char* surface_names[] = {
        "Bump Basic", "Bump Detailed", "Gash Deep", "Gash Fine",
        "Pimple", "Hairlet", "Groove Wide", "Groove Tight",
        "Fold Natural", "Fold Sharp", "Cloth Weave", "Cloth Knit",
        "Skin Pore", "Skin Wrinkle", "Leather", "Canvas",
        "Brick", "Stone", "Wood Grain", "Metal Grain",
        "Scales Armor", "Chain Mail", "Dent", "Corrosion",
        "Fabric Linen", "Fabric Cotton", "Marble", "Granite",
        "Weathered", "Cracked", "Emboss", "Inlay"
    };
    
    for (int i = 0; i < 32; i++) {
        state->surface_kit.mappings[i].mapping_id = i;
        strncpy(state->surface_kit.mappings[i].name, surface_names[i], sizeof(state->surface_kit.mappings[i].name) - 1);
        state->surface_kit.mappings[i].name[sizeof(state->surface_kit.mappings[i].name) - 1] = '\0';
        state->surface_kit.mappings[i].depth = 0.5f;
        state->surface_kit.mappings[i].detail = 0.8f;
        state->surface_kit.mappings[i].pattern_type = i;
    }

    /* Initialize NodeCraft network */
    state->network.max_nodes = 1000;
    state->network.max_links = 5000;
    state->network.node_count = 0;
    state->network.link_count = 0;
    state->network.nodes = (NodePoint*)malloc(sizeof(NodePoint) * state->network.max_nodes);
    state->network.links = (NodeLink*)malloc(sizeof(NodeLink) * state->network.max_links);
    
    if (!state->network.nodes || !state->network.links) {
        free(state->network.nodes);
        free(state->network.links);
        free(state);
        return NULL;
    }

    state->mode = 0;
    state->active_brush = 0;
    state->active_mapping = 0;
    
    return state;
}

/* ============== TEXTURE BRUSH OPERATIONS ============== */
int txtur_apply_texture_brush(TxTURPluginState* state, int brush_id, Vec3 position, float intensity) {
    if (!state || brush_id < 0 || brush_id >= 12) return -1;
    
    TextureBrush* brush = &state->texture_kit.brushes[brush_id];
    
    /* Validate intensity */
    if (intensity < 0.0f) intensity = 0.0f;
    if (intensity > 1.0f) intensity = 1.0f;
    
    /* Apply brush logic */
    brush->strength = intensity * 0.5f;
    
    return 0;
}

/* ============== SURFACE MAPPING OPERATIONS ============== */
int txtur_apply_surface_mapping(TxTURPluginState* state, int mapping_id, Vec3 position, float depth) {
    if (!state || mapping_id < 0 || mapping_id >= 32) return -1;
    
    SurfaceMapping* mapping = &state->surface_kit.mappings[mapping_id];
    
    if (depth < 0.0f) depth = 0.0f;
    if (depth > 1.0f) depth = 1.0f;
    
    mapping->depth = depth;
    
    return 0;
}

/* ============== NODECRAFT OPERATIONS ============== */
int txtur_add_node(TxTURPluginState* state, Vec3 position, float scale) {
    if (!state || state->network.node_count >= state->network.max_nodes) return -1;
    
    NodePoint* node = &state->network.nodes[state->network.node_count];
    node->node_id = state->network.node_count;
    node->position = position;
    node->scale = scale;
    node->connection_count = 0;
    
    return state->network.node_count++;
}

int txtur_add_link(TxTURPluginState* state, int from_id, int to_id, LinkageType type, float thickness) {
    if (!state || state->network.link_count >= state->network.max_links) return -1;
    if (from_id < 0 || from_id >= state->network.node_count) return -1;
    if (to_id < 0 || to_id >= state->network.node_count) return -1;
    
    NodeLink* link = &state->network.links[state->network.link_count];
    link->from_node = from_id;
    link->to_node = to_id;
    link->type = type;
    link->thickness = thickness;
    link->tension = 0.5f;
    
    state->network.nodes[from_id].connection_count++;
    state->network.nodes[to_id].connection_count++;
    
    return state->network.link_count++;
}

/* ============== MODE SWITCHING ============== */
int txtur_set_mode(TxTURPluginState* state, int mode) {
    if (!state || mode < 0 || mode > 3) return -1;
    state->mode = mode;
    return 0;
}

/* ============== FILE I/O FOR BLEND COMPATIBILITY ============== */
int txtur_save_state(TxTURPluginState* state, const char* filepath) {
    if (!state || !filepath) return -1;
    
    FILE* f = fopen(filepath, "wb");
    if (!f) return -1;
    
    /* Write header */
    uint32_t magic = 0x54785455; /* "TxTU" */
    fwrite(&magic, sizeof(uint32_t), 1, f);
    
    uint32_t version = 1;
    fwrite(&version, sizeof(uint32_t), 1, f);
    
    /* Write state data */
    fwrite(&state->mode, sizeof(int), 1, f);
    fwrite(&state->active_brush, sizeof(int), 1, f);
    fwrite(&state->active_mapping, sizeof(int), 1, f);
    
    /* Write texture brushes */
    fwrite(&state->texture_kit.brush_count, sizeof(int), 1, f);
    for (int i = 0; i < state->texture_kit.brush_count; i++) {
        TextureBrush* brush = &state->texture_kit.brushes[i];
        fwrite(brush->name, sizeof(char), 64, f);
        fwrite(&brush->brush_id, sizeof(int), 1, f);
        fwrite(&brush->falloff, sizeof(float), 1, f);
        fwrite(&brush->strength, sizeof(float), 1, f);
        fwrite(&brush->radius, sizeof(float), 1, f);
    }
    
    /* Write surface mappings */
    fwrite(&state->surface_kit.mapping_count, sizeof(int), 1, f);
    for (int i = 0; i < state->surface_kit.mapping_count; i++) {
        SurfaceMapping* mapping = &state->surface_kit.mappings[i];
        fwrite(mapping->name, sizeof(char), 64, f);
        fwrite(&mapping->mapping_id, sizeof(int), 1, f);
        fwrite(&mapping->depth, sizeof(float), 1, f);
        fwrite(&mapping->detail, sizeof(float), 1, f);
        fwrite(&mapping->pattern_type, sizeof(int), 1, f);
    }
    
    /* Write NodeCraft network */
    fwrite(&state->network.node_count, sizeof(int), 1, f);
    fwrite(&state->network.link_count, sizeof(int), 1, f);
    
    for (int i = 0; i < state->network.node_count; i++) {
        NodePoint* node = &state->network.nodes[i];
        fwrite(&node->node_id, sizeof(int), 1, f);
        fwrite(&node->position, sizeof(Vec3), 1, f);
        fwrite(&node->scale, sizeof(float), 1, f);
        fwrite(&node->connection_count, sizeof(int), 1, f);
    }
    
    for (int i = 0; i < state->network.link_count; i++) {
        NodeLink* link = &state->network.links[i];
        fwrite(&link->from_node, sizeof(int), 1, f);
        fwrite(&link->to_node, sizeof(int), 1, f);
        fwrite(&link->type, sizeof(LinkageType), 1, f);
        fwrite(&link->tension, sizeof(float), 1, f);
        fwrite(&link->thickness, sizeof(float), 1, f);
    }
    
    fclose(f);
    return 0;
}

int txtur_load_state(TxTURPluginState* state, const char* filepath) {
    if (!state || !filepath) return -1;
    
    FILE* f = fopen(filepath, "rb");
    if (!f) return -1;
    
    uint32_t magic, version;
    fread(&magic, sizeof(uint32_t), 1, f);
    fread(&version, sizeof(uint32_t), 1, f);
    
    if (magic != 0x54785455 || version != 1) {
        fclose(f);
        return -1;
    }
    
    fread(&state->mode, sizeof(int), 1, f);
    fread(&state->active_brush, sizeof(int), 1, f);
    fread(&state->active_mapping, sizeof(int), 1, f);
    
    fread(&state->texture_kit.brush_count, sizeof(int), 1, f);
    if (state->texture_kit.brush_count < 0 || state->texture_kit.brush_count > MAX_BRUSHES) {
        state->texture_kit.brush_count = MAX_BRUSHES;
    }
    for (int i = 0; i < state->texture_kit.brush_count; i++) {
        TextureBrush* brush = &state->texture_kit.brushes[i];
        fread(brush->name, sizeof(char), 64, f);
        fread(&brush->brush_id, sizeof(int), 1, f);
        fread(&brush->falloff, sizeof(float), 1, f);
        fread(&brush->strength, sizeof(float), 1, f);
        fread(&brush->radius, sizeof(float), 1, f);
    }
    
    fread(&state->surface_kit.mapping_count, sizeof(int), 1, f);
    if (state->surface_kit.mapping_count < 0 || state->surface_kit.mapping_count > MAX_MAPPINGS) {
        state->surface_kit.mapping_count = MAX_MAPPINGS;
    }
    for (int i = 0; i < state->surface_kit.mapping_count; i++) {
        SurfaceMapping* mapping = &state->surface_kit.mappings[i];
        fread(mapping->name, sizeof(char), 64, f);
        fread(&mapping->mapping_id, sizeof(int), 1, f);
        fread(&mapping->depth, sizeof(float), 1, f);
        fread(&mapping->detail, sizeof(float), 1, f);
        fread(&mapping->pattern_type, sizeof(int), 1, f);
    }
    
    fread(&state->network.node_count, sizeof(int), 1, f);
    if (state->network.node_count < 0 || state->network.node_count > state->network.max_nodes) {
        state->network.node_count = state->network.max_nodes;
    }
    fread(&state->network.link_count, sizeof(int), 1, f);
    if (state->network.link_count < 0 || state->network.link_count > state->network.max_links) {
        state->network.link_count = state->network.max_links;
    }
    
    for (int i = 0; i < state->network.node_count; i++) {
        NodePoint* node = &state->network.nodes[i];
        fread(&node->node_id, sizeof(int), 1, f);
        fread(&node->position, sizeof(Vec3), 1, f);
        fread(&node->scale, sizeof(float), 1, f);
        fread(&node->connection_count, sizeof(int), 1, f);
    }
    
    for (int i = 0; i < state->network.link_count; i++) {
        NodeLink* link = &state->network.links[i];
        fread(&link->from_node, sizeof(int), 1, f);
        fread(&link->to_node, sizeof(int), 1, f);
        fread(&link->type, sizeof(LinkageType), 1, f);
        fread(&link->tension, sizeof(float), 1, f);
        fread(&link->thickness, sizeof(float), 1, f);
    }
    
    fclose(f);
    return 0;
}

/* ============== CLEANUP ============== */
void txtur_cleanup(TxTURPluginState* state) {
    if (!state) return;
    free(state->network.nodes);
    free(state->network.links);
    free(state);
}

/* ============== LIBRARY EXPORTS / BRIDGE HELPERS ============== */
TXTUR_API const char* txtur_get_version(void) {
    return "TxTUR C Plugin v1.0";
}

TXTUR_API const char* txtur_get_info(void) {
    return "TxTUR: texture brushes (12), surface mappings (32), nodecraft network";
}

/* Create a small Python Blender addon that uses ctypes to load this library and
   expose a minimal UI. The generated file should be placed in the Blender addon
   folder or next to the compiled library. */
TXTUR_API int txtur_generate_blender_addon(const char* filepath) {
    if (!filepath) return -1;
    FILE* f = fopen(filepath, "w");
    if (!f) return -1;

    const char* py =
"bl_info = {\n"
"    \"name\": \"TxTUR C Bridge\",\n"
"    \"blender\": (2, 80, 0),\n"
"    \"category\": \"Texture\",\n"
"}\n\n"
"import bpy\n"
"import os\n"
"import ctypes\n"
"from ctypes import c_int, c_float, c_char_p\n\n"
"# Library name - change if different after build\n"
"_lib_name = 'blenderTxTUR.dll'\n"
"if os.name != 'nt':\n"
"    _lib_name = 'libblenderTxTUR.so'\n"
"_lib = None\n"
"try:\n"
"    _lib = ctypes.CDLL(os.path.join(os.path.dirname(__file__), _lib_name))\n"
"except Exception:\n"
"    try:\n"
"        _lib = ctypes.CDLL(_lib_name)\n"
"    except Exception:\n"
"        _lib = None\n\n"
"def lib_ok():\n"
"    return _lib is not None\n\n"
"class TXTUR_OT_init(bpy.types.Operator):\n"
"    bl_idname = \"txtur.init\"\n"
"    bl_label = \"Initialize TxTUR\"\n\n"
"    def execute(self, context):\n"
"        if not lib_ok():\n"
"            self.report({'ERROR'}, 'TxTUR library not loaded')\n"
"            return {'CANCELLED'}\n"
"        try:\n"
"            _lib.txtur_get_info.restype = ctypes.c_char_p\n"
"            info = _lib.txtur_get_info()\n"
"            self.report({'INFO'}, info.decode() if info else 'no-info')\n"
"        except Exception:\n"
"            pass\n"
"        return {'FINISHED'}\n\n"
"class TXTUR_PT_panel(bpy.types.Panel):\n"
"    bl_label = \"TxTUR Bridge\"\n"
"    bl_idname = \"TXTUR_PT_panel\"\n"
"    bl_space_type = 'VIEW_3D'\n"
"    bl_region_type = 'UI'\n"
"    bl_category = 'TxTUR'\n\n"
"    def draw(self, context):\n"
"        layout = self.layout\n"
"        row = layout.row()\n"
"        row.operator('txtur.init')\n"
"        row = layout.row()\n"
"        row.label(text='This panel calls the TxTUR C lib via ctypes')\n\n"
"def register():\n"
"    bpy.utils.register_class(TXTUR_OT_init)\n"
"    bpy.utils.register_class(TXTUR_PT_panel)\n\n"
"def unregister():\n"
"    bpy.utils.unregister_class(TXTUR_PT_panel)\n"
"    bpy.utils.unregister_class(TXTUR_OT_init)\n\n"
"if __name__ == '__main__':\n"
"    register()\n";

    fprintf(f, "%s", py);
    fclose(f);
    return 0;
}

/* ============== TEST IMAGE GENERATOR ==============
   Exports a simple function that fills a provided RGBA buffer with a test
   gradient. This allows the Python addon to request image data from the C
   side for quick visual verification inside Blender.
*/
TXTUR_API int txtur_fill_test_image(uint8_t* buf, int width, int height) {
    if (!buf || width <= 0 || height <= 0) return 0;
    int w = width;
    int h = height;
    for (int y = 0; y < h; y++) {
        for (int x = 0; x < w; x++) {
            int idx = (y * w + x) * 4;
            /* simple gradient: R = x, G = y, B = 128, A = 255 */
            buf[idx + 0] = (uint8_t)((x * 255) / (w - 1));
            buf[idx + 1] = (uint8_t)((y * 255) / (h - 1));
            buf[idx + 2] = 128;
            buf[idx + 3] = 255;
        }
    }
    return 1;
}

/* ============== SIMPLE SINGLETON BRIDGE ============== */
static TxTURPluginState* g_txtur_state = NULL;

TXTUR_API int txtur_start(void) {
    if (!g_txtur_state) g_txtur_state = txtur_init();
    return g_txtur_state ? 1 : 0;
}

TXTUR_API void txtur_stop(void) {
    if (g_txtur_state) {
        txtur_cleanup(g_txtur_state);
        g_txtur_state = NULL;
    }
}

TXTUR_API int txtur_get_brush_count(void) {
    return 12;
}

TXTUR_API const char* txtur_get_brush_name(int id) {
    if (!g_txtur_state) {
        if (!txtur_start()) return NULL;
    }
    if (id < 0 || id >= g_txtur_state->texture_kit.brush_count) return NULL;
    return g_txtur_state->texture_kit.brushes[id].name;
}

TXTUR_API int txtur_apply_texture_simple(int brush_id, float x, float y, float z, float intensity) {
    if (!g_txtur_state) {
        if (!txtur_start()) return -1;
    }
    Vec3 pos = { x, y, z };
    return txtur_apply_texture_brush(g_txtur_state, brush_id, pos, intensity);
}

TXTUR_API int txtur_get_mapping_count(void) {
    return 32;
}

TXTUR_API const char* txtur_get_mapping_name(int id) {
    if (!g_txtur_state) {
        if (!txtur_start()) return NULL;
    }
    if (id < 0 || id >= g_txtur_state->surface_kit.mapping_count) return NULL;
    return g_txtur_state->surface_kit.mappings[id].name;
}

TXTUR_API int txtur_apply_mapping_simple(int mapping_id, float x, float y, float z, float depth) {
    if (!g_txtur_state) {
        if (!txtur_start()) return -1;
    }
    Vec3 pos = { x, y, z };
    return txtur_apply_surface_mapping(g_txtur_state, mapping_id, pos, depth);
}

/* NodeCraft wrappers */
TXTUR_API int txtur_node_add(float x, float y, float z, float scale) {
    if (!g_txtur_state) {
        if (!txtur_start()) return -1;
    }
    Vec3 pos = { x, y, z };
    return txtur_add_node(g_txtur_state, pos, scale);
}

TXTUR_API int txtur_node_link(int from_id, int to_id, int linkage_type, float thickness) {
    if (!g_txtur_state) {
        if (!txtur_start()) return -1;
    }
    if (linkage_type < 0) linkage_type = 0;
    return txtur_add_link(g_txtur_state, from_id, to_id, (LinkageType)linkage_type, thickness);
}

TXTUR_API int txtur_set_mode_simple(int mode) {
    if (!g_txtur_state) {
        if (!txtur_start()) return -1;
    }
    return txtur_set_mode(g_txtur_state, mode);
}

/* ============== DISPLACEMENT SAMPLER ============== */
/* Returns a procedural displacement value at world coordinates (x,y,z).
   Value is in Blender units; positive values push along normals. */
TXTUR_API float txtur_sample_displacement(float x, float y, float z) {
    if (!g_txtur_state) {
        if (!txtur_start()) return 0.0f;
    }
    if (!g_txtur_state) return 0.0f;

    int b = g_txtur_state->active_brush;
    if (b < 0 || b >= g_txtur_state->texture_kit.brush_count) b = 0;
    float brush_strength = g_txtur_state->texture_kit.brushes[b].strength;

    int m = g_txtur_state->active_mapping;
    if (m < 0 || m >= g_txtur_state->surface_kit.mapping_count) m = 0;
    float mapping_depth = g_txtur_state->surface_kit.mappings[m].depth;

    /* simple procedural function using sines to produce repeatable patterns */
    float v = sinf(x * 0.12f + (float)b) * cosf(y * 0.07f) * sinf(z * 0.03f);
    v = (v * 0.5f) + 0.5f; /* normalize to 0..1 */
    return v * brush_strength * mapping_depth;
}

/* ============== MAIN ENTRY POINT ============== */
int main(void) {
    TxTURPluginState* plugin = txtur_init();
    if (!plugin) {
        fprintf(stderr, "Failed to initialize TxTUR plugin\n");
        return 1;
    }
    
    printf("TxTUR Plugin initialized successfully\n");
    printf("Texture Brushes: %d\n", plugin->texture_kit.brush_count);
    printf("Surface Mappings: %d\n", plugin->surface_kit.mapping_count);
    
    txtur_cleanup(plugin);
    return 0;
}