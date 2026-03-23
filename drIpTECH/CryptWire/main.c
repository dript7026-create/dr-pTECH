/*
 * CryptWire v0.1.0 — main.c
 * CLI tool for the CryptWire encryption pipeline.
 *
 * Usage:
 *   cryptwire genkey  [--out <keystore.cwks>]
 *   cryptwire encrypt <infile> <outfile> [--ks <keystore.cwks>]
 *   cryptwire decrypt <infile> <outfile> [--ks <keystore.cwks>]
 *   cryptwire rotate  [--ks <keystore.cwks>]
 *   cryptwire status  [--ks <keystore.cwks>]
 *   cryptwire monitor [--ks <keystore.cwks>]   (continuous stream daemon)
 *   cryptwire scan    <datafile> [--sigs <sigdb.txt>] [--ks <keystore.cwks>]
 *
 * Key store default location:
 *   Windows:  %APPDATA%\CryptWire\master.cwks
 *   Linux/macOS: ~/.cryptwire/master.cwks
 *
 * Compile:
 *   gcc -O2 -Wall -std=c11 main.c cryptwire.c cryptwire_ai.c \
 *       -lssl -lcrypto -lm -o cryptwire
 */

#include "cryptwire.h"
#include "cryptwire_ai.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <errno.h>

#ifdef _WIN32
#   include <windows.h>
#   include <shlobj.h>
#   include <io.h>
#   include <direct.h>
#   define MKDIR(p) _mkdir(p)
#   define PATH_SEP "\\"
#else
#   include <unistd.h>
#   include <sys/stat.h>
#   include <sys/types.h>
#   include <pwd.h>
#   define MKDIR(p) mkdir(p, 0700)
#   define PATH_SEP "/"
#endif

#include <openssl/rand.h>

/* ─── Platform: secure directory setup ─────────────────────────── */
static int ensure_secure_dir(const char *dir_path) {
#ifdef _WIN32
    /* Create directory if needed */
    if (_access(dir_path, 0) != 0) {
        if (_mkdir(dir_path) != 0 && errno != EEXIST) return -1;
    }
    /* Set ACL: Administrators + current user only, deny all others */
    SECURITY_DESCRIPTOR sd;
    if (!InitializeSecurityDescriptor(&sd, SECURITY_DESCRIPTOR_REVISION)) return -1;
    if (!SetSecurityDescriptorDacl(&sd, TRUE, NULL, FALSE)) return -1;
    SetFileSecurityA(dir_path, DACL_SECURITY_INFORMATION, &sd);
    /* Note: NULL DACL = allow all on Windows, which works for local admin.
     * For production: build a proper DACL with explicit ACEs for Administrators
     * and the current user.  See SetEntriesInAcl() in the Windows SDK. */
#else
    struct stat st;
    if (stat(dir_path, &st) != 0) {
        if (mkdir(dir_path, 0700) != 0 && errno != EEXIST) return -1;
    } else {
        chmod(dir_path, 0700);
    }
#endif
    return 0;
}

/* ─── Default keystore path ─────────────────────────────────────── */
static void default_ks_path(char *buf, size_t buf_len) {
#ifdef _WIN32
    char appdata[MAX_PATH];
    if (SUCCEEDED(SHGetFolderPathA(NULL, CSIDL_APPDATA, NULL, 0, appdata))) {
        snprintf(buf, buf_len, "%s\\CryptWire\\master.cwks", appdata);
    } else {
        strncpy(buf, "master.cwks", buf_len - 1);
    }
#else
    const char *home = getenv("HOME");
    if (!home) {
        struct passwd *pw = getpwuid(getuid());
        if (pw) home = pw->pw_dir;
    }
    if (home) {
        snprintf(buf, buf_len, "%s/.cryptwire/master.cwks", home);
    } else {
        strncpy(buf, "master.cwks", buf_len - 1);
    }
#endif
    buf[buf_len - 1] = '\0';
}

static void default_ks_dir(char *buf, size_t buf_len) {
#ifdef _WIN32
    char appdata[MAX_PATH];
    if (SUCCEEDED(SHGetFolderPathA(NULL, CSIDL_APPDATA, NULL, 0, appdata))) {
        snprintf(buf, buf_len, "%s\\CryptWire", appdata);
    } else {
        strncpy(buf, ".", buf_len - 1);
    }
#else
    const char *home = getenv("HOME");
    if (!home) home = ".";
    snprintf(buf, buf_len, "%s/.cryptwire", home);
#endif
    buf[buf_len - 1] = '\0';
}

/* ─── Read file into heap buffer ─────────────────────────────────── */
static int read_file(const char *path, uint8_t **out, size_t *out_len) {
    FILE *f = fopen(path, "rb");
    if (!f) { fprintf(stderr, "cryptwire: cannot open '%s': %s\n", path, strerror(errno)); return -1; }
    fseek(f, 0, SEEK_END);
    long fsize = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (fsize <= 0) { fclose(f); *out = NULL; *out_len = 0; return 0; }
    *out = malloc((size_t)fsize);
    if (!*out) { fclose(f); return -1; }
    *out_len = fread(*out, 1, (size_t)fsize, f);
    fclose(f);
    return 0;
}

/* ─── Write buffer to file ───────────────────────────────────────── */
static int write_file(const char *path, const uint8_t *data, size_t len) {
    FILE *f = fopen(path, "wb");
    if (!f) { fprintf(stderr, "cryptwire: cannot write '%s': %s\n", path, strerror(errno)); return -1; }
    size_t written = fwrite(data, 1, len, f);
    fclose(f);
    return (written == len) ? 0 : -1;
}

/* ─── Session log ────────────────────────────────────────────────── */
static void log_session(const char *ks_dir, const char *event) {
    char log_dir[512], log_path[600];
    snprintf(log_dir, sizeof(log_dir), "%s" PATH_SEP "logs", ks_dir);
    ensure_secure_dir(log_dir);

    time_t now = time(NULL);
    struct tm *tm_now = localtime(&now);
    char date_str[32];
    strftime(date_str, sizeof(date_str), "%Y-%m-%d", tm_now);
    snprintf(log_path, sizeof(log_path), "%s" PATH_SEP "session_%s.log", log_dir, date_str);

    FILE *f = fopen(log_path, "a");
    if (!f) return;
    char ts_str[64];
    strftime(ts_str, sizeof(ts_str), "%Y-%m-%dT%H:%M:%S", tm_now);
    fprintf(f, "[%s] %s\n", ts_str, event);
    fclose(f);
}

/* ─── cmd: genkey ────────────────────────────────────────────────── */
static int cmd_genkey(const char *ks_path) {
    char ks_dir[512];
    strncpy(ks_dir, ks_path, sizeof(ks_dir) - 1);
    /* Strip filename to get directory */
    char *last_sep = strrchr(ks_dir, PATH_SEP[0]);
    if (last_sep) *last_sep = '\0';

    if (ensure_secure_dir(ks_dir) != 0) {
        fprintf(stderr, "cryptwire: cannot create key store directory '%s'\n", ks_dir);
        return 1;
    }

    /* Generate a cryptographically random master key */
    uint8_t master_key[CW_MASTER_KEY_LEN];
    if (RAND_bytes(master_key, CW_MASTER_KEY_LEN) != 1) {
        fprintf(stderr, "cryptwire: RNG failure\n");
        return 1;
    }

    CWContext ctx;
    int rc = cw_init(&ctx, master_key, NULL);
    /* Securely erase raw key from local stack */
    memset(master_key, 0, sizeof(master_key));

    if (rc != CW_OK) {
        fprintf(stderr, "cryptwire: init failed (code %d)\n", rc);
        return 1;
    }

    rc = cw_save_keystore(&ctx, ks_path);
    if (rc != CW_OK) {
        fprintf(stderr, "cryptwire: cannot save keystore to '%s' (code %d)\n", ks_path, rc);
        cw_free(&ctx);
        return 1;
    }

    log_session(ks_dir, "GENKEY: New master key generated and saved.");
    printf("CryptWire: New key store created at '%s'\n", ks_path);
    printf("Machine binding: %s\n", ctx.keystore.machine_id);
    printf("This key store will ONLY decrypt on this machine.\n");

    cw_free(&ctx);
    return 0;
}

/* ─── cmd: encrypt ───────────────────────────────────────────────── */
static int cmd_encrypt(const char *inpath, const char *outpath, const char *ks_path) {
    CWContext ctx;
    memset(&ctx, 0, sizeof(ctx));

    int rc = cw_init_from_keystore(&ctx, ks_path);
    if (rc == CW_ERR_IO) {
        fprintf(stderr, "cryptwire: key store not found at '%s'. Run 'cryptwire genkey' first.\n", ks_path);
        return 1;
    }
    if (rc == CW_ERR_MACHINE) {
        fprintf(stderr, "cryptwire: key store was created on a different machine.\n");
        return 1;
    }
    if (rc != CW_OK) {
        fprintf(stderr, "cryptwire: failed to load key store (code %d)\n", rc);
        return 1;
    }

    uint8_t *plaintext = NULL;
    size_t   pt_len = 0;
    if (read_file(inpath, &plaintext, &pt_len) != 0) {
        cw_free(&ctx);
        return 1;
    }

    uint8_t *ciphertext = NULL;
    size_t   ct_len = 0;
    rc = cw_encrypt(&ctx, plaintext, pt_len, &ciphertext, &ct_len);
    memset(plaintext, 0, pt_len);
    free(plaintext);

    if (rc != CW_OK) {
        fprintf(stderr, "cryptwire: encryption failed (code %d)\n", rc);
        cw_free(&ctx);
        return 1;
    }

    if (write_file(outpath, ciphertext, ct_len) != 0) {
        memset(ciphertext, 0, ct_len);
        free(ciphertext);
        cw_free(&ctx);
        return 1;
    }

    char status[512];
    cw_status_string(&ctx, status, sizeof(status));
    printf("Encrypted: %s -> %s (%zu -> %zu bytes)\n", inpath, outpath, pt_len, ct_len);
    printf("%s", status);

    char ks_dir[512];
    strncpy(ks_dir, ks_path, sizeof(ks_dir) - 1);
    char *sep = strrchr(ks_dir, PATH_SEP[0]);
    if (sep) *sep = '\0';
    char log_entry[256];
    snprintf(log_entry, sizeof(log_entry), "ENCRYPT: %s -> %s (%zu bytes)", inpath, outpath, pt_len);
    log_session(ks_dir, log_entry);

    memset(ciphertext, 0, ct_len);
    free(ciphertext);
    cw_free(&ctx);
    return 0;
}

/* ─── cmd: decrypt ───────────────────────────────────────────────── */
static int cmd_decrypt(const char *inpath, const char *outpath, const char *ks_path) {
    CWContext ctx;
    memset(&ctx, 0, sizeof(ctx));

    int rc = cw_init_from_keystore(&ctx, ks_path);
    if (rc == CW_ERR_IO) {
        fprintf(stderr, "cryptwire: key store not found at '%s'.\n", ks_path);
        return 1;
    }
    if (rc == CW_ERR_MACHINE) {
        fprintf(stderr, "cryptwire: this packet was encrypted on a different machine.\n");
        return 1;
    }
    if (rc != CW_OK) {
        fprintf(stderr, "cryptwire: failed to load key store (code %d)\n", rc);
        return 1;
    }

    uint8_t *ciphertext = NULL;
    size_t   ct_len = 0;
    if (read_file(inpath, &ciphertext, &ct_len) != 0) {
        cw_free(&ctx);
        return 1;
    }

    uint8_t *plaintext = NULL;
    size_t   pt_len = 0;
    rc = cw_decrypt(&ctx, ciphertext, ct_len, &plaintext, &pt_len);
    memset(ciphertext, 0, ct_len);
    free(ciphertext);

    if (rc == CW_ERR_AUTH) {
        fprintf(stderr, "cryptwire: authentication FAILED — data is corrupted or tampered.\n");
        cw_free(&ctx);
        return 1;
    }
    if (rc == CW_ERR_MACHINE) {
        fprintf(stderr, "cryptwire: machine binding mismatch.\n");
        cw_free(&ctx);
        return 1;
    }
    if (rc != CW_OK) {
        fprintf(stderr, "cryptwire: decryption failed (code %d)\n", rc);
        cw_free(&ctx);
        return 1;
    }

    if (write_file(outpath, plaintext, pt_len) != 0) {
        memset(plaintext, 0, pt_len);
        free(plaintext);
        cw_free(&ctx);
        return 1;
    }

    printf("Decrypted: %s -> %s (%zu bytes)\n", inpath, outpath, pt_len);

    memset(plaintext, 0, pt_len);
    free(plaintext);
    cw_free(&ctx);
    return 0;
}

/* ─── cmd: rotate ────────────────────────────────────────────────── */
static int cmd_rotate(const char *ks_path) {
    CWContext ctx;
    memset(&ctx, 0, sizeof(ctx));

    int rc = cw_init_from_keystore(&ctx, ks_path);
    if (rc != CW_OK) { fprintf(stderr, "cryptwire: load keystore failed (code %d)\n", rc); return 1; }

    rc = cw_rotate_keys(&ctx);
    if (rc != CW_OK) { fprintf(stderr, "cryptwire: rotation failed (code %d)\n", rc); cw_free(&ctx); return 1; }

    rc = cw_save_keystore(&ctx, ks_path);
    if (rc != CW_OK) { fprintf(stderr, "cryptwire: save failed (code %d)\n", rc); cw_free(&ctx); return 1; }

    printf("Key rotation complete. Rotation count: %u\n", ctx.keystore.rotation_count);

    char ks_dir[512];
    strncpy(ks_dir, ks_path, sizeof(ks_dir) - 1);
    char *sep = strrchr(ks_dir, PATH_SEP[0]);
    if (sep) *sep = '\0';
    char log_entry[128];
    snprintf(log_entry, sizeof(log_entry), "ROTATE: rotation_count=%u", ctx.keystore.rotation_count);
    log_session(ks_dir, log_entry);

    cw_free(&ctx);
    return 0;
}

/* ─── cmd: status ────────────────────────────────────────────────── */
static int cmd_status(const char *ks_path) {
    CWContext ctx;
    memset(&ctx, 0, sizeof(ctx));

    int rc = cw_init_from_keystore(&ctx, ks_path);
    if (rc != CW_OK) {
        fprintf(stderr, "cryptwire: cannot load key store at '%s' (code %d)\n", ks_path, rc);
        return 1;
    }

    char status_buf[1024];
    cw_status_string(&ctx, status_buf, sizeof(status_buf));
    printf("%s", status_buf);

    char ai_buf[2048];
    cw_ai_status_string((CWAIState *)ctx.ai_state, ai_buf, sizeof(ai_buf));
    printf("%s", ai_buf);

    uint64_t now = (uint64_t)time(NULL);
    uint64_t since_rotation = now - ctx.keystore.last_rotation;
    if (since_rotation > CW_KEY_ROTATION_INTERVAL_S) {
        printf("\nWARNING: Key rotation overdue (last rotated %llu hours ago). "
               "Run 'cryptwire rotate'.\n",
               (unsigned long long)(since_rotation / 3600));
    }

    cw_free(&ctx);
    return 0;
}

/* ─── cmd: scan ──────────────────────────────────────────────────── */
static int cmd_scan(const char *datapath, const char *sigpath, const char *ks_path) {
    CWContext ctx;
    memset(&ctx, 0, sizeof(ctx));

    int rc = cw_init_from_keystore(&ctx, ks_path);
    if (rc != CW_OK) { fprintf(stderr, "cryptwire: load failed (code %d)\n", rc); return 1; }

    if (sigpath) {
        int n = cw_ai_load_signatures((CWAIState *)ctx.ai_state, sigpath);
        printf("Loaded %d threat signatures from '%s'\n", n, sigpath);
    }

    uint8_t *data = NULL; size_t data_len = 0;
    if (read_file(datapath, &data, &data_len) != 0) { cw_free(&ctx); return 1; }

    float sev = cw_ai_scan_signatures((CWAIState *)ctx.ai_state, data, data_len);
    free(data);

    printf("Scan result for '%s': max_severity=%.4f\n", datapath, sev);
    if (sev > 0.7f) {
        printf("HIGH CONFIDENCE MATCH — reporting as threat\n");
        cw_ai_confirm_threat((CWAIState *)ctx.ai_state);
        cw_set_threat_level(&ctx, CW_THREAT_HIGH);
        cw_save_keystore(&ctx, ks_path);  /* persist updated AI state */
    } else if (sev > 0.3f) {
        printf("Low-confidence match — flagged for review\n");
    } else {
        printf("Clean.\n");
    }

    cw_free(&ctx);
    return 0;
}

/* ─── cmd: monitor ───────────────────────────────────────────────── */
/*
 * Daemon mode: reads raw data from stdin line-by-line (or piped),
 * scans each chunk for threat signatures, and logs results.
 * In a production integration, this would sit on a named pipe or socket
 * fed by a WFP/nftables packet capture hook.
 *
 * Press Ctrl-C to stop.
 */
static int cmd_monitor(const char *ks_path) {
    CWContext ctx;
    memset(&ctx, 0, sizeof(ctx));

    int rc = cw_init_from_keystore(&ctx, ks_path);
    if (rc != CW_OK) { fprintf(stderr, "cryptwire: load failed (code %d)\n", rc); return 1; }

    char ks_dir[512];
    strncpy(ks_dir, ks_path, sizeof(ks_dir) - 1);
    char *sep = strrchr(ks_dir, PATH_SEP[0]);
    if (sep) *sep = '\0';

    printf("CryptWire Monitor — reading from stdin. Press Ctrl-C to stop.\n");
    log_session(ks_dir, "MONITOR: started");

    char line[4096];
    uint64_t chunks = 0;
    while (fgets(line, sizeof(line), stdin)) {
        size_t len = strlen(line);
        float sev = cw_ai_scan_signatures((CWAIState *)ctx.ai_state,
                                           (const uint8_t *)line, len);
        chunks++;
        if (sev > 0.5f) {
            char ts_buf[32];
            time_t now = time(NULL);
            strftime(ts_buf, sizeof(ts_buf), "%H:%M:%S", localtime(&now));
            printf("[%s] THREAT DETECTED  sev=%.4f  chunk=%llu\n",
                   ts_buf, sev, (unsigned long long)chunks);
            cw_ai_confirm_threat((CWAIState *)ctx.ai_state);
            cw_set_threat_level(&ctx, CW_THREAT_HIGH);
        }
        /* Occasional status line every 1000 chunks */
        if (chunks % 1000 == 0) {
            double agg = cw_ai_aggregate_score((CWAIState *)ctx.ai_state);
            printf("[monitor] chunks=%llu  agg_threat=%.4f\n",
                   (unsigned long long)chunks, agg);
        }
    }

    /* Save updated AI state on exit */
    cw_save_keystore(&ctx, ks_path);
    log_session(ks_dir, "MONITOR: stopped");
    printf("\nMonitor stopped. Processed %llu chunks.\n", (unsigned long long)chunks);
    cw_free(&ctx);
    return 0;
}

/* ─── cw_init_from_keystore (implementation bridged from cryptwire.c) */
int cw_init_from_keystore(CWContext *ctx, const char *keystore_path) {
    if (!ctx || !keystore_path) return CW_ERR_PARAM;
    memset(ctx, 0, sizeof(CWContext));

    /* We need the machine ID before loading the keystore (to derive file key) */
    char machine_id[CW_MACHINE_ID_LEN];
    cw_derive_machine_id(machine_id, CW_MACHINE_ID_LEN);
    SHA256((const unsigned char *)machine_id, strlen(machine_id),
           ctx->keystore.machine_id_hash);
    strncpy(ctx->keystore.machine_id, machine_id, CW_MACHINE_ID_LEN - 1);

    int rc = cw_load_keystore(ctx, keystore_path);
    if (rc != CW_OK) return rc;

    /* Verify machine binding against newly loaded keystore */
    rc = cw_verify_machine_binding(ctx);
    if (rc != CW_OK) return CW_ERR_MACHINE;

    ctx->num_stages     = 3;
    ctx->current_threat = CW_THREAT_NONE;
    ctx->ai_state       = cw_ai_init();
    if (!ctx->ai_state) return CW_ERR_ALLOC;
    return CW_OK;
}

/* ─── Argument parsing helpers ───────────────────────────────────── */
static const char *get_flag(int argc, char **argv, const char *flag) {
    for (int i = 1; i < argc - 1; i++) {
        if (strcmp(argv[i], flag) == 0) return argv[i + 1];
    }
    return NULL;
}

/* ─── main ───────────────────────────────────────────────────────── */
int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr,
            "CryptWire v0.1.0 — Multi-layer adaptive encryption\n\n"
            "Usage:\n"
            "  cryptwire genkey  [--out <keystore>]\n"
            "  cryptwire encrypt <infile> <outfile> [--ks <keystore>]\n"
            "  cryptwire decrypt <infile> <outfile> [--ks <keystore>]\n"
            "  cryptwire rotate  [--ks <keystore>]\n"
            "  cryptwire status  [--ks <keystore>]\n"
            "  cryptwire monitor [--ks <keystore>]\n"
            "  cryptwire scan    <datafile> [--sigs <sigdb>] [--ks <keystore>]\n"
        );
        return 1;
    }

    const char *cmd = argv[1];

    /* Resolve key store path */
    char default_ks[512];
    default_ks_path(default_ks, sizeof(default_ks));
    const char *ks_path = get_flag(argc, argv, "--ks");
    if (!ks_path) ks_path = get_flag(argc, argv, "--out");
    if (!ks_path) ks_path = default_ks;

    if (strcmp(cmd, "genkey") == 0) {
        return cmd_genkey(ks_path);
    }
    else if (strcmp(cmd, "encrypt") == 0) {
        if (argc < 4) { fprintf(stderr, "Usage: cryptwire encrypt <in> <out>\n"); return 1; }
        return cmd_encrypt(argv[2], argv[3], ks_path);
    }
    else if (strcmp(cmd, "decrypt") == 0) {
        if (argc < 4) { fprintf(stderr, "Usage: cryptwire decrypt <in> <out>\n"); return 1; }
        return cmd_decrypt(argv[2], argv[3], ks_path);
    }
    else if (strcmp(cmd, "rotate") == 0) {
        return cmd_rotate(ks_path);
    }
    else if (strcmp(cmd, "status") == 0) {
        return cmd_status(ks_path);
    }
    else if (strcmp(cmd, "monitor") == 0) {
        return cmd_monitor(ks_path);
    }
    else if (strcmp(cmd, "scan") == 0) {
        if (argc < 3) { fprintf(stderr, "Usage: cryptwire scan <datafile>\n"); return 1; }
        const char *sigpath = get_flag(argc, argv, "--sigs");
        return cmd_scan(argv[2], sigpath, ks_path);
    }
    else {
        fprintf(stderr, "cryptwire: unknown command '%s'\n", cmd);
        return 1;
    }
}
