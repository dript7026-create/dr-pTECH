cmake_minimum_required(VERSION 3.10)
project(BangoEngineTarget C)

set(CMAKE_C_STANDARD 99)

add_library(bango_engine_target STATIC
    src/bango_engine_target.c
    src/bango_telemetry_bridge_stub.c
)

target_include_directories(bango_engine_target PUBLIC include)
