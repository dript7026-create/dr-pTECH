# CryptWire v0.1.0 — Makefile
#
# Targets:
#   make            — build cryptwire (Linux/macOS, requires OpenSSL)
#   make windows    — build for Windows with MinGW + OpenSSL
#   make clean      — remove build artefacts
#   make test       — run basic encrypt/decrypt roundtrip test
#
# ─── Linux / macOS ───────────────────────────────────────────────────
CC      = gcc
CFLAGS  = -Wall -Wextra -Wpedantic -O2 -std=c11 \
          -D_POSIX_C_SOURCE=200809L
LDFLAGS = -lssl -lcrypto -lm

# If OpenSSL is installed in a non-standard prefix (e.g. Homebrew on macOS):
#   make OPENSSL_PREFIX=/opt/homebrew/opt/openssl@3
ifdef OPENSSL_PREFIX
  CFLAGS  += -I$(OPENSSL_PREFIX)/include
  LDFLAGS += -L$(OPENSSL_PREFIX)/lib -Wl,-rpath,$(OPENSSL_PREFIX)/lib
endif

TARGET = cryptwire
SRCS   = main.c cryptwire.c cryptwire_ai.c
HDRS   = cryptwire.h cryptwire_ai.h
OBJS   = $(SRCS:.c=.o)

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) -o $@ $^ $(LDFLAGS)

%.o: %.c $(HDRS)
	$(CC) $(CFLAGS) -c -o $@ $<

# ─── Windows (MinGW-w64 + OpenSSL Win64) ─────────────────────────────
# Adjust OPENSSL_WIN to your OpenSSL installation.
# Download OpenSSL for Windows: https://slproweb.com/products/Win32OpenSSL.html
OPENSSL_WIN  = C:/OpenSSL-Win64
CC_WIN       = x86_64-w64-mingw32-gcc
CFLAGS_WIN   = -Wall -Wextra -O2 -std=c11 \
               -I$(OPENSSL_WIN)/include \
               -DWIN32_LEAN_AND_MEAN
LDFLAGS_WIN  = -L$(OPENSSL_WIN)/lib \
               -lssl -lcrypto -lws2_32 -lcrypt32 -lm \
               -Wl,-Bstatic -static-libgcc

windows:
	$(CC_WIN) $(CFLAGS_WIN) -o cryptwire.exe $(SRCS) $(LDFLAGS_WIN)

# ─── Test target ─────────────────────────────────────────────────────
TEST_DIR = /tmp/cw_test
TESTFILE = $(TEST_DIR)/plaintext.bin
ENC_FILE = $(TEST_DIR)/encrypted.cwt
DEC_FILE = $(TEST_DIR)/decrypted.bin
KS_FILE  = $(TEST_DIR)/test.cwks

test: all
	@mkdir -p $(TEST_DIR)
	@echo "Generating test data (1024 random bytes)..."
	@dd if=/dev/urandom of=$(TESTFILE) bs=1024 count=1 2>/dev/null
	@echo
	@echo "--- Generate key store ---"
	./$(TARGET) genkey --out $(KS_FILE)
	@echo
	@echo "--- Encrypt ---"
	./$(TARGET) encrypt $(TESTFILE) $(ENC_FILE) --ks $(KS_FILE)
	@echo
	@echo "--- Decrypt ---"
	./$(TARGET) decrypt $(ENC_FILE) $(DEC_FILE) --ks $(KS_FILE)
	@echo
	@echo "--- Verify roundtrip ---"
	@if cmp -s $(TESTFILE) $(DEC_FILE); then \
	  echo "PASS: plaintext == decrypted"; \
	else \
	  echo "FAIL: mismatch!"; exit 1; \
	fi
	@echo
	@echo "--- Status ---"
	./$(TARGET) status --ks $(KS_FILE)

clean:
	rm -f $(OBJS) $(TARGET) $(TARGET).exe

.PHONY: all windows test clean
