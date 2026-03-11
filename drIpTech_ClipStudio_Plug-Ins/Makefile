CC = gcc
CFLAGS = -std=c11 -O2 -Wall
SRC = ClipStudioPixelBrushSuite.c test_plugin_demo.c
TARGET = test_plugin_demo

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC)

clean:
	rm -f $(TARGET)
