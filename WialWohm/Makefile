CC=gcc
CFLAGS=-I src -O2
SRC=src/main.c src/data.c
OUT=WialWohm.exe

all:
	$(CC) $(CFLAGS) -o $(OUT) $(SRC)

clean:
	del $(OUT) 2>nul || true
