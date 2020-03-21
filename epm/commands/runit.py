from epm.commands import Command, register_command, ArgparseArgument


class Run(Command):
    """
    """

    name = 'run'
    help = 'Execute command in epm running environment.'
    #prog = 'epm [-p PROFILE] [-s SCHEME] [-r RUNNER] %s' % name

    def __init__(self):
        Command.__init__(self, [])

    def run(self, args):
        print(args)


register_command(Run)
