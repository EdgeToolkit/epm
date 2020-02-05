cmake_minimum_required(VERSION 3.1.2)
project({{ name }}_test CXX)

set(CMAKE_VERBOSE_MAKEFILE TRUE)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()


find_package(GTest REQUIRED)
if (NOT GTEST_FOUND)
    message(FATAL_ERROR "Could not find GTest")
endif()

if(WITH_GMOCK)
    find_package(GMock REQUIRED)
    if (NOT GMOCK_FOUND)
        message(FATAL_ERROR "Could not find GMock")
    endif()
endif()

if(MSVC)
  set(CMAKE_EXE_LINKER_FLAGS /ignore:4099)
endif()

#get_filename_component(test_source_dir {{ '${%s_TEST_SOURCE_DIR} ' % name }} PATH)
set(test_source_dir ${CMAKE_CURRENT_SOURCE_DIR})
include_directories( ${test_source_dir}/src )

set(_SRC_PATTERN ${test_source_dir}/src/*.c
    ${test_source_dir}/src/*.h ${test_source_dir}/src/*.hpp
    ${test_source_dir}/src/*.cpp ${test_source_dir}/src/*.cc)

file(GLOB_RECURSE _test_SRCS  ${_SRC_PATTERN})

source_group(TREE ${test_source_dir} FILES ${_test_SRCS} )

if(WITH_MAIN)
    add_executable(${PROJECT_NAME} ${_test_SRCS})
else()
    add_executable(${PROJECT_NAME} main.cpp ${_test_SRCS})
endif()


target_link_libraries(${PROJECT_NAME} ${CONAN_LIBS} {{ name}})
set_property(TARGET ${PROJECT_NAME} PROPERTY CXX_STANDARD 11)
if(WITH_GMOCK)
    target_compile_definitions(${PROJECT_NAME} PRIVATE WITH_GMOCK)
endif()
