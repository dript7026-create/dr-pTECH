/* ecbmps_compiler.c — Assembles source content into a .ecbmps binary
 *
 * Usage:
 *   ecbmps_compiler -o output.ecbmps -t "Book Title" -a "Author"
 *                   page1.txt page2.png page3.txt+img.png ...
 *
 * A source argument without '+' is either plain text (.txt) or a
 * standalone image (.png/.jpg).  An argument with '+' like
 * "story.txt+art.png" becomes a combined text+image page.
 */

#include "common.h"

#define MAX_SRC_PAGES 2048

typedef struct {
    const char *text_path;
    const char *image_path;
    uint8_t page_type;
} SourcePage;

static SourcePage g_pages[MAX_SRC_PAGES];
static int g_page_count = 0;
static const char *g_title = "Untitled";
static const char *g_author = "Unknown";
static const char *g_output = NULL;

static int is_image_ext(const char *path) {
    const char *dot = strrchr(path, '.');
    if (!dot) return 0;
    return _stricmp(dot, ".png") == 0 || _stricmp(dot, ".jpg") == 0 ||
           _stricmp(dot, ".jpeg") == 0 || _stricmp(dot, ".bmp") == 0;
}

static void parse_source_arg(const char *arg) {
    if (g_page_count >= MAX_SRC_PAGES) {
        fprintf(stderr, "Too many pages (max %d)\n", MAX_SRC_PAGES);
        return;
    }
    SourcePage *pg = &g_pages[g_page_count];
    const char *plus = strchr(arg, '+');
    if (plus) {
        size_t tlen = (size_t)(plus - arg);
        char *text_part = (char *)malloc(tlen + 1);
        memcpy(text_part, arg, tlen);
        text_part[tlen] = '\0';
        pg->text_path = text_part;
        pg->image_path = plus + 1;
        pg->page_type = ECBMPS_PAGE_COMBINED;
    } else if (is_image_ext(arg)) {
        pg->text_path = NULL;
        pg->image_path = arg;
        pg->page_type = ECBMPS_PAGE_IMAGE;
    } else {
        pg->text_path = arg;
        pg->image_path = NULL;
        pg->page_type = ECBMPS_PAGE_TEXT;
    }
    g_page_count++;
}

static int parse_args(int argc, char **argv) {
    int i;
    for (i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-o") == 0 && i + 1 < argc) {
            g_output = argv[++i];
        } else if (strcmp(argv[i], "-t") == 0 && i + 1 < argc) {
            g_title = argv[++i];
        } else if (strcmp(argv[i], "-a") == 0 && i + 1 < argc) {
            g_author = argv[++i];
        } else if (argv[i][0] != '-') {
            parse_source_arg(argv[i]);
        } else {
            fprintf(stderr, "Unknown option: %s\n", argv[i]);
            return 0;
        }
    }
    if (!g_output) {
        fprintf(stderr, "Usage: ecbmps_compiler -o output.ecbmps [-t title] [-a author] page...\n");
        return 0;
    }
    if (g_page_count == 0) {
        fprintf(stderr, "No pages specified\n");
        return 0;
    }
    return 1;
}

static uint8_t detect_image_format(const char *path) {
    const char *dot = strrchr(path, '.');
    if (!dot) return ECBMPS_IMG_RAW;
    if (_stricmp(dot, ".png") == 0) return ECBMPS_IMG_PNG;
    if (_stricmp(dot, ".jpg") == 0 || _stricmp(dot, ".jpeg") == 0) return ECBMPS_IMG_JPEG;
    return ECBMPS_IMG_RAW;
}

int main(int argc, char **argv) {
    FILE *out;
    EcbmpsHeader header;
    EcbmpsTocEntry *toc;
    uint64_t cursor;
    int i;
    uint32_t title_len, author_len;

    if (!parse_args(argc, argv)) return 1;

    out = fopen(g_output, "wb");
    if (!out) {
        fprintf(stderr, "Cannot open %s for writing\n", g_output);
        return 1;
    }

    /* Reserve header space */
    memset(&header, 0, sizeof(header));
    header.magic = ECBMPS_MAGIC;
    header.version = ECBMPS_VERSION;
    header.page_count = (uint32_t)g_page_count;
    header.flags = ECBMPS_FLAG_HAS_TOC;
    fwrite(&header, sizeof(header), 1, out);

    /* Title section */
    header.title_offset = (uint64_t)ftell(out);
    title_len = (uint32_t)strlen(g_title);
    author_len = (uint32_t)strlen(g_author);
    write_u32(out, title_len);
    fwrite(g_title, 1, title_len, out);
    write_u32(out, author_len);
    fwrite(g_author, 1, author_len, out);

    /* TOC placeholder */
    header.toc_offset = (uint64_t)ftell(out);
    toc = (EcbmpsTocEntry *)calloc(g_page_count, sizeof(EcbmpsTocEntry));
    fwrite(toc, sizeof(EcbmpsTocEntry), g_page_count, out);

    /* Write page data */
    for (i = 0; i < g_page_count; i++) {
        SourcePage *sp = &g_pages[i];
        long start = ftell(out);
        toc[i].page_offset = (uint64_t)start;
        toc[i].page_type = sp->page_type;
        toc[i].flags = 0;
        toc[i].reserved = 0;

        if (sp->page_type == ECBMPS_PAGE_TEXT) {
            long sz = 0;
            void *text = read_entire_file(sp->text_path, &sz);
            if (!text) {
                fprintf(stderr, "Cannot read %s\n", sp->text_path);
                fclose(out);
                return 1;
            }
            write_u32(out, (uint32_t)sz);
            fwrite(text, 1, (size_t)sz, out);
            free(text);
        } else if (sp->page_type == ECBMPS_PAGE_IMAGE) {
            long sz = 0;
            void *img = read_entire_file(sp->image_path, &sz);
            if (!img) {
                fprintf(stderr, "Cannot read %s\n", sp->image_path);
                fclose(out);
                return 1;
            }
            write_u8(out, detect_image_format(sp->image_path));
            write_u32(out, 0); /* width — to be filled by viewer from image header */
            write_u32(out, 0); /* height */
            write_u32(out, (uint32_t)sz);
            fwrite(img, 1, (size_t)sz, out);
            free(img);
        } else {
            /* Combined */
            long tsz = 0, isz = 0;
            void *text = read_entire_file(sp->text_path, &tsz);
            void *img = read_entire_file(sp->image_path, &isz);
            if (!text) {
                fprintf(stderr, "Cannot read %s\n", sp->text_path);
                fclose(out);
                return 1;
            }
            write_u32(out, (uint32_t)tsz);
            fwrite(text, 1, (size_t)tsz, out);
            free(text);
            if (img) {
                write_u8(out, 1); /* image_count = 1 */
                write_u8(out, detect_image_format(sp->image_path));
                write_u16(out, 0);  /* layout_x */
                write_u16(out, 0);  /* layout_y */
                write_u16(out, 0);  /* layout_w — viewer deduces from image */
                write_u16(out, 0);  /* layout_h */
                write_u32(out, (uint32_t)isz);
                fwrite(img, 1, (size_t)isz, out);
                free(img);
                toc[i].flags = 0x01; /* has_images_inline */
            } else {
                write_u8(out, 0); /* image_count = 0 */
            }
        }
        toc[i].page_size = (uint32_t)((uint64_t)ftell(out) - toc[i].page_offset);
    }

    /* User data section (empty) */
    header.userdata_offset = (uint64_t)ftell(out);
    write_u32(out, ECBMPS_UD_MAGIC);
    write_u16(out, 0); /* bookmark_count */
    write_u16(out, 0); /* highlight_count */

    /* Rewrite header with final offsets */
    fseek(out, 0, SEEK_SET);
    fwrite(&header, sizeof(header), 1, out);

    /* Rewrite TOC with final page offsets/sizes */
    fseek(out, (long)header.toc_offset, SEEK_SET);
    fwrite(toc, sizeof(EcbmpsTocEntry), g_page_count, out);

    fclose(out);
    free(toc);

    printf("Compiled %d pages into %s\n", g_page_count, g_output);
    printf("  Title:  %s\n  Author: %s\n", g_title, g_author);
    return 0;
}
