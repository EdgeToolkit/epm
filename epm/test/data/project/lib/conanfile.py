#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import glob
import shutil
import yaml

from conans import ConanFile, CMake, tools
from epm.tool.conan import ConanMeta

class Lib1Conan(ConanFile):
    _meta = ConanMeta()
    name = _meta.name
    version = _meta.version
    url = _meta.url
    description = _meta.description
    license = _meta.license
    author = _meta.author
    homepage = _meta.homepage
    topics = _meta.topics

    exports = ["package.yml", "conanfile.py"]
    exports_sources = ["CMakeLists.txt", "test_pacakge/*",
                       "include/*", "source/*", "cmake/*"]
    generators = "cmake"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False],
               "fPIC": [True, False]
               }
    default_options = {"shared": False,
                       "fPIC": True
                       }

    def requirements(self):
        for reference in self._meta.dependencies:
            self.requires(reference)

    def configure(self):
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            del self.options.fPIC

    def _configure_cmake(self):
        cmake = CMake(self, set_cmake_flags=True)
        cmake.configure()
        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()


    def package(self):
        cmake = self._configure_cmake()
        cmake.install()

        if self.settings.compiler == 'gcc' and 'arm' in self.settings.arch:
            for i in glob.glob('%s/lib/*.so*' % self.package_folder):
                if os.path.isfile(i) and not i.endswith('.strip'):
                    name = os.path.basename(i)
                    getsize = os.path.getsize
                    print('[%s] %d KB' % (name, getsize(i) / 1000))

                    strip = i + '.strip'
                    shutil.copy(i, strip)
                    self.run('$STRIP %s' % strip)
                    print('[%s] %d KB after striped' % (name, getsize(strip) / 1000))
                    os.remove(strip)


    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        self.cpp_info.libs.sort(reverse=True)

        if self.settings.os == "Windows":
            if self.options.shared:
                self.cpp_info.defines = ["LIB-1_USE_DLLS"]
