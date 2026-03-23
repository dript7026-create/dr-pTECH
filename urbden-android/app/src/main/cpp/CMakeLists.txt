cmake_minimum_required(VERSION 3.10)
project(native-lib)

add_library(native-lib SHARED
            native-lib.c
            generator.c
            world.c
            npc.c
            economy.c
            seed_asm.S)

find_library(log-lib log)

target_link_libraries(native-lib
                      ${log-lib})
