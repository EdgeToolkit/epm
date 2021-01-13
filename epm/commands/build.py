
from epm.commands import Command, register_command, ArgparseArgument


class Build(Command):
    '''
    Build specified target package according PROFILE and SCHEME.
    if the SCHEME not specified, will build default options (which defined
    in conanfile.py default_options).

    The RUNNER can be auto, shell, docker. if not specified, it will take as auto.

    '''

    name = 'build'
    help = 'Builds a binary package for the project.'
    prog = 'epm [-p PROFILE] [-s SCHEME] [-r RUNNER] %s' % name

    def __init__(self):
            args = [

                ArgparseArgument("-c", "--configure", default=None, action="store_true",
                                    help="Execute the configuration step to configure the this C/C++ project."
                                         "When specified, make/package/sandbox won't run unless "
                                         "--make/--package/--sandbox specified"),

                ArgparseArgument("-m", "--make", default=None, action="store_true",
                                    help="Execute the make step to build the C/C++ lib or executable,. When "
                                         "specified, configure/package/sandbox won't run unless "
                                         "--configure/--package/--sandbox specified"),

                ArgparseArgument("-p", "--package", default=None, action="store_true",
                                    help=""),

                ArgparseArgument("-t", "--test", default=None, action='append',
                                 help=""),

                ArgparseArgument("--program", default=None, action='append',
                                 help=""),

            ]
            Command.__init__(self, args)

    def run(self, args, api):

        steps = []
        steps += ['configure'] if args.configure else []
        steps += ['make'] if args.make else []
        steps += ['package'] if args.package else []
        program = args.program or []

        param = self.parameter(args)
        if not steps:
            if not program:
                steps = ['configure', 'make', 'package']
                program = None

        param['steps'] = steps
        param['step'] = steps
        param['program'] = program

        api.build(param)





register_command(Build)

