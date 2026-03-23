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

/* --- MindSphereRivalary: persistent rival-memory modeling --- */

#define MINDSPHERE_NAME_MAX 48
#define MINDSPHERE_ARCHETYPE_MAX 24
#define MINDSPHERE_ACTION_COUNT 3
#define MINDSPHERE_DEFAULT_STATES 16
#define MINDSPHERE_STYLE_ACTION_SLOTS 8
#define MINDSPHERE_GENOME_TRAITS 6
#define MINDSPHERE_FREQUENCY_BANDS 5
#define MINDSPHERE_ACTOR_NAME_MAX 48

typedef struct MindSphereConfig {
    size_t replay_capacity;
    double replay_decay;
    int planner_states;
    int planner_actions;
    double planner_alpha;
    double planner_gamma;
    double planner_epsilon;
    int narrative_protocol_enabled;
} MindSphereConfig;

typedef struct MindGenomeProfile {
    double personality[MINDSPHERE_GENOME_TRAITS];
    double intellect[MINDSPHERE_GENOME_TRAITS];
    double ethics[MINDSPHERE_GENOME_TRAITS];
} MindGenomeProfile;

typedef struct ConsciousnessSpectrum {
    double unconscious_pull;
    double subconscious_pull;
    double conscious_pull;
    double peripheral_awareness;
    double discovery_drive;
    double frequency[MINDSPHERE_FREQUENCY_BANDS];
} ConsciousnessSpectrum;

typedef struct MindSphereNarrativeHooks {
    int active;
    double revelation_pressure;
    double alliance_pressure;
    double rupture_pressure;
    double ending_pressure;
    double omen_pressure;
} MindSphereNarrativeHooks;

typedef struct MindActorProfile {
    char label[MINDSPHERE_ACTOR_NAME_MAX];
    MindGenomeProfile genome;
    ConsciousnessSpectrum consciousness;
    MindSphereNarrativeHooks narrative;
} MindActorProfile;

typedef struct MindResonanceLink {
    double frequency[MINDSPHERE_FREQUENCY_BANDS];
    double familiarity;
    double reciprocity;
    double tension;
    double permeability;
} MindResonanceLink;

typedef struct RivalTacticalHistory {
    unsigned long action_uses[MINDSPHERE_STYLE_ACTION_SLOTS];
    unsigned long action_successes[MINDSPHERE_STYLE_ACTION_SLOTS];
    unsigned long action_failures[MINDSPHERE_STYLE_ACTION_SLOTS];
    unsigned long combo_links[MINDSPHERE_STYLE_ACTION_SLOTS][MINDSPHERE_STYLE_ACTION_SLOTS];
    int last_action;
    double combo_commitment;
    double pressure_bias;
    double counter_bias;
    double spacing_bias;
} RivalTacticalHistory;

typedef struct RivalMoralHistory {
    double mercy;
    double duty;
    double candor;
    double ambition;
    unsigned long dialogue_choices;
    unsigned long spared_count;
    unsigned long punished_count;
    unsigned long promises_kept;
    unsigned long promises_broken;
} RivalMoralHistory;

typedef struct RivalIdentity {
    int id;
    char name[MINDSPHERE_NAME_MAX];
    char archetype[MINDSPHERE_ARCHETYPE_MAX];
    double grudge;
    double fear;
    double dominance;
    double adaptability;
    unsigned long engagements;
    int defeats;
    int survives;
    RivalTacticalHistory tactics;
    RivalMoralHistory morals;
    MindActorProfile self_model;
    MindResonanceLink player_resonance;
    Agent psyche;
    ReplayBuffer replay;
    QLearner planner;
} RivalIdentity;

typedef struct MindSphereRivalary {
    RivalIdentity *rivals;
    size_t count;
    size_t capacity;
    unsigned long tick;
    MindSphereConfig config;
    MindActorProfile player_model;
    ConsciousnessSpectrum collective_field;
    MindSphereNarrativeHooks dormant_narrative;
} MindSphereRivalary;

typedef RivalIdentity AntithEntity;

MindSphereConfig mindsphere_default_config(void);
int mindsphere_init(MindSphereRivalary *ms, size_t capacity);
int mindsphere_init_with_config(MindSphereRivalary *ms, size_t capacity, const MindSphereConfig *config);
void mindsphere_free(MindSphereRivalary *ms);
RivalIdentity *mindsphere_add_rival(MindSphereRivalary *ms, const char *name, const char *archetype, unsigned int seed);
AntithEntity *mindsphere_add_antithentity(MindSphereRivalary *ms, const char *name, const char *archetype, unsigned int seed);
int mindsphere_choose_action(RivalIdentity *rival, int state);
void mindsphere_record_outcome(MindSphereRivalary *ms, RivalIdentity *rival, int state, int action, double reward, int next_state, int done);
void mindsphere_record_dialogue_choice(RivalIdentity *rival, double mercy_delta, double duty_delta, double candor_delta, double ambition_delta);
void mindsphere_record_consequence(RivalIdentity *rival, double severity, int spared_opponent, int promise_kept);
void mindsphere_seed_actor_profile(MindActorProfile *profile, const char *label, unsigned int seed);
void mindsphere_seed_player_profile(MindSphereRivalary *ms, const char *label, unsigned int seed);
void mindsphere_record_player_style(MindSphereRivalary *ms, double pressure, double counter_bias, double spacing_bias, double combo_affinity);
void mindsphere_record_player_choice(MindSphereRivalary *ms, double mercy_delta, double duty_delta, double candor_delta, double ambition_delta);
void mindsphere_sync_resonance(MindSphereRivalary *ms);
void mindsphere_collect_narrative_hooks(const MindSphereRivalary *ms, MindSphereNarrativeHooks *out_hooks);
/* replay rehearsal returns the number of sampled entries consumed for training */
size_t mindsphere_rehearse_rival(RivalIdentity *rival, size_t sample_count);
size_t mindsphere_rehearse_all(MindSphereRivalary *ms, size_t sample_count);
double mindsphere_compute_threat(const RivalIdentity *rival);
void mindsphere_describe_rival(const RivalIdentity *rival, char *buffer, size_t buffer_size);
int mindsphere_save(const MindSphereRivalary *ms, const char *path);
int mindsphere_load(MindSphereRivalary *ms, const char *path);


#endif
