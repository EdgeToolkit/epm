import os
from epm.util.files import save_yaml, load_yaml
from collections import namedtuple

class Config(object):

    def __init__(self, filename='~/.epm/config.yml'):
        self._filename = filename
        if os.path.exists(self._filename):
            self._data = load_yaml(self._filename) or {}
        self._data = dict({'venv': {},
                           'registry': {}
                           }, **self._data)

    @property
    def venv(self):
        VEnv = namedtuple('VEnv', ['name'])
        value = self._data.get('venv')
        if value is None or value.get('name') is None:
            return None
        return VEnv(value['name'])

    @property
    def environment(self):
        return self._data.get('environment', {})

    @property
    def remotes:
        Remote = namedtuple('Remote', ['url', 'username', 'password'])
        remotes = []
        for r in self._data.get('remotes', []):
            url = r['url']
            username = r.get('username', None)
            password = r.get('password', None)
            remotes.append(Remote(url, username, password))
        return remotes

    @property
    def env_vars(self):
        '''
        '''
        env = {}
        for key, value in self.environment.items():
            val = os.environ[key]
            if val:
                env[key] = val
        return dict(self.environment, **env)


    def get(self, section, default=None):
        return self._data.get(section, default)




