import os
import re
import yaml
from string import Template
from conans.client.tools import net


def split(txt, keys):
    for key in keys:
        result = txt.split(key, 1)
        
class Mirror(object):

    def __init__(self, filename):
        self._filename = os.path.abspath(filename)

        with open(filename) as f:
            self._config = yaml.safe_load(f)
            self._package = self._config.get('package', {})
        self._property = self._config.get('property') or dict()

    def find_package(self, name, url):
        rules = self._get_rules(name)
        if not rules:
            return None

        for expr, symbols, pattern in rules:
            m = pattern.match(url)
            if m:
                try:
                    kwargs = dict(self._property, **m.groupdict())
                    return expr.substitute(kwargs)
                except:
                    pass

        return None

    def _get_rules(self, name):
        config = self._package.get(name)
        if not config:
            return None

        if '__rules__' in config:
            return config['__rules__']

        rules = list()

        for expr, urls in config.items():

            if expr in ['property']:
                continue

            if isinstance(urls, str):
                urls = [urls]
            expr = Template(expr)

            for url in urls:
                keys = set()
                pattern = ''
                for txt, symbol in re.findall(r'([\w\-\.\:/]+)|(\$\{[a-z]+\})', url):
                    if symbol:
                        name = symbol[2:-1]
                        keys.add(name)
                        pattern += r'(?P<%s>\w[\w\.\-]+)' % name
                    else:
                        txt = txt.replace('\\', '\\\\')
                        for i in r'.：*<>-+':
                            txt = txt.replace(i, '\\'+i)
                        pattern += txt
                rules.append((expr, keys, re.compile(pattern)))
        config['__rules__'] = rules

        return rules

    @staticmethod
    def load():
        from epm import HOME_DIR
        from epm.util import get_workbench_dir
        workbench = os.getenv('EPM_WORKBENCH') or HOME_DIR

        path = os.path.join(get_workbench_dir(workbench), 'mirrors.yml')
        if os.path.exists(path):
            try:
                return Mirror(path)
            except Exception as e:
                print(e)
        return None


conan_download = net.download


def register_mirror(mirror, name):

    def download(url, filename, **kwargs):

        urls = []
        if isinstance(url, (list, tuple)):
            for i in url:
                real_url = None
                try:
                    real_url = mirror.find_package(name, i)
                    if real_url:
                        print('[mirror] {} -> {}'.format(i, real_url))
                except Exception as e:
                    print(e)

                urls.append(real_url or i)
        else:
            assert  False
            result = mirror.find_package(name, url)
            if result:
                urls.append(result)
                print('[mirror] {} -> {}'.format(i, result))
            else:
                urls = url
        conan_download(urls, filename, **kwargs)
    net.download = download


def unregister_mirror():
    net.download = conan_download

if __name__ == '__main__':
    m = Mirror(r'E:\WebKit\EPMKit\epm\epm\test\data\mirror\mirrors.yml')
    url =r'https://downloads.sourceforge.net/project/libpng/zlib/2.1.11/zlib-2.1.11-tar.gz'
    #url =r'https://zlib.net/zlib-2.1.11-tar.gz'
    url = m.find_package('zlib', url)
    print(url)