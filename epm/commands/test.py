from epm.commands import Command, register_command, ArgparseArgument


class TestCommand(Command):
    """
    """

    name = 'test'
    help = 'run test program defined in the package project (package.yml->test).'

    def __init__(self):
        args = [

            ArgparseArgument("name", type=str,
                             help="The test program name which is the key of `test` section.")
            ]

        Command.__init__(self, args)

    def run(self, args, api):
        param = self.parameter(args)
        param['command'] = args.name
        param['args'] = args.argv

        api.sandbox(param)


register_command(TestCommand)
