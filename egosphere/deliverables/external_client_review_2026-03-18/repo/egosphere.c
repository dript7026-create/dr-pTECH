#include "egosphere.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <time.h>
#include <stdint.h>
#include <math.h>

#define MINDSPHERE_SAVE_MAGIC 0x4D534652u /* MSFR */
#define MINDSPHERE_SAVE_VERSION 4u

enum {
    PERSONALITY_ASSERTIVE = 0,
    PERSONALITY_CURIOUS = 1,
    PERSONALITY_EMPATHIC = 2,
    PERSONALITY_DISCIPLINED = 3,
    PERSONALITY_VOLATILE = 4,
    PERSONALITY_PATIENT = 5,
};

enum {
    INTELLECT_FORESIGHT = 0,
    INTELLECT_PATTERN = 1,
    INTELLECT_ABSTRACTION = 2,
    INTELLECT_ADAPTABILITY = 3,
    INTELLECT_SOCIAL = 4,
    INTELLECT_MEMORY = 5,
};

enum {
    ETHIC_MERCY = 0,
    ETHIC_DUTY = 1,
    ETHIC_CANDOR = 2,
    ETHIC_AMBITION = 3,
    ETHIC_RECIPROCITY = 4,
    ETHIC_RESTRAINT = 5,
};

static void memory_ensure_capacity(Memory *m) {
    if (m->count >= m->capacity) {
        size_t newcap = m->capacity ? m->capacity * 2 : 8;
        Experience *n = (Experience*)realloc(m->items, newcap * sizeof(Experience));
        if (!n) return;
        m->items = n;
        m->capacity = newcap;
    }
}

static int write_u32(FILE *fp, uint32_t value) {
    return fwrite(&value, sizeof(value), 1, fp) == 1;
}

static int write_u64(FILE *fp, uint64_t value) {
    return fwrite(&value, sizeof(value), 1, fp) == 1;
}

static int write_double(FILE *fp, double value) {
    return fwrite(&value, sizeof(value), 1, fp) == 1;
}

static int write_string(FILE *fp, const char *value) {
    uint32_t len = value ? (uint32_t)strlen(value) : 0u;
    if (!write_u32(fp, len)) return 0;
    if (len == 0) return 1;
    return fwrite(value, 1, len, fp) == len;
}

static int read_u32(FILE *fp, uint32_t *value) {
    return fread(value, sizeof(*value), 1, fp) == 1;
}

static int read_u64(FILE *fp, uint64_t *value) {
    return fread(value, sizeof(*value), 1, fp) == 1;
}

static int read_double(FILE *fp, double *value) {
    return fread(value, sizeof(*value), 1, fp) == 1;
}

static int read_string(FILE *fp, char **value) {
    uint32_t len = 0;
    char *buffer;

    if (!read_u32(fp, &len)) return 0;
    buffer = (char*)malloc((size_t)len + 1u);
    if (!buffer) return 0;
    if (len > 0 && fread(buffer, 1, len, fp) != len) {
        free(buffer);
        return 0;
    }
    buffer[len] = '\0';
    *value = buffer;
    return 1;
}

static void free_loaded_rivals(MindSphereRivalary *ms) {
    size_t i;
    if (!ms || !ms->rivals) return;
    for (i = 0; i < ms->count; ++i) {
        egosphere_free_agent(&ms->rivals[i].psyche);
        rb_free(&ms->rivals[i].replay);
        q_free(&ms->rivals[i].planner);
    }
    free(ms->rivals);
    ms->rivals = NULL;
    ms->count = 0;
    ms->capacity = 0;
    ms->tick = 0;
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
    if (!q || !q->Q) return 0.0;
    if (state < 0 || state >= q->nstates || action < 0 || action >= q->nactions) return 0.0;
    return q->Q[state * q->nactions + action];
}

int q_select_action(QLearner *q, int state) {
    if (!q || !q->Q || q->nactions <= 0 || q->nstates <= 0) return 0;
    if (state < 0 || state >= q->nstates) return 0;
    if (((double)rand() / RAND_MAX) < q->epsilon) return rand() % q->nactions;
    double best = -INFINITY; int best_a = 0;
    for (int a = 0; a < q->nactions; ++a) {
        double v = q_get(q, state, a);
        if (v > best) { best = v; best_a = a; }
    }
    return best_a;
}

void q_update(QLearner *q, int state, int action, double reward, int next_state, int done) {
    if (!q || !q->Q) return;
    if (state < 0 || state >= q->nstates) return;
    if (action < 0 || action >= q->nactions) return;
    double qsa = q_get(q, state, action);
    double max_next = 0.0;
    if (!done) {
        if (next_state < 0 || next_state >= q->nstates) return;
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
    if (!d || !d->weights || !features || !out_q || d->nactions <= 0 || d->nfeatures <= 0) return;
    for (int a = 0; a < d->nactions; ++a) {
        double sum = 0.0;
        for (int f = 0; f < d->nfeatures; ++f) sum += d->weights[a * d->nfeatures + f] * features[f];
        out_q[a] = sum;
    }
}

void dqn_train(DQN *d, const double *features, int action, double reward, const double *next_features, int done) {
    if (!d || !d->weights || !features || !next_features) return;
    if (action < 0 || action >= d->nactions) return;
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

/* ---------------- MindSphereRivalary Implementation ---------------- */

static void copy_cstr(char *dest, size_t dest_size, const char *src) {
    if (!dest || dest_size == 0) return;
    if (!src) {
        dest[0] = '\0';
        return;
    }
    strncpy(dest, src, dest_size - 1);
    dest[dest_size - 1] = '\0';
}

static double clamp_range(double value, double min_value, double max_value) {
    if (value < min_value) return min_value;
    if (value > max_value) return max_value;
    return value;
}

static int normalize_index(int value, int count) {
    if (count <= 0) return 0;
    value %= count;
    if (value < 0) value += count;
    return value;
}

static double clamp_unit(double value) {
    return clamp_range(value, 0.0, 1.0);
}

static unsigned int mindsphere_prng_step(unsigned int *state) {
    unsigned int value = *state ? *state : 0xA341316Cu;
    value ^= value << 13;
    value ^= value >> 17;
    value ^= value << 5;
    *state = value;
    return value;
}

static double mindsphere_seeded_unit(unsigned int *state) {
    return (double)(mindsphere_prng_step(state) & 0xFFFFu) / 65535.0;
}

static double trait_similarity(const double *lhs, const double *rhs) {
    double total = 0.0;
    int i;
    for (i = 0; i < MINDSPHERE_GENOME_TRAITS; ++i) {
        total += 1.0 - fabs(lhs[i] - rhs[i]);
    }
    return total / (double)MINDSPHERE_GENOME_TRAITS;
}

void mindsphere_seed_actor_profile(MindActorProfile *profile, const char *label, unsigned int seed) {
    unsigned int state = seed ^ 0x9E3779B9u;
    int i;
    if (!profile) return;
    memset(profile, 0, sizeof(*profile));
    copy_cstr(profile->label, sizeof(profile->label), label ? label : "actor");
    for (i = 0; i < MINDSPHERE_GENOME_TRAITS; ++i) {
        profile->genome.personality[i] = clamp_unit(0.28 + mindsphere_seeded_unit(&state) * 0.52);
        profile->genome.intellect[i] = clamp_unit(0.24 + mindsphere_seeded_unit(&state) * 0.58);
        profile->genome.ethics[i] = clamp_unit(0.22 + mindsphere_seeded_unit(&state) * 0.56);
    }
    profile->consciousness.unconscious_pull = clamp_unit(0.25 + mindsphere_seeded_unit(&state) * 0.35);
    profile->consciousness.subconscious_pull = clamp_unit(0.28 + mindsphere_seeded_unit(&state) * 0.35);
    profile->consciousness.conscious_pull = clamp_unit(0.24 + mindsphere_seeded_unit(&state) * 0.36);
    profile->consciousness.peripheral_awareness = clamp_unit(0.16 + mindsphere_seeded_unit(&state) * 0.32);
    profile->consciousness.discovery_drive = clamp_unit(0.20 + mindsphere_seeded_unit(&state) * 0.42);
    for (i = 0; i < MINDSPHERE_FREQUENCY_BANDS; ++i) {
        profile->consciousness.frequency[i] = clamp_unit(0.18 + mindsphere_seeded_unit(&state) * 0.46);
    }
    profile->narrative.active = 0;
}

static void mindsphere_init_resonance_link(MindResonanceLink *link) {
    if (!link) return;
    memset(link, 0, sizeof(*link));
    link->permeability = 0.2;
}

static void mindsphere_init_default_player_profile(MindSphereRivalary *ms) {
    if (!ms) return;
    mindsphere_seed_actor_profile(&ms->player_model, "player", 0xC0DEFACEu);
    ms->player_model.consciousness.peripheral_awareness = clamp_unit(ms->player_model.consciousness.peripheral_awareness + 0.12);
    memset(&ms->collective_field, 0, sizeof(ms->collective_field));
    memset(&ms->dormant_narrative, 0, sizeof(ms->dormant_narrative));
}

void mindsphere_seed_player_profile(MindSphereRivalary *ms, const char *label, unsigned int seed) {
    if (!ms) return;
    mindsphere_seed_actor_profile(&ms->player_model, label ? label : "player", seed);
    ms->player_model.consciousness.peripheral_awareness = clamp_unit(ms->player_model.consciousness.peripheral_awareness + 0.12);
}

static void mindsphere_init_histories(RivalIdentity *rival) {
    if (!rival) return;
    memset(&rival->tactics, 0, sizeof(rival->tactics));
    memset(&rival->morals, 0, sizeof(rival->morals));
    rival->tactics.last_action = -1;
    rival->morals.mercy = 0.5;
    rival->morals.duty = 0.5;
    rival->morals.candor = 0.5;
    rival->morals.ambition = 0.5;
    mindsphere_seed_actor_profile(&rival->self_model, rival->name, (unsigned int)(0x51ED270Bu ^ (unsigned int)rival->id));
    mindsphere_init_resonance_link(&rival->player_resonance);
}

static void mindsphere_record_tactic_history(RivalIdentity *rival, int action, double reward) {
    int slot;
    int last_slot;
    double action_ratio;
    double positive_weight;
    double negative_weight;
    if (!rival) return;
    slot = normalize_index(action, MINDSPHERE_STYLE_ACTION_SLOTS);
    last_slot = rival->tactics.last_action;
    rival->tactics.action_uses[slot] += 1;
    if (reward >= 0.0) rival->tactics.action_successes[slot] += 1;
    else rival->tactics.action_failures[slot] += 1;
    if (last_slot >= 0 && last_slot < MINDSPHERE_STYLE_ACTION_SLOTS) {
        rival->tactics.combo_links[last_slot][slot] += 1;
        if (slot != last_slot) {
            rival->tactics.combo_commitment = clamp_unit(rival->tactics.combo_commitment + 0.025 * (reward >= 0.0 ? 1.0 : -0.35));
        }
    }
    action_ratio = (double)slot / (double)(MINDSPHERE_STYLE_ACTION_SLOTS - 1);
    positive_weight = reward > 0.0 ? reward : 0.0;
    negative_weight = reward < 0.0 ? -reward : 0.0;
    rival->tactics.pressure_bias = clamp_unit(rival->tactics.pressure_bias + positive_weight * (0.03 + 0.05 * action_ratio) - negative_weight * 0.015);
    rival->tactics.spacing_bias = clamp_unit(rival->tactics.spacing_bias + positive_weight * (0.03 + 0.05 * (1.0 - action_ratio)) - negative_weight * 0.015);
    if (last_slot >= 0 && slot != last_slot) {
        rival->tactics.counter_bias = clamp_unit(rival->tactics.counter_bias + positive_weight * 0.04 - negative_weight * 0.01);
    } else {
        rival->tactics.counter_bias = clamp_unit(rival->tactics.counter_bias - negative_weight * 0.005);
    }
    rival->tactics.last_action = slot;
}

void mindsphere_record_dialogue_choice(RivalIdentity *rival, double mercy_delta, double duty_delta, double candor_delta, double ambition_delta) {
    if (!rival) return;
    rival->morals.dialogue_choices += 1;
    rival->morals.mercy = clamp_unit(rival->morals.mercy + mercy_delta);
    rival->morals.duty = clamp_unit(rival->morals.duty + duty_delta);
    rival->morals.candor = clamp_unit(rival->morals.candor + candor_delta);
    rival->morals.ambition = clamp_unit(rival->morals.ambition + ambition_delta);
    rival->self_model.genome.ethics[ETHIC_MERCY] = clamp_unit(rival->self_model.genome.ethics[ETHIC_MERCY] + mercy_delta);
    rival->self_model.genome.ethics[ETHIC_DUTY] = clamp_unit(rival->self_model.genome.ethics[ETHIC_DUTY] + duty_delta);
    rival->self_model.genome.ethics[ETHIC_CANDOR] = clamp_unit(rival->self_model.genome.ethics[ETHIC_CANDOR] + candor_delta);
    rival->self_model.genome.ethics[ETHIC_AMBITION] = clamp_unit(rival->self_model.genome.ethics[ETHIC_AMBITION] + ambition_delta);
    rival->self_model.narrative.revelation_pressure = clamp_unit(rival->self_model.narrative.revelation_pressure + 0.03 * fabs(candor_delta));
    rival->self_model.narrative.alliance_pressure = clamp_unit(rival->self_model.narrative.alliance_pressure + 0.03 * mercy_delta + 0.02 * duty_delta);
    rival->self_model.narrative.rupture_pressure = clamp_unit(rival->self_model.narrative.rupture_pressure + 0.03 * ambition_delta - 0.02 * mercy_delta);
}

void mindsphere_record_consequence(RivalIdentity *rival, double severity, int spared_opponent, int promise_kept) {
    double weight;
    if (!rival) return;
    weight = fabs(severity);
    if (spared_opponent) {
        rival->morals.spared_count += 1;
        rival->morals.mercy = clamp_unit(rival->morals.mercy + 0.08 * weight);
        rival->morals.ambition = clamp_unit(rival->morals.ambition - 0.03 * weight);
    } else {
        rival->morals.punished_count += 1;
        rival->morals.mercy = clamp_unit(rival->morals.mercy - 0.06 * weight);
        rival->morals.ambition = clamp_unit(rival->morals.ambition + 0.05 * weight);
    }
    if (promise_kept) {
        rival->morals.promises_kept += 1;
        rival->morals.duty = clamp_unit(rival->morals.duty + 0.06 * weight);
        rival->morals.candor = clamp_unit(rival->morals.candor + 0.04 * weight);
    } else {
        rival->morals.promises_broken += 1;
        rival->morals.duty = clamp_unit(rival->morals.duty - 0.05 * weight);
        rival->morals.candor = clamp_unit(rival->morals.candor - 0.06 * weight);
    }
    rival->self_model.genome.ethics[ETHIC_RECIPROCITY] = clamp_unit(0.9 * rival->self_model.genome.ethics[ETHIC_RECIPROCITY] + 0.1 * (promise_kept ? 1.0 : 0.0));
    rival->self_model.genome.ethics[ETHIC_RESTRAINT] = clamp_unit(0.9 * rival->self_model.genome.ethics[ETHIC_RESTRAINT] + 0.1 * (spared_opponent ? 1.0 : 0.0));
    rival->self_model.narrative.ending_pressure = clamp_unit(rival->self_model.narrative.ending_pressure + 0.04 * weight);
    rival->self_model.narrative.omen_pressure = clamp_unit(rival->self_model.narrative.omen_pressure + 0.03 * weight * (promise_kept ? 0.5 : 1.0));
}

MindSphereConfig mindsphere_default_config(void) {
    MindSphereConfig config;
    config.replay_capacity = 256;
    config.replay_decay = 0.997;
    config.planner_states = MINDSPHERE_DEFAULT_STATES;
    config.planner_actions = MINDSPHERE_ACTION_COUNT;
    config.planner_alpha = 0.08;
    config.planner_gamma = 0.92;
    config.planner_epsilon = 0.18;
    config.narrative_protocol_enabled = 0;
    return config;
}

int mindsphere_init(MindSphereRivalary *ms, size_t capacity) {
    MindSphereConfig config = mindsphere_default_config();
    return mindsphere_init_with_config(ms, capacity, &config);
}

int mindsphere_init_with_config(MindSphereRivalary *ms, size_t capacity, const MindSphereConfig *config) {
    MindSphereConfig resolved;
    if (!ms || capacity == 0) return 0;
    resolved = config ? *config : mindsphere_default_config();
    if (resolved.replay_capacity == 0) resolved.replay_capacity = 256;
    if (resolved.replay_decay <= 0.0 || resolved.replay_decay > 1.0) resolved.replay_decay = 0.997;
    if (resolved.planner_states <= 0) resolved.planner_states = MINDSPHERE_DEFAULT_STATES;
    if (resolved.planner_actions <= 0) resolved.planner_actions = MINDSPHERE_ACTION_COUNT;
    if (resolved.planner_alpha <= 0.0) resolved.planner_alpha = 0.08;
    if (resolved.planner_gamma <= 0.0) resolved.planner_gamma = 0.92;
    if (resolved.planner_epsilon < 0.0) resolved.planner_epsilon = 0.18;
    if (resolved.narrative_protocol_enabled < 0) resolved.narrative_protocol_enabled = 0;
    ms->rivals = (RivalIdentity*)calloc(capacity, sizeof(RivalIdentity));
    if (!ms->rivals) return 0;
    ms->count = 0;
    ms->capacity = capacity;
    ms->tick = 0;
    ms->config = resolved;
    mindsphere_init_default_player_profile(ms);
    return 1;
}

void mindsphere_free(MindSphereRivalary *ms) {
    size_t i;
    if (!ms) return;
    for (i = 0; i < ms->count; ++i) {
        egosphere_free_agent(&ms->rivals[i].psyche);
        rb_free(&ms->rivals[i].replay);
        q_free(&ms->rivals[i].planner);
    }
    free(ms->rivals);
    ms->rivals = NULL;
    ms->count = 0;
    ms->capacity = 0;
    ms->tick = 0;
    ms->config = mindsphere_default_config();
    memset(&ms->player_model, 0, sizeof(ms->player_model));
    memset(&ms->collective_field, 0, sizeof(ms->collective_field));
    memset(&ms->dormant_narrative, 0, sizeof(ms->dormant_narrative));
}

RivalIdentity *mindsphere_add_rival(MindSphereRivalary *ms, const char *name, const char *archetype, unsigned int seed) {
    RivalIdentity *rival;
    double base;
    if (!ms || ms->count >= ms->capacity) return NULL;

    rival = &ms->rivals[ms->count];
    memset(rival, 0, sizeof(*rival));
    rival->id = (int)ms->count;
    copy_cstr(rival->name, sizeof(rival->name), name ? name : "Rival");
    copy_cstr(rival->archetype, sizeof(rival->archetype), archetype ? archetype : "adaptive");

    srand(seed ^ (unsigned int)(uintptr_t)rival);
    base = (double)(rand() % 1000) / 1000.0;
    rival->grudge = 0.35 + base * 0.4;
    rival->fear = 0.15 + (1.0 - base) * 0.3;
    rival->dominance = 0.25 + base * 0.5;
    rival->adaptability = 0.30 + ((double)(rand() % 1000) / 1000.0) * 0.5;
    mindsphere_init_histories(rival);

    egosphere_init_agent(&rival->psyche, rival->name);
    if (!rival->psyche.name ||
        !rb_init(&rival->replay, ms->config.replay_capacity, ms->config.replay_decay) ||
        !q_init(&rival->planner, ms->config.planner_states, ms->config.planner_actions, ms->config.planner_alpha, ms->config.planner_gamma, ms->config.planner_epsilon)) {
        egosphere_free_agent(&rival->psyche);
        rb_free(&rival->replay);
        q_free(&rival->planner);
        memset(rival, 0, sizeof(*rival));
        return NULL;
    }

    ms->count += 1;
    return rival;
}

AntithEntity *mindsphere_add_antithentity(MindSphereRivalary *ms, const char *name, const char *archetype, unsigned int seed) {
    return mindsphere_add_rival(ms, name, archetype, seed);
}

void mindsphere_record_player_style(MindSphereRivalary *ms, double pressure, double counter_bias, double spacing_bias, double combo_affinity) {
    if (!ms) return;
    ms->player_model.consciousness.frequency[0] = clamp_unit(0.85 * ms->player_model.consciousness.frequency[0] + 0.15 * clamp_unit(pressure));
    ms->player_model.consciousness.frequency[1] = clamp_unit(0.85 * ms->player_model.consciousness.frequency[1] + 0.15 * clamp_unit(counter_bias));
    ms->player_model.consciousness.frequency[2] = clamp_unit(0.85 * ms->player_model.consciousness.frequency[2] + 0.15 * clamp_unit(spacing_bias));
    ms->player_model.consciousness.frequency[3] = clamp_unit(0.85 * ms->player_model.consciousness.frequency[3] + 0.15 * clamp_unit(combo_affinity));
    ms->player_model.genome.personality[PERSONALITY_ASSERTIVE] = clamp_unit(0.9 * ms->player_model.genome.personality[PERSONALITY_ASSERTIVE] + 0.1 * clamp_unit(pressure));
    ms->player_model.genome.personality[PERSONALITY_PATIENT] = clamp_unit(0.9 * ms->player_model.genome.personality[PERSONALITY_PATIENT] + 0.1 * clamp_unit(spacing_bias));
    ms->player_model.genome.intellect[INTELLECT_ADAPTABILITY] = clamp_unit(0.9 * ms->player_model.genome.intellect[INTELLECT_ADAPTABILITY] + 0.1 * clamp_unit(counter_bias));
    ms->player_model.consciousness.discovery_drive = clamp_unit(ms->player_model.consciousness.discovery_drive + 0.02 * clamp_unit(combo_affinity + counter_bias));
}

void mindsphere_record_player_choice(MindSphereRivalary *ms, double mercy_delta, double duty_delta, double candor_delta, double ambition_delta) {
    if (!ms) return;
    ms->player_model.genome.ethics[ETHIC_MERCY] = clamp_unit(ms->player_model.genome.ethics[ETHIC_MERCY] + mercy_delta);
    ms->player_model.genome.ethics[ETHIC_DUTY] = clamp_unit(ms->player_model.genome.ethics[ETHIC_DUTY] + duty_delta);
    ms->player_model.genome.ethics[ETHIC_CANDOR] = clamp_unit(ms->player_model.genome.ethics[ETHIC_CANDOR] + candor_delta);
    ms->player_model.genome.ethics[ETHIC_AMBITION] = clamp_unit(ms->player_model.genome.ethics[ETHIC_AMBITION] + ambition_delta);
    ms->player_model.consciousness.peripheral_awareness = clamp_unit(ms->player_model.consciousness.peripheral_awareness + 0.03 * fabs(mercy_delta - ambition_delta));
}

void mindsphere_sync_resonance(MindSphereRivalary *ms) {
    size_t i;
    double revelation_total = 0.0;
    double alliance_total = 0.0;
    double rupture_total = 0.0;
    double ending_total = 0.0;
    double omen_total = 0.0;
    if (!ms || ms->count == 0) return;
    memset(&ms->collective_field, 0, sizeof(ms->collective_field));
    for (i = 0; i < ms->count; ++i) {
        RivalIdentity *rival = &ms->rivals[i];
        double personality_similarity = trait_similarity(ms->player_model.genome.personality, rival->self_model.genome.personality);
        double intellect_similarity = trait_similarity(ms->player_model.genome.intellect, rival->self_model.genome.intellect);
        double ethic_similarity = trait_similarity(ms->player_model.genome.ethics, rival->self_model.genome.ethics);
        double dissonance = 1.0 - (personality_similarity * 0.4 + intellect_similarity * 0.25 + ethic_similarity * 0.35);
        int band;
        rival->player_resonance.frequency[0] = clamp_unit((ms->player_model.consciousness.frequency[0] + rival->tactics.pressure_bias) * 0.5);
        rival->player_resonance.frequency[1] = clamp_unit((ms->player_model.consciousness.frequency[1] + rival->tactics.counter_bias) * 0.5);
        rival->player_resonance.frequency[2] = clamp_unit((ms->player_model.consciousness.frequency[2] + rival->tactics.spacing_bias) * 0.5);
        rival->player_resonance.frequency[3] = clamp_unit((ms->player_model.genome.ethics[ETHIC_CANDOR] + rival->morals.candor) * 0.5);
        rival->player_resonance.frequency[4] = clamp_unit((ms->player_model.consciousness.discovery_drive + rival->self_model.consciousness.discovery_drive) * 0.5);
        rival->player_resonance.familiarity = clamp_unit(0.18 + 0.004 * (double)rival->engagements + 0.22 * personality_similarity);
        rival->player_resonance.reciprocity = clamp_unit(0.25 + 0.35 * ethic_similarity + 0.20 * intellect_similarity + 0.20 * (1.0 - rival->fear));
        rival->player_resonance.tension = clamp_unit(0.25 + 0.30 * dissonance + 0.20 * rival->grudge + 0.15 * rival->morals.ambition + 0.10 * mindsphere_compute_threat(rival));
        rival->player_resonance.permeability = clamp_unit((ms->player_model.consciousness.peripheral_awareness + rival->self_model.consciousness.subconscious_pull + rival->self_model.consciousness.discovery_drive) / 3.0);
        rival->self_model.consciousness.unconscious_pull = clamp_unit(0.88 * rival->self_model.consciousness.unconscious_pull + 0.12 * rival->player_resonance.tension);
        rival->self_model.consciousness.subconscious_pull = clamp_unit(0.88 * rival->self_model.consciousness.subconscious_pull + 0.12 * rival->player_resonance.reciprocity);
        rival->self_model.consciousness.conscious_pull = clamp_unit(0.88 * rival->self_model.consciousness.conscious_pull + 0.12 * rival->player_resonance.familiarity);
        rival->self_model.consciousness.peripheral_awareness = clamp_unit(0.90 * rival->self_model.consciousness.peripheral_awareness + 0.10 * rival->player_resonance.permeability);
        rival->self_model.consciousness.discovery_drive = clamp_unit(0.90 * rival->self_model.consciousness.discovery_drive + 0.10 * (rival->player_resonance.tension + rival->player_resonance.reciprocity) * 0.5);
        revelation_total += rival->player_resonance.permeability * rival->self_model.consciousness.discovery_drive;
        alliance_total += rival->player_resonance.reciprocity * rival->morals.mercy;
        rupture_total += rival->player_resonance.tension * (1.0 - rival->morals.mercy + rival->morals.ambition) * 0.5;
        ending_total += mindsphere_compute_threat(rival) * (0.4 + rival->morals.ambition * 0.6);
        omen_total += rival->self_model.consciousness.unconscious_pull * rival->player_resonance.frequency[4];
        for (band = 0; band < MINDSPHERE_FREQUENCY_BANDS; ++band) {
            ms->collective_field.frequency[band] += rival->player_resonance.frequency[band];
        }
        ms->collective_field.unconscious_pull += rival->self_model.consciousness.unconscious_pull;
        ms->collective_field.subconscious_pull += rival->self_model.consciousness.subconscious_pull;
        ms->collective_field.conscious_pull += rival->self_model.consciousness.conscious_pull;
        ms->collective_field.peripheral_awareness += rival->self_model.consciousness.peripheral_awareness;
        ms->collective_field.discovery_drive += rival->self_model.consciousness.discovery_drive;
    }
    for (i = 0; i < MINDSPHERE_FREQUENCY_BANDS; ++i) {
        ms->collective_field.frequency[i] /= (double)ms->count;
    }
    ms->collective_field.unconscious_pull /= (double)ms->count;
    ms->collective_field.subconscious_pull /= (double)ms->count;
    ms->collective_field.conscious_pull /= (double)ms->count;
    ms->collective_field.peripheral_awareness /= (double)ms->count;
    ms->collective_field.discovery_drive /= (double)ms->count;
    ms->dormant_narrative.active = ms->config.narrative_protocol_enabled ? 1 : 0;
    ms->dormant_narrative.revelation_pressure = revelation_total / (double)ms->count;
    ms->dormant_narrative.alliance_pressure = alliance_total / (double)ms->count;
    ms->dormant_narrative.rupture_pressure = rupture_total / (double)ms->count;
    ms->dormant_narrative.ending_pressure = ending_total / (double)ms->count;
    ms->dormant_narrative.omen_pressure = omen_total / (double)ms->count;
}

void mindsphere_collect_narrative_hooks(const MindSphereRivalary *ms, MindSphereNarrativeHooks *out_hooks) {
    if (!out_hooks) return;
    if (!ms) {
        memset(out_hooks, 0, sizeof(*out_hooks));
        return;
    }
    *out_hooks = ms->dormant_narrative;
}

int mindsphere_choose_action(RivalIdentity *rival, int state) {
    int action_count;
    int aggressive_action;
    int cautious_action;
    int planner_action;
    int psyche_action;
    int planner_state;
    if (!rival) return 0;
    if (rival->planner.nactions <= 0 || rival->planner.nstates <= 0 || !rival->planner.Q) return 0;

    action_count = rival->planner.nactions > 0 ? rival->planner.nactions : MINDSPHERE_ACTION_COUNT;
    aggressive_action = action_count > 0 ? action_count - 1 : 0;
    cautious_action = action_count > 1 ? 1 : 0;
    planner_state = normalize_index(state, rival->planner.nstates);

    planner_action = q_select_action(&rival->planner, planner_state);
    psyche_action = egosphere_decide_action(&rival->psyche, CONTEXT_COMBAT) % action_count;

    if ((rival->tactics.pressure_bias > 0.72 || rival->player_resonance.tension > 0.72) && rival->dominance > rival->fear) {
        return aggressive_action;
    }
    if ((rival->fear > 0.65 || rival->tactics.spacing_bias > rival->tactics.pressure_bias + 0.18 || rival->player_resonance.reciprocity > 0.72) && planner_action == aggressive_action) {
        return cautious_action;
    }
    if (rival->tactics.counter_bias > 0.68 && rival->tactics.last_action >= 0) {
        return normalize_index(rival->tactics.last_action + 1, action_count);
    }
    return (planner_action + psyche_action) % action_count;
}

void mindsphere_record_outcome(MindSphereRivalary *ms, RivalIdentity *rival, int state, int action, double reward, int next_state, int done) {
    double abs_reward;
    double grudge_delta;
    double fear_delta;
    double dominance_delta;
    double adaptability_delta;
    int psyche_action;
    int planner_state;
    int planner_next_state;
    int planner_action;
    if (!rival) return;
    if (rival->planner.nactions <= 0 || rival->planner.nstates <= 0 || !rival->planner.Q) return;

    abs_reward = fabs(reward) + 1e-4;
    planner_state = normalize_index(state, rival->planner.nstates);
    planner_next_state = normalize_index(next_state, rival->planner.nstates);
    planner_action = normalize_index(action, rival->planner.nactions);
    psyche_action = action % 3;
    if (psyche_action < 0) psyche_action += 3;
    rb_push(&rival->replay, state, planner_action, reward, next_state, done, abs_reward);
    q_update(&rival->planner, planner_state, planner_action, reward, planner_next_state, done);
    egosphere_update(&rival->psyche, psyche_action, reward, CONTEXT_COMBAT);
    mindsphere_record_tactic_history(rival, planner_action, reward);
    rival->engagements += 1;
    rival->self_model.genome.personality[PERSONALITY_ASSERTIVE] = clamp_unit(0.93 * rival->self_model.genome.personality[PERSONALITY_ASSERTIVE] + 0.07 * rival->tactics.pressure_bias);
    rival->self_model.genome.personality[PERSONALITY_PATIENT] = clamp_unit(0.93 * rival->self_model.genome.personality[PERSONALITY_PATIENT] + 0.07 * rival->tactics.spacing_bias);
    rival->self_model.genome.intellect[INTELLECT_ADAPTABILITY] = clamp_unit(0.92 * rival->self_model.genome.intellect[INTELLECT_ADAPTABILITY] + 0.08 * rival->adaptability);
    rival->self_model.genome.intellect[INTELLECT_MEMORY] = clamp_unit(0.90 * rival->self_model.genome.intellect[INTELLECT_MEMORY] + 0.10 * clamp_unit((double)rival->engagements / 64.0));
    rival->self_model.consciousness.frequency[0] = clamp_unit(0.90 * rival->self_model.consciousness.frequency[0] + 0.10 * rival->tactics.pressure_bias);
    rival->self_model.consciousness.frequency[1] = clamp_unit(0.90 * rival->self_model.consciousness.frequency[1] + 0.10 * rival->tactics.counter_bias);
    rival->self_model.consciousness.frequency[2] = clamp_unit(0.90 * rival->self_model.consciousness.frequency[2] + 0.10 * rival->tactics.spacing_bias);
    rival->self_model.consciousness.frequency[3] = clamp_unit(0.90 * rival->self_model.consciousness.frequency[3] + 0.10 * rival->tactics.combo_commitment);
    rival->self_model.consciousness.unconscious_pull = clamp_unit(0.92 * rival->self_model.consciousness.unconscious_pull + 0.08 * rival->grudge);
    rival->self_model.consciousness.subconscious_pull = clamp_unit(0.92 * rival->self_model.consciousness.subconscious_pull + 0.08 * rival->adaptability);
    rival->self_model.consciousness.conscious_pull = clamp_unit(0.92 * rival->self_model.consciousness.conscious_pull + 0.08 * (1.0 - rival->fear));

    grudge_delta = reward < 0.0
        ? abs_reward * 0.18 * (1.0 - rival->grudge)
        : -abs_reward * 0.04 * (0.35 + rival->grudge);
    fear_delta = reward < 0.0
        ? abs_reward * 0.11 * (1.0 - rival->fear)
        : -abs_reward * 0.06 * (0.30 + rival->fear);
    dominance_delta = reward >= 0.0
        ? reward * 0.09 * (1.0 - rival->dominance)
        : reward * 0.07 * (0.45 + rival->dominance);
    adaptability_delta = abs_reward * 0.02 * (1.0 - rival->adaptability);

    rival->grudge = clamp_range(rival->grudge + grudge_delta, 0.04, 0.96);
    rival->fear = clamp_range(rival->fear + fear_delta, 0.04, 0.96);
    rival->dominance = clamp_range(rival->dominance + dominance_delta, 0.08, 0.96);
    rival->adaptability = clamp_range(rival->adaptability + adaptability_delta, 0.15, 0.98);

    if (reward > 0.45) {
        rival->survives += 1;
    }
    if (reward < -0.45) {
        rival->defeats += 1;
    }

    if (ms) {
        ms->tick += 1;
        mindsphere_sync_resonance(ms);
    }
}

size_t mindsphere_rehearse_rival(RivalIdentity *rival, size_t sample_count) {
    ReplayBufferEntry *batch;
    size_t got = 0;
    size_t i;
    if (!rival || sample_count == 0) return 0;
    if (!rival->replay.entries || rival->replay.count == 0) return 0;
    if (!rival->planner.Q || rival->planner.nstates <= 0 || rival->planner.nactions <= 0) return 0;

    batch = rb_sample(&rival->replay, sample_count, &got);
    if (!batch) return 0;

    for (i = 0; i < got; ++i) {
        q_update(
            &rival->planner,
            normalize_index(batch[i].state, rival->planner.nstates),
            normalize_index(batch[i].action, rival->planner.nactions),
            batch[i].reward,
            normalize_index(batch[i].next_state, rival->planner.nstates),
            batch[i].done);
    }

    free(batch);
    return got;
}

size_t mindsphere_rehearse_all(MindSphereRivalary *ms, size_t sample_count) {
    size_t total = 0;
    size_t i;
    if (!ms || sample_count == 0) return 0;
    for (i = 0; i < ms->count; ++i) {
        total += mindsphere_rehearse_rival(&ms->rivals[i], sample_count);
    }
    return total;
}

double mindsphere_compute_threat(const RivalIdentity *rival) {
    double history_pressure;
    double survival_pressure;
    double tactical_pressure;
    double moral_pressure;
    if (!rival) return 0.0;
    history_pressure = 0.20 * (1.0 - exp(-0.025 * (double)rival->engagements));
    survival_pressure = 0.18 * (1.0 - exp(-0.03 * rival->survives));
    tactical_pressure = rival->tactics.pressure_bias * 0.14 + rival->tactics.combo_commitment * 0.10 + rival->tactics.counter_bias * 0.08 + rival->tactics.spacing_bias * 0.04;
    moral_pressure = rival->morals.ambition * 0.06 + rival->morals.duty * 0.04 + (1.0 - rival->morals.mercy) * 0.03;
    return rival->grudge * 0.26 + rival->dominance * 0.18 + rival->adaptability * 0.14 + history_pressure + survival_pressure + tactical_pressure + moral_pressure - rival->fear * 0.10;
}

void mindsphere_describe_rival(const RivalIdentity *rival, char *buffer, size_t buffer_size) {
    if (!buffer || buffer_size == 0) return;
    if (!rival) {
        copy_cstr(buffer, buffer_size, "no rival");
        return;
    }

    snprintf(
        buffer,
        buffer_size,
        "%s [%s] threat=%.2f pressure=%.2f combo=%.2f mercy=%.2f ambition=%.2f engagements=%lu",
        rival->name,
        rival->archetype,
        mindsphere_compute_threat(rival),
        rival->tactics.pressure_bias,
        rival->tactics.combo_commitment,
        rival->morals.mercy,
        rival->morals.ambition,
        rival->engagements);
}

static int save_tactical_history(FILE *fp, const RivalTacticalHistory *tactics) {
    size_t i;
    size_t j;
    for (i = 0; i < MINDSPHERE_STYLE_ACTION_SLOTS; ++i) {
        if (!write_u64(fp, (uint64_t)tactics->action_uses[i])) return 0;
        if (!write_u64(fp, (uint64_t)tactics->action_successes[i])) return 0;
        if (!write_u64(fp, (uint64_t)tactics->action_failures[i])) return 0;
    }
    for (i = 0; i < MINDSPHERE_STYLE_ACTION_SLOTS; ++i) {
        for (j = 0; j < MINDSPHERE_STYLE_ACTION_SLOTS; ++j) {
            if (!write_u64(fp, (uint64_t)tactics->combo_links[i][j])) return 0;
        }
    }
    if (!write_u32(fp, (uint32_t)(tactics->last_action + 1))) return 0;
    if (!write_double(fp, tactics->combo_commitment)) return 0;
    if (!write_double(fp, tactics->pressure_bias)) return 0;
    if (!write_double(fp, tactics->counter_bias)) return 0;
    if (!write_double(fp, tactics->spacing_bias)) return 0;
    return 1;
}

static int load_tactical_history(FILE *fp, RivalTacticalHistory *tactics) {
    size_t i;
    size_t j;
    uint32_t stored_last_action = 0;
    memset(tactics, 0, sizeof(*tactics));
    for (i = 0; i < MINDSPHERE_STYLE_ACTION_SLOTS; ++i) {
        uint64_t action_uses = 0;
        uint64_t action_successes = 0;
        uint64_t action_failures = 0;
        if (!read_u64(fp, &action_uses)) return 0;
        if (!read_u64(fp, &action_successes)) return 0;
        if (!read_u64(fp, &action_failures)) return 0;
        tactics->action_uses[i] = (unsigned long)action_uses;
        tactics->action_successes[i] = (unsigned long)action_successes;
        tactics->action_failures[i] = (unsigned long)action_failures;
    }
    for (i = 0; i < MINDSPHERE_STYLE_ACTION_SLOTS; ++i) {
        for (j = 0; j < MINDSPHERE_STYLE_ACTION_SLOTS; ++j) {
            uint64_t combo_links = 0;
            if (!read_u64(fp, &combo_links)) return 0;
            tactics->combo_links[i][j] = (unsigned long)combo_links;
        }
    }
    if (!read_u32(fp, &stored_last_action)) return 0;
    if (!read_double(fp, &tactics->combo_commitment)) return 0;
    if (!read_double(fp, &tactics->pressure_bias)) return 0;
    if (!read_double(fp, &tactics->counter_bias)) return 0;
    if (!read_double(fp, &tactics->spacing_bias)) return 0;
    tactics->last_action = (int)stored_last_action - 1;
    return 1;
}

static int save_moral_history(FILE *fp, const RivalMoralHistory *morals) {
    if (!write_double(fp, morals->mercy)) return 0;
    if (!write_double(fp, morals->duty)) return 0;
    if (!write_double(fp, morals->candor)) return 0;
    if (!write_double(fp, morals->ambition)) return 0;
    if (!write_u64(fp, (uint64_t)morals->dialogue_choices)) return 0;
    if (!write_u64(fp, (uint64_t)morals->spared_count)) return 0;
    if (!write_u64(fp, (uint64_t)morals->punished_count)) return 0;
    if (!write_u64(fp, (uint64_t)morals->promises_kept)) return 0;
    if (!write_u64(fp, (uint64_t)morals->promises_broken)) return 0;
    return 1;
}

static int load_moral_history(FILE *fp, RivalMoralHistory *morals) {
    uint64_t dialogue_choices = 0;
    uint64_t spared_count = 0;
    uint64_t punished_count = 0;
    uint64_t promises_kept = 0;
    uint64_t promises_broken = 0;
    memset(morals, 0, sizeof(*morals));
    if (!read_double(fp, &morals->mercy)) return 0;
    if (!read_double(fp, &morals->duty)) return 0;
    if (!read_double(fp, &morals->candor)) return 0;
    if (!read_double(fp, &morals->ambition)) return 0;
    if (!read_u64(fp, &dialogue_choices)) return 0;
    if (!read_u64(fp, &spared_count)) return 0;
    if (!read_u64(fp, &punished_count)) return 0;
    if (!read_u64(fp, &promises_kept)) return 0;
    if (!read_u64(fp, &promises_broken)) return 0;
    morals->dialogue_choices = (unsigned long)dialogue_choices;
    morals->spared_count = (unsigned long)spared_count;
    morals->punished_count = (unsigned long)punished_count;
    morals->promises_kept = (unsigned long)promises_kept;
    morals->promises_broken = (unsigned long)promises_broken;
    return 1;
}

static int save_genome_profile(FILE *fp, const MindGenomeProfile *genome) {
    size_t i;
    for (i = 0; i < MINDSPHERE_GENOME_TRAITS; ++i) {
        if (!write_double(fp, genome->personality[i])) return 0;
    }
    for (i = 0; i < MINDSPHERE_GENOME_TRAITS; ++i) {
        if (!write_double(fp, genome->intellect[i])) return 0;
    }
    for (i = 0; i < MINDSPHERE_GENOME_TRAITS; ++i) {
        if (!write_double(fp, genome->ethics[i])) return 0;
    }
    return 1;
}

static int load_genome_profile(FILE *fp, MindGenomeProfile *genome) {
    size_t i;
    memset(genome, 0, sizeof(*genome));
    for (i = 0; i < MINDSPHERE_GENOME_TRAITS; ++i) {
        if (!read_double(fp, &genome->personality[i])) return 0;
    }
    for (i = 0; i < MINDSPHERE_GENOME_TRAITS; ++i) {
        if (!read_double(fp, &genome->intellect[i])) return 0;
    }
    for (i = 0; i < MINDSPHERE_GENOME_TRAITS; ++i) {
        if (!read_double(fp, &genome->ethics[i])) return 0;
    }
    return 1;
}

static int save_consciousness(FILE *fp, const ConsciousnessSpectrum *spectrum) {
    size_t i;
    if (!write_double(fp, spectrum->unconscious_pull)) return 0;
    if (!write_double(fp, spectrum->subconscious_pull)) return 0;
    if (!write_double(fp, spectrum->conscious_pull)) return 0;
    if (!write_double(fp, spectrum->peripheral_awareness)) return 0;
    if (!write_double(fp, spectrum->discovery_drive)) return 0;
    for (i = 0; i < MINDSPHERE_FREQUENCY_BANDS; ++i) {
        if (!write_double(fp, spectrum->frequency[i])) return 0;
    }
    return 1;
}

static int load_consciousness(FILE *fp, ConsciousnessSpectrum *spectrum) {
    size_t i;
    memset(spectrum, 0, sizeof(*spectrum));
    if (!read_double(fp, &spectrum->unconscious_pull)) return 0;
    if (!read_double(fp, &spectrum->subconscious_pull)) return 0;
    if (!read_double(fp, &spectrum->conscious_pull)) return 0;
    if (!read_double(fp, &spectrum->peripheral_awareness)) return 0;
    if (!read_double(fp, &spectrum->discovery_drive)) return 0;
    for (i = 0; i < MINDSPHERE_FREQUENCY_BANDS; ++i) {
        if (!read_double(fp, &spectrum->frequency[i])) return 0;
    }
    return 1;
}

static int save_narrative_hooks(FILE *fp, const MindSphereNarrativeHooks *hooks) {
    if (!write_u32(fp, (uint32_t)hooks->active)) return 0;
    if (!write_double(fp, hooks->revelation_pressure)) return 0;
    if (!write_double(fp, hooks->alliance_pressure)) return 0;
    if (!write_double(fp, hooks->rupture_pressure)) return 0;
    if (!write_double(fp, hooks->ending_pressure)) return 0;
    if (!write_double(fp, hooks->omen_pressure)) return 0;
    return 1;
}

static int load_narrative_hooks(FILE *fp, MindSphereNarrativeHooks *hooks) {
    uint32_t active = 0;
    memset(hooks, 0, sizeof(*hooks));
    if (!read_u32(fp, &active)) return 0;
    hooks->active = (int)active;
    if (!read_double(fp, &hooks->revelation_pressure)) return 0;
    if (!read_double(fp, &hooks->alliance_pressure)) return 0;
    if (!read_double(fp, &hooks->rupture_pressure)) return 0;
    if (!read_double(fp, &hooks->ending_pressure)) return 0;
    if (!read_double(fp, &hooks->omen_pressure)) return 0;
    return 1;
}

static int save_actor_profile(FILE *fp, const MindActorProfile *profile) {
    if (!write_string(fp, profile->label)) return 0;
    if (!save_genome_profile(fp, &profile->genome)) return 0;
    if (!save_consciousness(fp, &profile->consciousness)) return 0;
    if (!save_narrative_hooks(fp, &profile->narrative)) return 0;
    return 1;
}

static int load_actor_profile(FILE *fp, MindActorProfile *profile) {
    char *label = NULL;
    memset(profile, 0, sizeof(*profile));
    if (!read_string(fp, &label)) return 0;
    copy_cstr(profile->label, sizeof(profile->label), label);
    free(label);
    if (!load_genome_profile(fp, &profile->genome)) return 0;
    if (!load_consciousness(fp, &profile->consciousness)) return 0;
    if (!load_narrative_hooks(fp, &profile->narrative)) return 0;
    return 1;
}

static int save_resonance_link(FILE *fp, const MindResonanceLink *link) {
    size_t i;
    for (i = 0; i < MINDSPHERE_FREQUENCY_BANDS; ++i) {
        if (!write_double(fp, link->frequency[i])) return 0;
    }
    if (!write_double(fp, link->familiarity)) return 0;
    if (!write_double(fp, link->reciprocity)) return 0;
    if (!write_double(fp, link->tension)) return 0;
    if (!write_double(fp, link->permeability)) return 0;
    return 1;
}

static int load_resonance_link(FILE *fp, MindResonanceLink *link) {
    size_t i;
    memset(link, 0, sizeof(*link));
    for (i = 0; i < MINDSPHERE_FREQUENCY_BANDS; ++i) {
        if (!read_double(fp, &link->frequency[i])) return 0;
    }
    if (!read_double(fp, &link->familiarity)) return 0;
    if (!read_double(fp, &link->reciprocity)) return 0;
    if (!read_double(fp, &link->tension)) return 0;
    if (!read_double(fp, &link->permeability)) return 0;
    return 1;
}

static int save_agent(FILE *fp, const Agent *agent) {
    uint64_t count;
    size_t i;

    if (!write_string(fp, agent && agent->name ? agent->name : "")) return 0;
    if (!write_double(fp, agent->id.weight)) return 0;
    if (!write_double(fp, agent->ego.weight)) return 0;
    if (!write_double(fp, agent->superego.weight)) return 0;
    if (!write_double(fp, agent->priors.pattern_trust)) return 0;
    for (i = 0; i < 3; ++i) {
        if (!write_double(fp, agent->priors.bias_action[i])) return 0;
    }
    count = (uint64_t)agent->memory.count;
    if (!write_u64(fp, count)) return 0;
    for (i = 0; i < agent->memory.count; ++i) {
        const Experience *exp = &agent->memory.items[i];
        if (!write_u32(fp, (uint32_t)exp->action)) return 0;
        if (!write_double(fp, exp->reward)) return 0;
        if (!write_u32(fp, (uint32_t)exp->context)) return 0;
    }
    return 1;
}

static int load_agent(FILE *fp, Agent *agent) {
    uint64_t count = 0;
    size_t i;

    memset(agent, 0, sizeof(*agent));
    if (!read_string(fp, &agent->name)) return 0;
    if (!read_double(fp, &agent->id.weight)) return 0;
    if (!read_double(fp, &agent->ego.weight)) return 0;
    if (!read_double(fp, &agent->superego.weight)) return 0;
    if (!read_double(fp, &agent->priors.pattern_trust)) return 0;
    for (i = 0; i < 3; ++i) {
        if (!read_double(fp, &agent->priors.bias_action[i])) return 0;
    }
    if (!read_u64(fp, &count)) return 0;
    if (count > 0) {
        agent->memory.items = (Experience*)calloc((size_t)count, sizeof(Experience));
        if (!agent->memory.items) return 0;
        agent->memory.capacity = (size_t)count;
        agent->memory.count = (size_t)count;
    }
    for (i = 0; i < (size_t)count; ++i) {
        uint32_t action = 0;
        uint32_t context = 0;
        if (!read_u32(fp, &action)) return 0;
        if (!read_double(fp, &agent->memory.items[i].reward)) return 0;
        if (!read_u32(fp, &context)) return 0;
        agent->memory.items[i].action = (int)action;
        agent->memory.items[i].context = (Context)context;
    }
    return 1;
}

static int save_replay(FILE *fp, const ReplayBuffer *rb) {
    uint64_t count = (uint64_t)rb->count;
    uint64_t capacity = (uint64_t)rb->capacity;
    uint64_t next_index = (uint64_t)rb->next_index;
    size_t i;

    if (!write_u64(fp, capacity)) return 0;
    if (!write_u64(fp, count)) return 0;
    if (!write_u64(fp, next_index)) return 0;
    if (!write_double(fp, rb->total_priority)) return 0;
    if (!write_double(fp, rb->decay)) return 0;
    if (!write_u64(fp, (uint64_t)rb->t)) return 0;
    for (i = 0; i < rb->count; ++i) {
        const ReplayBufferEntry *entry = &rb->entries[i];
        if (!write_u32(fp, (uint32_t)entry->state)) return 0;
        if (!write_u32(fp, (uint32_t)entry->action)) return 0;
        if (!write_double(fp, entry->reward)) return 0;
        if (!write_u32(fp, (uint32_t)entry->next_state)) return 0;
        if (!write_u32(fp, (uint32_t)entry->done)) return 0;
        if (!write_double(fp, entry->priority)) return 0;
        if (!write_u64(fp, (uint64_t)entry->timestamp)) return 0;
    }
    return 1;
}

static int load_replay(FILE *fp, ReplayBuffer *rb) {
    uint64_t capacity = 0;
    uint64_t count = 0;
    uint64_t next_index = 0;
    uint64_t t = 0;
    size_t i;

    memset(rb, 0, sizeof(*rb));
    if (!read_u64(fp, &capacity)) return 0;
    if (!read_u64(fp, &count)) return 0;
    if (!read_u64(fp, &next_index)) return 0;
    if (!read_double(fp, &rb->total_priority)) return 0;
    if (!read_double(fp, &rb->decay)) return 0;
    if (!read_u64(fp, &t)) return 0;
    rb->capacity = (size_t)capacity;
    rb->count = (size_t)count;
    rb->next_index = (size_t)next_index;
    rb->t = (unsigned long)t;
    if (rb->capacity > 0) {
        rb->entries = (ReplayBufferEntry*)calloc(rb->capacity, sizeof(ReplayBufferEntry));
        if (!rb->entries) return 0;
    }
    for (i = 0; i < rb->count; ++i) {
        ReplayBufferEntry *entry = &rb->entries[i];
        uint32_t state = 0;
        uint32_t action = 0;
        uint32_t next_state = 0;
        uint32_t done = 0;
        uint64_t timestamp = 0;
        if (!read_u32(fp, &state)) return 0;
        if (!read_u32(fp, &action)) return 0;
        if (!read_double(fp, &entry->reward)) return 0;
        if (!read_u32(fp, &next_state)) return 0;
        if (!read_u32(fp, &done)) return 0;
        if (!read_double(fp, &entry->priority)) return 0;
        if (!read_u64(fp, &timestamp)) return 0;
        entry->state = (int)state;
        entry->action = (int)action;
        entry->next_state = (int)next_state;
        entry->done = (int)done;
        entry->timestamp = (unsigned long)timestamp;
    }
    return 1;
}

static int save_qlearner(FILE *fp, const QLearner *planner) {
    size_t total;
    size_t i;

    if (!write_u32(fp, (uint32_t)planner->nstates)) return 0;
    if (!write_u32(fp, (uint32_t)planner->nactions)) return 0;
    if (!write_double(fp, planner->alpha)) return 0;
    if (!write_double(fp, planner->gamma)) return 0;
    if (!write_double(fp, planner->epsilon)) return 0;
    total = (size_t)planner->nstates * (size_t)planner->nactions;
    for (i = 0; i < total; ++i) {
        if (!write_double(fp, planner->Q[i])) return 0;
    }
    return 1;
}

static int load_qlearner(FILE *fp, QLearner *planner) {
    uint32_t nstates = 0;
    uint32_t nactions = 0;
    size_t total;
    size_t i;

    memset(planner, 0, sizeof(*planner));
    if (!read_u32(fp, &nstates)) return 0;
    if (!read_u32(fp, &nactions)) return 0;
    planner->nstates = (int)nstates;
    planner->nactions = (int)nactions;
    if (!read_double(fp, &planner->alpha)) return 0;
    if (!read_double(fp, &planner->gamma)) return 0;
    if (!read_double(fp, &planner->epsilon)) return 0;
    total = (size_t)planner->nstates * (size_t)planner->nactions;
    planner->Q = (double*)calloc(total, sizeof(double));
    if (!planner->Q) return 0;
    for (i = 0; i < total; ++i) {
        if (!read_double(fp, &planner->Q[i])) return 0;
    }
    return 1;
}

int mindsphere_save(const MindSphereRivalary *ms, const char *path) {
    FILE *fp;
    size_t i;

    if (!ms || !path) return 0;
    fp = fopen(path, "wb");
    if (!fp) return 0;

    if (!write_u32(fp, MINDSPHERE_SAVE_MAGIC) ||
        !write_u32(fp, MINDSPHERE_SAVE_VERSION) ||
        !write_u64(fp, (uint64_t)ms->count) ||
        !write_u64(fp, (uint64_t)ms->capacity) ||
        !write_u64(fp, (uint64_t)ms->tick) ||
        !write_u64(fp, (uint64_t)ms->config.replay_capacity) ||
        !write_double(fp, ms->config.replay_decay) ||
        !write_u32(fp, (uint32_t)ms->config.planner_states) ||
        !write_u32(fp, (uint32_t)ms->config.planner_actions) ||
        !write_double(fp, ms->config.planner_alpha) ||
        !write_double(fp, ms->config.planner_gamma) ||
        !write_double(fp, ms->config.planner_epsilon) ||
        !write_u32(fp, (uint32_t)ms->config.narrative_protocol_enabled) ||
        !save_actor_profile(fp, &ms->player_model) ||
        !save_consciousness(fp, &ms->collective_field) ||
        !save_narrative_hooks(fp, &ms->dormant_narrative)) {
        fclose(fp);
        return 0;
    }

    for (i = 0; i < ms->count; ++i) {
        const RivalIdentity *rival = &ms->rivals[i];
        if (!write_u32(fp, (uint32_t)rival->id) ||
            !write_string(fp, rival->name) ||
            !write_string(fp, rival->archetype) ||
            !write_double(fp, rival->grudge) ||
            !write_double(fp, rival->fear) ||
            !write_double(fp, rival->dominance) ||
            !write_double(fp, rival->adaptability) ||
            !write_u64(fp, (uint64_t)rival->engagements) ||
            !write_u32(fp, (uint32_t)rival->defeats) ||
            !write_u32(fp, (uint32_t)rival->survives) ||
            !save_tactical_history(fp, &rival->tactics) ||
            !save_moral_history(fp, &rival->morals) ||
            !save_actor_profile(fp, &rival->self_model) ||
            !save_resonance_link(fp, &rival->player_resonance) ||
            !save_agent(fp, &rival->psyche) ||
            !save_replay(fp, &rival->replay) ||
            !save_qlearner(fp, &rival->planner)) {
            fclose(fp);
            return 0;
        }
    }

    fclose(fp);
    return 1;
}

int mindsphere_load(MindSphereRivalary *ms, const char *path) {
    FILE *fp;
    uint32_t magic = 0;
    uint32_t version = 0;
    uint64_t count = 0;
    uint64_t capacity = 0;
    uint64_t tick = 0;
    uint64_t replay_capacity = 0;
    uint32_t planner_states = 0;
    uint32_t planner_actions = 0;
    uint32_t narrative_protocol_enabled = 0;
    MindSphereRivalary loaded = {0};
    size_t i;

    if (!ms || !path) return 0;
    fp = fopen(path, "rb");
    if (!fp) return 0;
    if (!read_u32(fp, &magic) || !read_u32(fp, &version) || magic != MINDSPHERE_SAVE_MAGIC || (version != 2u && version != 3u && version != MINDSPHERE_SAVE_VERSION)) {
        fclose(fp);
        return 0;
    }
    if (!read_u64(fp, &count) ||
        !read_u64(fp, &capacity) ||
        !read_u64(fp, &tick) ||
        !read_u64(fp, &replay_capacity) ||
        !read_double(fp, &loaded.config.replay_decay) ||
        !read_u32(fp, &planner_states) ||
        !read_u32(fp, &planner_actions) ||
        !read_double(fp, &loaded.config.planner_alpha) ||
        !read_double(fp, &loaded.config.planner_gamma) ||
        !read_double(fp, &loaded.config.planner_epsilon) ||
        !((version >= 4u) ? read_u32(fp, &narrative_protocol_enabled) : 1)) {
        fclose(fp);
        return 0;
    }

    loaded.config.replay_capacity = (size_t)replay_capacity;
    loaded.config.planner_states = (int)planner_states;
    loaded.config.planner_actions = (int)planner_actions;
    loaded.config.narrative_protocol_enabled = (int)narrative_protocol_enabled;
    if (loaded.config.replay_capacity == 0 || loaded.config.planner_states <= 0 || loaded.config.planner_actions <= 0) {
        fclose(fp);
        return 0;
    }
    loaded.capacity = (size_t)(capacity < count ? count : capacity);
    loaded.count = (size_t)count;
    loaded.tick = (unsigned long)tick;
    if (loaded.capacity > 0) {
        loaded.rivals = (RivalIdentity*)calloc(loaded.capacity, sizeof(RivalIdentity));
        if (!loaded.rivals) {
            fclose(fp);
            return 0;
        }
    }
    mindsphere_init_default_player_profile(&loaded);
    if (version >= 4u) {
        if (!load_actor_profile(fp, &loaded.player_model) ||
            !load_consciousness(fp, &loaded.collective_field) ||
            !load_narrative_hooks(fp, &loaded.dormant_narrative)) {
            fclose(fp);
            free_loaded_rivals(&loaded);
            return 0;
        }
    }

    for (i = 0; i < loaded.count; ++i) {
        RivalIdentity *rival = &loaded.rivals[i];
        char *name = NULL;
        char *archetype = NULL;
        uint32_t id = 0;
        uint64_t engagements = 0;
        uint32_t legacy_advancements = 0;
        uint32_t defeats = 0;
        uint32_t survives = 0;
        if (!read_u32(fp, &id) ||
            !read_string(fp, &name) ||
            !read_string(fp, &archetype) ||
            !read_double(fp, &rival->grudge) ||
            !read_double(fp, &rival->fear) ||
            !read_double(fp, &rival->dominance) ||
            !read_double(fp, &rival->adaptability) ||
            !((version >= 3u) ? read_u64(fp, &engagements) : read_u32(fp, &legacy_advancements)) ||
            !read_u32(fp, &defeats) ||
            !read_u32(fp, &survives) ||
            !((version >= 3u) ? load_tactical_history(fp, &rival->tactics) : 1) ||
            !((version >= 3u) ? load_moral_history(fp, &rival->morals) : 1) ||
            !((version >= 4u) ? load_actor_profile(fp, &rival->self_model) : 1) ||
            !((version >= 4u) ? load_resonance_link(fp, &rival->player_resonance) : 1) ||
            !load_agent(fp, &rival->psyche) ||
            !load_replay(fp, &rival->replay) ||
            !load_qlearner(fp, &rival->planner)) {
            free(name);
            free(archetype);
            fclose(fp);
            free_loaded_rivals(&loaded);
            return 0;
        }
        rival->id = (int)id;
        rival->engagements = (unsigned long)engagements;
        rival->defeats = (int)defeats;
        rival->survives = (int)survives;
        if (version < 3u) {
            mindsphere_init_histories(rival);
            rival->engagements = rival->survives + rival->defeats + (unsigned long)legacy_advancements;
        }
        copy_cstr(rival->name, sizeof(rival->name), name);
        copy_cstr(rival->archetype, sizeof(rival->archetype), archetype);
        if (version < 4u) {
            mindsphere_seed_actor_profile(&rival->self_model, rival->name, (unsigned int)(0x51ED270Bu ^ id));
            mindsphere_init_resonance_link(&rival->player_resonance);
        }
        free(name);
        free(archetype);
    }

    if (version < 4u) {
        mindsphere_sync_resonance(&loaded);
    }

    fclose(fp);
    free_loaded_rivals(ms);
    *ms = loaded;
    return 1;
}


