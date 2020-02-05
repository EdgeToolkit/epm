
import os
import platform

from conans.paths import conan_expand_user


def get_epm_user_home():
    user_home = os.getenv("EPM_USER_HOME", "~")
    tmp = conan_expand_user(user_home)
    if not os.path.isabs(tmp):
        raise Exception("Invalid EPM_USER_HOME value '%s', "
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
