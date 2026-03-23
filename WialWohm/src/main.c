#include <stdio.h>
#include "data.h"

int main(void) {
    init_game_data();

    printf("WialWohm prototype data summary:\n");
    printf("- Wial evolutions: %d\n", WIAL_EVOLUTIONS_COUNT);
    printf("  first: %s\n", wial_evolutions[0]);
    printf("  last:  %s\n", wial_evolutions[WIAL_EVOLUTIONS_COUNT-1]);

    printf("- Enemies: %d\n", ENEMIES_COUNT);
    printf("  sample: %s, %s\n", enemies[0], enemies[ENEMIES_COUNT/2]);

    printf("- Wohm types: %d\n", WOHM_TYPES_COUNT);
    for (int i = 0; i < WOHM_TYPES_COUNT; ++i) printf("  %s\n", wohm_types[i]);

    printf("- Resources: %d (sample)\n", RESOURCES_COUNT);
    printf("  %s, %s, %s\n", resources[0], resources[1], resources[RESOURCES_COUNT-1]);

    printf("- Crops: %d (first crop seed/plant/fruit)\n", CROPS_COUNT);
    printf("  %s / %s / %s\n", crops[0].seed, crops[0].plant, crops[0].fruit);

    printf("- Tools: %d\n", TOOLS_COUNT);
    for (int i = 0; i < TOOLS_COUNT; ++i) printf("  %s\n", tools[i]);

    cleanup_game_data();
    return 0;
}
