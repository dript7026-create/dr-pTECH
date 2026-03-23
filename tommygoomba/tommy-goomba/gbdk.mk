# GBDK Makefile Configuration for TOMMY GOOMBA

TARGET := tommygoomba
GBDK_DIR := gbdk
SRC_DIR := src
INC_DIR := include
ASSETS_DIR := assets
OBJ_DIR := obj

# Source files
SRC_FILES := $(wildcard $(SRC_DIR)/*.c) $(wildcard $(SRC_DIR)/stages/*.c) $(ASSETS_DIR)/tiles/tileset.c $(ASSETS_DIR)/maps/*.c $(ASSETS_DIR)/sprites/sprites.c
OBJ_FILES := $(patsubst $(SRC_DIR)/%.c,$(OBJ_DIR)/%.rel,$(SRC_FILES))

# Include directories
INCLUDES := -I$(INC_DIR) -I$(ASSETS_DIR)

# Compiler and linker options
CFLAGS := -Wall -Werror -mgbz80 -O2 $(INCLUDES)
LDFLAGS := -lgbdk

# Build rules
all: $(TARGET).gb

$(TARGET).gb: $(OBJ_FILES)
	$(GBDK_DIR)/gbdk -o $@ $^

$(OBJ_DIR)/%.rel: $(SRC_DIR)/%.c
	@mkdir -p $(OBJ_DIR)
	$(GBDK_DIR)/gbdk -c $(CFLAGS) -o $@ $<

clean:
	rm -f $(OBJ_DIR)/*.rel $(TARGET).gb

.PHONY: all clean