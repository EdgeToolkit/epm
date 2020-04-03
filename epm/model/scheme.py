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
        manifest = manifest or self.project.manifest
        schemes = manifest.get('scheme', {})
        options = schemes.get(name, {})
        print(name, '==========', options)
        dependencies = manifest.get('dependencies', {})

        dep_options = options.get('.dependencies', {})

        # pick up options of this package.yml
        options = {k: v for k, v in options.items() if k[0] != '.'}
        deps = {}

        for pkg, sch in dep_options.items():
            import pprint
            pprint.pprint(dependencies)
            for lib in dependencies:
                print('lib', lib)
                for key, info in lib.items():
                    print('$', key, info)
                    if key == pkg:
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


            storage = storage or self.project.api.conan_storage_path
            with environment_append({'CONAN_STORAGE_PATH': storage}):
                recipe = conan.inspect(reference, [])


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

    def _options(self, package=False):
        return OptionsValues(self._options_items(package))

    @property
    def options(self):
        return self._options(False)

    @property
    def package_options(self):
        return self._options(True)

#    def as_list(self, package=False):
#        return OptionsValues(self._options_items(package)).as_list()


#class Scheme(object):
#
#    def __init__(self, name, project):
#
#        self.name = name[:-8] if name.endswith('@default') else name
#        self.project = project
#        self._profile = None
#        self._options = None
#
#    @property
#    def profile_(self):
#        if self._profile is None:
#            name, _ = split_plan_name(self.name)
#            if not name:
#                raise EException('Can not load profile with the empty profile name: %s' % name)
#            self._profile = Profile(name, self.profile.api.home_dir)
#
#            #self._profile = ProfileManager().profile(name)
#        return self._profile
#
#    @property
#    def profile(self):
#        if self._profile is None:
#            name, _ = parse_scheme_name(self.name)
#            if not name:
#                raise EException('Can not load profile with the empty profile name: %s' % name)
#
#            self._profile = Profile(name, self.project.api.home_dir)
#        return self._profile
#    @property
#    def options(self):
#        if self._options is None:
#            _, name = split_plan_name(self.name)
#            self._options = Options(name, self.project)
#        return self._options
#
#
#