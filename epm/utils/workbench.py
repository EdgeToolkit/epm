
import os
import sys

import urllib
import shutil
import zipfile
import tempfile
import subprocess
from urllib.parse import urlparse

from conans.util.files import rmdir, mkdir
from conans.client.tools import environment_append


from epm import __version__, HOME_DIR
from epm.utils import PLATFORM, banner_display_mode

from epm.errors import EException
from epm.api import API
from epm.model.runner import Output
from epm.model.config import Config




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


_LOGO_DOCKER = r'''
     __________  __  ___
    / ____/ __ \/  |/  /  {epm_version:<17} 
   / __/ / /_/ / /|_/ / 
  / /___/ ____/ /  / /            ## ## ##        ==          
 /_____/_/   /_/  /_/          ## ## ## ## ##    ===          
                           /"""""""""""""""""\___/ ===        
 ~~~~~~~~~~~~~~~~~~~~~~~~~ {{~~ ~~~~ ~~~ ~~~~ ~~~ ~ /  ===- ~~~ 
                            \______ o           __/            
                              \    \         __/               
                               \____\_______/ {docker_image:<16}
'''


_DOCKER = r'''
              
                EPM: {epm_version:<17}
              
                        ## ## ##        ==          
                     ## ## ## ## ##    ===          
                 /"""""""""""""""""\___/ ===        
 ~~~~~~~~~~~~~~ {{~~ ~~~~ ~~~ ~~~~ ~~~ ~ /  ===- ~~~ 
                 \______ o           __/            
                   \    \         __/               
                    \____\_______/ {docker_image:<16}
'''





def banner(name=None):
    image = os.getenv('EPM_DOCKER_IMAGE') or ''
    logo = _DOCKER if image else _LOGO

    name = name or os.getenv('EPM_WORKBENCH')

    txt = logo.format(epm_version=__version__, docker_image=image, name=name)

    if banner_display_mode() != 'no':
        print(txt)
    return banner


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


def install(origin, editable=False, out=None):
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

    banner(name)



_CMD = r'''
@ECHO OFF
title Workbench - {name}
prompt $p [workbench - {name}] $_$$

'''

_RCFILE = r'''
export PS1='\[\033[01;32m\]\u@\h - workbench - {name}\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\n\$ '
'''
#subprocess.call("(dir 2>&1 *`|echo CMD);&<# rem #>echo PowerShell", shell=True)
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
    else:
        folder = HOME_DIR
        name = 'default'
    config = Config(os.path.join(folder, 'config.yml'))
    api = API(workbench=name)
    storage = api.conan_storage_path
    # TODO: add short_path handle
    env_vars = {'CONAN_STORAGE_PATH': storage,
                'CONAN_USER_HOME': api.workbench_dir,
                'EPM_WORKBENCH': name,
                'CONAN_USER_HOME_SHORT': config.conan.short_path
               }

    env_vars.update(config.environment)

    with environment_append(env_vars):
        win = PLATFORM == 'Windows'
        filename = 'startup.cmd' if win else 'bash.rc'
        filename = os.path.join(folder, filename)
        txt = _CMD if win else _RCFILE
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                f.write(txt.format(name=name))
                f.close()
        banner(name)
        print('\n')
        print(' {:>16}: {}'.format('workbench', os.getenv('EPM_WORKBENCH')))
        print(' {:>16}: {}'.format('home', os.getenv('CONAN_USER_HOME')))
        print(' {:>16}: {}'.format('storage', os.getenv('CONAN_STORAGE_PATH')))
        print(' {:>16}: {}'.format('short', os.getenv('CONAN_USER_HOME_SHORT')))
        print('\n')

        if win:
            subprocess.run(['cmd.exe', '/k', filename])
        else:
            subprocess.run(['/bin/bash', '--rcfile', filename])
    banner()

