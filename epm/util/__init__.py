import os
import sys
import yaml
import pathlib
from epm.enums import Platform, Architecture
from epm.errors import EException


#class ArgparseArgument(object):
#
#    def __init__(self, *name, **kwargs):
#        self.name = name
#        self.args = kwargs
#
#    def add_to_parser(self, parser):
#        parser.add_argument(*self.name, **self.args)
#

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

def sempath(path, kwords, format='${%s}'):
    """ semantic path, replace path prefix with folders value and return the met one

    :param path: <string> to semantic
    :param prefixs: ordered dict name: directory
    :return:
    """
    for i in kwords:
        if isinstance(i, str):
            name, prefix = i.split('=', 1)
        elif isinstance(i, tuple):
            name, prefix = i
        else:
            raise SyntaxError('kwords must be str or tuple.')

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


#def split_plan_name(c):
#    """split the configuration option to profile and scheme
#
#    :param c: configuration string token
#    :return: tuple profile, scheme
#    """
#    tokens = c.split('@', 1)
#    profile = tokens[0]
#    scheme = None
#    if len(tokens) == 2:
#        if tokens[1] not in ['default']:
#            scheme = tokens[1]
#    return profile, scheme
#
#
#def merge_plan_name(profile, scheme=None):
#    """merge the profile and scheme to a configuration string
#
#    :param profile:
#    :param scheme:
#    :return:
#    """
#    return profile + '@%s' % scheme if scheme else ''



##################################
_debug_configuration = None


def _get_debug_configuration():
    global _debug_configuration
    if _debug_configuration is None:
        _debug_configuration = {}
        filename = os.getenv('EPM_DEBUG_CONFIG_FILE')
        if filename:
            if os.path.exists(filename):
                try:
                    with open(filename) as f:
                        _debug_configuration = yaml.safe_load(f)
                except Exception as e:
                    print('load debug config file %s failed.\n%s' % (filename, e))
                print('==== EPM_DEBUG_CONFIG_FILE: %s ====' % filename)
                import pprint
                pprint.pprint(_debug_configuration, depth=10, indent=2)
            else:
                print('the specified debug config file <%s> not exists' % filename)
    return _debug_configuration
