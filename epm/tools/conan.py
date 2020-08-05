import re
import os
import pathlib

from conans.client.tools.env import environment_append, no_op
from conans.client.build.meson import Meson as _Meson
from conans.client.generators.pkg_config import PkgConfigGenerator as _PkgConfigGenerator
from conans import ConanFile
from conans.client.generators import registered_generators

from epm.enums import Platform
from epm.tools import get_channel, create_requirements, add_build_requirements
from epm.utils import PLATFORM, load_yaml
from epm.utils.mirror import Mirror

def MetaClass(ConanFileClass=None, manifest=None, test_package=False):

    manifest = manifest or '../package.yml' if test_package else 'package.yml'
    minfo = load_yaml(manifest)

    name = minfo.get('name')
    version = str(minfo.get('version'))
    user = minfo.get('user')
    exports = [manifest]
    ClassName = re.sub(r'\W', '_', os.path.basename(os.path.normpath(os.path.abspath(manifest))))
    ConanFileClass = ConanFileClass or ConanFile

    mirror = Mirror.load()

    if mirror:
        mirror.register(name)
    #registered_generators.add('pkg_config', PkgConfigGenerator, custom=True)

    member = dict(name=name, version=version, __meta_information__=minfo)
    if test_package:
        folder = os.path.basename(os.path.abspath('.'))
        ClassName = '{}_TestPackage_{}'.format(re.sub(r'\W', '_', folder), ClassName)

        requires = ('%s/%s@%s/%s' % (name, version,
                                     user or '_',
                                     get_channel(user) or '_'))
        member['name'] += '-{}'.format(folder)
        member['requires'] = requires

        CoanFileEx = ConanFileClass

    else:
        member['exports'] = exports

        class CoanFileEx(ConanFileClass):

            def requirements(self):
                self.requires = create_requirements(self.__meta_information__,
                                                    self.settings,
                                                    self.options)

            def build_requirements(self):
                add_build_requirements(self.build_requires, self.__meta_information__, self.settings, self.options)


    return type(ClassName, (CoanFileEx,), member)

def delete(fn):
    def _wrapper(self, *args):
        this = super(self.__class__, self)
        f = getattr(this, fn.__name__, None)
        return None if f is None else f(*args)
    return _wrapper


def replace(fn, new_fn):
    def _wrapper(self, *args):

        if callable(new_fn):
            return new_fn(self, *args)
        elif isinstance(new_fn, str):
            f = getattr(self, new_fn, None)
            return None if f is None else f(*args)
        else:
            raise Exception('Invalid new_fn (%s) to replace %s' % (type(new_fn), fn.__name__))
    return _wrapper


class Meson(_Meson):

    def _run(self, command):
        pc_paths = None
        if PLATFORM == Platform.WINDOWS:
            from conans.client.tools.win import unix_path, MSYS2
            pc_paths = os.getenv("PKG_CONFIG_PATH") or None
            if pc_paths:
                pc_paths = unix_path(paths, MSYS2)

        with environment_append({"PKG_CONFIG_PATH":pc_paths}) if not pc_paths else no_op():
            super(Meson, self)._run(command)


class PkgConfigGenerator(_PkgConfigGenerator):
    
    @property
    def content(self):
        ret = {}

        for depname, cpp_info in self.deps_build_info.dependencies:
            pc_files = []
            for i in cpp_info.libdirs:
                path = os.path.join(cpp_info.rootpath, i, 'pkgconfig')
                import glob
                pc_files += glob.glob('%s/*.pc' % path)

            if not pc_files:
                pc_files = glob.glob('%s/pkgocnfig/*.pc' % cpp_info.rootpath)

            if pc_files:

                for pc in pc_files:
                    name = os.path.basename(pc)
                    with open(pc) as f:
                        txt = f.read()
                    line = 'prefix=%s' % pathlib.PurePath(cpp_info.rootpath).as_posix()

                    ret[name] = re.sub(r'prefix=.+', line, txt, 1)
            else:
                name = cpp_info.get_name(PkgConfigGenerator.name)
                ret["%s.pc" % name] = self.single_pc_file_contents(name, cpp_info)

        return ret
