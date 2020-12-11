import sys
import os
import shutil
import yaml


from conans.util.files import mkdir
from conans.client.conan_api import ConanAPIV1 as ConanAPI, api_method as conan_api_method
from conans.client.output import colorama_initialize
from conans.client.userio import UserIO as UserIO
from conans.client.tools import environment_append

from epm.worker.build import Builder
from epm.worker.sandbox import Sandbox
from epm.worker.create import Creator
from epm.worker.runit import Runit
from epm.worker.upload import Uploader
from epm.worker.download import Downloader


from epm import HOME_DIR, DATA_DIR
from epm.model.runner import Output
from epm.errors import EException


CONAN_FOLDER_NAME = '.conan'


class APIUtils(object):
    _HOME_WORKBENCH = None
    _PACKAGE_NAME = None

    workbench_dir = None
    out = None
    user_io = None
    _CONFIG = None

    @staticmethod
    def initialize_home_workbench():
        if APIUtils._HOME_WORKBENCH is None:
            APIUtils._HOME_WORKBENCH = HOME_DIR
            if not os.getenv('EPM_WORKBENCH'):
                conan_home = os.path.join(HOME_DIR, CONAN_FOLDER_NAME)
                settings_file = os.path.join(conan_home, 'settings.yml')
                if not os.path.exists(settings_file):
                    filename = os.path.join(DATA_DIR, 'conan', 'settings.yml')
                    mkdir(conan_home)
                    shutil.copy(filename, settings_file)
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

        conan = ConanAPI(self.conan_home)

        with environment_append({'CONAN_USER_HOME': self.conan_home}):
            path = conan.config_get("storage.path", quiet=True)

        storage = self.config.conan.storage
        if storage:
            if storage.startswith('${workbench}'):
                path = storage.replace('${workbench}', self.workbench_dir)
            elif storage.startswith('~'):
                path = os.path.expanduser(storage)
            else:
                path = storage
        path = os.path.abspath(path)

        return path

    @property
    def conan_short_path(self):
        short_path = self.config.conan.short_path
        path = None
        if short_path:
            if short_path.startswith('${workbench}'):
                path = short_path.replace('${workbench}', self.workbench_dir)
            elif short_path.startswith('~'):
                path = os.path.expanduser(self.config.conan.storage)
            else:
                path = short_path

        return path

    @property
    def config(self):
        if self._CONFIG is None:
            from epm.model.config import Config
            self._CONFIG = Config(os.path.join(self.workbench_dir, 'config.yml'))

        return self._CONFIG

def api_method(f):

    def wrapper(api, *args, **kwargs):
        old_curdir = os.getcwd()
        try:
            env_vars = api.config.get('environment', {})
            env_vars = dict(api.env_vars, **env_vars)
            if api.conan_storage_path:
                env_vars['CONAN_STORAGE_PATH'] = api.conan_storage_path

            if api.conan_short_path:
                env_vars['CONAN_USER_HOME_SHORT'] = api.conan_short_path

            with environment_append(env_vars):
                return f(api, *args, **kwargs)

        finally:
            os.chdir(old_curdir)
    return wrapper


def request_profile(f):

    def wrapper(api, *args, **kwargs):
        param = args[0]
        if 'PROFILE' not in param:
            raise EException('%s required `profile` missed.' % f.__name__)
        return f(api, *args, **kwargs)
    return wrapper


class APIv1(APIUtils):
    VERSION = '0.1'

    @classmethod
    def factory(cls):
        return cls()

    def __init__(self, workbench=None, output=None, user_io=None, color=None):
        from epm.utils import get_workbench_dir

        APIUtils.initialize_home_workbench()

        color = color or colorama_initialize()
        self.out = output or Output(sys.stdout, sys.stderr, color)

        self.user_io = user_io or UserIO(out=self.out)

        workbench = workbench or os.getenv('EPM_WORKBENCH')
        self.workbench_dir = get_workbench_dir(workbench)

        self._conan = None
        self._config = None
        self.env_vars = {}

    def project(self, profile, scheme=None):
        from epm.model.project import Project
        return Project(profile, scheme, self)

    @api_method
    @request_profile
    def build(self, param):
        worker = Builder(self)
        worker.exec(param)

    @api_method
    @request_profile
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
    @request_profile
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
            with open(path) as f:
                self._config = yaml.safe_load(f)
        return self._config

@conan_api_method
def conanfile_instance(conan, path, profile=None):


    from conans.model.ref import ConanFileReference, PackageReference, check_valid_ref
    from conans.errors import ConanException
    from conans.client.recorder.action_recorder import ActionRecorder
    from conans.util.conan_v2_mode import CONAN_V2_MODE_ENVVAR

    remotes = conan.app.load_remotes(remote_name=None)
    try:
        ref = ConanFileReference.loads(path)
    except ConanException:
        conanfile_path = os.path.join(path, 'conanfile.py')
        conanfile = conan.app.loader.load_named(conanfile_path, None, None, None, None)
        ref = ConanFileReference(conanfile.name, conanfile.version, None, None)
    else:
        update = False
        result = conan.app.proxy.get_recipe(ref, update, update, remotes, ActionRecorder())
        conanfile_path, _, _, ref = result
        conanfile = conan.app.loader.load_basic(conanfile_path)
        conanfile.name = ref.name
        conanfile.version = str(ref.version) \
            if os.environ.get(CONAN_V2_MODE_ENVVAR, False) else ref.version

    #conan.app.cache.default_profile = profile.path.host
#    import tempfile
#    mkdir(".epm/tmp/profiles")
#    pdir = tempfile.mkdtemp(dir=".epm/tmp/profiles")
#    from conans.model.graph_info import GraphInfo
#    from conans.model.graph_lock import GraphLockFile

#    GraphInfo(profile.host, root_ref=ref).save(pdir)
#    GraphLockFile(profile.host, None).save(pdir)
    instance = conan.app.graph_manager.load_consumer_conanfile(conanfile_path, None)
#    print('+++++++++', instance.settings.os, instance.settings.arch)
#    instance.settings = profile.settings
    from conans.model.settings import Settings
    from conans.tools import load
    settings = Settings.loads(load(os.path.join(conan.app.cache_folder, 'settings.yml')))
    settings.os = profile.host.settings['os']
    settings.arch = profile.host.settings['arch']
    settings.compiler = profile.host.settings['compiler']
    settings.compiler.version = profile.host.settings['compiler.version']
    instance.settings = settings

    if hasattr(instance, 'configure'):
        instance.configure()

    if hasattr(instance, 'config_options'):
        instance.config_options()
    return conanfile, instance









API = APIv1
