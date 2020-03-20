
import os
import sys
import yaml
import urllib
import shutil
import tarfile
import zipfile
import tempfile
from jinja2 import PackageLoader, Environment
import subprocess

from urllib.parse import urlparse
from jinja2 import Environment, BaseLoader
from conans.client.output import ConanOutput as Output
from epm.util import system_info
from epm.util.files import load_yaml, save_yaml, save, rmdir, mkdir
from epm.errors import EException
from epm.paths import get_epm_home_dir
from epm.api import API
from conans.tools import environment_append


PLATFORM, ARCH = system_info()


_Banner = '''
                 
      __________  __  ___
     / ____/ __ \/  |/  / VIRTUAL ENVIROMENT {name}
    / __/ / /_/ / /|_/ /  
   / /___/ ____/ /  / /   Channel: {channel}
  /_____/_/   /_/  /_/    
                               

  * directory     : {instd}
  * conan         : {conan}
  * conan storage : {storage_path}

'''

_SetupHint = '''
virtual environment '{name}' setup done, run active script to active
In Windows
   $ active.bat
In Linux
   $ source ./active.sh

or use epm
   $ epm venv shell {name}
  
 
'''


class VirtualEnvironment(object):

    def __init__(self, api, name=None, out=None, directory=None):
        self._api = api
        self._directory = os.path.abspath(directory or '.')
        self._jinja2 = Environment(loader=PackageLoader('epm', 'data/venv'))
        self._out = out or self._api.out or Output(sys.stdout)
        self._hapi = None

    def _cache(self, path):
        url = urlparse(path)
        config_folder = path

        if url.scheme in ['http', 'https']:
            download_dir = tempfile.mkdtemp(suffix='epm.download')
            filename = os.path.join(download_dir, os.path.basename(path))
            urllib.request.urlretrieve(path, filename)
            config_folder = os.path.join(download_dir, 'venv.config')
            zfile = zipfile.ZipFile(filename)
            zfile.extractall(config_folder)

        if not os.path.exists(config_folder):
            raise Exception('Invalid install path {}'.format(path))
        return config_folder

    def _initialize(self, name=None):
        hapi = self.hapi
        hconf = hapi.config
        registry = hconf.registry.get('virtual-environment', {})

        path = hapi.home_dir
        if name in [None, '~']:
            venv = {'name': '~',
                    'path': path,
                    'channel': 'public'
                    }
            venv = dict(venv, **hconf.venv)
            name = '~'
            api = hapi

        else:
            if name not in registry:
                raise EException('%s not registered venv.')
            path = registry[name]['path']
            api = API(path, output=self._out)
            venv = api.config.venv
        mkdir(path)

        conan = api.conan
        conan.remote_clean()

        remotes = venv.get('remotes', [])
        for remote in remotes:
            for name, url in remote.items():
                conan.remote_add(name, url, verify_ssl=True)

        def _render(filename):
            _dict = dict({'channel': 'public',
                          'environment': {}
                          }, **venv)
            tmpl = self._jinja2.get_template(filename + '.j2')
            content = tmpl.render(_dict)
            save(os.path.join(path, filename), content)

        _render('active.bat')
        _render('active.sh')
        _render('bash.rc')

        self._out.info(_SetupHint.format(name=name))

    def setup(self, url, name=None):
        hapi = self.hapi
        hconf = self.hapi.config
        registry = hconf.registry.get('virtual-environment', {})

        if name in registry:
            raise Exception('{} venv already installed, clear it try again.'.format(name))

        if os.path.exists('.conan'):
            raise Exception('current directory is dirty .conan is exits.')

        cached = self._cache(url)
        venv = load_yaml(os.path.join(cached, 'venv.yml')) or {}
        name = name or venv.get('name')
        if not name:
            raise Exception('venv name not defined, neither command nor config file.>')
        if name in registry:
            raise Exception('{} venv already installed, clear it try again.'.format(name))

        registry['origin'] = url
        registry['path'] = self._directory
        environment = venv.get('environment')
        if environment:
            registry['environment'] = environment
        mkdir(self._directory)
        hconf.save()

        self._initialize(name)

    @property
    def home_config(self):
        with environment_append({'EPM_HOME_DIR': None}):
            global_api = API(self._api.out)
            return global_api.config

    @property
    def hapi(self):
        '''HOME API'''
        if self._hapi is None:
            with environment_append({'EPM_HOME_DIR': None}):
                self._hapi = API()
        return self._hapi

    def clear(self, name, do_clear=False):
        hapi = self.hapi
        hconf = hapi.config
        registry = hconf.registry.get('virtual-environment', {})
        if not name or name not in registry:
            print('do nothing as %s is not a setup virtual environment' % name)
            return

        info = registry[name]
        instd = info.get('path')
        del registry[name]

        hconf.save()

    def shell(self, name=None):
        hapi = self.hapi
        hconf = hapi.config
        registry = hconf.registry.get('virtual-environment', {})
        name = '~' if name is None else name
        scripts = ['active.bat', 'active.sh', 'bash.rc']

        if name == '~':
            path = hapi.home_dir
            for i in scripts:
                filename = os.path.join(path, i)
                if not os.path.exists(filename):
                    self._initialize(None)
                    break
        else:
            if name not in registry:
                raise EException('%s virtual environment was registered.')
            path = registry[name]['path']

            for i in ['active.bat', 'active.sh', 'bash.rc']:
                filename = os.path.join(path, i)
                if not os.path.exists(filename):
                    raise EException('%s virtual environment may not setup.' % name)

        filename = os.path.join(path, 'active.{}'.format('bat' if PLATFORM == 'Windows' else 'sh'))
        rcfile = os.path.join(path, 'bash.rc')

        env = os.environ.copy()
        if PLATFORM == 'Windows':
            subprocess.run(['cmd.exe', '/k', filename], env=env)
        else:
            subprocess.run(['/bin/bash', '--rcfile', rcfile], env=env)

    @staticmethod
    def banner():
        from epm.paths import get_epm_home_dir
        from conans.paths import get_conan_user_home
        from epm.tool import Dummy
        from epm.api import API
        api = API()
        conan = api.conan
        storage_path = conan.config_get('storage.path', quiet=True)

        return _Banner.format(name=os.environ.get('EPM_VENV_NAME'),
                              channel=os.environ.get('EPM_CHANNEL'),
                              instd=get_epm_home_dir(),
                              conan=conan.cache_folder, #os.path.join(get_conan_user_home(), '.conan'),
                              storage_path=storage_path)






