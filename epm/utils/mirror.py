import os
import re
import yaml
import fnmatch
from urllib.parse import urlparse

from string import Template
from conans.client.tools import net

from epm import HOME_DIR
from epm.utils import get_workbench_dir
conan_download = net.download

class Mirror(object):
    DATA = None

    def __init__(self, url):
        if not Mirror.DATA:
            config, rule, mirror = self._load_rule(url)
            Mirror.DATA = {'config': config, 'rule': rule, 
            'mirror': mirror}

    @property
    def rules(self):
        return Mirror.DATA.get('rule') or {}

    @property
    def config(self):
        return Mirror.DATA.get('config') or {}

    @property
    def mirror(self):
        return Mirror.DATA.get('mirror') or None



    def _load_rule(self, url):
        filename = url
        if url.startswith('http://') or url.startswith('http://'):
            filename = '.mirror.yml'
            if os.path.exists(filename):
                os.remove(filename)
            net.download([url], filename)
        filename = os.path.abspath(filename)
        with open(filename) as f:
            config = yaml.safe_load(f) 
        
        mirror = config.pop('.mirror', None)
        rules = []
        for base, patterns in config.items():
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
        return config, rules, mirror

    def get(self, url):
        mirror = os.getenv('EPM_MIRROR_BASE_URL', None) or self.mirror
        if not mirror:
            return None
        if mirror.endswith('/'):
            mirror = mirror[:-1]
            
        parser = urlparse(url)        
        for rule in self.rules:
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
            origin = [url]
            if isinstance(url, (list, tuple)):
                origin = list(url)

            urls = [] #list(url)    
            for i in origin:
                real_url = None
                try:
                    real_url = self.get(i)
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
    
