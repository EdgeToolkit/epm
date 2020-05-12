import os
from epm.worker import Worker, DockerRunner, param_encode
from epm.model.project import Project
from epm.errors import EException, APIError
#from epm.model.sandbox import Program
from conans.tools import environment_append
from epm.paths import HOME_EPM_DIR
#from epm.model import sandbox_builds_filter

class Docker(DockerRunner):

    def __init__(self, api, project):
        super(Docker, self).__init__(api, project)


class Builder(Worker):

    def __init__(self, api=None):
        super(Builder, self).__init__(api)

    def _exec(self, project, steps):
        for i in self.conan.editable_list():
            self.conan.editable_remove(i)

        for i in ['configure', 'make', 'package']:
            if i in steps:
                fn = getattr(self, '_%s' % i)
                self.out.highlight('[building - %s ......]\n' % i)
                with environment_append(self.api.config.env_vars):
                    fn(project)

    def exec(self, param):
        project = Project(param['PROFILE'], param.get('SCHEME'), self.api)
        runner = param.get('RUNNER') or 'auto'
        if runner == 'auto':
            runner = 'docker' if project.profile.docker.builder else 'shell'

        if runner == 'shell':
            steps = param.get('steps')

            try:
                self._exec(project, steps)
            except APIError:
                raise
            except BaseException as e:
                raise APIError('other error ', details={
                    'info': str(e)
                })

            program = param.get('sandbox')
            if program:
                program = None if program == '*' else program

                from epm.worker.sandbox import Builder as SB
                sb = SB(project)
                sb.exec(program)

        elif runner == 'docker':
            param['RUNNER'] = 'shell'
            docker = Docker(self.api, project)
            docker.WD = '$home/.project/%s' % project.name

            docker.add_volume(project.dir, docker.WD)
            docker.add_volume(HOME_EPM_DIR, '$home/.epm')
            docker.exec('epm api build %s' % param_encode(param))

    #def _build_sandbox(self, project, sandbox):
    #    if not sandbox or sandbox in ['*']:
    #        sandbox = None
    #
    #    builds = sandbox_builds_filter(sandbox, project.manifest.sandbox.values())
    #    conan = self.api.conan
    #    options = ['%s=%s' % (k, v) for k, v in project.scheme.package_options.as_list()]
    #
    #    for folder, sbs in builds.items():
    #
    #        self.api.out.highlight('[build sandbox program] %s. project folder  %s'
    #                               % (",".join([x.name for x in sbs]), folder))
    #
    #        conanfile_path = os.path.join(folder, 'conanfile.py')
    #
    #        instd = os.path.join(project.folder.out, folder, 'build')
    #
    #        info = conan.install(path=conanfile_path,
    #                             name='%s-%s' % (project.name, folder.replace('-', '_')),
    #                             settings=None,  # should be same as profile
    #                             options=options,
    #                             profile_names=[project.generate_profile()],
    #                             install_folder=instd)
    #
    #        conan.build(conanfile_path=conanfile_path,
    #                    build_folder=instd,
    #                    install_folder=instd)
    #        for sb in sbs:
    #            program = Program(project, sb, instd)
    #            program.generate(sb.name)
    #

    def _configure(self, project):
        scheme = project.scheme
        profile = project.profile
        conan = self.api.conan
        wd = '.'
        project.initialize()

        filename = os.path.join(project.folder.out, 'profile')
        profile.save(filename)

        options = ['%s=%s' % (k, v) for (k, v) in scheme.options.as_list()]

        info = conan.install(path=wd,
                             name=project.name,
                             version=project.version,
                             user=project.user,
                             channel=project.channel,
                             settings=None,  # should be same as profile
                             options=options,
                             profile_names=[filename],
                             install_folder=project.folder.build)

        if info['error']:
            raise APIError('failed when building project %s | %s in configure step'
                           % (project.name, scheme.name), details={

                           })

        conan.source(wd)

    def _make(self, project):
        conan = self.api.conan
        wd = '.'

        info = conan.build(conanfile_path=wd,
                           package_folder=project.folder.package,
                           build_folder=project.folder.build,
                           install_folder=project.folder.build)
        #self._sandbox(project, 'build')

    def _package(self, project):

        conan = self.api.conan
        wd = '.'

        info = conan.package(path=wd,
                             build_folder=project.folder.build,
                             package_folder=project.folder.package,
                             install_folder=project.folder.build)
        #self._sandbox(project, 'package')

    #def _test(self, project):
    #    conan = self.api.conan
    #    wd = '.'
    #
    #    info = conan.editable_add(path=project.dir,
    #                              reference=str(project.reference),
    #                              layout=project.layout,
    #                              cwd=wd)
    #    options = ['%s=%s' % (k, v) for k, v in project.scheme.package_options.as_list()]
    #    tests = project.tests or []
    #    if not tests:
    #        if os.path.exists('test_package/conanfile.py'):
    #            tests = ['test_package']
    #
    #    for i in tests:
    #        conanfile_path = os.path.join(i, 'conanfile.py')
    #        if not os.path.exists(conanfile_path):
    #            raise EException('specified test <%s> miss Makefile.py' % i)
    #        instd = os.path.join(project.folder.test, i, 'build')
    #        pkgdir = os.path.join(project.folder.test, i, 'package')
    #        info = conan.install(path=conanfile_path,
    #                             name='%s-%s' % (project.name, i),
    #                             settings=None,
    #                             options=options,
    #                             profile_names=[project.generate_profile()],
    #                             install_folder=instd)
    #
    #        conan.build(conanfile_path=conanfile_path,
    #                    package_folder=pkgdir,
    #                    build_folder=instd,
    #                    install_folder=instd)
    #
    #        conan.package(path=conanfile_path,
    #                      build_folder=instd,
    #                      package_folder=pkgdir,
    #                      install_folder=instd)
    #
    #        self._sandbox(project, 'test')
    #
    #def _sandbox(self, project, folder):
    #    storage = self.api.conan_storage_path
    #    m = project.manifest.as_dict()
    #    for name, command in m.get('sandbox', {}).items():
    #        if command.startswith(folder):
    #            try:
    #                program = Program(project, command, storage)
    #                program.generate(name)
    #            except Exception as e:
    #                raise APIError('failed to create sandbox command %s' % name, details={
    #                })

#
#class SandboxBuilder(Worker):
#    def __init__(self, api=None):
#        super(SandboxBuilder, self).__init__(api)
#
#    def exec(self, param):
#        project = Project(param['PROFILE'], param.get('SCHEME'), self.api)
#        runner = param.get('RUNNER') or 'auto'
#
#        if runner == 'auto':
#            runner = 'docker' if project.profile.docker.builder else 'shell'
#
#        if runner == 'shell':
#            steps = param.get('steps') or ['configure', 'make']
#            if isinstance(steps, str):
#                steps = [steps]
#
#            program = param.get('name')
#            try:
#                self._build_sandbox(project, steps, program)
#            except APIError:
#                raise
#            except BaseException as e:
#                raise APIError('other error ', details={
#                    'info': str(e)
#                })
#        elif runner == 'docker':
#            param['RUNNER'] = 'shell'
#            docker = Docker(self.api, project)
#            docker.WD = '$home/.project/%s' % project.name
#
#            docker.add_volume(project.dir, docker.WD)
#            docker.add_volume(HOME_EPM_DIR, '$home/.epm')
#            docker.exec('epm api sandbox-build %s' % param_encode(param))
#
#    def _build_sandbox(self, project, steps, program):
#        program = program or None
#
#        builds = sandbox_builds_filter(program, project.manifest.sandbox.values())
#        conan = self.api.conan
#        options = ['%s=%s' % (k, v) for k, v in project.scheme.package_options.as_list()]
#
#        filename = os.path.join(project.folder.out, 'profile')
#        project.profile.save(filename)
#
#        for folder, sbs in builds.items():
#
#            self.api.out.highlight('[build sandbox program] %s. project folder  %s'
#                                   % (",".join([x.name for x in sbs]), folder))
#
#            conanfile_path = os.path.join(folder, 'conanfile.py')
#
#            instd = os.path.join(project.folder.out, folder, 'build')
#            if 'configure' in steps:
#
#                info = conan.install(path=conanfile_path,
#                                     name='%s-%s' % (project.name, folder.replace('-', '_')),
#                                     settings=None,  # should be same as profile
#                                     options=options,
#                                     profile_names=[filename],
#                                     install_folder=instd)
#            if 'make' in steps:
#
#                conan.build(conanfile_path=conanfile_path,
#                            build_folder=instd,
#                            install_folder=instd)
#                for sb in sbs:
#                    program = Program(project, sb, instd)
#                    program.generate(sb.name)
#