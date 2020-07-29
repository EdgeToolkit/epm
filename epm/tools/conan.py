import os
import yaml
from conans.model.ref import ConanFileReference, get_reference_fields
import re
import pathlib
from conans import ConanFile
from epm.model.config import MetaInformation
from epm.util.mirror import Mirror,register_mirror
from epm.util import symbolize

def get_channel(user=None, channel=None):

    if not user:
        if channel is None:
            return None
        raise Exception('No `user` defined with channel defined (%s) not allowed.' % channel)

    def _(x):
        from epm.util import symbolize
        return symbolize('_' + x.upper())
    keys = ['EPM_CHANNEL']
    result = 'public' if os.getenv('EPM_USER', user) else None
    if channel:
        keys.append('EPM_USER_CHANNEL' + _(channel))
        if user:
            keys.append('EPM_USER{user}CHANNEL{channel}'.format(user=_(user), channel=_(channel)))
    else:
        if user:
            keys.append('EPM_USER{user}CHANNEL'.format(user=_(user)))

    for k in keys:
        result = os.getenv(k, result)
    return result

_PackagerClassId = 0


class MetaInfo(object):

    def __init__(self, metainfo, conanfile):
        self._metainfo = metainfo
        self._conanfile = conanfile

    @property
    def dependencies(self):
        return self._metainfo.get_requirements(self._conanfile.settings)


class ConanFileEx(ConanFile):

    def __init__(self, *args, **kwargs):
        super(ConanFileEx, self).__init__(*args, **kwargs)

        mirror = Mirror.load()
        if mirror:
            mirror.register(self.name)

    @property
    def metainfo(self):
        return MetaInfo(self._META_INFO, self)

    @property
    def manifest(self):
        return MetaInfo(self._META_INFO, self)


def Packager(manifest='package.yml'):
    metainfo = MetaInformation(manifest)
    name = metainfo.name
    version = metainfo.version
    user = metainfo.user

    global _PackagerClassId
    _PackagerClassId += 1
    class_name = symbolize('_%d_%s_%s_%s' % (_PackagerClassId, str(user), name, version))

    exports = [manifest]
    klass = type(class_name, (ConanFileEx,),
                 dict(name=name, version=version, exports=exports,
                      _META_INFO=metainfo))
    return klass


def TestPackager(manifest='../package.yml'):
    metainfo = MetaInformation(manifest)

    name = metainfo.name
    version = metainfo.version
    user = metainfo.user

    global _PackagerClassId
    _PackagerClassId += 1
    class_name = symbolize('_%d_%s_%s_%s' % (_PackagerClassId, user, name, version))
    from conans import ConanFile

    requires = ('%s/%s@%s/%s' % (name, version,
                                 user or '_',
                                 get_channel(user) or '_'))
    klass = type(class_name, (ConanFile,),
                 dict(version=version,
                      manifest=metainfo,
                      _META_INFO = metainfo,
                      requires=requires))
    return klass

