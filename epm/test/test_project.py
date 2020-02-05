import os
import unittest
import tempfile

from epm.util.files import mkdir, rmdir
from epm.paths import TEST_DATA_DIR
from epm.model.project import Project
from conans.client.profile_loader import read_profile
from collections import OrderedDict

_DEFAULT_LIB_PRJ_DIR = os.path.join(TEST_DATA_DIR, 'project', 'lib')


class TestCase(unittest.TestCase):

    _WD = None
    _home = None

    def setUp(self):

        if self._WD is None:
            self._WD = os.path.abspath('epm.test.temp')
            rmdir(self._WD)
            mkdir(self._WD)

        if self._home is None:
            self._home = os.path.join(self._WD, 'epm.home')
            rmdir(self._home)
            mkdir(self._home)

        self._OLD_EPM_USER_HOME = os.environ.get('EPM_USER_HOME')
        os.environ['EPM_USER_HOME'] = self._home

        self._OLD_CD = os.path.abspath('.')
        os.chdir(self._WD)

    def tearDown(self):
        if self._OLD_EPM_USER_HOME:
            os.environ['EPM_USER_HOME'] = self._OLD_EPM_USER_HOME
        else:
            del os.environ['EPM_USER_HOME']
        os.chdir(self._OLD_CD)


class ProjectTestCase(TestCase):

    def test_project_lib_none_scheme(self):
        prj = Project(None, directory=_DEFAULT_LIB_PRJ_DIR)
        self.assertIsNone(prj.scheme)

        self.assertEqual(prj.version, '0.0.1')
        self.assertEqual(prj.name, 'lib')
        self.assertEqual(prj.user, 'example')
        self.assertEqual(prj.channel, 'public')
        self.assertEqual(prj.reference, 'lib/0.0.1@example/public')

        self.assertEqual(prj.folder.cache, '.epm')
        self.assertIsNone(prj.folder.out)
        self.assertIsNone(prj.folder.build)
        self.assertIsNone(prj.folder.test)
        self.assertIsNone(prj.folder.package)

    def test_project_lib(self):

        def _test(name, settings):
            prj = Project(name, directory=_DEFAULT_LIB_PRJ_DIR)
            self.assertEqual(prj.scheme.name, name)

            self.assertEqual(prj.version, '0.0.1')
            self.assertEqual(prj.name, 'lib')
            self.assertEqual(prj.user, 'example')
            self.assertEqual(prj.channel, 'public')
            self.assertEqual(prj.reference, 'lib/0.0.1@example/public')

            self.assertEqual(prj.folder.cache, '.epm')
            self.assertEqual(prj.folder.out, '.epm/%s' % name)
            self.assertEqual(prj.folder.build, '.epm/%s/build' % name)
            self.assertEqual(prj.folder.test, '.epm/%s/test_package' % name)
            self.assertEqual(prj.folder.package, '.epm/%s/package' % name)

            scheme = prj.scheme
            profile = scheme.profile
            profile.save('%s.profile' % name)
            pr, _ = read_profile('%s.profile' % name, '.', '.')

            self.assertEqual(pr.settings, settings)

        _test('gcc5',
              OrderedDict([('os', 'Linux'), ('os_build', 'Linux'), ('arch', 'x86_64'), ('arch_build', 'x86_64'),
                           ('compiler', 'gcc'), ('compiler.version', '5'), ('compiler.libcxx', 'libstdc++11'),
                           ('build_type', 'Release')]))
        _test('gcc5.d',
              OrderedDict([('os', 'Linux'), ('os_build', 'Linux'), ('arch', 'x86_64'), ('arch_build', 'x86_64'),
                           ('compiler', 'gcc'), ('compiler.version', '5'), ('compiler.libcxx', 'libstdc++11'),
                           ('build_type', 'Debug')]))









