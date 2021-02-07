{% set name = argument.name %}
{% set version = argument.version %}
{% set id = name.replace('-', '_') %}
{% set ID = name.upper() %}
import os
from conans import ConanFile, CMake
from epm.tools.conan import as_program
ConanFile = as_program(ConanFile)

class Program{{id|capitalize}}Conan(ConanFile):
    settings = "os", "compiler", "arch", "build_type"
    generators = "cmake", "pkg_config"


    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

