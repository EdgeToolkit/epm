
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
     / ____/ __ \/  |/  / WORK ENVIROMENT {name}
    / __/ / /_/ / /|_/ /  
   / /___/ ____/ /  / /   Default channel: {channel}
  /_____/_/   /_/  /_/    
                               
  * directory     : {instd}
  * conan         : {conan}
  * conan storage : {storage_path}
  
  {description}

'''

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
    from epm.tool.conan import get_channel
    from epm.api import API
    infos = get_all_installed_wenv_info()
    name = name or os.getenv('EPM_WORK_ENVIRONMENT')

    info = infos.get(name)
    if not info:
        return "Can not find %s in installed work environment." % name
    instd = info['location']
    api = API(instd)
    conan = api.conan
    storage = conan.config_get('storage.path', quiet=True)
    desc = info['config'].get('wenv', {}).get('description')
    desc = "\n  ".join(desc.split("\n"))

    from os.path import normpath as _

    return _Banner.format(name=name,
                          channel=get_channel(),
                          instd=_(instd),
                          conan=_(conan.cache_folder),
                          storage_path=_(storage),
                          description=desc)


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


def install(origin, to=None, out=None):
    from conans.client.tools import ConanOutput
    from epm.model.config import Config

    out = out or ConanOutput(sys.stdout, sys.stderr, color=True)
    folder = _cache(origin)
    config = Config(os.path.join(folder, 'config.yml'))

    name = config.wenv.name
    instd = os.path.join(HOME_EPM_DIR, 'wenv', name)
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
            jinja2 = Environment(loader=PackageLoader('epm', 'data/wenv'))
            tmpl = jinja2.get_template(filename + '.j2')
            content = tmpl.render(config=config)
            save(os.path.join(instd, filename), content)
        if not os.path.exists(os.path.join(instd, i)):
            _render('active.bat')
            _render('active.sh')
            _render('bash.rc')
    conand = os.path.join(instd, '.conan')
    mkdir(conand)

    from conans.client.conan_api import ConanAPIV1 as ConanAPI
    conan = ConanAPI(conand)
    conan.remote_clean()
    for remote in config.remotes:
        conan.remote_add(remote.name, remote.url, verify_ssl=False)
        if remote.username:
            conan.user_set(remote.username, remote.name)

    out.info(_SetupHint.format(name=config.wenv.name))


def active(name):

    path = os.path.join(HOME_EPM_DIR, 'wenv', name)
    if not os.path.exists(path):
        raise EException('Work environment %s not installed.' % name)
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

    from conans.client.tools import environment_append

    infos = get_all_installed_wenv_info()

    info = infos.get(name)
    if not info:
        return "Can not find %s in installed work environment." % name
    instd = info['location']
    api = API(instd)
    conan = api.conan
    storage = conan.config_get('storage.path', quiet=True)
    # TODO: add short_path handle
    env_vars = {'CONAN_STORAGE_PATH': storage,
                'CONAN_USER_HOME': instd,
               }

    with environment_append(env_vars):
        if PLATFORM == 'Windows':
            subprocess.run(['cmd.exe', '/k', filename])
        else:
            subprocess.run(['/bin/bash', '--rcfile', rcfile])

