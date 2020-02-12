import os
import warnings
import os
import unittest
import docker

from conans.client.conan_api import ConanAPIV1 as ConanAPI
from epm.api import API
from epm.util.files import mkdir, rmdir
from epm.util.files import load_yaml

EPM_TEST_FOLDER = os.getenv('EPM_TEST_FOLDER', None)

from epm.util import system_info
PLATFORM, ARCH = system_info()

from conans.client.tools.win import vs_installation_path


class Configure(object):

    def __init__(self, filename=None):
        self._is_docker_startup = None
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
    def arch(self):
        return ARCH

    @property
    def is_docker_startup(self):
        if self._is_docker_startup is None:
            client = docker.from_env()
            try:
                client.ping()
                self._is_docker_startup = True
            except:
                self._is_docker_startup = False
        return self._is_docker_startup
        
    @property
    def remotes(self):
        return self._items.get('remotes', {})

CONFIG = Configure(os.environ.get('EPM_TEST_CONFIG'))

class TestCase(unittest.TestCase):

    _WD = None
    _home = None

    api = None
    conan_server = False
    remotes = None
    config = CONFIG

    @staticmethod
    def setUpClass():
        pass

    @staticmethod
    def tearDownClass():
        pass

    def setUp(self):

        if self._WD is None:
            self._WD = os.path.abspath('epm.test.temp')
            rmdir(self._WD)
            mkdir(self._WD)

        if self._home is None:
            self._home = os.path.join(self._WD, 'epm.home')
            rmdir(self._home)
            mkdir(self._home)

        self._OLD_EPM_HOME_DIR = os.getenv('EPM_HOME_DIR')
        os.environ['EPM_HOME_DIR'] = self._home

        self._OLD_CD = os.path.abspath('.')
        os.chdir(self._WD)

        if self.conan_server:
            api = API()
            conan = api.conan
            conan.remote_clean()
            for name, remote in self.config.remotes.items():
                url = remote['url']
                conan.remote_add(remote_name=name, url=url, verify_ssl=False)
                username = remote.get('username')
                password = remote.get('password')
                if username and password:
                    conan.authenticate(username, password=password, remote_name=name, skip_auth=True)


    def tearDown(self):

        if self._OLD_EPM_HOME_DIR:
            os.environ['EPM_HOME_DIR'] = self._OLD_EPM_HOME_DIR
        else:
            del os.environ['EPM_HOME_DIR']
        os.chdir(self._OLD_CD)

