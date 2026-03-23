#include "TxTURPipelineBridge.h"

#include <stdio.h>

static const char *txtur_safe_string(const char *value) {
    return value ? value : "";
}

static void txtur_write_string(FILE *f, const char *value) {
    for (; value && *value; ++value) {
        if (*value == '"' || *value == '\\') {
            fputc('\\', f);
        }
        fputc(*value, f);
    }
}

int txtur_pipeline_write_conversion_plan(
    const char *output_path,
    const char *project_name,
    const TxTURSpriteLift *lifts,
    size_t lift_count,
    const TxTURScenePlan *scenes,
    size_t scene_count) {
    FILE *f;
    size_t i;
    if (!output_path || !project_name) return 0;
    f = fopen(output_path, "wb");
    if (!f) return 0;

    fprintf(f, "{\n  \"project_name\": \"");
    txtur_write_string(f, project_name);
    fprintf(f, "\",\n  \"lift_plan\": [\n");

    for (i = 0; lifts && i < lift_count; ++i) {
        fprintf(f, "    { \"asset_id\": \"");
        txtur_write_string(f, lifts[i].asset_id);
        fprintf(f, "\", \"source_path\": \"");
        txtur_write_string(f, lifts[i].source_path);
        fprintf(f, "\", \"extrusion_depth\": %.3f, \"frame_count\": %d }%s\n",
                lifts[i].extrusion_depth,
                lifts[i].frame_count,
                (i + 1 == lift_count) ? "" : ",");
    }
    fprintf(f, "  ],\n  \"scene_plan\": [\n");

    for (i = 0; scenes && i < scene_count; ++i) {
        fprintf(f, "    { \"scene_id\": \"");
        txtur_write_string(f, scenes[i].scene_id);
        fprintf(f, "\", \"location\": \"");
        txtur_write_string(f, scenes[i].location);
        fprintf(f, "\", \"first_frame\": %d, \"last_frame\": %d }%s\n",
                scenes[i].first_frame,
                scenes[i].last_frame,
                (i + 1 == scene_count) ? "" : ",");
    }
    fprintf(f, "  ]\n}\n");
    fclose(f);
    return 1;
}

static void txtur_write_json_string(FILE *f, const char *value) {
    fputc('"', f);
    txtur_write_string(f, txtur_safe_string(value));
    fputc('"', f);
}

int txtur_pipeline_write_blender_import_spec(
    const char *output_path,
    const char *project_name,
    const TxTURMaterialProfile *materials,
    size_t material_count,
    const TxTURRigPlan *rigs,
    size_t rig_count,
    const TxTURNodeCraftNode *nodes,
    size_t node_count,
    const TxTURNodeCraftLink *links,
    size_t link_count) {
    FILE *f;
    size_t i;
    if (!output_path || !project_name) return 0;
    f = fopen(output_path, "wb");
    if (!f) return 0;

    fprintf(f, "{\n  \"project_name\": ");
    txtur_write_json_string(f, project_name);
    fprintf(f, ",\n  \"materials\": [\n");
    for (i = 0; materials && i < material_count; ++i) {
        fprintf(f, "    { \"name\": ");
        txtur_write_json_string(f, materials[i].profile_name);
        fprintf(f, ", \"shader\": ");
        txtur_write_json_string(f, materials[i].shader_name);
        fprintf(f, ", \"roughness\": %.3f, \"normal_strength\": %.3f }%s\n",
                materials[i].roughness,
                materials[i].normal_strength,
                (i + 1 == material_count) ? "" : ",");
    }
    fprintf(f, "  ],\n  \"rig_plan\": [\n");
    for (i = 0; rigs && i < rig_count; ++i) {
        fprintf(f, "    { \"asset_id\": ");
        txtur_write_json_string(f, rigs[i].asset_id);
        fprintf(f, ", \"armature\": ");
        txtur_write_json_string(f, rigs[i].armature_name);
        fprintf(f, ", \"root_bone\": ");
        txtur_write_json_string(f, rigs[i].root_bone);
        fprintf(f, " }%s\n", (i + 1 == rig_count) ? "" : ",");
    }
    fprintf(f, "  ],\n  \"nodecraft\": {\n    \"nodes\": [\n");
    for (i = 0; nodes && i < node_count; ++i) {
        fprintf(f, "      { \"id\": ");
        txtur_write_json_string(f, nodes[i].node_id);
        fprintf(f, ", \"position\": [%.3f, %.3f, %.3f], \"scale\": %.3f }%s\n",
                nodes[i].x,
                nodes[i].y,
                nodes[i].z,
                nodes[i].scale,
                (i + 1 == node_count) ? "" : ",");
    }
    fprintf(f, "    ],\n    \"links\": [\n");
    for (i = 0; links && i < link_count; ++i) {
        fprintf(f, "      { \"from\": ");
        txtur_write_json_string(f, links[i].from_node);
        fprintf(f, ", \"to\": ");
        txtur_write_json_string(f, links[i].to_node);
        fprintf(f, ", \"type\": ");
        txtur_write_json_string(f, links[i].link_type);
        fprintf(f, ", \"thickness\": %.3f }%s\n",
                links[i].thickness,
                (i + 1 == link_count) ? "" : ",");
    }
    fprintf(f, "    ]\n  }\n}\n");
    fclose(f);
    return 1;
}