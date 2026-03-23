#ifndef BANGO_SPACE_FRAME_H
#define BANGO_SPACE_FRAME_H

#ifdef __cplusplus
extern "C" {
#endif

#define BANGO_SPACE_FRAME_MAX_NODES 1728

typedef struct BangoSpaceNode {
    float x;
    float y;
    float z;
    float equilibrium_x;
    float equilibrium_y;
    float equilibrium_z;
    float displacement;
    float disturbance;
    float agitation;
    float pressure;
    float density;
    float radiation;
    float pore;
} BangoSpaceNode;

typedef struct BangoSpaceFrameMetrics {
    float dispersal;
    float disturbance;
    float disruption;
    float displacement;
    float pressure_density;
    float radiation;
    float pore_flux;
    float gravity_focus;
} BangoSpaceFrameMetrics;

typedef struct BangoSpaceFrame {
    float origin_x;
    float origin_y;
    float origin_z;
    float size_x;
    float size_y;
    float size_z;
    int cells_x;
    int cells_y;
    int cells_z;
    int node_count;
    BangoSpaceNode nodes[BANGO_SPACE_FRAME_MAX_NODES];
    BangoSpaceFrameMetrics metrics;
} BangoSpaceFrame;

void bango_space_frame_init(BangoSpaceFrame *frame, float origin_x, float origin_y, float origin_z, float size_x, float size_y, float size_z, int cells_x, int cells_y, int cells_z);
void bango_space_frame_update(BangoSpaceFrame *frame, float dt, float subject_x, float subject_y, float subject_z, float velocity_x, float velocity_y, float velocity_z, float observer_bias, float input_energy);
float bango_space_frame_sample_displacement(const BangoSpaceFrame *frame, float world_x, float world_y, float world_z);

#ifdef __cplusplus
}
#endif

#endif