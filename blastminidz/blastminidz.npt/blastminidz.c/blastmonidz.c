#include "blastmonidz.h"
#include "blastmonidz_bridge.h"
#include "blastmonidz_window.h"

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#ifdef _WIN32
#include <windows.h>
#endif

static void clear_screen(void) {
    printf("\033[2J\033[H");
}

static int read_console_line(char *buffer, size_t size) {
#ifdef _WIN32
    HANDLE stdin_handle = GetStdHandle(STD_INPUT_HANDLE);
    if (stdin_handle != INVALID_HANDLE_VALUE && stdin_handle != NULL) {
        for (;;) {
            DWORD wait_result = WaitForSingleObject(stdin_handle, 16);
            blastmonidz_bridge_poll();
            blastmonidz_window_pump();
            if (wait_result == WAIT_OBJECT_0) {
                break;
            }
            if (wait_result == WAIT_FAILED) {
                break;
            }
        }
    }
#endif
    if (!fgets(buffer, (int)size, stdin)) {
        clearerr(stdin);
        return 0;
    }
    return 1;
}

static void wait_for_enter(const char *prompt) {
    char buffer[32];
    printf("%s", prompt);
    read_console_line(buffer, sizeof(buffer));
}

static void print_archive_catalog(void) {
    int i;
    blastmonidz_bridge_publish_status("menu", "Archive catalog opened.");
    blastmonidz_window_present_archive();
    clear_screen();
    printf("=== BLASTMONIDZ ARCHIVE CATALOG ===\n\n");
    printf("Bomberman.zip is treated here as an ancestry archive, not as final content.\n");
    printf("Each legacy asset is remapped into BlastKin / Blastmonidz nomenclature and runtime roles.\n\n");
    printf("Live bridge inbox:  %s\n", blastmonidz_bridge_inbox_path());
    printf("Live bridge outbox: %s\n\n", blastmonidz_bridge_outbox_path());
    for (i = 0; i < MAX_ARCHIVE_ITEMS; ++i) {
        printf("[%02d] %s\n", i + 1, blastmonidz_archive_map[i].blastmonidz_id);
        printf("     source: %s\n", blastmonidz_archive_map[i].archive_entry);
        printf("     role:   %s\n", blastmonidz_archive_map[i].role);
        printf("     note:   %s\n\n", blastmonidz_archive_map[i].notes);
    }
    wait_for_enter("Press Enter to return to the title menu...");
}

static void print_lore_brief(void) {
    blastmonidz_bridge_publish_status("menu", "World brief opened.");
    blastmonidz_window_present_lore();
    clear_screen();
    printf("=== BLASTMONIDZ SETTING BRIEF ===\n\n");
    printf("BlastKin are sentient AI entities living inside a collective consciousness stream.\n");
    printf("ArtiSapiens are persistent synthetic rivals occupying the same data-spectrum.\n");
    printf("All genomes resonate through a 13-tier / 198-class adaptive hierarchy.\n");
    printf("Bomb Gems are electromineral obstacles whose chemistry mutates the arena and each Blastmonid.\n");
    printf("Consensus time runs through a 10x optical registration buffer; damage pushes a combatant behind that timeline.\n");
    printf("Each fighter also carries a decentralized self-communication feed tracking inner signal, world attunement, rival pressure, and ghost noise.\n");
    printf("If a Blastmonid falls, it slips into a ghost timeline, then manifests back when chemistry aligns.\n\n");
    printf("Side note: Blastminidz is the handheld spinoff line. In-world, those devices raise micro-cellular descendants\n");
    printf("of the arena Blastmonidz for wireless eco-chemical turf conflicts. This codebase implements the mainline\n");
    printf("Blastmonidz vertical slice and keeps Blastminidz as in-world lore rather than replacing it.\n\n");
    printf("Bridge status: %s\n\n", blastmonidz_bridge_latest_status());
    wait_for_enter("Press Enter to return to the title menu...");
}

static int show_title_menu(void) {
    char buffer[32];
    const AssetArchetype *logo_asset = blastmonidz_title_logo_asset();
    const AssetArchetype *backdrop_asset = blastmonidz_title_backdrop_asset();
    const AssetArchetype *motion_asset = blastmonidz_primary_motion_asset();
    for (;;) {
        blastmonidz_bridge_publish_status("menu", "Title menu idle and ready.");
        blastmonidz_window_present_title();
        clear_screen();
        printf("============================================================\n");
        printf("                    B L A S T M O N I D Z                   \n");
        printf("============================================================\n\n");
        printf("Blastmonidz: Consensus Arena Vertical Slice\n");
        printf("Archive-backed host build: Bomberman.zip now detonates as a maximized full-screen title wall with animated bomb cycles, rotating silhouette families, adaptive paint fields, and reactive arena props\n");
        printf("Priority title sources: %s, %s, %s\n", logo_asset->archive_entry, backdrop_asset->archive_entry, motion_asset->archive_entry);
        printf("Lore note: Blastminidz remains the handheld spinoff line inside the fiction.\n");
        printf("Deliverable scope: full match loop, save output, archive browser, and Windows companion render.\n\n");
        printf("Bridge status: %s\n", blastmonidz_bridge_latest_status());
        printf("Latest inbox:  %s\n", blastmonidz_bridge_latest_inbox());
        printf("Workflow files: %s | %s\n\n", blastmonidz_bridge_inbox_path(), blastmonidz_bridge_outbox_path());
        printf("1. Start arena run\n");
        printf("2. View world brief\n");
        printf("3. View archive catalog\n");
        printf("4. Quit\n\n");
        printf("Select: ");
        if (!read_console_line(buffer, sizeof(buffer))) {
            return 4;
        }
        if (buffer[0] == '1') {
            return 1;
        }
        if (buffer[0] == '2') {
            print_lore_brief();
        } else if (buffer[0] == '3') {
            print_archive_catalog();
        } else if (buffer[0] == '4') {
            return 4;
        }
    }
}

static void print_starter_draw(const GameState *state) {
    int i;
    blastmonidz_bridge_publish_status("run", "Starter draw revealed.");
    blastmonidz_window_present_starter_draw(state);
    clear_screen();
    printf("=== STARTER TOKEN DRAW ===\n\n");
    for (i = 0; i < MAX_PLAYERS; ++i) {
        const BlastKin *player = &state->players[i];
        printf("%s draws %s [%s] | doctrine=%s | base hp=%d | freq=%d | growth family=%s\n",
            player->name,
            player->mon.starter->name,
            player->is_human ? "Human BlastKin" : "ArtiSapien",
            blastmonidz_doctrine_name(player->doctrine),
            player->mon.max_health,
            player->mon.starter->base_frequency,
            player->mon.starter->growth_family);
    }
    printf("\n");
    wait_for_enter("Press Enter to launch the consensus arena...");
}

static void render_arena(const GameState *state) {
    ArenaView view = blastmonidz_calculate_view(state);
    const BlastmonidzHomeTile *focus_tile = blastmonidz_select_home_tile(state, state->players[0].mon.x, state->players[0].mon.y);
    char focus_tile_effects[192];
    char asset_genome[256];
    int y;
    int x;

    blastmonidz_describe_home_tile(focus_tile, focus_tile_effects, (int)sizeof(focus_tile_effects));
    blastmonidz_describe_genome_profile(&state->visuals.asset_genome, asset_genome, (int)sizeof(asset_genome));

    blastmonidz_window_present_arena(state);
    clear_screen();
    printf("BLASTMONIDZ | round %d | consensus tick %d | optical buffer %dx\n",
        state->round_index,
        state->consensus_tick,
        state->optical_buffer);
    printf("camera window: %dx%d tiles inside an arena scaled to %dx%d tiles\n",
        view.width,
        view.height,
        state->arena.width,
        state->arena.height);
    printf("chemistry: ion=%d spore=%d brine=%d | mineral pressure=%d | gems=%d\n\n",
        state->arena.chemistry[0],
        state->arena.chemistry[1],
        state->arena.chemistry[2],
        state->arena.mineral_pressure,
        blastmonidz_count_active_gems(&state->arena));
    printf("self-communication phase: %s | inner=%d world=%d rival=%d ghost=%d balance=%d\n\n",
        blastmonidz_world_phase_name(state),
        state->world_feed.inner_signal,
        state->world_feed.world_signal,
        state->world_feed.rival_signal,
        state->world_feed.ghost_signal,
        state->world_feed.balance);
    printf("focus home tile: %s [%c] | %s\n\n",
        focus_tile->name,
        focus_tile->glyph,
        focus_tile->theory_role);
    printf("tile effects: %s\n\n", focus_tile_effects);
    printf("asset genome: %s\n\n", asset_genome);
    printf("Bridge: %s\n", blastmonidz_bridge_latest_status());
    printf("Inbox:  %s\n\n", blastmonidz_bridge_latest_inbox());

    for (y = view.top; y < view.top + view.height; ++y) {
        for (x = view.left; x < view.left + view.width; ++x) {
            int player_id = blastmonidz_player_at(state, x, y);
            int bomb_id = blastmonidz_bomb_at(&state->arena, x, y);
            int gem_id = blastmonidz_gem_at(&state->arena, x, y);
            const BlastmonidzHomeTile *home_tile = blastmonidz_select_home_tile(state, x, y);
            if (player_id >= 0) {
                printf("%d", player_id + 1);
            } else if (bomb_id >= 0) {
                printf("o");
            } else if (gem_id >= 0) {
                printf("%c", state->arena.gems[gem_id].glyph);
            } else if (state->arena.tiles[y * state->arena.width + x] == TILE_WALL) {
                printf("#");
            } else if (state->arena.tiles[y * state->arena.width + x] == TILE_CRATE) {
                printf("+");
            } else {
                printf("%c", home_tile->glyph);
            }
        }
        printf("\n");
    }
    printf("\n");
    for (x = 0; x < MAX_PLAYERS; ++x) {
        const BlastKin *player = &state->players[x];
        char genome_line[256];
        blastmonidz_describe_genome_profile(&player->mon.cosmetic_genome, genome_line, (int)sizeof(genome_line));
        printf("%d:%s | doctrine=%s | wins=%d | hp=%d/%d | lag=%d | form=%s | concoction=%s | feed %d/%d/%d/%d/%d | ai=%s | %s | %s\n",
            x + 1,
            player->name,
            blastmonidz_doctrine_name(player->doctrine),
            player->run_wins,
            player->mon.health,
            player->mon.max_health,
            player->mon.delay_ticks,
            blastmonidz_growth_title(player->mon.growth_stage),
            blastmonidz_concoctions[player->mon.concoction_id],
                player->mon.self_feed.inner_signal,
                player->mon.self_feed.world_signal,
                player->mon.self_feed.rival_signal,
                player->mon.self_feed.ghost_signal,
                player->mon.self_feed.balance,
                    player->ai_debug_line,
                    player->mon.alive ? "active" : "ghost",
                    genome_line);
    }
    printf("\nLatest events:\n");
    for (x = 0; x < MAX_LOG_LINES; ++x) {
        if (state->log_lines[x][0] != '\0') {
            printf("- %s\n", state->log_lines[x]);
        }
    }
    printf("\nHome tile key: ");
    for (x = 0; x < BLASTMONIDZ_HOME_TILES; ++x) {
        printf("%c=%s%s",
            blastmonidz_home_tiles[x].glyph,
            blastmonidz_home_tiles[x].name,
            x == BLASTMONIDZ_HOME_TILES - 1 ? "" : " | ");
    }
    printf("\nControls: w/a/s/d move, b bomb, c cycle concoction, r manifest if ghost-ready, t wait, q quit run\n");
}

static int handle_human_turn(GameState *state) {
    char buffer[32];
    Blastonid *mon = &state->players[0].mon;
    if (!mon->alive) {
        printf("Ghost state. Press r to manifest when chemistry is aligned, or t to wait: ");
    } else if (mon->delay_ticks > 0) {
        printf("Consensus lag holds you for %d more ticks. Press t to continue: ", mon->delay_ticks);
    } else {
        printf("Command: ");
    }
    if (!read_console_line(buffer, sizeof(buffer))) {
        return 0;
    }
    return blastmonidz_handle_player_command(state, 0, (char)tolower((unsigned char)buffer[0]));
}

static int run_round(GameState *state) {
    int round_winner = -1;
    blastmonidz_begin_round(state);
    blastmonidz_bridge_publish_status("run", "Round started.");
    for (;;) {
        render_arena(state);
        if (!handle_human_turn(state)) {
            return 0;
        }
        blastmonidz_run_bot_turns(state);
        blastmonidz_advance_world(state);
        round_winner = blastmonidz_determine_round_winner(state);
        if (round_winner >= 0) {
            blastmonidz_announce_round_winner(state, round_winner);
            blastmonidz_bridge_publish_status("run", state->players[round_winner].name);
            render_arena(state);
            wait_for_enter("\nRound resolved. Press Enter to continue... ");
            return 1;
        }
    }
}

static void print_run_summary(const GameState *state) {
    int i;
    char asset_genome[256];
    blastmonidz_bridge_publish_status("run", "Run complete.");
    blastmonidz_window_present_summary(state);
    clear_screen();
    printf("=== RUN COMPLETE ===\n\n");
    blastmonidz_describe_genome_profile(&state->visuals.asset_genome, asset_genome, (int)sizeof(asset_genome));
    printf("Winner: %s\n", state->players[state->winner_id].name);
    printf("Rounds played: %d\n", state->round_index);
    printf("Consensus ticks accumulated: %d\n", state->consensus_tick);
    printf("World phase: %s\n", blastmonidz_world_phase_name(state));
    printf("Blastmonidz asset genome: %s\n", asset_genome);
    printf("Whole-self feed: inner=%d world=%d rival=%d ghost=%d balance=%d\n", state->world_feed.inner_signal, state->world_feed.world_signal, state->world_feed.rival_signal, state->world_feed.ghost_signal, state->world_feed.balance);
    printf("Profiles saved to %s and %s\n\n", blastmonidz_run_profile_path, blastmonidz_replay_summary_path);
    printf("Workflow bridge inbox:  %s\n", blastmonidz_bridge_inbox_path());
    printf("Workflow bridge outbox: %s\n", blastmonidz_bridge_outbox_path());
    printf("Latest inbox: %s\n\n", blastmonidz_bridge_latest_inbox());
    for (i = 0; i < MAX_PLAYERS; ++i) {
        const BlastKin *player = &state->players[i];
        char genome_line[256];
        blastmonidz_describe_genome_profile(&player->mon.cosmetic_genome, genome_line, (int)sizeof(genome_line));
        printf("%s | doctrine=%s | wins=%d | starter=%s | final form=%s | gems=%d | kills=%d | feed=%d/%d/%d/%d/%d | ai=%s | %s\n",
            player->name,
            blastmonidz_doctrine_name(player->doctrine),
            player->run_wins,
            player->mon.starter->name,
            blastmonidz_growth_title(player->mon.growth_stage),
            player->mon.gems_cleared,
            player->mon.round_kills,
            player->mon.self_feed.inner_signal,
            player->mon.self_feed.world_signal,
            player->mon.self_feed.rival_signal,
            player->mon.self_feed.ghost_signal,
            player->mon.self_feed.balance,
            player->ai_debug_line,
            genome_line);
    }
    printf("\nThis deliverable implements the complete vertical-slice loop: title, lore brief, archive catalog, starter draw,\n");
    printf("seeded procedural archive rendering, chemistry-driven growth, consensus lag, ghost-line re-entry, self-communication world feed, and first-to-3 progression,\n");
    printf("and saved run profile output. Campaign expansion and network play are intentionally outside this release scope.\n\n");
    wait_for_enter("Press Enter to exit...");
}

static void run_game(void) {
    GameState state;
    int keep_running = 1;

    blastmonidz_init_game(&state);
    print_starter_draw(&state);
    while (keep_running) {
        int winner_id;
        if (!run_round(&state)) {
            break;
        }
        winner_id = blastmonidz_check_run_winner(&state);
        if (winner_id >= 0) {
            state.winner_id = winner_id;
            keep_running = 0;
        } else {
            ++state.round_index;
        }
    }
    if (!keep_running && state.players[state.winner_id].run_wins >= TARGET_RUN_WINS) {
        blastmonidz_save_run_profile(&state);
        print_run_summary(&state);
    }
    blastmonidz_free_arena(&state.arena);
}

int main(void) {
    srand((unsigned int)time(NULL));
    blastmonidz_bridge_init();
    if (!blastmonidz_window_init()) {
        fprintf(stderr, "Failed to initialize the Blastmonidz companion window.\n");
    }
    for (;;) {
        int selection = show_title_menu();
        blastmonidz_bridge_poll();
        blastmonidz_window_pump();
        if (selection == 1) {
            run_game();
        } else if (selection == 4) {
            break;
        }
    }
    blastmonidz_window_shutdown();
    blastmonidz_bridge_shutdown();
    return 0;
}
