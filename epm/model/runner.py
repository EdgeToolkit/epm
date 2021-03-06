
from conans.client.output import ConanOutput
from epm.utils import PLATFORM


class Output(ConanOutput):

    def __init__(self, stream, stream_err=None, color=False):
        super(Output, self).__init__(stream, stream_err, color)

    def write(self, data, front=None, back=None, newline=False, error=False):
        if PLATFORM == 'Windows':
            data = data.replace('\r\n', '\n')
        super(Output, self).write(data, front, back, newline, error)

