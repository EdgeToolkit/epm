import sys
import os
import pathlib
import shutil

from epm.paths import DATA_DIR
from conans.util.files import mkdir

from conans.client.conan_api import ConanAPIV1 as ConanAPI
from conans.client.output import colorama_initialize
from conans.client.userio import UserIO as UserIO
from epm.paths import get_epm_cache_dir
from epm.worker.build import Builder
from epm.worker.create import Creator
from epm.worker.sandbox import Sandbox
from epm.worker.runit import Runit
from epm.worker.upload import Uploader
from epm.worker.download import Downloader
from epm.util.files import load_yaml
from conans.client.tools import environment_append
from epm.model.runner import Output


class APIUtils(object):
    _HOME_WORKBENCH = None
    CONAN_FOLDER_NAME = '.conan'

    workbench_dir = None
    out = None
    user_io = None

    #######
    @staticmethod
    def get_home_dir(self):
        return os.path.join(os.path.expanduser('~'), '.epm')

    @staticmethod
    def get_workbench_dir(self, name=None):
        if name:
            path = os.path.join(self.get_home_dir(), name)
            if not os.path.exists(path):
                return None
            return path

        path = os.getenv('EPM_CI_WORKBENCH_DIRECTORY')

        if os.getenv('EPM_CI_WORK_ENVIRONMENT_DIR'):
            print('EPM_CI_WORK_ENVIRONMENT_DIR was deprecated, please replace with EPM_CI_WORKBENCH_DIRECTORY.')
            path = os.getenv('EPM_CI_WORK_ENVIRONMENT_DIR')

        return path or self.get_home_dir()

    @staticmethod
    def initialize_home_workbench(self):
        if APIUtils._HOME_WORKBENCH is None:
            home = self.get_home_dir()
            conan_home = os.path.jion(home, APIUtils.CONAN_FOLDER_NAME)
            settings_file = os.path.join(conan_home, 'settings.yml')
            if not os.path.exists(settings_file):
                filename = os.path.join(DATA_DIR, 'conan', 'settings.yml')
                mkdir(conan_home)
                shutil.copy(filename, settings_file)
            APIUtils._HOME_WORKBENCH = home
        return APIUtils._HOME_WORKBENCH

    @property
    def conan_home(self):
        return os.path.join(self.workbench_dir, APIUtils.CONAN_FOLDER_NAME)

    @property
    def conan(self):
        if self._conan is None:
            self._conan = ConanAPI(self.conan_home, self.out, self.user_io)
        return self._conan

    @property
    def conan_storage_path(self):
        cache_folder = os.path.join(self.workbench_dir, APIUtils.CONAN_FOLDER_NAME)
        conan = ConanAPI(cache_folder)
        return conan.config_get("storage.path", quiet=True)

def api_method(f):
    def wrapper(api, *args, **kwargs):
        old_curdir = os.getcwd()
        try:
            env_vars = api.config.get('environment', {})
            env_vars = dict(api.env_vars, **env_vars)

            with environment_append(env_vars):
                return f(api, *args, **kwargs)

        finally:
            os.chdir(old_curdir)
    return wrapper


class APIv1(APIUtils):
    VERSION = '0.9'

    @classmethod
    def factory(cls):
        return cls()

    def __init__(self, cache_dir=None, output=None, user_io=None, color=None, workshop=None):
        APIUtils.initialize_home_workshop()

        color = color or colorama_initialize()
        self.out = output or Output(sys.stdout, sys.stderr, color)

        self.user_io = user_io or UserIO(out=self.out)

        workshop = workshop or cache_dir
        self.workshop_dir = APIUtils.get_workshop_dir(workshop)

        self.cache_dir = cache_dir or get_epm_cache_dir()

        self._conan = None
        self._config = None
        self.env_vars = {}

        self._CONFIG = None


    @property
    def config(self):
        if self._CONFIG is None:
            from epm.model.config import Config
            self._CONFIG = Config(os.path.join(self.cache_dir, 'config.yml'))

        return self._CONFIG

    def project(self, profile, scheme=None):
        from epm.model.project import Project
        return Project(profile, scheme, self)

    @api_method
    def build(self, param):
        worker = Builder(self)
        worker.exec(param)

    @api_method
    def sandbox_build(self, param):
        worker = SandboxBuilder(self)
        worker.exec(param)

    @api_method
    def create(self, param):
        worker = Creator(self)
        worker.exec(param)

    @api_method
    def upload(self, param):
        worker = Uploader(self)
        worker.exec(param)

    @api_method
    def download(self, param):
        worker = Downloader(self)
        worker.exec(param)

    @api_method
    def sandbox(self, param):
        project = self.project(param['PROFILE'], param.get('SCHEME'))
        sandbox = Sandbox(project, self)
        command = param['command']
        argv = param.get('args') or []
        runner = param.get('RUNNER', None)
        return sandbox.exec(command, runner=runner, argv=argv)

    @api_method
    def runit(self, param):
        command = param['command']
        argv = param.get('args') or []
        if command == 'conan':
            import subprocess
            with environment_append({'CONAN_STORAGE_PATH': self.conan_storage_path}):
                proc = subprocess.run(['conan'] + argv)
            return proc.returncode

        project = self.project(param.get('PROFILE'), param.get('SCHEME'))
        runit = Runit(project, self)
        runner = param.get('RUNNER', None)

        return runit.exec(command, runner=runner, argv=argv)

    @api_method
    def load_config(self, update=True):
        path = os.path.join(self.cache_dir, 'config.yml')
        if not os.path.exists(path):
            return {}
        if self._config is None or update:
            self._config = load_yaml(path)
        return self._config









API = APIv1
