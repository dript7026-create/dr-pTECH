#include "blastmonidz_bridge.h"

#include <stdio.h>
#include <string.h>
#include <time.h>

#ifdef _WIN32
#include <windows.h>
#include <sys/stat.h>
#define BLASTMONIDZ_PATH_MAX MAX_PATH
#define BLASTMONIDZ_STAT _stat
#define BLASTMONIDZ_STAT_STRUCT struct _stat
#else
#include <limits.h>
#include <sys/stat.h>
#define BLASTMONIDZ_PATH_MAX PATH_MAX
#define BLASTMONIDZ_STAT stat
#define BLASTMONIDZ_STAT_STRUCT struct stat
#endif

#define BLASTMONIDZ_BRIDGE_TEXT_MAX 256

static char g_inbox_path[BLASTMONIDZ_PATH_MAX] = {0};
static char g_outbox_path[BLASTMONIDZ_PATH_MAX] = {0};
static char g_latest_status[BLASTMONIDZ_BRIDGE_TEXT_MAX] = "Bridge offline.";
static char g_latest_inbox[BLASTMONIDZ_BRIDGE_TEXT_MAX] = "No external bridge message yet.";
static unsigned long long g_inbox_signature = 0;
static int g_initialized = 0;
#ifdef _WIN32
static HANDLE g_bridge_thread = NULL;
static volatile LONG g_bridge_running = 0;
#endif

static int read_latest_message(const char *path, char *buffer, size_t buffer_size);
static void append_outbox_entry(const char *channel, const char *message);

static void copy_text(char *dest, size_t dest_size, const char *text) {
    if (!dest || dest_size == 0) {
        return;
    }
    if (!text) {
        text = "";
    }
    snprintf(dest, dest_size, "%s", text);
}

static void trim_line(char *text) {
    size_t length;
    if (!text) {
        return;
    }
    length = strlen(text);
    while (length > 0 && (text[length - 1] == '\n' || text[length - 1] == '\r' || text[length - 1] == ' ' || text[length - 1] == '\t')) {
        text[length - 1] = '\0';
        --length;
    }
    while (*text == ' ' || *text == '\t') {
        memmove(text, text + 1, strlen(text));
    }
}

static void build_path(char *dest, size_t dest_size, const char *dir, const char *leaf) {
    size_t used;
    copy_text(dest, dest_size, dir);
    used = strlen(dest);
    if (used + 1 < dest_size && used > 0 && dest[used - 1] != '\\' && dest[used - 1] != '/') {
        dest[used++] = '\\';
        dest[used] = '\0';
    }
    if (used < dest_size) {
        strncat(dest, leaf, dest_size - used - 1);
    }
}

static void resolve_bridge_paths(void) {
    char module_path[BLASTMONIDZ_PATH_MAX];
    char *separator;
#ifdef _WIN32
    DWORD result = GetModuleFileNameA(NULL, module_path, (DWORD)sizeof(module_path));
    if (result == 0 || result >= sizeof(module_path)) {
            copy_text(module_path, sizeof(module_path), ".\\blastmonidz_host.exe");
    }
#else
        copy_text(module_path, sizeof(module_path), "./blastmonidz_host.exe");
#endif
    separator = strrchr(module_path, '\\');
    if (!separator) {
        separator = strrchr(module_path, '/');
    }
    if (separator) {
        *separator = '\0';
    } else {
        copy_text(module_path, sizeof(module_path), ".");
    }
        build_path(g_inbox_path, sizeof(g_inbox_path), module_path, "blastmonidz_bridge_inbox.txt");
        build_path(g_outbox_path, sizeof(g_outbox_path), module_path, "blastmonidz_bridge_outbox.txt");
}

static unsigned long long read_signature(const char *path) {
    BLASTMONIDZ_STAT_STRUCT info;
    if (!path || BLASTMONIDZ_STAT(path, &info) != 0) {
        return 0;
    }
    return ((unsigned long long)info.st_mtime << 32) ^ (unsigned long long)info.st_size;
}

static void poll_once(void) {
    unsigned long long signature;
    char message[BLASTMONIDZ_BRIDGE_TEXT_MAX];
    if (!g_initialized) {
        return;
    }
    signature = read_signature(g_inbox_path);
    if (signature == 0 || signature == g_inbox_signature) {
        return;
    }
    g_inbox_signature = signature;
    if (!read_latest_message(g_inbox_path, message, sizeof(message))) {
        return;
    }
    if (strcmp(message, g_latest_inbox) == 0) {
        return;
    }
    copy_text(g_latest_inbox, sizeof(g_latest_inbox), message);
    copy_text(g_latest_status, sizeof(g_latest_status), "Bridge synced a new external update.");
    append_outbox_entry("inbox", g_latest_inbox);
    append_outbox_entry("status", g_latest_status);
}

#ifdef _WIN32
static DWORD WINAPI blastmonidz_bridge_thread_main(LPVOID unused) {
    (void)unused;
    while (InterlockedCompareExchange(&g_bridge_running, 1, 1) == 1) {
        poll_once();
        Sleep(150);
    }
    return 0;
}
#endif

static int read_latest_message(const char *path, char *buffer, size_t buffer_size) {
    FILE *handle;
    char line[BLASTMONIDZ_BRIDGE_TEXT_MAX];
    int found;
    found = 0;
    if (!path || !buffer || buffer_size == 0) {
        return 0;
    }
    handle = fopen(path, "r");
    if (!handle) {
        return 0;
    }
    while (fgets(line, (int)sizeof(line), handle)) {
        trim_line(line);
        if (line[0] == '\0' || line[0] == '#') {
            continue;
        }
        copy_text(buffer, buffer_size, line);
        found = 1;
    }
    fclose(handle);
    return found;
}

static void append_outbox_entry(const char *channel, const char *message) {
    FILE *handle;
    time_t now;
    struct tm *time_info;
    char timestamp[32];
    if (!g_outbox_path[0] || !message) {
        return;
    }
    handle = fopen(g_outbox_path, "a");
    if (!handle) {
        return;
    }
    now = time(NULL);
    time_info = localtime(&now);
    if (time_info) {
        strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", time_info);
    } else {
        copy_text(timestamp, sizeof(timestamp), "unknown-time");
    }
    fprintf(handle, "[%s] %s | %s\n", timestamp, channel ? channel : "status", message);
    fclose(handle);
}

void blastmonidz_bridge_init(void) {
    FILE *handle;
    resolve_bridge_paths();
    handle = fopen(g_inbox_path, "a");
    if (handle) {
        fclose(handle);
    }
    copy_text(g_latest_status, sizeof(g_latest_status), "Bridge online. Polling external workflow inbox.");
    copy_text(g_latest_inbox, sizeof(g_latest_inbox), "No external bridge message yet.");
    g_inbox_signature = read_signature(g_inbox_path);
    g_initialized = 1;
#ifdef _WIN32
    InterlockedExchange(&g_bridge_running, 1);
    g_bridge_thread = CreateThread(NULL, 0, blastmonidz_bridge_thread_main, NULL, 0, NULL);
#endif
    append_outbox_entry("bridge", g_latest_status);
}

void blastmonidz_bridge_shutdown(void) {
    if (!g_initialized) {
        return;
    }
    copy_text(g_latest_status, sizeof(g_latest_status), "Bridge offline.");
    append_outbox_entry("bridge", g_latest_status);
#ifdef _WIN32
    InterlockedExchange(&g_bridge_running, 0);
    if (g_bridge_thread) {
        WaitForSingleObject(g_bridge_thread, 1000);
        CloseHandle(g_bridge_thread);
        g_bridge_thread = NULL;
    }
#endif
    g_initialized = 0;
}

void blastmonidz_bridge_poll(void) {
    poll_once();
}

void blastmonidz_bridge_publish_status(const char *channel, const char *message) {
    char status_line[BLASTMONIDZ_BRIDGE_TEXT_MAX];
    if (!g_initialized || !message) {
        return;
    }
    if (channel && channel[0]) {
        snprintf(status_line, sizeof(status_line), "%s: %s", channel, message);
    } else {
        copy_text(status_line, sizeof(status_line), message);
    }
    copy_text(g_latest_status, sizeof(g_latest_status), status_line);
    append_outbox_entry(channel ? channel : "status", message);
}

const char *blastmonidz_bridge_latest_status(void) {
    return g_latest_status;
}

const char *blastmonidz_bridge_latest_inbox(void) {
    return g_latest_inbox;
}

const char *blastmonidz_bridge_inbox_path(void) {
    return g_inbox_path;
}

const char *blastmonidz_bridge_outbox_path(void) {
    return g_outbox_path;
}