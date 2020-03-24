import os
import unittest
import platform
from epm.test import TestCase
from conans.tools import environment_append
from conans.paths import conan_expand_user
from pathlib import PurePath

class PathsTest(TestCase):

    def test_get_EPM_CACHE_DIR(self):
        from epm.paths import get_epm_cache_dir

        with environment_append({"EPM_CACHE_DIR": None}):
            path = get_epm_cache_dir()
            self.assertEqual(PurePath(path).as_posix(),
                             PurePath(conan_expand_user('~/.epm')).as_posix())

        if platform.system() == "Windows":
            HOME = r'c:\epm_test_home'
        else:
            HOME = '/epm/test/home'

        with environment_append({"EPM_CACHE_DIR": HOME}):
            path = get_epm_cache_dir()
            self.assertEqual(PurePath(path).as_posix(),
                             PurePath(HOME).as_posix())

