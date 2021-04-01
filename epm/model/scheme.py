import copy
from epm.tools import create_requirements, create_build_tools
from epm.tools import parse_multi_expr
from epm.api import conanfile_instance
from epm.utils.logger import syslog

class Scheme(object):

    def __init__(self, project, name=None):
        self._name = name or project.attribute.scheme
        self._project = project
        self._manifest = project.__meta_information__ or {}
        self._mdata = self._manifest.get('scheme') or {}

        if self._name is None:
            if self._manifest.get('scheme'):
                raise Exception(f'No scheme spcified!')
        else:
            if self._name not in self._manifest.get('scheme'):
                raise Exception(f'{self._name} is not defined in scheme.')

        self._mdata = self._mdata.get(self._name) or {}        
        self._deps = None
        self._options = None
        self._full_options = None
        self._reqs_options = None
        self._requires = None
        self._tools = None
        self._conanfile_options = None
        self._conanfile_settings = None

        self.conanfile, self.instance = conanfile_instance(self._project.api.conan, self._project.dir, project.profile)

    @property
    def name(self):
        return self._name

    @property
    def options(self):
        if self._options is None:
            options = {}
            default_options = self.conanfile.default_options
            scheme_options = self._mdata.get('options') or {}
            for k, v in self.instance.options.items():
                if k in scheme_options:
                    value = scheme_options[k]
                    if value != default_options[k]:
                        options[k] = value
            self._options = options
        return self._options

    @property
    def full_options(self):
        if self._full_options is None:
            options = {}
            default_options = self.conanfile.default_options
            scheme_options = self._mdata.get('options') or {}
            for k, v in self.instance.options.items():
                options[k] = scheme_options[k] if k in scheme_options else default_options[k]
            syslog.debug(f"\nfulloptions: \ndefault_opitons:{default_options}\nscheme_options:{scheme_options} options:{options}")
            self._full_options = options
        return self._full_options

    @property
    def dep_options(self):
        if self._reqs_options is None:
            self._reqs_options = {}
            if not self.deps:
                return self._reqs_options

            conan = self._project.api.conan
            settings = self._project.profile.host.settings
            for name, scheme in self.deps.items():
                ref = str(self.requires.get(name))
                options, deps = get_scheme_options(scheme, ref, settings, conan, profile=self._project.profile)
                self._reqs_options[name] = options
                self._reqs_options.update(dict(deps))

        return self._reqs_options


    @property
    def deps(self):
        """ deps package scheme name

        :return:
        """
        if self._deps is None:
            settings = self._project.profile.host.settings
            options = self.full_options

            self._deps = get_dep_scheme(self.name, self._mdata, self.requires, settings, options)
        return self._deps

    @property
    def requires(self):
        if self._requires is None:
            settings = self._project.profile.host.settings
            options = self.full_options
            self._requires = create_requirements(self._manifest, settings, options, profile=self._project.profile)
        return self._requires

#    @property
#    def default_options(self):
#        assert False
#        if self._default_options is None:
#            conanfile = self._project.conanfile_attributes or {}
#            self._default_options = conanfile.get('default_options') or {}
#        return self._default_options

    def as_list(self, test_package=False):
        prefix = '%s:' % self._project.name if test_package else ''
        options = ['%s%s=%s' % (prefix, k, v) for k, v in self.options.items()]
        for pkg, opts in self.dep_options.items():
            for k, v in opts.items():
                if k == 'fPIC':
                    continue
                options += ['%s:%s=%s' % (pkg, k, v)]
        return options


def get_dep_scheme(default, scheme, requires, settings, options, profile=None):
    """ parse specified scheme and return the dict with item package:schme

    :param default: undefined package scheme
    :param mdata: scheme defination [dict]
    :param scheme: scheme default name (the name of the schemd
    :param requires:
    :param settings:
    :param options:

    :return:
    """
    syslog.debug(f"get_dep_scheme: {requires}")

    result = {}
    for requirement in requires.values():
        name = requirement.ref.name
        expr = scheme.get(name)
        syslog.debug(f"requirement: {name} expr:{expr}")
        

        if not expr:
            result[name] = default
        elif isinstance(expr, str):
            result[name] = expr
        elif isinstance(expr, (list, dict)):
            result[name] = parse_multi_expr(expr, settings, options, profile=profile) or default
        else:
            raise NotImplementedError('not support ')

    return result


def get_scheme_options(scheme, reference, settings, conan, requires=None, profile=None):
    '''parse the specifed reference scheme options under the settings
    :param scheme: [str] scheme name
    :param reference: reference or path of conanfile
    :param settings: profile settings
    :param api:
    :return:
    '''

    assert isinstance(reference, str), reference
    conanfile, instance = conanfile_instance(conan, reference, profile)
    manifest = getattr(conanfile, '__meta_information__', None)
    if not manifest:
        return {k: v for k, v in instance.options.items()}, {}

    mdata = manifest.get('scheme', {}).get(scheme) or {}
    scheme_options = mdata.get('options') or {}

    options = {k: scheme_options.get(k, v) for k, v in instance.options.items()}
    print('-->', conanfile, 'profile', profile)
    requires = requires or create_requirements(manifest, settings, options, profile=profile)

    if not requires:
        return options, {}

    reqs_options = {}
    deps = get_dep_scheme(scheme, mdata, requires, settings, options, profile=profile)

    for name, sch in deps.items():
        ref = requires[name]
        from conans.model.requires import Requirement
        if isinstance(ref, Requirement):
            ref = str(ref.ref)
        o, po = get_scheme_options(sch, ref, settings, conan, profile=profile)
        reqs_options[name] = o
        reqs_options.update(po)

    return options, reqs_options