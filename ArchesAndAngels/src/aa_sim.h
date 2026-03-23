#ifndef AA_SIM_H
#define AA_SIM_H

#include <stdint.h>

#define AA_FACTION_COUNT 6
#define AA_DISTRICT_COUNT 5
#define AA_MAX_INCIDENTS 8

typedef enum AADistrictId {
    AA_RELAY_WARD = 0,
    AA_EMBER_FOREST_MARGIN,
    AA_VELVET_ARCADE,
    AA_ASH_BASILICA,
    AA_ANTLER_RAIL_FRONTIER,
} AADistrictId;

typedef enum AAFactionId {
    AA_ARCH_RELAY_HOUSES = 0,
    AA_PROTO_HOMO_EMBER_COURTS,
    AA_VELVET_PHARMACATE,
    AA_CHOIRS_OF_OBLIVION,
    AA_ANTLER_PRINCIPALITIES,
    AA_BRASS_MARIANISTS,
} AAFactionId;

typedef struct AAFaction {
    const char *name;
    int32_t force;
    int32_t doctrine;
    int32_t vice;
    int32_t industry;
    int32_t legitimacy;
} AAFaction;

typedef struct AADistrict {
    const char *name;
    int32_t labor;
    int32_t unrest;
    int32_t worship;
    int32_t vice;
    int32_t supply;
    AAFactionId controlling_faction;
} AADistrict;

typedef struct AAIncident {
    const char *label;
    const char *summary;
    AAFactionId aggressor;
    AAFactionId responder;
    int32_t severity;
} AAIncident;

typedef enum AAOperationId {
    AA_OPERATION_PUBLIC_WORKS = 0,
    AA_OPERATION_RELAY_CRACKDOWN,
    AA_OPERATION_CONSECRATE_PROCESSION,
    AA_OPERATION_SMUGGLE_COMPACT,
    AA_OPERATION_MUSTER_COLUMN,
    AA_OPERATION_ARCHIVE_CENSUS,
} AAOperationId;

typedef struct AAFactionAgenda {
    const char *label;
    const char *demand;
    AADistrictId target_district;
    AAOperationId desired_operation;
    int32_t urgency;
    int32_t momentum;
} AAFactionAgenda;

typedef struct AADistrictScenario {
    const char *title;
    const char *summary;
    const char *phase;
    AAOperationId stabilizing_operation;
    int32_t intensity;
    int32_t progress;
    int32_t cycle;
    int32_t generation;
    AAOperationId last_directive;
    int32_t recommendation_streak;
    int32_t ignored_recommendation_streak;
} AADistrictScenario;

typedef enum AADirectorPolicyId {
    AA_POLICY_NONE = 0,
    AA_POLICY_UNIFICATION_DOCTRINE,
    AA_POLICY_FREE_COMMERCE,
    AA_POLICY_MARTIAL_CONSOLIDATION,
    AA_POLICY_TOLERANCE_EDICT,
    AA_POLICY_MEMORIA_INTERDICT,
} AADirectorPolicyId;

#define AA_POLICY_COUNT 6

typedef struct AADirectorPolicy {
    const char *name;
    const char *summary;
    int32_t weeks_active;
    int32_t weeks_remaining;
} AADirectorPolicy;

#define AA_PROTAGONIST_COUNT 3
#define AA_MAX_MISSIONS 4

typedef struct AAProtagonist {
    const char *name;
    const char *title;
    const char *district_affinity;
    AADistrictId home_district;
    int32_t combat_readiness;
    int32_t intel_access;
    int32_t faction_trust[AA_FACTION_COUNT];
} AAProtagonist;

typedef struct AAMission {
    const char *label;
    const char *briefing;
    AADistrictId target_district;
    AAOperationId required_operation;
    int32_t protagonist_index;
    int32_t difficulty;
    int32_t active;
} AAMission;

typedef struct AASimState {
    uint32_t seed;
    int32_t week;
    int32_t treasury;
    int32_t fervor;
    int32_t intelligence;
    AAFaction factions[AA_FACTION_COUNT];
    AADistrict districts[AA_DISTRICT_COUNT];
    AAFactionAgenda agendas[AA_FACTION_COUNT];
    AADistrictScenario scenarios[AA_DISTRICT_COUNT];
    AADirectorPolicy active_policy;
    AADirectorPolicyId active_policy_id;
    AAProtagonist protagonists[AA_PROTAGONIST_COUNT];
    AAMission missions[AA_MAX_MISSIONS];
    int32_t mission_count;
    AAIncident incidents[AA_MAX_INCIDENTS];
    int32_t incident_count;
} AASimState;

void aa_sim_begin_week(AASimState *state);
void aa_sim_init(AASimState *state, uint32_t seed);
void aa_sim_apply_operation(AASimState *state, AAOperationId operation, AADistrictId district_id);
void aa_sim_apply_policy(AASimState *state, AADirectorPolicyId policy_id);
void aa_sim_step(AASimState *state);
void aa_sim_describe(const AASimState *state);
const char *aa_operation_name(AAOperationId operation);
const char *aa_policy_name(AADirectorPolicyId policy_id);
int32_t aa_district_pressure(const AASimState *state, AADistrictId district_id);
const char *aa_district_condition(const AASimState *state, AADistrictId district_id);
AAOperationId aa_recommend_operation(const AASimState *state, AADistrictId district_id);
int32_t aa_campaign_stability(const AASimState *state);
void aa_generate_missions(AASimState *state);
void aa_describe_missions(const AASimState *state);
void aa_describe_protagonists(const AASimState *state);

#endif