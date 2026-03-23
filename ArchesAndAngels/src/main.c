#include "aa_sim.h"
#include "aa_export.h"

#include "..\ArchesAndAngels_Sinner_of_Oblivion.h"

#include <string.h>
#include <stdio.h>


typedef struct AAPlannedTurn {
    AAOperationId operation;
    AADistrictId district;
    AADirectorPolicyId policy;
    const char *note;
} AAPlannedTurn;


static AADistrictId aa_pick_hottest_district(const AASimState *state) {
    int32_t index;
    int32_t best_pressure = -1;
    AADistrictId best_district = AA_RELAY_WARD;
    for (index = 0; index < AA_DISTRICT_COUNT; ++index) {
        int32_t pressure = aa_district_pressure(state, (AADistrictId)index);
        if (pressure > best_pressure) {
            best_pressure = pressure;
            best_district = (AADistrictId)index;
        }
    }
    return best_district;
}


static void aa_print_turn_header(const AASimState *state, int32_t turn, AADirectorPolicyId policy_id) {
    AADistrictId district = aa_pick_hottest_district(state);
    AAFactionId controller = state->districts[district].controlling_faction;
    printf("Week %d pre-brief\n", turn + 1);
    printf(
        "  Highest pressure district: %s (%s, pressure=%d)\n",
        state->districts[district].name,
        aa_district_condition(state, district),
        aa_district_pressure(state, district)
    );
    printf("  Recommended operation: %s\n", aa_operation_name(aa_recommend_operation(state, district)));
    printf(
        "  Active scenario card: %s [%s, gen %d, cycle %d]\n",
        state->scenarios[district].title,
        state->scenarios[district].phase,
        state->scenarios[district].generation,
        state->scenarios[district].cycle
    );
    printf("  Dominant faction signature: %s\n", arches_and_angels_faction_signature(controller));
    printf("  Story pillar emphasis: %s\n", arches_and_angels_story_pillar(turn));
    if (policy_id != AA_POLICY_NONE) {
        printf("  Director policy this week: %s\n", aa_policy_name(policy_id));
    }
}


static void aa_print_final_assessment(const AASimState *state) {
    int32_t stability = aa_campaign_stability(state);
    AADistrictId district = aa_pick_hottest_district(state);
    int32_t terminal_count = 0;
    int32_t settled_count = 0;
    int32_t index;
    for (index = 0; index < AA_DISTRICT_COUNT; ++index) {
        const char *phase = state->scenarios[index].phase;
        if (phase[0] == 't') { terminal_count += 1; }
        if (phase[0] == 's' && phase[1] == 'e') { settled_count += 1; }
    }
    printf("Final Assessment\n");
    printf("  Campaign stability: %d\n", stability);
    printf("  Residual flashpoint: %s via %s\n", state->districts[district].name, state->scenarios[district].title);
    printf("  Terminal crises: %d  Settled districts: %d\n", terminal_count, settled_count);
    if (stability >= 520) {
        printf("  Outlook: fragile consolidation. The merged city has not healed, but it has chosen to keep existing.\n");
    } else if (stability >= 430) {
        printf("  Outlook: unstable coexistence. Major districts are still governable, but another panic wave could crack the civic shell.\n");
    } else {
        printf("  Outlook: civic fracture. The merger remains a contested wound and armed doctrine will likely outrun administration next.\n");
    }
    if (terminal_count >= 3) {
        printf("  Strategic note: multiple districts have reached terminal crisis. The simulation maps are fracturing beyond civic recovery.\n");
    } else if (settled_count >= 3) {
        printf("  Strategic note: multiple districts have reached settled state. The traversal layer can open with stable home territories.\n");
    }
}


int main(int argc, char **argv) {
    AASimState state;
    int32_t turn;
    const char *json_output_path = 0;
    int arg_index;
    static const AAPlannedTurn opening_plan[] = {
        {AA_OPERATION_PUBLIC_WORKS, AA_RELAY_WARD, AA_POLICY_NONE, "Reopen infrastructure before the merged city tears its own supply lines apart."},
        {AA_OPERATION_SMUGGLE_COMPACT, AA_VELVET_ARCADE, AA_POLICY_TOLERANCE_EDICT, "Buy calm with contraband and medicine while legitimacy is still fluid. Suspend doctrine enforcement."},
        {AA_OPERATION_CONSECRATE_PROCESSION, AA_ASH_BASILICA, AA_POLICY_NONE, "Turn worship into public order before panic hardens into insurgency."},
        {AA_OPERATION_MUSTER_COLUMN, AA_ANTLER_RAIL_FRONTIER, AA_POLICY_MARTIAL_CONSOLIDATION, "Secure the rail frontier before hybrid raiders become the map's default logic. Declare martial authority."},
        {AA_OPERATION_ARCHIVE_CENSUS, AA_EMBER_FOREST_MARGIN, AA_POLICY_NONE, "Map the population so myth, labor, and hunger stop moving invisibly."},
        {AA_OPERATION_RELAY_CRACKDOWN, AA_RELAY_WARD, AA_POLICY_MEMORIA_INTERDICT, "Force the capital to declare what kind of order it actually intends to become. Freeze memory rewriting."},
        {AA_OPERATION_PUBLIC_WORKS, AA_VELVET_ARCADE, AA_POLICY_FREE_COMMERCE, "Shore up clinic infrastructure with open trade before the mercy market devours itself."},
        {AA_OPERATION_CONSECRATE_PROCESSION, AA_ASH_BASILICA, AA_POLICY_NONE, "Renew the mourning compact to prevent necropolitical entrenchment."},
        {AA_OPERATION_MUSTER_COLUMN, AA_ANTLER_RAIL_FRONTIER, AA_POLICY_UNIFICATION_DOCTRINE, "Press the frontier again under unified authority before shrine raiders regroup."},
        {AA_OPERATION_ARCHIVE_CENSUS, AA_RELAY_WARD, AA_POLICY_NONE, "Final census to lock the capital into legibility before the simulation closes."},
    };

    for (arg_index = 1; arg_index < argc; ++arg_index) {
        if (strcmp(argv[arg_index], "--json-out") == 0 && (arg_index + 1) < argc) {
            json_output_path = argv[++arg_index];
        }
    }

    aa_sim_init(&state, 0xA314613u);

    printf("%s\n", arches_and_angels_project_title());
    printf("Campaign frame: %s\n", arches_and_angels_project_core_premise());
    printf("Format vector: %s\n", arches_and_angels_project_format());
    printf("Strategic simulation slice with director policies, scenario successor chains, and mission briefings\n\n");

    aa_describe_protagonists(&state);
    printf("\n");

    for (turn = 0; turn < (int32_t)(sizeof(opening_plan) / sizeof(opening_plan[0])); ++turn) {
        aa_sim_begin_week(&state);

        if (opening_plan[turn].policy != AA_POLICY_NONE) {
            aa_sim_apply_policy(&state, opening_plan[turn].policy);
        }

        aa_print_turn_header(&state, turn, opening_plan[turn].policy);
        printf("Turn %d directive: %s in %s\n", turn + 1, aa_operation_name(opening_plan[turn].operation), state.districts[opening_plan[turn].district].name);
        printf("  %s\n", opening_plan[turn].note);
        if (aa_recommend_operation(&state, opening_plan[turn].district) == opening_plan[turn].operation) {
            printf("  Recommendation delta: chosen operation matches current recommendation\n");
        } else {
            printf("  Recommendation delta: chosen operation diverges from current recommendation\n");
        }
        aa_sim_apply_operation(&state, opening_plan[turn].operation, opening_plan[turn].district);
        aa_sim_step(&state);
        aa_sim_describe(&state);

        aa_generate_missions(&state);
        aa_describe_missions(&state);

        printf("\n");
    }

    aa_print_final_assessment(&state);

    if (json_output_path) {
        aa_generate_missions(&state);
        if (aa_export_state_json(&state, json_output_path) != 0) {
            fprintf(stderr, "Failed to export ArchesAndAngels state to %s\n", json_output_path);
            return 1;
        }
        printf("Exported campaign state to %s\n", json_output_path);
    }

    return 0;
}