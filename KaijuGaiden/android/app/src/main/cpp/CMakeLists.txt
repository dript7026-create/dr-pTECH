cmake_minimum_required(VERSION 3.10)

project(KaijuGaidenAndroid C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

set(WORKSPACE_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../../../../")
set(KAIJU_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../../../")
set(SDL_ROOT "${WORKSPACE_ROOT}/skazka_terranova_c/third_party/SDL")

set(SDL_SHARED ON CACHE BOOL "" FORCE)
set(SDL_STATIC OFF CACHE BOOL "" FORCE)
set(SDL_TEST OFF CACHE BOOL "" FORCE)
set(SDL_TESTS OFF CACHE BOOL "" FORCE)
set(SDL_DISABLE_INSTALL ON CACHE BOOL "" FORCE)

add_subdirectory("${SDL_ROOT}" "${CMAKE_CURRENT_BINARY_DIR}/SDL-build")

add_library(main SHARED
    android_main.c
    "${KAIJU_ROOT}/kaijugaiden.c"
    "${WORKSPACE_ROOT}/egosphere/egosphere.c"
)

target_include_directories(main PRIVATE
    "${WORKSPACE_ROOT}"
    "${WORKSPACE_ROOT}/egosphere"
    "${SDL_ROOT}/include"
)

target_compile_definitions(main PRIVATE TARGET_HOST)

target_link_libraries(main PRIVATE SDL2::SDL2 m log android OpenSLES GLESv1_CM GLESv2)