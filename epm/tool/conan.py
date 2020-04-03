
import os
import yaml
from epm.util import symbolize


def get_channel(group=None):
    """ get package channel according environment vars.

    :param group: package group
    :return: channel
    """

    channel = os.environ.get('EPM_CHANNEL', 'public')
    if group:
        symbol = symbolize('_'+group.upper())
        channel = os.environ.get('EPM_CHANNEL{}'.format(symbol), channel)
    return channel


def mirror(origin, name):
    ARCHIVE_URL = os.getenv('EPM_ARCHIVE_URL', None)
    if ARCHIVE_URL is None:
        return origin
    origin_url = origin['url']
    #url = '%s/%s/conandata.yml' % (self.ARCHIVE_URL, self.name)
    #name = name or self.name
    #folder = tempfile.mkdtemp(prefix='%s-%s' % (self.name, self.version))
    #filename = os.path.join(folder, 'conandata.yml')
    #tools.download(url, filename)
    #with open(filename) as f:
    #    data = yaml.safe_load(f)
    origin['url'] = '{mirror}/{name}/{basename}'.format(
        mirror=ARCHIVE_URL, name=name, basename=os.path.basename(origin_url))
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
            #self._require_check("build requirements configuration illegal", name, value)
            version = value['version']
            user = value.get('group') or self.user
            channel = value.get('channel') or get_channel(group=user)
            references.append("%s/%s@%s/%s" % (name, version, user, channel))
        return references

    def get(self, key, default=None):
        return self._meta.get(key, default)

#from conans import ConanFile, CMake, tools
#import tempfile
#import os
#class Makefile(ConanFile):
#    METADATA = ConanMeta()
#    name = METADATA.name
#    version = METADATA.version
#    url = METADATA.url
#    description = METADATA.description
#    license = METADATA.license
#    author = METADATA.author
#    homepage = METADATA.homepage
#    topics = METADATA.topics
#    ARCHIVE_URL = os.environ.get('EPM_ARCHIVE_URL', None)
#    exports = ["conanfile.py", "package.yml"]
#
#    def __init__(self, output, runner, display_name="", user=None, channel=None):
#        super(Makefile, self).__init__(output, runner, display_name, user, channel)
#
#    def try_mirror(self, origin, name=None):
#        if self.ARCHIVE_URL:
#            origin_url = origin['url']
#            url = '%s/%s/conandata.yml' % (self.ARCHIVE_URL, self.name)
#            name = name or self.name
#            folder = tempfile.mkdtemp(prefix='%s-%s' % (self.name, self.version))
#            filename = os.path.join(folder, 'conandata.yml')
#            #tools.download(url, filename)
#            #with open(filename) as f:
#            #    data = yaml.safe_load(f)
#            origin['url'] = '{mirror}/{name}/{basename}'.format(
#                mirror=self.ARCHIVE_URL, name=name, basename=os.path.basename(origin_url))
#        return origin
#
#    def join_patches(self, patches, folder=None):
#        folder = folder or self.source_folder
#        for i in ['base_path', 'patch_file']:
#            patches[i] = os.path.join(folder, patches[i])
#        return patches
#
#
#
#
#class TestMakefile(ConanFile):
#    generators = "cmake"
#
#    def __init__(self, output, runner, display_name="", user=None, channel=None):
#        super(TestMakefile, self).__init__(output, runner, display_name, user, channel)
#
#    @property
#    def target_reference(self):
#        reference = os.environ.get('EPM_TARGET_PACKAGE_REFERENCE')
#        if reference:
#            return reference
#        #pkg_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
#        #filename = os.path.join(pkg_dir, 'package.yml')
#        filename = 'package.yml'
#        if os.path.exists(filename):
#            meta = ConanMeta(filename)
#            return meta.reference
#        raise Exception('environment var EPM_TARGET_PACKAGE_REFERENCE not set.')
#
#    def requirements(self):
#        self.requires(self.target_reference)