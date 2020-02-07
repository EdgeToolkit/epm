import os
import warnings
import os
import unittest


from epm.util.files import mkdir, rmdir
from epm.util.files import load_yaml

EPM_TEST_FOLDER = os.getenv('EPM_TEST_FOLDER', None)

from epm.util import system_info
PLATFORM, ARCH = system_info()

from conans.client.tools.win import vs_installation_path


class Configure(object):

    def __init__(self, filename=None):
        filename = filename or 'test-conf.yml'
        self._items = {}
        try:
            if os.path.exists(filename):
                self._items = load_yaml(filename)
        except Exception as exc:
            print('load test config failed', exc)
            pass

    @property
    def with_vs2019(self):
        return bool(vs_installation_path(16))

    @property
    def platform(self):
        return PLATFORM

    @property
    def platform(self):
        return ARCH



CONFIG = Configure(os.environ.get('EPM_TEST_CONFIG'))


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
