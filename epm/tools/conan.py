import os
import yaml
from conans.model.ref import ConanFileReference, get_reference_fields
import re
import pathlib

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


from collections import namedtuple, OrderedDict
from conans.model.version import Version


def dependencies_to_reference(data, text=None):
    dependencies = data.get('dependencies', [])
    if not isinstance(dependencies, list):
        raise Exception('package.yml `dependencies` field should be list')
    deps = OrderedDict()
    for packages in dependencies:
        if isinstance(packages, str):
            name, version, user, channel, revision = get_reference_fields(packages)
            if user:
                channel = channel or get_channel(user=user)
            deps[name] = ConanFileReference(name, version, user, channel, revision)

        elif isinstance(packages, dict):
            if len(packages) > 1:
                text = yaml.dump({'dependencies': [packages]})
                reason = 'package.yml dependencies item wrong format, you may miss indent.'
                reason += '\n{}'.format(text)
                print(reason)
                raise Exception(reason)

            for name, option in packages.items():
                if 'version' not in option:
                    raise Exception('package.yml `dependencies` %s `version` not set' % name)

                version = option['version']
                user = option.get('user', None)
                channel = get_channel(user=user)
                channel = option.get('channel', channel)
                revision= option.get('revision', None)
                deps[name] = ConanFileReference(name, version, user, channel, revision)
        else:
            raise Exception('package.yml `dependencies` item should be dict or reference str ')

    return deps


#
# sandbox:
#   <name>: '<project>/<type>/<folder>/<archive>
# project: directory of sandbox program where placed conanfile.py
#          build, package, bin, not permitted
# type   :  `package` or `build` which depend on make script
# folder : None or 'bin'
# archive: program (without suffix) of the built
#

_P_PROJECT = r'(?P<project>\w[\w\-]+)/'
_P_TYPE = r'(?P<type>(build|package))/'
_P_FOLDER = r'(?P<folder>bin)?'
_P_PROGRAM = r'/(?P<program>\w[\w\-]+)'
_SANDBOX_PATTERN = re.compile(_P_PROJECT + _P_TYPE + _P_FOLDER + _P_PROGRAM + r'$')


class ManifestParser(object):

    def __init__(self, filename):
        if not os.path.exists(filename):
            raise Exception('Package manifest %s not exits!' % filename)

        self._filename = os.path.abspath(filename)

        with open(self._filename) as f:
            self.text = f.read()

        self.data = yaml.safe_load(self.text)

    def sandbox(self):
        Sandbox = namedtuple('Sandbox', 'content name directory type folder program param argv ports privileged')
        result = {}
        ports = []
        privileged = False
        for name, item in self.data.get('sandbox', {}).items():
            cmdstr = item
            if isinstance(item, dict):
                cmdstr = item['command']
                ports = item.get('ports', []) or []
                if isinstance(ports, int):
                    ports = [ports]
                privileged = item.get('privileged', False)

            parts = cmdstr.split(' ', 1)
            command = parts[0]
            command = pathlib.PurePath(command).as_posix()
            param = None if len(parts) < 2 else parts[1].strip()
            argv = param.split() if param else []
            m = _SANDBOX_PATTERN.match(command)
            if not m:
                raise Exception('sandbox {} invalid'.format(name))

            result[name] = Sandbox(item, name,
                                   m.group('project'), m.group('type'),
                                   m.group('folder'), m.group('program'),
                                   param, argv, ports, privileged)

        return result

    def dependencies(self):
        dependencies = self.data.get('dependencies', [])
        if not isinstance(dependencies, list):
            raise Exception('package.yml `dependencies` field should be list')
        deps = OrderedDict()
        for packages in dependencies:
            if isinstance(packages, str):
                name, version, user, channel, revision = get_reference_fields(packages)
                if user:
                    channel = channel or get_channel(user=user)
                deps[name] = ConanFileReference(name, version, user, channel, revision)

            elif isinstance(packages, dict):
                if len(packages) > 1:
                    text = yaml.dump({'dependencies': [packages]})
                    reason = 'package.yml dependencies item wrong format, you may miss indent.'
                    reason += '\n{}'.format(text)
                    print(reason)
                    raise Exception(reason)

                for name, option in packages.items():
                    if 'version' not in option:
                        raise Exception('package.yml `dependencies` %s `version` not set' % name)

                    version = option['version']
                    user = option.get('user', None)
                    channel = get_channel(user=user)
                    channel = option.get('channel', channel)
                    revision = option.get('revision', None)
                    deps[name] = ConanFileReference(name, version, user, channel, revision)
            else:
                raise Exception('package.yml `dependencies` item should be dict or reference str ')

        return deps


class Manifest(namedtuple("Manifest", "name version user dependencies sandbox")):
    """ Full reference of a package recipes, e.g.:
    opencv/2.4.10@lasote/testing
    """

    def __new__(cls, name, version, user, dependencies, sandbox=None):
        """Simple name creation.
        @param name:        string containing the desired name
        @param version:     string containing the desired version
        @param user:        string containing the user name
        @param dependencies: OrderDict of ConanFileReference for this package dependencies
        """
        version = Version(str(version)) if version is not None else None

        obj = super(cls, Manifest).__new__(cls, name, version, user, dependencies, sandbox)
        return obj

    @staticmethod
    def loads(filename='package.yml'):
        """
        """
        parser = ManifestParser(filename)
        data = parser.data
        name = data['name']
        version = data['version']
        user = data.get('user', None)
        deps = parser.dependencies()
        sandbox = parser.sandbox()

        manifest = Manifest(name, version, user, deps, sandbox)
        manifest._parser = parser
        manifest._data = data
        manifest._text = parser.text
        return manifest

    def as_dict(self):
        return self._data


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
    m = Manifest.loads(manifest)
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
    m = Manifest.loads(manifest)
    name = m.name
    version = m.version
    user = m.user

    global _PackagerClassId
    _PackagerClassId += 1
    class_name = symbolize('_%d_%s_%s_%s' % (_PackagerClassId, user, name, version))
    from conans import ConanFile

    requires = ('%s/%s@%s/%s' % (name, version,
                                 user or '_',
                                 get_channel(user) or '_'))
    klass = type(class_name, (ConanFile,),
                 dict(version=version,
                      manifest=m,
                      requires=requires))
    return klass
