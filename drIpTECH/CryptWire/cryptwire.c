/*
 * CryptWire v0.1.0 — cryptwire.c
 * Core multi-layer adaptive encryption pipeline.
 *
 * Pipeline execution per cw_encrypt():
 *
 *   [1] Derive num_stages from AI recommendation + current threat level.
 *   [2] For each stage i = 0..n:
 *         a) Derive a per-stage key via HKDF-SHA256(master_key, salt, info_i).
 *         b) Generate a fresh random IV.
 *         c) Encrypt the input buffer with the stage's AEAD / cipher.
 *         d) If i > 0 (feedback phase):
 *              - Mix auth_tag[i-1] into a "feedback key" via HKDF.
 *              - Re-encrypt stage i-1's ciphertext buffer in-place with the
 *                feedback key (AES-256-CTR, deterministic from tag = no extra IV).
 *         e) If 0 < i < n-1 (look-ahead phase):
 *              - Ask AI for the optimal algorithm for stage i+1.
 *              - Update stages[i+1].algo accordingly.
 *   [3] Compute seal:
 *         - Concatenate all auth_tags.
 *         - depth = base_seal_depth(threat_level) + ai_seal_extra.
 *         - Run depth iterations of HMAC-SHA256 over accumulator.
 *         - If depth >= 1000: insert one convergence round
 *           (extra PBKDF2 stretch with all ciphertext as salt) at iteration 999.
 *   [4] Serialise all stage headers + ciphertexts + seal into output buffer.
 *
 * Requires: OpenSSL >= 1.1.0
 */

#include "cryptwire.h"
#include "cryptwire_ai.h"

#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <time.h>

#ifdef _WIN32
#   include <windows.h>
#else
#   include <unistd.h>
#   include <sys/utsname.h>
#endif

#include <openssl/evp.h>
#include <openssl/hmac.h>
#include <openssl/rand.h>
#include <openssl/sha.h>
#include <openssl/kdf.h>
#include <openssl/err.h>
#include <openssl/aes.h>

/* ─── Internal helpers ──────────────────────────────────────────── */

static void cw_zero(void *p, size_t n) {
#ifdef _WIN32
    SecureZeroMemory(p, n);
#else
    volatile unsigned char *v = (volatile unsigned char *)p;
    while (n--) *v++ = 0;
#endif
}

/* Write uint16 / uint32 / uint64 in little-endian order */
static void write_u16le(uint8_t *p, uint16_t v) {
    p[0] = (uint8_t)(v);
    p[1] = (uint8_t)(v >> 8);
}
static void write_u32le(uint8_t *p, uint32_t v) {
    p[0] = (uint8_t)(v);
    p[1] = (uint8_t)(v >> 8);
    p[2] = (uint8_t)(v >> 16);
    p[3] = (uint8_t)(v >> 24);
}
static void write_u64le(uint8_t *p, uint64_t v) {
    write_u32le(p,     (uint32_t)(v));
    write_u32le(p + 4, (uint32_t)(v >> 32));
}
static uint32_t read_u32le(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
static uint64_t read_u64le(const uint8_t *p) {
    return (uint64_t)read_u32le(p) | ((uint64_t)read_u32le(p + 4) << 32);
}
static uint16_t read_u16le(const uint8_t *p) {
    return (uint16_t)p[0] | ((uint16_t)p[1] << 8);
}

/* ─── Random bytes ─────────────────────────────────────────────── */
int cw_rand_bytes(uint8_t *buf, size_t len) {
    if (RAND_bytes(buf, (int)len) != 1) return CW_ERR_CRYPTO;
    return CW_OK;
}

/* ─── Key derivation (HKDF-SHA256) ─────────────────────────────── */
int cw_derive_stage_key(const uint8_t *master_key, size_t mk_len,
                        const uint8_t *salt,       size_t salt_len,
                        const uint8_t *info,       size_t info_len,
                        uint8_t *out_key,          size_t out_len) {
    EVP_PKEY_CTX *pctx = EVP_PKEY_CTX_new_id(EVP_PKEY_HKDF, NULL);
    if (!pctx) return CW_ERR_CRYPTO;

    int rc = CW_OK;
    if (EVP_PKEY_derive_init(pctx) <= 0 ||
        EVP_PKEY_CTX_set_hkdf_md(pctx, EVP_sha256()) <= 0 ||
        EVP_PKEY_CTX_set1_hkdf_salt(pctx, salt, (int)salt_len) <= 0 ||
        EVP_PKEY_CTX_set1_hkdf_key(pctx, master_key, (int)mk_len) <= 0 ||
        EVP_PKEY_CTX_add1_hkdf_info(pctx, info, (int)info_len) <= 0 ||
        EVP_PKEY_derive(pctx, out_key, &out_len) <= 0) {
        rc = CW_ERR_CRYPTO;
    }
    EVP_PKEY_CTX_free(pctx);
    return rc;
}

/* ─── Machine ID derivation ─────────────────────────────────────── */
int cw_derive_machine_id(char *buf, size_t buf_len) {
    if (!buf || buf_len < CW_MACHINE_ID_LEN) return CW_ERR_PARAM;
    char raw[256];
    memset(raw, 0, sizeof(raw));

#ifdef _WIN32
    char hostname[MAX_COMPUTERNAME_LENGTH + 1];
    DWORD hlen = sizeof(hostname);
    if (!GetComputerNameA(hostname, &hlen)) {
        strncpy(hostname, "UNKNOWN_WIN", sizeof(hostname) - 1);
    }
    /* Volume serial of C:\ */
    DWORD vol_serial = 0;
    GetVolumeInformationA("C:\\", NULL, 0, &vol_serial, NULL, NULL, NULL, 0);
    snprintf(raw, sizeof(raw), "WIN:%s:VS%08lX", hostname, (unsigned long)vol_serial);
#else
    struct utsname uts;
    if (uname(&uts) == 0) {
        snprintf(raw, sizeof(raw), "UNX:%s:%s:%s", uts.nodename,
                 uts.machine, uts.release);
    } else {
        snprintf(raw, sizeof(raw), "UNX:UNKNOWN");
    }
#endif

    /* Hash raw string with SHA-256, hex-encode into buf */
    uint8_t digest[SHA256_DIGEST_LENGTH];
    SHA256((const unsigned char *)raw, strlen(raw), digest);
    for (int i = 0; i < SHA256_DIGEST_LENGTH && (size_t)(i*2+3) < buf_len; i++) {
        snprintf(buf + i*2, 3, "%02x", (unsigned)digest[i]);
    }
    buf[buf_len - 1] = '\0';
    return CW_OK;
}

/* ─── AES-256-GCM encrypt/decrypt (single-call wrappers) ────────── */

static int aes256_gcm_encrypt(const uint8_t *key,
                               const uint8_t *iv,  /* 12 bytes */
                               const uint8_t *aad, size_t aad_len,
                               const uint8_t *pt,  size_t pt_len,
                               uint8_t *ct,        /* caller-allocated, pt_len bytes */
                               uint8_t *tag        /* 16 bytes out */) {
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) return CW_ERR_CRYPTO;

    int rc = CW_ERR_CRYPTO, outl = 0, finl = 0;
    if (EVP_EncryptInit_ex(ctx, EVP_aes_256_gcm(), NULL, NULL, NULL) != 1) goto done;
    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_IVLEN, 12, NULL) != 1) goto done;
    if (EVP_EncryptInit_ex(ctx, NULL, NULL, key, iv) != 1) goto done;
    if (aad && aad_len > 0) {
        if (EVP_EncryptUpdate(ctx, NULL, &outl, aad, (int)aad_len) != 1) goto done;
    }
    if (EVP_EncryptUpdate(ctx, ct, &outl, pt, (int)pt_len) != 1) goto done;
    if (EVP_EncryptFinal_ex(ctx, ct + outl, &finl) != 1) goto done;
    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_GET_TAG, 16, tag) != 1) goto done;
    rc = CW_OK;
done:
    EVP_CIPHER_CTX_free(ctx);
    return rc;
}

static int aes256_gcm_decrypt(const uint8_t *key,
                               const uint8_t *iv,
                               const uint8_t *aad, size_t aad_len,
                               const uint8_t *ct,  size_t ct_len,
                               const uint8_t *tag,
                               uint8_t *pt) {
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) return CW_ERR_CRYPTO;

    int rc = CW_ERR_CRYPTO, outl = 0, finl = 0;
    if (EVP_DecryptInit_ex(ctx, EVP_aes_256_gcm(), NULL, NULL, NULL) != 1) goto done;
    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_IVLEN, 12, NULL) != 1) goto done;
    if (EVP_DecryptInit_ex(ctx, NULL, NULL, key, iv) != 1) goto done;
    if (aad && aad_len > 0) {
        if (EVP_DecryptUpdate(ctx, NULL, &outl, aad, (int)aad_len) != 1) goto done;
    }
    if (EVP_DecryptUpdate(ctx, pt, &outl, ct, (int)ct_len) != 1) goto done;
    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_TAG, 16, (void *)tag) != 1) goto done;
    if (EVP_DecryptFinal_ex(ctx, pt + outl, &finl) != 1) { rc = CW_ERR_AUTH; goto done; }
    rc = CW_OK;
done:
    EVP_CIPHER_CTX_free(ctx);
    return rc;
}

/* ─── ChaCha20-Poly1305 encrypt/decrypt ─────────────────────────── */

static int chacha20_poly_encrypt(const uint8_t *key,
                                  const uint8_t *nonce, /* 12 bytes */
                                  const uint8_t *aad,   size_t aad_len,
                                  const uint8_t *pt,    size_t pt_len,
                                  uint8_t *ct,
                                  uint8_t *tag) {
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) return CW_ERR_CRYPTO;

    int rc = CW_ERR_CRYPTO, outl = 0, finl = 0;
    if (EVP_EncryptInit_ex(ctx, EVP_chacha20_poly1305(), NULL, NULL, NULL) != 1) goto done;
    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_AEAD_SET_IVLEN, 12, NULL) != 1) goto done;
    if (EVP_EncryptInit_ex(ctx, NULL, NULL, key, nonce) != 1) goto done;
    if (aad && aad_len > 0) {
        if (EVP_EncryptUpdate(ctx, NULL, &outl, aad, (int)aad_len) != 1) goto done;
    }
    if (EVP_EncryptUpdate(ctx, ct, &outl, pt, (int)pt_len) != 1) goto done;
    if (EVP_EncryptFinal_ex(ctx, ct + outl, &finl) != 1) goto done;
    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_AEAD_GET_TAG, 16, tag) != 1) goto done;
    rc = CW_OK;
done:
    EVP_CIPHER_CTX_free(ctx);
    return rc;
}

static int chacha20_poly_decrypt(const uint8_t *key,
                                  const uint8_t *nonce,
                                  const uint8_t *aad,  size_t aad_len,
                                  const uint8_t *ct,   size_t ct_len,
                                  const uint8_t *tag,
                                  uint8_t *pt) {
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) return CW_ERR_CRYPTO;

    int rc = CW_ERR_CRYPTO, outl = 0, finl = 0;
    if (EVP_DecryptInit_ex(ctx, EVP_chacha20_poly1305(), NULL, NULL, NULL) != 1) goto done;
    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_AEAD_SET_IVLEN, 12, NULL) != 1) goto done;
    if (EVP_DecryptInit_ex(ctx, NULL, NULL, key, nonce) != 1) goto done;
    if (aad && aad_len > 0) {
        if (EVP_DecryptUpdate(ctx, NULL, &outl, aad, (int)aad_len) != 1) goto done;
    }
    if (EVP_DecryptUpdate(ctx, pt, &outl, ct, (int)ct_len) != 1) goto done;
    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_AEAD_SET_TAG, 16, (void *)tag) != 1) goto done;
    if (EVP_DecryptFinal_ex(ctx, pt + outl, &finl) != 1) { rc = CW_ERR_AUTH; goto done; }
    rc = CW_OK;
done:
    EVP_CIPHER_CTX_free(ctx);
    return rc;
}

/* ─── AES-256-CBC + HMAC-SHA256 (Encrypt-then-MAC) ─────────────── */

static int aes256_cbc_hmac_encrypt(const uint8_t *key, /* 32 bytes */
                                    const uint8_t *iv,  /* 16 bytes */
                                    const uint8_t *pt,  size_t pt_len,
                                    uint8_t *ct,        /* pt_len rounded up to 16 */
                                    size_t *ct_len_out,
                                    uint8_t *tag        /* 16 bytes — first 16 of HMAC */) {
    /* Pad to 16-byte boundary (PKCS7) */
    size_t pad = 16 - (pt_len % 16);
    size_t padded = pt_len + pad;
    uint8_t *padded_buf = malloc(padded);
    if (!padded_buf) return CW_ERR_ALLOC;
    memcpy(padded_buf, pt, pt_len);
    memset(padded_buf + pt_len, (int)pad, pad);

    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) { free(padded_buf); return CW_ERR_CRYPTO; }

    int rc = CW_ERR_CRYPTO, outl = 0, finl = 0;
    EVP_CIPHER_CTX_set_padding(ctx, 0);
    if (EVP_EncryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, key, iv) != 1) goto done;
    if (EVP_EncryptUpdate(ctx, ct, &outl, padded_buf, (int)padded) != 1) goto done;
    if (EVP_EncryptFinal_ex(ctx, ct + outl, &finl) != 1) goto done;
    *ct_len_out = (size_t)(outl + finl);

    /* HMAC-SHA256 over IV || ciphertext, use key[16..32] as MAC key */
    uint8_t hmac_out[32];
    unsigned int hmac_len = 32;
    HMAC(EVP_sha256(), key + 16, 16, ct, *ct_len_out, hmac_out, &hmac_len);
    memcpy(tag, hmac_out, 16);  /* store first 16 bytes as auth tag */
    rc = CW_OK;
done:
    EVP_CIPHER_CTX_free(ctx);
    cw_zero(padded_buf, padded);
    free(padded_buf);
    return rc;
}

static int aes256_cbc_hmac_decrypt(const uint8_t *key,
                                    const uint8_t *iv,
                                    const uint8_t *ct,  size_t ct_len,
                                    const uint8_t *tag, /* expected 16-byte tag */
                                    uint8_t *pt,
                                    size_t *pt_len_out) {
    /* Verify MAC before decrypting (Encrypt-then-MAC) */
    uint8_t hmac_out[32];
    unsigned int hmac_len = 32;
    HMAC(EVP_sha256(), key + 16, 16, ct, ct_len, hmac_out, &hmac_len);
    /* Constant-time comparison */
    int diff = 0;
    for (int i = 0; i < 16; i++) diff |= (hmac_out[i] ^ tag[i]);
    if (diff != 0) return CW_ERR_AUTH;

    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) return CW_ERR_CRYPTO;

    int rc = CW_ERR_CRYPTO, outl = 0, finl = 0;
    EVP_CIPHER_CTX_set_padding(ctx, 0);
    if (EVP_DecryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, key, iv) != 1) goto done;
    if (EVP_DecryptUpdate(ctx, pt, &outl, ct, (int)ct_len) != 1) goto done;
    if (EVP_DecryptFinal_ex(ctx, pt + outl, &finl) != 1) goto done;

    /* Strip PKCS7 padding */
    size_t total = (size_t)(outl + finl);
    uint8_t pad_val = pt[total - 1];
    if (pad_val == 0 || pad_val > 16) { rc = CW_ERR_AUTH; goto done; }
    for (size_t i = total - pad_val; i < total; i++) {
        if (pt[i] != pad_val) { rc = CW_ERR_AUTH; goto done; }
    }
    *pt_len_out = total - pad_val;
    rc = CW_OK;
done:
    EVP_CIPHER_CTX_free(ctx);
    return rc;
}

/* ─── Single-stage encrypt/decrypt dispatch ─────────────────────── */

static int stage_encrypt(const CWStage *s,
                          const uint8_t *pt, size_t pt_len,
                          uint8_t *ct, size_t *ct_len_out,
                          uint8_t *auth_tag) {
    const uint8_t *key = s->feedback_applied ? s->feedback_key : s->key;
    /* AAD: algo_id byte for domain separation */
    uint8_t aad[1] = { (uint8_t)s->algo };

    switch (s->algo) {
    case CW_ALGO_AES256_GCM:
        *ct_len_out = pt_len;
        return aes256_gcm_encrypt(key, s->iv, aad, 1, pt, pt_len, ct, auth_tag);
    case CW_ALGO_CHACHA20_POLY:
        *ct_len_out = pt_len;
        return chacha20_poly_encrypt(key, s->iv, aad, 1, pt, pt_len, ct, auth_tag);
    case CW_ALGO_AES256_CBC_HMAC:
        return aes256_cbc_hmac_encrypt(key, s->iv, pt, pt_len,
                                        ct, ct_len_out, auth_tag);
    default:
        /* Default to AES-256-GCM */
        *ct_len_out = pt_len;
        return aes256_gcm_encrypt(key, s->iv, aad, 1, pt, pt_len, ct, auth_tag);
    }
}

static int stage_decrypt(const CWStage *s,
                          const uint8_t *ct, size_t ct_len,
                          const uint8_t *auth_tag,
                          uint8_t *pt, size_t *pt_len_out) {
    const uint8_t *key = s->feedback_applied ? s->feedback_key : s->key;
    uint8_t aad[1] = { (uint8_t)s->algo };

    switch (s->algo) {
    case CW_ALGO_AES256_GCM:
        *pt_len_out = ct_len;
        return aes256_gcm_decrypt(key, s->iv, aad, 1, ct, ct_len, auth_tag, pt);
    case CW_ALGO_CHACHA20_POLY:
        *pt_len_out = ct_len;
        return chacha20_poly_decrypt(key, s->iv, aad, 1, ct, ct_len, auth_tag, pt);
    case CW_ALGO_AES256_CBC_HMAC:
        return aes256_cbc_hmac_decrypt(key, s->iv, ct, ct_len, auth_tag,
                                        pt, pt_len_out);
    default:
        *pt_len_out = ct_len;
        return aes256_gcm_decrypt(key, s->iv, aad, 1, ct, ct_len, auth_tag, pt);
    }
}

/* ─── Feedback reencryption (AES-256-CTR, deterministic key from tag) */
/* Reencrypt a ciphertext buffer in-place using a key derived from the
 * next stage's auth tag.  AES-256-CTR is used because it is a pure XOR
 * stream cipher: applying it twice restores the original (involutory). */
static int feedback_reencrypt(const uint8_t *auth_tag_next,
                               const uint8_t *master_key,
                               uint8_t *buf, size_t buf_len) {
    /* Derive a 32-byte feedback key from master_key and auth_tag_next */
    uint8_t fb_key[32];
    uint8_t info[17] = { 0x46, 0x42, 0x4B }; /* "FBK" prefix */
    memcpy(info + 3, auth_tag_next, 16);
    /* Use the auth tag itself as the HKDF salt for maximal entropy mixing */
    int rc = cw_derive_stage_key(master_key, CW_MASTER_KEY_LEN,
                                  auth_tag_next, CW_AUTH_TAG_LEN,
                                  info, 19,
                                  fb_key, 32);
    if (rc != CW_OK) return rc;

    /* AES-256-CTR with counter IV = first 16 bytes of tag (padded/truncated) */
    uint8_t ctr_iv[16];
    memcpy(ctr_iv, auth_tag_next, 16);

    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) return CW_ERR_CRYPTO;

    rc = CW_ERR_CRYPTO;
    int outl = 0, finl = 0;
    if (EVP_EncryptInit_ex(ctx, EVP_aes_256_ctr(), NULL, fb_key, ctr_iv) == 1 &&
        EVP_EncryptUpdate(ctx, buf, &outl, buf, (int)buf_len) == 1 &&
        EVP_EncryptFinal_ex(ctx, buf + outl, &finl) == 1) {
        rc = CW_OK;
    }
    EVP_CIPHER_CTX_free(ctx);
    cw_zero(fb_key, 32);
    return rc;
}

/* ─── Final SEAL computation ─────────────────────────────────────── */
/*
 * Seal iteratively applies HMAC-SHA256 to an accumulator seeded with
 * all stage auth tags concatenated.  At iteration 999 (if depth >= 1000),
 * one convergence round is inserted: a PBKDF2 stretch that folds in all
 * ciphertext data as additional entropy, making brute-force even costlier.
 */
static int compute_seal(const CWContext *ctx,
                         const uint8_t **ct_bufs, const size_t *ct_lens,
                         uint32_t depth,
                         uint8_t *seal_out /* 32 bytes */) {
    /* Seed: concatenation of all stage auth tags */
    uint8_t seed[CW_MAX_STAGES * CW_AUTH_TAG_LEN];
    size_t seed_len = 0;
    for (int i = 0; i < ctx->num_stages; i++) {
        memcpy(seed + seed_len, ctx->stages[i].auth_tag, CW_AUTH_TAG_LEN);
        seed_len += CW_AUTH_TAG_LEN;
    }

    uint8_t acc[32];
    /* Initial HMAC: HMAC-SHA256(master_key, seed) */
    unsigned int hlen = 32;
    HMAC(EVP_sha256(), ctx->keystore.master_key, CW_MASTER_KEY_LEN,
         seed, seed_len, acc, &hlen);

    for (uint32_t iter = 0; iter < depth; iter++) {
        /* Convergence round at iteration 999 when depth >= 1000 */
        if (iter == 999 && depth >= 1000) {
            /* Construct a combined salt from all ciphertext data */
            uint8_t ct_hash[32];
            EVP_MD_CTX *mctx = EVP_MD_CTX_new();
            EVP_DigestInit_ex(mctx, EVP_sha256(), NULL);
            for (int s = 0; s < ctx->num_stages; s++) {
                EVP_DigestUpdate(mctx, ct_bufs[s], ct_lens[s]);
            }
            EVP_DigestFinal_ex(mctx, ct_hash, NULL);
            EVP_MD_CTX_free(mctx);

            /* PBKDF2-HMAC-SHA256: 8192 iterations, salt=ct_hash, key=acc */
            uint8_t stretched[32];
            PKCS5_PBKDF2_HMAC((const char *)acc, 32,
                               ct_hash, 32,
                               8192, EVP_sha256(),
                               32, stretched);
            memcpy(acc, stretched, 32);
            cw_zero(stretched, 32);
            cw_zero(ct_hash, 32);
        }

        /* Standard iteration: HMAC-SHA256(master_key, acc || iter_bytes) */
        uint8_t iter_buf[36];
        memcpy(iter_buf, acc, 32);
        write_u32le(iter_buf + 32, iter);
        HMAC(EVP_sha256(), ctx->keystore.master_key, CW_MASTER_KEY_LEN,
             iter_buf, 36, acc, &hlen);
    }

    memcpy(seal_out, acc, 32);
    cw_zero(seed, sizeof(seed));
    cw_zero(acc, 32);
    return CW_OK;
}

/* ─── Seal depth from threat level ─────────────────────────────── */
static uint32_t base_seal_depth(CWThreatLevel t) {
    switch (t) {
    case CW_THREAT_NONE:     return CW_SEAL_DEPTH_NONE;
    case CW_THREAT_LOW:      return CW_SEAL_DEPTH_LOW;
    case CW_THREAT_MEDIUM:   return CW_SEAL_DEPTH_MEDIUM;
    case CW_THREAT_HIGH:     return CW_SEAL_DEPTH_HIGH;
    case CW_THREAT_CRITICAL: return CW_SEAL_DEPTH_CRITICAL;
    default:                 return CW_SEAL_DEPTH_NONE;
    }
}

/* ─── cw_init ───────────────────────────────────────────────────── */
int cw_init(CWContext *ctx, const uint8_t *master_key, const char *machine_id) {
    if (!ctx || !master_key) return CW_ERR_PARAM;
    memset(ctx, 0, sizeof(CWContext));

    memcpy(ctx->keystore.master_key, master_key, CW_MASTER_KEY_LEN);
    cw_rand_bytes(ctx->keystore.salt, CW_MASTER_SALT_LEN);
    ctx->keystore.creation_time  = (uint64_t)time(NULL);
    ctx->keystore.last_rotation  = ctx->keystore.creation_time;
    ctx->keystore.rotation_count = 0;
    ctx->keystore.kdf_iterations = 100000;

    if (machine_id) {
        strncpy(ctx->keystore.machine_id, machine_id, CW_MACHINE_ID_LEN - 1);
    } else {
        cw_derive_machine_id(ctx->keystore.machine_id, CW_MACHINE_ID_LEN);
    }
    SHA256((const unsigned char *)ctx->keystore.machine_id,
           strlen(ctx->keystore.machine_id),
           ctx->keystore.machine_id_hash);

    ctx->num_stages     = 3;   /* default; AI may increase this */
    ctx->current_threat = CW_THREAT_NONE;
    ctx->ai_state       = cw_ai_init();
    if (!ctx->ai_state) return CW_ERR_ALLOC;

    return CW_OK;
}

/* ─── cw_free ───────────────────────────────────────────────────── */
void cw_free(CWContext *ctx) {
    if (!ctx) return;
    if (ctx->ai_state) {
        cw_ai_free((CWAIState *)ctx->ai_state);
        ctx->ai_state = NULL;
    }
    cw_zero(ctx->keystore.master_key, CW_MASTER_KEY_LEN);
    cw_zero(ctx, sizeof(CWContext));
}

/* ─── cw_encrypt ─────────────────────────────────────────────────── */
int cw_encrypt(CWContext *ctx,
               const uint8_t *plaintext, size_t pt_len,
               uint8_t **ciphertext_out, size_t *ct_len_out) {
    if (!ctx || !plaintext || !ciphertext_out || !ct_len_out) return CW_ERR_PARAM;

    CWAIState *ai = (CWAIState *)ctx->ai_state;

    /* 1. Determine number of stages from AI + threat level */
    int n = cw_ai_recommend_num_stages(ai);
    if (n < 3) n = 3;
    if (n > CW_MAX_STAGES) n = CW_MAX_STAGES;
    ctx->num_stages = n;

    /* 2. Pre-derive all stage parameters */
    for (int i = 0; i < n; i++) {
        /* Look-ahead: get AI recommendation for this stage */
        ctx->stages[i].algo = (CWAlgo)cw_ai_recommend_algo(ai, i);

        /* Derive per-stage key: HKDF(master, salt, "CW_STAGE" || i) */
        uint8_t info[12];
        memcpy(info, "CW_STAGE", 8);
        write_u32le(info + 8, (uint32_t)i);
        cw_derive_stage_key(ctx->keystore.master_key, CW_MASTER_KEY_LEN,
                            ctx->keystore.salt, CW_MASTER_SALT_LEN,
                            info, 12,
                            ctx->stages[i].key, 32);

        /* Generate fresh random IV for this stage */
        cw_rand_bytes(ctx->stages[i].iv, CW_IV_LEN);
        ctx->stages[i].feedback_applied = 0;
    }

    /* 3. Allocate per-stage ciphertext buffers
     *    Max overhead per stage: +16 (PKCS7 padding possibility) */
    uint8_t **ct_bufs = calloc(n, sizeof(uint8_t *));
    size_t   *ct_lens  = calloc(n, sizeof(size_t));
    if (!ct_bufs || !ct_lens) {
        free(ct_bufs); free(ct_lens);
        return CW_ERR_ALLOC;
    }

    const uint8_t *current_input    = plaintext;
    size_t         current_input_len = pt_len;
    int rc = CW_OK;

    /* 4. Forward pass: encrypt each stage */
    for (int i = 0; i < n; i++) {
        size_t max_ct = current_input_len + 32; /* headroom for CBC pad */
        ct_bufs[i] = malloc(max_ct);
        if (!ct_bufs[i]) { rc = CW_ERR_ALLOC; goto cleanup; }

        rc = stage_encrypt(&ctx->stages[i],
                           current_input, current_input_len,
                           ct_bufs[i], &ct_lens[i],
                           ctx->stages[i].auth_tag);
        if (rc != CW_OK) goto cleanup;

        current_input     = ct_bufs[i];
        current_input_len = ct_lens[i];
    }

    /* 5. Feedback reencryption pass (stages 1..n-1 feed back into stage i-1) */
    for (int i = 1; i < n; i++) {
        /* auth_tag[i] feeds back into stage i-1 ciphertext */
        rc = feedback_reencrypt(ctx->stages[i].auth_tag,
                                 ctx->keystore.master_key,
                                 ct_bufs[i - 1], ct_lens[i - 1]);
        if (rc != CW_OK) goto cleanup;

        /* Record that stage i-1 now uses feedback-derived effective key
         * (needed for correct serialisation — decoder re-applies identical
         *  feedback_reencrypt using the recorded auth_tag) */
        ctx->stages[i - 1].feedback_applied = 1;
    }

    /* 6. Compute final seal */
    uint32_t seal_depth = base_seal_depth(ctx->current_threat)
                        + cw_ai_recommend_seal_extra(ai);
    ctx->seal_depth = seal_depth;

    rc = compute_seal(ctx,
                      (const uint8_t **)ct_bufs, ct_lens,
                      seal_depth, ctx->seal_digest);
    if (rc != CW_OK) goto cleanup;

    /* 7. Serialise to wire format */
    /*
     * Header: 4(magic) + 2(ver) + 1(num) + 1(flags) + 8(ts) + 32(machine_hash)
     *       = 48 bytes
     * Per stage: 1(algo) + 1(rsvd) + 16(iv) + 16(tag) + 4(clen) + ct
     *          = 38 + ct bytes
     * Trailer: 4(seal_depth) + 32(seal_digest) = 36 bytes
     */
    size_t total = 48;
    for (int i = 0; i < n; i++) total += 38 + ct_lens[i];
    total += 36;

    uint8_t *out = malloc(total);
    if (!out) { rc = CW_ERR_ALLOC; goto cleanup; }

    uint8_t *p = out;
    memcpy(p, CW_MAGIC, 4);        p += 4;
    write_u16le(p, 0x0001);        p += 2;
    *p++ = (uint8_t)n;
    *p++ = 0x00;                   /* flags reserved */
    write_u64le(p, (uint64_t)time(NULL)); p += 8;
    memcpy(p, ctx->keystore.machine_id_hash, 32); p += 32;

    for (int i = 0; i < n; i++) {
        *p++ = (uint8_t)ctx->stages[i].algo;
        *p++ = 0x00;                /* reserved */
        memcpy(p, ctx->stages[i].iv, CW_IV_LEN);       p += 16;
        memcpy(p, ctx->stages[i].auth_tag, CW_AUTH_TAG_LEN); p += 16;
        write_u32le(p, (uint32_t)ct_lens[i]);           p += 4;
        memcpy(p, ct_bufs[i], ct_lens[i]);              p += ct_lens[i];
    }

    write_u32le(p, seal_depth);  p += 4;
    memcpy(p, ctx->seal_digest, CW_SEAL_DIGEST_LEN);

    *ciphertext_out = out;
    *ct_len_out     = total;
    rc = CW_OK;

cleanup:
    for (int i = 0; i < n; i++) {
        if (ct_bufs[i]) {
            cw_zero(ct_bufs[i], ct_lens[i]);
            free(ct_bufs[i]);
        }
    }
    free(ct_bufs);
    free(ct_lens);
    return rc;
}

/* ─── cw_decrypt ─────────────────────────────────────────────────── */
int cw_decrypt(CWContext *ctx,
               const uint8_t *ciphertext, size_t ct_len,
               uint8_t **plaintext_out, size_t *pt_len_out) {
    if (!ctx || !ciphertext || !plaintext_out || !pt_len_out) return CW_ERR_PARAM;

    /* Parse header */
    if (ct_len < 84) return CW_ERR_FORMAT;  /* minimum viable packet */
    const uint8_t *p = ciphertext;

    if (memcmp(p, CW_MAGIC, 4) != 0) return CW_ERR_FORMAT;
    p += 4;
    uint16_t ver = read_u16le(p); p += 2;
    if (ver != 0x0001) return CW_ERR_FORMAT;

    int n = (int)*p++;
    p++;  /* flags */
    p += 8;  /* timestamp */

    /* Verify machine binding */
    uint8_t expected_machine_hash[32];
    SHA256((const unsigned char *)ctx->keystore.machine_id,
           strlen(ctx->keystore.machine_id), expected_machine_hash);
    if (memcmp(p, expected_machine_hash, 32) != 0) return CW_ERR_MACHINE;
    p += 32;

    if (n < 1 || n > CW_MAX_STAGES) return CW_ERR_FORMAT;

    /* Parse per-stage headers and ciphertext slices */
    uint8_t  *ct_bufs[CW_MAX_STAGES] = {0};
    size_t    ct_lens[CW_MAX_STAGES]  = {0};
    CWStage   dec_stages[CW_MAX_STAGES];
    memset(dec_stages, 0, sizeof(dec_stages));

    const uint8_t *end = ciphertext + ct_len - 36; /* leave room for trailer */
    int rc = CW_OK;

    for (int i = 0; i < n; i++) {
        if (p + 38 > end) { rc = CW_ERR_FORMAT; goto cleanup; }
        dec_stages[i].algo = (CWAlgo)*p++;
        p++;  /* reserved */
        memcpy(dec_stages[i].iv, p, 16);       p += 16;
        memcpy(dec_stages[i].auth_tag, p, 16); p += 16;
        uint32_t this_ct_len = read_u32le(p);  p += 4;
        if (p + this_ct_len > end) { rc = CW_ERR_FORMAT; goto cleanup; }

        ct_lens[i]  = this_ct_len;
        ct_bufs[i]  = malloc(this_ct_len + 32);
        if (!ct_bufs[i]) { rc = CW_ERR_ALLOC; goto cleanup; }
        memcpy(ct_bufs[i], p, this_ct_len);
        p += this_ct_len;
    }

    /* Parse trailer */
    uint32_t stored_seal_depth  = read_u32le(p); p += 4;
    const uint8_t *stored_seal  = p;

    /* Re-derive all stage keys from master key */
    for (int i = 0; i < n; i++) {
        uint8_t info[12];
        memcpy(info, "CW_STAGE", 8);
        write_u32le(info + 8, (uint32_t)i);
        cw_derive_stage_key(ctx->keystore.master_key, CW_MASTER_KEY_LEN,
                            ctx->keystore.salt, CW_MASTER_SALT_LEN,
                            info, 12,
                            dec_stages[i].key, 32);
        dec_stages[i].feedback_applied = 0;
    }

    /* Re-apply feedback reencryption (same as encrypt: for i=1..n-1,
     * stage i auth_tag feeds back into ct_bufs[i-1]) */
    for (int i = 1; i < n; i++) {
        rc = feedback_reencrypt(dec_stages[i].auth_tag,
                                 ctx->keystore.master_key,
                                 ct_bufs[i - 1], ct_lens[i - 1]);
        if (rc != CW_OK) goto cleanup;
    }

    /* Verify seal before decrypting any stage */
    /* Temporarily copy parsed stages into context for seal computation */
    int saved_n = ctx->num_stages;
    memcpy(ctx->stages, dec_stages, n * sizeof(CWStage));
    ctx->num_stages = n;

    uint8_t recomputed_seal[32];
    rc = compute_seal(ctx,
                      (const uint8_t **)ct_bufs, ct_lens,
                      stored_seal_depth, recomputed_seal);
    ctx->num_stages = saved_n;
    if (rc != CW_OK) goto cleanup;

    int seal_diff = 0;
    for (int i = 0; i < 32; i++) seal_diff |= (recomputed_seal[i] ^ stored_seal[i]);
    if (seal_diff != 0) { rc = CW_ERR_AUTH; goto cleanup; }

    /* Decrypt in reverse stage order */
    uint8_t *dec_bufs[CW_MAX_STAGES] = {0};
    size_t   dec_lens[CW_MAX_STAGES]  = {0};

    for (int i = n - 1; i >= 0; i--) {
        dec_bufs[i] = malloc(ct_lens[i] + 16);
        if (!dec_bufs[i]) { rc = CW_ERR_ALLOC; goto dec_cleanup; }

        rc = stage_decrypt(&dec_stages[i],
                           ct_bufs[i], ct_lens[i],
                           dec_stages[i].auth_tag,
                           dec_bufs[i], &dec_lens[i]);
        if (rc != CW_OK) goto dec_cleanup;
    }

    /* The stage-0 decrypted output is the original plaintext */
    *plaintext_out = dec_bufs[0];
    *pt_len_out    = dec_lens[0];
    dec_bufs[0]    = NULL;  /* ownership transferred */

dec_cleanup:
    for (int i = 1; i < n; i++) {
        if (dec_bufs[i]) { cw_zero(dec_bufs[i], dec_lens[i]); free(dec_bufs[i]); }
    }
cleanup:
    for (int i = 0; i < n; i++) {
        if (ct_bufs[i]) { cw_zero(ct_bufs[i], ct_lens[i]); free(ct_bufs[i]); }
    }
    return rc;
}

/* ─── cw_rotate_keys ─────────────────────────────────────────────── */
int cw_rotate_keys(CWContext *ctx) {
    if (!ctx) return CW_ERR_PARAM;
    /* New master key = HKDF-expand(old_master, new_salt, "CW_ROTATE" || count) */
    uint8_t new_salt[CW_MASTER_SALT_LEN];
    cw_rand_bytes(new_salt, CW_MASTER_SALT_LEN);

    uint8_t info[13];
    memcpy(info, "CW_ROTATE", 9);
    write_u32le(info + 9, ctx->keystore.rotation_count + 1);

    uint8_t new_key[CW_MASTER_KEY_LEN];
    int rc = cw_derive_stage_key(ctx->keystore.master_key, CW_MASTER_KEY_LEN,
                                  new_salt, CW_MASTER_SALT_LEN,
                                  info, 13,
                                  new_key, CW_MASTER_KEY_LEN);
    if (rc != CW_OK) return rc;

    cw_zero(ctx->keystore.master_key, CW_MASTER_KEY_LEN);
    memcpy(ctx->keystore.master_key, new_key, CW_MASTER_KEY_LEN);
    memcpy(ctx->keystore.salt, new_salt, CW_MASTER_SALT_LEN);
    ctx->keystore.last_rotation = (uint64_t)time(NULL);
    ctx->keystore.rotation_count++;

    cw_zero(new_key, CW_MASTER_KEY_LEN);
    return CW_OK;
}

/* ─── Keystore persistence ───────────────────────────────────────── */
/*
 * The keystore is persisted as:
 *   [4] magic "CWKS"
 *   [4] version 0x0001
 *   [32] encrypted payload (AES-256-GCM, key derived from machine-id PBKDF2)
 *   ... actually: 16 IV + 16 tag + sizeof(CWKeyStore) bytes ciphertext
 */
int cw_save_keystore(const CWContext *ctx, const char *path) {
    if (!ctx || !path) return CW_ERR_PARAM;

    /* Derive file-encryption key from machine_id using PBKDF2 */
    uint8_t file_key[32];
    uint8_t pbkdf2_salt[32];
    /* Fixed salt derived from machine_id hash so it's reproducible on same machine */
    SHA256((const unsigned char *)ctx->keystore.machine_id_hash, 32, pbkdf2_salt);
    PKCS5_PBKDF2_HMAC(ctx->keystore.machine_id, (int)strlen(ctx->keystore.machine_id),
                      pbkdf2_salt, 32,
                      ctx->keystore.kdf_iterations,
                      EVP_sha256(), 32, file_key);

    uint8_t iv[12];
    cw_rand_bytes(iv, 12);
    uint8_t ct[sizeof(CWKeyStore) + 16];
    uint8_t tag[16];
    size_t ct_len;
    uint8_t aad[4] = { 0x43, 0x57, 0x4B, 0x53 }; /* "CWKS" */

    int rc = aes256_gcm_encrypt(file_key, iv, aad, 4,
                                 (const uint8_t *)&ctx->keystore, sizeof(CWKeyStore),
                                 ct, tag);
    cw_zero(file_key, 32);
    if (rc != CW_OK) return rc;
    ct_len = sizeof(CWKeyStore);

    FILE *f = fopen(path, "wb");
    if (!f) return CW_ERR_IO;
    fwrite("CWKS", 1, 4, f);
    uint8_t ver[4]; write_u32le(ver, 0x0001); fwrite(ver, 1, 4, f);
    fwrite(iv, 1, 12, f);
    fwrite(tag, 1, 16, f);
    fwrite(ct, 1, ct_len, f);
    fclose(f);
    return CW_OK;
}

int cw_load_keystore(CWContext *ctx, const char *path) {
    if (!ctx || !path) return CW_ERR_PARAM;

    FILE *f = fopen(path, "rb");
    if (!f) return CW_ERR_IO;

    char magic[4];
    uint8_t ver_buf[4], iv[12], tag[16];
    uint8_t ct[sizeof(CWKeyStore)];

    if (fread(magic, 1, 4, f) != 4 || memcmp(magic, "CWKS", 4) != 0 ||
        fread(ver_buf, 1, 4, f) != 4 ||
        fread(iv, 1, 12, f) != 12 ||
        fread(tag, 1, 16, f) != 16 ||
        fread(ct, 1, sizeof(CWKeyStore), f) != sizeof(CWKeyStore)) {
        fclose(f); return CW_ERR_IO;
    }
    fclose(f);

    /* Derive machine id first (to derive the file key) */
    char machine_id[CW_MACHINE_ID_LEN];
    cw_derive_machine_id(machine_id, CW_MACHINE_ID_LEN);

    uint8_t machine_hash[32];
    SHA256((const unsigned char *)machine_id, strlen(machine_id), machine_hash);

    uint8_t pbkdf2_salt[32];
    SHA256(machine_hash, 32, pbkdf2_salt);

    uint8_t file_key[32];
    PKCS5_PBKDF2_HMAC(machine_id, (int)strlen(machine_id),
                      pbkdf2_salt, 32, 100000,
                      EVP_sha256(), 32, file_key);

    CWKeyStore ks;
    size_t pt_len;
    uint8_t aad[4] = { 0x43, 0x57, 0x4B, 0x53 };
    int rc = aes256_gcm_decrypt(file_key, iv, aad, 4,
                                 ct, sizeof(CWKeyStore), tag,
                                 (uint8_t *)&ks);
    cw_zero(file_key, 32);
    if (rc != CW_OK) return (rc == CW_ERR_AUTH) ? CW_ERR_MACHINE : rc;
    (void)pt_len;

    memcpy(&ctx->keystore, &ks, sizeof(CWKeyStore));
    cw_zero(&ks, sizeof(CWKeyStore));
    return CW_OK;
}

/* ─── Machine binding verification ─────────────────────────────── */
int cw_verify_machine_binding(const CWContext *ctx) {
    if (!ctx) return CW_ERR_PARAM;
    char current_id[CW_MACHINE_ID_LEN];
    cw_derive_machine_id(current_id, CW_MACHINE_ID_LEN);
    uint8_t current_hash[32];
    SHA256((const unsigned char *)current_id, strlen(current_id), current_hash);
    int diff = 0;
    for (int i = 0; i < 32; i++) diff |= (current_hash[i] ^ ctx->keystore.machine_id_hash[i]);
    return (diff == 0) ? CW_OK : CW_ERR_MACHINE;
}

/* ─── Threat level accessors ─────────────────────────────────────── */
CWThreatLevel cw_get_threat_level(const CWContext *ctx) {
    return ctx ? ctx->current_threat : CW_THREAT_NONE;
}
void cw_set_threat_level(CWContext *ctx, CWThreatLevel level) {
    if (ctx) ctx->current_threat = level;
}
void cw_report_threat_event(CWContext *ctx, int dim, double mag) {
    if (!ctx || !ctx->ai_state) return;
    cw_ai_observe((CWAIState *)ctx->ai_state, dim, (float)mag, 0.0);
    /* Update aggregate threat level based on AI score */
    double score = cw_ai_aggregate_score((CWAIState *)ctx->ai_state);
    if (score < 0.2)      ctx->current_threat = CW_THREAT_NONE;
    else if (score < 0.4) ctx->current_threat = CW_THREAT_LOW;
    else if (score < 0.6) ctx->current_threat = CW_THREAT_MEDIUM;
    else if (score < 0.8) ctx->current_threat = CW_THREAT_HIGH;
    else                  ctx->current_threat = CW_THREAT_CRITICAL;
}

/* ─── Status summary ─────────────────────────────────────────────── */
void cw_status_string(const CWContext *ctx, char *buf, size_t buf_len) {
    if (!ctx || !buf || buf_len < 16) return;
    const char *threat_names[] = { "NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL" };
    const char *algo_names[]   = { "?", "AES-256-GCM", "ChaCha20-Poly1305",
                                   "AES-256-CBC+HMAC", "AES-256-CTR+HMAC" };
    int t = (int)ctx->current_threat;
    if (t < 0 || t > 4) t = 0;

    int offset = snprintf(buf, buf_len,
        "CryptWire v0.1 | Stages: %d | Threat: %s | Seal depth: %u\n"
        "Key rotations: %u | Machine: %.16s...\nPipeline: ",
        ctx->num_stages, threat_names[t], ctx->seal_depth,
        ctx->keystore.rotation_count, ctx->keystore.machine_id);

    for (int i = 0; i < ctx->num_stages && offset < (int)buf_len - 32; i++) {
        int a = (int)ctx->stages[i].algo;
        if (a < 0 || a > 4) a = 0;
        offset += snprintf(buf + offset, buf_len - offset,
                           "%s%s", (i > 0 ? " -> " : ""), algo_names[a]);
    }
    snprintf(buf + offset, buf_len - offset, "\n");
}
