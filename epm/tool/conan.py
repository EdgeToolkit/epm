from epm.tools import conan as _conan
from epm.tools.conan import get_channel

Packager = _conan.Packager
TestPackager = _conan.TestPackager

import os
import re
from conans import ConanFile as _ConanFile
from epm.model.config import MetaInformation
from epm.util.mirror import Mirror, register_mirror


class MetaInfo(object):

    def __init__(self, metainfo, conanfile):
        self._metainfo = metainfo
        self._conanfile = conanfile

    @property
    def dependencies(self):
        return self._metainfo.get_requirements(self._conanfile.settings)


class Helper(object):

    @property
    def metainfo(self):
        return MetaInfo(self._META_INFO, self)


def MetaClass(ConanFileClass=None, manifest=None, test_package=False):

    manifest = manifest or '../package.yml' if test_package else 'package.yml'
    try:
        metainfo = MetaInformation(manifest)
        print(metainfo)
    except BaseException as e:
        print('==============================================')
        print(e)
    name = metainfo.name
    version = metainfo.version
    user = metainfo.user
    exports = [manifest]
    ClassName = re.sub(r'\W', '_', os.path.basename(os.path.normpath(os.path.abspath(manifest))))
    ConanFileClass = ConanFileClass or _ConanFile

    mirror = Mirror.load()
    if mirror:

        mirror.register(name)

    member = dict(name=name, version=version, _META_INFO=metainfo)
    if test_package:
        folder = os.path.basename(os.path.abspath('.'))
        ClassName = '{}_TestPackage_{}'.format(re.sub(r'\W', '_', folder), ClassName)

        requires = ('%s/%s@%s/%s' % (name, version,
                                     user or '_',
                                     get_channel(user) or '_'))
        member['name'] += '-{}'.format(folder)
        member['requires'] = requires
    else:
        member['exports'] = exports

    return type(ClassName, (Helper, ConanFileClass), member)
