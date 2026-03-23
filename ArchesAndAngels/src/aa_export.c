#include "aa_export.h"

#include <stdio.h>


static void json_write_escaped(FILE *stream, const char *text) {
    const char *cursor = text ? text : "";
    fputc('"', stream);
    while (*cursor) {
        switch (*cursor) {
            case '\\': fputs("\\\\", stream); break;
            case '"': fputs("\\\"", stream); break;
            case '\n': fputs("\\n", stream); break;
            case '\r': fputs("\\r", stream); break;
            case '\t': fputs("\\t", stream); break;
            default: fputc(*cursor, stream); break;
        }
        ++cursor;
    }
    fputc('"', stream);
}


static void json_write_campaign(FILE *stream, const AASimState *state) {
    fprintf(stream, "  \"campaign\": {\n");
    fprintf(stream, "    \"week\": %d,\n", state->week);
    fprintf(stream, "    \"treasury\": %d,\n", state->treasury);
    fprintf(stream, "    \"fervor\": %d,\n", state->fervor);
    fprintf(stream, "    \"intelligence\": %d,\n", state->intelligence);
    fprintf(stream, "    \"stability\": %d,\n", aa_campaign_stability(state));
    fprintf(stream, "    \"activePolicy\": ");
    json_write_escaped(stream, aa_policy_name(state->active_policy_id));
    fprintf(stream, "\n  }");
}


static void json_write_factions(FILE *stream, const AASimState *state) {
    int32_t index;
    fprintf(stream, "  \"factions\": [\n");
    for (index = 0; index < AA_FACTION_COUNT; ++index) {
        const AAFaction *faction = &state->factions[index];
        fprintf(stream, "    {\"id\": %d, \"name\": ", index);
        json_write_escaped(stream, faction->name);
        fprintf(stream, ", \"force\": %d, \"doctrine\": %d, \"vice\": %d, \"industry\": %d, \"legitimacy\": %d}",
            faction->force, faction->doctrine, faction->vice, faction->industry, faction->legitimacy);
        fprintf(stream, index + 1 < AA_FACTION_COUNT ? ",\n" : "\n");
    }
    fprintf(stream, "  ]");
}


static void json_write_districts(FILE *stream, const AASimState *state) {
    int32_t index;
    fprintf(stream, "  \"districts\": [\n");
    for (index = 0; index < AA_DISTRICT_COUNT; ++index) {
        const AADistrict *district = &state->districts[index];
        const AADistrictScenario *scenario = &state->scenarios[index];
        fprintf(stream, "    {\"id\": %d, \"name\": ", index);
        json_write_escaped(stream, district->name);
        fprintf(stream, ", \"control\": ");
        json_write_escaped(stream, state->factions[district->controlling_faction].name);
        fprintf(stream, ", \"labor\": %d, \"unrest\": %d, \"worship\": %d, \"vice\": %d, \"supply\": %d, \"pressure\": %d, \"condition\": ",
            district->labor, district->unrest, district->worship, district->vice, district->supply,
            aa_district_pressure(state, (AADistrictId)index));
        json_write_escaped(stream, aa_district_condition(state, (AADistrictId)index));
        fprintf(stream, ", \"recommendedOperation\": ");
        json_write_escaped(stream, aa_operation_name(aa_recommend_operation(state, (AADistrictId)index)));
        fprintf(stream, ", \"scenario\": {");
        fprintf(stream, "\"title\": ");
        json_write_escaped(stream, scenario->title);
        fprintf(stream, ", \"phase\": ");
        json_write_escaped(stream, scenario->phase);
        fprintf(stream, ", \"intensity\": %d, \"progress\": %d, \"generation\": %d, \"cycle\": %d, \"recommendationStreak\": %d, \"ignoredRecommendationStreak\": %d, \"focus\": ",
            scenario->intensity, scenario->progress, scenario->generation, scenario->cycle,
            scenario->recommendation_streak, scenario->ignored_recommendation_streak);
        json_write_escaped(stream, aa_operation_name(scenario->stabilizing_operation));
        fprintf(stream, "}}%s\n", index + 1 < AA_DISTRICT_COUNT ? "," : "");
    }
    fprintf(stream, "  ]");
}


static void json_write_agendas(FILE *stream, const AASimState *state) {
    int32_t index;
    fprintf(stream, "  \"agendas\": [\n");
    for (index = 0; index < AA_FACTION_COUNT; ++index) {
        const AAFactionAgenda *agenda = &state->agendas[index];
        fprintf(stream, "    {\"faction\": ");
        json_write_escaped(stream, state->factions[index].name);
        fprintf(stream, ", \"label\": ");
        json_write_escaped(stream, agenda->label);
        fprintf(stream, ", \"targetDistrict\": ");
        json_write_escaped(stream, state->districts[agenda->target_district].name);
        fprintf(stream, ", \"desiredOperation\": ");
        json_write_escaped(stream, aa_operation_name(agenda->desired_operation));
        fprintf(stream, ", \"urgency\": %d, \"momentum\": %d, \"demand\": ", agenda->urgency, agenda->momentum);
        json_write_escaped(stream, agenda->demand);
        fprintf(stream, "}%s\n", index + 1 < AA_FACTION_COUNT ? "," : "");
    }
    fprintf(stream, "  ]");
}


static void json_write_protagonists(FILE *stream, const AASimState *state) {
    int32_t index;
    fprintf(stream, "  \"protagonists\": [\n");
    for (index = 0; index < AA_PROTAGONIST_COUNT; ++index) {
        const AAProtagonist *protag = &state->protagonists[index];
        fprintf(stream, "    {\"name\": ");
        json_write_escaped(stream, protag->name);
        fprintf(stream, ", \"title\": ");
        json_write_escaped(stream, protag->title);
        fprintf(stream, ", \"homeDistrict\": ");
        json_write_escaped(stream, state->districts[protag->home_district].name);
        fprintf(stream, ", \"districtAffinity\": ");
        json_write_escaped(stream, protag->district_affinity);
        fprintf(stream, ", \"combatReadiness\": %d, \"intelAccess\": %d}", protag->combat_readiness, protag->intel_access);
        fprintf(stream, index + 1 < AA_PROTAGONIST_COUNT ? ",\n" : "\n");
    }
    fprintf(stream, "  ]");
}


static void json_write_missions(FILE *stream, const AASimState *state) {
    int32_t index;
    fprintf(stream, "  \"missions\": [\n");
    for (index = 0; index < state->mission_count; ++index) {
        const AAMission *mission = &state->missions[index];
        fprintf(stream, "    {\"label\": ");
        json_write_escaped(stream, mission->label);
        fprintf(stream, ", \"targetDistrict\": ");
        json_write_escaped(stream, state->districts[mission->target_district].name);
        fprintf(stream, ", \"requiredOperation\": ");
        json_write_escaped(stream, aa_operation_name(mission->required_operation));
        fprintf(stream, ", \"assignedProtagonist\": ");
        json_write_escaped(stream, state->protagonists[mission->protagonist_index].name);
        fprintf(stream, ", \"difficulty\": %d, \"briefing\": ", mission->difficulty);
        json_write_escaped(stream, mission->briefing);
        fprintf(stream, "}%s\n", index + 1 < state->mission_count ? "," : "");
    }
    fprintf(stream, "  ]");
}


static void json_write_incidents(FILE *stream, const AASimState *state) {
    int32_t index;
    fprintf(stream, "  \"incidents\": [\n");
    for (index = 0; index < state->incident_count; ++index) {
        const AAIncident *incident = &state->incidents[index];
        fprintf(stream, "    {\"label\": ");
        json_write_escaped(stream, incident->label);
        fprintf(stream, ", \"severity\": %d, \"aggressor\": ", incident->severity);
        json_write_escaped(stream, state->factions[incident->aggressor].name);
        fprintf(stream, ", \"responder\": ");
        json_write_escaped(stream, state->factions[incident->responder].name);
        fprintf(stream, ", \"summary\": ");
        json_write_escaped(stream, incident->summary);
        fprintf(stream, "}%s\n", index + 1 < state->incident_count ? "," : "");
    }
    fprintf(stream, "  ]");
}


int aa_export_state_json(const AASimState *state, const char *output_path) {
    FILE *stream;
    if (!state || !output_path) {
        return 1;
    }
    stream = fopen(output_path, "w");
    if (!stream) {
        return 2;
    }

    fprintf(stream, "{\n");
    json_write_campaign(stream, state);
    fprintf(stream, ",\n");
    json_write_factions(stream, state);
    fprintf(stream, ",\n");
    json_write_districts(stream, state);
    fprintf(stream, ",\n");
    json_write_agendas(stream, state);
    fprintf(stream, ",\n");
    json_write_protagonists(stream, state);
    fprintf(stream, ",\n");
    json_write_missions(stream, state);
    fprintf(stream, ",\n");
    json_write_incidents(stream, state);
    fprintf(stream, "\n}\n");

    fclose(stream);
    return 0;
}