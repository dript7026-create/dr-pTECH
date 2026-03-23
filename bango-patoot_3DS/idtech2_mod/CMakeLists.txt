cmake_minimum_required(VERSION 3.10)
project(BangoPatootGame C)

if(NOT DEFINED Q2_SDK_DIR)
    message(FATAL_ERROR "Please configure Q2_SDK_DIR to point to your Quake II SDK root")
endif()

if(NOT EXISTS "${Q2_SDK_DIR}/game/g_local.h")
    message(FATAL_ERROR "Q2_SDK_DIR does not appear valid: ${Q2_SDK_DIR}/game/g_local.h not found")
endif()

add_library(game SHARED
    game/bango_game.c
    generated/bango_asset_bootstrap.c
    ../bango_engine_target/src/bango_engine_target.c
    ../bango_engine_target/src/bango_telemetry_bridge_stub.c
)

set_target_properties(game PROPERTIES
    C_STANDARD 90
    C_STANDARD_REQUIRED ON
    C_EXTENSIONS ON
)

if(MINGW)
    target_link_options(game PRIVATE "-Wl,--allow-shlib-undefined")
endif()

target_include_directories(game PRIVATE
    ${Q2_SDK_DIR}/game
    generated
    ../bango_engine_target/include
    ../../drIpTECH_idTech2Plug-Ins/include
)

if(WIN32 OR MINGW)
    target_compile_definitions(game PRIVATE _CRT_SECURE_NO_WARNINGS)
    set_target_properties(game PROPERTIES OUTPUT_NAME "gamex86")
endif()

set_target_properties(game PROPERTIES PREFIX "")
