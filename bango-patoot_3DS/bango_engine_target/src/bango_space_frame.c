#include "../include/bango_space_frame.h"

#include <math.h>
#include <string.h>

static float bango_space_clampf(float value, float minimum, float maximum) {
    if (value < minimum) return minimum;
    if (value > maximum) return maximum;
    return value;
}

static float bango_space_length3(float x, float y, float z) {
    return sqrtf(x * x + y * y + z * z);
}

void bango_space_frame_init(BangoSpaceFrame *frame, float origin_x, float origin_y, float origin_z, float size_x, float size_y, float size_z, int cells_x, int cells_y, int cells_z) {
    int ix;
    int iy;
    int iz;
    int index;
    if (!frame) return;
    memset(frame, 0, sizeof(*frame));
    frame->origin_x = origin_x;
    frame->origin_y = origin_y;
    frame->origin_z = origin_z;
    frame->size_x = size_x;
    frame->size_y = size_y;
    frame->size_z = size_z;
    frame->cells_x = cells_x < 2 ? 2 : cells_x;
    frame->cells_y = cells_y < 2 ? 2 : cells_y;
    frame->cells_z = cells_z < 2 ? 2 : cells_z;
    index = 0;
    for (iz = 0; iz < frame->cells_z && index < BANGO_SPACE_FRAME_MAX_NODES; ++iz) {
        for (iy = 0; iy < frame->cells_y && index < BANGO_SPACE_FRAME_MAX_NODES; ++iy) {
            for (ix = 0; ix < frame->cells_x && index < BANGO_SPACE_FRAME_MAX_NODES; ++ix) {
                float tx = frame->cells_x > 1 ? (float)ix / (float)(frame->cells_x - 1) : 0.0f;
                float ty = frame->cells_y > 1 ? (float)iy / (float)(frame->cells_y - 1) : 0.0f;
                float tz = frame->cells_z > 1 ? (float)iz / (float)(frame->cells_z - 1) : 0.0f;
                BangoSpaceNode *node = &frame->nodes[index++];
                node->equilibrium_x = origin_x + size_x * tx;
                node->equilibrium_y = origin_y + size_y * ty;
                node->equilibrium_z = origin_z + size_z * tz;
                node->x = node->equilibrium_x;
                node->y = node->equilibrium_y;
                node->z = node->equilibrium_z;
                node->density = 0.5f;
                node->pore = 0.05f;
            }
        }
    }
    frame->node_count = index;
}

void bango_space_frame_update(BangoSpaceFrame *frame, float dt, float subject_x, float subject_y, float subject_z, float velocity_x, float velocity_y, float velocity_z, float observer_bias, float input_energy) {
    float total_disturbance;
    float total_disruption;
    float total_displacement;
    float total_pressure_density;
    float total_radiation;
    float total_pore_flux;
    float total_gravity_focus;
    float total_dispersal;
    float speed;
    int index;
    if (!frame) return;
    total_disturbance = 0.0f;
    total_disruption = 0.0f;
    total_displacement = 0.0f;
    total_pressure_density = 0.0f;
    total_radiation = 0.0f;
    total_pore_flux = 0.0f;
    total_gravity_focus = 0.0f;
    total_dispersal = 0.0f;
    speed = bango_space_length3(velocity_x, velocity_y, velocity_z);
    for (index = 0; index < frame->node_count; ++index) {
        BangoSpaceNode *node = &frame->nodes[index];
        float dx = node->equilibrium_x - subject_x;
        float dy = node->equilibrium_y - subject_y;
        float dz = node->equilibrium_z - subject_z;
        float distance = bango_space_length3(dx, dy, dz) + 0.001f;
        float normalized = bango_space_clampf(1.0f - distance / (frame->size_x + frame->size_y + frame->size_z), 0.0f, 1.0f);
        float gravity_focus = bango_space_clampf(1.0f / (1.0f + distance * 0.55f), 0.0f, 1.0f);
        float pressure_wave = normalized * (0.22f + speed * 0.14f + input_energy * 0.18f + observer_bias * 0.08f);
        float agitation = pressure_wave * (0.6f + gravity_focus * 0.8f);
        float radiation = agitation * (0.35f + observer_bias * 0.25f);
        float density = bango_space_clampf(0.35f + pressure_wave * 0.55f + gravity_focus * 0.18f, 0.0f, 1.2f);
        float pore = bango_space_clampf((density - 0.62f) * 0.85f + radiation * 0.22f, 0.0f, 1.0f);
        float pressure = bango_space_clampf(pressure_wave + density * 0.28f - pore * 0.18f, 0.0f, 1.25f);
        float displacement = pressure * 0.55f + radiation * 0.25f;

        node->disturbance = pressure_wave;
        node->agitation = agitation;
        node->radiation = radiation;
        node->density = density;
        node->pore = pore;
        node->pressure = pressure;
        node->displacement = displacement;
        node->x = node->equilibrium_x + (subject_x - node->equilibrium_x) * gravity_focus * pore * 0.06f;
        node->y = node->equilibrium_y + sinf(distance * 0.9f + input_energy * 4.0f) * displacement * 0.05f;
        node->z = node->equilibrium_z + (subject_z - node->equilibrium_z) * gravity_focus * pore * 0.06f;

        total_disturbance += node->disturbance;
        total_disruption += fabsf(node->pressure - node->density);
        total_displacement += node->displacement;
        total_pressure_density += node->pressure * node->density;
        total_radiation += node->radiation;
        total_pore_flux += node->pore;
        total_gravity_focus += gravity_focus;
        total_dispersal += bango_space_length3(node->x - node->equilibrium_x, node->y - node->equilibrium_y, node->z - node->equilibrium_z);
    }
    if (frame->node_count > 0) {
        float inv = 1.0f / (float)frame->node_count;
        frame->metrics.dispersal = total_dispersal * inv;
        frame->metrics.disturbance = total_disturbance * inv;
        frame->metrics.disruption = total_disruption * inv;
        frame->metrics.displacement = total_displacement * inv;
        frame->metrics.pressure_density = total_pressure_density * inv;
        frame->metrics.radiation = total_radiation * inv;
        frame->metrics.pore_flux = total_pore_flux * inv;
        frame->metrics.gravity_focus = total_gravity_focus * inv;
    }
    (void)dt;
}

float bango_space_frame_sample_displacement(const BangoSpaceFrame *frame, float world_x, float world_y, float world_z) {
    float weighted;
    float total_weight;
    int index;
    if (!frame || frame->node_count <= 0) return 0.0f;
    weighted = 0.0f;
    total_weight = 0.0f;
    for (index = 0; index < frame->node_count; ++index) {
        const BangoSpaceNode *node = &frame->nodes[index];
        float dx = node->equilibrium_x - world_x;
        float dy = node->equilibrium_y - world_y;
        float dz = node->equilibrium_z - world_z;
        float distance = bango_space_length3(dx, dy, dz);
        float weight = 1.0f / (0.2f + distance);
        weighted += node->displacement * weight;
        total_weight += weight;
    }
    return total_weight > 0.0f ? weighted / total_weight : 0.0f;
}