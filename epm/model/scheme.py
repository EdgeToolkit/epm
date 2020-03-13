import os
import yaml
import pprint
import copy
import glob
import shutil

from conans.client.profile_loader import read_profile
from conans.model.options import OptionsValues
from conans.tools import RunEnvironment
from epm.errors import EException
from epm.paths import DATA_DIR, get_epm_home_dir
from epm.util.files import load_yaml
from epm.util import split_plan_name

from collections import OrderedDict, namedtuple

from epm.util import is_elf, system_info
from epm.util.files import remove, rmdir, load_yaml
from epm.paths import get_epm_home_dir

from conans.client.tools import environment_append

PLATFORM, ARCH = system_info()


def parse_scheme_name(name):
    s = name.split('@')
    profile = s[0]
    options = None if len(s) == 1 else s
    options = None if options in ['default', 'None'] else options
    return profile, options


class Profile(object):
    """ Specific profile

    """

    def __init__(self, name, epm_dir):
        self.name = name
        self._epm_dir = epm_dir or get_epm_home_dir()
        self._filename = os.path.join(self._epm_dir, 'profiles', name)
        manifest = os.path.join(os.path.dirname(self._filename), 'manifest.yml')
        if not os.path.exists(manifest):
            raise EException('No %s for %s, you need to install.' % (manifest, name))

        if not os.path.exists(self._filename):
            raise EException('No  %s profile, you need to install.' % name)

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

class Options(object):

    def __init__(self, name, project):
        self._name = name
        self._scheme = None  # options name
        self._api = None
        self.project = project

    @property
    def name(self):
        return self._name

    def _parse(self, name, manifest=None):
        ''' parse the package (manifest) scheme (options) information

        :param name: name of scheme to be parsed
        :param manifest: manifest (package.yml)
        :return:
        '''
        manifest = manifest or self.project.manifest
        schemes = manifest.get('scheme', {})
        options = schemes.get('options', {}).get(name, {})
        dependencies = manifest.get('dependencies', {})

        dep_options = options.get('.dependencies', {})

        # pick up options of this package.yml
        options = {k: v for k, v in options.items() if k[0] != '.'}
        deps = {}

        for pkg, sch in dep_options.items():
            info = dependencies.get(pkg)  # get dependent package info
            if not info:
                raise EException('less information of %s, miss dependencies in package.yml ' % name)

            deps[pkg] = {**info, 'options': sch}

        return options, deps

    def _load_dep_schemes(self, libs, deps, storage=None):

        for name, info in deps.items():
            if name in libs.keys():
                continue

            scheme = info['options']
            version = info['version']
            user = info.get('group', self.project.group) #'['user']

            channel = info.get('channel', self.project.channel)

            conan = self.project.api.conan
            reference = '%s/%s@%s/%s' % (name, version, user, channel)
            print('===>', reference, '!!!')

            storage = storage or self.project.api.conan_storage_path
            with environment_append({'CONAN_STORAGE_PATH': storage}):
                recipe = conan.inspect(reference, [])
                print('@@@@------')
                print(recipe)

            path = os.path.join(storage, name, version, user, channel, 'export', 'package.yml')

            manifest = load_yaml(path)

            options, deps = self._parse(scheme, manifest)

            libs[name] = {'manifest': manifest, 'recipe': recipe, 'options': options, 'scheme.deps': deps}

#            log.info('scheme of {} reference={} loaded: \n{}'.format(
#                name, reference, pprint.pformat(libs[name], indent=2)))

            self._load_dep_schemes(libs, deps, storage)

    def _options_items(self, package):

        options, deps = self._parse(self.name)
        libs = {}
        self._load_dep_schemes(libs, deps)

        items = {}
        for k, v in options.items():
            key = '%s:%s' % (self.project.name, k) if package else k
            items[key] = v

        for name, info in libs.items():
            for k, v in info['options'].items():
                key = '%s:%s' % (name, k)
                items[key] = v
        return items

    def as_conan_options(self, package=False):
        return OptionsValues(self._options_items(package))

    def as_list(self, package=False):
        return OptionsValues(self._options_items(package)).as_list()


class Scheme(object):

    def __init__(self, name, project):

        self.name = name[:-8] if name.endswith('@default') else name
        self.project = project
        self._profile = None
        self._options = None

    @property
    def profile_(self):
        if self._profile is None:
            name, _ = split_plan_name(self.name)
            if not name:
                raise EException('Can not load profile with the empty profile name: %s' % name)
            self._profile = Profile(name, self.profile.api.home_dir)

            #self._profile = ProfileManager().profile(name)
        return self._profile

    @property
    def profile(self):
        if self._profile is None:
            name, _ = parse_scheme_name(self.name)
            if not name:
                raise EException('Can not load profile with the empty profile name: %s' % name)

            self._profile = Profile(name, self.project.api.home_dir)
        return self._profile
    @property
    def options(self):
        if self._options is None:
            _, name = split_plan_name(self.name)
            self._options = Options(name, self.project)
        return self._options


