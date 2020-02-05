import os
import unittest
import platform

from conans.tools import environment_append
from conans.paths import conan_expand_user


class PathsTest(unittest.TestCase):

    def test_get_epm_user_home(self):
        from epm.paths import get_epm_user_home

        with environment_append({"EPM_USER_HOME": None}):
            path = get_epm_user_home()
            self.assertEqual(path, conan_expand_user('~'))

        if platform.system() == "Windows":
            HOME = r'c:\epm_test_home'
        else:
            HOME = '/epm/test/home'

        with environment_append({"EPM_USER_HOME": HOME}):
            path = get_epm_user_home()
            self.assertEqual(path, HOME)

