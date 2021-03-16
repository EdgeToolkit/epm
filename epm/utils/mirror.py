import os
import re
import yaml
import fnmatch
from urllib.parse import urlparse

from string import Template
from conans.client.tools import net

from epm import HOME_DIR
from epm.utils import get_workbench_dir


class Mirror(object):
    Repo = False
    Packages = set()

    def __init__(self, filename):
        self._filename = os.path.abspath(filename)
        with open(self._filename) as f:
            self._config = yaml.safe_load(f)
        self._package = self._config.get('package') or dict()

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
            if m:
                try:
                    kwargs = dict(property, **m.groupdict())
                    return expr.substitute(kwargs)
                except Exception as e:
                    print('WARN: mirror config wrong', e)

        return None

    def _get_rules(self, name):
        config = self._package.get(name)
        if not config:
            return None

        if '__rules__' in config:
            return config['__rules__']

        if isinstance(config, str) and config.startswith('${') and config.endswith('}'):
            ref = config[2:-1]
            rules = self._get_rules(ref)
            self._package[name] = {'__rules__': rules, 'ref': ref}
            return rules


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
                for txt, var in re.findall(r'([~\w\-\.\:/]+)|(\$\{[a-z]+\})', url):
                    if var:
                        symbol = var[2:-1]
                        keys.add(symbol)
                        pattern += r'(?P<%s>\w[\w\.\-]+)' % symbol
                    else:
                        txt = txt.replace('\\', '\\\\')
                        #>>>* . ? + $ ^ [ ] ( ) { } | \ /
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
            workbench = os.getenv('EPM_WORKBENCH') or HOME_DIR
            Mirror.Repo = None

            for folder in [get_workbench_dir(workbench), HOME_DIR]:
                path = os.path.join(folder, 'mirrors.yml')
                if os.path.exists(path):
                    try:
                        Mirror.Repo = Mirror(path)
                        break
                    except Exception as e:
                        print(e)

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
                    import traceback
                    traceback.print_tb(e.__traceback__)

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



class Mirror(object):
    
    
    def __init__(self, filename):
        self._filename = os.path.abspath(filename)
        with open(self._filename) as f:
            self._config = yaml.safe_load(f)
        self._mirror = self._config.pop('.mirror', None)
        
        rules = []
        for base, patterns in self._config.items():
            if isinstance(patterns, str):
                patterns = [patterns]
            for p in patterns:
                parser = urlparse(p)
                fnmatch=None
                if parser.path and parser.path !='/':
                    fnmatch = re.sub(r'\$\{\w+\}', '*', parser.path)
                    if not fnmatch.endswith('/'):
                        fnmatch += '/'
                    fnmatch += '*'
                        
                from collections import namedtuple
                obj = namedtuple('X', 'base parser fnmatch')(base, parser, fnmatch)
                rules.append(obj)
        self._rules = rules
    
    def get(self, url):
        mirror = os.getenv('EPM_MIRROR_BASE_URL', None) or self._mirror
        if not mirror:
            return None
        if mirror.endswith('/'):
            mirror = mirror[:-1]
            
        parser = urlparse(url)        
        for rule in self._rules:
            if rule.parser.scheme != parser.scheme:
                continue
            if rule.parser.netloc != parser.netloc:
                continue
            
            path = None            
            if rule.fnmatch is None:
                path = f'{rule.base}/{parser.path}'
            elif fnmatch.fnmatch(parser.path, rule.fnmatch):
                n = len(rule.fnmatch.split('/'))-1
                fields = parser.path.split('/')                
                path = "/".join(fields[n:])
                path = f'{rule.base}/{path}'
            if path:
                return f"{mirror}/{path}"
        return None
    
    def hack_conan_download(self):
        def _download(url, filename, **kwargs):
            urls = [url]
            if isinstance(url, (list, tuple)):
                urls = list(url)
            urls = [] #list(url)    
            for i in list(url):
                real_url = None
                try:
                    real_url = self.get(url)
                    if real_url:
                        print('[mirror] {} -> {}'.format(i, real_url))
                except Exception as e:
                    print(e)
                    import traceback
                    traceback.print_tb(e.__traceback__)

                urls.append(real_url or i)
            if len(urls) > 1:
                print('download candidate urls:\n', "\n".join(urls))
            conan_download(urls, filename, **kwargs)

        net.download = _download

        
        
            
        
        
            
    
    
if __name__ == '__main__':
    name = 'pkgconf'
    url = r'https://github.com/kubeedge/kubeedge/releases/download/v1.5.0/kubeedge-v1.5.0-linux-amd64.tar.gz'
    mirror = Mirror(r'E:\edgetoolkit\mirror.yml')
    urls = ["https://zlib.net/zlib-1.2.11.tar.gz",
            "https://downloads.sourceforge.net/project/libpng/zlib/1.2.11/zlib-1.2.11.tar.gz",
            r'https://github.com/kubeedge/kubeedge/releases/download/v1.5.0/kubeedge-v1.5.0-linux-amd64.tar.gz'
    ]
    for url in urls:
        print('')
        print('*' , url)
        print('  ->', mirror.get(url))
    
