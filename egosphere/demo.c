#include "egosphere.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#define DEMO_SAVE_PATH "egosphere_rivals.dat"

static const char *ctx_name(Context c) { return c == CONTEXT_COMBAT ? "COMBAT" : "HABIT"; }

int main(void) {
    Agent a;
    MindSphereRivalary rivals = {0};
    MindSphereRivalary reloaded = {0};
    MindSphereConfig config = mindsphere_default_config();
    RivalIdentity *marshal;
    char rival_summary[256];
    MindSphereNarrativeHooks hooks;

    egosphere_init_agent(&a, "NPC_01");
    config.planner_states = 24;
    config.planner_actions = 5;
    config.replay_capacity = 384;
    config.narrative_protocol_enabled = 1;
    mindsphere_init_with_config(&rivals, 4, &config);
    mindsphere_seed_player_profile(&rivals, "Player Echo", 4242u);
    marshal = mindsphere_add_antithentity(&rivals, "The Ashen Magistrate", "verdict-knight", 1337u);

    /* Initialize replay buffer, Q-learner and DQN */
    ReplayBuffer rb;
    rb_init(&rb, 1024, 0.999);

    QLearner q;
    /* small state space: combine context (2) x last_action (3) => 6 states */
    q_init(&q, 6, 3, 0.05, 0.95, 0.2);

    DQN dqn;
    /* features: simple one-hot over state (6) concatenated with action one-hot (3) -> we use state features only here */
    dqn_init(&dqn, 6, 3, 0.01, 0.95);

    int last_action = 0;
    for (int t = 0; t < 500; ++t) {
        Context ctx = (t % 50 == 0) ? CONTEXT_COMBAT : CONTEXT_HABIT;
        int state = (int)ctx * 3 + (last_action % 3);

        /* select action via Q-learner (epsilon-greedy) */
        int action = q_select_action(&q, state);
        /* derive reward probabilistically */
        double reward = 0.0;
        if (ctx == CONTEXT_HABIT) {
            if (action == 1) reward = (rand() % 100) < 70 ? 0.4 : -0.05;
            if (action == 2) reward = (rand() % 100) < 50 ? 0.6 : -0.2;
        } else {
            if (action == 0) reward = (rand() % 100) < 60 ? 0.3 : -0.4;
            if (action == 1) reward = (rand() % 100) < 65 ? 0.2 : -0.5;
            if (action == 2) reward = (rand() % 100) < 40 ? 1.0 : -1.0;
        }

        int next_last_action = action;
        int next_state = (int)ctx * 3 + (next_last_action % 3);

        mindsphere_record_player_style(
            &rivals,
            ctx == CONTEXT_COMBAT ? 0.75 : 0.35,
            action == 1 ? 0.75 : 0.35,
            action == 0 ? 0.70 : 0.25,
            action == 2 ? 0.80 : 0.30);

        /* push into replay buffer; priority ~ abs(reward) */
        rb_push(&rb, state, action, reward, next_state, 0, fabs(reward) + 1e-3);

        /* update Q-table immediately (online) */
        q_update(&q, state, action, reward, next_state, 0);
        if (marshal) {
            int rival_action = mindsphere_choose_action(marshal, state);
            int action_alignment = rival_action % 3;
            double rival_reward = reward - (action_alignment == action ? 0.1 : -0.05);
            mindsphere_record_outcome(&rivals, marshal, state, rival_action, rival_reward, next_state, 0);
            if (t % 75 == 10) {
                mindsphere_record_dialogue_choice(marshal, -0.03, 0.04, 0.02, 0.01);
                mindsphere_record_player_choice(&rivals, 0.02, 0.01, 0.03, -0.02);
            }
            if (t % 90 == 45) {
                mindsphere_record_consequence(marshal, 0.8, (t / 45) % 2, (t / 90) % 2 == 0);
                mindsphere_record_player_choice(&rivals, (t / 45) % 2 ? -0.04 : 0.05, 0.02, 0.0, 0.03);
            }
            if (t % 16 == 0) {
                (void)mindsphere_rehearse_rival(marshal, 12);
            }
        }

        /* occasionally perform batch training from buffer for DQN and Q (demonstration) */
        if (t % 8 == 0 && rb.count >= 16) {
            size_t batch_n = 16;
            size_t got = 0;
            ReplayBufferEntry *batch = rb_sample(&rb, batch_n, &got);
            if (batch && got) {
                for (size_t i = 0; i < got; ++i) {
                    /* simple state features: one-hot over 6 states */
                    double features[6] = {0};
                    double next_features[6] = {0};
                    int s = batch[i].state;
                    int ns = batch[i].next_state;
                    if (s >= 0 && s < 6) features[s] = 1.0;
                    if (ns >= 0 && ns < 6) next_features[ns] = 1.0;

                    /* train DQN on the sampled batch entry */
                    dqn_train(&dqn, features, batch[i].action, batch[i].reward, next_features, batch[i].done);

                    /* also perform Q update from samples (to show integration) */
                    q_update(&q, batch[i].state, batch[i].action, batch[i].reward, batch[i].next_state, batch[i].done);
                }
                free(batch);
            }
        }

        /* occasionally print status */
        if (t % 50 == 0) {
            printf("t=%03d ctx=%s action=%d reward=%+.2f rb_count=%zu q_sample=[", t, ctx_name(ctx), action, reward, rb.count);
            for (int a = 0; a < 3; ++a) printf(" %.3f", q_get(&q, state, a));
            printf(" ]\n");
        }

        last_action = next_last_action;
    }

    if (marshal) {
        mindsphere_describe_rival(marshal, rival_summary, sizeof(rival_summary));
        printf("rival before save: %s\n", rival_summary);
        printf("resonance before save: familiarity=%.2f reciprocity=%.2f tension=%.2f permeability=%.2f\n",
            marshal->player_resonance.familiarity,
            marshal->player_resonance.reciprocity,
            marshal->player_resonance.tension,
            marshal->player_resonance.permeability);
        mindsphere_collect_narrative_hooks(&rivals, &hooks);
        printf("narrative field: active=%d revelation=%.2f alliance=%.2f rupture=%.2f ending=%.2f omen=%.2f\n",
            hooks.active,
            hooks.revelation_pressure,
            hooks.alliance_pressure,
            hooks.rupture_pressure,
            hooks.ending_pressure,
            hooks.omen_pressure);
    }

    if (!mindsphere_save(&rivals, DEMO_SAVE_PATH)) {
        fprintf(stderr, "failed to save rival state to %s\n", DEMO_SAVE_PATH);
    } else if (!mindsphere_load(&reloaded, DEMO_SAVE_PATH)) {
        fprintf(stderr, "failed to reload rival state from %s\n", DEMO_SAVE_PATH);
    } else if (reloaded.count > 0) {
        mindsphere_describe_rival(&reloaded.rivals[0], rival_summary, sizeof(rival_summary));
        printf("rival after load:  %s\n", rival_summary);
        printf("reloaded planner: states=%d actions=%d replay_capacity=%zu\n", reloaded.config.planner_states, reloaded.config.planner_actions, reloaded.config.replay_capacity);
        printf("reloaded resonance: familiarity=%.2f reciprocity=%.2f tension=%.2f permeability=%.2f\n",
            reloaded.rivals[0].player_resonance.familiarity,
            reloaded.rivals[0].player_resonance.reciprocity,
            reloaded.rivals[0].player_resonance.tension,
            reloaded.rivals[0].player_resonance.permeability);
    }

    /* cleanup */
    mindsphere_free(&reloaded);
    mindsphere_free(&rivals);
    rb_free(&rb);
    q_free(&q);
    dqn_free(&dqn);
    egosphere_free_agent(&a);
    return 0;
}

