from epm.commands import Command, register_command, ArgparseArgument


class RunX(Command):
    """
    """

    name = 'runx'
    help = 'Execute command in epm running environment.'

    def __init__(self):
        args = [

            ArgparseArgument("extension", type=str,
                             help="The name fo extension to be run.")
            ]

        Command.__init__(self, args)

    def run(self, args, api):
        param = self.parameter(args)
        param['command'] = args.extension
        param['args'] = args.argv
        return api.runx(param)


register_command(RunX)
