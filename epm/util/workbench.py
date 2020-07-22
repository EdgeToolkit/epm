
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
from epm.util import system_info
from epm.util.files import load_yaml, save_yaml, save, rmdir, mkdir
from epm.errors import EException
from epm.paths import get_epm_cache_dir
from epm.api import API
from epm.paths import HOME_EPM_DIR, DATA_DIR
from conans.tools import environment_append
from epm.model.runner import Output
from epm.model.config import Config
from conans.client.tools import environment_append
PLATFORM, ARCH = system_info()


_Banner = '''
                 
      __________  __  ___
     / ____/ __ \/  |/  / WORK ENVIROMENT {name}
    / __/ / /_/ / /|_/ /  
   / /___/ ____/ /  / /   Default channel: {channel}
  /_____/_/   /_/  /_/    
                               
  * directory     : {instd}
  * conan         : {conan}
  * conan storage : {storage_path}
  
  {description}

'''
_LOGO = '''

                                  M
                                 ' `
                                |  :|`-._
                                |  :|`-._`-._
                               /   ::\   `-._`-._
                              /     ::\      `-(_)
      __________  __  ___    |_________|      / /
     / ____/ __ \/  |/  /        `-'         / /
    / __/ / /_/ / /|_/ /                    / /
   / /___/ ____/ /  / /                    / /
  /_____/_/   /_/  /_/  {epm_version:<17} / /
 ________________________________________/ /________

'''



_LOGO_DOCKER = '''    
     __________  __  ___  
    / ____/ __ \/  |/  /  {epm_version:<17} 
   / __/ / /_/ / /|_/ /   
  / /___/ ____/ /  / /              ## ## ##        ==          
 /_____/_/   /_/  /_/            ## ## ## ## ##    ===          
                             /"""""""""""""""""\___/ ===        
 ~~~~~~~~~~~~~~~~~~~~~~~~~~~ {~~ ~~~~ ~~~ ~~~~ ~~~ ~ /  ===- ~~~ 
                              \______ o           __/            
                                \    \         __/               
                                 \____\_______/ {docker_image:<16}
'''




def banner(show='auto'):
    from epm import __version__
    image = os.getenv('EPM_DOCKER_IMAGE') or ''
    logo = _LOGO_DOCKER if image else _LOGO
    txt = logo.format(epm_version=__version__, docker_image=image)

    banner = os.getenv('EPM_DISPLAY_BANNER') or 'YES'
    if banner.lower() not in ['no']:
        print(txt)
    return txt


_SetupHint = '''
Work environment '{name}' setup done, run active script to active
In Windows
   $ active.bat
In Linux
   $ source ./active.sh

or use epm
   $ epm wenv shell {name}

'''


def load_virtual_environment(path):
    location = path
    if os.path.exists(path) and os.path.isfile(path):
        with open(path) as f:
            m = yaml.safe_load(f)
            location = m['location']
    assert os.path.isdir(location)
    with open(os.path.join(location, 'config.yml')) as f:
        config = yaml.safe_load(f)
        name = config['wenv']['name']
    return {
        'name': name,
        'location': location,
        'config': config
    }


def get_all_installed_wenv_info():
    path = os.path.join(HOME_EPM_DIR, 'wenv')
    if not os.path.exists(path):
        return {}

    results = {}
    for name in os.listdir(path):
        info = load_virtual_environment(os.path.join(path, name))
        results[info['name']] = info
    return results


def banner(name=None):
    name = name or os.getenv('EPM_WORKBENCH')
    from epm import __version__
    print(_LOGO.format(epm_version=__version__))



def _cache(path):
    url = urlparse(path)
    folder = path
    download_dir = tempfile.mkdtemp(suffix='epm.wenv')

    if url.scheme in ['http', 'https']:
        filename = os.path.join(download_dir, os.path.basename(path))
        urllib.request.urlretrieve(path, filename)
        folder = os.path.join(download_dir, 'wenv.config')
        zfile = zipfile.ZipFile(filename)
        zfile.extractall(folder)
    elif url.scheme.startswith('git+'):
        url = path[4:]
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

from epm import HOME_DIR

#subprocess.call("(dir 2>&1 *`|echo CMD);&<# rem #>echo PowerShell", shell=True)

def install(origin, editable, out=None):
    from epm.model.config import Config
    mkdir(os.path.join(HOME_DIR, '.workbench'))
    out = out or Output(sys.stdout, sys.stderr, color=True)
    folder = _cache(origin)
    config = Config(os.path.join(folder, 'config.yml'))

    name = config.workbench.name
    instd = os.path.join(HOME_DIR, '.workbench', name)
    if os.path.exists(instd):
        for i in range(1, 100):
            path = instd + str(i)
            if not os.path.exists(path):
                instd = path
                out.warn('{} workbench already installed install as {}{}'.format(name, name, i))
                break

    if editable:
        with open(instd, 'w') as f:
            f.write(folder)
        return

    shutil.copytree(folder, dst=instd)
    conand = os.path.join(instd, '.conan')
    mkdir(conand)

    from conans.client.conan_api import ConanAPIV1 as ConanAPI
    conan = ConanAPI(conand)
    conan.remote_clean()
    for remote in config.remotes:
        conan.remote_add(remote.name, remote.url, verify_ssl=False)
        if remote.username:
            conan.user_set(remote.username, remote.name)

    #out.info(_SetupHint.format(name=config.wenv.name))
    print(_LOGO)



_CMD = '''
@ECHO OFF
epm workbench banner

title Workbench - {name}
prompt $p [workbench - {name}] $_$$

'''


def active(name):
    if name:

        path = os.path.join(HOME_DIR, '.workbench', name)
        if not os.path.exists(path):
            raise EException('Workbench %s not installed.' % name)
        folder = path
        if os.path.isfile(path):
            with open(path) as f:
                folder = f.read().strip()
                if not os.path.isdir(folder):
                    raise EException('the actual installed folder %s not exists.' % folder)

        config = Config(os.path.join(folder, 'config.yml'))
    else:
        folder = HOME_DIR
        name = 'default'

    api = API(workbench=name)
    storage = api.conan_storage_path
    # TODO: add short_path handle
    env_vars = {'CONAN_STORAGE_PATH': storage,
                'CONAN_USER_HOME': api.conan_home,
                'EPM_WORKBENCH': name
               }
    print('=======================')
    print(env_vars)
    print('=======================')

    with environment_append(env_vars):
        if PLATFORM == 'Windows':
            filename = os.path.join(folder, 'startup.cmd')
            if not os.path.exists(filename):
                with open(filename, 'w') as f:
                    f.write(_CMD.format(name=name))
                    f.close()
            subprocess.run(['cmd.exe', '/k', filename])
        else:
            subprocess.run(['/bin/bash', '--rcfile', rcfile])

