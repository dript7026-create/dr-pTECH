#include <gba.h>
#include <stdio.h>
#include "vn.h"

void vn_play(void) {
    consoleDemoInit();
    const char *panels[] = {
        "Chapter 1: The Storm\nRei remembers the harbor lullaby.",
        "Chapter 2: Resonance\nNanites singing under the moon.",
        "Chapter 3: Choice\nPurify or Recode? The islands watch."
    };
    int panelsCount = 3;
    for (int i = 0; i < panelsCount; ++i) {
        consoleDemoInit();
        iprintf("%s\n\nPress A to continue.", panels[i]);
        while (!(keysDown() & KEY_A)) { VBlankIntrWait(); scanKeys(); }
        // small delay to prevent repeated instant advance
        for (int f = 0; f < 20; ++f) VBlankIntrWait();
    }
    iprintf("End of VN stub. Press START to return.");
    while (!(keysDown() & KEY_START)) { VBlankIntrWait(); scanKeys(); }
}
