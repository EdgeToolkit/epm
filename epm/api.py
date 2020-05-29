import sys
import os
from conans.client.conan_api import ConanAPIV1 as ConanAPI
from conans.client.output import ConanOutput , colorama_initialize
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


def api_method(f):
    def wrapper(api, *args, **kwargs):
        old_curdir = os.getcwd()
        try:
            env_vars = api.config.get('environment', {})
            env_vars = dict(api.env_vars, **env_vars)

            with environment_append(env_vars):
                return f(api, *args, **kwargs)
        except Exception as exc:
            raise
        finally:
            os.chdir(old_curdir)
    return wrapper


class APIv1(object):

    @classmethod
    def factory(cls):
        return cls()

    def __init__(self, cache_dir=None, output=None, user_io=None):
        color = colorama_initialize()
        self.out = output or ConanOutput(sys.stdout, sys.stderr, color)

        self.user_io = user_io or UserIO(out=self.out)
        self.cache_dir = cache_dir or get_epm_cache_dir()

        self._conan = None
        self._config = None
        self.env_vars = {}

        self._CONFIG = None

    @property
    def conan(self):
        cache_folder = os.path.join(self.cache_dir, '.conan')
        if self._conan is None:
            settings_file = os.path.join(cache_folder, 'settings.yml')
            if not os.path.exists(settings_file):
                from epm.paths import DATA_DIR
                from epm.util.files import mkdir
                import shutil
                filename = os.path.join(DATA_DIR, 'conan', 'settings.yml')
                mkdir(cache_folder)
                shutil.copy(filename, settings_file)

            self._conan = ConanAPI(cache_folder, self.out, self.user_io)
        return self._conan

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
        project = self.project(param.get('PROFILE'), param.get('SCHEME'))
        runit = Runit(project, self)
        command = param['command']
        argv = param.get('args') or []
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

    @property
    def conan_storage_path(self):
        cache_folder = os.path.join(self.cache_dir, '.conan')
        conan = ConanAPI(cache_folder)
        return conan.config_get("storage.path", quiet=True)


API = APIv1
