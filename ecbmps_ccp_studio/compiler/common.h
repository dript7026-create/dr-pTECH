/* common.h — shared definitions for ECBMPS and CCP compilers/viewers */
#ifndef ECBMPS_CCP_COMMON_H
#define ECBMPS_CCP_COMMON_H

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ---------- ECBMPS format ---------- */
#define ECBMPS_MAGIC      0x4D424345u  /* "ECBM" little-endian */
#define ECBMPS_VERSION    1u
#define ECBMPS_UD_MAGIC   0x55424345u  /* "ECBU" */
#define ECBMPS_MAX_PAGES  4096
#define ECBMPS_MAX_TITLE  512
#define ECBMPS_MAX_BOOKMARKS  256
#define ECBMPS_MAX_HIGHLIGHTS 1024

typedef struct {
    uint32_t magic;
    uint32_t version;
    uint32_t page_count;
    uint32_t flags;
    uint64_t title_offset;
    uint64_t toc_offset;
    uint64_t userdata_offset;
} EcbmpsHeader;

#define ECBMPS_FLAG_HAS_TOC   0x01u
#define ECBMPS_FLAG_HAS_COVER 0x02u

typedef struct {
    uint64_t page_offset;
    uint32_t page_size;
    uint8_t  page_type;   /* 0=text, 1=image, 2=combined */
    uint8_t  flags;
    uint16_t reserved;
} EcbmpsTocEntry;

#define ECBMPS_PAGE_TEXT     0
#define ECBMPS_PAGE_IMAGE    1
#define ECBMPS_PAGE_COMBINED 2

#define ECBMPS_IMG_RAW  0
#define ECBMPS_IMG_PNG  1
#define ECBMPS_IMG_JPEG 2

typedef struct {
    uint32_t page_index;
    uint32_t scroll_offset;
    uint8_t  label_length;
    char     label[255];
} EcbmpsBookmark;

typedef struct {
    uint32_t page_index;
    uint32_t start_char;
    uint32_t end_char;
    uint32_t color_rgba;
} EcbmpsHighlight;

/* ---------- CCP format ---------- */
#define CCP_MAGIC    0x31504343u  /* "CCP1" little-endian */
#define CCP_VERSION  2u
#define CCP_VERSION_V3 3u

typedef struct {
    uint32_t magic;
    uint32_t version;
    uint32_t page_count;
    uint64_t manifest_size;
    uint64_t source_zip_size;
} CcpHeader;

/* V3 header adds gameplay section (GPLY bytecode from CSP scripting) */
typedef struct {
    uint32_t magic;
    uint32_t version;          /* CCP_VERSION_V3 = 3 */
    uint32_t page_count;
    uint64_t manifest_size;
    uint64_t source_zip_size;
    uint64_t gameplay_size;    /* size of GPLY gameplay section */
} CcpHeaderV3;

/* ---------- Utility ---------- */
static inline void write_u32(FILE *f, uint32_t v) {
    fwrite(&v, 4, 1, f);
}
static inline void write_u64(FILE *f, uint64_t v) {
    fwrite(&v, 8, 1, f);
}
static inline void write_u16(FILE *f, uint16_t v) {
    fwrite(&v, 2, 1, f);
}
static inline void write_u8(FILE *f, uint8_t v) {
    fwrite(&v, 1, 1, f);
}
static inline uint32_t read_u32(FILE *f) {
    uint32_t v = 0;
    fread(&v, 4, 1, f);
    return v;
}
static inline uint64_t read_u64(FILE *f) {
    uint64_t v = 0;
    fread(&v, 8, 1, f);
    return v;
}

static inline long file_size(const char *path) {
    FILE *fp = fopen(path, "rb");
    if (!fp) return -1;
    fseek(fp, 0, SEEK_END);
    long sz = ftell(fp);
    fclose(fp);
    return sz;
}

static inline void *read_entire_file(const char *path, long *out_size) {
    FILE *fp = fopen(path, "rb");
    if (!fp) return NULL;
    fseek(fp, 0, SEEK_END);
    long sz = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    void *buf = malloc((size_t)sz);
    if (buf) fread(buf, 1, (size_t)sz, fp);
    fclose(fp);
    if (out_size) *out_size = sz;
    return buf;
}

#endif /* ECBMPS_CCP_COMMON_H */
