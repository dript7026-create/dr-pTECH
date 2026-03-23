#ifndef GRAVO_H
#define GRAVO_H

#include <stddef.h>

#if defined(__has_include)
#if __has_include(<windows.h>)
#include <windows.h>
#define GRAVO_HAS_WINDOWS 1
#endif
#if __has_include("../ORBEngine/include/orbengine.h")
#include "../ORBEngine/include/orbengine.h"
#define GRAVO_HAS_ORBENGINE 1
#endif
#if __has_include("../egosphere/egosphere.h")
#include "../egosphere/egosphere.h"
#define GRAVO_HAS_EGOSPHERE 1
#endif
#endif

#ifndef GRAVO_HAS_WINDOWS
typedef void *HDC;
typedef unsigned long WPARAM;
typedef struct tagRECT {
    long left;
    long top;
    long right;
    long bottom;
} RECT;
#endif

#ifndef GRAVO_HAS_ORBENGINE
typedef struct ORBEngineSandbox ORBEngineSandbox;
#endif

#if defined(GRAVO_HAS_WINDOWS) && defined(GRAVO_HAS_ORBENGINE) && defined(GRAVO_HAS_EGOSPHERE)
#define GRAVO_HAS_RUNTIME_DEPS 1
#endif

#ifdef __cplusplus
extern "C" {
#endif

typedef struct GravoRuntimeState GravoRuntimeState;

const wchar_t *gravo_get_concept_summary(void);
int gravo_get_weapon_count(void);
int gravo_get_shrine_count(void);
int gravo_get_narrative_beat_count(void);
int gravo_get_biome_count(void);
int gravo_get_enemy_family_count(void);

void gravo_seed_sandbox(ORBEngineSandbox *sandbox);

GravoRuntimeState *gravo_runtime_create(ORBEngineSandbox *sandbox, int autoplayEnabled);
void gravo_runtime_destroy(GravoRuntimeState *state);
void gravo_runtime_step(GravoRuntimeState *state, float deltaSeconds);
void gravo_runtime_render(GravoRuntimeState *state, HDC hdc, RECT clientRect);
void gravo_runtime_key_down(GravoRuntimeState *state, WPARAM key);
void gravo_runtime_key_up(GravoRuntimeState *state, WPARAM key);
int gravo_runtime_should_close(GravoRuntimeState *state);

#ifdef __cplusplus
}
#endif

#endif