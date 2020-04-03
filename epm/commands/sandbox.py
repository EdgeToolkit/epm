from epm.commands import Command, register_command, ArgparseArgument


class Sandbox(Command):
    """
    """

    name = 'sandbox'
    help = 'Sandbox to execute build/create binary package.'
    #prog = 'epm [-p PROFILE] [-s SCHEME] [-r RUNNER] %s' % name

    def __init__(self):
        args = [

            ArgparseArgument("sandbox_command", type=str,
                             help="The sandbox command witch defined in package.yml sandbox section.")
            ]

        Command.__init__(self, args)

    def run(self, args, api):
        param = self.parameter(args)
        param['command'] = args.sandbox_command
        param['args'] = args.argv
        api.sandbox(param)


register_command(Sandbox)
