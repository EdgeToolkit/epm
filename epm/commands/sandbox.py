from epm.commands import Command, register_command, ArgparseArgument


class Sandbox(Command):
    """
    """

    name = 'sandbox'
    help = 'Sandbox to execute build/create binary package.'
    #prog = 'epm [-p PROFILE] [-s SCHEME] [-r RUNNER] %s' % name

    def __init__(self):
        Command.__init__(self, [])

    def run(self, args):
        print(args)


register_command(Sandbox)
