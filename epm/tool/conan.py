import os
import yaml
from conans.model.ref import ConanFileReference


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


from collections import namedtuple, OrderedDict
from conans.model.version import Version


class Manifest(namedtuple("Manifest", "name version user dependencies")):
    """ Full reference of a package recipes, e.g.:
    opencv/2.4.10@lasote/testing
    """

    def __new__(cls, data, name, version, user, dependencies):
        """Simple name creation.
        @param name:        string containing the desired name
        @param version:     string containing the desired version
        @param user:        string containing the user name
        @param dependencies: OrderDict of ConanFileReference for this package dependencies
        """
        version = Version(version) if version is not None else None

        obj = super(cls, Manifest).__new__(cls, name, version, user, dependencies)
        return obj

    @staticmethod
    def loads(filename='package.yml'):
        """
        """
        if not os.path.exists(filename):
            raise Exception('Package manifest %s not exits!' % filename)

        with open(filename) as f:
            text = f.read()
            data = yaml.safe_load(f)

        name = data['name']
        version = data['version']
        user = data.get('user', None)
        dependencies = data.get('dependencies', [])
        if not isinstance(dependencies, list):
            raise Exception('package.yml `dependencies` field should be list')
        deps = OrderedDict()
        for packages in dependencies:
            if not isinstance(dependencies, dict):
                raise Exception('package.yml `dependencies` item should be dict')

            for name, option in packages.items():
                if 'version' not in option:
                    raise Exception('package.yml `dependencies` %s `version` not set' % name)

                version = option['version']
                user = option.get('user', None)
                channel = get_channel(user=user)
                channel = option.get('channel', channel)
                deps[name] = ConanFileReference(name, version, user, channel)

        manifest = Manifest(name, version, user, deps)
        manifest._data = data
        manifest._text = text
        return manifest

    def as_dict(self):
        return self._data


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
        return m
    return origin


def Packager(manifest='package.yml'):
    m = Manifest(manifest)
    name = m.name
    version = m.version
    user = m.user

    global _PackagerClassId
    _PackagerClassId += 1
    class_name = symbolize('_%d_%s_%s_%s' % (_PackagerClassId, str(user), name, version))
    from conans import ConanFile
    exports = [manifest]
    klass = type(class_name, (ConanFile,),
                 dict(name=name, version=version, manifest=m, exports=exports))
    return klass


def TestPackager(manifest='../package.yml'):
    m = Manifest(manifest)
    name = m.name
    version = m.version
    user = m.user

    global _PackagerClassId
    _PackagerClassId += 1
    class_name = symbolize('_%d_%s_%s_%s' % (_PackagerClassId, user, name, version))
    from conans import ConanFile
    m = Manifest(manifest)

    requires = ('%s/%s@%s/%s' % (name, version,
                                 user or '_',
                                 get_channel(user) or '_'))
    klass = type(class_name, (ConanFile,),
                 dict(version=version,
                      manifest=m,
                      requires=requires))
    return klass
