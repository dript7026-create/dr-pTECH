/*
 * CryptWire AI Module v0.1.0 — cryptwire_ai.h
 *
 * An 8-dimensional real-time threat analysis engine combined with a
 * genetic algorithm (GA) that evolves optimal algorithm selection and
 * pipeline depth parameters in response to confirmed threat events.
 *
 * Threat dimensions (indices 0-7):
 *   0  ENTROPY_ANOM     — unusual entropy in observed data streams
 *   1  FREQ_BURST       — request/packet frequency burst detection
 *   2  TIMING_PATTERN   — regularity suggesting timing-channel attacks
 *   3  SRC_REPUTATION   — score from local known-bad signature database
 *   4  PAYLOAD_SHAPE    — abnormal payload size / structure distribution
 *   5  PROTO_INTEGRITY  — protocol conformance anomalies
 *   6  TEMPORAL_CLUSTER — events clustered in time (attack waves)
 *   7  KEY_PROBE        — elevated key-derivation-overhead events (brute-force)
 *
 * GA genome encodes:
 *   - float weights[8]       : per-dimension sensitivity weights
 *   - uint8_t algo[8]        : preferred CWAlgo per pipeline stage slot
 *   - uint8_t num_stages     : preferred number of pipeline stages (3..8)
 *   - uint32_t seal_extra    : extra seal iterations added to base depth
 *
 * Fitness = 1.0 / ( weighted_threat_score * false_positive_rate + eps )
 */

#ifndef CRYPTWIRE_AI_H
#define CRYPTWIRE_AI_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ─── Threat dimension indices ──────────────────────────────────── */
#define CW_DIM_ENTROPY_ANOM     0
#define CW_DIM_FREQ_BURST       1
#define CW_DIM_TIMING_PATTERN   2
#define CW_DIM_SRC_REPUTATION   3
#define CW_DIM_PAYLOAD_SHAPE    4
#define CW_DIM_PROTO_INTEGRITY  5
#define CW_DIM_TEMPORAL_CLUSTER 6
#define CW_DIM_KEY_PROBE        7
#define CW_AI_DIMS              8

/* ─── GA parameters ─────────────────────────────────────────────── */
#define CW_GA_POPULATION    32
#define CW_GA_MAX_STAGES    8
#define CW_GA_MUTATION_RATE 0.12f
#define CW_GA_ELITE_N       4       /* top N preserved unchanged each gen */
#define CW_GA_GENERATIONS   10      /* generations run per threat event   */

/* ─── Threat signature entry (local database) ───────────────────── */
typedef struct {
    uint32_t id;
    char     description[128];
    uint8_t  pattern[32];    /* partial-match fingerprint */
    int      pattern_len;
    float    severity;       /* 0.0 .. 1.0 */
    int      active;
} CWThreatSig;

#define CW_MAX_SIGNATURES   256

/* ─── GA genome ──────────────────────────────────────────────────── */
typedef struct {
    float    weights[CW_AI_DIMS];    /* per-dim sensitivity             */
    uint8_t  algo[CW_GA_MAX_STAGES]; /* preferred CWAlgo per slot       */
    uint8_t  num_stages;             /* preferred stage count (3..8)    */
    uint32_t seal_extra;             /* extra seal iterations           */
    double   fitness;                /* evaluated fitness (higher=better) */
} CWGenome;

/* ─── Event ring-buffer (for temporal clustering detection) ─────── */
#define CW_EVENT_RING_SIZE  256
typedef struct {
    double   timestamp;    /* seconds since epoch (double for sub-second) */
    int      dimension;
    float    magnitude;
} CWThreatEvent;

/* ─── AI state ───────────────────────────────────────────────────── */
typedef struct {
    /* 8-dimensional live threat scores (exponential moving average) */
    double  dim_score[CW_AI_DIMS];
    double  dim_ema_alpha;           /* EMA smoothing factor, typ. 0.15 */

    /* Aggregate threat score (weighted dot product of genome & scores) */
    double  aggregate_threat;

    /* Genetic algorithm population */
    CWGenome population[CW_GA_POPULATION];
    int      generation;             /* total generations evolved */
    int      best_idx;               /* index of best genome in population */

    /* Event ring buffer */
    CWThreatEvent events[CW_EVENT_RING_SIZE];
    int           event_head;
    int           event_count;

    /* Threat signature database */
    CWThreatSig sigs[CW_MAX_SIGNATURES];
    int         sig_count;

    /* False positive tracking */
    uint64_t  total_alerts;
    uint64_t  confirmed_threats;

    /* Adaptation counters */
    uint64_t  events_since_evolution;
    uint64_t  total_evolutions;
} CWAIState;

/* ─── Public API ─────────────────────────────────────────────────── */

/*
 * Allocate and initialise a CWAIState with a default genome population.
 * Returns NULL on allocation failure.
 */
CWAIState *cw_ai_init(void);

/* Free all resources associated with an AI state. */
void cw_ai_free(CWAIState *ai);

/*
 * Record a threat observation on a specific dimension.
 * dimension : CW_DIM_* constant
 * magnitude : 0.0 (none) .. 1.0 (maximum)
 * timestamp : seconds since epoch (pass 0.0 to use current time)
 *
 * Automatically triggers GA evolution every 100 recorded events.
 */
void cw_ai_observe(CWAIState *ai, int dimension, float magnitude,
                   double timestamp);

/*
 * Check a data buffer against all loaded threat signatures.
 * Returns the highest severity matched (0.0 if no match).
 * Also updates dim_score[CW_DIM_PAYLOAD_SHAPE] on match.
 */
float cw_ai_scan_signatures(CWAIState *ai,
                             const uint8_t *data, size_t len);

/*
 * Compute the current aggregate threat score from the best genome.
 * Returns 0.0 .. 1.0 (1.0 = critical threat).
 */
double cw_ai_aggregate_score(const CWAIState *ai);

/*
 * Recommend the optimal algorithm for a given pipeline stage slot.
 * stage_idx : 0-based pipeline stage index
 * Returns a CWAlgo value from the best genome.
 */
int cw_ai_recommend_algo(const CWAIState *ai, int stage_idx);

/*
 * Recommend the optimal number of pipeline stages given current threat.
 * Returns 3 (low threat) .. 8 (critical threat).
 */
int cw_ai_recommend_num_stages(const CWAIState *ai);

/*
 * Recommend the extra seal iterations to add to the base seal depth.
 */
uint32_t cw_ai_recommend_seal_extra(const CWAIState *ai);

/*
 * Confirm that the last alert was a true positive threat.
 * Updates fitness scoring and may trigger an immediate GA evolution.
 */
void cw_ai_confirm_threat(CWAIState *ai);

/*
 * Mark the last alert as a false positive.
 * Penalises the current best genome and triggers evolution.
 */
void cw_ai_report_false_positive(CWAIState *ai);

/*
 * Run one full generation of the genetic algorithm manually.
 * Normally called automatically, but exposed for external control.
 */
void cw_ai_evolve(CWAIState *ai);

/*
 * Load threat signatures from a text file (one per line):
 *   <id> <severity 0.0-1.0> <hex_pattern> <description>
 */
int cw_ai_load_signatures(CWAIState *ai, const char *path);

/*
 * Fill buf with a human-readable status report (AI state summary).
 * buf must be at least 1024 bytes.
 */
void cw_ai_status_string(const CWAIState *ai, char *buf, size_t buf_len);

#ifdef __cplusplus
}
#endif

#endif /* CRYPTWIRE_AI_H */
