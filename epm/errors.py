

class EPMError(Exception):
    """
             Generic EPM exception
    """
    def __init__(self, *args, **kwargs):
        self.msg = kwargs.pop("msg", None)

    def as_dict(self):
        pass



class EException(Exception):
    """
         Generic EPM exception
    """
    def __init__(self, *args, **kwargs):
        self.msg = kwargs.pop("msg", None)
        self.details = kwargs.pop("details", None)
        self.traceback = kwargs.pop("traceback", None)

        super(EException, self).__init__(*args, **kwargs)

    def __str__(self):
        from conans.util.files import exception_message_safe
        msg = super(EException, self).__str__()


        return exception_message_safe(msg)


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

