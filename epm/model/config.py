import os
from epm.util.files import save_yaml, load_yaml
from collections import namedtuple

class Config(object):

    def __init__(self, filename='~/.epm/config.yml'):
        self._data = {}
        self._filename = filename
        print(self._filename, '[=========================')
        if os.path.exists(self._filename):
            print(self._filename, '[=========================>>>')
            self._data = load_yaml(self._filename)
        self._data = dict({'wenv': {},
                           'registry': {}
                           }, **self._data)

    @property
    def wenv(self):
        WEnv = namedtuple('WEnv', ['name', 'with_default_profiles', 'buildin_profiles'])

        value = self._data.get('wenv')

        if value is None or value.get('name') is None:
            return None
        with_default_profiles = value.get('with_default_profiles', False)
        buildin_profiles = value.get('buildin_profiles')
        return WEnv(value['name'], with_default_profiles, buildin_profiles)

    @property
    def environment(self):
        print(self._data, '!!!!!!!!!!!!!!!!')
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




