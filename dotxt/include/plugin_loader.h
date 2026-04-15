#ifndef DOTXT_PLUGIN_LOADER_H
#define DOTXT_PLUGIN_LOADER_H

#include <windows.h>

typedef struct DotxtPluginLoadReport {
    int manifestsFound;
    int loaded;
    int failed;
} DotxtPluginLoadReport;

void dotxt_load_plugins(const wchar_t* appRoot, DotxtPluginLoadReport* outReport);

#endif
