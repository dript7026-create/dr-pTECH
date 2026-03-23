#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* This test harness includes the implementation directly for simplicity. 
   It is compiled with -DGENOME_ENABLED=1 to enable GA behavior. */
#include "userpersonalitytracking.c"

int main(void) {
    ProfileSystem *sys = init_profile_system();
    if (!sys) {
        fprintf(stderr, "Failed to init profile system\n");
        return 1;
    }

    UserProfile *p = create_user_profile("test_user");
    if (!p) {
        fprintf(stderr, "Failed to create profile\n");
        cleanup_profile_system(sys);
        return 1;
    }

    /* place created profile into the system for cleanup convenience (shallow copy) */
    if (sys->profile_count < MAX_USERS) {
        sys->profiles[sys->profile_count] = *p; /* copy struct; interactions pointer kept */
        sys->profile_count++;
        free(p); /* free temporary allocation, interactions remain owned by system->profiles */
    }

    /* simulate interactions over the last 20 minutes */
    time_t now = time(NULL);
    for (int i = 0; i < 12; i++) {
        char buf[200];
        snprintf(buf, sizeof(buf), "simulated message %d", i);
        int response_time = 200 + (i * 50);
        float sentiment = 0.2f + (0.06f * i);
        log_interaction(&sys->profiles[0], buf, response_time, sentiment);
        /* stagger timestamps backward (so some fall within 30 minutes) */
        sys->profiles[0].interactions[sys->profiles[0].interaction_count - 1].timestamp = now - (i * 60);
    }

    /* set a target satisfaction score to guide GA */
    sys->profiles[0].satisfaction_score = 0.75f;

    printf("Before evolve:\n");
    print_profile_summary(&sys->profiles[0]);

    /* evolve and attach genome (flash-profile window: 30 minutes) */
    evolve_and_attach_genome(&sys->profiles[0], 30);

    float eval = evaluate_profile_genome(&sys->profiles[0]);
    printf("Evaluated genome output: %.4f\n", eval);

    printf("After evolve:\n");
    print_profile_summary(&sys->profiles[0]);

    cleanup_profile_system(sys);
    return 0;
}
