import os
import pathlib
from collections import namedtuple
from string import Template
from epm.util import system_info

from epm.util.files import rmdir, mkdir, save, load_yaml, save_yaml

PLATFORM, ARCH = system_info()

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


class Project(object):

    def __init__(self, profile, scheme, api=None, directory='.'):
        """Project meta information class
        :param profile: the name of Profile
        :param scheme: the name of Scheme
        :param api:
        """
        self._profile_name = profile
        self._scheme_name = scheme
        self._scheme = None
        self._profile = None

        self._manifest = None
        self._conan_meta = None
        self._api = api
        self._conan_storage_path = None
        self.dir = pathlib.PurePath(os.path.abspath(directory)).as_posix()

    def initialize(self):
        rmdir(self.folder.out)
        mkdir(self.folder.out)
        self._generate_layout()

    def _generate_layout(self):
        manifest = self.manifest
        template = manifest.get('conan.layout', DEFALT_CONAN_LAYOUT)
        layout = Template(template)

        text = layout.substitute(out_dir=self.folder.out)
        with open(self.layout, 'w') as f:
            f.write(text)
            f.flush()

    def save(self, info={}):
        save_yaml(os.path.join(self.folder.out, 'buildinfo.yml'), info)

    @property
    def buildinfo(self):
        return load_yaml(os.path.join(self.folder.out, 'buildinfo.yml'))

    @property
    def api(self):
        if not self._api:
            from epm.api import API
            self._api = API()
        return self._api

    @property
    def name(self):
        return self.manifest['name']

    @property
    def version(self):
        return self.manifest['version']

    @property
    def group(self):
        return self.manifest['group']

    @property
    def channel(self):
        from epm.tool.conan import get_channel
        return get_channel(group=self.group)

    @property
    def reference(self):
        return '%s/%s@%s/%s' % (self.name, self.version, self.group, self.channel)

    @property
    def profile(self):
        if self._profile_name is None:
            return None
        if self._profile is None:
            from epm.model.profile import Profile
            print('------------------@', self._profile_name, __file__)
            print('==================',self.api.cache_dir)
            self._profile = Profile(self._profile_name, self.api.cache_dir)
        return self._profile

    @property
    def scheme(self):
        if self._scheme is None:
            from epm.model.scheme import Scheme
            self._scheme = Scheme(self._scheme_name, self)

        return self._scheme

    @property
    def folder(self):
        Folder = namedtuple('Folder', ['cache', 'out', 'build', 'package', 'test', 'name'])
        cache = '.epm'
        out = build = package = test = None
        basename = self._profile_name
        if self._scheme_name:
            assert basename
            if self._scheme_name and self._scheme_name not in ['default', 'None']:
                basename += '@%s' % self._scheme_name

        if basename:
            out = '%s/%s' % (cache, basename)
            build = '%s/build' % out
            package = '%s/package' % out
            test = '%s/test' % out

        return Folder(cache, out, build, package, test, basename)

    @property
    def layout(self):
        return '%s/conan.layout' % self.folder.out

    @property
    def manifest(self):
        if self._manifest is None:
            path = os.path.join(self.dir, 'package.yml')
            self._manifest = load_yaml(path)

        return self._manifest

    @property
    def tests(self):
        return self.manifest.get('tests', None)

    def generate_profile(self, force=False):
        filename = os.path.join(self.folder.out, 'profile')
        if not os.path.exists(filename):
            self.scheme.profile.save(filename)
        return filename




