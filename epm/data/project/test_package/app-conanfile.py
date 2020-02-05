#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import yaml
from conans import ConanFile, CMake, tools

class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"

    def requirements(self):
        pass

    def build(self):
        pass
        
    def test(self):
        pass