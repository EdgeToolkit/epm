

class Dummy(object):
    """ dummy conan output
    """

    def __init__(self, stream, stream_err=None, color=False):
        self._stream = stream
        self._stream_err = stream_err or stream
        self._color = color

    @property
    def is_terminal(self):
        return False

    def writeln(self, data, front=None, back=None, error=False):
        pass

    def write(self, data, front=None, back=None, newline=False, error=False):
        pass

    def info(self, data):
        pass

    def highlight(self, data):
        pass

    def success(self, data):
        pass

    def warn(self, data):
        pass

    def error(self, data):
        pass

    def input_text(self, data):
        pass

    def rewrite_line(self, line):
        pass

    def flush(self):
        pass