#include <jni.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

#include "generator.h"
#include "world.h"
#include "npc.h"
#include "economy.h"

// Assembly helper
int get_seed_hash(const char* seed);

JNIEXPORT jstring JNICALL
Java_com_urbden_game_MainActivity_stringFromJNI(JNIEnv* env, jobject thiz, jstring jseed) {
    const char* seed = (*env)->GetStringUTFChars(env, jseed, 0);
    // Initialize systems
    generator_seed_from_string(seed);
    economy_init();
    world_generate(seed);

    char* wsum = world_summary();
    char* nsum = npc_list_summary();
    char* est = economy_status();

    char buf[2048];
    snprintf(buf, sizeof(buf), "Urbden Prototype\nSeed: %s\n%s\n\nNPCs:\n%s\nEconomy:\n%s\n--\n(Prototype) Use this seed to drive procedural generation and expand systems.", seed, wsum?wsum:"(no world)", nsum?nsum:"(no npcs)", est?est:"(no economy)");

    if (wsum) free(wsum);
    if (nsum) free(nsum);
    if (est) free(est);
    (*env)->ReleaseStringUTFChars(env, jseed, seed);
    return (*env)->NewStringUTF(env, buf);
}

// Initialize native systems with a seed
JNIEXPORT void JNICALL
Java_com_urbden_game_MainActivity_initNative(JNIEnv* env, jobject thiz, jstring jseed) {
    const char* seed = (*env)->GetStringUTFChars(env, jseed, 0);
    generator_seed_from_string(seed);
    economy_init();
    world_generate(seed);
    (*env)->ReleaseStringUTFChars(env, jseed, seed);
}

JNIEXPORT jint JNICALL
Java_com_urbden_game_MainActivity_getWorldWidth(JNIEnv* env, jobject thiz) {
    const World* w = world_get();
    return w ? w->w : 0;
}

JNIEXPORT jint JNICALL
Java_com_urbden_game_MainActivity_getWorldHeight(JNIEnv* env, jobject thiz) {
    const World* w = world_get();
    return w ? w->h : 0;
}

JNIEXPORT jint JNICALL
Java_com_urbden_game_MainActivity_getNPCCount(JNIEnv* env, jobject thiz) {
    return npc_count();
}

JNIEXPORT jint JNICALL
Java_com_urbden_game_MainActivity_getNPCX(JNIEnv* env, jobject thiz, jint idx) {
    const NPC* p = npc_get(idx);
    return p ? p->x : -1;
}

JNIEXPORT jint JNICALL
Java_com_urbden_game_MainActivity_getNPCY(JNIEnv* env, jobject thiz, jint idx) {
    const NPC* p = npc_get(idx);
    return p ? p->y : -1;
}

JNIEXPORT jboolean JNICALL
Java_com_urbden_game_MainActivity_isNPCRival(JNIEnv* env, jobject thiz, jint idx) {
    const NPC* p = npc_get(idx);
    return (jboolean)(p ? (p->is_rival ? JNI_TRUE : JNI_FALSE) : JNI_FALSE);
}

JNIEXPORT jstring JNICALL
Java_com_urbden_game_MainActivity_getNPCName(JNIEnv* env, jobject thiz, jint idx) {
    const NPC* p = npc_get(idx);
    if (!p) return (*env)->NewStringUTF(env, "");
    return (*env)->NewStringUTF(env, p->name);
}

JNIEXPORT jfloat JNICALL
Java_com_urbden_game_MainActivity_getNPCInfluence(JNIEnv* env, jobject thiz, jint idx) {
    return (jfloat)npc_get_influence(idx);
}

JNIEXPORT jint JNICALL
Java_com_urbden_game_MainActivity_exportWorldSnapshot(JNIEnv* env, jobject thiz, jstring jpath, jstring jseed) {
    const char* path = jpath ? (*env)->GetStringUTFChars(env, jpath, 0) : NULL;
    const char* seed = jseed ? (*env)->GetStringUTFChars(env, jseed, 0) : NULL;
    int r = world_export_snapshot(path, seed);
    if (path) (*env)->ReleaseStringUTFChars(env, jpath, path);
    if (seed) (*env)->ReleaseStringUTFChars(env, jseed, seed);
    return r;
}

// --- Direct ByteBuffer export for ultra-fast bulk access from Java
typedef struct {
    int32_t x;
    int32_t y;
    int32_t moral;
    int32_t is_rival;
    float influence;
} NPCPacked;

static NPCPacked* g_npc_buffer = NULL;
static size_t g_npc_buffer_size = 0;

static void rebuild_npc_buffer() {
    int n = npc_count();
    if (n <= 0) {
        if (g_npc_buffer) { free(g_npc_buffer); g_npc_buffer = NULL; g_npc_buffer_size = 0; }
        return;
    }
    size_t need = sizeof(NPCPacked) * (size_t)n;
    if (g_npc_buffer && g_npc_buffer_size >= need) {
        // reuse
    } else {
        if (g_npc_buffer) free(g_npc_buffer);
        g_npc_buffer = (NPCPacked*)malloc(need);
        g_npc_buffer_size = need;
    }
    for (int i = 0; i < n; ++i) {
        const NPC* p = npc_get(i);
        if (!p) continue;
        g_npc_buffer[i].x = p->x;
        g_npc_buffer[i].y = p->y;
        g_npc_buffer[i].moral = p->moral_tendency;
        g_npc_buffer[i].is_rival = p->is_rival ? 1 : 0;
        g_npc_buffer[i].influence = p->influence;
    }
}

JNIEXPORT jobject JNICALL
Java_com_urbden_game_MainActivity_getNPCBuffer(JNIEnv* env, jobject thiz) {
    rebuild_npc_buffer();
    if (!g_npc_buffer) return NULL;
    return (*env)->NewDirectByteBuffer(env, (void*)g_npc_buffer, (jlong)g_npc_buffer_size);
}

JNIEXPORT void JNICALL
Java_com_urbden_game_MainActivity_releaseNPCBuffer(JNIEnv* env, jobject thiz) {
    if (g_npc_buffer) {
        free(g_npc_buffer);
        g_npc_buffer = NULL;
        g_npc_buffer_size = 0;
    }
}
