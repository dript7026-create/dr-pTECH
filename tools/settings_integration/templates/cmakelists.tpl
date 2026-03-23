cmake_minimum_required(VERSION 3.16)
project({project_name})

set(CMAKE_CXX_STANDARD 17)

# Libraries requested by settings
{libs}

add_executable({project_name} src/main.cpp)

target_include_directories({project_name} PRIVATE ${CMAKE_SOURCE_DIR}/include)
