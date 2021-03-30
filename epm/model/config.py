import os
import yaml
from collections import namedtuple


HOME_DIR = os.path.join(os.path.expanduser('~'), '.epm')


class Config(object):

    def __init__(self, filename='~/.epm/config.yml'):
        self._data = {}
        self._filename = filename
        if os.path.exists(self._filename):
            with open(filename) as f:
                self._data = yaml.safe_load(f) or {}

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
        return self._data.get('environment') or {}

    def _parse_remotes(self, data):
        Remote = namedtuple('Remote', ['name', 'url', 'username', 'password'])
        remotes = []
        for it in data or []:
            name = it['name']
            url = it['url']
            username = it.get('username', None)
            password = it.get('password', None)
            remotes.append(Remote(name, url, username, password))
        return remotes

    @property
    def conan(self):
        Conan = namedtuple('Conan', ['storage', 'short_path', 'remotes'])
        conan = self._data.get('conan', {})
        storage = conan.get('storage') or None
        short_path = conan.get('short_path') or None

        remotes = self._parse_remotes(conan.get('remotes'))
        return Conan(storage, short_path, remotes)

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
    
    @property
    def data(self):
        return self._data

