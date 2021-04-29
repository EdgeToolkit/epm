import os
import subprocess
from epm.worker import Worker
from epm.errors import EConanException
from conans.tools import environment_append
from epm import HOME_DIR
from epm.model.program import Program
from epm.utils import PLATFORM
from epm.utils.docker import BuildDocker

#class Docker(DockerRunner):
#
#    def __init__(self, api, project):
#        super(Docker, self).__init__(api, project)

class editable_add(object):
    def __init__(self, project):
        self._project = project
        self._ref = None

    def __enter__(self):
        conan = self._project.api.conan
        path = self._project.dir
        layout = os.path.join(self._project.folder.out, "conan.layout")
        ref = str(self._project.reference)
        cwd = path
        conan.editable_add(path, ref, layout, cwd)
        self._ref = ref

    def __exit__(self, type, value, trace):
        if self._ref:
            conan = self._project.api.conan
            conan.editable_remove(self._ref)

class Builder(Worker):

    def __init__(self, api=None):
        super(Builder, self).__init__(api)
        self._step = None

    def _exec(self, project, step, program):
        for i in self.conan.editable_list():
            self.conan.editable_remove(i)
        if not step and not program:
            step = None
            program = None

        for i in ['configure', 'make', 'package']:
            if step is None or i in step:
                prefix = '_go_' if project.language=='go' else '_'
                fn = getattr(self, '{}{}'.format(prefix, i))
                self.out.highlight('[building - %s ......]\n' % i)
                with environment_append(self.api.config.env_vars):
                    fn(project)
       
        self._build_program(project, program)
            
    def _build_program(project, target=None):
        if project.language != 'c':
            return
        built = set()
        with editable_add(project):
            for name, test in project.test.items():
                if target is None or name in target:
                    if not test.project:
                        continue
                    if test.project in built:
                        continue                       
                    program = Program(project, name)
                    program.build()
                    built.add(test.project)
                    
            for name, test in project.test.items():
                if target is None or name in target:
                    program = Program(project, name)
                    program.generate('build')

    def exec(self, param):
        project = self.api.project(param['PROFILE'], param.get('SCHEME'))

        step = param.get('step')
        program = param.get('program')
        runner = param.get('RUNNER') or os.getenv('EPM_RUNNER') or 'auto'

        if runner == 'auto':
            runner = 'docker' if project.profile.docker.builder else 'shell'

        if runner == 'shell':
            self._exec(project, step, program)

        elif runner == 'docker':
            docker = BuildDocker(project)

            command = f"epm --runner shell --profile {project.profile.name}"
            if project.scheme and project.scheme.name:
                command += f" --scheme {project.scheme.name}"
            command += f" build"
            if step:
                command += "".join([f" --{i}" for i in step])
            if program:
                command += "".join([f" --program {i}" for i in program])
            docker.environment['EPM_RUNNING_SYSTEM'] = 'docker'

            proc = docker.run(command)
            if proc.returncode:
                raise Exception(f"[Docker] {command} failed.")

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

    def _go_configure(self, project):
        pass

    def _go_make(self, project):
        from conans.tools import mkdir
        mkdir(project.path.build)
        output = project.path.build
        if project.name:
            output = os.path.join(output, project.name)
        command = ['go', 'build', '-o', output]
        proc = subprocess.run(command)
        if proc.returncode:
            raise Exception(f"[go]] build failed.")


    def _go_package(self, project):
        pass
