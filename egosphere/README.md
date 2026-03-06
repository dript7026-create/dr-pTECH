# egosphere

Minimal scaffold for the `egosphere` AI module.

Build:

```sh
gcc -std=c11 -O2 -o demo egosphere.c demo.c
```

Run:

```sh
./demo
```

Files:

- `egosphere.h` — public API and types
- `egosphere.c` — implementation (id / ego / superego tiers, memory, simple learning)
- `demo.c` — tiny runner that simulates an agent
