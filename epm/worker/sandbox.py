

import os
import glob
import fnmatch
from epm.errors import EException
from epm.worker import Worker
from epm.model.project import Project
from epm.errors import APIError
from epm.model.sandbox import Program
from epm.util import is_elf, system_info
from epm.util.files import remove, rmdir, load_yaml

PLATFORM, ARCH = system_info()


def is_running_native(scheme):
    profile = scheme.profile


class Runner(object):

    def __init__(self, sandbox, name=None):
        self._name = name
        self._sandbox = sandbox

    def _load_config(self, name=None):
        name = name or self._name
        config = self._sandbox.api.load_config()
        runners = config.get('runner', {})
        profile = self._sandbox.project.scheme.profile
        runner = None

        if name is None:
            if profile.is_running_native:
                runner = {'shell': 'dos'}
            elif profile.docker.runner:
                runner = {'docker': {
                    'image': profile.docker.runner['image'],
                    'shell': profile.docker.runner['shell'],
                    'WD': profile.docker.runner['home']
                }}
            else:
                for _, i in runners.items():
                    platform = i.get('information', {}).get('platform')
                    arch = i.get('information', {}).get('arch')
                    distro = i.get('information', {}).get('distro')

                    if profile.settings['os'] == platform and profile.settings['arch'] == arch:
                        if 'arm' in arch:
                            if profile.settings.get('compiler.toolchain') == 'arm-hisiv300-linux':
                                if distro in ['EdgeOS']:
                                    runner = i
                                    break
                        else:
                            runner = i
                            break
        else:
            runner = runners.get(name)
            if not runner:
                raise EException('specified runner %s not configured!' % name)
        return config.get('localhost'), runner

    def exec(self, command, argv):
        project = self._sandbox.project
        manifest = project.manifest
        if not manifest.get('sandbox', {}).get(command):
            raise EException('No sandbox command %s defined' % command)

        filename = os.path.normpath(os.path.join(project.folder.out, 'sandbox', command))

        localhost, runner_config = self._load_config()
        if runner_config.get('remote'):
            pass
        elif runner_config.get('docker'):
            pass
        else:  # local
            from conans.client.tools import ConanRunner
            runner = ConanRunner(output=self._sandbox.api.out)
            command = [filename] + argv
            return runner(command)


class Sandbox(Worker):

    def __init__(self, project, api=None):
        super(Sandbox, self).__init__(api)
        self.project = project

    def exec(self, command, runner=None, argv=[]):
        runner = Runner(self, runner)
        return runner.exec(command, argv)
