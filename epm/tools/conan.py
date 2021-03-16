import re
import os
import yaml
import copy
import uuid

from .generators.pkg_config import PkgConfigGenerator

from conans import ConanFile


from epm.tools import get_channel, create_requirements, add_build_requirements
from epm.utils.mirror import Mirror


generator_classes = {'pkg-config.legacy': PkgConfigGenerator}

#
#def _conanfile_hacking(minfo, generator=None):
#    name = minfo['name']
#
#    mirror = Mirror.load()
#    if mirror:
#        mirror.register(name)


def _ConanfileEx(klass):

    class _Klass(klass):

        def requirements(self):
            self.requires = create_requirements(self.__meta_information__,
                                                self.settings,
                                                self.options,
                                                conanfile=self)

        def build_requirements(self):
            add_build_requirements(self.build_requires, self.__meta_information__,
                                   self.settings, self.options,
                                   conanfile=self)
    return _Klass


def _load_manifest(filename):
    with open(filename) as f:
        minfo = yaml.safe_load(f)
        minfo['version'] = str(minfo['version'])
    return minfo

def _mirror():
    rule = os.getenv('EPM_MIRROR_RULES')
    if rule:
        try:
            mirorr = Mirror(rule)
            mirorr.hack_conan_download()
        except:
            
    
def as_package(klass):
    manifest = 'package.yml'

    if not os.path.exists(manifest):
        raise Exception('Invalid program directory (miss package.yml)')

    minfo = _load_manifest(manifest)

    name = minfo['name']
    version = minfo['version']
    exports = [manifest]
    class_name = "{}-{}".format(name, uuid.uuid4())

    _mirror()

    member = dict(name=name, version=version, exports=exports,
                  __meta_information__=minfo)

    klass = _ConanfileEx(klass)

    return type(class_name, (klass,), member)


def _make_program_metainfo(name, origin):
    program = None
    meta = copy.deepcopy(origin)
    for i in meta['program']:
        if i['name'] == name:
            program = i
            break

    package_name = origin['name']
    version = origin['version']
    meta['name'] = name

    dependencies = meta.get('dependencies') or {}
    dependencies[package_name] = version
    meta['dependencies'] = dependencies

    build_tools = meta.get('build-tools') or {}
    build_tools.update(program.get('build-tools') or {})
    meta['build-tools'] = build_tools
    return meta


def as_program(klass):
    name = os.getenv('EPM_PROGRAM_NAME')
    directory = os.getenv('EPM_PROJECT_DIRECTORY')
    manifest = os.path.join(directory, 'package.yml')

    if not name:
        raise Exception('EPM_PROGRAM_NAME env not defined.')
    if not directory:
        raise Exception('EPM_PROJECT_DIRECTORY env not defined.')
    if not os.path.exists(manifest):
        raise Exception('Invalid program directory (miss package.yml)')

    __meta_information__ = _load_manifest(manifest)

    minfo = _make_program_metainfo(name, __meta_information__)

    version = str(__meta_information__.get('version'))
    class_name = "{}-{}".format(name, uuid.uuid4())

    _mirror()
    
    member = dict(name=name, version=version, __meta_information__=minfo)

    # workaround
    member['options'] = {"shared": [True, False]}
    member['default_options'] = {"shared": False}

    klass = _ConanfileEx(klass)

    return type(class_name, (klass,), member)


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
