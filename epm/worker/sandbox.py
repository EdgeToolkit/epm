

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
            runner = dict(self._runner, home='/tmp', shell='/bin/bash')
            localhost = self._config['localhost']
            ssh = SSH(runner['hostname'], runner['ssh']['username'], runner['ssh']['password'], runner['ssh']['port'])
            ssh.open()
            ssh.WD = runner['home']

            # mkdir HOST_FOLDER
            cmd = '[ ! -d {0} ] && mkdir {0}'.format(HOST_FOLDER)
            ssh.call(cmd)

            cmd = '[ -d {0} ] && rm -rf {0}'.format(SANDBOX_FOLDER)
            ssh.call(cmd)

            def _mnt(path, directory):
                cmd = '[ ! -d {0} ] && mkdir {0}'.format(directory)
                ssh.call(cmd)

                ssh.mount(path, directory,
                          interface=localhost['hostname'],
                          username=localhost['username'],
                          password=localhost['password'])

            _mnt(self._project.dir, PROJECT_FOLDER)
            _mnt(conan_storage, CONAN_STORAGE)

            command = [pathlib.PurePath(filename).as_posix()] + argv
            return ssh.call(command, cwd=PROJECT_FOLDER)


class Sandbox(Worker):

    def __init__(self, project, api=None):
        super(Sandbox, self).__init__(api)
        self.project = project

    def exec(self, command, runner=None, argv=[]):
        runner = Runner(self, runner)

        return runner.exec(command, argv)
