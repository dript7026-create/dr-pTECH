/* ccp_compiler.c — Assembles source content into a .ccp binary
 *
 * Usage:
 *   ccp_compiler -o output.ccp -m manifest.json [-z source.zip] [-g gameplay.gply]
 *
 * The manifest JSON describes pages, interactive regions, prompt maps,
 * and optionally a source ZIP containing .clip files and raw artwork.
 *
 * V3 format: when a gameplay section (-g) is provided, the output uses
 * the CcpHeaderV3 format (36 bytes) with the GPLY bytecode section
 * appended after the source ZIP.  The .gply file is produced by
 * compiling CSP VisualScript / pipeline-bridge exports into bytecode.
 * The source ZIP should contain compressed .clip files with embedded
 * interactivity scripting from Clip Studio Paint.
 */

#include "common.h"

static const char *g_output = NULL;
static const char *g_manifest_path = NULL;
static const char *g_zip_path = NULL;
static const char *g_gameplay_path = NULL;

static int parse_args(int argc, char **argv) {
    int i;
    for (i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-o") == 0 && i + 1 < argc) {
            g_output = argv[++i];
        } else if (strcmp(argv[i], "-m") == 0 && i + 1 < argc) {
            g_manifest_path = argv[++i];
        } else if (strcmp(argv[i], "-z") == 0 && i + 1 < argc) {
            g_zip_path = argv[++i];
        } else if (strcmp(argv[i], "-g") == 0 && i + 1 < argc) {
            g_gameplay_path = argv[++i];
        } else {
            fprintf(stderr, "Unknown option: %s\n", argv[i]);
            return 0;
        }
    }
    if (!g_output || !g_manifest_path) {
        fprintf(stderr,
            "Usage: ccp_compiler -o output.ccp -m manifest.json "
            "[-z source.zip] [-g gameplay.gply]\n"
            "\n"
            "Options:\n"
            "  -o  Output .ccp file path\n"
            "  -m  JSON manifest describing pages and interactive regions\n"
            "  -z  Source ZIP of .clip files (compressed Clip Studio artwork)\n"
            "  -g  Pre-compiled GPLY gameplay bytecode section\n"
            "      (compiled from CSP VisualScript / pipeline-bridge exports)\n");
        return 0;
    }
    return 1;
}

/* Count pages by scanning for "page" keys in the manifest JSON.
 * This is intentionally simplistic — a real parser would use cJSON or similar.
 */
static uint32_t count_pages_in_manifest(const char *json, long size) {
    uint32_t count = 0;
    const char *p = json;
    const char *end = json + size;
    while (p < end) {
        p = memchr(p, '"', (size_t)(end - p));
        if (!p) break;
        if (end - p > 5 && memcmp(p, "\"page\"", 6) == 0) {
            count++;
        }
        p++;
    }
    return count;
}

int main(int argc, char **argv) {
    FILE *out;
    long manifest_size = 0;
    void *manifest_data = NULL;
    long zip_size = 0;
    void *zip_data = NULL;
    long gameplay_size = 0;
    void *gameplay_data = NULL;

    if (!parse_args(argc, argv)) return 1;

    manifest_data = read_entire_file(g_manifest_path, &manifest_size);
    if (!manifest_data) {
        fprintf(stderr, "Cannot read manifest %s\n", g_manifest_path);
        return 1;
    }

    if (g_zip_path) {
        zip_data = read_entire_file(g_zip_path, &zip_size);
        if (!zip_data) {
            fprintf(stderr, "Cannot read zip %s\n", g_zip_path);
            free(manifest_data);
            return 1;
        }
    }

    if (g_gameplay_path) {
        gameplay_data = read_entire_file(g_gameplay_path, &gameplay_size);
        if (!gameplay_data) {
            fprintf(stderr, "Cannot read gameplay %s\n", g_gameplay_path);
            free(manifest_data);
            free(zip_data);
            return 1;
        }
        /* Validate GPLY magic */
        if (gameplay_size >= 4) {
            uint32_t gply_magic;
            memcpy(&gply_magic, gameplay_data, 4);
            if (gply_magic != 0x594C5047u) {
                fprintf(stderr, "Warning: gameplay file does not have GPLY magic\n");
            }
        }
    }

    out = fopen(g_output, "wb");
    if (!out) {
        fprintf(stderr, "Cannot open %s for writing\n", g_output);
        free(manifest_data);
        free(zip_data);
        free(gameplay_data);
        return 1;
    }

    uint32_t page_count = count_pages_in_manifest(
        (const char *)manifest_data, manifest_size);

    if (gameplay_data) {
        /* V3 format with gameplay section */
        CcpHeaderV3 header;
        memset(&header, 0, sizeof(header));
        header.magic           = CCP_MAGIC;
        header.version         = CCP_VERSION_V3;
        header.page_count      = page_count;
        header.manifest_size   = (uint64_t)manifest_size;
        header.source_zip_size = (uint64_t)zip_size;
        header.gameplay_size   = (uint64_t)gameplay_size;

        fwrite(&header, sizeof(header), 1, out);
        fwrite(manifest_data, 1, (size_t)manifest_size, out);
        if (zip_data)
            fwrite(zip_data, 1, (size_t)zip_size, out);
        fwrite(gameplay_data, 1, (size_t)gameplay_size, out);

        fclose(out);

        printf("Compiled CCP v3: %s\n", g_output);
        printf("  Pages:    %u\n",   header.page_count);
        printf("  Manifest: %llu bytes\n", (unsigned long long)header.manifest_size);
        printf("  Source:   %llu bytes\n", (unsigned long long)header.source_zip_size);
        printf("  Gameplay: %llu bytes (GPLY bytecode)\n", (unsigned long long)header.gameplay_size);
    } else {
        /* V2 format (backward compatible) */
        CcpHeader header;
        memset(&header, 0, sizeof(header));
        header.magic           = CCP_MAGIC;
        header.version         = CCP_VERSION;
        header.page_count      = page_count;
        header.manifest_size   = (uint64_t)manifest_size;
        header.source_zip_size = (uint64_t)zip_size;

        fwrite(&header, sizeof(header), 1, out);
        fwrite(manifest_data, 1, (size_t)manifest_size, out);
        if (zip_data)
            fwrite(zip_data, 1, (size_t)zip_size, out);

        fclose(out);

        printf("Compiled CCP v2: %s\n", g_output);
        printf("  Pages:    %u\n",   header.page_count);
        printf("  Manifest: %llu bytes\n", (unsigned long long)header.manifest_size);
        printf("  Source:   %llu bytes\n", (unsigned long long)header.source_zip_size);
    }

    free(manifest_data);
    free(zip_data);
    free(gameplay_data);
    return 0;
}
