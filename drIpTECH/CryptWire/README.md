# CryptWire v0.1.0

Multi-layer adaptive encryption pipeline with AI-guided threat response.

---

## What it is

CryptWire is a C library + CLI tool that wraps data in a cascaded series of
authenticated encryption stages. The number of stages, the algorithm chosen
per stage, and the depth of the final cryptographic seal all adapt in real
time based on an 8-dimensional threat-analysis engine backed by a genetic
algorithm (GA).

It is **not** a VPN, firewall, or kernel driver. It is a data-at-rest and
data-in-transit encryption layer — every file or byte-stream you pass through
it comes out wrapped in the CryptWire packet format, verifiable only on the
same machine that encrypted it.

---

## Pipeline

```
Plaintext
   │
   ▼  Stage 0 — AES-256-GCM  (no feedback from prior stage)
   │     key₀ = HKDF(master, salt, "CW_STAGE0")
   │     IV₀  = RAND(12 bytes)
   │     ── outputs ct₀, tag₀
   │
   ▼  Stage 1 — ChaCha20-Poly1305  (feedback: tag₁ → re-encrypts ct₀)
   │     key₁ = HKDF(master, salt, "CW_STAGE1")
   │     ct₀  ← AES-256-CTR(HKDF(master, tag₁, "FBK"), ct₀)   [FEEDBACK]
   │     AI recommends algo for Stage 2                          [LOOK-AHEAD]
   │     ── outputs ct₁, tag₁
   │
   ▼  Stage 2 — [AI recommended]   (feedback: tag₂ → re-encrypts ct₁)
   │     key₂ = HKDF(master, salt, "CW_STAGE2")
   │     ct₁  ← AES-256-CTR(HKDF(master, tag₂, "FBK"), ct₁)   [FEEDBACK]
   │     ── outputs ct₂, tag₂
   │
   ▼  [Further stages if threat level is HIGH/CRITICAL — up to 8 total]
   │
   ▼  SEAL — depth-scaled HMAC-SHA256 chain
         depth = base(threat_level) + AI_seal_extra
         Seed  = concat(tag₀, tag₁, …, tagₙ)
         acc   = HMAC-SHA256(master, seed)
         for i in 0..depth-1:
             if i == 999 and depth ≥ 1000:    ← CONVERGENCE ROUND
                 acc = PBKDF2(acc, SHA256(all_ciphertexts), 8192 iter)
             acc = HMAC-SHA256(master, acc ‖ i)
         seal_digest = acc   [appended to output packet]
```

### Seal depth table

| Threat level | Base depth   |
|:-------------|:-------------|
| NONE         | 64           |
| LOW          | 256          |
| MEDIUM       | 1 024        |
| HIGH         | 4 096        |
| CRITICAL     | 16 384  (+convergence round at iter 999) |

The AI module adds `seal_extra` iterations on top of the base, scaled by the
GA's best genome fitness against current threat observations.

---

## AI Module

### 8 threat dimensions

| # | Name              | What it measures |
|:--|:------------------|:-----------------|
| 0 | `ENTROPY_ANOM`    | Unusual entropy in observed streams |
| 1 | `FREQ_BURST`      | Request / packet frequency spikes |
| 2 | `TIMING_PATTERN`  | Regularity suggesting timing attacks |
| 3 | `SRC_REPUTATION`  | Matches against threat signature DB |
| 4 | `PAYLOAD_SHAPE`   | Abnormal payload size / structure |
| 5 | `PROTO_INTEGRITY` | Protocol conformance anomalies |
| 6 | `TEMPORAL_CLUSTER`| Events clustered in time (attack waves) |
| 7 | `KEY_PROBE`       | Elevated key-derivation-overhead events |

Each dimension is updated via exponential moving average (α=0.15). Temporal
clustering is additionally detected by a sliding 5-second event window.

### Genetic algorithm evolution

- **Population:** 32 genomes
- **Genome:** `float weights[8]` + `uint8_t algo[8]` (per-stage algorithm
  preference) + `num_stages` + `seal_extra`
- **Fitness:** `1 / (weighted_threat_score × false_positive_rate + ε)`
- **Selection:** tournament (k=4)
- **Crossover:** single-point on weight array + separate point on algo array
- **Mutation:** Gaussian perturbation (σ=0.1) on weights, random flip on algos
- **Elite:** top 4 genomes preserved unchanged each generation
- **Trigger:** every 100 observed events, or immediately on confirmed threat

---

## Key storage

Keys are **never** stored in plaintext. The key store file (`master.cwks`) is:

1. Encrypted with AES-256-GCM using a file-encryption key derived by
   PBKDF2-HMAC-SHA256 from the **machine fingerprint** (hostname + volume
   serial on Windows; hostname + UTS on Linux).
2. Stored in a restricted-permissions directory:
   - Windows: `%APPDATA%\CryptWire\`  (ACL: Administrators + current user)
   - Linux: `~/.cryptwire/`  (chmod 0700)
3. Bound to the current machine: a machine-ID hash embedded in every encrypted
   packet causes decryption to fail on any other machine.

Session logs (human-readable event log, **not** key material) are written to
`<keystore_dir>/logs/session_YYYY-MM-DD.log`, also in the restricted directory.

> **Why not scatter keys across the disk?**  Scattering raw key material
> increases the attack surface: an adversary who gains read access to any one
> copy wins.  A single encrypted, permission-restricted key store is harder to
> exfiltrate and easier to audit.

---

## Wire format

```
Offset  Length  Field
──────  ──────  ───────────────────────────────────────────────
0       4       Magic: "CWIR" (0x43 0x57 0x49 0x52)
4       2       Version: 0x0001 (LE)
6       1       num_stages
7       1       flags (reserved)
8       8       timestamp (Unix seconds, uint64 LE)
16      32      machine_id_hash (SHA-256 of machine fingerprint)
── per stage (repeat num_stages times) ──────────────────────────
48+     1       algo_id (1=AES-GCM, 2=ChaCha20-Poly, 3=CBC-HMAC)
        1       reserved
        16      IV / nonce (padded to 16 bytes)
        16      auth_tag
        4       ct_len (LE)
        ct_len  ciphertext bytes
── trailer ───────────────────────────────────────────────────────
        4       seal_depth (LE)
        32      seal_digest (HMAC-SHA256)
```

---

## Build

### Linux / macOS

```sh
# Install OpenSSL dev headers first:
#   Ubuntu/Debian: sudo apt install libssl-dev
#   macOS/Homebrew: brew install openssl@3

cd drIpTECH/CryptWire
make
```

### Windows (MinGW-w64)

1. Install [OpenSSL for Windows](https://slproweb.com/products/Win32OpenSSL.html)
   (e.g. to `C:\OpenSSL-Win64`).
2. Install MinGW-w64 or use the MSYS2 MinGW shell.

```sh
make windows
# or cross-compile from Linux:
# make windows OPENSSL_WIN=/path/to/openssl-win64-headers
```

Alternatively, use CMake with the MSVC toolchain and `-DOPENSSL_ROOT_DIR=...`.

---

## Usage

```sh
# 1. Generate a machine-bound key store (do this once per machine)
cryptwire genkey

# 2. Encrypt a file
cryptwire encrypt secret.txt secret.cwt

# 3. Decrypt
cryptwire decrypt secret.cwt secret_recovered.txt

# 4. Rotate master key (run on a schedule — default reminder: every 6 hours)
cryptwire rotate

# 5. Show pipeline + AI threat state
cryptwire status

# 6. Continuous stream monitoring (piped or from stdin)
tail -f /var/log/syslog | cryptwire monitor

# 7. Scan a file against threat signature database
cryptwire scan suspicious_payload.bin --sigs signatures.txt
```

---

## Threat signature database format

Plain text, one entry per line:
```
<id> <severity 0.0–1.0> <hex_pattern> <description>
1 0.9 deadbeef "Known bad magic bytes"
2 0.7 4d5a9000 "Windows PE header in unexpected context"
```

---

## Network / machine-wide encryption

CryptWire provides the **encryption layer**. To intercept the full machine
data stream, you need an OS-level integration:

- **Windows:** Windows Filtering Platform (WFP) callout driver or a TUN
  adapter using the WinTun/OpenVPN-DCO driver. Feed captured bytes through
  `cw_encrypt()` / `cw_decrypt()` in a kernel/userspace split.
- **Linux:** `nftables` + `NFQUEUE` or a TUN/TAP virtual interface. Integrate
  CryptWire as the userspace packet processor via `libnetfilter_queue`.

These integration drivers are outside the scope of v0.1 and require separate
OS-specific development + code-signing.

---

## Server deployment

To deploy CryptWire on a server:

1. Build the binary on the target server (or cross-compile for its architecture).
2. Run `cryptwire genkey` on that server to create a machine-bound key store.
3. Configure the service (systemd unit, Windows service) to invoke
   `cryptwire monitor` or to call the library functions from your application.
4. Set strict filesystem ACLs on `%APPDATA%\CryptWire\` (Windows) or
   `~/.cryptwire/` (Linux) so only the service account can read it.
5. Schedule `cryptwire rotate` every 6 hours via cron / Task Scheduler.

> **Important:** Each server must generate its own key store. A key store
> created on one machine cannot decrypt data on another machine.

---

## Security notes and known limitations (v0.1)

- AES-256-GCM and ChaCha20-Poly1305 are NIST/IETF-approved AEAD ciphers.
  The multi-layer construction provides defence-in-depth but the practical
  security floor is AES-256 (computationally secure against known attacks).
- HKDF-SHA256 (RFC 5869) is used for all key derivation.
- The feedback reencryption step (AES-256-CTR with tag-derived key) creates
  cross-stage authentication binding. It is involutory: applying it twice
  restores the original.
- No network communication is performed by this library. Threat data must be
  fed in by the calling application.
- The GA "real-time research" lives entirely in-process; external threat
  intelligence feeds must be imported via the signature database file.
- v0.1 does not implement authenticated key exchange. Both encrypt and decrypt
  sides must share the same key store (symmetric-key model).
- Signed manifests and key-exchange protocol are planned for v0.2.

---

## Roadmap

| Version | Planned features |
|:--------|:-----------------|
| v0.1    | Core pipeline, AEAD layers, AI/GA module, machine-bound key store, CLI |
| v0.2    | Signed packet manifests (Ed25519), key-exchange bootstrap (X25519 ECDH) |
| v0.3    | External threat-intel feed API, encrypted signature DB, stream-cipher tunnel mode |
| v0.4    | WFP/nftables integration guide + reference driver skeleton |

---

*CryptWire is research / prototype software. Conduct a formal security audit
before using it to protect production data.*
