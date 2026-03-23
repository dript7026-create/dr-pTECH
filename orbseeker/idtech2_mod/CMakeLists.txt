cmake_minimum_required(VERSION 3.10)
project(OrbSeekerGame C)

# Placeholder CMake for building the Quake II `game` module.
# Edit `Q2_SDK_DIR` to point to your Quake II SDK root that provides headers
# (g_local.h, q_shared.h) and link libraries. This template produces a shared
# library named `game` (game.dll on Windows, game.so on Linux).

if(NOT DEFINED Q2_SDK_DIR)
    message(FATAL_ERROR "Please configure Q2_SDK_DIR to point to your Quake II SDK root")
endif()

set(SOURCES
    game/orbseeker_game.c
)

include_directories(${Q2_SDK_DIR}/include)

add_library(game SHARED ${SOURCES})

# You will need to link against the engine or provide the proper link libraries
# For Windows/MSVC you might set ENGINE_LIB and link it here. Example:
# target_link_libraries(game PRIVATE ${ENGINE_LIB})

set_target_properties(game PROPERTIES PREFIX "" )

message(STATUS "CMake configured. Edit Q2_SDK_DIR and link settings before building.")
