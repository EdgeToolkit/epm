cmake_minimum_required(VERSION 3.0)
project(test_package)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

add_executable(test_liba test_package.cpp)
target_link_libraries(test_liba ${CONAN_LIBS})
#set_target_properties(test_zlib PROPERTIES OUTPUT_NAME "test")
