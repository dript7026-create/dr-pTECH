#ifndef CLIPSTUDIO_PIXEL_BRUSH_SUITE_H
#define CLIPSTUDIO_PIXEL_BRUSH_SUITE_H

#include <stddef.h>

/* Basic brush and canvas types exposed to consumers */
typedef struct {
    int pixel_size;           /* 1-32 pixel dimension */
    float opacity;            /* 0.0-1.0 */
    int brush_type;           /* 0=standard, 1=watercolor, 2=oil, 3=airbrush, 4=charcoal, 5=feathered */
    float intensity;          /* spectral slider: 0.0-1.0 */
    int layer_depth;          /* trans-layer depth level */
    int animation_frame;      /* current timeline frame */
} BrushProperties;

typedef struct {
    float x, y;
    float pressure;
} CanvasStroke;

typedef struct {
    int width, height;
    int layer_count;
    unsigned char** layer_data;
    BrushProperties active_brush;
} CanvasState;

/* Pixel application utilities */
void apply_pixel_alpha(CanvasState* canvas, int x, int y, float alpha, int layer_idx);
void update_animation_frame(CanvasState* canvas, int frame);
/* Specific brush type application helpers (forward declarations) */
void apply_standard_pixel(CanvasState* canvas, int x, int y, int size, BrushProperties* brush);
void apply_watercolor_pixel(CanvasState* canvas, int x, int y, int size, BrushProperties* brush, float pressure);
void apply_oil_pixel(CanvasState* canvas, int x, int y, int size, BrushProperties* brush, float pressure);
void apply_airbrush_pixel(CanvasState* canvas, int x, int y, int size, BrushProperties* brush, float pressure);
void apply_charcoal_pixel(CanvasState* canvas, int x, int y, int size, BrushProperties* brush);
void apply_feathered_pixel(CanvasState* canvas, int x, int y, int size, BrushProperties* brush, float pressure);

/* Translayer gradation and AI inbetweening */
void apply_translayer_gradation(CanvasState* canvas, int x, int y, int size, BrushProperties* brush, float z_depth);
void ai_inbetween_frames(CanvasState* canvas, int start_frame, int end_frame);

/* Timeline and scene sequencing */
typedef enum {
    FRAME_KEY,
    FRAME_BLANK,
    FRAME_INBETWEEN,
    FRAME_TRIGGER
} AnimationFrameType;

typedef struct {
    AnimationFrameType type;
    int frame_index;
} TimelineFrame;

typedef struct {
    int first_trigger_frame;
    int last_trigger_frame;
    char scene_name[64];
} SceneSequence;

/* Dynamic SceneSequence array */
typedef struct {
    SceneSequence* items;
    size_t count;
    size_t capacity;
} SceneSequenceArray;

int scene_array_init(SceneSequenceArray* arr, size_t initial_capacity);
void scene_array_free(SceneSequenceArray* arr);
int add_scene_sequence(SceneSequenceArray* arr, int first, int last, const char* name);

/* Visual scripting types */
typedef struct {
    char symbol_name[64];
    int timeline_length;
    TimelineFrame* frames;
    size_t frames_count;
    size_t frames_capacity;
} SymbolObject;

typedef struct {
    char button_name[64];
    SymbolObject* animation;
} ButtonObject;

typedef struct {
    char script_name[64];
    char script_type[32];
    SymbolObject* target_symbol;
} VisualScript;

typedef struct {
    int hitbox_count;
    float* hitbox_data;
} HitDetection;

/* Symbol management */
int symbol_init(SymbolObject* s, const char* name, int timeline_length);
int symbol_add_frame(SymbolObject* s, AnimationFrameType type, int frame_index);
void symbol_free(SymbolObject* s);

/* Scripting helpers */
void tie_script_to_symbol(VisualScript* script, SymbolObject* symbol);
void tie_script_to_button(VisualScript* script, ButtonObject* button);
void tie_script_to_frame(VisualScript* script, TimelineFrame* frame);
void define_hit_detection(HitDetection* hit, int count, float* data);

#endif
