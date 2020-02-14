
import os
import platform

from conans.paths import conan_expand_user

def get_epm_home_dir():
    home = os.getenv("EPM_HOME_DIR") or "~/.epm"
    tmp = conan_expand_user(home)
    if not os.path.isabs(tmp):
        raise Exception("Invalid EPM_HOME_DIR value '%s', "
                        "please specify an absolute or path starting with ~/ "
                        "(relative to user home)" % tmp)
    return os.path.abspath(tmp)


# Files and Folders

PACKAGEMETAFILE = "package.yml"
BUILDMETAFILE= "build-meta.yml"

BUILDFOLDER = 'build'
TESTBUILDFOLDER = 'test_build'
PACKAGEFOLDER = 'package'


import epm
DATA_DIR = os.path.join(os.path.dirname(epm.__file__), 'data')
TEST_DATA_DIR = os.path.join(os.path.dirname(epm.__file__), 'test', 'data')
