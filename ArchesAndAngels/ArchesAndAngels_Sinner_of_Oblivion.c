/*
 * ArchesAndAngels: Sinner of Oblivion
 *
 * Date: 2026-03-13
 *
 * Windows-safe filename note:
 * The project title contains a colon in prose, but this source file uses
 * "ArchesAndAngels_Sinner_of_Oblivion.c" because ':' is not valid in a
 * Windows filename.
 *
 * This file is a saved concept stub for a future game project. It records the
 * design brief in code-facing form so the idea can be expanded into a runtime,
 * content pipeline, or NanoPlay_t and PlayHub adjacent derivatives later.
 */

#include <stdint.h>

#include "ArchesAndAngels_Sinner_of_Oblivion.h"

typedef struct {
    const char *title;
    const char *format;
    const char *camera;
    const char *genre_stack;
    const char *core_premise;
} AAProjectIdentity;

typedef struct {
    const char *era_cluster;
    const char *collision_event;
    const char *primary_conflict;
    const char *social_shock;
    const char *starting_condition;
} AATimeClash;

typedef struct {
    const char *civilization;
    const char *position;
    const char *signature;
} AAFaction;

typedef struct {
    const char *name;
    const char *mode;
    const char *purpose;
} AACompanionBuild;

static const AAProjectIdentity AA_IDENTITY = {
    "ArchesAndAngels: Sinner of Oblivion",
    "NanoPlay_t open-world top-down metroidvania graphical real-time action-rpg puzzle adventure twin-stick shooter tactical simulator civilization and spiritual worship economic reality simulator",
    "top-down exploration with dense interior combat and territory-scale simulation layers",
    "action-rpg + twin-stick combat + tactical sim + civilization management + spiritual economy sim",
    "An Edwardian/Victorian/Tesla-Edison industrial world and concurrent mainland Europe/North Asia social orders collide with a first pre-historic iron-age Proto-Homo tribal simian civilization already at war with multiple animal-hominid hybrid empires. The culture shock detonates into immediate techno-mystic, sexual, narcotic, economic, and religious upheaval, and the player enters at the instant the old moral frame breaks."
};

static const AATimeClash AA_COLLISION = {
    "Edwardian, Victorian, Tesla-Edison industrialism, mainland Europe, North Asia, and first iron-age Proto-Homo simian tribal civilization",
    "A time-clash tears layered city-states, steam grids, ritual forests, and iron-age simian empires into one unstable shared world map",
    "Every faction attempts to weaponize either memory, electricity, bloodline myth, narcotic trade, or spiritual legitimacy before the others stabilize the merged world",
    "Sexual and drug revolutions erupt immediately because taboos, medicines, rites, and technologies no longer agree about the body, desire, reproduction, or transcendence",
    "The game begins during the first civic week of the merger, when nobody yet controls the maps, the scripture, or the power grid"
};

static const AAFaction AA_FACTIONS[] = {
    {"The Arch Relay Houses", "post-Victorian power syndicate", "electrical infrastructure, pneumatic trade, shock-lit sanctuaries"},
    {"Proto-Homo Ember Courts", "simian iron-age confederacy", "charcoal metallurgy, ancestor law, beast-banner warfare"},
    {"The Velvet Pharmacate", "vice and medicine combine", "narcotic diplomacy, body modification, aphrodisiac cult logistics"},
    {"Choirs of Oblivion", "memory-negative spiritual order", "amnesia rites, anti-history evangelism, soul debt accounting"},
    {"The Antler Principalities", "animal-hominid frontier empire", "mounted migration warfare, fungal storage economies, shrine predation"},
    {"The Brass Marianists", "clockwork missionary machine state", "portable chapels, rail cannons, confession indexing"},
};

static const AACompanionBuild AA_SIDELINE_SKUS[] = {
    {"ArchesAndAngels_NanoPlay_t", "primary release", "full simulation breadth with twin-stick field combat and territorial spiritual economy"},
    {"DripDungeons_ArchesAndAngels", "PlayHub adjacent version", "compressed DripDungeons adaptation focused on dungeon delves, faction spillover, relic extraction, and roster-driven shrine wars"},
};

static const char *AA_CORE_SYSTEMS[] = {
    "Real-time twin-stick combat with melee, ballistic, improvised chemical, and ritual weapons",
    "Open-world top-down traversal with metroidvania route locks tied to technology, worship rites, and cultural literacy",
    "Settlement and trade simulation tracking vice, fertility, doctrine, fuel, iron, and spiritual legitimacy",
    "A civilization-scale diplomacy layer where species hybrid empires and simian clans can unify, fracture, interbreed, or declare holy trade monopolies",
    "Spiritual worship simulation where living gods, emergent saints, and machine-lit angels compete for ritual attention",
    "Tactical incident layer for raids, civic coups, narcotic panics, labor strikes, and animal-hominid frontier incursions",
    "Economic reality simulation linking commodity scarcity, addiction, desire, and doctrine to military strength and public order",
};

static const char *AA_STORY_PILLARS[] = {
    "Time-collision grief and opportunism",
    "Technological seduction versus ancestral belonging",
    "Immediate liberation and immediate exploitation",
    "Bodies as sites of politics, pleasure, industry, and worship",
    "Hybrid empires deciding whether memory is a burden, a weapon, or a sacrament",
};

int arches_and_angels_concept_checksum(void) {
    return (int)(sizeof(AA_FACTIONS) + sizeof(AA_CORE_SYSTEMS) + sizeof(AA_STORY_PILLARS) + sizeof(AA_SIDELINE_SKUS));
}


const char *arches_and_angels_project_title(void) {
    return AA_IDENTITY.title;
}


const char *arches_and_angels_project_format(void) {
    return AA_IDENTITY.format;
}


const char *arches_and_angels_project_core_premise(void) {
    return AA_IDENTITY.core_premise;
}


int32_t arches_and_angels_story_pillar_count(void) {
    return (int32_t)(sizeof(AA_STORY_PILLARS) / sizeof(AA_STORY_PILLARS[0]));
}


const char *arches_and_angels_story_pillar(int32_t index) {
    int32_t count = arches_and_angels_story_pillar_count();
    if (count <= 0) {
        return "";
    }
    if (index < 0) {
        index = -index;
    }
    return AA_STORY_PILLARS[index % count];
}


const char *arches_and_angels_faction_signature(int32_t index) {
    int32_t count = (int32_t)(sizeof(AA_FACTIONS) / sizeof(AA_FACTIONS[0]));
    if (count <= 0) {
        return "";
    }
    if (index < 0) {
        index = -index;
    }
    return AA_FACTIONS[index % count].signature;
}