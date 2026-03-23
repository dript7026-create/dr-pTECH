#ifndef SYNTHVOICE_H
#define SYNTHVOICE_H

#include <stdint.h>
#include <stddef.h>

#define SYNTHVOICE_BANK_FILE L"synthvoice_bank.dat"
#define SYNTHVOICE_PERSONALITY_FILE L"synthvoice_personality.dat"
#define SYNTHVOICE_MAX_SCHEDULE_ITEMS 32

typedef enum AudioRole
{
    ROLE_KICK,
    ROLE_SNARE,
    ROLE_HAT,
    ROLE_BASS,
    ROLE_PAD,
    ROLE_LEAD,
    ROLE_FX,
    ROLE_ANY,
    ROLE_COUNT
} AudioRole;

typedef struct PromptStyle
{
    float energy;
    float density;
    float brightness;
    int minorMode;
    float swing;
    float mutationRate;
    float roleWeights[ROLE_COUNT];
} PromptStyle;

typedef struct SynthVoiceBank
{
    uint32_t version;
    uint32_t totalRuns;
    uint32_t learnedSampleCount;
    uint32_t successfulRenders;
    float avgTempo;
    float avgEnergy;
    float avgDensity;
    float avgBrightness;
    float avgSwing;
    float roleAffinity[ROLE_COUNT];
    float keyAffinity[12];
    float meterAffinity[12];
    float tagWeights[8];
    wchar_t lastPrompt[256];
} SynthVoiceBank;

typedef struct SynthVoiceScheduleItem
{
    int active;
    wchar_t title[96];
    wchar_t due[48];
    wchar_t tag[48];
    wchar_t note[160];
} SynthVoiceScheduleItem;

typedef struct SynthVoicePersonality
{
    uint32_t version;
    uint32_t chatCount;
    uint32_t notificationCount;
    wchar_t displayName[64];
    wchar_t communicationTone[64];
    wchar_t greeting[96];
    wchar_t lastUser[64];
    wchar_t lastSummary[256];
    float warmth;
    float directness;
    float initiative;
    SynthVoiceScheduleItem schedule[SYNTHVOICE_MAX_SCHEDULE_ITEMS];
} SynthVoicePersonality;

void synthvoice_bank_reset_defaults(SynthVoiceBank *bank);
void synthvoice_bank_load_in_module_dir(SynthVoiceBank *bank);
void synthvoice_bank_save_in_module_dir(const SynthVoiceBank *bank);
void synthvoice_personality_reset_defaults(SynthVoicePersonality *personality);
void synthvoice_personality_load_in_module_dir(SynthVoicePersonality *personality);
void synthvoice_personality_save_in_module_dir(const SynthVoicePersonality *personality);

void synthvoice_learn_from_roles(SynthVoiceBank *bank, const int *roleCounts, int roleCount);
void synthvoice_learn_tag(SynthVoiceBank *bank, const wchar_t *text, float amount);
void synthvoice_style_from_prompt(const SynthVoiceBank *bank, const wchar_t *prompt, PromptStyle *style);
void synthvoice_record_result(
    SynthVoiceBank *bank,
    const PromptStyle *style,
    int tempo,
    int totalFrames,
    int totalBars,
    int keyIndex,
    int meterIndex,
    const wchar_t *prompt);

void synthvoice_personality_note_generation(
    SynthVoicePersonality *personality,
    const SynthVoiceBank *bank,
    const wchar_t *prompt,
    const wchar_t *renderedPath);

int synthvoice_personality_add_schedule(
    SynthVoicePersonality *personality,
    const wchar_t *title,
    const wchar_t *due,
    const wchar_t *tag,
    const wchar_t *note);

void synthvoice_personality_chat(
    const SynthVoicePersonality *personality,
    const SynthVoiceBank *bank,
    const wchar_t *user,
    const wchar_t *message,
    wchar_t *buffer,
    size_t bufferCount);

void synthvoice_personality_format_summary_json(
    const SynthVoicePersonality *personality,
    const SynthVoiceBank *bank,
    wchar_t *buffer,
    size_t bufferCount);

void synthvoice_personality_format_diagnostics_json(
    const SynthVoicePersonality *personality,
    const SynthVoiceBank *bank,
    wchar_t *buffer,
    size_t bufferCount);

void synthvoice_personality_format_schedule_json(
    const SynthVoicePersonality *personality,
    wchar_t *buffer,
    size_t bufferCount);

void synthvoice_personality_format_notification(
    const SynthVoicePersonality *personality,
    const wchar_t *message,
    wchar_t *buffer,
    size_t bufferCount);

#endif