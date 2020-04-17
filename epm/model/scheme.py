import os
import yaml
import pprint
import copy
import glob
import shutil
import copy

from conans.client.profile_loader import read_profile
from conans.model.options import OptionsValues
from conans.tools import RunEnvironment
from epm.errors import EException
from epm.paths import DATA_DIR
from epm.util.files import load_yaml
#from epm.util import split_plan_name

from collections import OrderedDict, namedtuple

from epm.util import is_elf, system_info
from epm.util.files import remove, rmdir, load_yaml

from conans.client.tools import environment_append

PLATFORM, ARCH = system_info()

class Scheme(object):

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
        conan = self.project.api.conan
        conanfile = conan.inspect(self.project.dir, ['settings', 'options', 'default_options', 'manifest'])
        manifest = manifest or conanfile['manifest'] or self.project.manifest
        schemes = manifest.get('scheme', {})
        scheme = schemes.get(name, {})

        deps = copy.deepcopy(manifest['dependencies'])

        options = scheme.get('options', {})
        for pkg in deps.values():
            pkg.scheme = None
            pkg.options = None

        for k, v in scheme.items():
            if k in deps:
                deps[k].scheme = v
                deps[k].options = None

        return options, deps

    def _load_dep_schemes(self, libs, deps, storage=None):


        for name, ref in deps.items():
            assert ref.scheme is None
            continue
            if name in libs.keys():
                continue

            scheme = info['options']
            version = info['version']
            user = info.get('group', self.project.group) #'['user']

            channel = info.get('channel', self.project.channel)

            conan = self.project.api.conan
            reference = '%s/%s@%s/%s' % (name, version, user, channel)


            storage = storage or self.project.api.conan_storage_path
            with environment_append({'CONAN_STORAGE_PATH': storage}):
                recipe = conan.inspect(reference, [])


            path = os.path.join(storage, name, version, user, channel, 'export', 'package.yml')

            manifest = load_yaml(path)

            options, deps = self._parse(scheme, manifest)

            libs[name] = {'manifest': manifest, 'recipe': recipe, 'options': options, 'scheme.deps': deps}

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

    def _options(self, package=False):
        return OptionsValues(self._options_items(package))

    @property
    def options(self):
        return self._options(False)

    @property
    def package_options(self):
        return self._options(True)
