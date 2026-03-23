#include <stdint.h>

typedef uint16_t u16;

#define REG_DISPCNT (*(volatile u16 *)0x04000000)
#define MODE3 0x0003
#define BG2_ENABLE 0x0400
#define RGB15(r,g,b) ((r) | ((g) << 5) | ((b) << 10))

static volatile u16 *const video = (volatile u16 *)0x06000000;

int main(void) {
    int x;
    int y;
    REG_DISPCNT = MODE3 | BG2_ENABLE;

    for (y = 0; y < 160; ++y) {
        for (x = 0; x < 240; ++x) {
            u16 color;
            if (y < 32) color = RGB15(31, 0, 0);
            else if (y < 64) color = RGB15(31, 31, 0);
            else if (y < 96) color = RGB15(0, 31, 0);
            else if (y < 128) color = RGB15(0, 0, 31);
            else color = RGB15(31, 31, 31);

            if (((x / 8) + (y / 8)) & 1) {
                color ^= RGB15(8, 8, 8);
            }
            video[y * 240 + x] = color;
        }
    }

    for (;;) {
    }
}