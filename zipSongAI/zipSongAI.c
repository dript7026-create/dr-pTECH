#define _CRT_SECURE_NO_WARNINGS
#define UNICODE
#define _UNICODE

#include <windows.h>
#include <commctrl.h>
#include <commdlg.h>
#include <mmsystem.h>
#include <shellapi.h>
#include <shlwapi.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>
#include <math.h>
#include <time.h>

#include "synthvoice.h"

#pragma comment(lib, "comctl32.lib")
#pragma comment(lib, "comdlg32.lib")
#pragma comment(lib, "gdi32.lib")
#pragma comment(lib, "shell32.lib")
#pragma comment(lib, "shlwapi.lib")
#pragma comment(lib, "user32.lib")
#pragma comment(lib, "winmm.lib")

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#define APP_CLASS L"zipSongAIWindow"
#define PLAYER_CLASS L"zipSongAIPlayerWindow"
#define MAX_SAMPLES 512
#define MAX_SEGMENTS 64
#define OUTPUT_SAMPLE_RATE 44100
#define TIMELINE_TOP 470
#define TIMELINE_HEIGHT 220

enum
{
    IDC_ZIP_PATH = 1001,
    IDC_BROWSE_ZIP,
    IDC_PROMPT,
    IDC_TEMPO,
    IDC_TIMENUM,
    IDC_TIMEDEN,
    IDC_KEY,
    IDC_SEGMENT_LIST,
    IDC_SEGMENT_NAME,
    IDC_SEGMENT_TAG,
    IDC_SEGMENT_BARS,
    IDC_SEGMENT_TEMPO,
    IDC_SEGMENT_TIMENUM,
    IDC_SEGMENT_TIMEDEN,
    IDC_SEGMENT_KEY,
    IDC_SEGMENT_ADD,
    IDC_SEGMENT_REMOVE,
    IDC_SEGMENT_UP,
    IDC_SEGMENT_DOWN,
    IDC_SEGMENT_APPLY,
    IDC_GENERATE,
    IDC_STATUS,
    IDC_PLAY,
    IDC_STOP,
    IDC_SAVE
};

typedef struct Sample
{
    wchar_t path[MAX_PATH];
    wchar_t name[128];
    AudioRole role;
    int channels;
    int sampleRate;
    int frames;
    float *data;
} Sample;

typedef struct Segment
{
    wchar_t name[32];
    wchar_t tag[64];
    int bars;
    int tempo;
    int timeNum;
    int timeDen;
    int keyIndex;
    COLORREF color;
} Segment;

typedef struct Rng
{
    uint64_t state;
} Rng;

typedef struct AppState
{
    HWND hwndMain;
    HWND hwndPlayer;
    HWND editZip;
    HWND editPrompt;
    HWND editTempo;
    HWND editTimeNum;
    HWND editTimeDen;
    HWND comboKey;
    HWND listSegments;
    HWND editSegName;
    HWND editSegTag;
    HWND editSegBars;
    HWND editSegTempo;
    HWND editSegTimeNum;
    HWND editSegTimeDen;
    HWND comboSegKey;
    HWND status;
    HWND playerPathLabel;
    SynthVoiceBank synthVoice;
    SynthVoicePersonality personality;
    Sample samples[MAX_SAMPLES];
    int sampleCount;
    Segment segments[MAX_SEGMENTS];
    int segmentCount;
    int selectedSegment;
    wchar_t extractedDir[MAX_PATH];
    wchar_t renderedPath[MAX_PATH];
    wchar_t loadedZip[MAX_PATH];
    uint64_t generationCounter;
} AppState;

static const wchar_t *g_keys[] = {
    L"C", L"C#", L"D", L"Eb", L"E", L"F", L"F#", L"G", L"Ab", L"A", L"Bb", L"B"
};

static AppState g_app;

static void set_status(const wchar_t *text);
static int clamp_int(int value, int minimum, int maximum);
static float clamp_float(float value, float minimum, float maximum);
static int weighted_role_pick(Rng *rng, AudioRole primaryRole, AudioRole fallbackRole, const PromptStyle *style);
static uint32_t rng_next_u32(Rng *rng);
static float rng_next_float(Rng *rng);
static int rng_range(Rng *rng, int minimum, int maximum);
static COLORREF role_color(AudioRole role);
static AudioRole classify_role(const wchar_t *name);
static int read_int(HWND control, int fallback);
static void write_int(HWND control, int value);
static void free_samples(void);
static int load_wav_file(const wchar_t *path, Sample *sample);
static void scan_samples_recursive(const wchar_t *directory);
static int run_process_wait(const wchar_t *commandLine);
static int extract_zip_to_temp(const wchar_t *zipPath, wchar_t *outDirectory, size_t outDirectoryCount);
static PromptStyle analyze_prompt(const wchar_t *prompt);
static double midi_to_freq(int midi);
static void mix_float_sample(float *mix, int totalFrames, int outStart, const Sample *sample, float gain, float pan);
static void mix_sine_note(float *mix, int totalFrames, int startFrame, int durationFrames, double frequency, float gain, float pan, float brightness);
static void mix_noise_hit(float *mix, int totalFrames, int startFrame, int durationFrames, float gain, float pan, Rng *rng);
static void mix_kick(float *mix, int totalFrames, int startFrame, int durationFrames, float gain);
static int gather_role_indices(AudioRole role, int *indices, int maxIndices);
static Sample *pick_sample(Rng *rng, AudioRole primaryRole, AudioRole fallbackRole);
static int section_total_beats(const Segment *segment);
static void render_section(float *mix, int totalFrames, int sectionStartFrame, const Segment *segment, PromptStyle style, Rng *rng);
static int write_output_wav(const wchar_t *path, const float *mix, int frames);
static int prepare_samples_from_zip(const wchar_t *zipPath);
static int total_song_frames(void);
static int generate_song(void);
static void fill_key_combo(HWND combo);
static void init_default_segments(void);
static void refresh_segment_list(void);
static void load_selected_segment_fields(void);
static void apply_selected_segment_fields(void);
static void add_segment(void);
static void remove_segment(void);
static void move_segment(int delta);
static void browse_zip(void);
static void draw_timeline(HDC hdc);
static LRESULT CALLBACK player_wnd_proc(HWND hwnd, UINT message, WPARAM wParam, LPARAM lParam);
static void show_player_window(void);
static void sync_global_fields_to_selected(void);
static LRESULT CALLBACK main_wnd_proc(HWND hwnd, UINT message, WPARAM wParam, LPARAM lParam);

static void set_status(const wchar_t *text)
{
    if (g_app.status)
    {
        SetWindowTextW(g_app.status, text);
    }
}

static int clamp_int(int value, int minimum, int maximum)
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

static float clamp_float(float value, float minimum, float maximum)
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

static int weighted_role_pick(Rng *rng, AudioRole primaryRole, AudioRole fallbackRole, const PromptStyle *style)
{
    int indices[MAX_SAMPLES];
    float weights[MAX_SAMPLES];
    float totalWeight = 0.0f;
    float cursor;
    int count;
    int index;
    count = gather_role_indices(primaryRole, indices, MAX_SAMPLES);
    if (count == 0 && fallbackRole != primaryRole)
    {
        count = gather_role_indices(fallbackRole, indices, MAX_SAMPLES);
    }
    if (count == 0)
    {
        return -1;
    }

    for (index = 0; index < count; ++index)
    {
        AudioRole role = g_app.samples[indices[index]].role;
        weights[index] = style->roleWeights[role] * (0.65f + rng_next_float(rng) * (0.35f + style->mutationRate));
        totalWeight += weights[index];
    }

    cursor = rng_next_float(rng) * totalWeight;
    for (index = 0; index < count; ++index)
    {
        cursor -= weights[index];
        if (cursor <= 0.0f)
        {
            return indices[index];
        }
    }
    return indices[count - 1];
}

static uint32_t rng_next_u32(Rng *rng)
{
    uint64_t x = rng->state;
    x ^= x << 13;
    x ^= x >> 7;
    x ^= x << 17;
    rng->state = x;
    return (uint32_t)(x & 0xFFFFFFFFu);
}

static float rng_next_float(Rng *rng)
{
    return (float)(rng_next_u32(rng) / 4294967295.0);
}

static int rng_range(Rng *rng, int minimum, int maximum)
{
    if (maximum <= minimum)
    {
        return minimum;
    }
    return minimum + (int)(rng_next_u32(rng) % (uint32_t)(maximum - minimum + 1));
}

static COLORREF role_color(AudioRole role)
{
    switch (role)
    {
    case ROLE_KICK:
        return RGB(195, 62, 62);
    case ROLE_SNARE:
        return RGB(214, 130, 52);
    case ROLE_HAT:
        return RGB(220, 192, 72);
    case ROLE_BASS:
        return RGB(64, 139, 89);
    case ROLE_PAD:
        return RGB(80, 129, 176);
    case ROLE_LEAD:
        return RGB(125, 92, 182);
    case ROLE_FX:
        return RGB(74, 160, 165);
    default:
        return RGB(128, 128, 128);
    }
}

static AudioRole classify_role(const wchar_t *name)
{
    if (StrStrIW(name, L"kick") || StrStrIW(name, L"bd"))
    {
        return ROLE_KICK;
    }
    if (StrStrIW(name, L"snare") || StrStrIW(name, L"clap"))
    {
        return ROLE_SNARE;
    }
    if (StrStrIW(name, L"hat") || StrStrIW(name, L"cym") || StrStrIW(name, L"hh"))
    {
        return ROLE_HAT;
    }
    if (StrStrIW(name, L"bass") || StrStrIW(name, L"sub"))
    {
        return ROLE_BASS;
    }
    if (StrStrIW(name, L"pad") || StrStrIW(name, L"chord") || StrStrIW(name, L"ambient"))
    {
        return ROLE_PAD;
    }
    if (StrStrIW(name, L"lead") || StrStrIW(name, L"arp") || StrStrIW(name, L"melody") || StrStrIW(name, L"vocal"))
    {
        return ROLE_LEAD;
    }
    if (StrStrIW(name, L"fx") || StrStrIW(name, L"riser") || StrStrIW(name, L"impact") || StrStrIW(name, L"sweep"))
    {
        return ROLE_FX;
    }
    return ROLE_ANY;
}

static int read_int(HWND control, int fallback)
{
    wchar_t buffer[64];
    GetWindowTextW(control, buffer, 63);
    if (!buffer[0])
    {
        return fallback;
    }
    return _wtoi(buffer);
}

static void write_int(HWND control, int value)
{
    wchar_t buffer[32];
    swprintf(buffer, 32, L"%d", value);
    SetWindowTextW(control, buffer);
}

static void free_samples(void)
{
    int index;
    for (index = 0; index < g_app.sampleCount; ++index)
    {
        free(g_app.samples[index].data);
        g_app.samples[index].data = NULL;
    }
    g_app.sampleCount = 0;
}

static int load_wav_file(const wchar_t *path, Sample *sample)
{
    FILE *file = _wfopen(path, L"rb");
    uint32_t riffSize = 0;
    uint16_t audioFormat = 0;
    uint16_t channels = 0;
    uint32_t sampleRate = 0;
    uint16_t bitsPerSample = 0;
    uint8_t *rawData = NULL;
    uint32_t rawSize = 0;
    uint8_t chunkId[4];
    uint32_t chunkSize = 0;
    int frames = 0;
    int index;

    if (!file)
    {
        return 0;
    }

    if (fread(chunkId, 1, 4, file) != 4 || memcmp(chunkId, "RIFF", 4) != 0)
    {
        fclose(file);
        return 0;
    }
    fread(&riffSize, sizeof(uint32_t), 1, file);
    if (fread(chunkId, 1, 4, file) != 4 || memcmp(chunkId, "WAVE", 4) != 0)
    {
        fclose(file);
        return 0;
    }

    while (fread(chunkId, 1, 4, file) == 4 && fread(&chunkSize, sizeof(uint32_t), 1, file) == 1)
    {
        if (memcmp(chunkId, "fmt ", 4) == 0)
        {
            uint32_t bytesRead = 0;
            fread(&audioFormat, sizeof(uint16_t), 1, file);
            fread(&channels, sizeof(uint16_t), 1, file);
            fread(&sampleRate, sizeof(uint32_t), 1, file);
            fseek(file, 6, SEEK_CUR);
            fread(&bitsPerSample, sizeof(uint16_t), 1, file);
            bytesRead = 16;
            if (chunkSize > bytesRead)
            {
                fseek(file, chunkSize - bytesRead, SEEK_CUR);
            }
        }
        else if (memcmp(chunkId, "data", 4) == 0)
        {
            rawData = (uint8_t *)malloc(chunkSize);
            if (!rawData)
            {
                fclose(file);
                return 0;
            }
            if (fread(rawData, 1, chunkSize, file) != chunkSize)
            {
                free(rawData);
                fclose(file);
                return 0;
            }
            rawSize = chunkSize;
        }
        else
        {
            fseek(file, chunkSize, SEEK_CUR);
        }

        if (chunkSize & 1)
        {
            fseek(file, 1, SEEK_CUR);
        }
    }

    fclose(file);

    if (!rawData || audioFormat != 1 || (bitsPerSample != 8 && bitsPerSample != 16) || (channels != 1 && channels != 2) || sampleRate == 0)
    {
        free(rawData);
        return 0;
    }

    frames = (int)(rawSize / (channels * (bitsPerSample / 8)));
    sample->data = (float *)malloc(sizeof(float) * frames * 2);
    if (!sample->data)
    {
        free(rawData);
        return 0;
    }

    for (index = 0; index < frames; ++index)
    {
        float left;
        float right;
        if (bitsPerSample == 16)
        {
            int16_t *pcm = (int16_t *)rawData;
            if (channels == 1)
            {
                left = right = pcm[index] / 32768.0f;
            }
            else
            {
                left = pcm[index * 2] / 32768.0f;
                right = pcm[index * 2 + 1] / 32768.0f;
            }
        }
        else
        {
            uint8_t *pcm8 = rawData;
            if (channels == 1)
            {
                left = right = ((int)pcm8[index] - 128) / 128.0f;
            }
            else
            {
                left = ((int)pcm8[index * 2] - 128) / 128.0f;
                right = ((int)pcm8[index * 2 + 1] - 128) / 128.0f;
            }
        }
        sample->data[index * 2] = clamp_float(left, -1.0f, 1.0f);
        sample->data[index * 2 + 1] = clamp_float(right, -1.0f, 1.0f);
    }

    free(rawData);
    sample->channels = 2;
    sample->sampleRate = (int)sampleRate;
    sample->frames = frames;
    sample->role = classify_role(sample->name);
    return 1;
}

static void scan_samples_recursive(const wchar_t *directory)
{
    wchar_t pattern[MAX_PATH];
    WIN32_FIND_DATAW findData;
    HANDLE handle;

    swprintf(pattern, MAX_PATH, L"%ls\\*", directory);
    handle = FindFirstFileW(pattern, &findData);
    if (handle == INVALID_HANDLE_VALUE)
    {
        return;
    }

    do
    {
        if (wcscmp(findData.cFileName, L".") == 0 || wcscmp(findData.cFileName, L"..") == 0)
        {
            continue;
        }

        if (findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)
        {
            wchar_t child[MAX_PATH];
            swprintf(child, MAX_PATH, L"%ls\\%ls", directory, findData.cFileName);
            scan_samples_recursive(child);
        }
        else if (g_app.sampleCount < MAX_SAMPLES)
        {
            const wchar_t *ext = PathFindExtensionW(findData.cFileName);
            if (ext && (_wcsicmp(ext, L".wav") == 0 || _wcsicmp(ext, L".wave") == 0))
            {
                Sample *sample = &g_app.samples[g_app.sampleCount];
                ZeroMemory(sample, sizeof(*sample));
                swprintf(sample->path, MAX_PATH, L"%ls\\%ls", directory, findData.cFileName);
                wcsncpy(sample->name, findData.cFileName, 127);
                sample->name[127] = 0;
                if (load_wav_file(sample->path, sample))
                {
                    ++g_app.sampleCount;
                }
            }
        }
    } while (FindNextFileW(handle, &findData));

    FindClose(handle);
}

static int run_process_wait(const wchar_t *commandLine)
{
    STARTUPINFOW startupInfo;
    PROCESS_INFORMATION processInfo;
    wchar_t buffer[2048];
    DWORD exitCode = 1;

    ZeroMemory(&startupInfo, sizeof(startupInfo));
    ZeroMemory(&processInfo, sizeof(processInfo));
    startupInfo.cb = sizeof(startupInfo);
    wcsncpy(buffer, commandLine, 2047);
    buffer[2047] = 0;

    if (!CreateProcessW(NULL, buffer, NULL, NULL, FALSE, CREATE_NO_WINDOW, NULL, NULL, &startupInfo, &processInfo))
    {
        return 0;
    }

    WaitForSingleObject(processInfo.hProcess, INFINITE);
    GetExitCodeProcess(processInfo.hProcess, &exitCode);
    CloseHandle(processInfo.hThread);
    CloseHandle(processInfo.hProcess);
    return exitCode == 0;
}

static int extract_zip_to_temp(const wchar_t *zipPath, wchar_t *outDirectory, size_t outDirectoryCount)
{
    wchar_t tempRoot[MAX_PATH];
    wchar_t timestamp[128];
    FILETIME fileTime;
    ULARGE_INTEGER value;
    wchar_t command[2048];

    if (!GetTempPathW(MAX_PATH, tempRoot))
    {
        return 0;
    }

    GetSystemTimeAsFileTime(&fileTime);
    value.LowPart = fileTime.dwLowDateTime;
    value.HighPart = fileTime.dwHighDateTime;
    swprintf(timestamp, 128, L"zipSongAI_%llu", (unsigned long long)value.QuadPart);
    swprintf(outDirectory, outDirectoryCount, L"%ls%ls", tempRoot, timestamp);

    if (!CreateDirectoryW(outDirectory, NULL))
    {
        return 0;
    }

    swprintf(command, 2048,
             L"powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \"Expand-Archive -LiteralPath '%ls' -DestinationPath '%ls' -Force\"",
             zipPath, outDirectory);
    return run_process_wait(command);
}

static PromptStyle analyze_prompt(const wchar_t *prompt)
{
    PromptStyle style;
    synthvoice_style_from_prompt(&g_app.synthVoice, prompt, &style);
    return style;
}

static double midi_to_freq(int midi)
{
    return 440.0 * pow(2.0, (midi - 69) / 12.0);
}

static void mix_float_sample(float *mix, int totalFrames, int outStart, const Sample *sample, float gain, float pan)
{
    float leftGain = gain * (pan <= 0.0f ? 1.0f : 1.0f - pan);
    float rightGain = gain * (pan >= 0.0f ? 1.0f : 1.0f + pan);
    float ratio = sample->sampleRate / (float)OUTPUT_SAMPLE_RATE;
    float sourcePos = 0.0f;
    int outFrame = outStart;

    while (outFrame < totalFrames)
    {
        int baseIndex = (int)sourcePos;
        float frac;
        float left;
        float right;

        if (baseIndex >= sample->frames - 1)
        {
            break;
        }

        frac = sourcePos - baseIndex;
        left = sample->data[baseIndex * 2] * (1.0f - frac) + sample->data[(baseIndex + 1) * 2] * frac;
        right = sample->data[baseIndex * 2 + 1] * (1.0f - frac) + sample->data[(baseIndex + 1) * 2 + 1] * frac;
        mix[outFrame * 2] += left * leftGain;
        mix[outFrame * 2 + 1] += right * rightGain;
        sourcePos += ratio;
        ++outFrame;
    }
}

static void mix_sine_note(float *mix, int totalFrames, int startFrame, int durationFrames, double frequency, float gain, float pan, float brightness)
{
    int frame;
    float leftGain = gain * (pan <= 0.0f ? 1.0f : 1.0f - pan);
    float rightGain = gain * (pan >= 0.0f ? 1.0f : 1.0f + pan);
    float phase = 0.0f;
    float phaseStep = (float)(2.0 * M_PI * frequency / OUTPUT_SAMPLE_RATE);
    int endFrame = startFrame + durationFrames;
    if (endFrame > totalFrames)
    {
        endFrame = totalFrames;
    }

    for (frame = startFrame; frame < endFrame; ++frame)
    {
        float t = (frame - startFrame) / (float)(durationFrames > 0 ? durationFrames : 1);
        float attack = t < 0.08f ? (t / 0.08f) : 1.0f;
        float release = t > 0.8f ? (1.0f - t) / 0.2f : 1.0f;
        float envelope = clamp_float(attack, 0.0f, 1.0f) * clamp_float(release, 0.0f, 1.0f);
        float wave = sinf(phase) * 0.75f + sinf(phase * 2.0f) * (0.15f + brightness * 0.1f);
        mix[frame * 2] += wave * envelope * leftGain;
        mix[frame * 2 + 1] += wave * envelope * rightGain;
        phase += phaseStep;
    }
}

static void mix_noise_hit(float *mix, int totalFrames, int startFrame, int durationFrames, float gain, float pan, Rng *rng)
{
    int frame;
    float leftGain = gain * (pan <= 0.0f ? 1.0f : 1.0f - pan);
    float rightGain = gain * (pan >= 0.0f ? 1.0f : 1.0f + pan);
    int endFrame = startFrame + durationFrames;
    if (endFrame > totalFrames)
    {
        endFrame = totalFrames;
    }
    for (frame = startFrame; frame < endFrame; ++frame)
    {
        float t = (frame - startFrame) / (float)(durationFrames > 0 ? durationFrames : 1);
        float envelope = (1.0f - t) * (1.0f - t);
        float noise = rng_next_float(rng) * 2.0f - 1.0f;
        mix[frame * 2] += noise * envelope * leftGain;
        mix[frame * 2 + 1] += noise * envelope * rightGain;
    }
}

static void mix_kick(float *mix, int totalFrames, int startFrame, int durationFrames, float gain)
{
    int frame;
    float phase = 0.0f;
    int endFrame = startFrame + durationFrames;
    if (endFrame > totalFrames)
    {
        endFrame = totalFrames;
    }
    for (frame = startFrame; frame < endFrame; ++frame)
    {
        float t = (frame - startFrame) / (float)(durationFrames > 0 ? durationFrames : 1);
        float freq = 120.0f - 80.0f * t;
        float step = (float)(2.0 * M_PI * freq / OUTPUT_SAMPLE_RATE);
        float env = (1.0f - t) * (1.0f - t);
        float value = sinf(phase) * env * gain;
        mix[frame * 2] += value;
        mix[frame * 2 + 1] += value;
        phase += step;
    }
}

static int gather_role_indices(AudioRole role, int *indices, int maxIndices)
{
    int count = 0;
    int index;
    for (index = 0; index < g_app.sampleCount && count < maxIndices; ++index)
    {
        if (g_app.samples[index].role == role || (role == ROLE_ANY && g_app.samples[index].role == ROLE_ANY))
        {
            indices[count++] = index;
        }
    }
    return count;
}

static Sample *pick_sample(Rng *rng, AudioRole primaryRole, AudioRole fallbackRole)
{
    int indices[MAX_SAMPLES];
    int count = gather_role_indices(primaryRole, indices, MAX_SAMPLES);
    if (count == 0 && fallbackRole != primaryRole)
    {
        count = gather_role_indices(fallbackRole, indices, MAX_SAMPLES);
    }
    if (count == 0)
    {
        return NULL;
    }
    return &g_app.samples[indices[rng_range(rng, 0, count - 1)]];
}

static int section_total_beats(const Segment *segment)
{
    return segment->bars * segment->timeNum;
}

static void render_section(float *mix, int totalFrames, int sectionStartFrame, const Segment *segment, PromptStyle style, Rng *rng)
{
    int beat;
    double beatFrames = (60.0 / segment->tempo) * OUTPUT_SAMPLE_RATE * (4.0 / segment->timeDen);
    double barFrames = beatFrames * segment->timeNum;
    int totalBeats = section_total_beats(segment);
    int keyRoot = 48 + segment->keyIndex;
    int majorScale[7] = {0, 2, 4, 5, 7, 9, 11};
    int minorScale[7] = {0, 2, 3, 5, 7, 8, 10};
    int *scale = style.minorMode ? minorScale : majorScale;

    for (beat = 0; beat < totalBeats; ++beat)
    {
        int beatInBar = beat % segment->timeNum;
        float swingShift = (beatInBar % 2 == 1) ? style.swing * 0.5f : 0.0f;
        int frame = sectionStartFrame + (int)((beat + swingShift) * beatFrames);
        int eighthFrame = sectionStartFrame + (int)((beat + 0.5f + swingShift * 0.5f) * beatFrames);
        int kickIndex = weighted_role_pick(rng, ROLE_KICK, ROLE_ANY, &style);
        int snareIndex = weighted_role_pick(rng, ROLE_SNARE, ROLE_ANY, &style);
        int hatIndex = weighted_role_pick(rng, ROLE_HAT, ROLE_ANY, &style);
        Sample *kick = kickIndex >= 0 ? &g_app.samples[kickIndex] : NULL;
        Sample *snare = snareIndex >= 0 ? &g_app.samples[snareIndex] : NULL;
        Sample *hat = hatIndex >= 0 ? &g_app.samples[hatIndex] : NULL;

        if (beatInBar == 0 || (style.energy > 0.75f && beatInBar == segment->timeNum - 1 && rng_next_float(rng) > 0.4f))
        {
            if (kick && kick->role == ROLE_KICK)
            {
                mix_float_sample(mix, totalFrames, frame, kick, 0.85f, 0.0f);
            }
            else
            {
                mix_kick(mix, totalFrames, frame, (int)(beatFrames * 0.45), 0.55f);
            }
        }

        if (segment->timeNum >= 4 && beatInBar == 2)
        {
            if (snare && snare->role == ROLE_SNARE)
            {
                mix_float_sample(mix, totalFrames, frame, snare, 0.65f, 0.0f);
            }
            else
            {
                mix_noise_hit(mix, totalFrames, frame, (int)(beatFrames * 0.18), 0.28f, 0.0f, rng);
            }
        }
        else if (segment->timeNum == 3 && beatInBar == 1)
        {
            if (snare)
            {
                mix_float_sample(mix, totalFrames, frame, snare, 0.55f, 0.0f);
            }
        }

        if (hat && rng_next_float(rng) < (0.55f + style.density * 0.3f))
        {
            mix_float_sample(mix, totalFrames, frame, hat, 0.22f, -0.1f);
        }
        else if (rng_next_float(rng) < 0.65f)
        {
            mix_noise_hit(mix, totalFrames, frame, (int)(beatFrames * 0.08), 0.07f, -0.2f, rng);
        }

        if (rng_next_float(rng) < (0.42f + style.density * 0.35f))
        {
            if (hat)
            {
                mix_float_sample(mix, totalFrames, eighthFrame, hat, 0.14f, 0.2f);
            }
            else
            {
                mix_noise_hit(mix, totalFrames, eighthFrame, (int)(beatFrames * 0.06), 0.05f, 0.15f, rng);
            }
        }

        if (beatInBar == 0 || rng_next_float(rng) < 0.25f)
        {
            int degree = rng_range(rng, 0, 6);
            int midi = keyRoot + scale[degree] - (degree > 3 ? 12 : 0);
            int duration = (int)(beatFrames * (beatInBar == 0 ? 1.8 : 0.85));
            int bassIndex = weighted_role_pick(rng, ROLE_BASS, ROLE_PAD, &style);
            Sample *bass = bassIndex >= 0 ? &g_app.samples[bassIndex] : NULL;
            if (bass && bass->role == ROLE_BASS)
            {
                mix_float_sample(mix, totalFrames, frame, bass, 0.33f, -0.05f);
            }
            mix_sine_note(mix, totalFrames, frame, duration, midi_to_freq(midi), 0.12f + style.energy * 0.08f, -0.05f, style.brightness * 0.6f);
        }

        if (rng_next_float(rng) < (0.30f + style.density * 0.2f))
        {
            int degree = rng_range(rng, 0, 6);
            int midi = keyRoot + 12 + scale[degree];
            int duration = (int)(beatFrames * (0.5 + rng_next_float(rng) * 0.7));
            mix_sine_note(mix, totalFrames, frame, duration, midi_to_freq(midi), 0.06f + style.brightness * 0.05f, 0.18f, style.brightness);
        }
    }

    if (StrStrIW(segment->tag, L"rise") || StrStrIW(segment->tag, L"lift") || StrStrIW(segment->name, L"chorus"))
    {
        int fxIndex = weighted_role_pick(rng, ROLE_FX, ROLE_PAD, &style);
        Sample *fx = fxIndex >= 0 ? &g_app.samples[fxIndex] : NULL;
        if (fx)
        {
            mix_float_sample(mix, totalFrames, sectionStartFrame, fx, 0.38f, 0.0f);
        }
    }

    if (StrStrIW(segment->tag, L"break") || StrStrIW(segment->name, L"bridge"))
    {
        int frame = sectionStartFrame + (int)(barFrames * (segment->bars > 1 ? 1 : 0));
        mix_noise_hit(mix, totalFrames, frame, (int)(beatFrames * 0.8), 0.18f, 0.0f, rng);
    }
}

static int write_output_wav(const wchar_t *path, const float *mix, int frames)
{
    FILE *file = _wfopen(path, L"wb");
    uint32_t dataSize = (uint32_t)(frames * 2 * sizeof(int16_t));
    uint32_t riffSize = 36 + dataSize;
    uint16_t audioFormat = 1;
    uint16_t channels = 2;
    uint32_t sampleRate = OUTPUT_SAMPLE_RATE;
    uint32_t byteRate = sampleRate * channels * sizeof(int16_t);
    uint16_t blockAlign = channels * sizeof(int16_t);
    uint16_t bitsPerSample = 16;
    int index;

    if (!file)
    {
        return 0;
    }

    fwrite("RIFF", 1, 4, file);
    fwrite(&riffSize, sizeof(uint32_t), 1, file);
    fwrite("WAVE", 1, 4, file);
    fwrite("fmt ", 1, 4, file);
    {
        uint32_t fmtSize = 16;
        fwrite(&fmtSize, sizeof(uint32_t), 1, file);
    }
    fwrite(&audioFormat, sizeof(uint16_t), 1, file);
    fwrite(&channels, sizeof(uint16_t), 1, file);
    fwrite(&sampleRate, sizeof(uint32_t), 1, file);
    fwrite(&byteRate, sizeof(uint32_t), 1, file);
    fwrite(&blockAlign, sizeof(uint16_t), 1, file);
    fwrite(&bitsPerSample, sizeof(uint16_t), 1, file);
    fwrite("data", 1, 4, file);
    fwrite(&dataSize, sizeof(uint32_t), 1, file);

    for (index = 0; index < frames * 2; ++index)
    {
        float value = clamp_float(mix[index], -1.0f, 1.0f);
        int16_t pcm = (int16_t)(value * 32767.0f);
        fwrite(&pcm, sizeof(int16_t), 1, file);
    }

    fclose(file);
    return 1;
}

static int prepare_samples_from_zip(const wchar_t *zipPath)
{
    int roleCounts[ROLE_COUNT] = {0};
    int index;
    free_samples();

    if (!extract_zip_to_temp(zipPath, g_app.extractedDir, MAX_PATH))
    {
        set_status(L"ZIP extraction failed. Ensure PowerShell Expand-Archive can read the pack.");
        return 0;
    }

    scan_samples_recursive(g_app.extractedDir);
    for (index = 0; index < g_app.sampleCount; ++index)
    {
        roleCounts[g_app.samples[index].role] += 1;
    }
    synthvoice_learn_from_roles(&g_app.synthVoice, roleCounts, ROLE_COUNT);
    synthvoice_bank_save_in_module_dir(&g_app.synthVoice);
    wcsncpy(g_app.loadedZip, zipPath, MAX_PATH - 1);
    g_app.loadedZip[MAX_PATH - 1] = 0;

    if (g_app.sampleCount == 0)
    {
        set_status(L"No WAV files were found inside the ZIP sample pack.");
        return 0;
    }

    return 1;
}

static int total_song_frames(void)
{
    int total = 0;
    int index;
    for (index = 0; index < g_app.segmentCount; ++index)
    {
        double beatFrames = (60.0 / g_app.segments[index].tempo) * OUTPUT_SAMPLE_RATE * (4.0 / g_app.segments[index].timeDen);
        total += (int)(beatFrames * g_app.segments[index].timeNum * g_app.segments[index].bars);
    }
    return total;
}

static int generate_song(void)
{
    wchar_t zipPath[MAX_PATH];
    wchar_t prompt[1024];
    PromptStyle style;
    FILETIME fileTime;
    LARGE_INTEGER counter;
    ULARGE_INTEGER ftValue;
    Rng rng;
    float *mix;
    int frames;
    int index;
    int cursor = 0;
    int totalBars = 0;
    wchar_t tempRoot[MAX_PATH];

    GetWindowTextW(g_app.editZip, zipPath, MAX_PATH - 1);
    GetWindowTextW(g_app.editPrompt, prompt, 1023);
    if (!zipPath[0])
    {
        MessageBoxW(g_app.hwndMain, L"Select a ZIP sample pack first.", L"zipSongAI", MB_ICONWARNING);
        return 0;
    }

    if (!g_app.loadedZip[0] || wcscmp(zipPath, g_app.loadedZip) != 0 || g_app.sampleCount == 0)
    {
        set_status(L"Extracting ZIP and indexing WAV samples...");
        if (!prepare_samples_from_zip(zipPath))
        {
            return 0;
        }
    }

    frames = total_song_frames();
    if (frames <= 0)
    {
        MessageBoxW(g_app.hwndMain, L"Song timeline is empty.", L"zipSongAI", MB_ICONWARNING);
        return 0;
    }

    mix = (float *)calloc((size_t)frames * 2, sizeof(float));
    if (!mix)
    {
        MessageBoxW(g_app.hwndMain, L"Unable to allocate render buffer.", L"zipSongAI", MB_ICONERROR);
        return 0;
    }

    style = analyze_prompt(prompt);
    GetSystemTimeAsFileTime(&fileTime);
    QueryPerformanceCounter(&counter);
    ftValue.LowPart = fileTime.dwLowDateTime;
    ftValue.HighPart = fileTime.dwHighDateTime;
    ++g_app.generationCounter;
    rng.state = ftValue.QuadPart ^ (uint64_t)counter.QuadPart ^ (g_app.generationCounter * 0x9E3779B97F4A7C15ull);
    if (rng.state == 0)
    {
        rng.state = 0xA531D1B7u;
    }

    for (index = 0; index < g_app.segmentCount; ++index)
    {
        Segment adjusted = g_app.segments[index];
        adjusted.tempo = clamp_int(adjusted.tempo, 40, 240);
        adjusted.timeNum = clamp_int(adjusted.timeNum, 2, 12);
        adjusted.timeDen = adjusted.timeDen == 8 ? 8 : 4;
        adjusted.keyIndex = clamp_int(adjusted.keyIndex, 0, 11);
        synthvoice_learn_tag(&g_app.synthVoice, adjusted.tag, 0.03f);
        render_section(mix, frames, cursor, &adjusted, style, &rng);
        cursor += (int)((60.0 / adjusted.tempo) * OUTPUT_SAMPLE_RATE * (4.0 / adjusted.timeDen) * adjusted.timeNum * adjusted.bars);
        totalBars += adjusted.bars;
    }

    {
        float peak = 0.001f;
        for (index = 0; index < frames * 2; ++index)
        {
            float magnitude = fabsf(mix[index]);
            if (magnitude > peak)
            {
                peak = magnitude;
            }
        }
        if (peak > 0.95f)
        {
            float scale = 0.92f / peak;
            for (index = 0; index < frames * 2; ++index)
            {
                mix[index] *= scale;
            }
        }
    }

    if (!GetTempPathW(MAX_PATH, tempRoot))
    {
        free(mix);
        return 0;
    }
    swprintf(g_app.renderedPath, MAX_PATH, L"%lszipSongAI_render_%llu.wav", tempRoot, (unsigned long long)g_app.generationCounter);

    if (!write_output_wav(g_app.renderedPath, mix, frames))
    {
        free(mix);
        MessageBoxW(g_app.hwndMain, L"Failed to write the rendered WAV file.", L"zipSongAI", MB_ICONERROR);
        return 0;
    }

    free(mix);
    synthvoice_record_result(
        &g_app.synthVoice,
        &style,
        read_int(g_app.editTempo, 110),
        frames,
        totalBars,
        (int)SendMessageW(g_app.comboKey, CB_GETCURSEL, 0, 0),
        clamp_int(read_int(g_app.editTimeNum, 4) - 1, 0, 11),
        prompt);
    synthvoice_personality_note_generation(&g_app.personality, &g_app.synthVoice, prompt, g_app.renderedPath);
    synthvoice_bank_save_in_module_dir(&g_app.synthVoice);
    synthvoice_personality_save_in_module_dir(&g_app.personality);
    {
        wchar_t status[256];
        swprintf(status, 256, L"%ls complete. Runs: %u | samples learned: %u | render #%llu",
                 g_app.personality.displayName,
                 g_app.synthVoice.totalRuns,
                 g_app.synthVoice.learnedSampleCount,
                 (unsigned long long)g_app.generationCounter);
        set_status(status);
    }
    return 1;
}

static void fill_key_combo(HWND combo)
{
    int index;
    for (index = 0; index < 12; ++index)
    {
        SendMessageW(combo, CB_ADDSTRING, 0, (LPARAM)g_keys[index]);
    }
}

static void init_default_segments(void)
{
    g_app.segmentCount = 4;

    wcscpy(g_app.segments[0].name, L"Intro");
    wcscpy(g_app.segments[0].tag, L"lift");
    g_app.segments[0].bars = 8;
    g_app.segments[0].tempo = 108;
    g_app.segments[0].timeNum = 4;
    g_app.segments[0].timeDen = 4;
    g_app.segments[0].keyIndex = 0;
    g_app.segments[0].color = RGB(77, 125, 184);

    wcscpy(g_app.segments[1].name, L"Verse");
    wcscpy(g_app.segments[1].tag, L"steady");
    g_app.segments[1].bars = 16;
    g_app.segments[1].tempo = 108;
    g_app.segments[1].timeNum = 4;
    g_app.segments[1].timeDen = 4;
    g_app.segments[1].keyIndex = 0;
    g_app.segments[1].color = RGB(80, 152, 95);

    wcscpy(g_app.segments[2].name, L"Chorus");
    wcscpy(g_app.segments[2].tag, L"rise");
    g_app.segments[2].bars = 16;
    g_app.segments[2].tempo = 112;
    g_app.segments[2].timeNum = 4;
    g_app.segments[2].timeDen = 4;
    g_app.segments[2].keyIndex = 0;
    g_app.segments[2].color = RGB(202, 111, 59);

    wcscpy(g_app.segments[3].name, L"Outro");
    wcscpy(g_app.segments[3].tag, L"fade");
    g_app.segments[3].bars = 8;
    g_app.segments[3].tempo = 104;
    g_app.segments[3].timeNum = 4;
    g_app.segments[3].timeDen = 4;
    g_app.segments[3].keyIndex = 0;
    g_app.segments[3].color = RGB(125, 92, 182);

    g_app.selectedSegment = 0;
}

static void refresh_segment_list(void)
{
    int index;
    SendMessageW(g_app.listSegments, LB_RESETCONTENT, 0, 0);
    for (index = 0; index < g_app.segmentCount; ++index)
    {
        wchar_t item[256];
        swprintf(item, 256, L"%d. %ls | %d bars | %d/%d | %d BPM | %ls | tag:%ls",
                 index + 1,
                 g_app.segments[index].name,
                 g_app.segments[index].bars,
                 g_app.segments[index].timeNum,
                 g_app.segments[index].timeDen,
                 g_app.segments[index].tempo,
                 g_keys[g_app.segments[index].keyIndex],
                 g_app.segments[index].tag);
        SendMessageW(g_app.listSegments, LB_ADDSTRING, 0, (LPARAM)item);
    }
    SendMessageW(g_app.listSegments, LB_SETCURSEL, g_app.selectedSegment, 0);
    InvalidateRect(g_app.hwndMain, NULL, TRUE);
}

static void load_selected_segment_fields(void)
{
    Segment *segment;
    if (g_app.selectedSegment < 0 || g_app.selectedSegment >= g_app.segmentCount)
    {
        return;
    }
    segment = &g_app.segments[g_app.selectedSegment];
    SetWindowTextW(g_app.editSegName, segment->name);
    SetWindowTextW(g_app.editSegTag, segment->tag);
    write_int(g_app.editSegBars, segment->bars);
    write_int(g_app.editSegTempo, segment->tempo);
    write_int(g_app.editSegTimeNum, segment->timeNum);
    write_int(g_app.editSegTimeDen, segment->timeDen);
    SendMessageW(g_app.comboSegKey, CB_SETCURSEL, segment->keyIndex, 0);
}

static void apply_selected_segment_fields(void)
{
    Segment *segment;
    if (g_app.selectedSegment < 0 || g_app.selectedSegment >= g_app.segmentCount)
    {
        return;
    }

    segment = &g_app.segments[g_app.selectedSegment];
    GetWindowTextW(g_app.editSegName, segment->name, 31);
    GetWindowTextW(g_app.editSegTag, segment->tag, 63);
    segment->bars = clamp_int(read_int(g_app.editSegBars, segment->bars), 1, 64);
    segment->tempo = clamp_int(read_int(g_app.editSegTempo, segment->tempo), 40, 240);
    segment->timeNum = clamp_int(read_int(g_app.editSegTimeNum, segment->timeNum), 2, 12);
    {
        int den = read_int(g_app.editSegTimeDen, segment->timeDen);
        segment->timeDen = den == 8 ? 8 : 4;
    }
    segment->keyIndex = (int)SendMessageW(g_app.comboSegKey, CB_GETCURSEL, 0, 0);
    if (segment->keyIndex < 0)
    {
        segment->keyIndex = 0;
    }
    refresh_segment_list();
    load_selected_segment_fields();
}

static void add_segment(void)
{
    int insertAt;
    int index;
    if (g_app.segmentCount >= MAX_SEGMENTS)
    {
        return;
    }
    insertAt = g_app.selectedSegment >= 0 ? g_app.selectedSegment + 1 : g_app.segmentCount;
    for (index = g_app.segmentCount; index > insertAt; --index)
    {
        g_app.segments[index] = g_app.segments[index - 1];
    }
    wcscpy(g_app.segments[insertAt].name, L"New Part");
    wcscpy(g_app.segments[insertAt].tag, L"idea");
    g_app.segments[insertAt].bars = 8;
    g_app.segments[insertAt].tempo = read_int(g_app.editTempo, 110);
    g_app.segments[insertAt].timeNum = read_int(g_app.editTimeNum, 4);
    g_app.segments[insertAt].timeDen = read_int(g_app.editTimeDen, 4) == 8 ? 8 : 4;
    g_app.segments[insertAt].keyIndex = (int)SendMessageW(g_app.comboKey, CB_GETCURSEL, 0, 0);
    g_app.segments[insertAt].color = role_color((AudioRole)(insertAt % ROLE_COUNT));
    ++g_app.segmentCount;
    g_app.selectedSegment = insertAt;
    refresh_segment_list();
    load_selected_segment_fields();
}

static void remove_segment(void)
{
    int index;
    if (g_app.segmentCount <= 1 || g_app.selectedSegment < 0 || g_app.selectedSegment >= g_app.segmentCount)
    {
        return;
    }
    for (index = g_app.selectedSegment; index < g_app.segmentCount - 1; ++index)
    {
        g_app.segments[index] = g_app.segments[index + 1];
    }
    --g_app.segmentCount;
    if (g_app.selectedSegment >= g_app.segmentCount)
    {
        g_app.selectedSegment = g_app.segmentCount - 1;
    }
    refresh_segment_list();
    load_selected_segment_fields();
}

static void move_segment(int delta)
{
    int target = g_app.selectedSegment + delta;
    Segment temp;
    if (g_app.selectedSegment < 0 || g_app.selectedSegment >= g_app.segmentCount || target < 0 || target >= g_app.segmentCount)
    {
        return;
    }
    temp = g_app.segments[g_app.selectedSegment];
    g_app.segments[g_app.selectedSegment] = g_app.segments[target];
    g_app.segments[target] = temp;
    g_app.selectedSegment = target;
    refresh_segment_list();
    load_selected_segment_fields();
}

static void browse_zip(void)
{
    OPENFILENAMEW ofn;
    wchar_t path[MAX_PATH] = L"";
    ZeroMemory(&ofn, sizeof(ofn));
    ofn.lStructSize = sizeof(ofn);
    ofn.hwndOwner = g_app.hwndMain;
    ofn.lpstrFilter = L"ZIP sample packs\0*.zip\0All files\0*.*\0";
    ofn.lpstrFile = path;
    ofn.nMaxFile = MAX_PATH;
    ofn.Flags = OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST;
    if (GetOpenFileNameW(&ofn))
    {
        SetWindowTextW(g_app.editZip, path);
        set_status(L"ZIP selected. Adjust the prompt and timeline, then generate.");
    }
}

static void draw_timeline(HDC hdc)
{
    RECT outer = {20, TIMELINE_TOP, 1040, TIMELINE_TOP + TIMELINE_HEIGHT};
    HBRUSH background = CreateSolidBrush(RGB(24, 26, 30));
    HPEN border = CreatePen(PS_SOLID, 1, RGB(76, 85, 97));
    int totalBars = 0;
    int cursor = outer.left + 12;
    int innerWidth = (outer.right - outer.left) - 24;
    int index;
    SetBkMode(hdc, TRANSPARENT);
    FillRect(hdc, &outer, background);
    SelectObject(hdc, border);
    Rectangle(hdc, outer.left, outer.top, outer.right, outer.bottom);
    SetTextColor(hdc, RGB(224, 226, 230));
    TextOutW(hdc, outer.left + 12, outer.top + 10, L"Song Timeline", 13);

    for (index = 0; index < g_app.segmentCount; ++index)
    {
        totalBars += g_app.segments[index].bars;
    }
    if (totalBars <= 0)
    {
        totalBars = 1;
    }

    for (index = 0; index < g_app.segmentCount; ++index)
    {
        int width = (g_app.segments[index].bars * innerWidth) / totalBars;
        RECT box;
        HBRUSH fill;
        wchar_t text[192];
        if (index == g_app.segmentCount - 1)
        {
            width = outer.right - 12 - cursor;
        }
        if (width < 70)
        {
            width = 70;
        }
        box.left = cursor;
        box.top = outer.top + 42;
        box.right = cursor + width;
        box.bottom = outer.bottom - 20;
        fill = CreateSolidBrush(g_app.segments[index].color);
        FillRect(hdc, &box, fill);
        DeleteObject(fill);
        if (index == g_app.selectedSegment)
        {
            HPEN selectedPen = CreatePen(PS_SOLID, 3, RGB(255, 255, 255));
            SelectObject(hdc, selectedPen);
            Rectangle(hdc, box.left, box.top, box.right, box.bottom);
            DeleteObject(selectedPen);
            SelectObject(hdc, border);
        }
        else
        {
            Rectangle(hdc, box.left, box.top, box.right, box.bottom);
        }
        SetTextColor(hdc, RGB(245, 247, 250));
        swprintf(text, 192, L"%ls\n%ls\n%d bars | %d BPM | %d/%d | %ls",
                 g_app.segments[index].name,
                 g_app.segments[index].tag,
                 g_app.segments[index].bars,
                 g_app.segments[index].tempo,
                 g_app.segments[index].timeNum,
                 g_app.segments[index].timeDen,
                 g_keys[g_app.segments[index].keyIndex]);
        DrawTextW(hdc, text, -1, &box, DT_CENTER | DT_VCENTER | DT_WORDBREAK);
        cursor += width + 6;
    }

    DeleteObject(background);
    DeleteObject(border);
}

static LRESULT CALLBACK player_wnd_proc(HWND hwnd, UINT message, WPARAM wParam, LPARAM lParam)
{
    switch (message)
    {
    case WM_CREATE:
    {
        CreateWindowW(L"STATIC", L"Rendered song:", WS_CHILD | WS_VISIBLE, 20, 20, 120, 20, hwnd, NULL, NULL, NULL);
        g_app.playerPathLabel = CreateWindowW(L"STATIC", g_app.renderedPath, WS_CHILD | WS_VISIBLE, 20, 45, 520, 40, hwnd, NULL, NULL, NULL);
        CreateWindowW(L"BUTTON", L"Play", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 20, 95, 90, 30, hwnd, (HMENU)IDC_PLAY, NULL, NULL);
        CreateWindowW(L"BUTTON", L"Stop", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 120, 95, 90, 30, hwnd, (HMENU)IDC_STOP, NULL, NULL);
        CreateWindowW(L"BUTTON", L"Save As...", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 220, 95, 110, 30, hwnd, (HMENU)IDC_SAVE, NULL, NULL);
        return 0;
    }
    case WM_COMMAND:
        switch (LOWORD(wParam))
        {
        case IDC_PLAY:
            PlaySoundW(g_app.renderedPath, NULL, SND_FILENAME | SND_ASYNC | SND_NODEFAULT);
            return 0;
        case IDC_STOP:
            PlaySoundW(NULL, NULL, 0);
            return 0;
        case IDC_SAVE:
        {
            OPENFILENAMEW ofn;
            wchar_t outputPath[MAX_PATH] = L"generated_song.wav";
            ZeroMemory(&ofn, sizeof(ofn));
            ofn.lStructSize = sizeof(ofn);
            ofn.hwndOwner = hwnd;
            ofn.lpstrFilter = L"Wave files\0*.wav\0All files\0*.*\0";
            ofn.lpstrFile = outputPath;
            ofn.nMaxFile = MAX_PATH;
            ofn.Flags = OFN_OVERWRITEPROMPT;
            if (GetSaveFileNameW(&ofn))
            {
                if (!CopyFileW(g_app.renderedPath, outputPath, FALSE))
                {
                    MessageBoxW(hwnd, L"Failed to save the rendered song.", L"zipSongAI", MB_ICONERROR);
                }
            }
            return 0;
        }
        }
        break;
    case WM_DESTROY:
        if (g_app.hwndPlayer == hwnd)
        {
            g_app.hwndPlayer = NULL;
            g_app.playerPathLabel = NULL;
        }
        return 0;
    }
    return DefWindowProcW(hwnd, message, wParam, lParam);
}

static void show_player_window(void)
{
    if (g_app.hwndPlayer)
    {
        SetWindowTextW(g_app.hwndPlayer, L"zipSongAI Player");
        if (g_app.playerPathLabel)
        {
            SetWindowTextW(g_app.playerPathLabel, g_app.renderedPath);
        }
        ShowWindow(g_app.hwndPlayer, SW_SHOW);
        SetForegroundWindow(g_app.hwndPlayer);
        InvalidateRect(g_app.hwndPlayer, NULL, TRUE);
        return;
    }

    g_app.hwndPlayer = CreateWindowExW(
        WS_EX_APPWINDOW,
        PLAYER_CLASS,
        L"zipSongAI Player",
        WS_OVERLAPPEDWINDOW | WS_VISIBLE,
        CW_USEDEFAULT,
        CW_USEDEFAULT,
        600,
        200,
        NULL,
        NULL,
        GetModuleHandleW(NULL),
        NULL);
}

static void sync_global_fields_to_selected(void)
{
    Segment *segment;
    if (g_app.selectedSegment < 0 || g_app.selectedSegment >= g_app.segmentCount)
    {
        return;
    }
    segment = &g_app.segments[g_app.selectedSegment];
    segment->tempo = clamp_int(read_int(g_app.editTempo, segment->tempo), 40, 240);
    segment->timeNum = clamp_int(read_int(g_app.editTimeNum, segment->timeNum), 2, 12);
    segment->timeDen = read_int(g_app.editTimeDen, segment->timeDen) == 8 ? 8 : 4;
    segment->keyIndex = (int)SendMessageW(g_app.comboKey, CB_GETCURSEL, 0, 0);
    if (segment->keyIndex < 0)
    {
        segment->keyIndex = 0;
    }
    refresh_segment_list();
    load_selected_segment_fields();
}

static LRESULT CALLBACK main_wnd_proc(HWND hwnd, UINT message, WPARAM wParam, LPARAM lParam)
{
    switch (message)
    {
    case WM_CREATE:
    {
        HFONT font = (HFONT)GetStockObject(DEFAULT_GUI_FONT);
        g_app.hwndMain = hwnd;

        CreateWindowW(L"STATIC", L"ZIP Sample Pack", WS_CHILD | WS_VISIBLE, 20, 18, 140, 20, hwnd, NULL, NULL, NULL);
        g_app.editZip = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"", WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL, 20, 42, 760, 26, hwnd, (HMENU)IDC_ZIP_PATH, NULL, NULL);
        CreateWindowW(L"BUTTON", L"Browse...", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 790, 42, 100, 26, hwnd, (HMENU)IDC_BROWSE_ZIP, NULL, NULL);

        CreateWindowW(L"STATIC", L"Guide Prompt", WS_CHILD | WS_VISIBLE, 20, 82, 140, 20, hwnd, NULL, NULL, NULL);
        g_app.editPrompt = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"Procedural indie-electronic song with a bright intro, dark verse, rising chorus, and a clean outro.", WS_CHILD | WS_VISIBLE | ES_MULTILINE | ES_AUTOVSCROLL | WS_VSCROLL, 20, 106, 520, 108, hwnd, (HMENU)IDC_PROMPT, NULL, NULL);

        CreateWindowW(L"STATIC", L"Base Tempo", WS_CHILD | WS_VISIBLE, 570, 106, 90, 20, hwnd, NULL, NULL, NULL);
        g_app.editTempo = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"110", WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL, 570, 130, 70, 24, hwnd, (HMENU)IDC_TEMPO, NULL, NULL);

        CreateWindowW(L"STATIC", L"Time Signature", WS_CHILD | WS_VISIBLE, 660, 106, 110, 20, hwnd, NULL, NULL, NULL);
        g_app.editTimeNum = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"4", WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL, 660, 130, 40, 24, hwnd, (HMENU)IDC_TIMENUM, NULL, NULL);
        g_app.editTimeDen = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"4", WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL, 706, 130, 40, 24, hwnd, (HMENU)IDC_TIMEDEN, NULL, NULL);

        CreateWindowW(L"STATIC", L"Key", WS_CHILD | WS_VISIBLE, 770, 106, 50, 20, hwnd, NULL, NULL, NULL);
        g_app.comboKey = CreateWindowW(L"COMBOBOX", L"", WS_CHILD | WS_VISIBLE | CBS_DROPDOWNLIST, 770, 130, 120, 180, hwnd, (HMENU)IDC_KEY, NULL, NULL);
        fill_key_combo(g_app.comboKey);
        SendMessageW(g_app.comboKey, CB_SETCURSEL, 0, 0);

        CreateWindowW(L"STATIC", L"Song Sections", WS_CHILD | WS_VISIBLE, 20, 230, 120, 20, hwnd, NULL, NULL, NULL);
        g_app.listSegments = CreateWindowExW(WS_EX_CLIENTEDGE, L"LISTBOX", L"", WS_CHILD | WS_VISIBLE | LBS_NOTIFY | WS_VSCROLL, 20, 254, 520, 190, hwnd, (HMENU)IDC_SEGMENT_LIST, NULL, NULL);

        CreateWindowW(L"STATIC", L"Section Name", WS_CHILD | WS_VISIBLE, 570, 230, 100, 20, hwnd, NULL, NULL, NULL);
        g_app.editSegName = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"", WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL, 570, 254, 140, 24, hwnd, (HMENU)IDC_SEGMENT_NAME, NULL, NULL);
        CreateWindowW(L"STATIC", L"Context Tag", WS_CHILD | WS_VISIBLE, 720, 230, 90, 20, hwnd, NULL, NULL, NULL);
        g_app.editSegTag = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"", WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL, 720, 254, 170, 24, hwnd, (HMENU)IDC_SEGMENT_TAG, NULL, NULL);

        CreateWindowW(L"STATIC", L"Bars", WS_CHILD | WS_VISIBLE, 570, 292, 50, 20, hwnd, NULL, NULL, NULL);
        g_app.editSegBars = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"8", WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL, 570, 316, 55, 24, hwnd, (HMENU)IDC_SEGMENT_BARS, NULL, NULL);
        CreateWindowW(L"STATIC", L"Tempo", WS_CHILD | WS_VISIBLE, 635, 292, 50, 20, hwnd, NULL, NULL, NULL);
        g_app.editSegTempo = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"110", WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL, 635, 316, 60, 24, hwnd, (HMENU)IDC_SEGMENT_TEMPO, NULL, NULL);
        CreateWindowW(L"STATIC", L"Meter", WS_CHILD | WS_VISIBLE, 705, 292, 50, 20, hwnd, NULL, NULL, NULL);
        g_app.editSegTimeNum = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"4", WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL, 705, 316, 40, 24, hwnd, (HMENU)IDC_SEGMENT_TIMENUM, NULL, NULL);
        g_app.editSegTimeDen = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"4", WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL, 750, 316, 40, 24, hwnd, (HMENU)IDC_SEGMENT_TIMEDEN, NULL, NULL);
        CreateWindowW(L"STATIC", L"Key", WS_CHILD | WS_VISIBLE, 800, 292, 40, 20, hwnd, NULL, NULL, NULL);
        g_app.comboSegKey = CreateWindowW(L"COMBOBOX", L"", WS_CHILD | WS_VISIBLE | CBS_DROPDOWNLIST, 800, 316, 90, 180, hwnd, (HMENU)IDC_SEGMENT_KEY, NULL, NULL);
        fill_key_combo(g_app.comboSegKey);

        CreateWindowW(L"BUTTON", L"Add", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 570, 360, 70, 28, hwnd, (HMENU)IDC_SEGMENT_ADD, NULL, NULL);
        CreateWindowW(L"BUTTON", L"Remove", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 650, 360, 80, 28, hwnd, (HMENU)IDC_SEGMENT_REMOVE, NULL, NULL);
        CreateWindowW(L"BUTTON", L"Move Up", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 740, 360, 75, 28, hwnd, (HMENU)IDC_SEGMENT_UP, NULL, NULL);
        CreateWindowW(L"BUTTON", L"Move Down", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 820, 360, 90, 28, hwnd, (HMENU)IDC_SEGMENT_DOWN, NULL, NULL);
        CreateWindowW(L"BUTTON", L"Apply Changes", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 570, 396, 140, 30, hwnd, (HMENU)IDC_SEGMENT_APPLY, NULL, NULL);

        CreateWindowW(L"BUTTON", L"Generate Unique Song", WS_CHILD | WS_VISIBLE | BS_DEFPUSHBUTTON, 760, 396, 180, 34, hwnd, (HMENU)IDC_GENERATE, NULL, NULL);
        {
            wchar_t initialStatus[256];
            swprintf(initialStatus, 256, L"%ls ready. Prior runs: %u. Select a ZIP and shape the timeline.", g_app.personality.displayName, g_app.synthVoice.totalRuns);
            g_app.status = CreateWindowW(L"STATIC", initialStatus, WS_CHILD | WS_VISIBLE, 20, 705, 1020, 24, hwnd, (HMENU)IDC_STATUS, NULL, NULL);
        }

        SendMessageW(g_app.editZip, WM_SETFONT, (WPARAM)font, TRUE);
        SendMessageW(g_app.editPrompt, WM_SETFONT, (WPARAM)font, TRUE);
        SendMessageW(g_app.editTempo, WM_SETFONT, (WPARAM)font, TRUE);
        SendMessageW(g_app.editTimeNum, WM_SETFONT, (WPARAM)font, TRUE);
        SendMessageW(g_app.editTimeDen, WM_SETFONT, (WPARAM)font, TRUE);
        SendMessageW(g_app.comboKey, WM_SETFONT, (WPARAM)font, TRUE);
        SendMessageW(g_app.listSegments, WM_SETFONT, (WPARAM)font, TRUE);
        SendMessageW(g_app.editSegName, WM_SETFONT, (WPARAM)font, TRUE);
        SendMessageW(g_app.editSegTag, WM_SETFONT, (WPARAM)font, TRUE);
        SendMessageW(g_app.editSegBars, WM_SETFONT, (WPARAM)font, TRUE);
        SendMessageW(g_app.editSegTempo, WM_SETFONT, (WPARAM)font, TRUE);
        SendMessageW(g_app.editSegTimeNum, WM_SETFONT, (WPARAM)font, TRUE);
        SendMessageW(g_app.editSegTimeDen, WM_SETFONT, (WPARAM)font, TRUE);
        SendMessageW(g_app.comboSegKey, WM_SETFONT, (WPARAM)font, TRUE);
        SendMessageW(g_app.status, WM_SETFONT, (WPARAM)font, TRUE);

        init_default_segments();
        refresh_segment_list();
        load_selected_segment_fields();
        return 0;
    }
    case WM_COMMAND:
        switch (LOWORD(wParam))
        {
        case IDC_BROWSE_ZIP:
            browse_zip();
            return 0;
        case IDC_SEGMENT_LIST:
            if (HIWORD(wParam) == LBN_SELCHANGE)
            {
                g_app.selectedSegment = (int)SendMessageW(g_app.listSegments, LB_GETCURSEL, 0, 0);
                load_selected_segment_fields();
                InvalidateRect(hwnd, NULL, TRUE);
            }
            return 0;
        case IDC_SEGMENT_ADD:
            add_segment();
            return 0;
        case IDC_SEGMENT_REMOVE:
            remove_segment();
            return 0;
        case IDC_SEGMENT_UP:
            move_segment(-1);
            return 0;
        case IDC_SEGMENT_DOWN:
            move_segment(1);
            return 0;
        case IDC_SEGMENT_APPLY:
            apply_selected_segment_fields();
            return 0;
        case IDC_GENERATE:
            sync_global_fields_to_selected();
            apply_selected_segment_fields();
            if (generate_song())
            {
                show_player_window();
                PlaySoundW(g_app.renderedPath, NULL, SND_FILENAME | SND_ASYNC | SND_NODEFAULT);
            }
            return 0;
        }
        break;
    case WM_PAINT:
    {
        PAINTSTRUCT ps;
        HDC hdc = BeginPaint(hwnd, &ps);
        draw_timeline(hdc);
        EndPaint(hwnd, &ps);
        return 0;
    }
    case WM_DESTROY:
        PlaySoundW(NULL, NULL, 0);
        free_samples();
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProcW(hwnd, message, wParam, lParam);
}

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE previous, PWSTR commandLine, int showCommand)
{
    WNDCLASSEXW mainClass;
    WNDCLASSEXW playerClass;
    MSG message;
    INITCOMMONCONTROLSEX commonControls;
    (void)previous;
    (void)commandLine;

    ZeroMemory(&g_app, sizeof(g_app));
    synthvoice_bank_load_in_module_dir(&g_app.synthVoice);
    synthvoice_personality_load_in_module_dir(&g_app.personality);

    commonControls.dwSize = sizeof(commonControls);
    commonControls.dwICC = ICC_WIN95_CLASSES;
    InitCommonControlsEx(&commonControls);

    ZeroMemory(&mainClass, sizeof(mainClass));
    mainClass.cbSize = sizeof(mainClass);
    mainClass.lpfnWndProc = main_wnd_proc;
    mainClass.hInstance = instance;
    mainClass.hCursor = LoadCursor(NULL, IDC_ARROW);
    mainClass.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    mainClass.lpszClassName = APP_CLASS;
    mainClass.hIcon = LoadIcon(NULL, IDI_APPLICATION);
    RegisterClassExW(&mainClass);

    ZeroMemory(&playerClass, sizeof(playerClass));
    playerClass.cbSize = sizeof(playerClass);
    playerClass.lpfnWndProc = player_wnd_proc;
    playerClass.hInstance = instance;
    playerClass.hCursor = LoadCursor(NULL, IDC_ARROW);
    playerClass.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    playerClass.lpszClassName = PLAYER_CLASS;
    playerClass.hIcon = LoadIcon(NULL, IDI_INFORMATION);
    RegisterClassExW(&playerClass);

    CreateWindowExW(
        WS_EX_APPWINDOW,
        APP_CLASS,
        L"zipSongAI - Prompt-Guided ZIP Sample Song Generator",
        WS_OVERLAPPEDWINDOW | WS_VISIBLE,
        CW_USEDEFAULT,
        CW_USEDEFAULT,
        1080,
        790,
        NULL,
        NULL,
        instance,
        NULL);

    ShowWindow(g_app.hwndMain, showCommand);
    UpdateWindow(g_app.hwndMain);

    while (GetMessageW(&message, NULL, 0, 0) > 0)
    {
        TranslateMessage(&message);
        DispatchMessageW(&message);
    }

    return (int)message.wParam;
}