    .text
    .global get_seed_hash
    .type get_seed_hash, %function
get_seed_hash:
    // ARM64 (aarch64) simple hash: return first byte of string (0 if NULL)
    // x0 = pointer to string
    cbz x0, .Lnull
    ldrb w0, [x0]
    ret
.Lnull:
    mov w0, #0
    ret
