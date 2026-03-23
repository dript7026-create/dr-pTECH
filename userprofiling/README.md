# userprofiling — Genomic GA test notes

By default the genomic / GA functionality in `userpersonalitytracking.c` is inactive.

- To enable at compile time, define `GENOME_ENABLED=1`.
- Compile and run the provided test harness to simulate interactions and evolve a genome.

Example compile + run (from repository root):

```bash
gcc -O2 -std=c11 -lm -DGENOME_ENABLED=1 -o userprofile userprofiling/test_genome.c
./userprofile
```

Files:
- `userpersonalitytracking.c`: main profiling code (genome/GA behind `GENOME_ENABLED`).
- `test_genome.c`: small harness that simulates interactions and calls `evolve_and_attach_genome()`.

Use this harness as a starting point for integration tests or real data feeds.
