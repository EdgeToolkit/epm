import re
import os
import pathlib
from collections import namedtuple
from conans.model.requires import Requirements
from conans.model.ref import ConanFileReference
from conans.model.settings import Settings
from conans.model.options import Options, PackageOptionValues, OptionsValues


def get_channel(user):
    if user is None:
        return None
    symbol = re.sub(r'\-', '_', user)
    channel = os.getenv('EPM_DEFAULT_CHANNEL_%s' % symbol.upper())
    return channel or 'public'


def If(expr, settings, options):
    if not expr:
        return True

    vars = {}
    if isinstance(settings, Settings):
        settings = {k: v for(k, v) in settings.values_list}

    vars.update(settings or {})

    if isinstance(options, Options):
        options = {'options.%s' % k: v for (k, v) in options.values.as_list()}
    vars.update(options or {})

    from epm.utils.yacc.condition import Yacc
    yacc = Yacc(vars)

    return yacc.parse(expr)


def parse_multi_expr(m, settings, options):
    """

    :param m: multi expression list (item is dict) or dict

    :param settings:
    :param options:
    :return:
    """
    for exprs in m if isinstance(m, list) else [m]:
        for name, expr in exprs.items():
            assert isinstance(name, (str, float, int)) and isinstance(expr, str)
            if If(expr, settings, options):
                return name  # specified
    return None


def create_requirements(minfo, settings=None, options=None):
    ''' create requirements (conan reference order dict name: reference)

    :param minfo: meta information dict
    :param settings:
    :param options:
    :return:
    '''
    requires = Requirements()
    if not minfo:
        return requires
    any = settings is None and options is None
    packages = minfo.get('dependencies') or {}
    for name, attr in packages.items():
        if isinstance(attr, (str, int, float)):
            ref = ConanFileReference(name, str(attr), '_', '_')
            requires.add_ref(ref)
        else:
            assert isinstance(attr, dict)
            if any or If(attr.get('if'), settings, options):
                version = str(attr['version'])
                user = attr.get('user')
                channel = attr.get('channel') or get_channel(user)
                private = attr.get('private') is True
                override = attr.get('override') is True

                ref = ConanFileReference(name, version, user, channel)
                requires.add_ref(ref, private=private, override=override)
    return requires


def add_build_requirements(requires, minfo, settings=None, options=None):
    ''' create requirements (conan reference order dict name: reference)

    :param minfo: meta information dict
    :param settings:
    :param options:
    :return:
    '''
    if not minfo:
        return requires

    default_user = 'build-tools'
    default_channel = 'public'

    any = settings is None and options is None
    packages = minfo.get('build-tools') or {}

    for name, attr in packages.items():

        if isinstance(attr, (str, int, float)):
            ref = ConanFileReference(name, str(attr), default_user, default_channel)
            requires(ref)
        else:
            assert isinstance(attr, dict)


            if any or If(attr.get('if'), settings, options):
                print(name, attr, '~~~~~~~~~~~', options, settings)

                version = str(attr['version'])
                user = attr.get('user') or default_user
                channel = attr.get('channel') or default_channel
                ref = ConanFileReference(name, version, user, channel)

                requires(ref)
    return requires

def parse_sandbox(manifest):
    _P_PROJECT = r'(?P<project>\w[\w\-]+)/'
    _P_TYPE = r'((?P<project>\w[\w\-]+)/)?(?P<type>(build|package))/'
    _P_FOLDER = r'(?P<folder>bin)?'
    _P_PROGRAM = r'/(?P<program>\w[\w\-]+)'
    _SANDBOX_PATTERN = re.compile(_P_TYPE + _P_FOLDER + _P_PROGRAM + r'$')

    Sandbox = namedtuple('Sandbox', 'content name directory type folder program param argv ports privileged')
    result = {}
    ports = []
    privileged = False
    for name, item in manifest.get('sandbox', {}).items():

        cmdstr = item
        if isinstance(item, dict):
            cmdstr = item['command']
            ports = item.get('ports', []) or []
            if isinstance(ports, int):
                ports = [ports]
            privileged = item.get('privileged', False)

        parts = cmdstr.split(' ', 1)
        command = parts[0]
        command = pathlib.PurePath(command).as_posix()
        param = None if len(parts) < 2 else parts[1].strip()
        argv = param.split() if param else []
        m = _SANDBOX_PATTERN.match(command)
        if not m:
            raise Exception('sandbox {} invalid'.format(name))

        result[name] = Sandbox(item, name,
                               m.group('project'), m.group('type'),
                               m.group('folder'), m.group('program'),
                               param, argv, ports, privileged)

    return result