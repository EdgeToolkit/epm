import os
import pathlib
from epm.errors import EConanException, EException
from epm.worker import Worker
from epm.model.sandbox import Program
from epm.utils import PLATFORM
from conans.client.tools import ConanRunner
from epm.tools.ssh import SSH
from epm.tools import parse_sandbox
from conans.tools import environment_append


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

        conan_storage = os.path.normpath(self._api.conan_storage_path)

        env = {'CONAN_STORAGE_PATH': conan_storage}
        if self._name in ['shell', 'docker']:
            runner = ConanRunner(output=self._api.out)
            command = [filename] + argv

            with environment_append(env):
                return runner(command)

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
            from epm.model.sandbox import HOST_FOLDER, PROJECT_FOLDER, CONAN_STORAGE, SANDBOX_FOLDER
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


class Builder(object):

    def __init__(self, project, is_create_method=False):
        self._project = project
        self._api = project.api
        self._is_create_method = is_create_method

    def exec(self, program=None, steps=None):
        if 'sandbox' not in self._project.__meta_information__:
            conanfile_path = os.path.join(self._project.dir, 'test_package', 'coanfile.py')
            if os.path.isfile(conanfile_path):
                print('===== Build TEST_PACKAGE')
                self._configure(conanfile_path)
                self._build(conanfile_path)
        else:
            self._exec(program, steps)

    def _configure(self, conanfile_path, name='test_package'):
        conan = self._project.api.conan
        scheme = self._project.scheme
        build_folder = os.path.join(self._project.folder.out, name, 'build')
        info = conan.install(conanfile_path,
                             name=name,
                             settings=None,  # should be same as profile
                             options=scheme.as_list(True),
                             profile_names=[self._profile],
                             install_folder=build_folder)
        if info['error']:
            raise EConanException('configure sandbox <{}> failed.'.format(name), info)

    def _build(self, conanfile_path, name='test_package'):
        conan = self._project.api.conan
        build_folder = os.path.join(self._project.folder.out, name, 'build')
        conan.build(conanfile_path,
                    build_folder=build_folder,
                    install_folder=build_folder
                    )


    @property
    def _profile(self):
        profile = os.path.join(self._project.folder.out, 'profile')
        if not os.path.exists(profile):
            self._project.profile.save(profile)
        return profile

    def _exec(self, program=None, steps=None):
        scheme = self._project.scheme
        sandbox = parse_sandbox(self._project.__meta_information__)
        steps = steps or ['configure', 'make']
        program = program or sandbox.keys()
        if isinstance(program, str):
            program = [program]

        undef = set(program).difference(sandbox.keys())
        if undef:
            raise EException('{} NOT valid sandbox item'.format(",".join(undef)))

        candidate = {}
        for name in program:
            sb = sandbox[name]
            directory = sb.directory if sb.directory else ''
            if sb.directory not in candidate:
                candidate[directory] = []
            candidate[directory].append(sb)

        profile = os.path.join(self._project.folder.out, 'profile')
        if 'configure' in steps:
            self._project.profile.save(profile)
        conan = self._api.conan

        for folder, sbs in candidate.items():
            if folder:
                conanfile_path = os.path.join(folder, 'conanfile.py')
                build_folder = os.path.join(self._project.folder.out, folder, 'build')

                name = '{}-{}'.format(self._project.name, folder.replace('-', '_'))

            def _(step):
                self._api.out.highlight('[%s sandbox program] %s. project folder  %s'
                                       % (step, ",".join([x.name for x in sbs]), folder))

            _('Build')

            if 'configure' in steps and folder:
                _('configure')
                info = conan.install(conanfile_path,
                                     name=name,
                                     settings=None,  # should be same as profile
                                     options=scheme.as_list(True),
                                     profile_names=[profile],
                                     install_folder=build_folder)
                if info['error']:
                    raise EConanException('configure sandbox <{}> failed.'.format(folder), info)

            if 'make' in steps and folder:
                _('make')
                conan.build(conanfile_path,
                            build_folder=build_folder,
                            install_folder=build_folder
                            )

            if 'make' in steps:
                for sb in sbs or []:

                    subpath = build_folder if folder else os.path.join(self._project.folder.out, sb.type)
                    if self._is_create_method and not folder:
                        id = self._project.record.get('package_id')

                        subpath = os.path.join(os.getenv('CONAN_STORAGE_PATH'), self._project.reference.dir_repr(),
                                               sb.type, id)

                    program = Program(self._project, sb, subpath)
                    program.generate(sb.name)



class _TODEL_Builder(object):

    def __init__(self, project, is_create_method=False):
        self._project = project
        self._api = project.api
        self._is_create_method = is_create_method

    def exec(self, program=None, steps=None):
        scheme = self._project.scheme
        sandbox = parse_sandbox(self._project.__meta_information__)
        steps = steps or ['configure', 'make']
        program = program or sandbox.keys()
        if isinstance(program, str):
            program = [program]

        undef = set(program).difference(sandbox.keys())
        if undef:
            raise EException('{} NOT valid sandbox item'.format(",".join(undef)))

        candidate = {}
        for name in program:
            sb = sandbox[name]
            directory = sb.directory if sb.directory else ''
            if sb.directory not in candidate:
                candidate[directory] = []
            candidate[directory].append(sb)

        profile = os.path.join(self._project.folder.out, 'profile')
        if 'configure' in steps:
            self._project.profile.save(profile)
        conan = self._api.conan

        for folder, sbs in candidate.items():
            if folder:
                conanfile_path = os.path.join(folder, 'conanfile.py')
                build_folder = os.path.join(self._project.folder.out, folder, 'build')

                name = '{}-{}'.format(self._project.name, folder.replace('-', '_'))

            def _(step):
                self._api.out.highlight('[%s sandbox program] %s. project folder  %s'
                                       % (step, ",".join([x.name for x in sbs]), folder))

            _('Build')

            if 'configure' in steps and folder:
                _('configure')
                info = conan.install(conanfile_path,
                                     name=name,
                                     settings=None,  # should be same as profile
                                     options=scheme.as_list(True),
                                     profile_names=[profile],
                                     install_folder=build_folder)
                if info['error']:
                    raise EConanException('configure sandbox <{}> failed.'.format(folder), info)

            if 'make' in steps and folder:
                _('make')
                conan.build(conanfile_path,
                            build_folder=build_folder,
                            install_folder=build_folder
                            )

            if 'make' in steps:
                for sb in sbs or []:

                    subpath = build_folder if folder else os.path.join(self._project.folder.out, sb.type)
                    if self._is_create_method and not folder:
                        id = self._project.record.get('package_id')

                        subpath = os.path.join(os.getenv('CONAN_STORAGE_PATH'), self._project.reference.dir_repr(),
                                               sb.type, id)

                    program = Program(self._project, sb, subpath)
                    program.generate(sb.name)
