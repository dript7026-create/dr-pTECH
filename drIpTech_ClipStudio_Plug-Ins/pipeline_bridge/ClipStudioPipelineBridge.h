#ifndef CLIPSTUDIO_PIPELINE_BRIDGE_H
#define CLIPSTUDIO_PIPELINE_BRIDGE_H

#include <stddef.h>

#include "../ClipStudioPixelBrushSuite.h"

typedef struct {
    const char *project_name;
    int canvas_width;
    int canvas_height;
    int layer_count;
} CSPipelineExportDesc;

typedef struct {
    const char *layer_name;
    const char *blend_mode;
    int visible;
    int locked;
} CSPipelineLayerDesc;

typedef struct {
    const char *symbol_name;
    int frame_index;
    float x;
    float y;
    float w;
    float h;
    const char *kind;
} CSPipelineHitboxDesc;

typedef struct {
    const char *binding_name;
    const char *event_name;
    const char *target_symbol;
    const char *command;
} CSPipelineScriptBindingDesc;

int csp_pipeline_write_export(
    const char *output_path,
    const CSPipelineExportDesc *desc,
    const SceneSequenceArray *scenes,
    const SymbolObject *symbols,
    size_t symbol_count,
    const VisualScript *scripts,
    size_t script_count);

int csp_pipeline_write_runtime_manifest(
    const char *output_path,
    const char *project_name,
    int timeline_fps,
    const CSPipelineLayerDesc *layers,
    size_t layer_count,
    const CSPipelineHitboxDesc *hitboxes,
    size_t hitbox_count,
    const CSPipelineScriptBindingDesc *bindings,
    size_t binding_count);

int csp_pipeline_write_script_binding(const char *output_path, const VisualScript *script);

#endif