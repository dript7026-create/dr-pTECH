## KaijuGaiden devkitPro Makefile (minimal skeleton)
# Note: This is a lightweight example. Install devkitPro/devkitARM and adjust paths as needed.

TITLE := kaijugaiden
SOURCES := kaijugaiden_gba.c src/game.c src/genetics.c src/boss.c src/vn.c src/state.c src/password.c src/boss_manager.c src/minion.c src/gba_assets_loader.c src/ui.c src/audio.c src/sprites.c
OBJECTS := $(SOURCES:.c=.o)

CC := arm-none-eabi-gcc
OBJCOPY := arm-none-eabi-objcopy

CFLAGS := -mthumb -mthumb-interwork -O2 -Wall -fno-strict-aliasing -ffast-math
LDFLAGS :=

# If libgba headers/libs are available in a local devkitPro install, add them
ifneq ($(wildcard /c/devkitPro/libgba/include/gba.h),)
CFLAGS += -I/c/devkitPro/libgba/include
LDFLAGS += -L/c/devkitPro/libgba/lib -lgba
endif

# Prefer an absolute nosys.specs from a local devkitPro install when available
ifneq ($(wildcard /c/devkitPro/devkitARM/arm-none-eabi/lib/nosys.specs),)
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
	rm -f $(TITLE).elf $(TITLE).gba $(OBJECTS)

.PHONY: all clean

# Host build (Windows / MSYS2) — builds a console executable using local shims
HOST_SOURCES := $(SOURCES) src/host_gba.c
HOST_CC := gcc
HOST_CFLAGS := -DHOST_BUILD -Iinclude -O2 -Wall

.PHONY: host
host: host.exe

host.exe: $(HOST_SOURCES)
	$(HOST_CC) $(HOST_CFLAGS) $(HOST_SOURCES) -o host.exe

# convenience target: generate GBA headers from placeholder assets
.PHONY: gba-convert
gba-convert:
	python tools/convert_to_gba.py --src assets/placeholderassets --out build/gba

# Run the graphical host (Tkinter). Checks availability then launches.
.PHONY: host_gui
host_gui:
	python host_check_tk.py
	python host_graphical.py

# Build xinput wrapper (windows only)
build/xinput_wrapper.dll: src/xinput_wrapper.c src/xinput_wrapper.h
	@if not exist build mkdir build
	@gcc -shared -o build/xinput_wrapper.dll src/xinput_wrapper.c -Wl,--output-def,build/xinput_wrapper.def

.PHONY: xinput-wrap
xinput-wrap: build/xinput_wrapper.dll
	@echo Built xinput wrapper

