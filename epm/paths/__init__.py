
import os
import platform
import filecmp
import time
from epm.util.files import save

from conans.paths import conan_expand_user

def get_epm_cache_dir(name=None):
    print(os.environ)
    folder = HOME_EPM_DIR
    vname = name or os.getenv('EPM_VIRTUAL_ENVIRONMENT')
    print('VName:', vname)
    if vname:
        from epm.tool.venv import get_all_installed_venv_info
        infos = get_all_installed_venv_info()
        if not infos.get(vname):
            raise Exception('epm virtual environment <%s> not exists' % vname)
        folder = infos[vname]['location']
    print('*', folder)
    return folder

#    home = os.getenv("EPM_CACHE_DIR") or "~/.epm"
#    tmp = conan_expand_user(home)
#    if not os.path.isabs(tmp):
#        raise Exception("Invalid EPM_CACHE_DIR value '%s', "
#                        "please specify an absolute or path starting with ~/ "
#                        "(relative to user home)" % tmp)
#    return os.path.abspath(tmp)



# Files and Folders

PACKAGEMETAFILE = "package.yml"
BUILDMETAFILE= "build-meta.yml"

BUILDFOLDER = 'build'
TESTBUILDFOLDER = 'test_build'
PACKAGEFOLDER = 'package'
PROFILES_FOLDER = 'profiles'

HOME_EPM_DIR = conan_expand_user("~/.epm")
if not os.path.exists(HOME_EPM_DIR):
    os.makedirs(HOME_EPM_DIR)

EPM_PROJECT_TEMPLATE_DIR = os.path.join(HOME_EPM_DIR, 'project-templates')

import epm
DATA_DIR = os.path.join(os.path.dirname(epm.__file__), 'data')
TEST_DATA_DIR = os.path.join(os.path.dirname(epm.__file__), 'test', 'data')


def is_home_epm_dir(folder):
    _MARKERFILE = '.home.epm.marker'
    marker = os.path.exists(HOME_EPM_DIR, _MARKERFILE)
    if not os.path.exists(marker):
        localtime = time.asctime(time.localtime(time.time()))
        save(marker, localtime)

    filename = os.path.join(folder, '_MARKERFILE')

    if not os.path.exists(marker):
        return False
    return filecmp.cmp(marker, filename)
