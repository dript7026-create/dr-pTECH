CC = gcc
CFLAGS = -std=c11 -O2 -Wall
LDFLAGS = -lm
PYTHON ?= python
SRC = egosphere.c demo.c
TARGET = demo
SMOKE_TARGET = smoke_test
SMOKE_SRC = egosphere.c smoke_test.c

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC) $(LDFLAGS)

$(SMOKE_TARGET): $(SMOKE_SRC)
	$(CC) $(CFLAGS) -o $(SMOKE_TARGET) $(SMOKE_SRC) $(LDFLAGS)

smoke-test: $(SMOKE_TARGET)
	./$(SMOKE_TARGET)

test: smoke-test

validate-pipeline:
	$(PYTHON) tools/validate_pipeline.py

validate-pipeline-all:
	$(PYTHON) tools/validate_pipeline.py --suite all

validate-pipeline-gui:
	$(PYTHON) tools/validate_pipeline.py --gui

pipeline-test: validate-pipeline-all

clean:
	rm -f $(TARGET) $(SMOKE_TARGET) egosphere_rivals.dat smoke_rivals.dat

inspect:
	$(PYTHON) tools/inspect_mindsphere_save.py egosphere_rivals.dat --full

