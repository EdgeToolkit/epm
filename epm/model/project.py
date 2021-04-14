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
        self._filename = os.path.join(self._project.folder.out, self._FILENAME)

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
        self.__meta_information__ = {}
        self._conanfile_attributes = None

        self._conan_storage_path = None
        self._record = None
        self._dir = pathlib.PurePath(os.path.abspath(directory)).as_posix()

        try:
            with open(os.path.join(self.dir, 'package.yml')) as f:
                self.__meta_information__ = yaml.safe_load(f) or {}
                if 'version' in self.__meta_information__:
                    self.__meta_information__['version'] = str(self.__meta_information__['version'])
        except:
            pass

        mdata = self.__meta_information__ or {}
        mdata = mdata.get('scheme') or {}
        if scheme in ['none', 'None', 'NONE'] or not scheme:
            scheme = None

        if scheme and scheme not in mdata:
            raise EException(f'Specified scheme <{scheme}> not defined. [{mdata}]')

        Attribute = namedtuple('Attribute', ['scheme', 'profile'])
        self.attribute = Attribute(scheme, profile)
        
    @property
    def dir(self):
        return self._dir

    def setup(self):
        rmdir(self.folder.out)
        mkdir(self.folder.out)
        self._generate_layout()

        shutil.copy(self.profile.path.host, self.abspath.profile_host)
        shutil.copy(self.profile.path.build, self.abspath.profile_build)

    def _generate_layout(self):
        manifest = self.__meta_information__ or dict()
        template = manifest.get('conan.layout', DEFALT_CONAN_LAYOUT)
        layout = Template(template)

        text = layout.substitute(out_dir=self.folder.out)
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

    @property
    def folder(self):
        """
        .cache: .epm
        .name:  <profile>@<scheme>
        .program: .epm/<profile>@<scheme>/program
        .package: .epm/<profile>@<scheme>/package
        .build: .epm/<profile>@<scheme>/build
        :return:
        """
        Folder = namedtuple('Folder', ['cache', 'out', 'build', 'package', 'test', 'name', 'program'])
        cache = '.epm'
        out = build = package = test = program = None
        basename = self.attribute.profile
        scheme = self.attribute.scheme
        if scheme and scheme not in ['default', 'None']:
            basename += '@%s' % scheme

        if basename:
            out = '%s/%s' % (cache, basename)
            build = '%s/build' % out
            package = '%s/package' % out
            test = '%s/test' % out
            program = '%s/program' % out

        return Folder(cache, out, build, package, test, basename, program)

    def _make_path(self, posix=True, absolute=True):
        """
        """
        Path = namedtuple('Path', ['root', 'cache', 'out', 'build', 'package', 'profile', 'build_profile',
                                   'profile_host', 'profile_build', 'cross_file', 'program'
                                   ])
        root = '.'
        cache = '.epm'
        out = build = package = test = None
        basename = self.attribute.profile
        scheme = self.attribute.scheme

        def _(x):
            if absolute:
                x = os.path.normpath(os.path.join(self._dir, x))
            if posix:
                x = pathlib.PurePath(x).as_posix()
            return x

        if isinstance(scheme, str):
            basename += '@%s' % scheme

        profile = build_profile = profile_host = profile_build = cross_file = program = None

        if basename:
            out = _(os.path.join(cache, basename))
            build = _(os.path.join(out, 'build'))
            package = _(os.path.join(out, 'package'))
            profile = _(os.path.join(out, 'profile'))
            program = _(os.path.join(out, 'program'))
            build_profile = _(os.path.join(out, 'build_profile'))


            profile_host = _(os.path.join(out,  Project.CONAN_PROFILE_BUILD))
            profile_build = _(os.path.join(out, Project.CONAN_PROFILE_HOST))
            cross_file = _(os.path.join(out, Project.MESON_CROSS_FILE))

        return Path(root, cache, out, build, package, profile, build_profile,
                    profile_host, profile_build, cross_file, program)

    @property
    def path(self):
        return self._make_path(False, False)

    @property
    def path_posix(self):
        return self._make_path(True, False)

    @property
    def abspath(self):
        return self._make_path(False, True)

    @property
    def abspath_posix(self):
        return self._make_path(True, True)

    @property
    def layout(self):
        return '%s/conan.layout' % self.folder.out

    @property
    def conanfile_attributes(self):
        if self._conanfile_attributes is None:
            self._conanfile_attributes = conanfile_inspect(os.path.join(self.dir, 'conanfile.py'))
        return self._conanfile_attributes

#    @property
#    def test_packages(self):
#        tests = self.__meta_information__.get('test_package') or []
#
#        if not tests and os.path.exists('test_package/conanfile.py'):
#            tests = ['test_package']
#        return tests

    @property
    def profile(self):
        if self._profile is None:
            from epm.model.profile import Profile
            self._profile = Profile(self.attribute.profile, self.api.workbench_dir)
        return self._profile

    @property
    def available(self):
        """ TODO: check the `profile` `scheme` compose is available for build

        :return:
        """
        
        return True


