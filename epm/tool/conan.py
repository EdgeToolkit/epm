from epm.errors import EException
from epm.tools.conan import get_channel
from epm.util import conanfile_inspect
from epm.util import load_yaml
from conans.client.generators import registered_generators


import os
import re
from conans import ConanFile
from conans.model.requires import Requirement
from conans.model.ref import ConanFileReference


from epm.util.mirror import Mirror, register_mirror
from conans.client.conan_api import ConanAPIV1 as ConanAPI


def If(expr, settings, options):
    if not expr:
        return True
    vars = {'options': options}
    for k, v in settings.items():
        vars[k] = v

    return eval(expr, {}, vars)


def create_requirements(minfo, settings=None, options=None):
    ''' create requirements (conan reference order dict name: reference)

    :param minfo: meta information dict
    :param settings:
    :param options:
    :return:
    '''
    requires = Requirement()
    if not minfo:
        return requires
    any = settings is None and options is None
    packages = minfo.get('dependencies') or []
    for package in packages:
        assert isinstance(attr, dict)
        for name, attr in package.items():
            if isinstance(attr, str):
                requires.add(attr)
            else:
                assert isinstance(attr, dict)
                if any or If(attr.get('if', settings, options)):
                    version = attr['version']
                    user = attr.get('user')
                    channel = attr.get('channel')
                    ref = ConanFileReference(name, version, user, channel)
                    requires.add_ref(ref)
    return requires

def create_options(minfo, scheme, settings, default_options):
    pass

def MetaClass(ConanFileClass=None, manifest=None, test_package=False):

    manifest = manifest or '../package.yml' if test_package else 'package.yml'
    minfo = load_yaml(manifest)

    name = minfo.get('name')
    version = minfo.get('version')
    user = minfo.get('user')
    exports = [manifest]
    ClassName = re.sub(r'\W', '_', os.path.basename(os.path.normpath(os.path.abspath(manifest))))
    ConanFileClass = ConanFileClass or ConanFile

    mirror = Mirror.load()
    if mirror:
        mirror.register(name)
    registered_generators.add('pkg_config', PkgConfigGenerator, custom=True)

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
                self.requires = create_requirements()

    return type(ClassName, CoanFileEx, member)


def delete(fn):
    def _wrapper(self, *args):
        this = super(self.__class__, self)
        getattr(this, fn.__name__)(*args)
    return _wrapper


######################### MESON HACK #################################
import os
from conans.client.tools.env import environment_append, no_op


from epm.enums import Platform
from epm.util import system_info
from conans.client.build.meson import Meson as _Meson

PLATFORM, ARCH = system_info()

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



############################ PKG-CONFIG ########################################
from conans.client.generators.pkg_config import PkgConfigGenerator as _PkgConfigGenerator

import pathlib


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
