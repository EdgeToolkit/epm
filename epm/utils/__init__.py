import os
import sys
import pathlib
import yaml
from conans.client.conan_api import ConanAPIV1 as ConanAPI

from epm import HOME_DIR
from epm.enums import Platform, Architecture
from epm.errors import EException


def windows_arch():
    """
    Detecting the 'native' architecture of Windows is not a trivial task. We
    cannot trust that the architecture that Python is built for is the 'native'
    one because you can run 32-bit apps on 64-bit Windows using WOW64 and
    people sometimes install 32-bit Python on 64-bit Windows.
    """
    # These env variables are always available. See:
    # https://msdn.microsoft.com/en-us/library/aa384274(VS.85).aspx
    # https://blogs.msdn.microsoft.com/david.wang/2006/03/27/howto-detect-process-bitness/
    arch = os.environ.get('PROCESSOR_ARCHITEW6432', '').lower()
    if not arch:
        # If this doesn't exist, something is messing with the environment
        try:
            arch = os.environ['PROCESSOR_ARCHITECTURE'].lower()
        except KeyError:
            raise EException('Unable to detect Windows architecture')
    return arch


def system_info():
    '''
    Get the sysem information.
    Return a tuple with the platform type, the architecture and the
    distribution
    '''
    # Get the platform info
    platform = os.environ.get('OS', '').lower()
    if not platform:
        platform = sys.platform
    if platform.startswith('win'):
        platform = Platform.WINDOWS
    elif platform.startswith('darwin'):
        platform = Platform.DARWIN
    elif platform.startswith('linux'):
        platform = Platform.LINUX
    else:
        raise EException("Platform %s not supported" % platform)

    # Get the architecture info
    if platform == Platform.WINDOWS:
        arch = windows_arch()
        if arch in ('x64', 'amd64'):
            arch = Architecture.X86_64
        elif arch == 'x86':
            arch = Architecture.X86
        else:
            raise EException(_("Windows arch %s is not supported") % arch)
    else:
        uname = os.uname()
        arch = uname[4]
        if arch == 'x86_64':
            arch = Architecture.X86_64
        elif arch.endswith('86'):
            arch = Architecture.X86
        elif arch.startswith('armv7'):
            arch = Architecture.ARMv7
        elif arch.startswith('arm'):
            arch = Architecture.ARM
        else:
            raise EException(_("Architecture %s not supported") % arch)

    return platform, arch



def is_elf(filename):
    with open(filename, 'rb') as f:
        return f.read(4) == b'\x7fELF'

    return False


def XSym(filename):
    with open(filename) as f:
        line = f.readline(256).replace('\n', '')
        if line == 'XSym':
            f.readline(256)
            f.readline(256)
            line = f.readline(256).replace('\n', '')
            return line if line else None
    return None


def sempath(path, prefixes, format='${%s}'):
    """ semantic path, replace path prefix with folders value and return the met one
    """
    if isinstance(prefixes, str):
        prefixes = [prefixes]

    for i in prefixes:
        if isinstance(i, str):
            name, prefix = i.split('=', 1)
        elif isinstance(i, tuple):
            name, prefix = i
        else:
            raise SyntaxError('kwargs must be str or tuple.')

        try:
            tail = pathlib.PurePath(path).relative_to(prefix)
        except:
            continue
        return '%s/%s' % (format % name, tail.as_posix())

    return None


def symbolize(string):
    """ symbolize the string by replace non identifier char to '_'

    :param string: the string to be symbolized
    :return:
    """
    symbol = "".join(['_' if s in r"-.@:\\/" else s for s in string])
    if not symbol.isidentifier():
        raise SyntaxError('{} can not be converted to symbol.'.format(string))
    return symbol


def get_workbench_dir(name=None):
    workbench = os.path.join(HOME_DIR, '.workbench')
    if not name or name in ['default']:
        return HOME_DIR

    path = os.path.join(workbench, name)
    if os.path.isfile(path):
        with open(path) as f:
            path = f.read().strip()
            return path

    if os.path.isdir(path):
        return path

    return None


def banner_display_mode():
    banner = os.getenv('EPM_BANNER_DISPLAY_MODE') or 'auto'
    banner = banner.lower()
    if banner in ['no', 'false', 'off', 'disable']:
        banner = 'no'
    return banner


def conanfile_inspect(path, attributes=None):
    if not os.path.exists(path):
        return None
    attributes = attributes or ['generators', 'exports', 'settings', 'options', 'default_options',
                                '__meta_information__']
    conan = ConanAPI()
    return conan.inspect(path, attributes)


def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)


def load_yaml(path, default=None):
    if not os.path.exists(path):
        if default is None:
            raise IOError(path)
        return default

    with open(path) as f:
        return yaml.safe_load(f)


def save_yaml(data, path):
    with open(path, 'w') as f:
        yaml.safe_dump(data, f)


