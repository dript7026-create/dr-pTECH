#include "egosphere.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <time.h>
#include <stdint.h>
#include <math.h>

static void memory_ensure_capacity(Memory *m) {
    if (m->count >= m->capacity) {
        size_t newcap = m->capacity ? m->capacity * 2 : 8;
        Experience *n = (Experience*)realloc(m->items, newcap * sizeof(Experience));
        if (!n) return;
        m->items = n;
        m->capacity = newcap;
    }
}

void egosphere_init_agent(Agent *a, const char *name) {
    size_t n = strlen(name) + 1;
    a->name = (char*)malloc(n);
    if (a->name) memcpy(a->name, name, n);
    srand((unsigned)time(NULL) ^ (unsigned)(uintptr_t)a);
    /* initialize tier weights */
    a->id.weight = 0.5 + ((double)rand() / RAND_MAX) * 0.5;      /* impulsive */
    a->ego.weight = 0.4 + ((double)rand() / RAND_MAX) * 0.6;     /* reasoning */
    a->superego.weight = 0.1 + ((double)rand() / RAND_MAX) * 0.5;/* rules/morals */
    /* initialize priors */
    a->priors.pattern_trust = 0.2 + ((double)rand() / RAND_MAX) * 0.6; /* 0..1 */
    for (int i = 0; i < 3; ++i) {
        a->priors.bias_action[i] = (((double)rand() / RAND_MAX) - 0.5) * 0.4; /* small bias */
    }
    a->memory.items = NULL;
    a->memory.count = 0;
    a->memory.capacity = 0;
}

void egosphere_free_agent(Agent *a) {
    if (!a) return;
    free(a->name);
    free(a->memory.items);
    a->name = NULL;
    a->memory.items = NULL;
    a->memory.count = 0;
    a->memory.capacity = 0;
}

void egosphere_record_experience(Agent *a, int action, double reward, Context ctx) {
    memory_ensure_capacity(&a->memory);
    if (a->memory.count < a->memory.capacity) {
        a->memory.items[a->memory.count].action = action;
        a->memory.items[a->memory.count].reward = reward;
        a->memory.items[a->memory.count].context = ctx;
        a->memory.count++;
    }
}

/* compute smoothed average reward for action in given context */
static double avg_reward_for(Agent *a, int action, Context ctx) {
    double sum = 0.0;
    int cnt = 0;
    for (size_t i = 0; i < a->memory.count; ++i) {
        Experience *e = &a->memory.items[i];
        if (e->action == action && e->context == ctx) {
            sum += e->reward;
            cnt++;
        }
    }
    if (cnt == 0) return 0.0;
    return sum / cnt;
}

/* Decide action using a mix of tiers, priors, habit and context-sensitive reasoning. */
int egosphere_decide_action(Agent *a, Context ctx) {
    /* candidate actions: 0,1,2 */
    double scores[3] = {0};

    /* habit: prefer last action slightly */
    int last_action = -1;
    if (a->memory.count) last_action = a->memory.items[a->memory.count - 1].action;

    for (int act = 0; act < 3; ++act) {
        double expected = avg_reward_for(a, act, ctx);

        /* priors: pattern_trust amplifies reliance on expected value */
        expected = expected * (1.0 + a->priors.pattern_trust);

        /* incorporate bias (can be maladaptive) */
        expected += a->priors.bias_action[act];

        /* id: randomness and urgency, gives exploration potential */
        double id_component = a->id.weight * (((double)rand() / RAND_MAX) * 0.5);

        /* ego: rational expected utility (prefers higher expected reward)
           in combat, ego importance increases; in habit contexts, ego focuses on efficiency */
        double ego_scale = a->ego.weight * (ctx == CONTEXT_COMBAT ? 1.2 : 0.9);
        double ego_component = ego_scale * expected;

        /* superego: applies conservative penalty to very risky actions (negative expected reward) */
        double superego_component = a->superego.weight * (expected > 0.0 ? expected * 0.5 : expected * 1.0);

        /* habit bonus */
        double habit_bonus = 0.0;
        if (last_action == act) {
            habit_bonus = 0.1 * (1.0 + a->priors.pattern_trust);
        }

        /* combine */
        scores[act] = id_component + ego_component + superego_component + habit_bonus;

        /* context-specific tactical modifiers for combat: action 2 considered high-risk/high-reward */
        if (ctx == CONTEXT_COMBAT && act == 2) {
            scores[act] += a->id.weight * 0.2; /* reflexive aggressive push */
        }
    }

    /* pick best score, with small tie-breaker randomness */
    int best = 0;
    double best_score = scores[0];
    for (int i = 1; i < 3; ++i) {
        double s = scores[i] + (((double)rand() / RAND_MAX) * 1e-6);
        if (s > best_score) { best_score = s; best = i; }
    }

    return best;
}

void egosphere_update(Agent *a, int action, double reward, Context ctx) {
    egosphere_record_experience(a, action, reward, ctx);

    /* learn: adjust tier weights slightly toward outcomes */
    double lr = 0.02;
    /* ego learns faster in combat */
    double ego_lr = (ctx == CONTEXT_COMBAT) ? lr * 1.5 : lr;

    a->id.weight += lr * reward * 0.3;
    a->ego.weight += ego_lr * reward * 0.7;
    a->superego.weight += lr * reward * 0.2;

    /* update priors (confirmation bias): if action rewarded, increase bias toward it */
    double bias_lr = 0.01;
    a->priors.bias_action[action] += bias_lr * reward;
    /* pattern trust increases with consistent positive rewards */
    double recent = 0.0;
    int count = 0;
    for (size_t i = (a->memory.count > 5 ? a->memory.count - 5 : 0); i < a->memory.count; ++i) {
        recent += a->memory.items[i].reward;
        count++;
    }
    if (count) recent /= count;
    a->priors.pattern_trust += 0.005 * recent; /* small drift */

    /* clamp sensible ranges */
    if (a->id.weight < 0.0) a->id.weight = 0.0;
    if (a->ego.weight < 0.0) a->ego.weight = 0.0;
    if (a->superego.weight < 0.0) a->superego.weight = 0.0;
    if (a->priors.pattern_trust < -1.0) a->priors.pattern_trust = -1.0;
    if (a->priors.pattern_trust > 2.0) a->priors.pattern_trust = 2.0;
}

/* ---------------- Replay Buffer Implementation ---------------- */

int rb_init(ReplayBuffer *rb, size_t capacity, double decay) {
    if (!rb || capacity == 0) return 0;
    rb->entries = (ReplayBufferEntry*)calloc(capacity, sizeof(ReplayBufferEntry));
    if (!rb->entries) return 0;
    rb->capacity = capacity;
    rb->count = 0;
    rb->next_index = 0;
    rb->total_priority = 0.0;
    rb->decay = decay > 0.0 ? decay : 1.0;
    rb->t = 0;
    return 1;
}

void rb_free(ReplayBuffer *rb) {
    if (!rb) return;
    free(rb->entries);
    rb->entries = NULL;
    rb->capacity = rb->count = rb->next_index = 0;
    rb->total_priority = 0.0;
}

static void rb_apply_decay_if_needed(ReplayBuffer *rb) {
    rb->t++;
    if (rb->decay >= 1.0) return;
    if (rb->t % 128 == 0) {
        double tot = 0.0;
        for (size_t i = 0; i < rb->count; ++i) {
            rb->entries[i].priority *= rb->decay;
            tot += rb->entries[i].priority;
        }
        rb->total_priority = tot;
    }
}

void rb_push(ReplayBuffer *rb, int state, int action, double reward, int next_state, int done, double priority) {
    if (!rb || !rb->entries) return;
    /* clamp priority */
    double p = fabs(priority) + 1e-6;
    /* if inserting into full buffer, subtract overwritten priority */
    if (rb->count < rb->capacity) {
        size_t idx = rb->next_index;
        rb->entries[idx].state = state;
        rb->entries[idx].action = action;
        rb->entries[idx].reward = reward;
        rb->entries[idx].next_state = next_state;
        rb->entries[idx].done = done;
        rb->entries[idx].priority = p;
        rb->entries[idx].timestamp = rb->t++;
        rb->total_priority += p;
        rb->next_index = (rb->next_index + 1) % rb->capacity;
        rb->count++;
    } else {
        size_t idx = rb->next_index;
        /* subtract old */
        rb->total_priority -= rb->entries[idx].priority;
        rb->entries[idx].state = state;
        rb->entries[idx].action = action;
        rb->entries[idx].reward = reward;
        rb->entries[idx].next_state = next_state;
        rb->entries[idx].done = done;
        rb->entries[idx].priority = p;
        rb->entries[idx].timestamp = rb->t++;
        rb->total_priority += p;
        rb->next_index = (rb->next_index + 1) % rb->capacity;
    }
    rb_apply_decay_if_needed(rb);
}

ReplayBufferEntry *rb_sample(ReplayBuffer *rb, size_t sample_count, size_t *out_count) {
    if (!rb || rb->count == 0) { if (out_count) *out_count = 0; return NULL; }
    size_t n = sample_count;
    if (n == 0) { if (out_count) *out_count = 0; return NULL; }
    ReplayBufferEntry *batch = (ReplayBufferEntry*)malloc(n * sizeof(ReplayBufferEntry));
    if (!batch) { if (out_count) *out_count = 0; return NULL; }

    /* simple proportional sampling by priority (O(N) per sample). To avoid overlapping
       memory issues, we copy out entries into a new array. */
    for (size_t i = 0; i < n; ++i) {
        double r = ((double)rand() / RAND_MAX) * rb->total_priority;
        double cum = 0.0;
        size_t chosen = 0;
        for (size_t j = 0; j < rb->count; ++j) {
            cum += rb->entries[j].priority;
            if (r <= cum) { chosen = j; break; }
        }
        /* copy selected entry */
        batch[i] = rb->entries[chosen];
    }
    if (out_count) *out_count = n;
    return batch;
}

void rb_update_priority(ReplayBuffer *rb, size_t index, double new_priority) {
    if (!rb || rb->count == 0 || index >= rb->count) return;
    double p = fabs(new_priority) + 1e-6;
    rb->total_priority = rb->total_priority - rb->entries[index].priority + p;
    rb->entries[index].priority = p;
}

/* ---------------- Tabular Q-learner Implementation ---------------- */

int q_init(QLearner *q, int nstates, int nactions, double alpha, double gamma, double epsilon) {
    if (!q || nstates <= 0 || nactions <= 0) return 0;
    q->nstates = nstates;
    q->nactions = nactions;
    q->Q = (double*)calloc((size_t)nstates * nactions, sizeof(double));
    if (!q->Q) return 0;
    q->alpha = alpha;
    q->gamma = gamma;
    q->epsilon = epsilon;
    return 1;
}

void q_free(QLearner *q) {
    if (!q) return;
    free(q->Q);
    q->Q = NULL;
}

double q_get(QLearner *q, int state, int action) {
    if (!q) return 0.0;
    if (state < 0 || state >= q->nstates || action < 0 || action >= q->nactions) return 0.0;
    return q->Q[state * q->nactions + action];
}

int q_select_action(QLearner *q, int state) {
    if (!q) return 0;
    if (((double)rand() / RAND_MAX) < q->epsilon) return rand() % q->nactions;
    double best = -INFINITY; int best_a = 0;
    for (int a = 0; a < q->nactions; ++a) {
        double v = q_get(q, state, a);
        if (v > best) { best = v; best_a = a; }
    }
    return best_a;
}

void q_update(QLearner *q, int state, int action, double reward, int next_state, int done) {
    if (!q) return;
    double qsa = q_get(q, state, action);
    double max_next = 0.0;
    if (!done) {
        max_next = q_get(q, next_state, 0);
        for (int a = 1; a < q->nactions; ++a) {
            double v = q_get(q, next_state, a);
            if (v > max_next) max_next = v;
        }
    }
    double target = reward + (done ? 0.0 : q->gamma * max_next);
    q->Q[state * q->nactions + action] += q->alpha * (target - qsa);
}

/* ---------------- Simple Linear DQN Implementation ---------------- */

int dqn_init(DQN *d, int nfeatures, int nactions, double lr, double gamma) {
    if (!d || nfeatures <= 0 || nactions <= 0) return 0;
    d->nfeatures = nfeatures;
    d->nactions = nactions;
    d->weights = (double*)calloc((size_t)nactions * nfeatures, sizeof(double));
    if (!d->weights) return 0;
    d->lr = lr;
    d->gamma = gamma;
    return 1;
}

void dqn_free(DQN *d) {
    if (!d) return;
    free(d->weights);
    d->weights = NULL;
}

void dqn_predict(DQN *d, const double *features, double *out_q) {
    for (int a = 0; a < d->nactions; ++a) {
        double sum = 0.0;
        for (int f = 0; f < d->nfeatures; ++f) sum += d->weights[a * d->nfeatures + f] * features[f];
        out_q[a] = sum;
    }
}

void dqn_train(DQN *d, const double *features, int action, double reward, const double *next_features, int done) {
    /* compute current Q and next Q */
    double *q_cur = (double*)malloc(sizeof(double) * d->nactions);
    double *q_next = (double*)malloc(sizeof(double) * d->nactions);
    if (!q_cur || !q_next) { free(q_cur); free(q_next); return; }
    dqn_predict(d, features, q_cur);
    dqn_predict(d, next_features, q_next);
    double max_next = q_next[0];
    for (int a = 1; a < d->nactions; ++a) if (q_next[a] > max_next) max_next = q_next[a];
    double target = reward + (done ? 0.0 : d->gamma * max_next);
    double td = target - q_cur[action];

    /* gradient descent on linear weights: w_a <- w_a + lr * td * features */
    for (int f = 0; f < d->nfeatures; ++f) {
        d->weights[action * d->nfeatures + f] += d->lr * td * features[f];
    }

    free(q_cur); free(q_next);
}


