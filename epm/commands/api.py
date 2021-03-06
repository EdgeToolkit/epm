
from epm.commands import Command, register_command, ArgparseArgument
from epm.errors import EException
#from epm.worker import param_decode
from epm.utils.logger import syslog

class APICommand(Command):
    '''

    '''

    name = 'api'
    help = 'call epm api via command.'

    def __init__(self):
            args = [
                ArgparseArgument('method', nargs=1, help="the api method to be called"),

                ArgparseArgument('param', nargs='?', help="param of api method which is base64 encode for json"),

                ]
            Command.__init__(self, args)

    def run(self, args, api):
        param = None
        if args.param:
            param = param_decode(args.param)
            import pprint
            syslog.info('API command (%s) with param:\n%s\n' % (args.method, pprint.pformat(param, indent=2)))

        method = getattr(api, args.method[0])
        if not method:
            raise EException('epm API no method <%s>.' % args.method)
        method(param)


#register_command(APICommand)
