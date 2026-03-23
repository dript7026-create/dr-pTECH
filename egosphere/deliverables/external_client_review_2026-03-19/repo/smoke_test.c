#include "egosphere.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

#define SMOKE_SAVE_PATH "smoke_rivals.dat"

int main(void) {
    MindSphereConfig config = mindsphere_default_config();
    MindSphereRivalary source = {0};
    MindSphereRivalary loaded = {0};
    RivalIdentity *rival;
    MindSphereNarrativeHooks hooks;
    char before[256];
    char after[256];

    config.planner_states = 32;
    config.planner_actions = 4;
    config.replay_capacity = 96;
    config.replay_decay = 0.993;
    config.narrative_protocol_enabled = 1;

    assert(mindsphere_init_with_config(&source, 2, &config));
    mindsphere_seed_player_profile(&source, "Smoke Player", 1441u);
    rival = mindsphere_add_antithentity(&source, "Smoke Rival", "inspector", 777u);
    assert(rival != NULL);

    mindsphere_record_player_style(&source, 0.70, 0.45, 0.55, 0.85);
    mindsphere_record_outcome(&source, rival, 3, 2, 0.75, 9, 0);
    mindsphere_record_outcome(&source, rival, 9, 3, -0.45, 12, 0);
    mindsphere_record_outcome(&source, rival, 12, 1, 0.60, 15, 1);
    mindsphere_record_dialogue_choice(rival, 0.10, -0.05, 0.02, 0.04);
    mindsphere_record_consequence(rival, 0.75, 1, 0);
    mindsphere_record_player_choice(&source, 0.04, 0.02, 0.03, -0.01);
    assert(mindsphere_rehearse_rival(rival, 2) == 2);

    assert(rival->planner.nactions == 4);
    assert(rival->planner.nstates == 32);
    assert(rival->engagements == 3);
    assert(rival->morals.dialogue_choices == 1);
    assert(rival->morals.spared_count == 1);
    assert(rival->player_resonance.familiarity > 0.0);
    mindsphere_collect_narrative_hooks(&source, &hooks);
    assert(hooks.active == 1);
    assert(hooks.ending_pressure > 0.0);
    mindsphere_describe_rival(rival, before, sizeof(before));

    assert(mindsphere_save(&source, SMOKE_SAVE_PATH));
    assert(mindsphere_load(&loaded, SMOKE_SAVE_PATH));
    assert(loaded.count == 1);
    assert(loaded.config.planner_states == 32);
    assert(loaded.config.planner_actions == 4);
    assert(loaded.config.replay_capacity == 96);
    mindsphere_describe_rival(&loaded.rivals[0], after, sizeof(after));
    assert(strcmp(before, after) == 0);
    assert(loaded.rivals[0].replay.count == rival->replay.count);
    assert(loaded.rivals[0].planner.nactions == rival->planner.nactions);
    assert(loaded.rivals[0].planner.nstates == rival->planner.nstates);
    assert(loaded.rivals[0].engagements == rival->engagements);
    assert(loaded.rivals[0].morals.promises_broken == rival->morals.promises_broken);
    assert(loaded.rivals[0].player_resonance.familiarity == rival->player_resonance.familiarity);
    assert(strcmp(loaded.player_model.label, "Smoke Player") == 0);
    mindsphere_collect_narrative_hooks(&loaded, &hooks);
    assert(hooks.active == 1);
    assert(mindsphere_rehearse_all(&loaded, 1) == 1);

    printf("smoke-test ok: %s\n", after);

    mindsphere_free(&loaded);
    mindsphere_free(&source);
    return 0;
}