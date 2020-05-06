
import os
import platform
import filecmp
import time
from epm.util.files import save


from conans.paths import conan_expand_user

def get_epm_cache_dir(name=None):
    from epm.tool import wenv
    ci_venvd = os.getenv('EPM_CI_WORK_ENVIRONMENT_DIR')
    if ci_venvd:
        return ci_venvd
    folder = HOME_EPM_DIR
    wname = name or os.getenv('EPM_WORK_ENVIRONMENT')
    if wname:
        infos = wenv.get_all_installed_wenv_info()
        if not infos.get(wname):
            raise Exception('epm work environment <%s> not exists' % vname)
        folder = infos[wname]['location']
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
