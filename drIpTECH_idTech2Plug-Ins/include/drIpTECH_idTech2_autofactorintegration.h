#ifndef DRIPTECH_IDTECH2_AUTOFACTORINTEGRATION_H
#define DRIPTECH_IDTECH2_AUTOFACTORINTEGRATION_H

#include <stddef.h>

typedef struct {
    const char *asset_id;
    const char *asset_path;
    const char *asset_type;
} DriptechIdAsset;

typedef struct {
    const char *system_name;
} DriptechIdSystem;

typedef struct {
    const char *alias;
    const char *asset_path;
    const char *asset_type;
} DriptechIdPrecache;

typedef struct {
    const char *system_name;
    const char *init_fn;
    const char *tick_fn;
} DriptechIdDispatch;

typedef struct {
    const char *entity_id;
    const char *classname;
    const char *asset_id;
    int x;
    int y;
    int z;
} DriptechIdSpawn;

int driptech_idtech2_emit_registry(
    const char *header_path,
    const char *source_path,
    const char *prefix,
    const DriptechIdAsset *assets,
    size_t asset_count,
    const DriptechIdSystem *systems,
    size_t system_count,
    const DriptechIdSpawn *spawns,
    size_t spawn_count);

int driptech_idtech2_emit_runtime(
    const char *header_path,
    const char *source_path,
    const char *prefix,
    const DriptechIdAsset *assets,
    size_t asset_count,
    const DriptechIdPrecache *precache,
    size_t precache_count,
    const DriptechIdSystem *systems,
    size_t system_count,
    const DriptechIdDispatch *dispatch,
    size_t dispatch_count,
    const DriptechIdSpawn *spawns,
    size_t spawn_count);

#endif