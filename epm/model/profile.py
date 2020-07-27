import os
import yaml
import shutil
import pathlib

from conans.client.profile_loader import read_profile
from epm.errors import EException
from epm.paths import DATA_DIR, get_epm_cache_dir

from collections import namedtuple

from epm.util import system_info

from epm.util import get_workbench_dir, HOME_DIR

PLATFORM, ARCH = system_info()


class Profile(object):
    """ Specific profile

    """
    _checked_default_profiles = False

    def __init__(self, name, folder):
        self.name = name
        folder = folder or get_workbench_dir(os.getenv('EPM_WORKBENCH'))

        if not Profile._checked_default_profiles:
            Profile.install_default_profiles()
            Profile._checked_default_profiles = True

        self._filename = os.path.join(folder, 'profiles', name)
        manifest = os.path.join(os.path.dirname(self._filename), 'manifest.yml')
        if not os.path.exists(manifest):
            raise EException('Can not find manifest.yml in profile <{}> folder {}.' % (
                             os.path.dirname(self._filename), name))

        if not os.path.exists(self._filename):
            raise EException('Can not find profile <%s>.' % name)

        with open(manifest) as f:
            self._manifest = yaml.safe_load(f)

        self._meta = None

        for family, value in self._manifest.items():
            for name, spec in value['profiles'].items():
                if name == os.path.basename(self.name):
                    self._meta = dict(value, **spec)
                    del self._meta['profiles']
                    break
        if self._meta is None:
            raise EException('No properties defined for profile %s' % self.name)

        name = os.path.basename(self.name)
        folder = os.path.dirname(self._filename)
        self._profile, _ = read_profile(name, folder, folder)

    @property
    def docker(self):
        Docker = namedtuple('Docker', ['builder', 'runner'])
        docker = self._meta.get('docker')
        runner = docker.get('runner') if docker else None
        builder = docker.get('builder') if docker else None

        return Docker(builder, runner)

    def save(self, filename):
        folder = os.path.dirname(filename)
        if not os.path.exists(folder):
            os.makedirs(folder)
        shutil.copyfile(self._filename, filename)

    @property
    def settings(self):
        return self._profile.settings

    @property
    def is_running_native(self):
        if PLATFORM != self.settings['os']:
            return False
        arch = self.settings['arch']
        assert(arch in ['x86', 'x86_64'])
        if ARCH == arch:
            return True

        if PLATFORM == 'Windows':
            return 'x86' == arch
        else:
            return False

    @property
    def builders(self):

        arch = self.settings['arch']
        platform = self.settings['os']

        if PLATFORM == 'Windows':
            if platform == 'Windows':
                return ['shell']
            elif platform == 'Linux':
                return ['docker']
        elif PLATFORM == 'Linux':
            if platform == 'Linux':
                return ['docker', 'shell']
        return None

    @property
    def is_cross_build(self):
        return PLATFORM != self.settings['os'] or ARCH != self.settings['arch']

    @staticmethod
    def install_default_profiles(cached=None):
        cached = cached or HOME_DIR

        if pathlib.PurePath(os.path.abspath(cached)).as_posix() != pathlib.PurePath(HOME_DIR).as_posix():
            return

        pd = os.path.normpath(os.path.join(cached, 'profiles'))
        if not os.path.exists(pd):
            os.makedirs(pd)

        manifest = os.path.join(pd, 'manifest.yml')
        if not os.path.exists(manifest):
            buildin = os.path.normpath(os.path.join(DATA_DIR, 'profiles'))
            with open(os.path.join(buildin, 'manifest.yml')) as f:
                m = yaml.safe_load(f)
            files = ['manifest.yml']

            for _, family in m.items():
                files += family.get('profiles', {}).keys() or []

            for j in files:
                shutil.copy(os.path.join(buildin, j), os.path.join(pd, j))

