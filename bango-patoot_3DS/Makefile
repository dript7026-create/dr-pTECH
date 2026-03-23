.SUFFIXES:

ifeq ($(strip $(DEVKITARM)),)
$(error "Please set DEVKITARM in your environment. export DEVKITARM=<path to>devkitARM")
endif

TOPDIR ?= $(CURDIR)
include $(DEVKITARM)/3ds_rules

DEVKITPRO_UNIX   := $(patsubst C:/%,/c/%,$(subst \,/,$(DEVKITPRO)))
CTRULIB_UNIX     := $(DEVKITPRO_UNIX)/libctru
PORTLIBS_3DS     := $(DEVKITPRO_UNIX)/portlibs/3ds

TARGET          :=      BangoPatoot
BUILD           :=      build
SOURCES         :=      . ../egosphere bango_engine_target/src
INCLUDES        :=      . ../egosphere bango_engine_target/include
NO_SMDH         :=      1

ARCH    :=      -march=armv6k -mtune=mpcore -mfloat-abi=hard -mtp=soft

CFLAGS  :=      -g -Wall -O2 -mword-relocations -ffunction-sections $(ARCH)
CFLAGS  +=      $(INCLUDE) -D__3DS__
CXXFLAGS        :=      $(CFLAGS) -fno-rtti -fno-exceptions -std=gnu++11
ASFLAGS :=      -g $(ARCH)
LDFLAGS =       -specs=3dsx.specs -g $(ARCH) -Wl,-Map,$(notdir $*.map)
LIBS    :=      -lcitro2d -lcitro3d -lctru -lm
LIBDIRS :=      $(CTRULIB_UNIX) $(PORTLIBS_3DS)

ifneq ($(BUILD),$(notdir $(CURDIR)))

export OUTPUT   :=      $(CURDIR)/$(TARGET)
export TOPDIR   :=      $(CURDIR)
export VPATH    :=      $(foreach dir,$(SOURCES),$(TOPDIR)/$(dir))
export DEPSDIR  :=      $(CURDIR)/$(BUILD)

CFILES          :=      bango-patoot_3DS.c egosphere.c bango_engine_target.c bango_telemetry_bridge_stub.c
export OFILES_SOURCES   :=      $(CFILES:.c=.o)
export OFILES   :=      $(OFILES_SOURCES)
export INCLUDE  :=      $(foreach dir,$(INCLUDES),-I$(TOPDIR)/$(dir)) \
                        $(foreach dir,$(LIBDIRS),-I$(dir)/include) \
						-I$(TOPDIR)/$(BUILD)
export LIBPATHS :=      $(foreach dir,$(LIBDIRS),-L$(dir)/lib)
export _3DSXDEPS :=
export LD       :=      $(CC)

.PHONY: all clean

all: $(BUILD)
	@$(MAKE) --no-print-directory -C $(BUILD) -f $(CURDIR)/Makefile

$(BUILD):
	@mkdir -p $@

clean:
	@echo clean ...
	@rm -fr $(BUILD) $(TARGET).3dsx $(TARGET).elf $(TARGET).smdh

else

$(OUTPUT).3dsx : $(OUTPUT).elf $(_3DSXDEPS)
$(OUTPUT).elf  : $(OFILES)

-include $(DEPSDIR)/*.d

endif