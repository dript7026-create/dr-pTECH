#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

typedef enum {
    SSB_CONTENT_MUSIC,
    SSB_CONTENT_SFX,
    SSB_CONTENT_SOUNDSCAPE
} SSBContentType;

typedef enum {
    SSB_MODEL_FOREST_DRONE,
    SSB_MODEL_COMBAT_HEARTBEAT,
    SSB_MODEL_MENU_DREAM,
    SSB_MODEL_BITE_IMPACT,
    SSB_MODEL_DASH_SURGE,
    SSB_MODEL_HEAL_BLOOM,
    SSB_MODEL_RAINFOREST_BED
} SSBModelType;

typedef struct {
    int sample_rate;
    int bit_depth;
    int channels;
    float duration_seconds;
    unsigned int seed;
    float base_frequency;
    float sub_frequency;
    float intensity;
    float spatial_width;
    float noise_amount;
} SSBRenderConfig;

typedef struct {
    float *left;
    float *right;
    int frame_count;
    SSBRenderConfig config;
} SSBAudioBuffer;

typedef void (*SSBExternalGenerator)(SSBAudioBuffer *buffer, const SSBRenderConfig *config, void *user_data);

typedef struct {
    SSBExternalGenerator callback;
    void *user_data;
} SSBExternalBridge;

static uint32_t ssb_rand_u32(uint32_t *state) {
    *state = (*state * 1664525u) + 1013904223u;
    return *state;
}

static float ssb_rand_bipolar(uint32_t *state) {
    return ((ssb_rand_u32(state) >> 8) / 8388607.5f) - 1.0f;
}

static float ssb_clamp(float v, float lo, float hi) {
    return v < lo ? lo : (v > hi ? hi : v);
}

static void ssb_zero(SSBAudioBuffer *buffer) {
    memset(buffer->left, 0, sizeof(float) * (size_t)buffer->frame_count);
    memset(buffer->right, 0, sizeof(float) * (size_t)buffer->frame_count);
}

static SSBAudioBuffer ssb_create_buffer(const SSBRenderConfig *config) {
    SSBAudioBuffer buffer;
    buffer.frame_count = (int)(config->duration_seconds * (float)config->sample_rate);
    buffer.left = (float *)calloc((size_t)buffer.frame_count, sizeof(float));
    buffer.right = (float *)calloc((size_t)buffer.frame_count, sizeof(float));
    buffer.config = *config;
    return buffer;
}

static void ssb_destroy_buffer(SSBAudioBuffer *buffer) {
    free(buffer->left);
    free(buffer->right);
    buffer->left = NULL;
    buffer->right = NULL;
    buffer->frame_count = 0;
}

static void ssb_apply_binaural_pan(SSBAudioBuffer *buffer, int index, float sample, float pan) {
    float left_gain = sqrtf(0.5f * (1.0f - pan));
    float right_gain = sqrtf(0.5f * (1.0f + pan));
    buffer->left[index] += sample * left_gain;
    buffer->right[index] += sample * right_gain;
}

static void ssb_render_forest_drone(SSBAudioBuffer *buffer) {
    uint32_t rng = buffer->config.seed;
    float base = buffer->config.base_frequency;
    float sub = buffer->config.sub_frequency;
    for (int i = 0; i < buffer->frame_count; ++i) {
        float t = (float)i / (float)buffer->config.sample_rate;
        float bed = sinf(2.0f * (float)M_PI * base * t) * 0.28f;
        float undertone = sinf(2.0f * (float)M_PI * sub * t) * 0.22f;
        float whisper = ssb_rand_bipolar(&rng) * buffer->config.noise_amount * 0.08f;
        float pan = sinf(2.0f * (float)M_PI * 0.07f * t) * buffer->config.spatial_width;
        float pulse = sinf(2.0f * (float)M_PI * 0.5f * t) * 0.06f;
        ssb_apply_binaural_pan(buffer, i, (bed + undertone + whisper + pulse) * buffer->config.intensity, pan);
    }
}

static void ssb_render_combat_heartbeat(SSBAudioBuffer *buffer) {
    uint32_t rng = buffer->config.seed;
    for (int i = 0; i < buffer->frame_count; ++i) {
        float t = (float)i / (float)buffer->config.sample_rate;
        float beat = powf(fmaxf(0.0f, sinf(2.0f * (float)M_PI * 1.8f * t)), 6.0f) * 0.45f;
        float bass = sinf(2.0f * (float)M_PI * (buffer->config.base_frequency + 20.0f) * t) * 0.22f;
        float grit = ssb_rand_bipolar(&rng) * 0.03f * buffer->config.noise_amount;
        float pan = sinf(2.0f * (float)M_PI * 0.3f * t) * 0.25f;
        ssb_apply_binaural_pan(buffer, i, (beat + bass + grit) * buffer->config.intensity, pan);
    }
}

static void ssb_render_menu_dream(SSBAudioBuffer *buffer) {
    for (int i = 0; i < buffer->frame_count; ++i) {
        float t = (float)i / (float)buffer->config.sample_rate;
        float chord = sinf(2.0f * (float)M_PI * buffer->config.base_frequency * t) * 0.14f;
        chord += sinf(2.0f * (float)M_PI * buffer->config.base_frequency * 1.25f * t) * 0.12f;
        chord += sinf(2.0f * (float)M_PI * buffer->config.base_frequency * 1.5f * t) * 0.10f;
        float shimmer = sinf(2.0f * (float)M_PI * 6.0f * t) * 0.03f;
        float pan = sinf(2.0f * (float)M_PI * 0.1f * t) * buffer->config.spatial_width;
        ssb_apply_binaural_pan(buffer, i, (chord + shimmer) * buffer->config.intensity, pan);
    }
}

static void ssb_render_one_shot(SSBAudioBuffer *buffer, float attack_hz, float decay, float noise_mix) {
    uint32_t rng = buffer->config.seed;
    for (int i = 0; i < buffer->frame_count; ++i) {
        float t = (float)i / (float)buffer->config.sample_rate;
        float env = expf(-decay * t);
        float tone = sinf(2.0f * (float)M_PI * attack_hz * t);
        float noise = ssb_rand_bipolar(&rng) * noise_mix;
        float pan = sinf(2.0f * (float)M_PI * 12.0f * t) * 0.15f;
        ssb_apply_binaural_pan(buffer, i, (tone * (1.0f - noise_mix) + noise) * env * buffer->config.intensity, pan);
    }
}

static void ssb_render_model(SSBAudioBuffer *buffer, SSBModelType model) {
    switch (model) {
        case SSB_MODEL_FOREST_DRONE:
        case SSB_MODEL_RAINFOREST_BED:
            ssb_render_forest_drone(buffer);
            break;
        case SSB_MODEL_COMBAT_HEARTBEAT:
            ssb_render_combat_heartbeat(buffer);
            break;
        case SSB_MODEL_MENU_DREAM:
            ssb_render_menu_dream(buffer);
            break;
        case SSB_MODEL_BITE_IMPACT:
            ssb_render_one_shot(buffer, 92.0f, 10.0f, 0.35f);
            break;
        case SSB_MODEL_DASH_SURGE:
            ssb_render_one_shot(buffer, 180.0f, 7.0f, 0.20f);
            break;
        case SSB_MODEL_HEAL_BLOOM:
            ssb_render_one_shot(buffer, 520.0f, 4.0f, 0.08f);
            break;
        default:
            ssb_zero(buffer);
            break;
    }
}

static void ssb_mix_external(SSBAudioBuffer *buffer, const SSBExternalBridge *bridge) {
    if (bridge && bridge->callback) {
        bridge->callback(buffer, &buffer->config, bridge->user_data);
    }
}

static void ssb_normalize(SSBAudioBuffer *buffer) {
    float peak = 0.001f;
    for (int i = 0; i < buffer->frame_count; ++i) {
        float l = fabsf(buffer->left[i]);
        float r = fabsf(buffer->right[i]);
        if (l > peak) peak = l;
        if (r > peak) peak = r;
    }
    float gain = 0.92f / peak;
    for (int i = 0; i < buffer->frame_count; ++i) {
        buffer->left[i] *= gain;
        buffer->right[i] *= gain;
    }
}

static int ssb_write_wav(const char *path, const SSBAudioBuffer *buffer, int mono_downmix) {
    FILE *fp = fopen(path, "wb");
    if (!fp) return 0;

    int channels = mono_downmix ? 1 : 2;
    int bytes_per_sample = buffer->config.bit_depth / 8;
    int data_size = buffer->frame_count * channels * bytes_per_sample;
    int chunk_size = 36 + data_size;
    int byte_rate = buffer->config.sample_rate * channels * bytes_per_sample;
    int block_align = channels * bytes_per_sample;

    fwrite("RIFF", 1, 4, fp);
    fwrite(&chunk_size, 4, 1, fp);
    fwrite("WAVEfmt ", 1, 8, fp);
    {
        int subchunk1 = 16;
        short audio_format = 1;
        short ch = (short)channels;
        short bits = (short)buffer->config.bit_depth;
        fwrite(&subchunk1, 4, 1, fp);
        fwrite(&audio_format, 2, 1, fp);
        fwrite(&ch, 2, 1, fp);
        fwrite(&buffer->config.sample_rate, 4, 1, fp);
        fwrite(&byte_rate, 4, 1, fp);
        fwrite(&block_align, 2, 1, fp);
        fwrite(&bits, 2, 1, fp);
    }
    fwrite("data", 1, 4, fp);
    fwrite(&data_size, 4, 1, fp);

    for (int i = 0; i < buffer->frame_count; ++i) {
        float left = ssb_clamp(buffer->left[i], -1.0f, 1.0f);
        float right = ssb_clamp(buffer->right[i], -1.0f, 1.0f);
        if (buffer->config.bit_depth == 16) {
            short l = (short)(left * 32767.0f);
            short r = (short)(right * 32767.0f);
            if (mono_downmix) {
                short m = (short)(((float)l + (float)r) * 0.5f);
                fwrite(&m, sizeof(short), 1, fp);
            } else {
                fwrite(&l, sizeof(short), 1, fp);
                fwrite(&r, sizeof(short), 1, fp);
            }
        } else {
            uint8_t l = (uint8_t)(128 + left * 127.0f);
            uint8_t r = (uint8_t)(128 + right * 127.0f);
            if (mono_downmix) {
                uint8_t m = (uint8_t)(((int)l + (int)r) / 2);
                fwrite(&m, sizeof(uint8_t), 1, fp);
            } else {
                fwrite(&l, sizeof(uint8_t), 1, fp);
                fwrite(&r, sizeof(uint8_t), 1, fp);
            }
        }
    }

    fclose(fp);
    return 1;
}

static SSBRenderConfig ssb_default_config(void) {
    SSBRenderConfig cfg;
    cfg.sample_rate = 44100;
    cfg.bit_depth = 16;
    cfg.channels = 2;
    cfg.duration_seconds = 6.0f;
    cfg.seed = 1337u;
    cfg.base_frequency = 74.0f;
    cfg.sub_frequency = 18.5f;
    cfg.intensity = 0.85f;
    cfg.spatial_width = 0.65f;
    cfg.noise_amount = 0.35f;
    return cfg;
}

static SSBRenderConfig ssb_gba_profile(float duration_seconds) {
    SSBRenderConfig cfg = ssb_default_config();
    cfg.sample_rate = 18157;
    cfg.bit_depth = 8;
    cfg.channels = 1;
    cfg.duration_seconds = duration_seconds;
    cfg.spatial_width = 0.20f;
    cfg.noise_amount = 0.18f;
    return cfg;
}

/*
GBA integration note:
- True binaural / surround rendering is not realistic on the GBA hardware itself.
- The intended TommyBeta path is to author richer stereo source assets offline with this tool,
  then export GBA-safe mono or narrow-stereo downmixes at low sample rates for ROM playback.
- Richer engines on PC / console can use the same synthesis core plus external generators in real time.
*/

int main(void) {
    SSBRenderConfig forest_cfg = ssb_default_config();
    SSBRenderConfig bite_cfg = ssb_default_config();
    SSBRenderConfig gba_cfg = ssb_gba_profile(4.0f);

    bite_cfg.duration_seconds = 1.2f;
    bite_cfg.base_frequency = 92.0f;
    bite_cfg.sub_frequency = 28.0f;

    SSBAudioBuffer forest = ssb_create_buffer(&forest_cfg);
    SSBAudioBuffer bite = ssb_create_buffer(&bite_cfg);
    SSBAudioBuffer gba = ssb_create_buffer(&gba_cfg);

    ssb_render_model(&forest, SSB_MODEL_RAINFOREST_BED);
    ssb_render_model(&bite, SSB_MODEL_BITE_IMPACT);
    ssb_render_model(&gba, SSB_MODEL_MENU_DREAM);

    ssb_normalize(&forest);
    ssb_normalize(&bite);
    ssb_normalize(&gba);

    ssb_write_wav("SubSoundBiNeural_forest_bed.wav", &forest, 0);
    ssb_write_wav("SubSoundBiNeural_bite_impact.wav", &bite, 0);
    ssb_write_wav("SubSoundBiNeural_gba_menu_downmix.wav", &gba, 1);

    ssb_destroy_buffer(&forest);
    ssb_destroy_buffer(&bite);
    ssb_destroy_buffer(&gba);

    return 0;
}