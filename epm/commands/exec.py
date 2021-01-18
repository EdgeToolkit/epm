from epm.commands import Command, register_command, ArgparseArgument


class Exec(Command):
    """
    """
    name = 'exec'
    help = 'Execute program in sandbox.'

    def __init__(self):
        args = [

            ArgparseArgument("name", type=str,
                             help="The executable name of program which defined in package.yml program section.")
            ]

        Command.__init__(self, args)

    def run(self, args, api):

        param = self.parameter(args)
        param['name'] = args.name
        param['args'] = args.argv

        api.sandbox(param)


register_command(Exec)
