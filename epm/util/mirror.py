import os
import re
import yaml
from string import Template
from conans.client.tools import net


def split(txt, keys):
    for key in keys:
        result = txt.split(key, 1)


class Mirror(object):
    Repo = False
    Packages = set()

    def __init__(self, filename):
        self._filename = os.path.abspath(filename)

        with open(filename) as f:
            self._config = yaml.safe_load(f)
            self._package = self._config.get('package', {})
            if isinstance(self._package, str):
                print('mirror package has been redirect to %s' % self._package)
                with open(self._package) as f:
                    data = yaml.safe_load(f)
                    self._package = data.get('package') or dict()
        print('*************', self._package.get('libsoap'))

        self._property = self._config.get('property') or dict()

    def find(self, url):
        for name in self.Packages:
            result = self.find_package(name, url)
            if result:
                return result
        return None

    def find_package(self, name, url):
        rules = self._get_rules(name)
        if not rules:
            return None

        property = {}
        property.update(self._property)

        for expr, symbols, pattern in rules:
            m = pattern.match(url)
            print("[%s] :" % name, expr, symbols, pattern)
            print('m=', m, 'url:', url)
            if m:
                try:
                    kwargs = dict(property, **m.groupdict())
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
        import copy

        config = copy.deepcopy(config)
        self._package[name] = config

        rules = list()
        for expr, urls in config.items():

            expr = expr.replace('${__name__}', name)

            if expr in ['property']:
                continue

            if isinstance(urls, str):
                urls = [urls]
            expr = Template(expr)

            for url in urls:
                url = url.replace('${__name__}', name)
                keys = set()
                pattern = ''
                for txt, var in re.findall(r'([\w\-\.\:/]+)|(\$\{[a-z]+\})', url):
                    if var:
                        symbol = var[2:-1]
                        keys.add(symbol)
                        pattern += r'(?P<%s>\w[\w\.\-]+)' % symbol
                    else:
                        txt = txt.replace('\\', '\\\\')
                        for i in r'.：*<>-+':
                            txt = txt.replace(i, '\\'+i)
                        pattern += txt
                rules.append((expr, keys, re.compile(pattern)))
        config['__rules__'] = rules

        return rules

    def register(self, name):
        self.Packages.add(name)

    @staticmethod
    def load():
        if Mirror.Repo is False:
            from epm import HOME_DIR
            from epm.util import get_workbench_dir
            workbench = os.getenv('EPM_WORKBENCH') or HOME_DIR

            path = os.path.join(get_workbench_dir(workbench), 'mirrors.yml')
            if os.path.exists(path):
                try:
                    Mirror.Repo = Mirror(path)
                except Exception as e:
                    print(e)
                    Mirror.Repo = None

            if Mirror.Repo:
                register_mirror(Mirror.Repo)

        return Mirror.Repo


conan_download = net.download


def register_mirror(mirror):

    def download(url, filename, **kwargs):

        urls = []
        if isinstance(url, (list, tuple)):
            for i in url:
                real_url = None
                try:
                    real_url = mirror.find(i)
                    if real_url:
                        print('[mirror] {} -> {}'.format(i, real_url))
                except Exception as e:
                    print(e)

                urls.append(real_url or i)
        else:
            real_url = mirror.find(url)
            if real_url:
                print('[mirror] {} -> {}'.format(url, real_url))
            urls = real_url or url
        conan_download(urls, filename, **kwargs)

    net.download = download


def unregister_mirror():
    net.download = conan_download

