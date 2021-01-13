import re
import os
import yaml
from .generators.pkg_config import PkgConfigGenerator
from conans import ConanFile


from epm.tools import get_channel, create_requirements, add_build_requirements
from epm.utils.mirror import Mirror


generator_classes = {'pkg-config.legacy': PkgConfigGenerator}


def _conanfile_hacking(minfo, generator=None):
    name = minfo['name']

    mirror = Mirror.load()
    if mirror:
        mirror.register(name)


def MetaClass(ConanFileClass=None, manifest=None, test_package=False, generator=None):

    manifest = manifest or '../package.yml' if test_package else 'package.yml'
    if os.environ.get('EPM_PROGRAM_NAME'):
        test_package = True
        manifest = os.path.join(os.getenv('EPM_PROJECT_DIRECTORY'), 'package.yml')

    print('EPM_PROGRAM_NAME', os.environ.get('EPM_PROGRAM_NAME'))
    print('test_package', test_package)

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
        print('+++++++++++++++++++++++')
        print(member)

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

from epm.utils import abspath
import copy
import uuid

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


def as_package(klass):
    manifest = 'package.yml'

    if not os.path.exists(manifest):
        raise Exception('Invalid program directory (miss package.yml)')

    with open(manifest) as f:
        minfo = yaml.safe_load(f)

    name = minfo['name']
    version = minfo['version']
    exports = [manifest]
    class_name = "{}-{}".format(name, uuid.uuid4())
    #class_name = re.sub(r'\W', '_', class_name)

    _conanfile_hacking(minfo)

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
    import pprint
    pprint.pprint(meta)
    print('--------------------------------------------------------')
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

    with open(manifest) as f:
        __meta_information__ = yaml.safe_load(f)
    minfo = _make_program_metainfo(name, __meta_information__)

    version = str(__meta_information__.get('version'))
    class_name = "{}-{}".format(name, uuid.uuid4())
#    class_name = re.sub(r'\W', '_', class_name)

    _conanfile_hacking(minfo)

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
