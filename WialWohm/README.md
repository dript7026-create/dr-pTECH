# WialWohm Prototype

Lightweight C prototype for the WialWohm data model (formerly OrgyBhorgey). Generates sample data sets for Wials (evolutions), Wohms (types), enemies, resources, crops, and tools.

Build (MinGW/clang/gcc on Windows):

```bash
gcc -I src -o WialWohm.exe src/main.c src/data.c
```

The user will supply graphical assets later for integration into an ORBEngine-based demo.
