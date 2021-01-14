{% set name = argument.name %}
{% set version = argument.version %}
{% set id = name.replace('-', '_') %}
{% set ID = name.upper() %}
#ifndef _{{ID}}_LIBRARY__HEADER_H_
#define _{{ID}}_LIBRARY__HEADER_H_
#include "declare.h"

{{ID}}_C_API const char* {{id}}_version();

#endif //!_{{ID}}_LIBRARY__HEADER_H_