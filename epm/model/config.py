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
        VEnv = namedtuple('VEnv', ['name', 'with_default_profiles', 'buildin_profiles'])

        value = self._data.get('venv')

        if value is None or value.get('name') is None:
            return None
        with_default_profiles = value.get('with_default_profiles', False)
        buildin_profiles = value.get('buildin_profiles')
        return VEnv(value['name'], with_default_profiles, buildin_profiles)

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
            val = os.environ[key]
            if val:
                env[key] = val
        return dict(self.environment, **env)

    def get(self, section, default=None):
        return self._data.get(section, default)




