
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
from epm.util.files import load_yaml, save_yaml, save, rmdir

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
class VirtualEnviron(object):

    def __init__(self, name=None, directory=None, out=None):
        self._name = name or os.environ.get('EPM_VENV_NAME')
        self._directory = directory or os.environ.get('EPM_VENV_DIR') or os.path.abspath('.')
        self._reg_filename = os.path.expanduser('~/.epm/venv.yml')
        self._jinja2 = Environment(loader=PackageLoader('epm', 'data/venv'))
        self._venv = None

        self._out = out or Output(sys.stdout)

    def register(self):
        if not os.path.exists(self._reg_filename):
            return {}
        return load_yaml(self._reg_filename) or {}

    def update(self, venv, name=None):
        name = name or self._name
        reg = self.register()
        if name in reg and venv is None:
            del reg[name]
        else:
            reg[name] = venv
        save_yaml(self._reg_filename, reg)

    def install_source(self, path):
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

    def setup(self, url, name=None):

        reg = self.register() or {}
        if name in reg:
            raise Exception('{} venv already installed, clear it try again.'.format(self._name))

        if os.path.exists('.conan'):
            raise Exception('current directory is dirty .conan is exits.')

        instd = self.install_source(url)
        path = os.path.join(instd, 'config.yml')
        conf = load_yaml(path) or {}
        self._name = name = name or conf.get('name')
        if not name:
            raise Exception('venv name not defined, neither command nor config file.>')

        if name in reg:
            raise Exception('{} venv already installed, clear it try again.'.format(self._name))

        wd = os.path.abspath('.')
        channel = conf.get('channel', 'public')
        self._venv = {
            'install-source': url,
            'name': name,
            'install-dir': wd,
            'config': conf,
            'channel': channel,
        }
        remotes = conf.get('remotes')
        if remotes:
            self._venv['remotes'] = remotes

        self.update(self._venv, name)

        from epm.api import API
        api = API(wd)
        conan = api.conan
        conan.remote_clean()
        conan.users_clean()

        remotes = conf.get('remotes', [])
        for remote in remotes:
            for name, url in remote.items():
                conan.remote_add(name, url, verify_ssl=True)

        def render(template, filename):
            tmpl = self._jinja2.get_template(template)
            content = tmpl.render(name=self._venv['name'],
                                  path=self._venv['install-dir'],
                                  channel=channel)

            with open(filename, 'w') as f:
                f.write(content)

        render('active.bat', 'active.bat')
        render('active.sh', 'active.sh')
        self._out.info(_SetupHint.format(name=self._name))

    def clear(self, name, do_clear=False):
        reg = self.register()
        if not name or name not in reg:
            print('do nothing as %s is not a setup virtual environment' % name)
            return

        info = reg[name]
        instd = info.get('install-dir')

        self.update(None, name)
        if do_clear:
            if os.path.exists(instd):
                rmdir(instd)
        else:
            print('install dir <%s> not clean' % instd)

    def shell(self, name=None):
        if os.getenv('EPM_VENV_NAME'):
            self._out.error('running in %s virtual environment, can not open another venv shell.')
            return

        reg = self.register()

        if name is None:
            from epm.paths import get_epm_home_dir
            instd = get_epm_home_dir()
        else:
            venv = reg.get(name)
            if not venv:
                self._out.error('{} venv not setup.'.format(name))
                return

            instd = venv.get('install-dir')
            if not instd or not os.path.exists(instd):
                self._out.error('{} install dir({}) was destroyed.'.format(name, instd))
                return

        script = os.path.join(instd, 'active.{}'.format('bat' if PLATFORM == 'Windows' else 'sh'))

        env = os.environ.copy()
        if PLATFORM == 'Windows':
            subprocess.run(['cmd.exe', '/k', script], env=env)
        else:
            # TODO:
            pass
            #subprocess.run(['/bin/bash','-i', script)

    def active(self):
        env = os.environ.copy()
        if env.get('EPM_VENV_NAME') or env.get('EPM_VENV_DIR'):
            self._out.error('venv can not be active in a venv shell.')
            return

        reg = self.register()
        venv = reg.get(self._name)
        if not venv:
            self._out.error('{} venv not setup.'.format(self._name))
            return

        instd = venv.get('install-dir')
        if not instd or not os.path.exists(instd) or \
                not os.path.isdir(instd + '/.conan') or \
                not os.path.isdir(instd + '/.epm') or \
                not os.path.isfile(instd + '/active.bat') or\
                not os.path.isfile(instd + '/active.sh'):
            self._out.error('{} install dir({}) was destroyed.'.format(self._name,instd))
            return

        script = os.path.join(instd, 'active.{}'.format('bat' if PLATFORM == 'Windows' else 'sh'))

        if PLATFORM == 'Windows':
            subprocess.run(['cmd.exe', '/k', script], env=env)
        else:
            # TODO:
            pass
            #subprocess.run(['/bin/bash','-i', script)

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
                              conan=os.path.join(get_conan_user_home(), '.conan'),
                              storage_path=storage_path)






