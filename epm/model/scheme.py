import os
from conans.model.options import OptionsValues
from epm.util import system_info
from epm.utils import conanfile_inspect
from epm.tools import create_requirements
from epm.tools import If, parse_multi_expr

PLATFORM, ARCH = system_info()

'''
scheme:
  default: shared
  shared:
    options:
       xxx: yyy
       xxx: yyy
    zlib: shared
    libpng:
    - shared: os == Windows
'''


def parse_dep_scheme(default, scheme, requires, settings, options):
    """ parse specified scheme and return the dict with item package:schme

    :param default: undefined package scheme
    :param mdata: scheme defination [dict]
    :param scheme: scheme default name (the name of the schemd
    :param requires:
    :param settings:
    :param options:

    :return:
    """
    result = {}
    for ref in requires:
        expr = scheme.get(ref.name)
        if not expr:
            result[ref.name] = default
        elif isinstance(expr, str):
            result[ref.name] = expr
        elif isinstance(expr, (list, dict)):
            result[ref.name] = parse_multi_expr(expr, settings, options) or default
        else:
            raise NotImplementedError('not support ')
    return result


def parse_scheme_options(scheme, reference, settings, conan, requires=None):
    '''parse the specifed reference scheme options under the settings
    :param scheme: [str] scheme name
    :param reference: reference or path of conanfile
    :param settings: profile settings
    :param api:
    :return:
    '''
    if isinstance(reference, dict):
        conanfile = reference
    else:
        conanfile = conan.inspect(reference, ['default_options', '__meta_information__'])

    manifest = conanfile.get('__meta_information__')
    default_options = conanfile.get('default_options', {})
    if not manifest:
        return default_options, {}

    mdata = manifest.get('scheme', {}).get(scheme) or {}
    options = mdata.get('options') or {}

    default_options = conanfile.get('default_options') or {}
    opts = {k: options.get(k, v) for k, v in default_options.items()}
    requires = requires or create_requirements(manifest, settings, opts)
    if not requires:
        return options, {}

    reqs_options = {}
    deps = parse_dep_scheme(mdata, scheme, requires, settings, opts)

    for name, sch in deps.items():
        o, po = parse_scheme_options(sch, requires[name], settings, conan)
        reqs_options[name] = o
        reqs_options.update(po)

    return options, reqs_options


def parse_options(mdata, settings, default_options):
    options = {}
    for name, expr in mdata.items():
        value = expr if isinstance(expr, str) else parse_multi_expr(expr, settings, None)
        if not isinstance(value, str):
            raise Exception("option <%s> not able to parse" % name)
        options[name] = value
    return options, {k: options.get(k, v) for k, v in default_options.items()}


class Scheme(object):

    def __init__(self, project, name=None):
        self._name = name or project.attribute.scheme
        self._project = project
        self._manifest = project.__meta_information__ or {}
        self._mdata = self._manifest.get('scheme') or {}
        self._deps = None
        self._options = None
        self._reqs_options = None
        self._default_options = None

    @property
    def name(self):
        return self._name

    @property
    def options(self):
        if self._options is None:
            self._options, _ = parse_options(self._mdata.get('options'),
                                             self._project.profile.settings,
                                             self.default_options)
        return self._options

    @property
    def reqs_options(self):
        if self._reqs_options is None:
            self._reqs_options = {}
            if not self.deps:
                return self._reqs_options

            conan = self._project.api.conan
            settings = self._project.profile.settings
            conanfile = self._project.conanfile_attributes
            for name, scheme in self.deps.items():
                options, reqs_options = parse_scheme_options(scheme, conanfile, settings, conan)
                self._reqs_options[name] = options
                self._reqs_options.update(reqs_options)
        return self._reqs_options

    @property
    def deps(self):
        """ deps package scheme name

        :return:
        """
        if self._deps is None
            settings = self._project.profile.settings
            options = {k: self.options.get(k, v) for k, v in self.default_options.items()}
            requires = create_requirements(self._manifest, settings, options)
            self._deps = parse_dep_scheme(self.name, self._mdata, requires, settings, options)
        return self._deps

    @property
    def default_options(self):
        if self._default_options is None:
            conanfile = self._project.conanfile_attributes
            self._default_options = conanfile.get('default_options') or {}
        return self._default_options



