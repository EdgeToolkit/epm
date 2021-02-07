{% set name = argument.name %}
{% set version = argument.version %}
{% set id = name.replace('-', '_') %}
{% set ID = name.upper() %}
option({CXX11_ENABLE "enable C++ 11 compile feature." OFF)
if(CXX11_ENABLE)
    if (CYGWIN)
      set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=gnu++11")
    else()
      set(CMAKE_CXX_STANDARD 11)
      set(CMAKE_CXX_STANDARD_REQUIRED ON)
      set(CMAKE_CXX_EXTENSIONS OFF)
    endif()
endif()

set({{ID}}_DEBUG_POSTFIX "" CACHE STRING "Default debug postfix")
mark_as_advanced({{ID}}_DEBUG_POSTFIX)

{% if type == 'lib' %}
if (BUILD_SHARED_LIBS)
  set({{ID}}_BUILD_SHARED_LIBS_DEFAULT ON)
else (BUILD_SHARED_LIBS)
  set({{ID}}_BUILD_SHARED_LIBS_DEFAULT OFF)
endif()

option({{ID}}_BUILD_SHARED_LIBS "Build Shared Libraries" ${ {{ID}}_BUILD_SHARED_LIBS_DEFAULT })

if ({{ID}}_BUILD_SHARED_LIBS)
  set({{ID}}_SHARED_OR_STATIC "SHARED")
else ({{ID}}_BUILD_SHARED_LIBS)
  set({{ID}}_SHARED_OR_STATIC "STATIC")
  # In case we are building static libraries, link also the runtime library statically
  # so that MSVCR*.DLL is not required at runtime.
  # https://msdn.microsoft.com/en-us/library/2kzt1wy3.aspx
  # This is achieved by replacing msvc option /MD with /MT and /MDd with /MTd
  # http://www.cmake.org/Wiki/CMake_FAQ#How_can_I_build_my_MSVC_application_with_a_static_runtime.3F
  if (MSVC AND {{ID}}_MSVC_STATIC_RUNTIME)
    foreach(flag_var
        CMAKE_CXX_FLAGS CMAKE_CXX_FLAGS_DEBUG CMAKE_CXX_FLAGS_RELEASE
        CMAKE_CXX_FLAGS_MINSIZEREL CMAKE_CXX_FLAGS_RELWITHDEBINFO)
      if(${flag_var} MATCHES "/MD")
        string(REGEX REPLACE "/MD" "/MT" ${flag_var} "${${flag_var}}")
      endif(${flag_var} MATCHES "/MD")
    endforeach(flag_var)
  endif (MSVC AND {{ID}}_MSVC_STATIC_RUNTIME)
endif ()

{% endif %}