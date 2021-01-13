import os
'''
program:
- name: test_package
  location: test_package
  executable:
  - name: t
    argv: []
    location: test_package/bin/test_package

  argv:
  build-tools:
  dependencies:
'''


class Executable:
    program = None
    name = None
    location = None
    executable = None
    argv = []

    def __init__(self, program, project, config):
        pass


class Program(object):
    name = None
    location = None
    executable = []
    argv = None
    requirements = []
    build_requirements = []

    def __init__(self, project, config):
        self._project = project
        self._config = config
        self.name = self._config['name']
        self.location = self._config.get('location') or None
        self.argv = self._config.get('argv') or None
        #self.executalbe

    def _load_executable(self):
        e = self._config.get('executable')
        if not e:
            return
        if isinstance(e, str):
            self.executable.append(Executable(self, self._project, {'name': e}))
        elif isinstance(e, list):
            for i in e:
                self.executable.append(Executable(self, self._project, i))
        else:
            raise SyntaxError('program.executable not support type {}'.format(type(e)))

    def build(self):
        if not self.location:
            return
        name = self.name
        project = self._project

        project.api.out.highlight(f"\n==== build program ({name})\n")

        build_folder = os.path.join(project.folder.program, name)
        WD = os.path.join(project.dir, self.location)

        conan = project.api.conan
        scheme = project.scheme
        from conans.tools import environment_append

        with environment_append({'EPM_PROJECT_DIRECTORY': project.dir,
                                 'EPM_PROGRAM_NAME': name}):
            print(WD, '============================', build_folder)
            info = conan.install(WD,
                                 options=scheme.as_list(True),
                                 profile_names=[project.abspath.profile_host],
                                 install_folder=build_folder,
                                 profile_build=project.profile.build)
            if info['error']:
                raise Exception('configure program <{}> failed.'.format(self.location), info)

            conan.build(WD,
                        build_folder=build_folder,
                        install_folder=build_folder)





    @staticmethod
    def load(project):

        config = project.metainfo.get('program')
        if not config:
            return []
        program = []
        for conf in config:
            program.append(Program(project, conf))
        return program


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


def build_program(project, target):
    with editable_add(project):
        for program in Program.load(project):
            if target is None or program.name in target:
                conan = project.api.conan
                for k, v in conan.editable_list().items():
                    print(k, '**', v)
                program.build()
