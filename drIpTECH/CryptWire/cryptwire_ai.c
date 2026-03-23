/*
 * CryptWire AI Module v0.1.0 — cryptwire_ai.c
 *
 * 8-dimensional threat analysis engine + genetic algorithm for adaptive
 * crypto pipeline parameter evolution.
 *
 * Threat dimensions (CW_DIM_*):
 *   0  ENTROPY_ANOM     — unusual entropy in observed data streams
 *   1  FREQ_BURST       — request/packet frequency burst detection
 *   2  TIMING_PATTERN   — regularity suggesting timing-channel attack
 *   3  SRC_REPUTATION   — known-bad signature matches
 *   4  PAYLOAD_SHAPE    — abnormal size/structure distribution
 *   5  PROTO_INTEGRITY  — protocol conformance anomalies
 *   6  TEMPORAL_CLUSTER — events clustered in time (attack waves)
 *   7  KEY_PROBE        — elevated key-derivation overhead events
 *
 * Genetic algorithm:
 *   Population of CW_GA_POPULATION genomes.
 *   Each genome: float weights[8], uint8_t algo-per-stage[8], num_stages, seal_extra.
 *   Fitness = 1 / (weighted_threat_score * false_positive_rate + epsilon)
 *   Evolution triggered every 100 observed events, or immediately on confirmed threat.
 */

#include "cryptwire_ai.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <time.h>

/* ─── Internal utilities ─────────────────────────────────────────── */

/* Pseudo-random float in [0, 1) — seeded lazily */
static unsigned long cw_rand_state = 0;

static float cw_frand(void) {
    if (cw_rand_state == 0) cw_rand_state = (unsigned long)time(NULL);
    /* xorshift32 */
    cw_rand_state ^= cw_rand_state << 13;
    cw_rand_state ^= cw_rand_state >> 17;
    cw_rand_state ^= cw_rand_state << 5;
    return (float)(cw_rand_state & 0x7FFFFFFFUL) / (float)0x80000000UL;
}

/* Box-Muller Gaussian sample N(0, sigma) */
static float cw_gauss(float sigma) {
    float u = cw_frand();
    float v = cw_frand();
    if (u < 1e-7f) u = 1e-7f;
    float n = sqrtf(-2.0f * logf(u)) * cosf(2.0f * 3.14159265f * v);
    return n * sigma;
}

static float clampf(float x, float lo, float hi) {
    return x < lo ? lo : (x > hi ? hi : x);
}

/* ─── Genome initialisation (random) ────────────────────────────── */
static void genome_randomize(CWGenome *g) {
    for (int i = 0; i < CW_AI_DIMS; i++) {
        g->weights[i] = 0.1f + cw_frand() * 0.9f;   /* (0.1, 1.0] */
    }
    for (int i = 0; i < CW_GA_MAX_STAGES; i++) {
        /* Cycle through the 4 known algorithms */
        g->algo[i] = (uint8_t)(1 + ((int)(cw_frand() * 3.99f) % 4));
    }
    g->num_stages = 3 + (uint8_t)(cw_frand() * 6.0f) % 6;  /* 3..8 */
    if (g->num_stages < 3) g->num_stages = 3;
    if (g->num_stages > 8) g->num_stages = 8;
    g->seal_extra = (uint32_t)(cw_frand() * 512.0f);
    g->fitness = 0.0;
}

/* ─── Fitness evaluation ─────────────────────────────────────────── */
/*
 * Fitness is computed from the threat scores the genome would have
 * produced vs what actually happened.  We approximate this as:
 *   threat_estimate = dot(weights, dim_scores)  (normalised to [0,1])
 *   fp_rate = (total_alerts - confirmed) / (total_alerts + 1)
 *   fitness = 1.0 / (threat_estimate * fp_rate + 1e-6)
 * A genome that assigns high weight to dimensions that are genuinely
 * correlated with confirmed threats, and low weight to noisy ones,
 * will minimise fp_rate and raise fitness.
 */
static void genome_evaluate(CWGenome *g, const CWAIState *ai) {
    double weighted_threat = 0.0;
    double weight_sum = 0.0;
    for (int d = 0; d < CW_AI_DIMS; d++) {
        weighted_threat += (double)g->weights[d] * ai->dim_score[d];
        weight_sum      += (double)g->weights[d];
    }
    if (weight_sum > 0.0) weighted_threat /= weight_sum;
    double fp_rate = 1.0;
    if (ai->total_alerts > 0) {
        double confirmed = (double)ai->confirmed_threats;
        fp_rate = 1.0 - (confirmed / (double)(ai->total_alerts + 1));
        if (fp_rate < 1e-6) fp_rate = 1e-6;
    }
    g->fitness = 1.0 / (weighted_threat * fp_rate + 1e-6);
}

/* ─── Tournament selection ───────────────────────────────────────── */
static int tournament_select(const CWAIState *ai, int k) {
    int best = (int)(cw_frand() * CW_GA_POPULATION) % CW_GA_POPULATION;
    for (int i = 1; i < k; i++) {
        int candidate = (int)(cw_frand() * CW_GA_POPULATION) % CW_GA_POPULATION;
        if (ai->population[candidate].fitness > ai->population[best].fitness)
            best = candidate;
    }
    return best;
}

/* ─── Single-point crossover ─────────────────────────────────────── */
static void genome_crossover(const CWGenome *a, const CWGenome *b, CWGenome *child) {
    /* Crossover point in weights array */
    int cx = (int)(cw_frand() * (CW_AI_DIMS - 1)) + 1;  /* 1..7 */
    for (int i = 0; i < CW_AI_DIMS; i++) {
        child->weights[i] = (i < cx) ? a->weights[i] : b->weights[i];
    }
    /* Algo array crossover at a different point */
    int cx2 = (int)(cw_frand() * (CW_GA_MAX_STAGES - 1)) + 1;
    for (int i = 0; i < CW_GA_MAX_STAGES; i++) {
        child->algo[i] = (i < cx2) ? a->algo[i] : b->algo[i];
    }
    /* Blend num_stages and seal_extra */
    child->num_stages  = (cw_frand() < 0.5f) ? a->num_stages : b->num_stages;
    child->seal_extra  = (uint32_t)(((float)a->seal_extra + (float)b->seal_extra) * 0.5f);
    child->fitness = 0.0;
}

/* ─── Mutation ───────────────────────────────────────────────────── */
static void genome_mutate(CWGenome *g, float rate) {
    for (int i = 0; i < CW_AI_DIMS; i++) {
        if (cw_frand() < rate) {
            g->weights[i] = clampf(g->weights[i] + cw_gauss(0.1f), 0.01f, 1.0f);
        }
    }
    for (int i = 0; i < CW_GA_MAX_STAGES; i++) {
        if (cw_frand() < rate) {
            g->algo[i] = (uint8_t)(1 + ((int)(cw_frand() * 3.99f)) % 4);
        }
    }
    if (cw_frand() < rate) {
        int delta = (cw_frand() < 0.5f) ? 1 : -1;
        int ns = (int)g->num_stages + delta;
        if (ns < 3) ns = 3;
        if (ns > 8) ns = 8;
        g->num_stages = (uint8_t)ns;
    }
    if (cw_frand() < rate) {
        g->seal_extra = (uint32_t)clampf(
            (float)g->seal_extra + cw_gauss(64.0f), 0.0f, 8192.0f);
    }
}

/* ─── Sort population descending by fitness ─────────────────────── */
static int genome_cmp(const void *a, const void *b) {
    double fa = ((const CWGenome *)a)->fitness;
    double fb = ((const CWGenome *)b)->fitness;
    if (fa > fb) return -1;
    if (fa < fb) return  1;
    return 0;
}

/* ─── cw_ai_init ─────────────────────────────────────────────────── */
CWAIState *cw_ai_init(void) {
    CWAIState *ai = (CWAIState *)calloc(1, sizeof(CWAIState));
    if (!ai) return NULL;

    ai->dim_ema_alpha = 0.15;

    /* Seed random state from current time */
    cw_rand_state = (unsigned long)time(NULL);

    /* Initialise population with random genomes */
    for (int i = 0; i < CW_GA_POPULATION; i++) {
        genome_randomize(&ai->population[i]);
    }
    ai->generation = 0;
    ai->best_idx   = 0;

    /* Default: no signatures loaded */
    ai->sig_count = 0;

    /* EMA dim scores start at 0 */
    for (int d = 0; d < CW_AI_DIMS; d++) ai->dim_score[d] = 0.0;

    return ai;
}

/* ─── cw_ai_free ─────────────────────────────────────────────────── */
void cw_ai_free(CWAIState *ai) {
    if (!ai) return;
    /* Zero sensitive state before freeing */
    memset(ai, 0, sizeof(CWAIState));
    free(ai);
}

/* ─── cw_ai_observe ──────────────────────────────────────────────── */
void cw_ai_observe(CWAIState *ai, int dimension, float magnitude, double timestamp) {
    if (!ai || dimension < 0 || dimension >= CW_AI_DIMS) return;

    if (timestamp <= 0.0) timestamp = (double)time(NULL);

    /* EMA update for the specific dimension */
    double m = (double)clampf(magnitude, 0.0f, 1.0f);
    double a = ai->dim_ema_alpha;
    ai->dim_score[dimension] = a * m + (1.0 - a) * ai->dim_score[dimension];

    /* Temporal clustering: record event in ring buffer */
    CWThreatEvent *ev = &ai->events[ai->event_head % CW_EVENT_RING_SIZE];
    ev->timestamp = timestamp;
    ev->dimension = dimension;
    ev->magnitude = magnitude;
    ai->event_head = (ai->event_head + 1) % CW_EVENT_RING_SIZE;
    if (ai->event_count < CW_EVENT_RING_SIZE) ai->event_count++;

    /* Temporal clustering analysis:
     * Count events in the last 5-second window and boost CW_DIM_TEMPORAL_CLUSTER */
    int recent = 0;
    double window_start = timestamp - 5.0;
    for (int i = 0; i < ai->event_count; i++) {
        int idx = ((ai->event_head - 1 - i) + CW_EVENT_RING_SIZE) % CW_EVENT_RING_SIZE;
        if (ai->events[idx].timestamp >= window_start) recent++;
        else break;
    }
    if (recent > 10) {
        double cluster_score = clampf((float)(recent - 10) / 50.0f, 0.0f, 1.0f);
        ai->dim_score[CW_DIM_TEMPORAL_CLUSTER] =
            a * cluster_score + (1.0 - a) * ai->dim_score[CW_DIM_TEMPORAL_CLUSTER];
    }

    /* Alert counter */
    if (m > 0.5) ai->total_alerts++;

    /* Trigger evolution every 100 events */
    ai->events_since_evolution++;
    if (ai->events_since_evolution >= 100) {
        cw_ai_evolve(ai);
        ai->events_since_evolution = 0;
    }

    /* Recompute aggregate */
    ai->aggregate_threat = cw_ai_aggregate_score(ai);
}

/* ─── cw_ai_scan_signatures ──────────────────────────────────────── */
float cw_ai_scan_signatures(CWAIState *ai, const uint8_t *data, size_t len) {
    if (!ai || !data || len == 0) return 0.0f;
    float max_sev = 0.0f;

    for (int i = 0; i < ai->sig_count; i++) {
        const CWThreatSig *sig = &ai->sigs[i];
        if (!sig->active || sig->pattern_len <= 0) continue;
        /* Naive substring scan — fast enough for short signatures */
        for (size_t off = 0; off + (size_t)sig->pattern_len <= len; off++) {
            if (memcmp(data + off, sig->pattern, (size_t)sig->pattern_len) == 0) {
                if (sig->severity > max_sev) max_sev = sig->severity;
                break;
            }
        }
    }

    if (max_sev > 0.0f) {
        cw_ai_observe(ai, CW_DIM_PAYLOAD_SHAPE, max_sev, 0.0);
    }
    return max_sev;
}

/* ─── cw_ai_aggregate_score ──────────────────────────────────────── */
double cw_ai_aggregate_score(const CWAIState *ai) {
    if (!ai) return 0.0;
    const CWGenome *best = &ai->population[ai->best_idx];
    double score = 0.0, weight_sum = 0.0;
    for (int d = 0; d < CW_AI_DIMS; d++) {
        score       += (double)best->weights[d] * ai->dim_score[d];
        weight_sum  += (double)best->weights[d];
    }
    if (weight_sum <= 0.0) return 0.0;
    double normalised = score / weight_sum;
    return normalised > 1.0 ? 1.0 : normalised;
}

/* ─── cw_ai_recommend_algo ───────────────────────────────────────── */
int cw_ai_recommend_algo(const CWAIState *ai, int stage_idx) {
    if (!ai || stage_idx < 0 || stage_idx >= CW_GA_MAX_STAGES) return 1; /* AES-GCM */
    int a = (int)ai->population[ai->best_idx].algo[stage_idx];
    if (a < 1 || a > 4) a = 1;
    return a;
}

/* ─── cw_ai_recommend_num_stages ─────────────────────────────────── */
int cw_ai_recommend_num_stages(const CWAIState *ai) {
    if (!ai) return 3;
    int base = (int)ai->population[ai->best_idx].num_stages;
    /* Also scale with aggregate threat: critical threat → max stages */
    double score = cw_ai_aggregate_score(ai);
    int by_threat = 3 + (int)(score * 5.0);  /* 3..8 */
    return (by_threat > base) ? by_threat : base;
}

/* ─── cw_ai_recommend_seal_extra ─────────────────────────────────── */
uint32_t cw_ai_recommend_seal_extra(const CWAIState *ai) {
    if (!ai) return 0;
    return ai->population[ai->best_idx].seal_extra;
}

/* ─── cw_ai_confirm_threat ───────────────────────────────────────── */
void cw_ai_confirm_threat(CWAIState *ai) {
    if (!ai) return;
    ai->confirmed_threats++;
    /* Immediately evolve to reinforce the detecting genome */
    cw_ai_evolve(ai);
}

/* ─── cw_ai_report_false_positive ───────────────────────────────── */
void cw_ai_report_false_positive(CWAIState *ai) {
    if (!ai) return;
    /* Penalise the best genome by temporarily zeroing its fitness */
    ai->population[ai->best_idx].fitness *= 0.5;
    cw_ai_evolve(ai);
}

/* ─── cw_ai_evolve — one GA generation ──────────────────────────── */
void cw_ai_evolve(CWAIState *ai) {
    if (!ai) return;

    /* Evaluate all genomes */
    for (int i = 0; i < CW_GA_POPULATION; i++) {
        genome_evaluate(&ai->population[i], ai);
    }

    /* Sort by fitness descending */
    qsort(ai->population, CW_GA_POPULATION, sizeof(CWGenome), genome_cmp);
    ai->best_idx = 0;  /* best is at index 0 after sort */

    /* Elite selection: preserve top CW_GA_ELITE_N unchanged */
    CWGenome next_gen[CW_GA_POPULATION];
    memcpy(next_gen, ai->population, CW_GA_ELITE_N * sizeof(CWGenome));

    /* Fill the rest via tournament selection + crossover + mutation */
    for (int i = CW_GA_ELITE_N; i < CW_GA_POPULATION; i++) {
        int p1 = tournament_select(ai, 4);
        int p2 = tournament_select(ai, 4);
        genome_crossover(&ai->population[p1], &ai->population[p2], &next_gen[i]);
        genome_mutate(&next_gen[i], CW_GA_MUTATION_RATE);
    }

    memcpy(ai->population, next_gen, CW_GA_POPULATION * sizeof(CWGenome));
    ai->generation++;
    ai->total_evolutions++;
}

/* ─── cw_ai_load_signatures ──────────────────────────────────────── */
/*
 * File format (text, one signature per line):
 *   <id> <severity> <hex_pattern> <description...>
 * Example:
 *   1 0.9 deadbeefcafe "SQL injection probe"
 */
int cw_ai_load_signatures(CWAIState *ai, const char *path) {
    if (!ai || !path) return -1;
    FILE *f = fopen(path, "r");
    if (!f) return -1;

    ai->sig_count = 0;
    char line[512];
    while (fgets(line, sizeof(line), f) && ai->sig_count < CW_MAX_SIGNATURES) {
        if (line[0] == '#' || line[0] == '\n') continue;

        CWThreatSig sig;
        memset(&sig, 0, sizeof(sig));

        char hex_buf[128] = {0};
        char desc_buf[128] = {0};

        if (sscanf(line, "%u %f %127s %127[^\n]",
                   &sig.id, &sig.severity, hex_buf, desc_buf) < 3) continue;

        /* Parse hex pattern */
        size_t hex_len = strlen(hex_buf);
        sig.pattern_len = (int)(hex_len / 2);
        if (sig.pattern_len > 32) sig.pattern_len = 32;
        for (int i = 0; i < sig.pattern_len; i++) {
            unsigned int byte_val = 0;
            if (sscanf(hex_buf + i*2, "%02x", &byte_val) == 1)
                sig.pattern[i] = (uint8_t)byte_val;
        }

        strncpy(sig.description, desc_buf,
                sizeof(sig.description) - 1);
        sig.severity = clampf(sig.severity, 0.0f, 1.0f);
        sig.active = 1;
        ai->sigs[ai->sig_count++] = sig;
    }
    fclose(f);
    return ai->sig_count;
}

/* ─── cw_ai_status_string ────────────────────────────────────────── */
void cw_ai_status_string(const CWAIState *ai, char *buf, size_t buf_len) {
    if (!ai || !buf || buf_len < 32) return;

    static const char *dim_names[CW_AI_DIMS] = {
        "EntropyAnom", "FreqBurst", "TimingPat", "SrcReputation",
        "PayloadShape", "ProtoInteg", "TempCluster", "KeyProbe"
    };

    const CWGenome *best = &ai->population[0];
    double agg = cw_ai_aggregate_score(ai);

    int off = snprintf(buf, buf_len,
        "=== CryptWire AI State ===\n"
        "Aggregate threat:  %.4f\n"
        "GA generation:     %d  (evolutions: %llu)\n"
        "Best genome stages:%d  seal_extra: %u\n"
        "Alerts: %llu  Confirmed: %llu\n"
        "Signatures loaded: %d\n"
        "Dimension scores:\n",
        agg, ai->generation,
        (unsigned long long)ai->total_evolutions,
        (int)best->num_stages, best->seal_extra,
        (unsigned long long)ai->total_alerts,
        (unsigned long long)ai->confirmed_threats,
        ai->sig_count);

    for (int d = 0; d < CW_AI_DIMS && off < (int)buf_len - 64; d++) {
        off += snprintf(buf + off, buf_len - off,
                        "  %-14s  score=%.4f  weight=%.3f\n",
                        dim_names[d], ai->dim_score[d], best->weights[d]);
    }
}
