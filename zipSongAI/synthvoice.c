#define _CRT_SECURE_NO_WARNINGS
#define UNICODE
#define _UNICODE

#include "synthvoice.h"

#include <windows.h>
#include <shlwapi.h>
#include <stdio.h>
#include <string.h>
#include <wchar.h>

#pragma comment(lib, "shlwapi.lib")

static const wchar_t *g_synthvoice_tags[] = {
    L"rise", L"lift", L"break", L"steady", L"fade", L"dark", L"bright", L"ambient"
};

static float sv_clamp_float(float value, float minimum, float maximum);
static int sv_clamp_int(int value, int minimum, int maximum);
static void sv_get_module_path(wchar_t *buffer, size_t count, const wchar_t *fileName);

static float sv_clamp_float(float value, float minimum, float maximum)
{
    if (value < minimum)
    {
        return minimum;
    }
    if (value > maximum)
    {
        return maximum;
    }
    return value;
}

static int sv_clamp_int(int value, int minimum, int maximum)
{
    if (value < minimum)
    {
        return minimum;
    }
    if (value > maximum)
    {
        return maximum;
    }
    return value;
}

static void sv_get_module_path(wchar_t *buffer, size_t count, const wchar_t *fileName)
{
    wchar_t directory[MAX_PATH];
    GetModuleFileNameW(NULL, directory, MAX_PATH);
    PathRemoveFileSpecW(directory);
    swprintf(buffer, count, L"%ls\\%ls", directory, fileName);
}

void synthvoice_bank_reset_defaults(SynthVoiceBank *bank)
{
    int index;
    ZeroMemory(bank, sizeof(*bank));
    bank->version = 1;
    bank->avgTempo = 110.0f;
    bank->avgEnergy = 0.62f;
    bank->avgDensity = 0.55f;
    bank->avgBrightness = 0.54f;
    bank->avgSwing = 0.08f;
    for (index = 0; index < ROLE_COUNT; ++index)
    {
        bank->roleAffinity[index] = 1.0f;
    }
    for (index = 0; index < 12; ++index)
    {
        bank->keyAffinity[index] = 1.0f;
        bank->meterAffinity[index] = 1.0f;
    }
    for (index = 0; index < 8; ++index)
    {
        bank->tagWeights[index] = 1.0f;
    }
    wcscpy(bank->lastPrompt, L"untrained");
}

void synthvoice_bank_load_in_module_dir(SynthVoiceBank *bank)
{
    wchar_t path[MAX_PATH];
    FILE *file;
    synthvoice_bank_reset_defaults(bank);
    sv_get_module_path(path, MAX_PATH, SYNTHVOICE_BANK_FILE);
    file = _wfopen(path, L"rb");
    if (!file)
    {
        return;
    }
    if (fread(bank, sizeof(*bank), 1, file) != 1 || bank->version != 1)
    {
        synthvoice_bank_reset_defaults(bank);
    }
    fclose(file);
}

void synthvoice_bank_save_in_module_dir(const SynthVoiceBank *bank)
{
    wchar_t path[MAX_PATH];
    FILE *file;
    sv_get_module_path(path, MAX_PATH, SYNTHVOICE_BANK_FILE);
    file = _wfopen(path, L"wb");
    if (!file)
    {
        return;
    }
    fwrite(bank, sizeof(*bank), 1, file);
    fclose(file);
}

void synthvoice_personality_reset_defaults(SynthVoicePersonality *personality)
{
    ZeroMemory(personality, sizeof(*personality));
    personality->version = 1;
    wcscpy(personality->displayName, L"SynthVoice");
    wcscpy(personality->communicationTone, L"direct-adaptive");
    wcscpy(personality->greeting, L"SynthVoice is online and ready to coordinate generation workflows.");
    wcscpy(personality->lastUser, L"unknown");
    wcscpy(personality->lastSummary, L"No generations have been summarized yet.");
    personality->warmth = 0.58f;
    personality->directness = 0.82f;
    personality->initiative = 0.74f;
}

void synthvoice_personality_load_in_module_dir(SynthVoicePersonality *personality)
{
    wchar_t path[MAX_PATH];
    FILE *file;
    synthvoice_personality_reset_defaults(personality);
    sv_get_module_path(path, MAX_PATH, SYNTHVOICE_PERSONALITY_FILE);
    file = _wfopen(path, L"rb");
    if (!file)
    {
        return;
    }
    if (fread(personality, sizeof(*personality), 1, file) != 1 || personality->version != 1)
    {
        synthvoice_personality_reset_defaults(personality);
    }
    fclose(file);
}

void synthvoice_personality_save_in_module_dir(const SynthVoicePersonality *personality)
{
    wchar_t path[MAX_PATH];
    FILE *file;
    sv_get_module_path(path, MAX_PATH, SYNTHVOICE_PERSONALITY_FILE);
    file = _wfopen(path, L"wb");
    if (!file)
    {
        return;
    }
    fwrite(personality, sizeof(*personality), 1, file);
    fclose(file);
}

void synthvoice_learn_from_roles(SynthVoiceBank *bank, const int *roleCounts, int roleCount)
{
    int index;
    for (index = 0; index < roleCount && index < ROLE_COUNT; ++index)
    {
        bank->roleAffinity[index] += roleCounts[index] * 0.04f;
        bank->learnedSampleCount += (uint32_t)roleCounts[index];
    }
}

void synthvoice_learn_tag(SynthVoiceBank *bank, const wchar_t *text, float amount)
{
    int index;
    if (!text)
    {
        return;
    }
    for (index = 0; index < 8; ++index)
    {
        if (StrStrIW(text, g_synthvoice_tags[index]))
        {
            bank->tagWeights[index] += amount;
        }
    }
}

void synthvoice_style_from_prompt(const SynthVoiceBank *bank, const wchar_t *prompt, PromptStyle *style)
{
    int index;
    float tempoBias;
    ZeroMemory(style, sizeof(*style));
    style->energy = 0.65f;
    style->density = 0.55f;
    style->brightness = 0.55f;
    style->minorMode = 0;
    style->swing = 0.06f;
    style->mutationRate = 0.18f;
    for (index = 0; index < ROLE_COUNT; ++index)
    {
        style->roleWeights[index] = 1.0f;
    }

    if (StrStrIW(prompt, L"ambient") || StrStrIW(prompt, L"calm") || StrStrIW(prompt, L"dream"))
    {
        style->energy -= 0.2f;
        style->density -= 0.1f;
        style->brightness += 0.1f;
    }
    if (StrStrIW(prompt, L"aggressive") || StrStrIW(prompt, L"heavy") || StrStrIW(prompt, L"intense"))
    {
        style->energy += 0.25f;
        style->density += 0.2f;
    }
    if (StrStrIW(prompt, L"dark") || StrStrIW(prompt, L"moody") || StrStrIW(prompt, L"noir"))
    {
        style->minorMode = 1;
        style->brightness -= 0.2f;
    }
    if (StrStrIW(prompt, L"bright") || StrStrIW(prompt, L"uplifting") || StrStrIW(prompt, L"happy"))
    {
        style->brightness += 0.2f;
    }
    if (StrStrIW(prompt, L"minimal") || StrStrIW(prompt, L"sparse"))
    {
        style->density -= 0.2f;
    }
    if (StrStrIW(prompt, L"swing") || StrStrIW(prompt, L"groove"))
    {
        style->swing += 0.1f;
    }
    if (StrStrIW(prompt, L"cinematic") || StrStrIW(prompt, L"wide"))
    {
        style->roleWeights[ROLE_PAD] += 0.35f;
        style->roleWeights[ROLE_FX] += 0.25f;
    }
    if (StrStrIW(prompt, L"club") || StrStrIW(prompt, L"dance"))
    {
        style->roleWeights[ROLE_KICK] += 0.4f;
        style->roleWeights[ROLE_HAT] += 0.3f;
        style->roleWeights[ROLE_BASS] += 0.2f;
    }
    if (StrStrIW(prompt, L"melodic") || StrStrIW(prompt, L"anthemic"))
    {
        style->roleWeights[ROLE_LEAD] += 0.45f;
        style->roleWeights[ROLE_PAD] += 0.2f;
    }

    style->energy = sv_clamp_float(style->energy, 0.2f, 1.0f);
    style->density = sv_clamp_float(style->density, 0.2f, 1.0f);
    style->brightness = sv_clamp_float(style->brightness, 0.1f, 1.0f);
    style->swing = sv_clamp_float(style->swing, 0.0f, 0.35f);

    tempoBias = (bank->avgTempo - 110.0f) / 120.0f;
    style->energy = sv_clamp_float(style->energy * 0.78f + bank->avgEnergy * 0.22f + tempoBias * 0.15f, 0.15f, 1.0f);
    style->density = sv_clamp_float(style->density * 0.8f + bank->avgDensity * 0.2f, 0.15f, 1.0f);
    style->brightness = sv_clamp_float(style->brightness * 0.8f + bank->avgBrightness * 0.2f, 0.1f, 1.0f);
    style->swing = sv_clamp_float(style->swing * 0.6f + bank->avgSwing * 0.4f, 0.0f, 0.35f);
    style->mutationRate = sv_clamp_float(0.12f + (1.0f / (float)(bank->totalRuns + 2)), 0.08f, 0.4f);

    for (index = 0; index < ROLE_COUNT; ++index)
    {
        style->roleWeights[index] = sv_clamp_float(style->roleWeights[index] * (bank->roleAffinity[index] / (float)(bank->totalRuns + 1)), 0.4f, 2.6f);
    }

    if (StrStrIW(prompt, L"human") || StrStrIW(prompt, L"organic"))
    {
        style->swing = sv_clamp_float(style->swing + 0.08f, 0.0f, 0.35f);
    }
    if (StrStrIW(prompt, L"machine") || StrStrIW(prompt, L"precise"))
    {
        style->swing = sv_clamp_float(style->swing - 0.05f, 0.0f, 0.35f);
    }
}

void synthvoice_record_result(
    SynthVoiceBank *bank,
    const PromptStyle *style,
    int tempo,
    int totalFrames,
    int totalBars,
    int keyIndex,
    int meterIndex,
    const wchar_t *prompt)
{
    float runCount = (float)(bank->totalRuns + 1);
    bank->totalRuns += 1;
    bank->successfulRenders += 1;
    bank->avgTempo = ((bank->avgTempo * (runCount - 1.0f)) + tempo) / runCount;
    bank->avgEnergy = ((bank->avgEnergy * (runCount - 1.0f)) + style->energy) / runCount;
    bank->avgDensity = ((bank->avgDensity * (runCount - 1.0f)) + style->density) / runCount;
    bank->avgBrightness = ((bank->avgBrightness * (runCount - 1.0f)) + style->brightness) / runCount;
    bank->avgSwing = ((bank->avgSwing * (runCount - 1.0f)) + style->swing) / runCount;
    bank->keyAffinity[sv_clamp_int(keyIndex, 0, 11)] += 0.25f + totalBars * 0.002f;
    bank->meterAffinity[sv_clamp_int(meterIndex, 0, 11)] += 0.15f + totalFrames / 5292000.0f;
    synthvoice_learn_tag(bank, prompt, 0.08f);
    wcsncpy(bank->lastPrompt, prompt, 255);
    bank->lastPrompt[255] = 0;
}

void synthvoice_personality_note_generation(
    SynthVoicePersonality *personality,
    const SynthVoiceBank *bank,
    const wchar_t *prompt,
    const wchar_t *renderedPath)
{
    swprintf(personality->lastSummary,
             256,
             L"Prompt '%ls' rendered successfully. Runs=%u, learnedSamples=%u, output=%ls",
             prompt,
             bank->totalRuns,
             bank->learnedSampleCount,
             renderedPath);
}

int synthvoice_personality_add_schedule(
    SynthVoicePersonality *personality,
    const wchar_t *title,
    const wchar_t *due,
    const wchar_t *tag,
    const wchar_t *note)
{
    int index;
    for (index = 0; index < SYNTHVOICE_MAX_SCHEDULE_ITEMS; ++index)
    {
        if (!personality->schedule[index].active)
        {
            personality->schedule[index].active = 1;
            wcsncpy(personality->schedule[index].title, title ? title : L"Untitled", 95);
            wcsncpy(personality->schedule[index].due, due ? due : L"unscheduled", 47);
            wcsncpy(personality->schedule[index].tag, tag ? tag : L"general", 47);
            wcsncpy(personality->schedule[index].note, note ? note : L"", 159);
            personality->schedule[index].title[95] = 0;
            personality->schedule[index].due[47] = 0;
            personality->schedule[index].tag[47] = 0;
            personality->schedule[index].note[159] = 0;
            return 1;
        }
    }
    return 0;
}

void synthvoice_personality_chat(
    const SynthVoicePersonality *personality,
    const SynthVoiceBank *bank,
    const wchar_t *user,
    const wchar_t *message,
    wchar_t *buffer,
    size_t bufferCount)
{
    swprintf(buffer,
             bufferCount,
             L"%ls: user=%ls | tone=%ls | runs=%u | learnedSamples=%u | lastPrompt=%ls | response=I parsed '%ls' and would coordinate the next action through the SynthVoice API surface: chat, diagnostics, scheduling, notification, or generator handoff.",
             personality->displayName,
             user && user[0] ? user : personality->lastUser,
             personality->communicationTone,
             bank->totalRuns,
             bank->learnedSampleCount,
             bank->lastPrompt,
             message ? message : L"");
}

void synthvoice_personality_format_summary_json(
    const SynthVoicePersonality *personality,
    const SynthVoiceBank *bank,
    wchar_t *buffer,
    size_t bufferCount)
{
    swprintf(buffer,
             bufferCount,
             L"{\"service\":\"SynthVoice\",\"displayName\":\"%ls\",\"tone\":\"%ls\",\"runs\":%u,\"learnedSamples\":%u,\"lastPrompt\":\"%ls\",\"lastSummary\":\"%ls\"}",
             personality->displayName,
             personality->communicationTone,
             bank->totalRuns,
             bank->learnedSampleCount,
             bank->lastPrompt,
             personality->lastSummary);
}

void synthvoice_personality_format_diagnostics_json(
    const SynthVoicePersonality *personality,
    const SynthVoiceBank *bank,
    wchar_t *buffer,
    size_t bufferCount)
{
    swprintf(buffer,
             bufferCount,
             L"{\"service\":\"SynthVoice\",\"avgTempo\":%.2f,\"avgEnergy\":%.3f,\"avgDensity\":%.3f,\"avgBrightness\":%.3f,\"avgSwing\":%.3f,\"chatCount\":%u,\"notifications\":%u,\"initiative\":%.2f}",
             bank->avgTempo,
             bank->avgEnergy,
             bank->avgDensity,
             bank->avgBrightness,
             bank->avgSwing,
             personality->chatCount,
             personality->notificationCount,
             personality->initiative);
}

void synthvoice_personality_format_schedule_json(
    const SynthVoicePersonality *personality,
    wchar_t *buffer,
    size_t bufferCount)
{
    size_t used = 0;
    int index;
    used += swprintf(buffer + used, bufferCount - used, L"{\"schedule\":[");
    for (index = 0; index < SYNTHVOICE_MAX_SCHEDULE_ITEMS && used < bufferCount; ++index)
    {
        if (!personality->schedule[index].active)
        {
            continue;
        }
        used += swprintf(buffer + used,
                         bufferCount - used,
                         L"%ls{\"title\":\"%ls\",\"due\":\"%ls\",\"tag\":\"%ls\",\"note\":\"%ls\"}",
                         used > 14 ? L"," : L"",
                         personality->schedule[index].title,
                         personality->schedule[index].due,
                         personality->schedule[index].tag,
                         personality->schedule[index].note);
    }
    swprintf(buffer + used, bufferCount - used, L"]}");
}

void synthvoice_personality_format_notification(
    const SynthVoicePersonality *personality,
    const wchar_t *message,
    wchar_t *buffer,
    size_t bufferCount)
{
    swprintf(buffer,
             bufferCount,
             L"{\"notify\":\"%ls\",\"tone\":\"%ls\",\"message\":\"%ls\"}",
             personality->displayName,
             personality->communicationTone,
             message ? message : L"");
}