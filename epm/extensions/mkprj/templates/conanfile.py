{% set name = argument.name %}
{% set version = argument.version %}
{% set id = name.replace('-', '_') %}
{% set ID = name.upper() %}
from conans import ConanFile, CMake, tools
from epm.tools.conan import as_package
ConanFile = as_package(ConanFile)

class {{ID}}Conan(ConanFile):
    name = "{{name}}"
    description = "<TODO>"
    topics = ("conan", "{{name}}")
    url = "<TODO>"
    homepage = "<TODO>"
    license = "MIT"
    exports_sources = ["LICENSE", "CMakeLists.txt", "include/*", "source/*", "cmake/*"]
    generators = "cmake"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}

    _cmake = None

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            del self.options.fPIC

    def _configure_cmake(self):
        if not self._cmake:
            self._cmake = CMake(self)
            self._cmake.configure()
        return self._cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy("LICENSE", dst="licenses")
        cmake = self._configure_cmake()
        cmake.install()
    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)