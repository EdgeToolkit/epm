
import os
import yaml
from epm.util import symbolize


def get_channel(name=None):
    """ get package channel according environment vars.

    :param name: package name
    :return: channel
    """
    channel = os.environ.get('EPM_CHANNEL', 'public')
    if name:
        symbol = symbolize('_'+name)
        return os.environ.get('EPM_CHANNEL{}'.format(symbol), channel)
    return channel


_require_format_example = '''
{what}, {reason}
<{name}>
{value} 
'''


class ConanMeta(object):

    def __init__(self, filename='package.yml'):
        if filename and isinstance(filename, dict):

            self._meta = filename
        else:

            if not os.path.exists(filename):
                raise FileNotFoundError('epm manifest not exists.')

            with open(filename) as f:
                self._meta = yaml.safe_load(f)

    @property
    def name(self):
        return self._meta['name']

#    @property
#    def user(self):
#        return self._meta['group']
    @property
    def group(self):
        return self._meta['group']

    @property
    def channel(self):
        return get_channel(self.name)

    @property
    def version(self):
        return self._meta['version']

    @property
    def reference(self):
        return '{}/{}@{}/{}'.format(self.name, self.version, self.group, self.channel)

    @property
    def author(self):
        return self._meta.get('author', None)

    @property
    def description(self):
        return self._meta.get('description', None)

    @property
    def license(self):
        license = self._meta.get('license')
        return tuple(license) if license else None

    @property
    def url(self):
        return self._meta.get('url', None)

    @property
    def homepage(self):
        return self._meta.get('homepage', None)

    @property
    def topics(self):
        return self._meta.get('topics', None)

    @property
    def dependencies(self):
        references = []
        for packages in self._meta.get('dependencies', []):
            for name, option in packages.items():
                version = option['version']
                user = option.get('group') or self.group
                channel = option.get('channel') or get_channel(name)
                references.append("%s/%s@%s/%s" % (name, version, user, channel))

        return references

    @property
    def build_requires(self):
        references = []
        for name, value in self._meta.get('build_requires', {}).items():
            self._require_check("build requirements configuration illegal", name, value)
            version = value['version']
            user = value.get('group') or self.user
            channel = value.get('channel') or get_channel(name)
            references.append("%s/%s@%s/%s" % (name, version, user, channel))
        return references

    @staticmethod
    def _require_check(what, name, value):
        reason = ''
        if not isinstance(value, dict):
            reason += "format error, should be dict"
            for i in ['group', 'version']:
                if i not in value:
                    reason +=" missing filed %s" % i
        if reason:
            raise Exception(_require_format_example.format(waht=what, reason=reason, value=value, name=name))

    def get(self, key, default=None):
        return self._meta.get(key, default)


from conans import ConanFile, CMake, tools
class Makefile(ConanFile):
    METADATA = ConanMeta()
    name = METADATA.name
    version = METADATA.version
    url = METADATA.url
    description = METADATA.description
    license = METADATA.license
    author = METADATA.author
    homepage = METADATA.homepage
    topics = METADATA.topics
    ARCHIVE_URL = os.environ.get('EPM_ARCHIVE_URL', None)
    CONAN_DATA = METADATA.get('conan_data', {})
    exports = ["conanfile.py", "package.yml"]

    def __init__(self, output, runner, display_name="", user=None, channel=None):
        super(Makefile, self).__init__(output, runner, display_name, user, channel)


class TestMakefile(ConanFile):
    generators = "cmake"

    def __init__(self, output, runner, display_name="", user=None, channel=None):
        super(TestMakefile, self).__init__(output, runner, display_name, user, channel)

    @property
    def target_reference(self):
        reference = os.environ.get('EPM_TARGET_PACKAGE_REFERENCE')
        if reference:
            return reference
        pkg_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
        filename = os.path.join(pkg_dir, 'package.yml')
        filename = 'package.yml'
        if os.path.exists(filename):
            meta = ConanMeta(filename)
            return meta.reference
        raise Exception('environment var EPM_TARGET_PACKAGE_REFERENCE not set.')

    def requirements(self):
        self.requires(self.target_reference)