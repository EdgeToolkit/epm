
from epm.commands import Command, register_command, ArgparseArgument


class Create(Command):
    """
    Builds a binary package and storage in local cache.

    Uses the specified PROFILE and SCHEME.
    """

    name = 'create'
    help = 'Builds a binary package for the project and cache it in local.'
    prog = 'epm [-p PROFILE] [-s SCHEME] [-r RUNNER] %s' % name

    def __init__(self):
            args = [

                ArgparseArgument("--storage", default=None,
                                    help="all conan package will be download and cached under project directory"
                                         "that is conan storage path will be set at .conan folder in project."),

                ArgparseArgument("--clear", default=False, action="store_true",
                                    help="clear local cache of .conan in project"),

                ArgparseArgument("--no-sandbox", default=False, action="store_true",
                                 help="do not build sandbox program (with local cached package")

            ]
            Command.__init__(self, args)

    def run(self, args, api):
        param = self.parameter(args)
        if args.storage:
            param['storage'] = args.storage

        if args.clear:
            param['clear'] = args.clear

        if not args.no_sandbox:
            param['sandbox'] = True

        api.create(param)


register_command(Create)
