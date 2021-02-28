import re
import os

import pathlib

from conans.tools import cross_building

from collections import namedtuple
from conans.model.requires import Requirements
from conans.model.ref import ConanFileReference
from conans.model.settings import Settings
from conans.model.options import Options


def get_channel(user):
    if user is None:
        return None
    symbol = re.sub(r'\-', '_', user)
    channel = os.getenv('EPM_%s_CHANNEL' % symbol.upper())
    return channel or 'public'


def If(expr, settings, options, conanfile=None, profile=None):
    if not expr:
        return True

    cross_build = None
    if conanfile:
        cross_build = cross_building(conanfile.settings, skip_x64_x86=True)

    elif profile:
        cross_build = True
        host = profile.host.settings
        build = profile.read_build_profile().settings
        print('Host:', host)
        print('Build:', build)
        if host['os'] == build['os']:
            if host['arch'] == build['arch']:
                cross_build = False
            if host['os'] == 'Windows' and \
                    build['arch'] in ['x86_64', 'x86'] and \
                    host['arch'] in ['x86_64', 'x86']:
                cross_build = False
    print('conanfile:', conanfile, 'cross_build:', cross_build)
    assert cross_build is not None

    symbol = {'cross_build': cross_build}

    if isinstance(settings, Settings):
        settings = {k: v for(k, v) in settings.values_list}

    symbol.update(settings or {})

    if isinstance(options, Options):
        options = {'options.%s' % k: v for (k, v) in options.values.as_list()}
    else:
        options = {'options.%s' % k: v for (k, v) in options.items()}

    symbol.update(options or {})
    from epm.utils.yacc.condition import Yacc
    yacc = Yacc(symbol)

    result = yacc.parse(expr)
    return result


def parse_multi_expr(m, settings, options, conanfile=None, profile=None):
    """

    :param m: multi expression list (item is dict) or dict

    :param settings:
    :param options:
    :return:
    """
    for exprs in m if isinstance(m, list) else [m]:
        for name, expr in exprs.items():
            assert isinstance(name, (str, float, int)) and isinstance(expr, str)
            if If(expr, settings, options, conanfile, profile):
                return name  # specified
    return None


def _Ver(ver, minfo):
    version = str(ver)
    if '$' in version:
        version = version.replace('${__version__}', str(minfo['version']))
    return version


def create_requirements(minfo, settings=None, options=None, conanfile=None, profile=None):
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
            version = _Ver(attr, minfo)
            ref = ConanFileReference(name, version, None, None)
            requires.add_ref(ref)
        else:
            assert isinstance(attr, dict)
            if any or If(attr.get('if'), settings, options, conanfile, profile):
                version = _Ver(attr['version'], minfo)
                user = attr.get('user')
                channel = attr.get('channel') or get_channel(user)
                private = attr.get('private') is True
                override = attr.get('override') is True

                ref = ConanFileReference(name, version, user, channel)
                requires.add_ref(ref, private=private, override=override)
    return requires


def create_build_tools(minfo, settings=None, options=None, conanfile=None, profile=None):
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
    packages = minfo.get('build-tools') or {}
    for name, attr in packages.items():
        if isinstance(attr, (str, int, float)):
            version = _Ver(attr, minfo)
            ref = ConanFileReference(name, version, None, None)
            requires.add_ref(ref)
        else:
            assert isinstance(attr, dict)
            if any or If(attr.get('if'), settings, options, conanfile, profile):
                version = _Ver(attr['version'], minfo)
                user = attr.get('user')
                channel = attr.get('channel') or get_channel(user)
                private = attr.get('private') is True
                override = attr.get('override') is True

                ref = ConanFileReference(name, version, user, channel)
                requires.add_ref(ref, private=private, override=override)

    return requires


def add_build_requirements(requires, minfo, settings=None, options=None, conanfile=None, profile=None):
    ''' create requirements (conan reference order dict name: reference)

    :param minfo: meta information dict
    :param settings:
    :param options:
    :return:
    '''
    if not minfo:
        return requires

    default_user = None
    default_channel = None

    any = settings is None and options is None
    packages = minfo.get('build-tools') or {}

    for name, attr in packages.items():

        if isinstance(attr, (str, int, float)):
            version = _Ver(attr, minfo)
            ref = ConanFileReference(name, version, default_user, default_channel)

            requires(ref)
        else:
            assert isinstance(attr, dict)

            if any or If(attr.get('if'), settings, options, conanfile, profile):

                version = _Ver(attr['version'], minfo)
                user = attr.get('user') or default_user
                channel = attr.get('channel') or default_channel
                ref = ConanFileReference(name, version, user, channel)
                force_host_context = True if attr.get('force_host_context') else None

                requires(ref, force_host_context=force_host_context)
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

