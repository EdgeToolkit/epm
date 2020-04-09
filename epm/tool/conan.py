
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
            print(packages, '________________________', self._meta)
            for name, option in packages.items():
                print(name, option, '@--------------------')
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
