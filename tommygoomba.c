#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <conio.h>

#define STAGE_COUNT 66

int main(void) {
    srand((unsigned)time(NULL));
    int stage = rand() % STAGE_COUNT;
    int wife = rand() % STAGE_COUNT;
    int running = 1;

    puts("Tommy Goomba (Windows Console Simulation)");
    puts("A=search, J=left, L=right, I=+5, K=-5, Q=quit");

    while (running) {
        printf("\rStage %d/66 | Wife maybe at %d/66   ", stage + 1, wife + 1);
        if (_kbhit()) {
            int c = _getch();
            if (c == 'q' || c == 'Q') running = 0;
            else if (c == 'j' || c == 'J') stage = (stage + STAGE_COUNT - 1) % STAGE_COUNT;
            else if (c == 'l' || c == 'L') stage = (stage + 1) % STAGE_COUNT;
            else if (c == 'i' || c == 'I') stage = (stage + 5) % STAGE_COUNT;
            else if (c == 'k' || c == 'K') stage = (stage + STAGE_COUNT - 5) % STAGE_COUNT;
            else if (c == 'a' || c == 'A') {
                if (stage == wife) {
                    puts("\nReunion found. Win.");
                    break;
                } else {
                    puts("\nSearch failed.");
                }
            }
        }
    }
    puts("\nExit.");
    return 0;
}
