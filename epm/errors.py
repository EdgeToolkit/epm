
class EException(Exception):
    """
         Generic EPM exception
    """
    def __init__(self, *args, **kwargs):
        self.info = None
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

class APIError(Exception):

    def __init__(self, *args, **kwargs):
        self.info = None
        super(EException, self).__init__(*args, **kwargs)
