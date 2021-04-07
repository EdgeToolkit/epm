import os
import glob
import pathlib
import subprocess
import stat
from conans.tools import chdir
from epm.utils.logger import syslog
from epm.utils import PLATFORM, ARCH

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

''' Executable 搜索顺序
包编译程序( not program.location ):
  <包路径>/${program.executable}
  <包路径>/package/${program.executable}
  <包路径>/build/${program.executable}
测试程序(program)：
  program构建路径
    
'''


class Executable(object):

    def __init__(self, program, config):
        self._program = program
        self._project = program.project
        self._config = config

    @property
    def name(self):
        name = self._config.get('name')
        if name is False:
            return False
        if not name:
            name = self._program.name
        else:
            name = f"{self._program.name}.{name}"
        return name

    @property
    def _patterns(self):
        path = self._config['path']
        if isinstance(path, str):
            patterns = [path]
        elif isinstance(path, list):
            patterns = path
        else:
            raise SyntaxError('invalid type of program.executable definition {}.'.format(type(executable)))
        return patterns

    @property
    def storage_path(self):
        project = self._program.project
        return os.getenv('CONAN_STORAGE_PATH') or project.api.conan_storage_path

    @property
    def _is_win(self):
        return self._project.profile.host.settings['os'] == 'Windows'

    def _find(self, folder, root):
        storage = self.storage_path if root == 'storage' else self._project.dir
        with chdir(os.path.join(storage, folder)):
            for pattern in self._patterns:
                if self._is_win:
                    pattern = pattern + '.exe'
                path = glob.glob(pattern)
                syslog.info(f'find program.executable {self.name} in <{root}>:{storage}' +
                            "\nroot: {}".format(os.path.abspath('.')) +
                            "\npattern: {}".format(pattern) +
                            "\n {} found. {}".format(len(path), "\n".join(path)))

                if path:
                    return path[0]
        return None

    def generate(self):
        if self.name is False:
            return
        program = self._program
        project = program.project
        builtin = program.location is None
        package_id = project.record.get('package_id')
        folder = None
        where = 'storage'
        if builtin:
            build_folder = os.path.join(project.reference.dir_repr(), 'build', package_id)
            package_folder = os.path.join(project.reference.dir_repr(), 'package', package_id)
            for i in [package_folder, build_folder]:
                path = self._find(i, where)
                if path:
                    folder = i
                    break
        else:
            where = 'project'
            build_folder = os.path.join(project.path.program, program.name)
            path = self._find(build_folder, where)
            if path:
                folder = build_folder

        if not path or not folder:
            raise FileNotFoundError(f'can not find {self.name} in {where}.')

        rootpath = os.path.join(self.storage_path if where == 'storage' else project.dir)
        conaninfo_path = os.path.join(rootpath, folder, 'conaninfo.txt')
        from conans.model.info import ConanInfo
        from conans.util.files import load, mkdir
        conaninfo = ConanInfo.loads(load(conaninfo_path))
        libs, deps = self._parse_dynamic_libs(conaninfo)
        libdirs = set([os.path.dirname(x) for x in libs])
        depdirs = set([os.path.dirname(x) for x in deps])
        from collections import namedtuple
        context = {'libs': libs, 'deps': deps, 'package_id': package_id or '',
                   'dirs': namedtuple('D', 'lib, dep')(libdirs, depdirs),
                   'project': project, 'program': program, 'executable': self,
                   'filename': path, 'where': where,
                   'command': 'create' if package_id else 'build'
                   }
        self._render(context)

    def _render(self, context):
        from epm.utils import Jinja2
        from epm import DATA_DIR
        out_dir = os.path.join(self._project.abspath.out, 'sandbox', 'bin')
        j2 = Jinja2(directory=f"{DATA_DIR}/program", context=context)

        if self._is_win:
            j2.render("windows.cmd.j2", outfile=f"{out_dir}/{self.name}.cmd")
        else:
            j2.render("linux.sh.j2", outfile=f"{out_dir}/{self.name}")
            j2.render("linux.cmd.j2", outfile=f"{out_dir}/{self.name}.cmd")
            os.chmod(f"{out_dir}/run", stat.S_IRWXU | stat.S_IXGRP | stat.S_IRGRP | stat.S_IROTH)

    def _parse_dynamic_libs(self, conaninfo):
        libs = []
        deps = []
        win = bool(conaninfo.settings.os == 'Windows')
        storage = self.storage_path
        if not os.path.exists(storage):
            return list(), list()

        with chdir(storage):
            for pref in conaninfo.full_requires:
                path = os.path.join(pref.ref.dir_repr(), 'package', pref.id)
                if win:
                    lib = glob.glob(f'{path}/bin/*.dll')
                    lib += glob.glob(f'{path}/bin/**/*.dll', recursive=True)
                else:
                    lib = glob.glob(f'{path}/lib/*.so')
                    lib += glob.glob(f'{path}/lib/*.so.*')
                    lib += glob.glob(f'{path}/lib/**/*.so', recursive=True)
                    lib += glob.glob(f'{path}/lib/**/*.so.*', recursive=True)

                if pref.ref.name == self._project.name:
                    libs += lib
                else:
                    deps += lib

        def _(x):
            return pathlib.WindowsPath(x) if win else pathlib.PosixPath(x)

        return [_(x) for x in libs], [_(x) for x in deps]


class Program(object):
    name = None
    location = None
    executable = []
    argv = None
    requirements = []
    build_requirements = []

    def __init__(self, project, config):
        self.project = project
        self._config = config
        self.name = self._config.get('name') or None
        self.location = self._config.get('location')
        self.argv = self._config.get('argv') or None
        self._executable = None

    @property
    def executable(self):
        if self._executable is None:
            self._executable = []
            executables = []
            config = self._config.get('executable') or []
            if isinstance(config, str):
                executables = [{'name': None, 'path': [config]}]
            elif isinstance(config, list):
                for e in config:
                    assert isinstance(e, dict)
                    default = {'name': None}
                    executables.append(dict(default, **e))
            for config in executables:
                self._executable.append(Executable(self, config))
        return self._executable

    def build(self):
        if not self.location:
            return
        name = self.name
        project = self.project

        project.api.out.highlight(f"\n==== build program ({name})\n")

        build_folder = os.path.join(project.folder.program, name)
        WD = os.path.join(project.dir, self.location)

        conan = project.api.conan
        scheme = project.scheme
        from conans.tools import environment_append

        with environment_append({'EPM_PROJECT_DIRECTORY': project.dir,
                                 'EPM_PROGRAM_NAME': name}):
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

    @staticmethod
    def exec(project, name, argv, runner=None):
        """execute the specified executable program <name> in given runner

        """
        for program in Program.load(project):
            for e in program.executable:
                if e.name == program.name:
                    e.run


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


def build_program(project, target=None):
    with editable_add(project):
        for program in Program.load(project):
            if target is None or program.name in target:
                program.build()
                for e in program.executable:
                    e.generate()

def create_program(project, target=None):
    for program in Program.load(project):
        if target is None or program.name == target:
            program.build()
            for e in program.executable:
                e.generate()


def guess_runner(project, runner):
    if runner in ['docker', 'shell']:
        return runner
    if runner in ['auto', None]:
        if project.profile.docker.runner:
            return 'docker'
        _os = project.profile.host.settings['os']
        _arch = project.profile.host.settings['arch']
        if _os != PLATFORM or _arch != ARCH:
            raise Exception(f'the program({_os} {_arch}) is not runnable in current system.')
        return 'shell'
    assert isinstance(runner, str)
    return runner


def exec_program(project, name, argv, runner=None):
    """execute the specified executable program <name> in given runner

    """
    program = None
    executable = None
    out = project.api.out
    canidates = []

    for program in Program.load(project):

        for e in program.executable:
            canidates.append(e.name)
            if e.name == name:
                program = program
                executable = e
                break
    if executable is None:
        out.error(f"executable program <{name}> not defined in package.yml.\ndefined programs are:\n\t" +
                  "\t\n".join(canidates))
        return 128

    filename = pathlib.PurePath(f"{project.folder.out}/sandbox/bin/{name}").as_posix()
    if runner in ['shell', 'docker', None, 'auto']:
        if PLATFORM == 'Windows':
            filename = "{}.cmd".format(pathlib.WindowsPath(filename))

        command = [filename] + argv
        from conans.tools import environment_append
        with environment_append({'EPM_SANDBOX_RUNNER': runner}):
            proc = subprocess.run(command, shell=True)
            return proc.returncode
