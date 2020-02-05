import sys
import tempfile
import os
import unittest

from conans.tools import environment_append

from epm.model.scheme import ProfileManager


class ProfileTestCase(unittest.TestCase):

    _home = None

    def setUp(self):
        if self._home is None:
            self._home = tempfile.mkdtemp(suffix='@epm.test_profile')
        self._OLD_EPM_USER_HOME = os.environ.get('EPM_USER_HOME')
        os.environ['EPM_USER_HOME'] = self._home

    def tearDown(self):
        if self._OLD_EPM_USER_HOME:
            os.environ['EPM_USER_HOME'] = self._OLD_EPM_USER_HOME
        else:
            del os.environ['EPM_USER_HOME']

    def test_not_init(self):
        cache_folder = os.path.join(self._home, '_not_init')
        os.makedirs(cache_folder)
        with environment_append({'EPM_USER_HOME': cache_folder}):
            pm = ProfileManager(init=False)
            self.assertEqual(pm.folder, os.path.join(cache_folder, '.epm', 'profiles'))
            self.assertFalse(os.path.exists(pm.folder))

    def test_init(self):
        cache_folder = os.path.join(self._home, '_init')
        os.makedirs(cache_folder)
        with environment_append({'EPM_USER_HOME': cache_folder}):
            pm = ProfileManager()
            self.assertEqual(pm.folder, os.path.join(cache_folder, '.epm', 'profiles'))
            self.assertTrue(os.path.exists(pm.folder))
            self.assertSetEqual(set(os.listdir(pm.folder)), {'linux.yml', 'windows.yml'})

    def test_profiles(self):
        pm = ProfileManager()
        self.assertSetEqual(set(pm.families.keys()),
                            {'gcc5', 'gcc5-x86', 'hisi300', 'vs2019'})

































###########################################################################################


import epm
#from epm.model.profile import ProfileFactory

_DEFAULT_PROFILES_DIR = os.path.join(os.path.dirname(epm.__file__), 'data', 'default_profiles')
_ProfileSpec = {}


class ProfileTestBase(unittest.TestCase):

    def assertProfileEqual(self, first, second, msg=None):
        from conans.model.profile import Profile as ConanProfile
        if isinstance(first, str):
            self.assertIsInstance(second, ConanProfile)
        else:
            self.assertIsInstance(first, ConanProfile)
            self.assertIsInstance(second, str)
            first, second = second, first

        self.assertMultiLineEqual(first.strip(), second.dumps().strip(), msg)

from epm.model.scheme import ProfileManager

class ProfileTest(ProfileTestBase):

    def test_profile_manager(self):
        return



    def test_windows(self):
        return
        path = os.path.join(_DEFAULT_PROFILES_DIR, 'windows.yml')
        factory = ProfileFactory(None)
        factory.load(path)

        VisualStudio = {'Release': '', 'Debug': '.d', 'MT': '.MT', 'MTd': '.MTd'}

        for i in ['vs2019']:
            self.assertIn(i, factory.profiles)

            for type in VisualStudio.keys():
                name = i + VisualStudio[type]
                self.assertIn(type, factory.types(i))
                self.assertIn(name, factory.specs)
                profile = factory.conan_profile(name)
                self.assertProfileEqual(profile, _ProfileSpec[name])

    def test_linux(self):
        return
        path = os.path.join(_DEFAULT_PROFILES_DIR, 'linux.yml')
        factory = ProfileFactory(None)
        factory.load(path)
        GCC = {'Release': '', 'Debug': '.d'}

        for i in ['gcc5', 'gcc5-x86', 'hisi300']:
            self.assertIn(i, factory.profiles)

            for type in GCC.keys():
                name = i + GCC[type]
                self.assertIn(type, factory.types(i))
                self.assertIn(name, factory.specs)
                profile = factory.conan_profile(name)
                self.assertProfileEqual(profile, _ProfileSpec[name])

##########################################################
#               Validation Profiles
##########################################################


_ProfileSpec['vs2019'] = """
[settings]
os=Windows
os_build=Windows
arch=x86_64
arch_build=x86_64
compiler=Visual Studio
compiler.version=16
compiler.runtime=MD
build_type=Release
[options]
[build_requires]
[env]
"""

_ProfileSpec['vs2019.d'] = """    
[settings]
os=Windows
os_build=Windows
arch=x86_64
arch_build=x86_64
compiler=Visual Studio
compiler.version=16
compiler.runtime=MDd
build_type=Debug
[options]
[build_requires]
[env]
"""

_ProfileSpec['vs2019.MT'] = """    
[settings]
os=Windows
os_build=Windows
arch=x86_64
arch_build=x86_64
compiler=Visual Studio
compiler.version=16
compiler.runtime=MT
build_type=Release
[options]
[build_requires]
[env]
"""

_ProfileSpec['vs2019.MTd'] = """    
[settings]
os=Windows
os_build=Windows
arch=x86_64
arch_build=x86_64
compiler=Visual Studio
compiler.version=16
compiler.runtime=MTd
build_type=Debug
[options]
[build_requires]
[env]
"""

_ProfileSpec['gcc5'] = """
[settings]
os=Linux
os_build=Linux
arch=x86_64
arch_build=x86_64
compiler=gcc
compiler.version=5
compiler.libcxx=libstdc++11
build_type=Release
[options]
[build_requires]
[env]
"""

_ProfileSpec['gcc5.d'] = """
[settings]
os=Linux
os_build=Linux
arch=x86_64
arch_build=x86_64
compiler=gcc
compiler.version=5
compiler.libcxx=libstdc++11
build_type=Debug
[options]
[build_requires]
[env]
"""

_ProfileSpec['gcc5-x86'] = """
[settings]
os=Linux
os_build=Linux
arch=x86
arch_build=x86
compiler=gcc
compiler.version=5
compiler.libcxx=libstdc++11
build_type=Release
[options]
[build_requires]
[env]
"""

_ProfileSpec['gcc5-x86.d'] = """
[settings]
os=Linux
os_build=Linux
arch=x86
arch_build=x86
compiler=gcc
compiler.version=5
compiler.libcxx=libstdc++11
build_type=Debug
[options]
[build_requires]
[env]
"""


_ProfileSpec['hisi300'] = """
[settings]
os=Linux
os_build=Linux
arch=armv7
arch_build=x86
compiler=gcc
compiler.version=4.8
compiler.libcxx=libstdc++11
build_type=Release
compiler.toolchain=arm-hisiv300-linux
[options]
[build_requires]
[env]
"""

_ProfileSpec['hisi300.d'] = """
[settings]
os=Linux
os_build=Linux
arch=armv7
arch_build=x86
compiler=gcc
compiler.version=4.8
compiler.libcxx=libstdc++11
build_type=Debug
compiler.toolchain=arm-hisiv300-linux
[options]
[build_requires]
[env]
"""
