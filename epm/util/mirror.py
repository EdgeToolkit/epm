import os
import re
import yaml



def split(txt, keys):
    for key in keys:
        result = txt.split(key, 1)
        


_PATTER_SYMBOL = re.compile('\{[a-z]+\}')



class Mirror(object):

    def __init__(self, filename):
        self._filename = os.path.abspath(filename)
        with open(filename) as f:
            self._config = yaml.safe_load(f)
            self._package = self._config.get('package', {})

    def find_package(self, name, url):
        info = self._config.get('package', {}).get(name) or {}
        if not info:
            return

    def _x(self, name):
        config = self._package.get(name)
        if not config:
            return None
        if '__metaclass__' in config['__metaclass__']:
            return config['__metaclass__']

        property = config.get('property') or dict()
        symbols = []

        for key, urls in config.items():
            if isinstance(urls, str):
                urls = [urls]
            for url in urls:
                symbols += _PATTER_SYMBOL.split(url)

        for key, urls in config.items():
            if isinstance(urls, str):
                urls = [urls]
            for url in urls:
                symbols += _PATTER_SYMBOL.split(url)
