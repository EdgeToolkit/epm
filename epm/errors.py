import os
import traceback
from conans.errors import ConanException


class EException(Exception):
    """
         Generic EPM exception
    """
    def __init__(self, msg, **kwargs):
        self.info = {'__message__': msg, '__traceback__': []}
        self.info.update(**kwargs)
        e = self.info.get('exception')
        if isinstance(e, BaseException):
            detail = str(e)
            if detail:
                self.info['__message__'] += '\n  + {}'.format(detail)
            self.info.pop('exception')
            self.info['__traceback__'].append(e.__traceback__)

        super(EException, self).__init__(msg, kwargs)

    @property
    def message(self):
        return self.info.get('__message__', '?')

    def traceback(self, filename=None):

        file = None
        if filename:
            folder = os.path.dirname(filename)
            if not os.path.exists(folder):
                os.makedirs(folder)
            file = open(filename, 'w')

        traceback.print_tb(self.__traceback__, file=file)
        for tb in self.info['__traceback__']:
            if tb:
                traceback.print_tb(tb, file=file)
        if file:
            file.close()

    def __str__(self):
        import pprint
        return pprint.pformat(self.info)


class EConanException(EException):

    def __init__(self, msg, conan_exception):
        super(EConanException, self).__init__('{}\n[conan] {}\n'.format(msg, str(conan_exception)))
        self.info['__class__'] = type(self)
        if isinstance(conan_exception, ConanException):
            self.info['details'] = str(conan_exception)
            self.info['__traceback__'].append(conan_exception.__traceback__)
        elif isinstance(conan_exception, dict):
            self.info['details'] = str(conan_exception)


class EDockerException(EException):

    def __init__(self, docker):
        import os
        filename = os.path.join('.epm/{}.json'.format(docker.name))
        details = {'msg': 'execut command in docker failed. no details since no info file.'}
        if os.path.exists(filename):
            with open(filename) as f:
                import json
                details = json.loads(f)

        details['docker-exit-code'] = docker.returncode
        details['docker-command'] = docker.command_str
        msg = details.pop('msg')
        super(EDockerException, self).__init__(msg, **details)































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

