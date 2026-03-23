// Minimal host shim for GBA APIs used by the prototype when building on Windows
#ifndef GBA_H
#define GBA_H

#include <stdint.h>

typedef uint16_t u16;
typedef uint32_t u32;

// Key masks (simple mapping)
#define KEY_START 0x0001
#define KEY_A     0x0002
#define KEY_B     0x0004
#define KEY_SELECT 0x0008
#define KEY_L     0x0010
#define KEY_R     0x0020
#define KEY_UP    0x0040
#define KEY_DOWN  0x0080
#define KEY_LEFT  0x0100
#define KEY_RIGHT 0x0200

// Prototypes for host implementations
void irqInit(void);
void irqEnable(int flags);
void VBlankIntrWait(void);
void scanKeys(void);
u16 keysDown(void);
void consoleDemoInit(void);
int iprintf(const char *fmt, ...);
void consoleClear(void);

#endif // GBA_H
