import re
import os
import yaml
import copy
import uuid

from .generators.pkg_config import PkgConfigGenerator

from conans import ConanFile


from epm.tools import get_channel, create_requirements, add_build_requirements
from epm.utils.mirror import Mirror

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
        except Exception as e:
            print(e)
            import traceback
            traceback.print_tb(e.__traceback__)
            
    
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
    test = meta.get('test') or {}
    if name not in test:
        raise Exception(f"test {name} not defained in package.yml, please check `test` section" )

    program = test[name] or {}

    package_name = origin['name']
    version = origin['version']
    meta['name'] = name
 
    dependencies = {}
    if 'dependencies' not in program:
        dependencies[package_name] = version
    elif isinstance(program['dependencies'], dict):
            dependencies = program['dependencies']
    build_tools = program.get('build-tools') or {}
            
    meta['dependencies'] = dependencies
    meta['build-tools'] = build_tools
    try:
        del meta['test']
    except:
        pass
    return meta


def as_test(klass):
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
as_program = as_test

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

def append_test(fn):
    def _wrapper(self, *args):
        fn(self, *args)
        ftest = getattr(self, 'test', None)
        if ftest:
            self.output.highlight('+Calling test()')
            ftest()
        return None
    return _wrapper