#ifndef EGOSPHERE_H
#define EGOSPHERE_H

#include <stddef.h>

typedef enum {
    CONTEXT_HABIT = 0,
    CONTEXT_COMBAT = 1,
} Context;

typedef struct Experience {
    int action;
    double reward;
    Context context;
} Experience;

typedef struct Memory {
    Experience *items;
    size_t count;
    size_t capacity;
} Memory;

typedef struct Tier {
    double weight; /* influence magnitude */
} Tier;

typedef struct Priors {
    double pattern_trust; /* tendency to rely on learned patterns */
    double bias_action[3]; /* bias toward actions (can be maladaptive)
                             index by action id */
} Priors;

typedef struct Agent {
    char *name;
    Tier id;
    Tier ego;
    Tier superego;
    Priors priors;
    Memory memory;
} Agent;

/* lifecycle */
void egosphere_init_agent(Agent *a, const char *name);
void egosphere_free_agent(Agent *a);

/* record experience with context */
void egosphere_record_experience(Agent *a, int action, double reward, Context ctx);

/* decide action given current context */
int egosphere_decide_action(Agent *a, Context ctx);

/* update internal state after action and reward */
void egosphere_update(Agent *a, int action, double reward, Context ctx);

/* --- Prioritized / Decaying Replay Buffer --- */
typedef struct ReplayBufferEntry {
    int state;
    int action;
    double reward;
    int next_state;
    int done;
    double priority;
    unsigned long timestamp;
} ReplayBufferEntry;

typedef struct ReplayBuffer {
    ReplayBufferEntry *entries;
    size_t capacity;
    size_t count;
    size_t next_index;
    double total_priority;
    double decay; /* multiply priorities by decay factor periodically */
    unsigned long t; /* step counter */
} ReplayBuffer;

/* replay buffer lifecycle */
int rb_init(ReplayBuffer *rb, size_t capacity, double decay);
void rb_free(ReplayBuffer *rb);
void rb_push(ReplayBuffer *rb, int state, int action, double reward, int next_state, int done, double priority);
/* sample returns newly allocated array of entries; count is set; caller must free returned pointer */
ReplayBufferEntry *rb_sample(ReplayBuffer *rb, size_t sample_count, size_t *out_count);
void rb_update_priority(ReplayBuffer *rb, size_t index, double new_priority);

/* --- Tabular Q-learner (discrete small state space) --- */
typedef struct QLearner {
    int nstates;
    int nactions;
    double *Q; /* flattened [nstates * nactions] */
    double alpha;
    double gamma;
    double epsilon; /* for epsilon-greedy */
} QLearner;

int q_init(QLearner *q, int nstates, int nactions, double alpha, double gamma, double epsilon);
void q_free(QLearner *q);
double q_get(QLearner *q, int state, int action);
int q_select_action(QLearner *q, int state);
void q_update(QLearner *q, int state, int action, double reward, int next_state, int done);

/* --- Simple linear DQN approximator (no external ML deps) --- */
typedef struct DQN {
    int nfeatures; /* feature vector length */
    int nactions;
    double *weights; /* flattened [nactions * nfeatures] */
    double lr;
    double gamma;
} DQN;

int dqn_init(DQN *d, int nfeatures, int nactions, double lr, double gamma);
void dqn_free(DQN *d);
/* predict Q values for given feature vector (caller-provided array of size nactions) */
void dqn_predict(DQN *d, const double *features, double *out_q);
/* train on single (features, action, reward, next_features, done) */
void dqn_train(DQN *d, const double *features, int action, double reward, const double *next_features, int done);


#endif
