
from conans.client.output import ConanOutput
from epm.util import system_info
PLATFORM, ARCH = system_info()



class Output(ConanOutput):

    def __init__(self, stream, stream_err=None, color=False):
        super(Output, self).__init__(stream, stream_err, color)

    def write(self, data, front=None, back=None, newline=False, error=False):
        #if PLATFORM == 'Windows':
        print('*', len(data))
        n = len(data)
        for i in range(0, n):
            print(i, data[i], '*')
        data = data.replace('\r\n', '\n')
        super(Output, self).write(data, front, back, newline, error)

