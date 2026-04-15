TITLE ?= skulldummy_gba
SOURCES := src/main.c build/gba_assets/skulldummy_assets.c

CC := arm-none-eabi-gcc
OBJCOPY := arm-none-eabi-objcopy
GBAFIX := gbafix

GAME_TITLE := SKULLDUMMY
GAME_CODE := SKDY
MAKER_CODE := 01

CFLAGS := -mthumb -mthumb-interwork -O2 -Wall -fno-strict-aliasing -Ibuild/gba_assets
LDFLAGS :=

ifneq ($(wildcard /c/devkitPro/libgba/include/gba.h),)
CFLAGS += -I/c/devkitPro/libgba/include
LDFLAGS += -L/c/devkitPro/libgba/lib -lgba
endif

ifneq ($(wildcard /c/devkitPro/devkitARM/arm-none-eabi/lib/gba.specs),)
LDFLAGS += -specs=/c/devkitPro/devkitARM/arm-none-eabi/lib/gba.specs -Wl,-Map,$(TITLE).map
else
LDFLAGS += -specs=gba.specs -Wl,-Map,$(TITLE).map
endif

all: $(TITLE).gba

$(TITLE).elf: $(SOURCES)
	$(CC) $(CFLAGS) $(SOURCES) -o $(TITLE).elf $(LDFLAGS)

$(TITLE).gba: $(TITLE).elf
	$(OBJCOPY) -O binary $(TITLE).elf $(TITLE).gba
	$(GBAFIX) $(TITLE).gba -t$(GAME_TITLE) -c$(GAME_CODE) -m$(MAKER_CODE) -p

clean:
	rm -f $(TITLE).elf $(TITLE).gba $(TITLE).map

.PHONY: all clean