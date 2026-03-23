/*
 * CryptWire v0.1.0
 * Multi-layer adaptive encryption pipeline with AI-guided threat response.
 *
 * Pipeline ordering (E = encrypt, R = reencrypt):
 *   E0 → [R0←tag1] → E1 → [R1←tag2, AI→params2] → E2 → ... → En → SEAL
 *
 *   Stage 0  : Encrypt only (no feedback from prior stage — first stage)
 *   Stage 1..n-1: Encrypt, then feed current auth-tag back into prior stage's
 *                 key to double-reencrypt it; simultaneously AI recommends next
 *                 stage algorithm from 8-dim threat state (look-ahead).
 *   Stage n  : Encrypt only (no AI look-ahead — last stage)
 *   Final SEAL: HMAC-SHA256 depth-scaled by threat level, sealing the full
 *               pipeline output. Depth scales in 8 dimensions (one per AI
 *               threat axis). A hidden convergence round is applied at depth
 *               >=1000 iterations for any CRITICAL-threat seal.
 *
 * Ciphertext wire format (all LE):
 *   [4]  magic   = 0x43 0x57 0x49 0x52  ("CWIR")
 *   [2]  version = 0x0001
 *   [1]  num_stages
 *   [1]  flags
 *   [8]  timestamp (Unix seconds, uint64)
 *   [32] machine_id_hash (SHA-256 of machine fingerprint)
 *   Per stage:
 *     [1]  algo_id
 *     [1]  reserved
 *     [16] iv / nonce (padded)
 *     [16] auth_tag
 *     [4]  ct_len
 *     [ct_len] ciphertext
 *   [4]  seal_depth
 *   [32] seal_digest (HMAC-SHA256)
 *
 * Requires: OpenSSL >= 1.1.0   Link: -lssl -lcrypto
 */

#ifndef CRYPTWIRE_H
#define CRYPTWIRE_H

#include <stdint.h>
#include <stddef.h>
#include <time.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ─── Constants ─────────────────────────────────────────────────── */
#define CW_VERSION_MAJOR        0
#define CW_VERSION_MINOR        1
#define CW_MAGIC                "\x43\x57\x49\x52"   /* "CWIR" */
#define CW_MAX_STAGES           8
#define CW_MASTER_KEY_LEN       32
#define CW_MASTER_SALT_LEN      32
#define CW_MACHINE_ID_LEN       64
#define CW_MACHINE_HASH_LEN     32
#define CW_AUTH_TAG_LEN         16
#define CW_IV_LEN               16   /* GCM nonce is 12 bytes, padded to 16 */
#define CW_SEAL_DIGEST_LEN      32

/* Minimum seal iterations per threat level */
#define CW_SEAL_DEPTH_NONE      64
#define CW_SEAL_DEPTH_LOW       256
#define CW_SEAL_DEPTH_MEDIUM    1024
#define CW_SEAL_DEPTH_HIGH      4096
#define CW_SEAL_DEPTH_CRITICAL  16384   /* convergence round at >=1000 */

/* Key rotation interval (seconds) */
#define CW_KEY_ROTATION_INTERVAL_S   (60 * 60 * 6)   /* 6 hours default */

/* ─── Algorithm IDs ──────────────────────────────────────────────── */
typedef enum {
    CW_ALGO_AES256_GCM      = 0x01,
    CW_ALGO_CHACHA20_POLY   = 0x02,
    CW_ALGO_AES256_CBC_HMAC = 0x03,   /* CBC + explicit HMAC-SHA256 */
    CW_ALGO_AES256_CTR_HMAC = 0x04,   /* CTR + explicit HMAC-SHA256 */
    CW_ALGO_COUNT           = 4
} CWAlgo;

/* ─── Threat levels ──────────────────────────────────────────────── */
typedef enum {
    CW_THREAT_NONE     = 0,
    CW_THREAT_LOW      = 1,
    CW_THREAT_MEDIUM   = 2,
    CW_THREAT_HIGH     = 3,
    CW_THREAT_CRITICAL = 4
} CWThreatLevel;

/* ─── Pipeline stage ─────────────────────────────────────────────── */
typedef struct {
    CWAlgo   algo;
    uint8_t  key[CW_MASTER_KEY_LEN];     /* derived per-stage key      */
    uint8_t  iv[CW_IV_LEN];              /* IV/nonce (12 bytes for GCM) */
    uint8_t  auth_tag[CW_AUTH_TAG_LEN];  /* output AEAD tag            */
    uint8_t  feedback_key[CW_MASTER_KEY_LEN]; /* post-feedback derived key */
    int      feedback_applied;           /* was feedback-reencrypt done */
} CWStage;

/* ─── Key store ──────────────────────────────────────────────────── */
typedef struct {
    uint8_t  master_key[CW_MASTER_KEY_LEN];
    uint8_t  salt[CW_MASTER_SALT_LEN];
    uint64_t creation_time;      /* Unix timestamp                        */
    uint64_t last_rotation;      /* Unix timestamp of last rotation       */
    uint32_t rotation_count;     /* number of rotations since genesis     */
    char     machine_id[CW_MACHINE_ID_LEN];
    uint8_t  machine_id_hash[CW_MACHINE_HASH_LEN];
    uint32_t kdf_iterations;     /* PBKDF2 iterations for key wrapping    */
} CWKeyStore;

/* ─── Main context ───────────────────────────────────────────────── */
typedef struct {
    CWStage        stages[CW_MAX_STAGES];
    int            num_stages;           /* actual stages used (3..8)  */
    CWKeyStore     keystore;
    CWThreatLevel  current_threat;
    void          *ai_state;             /* opaque CWAIState*          */
    uint32_t       flags;

    /* seal state (filled during encrypt, checked during decrypt) */
    uint32_t       seal_depth;
    uint8_t        seal_digest[CW_SEAL_DIGEST_LEN];
} CWContext;

/* ─── Result codes ───────────────────────────────────────────────── */
#define CW_OK               0
#define CW_ERR_ALLOC       -1
#define CW_ERR_CRYPTO      -2
#define CW_ERR_IO          -3
#define CW_ERR_AUTH        -4   /* authentication/tag mismatch          */
#define CW_ERR_MACHINE     -5   /* wrong machine (machine-bound key)    */
#define CW_ERR_EXPIRED     -6   /* key rotation overdue                 */
#define CW_ERR_FORMAT      -7   /* malformed ciphertext                 */
#define CW_ERR_PARAM       -8   /* invalid parameter                    */

/* ─── Public API ─────────────────────────────────────────────────── */

/*
 * Initialise a CryptWire context with a raw master key.
 * Also initialises the AI module with default state.
 * ctx         - caller-allocated CWContext
 * master_key  - raw key bytes (must be CW_MASTER_KEY_LEN = 32)
 * machine_id  - NULL to auto-derive from hardware
 */
int cw_init(CWContext *ctx, const uint8_t *master_key, const char *machine_id);

/*
 * Initialise from a saved key store file.
 * The file must have been created on this machine (machine-binding enforced).
 */
int cw_init_from_keystore(CWContext *ctx, const char *keystore_path);

/* Free all heap allocations (AI state etc.). Does NOT free ctx itself. */
void cw_free(CWContext *ctx);

/*
 * Encrypt plaintext through the full pipeline.
 * Output buffer is heap-allocated; caller must free(*ciphertext_out).
 */
int cw_encrypt(CWContext *ctx,
               const uint8_t *plaintext, size_t pt_len,
               uint8_t **ciphertext_out, size_t *ct_len_out);

/*
 * Decrypt ciphertext that was produced by cw_encrypt on this machine.
 * Output buffer is heap-allocated; caller must free(*plaintext_out).
 */
int cw_decrypt(CWContext *ctx,
               const uint8_t *ciphertext, size_t ct_len,
               uint8_t **plaintext_out, size_t *pt_len_out);

/* Rotate the master key (HKDF-expand with new salt + rotation counter). */
int cw_rotate_keys(CWContext *ctx);

/* Persist / load the key store (encrypted at rest with machine-bound key). */
int cw_save_keystore(const CWContext *ctx, const char *path);
int cw_load_keystore(CWContext *ctx, const char *path);

/*
 * Derive a machine fingerprint string from hostname + volume serial.
 * buf must be at least CW_MACHINE_ID_LEN bytes.
 */
int cw_derive_machine_id(char *buf, size_t buf_len);

/* Verify the loaded key store belongs to this machine. */
int cw_verify_machine_binding(const CWContext *ctx);

/* Query / set threat level (AI normally updates this automatically). */
CWThreatLevel cw_get_threat_level(const CWContext *ctx);
void          cw_set_threat_level(CWContext *ctx, CWThreatLevel level);

/* Report an external threat event (feeds AI learning loop). */
void cw_report_threat_event(CWContext *ctx, int threat_dim, double magnitude);

/*
 * Return a human-readable summary of the current pipeline and threat state.
 * buf must be at least 512 bytes.
 */
void cw_status_string(const CWContext *ctx, char *buf, size_t buf_len);

/* Derive a per-stage key from master_key using HKDF-SHA256.
 * info encodes stage index + feedback material. */
int cw_derive_stage_key(const uint8_t *master_key, size_t mk_len,
                        const uint8_t *salt,       size_t salt_len,
                        const uint8_t *info,       size_t info_len,
                        uint8_t *out_key,          size_t out_len);

/* Generate cryptographically random bytes (wraps RAND_bytes). */
int cw_rand_bytes(uint8_t *buf, size_t len);

#ifdef __cplusplus
}
#endif

#endif /* CRYPTWIRE_H */
