CC ?= gcc
CXX ?= g++
CFLAGS ?= -O2 -Wall
LDFLAGS ?=

TARGET := {project_name}
SRC := $(wildcard src/*.c src/*.cpp)
OBJ := $(SRC:.c=.o)

all: build

build:
	$(CXX) $(CFLAGS) -o $(TARGET) $(SRC) $(LDFLAGS)

clean:
	rm -f $(TARGET) $(OBJ)
