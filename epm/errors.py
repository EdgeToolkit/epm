import os
import sys
import yaml
import traceback
import inspect
from conans.errors import ConanException

from epm import logger
class EException(Exception):
    """
         Generic EPM exception
    """
    attributes = {'__traceback__': []}

    def __init__(self, message, **kwargs):
        if isinstance(message, dict) and '__class__' in message:
            self.attributes = message
            super(EException, self).__init__(message)
            return
        self.attributes = dict(message=message, **kwargs)
        self.attributes['__class__'] = self.__class__.__name__
        self.attributes['__traceback__'] = [traceback.format_exc()]

        if 'exception' in self.attributes:
            e = self.attributes['exception']
            message += str(e)

            logger.error("{}\n{}".format(message, "".join(traceback.format_tb(e.__traceback__))))

            if isinstance(e, BaseException):
                self.attributes['exception'] = self._format_exception(e)
                self.attributes['__traceback__'].append(traceback.format_tb(e.__traceback__))

        super(EException, self).__init__(message)

    @property
    def message(self):
        return self.attributes.get('message', '?')

    @property
    def details(self):
        return ''

    @property
    def traceback(self):
        txt = ''
        for tb in self.info['__traceback__']:
            txt += traceback.format_tb(tb) if tb else ''
        return txt

    def save(self, filename):
        dir = os.path.dirname(filename)
        if not os.path.exists(dir):
            os.makedirs(dir)
        #print(self.attributes['exception'], type(self.attributes['exception']), '######',filename, dir)
        #return

        with open(filename, 'w') as f:
            yaml.safe_dump(self.attributes, f)


    def _format_exception(self, e):
        return str(e)

    def __str__(self):
        return self.message
        import pprint
        return pprint.pformat(self.attributes)


class EConanException(EException):

    def __init__(self, message, exception=None):
        super(EConanException, self).__init__(message + str(exception or ''), exception=exception)


class EDockerException(EException):

    def __init__(self, message, docker=None):
        from epm.worker import DockerBase
        if isinstance(docker, DockerBase):
            docker = {'returncode': docker.returncode,
                      'command': docker.command_str,
                      }

        super(EException, self).__init__(message, docker=docker)


class ESyntaxError(EException):

    def __init__(self, message):
        super(EException, self).__init__(message)


def load_exception(filename):
    with open(filename) as f:
        attrs = yaml.safe_load(f)
    class_name = attrs['__class__']
    classes = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    for name, klass in classes:
        if name == class_name:
            return klass(attrs)
    return EException(attrs)





















class ECommandError(EException):
    """ command or argument not correct
    """
    pass


class ESyntaxError(EException):
    """
    """
    pass


class ENotFoundError(EException):
    pass


class EInvalidConfiguration(EException):
    pass


class EMetadataError(EException):

    def __init__(self, msg, details=None, traceback=None):
        super(EMetadataError, self).__init__(msg=msg, details=details, traceback=traceback)

class APIError(Exception):

    def __init__(self, method, msg, details, traceback=None):
        self.method = method
        super(APIError, self).__init__(msg=msg, details=details, traceback=traceback)


class EConanAPIError(EException):
    def __init__(self, msg, details, traceback=None):
        super(APIError, self).__init__(msg=msg, details=details, traceback=traceback)


class EAPIError(EException):

    def __init__(self, method, msg, details, traceback=None, api=None):
        self.method = method
        super(APIError, self).__init__(msg=msg, details=details, traceback=traceback)


class EDockerAPIError(EException):

    def __init__(self, returncode, msg=None, api=None):
        self.returncode = returncode
        self.api = api
        #os.path.join('.epm/')
        super(EDockerAPIError, self).__init__(msg=msg)


class EForwardException(EException):
    """
        Conan error (exeception) wrapper
        this happend on executed conan methon and raised conan exception (ConanException)
    """

    def __init__(self, msg, exception, traceback):
        """
        :param msg: (str) msg description the action caused the error
        :param detail: (dict)
        :param conan: (ConanExeption) conan exception
        """
        super(EForwardException, self).__init__(msg=msg, traceback=traceback)
        self.exception = exception

