import os
from collections import namedtuple
from epm.utils import load_yaml

HOME_DIR = os.path.join(os.path.expanduser('~'), '.epm')


class Config(object):

    def __init__(self, filename='~/.epm/config.yml'):
        self._data = {}
        self._filename = filename
        self._data = load_yaml(filename, {})

    @property
    def workbench(self):
        Workbench = namedtuple('Workbench', ['name', 'default_scheme'])

        value = self._data.get('workbench')

        if value is None or value.get('name') is None:
            return None
        default_scheme = value.get('default_scheme') or None

        return Workbench(value['name'], default_scheme)

    @property
    def environment(self):
        return self._data.get('environment', {})

    @property
    def remotes(self):
        Remote = namedtuple('Remote', ['name', 'url', 'username', 'password'])
        remotes = []
        for item in self._data.get('remotes', []):
            for name, r in item.items():
                url = r['url']
                username = r.get('username', None)
                password = r.get('password', None)
                remotes.append(Remote(name, url, username, password))
        return remotes

    @property
    def env_vars(self):
        '''
        '''
        env = {}
        for key, value in self.environment.items():
            val = os.environ.get(key)
            if val:
                env[key] = val
        return dict(self.environment, **env)

    def get(self, section, default=None):
        return self._data.get(section, default)

