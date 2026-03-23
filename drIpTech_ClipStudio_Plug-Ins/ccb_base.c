#define _CRT_SECURE_NO_WARNINGS

#include "ccb_base.h"

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct CCBZipEntry {
    char name[260];
    uint16_t compression_method;
    uint32_t compressed_size32;
    uint32_t uncompressed_size32;
} CCBZipEntry;

typedef struct CCBZipIndex {
    CCBZipEntry *items;
    size_t count;
    size_t capacity;
} CCBZipIndex;

static int ccb_has_suffix(const char *value, const char *suffix)
{
    size_t value_len;
    size_t suffix_len;
    if (!value || !suffix)
    {
        return 0;
    }
    value_len = strlen(value);
    suffix_len = strlen(suffix);
    if (value_len < suffix_len)
    {
        return 0;
    }
    return _stricmp(value + value_len - suffix_len, suffix) == 0;
}

static uint16_t ccb_read_u16(const unsigned char *buffer)
{
    return (uint16_t)(buffer[0] | (buffer[1] << 8));
}

static uint32_t ccb_read_u32(const unsigned char *buffer)
{
    return (uint32_t)(buffer[0] | (buffer[1] << 8) | (buffer[2] << 16) | (buffer[3] << 24));
}

static uint64_t ccb_file_size(FILE *handle)
{
    long current;
    long end;
    current = ftell(handle);
    fseek(handle, 0, SEEK_END);
    end = ftell(handle);
    fseek(handle, current, SEEK_SET);
    return end >= 0 ? (uint64_t)end : 0u;
}

static int ccb_index_reserve(CCBZipIndex *index, size_t wanted)
{
    CCBZipEntry *next_items;
    size_t next_capacity;
    if (wanted <= index->capacity)
    {
        return 1;
    }
    next_capacity = index->capacity ? index->capacity * 2u : 16u;
    while (next_capacity < wanted)
    {
        next_capacity *= 2u;
    }
    next_items = (CCBZipEntry *)realloc(index->items, next_capacity * sizeof(CCBZipEntry));
    if (!next_items)
    {
        return 0;
    }
    index->items = next_items;
    index->capacity = next_capacity;
    return 1;
}

static int ccb_index_push(CCBZipIndex *index, const CCBZipEntry *entry)
{
    if (!ccb_index_reserve(index, index->count + 1u))
    {
        return 0;
    }
    index->items[index->count++] = *entry;
    return 1;
}

static void ccb_index_free(CCBZipIndex *index)
{
    free(index->items);
    index->items = NULL;
    index->count = 0u;
    index->capacity = 0u;
}

static int ccb_extract_page_number(const char *name, uint32_t *page_number)
{
    const char *cursor;
    unsigned long value;
    if (!name || !page_number)
    {
        return 0;
    }
    cursor = strrchr(name, '/');
    if (!cursor)
    {
        cursor = strrchr(name, '\\');
    }
    cursor = cursor ? cursor + 1 : name;
    if (tolower((unsigned char)cursor[0]) != 'p' || tolower((unsigned char)cursor[1]) != 'g')
    {
        return 0;
    }
    cursor += 2;
    if (!isdigit((unsigned char)*cursor))
    {
        return 0;
    }
    value = strtoul(cursor, NULL, 10);
    if (value == 0ul || value > CCB_MAX_PAGES)
    {
        return 0;
    }
    *page_number = (uint32_t)value;
    return 1;
}

static int ccb_zip_entry_compare(const void *lhs, const void *rhs)
{
    const CCBPageEntry *a = (const CCBPageEntry *)lhs;
    const CCBPageEntry *b = (const CCBPageEntry *)rhs;
    if (a->page_number < b->page_number)
    {
        return -1;
    }
    if (a->page_number > b->page_number)
    {
        return 1;
    }
    return _stricmp(a->clip_name, b->clip_name);
}

static int ccb_load_zip_index(const char *zip_path, CCBZipIndex *index)
{
    FILE *handle;
    unsigned char *data;
    size_t length;
    size_t cursor;
    int found;
    if (!zip_path || !index)
    {
        return 0;
    }
    handle = fopen(zip_path, "rb");
    if (!handle)
    {
        return 0;
    }
    length = (size_t)ccb_file_size(handle);
    data = (unsigned char *)malloc(length);
    if (!data)
    {
        fclose(handle);
        return 0;
    }
    rewind(handle);
    if (fread(data, 1u, length, handle) != length)
    {
        free(data);
        fclose(handle);
        return 0;
    }
    fclose(handle);

    found = 0;
    for (cursor = length > 22u ? length - 22u : 0u; cursor > 0u; --cursor)
    {
        if (data[cursor] == 0x50 && data[cursor + 1u] == 0x4b && data[cursor + 2u] == 0x05 && data[cursor + 3u] == 0x06)
        {
            uint32_t cd_offset = ccb_read_u32(data + cursor + 16u);
            uint16_t entry_count = ccb_read_u16(data + cursor + 10u);
            size_t entry_index;
            size_t cd_cursor = (size_t)cd_offset;
            found = 1;
            for (entry_index = 0u; entry_index < entry_count && cd_cursor + 46u <= length; ++entry_index)
            {
                uint16_t name_length;
                uint16_t extra_length;
                uint16_t comment_length;
                CCBZipEntry entry;
                if (!(data[cd_cursor] == 0x50 && data[cd_cursor + 1u] == 0x4b && data[cd_cursor + 2u] == 0x01 && data[cd_cursor + 3u] == 0x02))
                {
                    found = 0;
                    break;
                }
                memset(&entry, 0, sizeof(entry));
                name_length = ccb_read_u16(data + cd_cursor + 28u);
                extra_length = ccb_read_u16(data + cd_cursor + 30u);
                comment_length = ccb_read_u16(data + cd_cursor + 32u);
                entry.compression_method = ccb_read_u16(data + cd_cursor + 10u);
                entry.compressed_size32 = ccb_read_u32(data + cd_cursor + 20u);
                entry.uncompressed_size32 = ccb_read_u32(data + cd_cursor + 24u);
                if (name_length >= sizeof(entry.name))
                {
                    name_length = (uint16_t)(sizeof(entry.name) - 1u);
                }
                memcpy(entry.name, data + cd_cursor + 46u, name_length);
                entry.name[name_length] = '\0';
                if (!ccb_index_push(index, &entry))
                {
                    free(data);
                    return 0;
                }
                cd_cursor += 46u + name_length + extra_length + comment_length;
            }
            break;
        }
    }

    free(data);
    return found;
}

static int ccb_collect_pages(const CCBZipIndex *index, CCBPageEntry **pages_out, uint32_t *page_count_out)
{
    CCBPageEntry *pages;
    size_t page_count;
    size_t i;
    if (!index || !pages_out || !page_count_out)
    {
        return 0;
    }
    pages = (CCBPageEntry *)calloc(index->count ? index->count : 1u, sizeof(CCBPageEntry));
    if (!pages)
    {
        return 0;
    }
    page_count = 0u;
    for (i = 0u; i < index->count; ++i)
    {
        uint32_t page_number;
        if (!ccb_has_suffix(index->items[i].name, ".clip"))
        {
            continue;
        }
        if (!ccb_extract_page_number(index->items[i].name, &page_number))
        {
            continue;
        }
        strncpy(pages[page_count].clip_name, index->items[i].name, sizeof(pages[page_count].clip_name) - 1u);
        pages[page_count].clip_name[sizeof(pages[page_count].clip_name) - 1u] = '\0';
        pages[page_count].page_number = page_number;
        pages[page_count].compressed_size = index->items[i].compressed_size32;
        pages[page_count].uncompressed_size = index->items[i].uncompressed_size32;
        ++page_count;
    }
    qsort(pages, page_count, sizeof(CCBPageEntry), ccb_zip_entry_compare);
    *pages_out = pages;
    *page_count_out = (uint32_t)page_count;
    return page_count > 0u;
}

static char *ccb_load_text_file(const char *path)
{
    FILE *handle;
    uint64_t size;
    char *buffer;
    if (!path)
    {
        return NULL;
    }
    handle = fopen(path, "rb");
    if (!handle)
    {
        return NULL;
    }
    size = ccb_file_size(handle);
    buffer = (char *)malloc((size_t)size + 1u);
    if (!buffer)
    {
        fclose(handle);
        return NULL;
    }
    rewind(handle);
    if (fread(buffer, 1u, (size_t)size, handle) != (size_t)size)
    {
        free(buffer);
        fclose(handle);
        return NULL;
    }
    buffer[size] = '\0';
    fclose(handle);
    return buffer;
}

static void ccb_json_escape(FILE *handle, const char *value)
{
    const unsigned char *cursor = (const unsigned char *)value;
    fputc('"', handle);
    while (cursor && *cursor)
    {
        if (*cursor == '"' || *cursor == '\\')
        {
            fputc('\\', handle);
            fputc((int)*cursor, handle);
        }
        else if (*cursor == '\n')
        {
            fputs("\\n", handle);
        }
        else if (*cursor == '\r')
        {
            fputs("\\r", handle);
        }
        else if (*cursor == '\t')
        {
            fputs("\\t", handle);
        }
        else
        {
            fputc((int)*cursor, handle);
        }
        ++cursor;
    }
    fputc('"', handle);
}

static char *ccb_build_manifest_json(const CCBBookSpec *spec, const CCBPageEntry *pages, uint32_t page_count)
{
    FILE *memory;
    char *json;
    size_t size;
    uint32_t i;
    char *prompt_map_text;
    int close_result;
    memory = tmpfile();
    if (!memory)
    {
        return NULL;
    }
    prompt_map_text = ccb_load_text_file(spec->prompt_map_path);
    fputs("{\n  \"format\": \"ClipConceptBook\",\n", memory);
    fprintf(memory, "  \"version\": %u,\n", CCB_VERSION);
    fputs("  \"title\": ", memory);
    ccb_json_escape(memory, spec->title ? spec->title : "Untitled ClipConceptBook");
    fputs(",\n  \"book_mode\": ", memory);
    ccb_json_escape(memory, spec->book_mode ? spec->book_mode : "interactive");
    fputs(",\n  \"page_naming\": \"pg1-pgn\",\n", memory);
    fputs("  \"source_zip\": ", memory);
    ccb_json_escape(memory, spec->source_zip_path);
    fprintf(memory, ",\n  \"page_count\": %u,\n", page_count);
    fputs("  \"pages\": [\n", memory);
    for (i = 0u; i < page_count; ++i)
    {
        fprintf(memory, "    { \"page\": %u, \"clip\": ", pages[i].page_number);
        ccb_json_escape(memory, pages[i].clip_name);
        fprintf(memory, ", \"compressed_size\": %llu, \"uncompressed_size\": %llu }%s\n",
                (unsigned long long)pages[i].compressed_size,
                (unsigned long long)pages[i].uncompressed_size,
                (i + 1u == page_count) ? "" : ",");
    }
    fputs("  ]", memory);
    if (prompt_map_text)
    {
        fputs(",\n  \"prompt_map\": ", memory);
        fputs(prompt_map_text, memory);
        free(prompt_map_text);
    }
    fputs("\n}\n", memory);

    size = (size_t)ftell(memory);
    json = (char *)malloc(size + 1u);
    if (!json)
    {
        fclose(memory);
        return NULL;
    }
    rewind(memory);
    if (fread(json, 1u, size, memory) != size)
    {
        free(json);
        fclose(memory);
        return NULL;
    }
    json[size] = '\0';
    close_result = fclose(memory);
    if (close_result != 0)
    {
        free(json);
        return NULL;
    }
    return json;
}

static int ccb_copy_stream(FILE *src, FILE *dst)
{
    unsigned char buffer[16384];
    size_t got;
    while ((got = fread(buffer, 1u, sizeof(buffer), src)) > 0u)
    {
        if (fwrite(buffer, 1u, got, dst) != got)
        {
            return 0;
        }
    }
    return ferror(src) == 0;
}

int ccb_build_book(const CCBBookSpec *spec)
{
    CCBZipIndex zip_index;
    CCBPageEntry *pages;
    uint32_t page_count;
    char *manifest_json;
    FILE *src;
    FILE *dst;
    CCBHeader header;
    uint64_t source_zip_size;
    if (!spec || !spec->source_zip_path || !spec->output_ccp_path)
    {
        return 0;
    }
    memset(&zip_index, 0, sizeof(zip_index));
    pages = NULL;
    page_count = 0u;
    manifest_json = NULL;

    if (!ccb_load_zip_index(spec->source_zip_path, &zip_index))
    {
        ccb_index_free(&zip_index);
        return 0;
    }
    if (!ccb_collect_pages(&zip_index, &pages, &page_count))
    {
        ccb_index_free(&zip_index);
        free(pages);
        return 0;
    }
    manifest_json = ccb_build_manifest_json(spec, pages, page_count);
    if (!manifest_json)
    {
        ccb_index_free(&zip_index);
        free(pages);
        return 0;
    }

    src = fopen(spec->source_zip_path, "rb");
    dst = fopen(spec->output_ccp_path, "wb");
    if (!src || !dst)
    {
        if (src) fclose(src);
        if (dst) fclose(dst);
        ccb_index_free(&zip_index);
        free(pages);
        free(manifest_json);
        return 0;
    }

    source_zip_size = ccb_file_size(src);
    memcpy(header.magic, CCB_MAGIC, sizeof(header.magic));
    header.version = CCB_VERSION;
    header.page_count = page_count;
    header.manifest_size = (uint64_t)strlen(manifest_json);
    header.source_zip_size = source_zip_size;

    if (fwrite(&header, 1u, sizeof(header), dst) != sizeof(header))
    {
        fclose(src);
        fclose(dst);
        ccb_index_free(&zip_index);
        free(pages);
        free(manifest_json);
        return 0;
    }
    if (fwrite(manifest_json, 1u, (size_t)header.manifest_size, dst) != (size_t)header.manifest_size)
    {
        fclose(src);
        fclose(dst);
        ccb_index_free(&zip_index);
        free(pages);
        free(manifest_json);
        return 0;
    }
    if (!ccb_copy_stream(src, dst))
    {
        fclose(src);
        fclose(dst);
        ccb_index_free(&zip_index);
        free(pages);
        free(manifest_json);
        return 0;
    }

    fclose(src);
    fclose(dst);
    ccb_index_free(&zip_index);
    free(pages);
    free(manifest_json);
    return 1;
}

static void ccb_print_usage(const char *exe_name)
{
    fprintf(stderr, "Usage: %s <input.zip> <output.ccp> [--title NAME] [--mode MODE] [--prompt-map prompt_map.json]\n", exe_name);
}

int main(int argc, char **argv)
{
    CCBBookSpec spec;
    int index;
    if (argc < 3)
    {
        ccb_print_usage(argv[0]);
        return 1;
    }
    memset(&spec, 0, sizeof(spec));
    spec.source_zip_path = argv[1];
    spec.output_ccp_path = argv[2];
    spec.title = "ClipConceptBook";
    spec.book_mode = "interactive";
    for (index = 3; index < argc; ++index)
    {
        if (strcmp(argv[index], "--title") == 0 && index + 1 < argc)
        {
            spec.title = argv[++index];
        }
        else if (strcmp(argv[index], "--mode") == 0 && index + 1 < argc)
        {
            spec.book_mode = argv[++index];
        }
        else if (strcmp(argv[index], "--prompt-map") == 0 && index + 1 < argc)
        {
            spec.prompt_map_path = argv[++index];
        }
        else
        {
            ccb_print_usage(argv[0]);
            return 1;
        }
    }
    if (!ccb_build_book(&spec))
    {
        fprintf(stderr, "Failed to build ClipConceptBook from %s\n", spec.source_zip_path);
        return 2;
    }
    printf("Built %s\n", spec.output_ccp_path);
    return 0;
}