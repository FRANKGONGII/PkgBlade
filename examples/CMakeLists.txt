cmake_minimum_required(VERSION 3.10)

# 项目名称
project(LinkExample)
set(CMAKE_C_COMPILER gcc)

add_subdirectory(link_1_mylib)
add_subdirectory(library)

