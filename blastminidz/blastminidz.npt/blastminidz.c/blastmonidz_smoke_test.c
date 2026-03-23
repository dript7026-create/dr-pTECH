#include "blastmonidz.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

static void assert_feed_range(const BlastmonidzSelfFeed *feed) {
    assert(feed->inner_signal >= 0 && feed->inner_signal <= 100);
    assert(feed->world_signal >= 0 && feed->world_signal <= 100);
    assert(feed->rival_signal >= 0 && feed->rival_signal <= 100);
    assert(feed->ghost_signal >= 0 && feed->ghost_signal <= 100);
    assert(feed->balance >= 0 && feed->balance <= 100);
}

int main(void) {
    GameState state;
    const BlastmonidzHomeTile *tile;
    char tile_desc[192];
    char genome_desc[256];
    FILE *profile;
    FILE *replay;
    int i;

    srand(1337);
    blastmonidz_init_game(&state);

    assert(state.round_index == 1);
    assert(state.consensus_tick == 0);
    assert(state.visuals.run_seed != 0);
    assert(blastmonidz_visual_theme_name(&state)[0] != '\0');
    assert(blastmonidz_world_phase_name(&state)[0] != '\0');
    tile = blastmonidz_select_home_tile(&state, state.players[0].mon.x, state.players[0].mon.y);
    assert(tile != NULL);
    blastmonidz_describe_home_tile(tile, tile_desc, (int)sizeof(tile_desc));
    assert(tile_desc[0] != '\0');
    blastmonidz_describe_genome_profile(&state.players[0].mon.cosmetic_genome, genome_desc, (int)sizeof(genome_desc));
    assert(genome_desc[0] != '\0');
    assert(state.players[0].mon.cosmetic_genome.generation_passes == BLASTMONIDZ_GENOME_PASSES);
    assert(state.visuals.asset_genome.generation_passes == BLASTMONIDZ_GENOME_PASSES);
    assert_feed_range(&state.world_feed);

    assert(blastmonidz_handle_player_command(&state, 0, 'd') == 1);
    assert(blastmonidz_handle_player_command(&state, 0, 'c') == 1);
    assert(blastmonidz_handle_player_command(&state, 0, 'b') == 1);

    for (i = 0; i < 6; ++i) {
        blastmonidz_run_bot_turns(&state);
        blastmonidz_advance_world(&state);
        assert(state.consensus_tick == i + 1);
        assert_feed_range(&state.world_feed);
    }

    for (i = 0; i < MAX_PLAYERS; ++i) {
        assert_feed_range(&state.players[i].mon.self_feed);
    }

    state.players[0].run_wins = TARGET_RUN_WINS;
    state.winner_id = 0;
    blastmonidz_save_run_profile(&state);

    profile = fopen(blastmonidz_run_profile_path, "r");
    assert(profile != NULL);
    fclose(profile);
    replay = fopen(blastmonidz_replay_summary_path, "r");
    assert(replay != NULL);
    fclose(replay);

    blastmonidz_free_arena(&state.arena);
    printf("blastmonidz smoke test passed\n");
    return 0;
}