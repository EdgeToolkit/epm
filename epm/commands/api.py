
from epm.commands import Command, register_command, ArgparseArgument
from epm.errors import APIError
from epm.worker import param_decode


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

        method = getattr(api, args.method[0])
        if not method:
            raise APIError('epm API no method <%s>.' % args.method)
        method(param)


register_command(APICommand)
