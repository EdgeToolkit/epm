import re
import os
import yaml
from .generators.pkg_config import PkgConfigGenerator
from conans import ConanFile


from epm.tools import get_channel, create_requirements, add_build_requirements
from epm.utils.mirror import Mirror


generator_classes = {'pkg-config.legacy': PkgConfigGenerator}


def _conanfile_hacking(minfo, generator):
    name = minfo['name']

    mirror = Mirror.load()
    if mirror:
        mirror.register(name)


def MetaClass(ConanFileClass=None, manifest=None, test_package=False, generator=None):

    manifest = manifest or '../package.yml' if test_package else 'package.yml'
    with open(manifest) as f:
        minfo = yaml.safe_load(f)

    name = minfo.get('name')
    version = str(minfo.get('version'))
    user = minfo.get('user')
    channel = minfo.get('channel') or get_channel(user)
    exports = [manifest]
    ClassName = re.sub(r'\W', '_', os.path.basename(os.path.normpath(os.path.abspath(manifest))))
    ConanFileClass = ConanFileClass or ConanFile

    _conanfile_hacking(minfo, generator)

    member = dict(name=name, version=version, __meta_information__=minfo)
    if test_package:
        folder = os.path.basename(os.path.abspath('.'))
        ClassName = '{}_TestPackage_{}'.format(re.sub(r'\W', '_', folder), ClassName)

        requires = ('%s/%s@%s/%s' % (name, version,
                                     user or '_',
                                     channel or '_'))
        member['name'] += '_{}'.format(folder)
        member['requires'] = requires
        # workaround
        member['options'] = {"shared": [True, False]}
        member['default_options'] = {"shared": False}

        CoanFileEx = ConanFileClass

    else:
        member['exports'] = exports

        class CoanFileEx(ConanFileClass):

            def requirements(self):
                self.requires = create_requirements(self.__meta_information__,
                                                    self.settings,
                                                    self.options,
                                                    conanfile=self)

            def build_requirements(self):
                add_build_requirements(self.build_requires, self.__meta_information__,
                                       self.settings, self.options,
                                       conanfile=self)

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
