import sys
import os
import shutil

from epm.util.files import cache
from epm.util import system_info
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
        command = '{} {}'.format(" ".join(command), " ".join(argv))
        return runner(command)


class Runit(Worker):

    def __init__(self, project, api=None):
        super(Runit, self).__init__(api)
        self.project = project

    def exec(self, command, runner=None, argv=[]):

        m = self.project.metainfo.data
        script = m.get('script', {}).get(command)
        if not script:
            raise ModuleNotFoundError('no <{}> in script'.format(command))

        cmdline = script
        if isinstance(script, dict):
            location = script.get('location')
            cmdline = script.get('command')
            path = os.path.normpath(os.path.join('.epm', 'script', command))
            if os.path.exists(path):
                shutil.rmtree(path)
            d = cache(location)
            shutil.copytree(d, path)
            cmdline = '%s/%s' % (path, cmdline)

        cmdline = cmdline.strip()
        args = cmdline.split(' ', 1)
        filename = args[0]
        command = []

        if len(args) > 1:
            import shlex

            for i in shlex.split(args[1]):
                if ' ' in i:
                    i = '"{}"'.format(i)
                print('*', i)

                command.append(i)

        command = [filename] + command

        if filename.endswith('.py'):
            command = [sys.executable] + command

        profile = self.project.profile.name if self.project.profile else None
        scheme = self.project.scheme.name if self.project.scheme else None

        env_vars = {'EPM_RUN_PROFILE': profile,
                    'EPM_RUN_SCHEME': scheme,
                    'EPM_RUN_RUNNER': runner
                    }

        from conans.tools import environment_append
        with environment_append(env_vars):
            return Runner(self, 'shell').exec(command, argv)


