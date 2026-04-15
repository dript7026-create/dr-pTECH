#pragma bank 255

#include "../include/proghonorai.h"
#include "../submodules/HONORSPHERE/include/honorsphere.h"

static uint8_t proghonorai_clamp_u8(int16_t value) {
    if (value < 0) return 0u;
    if (value > 255) return 255u;
    return (uint8_t)value;
}

void proghonorai_init(ProgHonorAiContext *context, uint16_t world_seed, uint8_t level, uint8_t weapon_rank, uint8_t armor_rank) FARMERS_FEATHER_BANKED {
    uint8_t index;
    if (!context) return;

    context->world_seed = world_seed;
    context->commitment = (uint8_t)(56u + level * 10u + weapon_rank * 12u);
    context->patience = (uint8_t)(64u + armor_rank * 14u + level * 6u);
    context->footwork = (uint8_t)(72u + (world_seed & 0x1Fu));
    context->honor = (uint8_t)(96u + armor_rank * 10u + (world_seed & 0x0Fu));
    context->bond = (uint8_t)(48u + level * 8u);
    context->pressure = 0u;

    for (index = 0u; index < PROGHONORAI_PASSAGE_COUNT; ++index) {
        context->passage_bias[index] = (uint8_t)(((world_seed >> (index * 2u)) & 0x0Fu) * 5u + index * 7u);
    }
}

void proghonorai_record_movement(ProgHonorAiContext *context, uint8_t moved, uint8_t tile_kind) FARMERS_FEATHER_BANKED {
    if (!context || !moved) return;
    context->footwork = proghonorai_clamp_u8((int16_t)context->footwork + 3);
    if (tile_kind == 1u) {
        context->honor = proghonorai_clamp_u8((int16_t)context->honor + 1);
    } else {
        context->bond = proghonorai_clamp_u8((int16_t)context->bond + 1);
    }
    context->passage_bias[PROGHONORAI_PASSAGE_APPROACH] = proghonorai_clamp_u8((int16_t)context->passage_bias[PROGHONORAI_PASSAGE_APPROACH] + 1);
}

void proghonorai_record_rake(ProgHonorAiContext *context, uint8_t connected) FARMERS_FEATHER_BANKED {
    if (!context) return;
    context->commitment = proghonorai_clamp_u8((int16_t)context->commitment + (connected ? 8 : 4));
    context->pressure = proghonorai_clamp_u8((int16_t)context->pressure + (connected ? 7 : 3));
    context->honor = proghonorai_clamp_u8((int16_t)context->honor + (connected ? 1 : -2));
    context->passage_bias[PROGHONORAI_PASSAGE_WINDUP] = proghonorai_clamp_u8((int16_t)context->passage_bias[PROGHONORAI_PASSAGE_WINDUP] + 2);
}

void proghonorai_record_use(ProgHonorAiContext *context, uint8_t restorative) FARMERS_FEATHER_BANKED {
    if (!context || !restorative) return;
    context->patience = proghonorai_clamp_u8((int16_t)context->patience + 5);
    context->honor = proghonorai_clamp_u8((int16_t)context->honor + 4);
    context->bond = proghonorai_clamp_u8((int16_t)context->bond + 3);
    context->pressure = proghonorai_clamp_u8((int16_t)context->pressure - 6);
    context->passage_bias[PROGHONORAI_PASSAGE_RENDER] = proghonorai_clamp_u8((int16_t)context->passage_bias[PROGHONORAI_PASSAGE_RENDER] + 2);
}

void proghonorai_update(ProgHonorAiContext *context, uint8_t phase, uint8_t boss_active, uint8_t health, uint8_t max_health) FARMERS_FEATHER_BANKED {
    uint8_t missing_health;
    if (!context) return;

    missing_health = (max_health > health) ? (uint8_t)(max_health - health) : 0u;
    context->pressure = proghonorai_clamp_u8((int16_t)(phase * 18u) + (boss_active ? 68 : 0) + missing_health * 14u);
    context->bond = proghonorai_clamp_u8((int16_t)context->bond + (boss_active ? 1 : 0));
    context->honor = proghonorai_clamp_u8((int16_t)context->honor + ((context->patience > context->commitment) ? 1 : 0) - (boss_active ? 1 : 0));
    context->passage_bias[PROGHONORAI_PASSAGE_SPAWN] = proghonorai_clamp_u8((int16_t)context->passage_bias[PROGHONORAI_PASSAGE_SPAWN] + (boss_active ? 1 : 0));
}

void proghonorai_route(const ProgHonorAiContext *context, ProgHonorAiPassage passage, uint8_t threat, uint8_t tier, ProgHonorAiDirective *directive) FARMERS_FEATHER_BANKED {
    HonorSphereNode node;
    uint8_t score;
    if (!context || !directive) return;

    node.respect = proghonorai_clamp_u8((int16_t)context->honor + context->bond / 2u + context->patience / 3u);
    node.tension = proghonorai_clamp_u8((int16_t)context->pressure + context->commitment / 2u - context->patience / 4u);
    node.pressure = context->pressure;
    node.channel_bias = context->passage_bias[passage];
    score = honorsphere_score(&node, (uint8_t)passage, threat, tier);

    directive->passage_score = score;
    directive->tier_delta = (score > 172u && threat > 140u) ? 1 : ((score < 84u && tier > 0u) ? -1 : 0);
    directive->windup_delta = (score > 164u) ? -3 : ((score < 76u) ? 2 : 0);
    directive->lunge_frames_delta = (score > 168u) ? 2 : ((context->honor > 150u) ? 1 : 0);
    directive->stun_delta = (context->honor > 144u) ? 2 : ((score > 176u) ? -1 : 0);
    directive->speed_delta = (score > 156u && context->commitment > context->patience) ? 1 : ((context->honor > 148u) ? -1 : 0);
    directive->visual_pressure = proghonorai_clamp_u8((int16_t)score / 2u + context->pressure / 2u);
    directive->render_mode = (context->honor > 150u) ? 2u : ((context->pressure > 140u) ? 1u : 0u);

    directive->windup_delta += honorsphere_signed_delta(score, 2u);
}