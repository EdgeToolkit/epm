import re
import os
from conans.model.requires import Requirement
from conans.model.ref import ConanFileReference
from conans.model.settings import Settings
from conans.model.options import OptionsValues

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
        settings = settings.values_list()

    vars.update(settings or {})
    if isinstance(options, OptionsValues):
        for (k, v) in options.as_list():
            vars['options.%s' % k] = v

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
    requires = Requirement()
    if not minfo:
        return requires
    any = settings is None and options is None
    packages = minfo.get('dependencies') or []
    for package in packages:
        for name, attr in package.items():
            if isinstance(attr, str):
                requires.add(attr)
            else:
                assert isinstance(attr, dict)
                if any or If(attr.get('if', settings, options)):
                    version = attr['version']
                    user = attr.get('user')
                    channel = attr.get('channel')
                    ref = ConanFileReference(name, version, user, channel)
                    requires.add_ref(ref)
    return requires