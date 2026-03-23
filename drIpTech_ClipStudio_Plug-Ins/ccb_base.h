#ifndef CCB_BASE_H
#define CCB_BASE_H

#include <stddef.h>
#include <stdint.h>

#define CCB_MAGIC "CCP1"
#define CCB_VERSION 1u
#define CCB_MAX_PAGES 2048u

typedef struct CCBPageEntry {
    char clip_name[260];
    uint32_t page_number;
    uint64_t compressed_size;
    uint64_t uncompressed_size;
} CCBPageEntry;

typedef struct CCBBookSpec {
    const char *title;
    const char *book_mode;
    const char *source_zip_path;
    const char *output_ccp_path;
    const char *prompt_map_path;
} CCBBookSpec;

#pragma pack(push, 1)
typedef struct CCBHeader {
    char magic[4];
    uint32_t version;
    uint32_t page_count;
    uint64_t manifest_size;
    uint64_t source_zip_size;
} CCBHeader;
#pragma pack(pop)

int ccb_build_book(const CCBBookSpec *spec);

#endif