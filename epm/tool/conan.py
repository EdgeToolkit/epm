
import os
import yaml
from epm.util import symbolize

def get_channel(group=None):

    channel = os.environ.get('EPM_CHANNEL', 'public')
    if group:
        symbol = symbolize('_'+group.upper())
        channel = os.environ.get('EPM_CHANNEL{}'.format(symbol), channel)
    return channel


class Reference(object):

    def __init__(self, name, version, group, channel):
        self.name = name
        self.version = version
        self.group = group
        self.channel = channel

    def __str__(self):
        return '%s/%s@%s/%s' % (self.name, self.version, self.group, self.channel)


def normalize_manifest(manifest):
    group = manifest['group']
    from collections import OrderedDict
    deps = OrderedDict()

    for packages in manifest.get('dependencies', []):
        for name, option in packages.items():
            version = option['version']
            user = option.get('group', group)
            channel = option.get('channel') or get_channel(group=user)
            deps[name] = Reference(name, version, user, channel)
    manifest['dependencies'] = deps


def archive_mirror(conanfile, origin, folder=None, name=None):
    ARCHIVE_URL = os.getenv('EPM_ARCHIVE_URL', None)
    if ARCHIVE_URL is None:
        return origin
    name = name or conanfile.name
    folder = folder or name
    if isinstance(origin, dict):
        origin_url = origin['url']
        url = '{mirror}/{folder}/{basename}'.format(
            mirror=ARCHIVE_URL, folder=folder, basename=os.path.basename(origin_url))
        return dict(origin, **{'url': url})
    elif isinstance(origin, str):
        url = '{mirror}/{folder}/{basename}'.format(
            mirror=ARCHIVE_URL, folder=folder, basename=os.path.basename(origin))
        return url
    return origin


class PackageMetaInfo(object):

    def __init__(self, filename='package.yml'):
        if not os.path.exists(filename):
            raise Exception('Package manifest %s not exits!' % filename)

        with open(filename) as f:
            self._meta = yaml.safe_load(f)

    @property
    def name(self):
        return self._meta['name']

    @property
    def user(self):
        return self.group

    @property
    def group(self):
        return self._meta['group']

    @property
    def channel(self):
        return get_channel(group=self.group)

    @property
    def version(self):
        return self._meta['version']

    @property
    def reference(self):
        return '{}/{}@{}/{}'.format(self.name, self.version, self.group, self.channel)

    @property
    def dependencies(self):
        references = []
        for packages in self._meta.get('dependencies', []):
            for name, option in packages.items():
                version = option['version']
                user = option.get('group') or self.group
                channel = option.get('channel') or get_channel(group=user)
                references.append("%s/%s@%s/%s" % (name, version, user, channel))

        return references

    @property
    def build_requires(self):
        references = []
        for name, value in self._meta.get('build_requires', {}).items():
            version = value['version']
            user = value.get('group') or self.user
            channel = value.get('channel') or get_channel(group=user)
            references.append("%s/%s@%s/%s" % (name, version, user, channel))
        return references

    def get(self, key, default=None):
        return self._meta.get(key, default)

from epm.util import symbolize

_PackagerClassId = 0


def mirror(conanfile, origin, format='{name}/{basename}'):
    '''

    :param conanfile:
    :param origin:
    :param formatter:
    :return:
    '''
    ARCHIVE_URL = os.getenv('EPM_ARCHIVE_URL', None)
    if ARCHIVE_URL is None:
        conanfile.output.warning('environement `EPM_ARCHIVE_URL` not set use origin', origin)
        return origin

    url = origin['url'] if isinstance(origin, dict) else origin
    m = format.format(name=conanfile.name, basename=os.path.basename(url), version=conanfile.version)
    m = '%s/%s' % (ARCHIVE_URL, m)
    conanfile.output.info('mirror %s -> %s' % (url, m))

    if isinstance(origin, dict):
        return dict(origin, **{'url': m})
    elif isinstance(origin, str):
        return url
    return origin


def Packager(manifest='package.yml'):
    if not os.path.exists(manifest):
        raise Exception('package manifest file %s not exists' % manifest)

    with open(manifest) as f:
        _manifest = yaml.safe_load(f)
        normalize_manifest(_manifest)

    for i in ['name', 'version', 'group']:
        if i not in _manifest:
            raise Exception('`%s` field is required but not defined in %s' % (i, manifest))
    name = _manifest['name']
    version = _manifest['version']
    group = _manifest['group']
    global _PackagerClassId
    _PackagerClassId += 1
    class_name = symbolize('_%d_%s_%s_%s' % (_PackagerClassId, group, name, version))
    from conans import ConanFile
    exports = [manifest]
    klass = type(class_name, (ConanFile,),
                 dict(name=name, group=group, version=version,
                 manifest=_manifest, exports=exports))
    return klass


def TestPackager(manifest='../package.yml'):
    if not os.path.exists(manifest):
        raise Exception('package manifest file %s not exists' % manifest)

    with open(manifest) as f:
        _manifest = yaml.safe_load(f)
        normalize_manifest(_manifest)

    for i in ['name', 'version', 'group']:
        if i not in _manifest:
            raise Exception('`%s` field is required but not defined in %s' % (i, manifest))
    name = _manifest['name']
    version = _manifest['version']
    group = _manifest['group']
    global _PackagerClassId
    _PackagerClassId += 1
    class_name = symbolize('_%d_%s_%s_%s' % (_PackagerClassId, group, name, version))
    from conans import ConanFile

    requires = ('%s/%s@%s/%s' % (name, version, group, get_channel(group)))
    klass = type(class_name, (ConanFile,),
                 dict(group=group, version=version,
                      manifest=_manifest,
                      requires= requires))
    return klass
