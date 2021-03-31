import os
import yaml
import shutil
import pathlib
import glob
import pprint

from epm.utils.logger import syslog

from collections import namedtuple

from conans.tools import mkdir, rmdir

from conans.client.profile_loader import read_profile
from conans.client.conan_api import ProfileData

from epm.errors import EException
from epm import HOME_DIR, DATA_DIR
from epm.utils import get_workbench_dir, system_info

PLATFORM, ARCH = system_info()


def install_buildin_profiles(cached=None):
    cached = cached or HOME_DIR

    def _(x): pathlib.PurePath(x).as_posix()

    if _(os.path.abspath(cached)) != _(HOME_DIR):
        return

    path = os.path.join(cached, '.conan', 'settings.yml')
    if not os.path.exists(path):
        mkdir(os.path.dirname(path))
        shutil.copyfile(os.path.join(DATA_DIR, 'conan', 'settings.yml'), path)

    # only install for empty folder
    if glob.glob('%s/profiles/*.yml' % cached):
        return

    pr_dir = os.path.join(cached, 'profiles')    
    buildin = os.path.join(DATA_DIR, 'profiles')
    rmdir(pr_dir)
    shutil.copytree(buildin, pr_dir)
    return

    for i in os.listdir(buildin):
        path = os.path.join(buildin, i)
        name = os.path.basename(path)
        dst = os.path.join(pr_dir, name)
        print(i,'*', path, ' isfile:',os.path.isfile(path))
        if os.path.isfile(path):
            shutil.copy(path, dst)
        else:
            print('profile tree', path, '->',dst)
            shutil.copytree(path, dst)


def load_profiles_config(pr_dir):
    econfig = {}
    for path in glob.glob(f'{pr_dir}/*.yml'):
        with open(path) as f:
            data = yaml.safe_load(f)
        common = data.pop('.common', {}) or {}
        for name, config in data.items():
            if name in econfig:
                raise EException('Duplicate profile definition of <{}>. defined in \n\t{}\n\t{}'.format(
                    name, path, econfig['__file__']
                ))
            config['__file__'] = pathlib.PurePath(path).as_posix()
            config['__name__'] = name
            econfig[name] = dict(config, **common)
    syslog.debug('load profiles from {}\n{}\n'.format(pr_dir, pprint.pformat(econfig, indent=2)))
    return econfig


class Profile(object):
    """ Specific profile

    """
    _checked_default = False
    _CONFIGS = {}

    def __init__(self, name, folder):
        self.name = name
        folder = folder or get_workbench_dir(os.getenv('EPM_WORKBENCH'))

        if not Profile._checked_default:
            install_buildin_profiles(folder)
            Profile._checked_default = True
        self._workbench_dir = os.path.normpath(os.path.abspath(folder))
        self._root_dir = os.path.join(self._workbench_dir, 'profiles')
        self._config = None
        self._profile_build = None
        self._profile_host = None

    @property
    def config(self):
        if self._config is None:
            if self._root_dir not in Profile._CONFIGS:
                configs = load_profiles_config(self._root_dir)
                Profile._CONFIGS[self._root_dir] = configs

            else:
                configs = Profile._CONFIGS[self._root_dir]

            if self.name not in configs:
                import pprint
                pprint.pprint(configs)
                print(list(configs.keys()))
                raise EException('undefined profile name <%s>.' % self.name)
            self._config = configs[self.name]
        return self._config

    @property
    def docker(self):
        Docker = namedtuple('Docker', ['builder', 'runner'])

        docker = self.config.get('docker')
        runner = docker.get('runner') if docker else None
        builder = docker.get('builder') if docker else None

        return Docker(builder, runner)

    def save(self, filename):
        mkdir(os.path.dirname(filename))
        path = os.path.join(self._directory, self._manifest['family'], self._manifest['name'])
        shutil.copyfile(path, filename)

    @property
    def build(self):
        if self._profile_build is None:

            self._profile_build = ProfileData(profiles=[self.path.build],
                                              settings=None, options=None, env=None)
        return self._profile_build

    def read_build_profile(self):
        name = self.config['profile_build']
        folder = os.path.dirname(self.config['__file__'])
        profile, _ = read_profile(name, folder, folder)
        return profile

    @property
    def host(self):
        if self._profile_host is None:
            name = self.config['profile_host']
            folder = os.path.dirname(self.config['__file__'])
            self._profile_host, _ = read_profile(name, folder, folder)
        return self._profile_host

    @property
    def path(self):
        host = self.config['profile_host']
        build = self.config['profile_build']
        folder = os.path.dirname(self.config['__file__'])
        return namedtuple("ProfilePath", "host build")(
            os.path.join(folder, host), os.path.join(folder, build))
