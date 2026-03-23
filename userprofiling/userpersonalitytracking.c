#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifndef GENOME_ENABLED
#define GENOME_ENABLED 0
#endif

#define MAX_USERS 1000
#define MAX_INTERACTIONS 10000
#define MAX_TEXT_LENGTH 500
#define PERSONALITY_TRAITS 5
#define FLASH_PROFILE_FEATURES 8
#define GENOME_LENGTH 16
#define GA_POPULATION 24
#define GA_GENERATIONS 20
#define MUTATION_RATE 0.15f

typedef enum {
    OPENNESS,
    CONSCIENTIOUSNESS,
    EXTRAVERSION,
    AGREEABLENESS,
    NEUROTICISM
} PersonalityTrait;

typedef struct {
    char trait_name[50];
    float score;
    int samples;
} TraitScore;

typedef struct {
    time_t timestamp;
    char interaction[MAX_TEXT_LENGTH];
    int response_time_ms;
    float sentiment_score;
} UserInteraction;

typedef struct {
    char user_id[100];
    TraitScore traits[PERSONALITY_TRAITS];
    UserInteraction *interactions;
    int interaction_count;
    float risk_score;
    float satisfaction_score;
    float genome_output;
    int has_genome;
    float best_genome[GENOME_LENGTH];
} UserProfile;

typedef struct {
    UserProfile *profiles;
    int profile_count;
} ProfileSystem;

static float clampf(float value, float min_value, float max_value) {
    if (value < min_value) return min_value;
    if (value > max_value) return max_value;
    return value;
}

static float frand_range(float min_value, float max_value) {
    float unit = (float)rand() / (float)RAND_MAX;
    return min_value + ((max_value - min_value) * unit);
}

static float sigmoidf(float value) {
    return 1.0f / (1.0f + expf(-value));
}

void update_trait_score(UserProfile *profile, PersonalityTrait trait, float adjustment) {
    if (!profile || trait < 0 || trait >= PERSONALITY_TRAITS) return;

    profile->traits[trait].score = clampf(profile->traits[trait].score + adjustment, 0.0f, 1.0f);
    profile->traits[trait].samples++;
}

float predict_future_activity(UserProfile *profile) {
    float avg_sentiment = 0.0f;

    if (!profile || profile->interaction_count == 0) return 0.5f;

    for (int i = 0; i < profile->interaction_count; i++) {
        avg_sentiment += profile->interactions[i].sentiment_score;
    }
    avg_sentiment /= (float)profile->interaction_count;

    return clampf(
        (profile->traits[OPENNESS].score * 0.20f) +
        (profile->traits[CONSCIENTIOUSNESS].score * 0.25f) +
        (profile->traits[EXTRAVERSION].score * 0.15f) +
        (avg_sentiment * 0.40f),
        0.0f,
        1.0f
    );
}

void calculate_risk_score(UserProfile *profile) {
    float risk = 0.0f;

    if (!profile) return;

    if (profile->traits[NEUROTICISM].score > 0.70f) risk += 0.30f;
    if (profile->traits[AGREEABLENESS].score < 0.35f) risk += 0.15f;
    if (profile->traits[CONSCIENTIOUSNESS].score < 0.30f) risk += 0.10f;

    if (profile->interaction_count > 0) {
        float avg_sentiment = 0.0f;
        float avg_response_ms = 0.0f;

        for (int i = 0; i < profile->interaction_count; i++) {
            avg_sentiment += profile->interactions[i].sentiment_score;
            avg_response_ms += (float)profile->interactions[i].response_time_ms;
        }

        avg_sentiment /= (float)profile->interaction_count;
        avg_response_ms /= (float)profile->interaction_count;

        if (avg_sentiment < 0.30f) risk += 0.30f;
        if (avg_sentiment > 0.70f) risk -= 0.15f;
        if (avg_response_ms > 1200.0f) risk += 0.10f;
    }

    profile->risk_score = clampf(risk, 0.0f, 1.0f);
}

ProfileSystem *init_profile_system(void) {
    ProfileSystem *system = (ProfileSystem *)malloc(sizeof(ProfileSystem));
    if (!system) return NULL;

    system->profiles = (UserProfile *)calloc(MAX_USERS, sizeof(UserProfile));
    if (!system->profiles) {
        free(system);
        return NULL;
    }

    system->profile_count = 0;
    return system;
}

UserProfile *create_user_profile(const char *user_id) {
    static const char *trait_names[PERSONALITY_TRAITS] = {
        "Openness",
        "Conscientiousness",
        "Extraversion",
        "Agreeableness",
        "Neuroticism"
    };

    UserProfile *profile = (UserProfile *)calloc(1, sizeof(UserProfile));
    if (!profile) return NULL;

    strncpy(profile->user_id, user_id ? user_id : "unknown", sizeof(profile->user_id) - 1);
    profile->interactions = (UserInteraction *)calloc(MAX_INTERACTIONS, sizeof(UserInteraction));
    if (!profile->interactions) {
        free(profile);
        return NULL;
    }

    profile->satisfaction_score = 1.0f;
    for (int i = 0; i < PERSONALITY_TRAITS; i++) {
        strncpy(profile->traits[i].trait_name, trait_names[i], sizeof(profile->traits[i].trait_name) - 1);
        profile->traits[i].score = 0.5f;
        profile->traits[i].samples = 0;
    }

    return profile;
}

void log_interaction(UserProfile *profile, const char *interaction, int response_time, float sentiment) {
    UserInteraction *entry;

    if (!profile || !profile->interactions || profile->interaction_count >= MAX_INTERACTIONS) return;

    entry = &profile->interactions[profile->interaction_count];
    entry->timestamp = time(NULL);
    strncpy(entry->interaction, interaction ? interaction : "", MAX_TEXT_LENGTH - 1);
    entry->response_time_ms = response_time;
    entry->sentiment_score = clampf(sentiment, -1.0f, 1.0f);
    profile->interaction_count++;

    update_trait_score(profile, EXTRAVERSION, entry->sentiment_score * 0.05f);
    update_trait_score(profile, AGREEABLENESS, entry->sentiment_score * 0.04f);
    update_trait_score(profile, CONSCIENTIOUSNESS, response_time < 800 ? 0.03f : -0.04f);
    update_trait_score(profile, NEUROTICISM, response_time > 1500 ? 0.05f : -0.02f);
    update_trait_score(profile, OPENNESS, strlen(entry->interaction) > 40 ? 0.02f : 0.0f);

    calculate_risk_score(profile);
}

static int compute_flash_profile(UserProfile *profile, int minutes, float *out_features, int max_features) {
    time_t now;
    time_t cutoff;
    int sample_count;
    float sentiment_sum = 0.0f;
    float response_sum = 0.0f;
    int recent_messages = 0;

    if (!profile || !out_features || max_features < FLASH_PROFILE_FEATURES) return 0;

    now = time(NULL);
    cutoff = now - ((minutes > 0 ? minutes : 30) * 60);

    for (int i = 0; i < profile->interaction_count; i++) {
        if (profile->interactions[i].timestamp >= cutoff) {
            sentiment_sum += profile->interactions[i].sentiment_score;
            response_sum += (float)profile->interactions[i].response_time_ms;
            recent_messages++;
        }
    }

    sample_count = recent_messages > 0 ? recent_messages : profile->interaction_count;
    if (sample_count <= 0) {
        sample_count = 1;
    }

    if (recent_messages == 0 && profile->interaction_count > 0) {
        for (int i = 0; i < profile->interaction_count; i++) {
            sentiment_sum += profile->interactions[i].sentiment_score;
            response_sum += (float)profile->interactions[i].response_time_ms;
        }
    }

    out_features[0] = profile->traits[OPENNESS].score;
    out_features[1] = profile->traits[CONSCIENTIOUSNESS].score;
    out_features[2] = profile->traits[EXTRAVERSION].score;
    out_features[3] = profile->traits[AGREEABLENESS].score;
    out_features[4] = profile->traits[NEUROTICISM].score;
    out_features[5] = clampf((sentiment_sum / (float)sample_count + 1.0f) * 0.5f, 0.0f, 1.0f);
    out_features[6] = clampf(1.0f - ((response_sum / (float)sample_count) / 2000.0f), 0.0f, 1.0f);
    out_features[7] = clampf((float)recent_messages / (float)(minutes > 0 ? minutes : 30), 0.0f, 1.0f);
    return FLASH_PROFILE_FEATURES;
}

#if GENOME_ENABLED
static float eval_genome_on_features(const float *genome, int genome_length, const float *features, int feature_count) {
    float total;
    int usable;

    total = genome_length > feature_count ? genome[genome_length - 1] : 0.0f;
    usable = feature_count < genome_length - 1 ? feature_count : genome_length - 1;

    for (int i = 0; i < usable; i++) {
        total += genome[i] * features[i];
    }

    return sigmoidf(total);
}

static float genome_fitness(const float *genome, UserProfile *profile, const float *features, int feature_count) {
    float output = eval_genome_on_features(genome, GENOME_LENGTH, features, feature_count);
    float target = clampf(profile->satisfaction_score, 0.0f, 1.0f);
    float alignment = 1.0f - fabsf(output - target);
    float stability = 1.0f - profile->risk_score;
    float activity = predict_future_activity(profile);
    return (alignment * 0.60f) + (stability * 0.25f) + (activity * 0.15f);
}

static void seed_genome(UserProfile *profile, float *genome) {
    for (int i = 0; i < GENOME_LENGTH; i++) {
        genome[i] = frand_range(-0.35f, 0.35f);
    }

    genome[0] = profile->traits[OPENNESS].score - 0.5f;
    genome[1] = profile->traits[CONSCIENTIOUSNESS].score - 0.5f;
    genome[2] = profile->traits[EXTRAVERSION].score - 0.5f;
    genome[3] = profile->traits[AGREEABLENESS].score - 0.5f;
    genome[4] = 0.5f - profile->traits[NEUROTICISM].score;
    genome[GENOME_LENGTH - 1] = (profile->satisfaction_score - 0.5f) * 0.5f;
}

static void mutate_genome(float *genome) {
    for (int i = 0; i < GENOME_LENGTH; i++) {
        if (frand_range(0.0f, 1.0f) < MUTATION_RATE) {
            genome[i] = clampf(genome[i] + frand_range(-0.15f, 0.15f), -1.0f, 1.0f);
        }
    }
}

static void crossover_genome(const float *left, const float *right, float *child) {
    for (int i = 0; i < GENOME_LENGTH; i++) {
        child[i] = frand_range(0.0f, 1.0f) < 0.5f ? left[i] : right[i];
    }
}

static void evolve_population(UserProfile *profile, const float *features, int feature_count, float *out_best_genome) {
    float population[GA_POPULATION][GENOME_LENGTH];
    float scores[GA_POPULATION];
    int best_index = 0;

    for (int i = 0; i < GA_POPULATION; i++) {
        seed_genome(profile, population[i]);
        mutate_genome(population[i]);
    }

    for (int generation = 0; generation < GA_GENERATIONS; generation++) {
        best_index = 0;
        for (int i = 0; i < GA_POPULATION; i++) {
            scores[i] = genome_fitness(population[i], profile, features, feature_count);
            if (scores[i] > scores[best_index]) {
                best_index = i;
            }
        }

        for (int i = 0; i < GA_POPULATION; i++) {
            if (i == best_index) continue;
            crossover_genome(population[best_index], population[(i + best_index + 1) % GA_POPULATION], population[i]);
            mutate_genome(population[i]);
        }
    }

    for (int i = 0; i < GENOME_LENGTH; i++) {
        out_best_genome[i] = population[best_index][i];
    }
}

void evolve_and_attach_genome(UserProfile *profile, int minutes) {
    float features[FLASH_PROFILE_FEATURES] = {0.0f};
    float best_genome[GENOME_LENGTH] = {0.0f};
    int feature_count;

    if (!profile) return;

    feature_count = compute_flash_profile(profile, minutes, features, FLASH_PROFILE_FEATURES);
    if (feature_count <= 0) return;

    evolve_population(profile, features, feature_count, best_genome);
    for (int i = 0; i < GENOME_LENGTH; i++) {
        profile->best_genome[i] = best_genome[i];
    }

    profile->has_genome = 1;
    profile->genome_output = eval_genome_on_features(profile->best_genome, GENOME_LENGTH, features, feature_count);
    profile->satisfaction_score = clampf((profile->satisfaction_score + profile->genome_output) * 0.5f, 0.0f, 1.0f);
    calculate_risk_score(profile);
}

float evaluate_profile_genome(UserProfile *profile) {
    float features[FLASH_PROFILE_FEATURES] = {0.0f};
    int feature_count;

    if (!profile || !profile->has_genome) return 0.0f;

    feature_count = compute_flash_profile(profile, 30, features, FLASH_PROFILE_FEATURES);
    if (feature_count <= 0) return 0.0f;

    profile->genome_output = eval_genome_on_features(profile->best_genome, GENOME_LENGTH, features, feature_count);
    return profile->genome_output;
}
#else
void evolve_and_attach_genome(UserProfile *profile, int minutes) {
    (void)profile;
    (void)minutes;
}

float evaluate_profile_genome(UserProfile *profile) {
    (void)profile;
    return 0.0f;
}
#endif

void print_profile_summary(UserProfile *profile) {
    if (!profile) return;

    printf("\n=== User Profile: %s ===\n", profile->user_id);
    printf("Interactions: %d\n", profile->interaction_count);
    for (int i = 0; i < PERSONALITY_TRAITS; i++) {
        printf("%s: %.2f\n", profile->traits[i].trait_name, profile->traits[i].score);
    }
    printf("Risk Score: %.2f\n", profile->risk_score);
    printf("Satisfaction Score: %.2f\n", profile->satisfaction_score);
    printf("Activity Prediction: %.2f\n", predict_future_activity(profile));
    if (profile->has_genome) {
        printf("Genome Output: %.2f\n", profile->genome_output);
    }
}

void cleanup_profile_system(ProfileSystem *system) {
    if (!system) return;

    for (int i = 0; i < system->profile_count; i++) {
        free(system->profiles[i].interactions);
        system->profiles[i].interactions = NULL;
    }

    free(system->profiles);
    free(system);
}
