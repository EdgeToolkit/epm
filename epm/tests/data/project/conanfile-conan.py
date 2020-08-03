from conans import ConanFile

class Conan(ConanFile):
    name = "conan"
    url = "https://github.com/conan-io"
    homepage = "https://conan.io"
    license = "MIT"
    description = ("Conan conanfile")
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}
    generators = "cmake"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

