import sys
import traceback
class EException(Exception):
    """
         Generic EPM exception
    """

    def __init__(self, message, **kwargs):
        super(EException, self).__init__(message)


class EConanException(EException):

    def __init__(self, message, exception=None):
        self.exception = exception
        super(EConanException, self).__init__(message)


class EDockerException(EException):

    def __init__(self, message, docker=None):
        from epm.worker import DockerBase
        if isinstance(docker, DockerBase):
            self.docker = {'returncode': docker.returncode,
                      'command': docker.command_str,
                      }

        super(EException, self).__init__(message)

