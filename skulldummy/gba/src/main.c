#if defined(__INTELLISENSE__)
#include "C:/devkitPro/libgba/include/gba.h"
#else
#include <gba.h>
#endif
#include "skulldummy_assets.h"
#include <stdbool.h>
#include <stdint.h>

#define SCREEN_W 240
#define SCREEN_H 160

#define RGB15(r, g, b) ((r) | ((g) << 5) | ((b) << 10))
#define CLAMP_MIN(a, b) ((a) < (b) ? (b) : (a))
#define CLAMP_MAX(a, b) ((a) > (b) ? (b) : (a))

typedef uint16_t Color;

typedef enum BossMode {
    BOSS_IDLE = 0,
    BOSS_ADVANCE = 1,
    BOSS_COMBO = 2,
} BossMode;

typedef enum PromptType {
    PROMPT_UP = 0,
    PROMPT_DOWN = 1,
    PROMPT_LEFT = 2,
    PROMPT_RIGHT = 3,
    PROMPT_A = 4,
    PROMPT_B = 5,
} PromptType;

typedef enum SfxType {
    SFX_NONE = 0,
    SFX_WINDOW = 1,
    SFX_SUCCESS = 2,
    SFX_FAIL = 3,
    SFX_RELIC = 4,
    SFX_WIN = 5,
    SFX_LOSE = 6,
} SfxType;

typedef struct Prompt {
    PromptType type;
    int reward;
    int penalty;
} Prompt;

typedef struct GameState {
    int playerHealth;
    int bossHealth;
    int zoneIndex;
    int gearCount;
    int comboCount;
    int relicCharge;
    int tick;
    int windowTimer;
    int promptIndex;
    BossMode bossMode;
    bool qteWindowOpen;
    bool encounterResolved;
    bool playerWon;
} GameState;

typedef struct Note {
    uint16_t hz;
    uint8_t frames;
    uint8_t volume;
    uint8_t duty;
} Note;

typedef struct AudioState {
    int melodyTimer;
    int melodyIndex;
    int bassTimer;
    int bassIndex;
    int sfxTimer;
    int sfxIndex;
    SfxType activeSfx;
} AudioState;

static volatile Color *const videoBuffer = (volatile Color *)0x06000000;
static AudioState audioState;

static const Note kMelodyLoop[] = {
    { 294, 8, 10, 2 },
    { 349, 8, 9, 2 },
    { 440, 8, 10, 2 },
    { 587, 12, 11, 1 },
    { 523, 6, 10, 1 },
    { 440, 6, 9, 2 },
    { 349, 8, 9, 2 },
    { 294, 10, 10, 3 },
    { 294, 6, 8, 2 },
    { 349, 6, 8, 2 },
    { 392, 6, 9, 2 },
    { 440, 10, 10, 1 },
    { 392, 6, 9, 2 },
    { 349, 6, 8, 2 },
    { 330, 8, 8, 2 },
    { 294, 12, 10, 3 },
};

static const Note kBassLoop[] = {
    { 147, 16, 7, 3 },
    { 147, 8, 6, 3 },
    { 175, 8, 6, 2 },
    { 220, 16, 7, 2 },
    { 147, 16, 7, 3 },
    { 196, 8, 6, 2 },
    { 220, 8, 6, 2 },
    { 123, 16, 7, 3 },
};

static const Note kWindowSfx[] = {
    { 523, 3, 8, 1 },
    { 659, 4, 8, 1 },
};

static const Note kSuccessSfx[] = {
    { 784, 3, 9, 1 },
    { 988, 4, 10, 1 },
    { 1175, 5, 10, 1 },
};

static const Note kFailSfx[] = {
    { 247, 4, 9, 3 },
    { 220, 5, 8, 3 },
    { 196, 7, 7, 3 },
};

static const Note kRelicSfx[] = {
    { 440, 2, 8, 1 },
    { 587, 2, 9, 1 },
    { 784, 2, 10, 1 },
    { 1175, 6, 11, 1 },
};

static const Note kWinSfx[] = {
    { 587, 4, 9, 1 },
    { 784, 4, 10, 1 },
    { 988, 5, 10, 1 },
    { 1175, 8, 11, 1 },
};

static const Note kLoseSfx[] = {
    { 330, 4, 8, 3 },
    { 262, 5, 8, 3 },
    { 220, 6, 7, 3 },
    { 165, 8, 7, 3 },
};

static void drawBitmapFull(const uint16_t *bitmap) {
    for (int index = 0; index < SCREEN_W * SCREEN_H; ++index) {
        videoBuffer[index] = bitmap[index];
    }
}

static void drawBitmapTransparent(const uint16_t *bitmap, int width, int height, int dstX, int dstY) {
    for (int py = 0; py < height; ++py) {
        int screenY = dstY + py;
        if ((unsigned)screenY >= SCREEN_H) continue;
        for (int px = 0; px < width; ++px) {
            int screenX = dstX + px;
            if ((unsigned)screenX >= SCREEN_W) continue;
            uint16_t value = bitmap[py * width + px];
            if (value == SKULLDUMMY_TRANSPARENT_COLOR) continue;
            videoBuffer[screenY * SCREEN_W + screenX] = value;
        }
    }
}

static const Prompt kPrompts[] = {
    { PROMPT_UP, 12, 8 },
    { PROMPT_DOWN, 10, 7 },
    { PROMPT_LEFT, 9, 6 },
    { PROMPT_RIGHT, 9, 6 },
    { PROMPT_A, 14, 8 },
    { PROMPT_B, 11, 7 },
};

static const uint8_t kGlyphs[18][7] = {
    { 14, 17, 17, 31, 17, 17, 17 },
    { 30, 17, 17, 30, 17, 17, 30 },
    { 14, 17, 16, 16, 16, 17, 14 },
    { 30, 17, 17, 17, 17, 17, 30 },
    { 31, 16, 16, 30, 16, 16, 31 },
    { 31, 16, 16, 30, 16, 16, 16 },
    { 14, 17, 16, 23, 17, 17, 14 },
    { 17, 17, 17, 31, 17, 17, 17 },
    { 31, 4, 4, 4, 4, 4, 31 },
    { 1, 1, 1, 1, 17, 17, 14 },
    { 17, 18, 20, 24, 20, 18, 17 },
    { 16, 16, 16, 16, 16, 16, 31 },
    { 14, 17, 19, 21, 25, 17, 14 },
    { 4, 12, 4, 4, 4, 4, 14 },
    { 14, 17, 1, 2, 4, 8, 31 },
    { 31, 1, 2, 6, 1, 17, 14 },
    { 2, 6, 10, 18, 31, 2, 2 },
    { 31, 16, 30, 1, 1, 17, 14 },
};

static const char kGlyphMap[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ012345";

static int prompt_counter = 0;

static uint16_t squareFreqFromHz(int hz) {
    if (hz <= 0) return 0;
    int reg = 2048 - (131072 / hz);
    if (reg < 0) reg = 0;
    if (reg > 2047) reg = 2047;
    return (uint16_t)reg;
}

static void playSquare1(Note note) {
    if (note.hz == 0 || note.volume == 0) {
        SQR1CTRL = 0;
        return;
    }
    SQR1SWEEP = SQR1SWEEP_OFF;
    SQR1CTRL = SQR_VOL(note.volume) | SQR_DUTY(note.duty & 3) | 0x0008;
    SQR1FREQ = TRIFREQ_RESET | squareFreqFromHz(note.hz);
}

static void playSquare2(Note note) {
    if (note.hz == 0 || note.volume == 0) {
        SQR2CTRL = 0;
        return;
    }
    SQR2CTRL = SQR_VOL(note.volume) | SQR_DUTY(note.duty & 3) | 0x0008;
    SQR2FREQ = TRIFREQ_RESET | squareFreqFromHz(note.hz);
}

static void initAudio(void) {
    SNDSTAT = SNDSTAT_ENABLE;
    DMGSNDCTRL = DMGSNDCTRL_LVOL(7) | DMGSNDCTRL_RVOL(7) |
                 DMGSNDCTRL_LSQR1 | DMGSNDCTRL_RSQR1 |
                 DMGSNDCTRL_LSQR2 | DMGSNDCTRL_RSQR2;
    DSOUNDCTRL = DSOUNDCTRL_DMG100;
    SQR1SWEEP = SQR1SWEEP_OFF;
    SQR1CTRL = 0;
    SQR2CTRL = 0;
    audioState.melodyTimer = 0;
    audioState.melodyIndex = 0;
    audioState.bassTimer = 0;
    audioState.bassIndex = 0;
    audioState.sfxTimer = 0;
    audioState.sfxIndex = 0;
    audioState.activeSfx = SFX_NONE;
}

static void resetAudioLoop(void) {
    audioState.melodyTimer = 0;
    audioState.melodyIndex = 0;
    audioState.bassTimer = 0;
    audioState.bassIndex = 0;
    audioState.sfxTimer = 0;
    audioState.sfxIndex = 0;
    audioState.activeSfx = SFX_NONE;
}

static void startSfx(SfxType type) {
    audioState.activeSfx = type;
    audioState.sfxTimer = 0;
    audioState.sfxIndex = 0;
}

static const Note *getSfxSequence(SfxType type, int *count) {
    switch (type) {
        case SFX_WINDOW:
            *count = (int)(sizeof(kWindowSfx) / sizeof(kWindowSfx[0]));
            return kWindowSfx;
        case SFX_SUCCESS:
            *count = (int)(sizeof(kSuccessSfx) / sizeof(kSuccessSfx[0]));
            return kSuccessSfx;
        case SFX_FAIL:
            *count = (int)(sizeof(kFailSfx) / sizeof(kFailSfx[0]));
            return kFailSfx;
        case SFX_RELIC:
            *count = (int)(sizeof(kRelicSfx) / sizeof(kRelicSfx[0]));
            return kRelicSfx;
        case SFX_WIN:
            *count = (int)(sizeof(kWinSfx) / sizeof(kWinSfx[0]));
            return kWinSfx;
        case SFX_LOSE:
            *count = (int)(sizeof(kLoseSfx) / sizeof(kLoseSfx[0]));
            return kLoseSfx;
        case SFX_NONE:
        default:
            *count = 0;
            return 0;
    }
}

static void updateAudio(void) {
    if (audioState.melodyTimer <= 0) {
        Note note = kMelodyLoop[audioState.melodyIndex];
        playSquare1(note);
        audioState.melodyIndex = (audioState.melodyIndex + 1) % (int)(sizeof(kMelodyLoop) / sizeof(kMelodyLoop[0]));
        audioState.melodyTimer = note.frames;
    }
    audioState.melodyTimer -= 1;

    if (audioState.activeSfx != SFX_NONE) {
        int sfxCount = 0;
        const Note *sequence = getSfxSequence(audioState.activeSfx, &sfxCount);
        if (audioState.sfxTimer <= 0) {
            if (audioState.sfxIndex >= sfxCount) {
                audioState.activeSfx = SFX_NONE;
                audioState.sfxIndex = 0;
                audioState.sfxTimer = 0;
                SQR2CTRL = 0;
            } else {
                Note note = sequence[audioState.sfxIndex++];
                playSquare2(note);
                audioState.sfxTimer = note.frames;
            }
        }
        if (audioState.activeSfx != SFX_NONE) {
            audioState.sfxTimer -= 1;
        }
        return;
    }

    if (audioState.bassTimer <= 0) {
        Note note = kBassLoop[audioState.bassIndex];
        playSquare2(note);
        audioState.bassIndex = (audioState.bassIndex + 1) % (int)(sizeof(kBassLoop) / sizeof(kBassLoop[0]));
        audioState.bassTimer = note.frames;
    }
    audioState.bassTimer -= 1;
}

static void drawRect(int x, int y, int w, int h, Color color) {
    if (w <= 0 || h <= 0) return;
    for (int iy = 0; iy < h; ++iy) {
        int py = y + iy;
        if ((unsigned)py >= SCREEN_H) continue;
        for (int ix = 0; ix < w; ++ix) {
            int px = x + ix;
            if ((unsigned)px >= SCREEN_W) continue;
            videoBuffer[py * SCREEN_W + px] = color;
        }
    }
}

static void drawFrame(int x, int y, int w, int h, Color color) {
    drawRect(x, y, w, 1, color);
    drawRect(x, y + h - 1, w, 1, color);
    drawRect(x, y, 1, h, color);
    drawRect(x + w - 1, y, 1, h, color);
}

static void drawGlyph(char ch, int x, int y, int scale, Color color) {
    if (ch == ' ') return;
    int glyphIndex = -1;
    for (int i = 0; kGlyphMap[i] != '\0'; ++i) {
        if (kGlyphMap[i] == ch) {
            glyphIndex = i;
            break;
        }
    }
    if (glyphIndex < 0 || glyphIndex >= (int)(sizeof(kGlyphs) / sizeof(kGlyphs[0]))) return;
    for (int row = 0; row < 7; ++row) {
        for (int col = 0; col < 5; ++col) {
            if ((kGlyphs[glyphIndex][row] >> (4 - col)) & 1) {
                drawRect(x + col * scale, y + row * scale, scale, scale, color);
            }
        }
    }
}

static void drawText(const char *text, int x, int y, int scale, Color color) {
    int cursor = x;
    while (*text) {
        drawGlyph(*text, cursor, y, scale, color);
        cursor += 6 * scale;
        ++text;
    }
}

static void drawDigits(int value, int x, int y, int scale, Color color) {
    char buffer[12];
    int index = 0;
    if (value == 0) {
        buffer[index++] = '0';
    } else {
        int copy = value;
        char reversed[12];
        int rindex = 0;
        while (copy > 0 && rindex < 10) {
            reversed[rindex++] = (char)('0' + (copy % 10));
            copy /= 10;
        }
        while (rindex > 0) {
            buffer[index++] = reversed[--rindex];
        }
    }
    buffer[index] = '\0';
    drawText(buffer, x, y, scale, color);
}

static PromptType promptTypeForKeys(uint16_t downKeys) {
    if (downKeys & KEY_UP) return PROMPT_UP;
    if (downKeys & KEY_DOWN) return PROMPT_DOWN;
    if (downKeys & KEY_LEFT) return PROMPT_LEFT;
    if (downKeys & KEY_RIGHT) return PROMPT_RIGHT;
    if (downKeys & KEY_A) return PROMPT_A;
    return PROMPT_B;
}

static void startEncounter(GameState *state) {
    state->playerHealth = 100;
    state->bossHealth = 100;
    state->zoneIndex = 0;
    state->gearCount = 2;
    state->comboCount = 0;
    state->relicCharge = 35;
    state->tick = 0;
    state->windowTimer = 0;
    state->promptIndex = 0;
    state->bossMode = BOSS_IDLE;
    state->qteWindowOpen = false;
    state->encounterResolved = false;
    state->playerWon = false;
    resetAudioLoop();
}

static void advancePrompt(GameState *state) {
    prompt_counter = (prompt_counter + 1) % (int)(sizeof(kPrompts) / sizeof(kPrompts[0]));
    state->promptIndex = prompt_counter;
}

static void openWindow(GameState *state) {
    state->bossMode = (BossMode)((state->tick / 120 + state->zoneIndex) % 3);
    advancePrompt(state);
    state->qteWindowOpen = true;
    state->windowTimer = 22;
    startSfx(SFX_WINDOW);
}

static void resolveAnswer(GameState *state, PromptType answer) {
    const Prompt *prompt = &kPrompts[state->promptIndex];
    if (!state->qteWindowOpen || state->encounterResolved) return;

    state->qteWindowOpen = false;
    state->windowTimer = 0;
    if (answer == prompt->type) {
        state->bossHealth = CLAMP_MIN(state->bossHealth - prompt->reward, 0);
        state->comboCount = CLAMP_MAX(state->comboCount + 1, 0);
        state->gearCount = CLAMP_MAX(state->gearCount + 1, 5);
        state->relicCharge = CLAMP_MAX(state->relicCharge + 12, 100);
        startSfx(SFX_SUCCESS);
    } else {
        state->playerHealth = CLAMP_MIN(state->playerHealth - prompt->penalty, 0);
        state->comboCount = 0;
        startSfx(SFX_FAIL);
    }
}

static void updateGame(GameState *state) {
    scanKeys();
    uint16_t downKeys = keysDown();

    if (downKeys & KEY_START) {
        startEncounter(state);
        return;
    }

    if (state->encounterResolved) {
        if (downKeys & (KEY_A | KEY_B | KEY_START)) {
            startEncounter(state);
        }
        return;
    }

    if (downKeys & KEY_SELECT) {
        state->zoneIndex = (state->zoneIndex + 1) % 3;
        state->gearCount = CLAMP_MAX(state->gearCount + 1, 5);
        state->relicCharge = CLAMP_MAX(state->relicCharge + 18, 100);
        startSfx(SFX_WINDOW);
    }

    if ((downKeys & KEY_L) && state->relicCharge >= 50) {
        state->relicCharge = 10;
        state->bossHealth = CLAMP_MIN(state->bossHealth - 14, 0);
        startSfx(SFX_RELIC);
    }

    if (state->qteWindowOpen && (downKeys & (KEY_UP | KEY_DOWN | KEY_LEFT | KEY_RIGHT | KEY_A | KEY_B))) {
        resolveAnswer(state, promptTypeForKeys(downKeys));
    }

    state->tick += 1;
    if (state->tick % 120 == 0) {
        openWindow(state);
    }

    if (state->qteWindowOpen) {
        state->windowTimer -= 1;
        if (state->windowTimer <= 0) {
            const Prompt *prompt = &kPrompts[state->promptIndex];
            state->qteWindowOpen = false;
            state->playerHealth = CLAMP_MIN(state->playerHealth - prompt->penalty, 0);
            state->comboCount = 0;
            startSfx(SFX_FAIL);
        }
    }

    state->relicCharge = CLAMP_MAX(state->relicCharge + 1, 100);

    if (state->bossHealth <= 0 || state->playerHealth <= 0) {
        state->encounterResolved = true;
        state->playerWon = state->bossHealth <= 0;
        startSfx(state->playerWon ? SFX_WIN : SFX_LOSE);
    }
}

static void drawBar(int x, int y, int w, int h, int value, int maxValue, Color fillColor, Color backColor) {
    drawRect(x, y, w, h, backColor);
    int fillWidth = (value * (w - 2)) / maxValue;
    drawRect(x + 1, y + 1, fillWidth, h - 2, fillColor);
    drawFrame(x, y, w, h, RGB15(31, 31, 31));
}

static void drawBoss(const GameState *state) {
    const uint16_t (*frames)[SKULLDUMMY_SPRITE_PIXELS] = skulldummy_blunin_idle;
    if (state->bossMode == BOSS_ADVANCE) {
        frames = skulldummy_blunin_walk;
    } else if (state->bossMode == BOSS_COMBO) {
        frames = skulldummy_blunin_attack;
    }

    int sway = (state->tick / 6) % 6;
    int frame = (state->tick / 6) % SKULLDUMMY_BOSS_FRAME_COUNT;
    if (sway > 3) sway = 6 - sway;
    drawBitmapTransparent(frames[frame], SKULLDUMMY_SPRITE_W, SKULLDUMMY_SPRITE_H, 144 - sway, 48);
}

static void drawPlayer(const GameState *state) {
    int bob = (state->tick / 8) % 4;
    Color body = RGB15(14, 22, 18);
    Color trim = RGB15(28, 31, 28);
    drawRect(36, 90 - bob, 28, 28, body);
    drawRect(40, 94 - bob, 6, 6, trim);
    drawRect(54, 94 - bob, 6, 6, trim);
    drawRect(45, 109 - bob, 10, 3, trim);
    drawRect(30, 116 - bob, 14, 6, RGB15(10, 12, 12));
    drawRect(56, 116 - bob, 14, 6, RGB15(10, 12, 12));
}

static void drawPromptPanel(const GameState *state) {
    static const char *promptNames[] = { "UP", "DOWN", "LEFT", "RIGHT", "A", "B" };
    drawRect(78, 116, 84, 28, RGB15(3, 4, 6));
    drawFrame(78, 116, 84, 28, RGB15(22, 24, 29));
    if (state->qteWindowOpen) {
        drawText(promptNames[state->promptIndex], 96, 124, 2, RGB15(31, 27, 12));
        drawRect(144, 123, 8 + state->windowTimer * 2, 6, RGB15(30, 10, 10));
    } else {
        drawText("READ", 96, 124, 2, RGB15(16, 20, 26));
    }
}

static void drawScene(const GameState *state) {
    drawBitmapFull(skulldummy_backgrounds[state->zoneIndex]);

    drawPlayer(state);
    drawBoss(state);
    drawBitmapTransparent(skulldummy_relic_icon, SKULLDUMMY_ICON_W, SKULLDUMMY_ICON_H, 184, 118);

    drawText("SKULLDUMMY", 8, 8, 2, RGB15(31, 29, 22));
    drawText("ZONE", 8, 28, 1, RGB15(18, 22, 26));
    drawDigits(state->zoneIndex + 1, 42, 28, 1, RGB15(31, 31, 31));
    drawText("RELIC", 8, 40, 1, RGB15(18, 22, 26));
    drawDigits(state->relicCharge, 48, 40, 1, RGB15(25, 29, 14));
    drawText("COMBO", 8, 52, 1, RGB15(18, 22, 26));
    drawDigits(state->comboCount, 48, 52, 1, RGB15(29, 23, 23));
    drawText("GEAR", 8, 64, 1, RGB15(18, 22, 26));
    drawDigits(state->gearCount, 42, 64, 1, RGB15(24, 26, 31));

    drawBar(8, 82, 96, 10, state->playerHealth, 100, RGB15(10, 28, 16), RGB15(4, 6, 5));
    drawBar(136, 16, 96, 10, state->bossHealth, 100, RGB15(28, 9, 11), RGB15(6, 4, 4));
    drawBar(8, 146, 100, 8, state->relicCharge, 100, RGB15(23, 21, 8), RGB15(7, 7, 5));
    drawText("P", 2, 80, 1, RGB15(31, 31, 31));
    drawText("B", 128, 14, 1, RGB15(31, 31, 31));
    drawPromptPanel(state);

    if (state->encounterResolved) {
        drawRect(34, 56, 172, 42, RGB15(2, 2, 3));
        drawFrame(34, 56, 172, 42, RGB15(24, 24, 26));
        if (state->playerWon) {
            drawText("BLUNIN BROKE", 52, 66, 2, RGB15(28, 30, 15));
        } else {
            drawText("SKULL FELL", 58, 66, 2, RGB15(31, 19, 19));
        }
        drawText("PRESS A", 82, 84, 1, RGB15(21, 23, 27));
    }
}

int main(void) {
    irqInit();
    irqEnable(IRQ_VBLANK);
    SetMode(MODE_3 | BG2_ON);
    initAudio();

    GameState state;
    startEncounter(&state);

    while (1) {
        VBlankIntrWait();
        updateGame(&state);
        updateAudio();
        drawScene(&state);
    }
}