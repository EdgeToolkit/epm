import os
import yaml
import sys
import shutil

from conans.tools import ConanOutput as Output
from epm.util.files import mkdir
from jinja2 import PackageLoader, Environment

_DEP_DEMO = '''#
#dependencies:
#  lib-name:
#    version: <version of library which linked by this package>
#    group: <group of the lib, which was defined in its package.yml `group` field>
#  lib2-name:
#    version:   ......
#    group:     ......
#
#'''

_DESCRIPTION = '{name} is {type} ....'

_LICENSE = 'MIT'


class Generator(object):

    def __init__(self, args, type):
        self._type = type
        self._out_dir = os.path.abspath('.')
        self._jinja2_project_env = Environment(loader=PackageLoader('epm', 'data/project'))
        self._manifest = {}
        self.out = Output(sys.stdout, sys.stderr, color=True)

        if os.path.exists('package.yml'):
            with open('package.yml') as f:
                self._manifest = yaml.safe_load(f)

        name = os.path.basename(os.path.abspath('.'))
        name = self._manifest.get('name') or args.name or name
        version = self._manifest.get('version') or args.version or '0.0.1'

        self._manifest['name'] = name
        self._manifest['version'] = version

    @property
    def name(self):
        return self._manifest['name']

    @property
    def type(self):
        return self._type

    @property
    def version(self):
        return self._manifest['version']

    def _gitlab_ci(self):
        mkdir('script')
        mkdir('script/ci')
        self._copy('script/gitlab-ci.py')
        self._copy('script/ci/prolog.yml.j2')
        self._copy('script/ci/linux-gcc.yml.j2')
        self._copy('script/ci/linux-hisi.yml.j2')
        self._copy('script/ci/visualstudio.yml.j2')
        if self._type =='lib':
            self._copy('script/ci.yml')
        else:
            self._copy('script/ci-app.yml', 'script/ci.yml')

    def _copy(self, src, dst=None):
        dst = dst or src
        folder = os.path.dirname(dst)
        if folder and not os.path.exists(folder):
            mkdir(folder)
        import epm

        path = os.path.join(os.path.dirname(epm.__file__), 'data/project', src)
        shutil.copy(path, dst)

    def _common(self):
        self._gitlab_ci()
        self._out('.gitignore', '.gitignore')
        self._out('conanfile.py', 'conanfile.py')
        self._docs()

    def _docs(self):
        self._out('mkdocs.yml', 'mkdocs.yml')

        self._out('docs/index.md', 'docs/index.md')
        self._out('docs/release-notes.md', 'docs/release-notes.md')
        self._out('docs/user-guide.md', 'docs/user-guide.md')
        if not os.path.exists('README.md'):
            self._out('README.md', 'README.md')

    def _library(self):
        self._common()

        self._out('include/declaration.h', 'include/{0}/declaration.h'.format(self.name))
        self._out('include/lib.h', 'include/{0}/{0}.h'.format(self.name))
        self._out('source/lib.c', 'source/{0}.c'.format(self.name))

        self._out('CMakeLists.txt', 'CMakeLists.txt')
        self._out('cmake/libCMakeLists.txt', 'cmake/CMakeLists.txt')
        self._out('cmake/config.cmake.in', 'cmake/{}-config.cmake.in'.format(self.name))

        self._out('test_package/main.cpp', 'test_package/src/main.cpp')
        self._out('test_package/test.cpp', 'test_package/src/test.cpp')
        self._out('test_package/CMakeLists.txt', 'test_package/CMakeLists.txt')
        self._out('test_package/conanfile.py', 'test_package/conanfile.py')

    def _application(self):
        self._common()

        self._out('source/main.c', 'source/main.c')

        self._out('CMakeLists.txt', 'CMakeLists.txt')
        self._out('cmake/CMakeLists.txt', 'cmake/CMakeLists.txt')

        self._out('test_package/main.py', 'test_package/main.py')
        self._out('test_package/test_version.py', 'test_package/test_{}.py'.format(self.name))
        self._out('test_package/app-conanfile.py', 'test_package/conanfile.py')

    def _out(self, template, filename, **kwargs):
        env = self._jinja2_project_env
        tmpl = env.get_template(template)
        vars = dict({'name': self.name,
                     'version': self.version,
                     'type': self._type,
                     'manifest': self._manifest},
                    **kwargs)

        content = tmpl.render(vars)

        folder = os.path.dirname(os.path.abspath(filename))
        if not os.path.exists(folder):
            os.makedirs(folder)

        with open(filename, 'w') as f:
            f.write(content)

    def _gen_manifest(self):
        ''' format and update manifest
        '''
        import copy

        manifest = copy.deepcopy(self._manifest)
        license = manifest.get('license', _LICENSE)
        description = manifest.get('description', _DESCRIPTION.format(name=self.name, type=self.type))
        sandbox = manifest.get('sandbox', {})
        dependencies = manifest.get('dependencies', {})

        scheme = manifest.get('scheme', {})
        if not scheme.get('profile'):
            scheme['profile'] = ['vs2019', 'gcc5']
            scheme['options'] = {
                'dynamic': {'shared': True}
            }

            deps = {}
            for k, v in dependencies.items():
                deps[k] = 'dynamic'

#            if deps:
#                scheme['options']['dynamic']['.dependencies'] = deps

        script = manifest.get('script', {})

        if not script.get('gitlab-ci'):
            script['gitlab-ci'] = 'script/gitlab-ci.py'

        if self._type == 'app':
            if not script.get('test', {}):
                script['test'] = 'test_package/main.py'

            if not sandbox.get(self.name, {}):
                sandbox = {self.name: 'package/bin/%s' % self.name}

        else:
            if not sandbox.get('test_package', {}):
                sandbox = {'test_package': 'test_package/%s_test' % self.name}

        for key in ['name', 'version', 'group', 'sandbox', 'plan', 'script',
                    'dependencies', 'license', 'description']:
            if key in manifest.keys():
                del manifest[key]

        license = yaml.dump({'license': license}, default_flow_style=False)
        description = yaml.dump({'description': description}, default_flow_style=False)

        sandbox = yaml.dump({'sandbox': sandbox}, default_flow_style=False)

        options = scheme.get('options')
        if 'options' in scheme:
            scheme.pop('options')

        scheme = yaml.dump({'scheme': scheme}, default_flow_style=False)
        if options:
            txt = yaml.dump({'options': options}, default_flow_style=False)
            scheme += "\n".join(['  %s' % x for x in txt.split('\n')])

        script = yaml.dump({'script': script}, default_flow_style=False)
        dependencies = yaml.dump({'dependencies': dependencies},
                                 default_flow_style=False) if dependencies else _DEP_DEMO
        if os.path.exists('package.yml'):
            filename = 'package.yml.origin'
            i = 1
            while True:
                if not os.path.exists(filename):
                    break
                i += 1
                filename = 'package.yml.origin.{}'.format(i)

            os.rename('package.yml', filename)
        self._out('package.yml', 'package.yml',
                  scheme=scheme,
                  sandbox=sandbox,
                  script=script,
                  dependencies=dependencies,
                  license=license,
                  description=description)

    def run(self):
        if self._type == 'lib':
            self._library()
        if self._type == 'app':
            self._application()

        self._gen_manifest()
        self.out.success('{} package <{}> project created successfully.'.format(
            self.type, self.name))

        self.out.info('Please check README.md for details')
