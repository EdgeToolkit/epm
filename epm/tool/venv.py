
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

_ACTIVE_BASH = r'''#!/bin/bash
_WD=$(cd $(dirname "${BASH_SOURCE[0]}"); $PWD)

if [[ -n "$EPM_VENV_NAME" ]]
then
  echo "Already in virtual environment <$EPM_VENV_NAME>, you have to exits this venv, then try again."
  exit/b 1
fi

export EPM_VENV_NAME=~/.epm
export EPM_HOME_DIR=~/.epm
export CONAN_USER_HOME=$EPM_HOME_DIR
export EPM_CHANNEL=public

epm venv banner

if [[ -n $TERM ]]
then
        PS1='\[\033[02;32m\]\u@\h (@epm.venv)\[\033[02;34m\] \w \n\$\[\033[00m\] '
else
        PS1='\u@\h (@epm.venv) \w \n\$ '
fi
'''

_ACTIVE_BAT = r'''
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

        self._render('active.bat.j2', 'active.bat')
        self._render('active.sh.j2', 'active.sh')
        self._render('bash.rc.j2', 'bash.rc')

        self._out.info(_SetupHint.format(name=self._name))

    def _render(self, template, filename, venv=None):
        venv = venv or self._venv
        tmpl = self._jinja2.get_template(template)
        content = tmpl.render(name=venv.get('name', ''),
                              path=venv['install-dir'],
                              channel=venv.get('channel', 'public'))
        print('~~~~~~~`', filename)
        save(filename, content)

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
            venv = {'name': '', 'install-dir':instd, 'channel': 'public'}
            for i in ['active.bat', 'active.sh', 'bash.rc']:
                filename = os.path.join(instd, i)
                if not os.path.exists(filename):
                    self._render('%s.j2' % i, filename, venv)
        else:
            venv = reg.get(name)
            if not venv:
                self._out.error('{} venv not setup.'.format(name))
                return

            instd = venv.get('install-dir')
            if not instd or not os.path.exists(instd):
                self._out.error('{} install dir({}) was destroyed.'.format(name, instd))
                return

        filename = os.path.join(instd, 'active.{}'.format('bat' if PLATFORM == 'Windows' else 'sh'))
        rcfile = os.path.join(instd, 'bash.rc')

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
                              conan=os.path.join(get_conan_user_home(), '.conan'),
                              storage_path=storage_path)






