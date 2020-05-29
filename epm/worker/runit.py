import sys
import os
import pathlib
from epm.model.sandbox import Program
from epm.util import is_elf, system_info
from epm.util.files import remove, rmdir, load_yaml
from epm.worker import Worker
from conans.client.tools import ConanRunner
PLATFORM, ARCH = system_info()



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
        runner = ConanRunner(output=self._api.out)

        return runner(command + argv)


class Runit(Worker):

    def __init__(self, project, api=None):
        super(Runit, self).__init__(api)
        self.project = project

    def exec(self, command, runner=None, argv=[]):

        m = self.project.manifest.as_dict()
        script = m.get('script', {}).get(command)
        if not script:
            raise ModuleNotFoundError('no <{}> in script'.format(command))
        command = []
        if script.endswith('.py'):
            command = [sys.executable]
        command += [script]

        profile = self.project.profile.name if self.project.profile else None
        scheme = self.project.scheme.name if self.project.scheme else None


        env_vars = {'EPM_RUN_PROFILE':  profile,
                    'EPM_RUN_SCHEME': scheme,
                    'EPM_RUN_RUNNER': runner
                    }


        from conans.tools import environment_append
        with environment_append(env_vars):
            return Runner(self, 'shell').exec(command, argv)


