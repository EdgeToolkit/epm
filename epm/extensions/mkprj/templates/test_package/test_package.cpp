{% set name = argument.name %}
{% set version = argument.version %}
{% set id = name.replace('-', '_') %}
#include <stdio.h>
#include <liba/liba.h>

int main(){
    printf("{{name}} %s\n", {{id}}_version());
    return 0;
}