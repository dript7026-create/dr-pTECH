TITLE := gorge
SOURCES := src/main.c src/audio.c src/password.c

CC := arm-none-eabi-gcc
OBJCOPY := arm-none-eabi-objcopy

CFLAGS := -mthumb -mthumb-interwork -O2 -Wall -Wextra -std=gnu99 -fno-strict-aliasing
LDFLAGS :=

ifneq ($(wildcard /c/devkitPro/libgba/include/gba.h),)
CFLAGS += -I/c/devkitPro/libgba/include -I./src
LDFLAGS += -L/c/devkitPro/libgba/lib -lgba
else
CFLAGS += -I./src
endif

ifneq ($(wildcard /c/devkitPro/devkitARM/arm-none-eabi/lib/gba.specs),)
LDFLAGS += -specs=/c/devkitPro/devkitARM/arm-none-eabi/lib/gba.specs
else ifneq ($(wildcard /c/devkitPro/devkitARM/arm-none-eabi/lib/nosys.specs),)
LDFLAGS += -specs=/c/devkitPro/devkitARM/arm-none-eabi/lib/nosys.specs -Wl,-Ttext,0x08000000
else
LDFLAGS += -specs=nosys.specs -Wl,-Ttext,0x08000000
endif

all: $(TITLE).gba

$(TITLE).elf: $(SOURCES)
	$(CC) $(CFLAGS) $(SOURCES) -o $(TITLE).elf $(LDFLAGS)

$(TITLE).gba: $(TITLE).elf
	$(OBJCOPY) -O binary $(TITLE).elf $(TITLE).gba

clean:
	rm -f $(TITLE).elf $(TITLE).gba

.PHONY: all clean
