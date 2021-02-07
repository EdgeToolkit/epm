import os
import stat
import fnmatch
import pathlib
import glob
import copy
from jinja2 import Environment, FileSystemLoader
import subprocess
import time

from conans.client.tools import ConanRunner
from conans.tools import environment_append, chdir

from epm import DATA_DIR
from epm.utils import PLATFORM
from epm.utils.logger import syslog
from epm.errors import EConanException, EException
from epm.worker import Worker
from epm.tools.ssh import SSH
from conans.model.info import ConanInfo
from conans.util.files import load, mkdir


HOST_FOLDER = '@host'
PROJECT_FOLDER = '%s/project' % HOST_FOLDER
CONAN_STORAGE = '%s/conan.storage' % HOST_FOLDER
SANDBOX_FOLDER = '%s/.sandbox' % HOST_FOLDER


class Runner(object):

    def __init__(self, sandbox, name=None):
        self._name = name
        self._sandbox = sandbox
        self._project = sandbox.project
        self._profile = self._project.profile
        self._api = self._project.api
        self._config = self._sandbox.api.load_config()
        self._runner = None
        if not name:
            self._runner = self._profile.docker.runner
            name = 'docker' if self._runner else 'shell'
        else:
            if name not in ['shell', 'docker']:
                self._runner = self._config.get('runner', {}).get(name)
                if not self._runner:
                    raise Exception('<%s> not defined in config file runner section.' % name)
        self._name = name

        # TODO: add validation of being runnable for this profile

    def exec(self, command, argv):
        filename = os.path.normpath(os.path.join(self._project.folder.out, 'sandbox', command))
        if PLATFORM == 'Windows':
            if not os.path.exists(filename):
                for ext in ['.cmd', '.bat', '.ps1']:
                    if os.path.exists(filename + ext):
                        filename += ext
                        break

        if not os.path.exists(filename):
            raise EException("No <%s> sandbox program!" % command)

        conan_storage = os.path.normpath(self._api.conan_storage_path)

        env = {'CONAN_STORAGE_PATH': conan_storage}
        if self._name in ['shell', 'docker']:
            runner = ConanRunner(output=self._api.out)
            command = [filename] + argv
            #if PLATFORM == 'Linux':
            #    command = ['/bin/bash'] + command
            import locale

            language, encoding = locale.getdefaultlocale()

            with environment_append(env):
                proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        shell=True, encoding=encoding)
                while True:
                    out, err = proc.communicate()
                    if out:
                        print(out)
                    if err:
                        print(err)
                    if proc.poll() is None:
                        time.sleep(0.1)
                    else:
                        return proc.returncode

                #return runner(command)

        if 'docker' in self._runner:
            docker = dict(self._runner, home='/tmp', shell='/bin/bash')
            env['EPM_SANDBOX_IMAGE'] = docker['image']
            env['EPM_SANDBOX_HOME'] = docker['home']
            env['EPM_SANDBOX_SHELL'] = docker['shell']
            env['EPM_SANDBOX_RUNNER'] = 'shell'
            runner = ConanRunner(output=self._api.out)
            command = [filename] + argv

            with environment_append(env):
                return runner(command)

        elif 'ssh' in self._runner:
            runner = {'home': '/tmp', 'shell': '/bin/bash'}
            runner = dict(runner, **self._runner)

            localhost = self._config['localhost']
            ssh = SSH(runner['hostname'], runner['ssh']['username'], runner['ssh']['password'], runner['ssh']['port'])
            ssh.open()

            home = runner['home']
            project = '{}/{}'.format(home, PROJECT_FOLDER)
            storage = '{}/{}'.format(home, CONAN_STORAGE)
            sandbox = '{}/{}'.format(home, SANDBOX_FOLDER)
            home = '{}/{}'.format(runner['home'], HOST_FOLDER)

            cmd = 'mkdir -p {0}'.format(home)
            ssh.call(cmd, check=True)

            cmd = '[ -d {0} ] && rm -rf {0}'.format(sandbox)
            ssh.call(cmd)

            def _mnt(path, directory):
                cmd = '[ ! -d {0} ] && mkdir {0}'.format(directory)
                ssh.call(cmd)

                ssh.mount(path, directory,
                          interface=localhost['hostname'],
                          username=localhost['username'],
                          password=localhost['password'])
            _mnt(self._project.dir, project)
            _mnt(conan_storage, storage)

            command = "export EPM_SANDBOX_HOME={};".format(home)
            command += "export EPM_SANDBOX_STORAGE={};".format(storage)
            command += "export EPM_SANDBOX_PROJECT={};".format(project)
            command += "cd {} && ".format(project)
            command += './'+pathlib.PurePath(filename).as_posix()
            command = [command] + argv
            return ssh.call(command)


class Sandbox(Worker):

    def __init__(self, project, api=None):
        super(Sandbox, self).__init__(api)
        self.project = project

    def exec(self, command, runner=None, argv=[]):
        runner = Runner(self, runner)

        return runner.exec(command, argv)

def _build_test(project, program):
    name = program['name']

    project.api.out.highlight(f"\n==== build test ({name})\n")

    build_folder = os.path.join(project.folder.test, name)
    WD = os.path.join(project.dir, program['project'])

    conan = project.api.conan
    scheme = project.scheme

    info = conan.install(WD,
                         options=scheme.as_list(True),
                         profile_names=[project.abspath.profile_host],
                         install_folder=build_folder,
                         profile_build=project.profile.build)
    if info['error']:
        raise EConanException('configure test <{}> failed.'.format(folder), info)

    conan.build(WD,
                build_folder=build_folder,
                install_folder=build_folder)


def build_tests(project, tests=None):
    metainfo = project.metainfo
    sandboxes = metainfo.get('sandbox') or {}

    program = {}
    for name, sandbox in sandboxes.items():

        if isinstance(sandbox, str):
            sandbox = {'program': sandbox}
        prj = copy.deepcopy(sandbox)
        if not prj.get('project'):
            if os.path.exists(f"{name}/conanfile.py"):
                prj['project'] = name
            elif os.path.exists(f"test_package/{name}/conanfile.py"):
                prj['project'] = f"test_package/{name}"
        prj['name'] = name
        program[name] = prj
    if tests is None:
        tests = list(program.keys())

    for i in tests:
        if program[i].get('project'):
            _build_test(project, program[i])




################################################################################
#                                                                              #
#        Generator                                                             #
#                                                                              #
################################################################################
class Generator(object):

    def __init__(self, project, pattern, is_create=False, storage=None):
        self._project = project
        self._is_create = is_create
        self._wd = pathlib.PurePath(os.path.abspath('.')).as_posix()
        self._storage_path = storage or os.getenv('CONAN_STORAGE_PATH') or self._project.api.conan_storage_path
        self._short_path = os.getenv('CONAN_USER_HOME_SHORT') or 'c:'
        self._program = self._program_info(pattern, is_create)
        assert self._program, f"pattern: {pattern} is_create:{is_create}"

        self._conaninfo = ConanInfo.loads(load(self._program['conaninfo']))

        self._libs, self._deps = self._parse_dynamic_libs()

    def _path_format(self, path):
        path = pathlib.PurePath(path)
        storage = pathlib.PurePath(self._storage_path).as_posix()
        short = pathlib.PurePath(self._short_path).as_posix()
        cwd = pathlib.PurePath(self._project.dir).as_posix()

        try:
            return '${project}/%s' % path.relative_to(cwd)
        except:
            pass

        try:
            return '${storage}/%s' % path.relative_to(storage)
        except:
            pass

        try:
            return '${short}/%s' % path.relative_to(short)
        except:
            pass
        return None

    def _program_info(self, pattern, is_create):
        project = self._project
        folders = ['test', 'package', 'build']

        maps = {'build': ['${build}', '$build'],
                'package': ['${package}', '$build'],
                'test': ['${test}', '$test']
                }

        for folder, symbols in maps.items():
            for prefix in symbols:
                if pattern.startswith(prefix):
                    folders = [folder]
                    pattern = pattern[len(prefix)+1:]
                    break

        syslog.info(f"{pattern} -->> " + "|".join(folders))

        for folder in folders:
            if folder in ['build', 'package'] and is_create:
                id = project.record.get('package_id')
                root = 'storage'
                rpath = os.path.join(project.reference.dir_repr(), folder, id)
                rootpath = os.path.join(self._storage_path, rpath)

            else:
                root = 'project'
                rpath = os.path.join(project.path.out, folder)
                rootpath = os.path.join(project.dir, rpath)

            patterns = [pattern]
            if project.profile.host.settings['os'] == 'Windows':
                patterns = [f"{pattern}.exe"] + patterns

            syslog.info("searching in [{}] possible program : \n{}".format(folder, "\n".join(patterns)))

            for p in patterns:
                with chdir(rootpath):
                    result = glob.glob(p)
                    syslog.info('glob in {} for [{}]. find {}:\n{}'.format(rootpath, p, len(result), "\n".join(result)))
                    if not result:
                        continue
                    filename = result[0]
                    origin = folder
                    if origin == 'test':
                        sb = pattern.split('/')[0]
                        filename = f"test/{filename}"
                        conaninfo = os.path.join(rootpath, sb, 'conaninfo.txt')
                        if not os.path.exists(conaninfo):
                            conaninfo = os.path.join(rootpath, 'conaninfo.txt')
                    elif origin == 'package':
                        conaninfo = os.path.join(rootpath, 'conaninfo.txt')
                    assert os.path.exists(conaninfo)
                    return {'rootpath': rootpath,
                            'root': root,
                            'rpath': rpath,
                            'files': result,
                            'conaninfo': conaninfo,
                            'origin': origin,
                            'filename': filename,
                            'path': os.path.join(rootpath, result[0])
                            }
        return None

    def _parse_dynamic_libs(self):
        libs = []
        deps = []
        win = bool(self._conaninfo.settings.os == 'Windows')
        with chdir(self._storage_path):
            for pref in self._conaninfo.full_requires:
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

    def _template(self, filename):
        path = os.path.join(DATA_DIR, 'sandbox')
        env = Environment(loader=FileSystemLoader(path))

        def _basename(x):
            return os.path.basename(x)

        def _dirname(x):
            return os.path.dirname(x)

        env.filters['basename'] = _basename
        env.filters['dirname'] = _dirname

        env.trim_blocks = True
        template_file = os.path.basename(filename)
        template = env.get_template(template_file)
        return template

    def _windows(self, name, argv):
        libs = set()
        deps = set()

        for i in self._libs:
            libs.add(os.path.dirname(i))
        for i in self._deps:
            deps.add(os.path.dirname(i))

        template = self._template('windows.cmd.j2')

        return template.render(name=name,
                               libs=libs,
                               deps=deps,
                               project=self._project,
                               program=self._program,
                               command='create' if self._is_create else 'build',
                               package_id=self._project.record.get('package_id'),
                               arguments=" ".join(argv))

    def _render(self, name, argv, template):
        libs = set()
        deps = set()

        for i in self._libs:
            libs.add(os.path.dirname(i))
        for i in self._deps:
            deps.add(os.path.dirname(i))

        t = self._template(template)

        return t.render(name=name,
                        libs=libs,
                        deps=deps,
                        project=self._project,
                        program=self._program,
                        command='create' if self._is_create else 'build',
                        package_id=self._project.record.get('package_id'),
                        arguments=" ".join(argv))

    def run(self, name, argv):

        filename = os.path.join(self._project.folder.out, 'sandbox', name)
        mkdir(os.path.dirname(filename))

        if self._conaninfo.settings.os == 'Windows':
            script = self._windows(name, argv).encode('utf-8')
            with open(filename + '.cmd', 'wb') as f:
                f.write(script)
        else:
            script = self._render(name, argv, 'linux.sh.j2').encode('utf-8')
            with open(filename, 'wb') as f:
                f.write(script)
            mode = os.stat(filename).st_mode
            os.chmod(filename, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

            script = self._render(name, argv, 'linux.cmd.j2').encode('utf-8')
            with open(filename + '.cmd', 'wb') as f:
                f.write(script)

    def __repr__(self):
        txt = ""
        txt += f"filename: {self._filename}\n"
        txt += f"origin: {self._origin}\n"
        txt += "[full_requires]\n"
        for pref in self._conaninfo.full_requires:
            txt += "    {}:{} ({})\n".format(pref.ref.dir_repr(), pref.id, self._conaninfo.settings.os)
        return txt

    @staticmethod
    def build(project, is_create=False, targets=None):
        metadata = project.metainfo
        minfo = metadata.get('sandbox')
        if not minfo:
            return
        if not targets:
            targets = set(minfo.keys())

        if isinstance(targets, str):
            targets = {targets}
        elif isinstance(targets, list):
            targets = set(targets)
        targets &= set(minfo.keys())

        for name in targets:
            config = minfo[name]
            argv = ''
            if isinstance(config, dict):
                script = config['program']
            elif isinstance(config, str):
                script = config
            else:
                raise
            tokens = script.split(' ', 1)
            pattern = script
            if len(tokens) == 2:
                pattern = tokens[0]
                argv = tokens[1]

            Generator(project, pattern, is_create).run(name, argv)


