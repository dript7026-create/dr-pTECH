ROM=tommybeta.gb
SRC=src/main.c

all: $(ROM)

$(ROM): $(SRC)
	@echo Building $(ROM) with lcc (GBDK)
	@lcc -o $(ROM) $(SRC)

clean:
	-rm -f $(ROM) *.ihx *.asm *.sym *.lst
