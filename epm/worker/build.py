import os
from epm.worker import Worker, DockerRunner, param_encode
from epm.model.project import Project
from epm.errors import EException, EConanException, EDockerException
from conans.errors import ConanException
from conans.tools import environment_append
from epm import HOME_DIR



class Docker(DockerRunner):

    def __init__(self, api, project):
        super(Docker, self).__init__(api, project)


class Builder(Worker):

    def __init__(self, api=None):
        super(Builder, self).__init__(api)
        self._step = None

    def _exec(self, project, steps, sandbox):
        for i in self.conan.editable_list():
            self.conan.editable_remove(i)

        for i in ['configure', 'make', 'package']:
            if i in steps:
                fn = getattr(self, '_%s' % i)
                self.out.highlight('[building - %s ......]\n' % i)
                with environment_append(self.api.config.env_vars):
                    fn(project)

        if sandbox:

            program = None if sandbox == '*' else sandbox

            from epm.worker.sandbox import Builder as SandboxBuilder
            conan = self.api.conan
            conan.editable_add(path=project.dir,
                               reference=str(project.reference),
                               layout=project.layout,
                               cwd=project.dir)

            sb = SandboxBuilder(project)
            sb.exec(program)

    def exec(self, param):
        if 'PROFILE' not in param:
            raise EException('PROFILE required for build.')
        project = Project(param['PROFILE'], param.get('SCHEME'), self.api)
        runner = param.get('RUNNER') or 'auto'
        if runner == 'auto':
            runner = 'docker' if project.profile.docker.builder else 'shell'

        if runner == 'shell':
            steps = param.get('steps')
            sandbox = param.get('sandbox')

            try:
                self._exec(project, steps, sandbox)
            except EException as e:
                raise e
            except ConanException as e:
                raise EConanException('conan error in build', e)
            except BaseException as e:
                raise EException('execute build api failure.', exception=e)

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
        profile = project.profile
        conan = self.api.conan
        folder = os.path.join(project.dir, project.folder.build)
        project.initialize()

        filename = os.path.join(project.dir, project.folder.out, 'profile')
        profile.save(filename)

        options = ['%s=%s' % (k, v) for (k, v) in scheme.options.as_list()]

        info = conan.install(path=project.dir,
                             name=project.name,
                             version=project.version,
                             user=project.user,
                             channel=project.channel,
                             settings=None,  # should be same as profile
                             options=options,
                             profile_names=[filename],
                             install_folder=folder,
                             cwd=project.dir)
        if info['error']:
            raise EConanException('configure step failed on conan.install.', info)

        conan.source(project.dir, source_folder=folder, info_folder=folder)

    def _make(self, project):
        conan = self.api.conan
        folder = os.path.join(project.dir, project.folder.build)
        package_folder = os.path.join(project.dir, project.folder.package)

        conan.build(project.dir,
                    package_folder=package_folder,
                    build_folder=folder,
                    install_folder=folder,
                    cwd=project.dir)

    def _package(self, project):

        conan = self.api.conan
        folder = os.path.join(project.dir, project.folder.build)
        package_folder = os.path.join(project.dir, project.folder.package)

        conan.package(project.dir,
                      build_folder=folder,
                      package_folder=package_folder,
                      install_folder=folder,
                      cwd=project.dir)

