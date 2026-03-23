#include <windows.h>
#include <wchar.h>
#include <stdint.h>

#define APP_CLASS_NAME L"DripSweepArcadeWindow"
#define APP_TITLE L"DripSweep Arcade"
#define APP_WIDTH 1040
#define APP_HEIGHT 780
#define FRAME_TIMER_ID 1
#define FRAME_INTERVAL_MS 16
#define STATUS_MESSAGE (WM_APP + 1)
#define BRICK_ROWS 6
#define BRICK_COLS 10
#define DRIVE_LIMIT 16
#define MILESTONE_COUNT 4
#define AUTO_SWEEP_DELAY_MS 12000

typedef struct DriveInfo {
    wchar_t root[4];
    ULONGLONG totalBytes;
    ULONGLONG freeBytes;
    UINT driveType;
} DriveInfo;

typedef struct SweepSettings {
    int retentionDays;
    int autoSweep;
    int aggressiveMode;
    int cleanTempEnabled;
} SweepSettings;

typedef struct SweepSnapshot {
    MEMORYSTATUSEX memory;
    DriveInfo drives[DRIVE_LIMIT];
    int driveCount;
    wchar_t tempPath[MAX_PATH];
    wchar_t phase[96];
    DWORD filesScanned;
    DWORD filesDeleted;
    DWORD directoriesVisited;
    ULONGLONG bytesScanned;
    ULONGLONG bytesDeleted;
    FILETIME startedAt;
    FILETIME finishedAt;
    int complete;
} SweepSnapshot;

typedef struct SweepTelemetry {
    DWORD cpuLoadPercent;
    DWORD peakMemoryLoad;
    DWORD sweepCount;
    DWORD lowSpaceAlerts;
    DWORD hottestDrivePercentUsed;
    ULONGLONG sessionBytesDeleted;
    ULONGLONG bestSweepBytesDeleted;
    ULONGLONG lastSweepDurationMs;
    ULONGLONG autoSweepAtTick;
    wchar_t hottestDriveRoot[4];
    FILETIME cpuIdle;
    FILETIME cpuKernel;
    FILETIME cpuUser;
    int cpuPrimed;
} SweepTelemetry;

typedef struct GameState {
    float paddleX;
    float paddleWidth;
    float ballX;
    float ballY;
    float ballVX;
    float ballVY;
    int ballLaunched;
    int moveLeft;
    int moveRight;
    int bricks[BRICK_ROWS][BRICK_COLS];
    int score;
    int combo;
    int lives;
    int level;
    int rewardTier;
    int scoreMultiplier;
    int shieldCharges;
    float speedScale;
    wchar_t notice[96];
    ULONGLONG noticeUntilTick;
} GameState;

typedef struct AppState {
    CRITICAL_SECTION lock;
    HWND hwnd;
    HANDLE workerThread;
    volatile LONG sweepRunning;
    SweepSettings settings;
    SweepSnapshot sweep;
    SweepTelemetry telemetry;
    GameState game;
    ULONGLONG lastTick;
} AppState;

static AppState g_app;

static const ULONGLONG kMilestones[MILESTONE_COUNT] = {
    16ULL * 1024ULL * 1024ULL,
    64ULL * 1024ULL * 1024ULL,
    128ULL * 1024ULL * 1024ULL,
    256ULL * 1024ULL * 1024ULL
};

static ULONGLONG filetime_to_ull(FILETIME value) {
    ULARGE_INTEGER ui;
    ui.LowPart = value.dwLowDateTime;
    ui.HighPart = value.dwHighDateTime;
    return ui.QuadPart;
}

static ULONGLONG now_filetime_ull(void) {
    FILETIME nowUtc;
    GetSystemTimeAsFileTime(&nowUtc);
    return filetime_to_ull(nowUtc);
}

static void format_bytes(ULONGLONG bytes, wchar_t *buffer, size_t bufferCount) {
    const wchar_t *units[] = { L"B", L"KB", L"MB", L"GB", L"TB" };
    double value = (double)bytes;
    int unit = 0;
    while (value >= 1024.0 && unit < 4) {
        value /= 1024.0;
        unit += 1;
    }
    swprintf(buffer, bufferCount, L"%.2f %ls", value, units[unit]);
}

static void set_phase(const wchar_t *phase) {
    EnterCriticalSection(&g_app.lock);
    wcsncpy(g_app.sweep.phase, phase, sizeof(g_app.sweep.phase) / sizeof(wchar_t) - 1);
    g_app.sweep.phase[(sizeof(g_app.sweep.phase) / sizeof(wchar_t)) - 1] = L'\0';
    LeaveCriticalSection(&g_app.lock);
    if (g_app.hwnd != NULL) {
        PostMessageW(g_app.hwnd, STATUS_MESSAGE, 0, 0);
    }
}

static void set_notice(const wchar_t *notice, ULONGLONG durationMs) {
    wcsncpy(g_app.game.notice, notice, sizeof(g_app.game.notice) / sizeof(wchar_t) - 1);
    g_app.game.notice[(sizeof(g_app.game.notice) / sizeof(wchar_t)) - 1] = L'\0';
    g_app.game.noticeUntilTick = GetTickCount64() + durationMs;
}

static void fill_bricks(void) {
    int row;
    int col;
    for (row = 0; row < BRICK_ROWS; ++row) {
        for (col = 0; col < BRICK_COLS; ++col) {
            g_app.game.bricks[row][col] = 1;
        }
    }
}

static void apply_reward_profile(void) {
    float basePaddle = 110.0f + (float)g_app.game.rewardTier * 12.0f;
    if (basePaddle > 170.0f) {
        basePaddle = 170.0f;
    }
    g_app.game.paddleWidth = basePaddle;
    g_app.game.scoreMultiplier = g_app.game.rewardTier >= 3 ? 2 : 1;
    g_app.game.speedScale = g_app.game.rewardTier >= 4 ? 1.25f : 1.0f;
}

static void reset_ball(void) {
    g_app.game.ballLaunched = 0;
    g_app.game.ballX = g_app.game.paddleX + g_app.game.paddleWidth / 2.0f;
    g_app.game.ballY = 614.0f;
    g_app.game.ballVX = 210.0f * g_app.game.speedScale;
    g_app.game.ballVY = -240.0f * g_app.game.speedScale;
    g_app.game.combo = 0;
}

static void reset_game(void) {
    g_app.game.paddleX = 420.0f;
    g_app.game.moveLeft = 0;
    g_app.game.moveRight = 0;
    g_app.game.score = 0;
    g_app.game.combo = 0;
    g_app.game.lives = 3;
    g_app.game.level = 1;
    g_app.game.rewardTier = 0;
    g_app.game.scoreMultiplier = 1;
    g_app.game.shieldCharges = 0;
    g_app.game.speedScale = 1.0f;
    g_app.game.notice[0] = L'\0';
    g_app.game.noticeUntilTick = 0;
    apply_reward_profile();
    fill_bricks();
    reset_ball();
}

static int count_remaining_bricks(void) {
    int row;
    int col;
    int remaining = 0;
    for (row = 0; row < BRICK_ROWS; ++row) {
        for (col = 0; col < BRICK_COLS; ++col) {
            remaining += g_app.game.bricks[row][col] ? 1 : 0;
        }
    }
    return remaining;
}

static void grant_reward_tier(int tier) {
    g_app.game.rewardTier = tier;
    apply_reward_profile();

    if (tier == 1) {
        set_notice(L"Milestone 1: widened paddle unlocked", 5000);
    } else if (tier == 2) {
        g_app.game.lives += 1;
        g_app.game.shieldCharges += 1;
        set_notice(L"Milestone 2: bonus life and shield charge unlocked", 5000);
    } else if (tier == 3) {
        set_notice(L"Milestone 3: score multiplier doubled", 5000);
    } else if (tier == 4) {
        g_app.game.shieldCharges += 1;
        set_notice(L"Milestone 4: turbo ball and extra shield unlocked", 5000);
    }
}

static void sync_rewards_from_cleanup(ULONGLONG totalDeleted) {
    while (g_app.game.rewardTier < MILESTONE_COUNT && totalDeleted >= kMilestones[g_app.game.rewardTier]) {
        grant_reward_tier(g_app.game.rewardTier + 1);
    }
}

static void promote_next_level(void) {
    g_app.game.level += 1;
    g_app.game.score += 1500 * g_app.game.scoreMultiplier;
    fill_bricks();
    reset_ball();
    set_notice(L"Board cleared: next sector loaded", 4000);
}

static void update_cpu_load(void) {
    FILETIME idleTime;
    FILETIME kernelTime;
    FILETIME userTime;

    if (!GetSystemTimes(&idleTime, &kernelTime, &userTime)) {
        return;
    }

    if (g_app.telemetry.cpuPrimed) {
        ULONGLONG idleDelta = filetime_to_ull(idleTime) - filetime_to_ull(g_app.telemetry.cpuIdle);
        ULONGLONG kernelDelta = filetime_to_ull(kernelTime) - filetime_to_ull(g_app.telemetry.cpuKernel);
        ULONGLONG userDelta = filetime_to_ull(userTime) - filetime_to_ull(g_app.telemetry.cpuUser);
        ULONGLONG totalDelta = kernelDelta + userDelta;
        ULONGLONG busyDelta = totalDelta > idleDelta ? totalDelta - idleDelta : 0;
        if (totalDelta > 0) {
            g_app.telemetry.cpuLoadPercent = (DWORD)((busyDelta * 100ULL) / totalDelta);
        }
    } else {
        g_app.telemetry.cpuPrimed = 1;
    }

    g_app.telemetry.cpuIdle = idleTime;
    g_app.telemetry.cpuKernel = kernelTime;
    g_app.telemetry.cpuUser = userTime;
}

static void refresh_telemetry_peaks(void) {
    if (g_app.sweep.memory.dwMemoryLoad > g_app.telemetry.peakMemoryLoad) {
        g_app.telemetry.peakMemoryLoad = g_app.sweep.memory.dwMemoryLoad;
    }
}

static int is_old_enough(const FILETIME *lastWriteUtc, int retentionDays) {
    ULONGLONG cutoff = now_filetime_ull();
    ULONGLONG target = filetime_to_ull(*lastWriteUtc);
    ULONGLONG ageWindow = (ULONGLONG)retentionDays * 24ULL * 60ULL * 60ULL * 10000000ULL;
    return target + ageWindow < cutoff;
}

static int should_delete_file(const WIN32_FIND_DATAW *findData, ULONGLONG fileSize, const SweepSettings *settings) {
    if (!settings->cleanTempEnabled) {
        return 0;
    }
    if (settings->aggressiveMode && fileSize == 0) {
        return 1;
    }
    return is_old_enough(&findData->ftLastWriteTime, settings->retentionDays);
}

static void scan_and_clean_directory(const wchar_t *directoryPath, const SweepSettings *settings) {
    wchar_t searchPattern[MAX_PATH * 4];
    WIN32_FIND_DATAW findData;
    HANDLE findHandle;

    swprintf(searchPattern, sizeof(searchPattern) / sizeof(wchar_t), L"%ls\\*", directoryPath);
    findHandle = FindFirstFileW(searchPattern, &findData);
    if (findHandle == INVALID_HANDLE_VALUE) {
        return;
    }

    do {
        wchar_t childPath[MAX_PATH * 4];
        int isDirectory;
        ULONGLONG fileSize;

        if (wcscmp(findData.cFileName, L".") == 0 || wcscmp(findData.cFileName, L"..") == 0) {
            continue;
        }

        swprintf(childPath, sizeof(childPath) / sizeof(wchar_t), L"%ls\\%ls", directoryPath, findData.cFileName);
        isDirectory = (findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) != 0;

        if ((findData.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT) != 0) {
            continue;
        }

        if (isDirectory) {
            EnterCriticalSection(&g_app.lock);
            g_app.sweep.directoriesVisited += 1;
            LeaveCriticalSection(&g_app.lock);
            scan_and_clean_directory(childPath, settings);
            if (settings->aggressiveMode) {
                RemoveDirectoryW(childPath);
            }
            continue;
        }

        fileSize = ((ULONGLONG)findData.nFileSizeHigh << 32) | (ULONGLONG)findData.nFileSizeLow;

        EnterCriticalSection(&g_app.lock);
        g_app.sweep.filesScanned += 1;
        g_app.sweep.bytesScanned += fileSize;
        sync_rewards_from_cleanup(g_app.telemetry.sessionBytesDeleted + g_app.sweep.bytesDeleted);
        LeaveCriticalSection(&g_app.lock);

        if (should_delete_file(&findData, fileSize, settings)) {
            if (DeleteFileW(childPath)) {
                EnterCriticalSection(&g_app.lock);
                g_app.sweep.filesDeleted += 1;
                g_app.sweep.bytesDeleted += fileSize;
                sync_rewards_from_cleanup(g_app.telemetry.sessionBytesDeleted + g_app.sweep.bytesDeleted);
                LeaveCriticalSection(&g_app.lock);
            }
        }
    } while (FindNextFileW(findHandle, &findData));

    FindClose(findHandle);
}

static DWORD WINAPI sweep_thread_proc(LPVOID unused) {
    SweepSettings settings;
    DWORD driveMask;
    int driveCount = 0;
    wchar_t tempPath[MAX_PATH];
    FILETIME startedAt;
    DWORD lowSpaceAlerts = 0;
    DWORD hottestPercent = 0;
    wchar_t hottestRoot[4] = L"---";
    (void)unused;

    EnterCriticalSection(&g_app.lock);
    settings = g_app.settings;
    ZeroMemory(&g_app.sweep, sizeof(g_app.sweep));
    g_app.sweep.memory.dwLength = sizeof(g_app.sweep.memory);
    LeaveCriticalSection(&g_app.lock);

    set_phase(L"Collecting memory snapshot");
    GetSystemTimeAsFileTime(&startedAt);
    GlobalMemoryStatusEx(&g_app.sweep.memory);

    EnterCriticalSection(&g_app.lock);
    g_app.sweep.startedAt = startedAt;
    LeaveCriticalSection(&g_app.lock);

    set_phase(L"Inspecting storage volumes");
    driveMask = GetLogicalDrives();
    for (int index = 0; index < 26 && driveCount < DRIVE_LIMIT; ++index) {
        wchar_t root[] = L"A:\\";
        ULARGE_INTEGER freeBytesAvailable;
        ULARGE_INTEGER totalBytes;
        ULARGE_INTEGER totalFreeBytes;
        UINT driveType;
        DWORD usedPercent;
        if ((driveMask & (1u << index)) == 0) {
            continue;
        }
        root[0] = (wchar_t)(L'A' + index);
        driveType = GetDriveTypeW(root);
        if (driveType != DRIVE_FIXED && driveType != DRIVE_REMOVABLE) {
            continue;
        }
        if (!GetDiskFreeSpaceExW(root, &freeBytesAvailable, &totalBytes, &totalFreeBytes)) {
            continue;
        }

        usedPercent = totalBytes.QuadPart > 0
            ? (DWORD)(((totalBytes.QuadPart - totalFreeBytes.QuadPart) * 100ULL) / totalBytes.QuadPart)
            : 0;

        if (usedPercent >= 85 || totalFreeBytes.QuadPart < (20ULL * 1024ULL * 1024ULL * 1024ULL)) {
            lowSpaceAlerts += 1;
        }
        if (usedPercent >= hottestPercent) {
            hottestPercent = usedPercent;
            wcsncpy(hottestRoot, root, 4);
        }

        EnterCriticalSection(&g_app.lock);
        wcsncpy(g_app.sweep.drives[driveCount].root, root, 3);
        g_app.sweep.drives[driveCount].root[3] = L'\0';
        g_app.sweep.drives[driveCount].totalBytes = totalBytes.QuadPart;
        g_app.sweep.drives[driveCount].freeBytes = totalFreeBytes.QuadPart;
        g_app.sweep.drives[driveCount].driveType = driveType;
        driveCount += 1;
        g_app.sweep.driveCount = driveCount;
        LeaveCriticalSection(&g_app.lock);
    }

    set_phase(L"Scanning temp storage");
    if (settings.cleanTempEnabled && GetTempPathW(MAX_PATH, tempPath) > 0) {
        EnterCriticalSection(&g_app.lock);
        wcsncpy(g_app.sweep.tempPath, tempPath, MAX_PATH - 1);
        g_app.sweep.tempPath[MAX_PATH - 1] = L'\0';
        LeaveCriticalSection(&g_app.lock);
        scan_and_clean_directory(tempPath, &settings);
    }

    set_phase(L"Finalizing sweep results");
    EnterCriticalSection(&g_app.lock);
    GetSystemTimeAsFileTime(&g_app.sweep.finishedAt);
    g_app.sweep.complete = 1;
    g_app.telemetry.sweepCount += 1;
    g_app.telemetry.sessionBytesDeleted += g_app.sweep.bytesDeleted;
    if (g_app.sweep.bytesDeleted > g_app.telemetry.bestSweepBytesDeleted) {
        g_app.telemetry.bestSweepBytesDeleted = g_app.sweep.bytesDeleted;
    }
    g_app.telemetry.lastSweepDurationMs =
        (filetime_to_ull(g_app.sweep.finishedAt) - filetime_to_ull(g_app.sweep.startedAt)) / 10000ULL;
    g_app.telemetry.lowSpaceAlerts = lowSpaceAlerts;
    g_app.telemetry.hottestDrivePercentUsed = hottestPercent;
    wcsncpy(g_app.telemetry.hottestDriveRoot, hottestRoot, 4);
    sync_rewards_from_cleanup(g_app.telemetry.sessionBytesDeleted);
    if (g_app.settings.autoSweep) {
        g_app.telemetry.autoSweepAtTick = GetTickCount64() + AUTO_SWEEP_DELAY_MS;
    } else {
        g_app.telemetry.autoSweepAtTick = 0;
    }
    LeaveCriticalSection(&g_app.lock);

    set_phase(L"Sweep complete");
    InterlockedExchange(&g_app.sweepRunning, 0);
    if (g_app.hwnd != NULL) {
        PostMessageW(g_app.hwnd, STATUS_MESSAGE, 0, 0);
    }
    return 0;
}

static void start_sweep(void) {
    HANDLE threadHandle;
    if (InterlockedCompareExchange(&g_app.sweepRunning, 1, 0) != 0) {
        return;
    }
    if (g_app.workerThread != NULL) {
        CloseHandle(g_app.workerThread);
        g_app.workerThread = NULL;
    }
    threadHandle = CreateThread(NULL, 0, sweep_thread_proc, NULL, 0, NULL);
    if (threadHandle == NULL) {
        InterlockedExchange(&g_app.sweepRunning, 0);
        set_phase(L"Sweep failed to start");
        return;
    }
    g_app.workerThread = threadHandle;
}

static void draw_text_line(HDC hdc, int x, int y, COLORREF color, const wchar_t *text) {
    SetTextColor(hdc, color);
    TextOutW(hdc, x, y, text, (int)wcslen(text));
}

static void draw_card(HDC hdc, RECT rect, COLORREF background, COLORREF border, const wchar_t *title, const wchar_t *body) {
    HBRUSH brush = CreateSolidBrush(background);
    HPEN pen = CreatePen(PS_SOLID, 1, border);
    HGDIOBJ oldBrush = SelectObject(hdc, brush);
    HGDIOBJ oldPen = SelectObject(hdc, pen);
    Rectangle(hdc, rect.left, rect.top, rect.right, rect.bottom);
    SetBkMode(hdc, TRANSPARENT);
    draw_text_line(hdc, rect.left + 12, rect.top + 10, RGB(245, 248, 255), title);
    draw_text_line(hdc, rect.left + 12, rect.top + 34, RGB(190, 228, 223), body);
    SelectObject(hdc, oldBrush);
    SelectObject(hdc, oldPen);
    DeleteObject(brush);
    DeleteObject(pen);
}

static void paint_ui(HDC hdc, RECT clientRect) {
    RECT backRect = clientRect;
    HBRUSH background = CreateSolidBrush(RGB(12, 18, 28));
    HFONT headerFont;
    HFONT bodyFont;
    HFONT monoFont;
    HGDIOBJ oldFont;
    wchar_t buffer[320];
    wchar_t bytesBufferA[64];
    wchar_t bytesBufferB[64];
    wchar_t bytesBufferC[64];
    wchar_t bytesBufferD[64];
    wchar_t phaseBuffer[96];
    wchar_t noticeBuffer[96];
    MEMORYSTATUSEX memory;
    FILETIME startedAt;
    DriveInfo drives[DRIVE_LIMIT];
    SweepSettings settings;
    SweepTelemetry telemetry;
    int driveCount;
    DWORD filesScanned;
    DWORD filesDeleted;
    DWORD directoriesVisited;
    ULONGLONG bytesScanned;
    ULONGLONG bytesDeleted;
    ULONGLONG sessionDeletedDisplay;
    int sweepComplete;
    int running;
    RECT cardRect;
    RECT gameRect = { 40, 292, 996, 706 };
    const COLORREF brickColors[BRICK_ROWS] = {
        RGB(255, 120, 82), RGB(255, 176, 76), RGB(252, 220, 92),
        RGB(126, 212, 92), RGB(89, 190, 230), RGB(155, 132, 255)
    };

    FillRect(hdc, &backRect, background);
    DeleteObject(background);

    headerFont = CreateFontW(32, 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE, DEFAULT_CHARSET,
        OUT_OUTLINE_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY, VARIABLE_PITCH, L"Segoe UI");
    bodyFont = CreateFontW(18, 0, 0, 0, FW_MEDIUM, FALSE, FALSE, FALSE, DEFAULT_CHARSET,
        OUT_OUTLINE_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY, VARIABLE_PITCH, L"Segoe UI");
    monoFont = CreateFontW(15, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE, DEFAULT_CHARSET,
        OUT_OUTLINE_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY, FIXED_PITCH, L"Consolas");

    EnterCriticalSection(&g_app.lock);
    memory = g_app.sweep.memory;
    settings = g_app.settings;
    telemetry = g_app.telemetry;
    startedAt = g_app.sweep.startedAt;
    driveCount = g_app.sweep.driveCount;
    for (int index = 0; index < driveCount; ++index) {
        drives[index] = g_app.sweep.drives[index];
    }
    wcsncpy(phaseBuffer, g_app.sweep.phase, sizeof(phaseBuffer) / sizeof(wchar_t) - 1);
    phaseBuffer[(sizeof(phaseBuffer) / sizeof(wchar_t)) - 1] = L'\0';
    wcsncpy(noticeBuffer, g_app.game.notice, sizeof(noticeBuffer) / sizeof(wchar_t) - 1);
    noticeBuffer[(sizeof(noticeBuffer) / sizeof(wchar_t)) - 1] = L'\0';
    filesScanned = g_app.sweep.filesScanned;
    filesDeleted = g_app.sweep.filesDeleted;
    directoriesVisited = g_app.sweep.directoriesVisited;
    bytesScanned = g_app.sweep.bytesScanned;
    bytesDeleted = g_app.sweep.bytesDeleted;
    sweepComplete = g_app.sweep.complete;
    LeaveCriticalSection(&g_app.lock);
    running = (int)InterlockedCompareExchange(&g_app.sweepRunning, 0, 0);
    sessionDeletedDisplay = telemetry.sessionBytesDeleted;
    if (running && !sweepComplete) {
        sessionDeletedDisplay += bytesDeleted;
    }

    SetBkMode(hdc, TRANSPARENT);
    SetTextColor(hdc, RGB(242, 247, 255));
    oldFont = SelectObject(hdc, headerFont);
    TextOutW(hdc, 36, 24, APP_TITLE, (int)wcslen(APP_TITLE));
    SelectObject(hdc, bodyFont);
    draw_text_line(hdc, 38, 62, RGB(151, 198, 216), L"Operations dashboard above. Breakout retention challenge below.");

    cardRect.left = 38;
    cardRect.top = 96;
    cardRect.right = 270;
    cardRect.bottom = 176;
    swprintf(buffer, sizeof(buffer) / sizeof(wchar_t), L"RAM %lu%%   Peak %lu%%", memory.dwMemoryLoad, telemetry.peakMemoryLoad);
    draw_card(hdc, cardRect, RGB(25, 36, 52), RGB(57, 88, 116), L"RAM Pulse", buffer);

    cardRect.left = 286;
    cardRect.right = 518;
    format_bytes(bytesDeleted, bytesBufferA, sizeof(bytesBufferA) / sizeof(wchar_t));
    format_bytes(telemetry.bestSweepBytesDeleted, bytesBufferB, sizeof(bytesBufferB) / sizeof(wchar_t));
    swprintf(buffer, sizeof(buffer) / sizeof(wchar_t), L"Live %ls   Best %ls", bytesBufferA, bytesBufferB);
    draw_card(hdc, cardRect, RGB(28, 42, 48), RGB(70, 126, 116), L"Cleanup Yield", buffer);

    cardRect.left = 534;
    cardRect.right = 766;
    swprintf(buffer, sizeof(buffer) / sizeof(wchar_t), L"CPU %lu%%   Sweeps %lu", telemetry.cpuLoadPercent, telemetry.sweepCount);
    draw_card(hdc, cardRect, RGB(39, 37, 60), RGB(83, 104, 164), L"Live Telemetry", buffer);

    cardRect.left = 782;
    cardRect.right = 996;
    if (phaseBuffer[0] == L'\0') {
        wcsncpy(phaseBuffer, L"Press R to run a sweep", sizeof(phaseBuffer) / sizeof(wchar_t) - 1);
        phaseBuffer[(sizeof(phaseBuffer) / sizeof(wchar_t)) - 1] = L'\0';
    }
    draw_card(hdc, cardRect, RGB(47, 31, 45), RGB(136, 84, 129), L"Sweep Phase", phaseBuffer);

    cardRect.left = 38;
    cardRect.top = 186;
    cardRect.right = 518;
    cardRect.bottom = 272;
    format_bytes(sessionDeletedDisplay, bytesBufferC, sizeof(bytesBufferC) / sizeof(wchar_t));
    swprintf(buffer, sizeof(buffer) / sizeof(wchar_t),
        L"Plan: %d-day retention  Auto %ls  Aggressive %ls  Session reclaimed %ls",
        settings.retentionDays,
        settings.autoSweep ? L"on" : L"off",
        settings.aggressiveMode ? L"on" : L"off",
        bytesBufferC);
    draw_card(hdc, cardRect, RGB(22, 34, 42), RGB(57, 104, 114), L"Service Deck", buffer);

    cardRect.left = 534;
    cardRect.right = 996;
    cardRect.bottom = 272;
    if (running) {
        swprintf(buffer, sizeof(buffer) / sizeof(wchar_t),
            L"Scanning %lu files across %lu folders. Deleted %lu files. Duration %llums. Alerts %lu.",
            filesScanned,
            directoriesVisited,
            filesDeleted,
            (now_filetime_ull() - filetime_to_ull(startedAt)) / 10000ULL,
            telemetry.lowSpaceAlerts);
    } else if (sweepComplete) {
        format_bytes(bytesScanned, bytesBufferD, sizeof(bytesBufferD) / sizeof(wchar_t));
        swprintf(buffer, sizeof(buffer) / sizeof(wchar_t),
            L"Last sweep reviewed %ls in %llums. Hottest drive %ls at %lu%% used.",
            bytesBufferD,
            telemetry.lastSweepDurationMs,
            telemetry.hottestDriveRoot,
            telemetry.hottestDrivePercentUsed);
    } else {
        swprintf(buffer, sizeof(buffer) / sizeof(wchar_t),
            L"Ready. Keys: 1/2/3 retention, A auto-sweep, G aggressive mode, T temp cleanup, R run.");
    }
    draw_card(hdc, cardRect, RGB(16, 28, 38), RGB(61, 86, 104), L"Operator Feed", buffer);

    if (driveCount > 0) {
        wchar_t driveSummary[320];
        wchar_t freeBuffer[64];
        wchar_t totalBuffer[64];
        format_bytes(drives[0].freeBytes, freeBuffer, sizeof(freeBuffer) / sizeof(wchar_t));
        format_bytes(drives[0].totalBytes, totalBuffer, sizeof(totalBuffer) / sizeof(wchar_t));
        swprintf(driveSummary, sizeof(driveSummary) / sizeof(wchar_t),
            L"Lead volume %ls free %ls / %ls   low-space alerts %lu",
            drives[0].root,
            freeBuffer,
            totalBuffer,
            telemetry.lowSpaceAlerts);
        draw_text_line(hdc, 546, 246, RGB(210, 226, 238), driveSummary);
    }

    {
        HBRUSH gameBrush = CreateSolidBrush(RGB(7, 11, 18));
        HPEN borderPen = CreatePen(PS_SOLID, 1, RGB(64, 96, 120));
        HGDIOBJ oldBrush = SelectObject(hdc, gameBrush);
        HGDIOBJ oldPen = SelectObject(hdc, borderPen);
        Rectangle(hdc, gameRect.left, gameRect.top, gameRect.right, gameRect.bottom);
        SelectObject(hdc, oldBrush);
        SelectObject(hdc, oldPen);
        DeleteObject(gameBrush);
        DeleteObject(borderPen);
    }

    oldFont = SelectObject(hdc, bodyFont);
    swprintf(buffer, sizeof(buffer) / sizeof(wchar_t),
        L"Score %d   Lives %d   Level %d   Shields %d   Mult x%d   Perk Tier %d",
        g_app.game.score,
        g_app.game.lives,
        g_app.game.level,
        g_app.game.shieldCharges,
        g_app.game.scoreMultiplier,
        g_app.game.rewardTier);
    draw_text_line(hdc, 58, 308, RGB(226, 233, 242), buffer);

    if (noticeBuffer[0] != L'\0' && GetTickCount64() < g_app.game.noticeUntilTick) {
        draw_text_line(hdc, 58, 336, RGB(255, 214, 118), noticeBuffer);
    }

    for (int row = 0; row < BRICK_ROWS; ++row) {
        for (int col = 0; col < BRICK_COLS; ++col) {
            if (g_app.game.bricks[row][col]) {
                const float brickGap = 8.0f;
                const float brickWidth = (956.0f - ((float)BRICK_COLS + 1.0f) * brickGap) / (float)BRICK_COLS;
                const float brickHeight = 24.0f;
                const int left = (int)(40.0f + brickGap + (brickWidth + brickGap) * (float)col);
                const int top = (int)(372.0f + (brickHeight + brickGap) * (float)row);
                RECT brickRect = { left, top, left + (int)brickWidth, top + (int)brickHeight };
                HBRUSH brickBrush = CreateSolidBrush(brickColors[row]);
                FillRect(hdc, &brickRect, brickBrush);
                DeleteObject(brickBrush);
            }
        }
    }

    {
        RECT paddleRect = {
            (int)g_app.game.paddleX,
            292 + 414 - 34,
            (int)(g_app.game.paddleX + g_app.game.paddleWidth),
            292 + 414 - 18
        };
        HBRUSH paddleBrush = CreateSolidBrush(RGB(210, 238, 250));
        FillRect(hdc, &paddleRect, paddleBrush);
        DeleteObject(paddleBrush);
    }

    {
        HBRUSH ballBrush = CreateSolidBrush(RGB(255, 110, 110));
        HGDIOBJ oldBrush = SelectObject(hdc, ballBrush);
        HGDIOBJ oldPen = SelectObject(hdc, GetStockObject(NULL_PEN));
        Ellipse(hdc,
            (int)(g_app.game.ballX - 8.0f),
            (int)(g_app.game.ballY - 8.0f),
            (int)(g_app.game.ballX + 8.0f),
            (int)(g_app.game.ballY + 8.0f));
        SelectObject(hdc, oldBrush);
        SelectObject(hdc, oldPen);
        DeleteObject(ballBrush);
    }

    SelectObject(hdc, monoFont);
    draw_text_line(hdc, 58, 724, RGB(151, 198, 216),
        L"Controls: Left/Right move, Space launch, N reset game, R run sweep, 1/2/3 retention, A auto, G aggressive, T temp toggle.");

    SelectObject(hdc, oldFont);
    DeleteObject(headerFont);
    DeleteObject(bodyFont);
    DeleteObject(monoFont);
}

static void on_paint(HWND hwnd) {
    PAINTSTRUCT ps;
    RECT clientRect;
    HDC hdc = BeginPaint(hwnd, &ps);
    HDC memdc;
    HBITMAP bitmap;
    HGDIOBJ oldBitmap;

    GetClientRect(hwnd, &clientRect);
    memdc = CreateCompatibleDC(hdc);
    bitmap = CreateCompatibleBitmap(hdc, clientRect.right - clientRect.left, clientRect.bottom - clientRect.top);
    oldBitmap = SelectObject(memdc, bitmap);

    paint_ui(memdc, clientRect);
    BitBlt(hdc, 0, 0, clientRect.right - clientRect.left, clientRect.bottom - clientRect.top, memdc, 0, 0, SRCCOPY);

    SelectObject(memdc, oldBitmap);
    DeleteObject(bitmap);
    DeleteDC(memdc);
    EndPaint(hwnd, &ps);
}

static void update_game(float dt) {
    const float areaLeft = 40.0f;
    const float areaTop = 292.0f;
    const float areaWidth = 956.0f;
    const float areaHeight = 414.0f;
    const float paddleY = areaTop + areaHeight - 34.0f;
    const float ballRadius = 8.0f;
    const float paddleSpeed = 430.0f;
    const float brickGap = 8.0f;
    const float brickWidth = (areaWidth - ((float)BRICK_COLS + 1.0f) * brickGap) / (float)BRICK_COLS;
    const float brickHeight = 24.0f;
    const float brickTop = areaTop + 80.0f;
    int row;
    int col;

    if (g_app.game.moveLeft) {
        g_app.game.paddleX -= paddleSpeed * dt;
    }
    if (g_app.game.moveRight) {
        g_app.game.paddleX += paddleSpeed * dt;
    }
    if (g_app.game.paddleX < areaLeft) {
        g_app.game.paddleX = areaLeft;
    }
    if (g_app.game.paddleX + g_app.game.paddleWidth > areaLeft + areaWidth) {
        g_app.game.paddleX = areaLeft + areaWidth - g_app.game.paddleWidth;
    }

    if (!g_app.game.ballLaunched) {
        g_app.game.ballX = g_app.game.paddleX + g_app.game.paddleWidth / 2.0f;
        g_app.game.ballY = paddleY - ballRadius - 2.0f;
        return;
    }

    g_app.game.ballX += g_app.game.ballVX * dt;
    g_app.game.ballY += g_app.game.ballVY * dt;

    if (g_app.game.ballX - ballRadius <= areaLeft) {
        g_app.game.ballX = areaLeft + ballRadius;
        g_app.game.ballVX = -g_app.game.ballVX;
    }
    if (g_app.game.ballX + ballRadius >= areaLeft + areaWidth) {
        g_app.game.ballX = areaLeft + areaWidth - ballRadius;
        g_app.game.ballVX = -g_app.game.ballVX;
    }
    if (g_app.game.ballY - ballRadius <= areaTop) {
        g_app.game.ballY = areaTop + ballRadius;
        g_app.game.ballVY = -g_app.game.ballVY;
    }

    if (g_app.game.ballY + ballRadius >= paddleY &&
        g_app.game.ballY + ballRadius <= paddleY + 18.0f &&
        g_app.game.ballX >= g_app.game.paddleX &&
        g_app.game.ballX <= g_app.game.paddleX + g_app.game.paddleWidth &&
        g_app.game.ballVY > 0.0f) {
        float center = g_app.game.paddleX + g_app.game.paddleWidth / 2.0f;
        float offset = (g_app.game.ballX - center) / (g_app.game.paddleWidth / 2.0f);
        g_app.game.ballY = paddleY - ballRadius;
        g_app.game.ballVY = -g_app.game.ballVY;
        g_app.game.ballVX = (280.0f + (float)(g_app.game.level - 1) * 20.0f) * offset * g_app.game.speedScale;
    }

    for (row = 0; row < BRICK_ROWS; ++row) {
        for (col = 0; col < BRICK_COLS; ++col) {
            float bx;
            float by;
            float left;
            float right;
            float top;
            float bottom;
            if (!g_app.game.bricks[row][col]) {
                continue;
            }
            bx = areaLeft + brickGap + (brickWidth + brickGap) * (float)col;
            by = brickTop + (brickHeight + brickGap) * (float)row;
            left = bx;
            right = bx + brickWidth;
            top = by;
            bottom = by + brickHeight;

            if (g_app.game.ballX + ballRadius >= left &&
                g_app.game.ballX - ballRadius <= right &&
                g_app.game.ballY + ballRadius >= top &&
                g_app.game.ballY - ballRadius <= bottom) {
                g_app.game.bricks[row][col] = 0;
                g_app.game.score += (100 + g_app.game.combo * 10) * g_app.game.scoreMultiplier;
                g_app.game.combo += 1;
                if (g_app.game.ballY < top || g_app.game.ballY > bottom) {
                    g_app.game.ballVY = -g_app.game.ballVY;
                } else {
                    g_app.game.ballVX = -g_app.game.ballVX;
                }
                if (count_remaining_bricks() == 0) {
                    promote_next_level();
                }
                return;
            }
        }
    }

    if (g_app.game.ballY - ballRadius > areaTop + areaHeight) {
        if (g_app.game.shieldCharges > 0) {
            g_app.game.shieldCharges -= 1;
            reset_ball();
            set_notice(L"Shield charge spent: ball restored", 3500);
            return;
        }
        g_app.game.lives -= 1;
        if (g_app.game.lives <= 0) {
            reset_game();
            set_notice(L"New run armed", 3000);
        } else {
            reset_ball();
        }
    }
}

static void advance_frame(void) {
    ULONGLONG now = GetTickCount64();
    float dt;

    update_cpu_load();
    refresh_telemetry_peaks();

    if (g_app.lastTick == 0) {
        g_app.lastTick = now;
        return;
    }

    if (!InterlockedCompareExchange(&g_app.sweepRunning, 0, 0) &&
        g_app.settings.autoSweep &&
        g_app.telemetry.autoSweepAtTick != 0 &&
        now >= g_app.telemetry.autoSweepAtTick) {
        g_app.telemetry.autoSweepAtTick = 0;
        start_sweep();
    }

    dt = (float)(now - g_app.lastTick) / 1000.0f;
    if (dt > 0.033f) {
        dt = 0.033f;
    }
    g_app.lastTick = now;

    if (g_app.game.noticeUntilTick != 0 && now >= g_app.game.noticeUntilTick) {
        g_app.game.notice[0] = L'\0';
        g_app.game.noticeUntilTick = 0;
    }

    update_game(dt);
    InvalidateRect(g_app.hwnd, NULL, FALSE);
}

static void toggle_bool(int *value, const wchar_t *enabledText, const wchar_t *disabledText) {
    *value = !*value;
    if (*value) {
        set_notice(enabledText, 3000);
    } else {
        set_notice(disabledText, 3000);
    }
}

static LRESULT CALLBACK window_proc(HWND hwnd, UINT message, WPARAM wParam, LPARAM lParam) {
    (void)lParam;
    switch (message) {
    case WM_CREATE:
        g_app.hwnd = hwnd;
        reset_game();
        start_sweep();
        SetTimer(hwnd, FRAME_TIMER_ID, FRAME_INTERVAL_MS, NULL);
        return 0;
    case WM_TIMER:
        if (wParam == FRAME_TIMER_ID) {
            advance_frame();
        }
        return 0;
    case WM_KEYDOWN:
        switch (wParam) {
        case VK_LEFT:
            g_app.game.moveLeft = 1;
            break;
        case VK_RIGHT:
            g_app.game.moveRight = 1;
            break;
        case VK_SPACE:
            if (!g_app.game.ballLaunched) {
                g_app.game.ballLaunched = 1;
            }
            break;
        case 'N':
            reset_game();
            set_notice(L"Gameplay state reset", 2500);
            break;
        case 'R':
            start_sweep();
            break;
        case '1':
            g_app.settings.retentionDays = 3;
            set_notice(L"Retention window set to 3 days", 3000);
            break;
        case '2':
            g_app.settings.retentionDays = 7;
            set_notice(L"Retention window set to 7 days", 3000);
            break;
        case '3':
            g_app.settings.retentionDays = 14;
            set_notice(L"Retention window set to 14 days", 3000);
            break;
        case 'A':
            toggle_bool(&g_app.settings.autoSweep, L"Auto-sweep enabled", L"Auto-sweep disabled");
            if (!g_app.settings.autoSweep) {
                g_app.telemetry.autoSweepAtTick = 0;
            }
            break;
        case 'G':
            toggle_bool(&g_app.settings.aggressiveMode, L"Aggressive cleanup enabled", L"Aggressive cleanup disabled");
            break;
        case 'T':
            toggle_bool(&g_app.settings.cleanTempEnabled, L"Temp cleanup enabled", L"Temp cleanup disabled");
            break;
        }
        return 0;
    case WM_KEYUP:
        switch (wParam) {
        case VK_LEFT:
            g_app.game.moveLeft = 0;
            break;
        case VK_RIGHT:
            g_app.game.moveRight = 0;
            break;
        }
        return 0;
    case STATUS_MESSAGE:
        InvalidateRect(hwnd, NULL, FALSE);
        return 0;
    case WM_PAINT:
        on_paint(hwnd);
        return 0;
    case WM_ERASEBKGND:
        return 1;
    case WM_DESTROY:
        KillTimer(hwnd, FRAME_TIMER_ID);
        PostQuitMessage(0);
        return 0;
    default:
        return DefWindowProcW(hwnd, message, wParam, lParam);
    }
}

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE previousInstance, PWSTR commandLine, int showCommand) {
    WNDCLASSW windowClass;
    HWND hwnd;
    MSG message;
    (void)previousInstance;
    (void)commandLine;

    ZeroMemory(&g_app, sizeof(g_app));
    InitializeCriticalSection(&g_app.lock);

    g_app.settings.retentionDays = 7;
    g_app.settings.autoSweep = 0;
    g_app.settings.aggressiveMode = 0;
    g_app.settings.cleanTempEnabled = 1;

    ZeroMemory(&windowClass, sizeof(windowClass));
    windowClass.lpfnWndProc = window_proc;
    windowClass.hInstance = instance;
    windowClass.lpszClassName = APP_CLASS_NAME;
    windowClass.hCursor = LoadCursorW(NULL, IDC_ARROW);
    windowClass.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);

    if (!RegisterClassW(&windowClass)) {
        DeleteCriticalSection(&g_app.lock);
        return 1;
    }

    hwnd = CreateWindowExW(
        0,
        APP_CLASS_NAME,
        APP_TITLE,
        WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT,
        CW_USEDEFAULT,
        APP_WIDTH,
        APP_HEIGHT,
        NULL,
        NULL,
        instance,
        NULL);

    if (hwnd == NULL) {
        DeleteCriticalSection(&g_app.lock);
        return 1;
    }

    ShowWindow(hwnd, showCommand);
    UpdateWindow(hwnd);

    while (GetMessageW(&message, NULL, 0, 0) > 0) {
        TranslateMessage(&message);
        DispatchMessageW(&message);
    }

    if (g_app.workerThread != NULL) {
        WaitForSingleObject(g_app.workerThread, 3000);
        CloseHandle(g_app.workerThread);
    }
    DeleteCriticalSection(&g_app.lock);
    return (int)message.wParam;
}