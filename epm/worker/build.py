import os
from epm.worker import Worker, DockerRunner, param_encode
from epm.model.project import Project
from epm.errors import EException, APIError
from epm.model.sandbox import Program


class Docker(DockerRunner):

    def __init__(self, api, project):
        super(Docker, self).__init__(api, project)


class Builder(Worker):

    def __init__(self, api=None):
        super(Builder, self).__init__(api)

    def _exec(self, project, steps):
        for i in self.conan.editable_list():
            self.conan.editable_remove(i)

        for i in ['configure', 'package', 'install', 'test']:
            if i in steps:
                fn = getattr(self, '_%s' % i)
                self.out.highlight('[building - %s ......]' % i)
                fn(project)

    def exec(self, param):
        project = Project(param['scheme'], self.api)
        scheme = project.scheme
        runner = param.get('runner') or 'auto'

        if runner == 'auto':
            runner = 'docker' if scheme.profile.docker.builder else 'shell'

        if runner == 'shell':
            steps = param.get('step') or ['configure', 'package', 'install', 'test']
            if isinstance(steps, str):
                steps = [steps]

            try:
                self._exec(project, steps)
            except APIError:
                raise
            except BaseException as e:
                raise APIError('other error ', details={
                    'info': e
                })
        elif runner == 'docker':
            param['runner'] = 'shell'
            docker = Docker(self.api, project)
            docker.WD = '$home/.project/%s' % project.name

            docker.add_volume(project.dir, docker.WD)
            docker.add_volume(self.api.home_dir, '$home/@host/.epm')
            docker.environment['EPM_HOME_DIR'] = '$home/@host/.epm'
            docker.environment['CONAN_USER_HOME'] = '$home/@host/.epm'
            docker.exec('epm api build %s' % param_encode(param))

    def _configure(self, project):
        scheme = project.scheme
        conan = self.api.conan
        wd = '.'
        project.initialize()

        filename = os.path.join(project.folder.out, 'profile')
        scheme.profile.save(filename)

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

    def _package(self, project):
        conan = self.api.conan
        wd = '.'

        info = conan.build(conanfile_path=wd,
                           package_folder=project.folder.package,
                           build_folder=project.folder.build,
                           install_folder=project.folder.build)
        self._sandbox(project, 'build')

    def _install(self, project):

        conan = self.api.conan
        wd = '.'

        info = conan.package(path=wd,
                             build_folder=project.folder.build,
                             package_folder=project.folder.package,
                             install_folder=project.folder.build)
        self._sandbox(project, 'package')

    def _test(self, project):
        conan = self.api.conan
        wd = '.'
        profile_path = os.path.join(project.folder.out, 'profile')  # already generated in configure step

        info = conan.editable_add(path=project.dir,
                                  reference=project.reference,
                                  layout=project.layout,
                                  cwd=wd)
        options = ['%s=%s' % (k, v) for k, v in project.scheme.options.as_list(package=True)]

        info = conan.test(path='./test_package',
                          reference=project.reference,
                          settings=None,
                          options=options,
                          test_build_folder=project.folder.test,
                          profile_names=[profile_path])
        self._sandbox(project, 'test_package')

    def _sandbox(self, project, folder):
        storage = self.api.conan_storage_path
        for name, command in project.manifest.get('sandbox', {}).items():
            if command.startswith(folder):
                try:
                    program = Program(project, command, storage)
                    program.generate(name)
                except Exception as e:
                    raise APIError('failed to create sandbox command %s' % name, details={
                    })
