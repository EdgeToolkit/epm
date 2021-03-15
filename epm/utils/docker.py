import os
import stat
from conans.tools import mkdir, rmdir
from epm.utils import Jinja2, PLATFORM
import pathlib
from epm.utils.logger import syslog

class Volume(object):

    def __init__(self, source, destination, option=None):
        self.source = pathlib.PurePath(source).as_posix()
        self.destination = pathlib.PurePath(destination).as_posix()
        self.option = option

    @property
    def volume(self):
        v = f"{self.source}:{self.destination}"
        return f"{v}:{self.option}" if self.option else v

    @property
    def volume4win(self):
        destination = pathlib.PurePath(self.destination).as_posix()
        source = self.source.replace('/', "\\")
        v = f"{source}:{destination}"
        return f"{v}:{self.option}" if self.option else v


class _Docker(object):
    environment = {}

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
        self.workbench = workbench or os.environ.get('EPM_WORKBENCH') or ''
        self.project = project

        docker = self.project.profile.docker.builder
        prefix = os.getenv('EPM_DOCKER_BUILDER_IMAGE_PREFIX') or ''

        self.home = docker['home']
        self.image = prefix + docker['image']
        self.shell = docker['shell']
        self.cwd = f"{self.home}/project"

        src = os.path.expanduser('~/.epm')
        dst = f"{self.home}/.epm"
        #if self.workbench:
        #    src = os.path.join(src, '.workbench', self.workbench)
        #    dst = f"{dst}/.workbench/{self.workbench}"

        self.volume.append(Volume(src, dst))
        self.volume.append(Volume(self.project.dir, self.cwd))

    def generate(self, command):
        out_dir = os.path.join(self.project.folder.cache, 'docker', self.project.folder.name)
        rmdir(out_dir)
        mkdir(out_dir)

        context = {'docker': self, 'workbench': self.workbench or '',
                   'script_dir': pathlib.PurePath(out_dir).as_posix(),
                   'command': command}
        from epm.utils import Jinja2
        from epm import DATA_DIR
        j2 = Jinja2(f"{DATA_DIR}", context=context)
        for src, dst in [('docker/build.sh.j2', f"{out_dir}/build_docker.sh"),
                         ('docker/build.cmd.j2', f"{out_dir}/build_docker.cmd"),
                         ('docker/build_command.sh.j2', f"{out_dir}/docker_build_command.sh")]:
            j2.render(src, outfile=dst)
            os.chmod(dst, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        return out_dir

    def run(self, command):
        import subprocess
        out_dir = self.generate(command)
        if PLATFORM == 'Linux':
            out_dir = pathlib.PurePath(out_dir).as_posix()
            command = ['/bin/bash', f"{out_dir}/build_docker.sh"]
        elif PLATFORM == 'Windows':
            out_dir = pathlib.WindowsPath(out_dir)
            command = ['cmd.exe', '/c', f"{out_dir}\\build_docker.cmd"]
        else:
            raise Exception(f'Unsupported platform <{PLATFORM}>')
        from conans.tools import environment_append
        with environment_append({'EPM_WORKBENCH': self.workbench}):
            syslog.close()
            proc = subprocess.run(command)
            syslog.open('========== docker command done ===============')
        return proc

