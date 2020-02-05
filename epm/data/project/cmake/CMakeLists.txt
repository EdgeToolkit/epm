# Minimum CMake required
cmake_minimum_required(VERSION 3.1.3)

if({{ name }}_VERBOSE)
  message(STATUS "{{ name }} Configuring...")
endif()

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

# Project
project({{ name }})


# Options

option({{ name }}_CXX11_ENABLE "enable C++ 11 compile feature." {{ "ON" if cxx11 else "OFF" }})
option({{ name }}_MSVC_STATIC_RUNTIME "MSVC Link static runtime libraries." OFF)
if({{ name }}_CXX11_ENABLE)

    if (CYGWIN)
      set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=gnu++11")
    else()
      set(CMAKE_CXX_STANDARD 11)
      set(CMAKE_CXX_STANDARD_REQUIRED ON)
      set(CMAKE_CXX_EXTENSIONS OFF)
    endif()
endif({{ name }}_CXX11_ENABLE)

# In case we are building static libraries, link also the runtime library statically
# so that MSVCR*.DLL is not required at runtime.
# https://msdn.microsoft.com/en-us/library/2kzt1wy3.aspx
# This is achieved by replacing msvc option /MD with /MT and /MDd with /MTd
# http://www.cmake.org/Wiki/CMake_FAQ#How_can_I_build_my_MSVC_application_with_a_static_runtime.3F
if (MSVC AND {{ name }}_MSVC_STATIC_RUNTIME)
foreach(flag_var
    CMAKE_CXX_FLAGS CMAKE_CXX_FLAGS_DEBUG CMAKE_CXX_FLAGS_RELEASE
    CMAKE_CXX_FLAGS_MINSIZEREL CMAKE_CXX_FLAGS_RELWITHDEBINFO)
  if(${flag_var} MATCHES "/MD")
    string(REGEX REPLACE "/MD" "/MT" ${flag_var} "${${flag_var}}")
  endif(${flag_var} MATCHES "/MD")
endforeach(flag_var)
endif (MSVC AND {{ name }}_MSVC_STATIC_RUNTIME)


if (MSVC)
  # Build with multiple processes
  add_definitions(/MP)
  # MSVC warning suppressions
  add_definitions(
#    /wd4018 # 'expression' : signed/unsigned mismatch
#    /wd4065 # switch statement contains 'default' but no 'case' labels
#    /wd4146 # unary minus operator applied to unsigned type, result still unsigned
#    /wd4244 # 'conversion' conversion from 'type1' to 'type2', possible loss of data
#    /wd4251 # 'identifier' : class 'type' needs to have dll-interface to be used by clients of class 'type2'
#    /wd4267 # 'var' : conversion from 'size_t' to 'type', possible loss of data
#    /wd4305 # 'identifier' : truncation from 'type1' to 'type2'
#    /wd4307 # 'operator' : integral constant overflow
#    /wd4309 # 'conversion' : truncation of constant value
#    /wd4334 # 'operator' : result of 32-bit shift implicitly converted to 64 bits (was 64-bit shift intended?)
#    /wd4355 # 'this' : used in base member initializer list
#    /wd4506 # no definition for inline function 'function'
#    /wd4800 # 'type' : forcing value to bool 'true' or 'false' (performance warning)
#    /wd4996 # The compiler encountered a deprecated declaration.
  )

  # Suppress linker warnings about files with no symbols defined.
#  set(CMAKE_STATIC_LINKER_FLAGS /ignore:4221)

endif (MSVC)

get_filename_component(app_source_dir {{ '${%s_SOURCE_DIR} ' % name }} PATH)
include_directories(
  ${app_source_dir}/include
  ${app_source_dir}/source)

if (MSVC)
  # Add the "lib" prefix for generated .lib outputs.
  set(LIB_PREFIX lib)
else (MSVC)
  # When building with "make", "lib" prefix will be added automatically by
  # the build tool.
  set(LIB_PREFIX)
endif (MSVC)

##############################################################
#
# {{ name }} application
#
##############################################################
set(_SRC_PATTERN ${app_source_dir}/source/*.c
    ${app_source_dir}/source/*.h ${app_source_dir}/source/*.hpp
    ${app_source_dir}/source/*.cpp ${app_source_dir}/source/*.cc)
set(_HDR_PATTERN ${app_source_dir}/include/*.h ${app_source_dir}/include/*.hpp)

file(GLOB_RECURSE _app_SRCS  ${_SRC_PATTERN})
file(GLOB_RECURSE _app_HDRS  ${_HDR_PATTERN})
add_executable({{ name }}  ${_app_SRCS} ${_app_HDRS})
target_link_libraries({{ name }}  ${CONAN_LIBS} )

source_group(TREE ${app_source_dir} FILES ${_app_SRCS} ${_app_HDRS})


# Install configuration
set(_cmakedir_desc "Directory relative to CMAKE_INSTALL to install the cmake configuration files")
mark_as_advanced(CMAKE_INSTALL_CMAKEDIR)

# Install configuration
install(TARGETS {{ name }} EXPORT {{ name }}-targets
  RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR} COMPONENT {{ name }})



if({{ name }}_VERBOSE)
    message(STATUS "{{ name }} Configuring done")
endif()
