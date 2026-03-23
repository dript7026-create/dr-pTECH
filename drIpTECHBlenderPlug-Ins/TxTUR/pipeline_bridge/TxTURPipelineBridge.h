#ifndef TXTUR_PIPELINE_BRIDGE_H
#define TXTUR_PIPELINE_BRIDGE_H

#include <stddef.h>

typedef struct {
    const char *asset_id;
    const char *source_path;
    float extrusion_depth;
    int frame_count;
} TxTURSpriteLift;

typedef struct {
    const char *scene_id;
    const char *location;
    int first_frame;
    int last_frame;
} TxTURScenePlan;

typedef struct {
    const char *profile_name;
    const char *shader_name;
    float roughness;
    float normal_strength;
} TxTURMaterialProfile;

typedef struct {
    const char *asset_id;
    const char *armature_name;
    const char *root_bone;
} TxTURRigPlan;

typedef struct {
    const char *node_id;
    float x;
    float y;
    float z;
    float scale;
} TxTURNodeCraftNode;

typedef struct {
    const char *from_node;
    const char *to_node;
    const char *link_type;
    float thickness;
} TxTURNodeCraftLink;

int txtur_pipeline_write_conversion_plan(
    const char *output_path,
    const char *project_name,
    const TxTURSpriteLift *lifts,
    size_t lift_count,
    const TxTURScenePlan *scenes,
    size_t scene_count);

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
    size_t link_count);

#endif