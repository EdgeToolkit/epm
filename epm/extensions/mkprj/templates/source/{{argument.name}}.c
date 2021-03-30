{% set name = argument.name %}
{% set version = argument.version %}
{% set id = name.replace('-', '_') %}
{% set ID = name.upper() %}
#include <{{name}}/{{name}}.h>

{{ID}}_C_EXPORT const char* {{id}}_version()
{
    return "{{version}}";
}
