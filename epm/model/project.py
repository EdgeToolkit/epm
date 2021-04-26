import os
import pathlib
from collections import namedtuple
from string import Template
import shutil
import yaml

from conans.tools import rmdir, mkdir

from epm.utils import conanfile_inspect
from epm.errors import EException

DEFALT_CONAN_LAYOUT = '''
[includedirs]
include

[builddirs]
${out_dir}/build

[libdirs]
${out_dir}/build/lib

[bindirs]
${out_dir}/build/bin

[resdirs]
${out_dir}/build/res
'''


class Record(object):
    _FILENAME = 'record.yaml'

    def __init__(self, project):
        self._project = project
        self._data = None
        self._filename = os.path.join(self._project.path.out, self._FILENAME)

    def get(self, name, default=None):
        if self._data is None:
            try:
                with open(self._filename) as f:
                    self._data = yaml.safe_load(f)
            except:
                pass
            self._data = self._data or {}

        return self._data.get(name, default)

    def set(self, key, value):
        if self.get(key) == value:
            return

        if value is None:
            if key in self._data:
                del self._data[key]
            else:
                return
        else:
            self._data[key] = value
        with open(self._filename, 'w') as f:
            yaml.safe_dump(self._data, f)


class Project(object):
    CONAN_PROFILE_BUILD = 'conan-profile_build'
    CONAN_PROFILE_HOST = 'conan-profile_host'
    MESON_CROSS_FILE = 'meson-cross.ini'

    def __init__(self, profile, scheme, api=None, directory='.'):
        """Project meta information class
        """
        self._api = api
        self._dir = os.path.normpath(os.path.abspath(directory))

        self._requirements = None

        self._scheme = None
        self._profile = None
        self._test = None
        self.__meta_information__ = {}
        self._conanfile_attributes = None

        self._conan_storage_path = None
        self._record = None
        self._dir = pathlib.PurePath(os.path.abspath(directory)).as_posix()

        manifest = os.path.join(self.dir, 'package.yml')
        if os.path.isfile(manifest):
            with open(manifest) as f:
                self.__meta_information__ = yaml.safe_load(f) or {}
                if 'version' in self.__meta_information__:
                    self.__meta_information__['version'] = str(self.__meta_information__['version'])


        mdata = self.__meta_information__ or {}
        mdata = mdata.get('scheme') or {}
        if not scheme or scheme.lower() in ['none', 'default', 'unkown']:
            scheme = None

        if scheme and scheme not in mdata:
            raise EException(f'Specified scheme <{scheme}> not defined. [{mdata}]')

        Attribute = namedtuple('Attribute', ['scheme', 'profile'])
        self.attribute = Attribute(scheme, profile)

        self._output_dir = mdata.get('output_directory') or '_out'
        self._paths = {}
        
        self.language = mdata.get('language') or None
        if not self.language:
            if os.path.exists(f"{self._dir}/go.mod"):
                self.language = 'go'
            else:
                self.language = 'c'

    @property
    def dir(self):
        return self._dir

    def setup(self):
        rmdir(self.path.out)
        mkdir(self.path.out)
        if self.language == 'go':
            return

        self._generate_layout()

        shutil.copy(self.profile.path.host, self.abspath.profile_host)
        shutil.copy(self.profile.path.build, self.abspath.profile_build)

    def _generate_layout(self):
        manifest = self.__meta_information__ or dict()
        template = manifest.get('conan.layout', DEFALT_CONAN_LAYOUT)
        layout = Template(template)

        text = layout.substitute(out_dir=self.path.out)
        with open(self.layout, 'w') as f:
            f.write(text)
            f.flush()

    @property
    def record(self):
        if self._record is None:
            self._record = Record(self)
        return self._record

    @property
    def api(self):
        if not self._api:
            from epm.api import API
            self._api = API()
        return self._api

    def _minfo(self, *args):
        m = self.__meta_information__ or dict()
        n = len(args)
        for k in args:
            n -= 1
            if isinstance(m, dict):
                m = m.get(k)
                continue
        return m if n == 0 else None

    @property
    def metainfo(self):
        return self.__meta_information__ or {}

    @property
    def name(self):
        return self._minfo('name')

    @property
    def version(self):
        return str(self._minfo('version'))

    @property
    def user(self):
        user = self._minfo('user')
        if not user:
            user = os.getenv('EPM_USER') or None
        return user

    @property
    def channel(self):
        channel = self._minfo('channel')
        if not channel:
            from epm.tools import get_channel
            channel = get_channel(user=self.user)
        return channel

    @property
    def reference(self):
        from conans.model.ref import ConanFileReference
        return ConanFileReference(self.name, self.version, self.user, self.channel)

    @property
    def scheme(self):
        if self._scheme is None:
            from epm.model.scheme import Scheme
            self._scheme = Scheme(self)

        return self._scheme

    def _get_paths(self, absolute=False, posix=False):
        root = '.'
        cache= self._output_dir
        out = build = package = test = basename = None
        profile_host = profile_build = program = None
        if self.attribute.profile:
            scheme = self.attribute.scheme or 'none'
            basename = "{}/{}".format(self.attribute.profile, scheme)

        def _join(base, x):
            x = os.path.join(base, x)
            if absolute:
                x = os.path.normpath(os.path.join(self._dir, x))
            if posix:
                x = pathlib.PurePath(x).as_posix()
            return x

        if basename:
            out = _join(cache, basename)
            build = _join(out, 'build')
            package = _join(out, 'package')
            profile = _join(out, 'profile')
            program = _join(out, 'program')
            sandbox = _join(out, 'sandbox')
            profile_host = _join(out,  Project.CONAN_PROFILE_BUILD)
            profile_build = _join(out, Project.CONAN_PROFILE_HOST)

        Path = namedtuple('Path', ['root', 'cache', 'out', 
               'build', 'package', 'program', 'sandbox',
               'profile_host', 'profile_build'])
        return Path(root, cache, out, build, package, program, sandbox, profile_host, profile_build)

    @property
    def path(self):
        if 'path' not in self._paths:
            self._paths['path'] = self._get_paths()
        return self._paths['path']

    @property
    def abspath(self):
        if 'abspath' not in self._paths:
            self._paths['abspath'] = self._get_paths()
        return self._paths['abspath']

    @property
    def layout(self):
        return '%s/conan.layout' % self.path.out

    @property
    def conanfile_attributes(self):
        if self._conanfile_attributes is None:
            self._conanfile_attributes = conanfile_inspect(os.path.join(self.dir, 'conanfile.py'))
        return self._conanfile_attributes

    @property
    def profile(self):
        if self._profile is None:
            from epm.model.profile import Profile
            self._profile = Profile(self.attribute.profile, self.api.workbench_dir)
        return self._profile
    
    @property
    def test(self):
        if self._test is None:
            self._test = self._parse_test()
        return self._test
    def _parse_test(self):
        result = {}
        config = self.metainfo.get('test') or {}
        for name, conf in config.items():
            conf = conf or dict()
            assert isinstance(conf, dict)
            project = conf.get('project') or None
            program = name
            if 'program' in config:
                program = conf['program'] or ''
                if program.lower() in ['', 'null', 'none']:
                    program = None

            args = conf.get('args') or ''
            description = conf.get('description') or ''
            pattern= conf.get('pattern') or None
            if isinstance(pattern, str):
                patterns = [pattern]

            if pattern and not isinstance(path, list):
                raise SyntaxError(f'invalid type of program.pattern defined {pattern}.')

            result[name] = namedtuple("Test", "name project program args description pattern")(
                name, project, program, args, description, pattern)
        return result

    @property
    def available(self):
        """ TODO: check the `profile` `scheme` compose is available for build

        :return:
        """
        
        return True


