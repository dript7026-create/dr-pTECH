#include "ClipStudioPipelineBridge.h"

#include <stdio.h>

static const char *safe_string(const char *value) {
    return value ? value : "";
}

static void write_escaped(FILE *f, const char *s) {
    for (; s && *s; ++s) {
        if (*s == '"' || *s == '\\') {
            fputc('\\', f);
        }
        fputc(*s, f);
    }
}

int csp_pipeline_write_export(
    const char *output_path,
    const CSPipelineExportDesc *desc,
    const SceneSequenceArray *scenes,
    const SymbolObject *symbols,
    size_t symbol_count,
    const VisualScript *scripts,
    size_t script_count) {
    FILE *f;
    size_t i;
    if (!output_path || !desc) return 0;
    f = fopen(output_path, "wb");
    if (!f) return 0;

    fprintf(f, "{\n  \"project_name\": \"");
    write_escaped(f, desc->project_name ? desc->project_name : "untitled");
    fprintf(f, "\",\n  \"canvas\": { \"width\": %d, \"height\": %d, \"layers\": %d },\n", desc->canvas_width, desc->canvas_height, desc->layer_count);

    fprintf(f, "  \"scenes\": [\n");
    for (i = 0; scenes && i < scenes->count; ++i) {
        fprintf(f, "    { \"name\": \"");
        write_escaped(f, scenes->items[i].scene_name);
        fprintf(f, "\", \"first\": %d, \"last\": %d }%s\n",
                scenes->items[i].first_trigger_frame,
                scenes->items[i].last_trigger_frame,
                (i + 1 == scenes->count) ? "" : ",");
    }
    fprintf(f, "  ],\n");

    fprintf(f, "  \"symbols\": [\n");
    for (i = 0; symbols && i < symbol_count; ++i) {
        fprintf(f, "    { \"name\": \"");
        write_escaped(f, symbols[i].symbol_name);
        fprintf(f, "\", \"timeline_length\": %d, \"frames\": %u }%s\n",
                symbols[i].timeline_length,
                (unsigned)symbols[i].frames_count,
                (i + 1 == symbol_count) ? "" : ",");
    }
    fprintf(f, "  ],\n");

    fprintf(f, "  \"scripts\": [\n");
    for (i = 0; scripts && i < script_count; ++i) {
        fprintf(f, "    { \"name\": \"");
        write_escaped(f, scripts[i].script_name);
        fprintf(f, "\", \"type\": \"");
        write_escaped(f, scripts[i].script_type);
        fprintf(f, "\", \"target_symbol\": \"");
        write_escaped(f, scripts[i].target_symbol ? scripts[i].target_symbol->symbol_name : "");
        fprintf(f, "\" }%s\n", (i + 1 == script_count) ? "" : ",");
    }
    fprintf(f, "  ]\n}\n");

    fclose(f);
    return 1;
}

int csp_pipeline_write_script_binding(const char *output_path, const VisualScript *script) {
    FILE *f;
    if (!output_path || !script) return 0;
    f = fopen(output_path, "wb");
    if (!f) return 0;
    fprintf(f, "script=%s\ntype=%s\ntarget=%s\n",
            script->script_name,
            script->script_type,
            script->target_symbol ? script->target_symbol->symbol_name : "");
    fclose(f);
    return 1;
}

static void write_json_string(FILE *f, const char *value) {
    fputc('"', f);
    write_escaped(f, safe_string(value));
    fputc('"', f);
}

int csp_pipeline_write_runtime_manifest(
    const char *output_path,
    const char *project_name,
    int timeline_fps,
    const CSPipelineLayerDesc *layers,
    size_t layer_count,
    const CSPipelineHitboxDesc *hitboxes,
    size_t hitbox_count,
    const CSPipelineScriptBindingDesc *bindings,
    size_t binding_count) {
    FILE *f;
    size_t i;
    if (!output_path || !project_name) return 0;
    f = fopen(output_path, "wb");
    if (!f) return 0;

    fprintf(f, "{\n  \"project_name\": ");
    write_json_string(f, project_name);
    fprintf(f, ",\n  \"timeline_fps\": %d,\n", timeline_fps);

    fprintf(f, "  \"layers\": [\n");
    for (i = 0; layers && i < layer_count; ++i) {
        fprintf(f, "    { \"name\": ");
        write_json_string(f, layers[i].layer_name);
        fprintf(f, ", \"blend_mode\": ");
        write_json_string(f, layers[i].blend_mode);
        fprintf(f, ", \"visible\": %s, \"locked\": %s }%s\n",
                layers[i].visible ? "true" : "false",
                layers[i].locked ? "true" : "false",
                (i + 1 == layer_count) ? "" : ",");
    }
    fprintf(f, "  ],\n");

    fprintf(f, "  \"hitboxes\": [\n");
    for (i = 0; hitboxes && i < hitbox_count; ++i) {
        fprintf(f, "    { \"symbol\": ");
        write_json_string(f, hitboxes[i].symbol_name);
        fprintf(f, ", \"frame\": %d, \"x\": %.3f, \"y\": %.3f, \"w\": %.3f, \"h\": %.3f, \"kind\": ",
                hitboxes[i].frame_index,
                hitboxes[i].x,
                hitboxes[i].y,
                hitboxes[i].w,
                hitboxes[i].h);
        write_json_string(f, hitboxes[i].kind);
        fprintf(f, " }%s\n", (i + 1 == hitbox_count) ? "" : ",");
    }
    fprintf(f, "  ],\n");

    fprintf(f, "  \"script_bindings\": [\n");
    for (i = 0; bindings && i < binding_count; ++i) {
        fprintf(f, "    { \"name\": ");
        write_json_string(f, bindings[i].binding_name);
        fprintf(f, ", \"event\": ");
        write_json_string(f, bindings[i].event_name);
        fprintf(f, ", \"target_symbol\": ");
        write_json_string(f, bindings[i].target_symbol);
        fprintf(f, ", \"command\": ");
        write_json_string(f, bindings[i].command);
        fprintf(f, " }%s\n", (i + 1 == binding_count) ? "" : ",");
    }
    fprintf(f, "  ]\n}\n");

    fclose(f);
    return 1;
}