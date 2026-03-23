cmake_minimum_required(VERSION 3.10)
project(kaijugaiden_idtech2_port C)

find_package(SDL2 REQUIRED)
find_package(PNG REQUIRED)

include_directories(${SDL2_INCLUDE_DIRS} ${PNG_INCLUDE_DIRS})
add_executable(kaijugaiden_demo main_demo.c sprite_renderer.c)
target_link_libraries(kaijugaiden_demo ${SDL2_LIBRARIES} ${PNG_LIBRARIES} SDL2_image)
