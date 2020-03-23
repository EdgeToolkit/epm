import sys
import os
from conans.client.conan_api import ConanAPIV1 as ConanAPI
from conans.client.output import ConanOutput as Output, colorama_initialize
from conans.client.userio import UserIO as UserIO
from epm.paths import get_epm_home_dir
from epm.worker.build import Builder
from epm.worker.create import Creator
from epm.worker.sandbox import Sandbox
from epm.worker.upload import Uploader
from epm.util.files import load_yaml
from conans.client.tools import environment_append



def api_method(f):
    def wrapper(api, *args, **kwargs):
#        quiet = kwargs.pop("quiet", False)
        old_curdir = os.getcwd()
#        old_output = api.user_io.out
        try:
#            api.create_app(quiet_output=quiet_output)
#            log_command(f.__name__, kwargs)
            with environment_append(api.env_vars):
                return f(api, *args, **kwargs)
        except Exception as exc:
#            if quiet_output:
#                old_output.write(quiet_output._stream.getvalue())
#                old_output.flush()
#            msg = exception_message_safe(exc)
#            try:
#                log_exception(exc, msg)
#            except BaseException:
#                pass
            raise
        finally:
            os.chdir(old_curdir)
    return wrapper


class APIv1(object):

    @classmethod
    def factory(cls):
        return cls()

    def __init__(self, home_dir=None, output=None, user_io=None):
        color = colorama_initialize()
        self.out = output or Output(sys.stdout, sys.stderr, color)
        self.user_io = user_io or UserIO(out=self.out)
        self.home_dir = home_dir or get_epm_home_dir()

        self._conan = None
        self._config = None
        self.env_vars = {'CONAN_USER_HOME': self.home_dir,
                         'CONAN_STORAGE_PATH': os.path.join(self.home_dir, '.conan', 'data')}

        self._CONFIG = None

        from epm.model.profile import install_default_profiles
        install_default_profiles()

    @property
    def conan(self):
        cache_folder = os.path.join(self.home_dir, '.conan')
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
            self._CONFIG = Config(os.path.join(self.home_dir, 'config.yml'))

        return self._CONFIG

    def project(self, scheme):
        from epm.model.project import Project
        name = scheme if isinstance(scheme, str) else scheme['scheme']
        return Project(name, self)

    @api_method
    def build(self, param):
        worker = Builder(self)
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
    def sandbox(self, param):
        project = self.project(param['scheme'])
        sandbox = Sandbox(project, self)
        command = param['command']
        argv = param.get('args') or []
        runner = param.get('runner', None)
        return sandbox.exec(command, runner=runner, argv=argv)

    @api_method
    def load_config(self, update=True):
        path = os.path.join(self.home_dir, 'config.yml')
        if not os.path.exists(path):
            return {}
        if self._config is None or update:
            self._config = load_yaml(path)
        return self._config

    @property
    def conan_storage_path(self):
        return os.getenv('CONAN_STORAGE_PATH', os.path.join(self.home_dir, '.conan', 'data'))


API = APIv1
