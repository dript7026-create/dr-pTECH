#include "plugin_loader.h"

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>

#ifndef _countof
#define _countof(arr) (sizeof(arr) / sizeof((arr)[0]))
#endif

typedef struct ManifestData {
    char* text;
    size_t len;
} ManifestData;

static bool read_small_text_file_utf8(const wchar_t* path, ManifestData* out) {
    HANDLE file = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE) {
        return false;
    }

    LARGE_INTEGER size;
    if (!GetFileSizeEx(file, &size) || size.QuadPart < 0 || size.QuadPart > (1024 * 1024)) {
        CloseHandle(file);
        return false;
    }

    DWORD bytes = (DWORD)size.QuadPart;
    char* data = (char*)malloc((size_t)bytes + 1);
    if (!data) {
        CloseHandle(file);
        return false;
    }

    DWORD readBytes = 0;
    bool ok = ReadFile(file, data, bytes, &readBytes, NULL) && readBytes == bytes;
    CloseHandle(file);

    if (!ok) {
        free(data);
        return false;
    }

    data[bytes] = 0;
    out->text = data;
    out->len = bytes;
    return true;
}

static bool extract_json_string_value(const char* json, const char* key, char* outValue, size_t outValueSize) {
    char needle[128];
    _snprintf_s(needle, sizeof(needle), _TRUNCATE, "\"%s\"", key);

    const char* keyPos = strstr(json, needle);
    if (!keyPos) {
        return false;
    }

    const char* colon = strchr(keyPos + strlen(needle), ':');
    if (!colon) {
        return false;
    }

    const char* start = strchr(colon, '"');
    if (!start) {
        return false;
    }
    start += 1;

    const char* end = strchr(start, '"');
    if (!end || end <= start) {
        return false;
    }

    size_t len = (size_t)(end - start);
    if (len >= outValueSize) {
        return false;
    }

    memcpy(outValue, start, len);
    outValue[len] = 0;
    return true;
}

static bool to_wide(const char* u8, wchar_t* out, size_t outCount) {
    int needed = MultiByteToWideChar(CP_UTF8, 0, u8, -1, NULL, 0);
    if (needed <= 0 || (size_t)needed > outCount) {
        return false;
    }
    return MultiByteToWideChar(CP_UTF8, 0, u8, -1, out, needed) > 0;
}

static bool path_dirname(const wchar_t* path, wchar_t* outDir, size_t outCount) {
    wcsncpy_s(outDir, outCount, path, _TRUNCATE);
    wchar_t* slash = wcsrchr(outDir, L'\\');
    if (!slash) {
        return false;
    }
    *slash = 0;
    return true;
}

static void load_manifest(const wchar_t* manifestPath, DotxtPluginLoadReport* report) {
    report->manifestsFound += 1;

    ManifestData md = {0};
    if (!read_small_text_file_utf8(manifestPath, &md)) {
        report->failed += 1;
        return;
    }

    char entryU8[260];
    if (!extract_json_string_value(md.text, "entry", entryU8, sizeof(entryU8))) {
        free(md.text);
        report->failed += 1;
        return;
    }

    wchar_t entryW[MAX_PATH];
    if (!to_wide(entryU8, entryW, _countof(entryW))) {
        free(md.text);
        report->failed += 1;
        return;
    }

    wchar_t manifestDir[MAX_PATH];
    if (!path_dirname(manifestPath, manifestDir, _countof(manifestDir))) {
        free(md.text);
        report->failed += 1;
        return;
    }

    wchar_t dllPath[MAX_PATH];
    _snwprintf_s(dllPath, _countof(dllPath), _TRUNCATE, L"%s\\%s", manifestDir, entryW);

    HMODULE mod = LoadLibraryW(dllPath);
    if (mod) {
        report->loaded += 1;
    } else {
        report->failed += 1;
    }

    free(md.text);
}

static void scan_tier(const wchar_t* root, const wchar_t* tier, DotxtPluginLoadReport* report) {
    wchar_t pattern[MAX_PATH];
    _snwprintf_s(pattern, _countof(pattern), _TRUNCATE, L"%s\\plugins\\%s\\*.manifest.json", root, tier);

    WIN32_FIND_DATAW ffd;
    HANDLE h = FindFirstFileW(pattern, &ffd);
    if (h == INVALID_HANDLE_VALUE) {
        return;
    }

    do {
        if (ffd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) {
            continue;
        }

        wchar_t manifestPath[MAX_PATH];
        _snwprintf_s(manifestPath, _countof(manifestPath), _TRUNCATE, L"%s\\plugins\\%s\\%s", root, tier, ffd.cFileName);
        load_manifest(manifestPath, report);
    } while (FindNextFileW(h, &ffd));

    FindClose(h);
}

void dotxt_load_plugins(const wchar_t* appRoot, DotxtPluginLoadReport* outReport) {
    DotxtPluginLoadReport report = {0};

    scan_tier(appRoot, L"free", &report);
    scan_tier(appRoot, L"premium", &report);
    scan_tier(appRoot, L"enterprise", &report);

    if (outReport) {
        *outReport = report;
    }
}
