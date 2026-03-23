#include "blastmonidz_bridge.h"

#include <stdio.h>
#include <string.h>

#ifdef _WIN32
#include <windows.h>
#endif

int main(void) {
    FILE *handle;
    const char *message = "workflow: bridge smoke validation";

    blastmonidz_bridge_init();

    handle = fopen(blastmonidz_bridge_inbox_path(), "w");
    if (!handle) {
        fprintf(stderr, "failed to open inbox path: %s\n", blastmonidz_bridge_inbox_path());
        blastmonidz_bridge_shutdown();
        return 1;
    }
    fprintf(handle, "%s\n", message);
    fclose(handle);

#ifdef _WIN32
    Sleep(600);
#endif
    blastmonidz_bridge_poll();

    if (strstr(blastmonidz_bridge_latest_inbox(), message) == NULL) {
        fprintf(stderr, "bridge inbox was not updated: %s\n", blastmonidz_bridge_latest_inbox());
        blastmonidz_bridge_shutdown();
        return 2;
    }

    printf("bridge ok\n");
    printf("status=%s\n", blastmonidz_bridge_latest_status());
    printf("inbox=%s\n", blastmonidz_bridge_latest_inbox());
    printf("outbox=%s\n", blastmonidz_bridge_outbox_path());

    blastmonidz_bridge_shutdown();
    return 0;
}