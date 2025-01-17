add_executable(example example.c)
target_link_libraries(example PRIVATE mylib)

# 设置可执行文件的 RPATH，确保运行时可以找到共享库
message(STATUS "CMAKE_SOURCE_DIR = ${CMAKE_SOURCE_DIR}")
set_target_properties(example PROPERTIES
    INSTALL_RPATH ${CMAKE_SOURCE_DIR}/library
    BUILD_WITH_INSTALL_RPATH TRUE
)
