#include "aa_sim.h"

#include <stdio.h>


static int32_t clamp_stat(int32_t value, int32_t low, int32_t high) {
    if (value < low) {
        return low;
    }
    if (value > high) {
        return high;
    }
    return value;
}


static uint32_t aa_next_random(AASimState *state) {
    state->seed = (state->seed * 1664525u) + 1013904223u;
    return state->seed;
}


static int32_t aa_roll(AASimState *state, int32_t span) {
    return (int32_t)(aa_next_random(state) % (uint32_t)span);
}


static int32_t text_equals(const char *left, const char *right) {
    if (left == right) {
        return 1;
    }
    if (!left || !right) {
        return 0;
    }
    while (*left && *right) {
        if (*left != *right) {
            return 0;
        }
        ++left;
        ++right;
    }
    return (*left == '\0') && (*right == '\0');
}


static int32_t scenario_in_escalation_family(const char *phase) {
    return text_equals(phase, "escalated") || text_equals(phase, "crisis entrenched");
}


static int32_t scenario_in_stability_family(const char *phase) {
    return text_equals(phase, "stabilized") || text_equals(phase, "managed");
}


static void tick_policy(AASimState *state);


static void clear_incidents(AASimState *state) {
    int32_t index;
    state->incident_count = 0;
    for (index = 0; index < AA_MAX_INCIDENTS; ++index) {
        state->incidents[index].label = 0;
        state->incidents[index].summary = 0;
        state->incidents[index].aggressor = AA_ARCH_RELAY_HOUSES;
        state->incidents[index].responder = AA_ARCH_RELAY_HOUSES;
        state->incidents[index].severity = 0;
    }
}


static void push_incident(
    AASimState *state,
    const char *label,
    const char *summary,
    AAFactionId aggressor,
    AAFactionId responder,
    int32_t severity
) {
    AAIncident *incident;
    if (state->incident_count >= AA_MAX_INCIDENTS) {
        return;
    }
    incident = &state->incidents[state->incident_count++];
    incident->label = label;
    incident->summary = summary;
    incident->aggressor = aggressor;
    incident->responder = responder;
    incident->severity = severity;
}


static void init_agendas(AASimState *state) {
    state->agendas[AA_ARCH_RELAY_HOUSES] = (AAFactionAgenda){
        "Grid Absolutism",
        "The relay houses demand census-anchored order in Relay Ward before private lineages rebuild their own sovereign grids.",
        AA_RELAY_WARD,
        AA_OPERATION_ARCHIVE_CENSUS,
        63,
        0
    };
    state->agendas[AA_PROTO_HOMO_EMBER_COURTS] = (AAFactionAgenda){
        "Ancestor Furnace",
        "The ember courts want the forest margin mapped and provisioned before ancestral law is dissolved into imported property logic.",
        AA_EMBER_FOREST_MARGIN,
        AA_OPERATION_PUBLIC_WORKS,
        58,
        0
    };
    state->agendas[AA_VELVET_PHARMACATE] = (AAFactionAgenda){
        "Mercy Powder Market",
        "The pharmacate insists that Velvet Arcade remain supplied through tolerated contraband rather than punitive morality.",
        AA_VELVET_ARCADE,
        AA_OPERATION_SMUGGLE_COMPACT,
        71,
        0
    };
    state->agendas[AA_CHOIRS_OF_OBLIVION] = (AAFactionAgenda){
        "Unburial Sermon",
        "The choirs seek processional authority in Ash Basilica so forgetting becomes governance instead of panic.",
        AA_ASH_BASILICA,
        AA_OPERATION_CONSECRATE_PROCESSION,
        75,
        0
    };
    state->agendas[AA_ANTLER_PRINCIPALITIES] = (AAFactionAgenda){
        "Shrine Perimeter",
        "The frontier princes demand militia hardening along the rail frontier before migration routes become colonial choke points.",
        AA_ANTLER_RAIL_FRONTIER,
        AA_OPERATION_MUSTER_COLUMN,
        66,
        0
    };
    state->agendas[AA_BRASS_MARIANISTS] = (AAFactionAgenda){
        "Confession Index",
        "The brass missionaries want every district converted into legible inventory, beginning with the forest margin.",
        AA_EMBER_FOREST_MARGIN,
        AA_OPERATION_ARCHIVE_CENSUS,
        61,
        0
    };
}


static void init_scenarios(AASimState *state) {
    state->scenarios[AA_RELAY_WARD] = (AADistrictScenario){
        "Shock Cathedral Brownout",
        "The capital's old electrical sanctuaries are failing in sequence, and every blackout invites a private sovereignty test.",
        "active",
        AA_OPERATION_PUBLIC_WORKS,
        52,
        0,
        0,
        0,
        AA_OPERATION_PUBLIC_WORKS,
        0,
        0
    };
    state->scenarios[AA_EMBER_FOREST_MARGIN] = (AADistrictScenario){
        "Ancestor Furnace Succession",
        "Proto-Homo clans and missionary record-keepers are fighting over who may define inheritance, labor dues, and burial iron.",
        "active",
        AA_OPERATION_ARCHIVE_CENSUS,
        61,
        0,
        0,
        0,
        AA_OPERATION_ARCHIVE_CENSUS,
        0,
        0
    };
    state->scenarios[AA_VELVET_ARCADE] = (AADistrictScenario){
        "Mercy Powder Glut",
        "Medicine, aphrodisiacs, and contraband comfort are collapsing into a single mass market that now shapes civic obedience.",
        "active",
        AA_OPERATION_SMUGGLE_COMPACT,
        74,
        0,
        0,
        0,
        AA_OPERATION_SMUGGLE_COMPACT,
        0,
        0
    };
    state->scenarios[AA_ASH_BASILICA] = (AADistrictScenario){
        "Unburial Convocation",
        "Ritual authorities are reclassifying the dead as administrative assets, and every sermon redraws civil memory.",
        "active",
        AA_OPERATION_CONSECRATE_PROCESSION,
        79,
        0,
        0,
        0,
        AA_OPERATION_CONSECRATE_PROCESSION,
        0,
        0
    };
    state->scenarios[AA_ANTLER_RAIL_FRONTIER] = (AADistrictScenario){
        "Rail Shrine Migration",
        "Frontier bands are converting rail lines into moving shrines, turning logistics routes into contested devotional territory.",
        "active",
        AA_OPERATION_MUSTER_COLUMN,
        68,
        0,
        0,
        0,
        AA_OPERATION_MUSTER_COLUMN,
        0,
        0
    };
}


static void replace_scenario(
    AASimState *state,
    AADistrictId district_id,
    const char *phase,
    const char *title,
    const char *summary,
    AAOperationId stabilizing_operation,
    int32_t intensity,
    int32_t progress
) {
    AADistrictScenario *scenario = &state->scenarios[district_id];
    scenario->title = title;
    scenario->summary = summary;
    scenario->phase = phase;
    scenario->stabilizing_operation = stabilizing_operation;
    scenario->intensity = clamp_stat(intensity, 0, 100);
    scenario->progress = clamp_stat(progress, 0, 100);
    scenario->cycle += 1;
    scenario->generation += 1;
}


static void mutate_scenario_successor(AASimState *state, AADistrictId district_id, int32_t escalating) {
    AADistrict *district = &state->districts[district_id];
    switch (district_id) {
        case AA_RELAY_WARD:
            if (escalating) {
                replace_scenario(
                    state,
                    district_id,
                    "escalated",
                    "Private Grid Secession",
                    "Blackout blocs have stopped begging for current and are wiring private sanctuaries into armed micro-states.",
                    AA_OPERATION_RELAY_CRACKDOWN,
                    86,
                    12
                );
            } else {
                replace_scenario(
                    state,
                    district_id,
                    "stabilized",
                    "Managed Relay Truce",
                    "Civic engineers and guild electors have accepted a temporary maintenance compact, buying time without resolving sovereignty.",
                    AA_OPERATION_ARCHIVE_CENSUS,
                    34,
                    20
                );
            }
            break;
        case AA_EMBER_FOREST_MARGIN:
            if (escalating) {
                replace_scenario(
                    state,
                    district_id,
                    "escalated",
                    "Charcoal Tithe War",
                    "Clan furnaces and missionary ledgers now compete openly, turning burial iron and labor tribute into a running border war.",
                    AA_OPERATION_MUSTER_COLUMN,
                    84,
                    10
                );
            } else {
                replace_scenario(
                    state,
                    district_id,
                    "stabilized",
                    "Boundary Charter",
                    "Inheritance groves, chapel routes, and furnace quotas have been written into a temporary charter neither side fully trusts.",
                    AA_OPERATION_PUBLIC_WORKS,
                    32,
                    24
                );
            }
            break;
        case AA_VELVET_ARCADE:
            if (escalating) {
                replace_scenario(
                    state,
                    district_id,
                    "escalated",
                    "Clinic Protection Racket",
                    "Street clinics, pleasure houses, and medicine depots have fused into armed patronage chains that now tax every recovery ritual.",
                    AA_OPERATION_RELAY_CRACKDOWN,
                    89,
                    9
                );
            } else {
                replace_scenario(
                    state,
                    district_id,
                    "stabilized",
                    "Licensed Mercy Corridor",
                    "Supply routes remain morally compromised, but dosing, treatment, and escort lanes are at least legible enough to govern.",
                    AA_OPERATION_SMUGGLE_COMPACT,
                    36,
                    18
                );
            }
            break;
        case AA_ASH_BASILICA:
            if (escalating) {
                replace_scenario(
                    state,
                    district_id,
                    "escalated",
                    "Reliquary Audit Schism",
                    "The dead are being inventoried twice over, once as souls and once as assets, and rival liturgies now mobilize armed mourners.",
                    AA_OPERATION_ARCHIVE_CENSUS,
                    91,
                    8
                );
            } else {
                replace_scenario(
                    state,
                    district_id,
                    "stabilized",
                    "Civic Mourning Compact",
                    "Ritual leaders have conceded a narrower public rite, allowing grief to function as order without consuming the district whole.",
                    AA_OPERATION_CONSECRATE_PROCESSION,
                    33,
                    22
                );
            }
            break;
        case AA_ANTLER_RAIL_FRONTIER:
            if (escalating) {
                replace_scenario(
                    state,
                    district_id,
                    "escalated",
                    "Pilgrim Rail Ambushes",
                    "Moving shrines now travel with raiders, turning every supply convoy into a devotional skirmish and every station into a siege rumor.",
                    AA_OPERATION_MUSTER_COLUMN,
                    87,
                    11
                );
            } else {
                replace_scenario(
                    state,
                    district_id,
                    "stabilized",
                    "Escort Shrine Accord",
                    "Frontier escorts and shrine bands have reached a convoy-sharing pact that keeps trade alive while preserving armed ritual autonomy.",
                    AA_OPERATION_PUBLIC_WORKS,
                    35,
                    19
                );
            }
            break;
        default:
            replace_scenario(
                state,
                district_id,
                escalating ? "escalated" : "stabilized",
                district->name,
                "The district has entered a new unnamed scenario state.",
                escalating ? AA_OPERATION_MUSTER_COLUMN : AA_OPERATION_PUBLIC_WORKS,
                escalating ? 80 : 35,
                escalating ? 10 : 20
            );
            break;
    }

    push_incident(
        state,
        escalating ? "Scenario Mutation" : "Scenario Consolidation",
        state->scenarios[district_id].summary,
        district->controlling_faction,
        district->controlling_faction,
        escalating ? 7 : 4
    );
}


static void mutate_scenario_second_gen(AASimState *state, AADistrictId district_id, int32_t escalating) {
    AADistrict *district = &state->districts[district_id];
    switch (district_id) {
        case AA_RELAY_WARD:
            if (escalating) {
                replace_scenario(state, district_id, "terminal",
                    "Sovereign Grid Schism",
                    "Private micro-states have consolidated into armed electrical fiefdoms. The capital grid is now three rival networks, each with its own militia, liturgy, and toll schedule.",
                    AA_OPERATION_RELAY_CRACKDOWN, 95, 5);
            } else {
                replace_scenario(state, district_id, "settled",
                    "Relay Commons Charter",
                    "Guild electors and civic engineers have ratified a permanent maintenance compact. Power flows are predictable, if not generous, and sovereignty disputes have become administrative rather than armed.",
                    AA_OPERATION_PUBLIC_WORKS, 18, 65);
            }
            break;
        case AA_EMBER_FOREST_MARGIN:
            if (escalating) {
                replace_scenario(state, district_id, "terminal",
                    "Ancestral Iron Siege",
                    "Clan furnaces have barricaded the forest margin and declared burial-iron sovereignty. Missionary record-keepers are being expelled under threat of ritual execution.",
                    AA_OPERATION_MUSTER_COLUMN, 94, 4);
            } else {
                replace_scenario(state, district_id, "settled",
                    "Inheritance Grove Accord",
                    "Furnace clans and chapel archives have divided the margin into co-administered zones. Labor tribute flows predictably and burial rites proceed without armed contest.",
                    AA_OPERATION_ARCHIVE_CENSUS, 16, 68);
            }
            break;
        case AA_VELVET_ARCADE:
            if (escalating) {
                replace_scenario(state, district_id, "terminal",
                    "Pharmacate Sovereignty",
                    "The Velvet Arcade has declared itself an autonomous medical-pleasure state. Armed clinic-wardens enforce dosing schedules, and all commerce passes through narcotic patronage.",
                    AA_OPERATION_RELAY_CRACKDOWN, 96, 3);
            } else {
                replace_scenario(state, district_id, "settled",
                    "Regulated Mercy Market",
                    "Licensed clinics, taxed pleasure-houses, and inspected supply corridors have replaced the raw vice economy with something corrupt but governable.",
                    AA_OPERATION_SMUGGLE_COMPACT, 20, 62);
            }
            break;
        case AA_ASH_BASILICA:
            if (escalating) {
                replace_scenario(state, district_id, "terminal",
                    "Necropolitical Theocracy",
                    "The dead now outvote the living in district governance. Reliquary inventories have become census rolls, and mourning has become compulsory civic service.",
                    AA_OPERATION_ARCHIVE_CENSUS, 97, 2);
            } else {
                replace_scenario(state, district_id, "settled",
                    "Shared Mourning Calendar",
                    "Ritual authorities have accepted a civic mourning calendar that limits processional power while preserving public grief as a social adhesive.",
                    AA_OPERATION_CONSECRATE_PROCESSION, 15, 70);
            }
            break;
        case AA_ANTLER_RAIL_FRONTIER:
            if (escalating) {
                replace_scenario(state, district_id, "terminal",
                    "Rail Shrine Occupation",
                    "Frontier bands have seized permanent control of three major rail junctions. Every supply convoy is now a devotional tribute, and commerce moves only by shrine permission.",
                    AA_OPERATION_MUSTER_COLUMN, 93, 6);
            } else {
                replace_scenario(state, district_id, "settled",
                    "Convoy Covenant",
                    "Escort bands and trade caravans have formalized a permanent revenue-sharing covenant. Shrines travel freely but no longer blockade logistics.",
                    AA_OPERATION_PUBLIC_WORKS, 17, 66);
            }
            break;
        default:
            replace_scenario(state, district_id,
                escalating ? "terminal" : "settled",
                district->name,
                escalating ? "The district has entered a terminal crisis beyond conventional recovery."
                           : "The district has reached a durable settlement that may hold indefinitely.",
                escalating ? AA_OPERATION_MUSTER_COLUMN : AA_OPERATION_PUBLIC_WORKS,
                escalating ? 92 : 20,
                escalating ? 5 : 60);
            break;
    }

    push_incident(
        state,
        escalating ? "Second-Gen Crisis" : "Second-Gen Settlement",
        state->scenarios[district_id].summary,
        district->controlling_faction,
        district->controlling_faction,
        escalating ? 9 : 3
    );
}


static int32_t scenario_in_terminal_family(const char *phase) {
    return text_equals(phase, "terminal") || text_equals(phase, "settled");
}


static void evolve_scenarios(AASimState *state) {
    int32_t index;
    for (index = 0; index < AA_DISTRICT_COUNT; ++index) {
        AADistrictScenario *scenario = &state->scenarios[index];
        int32_t pressure = aa_district_pressure(state, (AADistrictId)index);
        int32_t escalating = (scenario->intensity >= 90) || (pressure >= 140 && scenario->intensity >= 82 && scenario->progress <= 28);
        int32_t stabilizing = (scenario->progress >= 72 && scenario->intensity <= 42);

        if (scenario_in_terminal_family(scenario->phase)) {
            continue;
        }

        if (escalating && scenario_in_escalation_family(scenario->phase) && scenario->generation >= 1) {
            mutate_scenario_second_gen(state, (AADistrictId)index, 1);
            continue;
        }
        if (stabilizing && scenario_in_stability_family(scenario->phase) && scenario->generation >= 1) {
            mutate_scenario_second_gen(state, (AADistrictId)index, 0);
            continue;
        }

        if (escalating && !scenario_in_escalation_family(scenario->phase)) {
            mutate_scenario_successor(state, (AADistrictId)index, 1);
            continue;
        }
        if (stabilizing && !scenario_in_stability_family(scenario->phase)) {
            mutate_scenario_successor(state, (AADistrictId)index, 0);
            continue;
        }
        if (escalating) {
            scenario->phase = "crisis entrenched";
            continue;
        }
        if (stabilizing) {
            scenario->phase = "managed";
            continue;
        }
        if (pressure >= 110 && scenario->progress >= 56 && scenario->intensity >= 70) {
            scenario->phase = "contested";
        } else if (scenario->progress >= 48 && scenario->intensity <= 55) {
            scenario->phase = "recovering";
        } else {
            scenario->phase = "active";
        }
    }
}


static void apply_agenda_response(AASimState *state, AAOperationId operation, AADistrictId district_id) {
    int32_t index;
    for (index = 0; index < AA_FACTION_COUNT; ++index) {
        AAFactionAgenda *agenda = &state->agendas[index];
        AAFaction *faction = &state->factions[index];
        if (agenda->target_district != district_id) {
            continue;
        }
        if (agenda->desired_operation == operation) {
            agenda->momentum = clamp_stat(agenda->momentum + 14, 0, 100);
            agenda->urgency = clamp_stat(agenda->urgency - 11, 0, 100);
            faction->legitimacy = clamp_stat(faction->legitimacy + 3, 0, 100);
            if (index == state->districts[district_id].controlling_faction) {
                state->districts[district_id].unrest = clamp_stat(state->districts[district_id].unrest - 3, 0, 100);
            }
        } else {
            agenda->momentum = clamp_stat(agenda->momentum - 4, 0, 100);
            agenda->urgency = clamp_stat(agenda->urgency + 6, 0, 100);
            faction->legitimacy = clamp_stat(faction->legitimacy - 1, 0, 100);
            if (agenda->urgency > 84) {
                state->districts[district_id].unrest = clamp_stat(state->districts[district_id].unrest + 2, 0, 100);
            }
        }
    }
}


static void apply_scenario_response(AASimState *state, AAOperationId operation, AADistrictId district_id) {
    AADistrictScenario *scenario;
    AADistrict *district;
    if (district_id < 0 || district_id >= AA_DISTRICT_COUNT) {
        return;
    }
    scenario = &state->scenarios[district_id];
    district = &state->districts[district_id];
    if (operation == scenario->stabilizing_operation) {
        scenario->intensity = clamp_stat(scenario->intensity - 16, 0, 100);
        scenario->progress = clamp_stat(scenario->progress + 18, 0, 100);
        district->unrest = clamp_stat(district->unrest - 4, 0, 100);
        district->supply = clamp_stat(district->supply + 3, 0, 100);
    } else {
        scenario->intensity = clamp_stat(scenario->intensity + 5, 0, 100);
        scenario->progress = clamp_stat(scenario->progress - 3, 0, 100);
    }
}


static void apply_recommendation_history(AASimState *state, AAOperationId operation, AADistrictId district_id) {
    AADistrictScenario *scenario;
    AADistrict *district;
    AAOperationId recommended;

    if (district_id < 0 || district_id >= AA_DISTRICT_COUNT) {
        return;
    }

    scenario = &state->scenarios[district_id];
    district = &state->districts[district_id];
    recommended = aa_recommend_operation(state, district_id);

    if (operation == recommended) {
        scenario->recommendation_streak = clamp_stat(scenario->recommendation_streak + 1, 0, 12);
        scenario->ignored_recommendation_streak = 0;
        scenario->progress = clamp_stat(scenario->progress + 3 + (scenario->recommendation_streak * 3), 0, 100);
        scenario->intensity = clamp_stat(scenario->intensity - (2 + (scenario->recommendation_streak * 2)), 0, 100);
        district->unrest = clamp_stat(district->unrest - scenario->recommendation_streak, 0, 100);

        if (scenario->recommendation_streak >= 2) {
            push_incident(
                state,
                "Recommendation Chain",
                "Repeated compliance with district recommendations is starting to produce durable administrative gains instead of one-week relief.",
                district->controlling_faction,
                district->controlling_faction,
                2 + scenario->recommendation_streak
            );
        }
    } else {
        scenario->ignored_recommendation_streak = clamp_stat(scenario->ignored_recommendation_streak + 1, 0, 12);
        scenario->recommendation_streak = 0;
        scenario->intensity = clamp_stat(scenario->intensity + 4 + (scenario->ignored_recommendation_streak * 3), 0, 100);
        scenario->progress = clamp_stat(scenario->progress - (2 + scenario->ignored_recommendation_streak), 0, 100);
        district->unrest = clamp_stat(district->unrest + (2 * scenario->ignored_recommendation_streak), 0, 100);
        district->supply = clamp_stat(district->supply - scenario->ignored_recommendation_streak, 0, 100);

        if (scenario->ignored_recommendation_streak >= 2) {
            push_incident(
                state,
                "Ignored Recommendation",
                "Repeatedly overriding district recommendations is compounding local pressure and forcing the scenario into a harsher medium-term state.",
                district->controlling_faction,
                district->controlling_faction,
                3 + scenario->ignored_recommendation_streak
            );
        }
    }

    scenario->last_directive = operation;
}


static void update_agendas(AASimState *state) {
    int32_t index;
    for (index = 0; index < AA_FACTION_COUNT; ++index) {
        AAFactionAgenda *agenda = &state->agendas[index];
        AAFaction *faction = &state->factions[index];
        AADistrict *district = &state->districts[agenda->target_district];
        agenda->urgency = clamp_stat(
            agenda->urgency +
            (district->unrest / 18) +
            (district->vice / 33) +
            ((100 - faction->legitimacy) / 20) -
            (agenda->momentum / 28),
            0,
            100
        );
        agenda->momentum = clamp_stat(agenda->momentum - 1, 0, 100);
        if (agenda->urgency >= 88) {
            push_incident(
                state,
                "Agenda Crisis",
                agenda->demand,
                (AAFactionId)index,
                district->controlling_faction,
                6 + (agenda->urgency / 20)
            );
            district->unrest = clamp_stat(district->unrest + 3, 0, 100);
        }
    }
}


static void update_scenarios(AASimState *state) {
    int32_t index;
    for (index = 0; index < AA_DISTRICT_COUNT; ++index) {
        AADistrictScenario *scenario = &state->scenarios[index];
        AADistrict *district = &state->districts[index];
        int32_t pressure = aa_district_pressure(state, (AADistrictId)index);
        scenario->intensity = clamp_stat(
            scenario->intensity +
            (pressure / 22) -
            (scenario->progress / 25) - 2,
            0,
            100
        );
        scenario->progress = clamp_stat(scenario->progress - 1, 0, 100);
        if (scenario->intensity >= 82) {
            push_incident(
                state,
                "Scenario Flashpoint",
                scenario->summary,
                district->controlling_faction,
                district->controlling_faction,
                scenario->intensity / 12
            );
            district->unrest = clamp_stat(district->unrest + 2, 0, 100);
        }
    }
}


const char *aa_operation_name(AAOperationId operation) {
    switch (operation) {
        case AA_OPERATION_PUBLIC_WORKS:
            return "Public Works";
        case AA_OPERATION_RELAY_CRACKDOWN:
            return "Relay Crackdown";
        case AA_OPERATION_CONSECRATE_PROCESSION:
            return "Consecrate Procession";
        case AA_OPERATION_SMUGGLE_COMPACT:
            return "Smuggle Compact";
        case AA_OPERATION_MUSTER_COLUMN:
            return "Muster Column";
        case AA_OPERATION_ARCHIVE_CENSUS:
            return "Archive Census";
        default:
            return "Unknown Operation";
    }
}


int32_t aa_district_pressure(const AASimState *state, AADistrictId district_id) {
    const AADistrict *district;
    const AAFaction *controller;
    int32_t pressure;
    if (district_id < 0 || district_id >= AA_DISTRICT_COUNT) {
        return 0;
    }
    district = &state->districts[district_id];
    controller = &state->factions[district->controlling_faction];
    pressure = (district->unrest * 2) + district->vice + district->worship - district->supply - (district->labor / 2);
    pressure += (100 - controller->legitimacy) / 2;
    pressure += (100 - controller->industry) / 3;
    if (district->unrest > 74) {
        pressure += 12;
    }
    if (district->supply < 36) {
        pressure += 10;
    }
    return clamp_stat(pressure, 0, 300);
}


const char *aa_district_condition(const AASimState *state, AADistrictId district_id) {
    int32_t pressure = aa_district_pressure(state, district_id);
    if (pressure >= 160) {
        return "collapse brink";
    }
    if (pressure >= 120) {
        return "insurrection risk";
    }
    if (pressure >= 85) {
        return "combustible";
    }
    if (pressure >= 55) {
        return "strained";
    }
    return "holding";
}


AAOperationId aa_recommend_operation(const AASimState *state, AADistrictId district_id) {
    const AADistrict *district;
    if (district_id < 0 || district_id >= AA_DISTRICT_COUNT) {
        return AA_OPERATION_PUBLIC_WORKS;
    }
    district = &state->districts[district_id];
    if (district->supply < 34 || district->labor < 36) {
        return AA_OPERATION_PUBLIC_WORKS;
    }
    if (district->unrest > 78 && district->vice < 58) {
        return AA_OPERATION_RELAY_CRACKDOWN;
    }
    if (district->worship > 78 && district->unrest > 52) {
        return AA_OPERATION_CONSECRATE_PROCESSION;
    }
    if (district->vice > 76 && district->supply < 62) {
        return AA_OPERATION_SMUGGLE_COMPACT;
    }
    if (district->controlling_faction == AA_ANTLER_PRINCIPALITIES || district->unrest > 66) {
        return AA_OPERATION_MUSTER_COLUMN;
    }
    return AA_OPERATION_ARCHIVE_CENSUS;
}


int32_t aa_campaign_stability(const AASimState *state) {
    int32_t index;
    int32_t total = 0;
    for (index = 0; index < AA_DISTRICT_COUNT; ++index) {
        const AADistrict *district = &state->districts[index];
        total += district->supply;
        total += district->labor;
        total += state->factions[district->controlling_faction].legitimacy;
        total -= district->unrest * 2;
        total -= (district->vice + district->worship) / 2;
    }
    total += state->treasury + state->fervor + state->intelligence;
    return total;
}


void aa_sim_begin_week(AASimState *state) {
    clear_incidents(state);
}


void aa_sim_init(AASimState *state, uint32_t seed) {
    state->seed = seed;
    state->week = 0;
    state->treasury = 54;
    state->fervor = 46;
    state->intelligence = 32;
    state->active_policy_id = AA_POLICY_NONE;
    state->active_policy = (AADirectorPolicy){"None", "No active policy.", 0, 0};
    state->mission_count = 0;
    clear_incidents(state);

    state->factions[AA_ARCH_RELAY_HOUSES] = (AAFaction){"Arch Relay Houses", 69, 45, 28, 82, 57};
    state->factions[AA_PROTO_HOMO_EMBER_COURTS] = (AAFaction){"Proto-Homo Ember Courts", 74, 66, 16, 39, 61};
    state->factions[AA_VELVET_PHARMACATE] = (AAFaction){"Velvet Pharmacate", 41, 37, 88, 55, 34};
    state->factions[AA_CHOIRS_OF_OBLIVION] = (AAFaction){"Choirs of Oblivion", 52, 91, 31, 26, 58};
    state->factions[AA_ANTLER_PRINCIPALITIES] = (AAFaction){"Antler Principalities", 78, 54, 42, 44, 49};
    state->factions[AA_BRASS_MARIANISTS] = (AAFaction){"Brass Marianists", 61, 79, 24, 72, 63};

    state->districts[0] = (AADistrict){"Relay Ward", 71, 28, 39, 34, 81, AA_ARCH_RELAY_HOUSES};
    state->districts[1] = (AADistrict){"Ember Forest Margin", 63, 36, 68, 22, 47, AA_PROTO_HOMO_EMBER_COURTS};
    state->districts[2] = (AADistrict){"Velvet Arcade", 54, 49, 27, 79, 58, AA_VELVET_PHARMACATE};
    state->districts[3] = (AADistrict){"Ash Basilica", 48, 34, 88, 18, 44, AA_CHOIRS_OF_OBLIVION};
    state->districts[4] = (AADistrict){"Antler Rail Frontier", 58, 41, 33, 29, 52, AA_ANTLER_PRINCIPALITIES};
    init_agendas(state);
    init_scenarios(state);

    state->protagonists[0] = (AAProtagonist){
        "Vael Ashborne", "Relay Auditor",
        "Infrastructure and grid politics",
        AA_RELAY_WARD, 42, 71,
        {65, 30, 20, 25, 15, 55}
    };
    state->protagonists[1] = (AAProtagonist){
        "Kez Thornmantle", "Frontier Warden",
        "Border patrol and shrine diplomacy",
        AA_ANTLER_RAIL_FRONTIER, 78, 38,
        {20, 55, 15, 30, 70, 25}
    };
    state->protagonists[2] = (AAProtagonist){
        "Sister Pyreth", "Choir Dissident",
        "Ritual subversion and memory politics",
        AA_ASH_BASILICA, 35, 62,
        {25, 40, 45, 72, 20, 50}
    };
}


void aa_sim_apply_operation(AASimState *state, AAOperationId operation, AADistrictId district_id) {
    AADistrict *district;
    AAFaction *controller;
    if (district_id < 0 || district_id >= AA_DISTRICT_COUNT) {
        return;
    }

    district = &state->districts[district_id];
    controller = &state->factions[district->controlling_faction];

    switch (operation) {
        case AA_OPERATION_PUBLIC_WORKS:
            state->treasury = clamp_stat(state->treasury - 6, 0, 100);
            district->labor = clamp_stat(district->labor + 8, 0, 100);
            district->supply = clamp_stat(district->supply + 10, 0, 100);
            district->unrest = clamp_stat(district->unrest - 6, 0, 100);
            controller->industry = clamp_stat(controller->industry + 4, 0, 100);
            push_incident(
                state,
                "Public Works",
                "Crews raise relay pylons, repair roads, and reopen civic supply lanes under armed supervision.",
                district->controlling_faction,
                district->controlling_faction,
                3
            );
            break;
        case AA_OPERATION_RELAY_CRACKDOWN:
            state->intelligence = clamp_stat(state->intelligence + 5, 0, 100);
            district->unrest = clamp_stat(district->unrest - 9, 0, 100);
            district->vice = clamp_stat(district->vice - 5, 0, 100);
            district->labor = clamp_stat(district->labor - 3, 0, 100);
            controller->force = clamp_stat(controller->force + 5, 0, 100);
            controller->legitimacy = clamp_stat(controller->legitimacy - 3, 0, 100);
            push_incident(
                state,
                "Crackdown",
                "Relay enforcers sweep alleys, seize stockpiles, and trade short-term order for long-term resentment.",
                AA_ARCH_RELAY_HOUSES,
                district->controlling_faction,
                5
            );
            break;
        case AA_OPERATION_CONSECRATE_PROCESSION:
            state->fervor = clamp_stat(state->fervor + 7, 0, 100);
            district->worship = clamp_stat(district->worship + 12, 0, 100);
            district->vice = clamp_stat(district->vice - 4, 0, 100);
            district->unrest = clamp_stat(district->unrest - 2, 0, 100);
            controller->doctrine = clamp_stat(controller->doctrine + 6, 0, 100);
            controller->legitimacy = clamp_stat(controller->legitimacy + 4, 0, 100);
            push_incident(
                state,
                "Procession",
                "A public rite redraws the district's mood and temporarily subordinates vice and fear to ceremony.",
                AA_CHOIRS_OF_OBLIVION,
                district->controlling_faction,
                4
            );
            break;
        case AA_OPERATION_SMUGGLE_COMPACT:
            state->treasury = clamp_stat(state->treasury + 8, 0, 100);
            state->intelligence = clamp_stat(state->intelligence + 2, 0, 100);
            district->vice = clamp_stat(district->vice + 11, 0, 100);
            district->supply = clamp_stat(district->supply + 7, 0, 100);
            district->unrest = clamp_stat(district->unrest - 3, 0, 100);
            controller->vice = clamp_stat(controller->vice + 5, 0, 100);
            controller->legitimacy = clamp_stat(controller->legitimacy - 4, 0, 100);
            push_incident(
                state,
                "Smuggle Compact",
                "Protected contraband and medicine routes calm shortages while quietly corrupting the civic center.",
                AA_VELVET_PHARMACATE,
                district->controlling_faction,
                4
            );
            break;
        case AA_OPERATION_MUSTER_COLUMN:
            state->treasury = clamp_stat(state->treasury - 4, 0, 100);
            district->supply = clamp_stat(district->supply - 5, 0, 100);
            district->unrest = clamp_stat(district->unrest + 5, 0, 100);
            controller->force = clamp_stat(controller->force + 8, 0, 100);
            controller->industry = clamp_stat(controller->industry - 2, 0, 100);
            push_incident(
                state,
                "Muster",
                "Militia columns are raised from workshops, shrines, and hunting bands to harden the district's perimeter.",
                district->controlling_faction,
                AA_ANTLER_PRINCIPALITIES,
                5
            );
            break;
        case AA_OPERATION_ARCHIVE_CENSUS:
            state->intelligence = clamp_stat(state->intelligence + 9, 0, 100);
            district->labor = clamp_stat(district->labor + 3, 0, 100);
            district->worship = clamp_stat(district->worship - 3, 0, 100);
            district->vice = clamp_stat(district->vice - 2, 0, 100);
            controller->legitimacy = clamp_stat(controller->legitimacy + 3, 0, 100);
            push_incident(
                state,
                "Census",
                "Archivists, confessors, and quartermasters map the district population to turn rumor into policy leverage.",
                AA_BRASS_MARIANISTS,
                district->controlling_faction,
                3
            );
            break;
        default:
            break;
    }

    if (district->vice > 82 && district->worship > 72) {
        push_incident(
            state,
            "Body Panic",
            "Desire, doctrine, and rumor collide into a moral panic that neither priests nor traffickers can fully direct.",
            AA_VELVET_PHARMACATE,
            AA_CHOIRS_OF_OBLIVION,
            7
        );
        district->unrest = clamp_stat(district->unrest + 7, 0, 100);
    }

    apply_agenda_response(state, operation, district_id);
    apply_scenario_response(state, operation, district_id);
    apply_recommendation_history(state, operation, district_id);
}


static void drift_factions(AASimState *state) {
    int32_t index;
    for (index = 0; index < AA_FACTION_COUNT; ++index) {
        AAFaction *faction = &state->factions[index];
        faction->force = clamp_stat(faction->force + aa_roll(state, 7) - 3, 0, 100);
        faction->doctrine = clamp_stat(faction->doctrine + aa_roll(state, 5) - 2, 0, 100);
        faction->vice = clamp_stat(faction->vice + aa_roll(state, 7) - 3, 0, 100);
        faction->industry = clamp_stat(faction->industry + aa_roll(state, 7) - 3, 0, 100);
        faction->legitimacy = clamp_stat(faction->legitimacy + aa_roll(state, 5) - 2, 0, 100);
    }
}


static void drift_districts(AASimState *state) {
    int32_t index;
    for (index = 0; index < AA_DISTRICT_COUNT; ++index) {
        AADistrict *district = &state->districts[index];
        AAFaction *controller = &state->factions[district->controlling_faction];
        district->labor = clamp_stat(district->labor + (controller->industry / 20) - 2 + aa_roll(state, 5), 0, 100);
        district->worship = clamp_stat(district->worship + (controller->doctrine / 24) - 2 + aa_roll(state, 5), 0, 100);
        district->vice = clamp_stat(district->vice + (controller->vice / 22) - 1 + aa_roll(state, 5), 0, 100);
        district->supply = clamp_stat(district->supply + (controller->industry / 18) - 3 + aa_roll(state, 7), 0, 100);
        district->unrest = clamp_stat(
            district->unrest +
            ((district->vice + district->worship) / 40) -
            (district->supply / 28) +
            aa_roll(state, 7) - 2,
            0,
            100
        );
    }
}


static void resolve_control_shifts(AASimState *state) {
    int32_t index;
    for (index = 0; index < AA_DISTRICT_COUNT; ++index) {
        AADistrict *district = &state->districts[index];
        int32_t challenger_index;
        int32_t best_score = -9999;
        AAFactionId best_faction = district->controlling_faction;
        for (challenger_index = 0; challenger_index < AA_FACTION_COUNT; ++challenger_index) {
            AAFaction *candidate = &state->factions[challenger_index];
            int32_t score = candidate->force + candidate->legitimacy + aa_roll(state, 12) - district->unrest;
            if (score > best_score) {
                best_score = score;
                best_faction = (AAFactionId)challenger_index;
            }
        }
        if (best_faction != district->controlling_faction && district->unrest > 48) {
            push_incident(
                state,
                "Control Shift",
                "A district's civic balance breaks and a new faction seizes the local order.",
                best_faction,
                district->controlling_faction,
                district->unrest / 10
            );
            district->controlling_faction = best_faction;
            district->unrest = clamp_stat(district->unrest - 18, 0, 100);
        }
    }
}


static void generate_weekly_incidents(AASimState *state) {
    int32_t district_index;
    for (district_index = 0; district_index < AA_DISTRICT_COUNT; ++district_index) {
        AADistrict *district = &state->districts[district_index];
        if (district->vice > 74) {
            push_incident(
                state,
                "Vice Surge",
                "A narcotic and pleasure-market wave destabilizes ordinary trade and inflames faction opportunism.",
                AA_VELVET_PHARMACATE,
                district->controlling_faction,
                district->vice / 11
            );
        }
        if (district->worship > 78) {
            push_incident(
                state,
                "Doctrine March",
                "A worship bloc pushes public ritual authority into street-level governance.",
                AA_CHOIRS_OF_OBLIVION,
                district->controlling_faction,
                district->worship / 12
            );
        }
        if (district->unrest > 72) {
            push_incident(
                state,
                "Labor Rupture",
                "Workers, pilgrims, and militia cells fracture into open confrontation over supply and legitimacy.",
                district->controlling_faction,
                AA_ARCH_RELAY_HOUSES,
                district->unrest / 10
            );
        }
    }
}


void aa_sim_step(AASimState *state) {
    state->week += 1;
    drift_factions(state);
    drift_districts(state);
    update_agendas(state);
    update_scenarios(state);
    evolve_scenarios(state);
    tick_policy(state);
    generate_weekly_incidents(state);
    resolve_control_shifts(state);
}


void aa_sim_describe(const AASimState *state) {
    int32_t index;
    printf("ArchesAndAngels Simulation Week %d\n", state->week);
    printf("Director resources treasury=%d fervor=%d intelligence=%d\n", state->treasury, state->fervor, state->intelligence);
    printf("Campaign stability=%d\n", aa_campaign_stability(state));
    printf("Factions\n");
    for (index = 0; index < AA_FACTION_COUNT; ++index) {
        const AAFaction *faction = &state->factions[index];
        printf(
            "  %-24s force=%3d doctrine=%3d vice=%3d industry=%3d legitimacy=%3d\n",
            faction->name,
            faction->force,
            faction->doctrine,
            faction->vice,
            faction->industry,
            faction->legitimacy
        );
    }
    printf("Districts\n");
    for (index = 0; index < AA_DISTRICT_COUNT; ++index) {
        const AADistrict *district = &state->districts[index];
        printf(
            "  %-24s control=%-24s labor=%3d unrest=%3d worship=%3d vice=%3d supply=%3d pressure=%3d state=%s\n",
            district->name,
            state->factions[district->controlling_faction].name,
            district->labor,
            district->unrest,
            district->worship,
            district->vice,
            district->supply,
            aa_district_pressure(state, (AADistrictId)index),
            aa_district_condition(state, (AADistrictId)index)
        );
    }
    printf("Recommendations\n");
    for (index = 0; index < AA_DISTRICT_COUNT; ++index) {
        printf(
            "  %-24s -> %s\n",
            state->districts[index].name,
            aa_operation_name(aa_recommend_operation(state, (AADistrictId)index))
        );
    }
    printf("Scenario Cards\n");
    for (index = 0; index < AA_DISTRICT_COUNT; ++index) {
        const AADistrictScenario *scenario = &state->scenarios[index];
        printf(
            "  %-24s card=%s phase=%-10s gen=%d cycle=%2d intensity=%3d progress=%3d rec=%d ignore=%d focus=%s\n    %s\n",
            state->districts[index].name,
            scenario->title,
            scenario->phase,
            scenario->generation,
            scenario->cycle,
            scenario->intensity,
            scenario->progress,
            scenario->recommendation_streak,
            scenario->ignored_recommendation_streak,
            aa_operation_name(scenario->stabilizing_operation),
            scenario->summary
        );
    }
    printf("Faction Agendas\n");
    for (index = 0; index < AA_FACTION_COUNT; ++index) {
        const AAFactionAgenda *agenda = &state->agendas[index];
        printf(
            "  %-24s agenda=%s urgency=%3d momentum=%3d target=%s focus=%s\n    %s\n",
            state->factions[index].name,
            agenda->label,
            agenda->urgency,
            agenda->momentum,
            state->districts[agenda->target_district].name,
            aa_operation_name(agenda->desired_operation),
            agenda->demand
        );
    }
    printf("Incidents\n");
    if (state->incident_count == 0) {
        printf("  none\n");
    }
    for (index = 0; index < state->incident_count; ++index) {
        const AAIncident *incident = &state->incidents[index];
        printf(
            "  %-16s severity=%d aggressor=%s responder=%s\n    %s\n",
            incident->label,
            incident->severity,
            state->factions[incident->aggressor].name,
            state->factions[incident->responder].name,
            incident->summary
        );
    }
    if (state->active_policy_id != AA_POLICY_NONE) {
        printf("Active Policy\n");
        printf("  %s (weeks remaining: %d)\n", state->active_policy.name, state->active_policy.weeks_remaining);
        printf("    %s\n", state->active_policy.summary);
    }
}


const char *aa_policy_name(AADirectorPolicyId policy_id) {
    switch (policy_id) {
        case AA_POLICY_NONE:
            return "None";
        case AA_POLICY_UNIFICATION_DOCTRINE:
            return "Unification Doctrine";
        case AA_POLICY_FREE_COMMERCE:
            return "Free Commerce";
        case AA_POLICY_MARTIAL_CONSOLIDATION:
            return "Martial Consolidation";
        case AA_POLICY_TOLERANCE_EDICT:
            return "Tolerance Edict";
        case AA_POLICY_MEMORIA_INTERDICT:
            return "Memoria Interdict";
        default:
            return "Unknown Policy";
    }
}


void aa_sim_apply_policy(AASimState *state, AADirectorPolicyId policy_id) {
    int32_t index;

    if (policy_id == AA_POLICY_NONE) {
        return;
    }

    switch (policy_id) {
        case AA_POLICY_UNIFICATION_DOCTRINE:
            state->active_policy = (AADirectorPolicy){
                "Unification Doctrine",
                "All factions are ordered to subordinate local agendas to a single merged civic authority. Legitimacy rises, independence drops, urgency suppressed.",
                3, 3
            };
            for (index = 0; index < AA_FACTION_COUNT; ++index) {
                state->factions[index].legitimacy = clamp_stat(state->factions[index].legitimacy + 6, 0, 100);
                state->factions[index].force = clamp_stat(state->factions[index].force - 3, 0, 100);
                state->agendas[index].urgency = clamp_stat(state->agendas[index].urgency - 12, 0, 100);
                state->agendas[index].momentum = clamp_stat(state->agendas[index].momentum - 5, 0, 100);
            }
            state->fervor = clamp_stat(state->fervor - 8, 0, 100);
            state->intelligence = clamp_stat(state->intelligence + 4, 0, 100);
            break;

        case AA_POLICY_FREE_COMMERCE:
            state->active_policy = (AADirectorPolicy){
                "Free Commerce",
                "Trade restrictions are lifted across all districts. Supply and vice both surge while doctrine-driven factions lose moral leverage.",
                3, 3
            };
            for (index = 0; index < AA_DISTRICT_COUNT; ++index) {
                state->districts[index].supply = clamp_stat(state->districts[index].supply + 8, 0, 100);
                state->districts[index].vice = clamp_stat(state->districts[index].vice + 6, 0, 100);
                state->districts[index].unrest = clamp_stat(state->districts[index].unrest - 3, 0, 100);
            }
            state->treasury = clamp_stat(state->treasury + 12, 0, 100);
            state->factions[AA_VELVET_PHARMACATE].legitimacy = clamp_stat(state->factions[AA_VELVET_PHARMACATE].legitimacy + 8, 0, 100);
            state->factions[AA_CHOIRS_OF_OBLIVION].legitimacy = clamp_stat(state->factions[AA_CHOIRS_OF_OBLIVION].legitimacy - 6, 0, 100);
            state->agendas[AA_VELVET_PHARMACATE].momentum = clamp_stat(state->agendas[AA_VELVET_PHARMACATE].momentum + 15, 0, 100);
            break;

        case AA_POLICY_MARTIAL_CONSOLIDATION:
            state->active_policy = (AADirectorPolicy){
                "Martial Consolidation",
                "Military authority declared. Militia columns are authorized across all districts. Force rises, unrest spikes short-term, faction independence shrinks.",
                3, 3
            };
            for (index = 0; index < AA_FACTION_COUNT; ++index) {
                state->factions[index].force = clamp_stat(state->factions[index].force + 7, 0, 100);
                state->factions[index].legitimacy = clamp_stat(state->factions[index].legitimacy - 4, 0, 100);
                state->agendas[index].urgency = clamp_stat(state->agendas[index].urgency - 8, 0, 100);
            }
            for (index = 0; index < AA_DISTRICT_COUNT; ++index) {
                state->districts[index].unrest = clamp_stat(state->districts[index].unrest + 5, 0, 100);
            }
            state->treasury = clamp_stat(state->treasury - 10, 0, 100);
            state->factions[AA_ANTLER_PRINCIPALITIES].legitimacy = clamp_stat(state->factions[AA_ANTLER_PRINCIPALITIES].legitimacy + 8, 0, 100);
            break;

        case AA_POLICY_TOLERANCE_EDICT:
            state->active_policy = (AADirectorPolicy){
                "Tolerance Edict",
                "All doctrinal enforcement suspended. Worship pressures ease, vice tolerances widen, and faction religious agendas lose urgency.",
                3, 3
            };
            for (index = 0; index < AA_DISTRICT_COUNT; ++index) {
                state->districts[index].worship = clamp_stat(state->districts[index].worship - 10, 0, 100);
                state->districts[index].vice = clamp_stat(state->districts[index].vice + 4, 0, 100);
                state->districts[index].unrest = clamp_stat(state->districts[index].unrest - 4, 0, 100);
            }
            state->factions[AA_CHOIRS_OF_OBLIVION].doctrine = clamp_stat(state->factions[AA_CHOIRS_OF_OBLIVION].doctrine - 8, 0, 100);
            state->factions[AA_BRASS_MARIANISTS].doctrine = clamp_stat(state->factions[AA_BRASS_MARIANISTS].doctrine - 6, 0, 100);
            state->agendas[AA_CHOIRS_OF_OBLIVION].urgency = clamp_stat(state->agendas[AA_CHOIRS_OF_OBLIVION].urgency - 15, 0, 100);
            state->fervor = clamp_stat(state->fervor - 10, 0, 100);
            break;

        case AA_POLICY_MEMORIA_INTERDICT:
            state->active_policy = (AADirectorPolicy){
                "Memoria Interdict",
                "Historical records are frozen and all rewriting of civic memory is prohibited. Intelligence rises, Choir power drops, census factions gain leverage.",
                3, 3
            };
            state->intelligence = clamp_stat(state->intelligence + 12, 0, 100);
            state->factions[AA_CHOIRS_OF_OBLIVION].legitimacy = clamp_stat(state->factions[AA_CHOIRS_OF_OBLIVION].legitimacy - 10, 0, 100);
            state->factions[AA_CHOIRS_OF_OBLIVION].doctrine = clamp_stat(state->factions[AA_CHOIRS_OF_OBLIVION].doctrine - 12, 0, 100);
            state->factions[AA_BRASS_MARIANISTS].legitimacy = clamp_stat(state->factions[AA_BRASS_MARIANISTS].legitimacy + 8, 0, 100);
            state->agendas[AA_CHOIRS_OF_OBLIVION].urgency = clamp_stat(state->agendas[AA_CHOIRS_OF_OBLIVION].urgency + 10, 0, 100);
            state->agendas[AA_BRASS_MARIANISTS].momentum = clamp_stat(state->agendas[AA_BRASS_MARIANISTS].momentum + 12, 0, 100);
            for (index = 0; index < AA_DISTRICT_COUNT; ++index) {
                state->districts[index].worship = clamp_stat(state->districts[index].worship - 6, 0, 100);
            }
            break;

        default:
            return;
    }

    state->active_policy_id = policy_id;
    push_incident(
        state,
        "Policy Declared",
        state->active_policy.summary,
        AA_ARCH_RELAY_HOUSES,
        AA_ARCH_RELAY_HOUSES,
        5
    );
}


static void tick_policy(AASimState *state) {
    if (state->active_policy_id == AA_POLICY_NONE) {
        return;
    }
    state->active_policy.weeks_remaining -= 1;
    if (state->active_policy.weeks_remaining <= 0) {
        push_incident(
            state,
            "Policy Expired",
            state->active_policy.summary,
            AA_ARCH_RELAY_HOUSES,
            AA_ARCH_RELAY_HOUSES,
            3
        );
        state->active_policy_id = AA_POLICY_NONE;
        state->active_policy = (AADirectorPolicy){"None", "No active policy.", 0, 0};
    }
}


void aa_generate_missions(AASimState *state) {
    int32_t district_index;
    state->mission_count = 0;
    for (district_index = 0; district_index < AA_DISTRICT_COUNT && state->mission_count < AA_MAX_MISSIONS; ++district_index) {
        int32_t pressure = aa_district_pressure(state, (AADistrictId)district_index);
        const AADistrictScenario *scenario = &state->scenarios[district_index];
        int32_t protagonist_index;
        int32_t best_protag = 0;
        int32_t best_affinity = -1;
        AAMission *mission;

        if (pressure < 75) {
            continue;
        }

        for (protagonist_index = 0; protagonist_index < AA_PROTAGONIST_COUNT; ++protagonist_index) {
            int32_t affinity = state->protagonists[protagonist_index].faction_trust[state->districts[district_index].controlling_faction];
            if (state->protagonists[protagonist_index].home_district == (AADistrictId)district_index) {
                affinity += 20;
            }
            if (affinity > best_affinity) {
                best_affinity = affinity;
                best_protag = protagonist_index;
            }
        }

        mission = &state->missions[state->mission_count];
        mission->target_district = (AADistrictId)district_index;
        mission->required_operation = scenario->stabilizing_operation;
        mission->protagonist_index = best_protag;
        mission->difficulty = pressure / 10 + scenario->intensity / 15;
        mission->active = 1;

        switch ((AADistrictId)district_index) {
            case AA_RELAY_WARD:
                mission->label = "Restore Grid Authority";
                mission->briefing = "Infiltrate the failing relay sanctuaries and restore central power distribution before private grids become permanent.";
                break;
            case AA_EMBER_FOREST_MARGIN:
                mission->label = "Map the Inheritance Groves";
                mission->briefing = "Navigate the contested forest margin and document clan furnace-routes before the border war closes all access.";
                break;
            case AA_VELVET_ARCADE:
                mission->label = "Negotiate Clinic Corridors";
                mission->briefing = "Broker safe passage through armed clinic-wardens and establish a licensed supply chain before the mercy market collapses.";
                break;
            case AA_ASH_BASILICA:
                mission->label = "Disrupt the Reliquary Audit";
                mission->briefing = "Enter the basilica archives and prevent the dual inventory of the dead from becoming a permanent governance mechanism.";
                break;
            case AA_ANTLER_RAIL_FRONTIER:
                mission->label = "Secure Junction Three";
                mission->briefing = "Rally frontier escorts and clear the third rail junction before shrine bands convert it into a permanent devotional blockade.";
                break;
            default:
                mission->label = "Field Operation";
                mission->briefing = "Conduct field operations in the contested district.";
                break;
        }
        state->mission_count += 1;
    }
}


void aa_describe_missions(const AASimState *state) {
    int32_t index;
    printf("Mission Board\n");
    if (state->mission_count == 0) {
        printf("  No districts at mission-critical pressure this week.\n");
        return;
    }
    for (index = 0; index < state->mission_count; ++index) {
        const AAMission *mission = &state->missions[index];
        const AAProtagonist *protag = &state->protagonists[mission->protagonist_index];
        printf("  Mission %d: %s\n", index + 1, mission->label);
        printf("    District: %s  Difficulty: %d\n", state->districts[mission->target_district].name, mission->difficulty);
        printf("    Required operation: %s\n", aa_operation_name(mission->required_operation));
        printf("    Assigned protagonist: %s (%s)\n", protag->name, protag->title);
        printf("    %s\n", mission->briefing);
    }
}


void aa_describe_protagonists(const AASimState *state) {
    int32_t index;
    printf("Protagonists\n");
    for (index = 0; index < AA_PROTAGONIST_COUNT; ++index) {
        const AAProtagonist *protag = &state->protagonists[index];
        printf("  %-20s title=%-20s home=%s combat=%d intel=%d\n",
            protag->name, protag->title,
            state->districts[protag->home_district].name,
            protag->combat_readiness, protag->intel_access);
        printf("    Affinity: %s  Trust profile: ARH=%d PH=%d VP=%d CO=%d AP=%d BM=%d\n",
            protag->district_affinity,
            protag->faction_trust[0], protag->faction_trust[1],
            protag->faction_trust[2], protag->faction_trust[3],
            protag->faction_trust[4], protag->faction_trust[5]);
    }
}