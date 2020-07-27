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
from epm import HOME_DIR
from epm.util import get_workbench_dir

CONAN_FOLDER_NAME = '.conan'

class APIUtils(object):
    _HOME_WORKBENCH = None
    _PACKAGE_NAME = None

    workbench_dir = None
    out = None
    user_io = None

    @staticmethod
    def initialize_home_workbench():
        if APIUtils._HOME_WORKBENCH is None:
            conan_home = os.path.join(HOME_DIR, CONAN_FOLDER_NAME)
            settings_file = os.path.join(conan_home, 'settings.yml')
            if not os.path.exists(settings_file):
                filename = os.path.join(DATA_DIR, 'conan', 'settings.yml')
                mkdir(conan_home)
                shutil.copy(filename, settings_file)
            APIUtils._HOME_WORKBENCH = HOME_DIR
        return APIUtils._HOME_WORKBENCH

    @property
    def conan_home(self):
        return os.path.join(self.workbench_dir, CONAN_FOLDER_NAME)

    @property
    def conan(self):
        if self._conan is None:
            self._conan = ConanAPI(self.conan_home, self.out, self.user_io)
        return self._conan

    @property
    def conan_storage_path(self):

        cache_folder = os.path.join(self.workbench_dir, CONAN_FOLDER_NAME)
        conan = ConanAPI(cache_folder)

        with environment_append({'CONAN_USER_HOME': self.conan_home}):
            path = conan.config_get("storage.path", quiet=True)
        return path


def api_method(f):
    def wrapper(api, *args, **kwargs):
        old_curdir = os.getcwd()
        try:
            from epm.util.workbench import banner
            banner()
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

    def __init__(self, workbench=None, output=None, user_io=None, color=None):
        APIUtils.initialize_home_workbench()

        color = color or colorama_initialize()
        self.out = output or Output(sys.stdout, sys.stderr, color)

        self.user_io = user_io or UserIO(out=self.out)

        workbench = workbench or os.getenv('EPM_WORKBENCH')
        self.workbench_dir = get_workbench_dir(workbench)

        self._conan = None
        self._config = None
        self.env_vars = {}

        self._CONFIG = None

    @property
    def config(self):
        if self._CONFIG is None:
            from epm.model.config import Config
            self._CONFIG = Config(os.path.join(self.workbench_dir, 'config.yml'))

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
        path = os.path.join(self.workbench_dir, 'config.yml')
        if not os.path.exists(path):
            return {}
        if self._config is None or update:
            self._config = load_yaml(path)
        return self._config


API = APIv1
