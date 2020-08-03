import os
import yaml
import shutil
import pathlib
import glob
from collections import namedtuple

from conans.tools import mkdir

from conans.client.profile_loader import read_profile

from epm.errors import EException
from epm import HOME_DIR, DATA_DIR
from epm.utils import get_workbench_dir, system_info, load_yaml

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
    mkdir(pr_dir)
    buildin = os.path.join(DATA_DIR, 'profiles')
    for path in glob.glob('%s/*' % buildin):
        name = os.path.basename(path)
        dst = os.path.join(pr_dir, name)
        if os.path.isfile(path):
            shutil.copy(path, dst)
        else:
            shutil.copytree(path, dst)


def load_manifest(pr_dir):
    manifest = {}

    for path in glob.glob('%s/*.yml' % pr_dir):

        meta = load_yaml(path)
        family = os.path.basename(path)[:-4]
        for group, metadata in meta.items():
            profiles = metadata.pop('profiles')
            for name, pr in profiles.items():
                aliase = pr.get('aliase') or []
                if isinstance(aliase, str):
                    aliase = [aliase]

                description = pr.get('description', '')

                for i in [name] + aliase:
                    assert i not in manifest, 'profile <%s> duplicated' %i
                    manifest[i] = {'family': family,
                                   'group': group,
                                   'name': name,
                                   'description': description,
                                   'metadata': metadata}
    return manifest


class Profile(object):
    """ Specific profile

    """
    _checked_default_profiles = False
    _profile = None
    MANIFEST_CACHE = {}

    def __init__(self, name, folder):
        self.name = name
        folder = folder or get_workbench_dir(os.getenv('EPM_WORKBENCH'))

        if not Profile._checked_default_profiles:
            install_buildin_profiles(folder)
            Profile._checked_default_profiles = True

        self._directory = os.path.normpath(os.path.abspath(os.path.join(folder, 'profiles')))

        if self._directory not in self.MANIFEST_CACHE:
            profiles = load_manifest(self._directory)
        else:
            profiles = self.MANIFEST_CACHE[self._directory]
        if name not in profiles:
            raise EException('%name is not defined profile.')
        self._manifest = profiles[name]

    @property
    def docker(self):
        Docker = namedtuple('Docker', ['builder', 'runner'])
        meta = self._manifest['metadata']
        docker = meta.get('docker')
        runner = docker.get('runner') if docker else None
        builder = docker.get('builder') if docker else None

        return Docker(builder, runner)

    def save(self, filename):
        mkdir(os.path.dirname(filename))
        path = os.path.join(self._directory, self._manifest['group'], self._manifest['name'])
        shutil.copyfile(path, filename)

    @property
    def profile(self):
        if self._profile is None:
            name = self._manifest['name']
            folder = os.path.join(self._directory, self._manifest['family'])
            self._profile, _ = read_profile(name, folder, folder)
        return self._profile

    @property
    def settings(self):
        return self.profile.settings

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

