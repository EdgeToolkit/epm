
import os
import platform
import filecmp
import time
from epm.util.files import save

from conans.paths import conan_expand_user

def get_epm_cache_dir(name=None):
    ci_venvd = os.getenv('EPM_CI_VIRTUAL_ENVIRONMENT_DIR')
    if ci_venvd:
        return ci_venvd
    folder = HOME_EPM_DIR
    vname = name or os.getenv('EPM_VIRTUAL_ENVIRONMENT')
    if vname:
        from epm.tool.venv import get_all_installed_venv_info
        infos = get_all_installed_venv_info()
        if not infos.get(vname):
            raise Exception('epm virtual environment <%s> not exists' % vname)
        folder = infos[vname]['location']
    return folder

PACKAGEMETAFILE = "package.yml"
BUILDMETAFILE= "build-meta.yml"

BUILDFOLDER = 'build'
TESTBUILDFOLDER = 'test_build'
PACKAGEFOLDER = 'package'
PROFILES_FOLDER = 'profiles'

HOME_EPM_DIR = conan_expand_user("~/.epm")
if not os.path.exists(HOME_EPM_DIR):
    os.makedirs(HOME_EPM_DIR)


import epm
DATA_DIR = os.path.join(os.path.dirname(epm.__file__), 'data')
TEST_DATA_DIR = os.path.join(os.path.dirname(epm.__file__), 'test', 'data')


def is_home_epm_dir(folder):
    return os.path.normpath(folder) == os.path.normpath(HOME_EPM_DIR)
