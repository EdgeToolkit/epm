

import os
import glob
import fnmatch
import paramiko
import pathlib
from epm.errors import EException
from epm.worker import Worker
from epm.model.project import Project
from epm.errors import APIError
from epm.model.sandbox import Program
from epm.util import is_elf, system_info
from epm.util.files import remove, rmdir, load_yaml
from conans.client.tools import ConanRunner
from epm.tool.ssh import SSH
from conans.tools import environment_append


PLATFORM, ARCH = system_info()






class Remoter(SSH):

    def __init__(self, localhost, machine):
        self._localhost = localhost
        self._machine = machine
        super(Remoter, self).__init__(hostname=self._machine['hostname'],
                                      username=self._machine['ssh']['username'],
                                      password=self._machine['ssh']['password'],
                                      port=self._machine['ssh'].get('port'))

    def mount(self, source, directory, host):
        if not pathlib.PurePath(directory).is_absolute():
            directory = os.path.join(self.WD, directory)

        source = pathlib.PurePosixPath(source).as_posix()
        directory = pathlib.PurePosixPath(directory).as_posix()

        try:
            self.call('[[ -d {0} ]] && umount {0}'.format(directory))
        except:
            pass
        formatter = 'mount -t nfs -o nolock {hostname}:{source} {directory}'

        if PLATFORM == 'Windows':
            source = source.replace(':', '')
            formatter = 'mount -t cifs -o user={username},pass={password},noserverino //{hostname}/{source} {directory}'

        cmd = formatter.format(hostname=self._localhost['hostname'],
                               username=self._localhost['username'],
                               password=self._localhost['password'],
                               source=source,
                               directory=directory)
        self.call(cmd, check=True)







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
        conan_storage = self._api.conan_storage_path
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
            #ssh.WD = home

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

    def __init__(self, project):
        self._project = project
        self._api = project.api

    def exec(self, program=None, steps=None):
        metainfo = self._project.metainfo
        steps = steps or ['configure', 'make']
        program = program or metainfo.sandbox.keys()
        if isinstance(program, str):
            program = [program]

        undef = set(program).difference(metainfo.sandbox.keys())
        if undef:
            raise EException('{} NOT valid sandbox item'.format(",".join(undef)))

        sandboxes = {}
        for name in program:
            sb = metainfo.sandbox[name]
            directory = sb.directory if sb.directory else ''
            if sb.directory not in sandboxes:
                sandboxes[directory] = []
            sandboxes[directory].append(sb)

        profile = os.path.join(self._project.folder.out, 'profile')
        if 'configure' in steps:
            self._project.profile.save(profile)
        conan = self._api.conan
        options = ['%s=%s' % (k, v) for k, v in self._project.scheme.package_options.as_list()]

        for folder, sbs in sandboxes.items():
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
                                     options=options,
                                     profile_names=[profile],
                                     install_folder=build_folder)
                if info['error']:
                    raise Exception('configure sandbox %s failed.' % folder)

            if 'make' in steps and folder:
                _('make')
                conan.build(conanfile_path,
                            build_folder=build_folder,
                            install_folder=build_folder
                            )

            if 'make' in steps:

                for sb in sbs:
                    program = Program(self._project, sb, build_folder)
                    program.generate(sb.name)



