import os
import shlex
from epm.utils.process import Process
from epm.model.project import Project


class Sandbox(object):

    def __init__(self, name, directory='.', profile=None, scheme=None, runner=None, hostname=None):
        self._name = name
        profile = profile or os.getenv('EPM_SANDBOX_PROFILE')
        scheme = scheme or os.getenv('EPM_SANDBOX_SCHEME')
        self._runner = runner or os.getenv('EPM_SANDBOX_RUNNER')
        self._project = Project(profile, scheme, directory=directory)
        metainfo = self._project.metainfo
        config = metainfo.get('sandbox') or {}
        self._config = config.get(self._name)
        if not self._config:
            raise LookupError(f"Sandbox {self._name} not exists.")
        self._proc = None
        self._hostname = hostname or "127.0.0.1"

    @property
    def hostname(self):
        return self._hostname

    @property
    def proc(self):
        return self._proc

    def start(self, argv=[], archive=None):
        command = [f"{self._project.path.out}\\sandbox\\{self._name}.cmd"]
        self._proc = Process(command, shell=True,
                             cache_dir=os.path.join(self._project.path.out, 'temp'))
        env = None
        if archive:
            if not os.path.isabs(archive):
                os.path.join(self._project.dir, archive)
            env = {'EPM_SANDBOX_ARCHIVE': archive}
        self._proc.start(argv, env=env)
        return self._proc

