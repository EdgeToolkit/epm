{% set name = argument.name %}
{% set version = argument.version %}
{% set type = argument.type %}
{% set id = name.replace('-', '_') %}
{% set ID = name.upper() %}
# ---------------------------------------------------------
# Global cmake configuration
# ---------------------------------------------------------
cmake_minimum_required(VERSION 3.10)
# CMake policies
cmake_policy(SET CMP0022 NEW)
# On MacOS use @rpath/ for target's install name prefix path
if (POLICY CMP0042)
  cmake_policy(SET CMP0042 NEW)
endif ()
# Clear VERSION variables when no VERSION is given to project()
if(POLICY CMP0048)
  cmake_policy(SET CMP0048 NEW)
endif()

# ---------------------------------------------------------
# Project {{name}} configuration
# ---------------------------------------------------------
project({{name}})

# ---------------------------------------------------------
# Conan build info setup
# ---------------------------------------------------------
include("${CMAKE_BINARY_DIR}/conanbuildinfo.cmake")
conan_basic_setup()


include_directories( source)

set(_include_dir ${CMAKE_HOME_DIRECTORY}/include)
set(_source_dir ${CMAKE_HOME_DIRECTORY}/source)
set(_SRCs)
foreach(i "*.c" "*.cpp" "*.cxx")
  file(GLOB_RECURSE l "${_source_dir}/${i}")  
  list(APPEND _SRCs ${l})
endforeach()

set(_HDRs)
foreach(i "*.h" "*.hpp" "*.hxx")
  file(GLOB_RECURSE l "${_include_dir}/${i}")  
  list(APPEND _HDRs ${l})
endforeach()

include_directories(${_source_dir} ${_include_dir})

{% if type == 'lib' %}
add_library({{name}}  ${_SRCs} ${_HDRs})
if(BUILD_SHARED_LIBS)
  if(MSVC)
    target_compile_definitions({{name}}
    PUBLIC  {{ID}}_USE_DLLS
    PRIVATE {{ID}}_EXPORTS)
  endif()
endif()

# Install configuration
set(_cmakedir_desc "Directory relative to CMAKE_INSTALL to install the cmake configuration files")
if(NOT MSVC)
  set(CMAKE_INSTALL_CMAKEDIR "${CMAKE_INSTALL_LIBDIR}/cmake/{{name}}" CACHE STRING "${_cmakedir_desc}")
else()
  set(CMAKE_INSTALL_CMAKEDIR "cmake" CACHE STRING "${_cmakedir_desc}")
endif()
mark_as_advanced(CMAKE_INSTALL_CMAKEDIR)

# Install configuration
set(_cmakedir_desc "Directory relative to CMAKE_INSTALL to install the cmake configuration files")
configure_file(cmake/{{name}}-config.cmake.in
               ${CMAKE_INSTALL_CMAKEDIR}/{{name}}-config.cmake @ONLY)
export(TARGETS  {{name}}
      NAMESPACE  {{name}}::
      FILE ${CMAKE_INSTALL_CMAKEDIR}/{{name}}-targets.cmake )

install(EXPORT {{name}}-targets
    DESTINATION "${CMAKE_INSTALL_CMAKEDIR}"
    NAMESPACE  {{name}}::
    COMPONENT  {{name}}-export)

install(DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/${CMAKE_INSTALL_CMAKEDIR}/
      DESTINATION "${CMAKE_INSTALL_CMAKEDIR}"
      COMPONENT  {{name}}-export
      PATTERN  {{name}}-targets.cmake EXCLUDE )

install(DIRECTORY ${_include_dir}/
        DESTINATION  include
        FILES_MATCHING PATTERN "*.h")

install(TARGETS {{name}} EXPORT {{name}}-targets
        RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR} COMPONENT {{name}}
        LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR} COMPONENT {{name}}
        ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR} COMPONENT {{name}})

{% else %}
add_executable({{name}} ${_SRCs})
target_link_libraries({{name}} ${CONAN_LIBS})

install(TARGETS {{name}}
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION bin
    ARCHIVE DESTINATION lib)
{% endif %}

source_group(TREE  ${CMAKE_HOME_DIRECTORY} FILES ${_SRCS} ${_HDRS})