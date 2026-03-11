#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ClipStudioPixelBrushSuite.h"

int main(void) {
    /* create a small canvas */
    CanvasState* canvas = (CanvasState*)malloc(sizeof(CanvasState));
    canvas->width = 64;
    canvas->height = 64;
    canvas->layer_count = 4;
    canvas->layer_data = (unsigned char**)calloc(canvas->layer_count, sizeof(unsigned char*));
    for (int i = 0; i < canvas->layer_count; ++i) {
        canvas->layer_data[i] = (unsigned char*)calloc(canvas->width * canvas->height * 4, 1);
    }

    BrushProperties brush;
    memset(&brush, 0, sizeof(brush));
    brush.pixel_size = 4;
    brush.opacity = 0.8f;
    brush.intensity = 0.6f;
    brush.layer_depth = 0;

    /* apply translayer gradation */
    apply_translayer_gradation(canvas, 10, 10, brush.pixel_size, &brush, 0.5f);
    printf("Applied translayer gradation to canvas.\n");

    /* run AI inbetween stub */
    ai_inbetween_frames(canvas, 0, 3);
    printf("Ran ai_inbetween_frames (stub).\n");

    /* symbol and scene tests */
    SymbolObject sym;
    if (!symbol_init(&sym, "Hero", 10)) {
        fprintf(stderr, "symbol_init failed\n");
    }
    symbol_add_frame(&sym, FRAME_KEY, 0);
    symbol_add_frame(&sym, FRAME_INBETWEEN, 1);
    printf("Symbol '%s' has %zu frames.\n", sym.symbol_name, sym.frames_count);

    SceneSequenceArray scenes;
    scene_array_init(&scenes, 2);
    add_scene_sequence(&scenes, 0, 10, "Intro");
    add_scene_sequence(&scenes, 11, 20, "Battle");
    printf("Scene array contains %zu sequences.\n", scenes.count);

    VisualScript script;
    strncpy(script.script_name, "HeroEntrance", 63);
    script.script_name[63] = '\0';
    tie_script_to_symbol(&script, &sym);
    ButtonObject btn;
    tie_script_to_button(&script, &btn); /* btn.animation should be set */
    printf("Script '%s' tied to symbol '%s'.\n", script.script_name, script.target_symbol->symbol_name);

    /* hit detection test */
    HitDetection hit;
    float boxes[4] = {0.0f, 0.0f, 10.0f, 10.0f};
    define_hit_detection(&hit, 1, boxes);
    printf("Hit detection boxes: %d\n", hit.hitbox_count);

    /* cleanup */
    symbol_free(&sym);
    scene_array_free(&scenes);
    for (int i = 0; i < canvas->layer_count; ++i) free(canvas->layer_data[i]);
    free(canvas->layer_data);
    free(canvas);
    return 0;
}
