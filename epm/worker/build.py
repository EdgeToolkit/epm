import os
from epm.worker import Worker, DockerRunner, param_encode
from epm.errors import EConanException, EDockerException
from conans.tools import environment_append
from epm.worker.sandbox import Generator, build_tests
from epm import HOME_DIR


class Docker(DockerRunner):

    def __init__(self, api, project):
        super(Docker, self).__init__(api, project)


class Builder(Worker):

    def __init__(self, api=None):
        super(Builder, self).__init__(api)
        self._step = None

    def _exec(self, project, step, program):
        for i in self.conan.editable_list():
            self.conan.editable_remove(i)

        for i in ['configure', 'make', 'package']:
            if i in step:
                fn = getattr(self, '_%s' % i)
                self.out.highlight('[building - %s ......]\n' % i)
                with environment_append(self.api.config.env_vars):
                    fn(project)
        from epm.model.program import build_program
        build_program(project, program)

#        if tests or tests is None:
#            build_tests(project, tests)
#            Generator.build(project, is_create=False, targets=tests)

    def exec(self, param):
        project = self.api.project(param['PROFILE'], param.get('SCHEME'))

        runner = param.get('RUNNER') or 'auto'
        if runner == 'auto':
            runner = 'docker' if project.profile.docker.builder else 'shell'

        if runner == 'shell':
            step = param.get('step')
            program = param.get('program')
            self._exec(project, step, program)

        elif runner == 'docker':
            param['RUNNER'] = 'shell'
            docker = Docker(self.api, project)
            docker.WD = '$home/.project/%s' % project.name

            docker.add_volume(project.dir, docker.WD)
            docker.add_volume(HOME_DIR, '$home/.epm')
            docker.exec('epm api build %s' % param_encode(param))
            if docker.returncode:
                raise EDockerException(docker)

    def _configure(self, project):
        scheme = project.scheme

        conan = self.api.conan
        project.setup()
        path = project.abspath
        wd = os.getcwd()

        info = conan.install(path=wd,
                             name=project.name,
                             version=project.version,
                             user=project.user,
                             channel=project.channel,
                             settings=None,  # should be same as profile
                             options=scheme.as_list(),
                             profile_names=[path.profile_host],
                             profile_build=project.profile.build,
                             install_folder=path.build,
                             cwd=wd)
        if info['error']:
            raise EConanException('configure step failed on conan.install.', info)

        conan.source(wd)

    def _make(self, project):
        conan = self.api.conan
        path = project.abspath
        wd = os.getcwd()
        try:
            del os.environ['MESON_CROSS_FILE']
        except:
            pass
        if os.path.exists(path.cross_file):
            os.environ['MESON_CROSS_FILE'] = path.cross_file

        conan.build(wd,
                    package_folder=path.package,
                    build_folder=path.build,
                    install_folder=path.build,
                    source_folder=wd,
                    cwd=wd)

    def _package(self, project):
        conan = self.api.conan
        path = project.abspath
        wd = os.getcwd()

        conan.package(wd,
                      build_folder=path.build,
                      package_folder=path.package,
                      install_folder=path.build,
                      cwd=wd)

