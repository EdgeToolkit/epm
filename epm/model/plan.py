import os
import yaml
import pprint
import copy
import glob
import shutil

from conans.model.options import OptionsValues

from epm.errors import EException
from epm.paths import DATA_DIR, get_epm_user_home
from epm.util.files import load_yaml
from epm.util import split_plan_name

from collections import OrderedDict, namedtuple


class Profile(object):
    """ Specific profile

    """

    def __init__(self, meta):
        self.name = meta['name']
        self.family = meta['family']
        self.description = meta['description']
        self.type = meta['type']
        self.settings = meta['settings']
        self._meta = meta

    @property
    def docker(self):

        Docker = namedtuple('Docker', ['builder', 'runner'])

        runner = self._meta.get('docker', {}).get('runner', None)
        builder = self._meta.get('docker', {}).get('builder', None)
        return Docker(builder, runner)


class Scheme(object):

    def __init__(self, name, project):
        self._name = name
        self._scheme = None  # options name
        self._api = None
        self.project = project

    @property
    def name(self):
        return self._name

    @property
    def options(self):
        return self._options(False)

    @property
    def link_options(self):
        return self._options(True)

    @property
    def api(self):
        if self._api is None:
            self._api = self.project.api
        return self._api

    def _parse(self, name, manifest=None):
        ''' parse the package (manifest) scheme (options) information

        :param name: name of scheme to be parsed
        :param manifest: manifest (package.yml)
        :return:
        '''

        manifest = manifest or self.project.manifest
        plan = manifest.get('plan', {})
        scheme = plan.get('scheme', {}).get(name, {})
        dependencies = manifest.get('dependencies', {})

        # pick up options of this package.yml
        options = {k: v for k, v in scheme.items() if k[0] != '.'}
        deps = {}

        for pkg, sch in scheme.get('.dependencies', {}).items():

            info = dependencies.get(pkg)  # get dependent package info
            if not info:
                raise EException('less information of %s, miss dependencies in package.yml ' % name)

            deps[pkg] = {**info, 'scheme': sch}

        return options, deps

    def _load_dep_schemes(self, libs, deps, storage=None):

        for name, info in deps.items():
            if name in libs.keys():
                continue

            scheme = info['scheme']
            version = info['version']
            user = info['user']

            channel = info.get('channel', 'stable')

            conan = self.api.conan
            reference = '%s/%s@%s/%s' % (name, version, user, channel)
            recipe = conan.inspect(reference, [], user)
            storage = storage or self.project.conan_storage_path
            path = os.path.join(storage, name, version, user, channel, 'export', 'package.yml')

            manifest = load_yaml(path)

            options, deps = self._parse(scheme, manifest)

            libs[name] = {'manifest': manifest, 'recipe': recipe, 'options': options, 'scheme.deps': deps}

#            log.info('scheme of {} reference={} loaded: \n{}'.format(
#                name, reference, pprint.pformat(libs[name], indent=2)))

            self._load_dep_schemes(libs, deps, storage)

    def _options(self, link):
#        log.info('{} scheme.option link={}'.format(self._name, link))

        options, deps = self._parse(self.name)
        libs = {}
        self._load_dep_schemes(libs, deps)

        items = {}
        for k, v in options.items():
            key = '%s:%s' % (self.project.name, k) if link else k
            items[key] = v

        for name, info in libs.items():
            for k, v in info['options'].items():
                key = '%s:%s' % (name, k)
                items[key] = v

#        log.info('{} scheme.options link={}\n{}'.format(self._name, link, pprint.pformat(items, indent=2)))
        return OptionsValues(items)


class ProfileManager(object):

    def __init__(self, folder=None, init=True):
        """

        :param folder: EPM cache folder where
        :param init: if profile folder is empty install default profiles
        """
        self.folder = folder or os.path.join(get_epm_user_home(), '.epm', 'profiles')
        self.families = {}
        if init:
            self._initialize()
        self._load()

    def _load(self):
        for filename in glob.glob('{}/*.yml'.format(self.folder)):
            families = self.parse(filename)

        for name, family in families.items():
            if name in self.families:
                raise EException('%s duplicated defined' % name)

            for sname, spec in family.items():
                if sname in self.specs:
                    raise EException('%s duplicated defined' % sname)
            self.families[name] = family

    @property
    def specs(self):
        specs = {}
        for _, spec in self.families.items():
            specs = dict(specs, **spec)
        return specs

    def metadata(self, name):
        """get the sepc profile meta data

        :param name:
        :return:
        """
        return self.specs.get(name)

    def profile(self, name):
        meta = self.specs.get(name)
        if not meta:
            raise EException('The spec profile %s not exists.' % name)
        return Profile(meta)

    def _initialize(self):
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
        profiles = glob.glob('{}/*.yml'.format(self.folder))
        if not profiles:
            for filename in ['windows.yml', 'linux.yml']:
                shutil.copy(os.path.join(DATA_DIR, 'default_profiles', filename),
                            os.path.join(self.folder, filename))

    @staticmethod
    def _assembly_scheme(items):
        result = OrderedDict()
        for it in items:
            if isinstance(it, list):
                for i in it:
                    assert (isinstance(i, dict))
                    assert (len(i) == 1)
                    result.update(i)
            elif isinstance(it, dict):
                assert (len(it) == 1)
                result.update(it)
        return result

    @staticmethod
    def _assembly(items, scheme):
        assert (isinstance(scheme, OrderedDict))
        assert (isinstance(items, (dict, OrderedDict)))
        expect = set(scheme.keys())
        actual = set(items.keys())

        diff = expect.difference(actual)
        if diff:
            i = expect.intersection()
            missing = expect.difference(i)
            illegal = actual.difference(i)
            raise EException('Bad spec profile fields. {} {}'.format(
                "missing: {}".format(",".join(missing)) if missing else ' ',
                "illegal: {}".format(",".join(illegal)) if illegal else ' '))
        result = copy.copy(scheme)

        for name, value in items.items():

            if value not in scheme[name]:
                raise EException('illegal spec profile value {}, should be: {}'.format(
                    value, ",".join(scheme[name])))
            result[name] = value
        return result

    @staticmethod
    def parse(filename):
        meta = load_yaml(filename)
        schema = meta['.schema']
        families = {}

        for name, profile in meta.items():
            docker = {}
            if name == '.docker':
                docker = profile

            if name.startswith('.'):
                continue

            specs = {}
            settings = schema[profile['.scheme']]['settings']
            scheme = ProfileManager._assembly_scheme(settings)

            for type, spec in profile.items():
                description = None
                if type == '.description':
                    description = spec

                if type.startswith('.'):
                    continue

                sname = spec['name']
                assert (sname not in specs)

                try:
                    settings = ProfileManager._assembly(spec['settings'], scheme)
                except EException as e:
                    msg = str(e) + ' spec={}'.format(sname)
                    raise EException(msg)

                specs[sname] = {'type': type,
                                'name': sname,
                                'family': name,
                                'docker': docker,
                                'description': description,
                                '__file__': filename,
                                'settings': settings
                                }

            families[name] = specs

        return families


class Plan(object):

    def __init__(self, name, project):
        if name.endswith('@default'):
            name = name.replace('@default', '')
        self.name = name
        self.project = project
        self._profile = None
        self._scheme = None

    @property
    def profile(self):
        if self._profile is None:
            name, _ = split_plan_name(self.name)
            if not name:
                raise EException('Can not load profile with the empty profile name: %s' % name)

            self._profile = ProfileManager().profile(name)
        return self._profile

    @property
    def scheme(self):
        if self._scheme is None:
            _, name = split_plan_name(self.name)
            self._scheme = Scheme(name, self.project)
        return self._scheme


