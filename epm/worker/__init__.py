import os
import base64
import json

from epm.util import system_info
from epm.errors import EException, APIError

PLATFORM, ARCH = system_info()

def param_encode(param):
    if not param:
        return ''
    else:
        assert (isinstance(param, dict))
        return str(base64.b64encode(json.dumps(param).encode('utf-8')), 'utf-8')


def param_decode(param):
    assert (isinstance(param, str))
    return json.loads(base64.b64decode(param))


class Worker(object):

    def __init__(self, api=None):
        self._api = api
        self._out = None

    @property
    def api(self):
        if self._api is None:
            from epm.api import API
            self._api = API()
        return self._api

    @property
    def out(self):
        if self._out is None:
            self._out = self._api.out
        return self._out

    @property
    def conan(self):
        return self.api.conan


def _uname(prj):
    import time
    name = '%s_%s_%s' % (prj.name, prj.scheme.name, time.time())
    for i in "@:/":
        name = name.replace(i,'-')
    return name


class DockerRunner(object):
    _DEBUG = None

    def __init__(self, api, project=None):
        self._api = api
        self._project = project
        self.volumes = {}
        self.environment = {}
        self.WD = None
        self._pre_script = ''
        self.command_str = ''
        self.name = _uname(self._project)
        self.returncode =None

    def exec(self, commands, config=None):
        from conans.client.runner import ConanRunner as Runner
        config, WD, volumes, environment = self._preprocess(config)

        command = self._command(commands, config, WD, volumes, environment)
        args = ['docker', 'run', '--name', self.name, '--rm']

        if PLATFORM == 'Linux' and os.getuid():
            args = ['sudo'] + args

        for path, value in volumes.items():
            mode = value.get('mode', 'rw')
            bind = value['bind']
            vol = '%s:%s' % (path, bind)
            if mode == 'ro':
                vol += ':ro'
            args += ['-v', vol]

        for name, val in environment.items():
            args += ['-e', '%s=%s' % (name, val)]

        args += ['-e', 'EPM_DOCKER_IMAGE={}'.format(config['image'])]
        args += ['-e', 'EPM_DOCKER_CONTAINER_NAME={}'.format(self.name)]
        banner = os.getenv('EPM_DISPLAY_BANNER') or 'YES'
        args += [] if banner.lower() in ['no'] else ['-e', 'EPM_NO_BANNER={}'.format(banner)]

        workbench = os.environ.get('EPM_WORKBENCH')
        args += ['-e', 'EPM_WORKBENCH={}'.format(workbench)] if workbench else []

        wd = WD or config.get('home')
        args += ['-w', wd] if wd else []

        args += [config['image'], command]
        cmd = " ".join(args)

        out = self._api.out
        docker = Runner(output=out)
        self.command_str = cmd
        self.returncode = docker(cmd)
        print('------------------------------------------------')
        print(cmd)
        print('-----------------%d------------------------------' % self.returncode)
        return self.returncode

    def add_volume(self, path, bind, mode='rw'):
        """
        :param path: host path or volume
        :param bind: path in container
        :param mode: rw, ro
        :return:
        """
        self.volumes[path] = {'bind': bind, mode: mode}

    def _command(self, commands, config, wd, volumes, environment):
        sh = config.get('shell', '/bin/bash')

        if isinstance(commands, str):
            commands = [commands]

        command = r'%s -c "%s"' % (sh, " && ".join(commands))
        return command

    def _preprocess(self, config):
        profile = self._project.profile

        config = config or profile.docker.builder
        config = dict({'shell': '/bin/bash', 'home': '/tmp'}, **config)

        WD = self._docker_var_parse(config, self.WD)
        volumes = dict({}, **self.volumes)
        environment = {}
        for i in ['EPM_WORK_ENVIRONMENT']:
            val = os.environ.get(i)
            if val:
               environment[i] = val

        for key, value in volumes.items():
            value['bind'] = self._docker_var_parse(config, value['bind'])

        for key, value in self.environment.items():
            environment[key] = self._docker_var_parse(config, value)
        return config, WD, volumes, environment

    def _docker_var_parse(self, config, value):
        from string import Template
        s = Template(value)
        return s.substitute(config)


DockerBase = DockerRunner
