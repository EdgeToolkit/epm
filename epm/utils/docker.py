import os
from conans.tools import mkdir
from epm.utils import jinja_render


class Volume(object):

    def __init__(self, source, destination, option=None):
        self.source = source
        self.destination = destination
        self.option = option

    @property
    def volume(self):
        v = f"{self.source}:{self.destination}"
        return f"{v}:{self.option}" if self.option else v


class _Docker(object):
    enviroment = {}

    volume = []
    image = None
    cwd = None
    workbench = None

    def __init__(self):
        pass


class BuildDocker(_Docker):
    ENVIRONMENT = ['EPM_WORKBENCH']

    def __init__(self, project, workbench=None):
        super().__init__()
        self.workbench = workbench or os.environ['EPM_WORKBENCH']
        self.project = project


        docker = self.project.profile.docker.builder
        self.home = docker['home']
        self.image = docker['image']
        self.shell = docker['shell']
        self.cwd = f"{self.home}/project"

        src = os.path.expanduser('~/.epm')
        dst = f"{self.home}/.epm"
        if self.workbench:
            src = os.path.join(src, '.workbench', self.workbench)
            dst = f"{dst}/.workbench/{self.workbench}"

        self.volume.append(Volume(src, dst))
        self.volume.append(Volume(self.project.dir, self.cwd))

    def generate(self, command):

        out_dir = self.project.abspath.out
        mkdir(out_dir)
        context = {'docker': self, 'workbench': self.workbench,
                   'script_dir': self.project.folder.out,
                   'command': command}

        script = f"{out_dir}/build_docker.sh"

        jinja_render(context, 'docker/build.sh.j2', outfile=script)
        jinja_render(context, 'docker/build_command.sh.j2', outfile=f"{out_dir}/docker_build_command.sh")
        return script

    def run(self, command):
        import subprocess
        filename = self.generate(command)
        proc = subprocess.run(['/bin/bash', filename], stdout=subprocess.PIPE)
        return proc

