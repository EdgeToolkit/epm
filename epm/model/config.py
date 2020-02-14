import os
from epm.util.files import save_yaml, load_yaml


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
        return self._data['venv']

    @property
    def registry(self):
        return self._data['registry']

    def save(self, filename=None):
        filename = filename or self._filename
        data = {}
        for k, v in self._data.items():
            if v:
                data[k] = v
        save_yaml(filename, data)




