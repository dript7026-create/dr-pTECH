CC = gcc
CFLAGS = -std=c11 -O2 -Wall
SRC = egosphere.c demo.c
TARGET = demo

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC)

clean:
	rm -f $(TARGET)
