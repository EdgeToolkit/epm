import os
import pathlib
from collections import namedtuple
from string import Template
from epm.util import system_info
import yaml
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


class Record(object):
    _FILENAME = 'record.yaml'

    def __init__(self, project):
        self._project = project
        self._data = None

    def get(self, name, default=None):
        if self._data is None:
            path = os.path.join(self._project.folder.out, Record._FILENAME)
            if os.path.exists(path):
                with open(path, 'r') as f:
                    self._data = yaml.safe_load(f)
            self._data = dict()
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
        path = os.path.join(self._project.folder.out, Record._FILENAME)
        with open(path, 'w') as f:
            yaml.dump(self._data, f)

from collections import namedtuple

class Project(object):

    def __init__(self, profile, scheme, api=None, directory='.'):
        """Project meta information class
        :param profile: the name of Profile
        :param scheme: the name of Scheme
        :param api:
        """
        #self._profile_name = profile
        #self._scheme_name = scheme
        self._api = api
        self._dir = pathlib.PurePath(os.path.abspath(directory)).as_posix()

        self._scheme = None
        self._profile = None
        self.__meta_information__ = None

        #self._manifest = None # to be replaced by metainfo
        #self._metainfo = None
        #self._conan_meta = None

        self._conan_storage_path = None
        self._record = None
        self._dir = pathlib.PurePath(os.path.abspath(directory)).as_posix()
        Attribute = namedtuple('Attribute', ['profile', 'scheme'])
        self.attribute = Attribute(profile, scheme)
        self.__meta_information__ = load_yaml(os.path.join(self.dir, 'package.yml'))

    @property
    def dir(self):
        return self._dir

    def initialize(self):
        rmdir(self.folder.out)
        mkdir(self.folder.out)
        self._generate_layout()

    def _generate_layout(self):
        manifest = self.__meta_information__ or dict()
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
        value = None
        m = self.__meta_information__ or dict()
        n = len(args)
        for k in args:
            n -= 1
            if isinstance(m, dict):
                m = m.get(k)
                continue
        return m if n == 0 else None

    @property
    def name(self):
        return self._minfo('name')

    @property
    def version(self):
        return self._minfo('version')

    @property
    def user(self):
        return self._minfo('user')

    @property
    def channel(self):
        from epm.tools.conan import get_channel
        return get_channel(user=self.user)

    @property
    def reference(self):
        from conans.model.ref import ConanFileReference
        return ConanFileReference(self.name, self.version, self.user, self.channel)

    @property
    def profile(self):
        if self.attribute.profile is None:
            return None
        if self._profile is None:
            from epm.model.profile import Profile
            self._profile = Profile(self.attribute.profile, self.api.workbench_dir)
        return self._profile

    @property
    def scheme(self):
        if self._scheme is None:
            from epm.model.scheme import Scheme
            self._scheme = Scheme(self)

        return self._scheme

    @property
    def folder(self):
        Folder = namedtuple('Folder', ['cache', 'out', 'build', 'package', 'test', 'name'])
        cache = '.epm'
        out = build = package = test = None
        basename = self.attribute.profile
        scheme = self.attribute.scheme
        if scheme and scheme not in ['default', 'None']:
            basename += '@%s' % scheme

        if basename:
            out = '%s/%s' % (cache, basename)
            build = '%s/build' % out
            package = '%s/package' % out
            test = '%s' % out

        return Folder(cache, out, build, package, test, basename)

    @property
    def layout(self):
        return '%s/conan.layout' % self.folder.out
