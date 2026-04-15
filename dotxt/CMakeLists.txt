cmake_minimum_required(VERSION 3.20)
project(dotxt C)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

add_executable(dotxt WIN32
    src/main.c
    src/file_io.c
    src/plugin_loader.c
)

target_include_directories(dotxt PRIVATE include)

target_link_libraries(dotxt PRIVATE
    comctl32
    comdlg32
)
