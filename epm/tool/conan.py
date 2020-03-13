
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
        for name, value in self._meta.get('dependencies', {}).items():
            print(name, '====', value)
            #self._require_check("dependencies illegal.", name, value)
            version = value['version']
            user = value.get('group') or self.group
            channel = value.get('channel') or get_channel(name)
            references.append("%s/%s@%s/%s" % (name, version, user, channel))
        #dependencies = self._meta.get('dependencies', [])
        #for package in self._meta.get('dependencies', []):
        #    print('packaginfo', package, type(package), '*', isinstance(package, dict))
        #    assert isinstance(package, dict)
        #    assert len(package) == 1
        #    for name, value in package.items():
        #        self._require_check("dependencies illegal.", name, value)
        #        version = value['version']
        #        user = value.get('group') or self.group
        #        channel = value.get('channel') or get_channel(name)
        #        references.append("%s/%s@%s/%s" % (name, version, user, channel))
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

