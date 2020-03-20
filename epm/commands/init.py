
from epm.commands import Command, register_command, ArgparseArgument


class Init(Command):
    """
    """

    name = 'init'
    help = 'Initialize a C/C++ project for package development.'
    prog = 'epm [-p PROFILE] [-s SCHEME] [-r RUNNER] %s' % name

    def __init__(self):
            args = [
                ArgparseArgument("template", default=None, type=str,
                                 help="The template which used to generate project skeleton.")
                ArgparseArgument("--name", default=None, type=str,
                                 help="name of the package, if not specified use the folder name."),

                ArgparseArgument("--version", type=str, default='0.0.1',
                                 help="version of the package, if not specified use default value 0.0.1"),

                ]
            Command.__init__(self, args)

    def run(self, config, args):
        print('YES')


class ProjectTemplate(Command):
    """
    """

    name = 'project-template'
    help = 'Initialize a C/C++ project for package development.'
    prog = 'epm [-p PROFILE] [-s SCHEME] [-r RUNNER] %s' % name

    def __init__(self):
            args = [
                ArgparseArgument("template", default=None, type=str,
                                 help="The template which used to generate project skeleton.")
                ]
            Command.__init__(self, args)

    def run(self, config, args):
        print('YES')

register_command(Init)
