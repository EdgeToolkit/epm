
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
from epm.paths import get_epm_cache_dir
from epm.api import API
from epm.paths import HOME_EPM_DIR, DATA_DIR
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
  
  {description}

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

#def get_venv_install_dir(name):
#    path = os.path.join(HOME_EPM_DIR, 'venv', name)
#    if not os.path.exists(path):
#        return None
#    if os.path.isdir(path):
#        return path
#    elif os.path.isfile(path):
#        with open(path) as f:
#            m = yaml.safe_load(f)
#            path = m['location']
#            return path
#    else:
#        return None

def load_virtual_environment(path):
    name = None
    location = path
    config = {}
    if os.path.exists(path) and os.path.isfile(path):
        with open(path) as f:
            m = yaml.safe_load(f)
            location = m['location']
    assert os.path.isdir(location)
    with open(os.path.join(location, 'config.yml')) as f:
        config = yaml.safe_load(f)
        name = config['venv']['name']
    return {
        'name': name,
        'location': location,
        'config': config
    }


def get_all_installed_venv_info():
    path = os.path.join(HOME_EPM_DIR, 'venv')
    if not os.path.exists(path):
        return {}

    results = {}
    for name in os.listdir(path):
        info = load_virtual_environment(os.path.join(path, name))
        results[info['name']] = info
#        name = folder
#        location = os.path.join(path, name)
#        if os.path.isfile(location):
#            with open(path) as f:
#                m = yaml.safe_load(f)
#                location = m['location']
#        assert os.path.isdir(location)
#        with open(os.path.join(location, 'config.yml')) as f:
#            config = yaml.safe_load(f)
#        results[name] = {
#            'name': name,
#            'location': location,
#            'config': config
#        }
    return results



def banner(name=None):
    from epm.tool.conan import get_channel
    from epm.api import API
    infos = get_all_installed_venv_info()

    name = name or os.environ.get('EPM_VIRTUAL_ENVIRONMENT')
    info = infos.get(name)
    if not info:
        return " ? ? ? ?"
    instd = info['location']
    api = API(instd)
    conan = api.conan
    storage = conan.config_get('storage.path', quiet=True)
    desc = info['config'].get('venv', {}).get('description')
    desc = "\n  ".join(desc.split("\n"))

    return _Banner.format(name=name,
                          channel=get_channel(),
                          instd=instd,
                          conan=conan.cache_folder,  # os.path.join(get_conan_user_home(), '.conan'),
                          storage_path=storage,
                          description=desc)
def _cache(path):
    url = urlparse(path)
    folder = path
    download_dir = tempfile.mkdtemp(suffix='epm.venv')


    if url.scheme in ['http', 'https']:
        filename = os.path.join(download_dir, os.path.basename(path))
        urllib.request.urlretrieve(path, filename)
        folder = os.path.join(download_dir, 'venv.config')
        zfile = zipfile.ZipFile(filename)
        zfile.extractall(folder)
    elif url.scheme.startswith('git+'):
        url = path[4:]
        branch = None
        fields = url.split('@')
        options = ['--depth', '1']
        if len(fields) > 1:
            url = fields[0]
            branch = fields[-1]
            options += ['-b', branch]

        subprocess.run(['git', 'clone', url, download_dir] + options)
        rmdir(os.path.join(download_dir, '.git'))
        folder = download_dir

    if not os.path.exists(folder):
        raise Exception('Invalid install path {}'.format(path))
    return folder


def install(origin, to=None, out=None):
    from conans.client.tools import ConanOutput
    from epm.model.config import Config

    out = out or ConanOutput(sys.stdout, sys.stderr, color=True)
    folder = _cache(origin)
#    with open(os.path.join(folder, 'config.yml')) as f:
#        config = yaml.safe_load(f)
    config = Config(os.path.join(folder, 'config.yml'))

    name = config.venv.name
    instd = os.path.join(HOME_EPM_DIR, 'venv', name)
    if os.path.exists(instd):
        raise EException('%s virtual environment already installed, please check %s' % (name, instd))
    if to:
        with open(instd, 'w') as f:
            f.write(to)
            f.flush()
            f.close()
        instd = to

    from epm.util.files import rmdir, mkdir
    rmdir(instd)

    # copy files
    shutil.copytree(folder, dst=instd)


    scripts = ['active.bat', 'active.sh', 'bash.rc']
    for i in scripts:
        def _render(filename):
            jinja2 = Environment(loader=PackageLoader('epm', 'data/venv'))
            tmpl = jinja2.get_template(filename + '.j2')
            content = tmpl.render(config=config)
            save(os.path.join(instd, filename), content)
        if not os.path.exists(os.path.join(instd, i)):
            _render('active.bat')
            _render('active.sh')
            _render('bash.rc')
    conand = os.path.join(instd, '.conan')
    mkdir(conand)
    conan_conf = os.path.join(conand, 'conan.conf')
    if not os.path.exists(conan_conf):
        shutil.copy(os.pah.join(DATA_DIR, 'venv', '.conan', 'conan.conf'),
                    os.path.join(instd, '.conan', 'conan.conf'))

    conan_db = os.path.join(conand, '.conan.db')

    if config.venv.with_default_profiles:
        from epm.model.profile import Profile
        Profile.install_default_profiles(folder)


    # remotes clear
    from conans.client.conan_api import ConanAPIV1 as ConanAPI
    conan = ConanAPI(conand)
    conan.remote_clean()
    for remote in config.remotes:
        conan.remote_add(remote.name, remote.url, verify_ssl=False)
        if remote.username:
            conan.user_set(remote.username, remote.name)

    out.info(_SetupHint.format(name=config.venv.name))


def active(name):
    path = os.path.join(HOME_EPM_DIR, 'venv', name)
    if not os.path.exists(path):
        raise EException('Virtual environment %s not installed.' % name)
    folder = path
    if os.path.isfile(path):
        with open(path) as f:
            folder = f.read().strip()
            if not os.path.isdir(folder):
                raise EException('the actual installed folder %s not exists.' % folder)
    with open(os.path.join(folder, 'config.yml')) as f:
        config = yaml.safe_load(f)

    filename = os.path.join(folder, 'active.{}'.format('bat' if PLATFORM == 'Windows' else 'sh'))
    rcfile = os.path.join(folder, 'bash.rc')

    env = os.environ.copy()
    if PLATFORM == 'Windows':
        subprocess.run(['cmd.exe', '/k', filename], env=env)
    else:
        subprocess.run(['/bin/bash', '--rcfile', rcfile], env=env)

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

        path = hapi.cache_dir
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
        with environment_append({'EPM_CACHE_DIR': None}):
            global_api = API(self._api.out)
            return global_api.config

    @property
    def hapi(self):
        '''HOME API'''
        if self._hapi is None:
            with environment_append({'EPM_CACHE_DIR': None}):
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
            path = hapi.cache_dir
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
        from epm.paths import get_epm_cache_dir
        from conans.paths import get_conan_user_home
        from epm.tool import Dummy
        from epm.api import API
        api = API()
        conan = api.conan
        storage_path = conan.config_get('storage.path', quiet=True)

        return _Banner.format(name=os.environ.get('EPM_VENV_NAME'),
                              channel=os.environ.get('EPM_CHANNEL'),
                              instd=get_epm_cache_dir(),
                              conan=conan.cache_folder,  #os.path.join(get_conan_user_home(), '.conan'),
                              storage_path=storage_path)
