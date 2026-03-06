#include "egosphere.h"
#include <stdio.h>
#include <stdlib.h>

static const char *ctx_name(Context c) { return c == CONTEXT_COMBAT ? "COMBAT" : "HABIT"; }

int main(void) {
    Agent a;
    egosphere_init_agent(&a, "NPC_01");

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

        /* push into replay buffer; priority ~ abs(reward) */
        rb_push(&rb, state, action, reward, next_state, 0, fabs(reward) + 1e-3);

        /* update Q-table immediately (online) */
        q_update(&q, state, action, reward, next_state, 0);

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

    /* cleanup */
    rb_free(&rb);
    q_free(&q);
    dqn_free(&dqn);
    egosphere_free_agent(&a);
    return 0;
}

