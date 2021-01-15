#import os
#import base64
#import json
#
#from epm.utils import PLATFORM, banner_display_mode
#from epm.utils.logger import syslog
#from conans.tools import load, save
#
#def param_encode(param):
#    if not param:
#        return ''
#    else:
#        assert (isinstance(param, dict))
#        return str(base64.b64encode(json.dumps(param).encode('utf-8')), 'utf-8')
#
#
#def param_decode(param):
#    assert (isinstance(param, str))
#    return json.loads(base64.b64decode(param))


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

#
#def _uname(prj):
#    import time
#    name = '%s_%s_%s' % (prj.name, prj.scheme.name, time.time())
#    for i in "@:/":
#        name = name.replace(i, '-')
#    return name
#
#class DockerRunner(object):
#    _DEBUG = None
#
#    def __init__(self, api, project=None):
#        self._api = api
#        self._project = project
#        self.volumes = {}
#        self.environment = {}
#        self.WD = None
#        self._pre_script = ''
#        self.command_str = ''
#        self.name = _uname(self._project)
#        self.returncode =None
#
#    def exec(self, commands, config=None):
#        from conans.client.runner import ConanRunner as Runner
#        config, WD, volumes, environment = self._preprocess(config)
#        image = config['image']
#
#        command = self._command(commands, config, WD, volumes, environment)
#        args = ['--name', self.name, '--rm']
#
#        for path, value in volumes.items():
#            mode = value.get('mode', 'rw')
#            bind = value['bind']
#            vol = '%s:%s' % (path, bind)
#            if mode == 'ro':
#                vol += ':ro'
#            args += ['-v', vol]
#
#        for name, val in environment.items():
#            args += ['-e', '%s=%s' % (name, val)]
#
#        args += ['-e', 'EPM_DOCKER_IMAGE={}'.format(image)]
#        args += ['-e', 'EPM_DOCKER_CONTAINER_NAME={}'.format(self.name)]
#        args += ['-e', 'EPM_BANNER_DISPLAY_MODE={}'.format(banner_display_mode())]
#
#        workbench = os.environ.get('EPM_WORKBENCH')
#        args += ['-e', 'EPM_WORKBENCH={}'.format(workbench)] if workbench else []
#
#        wd = WD or config.get('home')
#        args += ['-w', wd] if wd else []
#
#        sudo = []
#
#        if PLATFORM == 'Linux' and os.getuid():
#            sudo = ['sudo', '-E']
#        self._pull_images_if_not_present(image, sudo)
#
#        cmd = sudo + ['docker', 'run'] + args + [image, command]
#        cmd = " ".join(cmd)
#
#        self._log_docker_command(args, image, command, cmd)
#
#        out = self._api.out
#        docker = Runner(output=out)
#        self.command_str = cmd
#
#        self.returncode = docker(cmd)
#        if self.returncode:
#            syslog.error('command execute in docker failed (%d)' % self.returncode)
#        else:
#            syslog.error('command execute in docker done.')
#        return self.returncode
#
#    def add_volume(self, path, bind, mode='rw'):
#        """
#        :param path: host path or volume
#        :param bind: path in container
#        :param mode: rw, ro
#        :return:
#        """
#        self.volumes[path] = {'bind': bind, mode: mode}
#
#    def _command(self, commands, config, wd, volumes, environment):
#        sh = config.get('shell', '/bin/bash')
#
#        if isinstance(commands, str):
#            commands = [commands]
#
#        command = r'%s -c "%s"' % (sh, " && ".join(commands))
#        return command
#
#    def _preprocess(self, config):
#        profile = self._project.profile
#
#        config = config or profile.docker.builder
#        config = dict({'shell': '/bin/bash', 'home': '/tmp'}, **config)
#
#        WD = self._docker_var_parse(config, self.WD)
#        volumes = dict({}, **self.volumes)
#        environment = {}
#        for i in ['EPM_WORK_ENVIRONMENT']:
#            val = os.environ.get(i)
#            if val:
#               environment[i] = val
#
#        for key, value in volumes.items():
#            value['bind'] = self._docker_var_parse(config, value['bind'])
#
#        for key, value in self.environment.items():
#            environment[key] = self._docker_var_parse(config, value)
#        return config, WD, volumes, environment
#
#    def _docker_var_parse(self, config, value):
#        from string import Template
#        s = Template(value)
#        return s.substitute(config)
#
#    def _log_docker_command(self, args, image, command, full_command_str):
#
#        if not os.path.exists('.epm/epm.prj'):
#            return
#        try:
#            epm_prj = load('.epm/epm.prj')
#            content = "docker run -it {}".format(" ".join(args))
#            content += " -v {}:/home/conan/epm ".format(epm_prj)
#            content += ' {} /bin/bash -c "pip install -e /home/conan/epm"'.format(image)
#            path = ".epm/docker-run{}".format(".cmd" if PLATFORM == 'Windows' else "")
#            save(path, content)
#        except:
#            pass
#
#    def _pull_images_if_not_present(self, image, sudo):
#        token = image.split(':')
#        name = token[0]
#        tag = 'latest' if len(token) == 1 else token[1]
#        import subprocess
#        command = sudo + ['docker', 'images', '-q', f"{name}:{tag}"]
#        proc = subprocess.run(command, stdout=subprocess.PIPE)
#        if proc.returncode or not proc.stdout:
#            self._api.out.info(f'docker image {image} not exits, pull it now.')
#            command = sudo + ['docker', 'pull', image]
#            subprocess.run(command, check=True)
#
#
#
#
#
#DockerBase = DockerRunner
