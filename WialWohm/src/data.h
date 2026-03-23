#ifndef WIALWOHM_DATA_H
#define WIALWOHM_DATA_H

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

#define WIAL_EVOLUTIONS_COUNT 123
#define ENEMIES_COUNT 56
#define WOHM_TYPES_COUNT 5
#define RESOURCES_COUNT 500
#define CROPS_COUNT 166
#define TOOLS_COUNT 3

extern char* wial_evolutions[WIAL_EVOLUTIONS_COUNT];
extern char* enemies[ENEMIES_COUNT];
extern char* wohm_types[WOHM_TYPES_COUNT];
extern char* resources[RESOURCES_COUNT];

typedef struct {
    char* id;
    char* seed;
    char* plant;
    char* fruit;
} Crop;

extern Crop crops[CROPS_COUNT];
extern char* tools[TOOLS_COUNT];

void init_game_data(void);
void cleanup_game_data(void);

#ifdef __cplusplus
}
#endif

#endif // WIALWOHM_DATA_H
